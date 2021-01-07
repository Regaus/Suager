import re
from datetime import datetime, timedelta as td, timezone

import pytz
from dateutil.relativedelta import relativedelta


def time_output(when: datetime, day: bool = True, seconds: bool = False, dow: bool = False, tz: bool = False):
    d, n = "%a, ", ''
    m = "34 June" if (when.day == 4 and when.month == 7) else "%d %b"
    f = f"{f'{d if dow else n}{m} %Y, ' if day else ''}%H:%M{':%S' if seconds else ''}{' %Z' if tz else ''}"
    return when.strftime(f)


def now(tz: str = None):
    if not tz:
        return datetime.now(tz=timezone.utc)
    return datetime.now(tz=pytz.timezone(tz))


def set_tz(dt: datetime, tz: str):
    return dt.astimezone(tz=pytz.timezone(tz))


def senko_lair_time(when: datetime):
    return when.astimezone(timezone(td(hours=1, minutes=30), "KST"))


def now_sl():
    return senko_lair_time(now(None))


def kargadia_convert(when: datetime):
    return when.astimezone(timezone(td(hours=1, minutes=30), "KST")) + relativedelta(years=-276, days=5)


def now_k():
    return kargadia_convert(now(None))
    # t = now(None).astimezone(timezone(td(hours=1, minutes=30), "KST"))
    # r = relativedelta(years=-276, days=5)
    # return t + r


# def time_k(day: bool = True, seconds: bool = True, dow: bool = False, tz: bool = False):
#     return time_output(now_k(), day, seconds, dow, tz)


def time(tz: str = None, day: bool = True, seconds: bool = True, dow: bool = False, _tz: bool = False):
    return time_output(now(tz), day, seconds, dow, _tz)


def from_ts(timestamp: int or float, tz: str = None) -> datetime:
    if not tz:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return datetime.fromtimestamp(timestamp, tz=pytz.timezone(tz))


def now_ts() -> float:
    return get_ts(now())


def get_ts(when: datetime) -> float:
    return datetime.timestamp(when)


def file_ts(name: str, ext: str = "txt") -> str:
    return f"{name}_{int(now_ts())}.{ext}"


def dt(year: int, month: int = 1, day: int = 1, hour: int = 0, minute: int = 0, second: int = 0):
    return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)


def interpret_time(period: str) -> None or td:
    matches = re.findall(r"(\d+(y|mo|w|d|h|m|s))", period)
    if not matches:
        return None
    else:
        _td = {}
        keys = {"y": "years", "mo": "months", "w": "weeks", "d": "days", "h": "hours", "m": "minutes", "s": "seconds"}
        for match, _period in matches:
            _length = match.replace(_period, "")
            key = keys.get(_period)
            length = int(_length)
            if key in _td:
                _td[key] += length
            else:
                _td[key] = length
        return relativedelta(**_td)


def add_time(delta: relativedelta):
    try:
        return datetime.utcnow() + delta, False
    except Exception as e:
        return f"{type(e).__name__}: {str(e)}", True


def rd_negative(delta: relativedelta):
    try:
        datetime.min + delta
        return False
    except (ValueError, OverflowError):
        return True
