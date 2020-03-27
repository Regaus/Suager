from datetime import datetime

from dateutil.relativedelta import relativedelta


def time_output(when: datetime, day: bool = True, seconds: bool = False, dow: bool = False):
    d, n = ["%a, ", '']
    f = f"{f'{d if dow else n}%d %b %Y, ' if day else ''}%H:%M{':%S' if seconds else ''}"
    return when.strftime(f)


def now(utc: bool = False):
    return datetime.utcnow() if utc else datetime.now()


def time(utc: bool = False, day: bool = True, seconds: bool = True, dow: bool = False):
    return time_output(now(utc), day, seconds, dow)


def get_time(timestamp: int, utc: bool = False):
    return datetime.utcfromtimestamp(timestamp) if utc else datetime.fromtimestamp(timestamp)


def from_ts(timestamp, utc=True):
    if utc:
        return datetime.utcfromtimestamp(timestamp)
    else:
        return datetime.fromtimestamp(timestamp)


def now_ts():
    return datetime.timestamp(now(False))


def file_ts(name, ext="txt"):
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


def timedelta(seconds: int):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    d, h, m, s = round(d), round(h), round(m), round(s)
    ds = f"{d}d " if d != 0 else ""
    hs = f"{h}h " if h != 0 or d != 0 else ""
    ms = f"{m}m {s}s"
    return ds + hs + ms
# Code yoinked from: https://github.com/iDevision/Life/blob/master/Life/cogs/utilities/utils.py


def timesince(when: datetime):
    t = now() - when
    return timedelta(int(t.total_seconds()))


def human_timedelta(dt, *, source=None, accuracy=3, brief=False, suffix=True):
    _now = source or datetime.utcnow()
    # Microsecond free zone
    _now = _now.replace(microsecond=0)
    dt = dt.replace(microsecond=0)

    # This implementation uses relativedelta instead of the much more obvious
    # divmod approach with seconds because the seconds approach is not entirely
    # accurate once you go over 1 week in terms of accuracy since you have to
    # hardcode a month as 30 or 31 days.
    # A query like "11 months" can be interpreted as "!1 months and 6 days"
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
