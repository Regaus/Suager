import json
import os
from datetime import date, datetime, timedelta, timezone, time as dt_time
from typing import Union

from dateutil.relativedelta import relativedelta

from utils import emotes, time

languages, countries, time_strings, weather = {}, {}, {}, {}
for folder in os.listdir("languages"):
    # if file.endswith(".json"):
    #     languages[file[:-5]] = json.loads(open(os.path.join("languages", file), encoding="utf-8").read())
    if folder != "__pychache__":
        try:  # Load main set of strings
            languages[folder] = json.loads(open(os.path.join("languages", folder, "strings.json"), encoding="utf-8").read())
        except FileNotFoundError:
            pass
        try:  # Load country names list
            countries[folder] = json.loads(open(os.path.join("languages", folder, "countries.json"), encoding="utf-8").read())
        except FileNotFoundError:
            pass
        try:  # Load time-related strings
            time_strings[folder] = json.loads(open(os.path.join("languages", folder, "time.json"), encoding="utf-8").read())
        except FileNotFoundError:
            pass
        try:  # Load weather-related strings
            weather[folder] = json.loads(open(os.path.join("languages", folder, "weather.json"), encoding="utf-8").read())
        except FileNotFoundError:
            pass


def splits(value: str, step: int = 4, joiner: str = " ") -> str:
    _split = value.split(".", 1)
    _float = "" if len(_split) == 1 else f".{_split[1]}"
    reverse = _split[0][::-1]
    return (joiner.join([reverse[i:i+step] for i in range(0, len(reverse), step)]))[::-1] + _float


def join(seq, joiner: str = ', ', final: str = 'and') -> str:
    size = len(seq)
    return '' if size == 0 else seq[0] if size == 1 else f"{seq[0]} {final} {seq[1]}" if size == 2 else f"{joiner.join(seq[:-1])} {final} {seq[-1]}"


class Language:
    """ Provides language support to my bots """
    def __init__(self, language: str):
        self.language = language

    @classmethod
    def get(cls, ctx):
        """ Find the language of the server """
        if hasattr(ctx, "channel"):
            if ctx.channel.id in [725835449502924901]:  # SR-8
                return cls("tebarian")
            elif ctx.channel.id in [787340111963881472, 799714065256808469]:  # RSL-1 channel and SR-11
                return cls("kargadian_west")
        # ex = ctx.bot.db.fetch("SELECT * FROM sqlite_master WHERE type='table' AND name='locales'")
        if ctx.guild is not None:
            data = ctx.bot.db.fetchrow("SELECT * FROM locales WHERE gid=? AND bot=?", (ctx.guild.id, ctx.bot.name))
            if data:
                return cls(data["locale"])
        return cls(ctx.bot.local_config["default_locale"])

    def bytes(self, value: int, precision: int = 2) -> str:
        """ Turn byte value into string """
        if self.language in ["kargadian_west", "tebarian"]:
            value //= 2
            names = ["V", "MV", "UV", "DV", "TV", "CV", "PV", "SV", "EV", "OV", "ZV"]
            step = 65536
        elif self.language == "russian":
            names = ["Б", "КБ", "МБ", "ГБ", "ТБ", "ПБ", "ЭБ", "ЗБ", "ЙБ"]
            step = 1024
        else:
            names = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
            step = 1024
        range_val = len(names)
        for i in range(range_val):
            req = step ** (i + 1)
            if value < req or i == range_val - 1:
                val = value / (step ** i)
                # number = gns(int(val), locale, 0, True) if precision == 0 else gfs(val, locale, precision, False)
                number = self.number(val, precision=precision, commas=val > 1024)
                return f"{number} {names[i]}"

    def number(self, value: Union[int, float], *, precision: int = 2, fill: int = 0, percentage: bool = False, commas: bool = True, positives: bool = False) -> str:
        """ Turn a number into a string """
        c = "," if commas else ""
        p = "+" if positives and value != 0 else ""
        try:
            if (type(value) == int or precision == 0) and not percentage:
                value = int(value)  # Make sure the value is an integer, in case it's a float with precision zero
                output = f"{value:{p}0{fill}{c}d}"
            else:
                f = "%" if percentage else "f"
                output = f"{value:{p}0{fill}{c}.{precision}{f}}"
            if self.language == "russian":
                output = output.replace(",", " ").replace(".", ",")
            return output
        except OverflowError:
            return self.string("generic_infinity")

    def string(self, string: str, *values, **kwargs) -> str:
        """ Get translated string """
        output = str((languages.get(self.language, languages["english"])).get(string, languages["english"].get(string, string)))
        try:
            return output.format(*values, **kwargs, emotes=emotes)
        except IndexError:
            for i, value in enumerate(values):
                output = output.replace(f"\x7b{i}\x7d", str(value))  # Try to fill in the values we do have
            return output
            # return f"Formatting failed:\n{output}\nFormat values:\n{', '.join([str(value) for value in values])}"

    def data(self, key: str):
        """ Get list/dict language entry """
        return (languages.get(self.language, languages["english"])).get(key, languages["english"].get(key))

    def weather_string(self, string: str, *values, **kwargs) -> str:
        """ Get translated weather string """
        output = str((weather.get(self.language, weather["english"])).get(string, weather["english"].get(string, string)))
        try:
            return output.format(*values, **kwargs, emotes=emotes)
        except IndexError:
            for i, value in enumerate(values):
                output = output.replace(f"\x7b{i}\x7d", str(value))  # Try to fill in the values we do have
            return output

    def weather_data(self, key: str):
        """ Get list/dict language entry """
        return (weather.get(self.language, weather["english"])).get(key, weather["english"].get(key))

    def time_string(self, string: str, *values, **kwargs) -> str:
        """ Get translated time string (languages/<language>/time.json) """
        output = str((time_strings.get(self.language, time_strings["english"])).get(string, time_strings["english"].get(string, string)))
        try:
            return output.format(*values, **kwargs, emotes=emotes)
        except IndexError:
            for i, value in enumerate(values):
                output = output.replace(f"\x7b{i}\x7d", str(value))  # Try to fill in the values we do have
            return output

    def time_data(self, key: str, default: str, time_class: str):
        """ Get time translation data (languages/<language>/time.json) """
        return (time_strings.get(self.language, time_strings[default])).get(key, time_strings[default].get(key)).get(time_class)

    def join(self, seq):
        """ x, y and z """
        return join(seq, final=self.string2("generic_and"))

    # Temporary aliases to get this to work with weather while I work on actual time support
    string2 = string
    data2 = data

    def yes(self, condition: bool) -> str:
        """ Yes or no """
        return self.string("generic_yes" if condition else "generic_no")

    def plural(self, value: Union[int, float], string: str, *, precision: int = 2, commas: bool = True) -> str:
        """ Plural form of words """
        data = self.data2(string)
        single = ["rsl-1f", "rsl-1g"]
        if self.language in single:
            name = data[0]
        elif self.language == "russian":
            name_1, name_2, name_pl = data
            many, ten, hundred = self.data2("_pl")
            value_hundred = value % hundred
            value_ten = value_hundred % ten
            name = name_pl if ten <= value_hundred <= ten * 2 or (value_ten >= many or value_ten == 0) else name_2 if value_ten != 1 else name_1
        else:
            name_1, name_2 = data
            cond = (value % 100) == 1 if self.language == "rsl-1e" else value == 1
            name = name_1 if cond else name_2
        output = self.number(value, precision=precision, commas=commas)
        reverse = []
        return f"{name} {output}" if self.language in reverse else f"{output} {name}"

    def delta_dt(self, dt: datetime, *, source: datetime = None, accuracy: int = 3, brief: bool = False, affix: bool = True) -> str:
        """ Convert timedelta into human string """
        now = source or time.now(None)
        then = dt.astimezone(timezone.utc)
        if then > now:
            delta = relativedelta(then, now)
            pre, suf = (self.string2("time_in_p"), self.string2("time_in_s")) if affix else ("", "")
        else:
            delta = relativedelta(now, then)
            pre, suf = (self.string2("time_ago_p"), self.string2("time_ago_s")) if affix else ("", "")
        attrs = [('years', 'time_year', 'time_y'), ('months', 'time_month', 'time_mo'), ('days', 'time_day', 'time_d'), ('hours', 'time_hour', 'time_h'),
                 ('minutes', 'time_minute', 'time_m'), ('seconds', 'time_second', 'time_s')]
        output = []
        no_weeks = []
        for attr in attrs:
            element = getattr(delta, attr[0])
            if not element:
                continue
            if attr[0] == "days" and self.language not in no_weeks:
                weeks = delta.weeks
                if weeks:
                    element -= weeks * 7
                    output.append(f"{self.number(weeks)}{self.string2('time_w')}" if brief else self.plural(weeks, 'time_week'))
                    # output.append(f"{gns(weeks, locale)}{gls('time_w', locale)}" if brief else plural(weeks, 'time_week', locale))
            if element <= 0:
                continue
            else:
                output.append(f"{self.number(element)}{self.string2(attr[2])}" if brief else f"{self.plural(element, attr[1])}")
            # if brief:
            #     output.append(f"{gns(element, locale)}{gls(attr[2], locale)}")
            # else:
            #     output.append(plural(element, attr[1], locale))
        output = output[:accuracy]
        if len(output) == 0:
            return self.string("time_now")
        else:
            if brief:
                return pre + ' '.join(output) + suf
            else:
                return pre + self.join(output) + suf

    def delta_int(self, seconds: Union[int, float], *, accuracy: int = 3, brief: bool = True, affix: bool = False) -> str:
        now = time.now(None)
        return self.delta_dt(now + timedelta(seconds=seconds), source=now, accuracy=accuracy, brief=brief, affix=affix)

    def delta_ts(self, timestamp: Union[int, float], *, accuracy: int = 3, brief: bool = True, affix: bool = False) -> str:
        return self.delta_dt(time.from_ts(timestamp, None), accuracy=accuracy, brief=brief, affix=affix)

    def delta_rd(self, delta: relativedelta, *, accuracy: int = 3, brief: bool = True, affix: bool = False) -> str:
        now = time.now(None)
        return self.delta_dt(now + delta, source=now, accuracy=accuracy, brief=brief, affix=affix)

    def date(self, when: Union[datetime, date], *, short: int = 0, dow: bool = False, year: bool = True) -> str:
        """ Convert the date to string

        Short: 0 = Full month name, 1 = Short month name, 2 = dd/mm/yyyy format"""
        no_weeks = []
        no_months = []
        # day, month = when.day, when.month
        # if day == 4 and month == 7:
        #     day, month = 34, 6
        if dow and self.language not in no_weeks:
            weekdays = self.data("time_weekdays")
            if self.language in ["kargadian_west", "tebarian", "kargadian_kaltarena"]:  # Also Kaltarena Kargadian
                wd = when.weekday()
                if when.hour < 6:
                    wd -= 1
                suffix = ["te", "re", "se", "ve"] if self.language == "kargadian_kaltarena" else ["tea", "rea", "sea", "vea"]
                weekday = weekdays[wd] + suffix[when.hour // 6]
            else:
                weekday = weekdays[when.weekday()]
            weekday = f"{weekday}, "
        else:
            weekday = ""
        _year = str(when.year)
        if short == 2 or self.language in no_months:
            return f"{weekday}{when.day}/{when.month}{'/' + _year if year else ''}"
        else:
            month_names_l = self.data("time_month_names")
            month_name = month_names_l[when.month % 12]
            month = month_name if short == 0 else month_name[:3]
            return f"{weekday}{when.day} {month}{' ' + _year if year else ''}"

    @staticmethod
    def time2(when: Union[datetime, dt_time], *, seconds: bool = True, tz: bool = False) -> str:
        """ Convert time to string """
        base = f"{when.hour:02d}:{when.minute:02d}"
        if seconds:
            base += f":{when.second:02d}"
        if tz:
            base += f" {when.tzname()}"
        return base

    def time(self, when: datetime = None, *, short: int = 0, dow: bool = False, seconds: bool = True, tz: bool = False) -> str:
        return f"{self.date(when, short=short, dow=dow, year=True)}, {self.time2(when, seconds=seconds, tz=tz)}"

    def time_weekday(self, obj, short: bool = True):
        """ Return the weekday name """
        # Using the object itself rather than its values will allow to more accurately represent weekdays for RSL-1
        day = obj.weekday
        time_class = obj.time_class()
        default = time_class.default_language
        value = "weekdays_short" if short else "weekdays"
        # _data = (time_strings.get(self.language, time_strings[default])).get(value, time_strings[default].get(value))
        # data = _data.get(time_class.__class__.__name__)
        name = self.time_data(value, default, obj.time_class.__name__)[day]
        if not short:
            if self.language in ["kargadian_west", "tebarian"] and not short:
                part = obj.hour // 6
                parts = ["tea", "rea", "sea", "vea"]
                name += parts[part]
            if self.language == "usturian":
                name = "Sharuad " + name
        return name or "None"

    def time_month(self, obj, short: bool = True):
        """ Return the month name """
        month = obj.month
        time_class = obj.time_class()
        default = time_class.default_language
        value = "months_short" if short else "months"
        # _data = (time_strings.get(self.language, time_strings[default])).get(value, time_strings[default].get(value))
        # data = _data.get(time_class.__class__.__name__)
        name = self.time_data(value, default, obj.time_class.__name__)[month - 1]
        return name or "None"

    def __str__(self):
        return self.language

    def __repr__(self):
        return f"<{self.__class__.__name__} code={self.language!r}>"


class FakeContext:
    def __init__(self, guild, bot):
        self.guild = guild
        self.bot = bot
