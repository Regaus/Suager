from datetime import datetime, timezone

from core.utils import time


class KargadiaTime:
    def __init__(self, year: int, month: int, day: int, hour: int, minute: int, second: int, ds: int = 1):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        wl = 8  # week length
        dow = ds % wl
        weekdays = ["Senka", "Navai", "Sanva", "Havlei", "Teine", "Kannai", "Sua", "Shira"]
        parts = ["tea", "rea", "sea", "vea"]
        part = self.hour // 8
        self.day_name = f"{weekdays[dow]}{parts[part]}"
        self.months = ["Senkannar", "Shirannar", "Kanvamar", "Shokamar", "Nurinnar", "Aijamar", "Kionnar", "Nuudamar",
                       "Bauzemar", "Tvinkannar", "Suannar", "Kittinnar", "Dekimar", "Haltannar", "Kaivennar", "Kärasmar"]

    def str_dec(self, dow: bool = True, month: bool = False, tz: bool = True):
        dn = f"{self.day_name}, " if dow else ""
        mn = f" {self.months[self.month - 1]} " if month else f"/{self.month:02d}/"
        return f"{dn}{self.day:02d}{mn}{self.year} RE, {self.hour:02d}:{self.minute:02d}:{self.second:02d}{' KST' if tz else ''}"

    def str_hex(self, dow: bool = False, month: bool = True, tz: bool = False):
        dn = f"{self.day_name}, " if dow else ""
        mn = f" {self.months[self.month - 1]} " if month else f"/{self.month:02X}/"
        return f"{dn}{self.day:02X}{mn}{self.year:X} RE, {self.hour:02X}:{self.minute:02X}:{self.second:02X}{' KST' if tz else ''}"

    def str_full(self):
        return f"{self.str_dec()} ({self.str_hex()})"


def time_kargadia(when: datetime = None):
    irl = when or time.now(None)
    start = datetime(1970, 1, 1, 6, 30, tzinfo=timezone.utc)
    total = (irl - start).total_seconds()
    ml = 32  # month length
    year = 1060
    day_length = 37.49865756 * 3600
    days = total / day_length
    secs = (days % 1) * day_length
    kdl = 32 ** 3  # Kargadia's day length
    ksl = day_length / kdl  # Second length compared to real time
    ks = int(secs / ksl)
    h, ms = divmod(ks, 32 * 32)
    m, s = divmod(ms, 32)
    dl = int(days)
    _ds = dl
    while True:
        yl = 513 if year % 8 == 0 else 512
        if dl > yl:
            year += 1
            dl -= yl
        else:
            break
    month, day = divmod(dl, ml)
    return KargadiaTime(year, month + 1, day + 1, h, m, s, _ds)
    # return f"{day_name}, {day + 1:02d}/{month + 1:02d}/{year}, {h:02d}:{m:02d}:{s:02d} ({day + 1:02X} {months[month]} {year:X} RE, {h:02X}:{m:02X}:{s:02X})"


def date_kargadia(when: datetime = None):
    return time_kargadia(when).str_full()
