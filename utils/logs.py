import os

from utils import time
error_channel = 691442857537568789


def get_place(version: str, what: str):
    return f"logs/{version}/{what}.rsf"


def create():
    for version in ["stable", "beta", "alpha"]:
        for folder in ["logs", "data"]:
            try:
                os.makedirs(f"{folder}/{version}")
            except FileExistsError:
                pass


def save(file: str, data: str, ow: bool = False):
    try:
        p = "w" if ow else "a"
        stuff = open(file, f"{p}+")
        stuff.write(f"{data}\n")  # Add in an extra newline just in case
        stuff.close()
    except UnicodeEncodeError:
        print(f"{time.time()} > Failed to save data ({data})")
