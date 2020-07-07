from datetime import datetime, timezone

from core.utils import time, bases


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
        return f"{dn}{self.day:02d}{mn}{self.year} RE, {self.hour:02d}:{self.minute:02d}:{self.second:02d}{' KCT' if tz else ''}"

    def str_hex(self, dow: bool = False, month: bool = True, tz: bool = False):
        dn = f"{self.day_name}, " if dow else ""
        mn = f" {self.months[self.month - 1]} " if month else f"/{self.month:02X}/"
        return f"{dn}{self.day:02X}{mn}{self.year:X} RE, {self.hour:02X}:{self.minute:02X}:{self.second:02X}{' KCT' if tz else ''}"

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


class ZeivelaTime:
    def __init__(self, year: int, month: int, day: int, hour: int, minute: int, second: int, ds: int = 1):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        wl = 6  # week length
        dow = ds % wl
        weekdays = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth"]
        self.day_name = f"Day of {weekdays[dow]}"
        self.months = ["Month 1", "Month 2", "Month 3", "Month 4", "Month 5", "Month 6",
                       "Month 7", "Month 8", "Month 9", "Month 10", "Month 11", "Month 12"]

    def str_dec(self, dow: bool = True, month: bool = False, tz: bool = True):
        dn = f"{self.day_name}, " if dow else ""
        mn = f" {self.months[self.month - 1]} " if month else f"/{self.month:02d}/"
        return f"{dn}{self.day:02d}{mn}{self.year} ZE, {self.hour:02d}:{self.minute:02d}:{self.second:02d}{' ZCT' if tz else ''}"

    def str_sen(self, dow: bool = False, month: bool = True, tz: bool = False):
        dn = f"{self.day_name}, " if dow else ""
        mn = f" {self.months[self.month - 1]} " if month else f"/{bases.base_6(self.month)}/"
        h, m, s = bases.base_6(self.hour).zfill(2), bases.base_6(self.minute).zfill(2), bases.base_6(self.second).zfill(2)
        return f"{dn}{bases.base_6(self.day)}{mn}{bases.base_6(self.year)} ZE, {h}:{m}:{s}{' ZCT' if tz else ''}"

    def str_full(self):
        return f"{self.str_dec()} ({self.str_sen()})"


def time_zeivela(when: datetime = None):
    irl = when or time.now(None)
    start = datetime(1970, 1, 1, 6, 30, tzinfo=timezone.utc)
    total = (irl - start).total_seconds()
    ml = 36  # month length
    year = 236
    day_length = 27.12176253 * 3600
    days = total / day_length
    secs = (days % 1) * day_length
    kdl = 36 ** 3  # Local day length
    ksl = day_length / kdl  # Second length compared to real time
    ks = int(secs / ksl)
    h, ms = divmod(ks, 36 * 36)
    m, s = divmod(ms, 36)
    dl = int(days)
    _ds = dl
    while True:
        yl = 421 if year % 3 == 0 else 420
        if dl > yl:
            year += 1
            dl -= yl
        else:
            break
    month, day = divmod(dl, ml)
    return ZeivelaTime(year, month + 1, day + 1, h, m, s, _ds)


def date_zeivela(when: datetime = None):
    return time_zeivela(when).str_full()


class KaltarynaTime:
    def __init__(self, year: int, month: int, day: int, hour: int, minute: int, second: int, ds: int = 1):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        wl = 8  # week length
        dow = ds % wl
        weekdays = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth"]
        self.day_name = f"{weekdays[dow]} Day"
        self.months = ["Month 1", "Month 2", "Month 3", "Month 4", "Month 5", "Month 6", "Month 7", "Month 8",
                       "Month 9", "Month 10", "Month 11", "Month 12", "Month 13", "Month 14", "Month 15", "Month 16"]

    def str_dec(self, dow: bool = True, month: bool = False, tz: bool = True):
        dn = f"{self.day_name}, " if dow else ""
        mn = f" {self.months[self.month - 1]} " if month else f"/{self.month:02d}/"
        return f"{dn}{self.day:02d}{mn}{self.year} KAE, {self.hour:02d}:{self.minute:02d}:{self.second:02d}{' ACT' if tz else ''}"

    def str_hex(self, dow: bool = False, month: bool = True, tz: bool = False):
        dn = f"{self.day_name}, " if dow else ""
        mn = f" {self.months[self.month - 1]} " if month else f"/{self.month:02X}/"
        return f"{dn}{self.day:02X}{mn}{self.year:X} KAE, {self.hour:02X}:{self.minute:02X}:{self.second:02X}{' ACT' if tz else ''}"

    def str_full(self):
        return f"{self.str_dec()} ({self.str_hex()})"


def time_kaltaryna(when: datetime = None):
    irl = when or time.now(None)
    start = datetime(1970, 1, 1, 6, 30, tzinfo=timezone.utc)
    total = (irl - start).total_seconds()
    ml = 50  # month length
    year = 71
    day_length = 51.642812 * 3600
    days = total / day_length
    secs = (days % 1) * day_length
    kdl = 32 ** 3  # Local day length
    ksl = day_length / kdl  # Second length compared to real time
    ks = int(secs / ksl)
    h, ms = divmod(ks, 32 * 32)
    m, s = divmod(ms, 32)
    dl = int(days)
    _ds = dl
    while True:
        yl = 800
        if dl > yl:
            year += 1
            dl -= yl
        else:
            break
    month, day = divmod(dl, ml)
    return KaltarynaTime(year, month + 1, day + 1, h, m, s, _ds)


def date_kaltaryna(when: datetime = None):
    return time_kaltaryna(when).str_full()
