from datetime import datetime
logs = []

class Log:
    def __init__(self, message, time=None):
        self.message = message
        self.time = time if time else datetime.now()

def add_alert(message):
    logs.append(Log(message))
