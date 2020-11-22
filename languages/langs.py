import json
import os
from datetime import datetime, timedelta, timezone

from dateutil.relativedelta import relativedelta

from core.utils import emotes, time

languages = {}
for file in os.listdir("languages"):
    if file.endswith(".json"):
        languages[file[:-5]] = json.loads(open(os.path.join("languages", file), encoding="utf-8").read())


def gbs(value: int, locale: str = "en_gb", precision: int = 2) -> str:  # Get Byte String
    """ Gets Byte value name (for dlram) """
    names = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
    step = 1024
    if locale in ["rsl-1_kg", "rsl-1_ku"]:
        value //= 2
        names = ["V", "KV", "UV", "DV", "TV", "CV", "PV", "SV", "EV", "OV"]
        step = 4096
    if locale == "ru_ru":
        names = ["Б", "КБ", "МБ", "ГБ", "ТБ", "ПБ", "ЭБ", "ЗБ", "ЙБ"]
    range_val = len(names)
    for i in range(range_val):
        req = step ** (i + 1)
        if value < req or i == range_val - 1:
            val = value / (step ** i)
            number = gns(int(val), locale, 0, True) if precision == 0 else gfs(val, locale, precision, False)
            return f"{number} {names[i]}"


def gns(value: int or float, locale: str = "en_gb", fill: int = 0, commas: bool = True) -> str:  # Get number string
    """ Get a string from an integer """
    try:
        value = int(value)
    except OverflowError:
        return "Infinity"
    if locale == "ru_ru":
        return f"{value:0{fill}{',' if commas else ''}d}".replace(",", " ")
    return f"{value:0{fill}{',' if commas else ''}d}"


def gfs(value: float, locale: str = "en_gb", pre: int = 2, per: bool = False) -> str:  # Get float string | pre = precision, per = percentage
    """ Get a string from a float """
    if locale == "ru_ru":
        return (f"{value:,.{pre}f}" if not per else f"{value:,.{pre}%}").replace(",", " ").replace(".", ",")
    return f"{value:,.{pre}f}" if not per else f"{value:,.{pre}%}"


def gl(ctx):
    if hasattr(ctx, "channel") and ctx.channel.id == 725835449502924901:
        return "rsl-1_ku"
    ex = ctx.bot.db.fetch("SELECT * FROM sqlite_master WHERE type='table' AND name='locales'")
    if ex and ctx.guild is not None:
        data = ctx.bot.db.fetchrow("SELECT * FROM locales WHERE gid=?", (ctx.guild.id,))
        if data:
            return data["locale"]
    return ctx.bot.local_config["default_locale"]


def gls(string: str, locale: str = "en_gb", *values, **kw_values) -> str:
    """ Get language string """
    output = str((languages.get(locale, languages["en_gb"])).get(string, languages["en_gb"].get(string, f"String not found: {string}")))
    try:
        return output.format(*values, **kw_values, emotes=emotes)
    except IndexError:
        return f"Formatting failed:\n{output}\nFormat values:\n{', '.join([str(value) for value in values])}"


def get_data(key: str, locale: str = "en_gb") -> list:  # Get multiple
    return (languages.get(locale, languages["en_gb"])).get(key, languages["en_gb"].get(key))


def yes(condition: bool, locale: str = "en_gb") -> str:
    return gls("generic_yes", locale) if condition else gls("generic_no", locale)


def plural(v: int, what: str, locale: str = "en_gb") -> str:
    """ Get plural form of words """
    if locale in ["rsl-1_kg", "ru_ru"]:
        name_1, name_2, name_pl = get_data(what, locale)
        pl = get_data("_pl", locale)
        p1, p2, p3 = pl
        v2 = v % int(p3)
        v3 = v2 % int(p2)
        name = name_pl if int(p2) <= v2 <= int(p2) * 2 or v3 >= int(p1) else name_2 if v3 != 1 else name_1
    else:
        name_1, name_2 = get_data(what, locale)
        cond = (v % 256) == 1 if locale == "rsl-1_ku" else v == 1
        name = name_1 if cond else name_2
    reverse = []
    return f"{name} {gns(v, locale)}" if locale in reverse else f"{gns(v, locale)} {name}"


def join(seq, joiner: str = ', ', final: str = 'and'):
    size = len(seq)
    return '' if size == 0 else seq[0] if size == 1 else f"{seq[0]} {final} {seq[1]}" if size == 2 else joiner.join(seq[:-1]) + f" {final} {seq[-1]}"


def td_dt(dt: datetime, locale: str = "en_gb", *, source: datetime = None, accuracy: int = 3, brief: bool = False, suffix: bool = False) -> str:
    """ Get a string from datetime differences """
    now = (source or time.now(None)).replace(microsecond=0)
    then = dt.astimezone(timezone.utc)
    if then > now:
        delta = relativedelta(then, now)
        pre = gls("time_in_p", locale) if suffix else ''
        suf = gls("time_in_s", locale) if suffix else ''
    else:
        delta = relativedelta(now, then)
        pre = gls("time_ago_p", locale) if suffix else ''
        suf = gls("time_ago_s", locale) if suffix else ''
    attrs = [('years', 'time_year', 'time_y'), ('months', 'time_month', 'time_mo'), ('days', 'time_day', 'time_d'), ('hours', 'time_hour', 'time_h'),
             ('minutes', 'time_minute', 'time_m'), ('seconds', 'time_second', 'time_s')]
    output = []
    for attr in attrs:
        element = getattr(delta, attr[0])
        if not element:
            continue
        if attr[0] == "days" and not locale.startswith("rsl-3"):
            weeks = delta.weeks
            if weeks:
                element -= weeks * 7
                output.append(f"{gns(weeks, locale)}{gls('time_w', locale)}" if brief else plural(weeks, 'time_week', locale))
        if element <= 0:
            continue
        if brief:
            output.append(f"{gns(element, locale)}{gls(attr[2], locale)}")
        else:
            output.append(plural(element, attr[1], locale))
    output = output[:accuracy]
    if len(output) == 0:
        return gls("time_now", locale)
    else:
        if brief:
            return pre + ' '.join(output) + suf
        else:
            return pre + join(output, final=gls("generic_and", locale)) + suf
# Code based on R. Danny


def td_int(seconds: int, locale: str = "en_gb", accuracy: int = 3, is_future: bool = False, brief: bool = True, suffix: bool = False) -> str:
    return td_dt(time.now(None) + timedelta(seconds=seconds if is_future else -seconds - 1), locale, accuracy=accuracy, brief=brief, suffix=suffix)


def td_ts(timestamp: int, locale: str = "en_gb", accuracy: int = 3, brief: bool = True, suffix: bool = False) -> str:
    return td_dt(time.from_ts(timestamp, None), locale, accuracy=accuracy, brief=brief, suffix=suffix)


def gts(when: datetime = None, locale: str = "en_gb", date: bool = True, short: bool = True, dow: bool = False, seconds: bool = False, tz: bool = False) -> str:
    """ Get localised time string """
    when = when or time.now(None)
    if locale in ["rsl-1_kg", "rsl-1_ku", "rsl-5"]:
        when = time.kargadia_convert(when)
    month_names_l = get_data("time_month_names", locale)
    base = ""
    if date:
        if dow and not (locale.startswith("rsl-3") or locale in ["rsl-1_kg", "rsl-5"]):
            weekdays = get_data("time_weekdays", locale)
            weekday = weekdays[when.weekday()]
            base += f"{weekday}, "
        if locale in ["en_us"]:
            base += f"{when.day:02d}/{when.month:02d}/{when.year:04d}, "
        else:
            month_name = month_names_l[when.month % 12]
            month_name_s = month_name[:3]
            month = month_name_s if short else month_name
            base += f"{gns(when.day, locale, 2)} {month} {gns(when.year, locale, 0, False)}, "
    hour = gns(when.hour, locale, 2)
    minute = gns(when.minute, locale, 2)
    second = gns(when.second, locale, 2)
    base += f"{hour}:{minute}"
    if seconds:
        base += f":{second}"
    if tz:
        base += f" {when.tzname()}"
    return base


def gts_date(when: datetime, locale: str = "en_gb", short: bool = False, year: bool = True) -> str:
    if locale in ["rsl-1_kg", "rsl-1_ku", "rsl-5"]:
        when = time.kargadia_convert(when)
    month_names_l = get_data("time_month_names", locale)
    month_name = month_names_l[when.month % 12]
    month_name_s = month_name[:3]
    month = month_name if not short else month_name_s
    return f"{gns(when.day, locale)} {month}{' ' + gns(when.year, locale, 0, False) if year else ''}"
