from __future__ import annotations

import os
from datetime import datetime

import jstyleson
from dateutil.relativedelta import relativedelta
from regaus import languages, time


_languages = {}
for file in os.listdir("languages"):
    if file.endswith(".json"):
        _languages[file[:-5]] = jstyleson.loads(open(os.path.join("languages", file), encoding="utf-8").read())
# languages.languages |= _languages
for _name, _data in _languages.items():
    if _name in languages.languages.keys():
        languages.languages[_name] |= _data
    else:
        languages.languages[_name] = _data


class Language(languages.Language):
    def delta_rd(self, delta: time.relativedelta | relativedelta, *, accuracy: int = 3, brief: bool = True, affix: bool = False) -> str:
        if isinstance(delta, relativedelta):
            now = datetime.now()
        else:
            now = time.datetime.now(time_class=delta.time_class)
        return self.delta_dt(now + delta, source=now, accuracy=accuracy, brief=brief, affix=affix)


class FakeContext:
    def __init__(self, guild, bot):
        self.guild = guild
        self.bot = bot
