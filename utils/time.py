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


def date_kargadia():
    kst = timezone(td(hours=1, minutes=30), "KST")
    irl = now(True).astimezone(kst)
    start = datetime(2000, 1, 1, 8, tzinfo=kst)  # Because why not?
    total = (irl - start).total_seconds()
    ml = 32  # month length
    wl = 8  # week length
    year = 1074
    day_length = 37.49865756 * 3600
    days = total / day_length
    secs = (days % 1) * day_length
    kdl = 32 ** 3  # Kargadia's day length
    ksl = day_length / kdl  # Second length compared to real time
    ks = int(secs / ksl)
    h, ms = divmod(ks, 32 * 32)
    m, s = divmod(ms, 32)
    dl = int(days)
    while True:
        yl = 513 if year % 8 == 0 else 512
        if dl > yl:
            year += 1
            dl -= yl
        else:
            break
    month, day = divmod(dl, ml)
    dow = dl % wl
    weekdays = ["Senka", "Navaite", "Sennen", "Karga", "Teinen", "Kannaite", "Sua", "Shira"]
    parts = ["tea", "rea", "sea", "vea"]
    part = h // 8
    day_name = f"{weekdays[dow]}{parts[part]}"
    months = ["Senkannar", "Shirannar", "Kanvamar", "Shokamar", "Nurinnar", "Aijamar", "Kionnar", "Nuudamar", "Bauzemar", "Tvinkannar",
              "Suannar", "Kittinnar", "Dekimar", "Haltannar", "Kaivennar", "Kärasmar"]
    return f"{day_name}, {day + 1:02X}/{month + 1:02X}/{year:X} RE {h:02X}:{m:02X}:{s:02X} ({day + 1:02d} {months[month]} {year}, {h:02d}:{m:02d}:{s:02d})"


def time_k(day: bool = True, seconds: bool = True, dow: bool = False, tz: bool = False):
    return time_output(now_k(), day, seconds, dow, tz)


def time(utc: bool = False, day: bool = True, seconds: bool = True, dow: bool = False, tz: bool = False):
    return time_output(now(utc), day, seconds, dow, tz)


def from_ts(timestamp: int or float, utc=False) -> datetime:
    from utils.generic import config
    if utc:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return datetime.fromtimestamp(timestamp, tz=pytz.timezone(config["timezone"]))


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
    t = now(False) - from_ts(get_ts(when), False)
    # This piece of shit complains about offset-naive and offset-aware datetime, but this horror somehow makes it shut the fuck up about it
    return timedelta(int(t.total_seconds()))


def human_timedelta(dt, *, source=None, accuracy=3, brief=False, suffix=True):
    _now = source or now(False)
    _now = _now.replace(microsecond=0)
    dt = from_ts(get_ts(dt), False)
    if dt > _now:
        delta = relativedelta(dt, _now)
        suffix = ''
    else:
        delta = relativedelta(_now, dt)
        suffix = ' ago' if suffix else ''
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
            return human_join(output, final='and') + suffix
        else:
            return ' '.join(output) + suffix
# Code from R. Danny


def timedelta(seconds: int, accuracy: int = 3, future: bool = False, suffix: bool = False, show_seconds=True):
    n = now(False)
    t = now(False) + td(seconds=seconds)
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
        return f"{p}{t}{s}"
# Code adopted from R. Danny
