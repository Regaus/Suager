from __future__ import annotations
import datetime as _datetime
from typing import Optional, overload, Type, Union

from utils import languages

__version__ = (1, 0, 0, 'rc', 2)
last_updated = (2021, 10, 1)
MIN_YEAR = -999999
MAX_YEAR = 999999


def _compare(x, y):
    return 0 if x == y else 1 if x > y else -1


def _compare_error(x, y):
    raise TypeError("can't compare '%s' to '%s'" % (
                    type(x).__name__, type(y).__name__))


class TimeClassError(TypeError):
    """ Defines an error where the Time Class of two dates/datetimes being compared does not match """
    def __init__(self, text=None):
        # self.text =
        super().__init__(text)


class Earth:
    def __init__(self):
        self.days_in_month = [-1, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        self.months_in_year = len(self.days_in_month) - 1
        self.days_in_year = sum(self.days_in_month[1:])
        self.days_before_month = [-1]
        dbm = 0
        for dim in self.days_in_month[1:]:
            self.days_before_month.append(dbm)
            dbm += dim
        del dbm, dim
        self.leap_day_month = 2  # The month where leap days are inserted
        self.default_language = "english"

        # These are not needed in EarthTime, this is just to provide compatibility for the other calendars
        # They need to be defined by subclasses
        self.start = None
        # self.start = datetime(1, tz=timezone.utc)
        self.day_length = 86400

        self.max_ordinal = self.ymd2ord(MAX_YEAR + 1, 1, 1) - 1  # 31/12/MAX_YEAR
        self.min_ordinal = self.ymd2ord(MIN_YEAR, 1, 1)          # 01/01/MIN_YEAR

    @staticmethod
    def _is_leap(year: int) -> int:
        """ Is this year a leap year """
        return int(year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))

    @staticmethod
    def _leap_days_until(years_passed: int):
        """ How many leaps were there before this year """
        return years_passed // 4 - years_passed // 100 + years_passed // 400

    def _days_before_year(self, year: int):
        """ Return the number of days from 01/01/MIN_YEAR until 01/01/year """
        years_passed = year - MIN_YEAR  # year MIN_YEAR is "year zero"
        return years_passed * self.days_in_year + self._leap_days_until(years_passed)

    def _days_since_ad(self, year: int):
        """ Days since 01/01/0001 """
        return self._days_before_year(year) - self._days_before_year(1)

    @staticmethod
    def _timestamp_part(days: int, hour: int, minute: int, second: int, us: int):
        """ Convert the hours, minutes and seconds out of a timestamp """
        return days * 86400 + hour * 3600 + minute * 60 + second + us / 1000000

    def timestamp(self, year: int, month: int = 1, day: int = 1, hour: int = 0, minute: int = 0, second: int = 0, us: int = 0):
        """ Return the timestamp of a date/datetime """
        # return (self.ymd2ord(year, month, day) - self.ymd2ord(1970, 1, 1)) * 86400 + hour * 3600 + minute * 60 + second + us / 1000000
        return self._timestamp_part(self.ymd2ord(year, month, day) - self.ymd2ord(1970, 1, 1), hour, minute, second, us)

    @staticmethod
    def _from_timestamp_part(ts: float):
        """ Convert the hours, minutes and seconds out of a timestamp """
        seconds, part = divmod(ts, 1)
        us = int(part * 1000000)
        days, hms = divmod(int(seconds), 86400)
        days += 1
        hour, ms = divmod(hms, 3600)
        minute, second = divmod(ms, 60)
        return int(days), int(hour), int(minute), int(second), int(us)

    def from_timestamp(self, ts: float):
        """ Convert from timestamp to datetime data """
        # This takes in the fact that Earth's unix timestamps start on 01/01/1970
        # seconds, part = divmod(ts, 1)
        # us = int(part * 1000000)
        # days, hms = divmod(int(seconds), 86400)
        # days += 1
        # hour, ms = divmod(hms, 3600)
        # minute, second = divmod(ms, 60)
        # second, part = divmod(s, 1)
        days, hour, minute, second, us = self._from_timestamp_part(ts)
        add = 719162  # 01/01/0001 -> 01/01/1970
        year, month, day = self.ord2ymd(days + add)
        # year += 1969
        return year, month, day, hour, minute, second, us

    def _days_in_month(self, year: int, month: int):
        """ The number of days in that month for that year """
        assert 1 <= month <= self.months_in_year, ("month must be in 1..%d" % self.months_in_year)
        days = self.days_in_month[month]
        if month == self.leap_day_month:
            days += self._is_leap(year)
        return days

    def _days_before_month(self, year: int, month: int):
        """ The number of days in the year preceding 01/month/year """
        assert 1 <= month <= self.months_in_year, ("month must be in 1..%d" % self.months_in_year)
        return self.days_before_month[month] + (month > self.leap_day_month and self._is_leap(year))

    def ymd2ord(self, year: int, month: int, day: int):
        """ year, month, day -> ordinal where 01/01/0001 is day 1 """
        assert 1 <= month <= self.months_in_year, ("month must be in 1..%d" % self.months_in_year)
        dim = self.days_in_month[month]
        assert 1 <= day <= dim, ('day must be in 1..%d' % dim)
        return self._days_since_ad(year) + self._days_before_month(year, month) + day

    def ord2ymd(self, n: int):
        """ ordinal -> (year, month, day) where 01/01/0001 is day 1 """
        n = int(n)  # Try to make sure that n is an integer, else this will break...
        n -= 1
        di400 = self._days_since_ad(401)  # days in 400 years
        di100 = self._days_since_ad(101)  # days in 100 years
        di4 = self._days_since_ad(5)  # days in 4 years
        assert di4 == 4 * 365 + 1
        assert di400 == 4 * di100 + 1
        assert di100 == 25 * di4 - 1

        n400, n = divmod(n, di400)  # the last 400-year cycle
        n100, n = divmod(n, di100)  # the last 100-year cycle before n
        n4, n = divmod(n, di4)  # the last 4-year cycle before n
        n1, n = divmod(n, 365)  # the last single year
        year = n400 * 400 + n100 * 100 + n4 * 4 + n1 + 1
        if n1 == 4 or n100 == 4:  # This means it's the 31/12 of the year before the last 4 or 400 year cycle
            assert n == 0
            return year - 1, 12, 31

        # This seems to check if the year is actually right
        is_leap = n1 == 3 and (n4 != 24 or n100 == 3)
        assert is_leap == self._is_leap(year)

        # This estimates the current month - the guess will be either exact or one too large
        month = (n + 50) // 32  # I have no idea how they came up with this, but it works so whatever...
        preceding = self.days_before_month[month] + (month > 2 and is_leap)
        if preceding > n:
            month -= 1
            preceding -= self.days_in_month[month] + (month == 2 and is_leap)
        n -= preceding
        assert 0 <= n < self._days_in_month(year, month)
        # Now the year and month will be correct, n is the offset since the start of the month
        return year, month, n + 1

    def check_date_fields(self, year: int, month: int, day: int):
        if not MIN_YEAR <= year <= MAX_YEAR:
            raise ValueError('year must be between %d and %d (got %d)' % (MIN_YEAR, MAX_YEAR, year))
        if not 1 <= month <= self.months_in_year:
            raise ValueError('month must be between 1 and %d (got %d)' % (self.months_in_year, month))
        dim = self._days_in_month(year, month)
        if not 1 <= day <= dim:
            raise ValueError('day must be between 1 and %d (got %d)' % (dim, day))
        return year, month, day

    @staticmethod
    def weekday(_date: Union[date, datetime]):
        """ Calculate the weekday from ordinal """
        return (_date.ordinal + 6) % 7

    def from_earth_time(self, when: datetime) -> datetime:
        if type(self) == Earth:  # No point in doing anything if it's EarthTime anyways
            return when

        if when.time_class != Earth:
            raise TimeClassError("Only EarthTime datetimes can be converted")
        when = when.to_timezone(timezone.utc)
        total = (when - self.start).total_seconds()
        days = total / self.day_length
        _seconds = (days % 1) * self.day_length
        local_second = self.day_length / 86400
        seconds = _seconds / local_second
        _time = time.from_part(seconds / 86400)
        # hour, ms = divmod(seconds, 3600)
        # minute, s = divmod(ms, 60)
        # second, us = divmod(s, 1)
        # _time = time(int(hour), int(minute), int(second), int(us * 1000000), tz=timezone.utc)
        _date = date.from_ordinal(int(days) + 1, self.__class__)  # self.start == 01/01/0001, not 16/16/0001
        return datetime.combine(_date, _time)

    def to_earth_time(self, when: datetime) -> datetime:
        if type(self) == Earth:  # No point in doing anything if it's EarthTime anyways
            return when

        if when.time_class != self.__class__:
            raise TimeClassError("Only %s datetimes can be converted" % self.__class__.__name__)
        # when = when.to_timezone(timezone.utc)
        days = when.to_part(day=True, utc=True)
        _seconds = days * 86400
        local_second = self.day_length / 86400
        seconds = _seconds * local_second
        day, second = divmod(seconds, 86400)
        delta = timedelta(days=day, seconds=second)
        return self.start + delta

    def str_format(self, obj, fmt: str, _language: str = None):
        """ Format the value """
        if _language is None:
            language = languages.Language(self.default_language)
        else:
            language = languages.Language(_language)
        output = fmt
        if isinstance(obj, (date, datetime)):
            if "%a" in fmt:
                output = output.replace("%a", language.time_weekday(obj, True))
            if "%A" in fmt:
                output = output.replace("%A", language.time_weekday(obj, False))
            if "%b" in fmt:
                output = output.replace("%b", language.time_month(obj, True))
            if "%B" in fmt:
                output = output.replace("%B", language.time_month(obj, False))
            if "%d" in fmt:
                output = output.replace("%d", "%02d" % obj.day)
            if "%j" in fmt:
                output = output.replace("%j", "%03d" % obj.year_day)
            if "%m" in fmt:
                output = output.replace("%m", "%02d" % obj.month)
            if "%u" in fmt:
                output = output.replace("%u", str(obj.weekday + 1))  # Weekday as 1-7
            if "%w" in fmt:
                output = output.replace("%w", str(obj.weekday))  # Weekday as 0-6
            if "%y" in fmt:
                output = output.replace("%y", "%02d" % (obj.year % 100))  # Last 2 digits of the year
            if "%Y" in fmt:
                output = output.replace("%Y", "%04d" % obj.year)
        if isinstance(obj, (time, datetime)):
            if "%H" in fmt:
                output = output.replace("%H", "%02d" % obj.hour)
            if "%I" in fmt:
                output = output.replace("%I", "%02d" % (obj.hour % 12 or 12))
            if "%p" in fmt:
                output = output.replace("%p", "am" if obj.hour < 12 else "pm")
            if "%M" in fmt:
                output = output.replace("%M", "%02d" % obj.minute)
            if "%S" in fmt:
                output = output.replace("%S", "%02d" % obj.second)
            if "%f" in fmt:
                output = output.replace("%f", "%06d" % obj.microsecond)
            if "%z" in fmt:
                output = output.replace("%z", _format_offset(obj.utcoffset()))
            if "%Z" in fmt:
                output = output.replace("%Z", obj.tz_name())
        output = output.replace("%%", "%")
        return output

    def __repr__(self):
        return "%s.%s()" % (self.__class__.__module__, self.__class__.__qualname__)

    def __str__(self):
        return self.__class__.__name__


class Virkada(Earth):
    """ Virkada calendar """
    def __init__(self):
        super().__init__()
        self.days_in_month = [-1, 30]
        self.months_in_year = len(self.days_in_month) - 1
        self.days_in_year = sum(self.days_in_month[1:])
        self.days_before_month = [-1]
        dbm = 0
        for dim in self.days_in_month[1:]:
            self.days_before_month.append(dbm)
            dbm += dim
        del dbm, dim
        self.leap_day_month = 1  # The month where leap days are inserted
        self.default_language = "english"

        # The day the first settlement was founded on Virkada
        self.start = datetime(2004, 1, 27, 7, 45, tz=timezone.utc)
        self.day_length = 62.73232495114 * 3600

        self.max_ordinal = self.ymd2ord(MAX_YEAR + 1, 1, 1) - 1  # 31/12/MAX_YEAR
        self.min_ordinal = self.ymd2ord(MIN_YEAR, 1, 1)  # 01/01/MIN_YEAR

    @staticmethod
    def _is_leap(year: int) -> int:
        return 1 if year % 10 in [0, 2, 3, 4, 5, 7, 8] else 0

    @staticmethod
    def _leap_days_until(years_passed: int):
        decades, year = divmod(years_passed, 10)
        leaps = decades * 7
        values = [0, 2, 3, 4, 5, 7, 8]
        for value in values:
            if year > value:
                leaps += 1
        return leaps

    def timestamp(self, year: int, month: int = 1, day: int = 1, hour: int = 0, minute: int = 0, second: int = 0, us: int = 0):
        # Virkada timestamp starts from 01/01/0001
        return self._timestamp_part(self.ymd2ord(year, month, day) - 1, hour, minute, second, us)

    def from_timestamp(self, ts: float):
        days, hour, minute, second, us = self._from_timestamp_part(ts)
        year, month, day = self.ord2ymd(days)
        return year, month, day, hour, minute, second, us

    def ord2ymd(self, n: int):
        n = int(n)  # Try to make sure that n is an integer, else this will break...
        n -= 1
        n10, n = divmod(n, 307)
        n1, n = divmod(n, 30)
        n -= self._leap_days_until(n1)
        year = n10 * 10 + n1 + 1

        if n < 0:
            year -= 1
            n += 30 + self._is_leap(year)

        # There is only 1 month on Virkada
        return year, 1, n + 1

    def weekday(self, _date: Union[date, datetime]):
        return 0


class Kargadia(Earth):
    """ Kargadian time and Kargadian calendar """
    def __init__(self):
        super().__init__()
        self.days_in_month = [-1, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16]
        self.months_in_year = len(self.days_in_month) - 1
        self.days_in_year = sum(self.days_in_month[1:])
        self.days_before_month = [-1]
        dbm = 0
        for dim in self.days_in_month[1:]:
            self.days_before_month.append(dbm)
            dbm += dim
        del dbm, dim
        self.leap_day_month = 1  # The month where leap days are inserted
        self.default_language = "kargadian_west"

        # Let's just say it was some kind of religious occasion in that year
        self.start = datetime(276, 12, 26, 22, 30, tz=timezone.utc)
        self.day_length = 27.7753663234561 * 3600

        self.max_ordinal = self.ymd2ord(MAX_YEAR + 1, 1, 1) - 1  # 31/12/MAX_YEAR
        self.min_ordinal = self.ymd2ord(MIN_YEAR, 1, 1)  # 01/01/MIN_YEAR

    @staticmethod
    def _is_leap(year: int) -> int:
        return int(year % 16 == 0)

    @staticmethod
    def _leap_days_until(years_passed: int):
        return years_passed // 16

    def timestamp(self, year: int, month: int = 1, day: int = 1, hour: int = 0, minute: int = 0, second: int = 0, us: int = 0):
        # The year 1728 is 0C6 in hex, and let's just say that they decided on this year to be their start of timestamps
        # Kargadians landed on Qevenerus on 05/12/1738, so this puts them 10 years ahead of their start of space colonisation
        return self._timestamp_part(self.ymd2ord(year, month, day) - self.ymd2ord(1728, 1, 1), hour, minute, second, us)

    def from_timestamp(self, ts: float):
        days, hour, minute, second, us = self._from_timestamp_part(ts)
        # year, month, day = self.ord2ymd(days)
        # year += 1727
        add = 442219  # 01/01/0001 -> 01/01/1728
        year, month, day = self.ord2ymd(days + add)
        return year, month, day, hour, minute, second, us

    def ord2ymd(self, n: int):
        n = int(n)  # Try to make sure that n is an integer, else this will break...
        n -= 1
        di16 = self._days_since_ad(17)  # days in 16 years
        assert di16 == 16 * 256 + 1
        n16, n = divmod(n, di16)  # The last 16-year cycle
        n1, n = divmod(n, 256)
        year = n16 * 16 + n1 + 1
        if n1 == 16:  # It's actually the last day of the 16-year cycle
            assert n == 0
            return year - 1, 16, 16

        is_leap = n1 == 15
        assert is_leap == self._is_leap(year)

        # Estimate the current month
        # It's simpler in Kargadia's case - each month is 16 days, so I can just easily >> 4 it
        month = (n >> 4) + 1
        preceding = self.days_before_month[month] + (month > 1 and is_leap)
        if preceding > n:
            month -= 1
            preceding -= self.days_in_month[month] + (month == 1 and is_leap)
        n -= preceding
        assert 0 <= n < self._days_in_month(year, month)
        return year, month, n + 1

    def weekday(self, _date: Union[date, datetime]):
        if _date.day == 17:  # Leap day
            day = 8
        else:
            day = _date.day % 8

        # Kargadian weekdays start at 6:00 am or "dawn", rather than midnight
        if _date.hour < 6:
            day -= 1

        if day == -1:
            day = 8 if (self._is_leap(_date.year) and _date.month == 2 and _date.day == 1) else 7
        return day


qevenerus_day = 19.1259928695 * 3600


class QevenerusKa(Earth):
    """ Qevenerus - Kargadian calendar """
    def __init__(self):
        super().__init__()
        self.days_in_month = [-1, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50]
        self.months_in_year = len(self.days_in_month) - 1
        self.days_in_year = sum(self.days_in_month[1:])
        self.days_before_month = [-1]
        dbm = 0
        for dim in self.days_in_month[1:]:
            self.days_before_month.append(dbm)
            dbm += dim
        del dbm, dim
        self.leap_day_month = 1  # The month where leap days are inserted
        self.default_language = "kargadian_kaltarena"

        # The first spring equinox after Kargadians' landing on Qevenerus
        self.start = datetime(1686, 11, 21, 11, 55, 21, tz=timezone.utc)
        self.day_length = qevenerus_day

        self.max_ordinal = self.ymd2ord(MAX_YEAR + 1, 1, 1) - 1  # 31/12/MAX_YEAR
        self.min_ordinal = self.ymd2ord(MIN_YEAR, 1, 1)  # 01/01/MIN_YEAR

    @staticmethod
    def _is_leap(year: int) -> int:
        return 0  # Qevenerus years are never leap

    @staticmethod
    def _leap_days_until(years_passed: int):
        return 0

    def timestamp(self, year: int, month: int = 1, day: int = 1, hour: int = 0, minute: int = 0, second: int = 0, us: int = 0):
        # They started their timestamps from the moment of landing, as Kargadian timestamps began 10 years prior
        return self._timestamp_part(self.ymd2ord(year, month, day) - 1, hour, minute, second, us)

    def from_timestamp(self, ts: float):
        days, hour, minute, second, us = self._from_timestamp_part(ts)
        year, month, day = self.ord2ymd(days)
        return year, month, day, hour, minute, second, us

    def ord2ymd(self, n: int):
        n = int(n)  # Try to make sure that n is an integer, else this will break...
        n -= 1
        n1, n = divmod(n, 800)
        year = n1 + 1
        # Estimate the current month
        month = (n // 50) + 1
        preceding = self.days_before_month[month]
        if preceding > n:
            month -= 1
            preceding -= self.days_in_month[month]
        n -= preceding
        assert 0 <= n < self._days_in_month(year, month)
        return year, month, n + 1

    def weekday(self, _date: Union[date, datetime]):
        day = _date.ordinal % 8

        # Kargadian weekdays start at 6:00 am or "dawn", rather than midnight
        if _date.hour < 6:
            day -= 1
        if day == -1:
            day = 7
        return day


class QevenerusUs(Earth):
    """ Qevenerus - Usturian calendar """
    def __init__(self):
        super().__init__()
        self.days_in_month = [-1, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40]
        self.months_in_year = len(self.days_in_month) - 1
        self.days_in_year = sum(self.days_in_month[1:])
        self.days_before_month = [-1]
        dbm = 0
        for dim in self.days_in_month[1:]:
            self.days_before_month.append(dbm)
            dbm += dim
        del dbm, dim
        self.leap_day_month = 1  # The month where leap days are inserted
        self.default_language = "kargadian_kaltarena"

        # The day Ancient Usturia formed
        self.start = datetime(-2174, 1, 24, 13, 25, 18, 731422, tz=timezone.utc)  # -2174 = 2175 BC
        self.day_length = qevenerus_day

        self.max_ordinal = self.ymd2ord(MAX_YEAR + 1, 1, 1) - 1  # 31/12/MAX_YEAR
        self.min_ordinal = self.ymd2ord(MIN_YEAR, 1, 1)  # 01/01/MIN_YEAR

    @staticmethod
    def _is_leap(year: int) -> int:
        return 0  # Qevenerus years are never leap

    @staticmethod
    def _leap_days_until(years_passed: int):
        return 0

    def timestamp(self, year: int, month: int = 1, day: int = 1, hour: int = 0, minute: int = 0, second: int = 0, us: int = 0):
        # The Usturian timestamp matches the Kargadian timestamp so that the two could actually work together...
        # Let's say that they just made their computers able to handle both calendars
        return self._timestamp_part(self.ymd2ord(year, month, day) - self.ymd2ord(2210, 18, 15), hour, minute, second, us)

    def from_timestamp(self, ts: float):
        days, hour, minute, second, us = self._from_timestamp_part(ts)
        add = 1767894  # 01/01/0001 -> 15/18/2210
        year, month, day = self.ord2ymd(days + add)
        return year, month, day, hour, minute, second, us

    def ord2ymd(self, n: int):
        n = int(n)  # Try to make sure that n is an integer, else this will break...
        n -= 1
        n1, n = divmod(n, 800)
        year = n1 + 1
        # Estimate the current month
        month = (n // 40) + 1
        preceding = self.days_before_month[month]
        if preceding > n:
            month -= 1
            preceding -= self.days_in_month[month]
        n -= preceding
        assert 0 <= n < self._days_in_month(year, month)
        return year, month, n + 1

    def weekday(self, _date: Union[date, datetime]):
        return _date.ordinal % 10


# class timedelta(_datetime.timedelta):
#     # For this class, total_days will show the actual amount of days passed, while days will be only days before prev month (like relative delta)
#     @property
#     def total_days(self):
#         return self.days
timedelta = _datetime.timedelta
tzinfo = _datetime.tzinfo
timezone = _datetime.timezone


def _check_time_fields(hour: int, minute: int, second: int, microsecond: int, fold: int):
    if not 0 <= hour <= 23:
        raise ValueError('hour must be between 0 and 23 (got %d)' % hour)
    if not 0 <= minute <= 59:
        raise ValueError('minute must be between 0 and 59 (got %d)' % minute)
    if not 0 <= second <= 59:
        raise ValueError('second must be between 0 and 59 (got %d)' % second)
    if not 0 <= microsecond <= 999999:
        raise ValueError('microsecond must be between 0 and 999999 (got %d)' % microsecond)
    if fold not in (0, 1):
        raise ValueError('fold must be either 0 or 1 (got %d)' % fold)
    return hour, minute, second, microsecond, fold


# Just raise TypeError if the arg isn't None or a string.
def _check_tzname(name):
    if name is not None and not isinstance(name, str):
        raise TypeError("tzinfo.tzname() must return None or string, not '%s'" % type(name))


def _check_utc_offset(name, offset):
    assert name in ("utcoffset", "dst")
    if offset is None:
        return
    if not isinstance(offset, timedelta):
        raise TypeError("tzinfo.%s() must return None or timedelta, not '%s'" % (name, type(offset)))
    if not -timedelta(1) < offset < timedelta(1):
        raise ValueError("%s()=%s, must be strictly between -timedelta(hours=24) and timedelta(hours=24)" % (name, offset))


def _check_tzinfo_arg(tz):
    if tz is not None and not isinstance(tz, tzinfo):
        raise TypeError("tzinfo argument must be None or of a tzinfo subclass")


def _format_offset(offset):
    s = ""
    if offset is not None:
        if offset.days < 0:  # Somehow this is supposed to return if it's negative
            sign = "-"
            offset *= -1
        else:
            sign = "+"
        hours, ms = divmod(offset, timedelta(hours=1))
        minutes, ss = divmod(ms, timedelta(minutes=1))
        s += "%s%02d:%02d" % (sign, hours, minutes)
        if ss or ss.microseconds:
            s += ":%02d" % ss.seconds
            if ss.microseconds:
                s += ".%06d" % ss.microseconds
    return s


class date(object):
    """ This object holds only date information """
    _year: int
    _month: int
    _day: int

    # Construct a new date object
    def __new__(cls, year: int, month: int = 1, day: int = 1, time_class=Earth):
        """ Construct a new date """
        _time_cls = time_class()
        year, month, day = _time_cls.check_date_fields(year, month, day)
        self = super().__new__(cls)
        self._year = year
        self._month = month
        self._day = day
        self._hashcode = -1
        self._time_cls = _time_cls
        return self

    @classmethod
    def from_timestamp(cls, timestamp: float, time_class=Earth):
        """ Construct a date from timestamp """
        _time_cls = time_class()
        year, month, day, _, _, _, _ = _time_cls.from_timestamp(timestamp)
        return cls(year, month, day, time_class)

    from_ts = from_timestamp

    @classmethod
    def from_datetime(cls, dt: _datetime.date):
        """ Construct a date out of datetime.date """
        return cls(dt.year, dt.month, dt.day, Earth)

    @classmethod
    def today(cls, time_class=Earth):
        """ Return today's date """
        if time_class == Earth:
            today = _datetime.date.today()
            return cls.from_datetime(today)
        else:
            return datetime.now(timezone.utc, Earth).from_earth_time(time_class).date()

    @classmethod
    def from_ordinal(cls, n: int, time_class=Earth):
        """ Construct a date from the ordinal value, where 01/01/0001 is day 1 """
        year, month, day = time_class().ord2ymd(n)
        return cls(year, month, day, time_class)

    @classmethod
    def from_iso(cls, date_string: str, time_class=Earth):
        """ Construct a date from ISO format """
        if not isinstance(date_string, str):
            raise TypeError("date_string must be str")
        data = date_string.split("-")
        if date_string[0] == "-":  # The year is negative
            data.pop(0)  # Remove the empty string as first value of list
            data[0] = "-" + data[0]  # Make the year actually negative
        return cls(int(data[0]), int(data[1]), int(data[2]), time_class)

    # Properties
    @property
    def year(self):
        return self._year

    @property
    def month(self):
        return self._month

    @property
    def day(self):
        return self._day

    @property
    def ordinal(self):
        """ The ordinal value of the date, where 01/01/0001 is day 1 """
        return self._time_cls.ymd2ord(self.year, self.month, self.day)

    @property
    def weekday(self):
        """ Day of the week, where Monday is 0 and Sunday is 6 """
        return self._time_cls.weekday(self)

    @property
    def year_day(self):
        """ Day of the year, where 1st Jan is day 1 """
        return self.ordinal - self._time_cls.ymd2ord(self.year, 1, 1) + 1

    @property
    def time_class(self):
        """ The Time Class used by this date object """
        return self._time_cls.__class__

    def replace(self, year: int = None, month: int = None, day: int = None):
        """ Change the date's values """
        if year is None:
            year = self._year
        if month is None:
            month = self._month
        if day is None:
            day = self._day
        # return type(self)(year, month, day)
        self._time_cls.check_date_fields(year, month, day)
        self._year = year
        self._month = month
        self._day = day

    # Converters
    def to_datetime(self):
        """ Convert to datetime.date """
        if self.time_class == Earth:
            return _datetime.date(self.year, self.month, self.day)
        else:
            raise TimeClassError("Only EarthTime date can be converted into datetime.date")

    def from_earth_time(self, time_class: Type[Earth]) -> date:
        """ Convert from Earth time to a different time class """
        if self.time_class != Earth:
            raise TimeClassError("self does not have EarthTime time class")
        if time_class == Earth:
            return self  # No point in converting to yourself
        return time_class().from_earth_time(datetime.combine(self, time())).date()

    def to_earth_time(self) -> date:
        """ Convert from current time class to Earth time """
        return self._time_cls.to_earth_time(datetime.combine(self, time())).date()

    def __repr__(self):
        """ Convert to full string """
        s = "%s.%s(%d, %d, %d)" % (self.__class__.__module__, self.__class__.__qualname__, self.year, self.month, self.day)
        if self.time_class is not Earth:
            assert s[-1:] == ")"
            s = s[:-1] + ", time_class=%r" % self._time_cls[:-2] + ")"
        return s

    def iso(self):
        """ Return ISO format string (YYYY-MM-DD) """
        return "%04d-%02d-%02d" % (self.year, self.month, self.day)

    __str__ = iso

    def format(self, fmt: str, language: str = None):
        """ Format the value """
        return self._time_cls.str_format(self, fmt, language)

    strftime = format

    def __format__(self, fmt: str):
        if not isinstance(fmt, str):
            raise TypeError("Format must be str, not %s" % type(fmt).__name__)
        if len(fmt) != 0:
            return self.format(fmt)
        return str(self)

    # Comparisons
    def _compare(self, other):
        assert isinstance(other, date)
        if self.time_class != other.time_class:
            raise TimeClassError("Cannot compare: Got two different time classes - %s and %s" % (self.time_class, other.time_class))
        return _compare((self.year, self.month, self.day), (other.year, other.month, other.day))

    def __eq__(self, other):
        if isinstance(other, date):
            return self._compare(other) == 0
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, date):
            return self._compare(other) <= 0
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, date):
            return self._compare(other) < 0
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, date):
            return self._compare(other) >= 0
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, date):
            return self._compare(other) > 0
        return NotImplemented

    # Tiny bytes values to represents this all, yes?
    def _get_state(self) -> bytes:
        year = self._year.to_bytes(3, "big", signed=True)
        month = self._month.to_bytes(1, "big", signed=False)
        day = self._day.to_bytes(1, "big", signed=False)
        return year + month + day

    def __hash__(self):
        if self._hashcode == -1:
            self._hashcode = hash(self._get_state())
        return self._hashcode

    # Calculations
    def __add__(self, other: timedelta) -> date:
        """ Add a timedelta to a date
        date + timedelta """
        # my timedelta will be a _datetime.timedelta, as it's its subclass
        if isinstance(other, _datetime.timedelta):
            days = other.days
            o = self.ordinal + days
            if self._time_cls.min_ordinal < o <= self._time_cls.max_ordinal:
                return type(self).from_ordinal(o, self.time_class)
            raise OverflowError("Result out of range")
        return NotImplemented

    __radd__ = __add__

    @overload
    def __sub__(self, other: date) -> timedelta: ...

    @overload
    def __sub__(self, other: _datetime.date) -> timedelta: ...

    @overload
    def __sub__(self, other: timedelta) -> date: ...

    def __sub__(self, other: Union[date, _datetime.date, timedelta]) -> Union[date, timedelta]:
        """ Subtract two dates, or a timedelta from a date
        date - date, or date - timedelta """
        if isinstance(other, timedelta):
            return self + (other * -1)
        if isinstance(other, date):
            if self.time_class != other.time_class:
                raise TimeClassError("Cannot subtract: Got two different time classes - %s and %s" % (self.time_class, other.time_class))
            d1 = self.ordinal
            d2 = other.ordinal
            return timedelta(days=d1 - d2)
        if isinstance(other, _datetime.date):
            d1 = self.ordinal
            d2 = other.toordinal()
            return timedelta(days=d1 - d2)
        return NotImplemented

    def __rsub__(self, other: Union[date, _datetime.date]) -> timedelta:
        """ Subtract two dates
        other - self """
        if isinstance(other, date):
            if self.time_class != other.time_class:
                raise TimeClassError("Cannot subtract: Got two different time classes - %s and %s" % (self.time_class, other.time_class))
            d1 = other.ordinal
            d2 = self.ordinal
            return timedelta(days=d1 - d2)
        if isinstance(other, _datetime.date):
            d1 = other.toordinal()
            d2 = self.ordinal
            return timedelta(days=d1 - d2)
        return NotImplemented


date.min = date(MIN_YEAR, 1, 1)
date.max = date(MAX_YEAR, 12, 31)
date.resolution = timedelta(days=1)


class time(object):
    _hour: int
    _minute: int
    _second: int
    _microsecond: int
    _tzinfo: Optional[tzinfo]
    _fold: int

    # Construct a new time object
    def __new__(cls, hour: int = 0, minute: int = 0, second: int = 0, microsecond: int = 0, tz: tzinfo = None, fold: int = 0):
        """ Construct a new time object """
        hour, minute, second, microsecond, fold = _check_time_fields(hour, minute, second, microsecond, fold)
        _check_tzinfo_arg(tz)
        self = object.__new__(cls)
        self._hour = hour
        self._minute = minute
        self._second = second
        self._microsecond = microsecond
        if tz is not None:
            self._tzinfo = tz
        else:
            self._tzinfo = timezone.utc
        self._hashcode = -1
        self._fold = fold
        return self

    @classmethod
    def from_iso(cls, time_string):
        if not isinstance(time_string, str):
            raise TypeError("time_string must be str")
        data = time_string.split(":", 2)
        s_data = data[2].split("+")
        if len(s_data) == 1:
            s_data = data[2].split("-")  # See if the offset is just negative
        seconds = float(s_data[0])
        second, us = divmod(seconds, 1)
        if len(s_data) == 2:
            o_data = s_data[1].split(":", 2)
            hours = int(o_data[0])
            minutes = int(o_data[1])
            if len(o_data) == 3:
                seconds = float(o_data[2])
            else:
                seconds = 0
            offset = timedelta(hours=hours, minutes=minutes, seconds=seconds)
            _timezone = _datetime.timezone(offset)
        else:
            _timezone = None
        return cls(int(data[0]), int(data[1]), int(second), int(us * 1000000), _timezone)

    @classmethod
    def from_datetime(cls, dt: _datetime.time):
        """ Convert from datetime.time """
        return cls(dt.hour, dt.minute, dt.second, dt.microsecond, dt.tzinfo, fold=dt.fold)

    @classmethod
    def from_part(cls, day_part: float):
        """ Convert from a day part (e.g. 0.5 for noon) """
        # seconds = int((day_part % 1) * 86400)
        # h, ms = divmod(seconds, 3600)
        # m, s = divmod(ms, 60)
        seconds = (day_part % 1) * 86400
        hour, ms = divmod(seconds, 3600)
        minute, s = divmod(ms, 60)
        second, us = divmod(s, 1)
        return cls(int(hour), int(minute), int(second), int(us * 1000000), timezone.utc)

    # Define properties
    @property
    def hour(self):
        return self._hour

    @property
    def minute(self):
        return self._minute

    @property
    def second(self):
        return self._second

    @property
    def microsecond(self):
        return self._microsecond

    @property
    def tzinfo(self):
        """ Timezone info object """
        return self._tzinfo

    @property
    def fold(self):
        return self._fold

    def replace(self, hour: int = None, minute: int = None, second: int = None, microsecond: int = None, tz: tzinfo = True, *, fold: int = None):
        """ Change the time's values """
        if hour is None:
            hour = self.hour
        if minute is None:
            minute = self.minute
        if second is None:
            second = self.second
        if microsecond is None:
            microsecond = self.microsecond
        if tz is True:
            tz: tzinfo = self.tzinfo
        if fold is None:
            fold = self.fold
        hour, minute, second, microsecond, fold = _check_time_fields(hour, minute, second, microsecond, fold)
        _check_tzinfo_arg(tz)
        self._hour = hour
        self._minute = minute
        self._second = second
        self._microsecond = microsecond
        if tz is None:
            self._tzinfo = timezone.utc
        else:
            self._tzinfo = tz
        self._fold = fold

    # Converters
    def to_datetime(self) -> _datetime.time:
        """ Convert into datetime.time"""
        return _datetime.time(self.hour, self.minute, self.second, self.microsecond, self.tzinfo, fold=self.fold)

    def to_part(self) -> float:
        """ Convert to a day part (e.g. 0.5 for noon) """
        return self.hour / 24 + self.minute / 1440 + self.second / 86400 + self.microsecond / 86400000000

    def _tz_str(self):
        """ Return formatted timezone offset (+xx:xx) or an empty string """
        off = self.utcoffset()
        return _format_offset(off)

    def __repr__(self):
        """ Convert to formal string, for repr() """
        if self._microsecond != 0:
            s = ", %d, %d" % (self._second, self._microsecond)
        elif self._second != 0:
            s = ", %d" % self._second
        else:
            s = ""
        s = "%s.%s(%d, %d%s)" % (self.__class__.__module__, self.__class__.__qualname__, self._hour, self._minute, s)
        if self._tzinfo is not None:
            assert s[-1:] == ")"
            s = s[:-1] + ", tzinfo=%r" % self._tzinfo + ")"
        if self._fold:
            assert s[-1:] == ")"
            s = s[:-1] + ", fold=1)"
        return s

    def iso(self, ms: bool = False, tz: bool = False):
        s = "%02d:%02d:%02d" % (self.hour, self.minute, self.second)
        if ms and self.microsecond:
            s += ".%06d" % self.microsecond
        if tz:
            _tz = self._tz_str()
            if _tz:
                s += _tz
        return s

    __str__ = iso

    def format(self, fmt: str, language: str = None):
        """ Format the value """
        return Earth().str_format(self, fmt, language)

    strftime = format

    def __format__(self, fmt: str):
        if not isinstance(fmt, str):
            raise TypeError("Format must be str, not %s" % type(fmt).__name__)
        if len(fmt) != 0:
            return self.format(fmt)
        return str(self)

    # Comparisons
    def _compare(self, other):
        assert isinstance(other, time)
        tz1, tz2 = self.tzinfo, other.tzinfo
        off1 = off2 = None

        if tz1 == tz2:
            base = True
        else:
            off1 = self.utcoffset()
            off2 = other.utcoffset()
            base = off1 == off2

        if base:
            return _compare((self.hour, self.minute, self.second, self.microsecond), (other.hour, other.minute, other.second, other.microsecond))
        if off1 is None:
            off1 = timedelta()
        if off2 is None:
            off2 = timedelta()
        hm1 = self.hour * 60 + self.minute - off1 // timedelta(minutes=1)
        hm2 = other.hour * 60 + other.minute - off2 // timedelta(minutes=1)
        return _compare((hm1, self.second, self.microsecond), (hm2, other.second, other.microsecond))

    def __eq__(self, other):
        if isinstance(other, time):
            return self._compare(other) == 0
        else:
            return NotImplemented

    def __le__(self, other):
        if isinstance(other, time):
            return self._compare(other) <= 0
        else:
            return NotImplemented

    def __lt__(self, other):
        if isinstance(other, time):
            return self._compare(other) < 0
        else:
            return NotImplemented

    def __ge__(self, other):
        if isinstance(other, time):
            return self._compare(other) >= 0
        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, time):
            return self._compare(other) > 0
        else:
            return NotImplemented

    # Timezone stuff
    def utcoffset(self):
        """ Return the timezone offset as timedelta - positive east of UTC, negative west of UTC """
        if self._tzinfo is None:
            return None
        offset = self._tzinfo.utcoffset(None)
        _check_utc_offset("utcoffset", offset)
        return offset

    def tz_name(self):
        """ Return the timezone name """
        if self._tzinfo is None:
            return None
        name = self._tzinfo.tzname(None)
        _check_tzname(name)
        return name

    def dst(self):
        """ Return 0 if DST is not in effect, or the DST offset (as timedelta positive eastward) if DST is in effect.
        This is purely informational; the DST offset has already been added to
        the UTC offset returned by utcoffset() if applicable, so there's no
        need to consult dst() unless you're interested in displaying the DST info. """
        if self._tzinfo is None:
            return None
        offset = self._tzinfo.dst(None)
        _check_utc_offset("dst", offset)
        return offset


time.min = time(0, 0, 0)
time.max = time(23, 59, 59, 999999)
time.resolution = timedelta(microseconds=1)


class datetime(object):
    _year: int
    _month: int
    _day: int
    _hour: int
    _minute: int
    _second: int
    _microsecond: int
    _tzinfo: Optional[tzinfo]
    _fold: int

    # Construct a new datetime
    def __new__(cls, year: int, month: int = 1, day: int = 1, hour: int = 0, minute: int = 0, second: int = 0, microsecond: int = 0,
                tz: tzinfo = None, time_class=Earth, *, fold: int = 0):
        _time_cls = time_class()
        year, month, day = _time_cls.check_date_fields(year, month, day)
        self = super().__new__(cls)
        self._year = year
        self._month = month
        self._day = day
        self._time_cls = _time_cls

        hour, minute, second, microsecond, fold = _check_time_fields(hour, minute, second, microsecond, fold)
        _check_tzinfo_arg(tz)
        self._hour = hour
        self._minute = minute
        self._second = second
        self._microsecond = microsecond
        if tz is not None:
            self._tzinfo = tz
        else:
            self._tzinfo = timezone.utc
        self._fold = fold
        return self

    @classmethod
    def _from_timestamp(cls, timestamp: float, tz: tzinfo, time_class):
        year, month, day, hour, minute, second, us = time_class.from_timestamp(timestamp)
        result = cls(year, month, day, hour, minute, second, us, timezone.utc, time_class.__class__)
        if tz is not None:
            if type(time_class) == Earth:
                try:
                    _tz_time = result.to_datetime()
                    result += tz.utcoffset(_tz_time)
                except ValueError:
                    result += tz.utcoffset(None)
        return result

    @classmethod
    def from_timestamp(cls, timestamp: float, tz: tzinfo = None, time_class=Earth):
        """ Construct a datetime from a timestamp """
        _time_cls = time_class()
        _check_tzinfo_arg(tz)
        return cls._from_timestamp(timestamp, tz, _time_cls)

    from_ts = from_timestamp

    @classmethod
    def from_datetime(cls, dt: _datetime.datetime):
        """ Construct a datetime from datetime.datetime """
        return cls(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, dt.tzinfo, Earth, fold=dt.fold)

    @classmethod
    def now(cls, tz: tzinfo = timezone.utc, time_class=Earth):
        """ Return the time right now """
        if time_class == Earth:
            # now = _datetime.datetime.utcnow()
            # now = now.replace(tzinfo=timezone.utc)
            # return cls.from_datetime(now).to_timezone(tz)
            now = _datetime.datetime.now(tz)
            return cls.from_datetime(now)
        else:
            _now = _datetime.datetime.now(timezone.utc)
            now = cls.from_datetime(_now)
            return time_class().from_earth_time(now).to_timezone(tz)

    @classmethod
    def combine(cls, _date: date, _time: time, tz: tzinfo = True):
        if not isinstance(_date, date):
            raise TypeError("_date must be a date instance")
        if not isinstance(_time, time):
            raise TypeError("_time must be a time instance")
        if tz is True:
            tz = _time.tzinfo
        return cls(_date.year, _date.month, _date.day, _time.hour, _time.minute, _time.second, _time.microsecond, tz, _date.time_class, fold=_time.fold)

    @classmethod
    def from_part(cls, day_part: float, time_class=Earth):
        """ Convert from a day part (e.g. 0.5 for noon) """
        _ordinal, _part = divmod(day_part, 1)
        _date = date.from_ordinal(int(_ordinal) + 1, time_class)
        _time = time.from_part(_part)
        return cls.combine(_date, _time)

    # Properties
    @property
    def year(self):
        return self._year

    @property
    def month(self):
        return self._month

    @property
    def day(self):
        return self._day

    @property
    def ordinal(self):
        """ The ordinal value of the date, where 01/01/0001 is day 1 """
        return self._time_cls.ymd2ord(self.year, self.month, self.day)

    @property
    def weekday(self):
        """ Day of the week, where Monday is 0 and Sunday is 6 """
        return self._time_cls.weekday(self)

    @property
    def year_day(self):
        """ Day of the year, where 1st Jan is day 1 """
        return self.ordinal - self._time_cls.ymd2ord(self.year, 1, 1) + 1

    @property
    def hour(self):
        return self._hour

    @property
    def minute(self):
        return self._minute

    @property
    def second(self):
        return self._second

    @property
    def microsecond(self):
        return self._microsecond

    @property
    def tzinfo(self) -> Optional[tzinfo]:
        """ Timezone info object """
        return self._tzinfo

    @property
    def fold(self):
        return self._fold

    @property
    def time_class(self):
        """ The Time Class used by this datetime object """
        return self._time_cls.__class__

    @property
    def timestamp(self):
        """ The timestamp of this datetime """
        out = self.copy()
        if self.tzinfo is not None:
            if self.time_class == Earth:
                try:
                    _tz_time = self.to_datetime()
                    out -= out.tzinfo.utcoffset(_tz_time)
                except ValueError:
                    out -= out.tzinfo.utcoffset(None)
        return self._time_cls.timestamp(self.year, self.month, self.day, self.hour, self.minute, self.second, self.microsecond)

    # Methods and Converters
    def replace(self, year: int = None, month: int = None, day: int = None, hour: int = None, minute: int = None, second: int = None,
                microsecond: int = None, tz: Optional[Union[tzinfo, bool]] = True, *, fold: int = None):
        """ Change the datetime's values """
        if year is None:
            year = self._year
        if month is None:
            month = self._month
        if day is None:
            day = self._day
        self._time_cls.check_date_fields(year, month, day)
        self._year = year
        self._month = month
        self._day = day

        if hour is None:
            hour = self.hour
        if minute is None:
            minute = self.minute
        if second is None:
            second = self.second
        if microsecond is None:
            microsecond = self.microsecond
        if tz is True:
            tz = self.tzinfo
        if fold is None:
            fold = self.fold
        hour, minute, second, microsecond, fold = _check_time_fields(hour, minute, second, microsecond, fold)
        _check_tzinfo_arg(tz)
        self._hour = hour
        self._minute = minute
        self._second = second
        self._microsecond = microsecond
        if tz is None:
            self._tzinfo = timezone.utc
        else:
            self._tzinfo = tz
        self._fold = fold

    def copy(self):
        return self.__class__(self.year, self.month, self.day, self.hour, self.minute, self.second, self.microsecond, self.tzinfo, self.time_class, fold=self.fold)

    def to_datetime(self) -> _datetime.datetime:
        """ Convert into datetime.datetime """
        if self.time_class == Earth:
            return _datetime.datetime(self.year, self.month, self.day, self.hour, self.minute, self.second, self.microsecond, self.tzinfo, fold=self.fold)
        else:
            raise TimeClassError("Only EarthTime datetime can be converted into datetime.datetime")

    def to_part(self, day: bool = False, utc: bool = True) -> float:
        """ Convert to a day part (e.g. 0.5 for noon) """
        when = self
        if utc:
            when = when.to_timezone(timezone.utc)
        out = when.hour / 24 + when.minute / 1440 + when.second / 86400 + when.microsecond / 86400000000
        if day:
            out += when.ordinal - 1
        return out

    def date(self):
        """ Return the date part """
        return date(self.year, self.month, self.day, self.time_class)

    def time(self):
        """ Return the time part, with tzinfo as None """
        return time(self.hour, self.minute, self.second, self.microsecond, None)

    def time_tz(self):
        """ Return the time part, with tzinfo """
        return time(self.hour, self.minute, self.second, self.microsecond, self.tzinfo, fold=self.fold)

    def from_earth_time(self, time_class: Type[Earth]) -> datetime:
        """ Convert from Earth time to a different time class """
        if self.time_class != Earth:
            raise TimeClassError("self does not have EarthTime time class")
        if time_class == Earth:
            return self  # No point in converting to yourself
        return time_class().from_earth_time(self)

    def to_earth_time(self) -> datetime:
        """ Convert from current time class to Earth time """
        return self._time_cls.to_earth_time(self)

    def to_timezone(self, tz: tzinfo = timezone.utc) -> datetime:
        if not isinstance(tz, tzinfo):
            raise TypeError("tz argument must be an instance of tzinfo")

        if tz is self.tzinfo:
            return self

        try:
            _tz_time = self.to_datetime()
            offset = self.tzinfo.utcoffset(_tz_time)
            tz_offset = tz.utcoffset(_tz_time)
        except (ValueError, TimeClassError):
            offset = self.tzinfo.utcoffset(None)
            tz_offset = tz.utcoffset(None)
        if offset is None:
            offset = timedelta(seconds=0)
        if tz_offset is None:
            tz_offset = timedelta(seconds=0)

        new_time = self - offset  # + (offset * -1)  # .replace(tzinfo=tz)
        new_time.replace(tz=tz)
        new_time += tz_offset
        return new_time

    as_timezone = as_tz = to_tz = to_timezone

    def iso(self, sep: str = "T", ms: bool = False, tz: bool = False):
        date_part = self.date().iso()
        time_part = self.time_tz().iso(ms, tz)
        return "%s%s%s" % (date_part, sep, time_part)

    def __repr__(self):
        stuff = [self.year, self.month, self.day, self.hour, self.minute, self.second, self.microsecond]
        if stuff[-1] == 0:  # if microsecond == 0
            stuff.pop(-1)
        if stuff[-1] == 0:  # if second == 0
            stuff.pop(-1)
        s = "%s.%s(%s)" % (self.__class__.__module__, self.__class__.__qualname__, ", ".join(map(str, stuff)))
        if self._tzinfo is not None:
            assert s[-1:] == ")"
            s = s[:-1] + ", tzinfo=%r" % self._tzinfo + ")"
        if self.time_class is not Earth:
            assert s[-1:] == ")"
            s = s[:-1] + ", time_class=%s" % repr(self._time_cls)[:-2] + ")"
        if self._fold:
            assert s[-1:] == ")"
            s = s[:-1] + ", fold=1)"
        return s

    def __str__(self):
        """ Convert to string """
        return self.iso(sep=" ", ms=False, tz=False)

    def format(self, fmt: str, language: str = None):
        """ Format the value """
        return self._time_cls.str_format(self, fmt, language)

    strftime = format

    def __format__(self, fmt: str):
        if not isinstance(fmt, str):
            raise TypeError("Format must be str, not %s" % type(fmt).__name__)
        if len(fmt) != 0:
            return self.format(fmt)
        return str(self)

    # Timezone stuff
    def utcoffset(self):
        """ Return the timezone offset as timedelta - positive east of UTC, negative west of UTC """
        if self._tzinfo is None:
            return None
        try:
            _tz_time = self.to_datetime()
            offset = self._tzinfo.utcoffset(_tz_time)
        except ValueError:
            offset = self._tzinfo.utcoffset(None)
        _check_utc_offset("utcoffset", offset)
        return offset

    def tz_name(self):
        """ Return the timezone name """
        if self._tzinfo is None:
            return None
        try:
            _tz_time = self.to_datetime()
            name = self._tzinfo.tzname(_tz_time)
        except ValueError:
            name = self._tzinfo.tzname(None)
        _check_tzname(name)
        return name

    def dst(self):
        """ Return 0 if DST is not in effect, or the DST offset (as timedelta positive eastward) if DST is in effect.
        This is purely informational; the DST offset has already been added to
        the UTC offset returned by utcoffset() if applicable, so there's no
        need to consult dst() unless you're interested in displaying the DST info. """
        if self._tzinfo is None:
            return None
        try:
            _tz_time = self.to_datetime()
            offset = self._tzinfo.dst(_tz_time)
        except ValueError:
            offset = self._tzinfo.dst(None)
        _check_utc_offset("dst", offset)
        return offset

    # Comparisons
    def _compare(self, other):
        assert isinstance(other, datetime)
        if self.time_class != other.time_class:
            raise TimeClassError("Cannot compare: Got two different time classes - %s and %s" % (self.time_class, other.time_class))

        tz1, tz2 = self.tzinfo, other.tzinfo
        # off1 = off2 = None

        if tz1 == tz2:
            base = True
        else:
            off1 = self.utcoffset()
            off2 = other.utcoffset()
            base = off1 == off2

        if base:
            return _compare((self.year, self.month, self.day, self.hour, self.minute, self.second, self.microsecond),
                            (other.year, other.month, other.day, other.hour, other.minute, other.second, other.microsecond))
        # if off1 is None:
        #     off1 = timedelta()
        # if off2 is None:
        #     off2 = timedelta()
        # hm1 = self.hour * 60 + self.minute - off1 // timedelta(minutes=1)
        # hm2 = other.hour * 60 + other.minute - off2 // timedelta(minutes=1)
        diff = self - other
        if diff.days < 0:
            return -1
        return diff and 1 or 0  # I have no idea how this works, but it's what datetime has

    def __eq__(self, other):
        if isinstance(other, datetime):
            return self._compare(other) == 0
        elif not isinstance(other, date):
            return NotImplemented
        else:
            return False

    def __le__(self, other):
        if isinstance(other, datetime):
            return self._compare(other) <= 0
        elif not isinstance(other, date):
            return NotImplemented
        else:
            _compare_error(self, other)

    def __lt__(self, other):
        if isinstance(other, datetime):
            return self._compare(other) < 0
        elif not isinstance(other, date):
            return NotImplemented
        else:
            _compare_error(self, other)

    def __ge__(self, other):
        if isinstance(other, datetime):
            return self._compare(other) >= 0
        elif not isinstance(other, date):
            return NotImplemented
        else:
            _compare_error(self, other)

    def __gt__(self, other):
        if isinstance(other, datetime):
            return self._compare(other) > 0
        elif not isinstance(other, date):
            return NotImplemented
        else:
            _compare_error(self, other)

    # Addition and Subtraction
    def __add__(self, other: timedelta) -> datetime:
        """ datetime + timedelta """
        if not isinstance(other, timedelta):
            return NotImplemented
        delta = timedelta(days=self.ordinal, hours=self.hour, minutes=self.minute, seconds=self.second, microseconds=self.microsecond)
        delta += other
        hour, ms = divmod(delta.seconds, 3600)
        minute, second = divmod(ms, 60)
        _date = date.from_ordinal(delta.days, self.time_class)
        self._time_cls.check_date_fields(_date.year, _date.month, _date.day)
        _time = time(hour, minute, second, delta.microseconds, self.tzinfo)
        return type(self).combine(_date, _time)
        # if self._time_cls.min_ordinal < delta.days <= self._time_cls.max_ordinal:
        #     return type(self).combine(date.from_ordinal(delta.days, self.time_class), time(hour, minute, second, delta.microseconds, self.tzinfo))
        # raise OverflowError("Result out of range")

    __radd__ = __add__

    @overload
    def __sub__(self, other: datetime) -> timedelta: ...

    @overload
    def __sub__(self, other: _datetime.datetime) -> timedelta: ...

    @overload
    def __sub__(self, other: timedelta) -> datetime: ...

    def __sub__(self, other: Union[datetime, _datetime.datetime, timedelta]) -> Union[datetime, timedelta]:
        """ datetime - datetime or datetime - timedelta """
        if isinstance(other, timedelta):
            return self + (other * -1)
        if isinstance(other, datetime):
            if self.time_class != other.time_class:
                raise TimeClassError("Cannot subtract: Got two different time classes - %s and %s" % (self.time_class, other.time_class))
            days2 = other.ordinal
        elif isinstance(other, _datetime.datetime):
            days2 = other.toordinal()
        else:
            return NotImplemented
        days1 = self.ordinal
        secs1 = self.second + self.minute * 60 + self.hour * 3600
        secs2 = other.second + other.minute * 60 + other.hour * 3600
        base = timedelta(days=days1 - days2, seconds=secs1 - secs2, microseconds=self.microsecond - other.microsecond)
        if self.tzinfo is other.tzinfo:
            return base
        off1 = self.utcoffset()
        off2 = other.utcoffset()
        if off1 == off2:
            return base
        if off1 is None:
            off1 = timedelta()
        if off2 is None:
            off2 = timedelta()
        return base + off2 - off1

    def __rsub__(self, other: Union[datetime, _datetime.datetime]) -> timedelta:
        """ datetime - datetime; other - self """
        if isinstance(other, datetime):
            if self.time_class != other.time_class:
                raise TimeClassError("Cannot subtract: Got two different time classes - %s and %s" % (self.time_class, other.time_class))
            days1 = other.ordinal
        elif isinstance(other, _datetime.datetime):
            days1 = other.toordinal()
        else:
            return NotImplemented
        days2 = self.ordinal
        secs1 = other.second + other.minute * 60 + other.hour * 3600
        secs2 = self.second + self.minute * 60 + self.hour * 3600
        base = timedelta(days=days1 - days2, seconds=secs1 - secs2, microseconds=self.microsecond - other.microsecond)
        if self.tzinfo is other.tzinfo:
            return base
        off1 = other.utcoffset()
        off2 = self.utcoffset()
        if off1 == off2:
            return base
        if off1 is None:
            off1 = timedelta()
        if off2 is None:
            off2 = timedelta()
        return base + off2 - off1


datetime.min = datetime(MIN_YEAR, 1, 1)
datetime.max = datetime(MAX_YEAR, 12, 31, 23, 59, 59, 999999)
datetime.resolution = timedelta(microseconds=1)
