from datetime import datetime, timezone
from typing import Optional

from core.utils import time


def solar_normal(now: datetime, start: datetime, day_length: float, year_len: int, ly_freq, months: list[int], leap_month: int, tz: float = 0):
    """ Calculate the time somewhere else """
    # hours, minutes and seconds settings removed since it now uses 24:60:60 anyways
    # ly_freq is a lambda/function that would calculate the logic behind leap years (since some are more complex than a single if-statement)
    total = (now - start).total_seconds()
    year = 1
    days = total / day_length + tz / 24
    seconds = (days % 1) * day_length
    local_second = day_length / 86400
    day_seconds = int(seconds / local_second)
    h, ms = divmod(day_seconds, 3600)
    m, s = divmod(ms, 60)
    days_overall = days_left = int(days)
    while True:
        year_length = year_len + ly_freq(year)
        if days_left >= year_length:
            year += 1
            days_left -= year_length
        else:
            break
    day = days_left
    month = 1
    leap = ly_freq(year)
    # extra = days_leap - days_nl
    if leap != 0:
        months[leap_month - 1] += leap
    for length in months:
        if day >= length:
            day -= length
            month += 1
        else:
            break
    return year, month, day + 1, h, m, s, days_overall, days_left


def time_zeivela(when: datetime = None, tz: float = 0):  # 23.4
    irl = when or time.now(None)
    start = datetime(60, 12, 5, 3, 40, tzinfo=timezone.utc)
    day_length = 20.4685576923076 * 3600
    month_lengths = [36] * 12
    # TODO: Update something to do with these months while RLC-2 and RLC-3 still don't exist

    def leap_calc(y: int):
        if y % 5 == 0:
            if y % 20 == 0:
                if y % 100 == 0:
                    return 1
                return 0
            return 1
        return 0

    year, month, day, h, m, s, ds, yd = solar_normal(irl, start, day_length, 212, leap_calc, month_lengths, 1, tz)
    weekdays = ["Vantakku", "Vantallu", "Hennettu", "Kaiva", "Leiva", "Kahkatu"]
    months = ["Vinhirus", "Kavderus", "Tinnerus", "Hednerus", "Hainerus", "Katterus",
              "Neiteverus", "Zeivellus", "Pentallus", "Tebarrus", "Faitualus", "Kaggarus"]
    output = TimeSolarNormal(year, month, day, h, m, s, weekdays, months, 6, ds, yd)
    output.day_name = f"Keina te {output.day_name}"
    if output.day == 37:
        output.day_name = f"Keine te Vantakku-Tahnall"
    output.month_name = f"te Vaiku te {output.month_name}"
    return output


def time_kargadia(when: datetime = None, tz: float = 0, language: str = "rsl-1k"):  # 23.5
    irl = when or time.now(None)
    start = datetime(276, 12, 26, 22, 30, tzinfo=timezone.utc)
    day_length = 27.7753663234561 * 3600
    month_lengths = [16] * 16
    year, month, day, h, m, s, ds, yd = solar_normal(irl, start, day_length, 256, lambda y: 1 if y % 16 == 0 else 0, month_lengths, 1, tz)
    weekdays, months = [f"{language} not available"] * 8, [f"{language} not available"] * 16
    if language == "rsl-1k":
        weekdays = ["Zeiju", "Hau", "Neevu", "Pesku", "Tuhtu", "Sida", "Maa", "Baste", "Dalka"]
        months = ["Senkavan", "Shiravan", "Nuuvan", "Bylkuvan", "Akuvan", "Vainavan", "Kiitavan", "Lürvuan",
                  "Raavan", "Kummavan", "Vittevan", "Avikkan", "Kaivyan", "Karratan", "Darvuan", "Suvakän"]
    elif language == "rsl-1i":
        weekdays = ["Zeiju", "Hau", "Neevu", "Pesku", "Tuhtu", "Sida", "Maa", "Baste", "Dalka"]
        months = ["Senkaan", "Shiraan", "Nuuan", "Bylkuan", "Akuan", "Vainaan", "Kiitaan", "Lürvuan",
                  "Raaan", "Kummaan", "Vittean", "Aviggan", "Kaivyan", "Karratan", "Darvuan", "Suvajan"]
    output = TimeSolarNormal(year, month, day, h, m, s, weekdays, months, 8, ds, yd)
    output.day_of_week = (output.day - 1) % 8
    if output.day == 17:
        output.day_of_week = 8
    if output.hour < 6:
        output.day_of_week -= 1
    if output.day_of_week == -1:
        output.day_of_week = 7
    parts = ["tea", "rea", "sea", "vea"]
    part = h // 6
    output.day_name = weekdays[output.day_of_week] + parts[part]
    return output


def time_kaltaryna(when: datetime = None, tz: float = 0):  # 23.6
    irl = when or time.now(None)
    start = datetime(1686, 11, 21, 11, 55, 21, tzinfo=timezone.utc)  # Time of landing on Qevenerus
    day_length = 19.1259928695 * 3600
    # day_length = 51.642812 * 3600
    month_lengths = [50] * 16
    year, month, day, h, m, s, ds, yd = solar_normal(irl, start, day_length, 800, lambda _: 0, month_lengths, 1, tz)
    weekdays = ["Senka", "Navate", "Sanvar", "Havas-Lesar", "Tenear", "Kannate", "Suvaker", "Shira"]
    months = ["Senka", "Shira", "Kanvarus", "Arkaneda", "Nurus", "Ai", "Kiona", "Gairnar",
              "Basrus", "Finkal", "Suvaker", "Kitta", "Semartar", "Kaltnar", "Kaiveal", "Karasnar"]
    output = TimeSolarNormal(year, month, day, h, m, s, weekdays, months, 8, ds, yd)
    if output.hour < 6:
        output.day_of_week -= 1
    parts = ["Tea", "Rea", "Sea", "Vea"]
    part = h // 6
    output.day_name = f"{parts[part]} ida {weekdays[output.day_of_week]}"
    output.month_name = f"ida Sakku ida {output.month_name}"
    return output


def time_sinvimania(when: datetime = None, tz: float = 0):  # 24.4
    irl = when or time.now(None)
    start = datetime(476, 1, 27, 12, tzinfo=timezone.utc)
    day_length = 11.35289 * 3600
    month_lengths = [31, 31, 31, 31, 31, 32, 31, 31, 31, 31, 31, 32]
    weekdays = ["Placeholder 1", "Placeholder 2", "Placeholder 3", "Placeholder 4", "Placeholder 5", "Placeholder 6"]
    months = ["Month 1", "Month 2", "Month 3", "Month 4", "Month 5", "Month 6", "Month 7", "Month 8", "Month 9", "Month 10", "Month 11", "Month 12"]
    year, month, day, h, m, s, ds, yd = solar_normal(irl, start, day_length, 374, lambda y: -1 if y % 5 == 0 else 0, month_lengths, 12, tz)
    return TimeSolarNormal(year, month, day, h, m, s, weekdays, months, 6, ds, yd)


def time_hosvalnerus(when: datetime = None, tz: float = 0):  # 24.5
    irl = when or time.now(None)
    start = datetime(171, 7, 1, 7, 30, tzinfo=timezone.utc)
    day_length = 23.7632 * 3600
    month_lengths = [19, 19, 19, 19, 19, 19, 19, 19, 19, 18, 19, 19, 19, 19, 19, 19, 19, 19, 19, 18]
    weekdays = ["Placeholder 1", "Placeholder 2", "Placeholder 3", "Placeholder 4", "Placeholder 5"]
    months = ["Month 1", "Month 2", "Month 3", "Month 4", "Month 5", "Month 6", "Month 7", "Month 8", "Month 9", "Month 10",
              "Month 11", "Month 12", "Month 13", "Month 14", "Month 15", "Month 16", "Month 17", "Month 18", "Month 19", "Month 20"]
    year, month, day, h, m, s, ds, yd = solar_normal(irl, start, day_length, 378, lambda y: 1 if y % 2 == 0 else 0, month_lengths, 20, tz)
    # year, month, day, h, m, s, ds = solar_normal(irl, start, day_length, 20, 20, 20, 378, 379, 2, month_lengths, 20, 0)
    return TimeSolarNormal(year, month, day, h, m, s, weekdays, months, 5, ds, yd)


class TimeSolarNormal:
    def __init__(self, year: int, month: int, day: int, hour: int, minute: int, second: int, down: list[str], mn: list[str], wl: int, ds: int, yd: int):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.dow_names = down
        self.month_names = mn
        self.week_length = wl
        self.ds = ds
        self.year_day = yd
        self.day_of_week = (self.ds - 1) % self.week_length
        self.day_name = self.dow_names[self.day_of_week]
        self.month_name = self.month_names[self.month - 1]

    def str(self, dow: bool = True, era: Optional[str] = None, month: bool = True):
        """ Output the date and time in a readable format """
        dn = f"{self.day_name}, " if dow else ""
        e = f" {era}" if era else ""
        m = f" (Month {self.month})" if month else ""
        return f"{dn}{self.day:02d} {self.month_name} {self.year}{e}, {self.hour:02d}:{self.minute:02d}:{self.second:02d}{m}"


def solar_longer(now: datetime, start: datetime, day_length: float, hours: int, mins: int, secs: int, days_nly: int, days_ly: int, ly_freq: int,
                 months: int, week_lengths: list[int], weeks_alternate: list[int], leap_month: int, alt_month: int, tz: float = 0):
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
    return year, month, week, day + 1, h, m, s, days_left


def time_kuastall_11(when: datetime = None):  # 24.11
    irl = when or time.now(None)
    start = datetime(1742, 1, 27, 10, 4, tzinfo=timezone.utc)
    day_length = 25.700005 * 3600
    weeks = [19] * 15 + [18]
    weeks2 = ([19] * 7 + [18]) * 2
    weekdays = ["Navadensea", "Kuadatsea", "Rujansea", "Senkasea", "Shirasea", "Leitakissea", "Arhanesea", "Nüriisea", "Rudvaldatsea", "Kionansea",
                "Kuarunsea", "Suvakyrsea", "Kittansea", "Valkyrusea", "Vahkandansea", "Kuastallsea", "Koansea", "Seldalkussea", "Sea Kudaganan"]
    year, month, week, day, h, m, s, yd = solar_longer(irl, start, day_length, 24, 60, 60, 19384, 19385, 5, 64, weeks, weeks2, 64, 8, 0)
    # year, month, week, day, h, m, s = solar_longer(irl, start, day_length, 24, 32, 32, 19384, 19385, 5, 64, weeks, weeks2, 64, 8, 0)
    return TimeSolarLong(year, month, week, day, h, m, s, weekdays, yd)


class TimeSolarLong:
    def __init__(self, year: int, month: int, week: int, day: int, hour: int, minute: int, second: int, down: list[str], yd: int):
        self.year = year
        self.month = month
        self.week = week
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.day_name = down[day - 1]
        self.year_day = yd
        # self.month_name = mn[month - 1]

    def str(self, dow: bool = True, era: Optional[str] = None):
        dn = f"{self.day_name}, " if dow else ""
        _era = f" {era}" if era is not None else ""
        return f"{dn}{self.day:02d}/{self.week:02d}/{self.month:02d}/{self.year:03d}{_era}, {self.hour:02d}:{self.minute:02d}:{self.second:02d}"
