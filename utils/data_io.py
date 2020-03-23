import json


def change_value(file, value, change_to):
    try:
        with open(file, "r") as jsonFile:
            data = json.load(jsonFile)
    except FileNotFoundError:
        raise FileNotFoundError("The file you tried to get does not exist...")

    data[value] = change_to
    with open(file, "w") as jsonFile:
        json.dump(data, jsonFile, indent=2)


def change_versions(version, value, new):
    data = json.loads(open("config.json", "r").read())
    data["bots"][version][value] = new
    open("config.json", "w").write(json.dumps(data))
    data = json.loads(open("config_example.json", "r").read())
    data["bots"][version][value] = new
    open("config_example.json", "w").write(json.dumps(data))


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
