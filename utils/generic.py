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
from utils import time, database, data_io


def print_error(text: str):
    return sys.stderr.write(f"{text}\n")


settings_template = {
    'locale': 'en',
    'prefixes': [],
    'use_default': True,
    'anti_spam': {
        'channels': [0, 1, 2]
    },
    'leveling': {
        'enabled': True,
        'xp_multiplier': 1.0,
        'level_up_message': "[MENTION] is now level **[LEVEL]**! <a:forsendiscosnake:613403121686937601>",
        'ignored_channels': [],
        'announce_channel': 0,
        'rewards': [
            {'level': 5001, 'role': 0},
            {'level': 5002, 'role': 0}
        ]
    },
    # "mute_role": 0,
    # "warns_to_mute": 3,
    "currency": "€",
    "shop_items": [
        {"cost": 1, "role": 0},
        {"cost": 2, "role": 0}
    ]
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
    """
    :param locale: language to use
    :param ts: timestamp to use
    :param short: Whether to use full month name or the first 3 letters
    :param show_year: whether to show year in the timestamp
    :param show_time: whether to show time (hh:mm)
    :param show_seconds: whether to show seconds
    :return: localised string for timestamp
    """
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


def get_locks() -> dict:
    try:
        return json.loads(open("data/locks.json", "r").read())
    except FileNotFoundError:
        return {"love_locks": [], "love_locks_s6": [], "love_exceptions": {}, "bad_locks": [], "channel_locks": [], "server_locks": {},
                "counter_locks": [], "heretics": {"1": [], "2": [], "3": []}}


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
locks = get_locks()
love_locks = locks["love_locks"]
love_locks2 = locks["love_locks_s6"]
love_exceptions = locks["love_exceptions"]
bad_locks = locks["bad_locks"]
channel_locks = locks["channel_locks"]
server_locks = locks["server_locks"]
counter_locks = locks["counter_locks"]
heretics = locks["heretics"]
tier_1 = heretics["1"]
tier_2 = heretics["2"]
tier_3 = heretics["3"]
db = database.Database()


def heresy(uid: int):
    t1 = uid in tier_1
    t2 = uid in tier_2
    t3 = uid in tier_3
    t0 = not (t1 or t2 or t3)
    val1 = "heretics"
    tier = ["1", "2", "3"]
    a1, a2 = "add", "remove"
    ret = 0
    if t0:
        data_io.change_values(val1, tier[0], a1, uid)
        data_io.change_values(val1, tier[1], a2, uid)
        data_io.change_values(val1, tier[2], a2, uid)
        ret = 1
    if t1:
        data_io.change_values(val1, tier[0], a2, uid)
        data_io.change_values(val1, tier[1], a1, uid)
        data_io.change_values(val1, tier[2], a2, uid)
        ret = 2
    if t2:
        data_io.change_values(val1, tier[0], a2, uid)
        data_io.change_values(val1, tier[1], a2, uid)
        data_io.change_values(val1, tier[2], a1, uid)
        ret = 3
    if t3:
        data_io.change_values(val1, tier[0], a2, uid)
        data_io.change_values(val1, tier[1], a2, uid)
        ret = 4
    return ret


def heresy_down(uid: int):
    t1 = uid in tier_1
    t2 = uid in tier_2
    t3 = uid in tier_3
    val1 = "heretics"
    tier = ["1", "2", "3"]
    a1, a2 = "add", "remove"
    if t1:
        data_io.change_values(val1, tier[0], a2, uid)
        data_io.change_values(val1, tier[1], a2, uid)
        data_io.change_values(val1, tier[2], a2, uid)
        return 0
    if t2:
        data_io.change_values(val1, tier[0], a1, uid)
        data_io.change_values(val1, tier[1], a2, uid)
        data_io.change_values(val1, tier[2], a2, uid)
        return 1
    if t3:
        data_io.change_values(val1, tier[0], a2, uid)
        data_io.change_values(val1, tier[1], a1, uid)
        data_io.change_values(val1, tier[2], a2, uid)
        return 2
    return -1


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


def is_love_locked(user: discord.Member, author: discord.Member) -> bool:
    try:
        return (user.id in love_locks and (author.id not in love_exceptions[str(user.id)])) and author.id != 597373963571691520  # Nuriki
    except KeyError:
        return user.id in love_locks and author.id != 597373963571691520


def is_love_locked2(user: discord.Member, author: discord.Member) -> bool:
    try:
        return (author.id in love_locks2 and (user.id not in love_exceptions[str(author.id)])) and user.id != 597373963571691520  # Nuriki
    except KeyError:
        return author.id in love_locks2 and user.id != 597373963571691520


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
