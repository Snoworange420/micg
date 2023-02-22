import json
import os

def saveConfig(username):

    filename = "config.json"

    if filename not in os.listdir('.'):
        with open(filename, 'w') as file:
            json.dump({}, file)


    with open(filename, 'w') as file:
        data = {
            "config": {
                "username": username,
            }
        }

        json.dump(data, file)

def _update_user_name(name: str):
    import main
    main.username = name
    pass
        
def loadConfig():

    filename = "config.json"

    if filename not in os.listdir('.'):
        with open(filename, 'w') as file:
            json.dump({}, file)
            return

    with open(filename, "r") as file:
        data = json.load(file)

        _update_user_name(data["config"]["username"])
