from __future__ import annotations

import json
import os
import random
import traceback
from io import BytesIO
from sys import stderr

import discord

from utils import time


def get_config() -> dict:
    return json.loads(open("config.json", "r", encoding="utf-8").read())


def get_version() -> dict:
    return json.loads(open("version.json", "r", encoding="utf-8").read())


def create_dirs():
    make_dir("data/logs")
    config = get_config()
    for bot in config["bots"]:
        make_dir(f"data/logs/{bot['internal_name']}")


def make_dir(dir_name):
    try:
        os.makedirs(dir_name)
    except FileExistsError:
        pass


def traceback_maker(err: BaseException, text: str = None, guild=None, author=None):
    _traceback = ''.join(traceback.format_tb(err.__traceback__))
    t = f"Command: {text}\n" if text is not None else ""
    g = f"Guild: {guild.name}\n" if guild is not None else ""
    a = f"User: {author.name}\n" if author is not None else ""
    error = f"{g}{a}{t}```py\n{_traceback}{type(err).__name__}: {err}\n```"
    return error


def print_error(*values):
    return print(*values, file=stderr)


def random_colour() -> int:
    return random.randint(0, 0xffffff)


def reason(who, why=None) -> str:
    if why is None:
        return f"[{who}] No reason specified"
    return f"[{who}] {why}"


async def pretty_results(ctx, filename: str = "Results", result: str = "Here are the results:", loop=None):
    # ctx = commands.Context
    if not loop:
        return await ctx.send("The result was empty...")
    pretty = "\r\n".join([f"[{str(num).zfill(2)}] {data}" for num, data in enumerate(loop, start=1)])
    if len(loop) < 15:
        return await ctx.send(f"{result} ```ini\n{pretty}```")
    data = BytesIO(pretty.encode('utf-8'))
    return await ctx.send(result, file=discord.File(data, filename=time.file_ts(filename.title())))


def random_id2() -> int:
    return random.randint(1000, 9999)


def bold(string: str) -> str:
    return f"**{string}**"


red, red2, yellow, green2, green = 0xff0000, 0xff4000, 0xffc000, 0xc0ff00, 0x00ff00
red3 = 0xff4040
