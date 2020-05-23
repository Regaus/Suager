import codecs
import json
import os
import pathlib
import random
import traceback
from collections import namedtuple
from datetime import datetime
from io import BytesIO
from langs import en, ru

import discord

from utils import time, database, data_io

prefix_template = {'prefixes': [], 'default': True}
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
    "mute_role": 0,
    # "warns_to_mute": 3,
    "currency": "€",
    "shop_items": [
        {"cost": 1, "role": 0},
        {"cost": 2, "role": 0}
    ]
}
# levels_template = deepcopy(settings_template)
# levels_template["leveling"]["enabled"] = False


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
    strings = {
        "ru": ru.data, "en": en.data, "debug": {}
    }
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


def get(file):
    try:
        with open(file, encoding='utf8') as data:
            # return json.load(data, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
            # return json.load(data, object_hook=lambda d: namedtuple('JSONData', d.keys())(*d.values()))
            return json.load(data, object_hook=lambda d: namedtuple('JSONData', d.keys())())
    except AttributeError:
        raise AttributeError("Unknown argument")
    except FileNotFoundError:
        raise FileNotFoundError("JSON file wasn't found")


def random_colour():
    return random.randint(0, 0xffffff)


def get_config():
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


def string_make(val, sa: int = 0, negative: bool = False, big: bool = False):
    """
    :param val: The value
    :param sa: The amount of 000's
    :param negative: Whether the value is negative or positive
    :param big: Whether to format like "mil" or "million"
    :return: The value's string
    """
    minus = "-" if negative else ""
    # res = ['', "K", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "O", "N", "D"]
    res = ['', 'K', 'mil', 'bil', 'tri', 'qua', 'qui', 'sext', 'sept', 'oct', 'non', 'dec']
    yes = ['', 'thousand', 'million', 'billion', 'trillion', 'quadrillion', 'quintillion', 'sextillion', 'septillion',
           'octillion', 'nonillion', 'decillion']
    if sa >= len(res):
        return f"{minus}{round_value(val):,}e{sa * 3}"
    return f"{minus}{round_value(val):,} {res[sa]}" if not big else f"{minus}{round_value(val):,} {yes[sa]}"


def value_string(val, sa: int = 0, k: bool = False, negative: bool = False, big: bool = False):
    """
    :param val: the value
    :param sa: The amount of times it was already divided by 1000
    :param k: Whether to show thousands, or to only start showing string for 1 million+
    :param negative: Whether the value is negative or not
    :param big: Whether to format like "mil" or "million"
    :return: The value's string
    """
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
            return value_string(val / 1000, sa + 1, k, negative, big)
        return string_make(val, sa, negative, big)
    except OverflowError:
        return "An overflow error's worth"
    except RecursionError:
        return "A recursion error's worth"
    except Exception as e:
        return f"An error - {e}"


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


# def action(what, *, who=None, why=None, many: int = 0, emote=None):
#     if who is None:
#         s = 's' if many else ''
#         output = f"**{what}** the id{s}/user{s}"
#     else:
#         output = f"**{what}** {who}"
#     if why is not None:
#         output += f" for {why}"
#     if emote is not None:
#         output += f" {emote}"
#     return f"<:allow:610828713424191498> Successfully {output}"


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


async def you_little_shit(senko_lair):
    ba = [senko_lair.get_member(94762492923748352), senko_lair.get_member(246652610747039744)]
    for little_shit in ba:
        name = str(little_shit.display_name).lower()
        if 'arch' in name:
            await little_shit.edit(nick="rule 4a", reason="Rule 4a")
        if 'python' in name:
            bad = ['bad', 'gae', 'gay', 'stupid', 'dump', 'stoopid']
            for word in bad:
                if word in name:
                    await little_shit.edit(nick="rule 14b", reason="Rule 14b")


# version = get("config.json").version
# invite = "https://discord.gg/cw7czUx"
invite = "https://discord.gg/senko/"
config = get_config()
owners = config["owners"]
love_locks = config["love_locks"]
love_exceptions = config["love_exceptions"]
bad_locks = config["bad_locks"]
channel_locks = config["channel_locks"]
server_locks = config["server_locks"]
heretics = config["heretics"]
tier_1 = heretics["1"]
tier_2 = heretics["2"]
tier_3 = heretics["3"]
# tier_4 = heretics["4"]
db = database.Database()


def heresy(uid: int):
    t1 = uid in tier_1
    t2 = uid in tier_2
    t3 = uid in tier_3
    t0 = not (t1 and t2 and t3)
    # data_io.change_values("heretics", str(tier), action, uid)
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
# prefixes = 'data/prefixes'


def is_love_locked(user: discord.Member, author: discord.Member) -> bool:
    return (user.id in love_locks and author.id not in love_exceptions[str(user.id)]) or author.id == 597373963571691520  # Nuriki


def line_count():
    docstring = False
    file_amount, functions, comments, lines, classes, docs = 0, 0, 0, 0, 0, 0

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
                    elif line.startswith('"""'):
                        docstring = not docstring
                    if docstring is True:
                        docs += 1
                    if line.endswith('"""'):
                        docstring = not docstring
                    if line.startswith("#"):
                        comments += 1
                        continue
                    if line.startswith(("def", "async def")):
                        functions += 1
                    if line.startswith("class"):
                        classes += 1
                    lines += 1

    return file_amount, functions, comments, lines, classes, docs
# https://github.com/iDevision/Life/blob/master/Life/cogs/utilities/utils.py#L44-L77
