import os
import random
import block
import json


class generator:
    def __init__(self, seed, floor=10):
        self.seed = seed  # unused

        # holes in the floor are a feature

        # a start to generate more world next to
        self.generated = {
            19: floor,
            20: floor,
            21: floor,
        }

        self.min_gen = 19
        self.min_gen_value = self.generated[self.min_gen]
        self.min_gen_slope = 0

        self.max_gen = 21
        self.max_gen_value = self.generated[self.max_gen]
        self.max_gen_slope = 0

    def gen(self, i):
        if i in self.generated:
            return self.generated[i]
        else:
            if i < self.min_gen - 1:
                for x in range(self.min_gen, i - 1, -1):
                    self._gen(x)
            elif i > self.max_gen + 1:
                for x in range(self.max_gen, i + 1):
                    self._gen(x)
            else:
                self._gen(i)

            return self.generated[i]

    def _gen(self, i):
        if i in self.generated:
            return self.generated[i]
        else:
            if i == self.min_gen - 1:
                self.min_gen_slope = min(max(-1, self.min_gen_slope + int(random.random() * 3) - 1), 1)
                self.min_gen_value += self.min_gen_slope
                self.generated[i] = self.min_gen_value
                self.min_gen = i
            elif i == self.max_gen + 1:
                self.max_gen_slope = min(max(-1, self.max_gen_slope + int(random.random() * 3) - 1), 1)
                self.max_gen_value += self.max_gen_slope
                self.generated[i] = self.max_gen_value
                self.max_gen = i
            else:
                self.generated[i] = 10

            return self.generated[i]

    def load(self, raw: dict):
        self.seed = raw['seed']

        self.generated = raw['gen']

        self.min_gen = raw['min_gen']
        self.min_gen_value = raw['min_gen_value']
        self.min_gen_slope = raw['min_gen_slope']

        self.max_gen = raw['max_gen']
        self.max_gen_value = raw['max_gen_value']
        self.max_gen_slope = raw['max_gen_slope']

    def save(self):
        return {
            'seed': self.seed,

            'gen': self.generated,

            'min_gen': self.min_gen,
            'min_gen_value': self.min_gen_value,
            'min_gen_slope': self.min_gen_slope,

            'max_gen': self.max_gen,
            'max_gen_value': self.max_gen_value,
            'max_gen_slope': self.max_gen_slope,
        }


class world:
    def __init__(self, gen: generator, gen_new=True, server=None, serving=False):
        self.gen = gen
        self.world = {}

        self.gen_new = gen_new
        self.server = server
        self.serving = serving

        self.blocks = block.load()

        self.to_update = []
        self.to_append = []

        self.filename = None

        if self.serving and self.server is None:
            assert False, 'you did it wrong'

    def gen_chunk(self, x, y):
        # print('chunk', x)
        # if self.filename is not None:
        #     with open('saves/' + self.filename, 'r') as file:
        #         w = json.load(file)
        #         if x in w:
        #             return w[x]

        if x in self.world:
            return

        c = []
        for dy in range(40):
            line = []
            for dx in range(40):
                line.append(block.block('air', self.blocks))
            c.append(line)

        if y <= 0:
            for i in range(40):
                height = self.gen.gen(i + x * 40) + y * 40
                for dy in range(min(height, 40)):
                    if dy == 0 and y == 0:
                        b = block.block('bedrock', self.blocks)

                    elif dy == height - 1:
                        b = block.block('grass', self.blocks)
                    elif dy == height - 2:
                        b = block.block('grass', self.blocks)

                    elif dy == height - 3:
                        b = block.block('dirt', self.blocks)
                    elif dy == height - 4:
                        b = block.block('dirt', self.blocks)
                    elif dy == height - 5:
                        b = block.block('dirt', self.blocks)

                    else:
                        if height - dy - 1 > 100 and random.random() > max(.99, 1 - (height - dy - 101) / 10):
                            b = block.block('diamond', self.blocks)
                        elif height - dy - 1 > 100 and random.random() > .9 - (height - dy - 101) / 50:
                            b = block.block('coal', self.blocks)
                        else:
                            b = block.block('stone', self.blocks)

                    b.x = i + x * 40
                    b.y = 39 - dy + y * 40

                    b.support = height - dy - 1
                    b.on_floor = True

                    c[39 - dy][i % 40] = b

        self.world[(x, y)] = c

    def get(self, x, y):
        if (x // 40, y // 40) in self.world:
            return self.world[(x // 40, y // 40)][y % 40][x % 40]
        else:
            if self.gen_new:
                self.gen_chunk(x // 40, y // 40)
            else:
                if self.server is not None:
                    self.server.get_chunk(x // 40, y // 40)
                else:
                    raise ValueError('if world.gen_new == False, you should give net.client')
            if (x // 40, y // 40) in self.world:
                return self.get(x, y)
            else:
                return block.block('air', self.blocks)

    def set(self, x, y, value: block.block, update=True):
        value.x = x
        value.y = y

        if y < 40:
            if self.gen_new:
                self.to_append += [self.get(value.x - 1, value.y), self.get(value.x, value.y - 1),
                                   self.get(value.x + 1, value.y), self.get(value.x, value.y + 1), value]

            if (x // 40, y // 40) in self.world:
                self.world[(x // 40, y // 40)][y % 40][x % 40] = value
                if self.server is not None and self.serving and update:  # TODO: chunk updates borkken (if online ofc.)
                    self.server.send_all('AP' + str(x) + ' ' + str(y) + ' ' + value.name)
                elif self.server is not None and not self.serving and update:  # multiplayer client
                    self.server.set_block(x, y, value)
            else:
                self.get(x, y)  # load the chunk

    def update(self, fast=False):
        # print(self.to_update)
        i = 0
        while len(self.to_update) and (i < 100 or fast):
            b = self.to_update[0]
            if b.y is not None:
                if b.y < 40:
                    self.to_append += b.update(self)
            self.to_update.pop(0)

            i += 1
        if not len(self.to_update):
            for b in self.to_append:
                if b not in self.to_update:
                    self.to_update.append(b)
            self.to_append = []

        # TODO: chunk unloading

    def save(self, file: str = None):
        if 'saves' not in os.listdir('./'):
            os.mkdir('saves')

        if file is not None:
            self.filename = file

        if self.filename is not None:
            if self.filename not in os.listdir('saves'):
                with open('saves/' + self.filename, 'w') as file:
                    json.dump({}, file)

            # with open('saves/' + self.filename, 'r') as file:
            #     w = json.load(file)
            # w2 = {}
            # for c in w:
            #     if c not in self.world:
            #         w2[c] = w[c]
            #     else:
            #         w2[c] = self.world[c]
            # for c in self.world:
            #     if c not in w2:
            #         w2[c] = self.world[c]
            with open('saves/' + self.filename, 'w') as file:
                w3 = {}
                for i in self.world:
                    c = []
                    for j in self.world[i]:
                        row = []
                        for b in j:
                            if type(b) != block.block:
                                # print('error:', b)
                                row.append({'name': 'air', 'support': 0})
                            else:
                                row.append({'name': b.name, 'support': b.support})
                        c.append(row)
                    w3[str(i[0]) + ' ' + str(i[1])] = c

                w3['data'] = {}
                w3['data']['gen'] = self.gen.save()

                json.dump(w3, file)

    def load(self, file: str = None):
        if file is not None:
            self.filename = file

        if self.filename is not None:
            with open('saves/' + self.filename, 'r') as file:
                raw = json.load(file)

                self.world = {}
                for i in raw:
                    if i != 'data':
                        c = []
                        y = int(i.split(' ')[1]) * 40
                        for j in raw[i]:
                            row = []
                            x = int(i.split(' ')[0]) * 40
                            for ib in j:
                                b = block.block(ib['name'], self.blocks)
                                b.support = ib['support']

                                b.x = x
                                b.y = y

                                b.on_floor = True

                                row.append(b)
                                x += 1
                            y += 1
                            c.append(row)
                        # print(i)
                        self.world[(int(i.split(' ')[0]), int(i.split(' ')[1]))] = c
                    else:
                        self.gen.load(raw[i]['gen'])  # TODO: also load and save player position and inventory
                        # TODO: also load other players if multiplayer server

                print('loaded')

    def serialize_chunk(self, x, y):
        out = ''
        if (x, y) not in self.world:
            self.gen_chunk(x, y)
        chunk = self.world[(x, y)]
        for row in chunk:
            for b in row:
                out += b.name + ','
        return out

    def deserialise_chunk(self, data: str):
        chunk = []
        split = data.split(' ')
        if len(split) != 3:
            raise Exception('chunk incorrectly formatted')
        x = 0
        y = 0
        row = []
        for b in split[2].split(','):
            b = block.block(b, self.blocks)
            b.x = x
            b.y = y
            row.append(b)
            x += 1

            if x == 40:
                chunk.append(row)
                row = []
                x = 0
                y += 1

        print('deserialised chunk', (int(split[0]), int(split[1])), 'size:', len(chunk[0]), len(chunk))
        self.world[(int(split[0]), int(split[1]))] = chunk
        print(self.world[(int(split[0]), int(split[1]))][39][20].name)
        print([c for c in self.world])