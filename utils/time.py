from datetime import datetime, timedelta as td, timezone

import pytz
from dateutil.relativedelta import relativedelta


def time_output(when: datetime, day: bool = True, seconds: bool = False, dow: bool = False, tz: bool = False):
    d, n = ["%a, ", '']
    f = f"{f'{d if dow else n}%d %b %Y, ' if day else ''}%H:%M{':%S' if seconds else ''}{' %Z' if tz else ''}"
    return when.strftime(f)


def now(utc: bool = False):
    from utils.generic import config
    if utc:
        return datetime.now(tz=timezone.utc)
    return datetime.now(tz=pytz.timezone(config["timezone"]))
    # return datetime.utcnow() if utc else datetime.now()


def set_tz(dt: datetime, tz: str):
    return dt.astimezone(tz=pytz.timezone(tz))


def now_k():
    t = now(True).astimezone(timezone(td(hours=1, minutes=30), "KST"))
    r = relativedelta(years=-276, days=5)
    return t + r


def time_k(day: bool = True, seconds: bool = True, dow: bool = False, tz: bool = False):
    return time_output(now_k(), day, seconds, dow, tz)


def time(utc: bool = False, day: bool = True, seconds: bool = True, dow: bool = False, tz: bool = False):
    return time_output(now(utc), day, seconds, dow, tz)


# def get_time(timestamp: int, utc: bool = False):
#     return datetime.utcfromtimestamp(timestamp) if utc else datetime.fromtimestamp(timestamp)


def from_ts(timestamp: int or float, utc=False) -> datetime:
    from utils.generic import config
    if utc:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return datetime.fromtimestamp(timestamp, tz=pytz.timezone(config["timezone"]))


def now_ts() -> float:
    return get_ts(now())
    # return datetime.timestamp(now(False))


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


# def timedelta(seconds: int, show_seconds: bool = True):
#     m, s = divmod(seconds, 60)
#     h, m = divmod(m, 60)
#     d, h = divmod(h, 24)
#     d, h, m, s = round(d), round(h), round(m), round(s)
#     ds = f"{d}d " if d != 0 else ""
#     hs = f"{h}h " if h != 0 or d != 0 else ""
#     ms = f"{m}m"
#     ss = f" {s}s" if show_seconds else ""
#     return ds + hs + ms + ss
# Code yoinked from: https://github.com/iDevision/Life/blob/master/Life/cogs/utilities/utils.py


def timesince(when: datetime):
    t = now(False) - from_ts(get_ts(when), False)
    # This piece of shit complains about offset-naive and offset-aware datetime, but this horror somehow makes it shut the fuck up about it
    return timedelta(int(t.total_seconds()))


def human_timedelta(dt, *, source=None, accuracy=3, brief=False, suffix=True):
    # _now = source or datetime.utcnow()
    _now = source or now(False)
    # Microsecond free zone
    _now = _now.replace(microsecond=0)
    # dt = dt.replace(microsecond=0)
    dt = from_ts(get_ts(dt), False)

    # This implementation uses relativedelta instead of the much more obvious
    # divmod approach with seconds because the seconds approach is not entirely
    # accurate once you go over 1 week in terms of accuracy since you have to
    # hardcode a month as 30 or 31 days.
    # A query like "11 months" can be interpreted as "11 months and 6 days"
    if dt > _now:
        delta = relativedelta(dt, _now)
        suffix = ''
    else:
        delta = relativedelta(_now, dt)
        suffix = ' ago' if suffix else ''

    attrs = [
        ('year', 'y'),
        ('month', 'mo'),
        ('day', 'd'),
        ('hour', 'h'),
        ('minute', 'm'),
        ('second', 's'),
    ]

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
            return human_join(output, final='and') + suffix
        else:
            return ' '.join(output) + suffix
# Code from R. Danny


def timedelta(seconds: int, accuracy: int = 3, future: bool = False, suffix: bool = False, show_seconds=True):
    # _now = source or datetime.utcnow()
    # _now = source or now(False)
    # Microsecond free zone
    # _now = _now.replace(microsecond=0)
    # dt = dt.replace(microsecond=0)
    n = now(False)
    t = now(False) + td(seconds=seconds)
    # delta = relativedelta(seconds=seconds).normalized()
    p = "in " if future and suffix else ""
    s = " ago" if not future and suffix else ""
    delta = relativedelta(t, n)
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
                output.append(f'{weeks}w')

        if elem <= 0:
            continue
        if not show_seconds and brief_attr == "s":
            continue
        output.append(f'{elem}{brief_attr}')

    if accuracy is not None:
        output = output[:accuracy]

    if len(output) == 0:
        return 'now'
    else:
        t = ' '.join(output)
        # if suffix:
        #     if future:
        #         t = 'in ' + t
        #     else:
        #         t += ' ago'
        return f"{p}{t}{s}"
        # if not brief:
        #     return human_join(output, final='and') + suffix
        # else:
        #     return ' '.join(output) + suffix
# Code adopted from R. Danny
