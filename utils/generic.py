import codecs
import json
import os
import pathlib
import random
import sys
import traceback
from datetime import datetime
from io import BytesIO

import discord

from langs import en, ru
from utils import time, database, data_io, locks


def print_error(text: str):
    return sys.stderr.write(f"{text}\n")


settings_template = {
    'locale': 'en',
    'prefixes': [],
    'use_default': True,
    'anti_spam': {
        'channels': []
    },
    'leveling': {
        'enabled': True,
        'xp_multiplier': 1.0,
        'level_up_message': "[MENTION] is now level **[LEVEL]**! <a:forsendiscosnake:613403121686937601>",
        'ignored_channels': [],
        'announce_channel': 0,
        'rewards': []
    },
    "currency": "€",
    "shop_items": []
}


async def send(text: str or None, channel: discord.TextChannel, *, embed: discord.Embed = None, file: discord.File = None,
               delete_after: float = None, e: bool = False, u: bool or list = False, r: bool or list = False):
    """
    :param text: The text to be sent
    :param channel: The channel to send the message to
    :param embed: The embed to attach to the message, if any
    :param file: The file to attach to the message, if any
    :param delete_after: The amount of seconds to delete the message after
    :param e: Whether to allow mentioning everyone
    :param u: Whether to allow mentioning users
    :param r: Whether to allow mentioning roles
    :return: The message sent
    """
    try:
        return await channel.send(content=text, embed=embed, file=file, delete_after=delete_after,
                                  allowed_mentions=discord.AllowedMentions(everyone=e, users=u, roles=r))
    except discord.Forbidden:
        await channel.send(gls(get_lang(channel.guild), "send_forbidden"))
        if text:
            return await channel.send(content=text, delete_after=delete_after, allowed_mentions=discord.AllowedMentions(everyone=e, users=u, roles=r))


def gls(locale: str, key: str, values: list = None):
    strings = {"ru": ru.data, "en": en.data, "debug": {}}
    use = strings.get(locale, strings["en"])
    out = use.get(key, key)
    if values is not None:
        for value in range(len(values)):
            out = out.replace(f"<val{value + 1}>", str(values[value]))
    return out


def time_ls(locale: str, ts: datetime, *, short: bool = True, show_year: bool = True, show_time: bool = True, show_seconds: bool = True):
    if locale == "ru":
        months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября",
                  "октября", "ноября", "декабря"]
    else:
        months = ["January", "February", "March", "April", "May", "June", "July", "August",
                  "September", "October", "November", "December"]
    d, mo, y = ts.day, ts.month, ts.year
    month = months[mo - 1]
    if short:
        month = month[:3]
    base = f"{d} {month}"
    if show_year:
        base += f" {y:04d}"
    if show_time:
        h, m, s = ts.hour, ts.minute, ts.second
        base += f" {h:02d}:{m:02d}"
        if show_seconds:
            base += f":{s:02d}"
    return base


def random_colour():
    return random.randint(0, 0xffffff)


def get_config() -> dict:
    return json.loads(open("config.json", "r").read())


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


def traceback_maker(err, advance: bool = True, text: str = None, guild=None, author=None):
    _traceback = ''.join(traceback.format_tb(err.__traceback__))
    n = "\n"
    g = f'Guild: {guild.name}\n' if guild is not None else ''
    a = f'User: {author.name}\n' if author is not None else ''
    error = f'{g}{a}```py\n{f"{text}{n}" if text is not None else ""}' \
            f'{_traceback}{type(err).__name__}: {err}\n```'
    return error if advance else f"{type(err).__name__}: {err}"


def reason(who, why=None):
    r = f"[ {who} ]"
    if why is None:
        return f"{r} No reason given..."
    return f"{r} {why}"


async def pretty_results(ctx, filename: str = "Results", result: str = "Here's the results:", loop=None):
    if not loop:
        return await ctx.send("The result was empty...")
    pretty = "\r\n".join([f"[{str(num).zfill(2)}] {data}" for num, data in enumerate(loop, start=1)])
    if len(loop) < 15:
        return await ctx.send(f"{result}```ini\n{pretty}```")
    data = BytesIO(pretty.encode('utf-8'))
    return await send(result, ctx.channel, file=discord.File(data, filename=time.file_ts(filename.title())))


invite = "https://discord.gg/cw7czUx"
config = get_config()
owners = config["owners"]
locked = locks.get_locks()
channel_locks = locked["channel_locks"]
server_locks = locked["server_locks"]
counter_locks = locked["counter_locks"]
love_locks = [424472476106489856, 523275160799805471]
love_exceptions = {424472476106489856: [417390734690484224, 273916273732222979, 689158123352883340],
                   523275160799805471: [302851022790066185, 273916273732222979, 707457134102708284, 667187968145883146]}
infidels = locks.get_infidels()
stage_1 = infidels["1"]
stage_2 = infidels["2"]
stage_3 = infidels["3"]
stage_4 = infidels["4"]
db = database.Database()


def infidel_base(uid: int):
    t1, t2, t3, t4 = uid in stage_1, uid in stage_2, uid in stage_3, uid in stage_4
    t0 = not (t1 or t2 or t3 or t4)
    # tiers = [str(i) for i in range(1, 8)]
    a1, a2 = "add", "remove"
    return t0, t1, t2, t3, t4, a1, a2


def infidel_up(uid: int):
    """ Move someone up the Infidel List """
    t0, t1, t2, t3, t4, a1, a2 = infidel_base(uid)
    a = 1 if t0 else 2 if t1 else 3 if t2 else 4 if t3 else 5 if t4 else -1
    if a != -1:  # if it ain't broken
        for i in range(1, 5):  # Stages 1 - 4
            if a == 5 and i == 4:
                continue  # Don't remove Stage 4 if Stage 4 is reached
            if i == a:
                data_io.change_infidels(i, a1, uid)
            if i != a:
                data_io.change_infidels(i, a2, uid)
    return a


def infidel_down(uid: int):
    """ Move someone down the Infidel List """
    t0, t1, t2, t3, t4, a1, a2 = infidel_base(uid)
    a = -2 if t0 else 0 if t1 else 1 if t2 else 2 if t3 else 3 if t4 else -1
    if a != -1:  # if it ain't broken
        for i in range(1, 5):  # Stages 1 - 4
            if i == a:
                data_io.change_infidels(i, a1, uid)
            if i != a:
                data_io.change_infidels(i, a2, uid)
    return a


def get_lang(guild: discord.Guild = None):
    if guild is None:
        return "en"
    _data = db.fetchrow("SELECT * FROM settings WHERE gid=?", (guild.id,))
    if not _data:
        return "en"
    data = json.loads(_data["data"])
    try:
        return data["locale"]
    except KeyError:
        return "en"


def is_locked(guild: discord.Guild or None, cmd: str):
    """ Returns whether the command is locked in the guild """
    if guild is None:
        return False
    else:
        gid = guild.id
    if str(gid) not in server_locks:
        return False
    return cmd in server_locks[str(gid)]


# def is_bad_locked(author: discord.Member) -> bool:
#     return author.id in stage_4 or author.id in stage_5 or author.id in stage_6 or author.id in stage_7


def is_love_locked(user: discord.Member, author: discord.Member) -> bool:
    try:
        return ((user.id in love_locks) and (author.id not in love_exceptions[user.id])) and author.id != 597373963571691520  # Nuriki
    except KeyError:
        return (user.id in love_locks) and author.id != 597373963571691520


# def is_love_locked2(user: discord.Member, author: discord.Member) -> bool:
#     try:
#         return ((author.id in stage_6 or author.id in stage_7) and (user.id not in love_exceptions[str(author.id)])) and user.id != 597373963571691520
#     except KeyError:
#         return (author.id in stage_6 or author.id in stage_7) and user.id != 597373963571691520


def line_count():
    file_amount, functions, comments, lines, classes = 0, 0, 0, 0, 0

    for dir_path, dir_name, file_names in os.walk("."):
        for name in file_names:

            if not name.endswith(".py"):
                continue
            file_amount += 1

            with codecs.open("./" + str(pathlib.PurePath(dir_path, name)), "r", "utf-8") as files_lines:
                for line in files_lines:
                    line = line.strip()
                    if len(line) == 0:
                        continue
                    if line.startswith("#"):
                        comments += 1
                        continue
                    if line.startswith(("def", "async def")):
                        functions += 1
                    if line.startswith("class"):
                        classes += 1
                    lines += 1

    return file_amount, functions, comments, lines, classes
# https://github.com/iDevision/Life/blob/master/Life/cogs/utilities/utils.py#L44-L77
