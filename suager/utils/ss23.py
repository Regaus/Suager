import random
from datetime import datetime, timezone

from core.utils import time, bases


class KargadiaTime:
    def __init__(self, year: int, month: int, day: int, hour: int, minute: int, second: int, ds: int = 1, tzn: str = "ST"):
        self.year = year
        self.month = month
        self.day = day
        if self.month == 17:
            self.month = 16
            self.day = 33
        self.hour = hour
        self.minute = minute
        self.second = second
        self.tz_name = tzn
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
        return f"{dn}{self.day:02d}{mn}{self.year} RE, {self.hour:02d}:{self.minute:02d}:{self.second:02d}{f' {self.tz_name}' if tz else ''}"

    def str_hex(self, dow: bool = False, month: bool = True, tz: bool = False):
        dn = f"{self.day_name}, " if dow else ""
        mn = f" {self.months[self.month - 1]} " if month else f"/{self.month:02X}/"
        return f"{dn}{self.day:02X}{mn}{self.year:X} RE, {self.hour:02X}:{self.minute:02X}:{self.second:02X}{f' {self.tz_name}' if tz else ''}"

    def str_full(self):
        return f"{self.str_dec()} ({self.str_hex()})"


def time_kargadia(when: datetime = None, tz: float = 0, tzn: str = "ST"):
    irl = when or time.now(None)
    start = datetime(1970, 1, 1, 6, 30, tzinfo=timezone.utc)
    total = (irl - start).total_seconds()
    ml = 32  # month length
    year = 1060
    day_length = 37.49865756 * 3600
    days = total / day_length
    days += tz / 32
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
        if dl >= yl:
            year += 1
            dl -= yl
        else:
            break
    month, day = divmod(dl, ml)
    return KargadiaTime(year, month + 1, day + 1, h, m, s, _ds, tzn)
    # return f"{day_name}, {day + 1:02d}/{month + 1:02d}/{year}, {h:02d}:{m:02d}:{s:02d} ({day + 1:02X} {months[month]} {year:X} RE, {h:02X}:{m:02X}:{s:02X})"


def date_kargadia(when: datetime = None, tz: float = 0, tzn: str = "ST"):
    return time_kargadia(when, tz, tzn).str_full()


class ZeivelaTime:
    def __init__(self, year: int, month: int, day: int, hour: int, minute: int, second: int, ds: int = 1, tzn: str = "ZST"):
        self.year = year
        self.month = month
        self.day = day
        if self.month == 13:
            self.month = 12
            self.day = 37
        self.hour = hour
        self.minute = minute
        self.second = second
        self.tz_name = tzn
        wl = 6  # week length
        dow = ds % wl
        weekdays = ["Kavderus", "Henrin", "Tahnall", "Hintarin", "Kaasdehte", "Vinhirus"]
        self.day_name = f"Keina te {weekdays[dow]}"
        self.months = ["Tinnerus", "Hednerus", "Hainerus", "Katterus", "Neiteverus", "Zeivellus",
                       "Pentallus", "Tebarrus", "Faitualus", "Sitterus", "Kaggarus", "Maivarus"]

    def str_dec(self, dow: bool = True, month: bool = False, tz: bool = True):
        dn = f"{self.day_name}, " if dow else ""
        mn = f" Vaiku te {self.months[self.month - 1]} " if month else f"/{self.month:02d}/"
        return f"{dn}{self.day:02d}{mn}{self.year} ZE, {self.hour:02d}:{self.minute:02d}:{self.second:02d}{f' {self.tz_name}' if tz else ''}"

    def str_sen(self, dow: bool = False, month: bool = True, tz: bool = False):
        dn = f"{self.day_name}, " if dow else ""
        mn = f" Vaiku te {self.months[self.month - 1]} " if month else f"/{bases.base_6(self.month)}/"
        h, m, s = bases.base_6(self.hour).zfill(2), bases.base_6(self.minute).zfill(2), bases.base_6(self.second).zfill(2)
        return f"{dn}{bases.base_6(self.day)}{mn}{bases.base_6(self.year)} ZE, {h}:{m}:{s}{f' {self.tz_name}' if tz else ''}"

    def str_full(self):
        return f"{self.str_dec()} ({self.str_sen()})"


def time_zeivela(when: datetime = None, tz: float = 0, tzn: str = "ZST"):
    irl = when or time.now(None)
    start = datetime(1970, 4, 1, tzinfo=timezone.utc)
    total = (irl - start).total_seconds()
    ml = 36  # month length
    year = 2774
    day_length = 27.12176253 * 3600
    days = total / day_length
    days += tz / 36
    secs = (days % 1) * day_length
    kdl = 36 ** 3  # Local day length
    ksl = day_length / kdl  # Second length compared to real time
    ks = int(secs / ksl)
    h, ms = divmod(ks, 36 * 36)
    m, s = divmod(ms, 36)
    dl = int(days)
    _ds = dl
    while True:
        yl = 433 if year % 3 == 0 else 432
        if dl >= yl:
            year += 1
            dl -= yl
        else:
            break
    month, day = divmod(dl, ml)
    return ZeivelaTime(year, month + 1, day + 1, h, m, s, _ds, tzn)


def date_zeivela(when: datetime = None, tz: float = 0, tzn: str = "ZST"):
    return time_zeivela(when, tz, tzn).str_full()


class KaltarynaTime:
    def __init__(self, year: int, month: int, day: int, hour: int, minute: int, second: int, ds: int = 1, tzn: str = "AST"):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.tz_name = tzn
        wl = 8  # week length
        dow = ds % wl
        weekdays = ["Senka", "Navaite", "Sanvakkar", "Havasleisar", "Teinear", "Kannaite", "Suvaker", "Shira"]
        self.day_name = f"Sea af {weekdays[dow]}"
        self.months = ["Senka", "Shira", "Kanvu", "Shokka", "Nurikkus", "Aija", "Kiommi", "Nuutal",
                       "Baaser", "Finkal", "Suvaker", "Kitte", "Dekear", "Kaltanner", "Kaiveal", "Karasmar"]

    def str_dec(self, dow: bool = True, month: bool = False, tz: bool = True):
        dn = f"{self.day_name}, " if dow else ""
        mn = f" Sakku af {self.months[self.month - 1]} " if month else f"/{self.month:02d}/"
        return f"{dn}{self.day:02d}{mn}{self.year} KT, {self.hour:02d}:{self.minute:02d}:{self.second:02d}{f' {self.tz_name}' if tz else ''}"

    def str_hex(self, dow: bool = False, month: bool = True, tz: bool = False):
        dn = f"{self.day_name}, " if dow else ""
        mn = f" Sakku af {self.months[self.month - 1]} " if month else f"/{self.month:02X}/"
        return f"{dn}{self.day:02X}{mn}{self.year:X} KT, {self.hour:02X}:{self.minute:02X}:{self.second:02X}{f' {self.tz_name}' if tz else ''}"

    def str_full(self):
        return f"{self.str_dec()} ({self.str_hex()})"


def time_kaltaryna(when: datetime = None, tz: float = 0, tzn: str = "KST"):
    irl = when or time.now(None)
    start = datetime(1686, 11, 21, 11, 55, 21, tzinfo=timezone.utc)
    total = (irl - start).total_seconds()
    ml = 50  # month length
    year = 1
    day_length = 51.642812 * 3600
    days = total / day_length
    days += tz / 64
    secs = (days % 1) * day_length
    kdl = 64 ** 3  # Local day length
    ksl = day_length / kdl  # Second length compared to real time
    ks = int(secs / ksl)
    h, ms = divmod(ks, 64 * 64)
    m, s = divmod(ms, 64)
    dl = int(days)
    _ds = dl
    while True:
        yl = 800
        if dl >= yl:
            year += 1
            dl -= yl
        else:
            break
    month, day = divmod(dl, ml)
    return KaltarynaTime(year, month + 1, day + 1, h, m, s, _ds, tzn)


def date_kaltaryna(when: datetime = None, tz: float = 0, tzn: str = "KST"):
    return time_kaltaryna(when, tz, tzn).str_full()


class Weather:
    def __init__(self, city_name: str):
        self.city = city_name
        self.planet = self.get_planet()
        self.lat, self.long, self.tz_name = self.get_location()
        self.tz = round(round(self.long / (180 / 32)) / 2, 1)
        self.time = self.get_time()
        self.time_out = self.time.str_dec(False, False, True)
        self.weather_patterns = self.get_patterns()
        self.temperature, self.is_raining, self.wind_speed = self.get_weather()

    def get_planet(self):
        kargadia = ["Sentagar", "Sentatebaria", "Kitnagar", "Murrangar", "Peaskar"]
        if self.city in kargadia:
            return "Kargadia"

    def get_location(self):
        places = {
            "Sentagar": [343, 486, "ST"],
            "Sentatebaria": [495, 727, "TBT"],
            "Kitnagar": [1294, 573, "KT"],
            "Murrangar": [371, 11, "MT"],
            "Peaskar": [218, 336, "PT"],
        }
        offset = 0
        if self.planet == "Kargadia":
            offset = -343
        y, x, tzn = places[self.city]
        y += offset
        if y < 0:
            y += 1800
        long = y / 5
        if long > 180:
            long = -(180 - long)
        lat = x / 5
        if lat < 90:
            lat = 90 - lat
        else:
            lat = -(lat - 90)
        return round(lat, 1), round(long, 1), tzn

    def get_time(self):
        if self.planet == "Kargadia":
            return time_kargadia(tz=self.tz, tzn=self.tz_name)
        if self.planet == "Zeivela":
            return time_zeivela(tz=self.tz, tzn=self.tz_name)
        if self.planet == "Kaltaryna":
            return time_kaltaryna(tz=self.tz, tzn=self.tz_name)

    def get_patterns(self):
        return {
            "Kargadia": {
                "Sentagar": {
                    "temperature_low_day": [31, 29, 26, 21, 17, 15, 16, 18, 20, 22, 26, 27, 29, 30, 31, 32],
                    "temperature_high_day": [37, 36, 34, 30, 26, 22, 24, 27, 30, 32, 33, 35, 37, 40, 42, 39],
                    "temperature_low_night": [24, 23, 21, 17, 14, 11, 13, 16, 17, 18, 21, 24, 25, 26, 26, 25],
                    "temperature_high_night": [32, 30, 28, 24, 20, 17, 18, 21, 23, 24, 29, 30, 32, 33, 33, 33],
                    "rain_chance": [61, 52, 50, 47, 25, 17, 22, 37, 42, 47, 52, 63, 92, 90, 79],
                    "winds_mult": 0.47
                }
            }
        }[self.planet][self.city]

    def get_weather(self):
        day_length = 36 if self.planet == "Zeivela" else 64 if self.planet == "Kaltaryna" else 32
        quarter = day_length // 4
        is_day = self.time.hour in range(quarter, quarter * 3)
        if is_day:
            ranges = self.weather_patterns["temperature_low_day"], self.weather_patterns["temperature_high_day"]
        else:
            ranges = self.weather_patterns["temperature_low_night"], self.weather_patterns["temperature_high_night"]
        month = self.time.month
        _low, _high = ranges
        low, high = _low[month], _high[month]
        rain_chance = self.weather_patterns["rain_chance"][month]
        wind_low, wind_high = [val * self.weather_patterns["winds_mult"] for val in [20, 40]]
        seed = month * 100 + self.time.day
        random.seed(seed)
        overall_temp = random.uniform(low, high)
        overall_wind = random.uniform(wind_low, wind_high)
        hour_float = (self.time.hour - 1) + self.time.minute / day_length
        multipliers = [1.07, 1.01, 0.96, 0.92, 0.88, 0.84, 0.83, 0.87, 0.91, 0.95, 0.98, 1.02, 1.06, 1.1, 1.13, 1.16, 1.14, 1.11, 1.09, 1.08]
        part = int(hour_float / day_length * 20)
        is_raining = rain_chance > random.random()
        return overall_temp * multipliers[part], is_raining, overall_wind * random.uniform(0.9, 1.1)
