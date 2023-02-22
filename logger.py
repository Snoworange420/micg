import os

def log(message):
    print(message)
    with open('latest.log', 'a', encoding="UTF-8") as f:
        f.write(message + "\n")
    
def resetLog():
    if "latest.log" not in os.listdir('.'):
        with open("latest.log", 'w', encoding="UTF-8") as f:
            f.write("")
            return
    
    with open("latest.log", "w", encoding="UTF-8") as f2:
        f2.truncate()