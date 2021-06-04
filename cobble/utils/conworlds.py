from datetime import date, datetime, time as dt_time, timezone
from math import acos, asin, cos, degrees as deg, radians as rad, sin, tan
from typing import Optional

import discord
from numpy import around
from numpy.random import Generator, PCG64

from core.utils import general, time


def solar_normal(now: datetime, start: datetime, day_length: float, days_nl: int, days_leap: int, ly_freq, months: list[int], leap_month: int, tz: float = 0):
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
        year_length = days_leap if ly_freq(year) else days_nl
        if days_left >= year_length:
            year += 1
            days_left -= year_length
        else:
            break
    day = days_left
    month = 1
    leap = ly_freq(year)
    extra = days_leap - days_nl
    if leap:
        months[leap_month - 1] += extra
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
    day_length = 10.0445856 * 3600  # New reduced day lengths while preserving local year length - 28/05/2021
    # day_length = 27.12176253 * 3600
    month_lengths = [36] * 12
    year, month, day, h, m, s, ds, yd = solar_normal(irl, start, day_length, 432, 433, lambda y: y % 3 == 0, month_lengths, 1, tz)
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
    day_length = 13.8876831 * 3600
    # day_length = 37.49865756 * 3600
    month_lengths = [32] * 16
    year, month, day, h, m, s, ds, yd = solar_normal(irl, start, day_length, 512, 513, lambda y: y % 8 == 0, month_lengths, 1, tz)
    # weekdays = [f"{wd}{parts[part]}" for wd in weekdays_sub]
    weekdays, months = [f"{language} not available"] * 8, [f"{language} not available"] * 16
    if language == "rsl-1d":
        weekdays = ["Senka", "Navai", "Sanva", "Havlei", "Teine", "Kannai", "Sua", "Shira"]
        months = ["Senkannaran", "Shirannaran", "Kanvamaran", "Arhanmaran", "Nurinnaran", "Aijamaran", "Kionnaran", "Gairannaran",
                  "Bassemaran", "Finkannaran", "Suvannaran", "Kittannaran", "Semarmaran", "Haltannaran", "Kaivynnaran", "Kärasmaran"]
    elif language == "rsl-1k":
        weekdays = ["Zeiju", "Hau", "Neevu", "Pesku", "Tuhtu", "Sida", "Maa", "Baste"]
        months = ["Senkavan", "Shiravan", "Nuuvan", "Kaivuan", "Antuvan", "Vainaran", "Kallüvan", "Hartuvan",
                  "Raavan", "Nummavan", "Vitteran", "Vaikivan", "Kaivyan", "Kaaratan", "Kiitavan", "Suvakän"]
    elif language == "rsl-1i":
        weekdays = ["Zeiju", "Hau", "Neevu", "Pesku", "Tuhtu", "Sida", "Maa", "Baste"]
        months = ["Senkaan", "Shiraan", "Nuuan", "Kaivuan", "Antuan", "Vainaan", "Kaijuan", "Hartuan",
                  "Raan", "Nummaan", "Vittean", "Vaikian", "Kaivyan", "Karratan", "Kiitaan", "Suvajan"]
    output = TimeSolarNormal(year, month, day, h, m, s, weekdays, months, 8, ds, yd)
    if output.hour < 6:
        output.day_of_week -= 1
    parts = ["tea", "rea", "sea", "vea"]
    part = h // 6
    output.day_name = weekdays[output.day_of_week] + parts[part]
    return output


def time_kaltaryna(when: datetime = None, tz: float = 0):  # 23.6
    irl = when or time.now(None)
    start = datetime(1686, 11, 21, 11, 55, 21, tzinfo=timezone.utc)
    day_length = 19.126 * 3600
    # day_length = 51.642812 * 3600
    month_lengths = [50] * 16
    year, month, day, h, m, s, ds, yd = solar_normal(irl, start, day_length, 800, 800, lambda _: False, month_lengths, 1, tz)
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
    year, month, day, h, m, s, ds, yd = solar_normal(irl, start, day_length, 374, 373, lambda y: y % 5 == 0, month_lengths, 12, tz)
    return TimeSolarNormal(year, month, day, h, m, s, weekdays, months, 6, ds, yd)


def time_hosvalnerus(when: datetime = None, tz: float = 0):  # 24.5
    irl = when or time.now(None)
    start = datetime(171, 7, 1, 7, 30, tzinfo=timezone.utc)
    day_length = 23.7632 * 3600
    month_lengths = [19, 19, 19, 19, 19, 19, 19, 19, 19, 18, 19, 19, 19, 19, 19, 19, 19, 19, 19, 18]
    weekdays = ["Placeholder 1", "Placeholder 2", "Placeholder 3", "Placeholder 4", "Placeholder 5"]
    months = ["Month 1", "Month 2", "Month 3", "Month 4", "Month 5", "Month 6", "Month 7", "Month 8", "Month 9", "Month 10",
              "Month 11", "Month 12", "Month 13", "Month 14", "Month 15", "Month 16", "Month 17", "Month 18", "Month 19", "Month 20"]
    year, month, day, h, m, s, ds, yd = solar_normal(irl, start, day_length, 378, 379, lambda y: y % 2 == 0, month_lengths, 20, tz)
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
        self.day_of_week = self.ds % self.week_length
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


places = {
    "Akkigar": ["Kargadia", 1282, 148],
    "Bylkangar": ["Kargadia", 1184, 665],
    "Erellgar": ["Kargadia", 638, 467],
    "Irtangar": ["Kargadia", 1349, 93],
    "Kanerakainead": ["Kargadia", 367, 51],
    "Kanertebaria": ["Kargadia", 355, 759],
    "Kirtinangar": ["Kargadia", 477, 158],
    "Kitnagar": ["Kargadia", 1496, 620],
    "Lakkeaina": ["Kargadia", 1337, 341],
    "Lersedigar": ["Kargadia", 707, 329],
    "Muruvasaitari": ["Kargadia", 1306, 266],
    "Neikelaa": ["Kargadia", 972, 402],
    "Peaskar": ["Kargadia", 244, 324],
    "Regavall": ["Kargadia", 672, 132],
    "Reggar": ["Kargadia", 591, 148],
    "Sentagar": ["Kargadia", 848, 249],
    "Sentatebaria": ["Kargadia", 298, 811],
    "Tebarimostus": ["Kargadia", 316, 759],
    "Tevivall": ["Kargadia", 490, 294],
    "Vaidoks": ["Kargadia", 1366, 496],
    "Viaransertangar": ["Kargadia", 893, 450],
}
offsets = {
    # "Kargadia": -343,
    "Kargadia": -848,
}
times = {
    "Zeivela": time_zeivela,
    "Kargadia": time_kargadia,
    "Kaltaryna": time_kaltaryna,
    "Sinvimania": time_sinvimania,
    "Hosvalnerus": time_hosvalnerus,
    "Kuastall-11": time_kuastall_11,
}
lengths = {
    "Zeivela": 432 + 1/3,
    "Kargadia": 512.125,
    "Kaltaryna": 800,
    "Sinvimania": 373.8,
    "Hosvalnerus": 378.5,
    "Kuastall-11": 19384.2,
}
month_counts = {
    "Zeivela": 12,
    "Kargadia": 16,
    "Kaltaryna": 16,
    "Sinvimania": 12,
    "Hosvalnerus": 20,
}
weathers = {

}


def random1(low: float = 0.0, high: float = 1.0, seed: int = 0) -> float:
    # state = RandomState(seed)
    state = Generator(PCG64(seed))
    return float(around(state.uniform(low, high, None), 1))


def random2(mean: float, sd: float, seed: int = 0) -> float:
    # state = RandomState(seed)
    state = Generator(PCG64(seed))
    return float(around(state.normal(mean, sd, None), 1))


class PlaceDoesNotExist(general.RegausError):
    def __init__(self, place):
        super().__init__(text=f"Place not found: {place}")


class Place:
    def __init__(self, place: str):
        self.place = place
        try:
            self.planet, self.lat, self.long = self.get_location()
        except KeyError:
            raise PlaceDoesNotExist(place)
        self.tz = round(self.long / (360 / 24))
        # self.tz = round(round(self.long / (180 / 24)) / 2, 1)
        time_function = times[self.planet]
        self.time = time_function(tz=self.tz)
        self.dt_time = dt_time(self.time.hour, self.time.minute, self.time.second)
        self.sun_data = Sun(self)
        try:
            self.weathers = weathers[self.place]
        except KeyError:
            self.weathers = None
        # self.weathers = patterns[self.place]

    def time_info(self):
        _time = f"{self.time.hour:02d}:{self.time.minute:02d}:{self.time.second:02d}"
        _date = f"{self.time.day:02d}/{self.time.month:02d}/{self.time.year}"
        return f"It is currently **{_time}** on **{_date}** in **{self.place}, {self.planet}**"

    def location(self, indent: bool = False):
        lat, long = self.lat, self.long
        n, e = "N" if lat > 0 else "S", "E" if long > 0 else "W"
        if lat < 0:
            lat *= -1
        if long < 0:
            long *= -1
        return f"{lat:>4.1f}°{n}, {long:>5.1f}°{e}" if indent else f"{lat}°{n}, {long}°{e}"

    def get_location(self):
        planet, x, y = places[self.place]
        offset = offsets[planet]
        x += offset
        long = x / 5
        if long > 180:
            long = -(360 - long)
        lat = y / 5
        if lat > 90:
            lat = 90 - lat
        else:
            lat = -(lat - 90)
        return planet, round(lat, 1), round(long, 1)

    def status(self):
        embed = discord.Embed(colour=general.random_colour())
        embed.title = f"Weather in **{self.place}, {self.planet}**"
        embed.description = f"Local time: **{self.time.str(dow=False, month=False)}**\nLocation: {self.location(False)}"
        _months = month_counts[self.planet]
        month = self.time.month
        if self.lat < 0:
            month += _months // 2
            month %= _months
        # spring 1-4, summer 5-8, autumn 9-12, winter 13-16
        _q1, _q2, _q3 = _months // 4, _months // 2, _months // 4 * 3
        if month <= _q1:
            season, s = "spring", 0
        elif _q1 < month <= _q2:
            season, s = "summer", 1
        elif _q2 < month <= _q3:
            season, s = "autumn", 2
        else:
            season, s = "winter", 3
        if self.weathers is not None:
            is_day = self.sun_data.sunrise < self.dt_time < self.sun_data.sunset
            if self.sun_data.sunrise == self.sun_data.sunset == dt_time(0, 0, 0):
                is_day = 1 < month <= _q2
            # if is_day:
            #     ranges = self.weathers["temperature_low_day"], self.weathers["temperature_high_day"]
            # else:
            #     ranges = self.weathers["temperature_low_night"], self.weathers["temperature_high_night"]
            # month = self.time.month
            # _low, _high = ranges
            # low, high = _low[month - 1], _high[month - 1]
            _mean, _sd = self.weathers["temperature_day" if is_day else "temperature_night"][season]
            # wind_low, wind_high = [val * self.weathers["winds_mult"] for val in [3, 50]]
            _seed0 = int(self.place[:8].lower(), base=36)
            _seed1 = self.time.ds * 1440  # Seed the day from 1/1/0001, multiplied by 1440 minutes.
            _seed2 = self.time.hour * 60
            # _seed3 = self.time.minute
            seed = _seed0 + _seed1
            seed2 = seed + _seed2
            # seed3 = seed + _seed3
            # _seed2 = (self.time.month * 100 + self.time.day) * 1440
            # seed = (month * 100 + self.time.day) * 1440
            # random.seed(self.place + str(seed))

            # temp = random.uniform(low, high)
            temp = random2(_mean, _sd, seed)
            # wind = random.uniform(wind_low, wind_high)
            # hour_part = self.time.hour + self.time.minute / 60
            # Temperature modifiers for every hour
            # adds = [-2, -3, -3, -3, -2, -1, 0, 0, 0, 1, 1, 2, 2, 3, 3, 3, 2, 2, 1, 1, 0, 0, -1, -1]
            # part = int(hour_part)
            # part_1 = hour_part % 1
            # part_2 = 1 - part_1
            # temp_add = 1 + (adds[part] * part_1 + adds[(part + 1) % 24] * part_2
            # random.seed(self.place + str(int(seed + hour_part * 60)))
            # wind *= random.uniform(0.97, 1.03)
            # rain = random.randint(0, 100) <= rain_chance
            # temp_add *= random.uniform(0.95, 1.05)
            # temp *= temp_add
            if self.dt_time < self.sun_data.sunrise:
                temp -= 1.75
            elif self.sun_data.sunrise <= self.dt_time < self.sun_data.solar_noon:
                temp -= 0.35
            elif self.sun_data.solar_noon <= self.dt_time < self.sun_data.sunset:
                temp += 1.25
            # No change between sunset and midnight
            temp_c = round(temp, 1)
            embed.add_field(name="Temperature", value=f"**{temp_c}°C**", inline=False)

            wind_mean, wind_sd = self.weathers["wind"]
            wind_max: int = self.weathers["wind_max"]
            wind_storm = self.weathers["wind_storms"]
            wind_base = random2(wind_mean, wind_sd, seed2)
            wind_stormer = random1(0, 1, seed)
            if wind_stormer > 0.9:  # 10% chance of low wind day
                wind_base *= 0.2
            if wind_stormer < wind_storm:
                wind_stormer2 = random1(0, 1, seed - 1)
                if wind_stormer2 < 0.07:
                    wind_base *= 4
                elif 0.07 <= wind_stormer2 < 0.14:
                    wind_base *= 3
                elif 0.14 <= wind_stormer2 < 0.70:  # 56%
                    wind_base *= 2
                else:  # 30%
                    wind_base *= 1.5
            if wind_base > wind_max:
                wind_base = wind_max
            speed_kmh = round(wind_base, 1)
            speed_mps = round(wind_base / 3.6, 1)
            if self.planet in ["Kargadia", "Kaltaryna"]:
                kp_base = 0.8192
                # m_name = "ks/h (kp/c)"
                speed_kpc = round(wind_base / kp_base, 1)
                speed_custom = f" | {speed_kpc} kh/h"
            else:
                speed_custom = ""
            embed.add_field(name="Wind speed", value=f"**{speed_kmh} km/h** | {speed_mps} m/s{speed_custom}", inline=False)

            rain_chance = self.weathers["rain_chance"][s]  # [month - 1]
            rain = random1(0, 100, seed2) <= rain_chance
            if rain:
                if -5 > temp_c > 5:
                    rain_out = "Rain" if random1(0, 1, seed2 - 3) < 0.5 else "Snow"
                else:
                    rain_out = "Rain" if temp_c > 0 else "Snow"
                    thunder_chance = 0
                    if 20 >= temp_c > 25:
                        thunder_chance = 0.3  # 30% chance of thunder while raining at 20-25 degrees
                    elif 25 >= temp_c > 30:
                        thunder_chance = 0.5  # 50% chance of thunder while raining at 25-30 degrees
                    elif temp_c >= 30:
                        thunder_chance = 0.7  # 70% chance of thunder while raining at above 30 degrees
                    if self.place == "Reggar":
                        thunder_chance *= 1.25  # My place is more likely to have thunder instead of normal, boring rain
                    if random1(0, 1, seed2) < thunder_chance:
                        rain_out = "Thunder"
            else:
                rain_out = "Sunny"
                cloud_chance = self.weathers["cloudiness"][s]
                overcast = self.weathers["overcast"][s]
                r = random1(0, 1, seed2)
                if r < cloud_chance:
                    rain_out = "Slightly cloudy"
                    r2 = random1(0, 1, seed2 - 1)
                    r3 = random1(0, 1, seed2 - 2)
                    if r2 < overcast:
                        rain_out = "Overcast"
                    elif r3 < 0.6:  # It's more likely to be cloudy than only slightly cloudy
                        rain_out = "Cloudy"
                # Account for clouds using the cloudiness set
            embed.add_field(name="Sky's Mood", value=rain_out, inline=False)
        else:
            embed.description += "\n\nWeather conditions not available."

        embed.add_field(name="Sunrise", value=self.sun_data.sunrise.isoformat(), inline=True)
        embed.add_field(name="Solar noon", value=self.sun_data.solar_noon.isoformat(), inline=True)
        embed.add_field(name="Sunset", value=self.sun_data.sunset.isoformat(), inline=True)
        embed.set_footer(text=f"Current season: {season.title()}")
        embed.timestamp = time.now(None)
        return embed


class Sun:
    def __init__(self, place: Place):
        self.place = place
        self.solar_noon, self.sunrise, self.sunset = self.get_data()

    def convert_time(self):
        year_start = date(2021, 1, 1)  # Assume it to always be 2021 to not deal with the year day differences shenanigans
        start = year_start.toordinal() - 693595  # To convert it to the calculator's date format
        _time = self.place.time
        year_day = _time.year_day
        addition = round(year_day / lengths[self.place.planet] * 365.25)  # Try to fit the date into a 365-day Earth year
        day_part = (_time.hour - self.place.tz) / 24 + _time.minute / 1440 + _time.second / 86400
        return start + addition + day_part

    @staticmethod
    def time_from_decimal(day_part: float):
        seconds = int((day_part % 1) * 86400)
        h, ms = divmod(seconds, 3600)
        m, s = divmod(ms, 60)
        return dt_time(h, m, s)

    def get_data(self):
        day_number: float = self.convert_time()
        solar_noon_t, sunrise_t, sunset_t = self.calculate(day_number)
        solar_noon = self.time_from_decimal(solar_noon_t)
        sunrise = self.time_from_decimal(sunrise_t)
        sunset = self.time_from_decimal(sunset_t)
        return solar_noon, sunrise, sunset

    def calculate(self, day_number: float):
        """
        Perform the actual calculations for sunrise, sunset and
        a number of related quantities.

        The results are stored in the instance variables
        sunrise_t, sunset_t and solar_noon_t
        """
        longitude = self.place.long  # in decimal degrees, east is positive
        latitude = self.place.lat  # in decimal degrees, north is positive

        j_day = day_number + 2415018.5  # Julian day
        j_cent = (j_day - 2451545) / 36525  # Julian century

        m_anom = 357.52911 + j_cent * (35999.05029 - 0.0001537 * j_cent)
        m_long = 280.46646 + j_cent * (36000.76983 + j_cent * 0.0003032) % 360
        eccent = 0.016708634 - j_cent * (0.000042037 + 0.0001537 * j_cent)
        m_obliq = 23 + (26 + (21.448 - j_cent * (46.815 + j_cent * (0.00059 - j_cent * 0.001813))) / 60) / 60
        obliq = m_obliq + 0.00256 * cos(rad(125.04 - 1934.136 * j_cent))
        vary = tan(rad(obliq / 2)) * tan(rad(obliq / 2))
        seqcent = sin(rad(m_anom)) * (1.914602 - j_cent * (0.004817 + 0.000014 * j_cent)) + sin(rad(2 * m_anom)) * (0.019993 - 0.000101 * j_cent) + sin(
            rad(3 * m_anom)) * 0.000289
        struelong = m_long + seqcent
        sapplong = struelong - 0.00569 - 0.00478 * sin(rad(125.04 - 1934.136 * j_cent))
        declination = deg(asin(sin(rad(obliq)) * sin(rad(sapplong))))

        eqtime = 4 * deg(
            vary * sin(2 * rad(m_long)) - 2 * eccent * sin(rad(m_anom)) + 4 * eccent * vary * sin(rad(m_anom)) * cos(2 * rad(m_long)) - 0.5 * vary
            * vary * sin(4 * rad(m_long)) - 1.25 * eccent * eccent * sin(2 * rad(m_anom)))

        solar_noon_t = (720 - 4 * longitude - eqtime + self.place.tz * 60) / 1440
        try:
            hour_angle = deg(acos(cos(rad(90.833)) / (cos(rad(latitude)) * cos(rad(declination))) - tan(rad(latitude)) * tan(rad(declination))))
            sunrise_t = solar_noon_t - hour_angle * 4 / 1440
            sunset_t = solar_noon_t + hour_angle * 4 / 1440
        except ValueError:
            sunrise_t, sunset_t = 0.0, 0.0  # Probably time so early in the year that there is no way to calculate its sunrise/sunset times
        return solar_noon_t, sunrise_t, sunset_t
