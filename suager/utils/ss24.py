from datetime import datetime, timezone
from typing import List, Optional

from core.utils import time


def solar_normal(now: datetime, start: datetime, day_length: float, hours: int, mins: int, secs: int, days_nly: int, days_ly: int, ly_freq: int,
                 month_lengths: List[int], leap_month: int, tz: float = 0):
    total = (now - start).total_seconds()
    year = 1
    days = total / day_length
    days += tz / hours
    seconds = (days % 1) * day_length
    local_day_length = hours * mins * secs
    local_second = day_length / local_day_length
    day_seconds = int(seconds / local_second)
    h, ms = divmod(day_seconds, mins * secs)
    m, s = divmod(ms, secs)
    days_oa = days_left = int(days)
    while True:
        year_length = days_ly if year % ly_freq == 0 else days_nly
        if days_left >= year_length:
            year += 1
            days_left -= year_length
        else:
            break
    day = days_left
    month = 1
    leap = year % ly_freq == 0
    extra_days = 1 if days_ly > days_nly else 0 if days_ly == days_nly else -1
    if leap:
        month_lengths[leap_month - 1] += extra_days
    for length in month_lengths:
        if day >= length:
            day -= length
            month += 1
        else:
            break
    return year, month, day + 1, h, m, s, days_oa


def solar_longer(now: datetime, start: datetime, day_length: float, hours: int, mins: int, secs: int, days_nly: int, days_ly: int, ly_freq: int,
                 months: int, week_lengths: List[int], weeks_alternate: List[int], leap_month: int, alt_month: int, tz: float = 0):
    total = (now - start).total_seconds()
    year = 1
    days = total / day_length
    days += tz / hours
    seconds = (days % 1) * day_length
    local_day_length = hours * mins * secs
    local_second = day_length / local_day_length
    day_seconds = int(seconds / local_second)
    h, ms = divmod(day_seconds, mins * secs)
    m, s = divmod(ms, secs)
    days_left = int(days)
    while True:
        year_length = days_ly if year % ly_freq == 0 else days_nly
        if days_left >= year_length:
            year += 1
            days_left -= year_length
        else:
            break
    day = days_left
    month = 1
    leap = year % ly_freq == 0
    # extra_days = 1 if days_ly > days_nly else 0 if days_ly == days_nly else -1
    month_lengths = [(week_lengths if m % alt_month > 0 else weeks_alternate) for m in range(1, months + 1)]
    if leap:
        month_lengths[leap_month - 1] = week_lengths
    for month_thing in month_lengths:
        length = sum(month_thing)
        if day >= length:
            day -= length
            month += 1
        else:
            break
    week = 1
    for week_length in month_lengths[month - 1]:
        if day >= week_length:
            day -= week_length
            week += 1
        else:
            break
    return year, month, week, day + 1, h, m, s


def time_sinvimania(when: datetime = None):
    irl = when or time.now(None)
    start = datetime(476, 1, 27, 12, tzinfo=timezone.utc)
    day_length = 11.35289 * 3600
    month_lengths = [31, 31, 31, 31, 31, 32, 31, 31, 31, 31, 31, 32]
    weekdays = ["Placeholder 1", "Placeholder 2", "Placeholder 3", "Placeholder 4", "Placeholder 5", "Placeholder 6"]
    months = ["Month 1", "Month 2", "Month 3", "Month 4", "Month 5", "Month 6", "Month 7", "Month 8", "Month 9", "Month 10", "Month 11", "Month 12"]
    year, month, day, h, m, s, ds = solar_normal(irl, start, day_length, 24, 24, 24, 374, 373, 5, month_lengths, 12, 0)
    return SS24Time(year, month, day, h, m, s, weekdays, months, 6, ds, None)


def time_hosvalnerus(when: datetime = None):
    irl = when or time.now(None)
    start = datetime(171, 7, 1, 7, 30, tzinfo=timezone.utc)
    day_length = 23.7632 * 3600
    month_lengths = [19, 19, 19, 19, 19, 19, 19, 19, 19, 18, 19, 19, 19, 19, 19, 19, 19, 19, 19, 18]
    weekdays = ["Placeholder 1", "Placeholder 2", "Placeholder 3", "Placeholder 4", "Placeholder 5"]
    months = ["Month 1", "Month 2", "Month 3", "Month 4", "Month 5", "Month 6", "Month 7", "Month 8", "Month 9", "Month 10",
              "Month 11", "Month 12", "Month 13", "Month 14", "Month 15", "Month 16", "Month 17", "Month 18", "Month 19", "Month 20"]
    year, month, day, h, m, s, ds = solar_normal(irl, start, day_length, 20, 20, 20, 378, 379, 2, month_lengths, 20, 0)
    return SS24Time(year, month, day, h, m, s, weekdays, months, 5, ds, None)


def time_kuastall_11(when: datetime = None):
    irl = when or time.now(None)
    start = datetime(1742, 1, 27, 10, 4, tzinfo=timezone.utc)
    day_length = 25.700005 * 3600
    weeks = [19] * 15 + [18]
    weeks2 = ([19] * 7 + [18]) * 2
    weekdays = ["Navadensea", "Sea Kuadan", "Rujazda Sea", "Senkata Sea", "Shirata Sea", "Leitakisea", "Arhanesea", "Nüriisea", "Rudvaldatsea", "Kionansea",
                "Kuarunsea", "Suvakyrda Sea", "Kittansea", "Valkyruda Sea", "Vahkandansea", "Sea Kuastallun", "Sea Koazan", "Sea Seldalkuvit", "Sea Kudaganan"]
    year, month, week, day, h, m, s = solar_longer(irl, start, day_length, 24, 32, 32, 19384, 19385, 5, 64, weeks, weeks2, 64, 8, 0)
    return LongYearTime(year, month, week, day, h, m, s, weekdays, None)


class SS24Time:
    def __init__(self, year: int, month: int, day: int, hour: int, minute: int, second: int, down: list, mn: list, wl: int, ds: int = 1, tzn: str = None):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.tz_name = tzn
        dow = ds % wl
        self.day_name = down[dow]
        self.month_name = mn[month - 1]

    def str(self, dow: bool = True, era: Optional[str] = None, tz: bool = False):
        dn = f"{self.day_name}, " if dow else ""
        # mn = self.months[self.month - 1]
        _era = f" {era}" if era is not None else ""
        _tz = f' {self.tz_name}' if tz else ''
        return f"{dn}{self.day:02d} {self.month_name} {self.year}{_era}, {self.hour:02d}:{self.minute:02d}:{self.second:02d}{_tz} (Month {self.month})"


class LongYearTime:
    def __init__(self, year: int, month: int, week: int, day: int, hour: int, minute: int, second: int, down: List[str], tzn: str = None):
        self.year = year
        self.month = month
        self.week = week
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.tz_name = tzn
        self.day_name = down[day - 1]
        # self.month_name = mn[month - 1]

    def str(self, dow: bool = True, era: Optional[str] = None, tz: bool = False):
        dn = f"{self.day_name}, " if dow else ""
        _era = f" {era}" if era is not None else ""
        _tz = f' {self.tz_name}' if tz else ''
        return f"{dn}{self.day:02d}/{self.week:02d}/{self.month:02d}/{self.year:03d}{_era}, {self.hour:02d}:{self.minute:02d}:{self.second:02d}{_tz}"
