import random
from datetime import date, datetime, timezone, time as dt_time
from typing import Optional
from math import cos, sin, acos, asin, tan, degrees as deg, radians as rad

import discord

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


def time_zeivela(when: datetime = None, tz: float = 0):
    irl = when or time.now(None)
    start = datetime(60, 12, 5, 3, 40, tzinfo=timezone.utc)
    day_length = 27.12176253 * 3600
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


def time_kargadia(when: datetime = None, tz: float = 0):
    irl = when or time.now(None)
    start = datetime(276, 12, 26, 22, 30, tzinfo=timezone.utc)
    day_length = 37.49865756 * 3600
    month_lengths = [32] * 16
    year, month, day, h, m, s, ds, yd = solar_normal(irl, start, day_length, 512, 513, lambda y: y % 8 == 0, month_lengths, 1, tz)
    # weekdays = [f"{wd}{parts[part]}" for wd in weekdays_sub]
    weekdays = ["Senka", "Navai", "Sanva", "Havlei", "Teine", "Kannai", "Sua", "Shira"]
    months = ["Senkannaran", "Shirannaran", "Kanvamaran", "Arhanmaran", "Nurinnaran", "Aijamaran", "Kionnaran", "Gairannaran",
              "Bassemaran", "Finkannaran", "Suvannaran", "Kittannaran", "Semarmaran", "Haltannaran", "Kaivynnaran", "Kärasmaran"]
    output = TimeSolarNormal(year, month, day, h, m, s, weekdays, months, 8, ds, yd)
    if output.hour < 6:
        output.day_of_week -= 1
    parts = ["tea", "rea", "sea", "vea"]
    part = h // 6
    output.day_name += parts[part]
    return output


def time_kaltaryna(when: datetime = None, tz: float = 0):
    irl = when or time.now(None)
    start = datetime(1686, 11, 21, 11, 55, 21, tzinfo=timezone.utc)
    day_length = 51.642812 * 3600
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
    output.day_name = f"{parts[part]} ida {output.day_name}"
    output.month_name = f"ida Sakku ida {output.month_name}"
    return output


def time_sinvimania(when: datetime = None, tz: float = 0):
    irl = when or time.now(None)
    start = datetime(476, 1, 27, 12, tzinfo=timezone.utc)
    day_length = 11.35289 * 3600
    month_lengths = [31, 31, 31, 31, 31, 32, 31, 31, 31, 31, 31, 32]
    weekdays = ["Placeholder 1", "Placeholder 2", "Placeholder 3", "Placeholder 4", "Placeholder 5", "Placeholder 6"]
    months = ["Month 1", "Month 2", "Month 3", "Month 4", "Month 5", "Month 6", "Month 7", "Month 8", "Month 9", "Month 10", "Month 11", "Month 12"]
    year, month, day, h, m, s, ds, yd = solar_normal(irl, start, day_length, 374, 373, lambda y: y % 5 == 0, month_lengths, 12, tz)
    return TimeSolarNormal(year, month, day, h, m, s, weekdays, months, 6, ds, yd)


def time_hosvalnerus(when: datetime = None, tz: float = 0):
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


places = {
    "Sentagar": ["Kargadia", 343, 486],
    "Sentatebaria": ["Kargadia", 495, 727],
    "Kitnagar": ["Kargadia", 1294, 573],
    "Murrangar": ["Kargadia", 371, 11],
    "Peaskar": ["Kargadia", 218, 336]
}
offsets = {
    "Kargadia": -343
}
times = {
    "Zeivela": time_zeivela,
    "Kargadia": time_kargadia,
    "Kaltaryna": time_kaltaryna,
    "Sinvimania": time_sinvimania,
    "Hosvalnerus": time_hosvalnerus,
}
lengths = {
    "Zeivela": 432,
    "Kargadia": 512,
    "Kaltaryna": 800,
    "Sinvimania": 374,
    "Hosvalnerus": 378,
}
patterns = {
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
        "rain_chance": [37, 31, 21, 17, 9, 6, 5, 5, 8, 11, 13, 17, 27, 33, 40, 39],
        "winds_mult": 0.81
    },
    "Kitnagar": {
        "temperature_low_day": [11, 7, 3, -1, -7, -14, -13, -10, -2, 4, 7, 11, 21, 20, 19, 17],
        "temperature_high_day": [17, 14, 9, 5, -1, -7, -10, -4, 6, 11, 18, 21, 27, 30, 30, 29],
        "temperature_low_night": [4, 1, -5, -10, -15, -20, -21, -14, -6, -1, 1, 5, 9, 10, 11, 7],
        "temperature_high_night": [12, 9, 5, 0, -4, -10, -9, -9, -5, 6, 10, 15, 20, 21, 20, 17],
        "rain_chance": [29, 27, 22, 18, 16, 12, 8, 11, 13, 14, 17, 22, 29, 36, 40, 36],
        "winds_mult": 0.67
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


class PlaceDoesNotExist(general.RegausError):
    def __init__(self, place):
        super().__init__(f"Place not found: {place}")


class Place:
    def __init__(self, place: str):
        self.place = place
        try:
            self.planet, self.lat, self.long = self.get_location()
        except KeyError:
            raise PlaceDoesNotExist(place)
        self.tz = round(round(self.long / (180 / 24)) / 2, 1)
        time_function = times[self.planet]
        self.time = time_function(tz=self.tz)
        self.dt_time = dt_time(self.time.hour, self.time.minute, self.time.second)
        self.sun_data = Sun(self)
        self.weathers = patterns[self.place]

    def get_location(self):
        offset = 0
        planet, x, y = places[self.place]
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
        embed.description = f"Local time: **{self.time.str(dow=False, month=False)}**"
        is_day = self.sun_data.sunrise < self.dt_time < self.sun_data.sunset
        if is_day:
            ranges = self.weathers["temperature_low_day"], self.weathers["temperature_high_day"]
        else:
            ranges = self.weathers["temperature_low_night"], self.weathers["temperature_high_night"]
        month = self.time.month
        _low, _high = ranges
        low, high = _low[month - 1], _high[month - 1]
        rain_chance = self.weathers["rain_chance"][month - 1]
        wind_low, wind_high = [val * self.weathers["winds_mult"] for val in [3, 50]]
        seed = (month * 100 + self.time.day) * 1440
        random.seed(self.place + str(seed))
        temp = random.uniform(low, high)
        wind = random.uniform(wind_low, wind_high)
        hour_part = self.time.hour + self.time.minute / 60
        # Temperature modifiers for every hour
        adds = [-2, -3, -3, -3, -2, -1, 0, 0, 0, 1, 1, 2, 2, 3, 3, 3, 2, 2, 1, 1, 0, 0, -1, -1]
        part = int(hour_part)
        part_1 = hour_part % 1
        part_2 = 1 - part_1
        temp_add = adds[part] * part_1 + adds[(part + 1) % 24] * part_2
        random.seed(self.place + str(int(seed + hour_part * 60)))
        wind *= random.uniform(0.97, 1.03)
        rain = random.randint(0, 100) <= rain_chance
        temp_add *= random.uniform(0.95, 1.05)
        temp_c = round(temp, 1)
        embed.add_field(name="Temperature", value=f"**{temp_c}°C**", inline=False)
        speed_kmh = round(wind, 1)
        speed_mps = round(wind / 3.6, 1)
        if self.planet in ["Kargadia", "Kaltaryna"]:
            kp_base = 0.8192
            # m_name = "ks/h (kp/c)"
            speed_kpc = round(wind / kp_base, 1)
            speed_custom = f" | {speed_kpc} kp/c"
        else:
            speed_custom = ""
        embed.add_field(name="Wind speed", value=f"**{speed_kmh} km/h** | {speed_mps} m/s{speed_custom}", inline=False)
        if rain:
            rain_out = "It's raining" if temp_c > 0 else "It's snowing"
        else:
            rain_out = "Nothing is falling from the sky"
        embed.add_field(name="Precipitation", value=rain_out, inline=False)
        embed.add_field(name="Sunrise", value=self.sun_data.sunrise.isoformat(), inline=True)
        embed.add_field(name="Solar noon", value=self.sun_data.solar_noon.isoformat(), inline=True)
        embed.add_field(name="Sunset", value=self.sun_data.sunset.isoformat(), inline=True)
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
        addition = round(year_day / lengths[self.place.planet] * 365)  # Try to fit the date into a 365-day Earth year
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
