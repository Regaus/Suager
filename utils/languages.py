from __future__ import annotations

import os
from datetime import datetime, time as dt_time

import jstyleson
import pytz
from dateutil.relativedelta import relativedelta
from regaus import languages, time
from regaus.conworlds import Place

from utils import database, emotes


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


db = database.Database("database.db")


class Language(languages.Language):
    @classmethod
    def get(cls, ctx, personal: bool = False):
        """ Find the language of the server """
        is_guild = hasattr(ctx, "guild") and ctx.guild is not None  # Whether we are in a guild or not
        if (personal and hasattr(ctx, "author")) or not is_guild:
            # Let users set their personal language (this behaviour is disabled by default, the command has to explicitly enable the personal languages)
            # The personal language is, however, always used in the DMs.
            data = ctx.bot.db.fetchrow("SELECT * FROM locales WHERE id=? AND bot=? AND type='user'", (ctx.author.id, ctx.bot.name))
            if data:
                return cls(data["locale"])
        if hasattr(ctx, "channel"):
            data = ctx.bot.db.fetchrow("SELECT * FROM locales WHERE id=? AND bot=? AND type='channel'", (ctx.channel.id, ctx.bot.name))
            if data:
                return cls(data["locale"])
            # # Channel:            secret-room-8,      secret-room-15
            # if ctx.channel.id in [725835449502924901, 969720792457822219]:
            #     return cls("ne_rc")
            # # Channels:             rsl-1,              secret-room-11,     secret-room-1
            # elif ctx.channel.id in [787340111963881472, 799714065256808469, 671520521174777869]:
            #     return cls("ne_rn")
        # ex = ctx.bot.db.fetch("SELECT * FROM sqlite_master WHERE type='table' AND name='locales'")
        if is_guild:
            data = ctx.bot.db.fetchrow("SELECT * FROM locales WHERE id=? AND bot=? AND type='guild'", (ctx.guild.id, ctx.bot.name))
            if data:
                return cls(data["locale"])
        return cls(ctx.bot.local_config["default_locale"])

    @staticmethod
    def get_timezone(uid: int, time_class: str = "Earth"):
        if time_class == "Earth":
            data = db.fetchrow("SELECT * FROM timezones WHERE uid=?", (uid,))
            if data:
                return pytz.timezone(data["tz"])
        elif time_class in ("Kargadia", "Arnattia", "Larihalia"):
            data = db.fetchrow("SELECT location FROM kargadia WHERE uid=?", (uid,))
            if data:
                try:
                    return Place(data["location"]).tz
                except (ValueError, AttributeError):  # Place does not exist or is not specified (null -> AttError)
                    return time.KargadianTimezone(time.timedelta(), "Virsetgar", "VSG")  # Since they have Virsetgar instead of UTC
            return time.KargadianTimezone(time.timedelta(), "Virsetgar", "VSG")
        return time.timezone.utc

    def number(self, value: int | float, *, precision: int = 2, fill: int = 0, percentage: bool = False, commas: bool = True, positives: bool = False, zws_end: bool = False) -> str:
        # Surround the full stops and spaces by "zero width non-joiners" to prevent Android from treating the number outputs like links (Why does this even have to be a problem?)
        return super().number(value, precision=precision, fill=fill, percentage=percentage, commas=commas, positives=positives)\
            .replace(".", "\u200c.\u200c").replace(" ", "\u200c \u200c") + ("\u200c" if zws_end else "")

    def string(self, string: str, *values, **kwargs) -> str:
        try:
            return super().string(string, *values, **kwargs, emotes=emotes)
        except AttributeError:
            return super().string(string, *values, **kwargs)  # If the emote is not available, just unload them

    def delta_rd(self, delta: time.relativedelta | relativedelta, *, accuracy: int = 3, brief: bool = True, affix: bool = False, case: str = "default") -> str:
        if isinstance(delta, relativedelta):
            now = datetime.now()
        else:
            now = time.datetime.now(time_class=delta.time_class)
        return self.delta_dt(now + delta, source=now, accuracy=accuracy, brief=brief, affix=affix, case=case)

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
            # if tz.__class__.__module__.startswith("pytz"):
            if isinstance(tz, pytz.tzinfo.DstTzInfo):
                tz_name = when.tzinfo._tzname  # type: ignore
                # Try to get the name of the timezone at the given time. For ambiguous cases,
                # assume non-DST tz name variant (except for some reason it sometimes uses the other one anyways).
                # tz_name = tz.tzname(when.as_timezone(time.timezone.utc).to_datetime().replace(tzinfo=None), is_dst=bool(when.tzinfo._dst))  # type: ignore
        case = case_override if case_override is not None else self.string("time_at_case") if at else "default"
        _date = self.date(when, short=short, dow=dow, year=True, case=case)
        _time = self.time2(when, seconds=seconds, tz=tz, tz_name=tz_name)
        if at:
            # This only changes to "date at time" instead of just "date, time"... it does not add "on"
            return self.string("time_at", date=_date, time=_time)
        else:
            return f"{_date}, {_time}"
