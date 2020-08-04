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
        self.months = ["Senkannar", "Shirannar", "Kanvamar", "Árkanmar", "Nurinnar", "Aijamar", "Kíonnar", "Gairannar",
                       "Bassemar", "Finkannar", "Suvannar", "Kittannar", "Semarmar", "Haltannar", "Kaivynnar", "Kärasmar"]

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
        weekdays = ["Vantakku", "Vantallu", "Hennettu", "Kaiva", "Leiva", "Kahkatu"]
        self.day_name = f"Keina te {weekdays[dow]}"
        if self.day == 37:
            self.day_name = f"Keine te Vantakku-Tahnall"
        self.months = ["Vinhirus", "Kavderus", "Tinnerus", "Hednerus", "Hainerus", "Katterus",
                       "Neiteverus", "Zeivellus", "Pentallus", "Tebarrus", "Faitualus", "Kaggarus"]

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
        weekdays = ["Senka", "Navate", "Sanvar", "Havas-Lesar", "Tenear", "Kannate", "Suvaker", "Shira"]
        day_part = "Sea" if self.hour in range(12, 52) else "Tea"
        self.day_name = f"{day_part} af {weekdays[dow]}"
        self.months = ["Senka", "Shira", "Kanvarus", "Arkanéda", "Nurus", "Aii", "Kiona", "Gairnar",
                       "Basrus", "Finkal", "Suvaker", "Kitta", "Sémartar", "Kaltnar", "Kaiveal", "Karasnar"]

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
        long = y / 5
        if long > 180:
            long = -(360 - long)
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
                },
                "Sentatebaria": {
                    "temperature_low_day": [-4, -7, -13, -17, -22, -27, -28, -26, -21, -17, -12, -6, 1, 7, 12, 5],
                    "temperature_high_day": [6, 0, -4, -11, -16, -19, -21, -17, -12, -8, -4, -1, 12, 18, 22, 14],
                    "temperature_low_night": [-11, -19, -23, -30, -31, -36, -41, -40, -27, -21, -17, -11, -7, -2, 7, -1],
                    "temperature_high_night": [1, -6, -12, -14, -19, -25, -26, -24, -17, -15, -11, -5, -1, 5, 7, 2],
                    "rain_chance": [37, 31, 21, 17, 9, 6, 5, 8, 11, 13, 17, 27, 33, 40, 39],
                    "winds_mult": 0.81
                },
                "Kitnagar": {
                    "temperature_low_day": [11, 7, 3, -1, -7, -14, -13, -10, -2, 4, 7, 11, 21, 20, 19, 17],
                    "temperature_high_day": [17, 14, 9, 5, -1, -7, -10, -4, 6, 11, 18, 21, 27, 30, 30, 29],
                    "temperature_low_night": [4, 1, -5, -10, -15, -20, -21, -14, -6, -1, 1, 5, 9, 10, 11, 7],
                    "temperature_high_night": [12, 9, 5, 0, -4, -10, -9, -9, -5, 6, 10, 15, 20, 21, 20, 17],
                    "rain_chance": [37, 31, 21, 17, 9, 6, 5, 8, 11, 13, 17, 27, 33, 40, 39],
                    "winds_mult": 0.81
                },
                "Murrangar": {
                    "temperature_low_day": [-51, -47, -34, -30, -27, -25, -24, -24, -27, -31, -37, -41, -50, -57, -63, -57],
                    "temperature_high_day": [-42, -33, -27, -24, -21, -20, -19, -20, -22, -25, -30, -33, -41, -47, -51, -49],
                    "temperature_low_night": [-52, -47, -36, -32, -30, -27, -26, -25, -29, -33, -40, -43, -51, -60, -63, -59],
                    "temperature_high_night": [-43, -35, -29, -26, -22, -21, -20, -20, -22, -26, -31, -34, -42, -49, -52, -50],
                    "rain_chance": [11, 14, 16, 20, 21, 22, 21, 20, 19, 17, 14, 13, 9, 6, 4, 7],
                    "winds_mult": 1.27
                },
                "Peaskar": {
                    "temperature_low_day": [27, 32, 37, 42, 45, 50, 54, 53, 45, 37, 27, 25, 22, 19, 16, 22],
                    "temperature_high_day": [32, 41, 47, 50, 53, 57, 61, 63, 57, 47, 39, 32, 29, 27, 24, 29],
                    "temperature_low_night": [13, 19, 20, 21, 23, 27, 24, 21, 19, 18, 14, 12, 9, 7, 7, 10],
                    "temperature_high_night": [27, 33, 38, 43, 46, 48, 50, 48, 42, 39, 30, 28, 24, 20, 21, 26],
                    "rain_chance": [1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 1],
                    "winds_mult": 0.72
                },
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
        low, high = _low[month - 1], _high[month - 1]
        rain_chance = self.weather_patterns["rain_chance"][month - 1]
        wind_low, wind_high = [val * self.weather_patterns["winds_mult"] for val in [20, 40]]
        seed = month * 100 + self.time.day
        random.seed(seed)
        overall_temp = random.uniform(low, high)
        overall_wind = random.uniform(wind_low, wind_high)
        hour_float = (self.time.hour - 1) + self.time.minute / day_length
        # multipliers = [1.07, 1.01, 0.96, 0.92, 0.88, 0.84, 0.83, 0.87, 0.91, 0.95, 0.98, 1.02, 1.06, 1.1, 1.13, 1.16, 1.14, 1.11, 1.09, 1.08]
        multipliers = [-3, -4, -5, -6, -7, -7, -4, -2, 0, 2, 3, 4, 6, 7, 8, 9, 8, 6, 3, 0]
        part = int(hour_float / day_length * 20)
        random.seed(seed * day_length ** 2 + hour_float * day_length)
        wind_speed = overall_wind * random.uniform(0.9, 1.1)
        is_raining = random.uniform(1, 100) < rain_chance
        additional = multipliers[part] * random.uniform(0.9, 1.1)
        return overall_temp + additional, is_raining, wind_speed
