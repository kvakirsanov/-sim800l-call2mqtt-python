from datetime import datetime

def get_time():
        return datetime.now().strftime("%Y-%m-%d %H:%I:%S")
