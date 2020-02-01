from datetime import datetime


def time_output(time: datetime, day: bool = True, seconds: bool = False, dow: bool=False):
    d, n = ["%a, ", '']
    f = f"{f'{d if dow else n}%d %b %Y, ' if day else ''}%H:%M{':%S' if seconds else ''}"
    return time.strftime(f)


def now(utc: bool = False):
    return datetime.utcnow() if utc else datetime.now()


def time(utc: bool = False, day: bool = True, seconds: bool = True, dow: bool=False):
    return time_output(now(utc), day, seconds, dow)


def get_time(timestamp: int, utc: bool = False):
    return datetime.utcfromtimestamp(timestamp) if utc else datetime.fromtimestamp(timestamp)