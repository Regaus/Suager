import json

from core.utils import time


def change_value(file, value, change_to):
    try:
        with open(file, "r") as jsonFile:
            data = json.load(jsonFile)
    except FileNotFoundError:
        raise FileNotFoundError("The file you tried to get does not exist...")

    data[value] = change_to
    with open(file, "w") as jsonFile:
        json.dump(data, jsonFile, indent=2)


def change_version(value: str, new: str, index: int):
    data = json.loads(open("config_v6.json", "r").read())
    data["bots"][index][value] = new
    data["bots"][index]["last_update"] = int(time.now_ts())
    open("config_v6.json", "w").write(json.dumps(data, indent=2))
    try:
        data = json.loads(open("config_v6_ex.json", "r").read())
        data["bots"][index][value] = new
        data["bots"][index]["last_update"] = int(time.now_ts())
        open("config_v6_ex.json", "w").write(json.dumps(data, indent=2))
    except FileNotFoundError:
        pass
