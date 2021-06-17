from datetime import date, time as dt_time
from math import acos, asin, cos, degrees as deg, radians as rad, sin, tan

import discord

from cobble.utils.times import time_hosvalnerus, time_kaltaryna, time_kargadia, time_kuastall_11, time_sinvimania, time_zeivela
from core.utils import general, time

places = {
    "Akkigar":             ["Kargadia", 1282.3, 148.7],
    "Bylkangar":           ["Kargadia", 1184.2, 665.8],
    "Bylkankaldanpeaskat": ["Kargadia", 1361.8, 835.2],
    "Degan Ihat":          ["Kargadia", 1744.6, 788.6],
    "Erellgar":            ["Kargadia",  637.1, 466.9],
    "Iha na Sevarddain":   ["Kargadia", 1352.5, 879.2],
    "Irtangar":            ["Kargadia", 1349.8,  93.4],
    "Kaivus na Advuräin":  ["Kargadia", 1199.0, 730.0],
    "Kanerakainead":       ["Kargadia",  506.0,  50.5],
    "Kanertebaria":        ["Kargadia",  333.5, 758.9],
    "Kiomigar":            ["Kargadia", 1310.8, 166.3],
    "Kirtinangar":         ["Kargadia",  477.3, 158.1],
    "Kitnagar":            ["Kargadia", 1494.9, 620.2],
    "Kunval na Shaivain":  ["Kargadia", 1224.3, 782.1],
    "Lakkeaina":           ["Kargadia", 1337.0, 341.1],
    "Leitagar":            ["Kargadia",  170.0, 157.2],
    "Lersedigar":          ["Kargadia",  707.6, 328.8],
    "Liidennan Koirantat": ["Kargadia",  147.7, 834.5],
    "Lirrinta Teinain":    ["Kargadia",   24.0, 796.3],
    "Muruvasaitari":       ["Kargadia", 1306.6, 264.6],
    "Neikelaa":            ["Kargadia",  971.4, 403.5],
    "Orlagar":             ["Kargadia",  174.3, 171.3],
    "Pakigar":             ["Kargadia",  177.7, 191.2],
    "Peaskar":             ["Kargadia",  244.9, 324.4],
    "Regavall":            ["Kargadia",  654.5, 111.7],  # Original: 672, 132
    "Reggar":              ["Kargadia",  617.1, 147.5],  # Original: 591, 148
    "Seivanlias":          ["Kargadia", 1623.5, 794.2],
    "Senkan Laikadu":      ["Kargadia",  518.9, 269.1],
    "Sentagar":            ["Kargadia",  843.7, 249.3],
    "Sentatebaria":        ["Kargadia",  298.4, 811.4],
    "Shonangar":           ["Kargadia",  173.9, 173.7],
    "Sunovalliat":         ["Kargadia",   87.9, 737.5],
    "Taivead":             ["Kargadia", 1606.7, 800.9],
    "Tebarimostus":        ["Kargadia",  315.4, 759.2],
    "Tentar Hintakadu":    ["Kargadia", 1428.7, 796.7],
    "Tevivall":            ["Kargadia",  491.3, 294.6],
    "Vaidoks":             ["Kargadia", 1366.5, 496.1],
    "Vintelingar":         ["Kargadia",  743.2, 461.7],
    "Virsetgar":           ["Kargadia",  893.8, 450.0],
}
offsets = {
    "Kargadia": -893.8,  # -843.7 | -343
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
    "Zeivela": 212.16,  # 432 + 1/3
    "Kargadia": 256.0625,  # 512.125
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
        self.tz += {
            "Kanertebaria": -1,
            "Regavall": -1,
        }.get(self.place, 0)
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
        n, e = "N" if lat >= 0 else "S", "E" if long >= 0 else "W"
        if lat < 0:
            lat *= -1
        if long < 0:
            long *= -1
        return f"{lat:>4.1f}°{n}, {long:>5.1f}°{e}" if indent else f"{lat:.1f}°{n}, {long:.1f}°{e}"

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
        embed.description = f"Local time: **{self.time.str(dow=False, month=False)}**\n" \
                            f"Time zone: {self.tz}:00 (Real offset {self.long / (360 / 24):.2f} hours)\n" \
                            f"Location: {self.location(False)}"
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
        if self.sun_data.sunrise == "Always daytime today":
            sunrise, noon, sunset = dt_time(0, 0, 0), self.sun_data.solar_noon, dt_time(23, 59, 59)
            is_day = True
            no_sun = True
        elif self.sun_data.sunrise == "Always nighttime today":
            sunrise, noon, sunset = self.sun_data.solar_noon, self.sun_data.solar_noon, self.sun_data.solar_noon
            is_day = False
            no_sun = True
        else:
            sunrise, noon, sunset = self.sun_data.sunrise, self.sun_data.solar_noon, self.sun_data.sunset
            is_day = sunrise < self.dt_time < sunset
            no_sun = False
        if self.weathers is not None:
            # if self.sun_data.sunrise == self.sun_data.sunset == dt_time(0, 0, 0):
            #     is_day = 1 < month <= _q2
            # if is_day:
            #     ranges = self.weathers["temperature_low_day"], self.weathers["temperature_high_day"]
            # else:
            #     ranges = self.weathers["temperature_low_night"], self.weathers["temperature_high_night"]
            # month = self.time.month
            # _low, _high = ranges
            # low, high = _low[month - 1], _high[month - 1]
            if no_sun and not is_day:
                part = "night2"
            else:
                cond1, cond2 = (noon < self.dt_time < dt_time(17), dt_time(17) < self.dt_time < sunset) if sunset > dt_time(17) else \
                    (noon < self.dt_time < sunset, sunset < self.dt_time < dt_time(21))
                if self.dt_time < sunrise:
                    part = "night2"
                elif sunrise < self.dt_time < noon:
                    part = "morning"
                elif cond1:
                    part = "afternoon"
                elif cond2:
                    part = "evening"
                else:
                    part = "night"
            _mean, _sd = self.weathers["temperature"][season][part]
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
            temp = general.random2(_mean, _sd, seed)
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
            # if not (no_sun and not is_day):
            # if self.dt_time < sunrise:
            #     temp -= 1.75
            # elif sunrise <= self.dt_time < noon:
            #     temp -= 0.35
            # elif noon <= self.dt_time < sunset:
            #     temp += 1.25
            # No change between sunset and midnight
            temp_c = round(temp, 1)
            embed.add_field(name="Temperature", value=f"**{temp_c}°C**", inline=False)

            wind_mean, wind_sd = self.weathers["wind"]
            wind_max: int = self.weathers["wind_max"]
            wind_storm = self.weathers["wind_storms"]
            wind_base = general.random2(wind_mean, wind_sd, seed2)
            wind_stormer = general.random1(0, 1, seed)
            if wind_stormer > 0.9:  # 10% chance of low wind day
                wind_base *= 0.2
            if wind_stormer < wind_storm:
                wind_stormer2 = general.random1(0, 1, seed - 1)
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
            rain = general.random1(0, 100, seed2) <= rain_chance
            if rain:
                if -5 > temp_c > 5:
                    rain_out = "Rain" if general.random1(0, 1, seed2 - 3) < 0.5 else "Snow"
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
                    if general.random1(0, 1, seed2) < thunder_chance:
                        rain_out = "Thunder"
            else:
                rain_out = "Sunny"
                cloud_chance = self.weathers["cloudiness"][s]
                overcast = self.weathers["overcast"][s]
                r = general.random1(0, 1, seed2)
                if r < cloud_chance:
                    rain_out = "Slightly cloudy"
                    r2 = general.random1(0, 1, seed2 - 1)
                    r3 = general.random1(0, 1, seed2 - 2)
                    if r2 < overcast:
                        rain_out = "Overcast"
                    elif r3 < 0.6:  # It's more likely to be cloudy than only slightly cloudy
                        rain_out = "Cloudy"
                # Account for clouds using the cloudiness set
            embed.add_field(name="Sky's Mood", value=rain_out, inline=False)
        else:
            embed.description += "\n\nWeather conditions not available."

        if no_sun:
            embed.add_field(name="Sunrise and Sunset", value=self.sun_data.sunrise, inline=True)
            embed.add_field(name="Solar noon", value=noon.isoformat(), inline=True)
        else:
            embed.add_field(name="Sunrise", value=sunrise.isoformat(), inline=True)
            embed.add_field(name="Solar noon", value=noon.isoformat(), inline=True)
            embed.add_field(name="Sunset", value=sunset.isoformat(), inline=True)
        embed.set_footer(text=f"Current season: {season.title()}")
        embed.timestamp = time.now(None)
        return embed


class Sun:
    def __init__(self, place: Place):
        self.place = place
        self.solar_noon, self.sunrise, self.sunset = self.get_data()

    def convert_time(self):
        year_start = date(2021, 1, 1)  # Assume it to always be 2021 to not deal with the year day differences shenanigans
        if self.place.planet in ["Kargadia", "Kaltaryna"]:
            year_start = date(2021, 3, 20)  # Kargadian years start in spring, so make it be the equinox
        start = year_start.toordinal() - 693595  # To convert it to the calculator's date format
        _time = self.place.time
        year_day = _time.year_day  # Amount of days past since New Year
        addition = round(year_day / lengths[self.place.planet] * 365.25)  # Try to fit the date into a 365-day Earth year
        day_part = (_time.hour - self.place.tz) / 24 + _time.minute / 1440 + _time.second / 86400  # How much of the day passed (as a fraction)
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
        if sunrise_t == 2 or sunset_t == 2:
            sunrise, sunset = "Always daytime today", "Always daytime today"
        elif sunrise_t == 3 or sunset_t == 3:
            sunrise, sunset = "Always nighttime today", "Always nighttime today"
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
        seqcent = sin(rad(m_anom)) * (1.914602 - j_cent * (0.004817 + 0.000014 * j_cent)) + sin(rad(2 * m_anom)) * (0.019993 - 0.000101 * j_cent) \
            + sin(rad(3 * m_anom)) * 0.000289
        struelong = m_long + seqcent
        sapplong = struelong - 0.00569 - 0.00478 * sin(rad(125.04 - 1934.136 * j_cent))
        declination = deg(asin(sin(rad(obliq)) * sin(rad(sapplong))))

        eqtime = 4 * deg(vary * sin(2 * rad(m_long)) - 2 * eccent * sin(rad(m_anom)) + 4 * eccent * vary * sin(rad(m_anom)) * cos(2 * rad(m_long))
                         - 0.5 * vary * vary * sin(4 * rad(m_long)) - 1.25 * eccent * eccent * sin(2 * rad(m_anom)))

        solar_noon_t = (720 - 4 * longitude - eqtime + self.place.tz * 60) / 1440
        output = cos(rad(90.833)) / (cos(rad(latitude)) * cos(rad(declination))) - tan(rad(latitude)) * tan(rad(declination))
        if -1 <= output <= 1:
            hour_angle = deg(acos(output))
            sunrise_t = solar_noon_t - hour_angle * 4 / 1440
            sunset_t = solar_noon_t + hour_angle * 4 / 1440
        elif output < -1:
            sunrise_t, sunset_t = 2, 2  # Eternal daylight
        else:
            sunrise_t, sunset_t = 3, 3  # Eternal nighttime
        return solar_noon_t, sunrise_t, sunset_t
