import os

from utils import time

error_channel = 691442857537568789


def create_logs():
    try:
        os.makedirs("data")
    except FileExistsError:
        pass


def log(log_type: str, data: str):
    date = time.now(False).strftime("%Y-%m-%d")
    try:
        os.makedirs(f"data/{date}")
    except FileExistsError:
        pass
    stuff = open(f"data/{date}/{log_type}.rsf", "a+")
    try:
        stuff.write(f"{data}\n")
        stuff.close()
    except UnicodeEncodeError:
        try:
            _data = data.encode("utf-8")  # Try to encode the shit
            stuff.write(f"{str(_data)[2:-1]}\n")
            stuff.close()
        except Exception as _:
            del _
            # if the shit still doesn't work, do literally nothing
