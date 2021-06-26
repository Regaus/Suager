import json

from utils import time


def change_value(file, value, change_to):
    try:
        with open(file, "r") as jsonFile:
            data = json.load(jsonFile)
    except FileNotFoundError:
        raise FileNotFoundError("The file you tried to get does not exist...")

    data[value] = change_to
    with open(file, "w") as jsonFile:
        json.dump(data, jsonFile, indent=2)


def change_version(value: str, new: str, name: str):
    data = json.loads(open("version.json", "r", encoding="utf-8").read())
    data[name][value] = new
    if value == "version":
        data[name]["last_update"] = int(time.now_ts())
    open("version.json", "w", encoding="utf-8").write(json.dumps(data, indent=2))
