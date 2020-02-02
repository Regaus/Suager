import json
import random
import traceback
from collections import namedtuple
from io import BytesIO
import discord

from utils import time


def get(file):
    try:
        with open(file, encoding='utf8') as data:
            # return json.load(data, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
            return json.load(data, object_hook=lambda d: namedtuple('JSONData', d.keys())(*d.values()))
    except AttributeError:
        raise AttributeError("Unknown argument")
    except FileNotFoundError:
        raise FileNotFoundError("JSON file wasn't found")


def random_colour():
    return random.randint(0, 0xffffff)


def get_config():
    return get("config.json")


def round_value(value):
    try:
        if value < 10:
            rounded = round(value, 2)
        elif 10 <= value < 100:
            rounded = round(value, 1)
        else:
            rounded = int(value)
        return rounded
    except Exception as e:
        return e


def string_make(val, sa: int = 0, negative: bool = False):
    minus = "-" if negative else ""
    res = ['', "K", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "O", "N", "D"]
    if sa >= len(res):
        return f"{minus}{round_value(val):,}e{sa*3}"
    return f"{minus}{round_value(val):,}{res[sa]}"


def value_string(val, sa: int = 0, k: bool = False, negative: bool = False):
    if val == float("inf"):
        return "Infinity"
    elif val == float("inf") * -1:
        return "Negative Infinity"
    if val != val:
        return "NaN"
    if val < 0:
        val *= -1
        negative = True
    try:
        if val < 1e6 and sa == 0 and not k:
            m = "-" if negative else ""
            return f"{m}{round_value(val):,}"
        if val / 1000 >= 1:
            return value_string(val/1000, sa + 1, k, negative)
        return string_make(val, sa, negative)
    except OverflowError:
        return "An overflow error's worth"
    except RecursionError:
        return "A recursion error's worth"
    except Exception as e:
        return f"An error - {e}"


def traceback_maker(err, advance: bool = True, text: str = None):
    _traceback = ''.join(traceback.format_tb(err.__traceback__))
    error = '```py\n{3}{1}{0}: {2}\n```'.format(
        type(err).__name__, _traceback, err, f"{text}\n" if text is not None else '')
    return error if advance else f"{type(err).__name__}: {err}"


def reason(who, why=None):
    r = f"[ {who} ]"
    if why is None:
        return f"{r} No reason given..."
    return f"{r} {why}"


def action(what, *, who=None, why=None, many: bool = False, emote=None):
    if who is None:
        s = 's' if many else ''
        output = f"**{what}** the id{s}/user{s}"
    else:
        output = f"**{what}** {who}"
    if why is not None:
        output += f" for {why}"
    if emote is not None:
        output += f" {emote}"
    return f"<:allow:610828713424191498> Successfully {output}"


async def pretty_results(ctx, filename: str = "Results", resultmsg: str = "Here's the results:", loop=None):
    if not loop:
        return await ctx.send("The result was empty...")

    pretty = "\r\n".join([f"[{str(num).zfill(2)}] {data}" for num, data in enumerate(loop, start=1)])

    if len(loop) < 15:
        return await ctx.send(f"{resultmsg}```ini\n{pretty}```")

    data = BytesIO(pretty.encode('utf-8'))
    await ctx.send(
        content=resultmsg,
        file=discord.File(data, filename=time.file_ts(filename.title()))
    )


# version = get("config.json").version
# invite = "https://discordapp.com/invite/UrHhtWE"
invite = "https://senko.weeb.services/lair"
owners = get("config.json").owners
prefixes = 'data/prefixes'
