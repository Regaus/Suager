from __future__ import annotations

import json
import os
import random
import re
import traceback
from io import BytesIO
from sys import stderr
from typing import Iterable

import discord

from utils import bot_data, logger, time


def get_config() -> dict:
    return json.loads(open("config.json", "r", encoding="utf-8").read())


def get_version() -> dict:
    return json.loads(open("version.json", "r", encoding="utf-8").read())


def create_dirs():
    make_dir("data/logs")
    config = get_config()
    for bot in config["bots"]:
        make_dir(f"data/logs/{bot['internal_name']}")
    make_dir("data/gtfs")
    make_dir("data/dcu")


def make_dir(dir_name):
    try:
        os.makedirs(dir_name)
    except FileExistsError:
        pass


def traceback_maker(err: BaseException, text: str = None, guild=None, author=None, code_block: bool = True, limit_text: bool = False):
    _text = f"Command: {text}\n" if text is not None else ""
    _guild = f"Guild: {guild.name}\n" if guild is not None else ""
    _author = f"User: {username(author)} ({author.name})\n" if author is not None else ""
    _traceback = ''.join(traceback.format_tb(err.__traceback__))
    _main_error = f"{type(err).__name__}: {err}"
    if limit_text:
        length = 2000 - len(_text) - len(_guild) - len(_author) - len(_main_error) - (code_block * 10)  # code block = 10 extra chars
        _traceback = _traceback[-length:]
    traceback_str = f"{_traceback}{_main_error}"
    _error = f"```py\n{traceback_str}\n```" if code_block else traceback_str
    error = f"{_guild}{_author}{_text}{_error}"
    return error


def print_error(*values):
    return print(*values, file=stderr)


def log_error(bot: bot_data.Bot, text: str):
    print_error(text)
    logger.log(bot.name, "errors", text)


def random_colour() -> int:
    return random.randint(0, 0xffffff)


def reason(who, why=None) -> str:
    if why is None:
        return f"[{who}] No reason specified"
    return f"[{who}] {why}"


def alphanumeric_sort(iterable: Iterable[str]) -> Iterable[str]:
    """ Sort a list of alphanumeric strings in a human-friendly way """
    return sorted(iterable, key=alphanumeric_sort_string)


def alphanumeric_sort_string(entry: str) -> tuple[str | int, ...]:
    """ Sort numbers and the rest of the text in a human-friendly way """
    def convert(text: str) -> int | str:
        return int(text) if text.isdigit() else text

    # The output is surrounded by an empty string on both sides, but at least it works.
    return tuple(convert(part) for part in re.split(r"([0-9]+)", entry))


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


def username(user: discord.User | discord.Member) -> str:
    """ Return the user's display name. """
    return user.global_name or user.name


def build_interaction_content(interaction: discord.Interaction) -> str:
    """ Build fake message content that displays interaction data """
    data: dict = interaction.data
    if "name" not in data:
        return "Unknown slash command"
    content = f"Slash command: /"
    elements = [data["name"]]
    # Dig through subcommands - Check that the first "option" is not a command/subcommand
    while (options := data.get("options", [])) and options[0]["type"] < 3:  # 1 = SUB_COMMAND, 2 = SUB_COMMAND_GROUP
        data = data["options"][0]
        elements.append(data["name"])
    # Add option values
    for option in data.get("options", []):
        elements.append(f"{option['name']}={str(option.get('value', None))}")
    return content + " ".join(elements)
