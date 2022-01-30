from __future__ import annotations

import os
from datetime import datetime

import jstyleson
from dateutil.relativedelta import relativedelta
from regaus import languages, time


# Update our language list from Regaus.py, to insert all the strings Suager, CobbleBot and Mizuki will use
_languages = {}
for file in os.listdir("languages/languages"):
    if file.endswith(".json"):
        _languages[file[:-5]] = jstyleson.loads(open(os.path.join("languages/languages", file), encoding="utf-8").read())
for _name, _data in _languages.items():
    if _name in languages.languages.keys():
        languages.languages[_name] |= _data
    else:
        languages.languages[_name] = _data

# Update our case list from Regaus.py, just in case there's something here before the proper Regaus.py update...
# We will assume that the overwritten cases are the correct ones, so we can safely ignore the ones stored in the library.
_cases = {}
for file in os.listdir("languages/cases"):
    if file.endswith(".json"):
        _cases[file[:-5]] = jstyleson.loads(open(os.path.join("languages/cases", file), encoding="utf-8").read())
for _name, _data in _cases.items():
    languages.cases[_name] = _data
    # if _name not in languages.cases.keys():
    #     languages.cases[_name] = _data
    # else:
    #     _original = languages.cases[_name]
    #     # Pattern[number][case]
    #     for _pattern, _v in _data.items():
    #         if _pattern in _original:
    #             _op = _original[_pattern]
    #             for _num, _cd in _v.items():
    #                 if _num in _op:
    #                     _op[_num] |= _cd
    #                 else:
    #                     _op[_num] = _cd
    #         else:
    #             _original[_pattern] = _v
del _languages, _cases, _name, _data  # , _original, _pattern, _v, _op, _num, _cd


class Language(languages.Language):
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
