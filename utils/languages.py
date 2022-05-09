from __future__ import annotations

import os
from datetime import datetime, time as dt_time

import jstyleson
import pytz
from dateutil.relativedelta import relativedelta
from regaus import languages, time
from regaus.conworlds import Place

from utils import database


def _read_dir(folder: str):
    out = {}
    for file in os.listdir(folder):
        if file.endswith(".json"):
            out[file[:-5]] = jstyleson.loads(open(os.path.join(folder, file), encoding="utf-8").read())
    return out


# Update our language list from Regaus.py, to insert all the strings Suager, CobbleBot and Mizuki will use
_languages = _read_dir("languages/languages")
for _name, _data in _languages.items():
    if _name in languages.languages.keys():
        languages.languages[_name] |= _data
    else:
        languages.languages[_name] = _data

# Insert country names
_countries = _read_dir("languages/countries")
for _name, _data in _countries.items():
    languages.languages[_name] |= _data  # We will assume that if country names are defined, then the language itself is defined already too...

# Update our case list from Regaus.py, just in case there's something here before the proper Regaus.py update...
# We will assume that the overwritten cases are the correct ones, so we can safely ignore the ones stored in the library.
_cases = _read_dir("languages/cases")
for _name, _data in _cases.items():
    languages.cases[_name] = _data
del _languages, _countries, _cases, _name, _data, _read_dir


db = database.Database()


class Language(languages.Language):
    @classmethod
    def get(cls, ctx):
        """ Find the language of the server """
        if hasattr(ctx, "channel"):
            # # Channel:            secret-room-8
            # if ctx.channel.id in [725835449502924901]:  # SR-8
            #     return cls("ka_re")
            # Channels:             rsl-1,              secret-room-11,     secret-room-1,      secret-room-8
            if ctx.channel.id in [787340111963881472, 799714065256808469, 671520521174777869, 725835449502924901]:
                return cls("ka_ne")
        # ex = ctx.bot.db.fetch("SELECT * FROM sqlite_master WHERE type='table' AND name='locales'")
        if ctx.guild is not None:
            data = ctx.bot.db.fetchrow("SELECT * FROM locales WHERE gid=? AND bot=?", (ctx.guild.id, ctx.bot.name))
            if data:
                return cls(data["locale"])
        return cls(ctx.bot.local_config["default_locale"])

    @staticmethod
    def get_timezone(uid: int, time_class: str = "Earth"):
        if time_class == "Earth":
            data = db.fetchrow("SELECT * FROM timezones WHERE uid=?", (uid,))
            if data:
                return pytz.timezone(data["tz"])
        elif time_class == "Kargadia":
            data = db.fetchrow("SELECT location FROM kargadia WHERE uid=?", (uid,))
            if data:
                try:
                    return Place(data["location"]).tz
                except ValueError:  # Place does not exist
                    return time.timezone.utc
        return time.timezone.utc

    def delta_rd(self, delta: time.relativedelta | relativedelta, *, accuracy: int = 3, brief: bool = True, affix: bool = False, case: str = "default") -> str:
        if isinstance(delta, relativedelta):
            now = datetime.now()
        else:
            now = time.datetime.now(time_class=delta.time_class)
        return self.delta_dt(now + delta, source=now, accuracy=accuracy, brief=brief, affix=affix)

    @staticmethod
    def time2(when: time.datetime | time.time | datetime | dt_time, *, seconds: bool = True, tz: bool = False, tz_name: str = None) -> str:
        """ Convert time to localised string """
        base = f"{when.hour:02d}:{when.minute:02d}"
        if seconds:
            base += f":{when.second:02d}"
        if tz:
            if not tz_name:
                if isinstance(when, (time.datetime, time.time)):
                    tzn = when.tz_name()
                else:
                    tzn = when.tzname()
                base += f" {tzn or 'UTC'}"
            else:
                base += f" {tz_name}"
        return base

    def time(self, when: datetime | time.datetime, *, short: int = 0, dow: bool = False, seconds: bool = True, tz: bool = False, at: bool = False,
             case_override: str = None, uid: int = None) -> str:
        """ Convert datetime to localised string

        If a user id is provided, it will try to convert the timezone to the user's local timezone, else leave it as is"""
        tz_name = None
        if uid:
            if isinstance(when, datetime):
                when = time.datetime.from_datetime(when)
            tz = self.get_timezone(uid, when.time_class.__name__)
            when = when.as_timezone(tz)
            if tz.__class__.__module__.startswith("pytz"):
                tz_name = tz.tzname(when.to_datetime().replace(tzinfo=None))
        case = case_override if case_override is not None else self.string("time_at_case") if at else "default"
        _date = self.date(when, short=short, dow=dow, year=True, case=case)
        _time = self.time2(when, seconds=seconds, tz=tz, tz_name=tz_name)
        if at:
            # This only changes to "date at time" instead of just "date, time"... it does not add "on"
            return self.string("time_at", date=_date, time=_time)
        else:
            return f"{_date}, {_time}"


class FakeContext:
    """ Build a fake Context instead of commands.Context to pass on to Language.get() """
    def __init__(self, guild, bot):
        self.guild = guild
        self.bot = bot
