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
        if day > length:
            day -= length
            month += 1
        else:
            break
    return year, month, day + 1, h, m, s, days_oa


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
