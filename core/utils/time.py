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


def now_k():
    t = now(None).astimezone(timezone(td(hours=1, minutes=30), "KST"))
    r = relativedelta(years=-276, days=5)
    return t + r


def time_k(day: bool = True, seconds: bool = True, dow: bool = False, tz: bool = False):
    return time_output(now_k(), day, seconds, dow, tz)


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


def human_join(seq, delim=', ', final='or'):
    size = len(seq)
    if size == 0:
        return ''
    if size == 1:
        return seq[0]
    if size == 2:
        return f'{seq[0]} {final} {seq[1]}'
    return delim.join(seq[:-1]) + f' {final} {seq[-1]}'


class Plural:
    def __init__(self, value):
        self.value = value

    def __format__(self, format_spec):
        v = self.value
        _singular, sep, _plural = format_spec.partition('|')
        _plural = _plural or f'{_singular}s'
        if abs(v) != 1:
            return f'{v} {_plural}'
        return f'{v} {_singular}'


def timesince(when: datetime):
    t = now(None) - from_ts(get_ts(when), None)
    # This piece of shit complains about offset-naive and offset-aware datetime, but this horror somehow makes it shut the fuck up about it
    return timedelta(int(t.total_seconds()))


def human_timedelta(dt: datetime, *, source: datetime = None, accuracy: int = 3, brief: bool = False, suffix: bool = True):
    _now = source or now(None)
    _now = _now.replace(microsecond=0)
    dt = from_ts(get_ts(dt), None)
    if dt > _now:
        delta = relativedelta(dt, _now)
        suffix = ''
        prefix = 'in ' if suffix else ''
    else:
        delta = relativedelta(_now, dt)
        suffix = ' ago' if suffix else ''
        prefix = ''
    attrs = [('year', 'y'), ('month', 'mo'), ('day', 'd'), ('hour', 'h'), ('minute', 'm'), ('second', 's')]
    output = []
    for attr, brief_attr in attrs:
        elem = getattr(delta, attr + 's')
        if not elem:
            continue
        if attr == 'day':
            weeks = delta.weeks
            if weeks:
                elem -= weeks * 7
                if not brief:
                    output.append(format(Plural(weeks), 'week'))
                else:
                    output.append(f'{weeks}w')
        if elem <= 0:
            continue
        if brief:
            output.append(f'{elem}{brief_attr}')
        else:
            output.append(format(Plural(elem), attr))
    if accuracy is not None:
        output = output[:accuracy]
    if len(output) == 0:
        return 'now'
    else:
        if not brief:
            return prefix + human_join(output, final='and') + suffix
        else:
            return prefix + ' '.join(output) + suffix
# Code based on R. Danny


def timedelta(seconds: int, accuracy: int = 3, future: bool = False, suffix: bool = False):
    return human_timedelta(now(None) + td(seconds=seconds if future else -seconds), accuracy=accuracy, suffix=suffix, brief=True)
