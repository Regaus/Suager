from __future__ import annotations

import json
import os
import random
import sys
import traceback
from io import BytesIO
from typing import Union

import discord
from numpy.random import Generator, PCG64

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


async def send(text: str | None, channel: discord.abc.GuildChannel | discord.Thread | discord.abc.PrivateChannel, *, embed: discord.Embed = None, embeds: list[discord.Embed] = None,
               file: discord.File = None, files: list[discord.File] = None, delete_after: float = None, e: bool = False, u: Union[bool, list] = False, r: Union[bool, list] = False):
    if text is not None:
        if len(text) > 2000:
            text = f"{text[:1997]}..."
            await channel.send("Message length exceeded 2000 characters...", delete_after=10)
    try:
        # Yes, it will complain about this "illegal" combination, but what the hell am I going to do?
        return await channel.send(content=text, embed=embed, embeds=embeds, file=file, files=files,
                                  delete_after=delete_after, allowed_mentions=discord.AllowedMentions(everyone=e, users=u, roles=r))
    except discord.Forbidden:
        await channel.send("Failed to send message. Please make sure that I have sufficient permissions (embed links and/or attach files)")
        if text:
            return await channel.send(content=text, delete_after=delete_after, allowed_mentions=discord.AllowedMentions(everyone=e, users=u, roles=r))


def traceback_maker(err, text: str = None, guild=None, author=None):
    _traceback = ''.join(traceback.format_tb(err.__traceback__))
    n = "\n"
    g = f'Guild: {guild.name}\n' if guild is not None else ''
    a = f'User: {author.name}\n' if author is not None else ''
    error = f'{g}{a}{f"Command: {text}{n}" if text is not None else ""}```py\n{_traceback}{type(err).__name__}: {err}\n```'
    return error


def print_error(text: str):
    return sys.stderr.write(f"{text}\n")


def random_colour() -> int:
    return random.randint(0, 0xffffff)


def reason(who, why=None) -> str:
    if why is None:
        return f"[{who}] No reason specified"
    return f"[{who}] {why}"


async def pretty_results(ctx, filename: str = "Results", result: str = "Here are the results:", loop=None):
    if not loop:
        return await send("The result was empty...", ctx.channel)
    pretty = "\r\n".join([f"[{str(num).zfill(2)}] {data}" for num, data in enumerate(loop, start=1)])
    if len(loop) < 15:
        return await send(f"{result} ```ini\n{pretty}```", ctx.channel)
    data = BytesIO(pretty.encode('utf-8'))
    return await send(result, ctx.channel, file=discord.File(data, filename=time.file_ts(filename.title())))


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


def random_id() -> int:
    return random.randint(1, 9999999)


def random_id2() -> int:
    return random.randint(1000, 9999)


def bold(string: str) -> str:
    return f"**{string}**"


class RegausError(Exception):
    def __init__(self, text):
        super().__init__(text)
        self.text = text


def random1(low: float = 0.0, high: float = 1.0, seed: int = 0) -> float:
    # state = RandomState(seed)
    state = Generator(PCG64(seed))
    return state.uniform(low, high, None)


# def random2(mean: float, sd: float, seed: int = 0) -> float:
#     # state = RandomState(seed)
#     state = Generator(PCG64(seed))
#     return state.normal(mean, sd, None)


red, red2, yellow, green2, green = 0xff0000, 0xff4000, 0xffc000, 0xc0ff00, 0x00ff00
