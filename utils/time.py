import re
from datetime import datetime, timedelta as td, timezone

import pytz
from dateutil.relativedelta import relativedelta


def dt(year: int, month: int = 1, day: int = 1, hour: int = 0, minute: int = 0, second: int = 0):
    return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)


zero = dt(1970)


def time_output(when: datetime, day: bool = True, seconds: bool = False, dow: bool = False, tz: bool = False):
    d, n = "%a, ", ''
    # m = "34 June" if (when.day == 4 and when.month == 7) else "%d %b"
    f = f"{f'{d if dow else n}%d %b %Y, ' if day else ''}%H:%M{':%S' if seconds else ''}{' %Z' if tz else ''}"
    return when.strftime(f)


def now(tz: str = None):
    if not tz:
        return datetime.now(tz=timezone.utc)
    return datetime.now(tz=pytz.timezone(tz))


def now2():
    return datetime.utcnow()


def set_tz(when: datetime, tz: str):
    if when.tzinfo is None:
        return datetime(when.year, when.month, when.day, when.hour, when.minute, when.second, when.microsecond, pytz.timezone(tz))
    return when.astimezone(tz=pytz.timezone(tz))


def senko_lair_time(when: datetime):
    return when.astimezone(timezone(td(hours=1, minutes=30), "SLT"))


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
    _tz = timezone.utc if not tz else pytz.timezone(tz)
    try:
        return datetime.fromtimestamp(timestamp, _tz)
    except OSError:
        return (zero + td(seconds=timestamp)).astimezone(_tz)
    # if not tz:
    #     return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    # return datetime.fromtimestamp(timestamp, tz=pytz.timezone(tz))


def now_ts() -> float:
    return get_ts(now())


def get_ts(when: datetime) -> float:
    try:
        return datetime.timestamp(when)
    except OSError:
        return (when - zero).total_seconds()  # Still shows exact amount of seconds between zero time and the timestamp


def file_ts(name: str, ext: str = "txt") -> str:
    return f"{name}_{int(now_ts())}.{ext}"


def interpret_time(period: str, cls=relativedelta, time_class=None) -> relativedelta:
    """Convert str to relativedelta - may be changed to use another class, eg r.py delta"""
    matches = re.findall(r"(\d+(y|mo|w|d|h|m|s))", period)
    if not matches:  # No matches found - not a valid relative time
        if time_class:
            return cls(seconds=0, time_class=time_class)  # type: ignore
        return cls(seconds=0)
    else:
        try:
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
            if time_class:
                _td["time_class"] = time_class
            return cls(**_td)
        except Exception as e:
            type(e)  # ignore haha yes
            if time_class:
                return cls(seconds=0, time_class=time_class)  # type: ignore
            return cls(seconds=0)


def add_time(delta: relativedelta):
    if rd_is_zero(delta):
        return "No time was specified, or an error has occurred.", True
    try:
        return datetime.utcnow() + delta, False
    except Exception as e:
        return f"{type(e).__name__}: {str(e)}", True


def rd_negative(delta: relativedelta) -> bool:
    try:
        datetime.min + delta
        return False
    except (ValueError, OverflowError):
        return True


def rd_is_zero(delta: relativedelta) -> bool:
    try:
        return datetime.min + delta == datetime.min
    except (ValueError, OverflowError):
        return False


def rd_is_above_1w(delta: relativedelta) -> bool:
    try:
        delta2 = ((now(None) + delta) - now(None)).total_seconds()
        return delta2 > 7 * 86400
        # no = False
        # if delta2.days > 7:
        #     no = True
        # elif delta2.days == 7:
        #     delta2.days -= 7
        #     if not rd_is_zero(delta2):
        #         no = True
        # return no
    except (ValueError, OverflowError):
        return True  # Errors out, assume something is wrong anyways


def rd_is_above_30d(delta: relativedelta) -> bool:
    try:
        delta2 = ((now(None) + delta) - now(None)).total_seconds()
        return delta2 > 30 * 86400
    except (ValueError, OverflowError):
        return True


def rd_is_below_15m(delta: relativedelta) -> bool:
    try:
        delta2 = ((now(None) + delta) - now(None)).total_seconds()
        return delta2 < 899
    except (ValueError, OverflowError):
        return True


def rd_is_below_1h(delta: relativedelta) -> bool:
    try:
        delta2 = ((now(None) + delta) - now(None)).total_seconds()
        return delta2 < 3599
    except (ValueError, OverflowError):
        return True


def rd_is_above_5y(delta: relativedelta) -> bool:
    try:
        delta2 = relativedelta(now(None) + delta, now(None))
        no = False
        if delta2.years > 5:
            no = True
        elif delta2.years == 5:
            delta2.years -= 5
            if not rd_is_zero(delta2):
                no = True
        return no
    except (ValueError, OverflowError):
        return True  # Errors out, assume something is wrong anyways


def rd_future(delta: relativedelta) -> bool:
    if delta.years >= 9999:
        return True
    try:
        datetime.min + delta
        return True
    except (ValueError, OverflowError):
        return False


def april_fools():
    _now = now2().date()
    return _now.day == 1 and _now.month == 4
