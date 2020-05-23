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


def change_version(value: str, new):
    data = json.loads(open("config.json", "r").read())
    data[value] = new
    data["last_update"] = int(time.now_ts())
    open("config.json", "w").write(json.dumps(data, indent=2))
    data = json.loads(open("config_example.json", "r").read())
    data[value] = new
    data["last_update"] = int(time.now_ts())
    open("config_example.json", "w").write(json.dumps(data, indent=2))


def change_values(value1: str, value2: str or None, action: str, value):
    data1 = json.loads(open("config.json", "r").read())
    data2 = json.loads(open("config_example.json", "r").read())
    if action == "add":
        if value2 is None:
            def change(data, key, val):
                try:
                    if val not in data[key]:
                        data[key].append(val)
                except KeyError:
                    data[key] = [val]
            change(data1, value1, value)
            change(data2, value1, value)
        else:
            def change(data, key1, key2, val):
                try:
                    if val not in data[key1][key2]:
                        data[key1][key2].append(val)
                except KeyError:
                    data[key1][key2] = [val]
            change(data1, value1, value2, value)
            change(data2, value1, value2, value)
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
            change(data2, value1, value)
        else:
            def change(data, key1, key2, val):
                try:
                    data[key1][key2].remove(val)
                except ValueError:
                    pass
                except KeyError:
                    data[key1][key2] = []
            change(data1, value1, value2, value)
            change(data2, value1, value2, value)
    # else:
    #     change1 = data1[value1][value2]
    # data[value] = new
    # data[value] = new
    open("config.json", "w").write(json.dumps(data1, indent=2))
    open("config_example.json", "w").write(json.dumps(data2, indent=2))


# def change_versions(version, value, new):
#     data = json.loads(open("config.json", "r").read())
#     data["bots"][version][value] = new
#     open("config.json", "w").write(json.dumps(data, indent=2))
#     data = json.loads(open("config_example.json", "r").read())
#     data["bots"][version][value] = new
#     open("config_example.json", "w").write(json.dumps(data, indent=2))


# def append_value(file, value, addition):
#     try:
#         with open(file, "r") as jsonFile:
#             data = json.load(jsonFile)
#     except FileNotFoundError:
#         raise FileNotFoundError("The file you tried to get does not exist...")
#
#     data[value].append(addition)
#     with open(file, "w") as jsonFile:
#         json.dump(data, jsonFile, indent=2)
