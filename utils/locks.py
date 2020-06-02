import json


def get_locks() -> dict:
    try:
        return json.loads(open("data/locks.json", "r").read())
    except FileNotFoundError:
        return {"love_exceptions": {}, "channel_locks": [], "server_locks": {}, "counter_locks": []}


def get_dict(amount: int) -> dict:
    d = {}
    for i in range(1, amount + 1):
        d[str(i)] = []
    return d


def get_infidels() -> dict:
    try:
        return json.loads(open("data/infidels.json", "r").read())
    except FileNotFoundError:
        return get_dict(7)
