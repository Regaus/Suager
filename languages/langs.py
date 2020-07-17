from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from core.utils import time


month_names = {
        "en_gb": ["December", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November"]
    }


def gbs(value: int, locale: str = "en_gb") -> str:  # Get Byte String
    """ Gets Byte value name (for dlram) """
    if locale == "en_gb":
        names = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
        step = 1024
    else:
        names = "Unknown"
        step = 1024
    range_val = len(names)
    for i in range(range_val):
        req = step ** (i + 1)
        if value < req or i == range_val - 1:
            return f"{value / (step ** i):,.2f} {names[i]}"


def gns(value: int, locale: str = "en_gb", fill: int = 0, commas: bool = True) -> str:  # Get number string
    """ Get a string from an integer """
    if locale == "en_gb":
        return f"{value:0{fill}{',' if commas else ''}d}"


def gfs(value: float, locale: str = "en_gb", precision: int = 2, percentage: bool = False) -> str:  # Get float string
    """ Get a string from a float """
    if locale == "en_gb":
        return f"{value:,.{precision}f}" if not percentage else f"{value:,.{precision}%}"


def put_commas(string: str) -> str:
    reverse = string[::-1]
    return (",".join([reverse[i:i+3] for i in range(0, len(reverse), 3)]))[::-1]


def plural(value: int, name_1: str, name_2: str = '', name_pl: str = '', locale: str = "en_gb") -> str:
    """ Get plural form """
    if locale == "en_gb":
        return f"{gns(value, locale)} {name_1}" if value == 1 else f"{gns(value, locale)} {name_1}s" if not name_2 or name_pl \
            else f"{gns(value, locale)} {name_2}"


def join(seq, joiner: str = ', ', final: str = 'and'):
    size = len(seq)
    return '' if size == 0 else seq[0] if size == 1 else f"{seq[0]} {final} {seq[1]}" if size == 2 else joiner.join(seq[:-1]) + f" {final} {seq[-1]}"


def td_dt(dt: datetime, locale: str = "en_gb", *, source: datetime = None, accuracy: int = 3, brief: bool = False, suffix: bool = False) -> str:
    """ Get a string from datetime differences """
    if locale:
        del locale  # Not used yet
    now = (source or time.now(None)).replace(microsecond=0)
    then = time.from_ts(time.get_ts(dt), None)
    suf, pre = '', ''
    if then > now:
        delta = relativedelta(then, now)
        pre = "in " if suffix else ""
    else:
        delta = relativedelta(now, then)
        suf = " ago" if suffix else ""
    attrs = [('years', 'year', 'y'), ('months', 'month', 'mo'), ('days', 'day', 'd'), ('hours', 'hour', 'h'), ('minutes', 'minute', 'm'),
             ('seconds', 'second', 's')]
    output = []
    for attr in attrs:
        element = getattr(delta, attr[0])
        if not element:
            continue
        if attr[0] == "days":
            weeks = delta.weeks
            if weeks:
                element -= weeks * 7
                output.append(f"{weeks}w" if brief else plural(weeks, 'week'))
        if element <= 0:
            continue
        if brief:
            output.append(f"{element}{attr[2]}")
        else:
            output.append(plural(element, attr[1]))
    output = output[:accuracy]
    if len(output) == 0:
        return "now"
    else:
        if brief:
            return pre + ' '.join(output) + suf
        else:
            return pre + join(output) + suf
# Code based on R. Danny


def td_int(seconds: int, locale: str = "en_gb", accuracy: int = 3, is_future: bool = False, brief: bool = True, suffix: bool = False) -> str:
    return td_dt(time.now(None) + timedelta(seconds=seconds if is_future else -seconds - 1), locale, accuracy=accuracy, brief=brief, suffix=suffix)


def td_ts(timestamp: int, locale: str = "en_gb", accuracy: int = 3, brief: bool = True, suffix: bool = False) -> str:
    return td_dt(time.from_ts(timestamp, None), locale, accuracy=accuracy, brief=brief, suffix=suffix)


def gts(when: datetime = None, locale: str = "en_gb", date: bool = True, short: bool = True, dow: bool = False, seconds: bool = False, tz: bool = False) -> str:
    """ Get localised time string """
    when = when or time.now(None)
    month_names_l = month_names.get(locale, month_names["en_gb"])
    base = ""
    if date:
        if dow:
            weekdays = {
                "en_gb": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            }
            weekday = (weekdays.get(locale, weekdays["en_gb"]))[when.weekday()]
            base += f"{weekday}, "
        base += gns(when.day, locale, 2)
        month_name = month_names_l[when.month % 12]
        month_name_s = month_name[:3]
        month = month_name if not short else month_name_s
        base += f" {month} "
        base += gns(when.year, locale, commas=False) + ", "
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
    month_names_l = month_names.get(locale, month_names["en_gb"])
    month_name = month_names_l[when.month % 12]
    month_name_s = month_name[:3]
    month = month_name if not short else month_name_s
    return f"{gns(when.day, locale)} {month}{' ' + gns(when.year, locale, 0, False) if year else ''}"
