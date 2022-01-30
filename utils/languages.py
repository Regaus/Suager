from __future__ import annotations

import os
from datetime import datetime

import jstyleson
from dateutil.relativedelta import relativedelta
from regaus import languages, time


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


class Language(languages.Language):
    @classmethod
    def get(cls, ctx):
        """ Find the language of the server """
        if hasattr(ctx, "channel"):
            if ctx.channel.id in [725835449502924901]:  # SR-8
                return cls("ka_re")
            elif ctx.channel.id in [787340111963881472, 799714065256808469]:  # RSL-1 channel and SR-11
                return cls("ka_ne")
        # ex = ctx.bot.db.fetch("SELECT * FROM sqlite_master WHERE type='table' AND name='locales'")
        if ctx.guild is not None:
            data = ctx.bot.db.fetchrow("SELECT * FROM locales WHERE gid=? AND bot=?", (ctx.guild.id, ctx.bot.name))
            if data:
                return cls(data["locale"])
        return cls(ctx.bot.local_config["default_locale"])

    def delta_rd(self, delta: time.relativedelta | relativedelta, *, accuracy: int = 3, brief: bool = True, affix: bool = False, case: str = "default") -> str:
        if isinstance(delta, relativedelta):
            now = datetime.now()
        else:
            now = time.datetime.now(time_class=delta.time_class)
        return self.delta_dt(now + delta, source=now, accuracy=accuracy, brief=brief, affix=affix)


class FakeContext:
    def __init__(self, guild, bot):
        self.guild = guild
        self.bot = bot
