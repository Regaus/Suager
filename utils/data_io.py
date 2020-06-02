import json

from utils import time, locks


def change_value(file, value, change_to):
    try:
        with open(file, "r") as jsonFile:
            data = json.load(jsonFile)
    except FileNotFoundError:
        raise FileNotFoundError("The file you tried to get does not exist...")

    data[value] = change_to
    with open(file, "w") as jsonFile:
        json.dump(data, jsonFile, indent=2)


def change_version(value: str, new):
    data = json.loads(open("config.json", "r").read())
    data[value] = new
    data["last_update"] = int(time.now_ts())
    open("config.json", "w").write(json.dumps(data, indent=2))
    data = json.loads(open("config_example.json", "r").read())
    data[value] = new
    data["last_update"] = int(time.now_ts())
    open("config_example.json", "w").write(json.dumps(data, indent=2))


def change_locks(value1: str, value2: str or None, action: str, value):
    data1 = locks.get_locks()
    if action == "add":
        if value2 is None:
            def change(data, key, val):
                try:
                    if val not in data[key]:
                        data[key].append(val)
                except KeyError:
                    data[key] = [val]
            change(data1, value1, value)
        else:
            def change(data, key1, key2, val):
                try:
                    if val not in data[key1][key2]:
                        data[key1][key2].append(val)
                except KeyError:
                    data[key1][key2] = [val]
            change(data1, value1, value2, value)
    if action == "remove":
        if value2 is None:
            def change(data, key, val):
                try:
                    data[key].remove(val)
                except ValueError:
                    pass
                except KeyError:
                    data[key] = []
            change(data1, value1, value)
        else:
            def change(data, key1, key2, val):
                try:
                    data[key1][key2].remove(val)
                except ValueError:
                    pass
                except KeyError:
                    data[key1][key2] = []
            change(data1, value1, value2, value)
    open("data/locks.json", "w+").write(json.dumps(data1, indent=2))


def change_infidels(tier: int, action: str, uid: int):
    data1 = locks.get_infidels()
    if action == "add":
        data1[str(tier)].append(uid)
    if action == "remove":
        try:
            data1[str(tier)].remove(uid)
        except ValueError:
            pass  # means it already isn't there
    open("data/infidels.json", "w+").write(json.dumps(data1, indent=2))
