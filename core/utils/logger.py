import os

from core.utils import time


def log(name: str, log_type: str, data: str):
    date = time.now(None).strftime("%Y-%m-%d")
    try:
        os.makedirs(f"data/{name}/logs/{date}")
    except FileExistsError:
        pass
    stuff = open(f"data/{name}/logs/{date}/{log_type}.rsf", "a+", encoding="utf-8")
    try:
        stuff.write(f"{data}\n")
        stuff.close()
    except UnicodeEncodeError as e:
        print(e)
        try:
            _data = data.encode("utf-8")  # Try to encode the shit
            stuff.write(f"{str(_data)[2:-1]}\n")
            stuff.close()
        except Exception as _:
            del _
