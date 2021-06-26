from datetime import time as dt_time
from math import acos, asin, cos, degrees as deg, radians as rad, sin

import discord

from utils.times import time_hosvalnerus, time_kaltaryna, time_kargadia, time_kuastall_11, time_sinvimania, time_zeivela
from utils import general, languages, time

places = {
    "Akkigar":             ["Kargadia", 2602.1,  313.1],
    "Bylkangar":           ["Kargadia", 2382.3, 1311.8],
    "Bylkankaldanpeaskat": ["Kargadia", 2828.2, 1689.3],
    "Bylkanseivanlias":    ["Kargadia", 3283.0, 1553.2],
    "Bylkantaivead":       ["Kargadia", 3274.3, 1564.4],
    "Degan Ihat":          ["Kargadia", 3539.7, 1536.5],
    "Ekspigar":            ["Kargadia", 2560.4,  317.3],
    "Erellgar":            ["Kargadia", 1275.5,  944.2],
    "Erdapeaskat":         ["Kargadia",  504.1, 1140.6],
    "Huntavall":           ["Kargadia", 1545.2, 1529.9],
    "Iha na Sevarddain":   ["Kargadia", 2791.5, 1745.7],
    "Irtangar":            ["Kargadia", 2731.3,  163.8],
    "Kaivus na Advuräin":  ["Kargadia", 2510.2, 1515.1],
    "Kanerakainead":       ["Kargadia", 1015.0,  100.8],
    "Kanertebaria":        ["Kargadia",  666.6, 1515.9],
    "Kiomigar":            ["Kargadia", 2628.7,  349.0],
    "Kirtinangar":         ["Kargadia",  953.3,  319.2],
    "Kitnagar":            ["Kargadia", 3005.5, 1240.0],
    "Kunval na Shaivain":  ["Kargadia", 2623.3, 1624.5],
    "Lakkeaina":           ["Kargadia", 2662.6,  673.6],
    "Leitagar":            ["Kargadia",  335.4,  318.4],
    "Lersedigar":          ["Kargadia", 1417.2,  631.3],
    "Liidennan Koirantat": ["Kargadia",  317.7, 1664.1],
    "Lirrinta Teinain":    ["Kargadia",   25.0, 1598.4],
    "Muruvasaitari":       ["Kargadia", 2614.2,  526.3],
    "Neikelaa":            ["Kargadia", 1960.6,  733.1],
    "Nurvutgar":           ["Kargadia", 2114.1, 1498.2],
    "Orlagar":             ["Kargadia",  342.7,  346.7],
    "Pakigar":             ["Kargadia",  347.5,  376.0],
    "Peaskar":             ["Kargadia",  510.0,  642.4],
    "Regavall":            ["Kargadia", 1295.3,  210.8],
    "Reggar":              ["Kargadia", 1236.4,  300.0],
    "Seankar Kainead":     ["Kargadia", 2670.4, 1800.0],
    "Senkadar Laikadu":    ["Kargadia", 1031.7,  548.6],
    "Sentagar":            ["Kargadia", 1691.2,  495.3],
    "Sentatebaria":        ["Kargadia",  602.3, 1610.5],
    "Shonangar":           ["Kargadia",  344.1,  347.8],
    "Steirigar":           ["Kargadia",  305.2,  538.2],
    "Sunovalliat":         ["Kargadia",  157.2, 1462.2],
    "Tebarimostus":        ["Kargadia",  636.2, 1524.7],
    "Tentar Hintakadu":    ["Kargadia", 2877.7, 1579.9],
    "Tevivall":            ["Kargadia",  982.3,  576.2],
    "Vaidoks":             ["Kargadia", 2754.5,  986.3],
    "Vintelingar":         ["Kargadia", 1485.2,  892.5],
    "Virsetgar":           ["Kargadia", 1800.0,  900.0],

    "Kaltarena":           ["Qevenerus", 2100.0,  655.1],
}
offsets = {
    "Kargadia": -1800.0,  # -843.7 | -343
    "Qevenerus": -2100.0,
}
times = {
    "Zeivela": time_zeivela,
    "Kargadia": time_kargadia,
    "Qevenerus": time_kaltaryna,

    "Sinvimania": time_sinvimania,
    "Hosvalnerus": time_hosvalnerus,
    "Kuastall-11": time_kuastall_11,
}
lengths = {
    "Zeivela": 212.16,  # 432 + 1/3
    "Kargadia": 256.0625,  # 512.125
    "Qevenerus": 800.0,

    "Sinvimania": 373.8,
    "Hosvalnerus": 378.5,
    "Kuastall-11": 19384.2,
}
month_counts = {
    "Zeivela": 12,
    "Kargadia": 16,
    "Qevenerus": 16,

    "Sinvimania": 12,
    "Hosvalnerus": 20,
}
eccentricity = {
    "Zeivela": 0.0271,
    "Kargadia": 0.01721,
    "Qevenerus": 0.0216,
}
axial_tilts = {
    "Zeivela": 23.47,
    "Kargadia": 26.7,
    "Qevenerus": 63.71,
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
            "Kiomigar": -1,
            "Regavall": -1,
        }.get(self.place, 0)
        # self.tz = round(round(self.long / (180 / 24)) / 2, 1)
        time_function = times[self.planet]
        self.time = time_function(tz=self.tz)
        # self.time = time_function(datetime(276, 12, 26, 22, 30, tzinfo=timezone.utc) + timedelta(days=296.3429057999991 * 10000), tz=self.tz)
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
        return f"{lat:>5.2f}°{n}, {long:>6.2f}°{e}" if indent else f"{lat:.2f}°{n}, {long:.2f}°{e}"

    def get_location(self):
        planet, x, y = places[self.place]
        offset = offsets[planet]
        x += offset
        size = 10
        long = x / size
        if long > 180:
            long = -(360 - long)
        lat = y / size
        if lat > 90:
            lat = 90 - lat
        else:
            lat = -(lat - 90)
        return planet, lat, long

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
            sun_output = f"{self.sun_data.sunrise}\nSolar noon: {noon.isoformat()}"
        else:
            daylight = languages.td_int(self.sun_data.daylight_length * 86400, "en", 2, brief=False)
            sun_output = f"`Dawn:       {self.sun_data.dawn.isoformat()}`\n" \
                         f"`Sunrise:    {sunrise.isoformat()}`\n" \
                         f"`Solar noon: {noon.isoformat()}`\n" \
                         f"`Sunset:     {sunset.isoformat()}`\n" \
                         f"`Dusk:       {self.sun_data.dusk.isoformat()}`\n\n" \
                         f"Daylight length: {daylight}"
        embed.add_field(name="About the Sun", value=sun_output, inline=False)

        # if no_sun:
        #     embed.add_field(name="Sunrise and Sunset", value=self.sun_data.sunrise, inline=True)
        #     embed.add_field(name="Solar noon", value=noon.isoformat(), inline=True)
        # else:
        #     embed.add_field(name="Sunrise", value=sunrise.isoformat(), inline=True)
        #     embed.add_field(name="Solar noon", value=noon.isoformat(), inline=True)
        #     embed.add_field(name="Sunset", value=sunset.isoformat(), inline=True)
        embed.set_footer(text=f"Current season: {season.title()}")
        embed.timestamp = time.now(None)
        return embed


def time_from_decimal(day_part: float):
    seconds = int((day_part % 1) * 86400)
    h, ms = divmod(seconds, 3600)
    m, s = divmod(ms, 60)
    return dt_time(h, m, s)


class Sun:
    def __init__(self, place: Place):
        self.place = place
        self.solar_noon, self.sunrise, self.sunset, self.dawn, self.dusk, self.daylight_length = self.get_data()

    def calculate(self):
        _time = self.place.time
        # Total days passed + current part of day, adjusted to central TZ | Started from the dawn of the calendar
        days = _time.ds + (_time.hour - self.place.tz) / 24 + _time.minute / 1440 + _time.second / 86400
        year_length = lengths[self.place.planet]  # Exact length of the year in local solar days
        # year_day = days % year_length  # Current day of the real solar year, without any calendar error
        # solar_day = year_day - self.place.long / 360  # Day adjusted to current longitude

        # Assume that perihelion was exactly at December solstice of year 0, and adjust the amount of days passed to perihelion
        # Perihelion variable shows the mean anomaly of the star at 1/1/0001
        perihelion = {
            "Kargadia": 90,
            "Qevenerus": 90,  # This calculation uses the solar RSL-1h calendar
        }[self.place.planet]
        spin_speed = 360 / year_length  # 1.4059067610446667
        # per_days = (year_day + perihelion) % year_length  # Days passed, adjusted to the perihelion
        mean_anomaly = (perihelion + spin_speed * days) % 360
        # mean_anomaly = 360 * (per_days / year_length)  # Current mean anomaly, in degrees
        coefficient = eccentricity[self.place.planet] * 114.6  # EOC coefficient seems to be approximately 114.6x the eccentricity
        equation_of_centre = coefficient * sin(rad(mean_anomaly))
        ecliptic_longitude = (mean_anomaly + equation_of_centre + 180 + 87) % 360  # degrees
        axial_tilt = axial_tilts[self.place.planet]  # Axial tilt (obliquity) of the planet, in degrees
        declination = deg(asin(sin(rad(ecliptic_longitude)) * sin(rad(axial_tilt))))  # Declination of the sun, degrees
        # (720 - 4 * self.place.long - eq_of_time + self.place.tz * 60) / 1440
        solar_noon_t = 0.5 + 0.0053 * sin(rad(mean_anomaly)) - 0.0069 * sin(rad(2 * ecliptic_longitude)) - self.place.long / 360 + self.place.tz / 24  # Fraction of the day

        def hour_angle_cos(zenith: float):
            return (sin(rad(zenith) - sin(rad(self.place.lat)) * sin(rad(declination)))) / (cos(rad(self.place.lat)) * cos(rad(declination)))

        sunrise_cos = hour_angle_cos(-0.833)
        twilight_cos = hour_angle_cos(-6)
        if -1 <= sunrise_cos <= 1:
            hour_angle = deg(acos(sunrise_cos))
            sunrise_t = solar_noon_t - hour_angle * 4 / 1440
            sunset_t = solar_noon_t + hour_angle * 4 / 1440
            if -1 <= twilight_cos <= 1:
                twilight_ha = deg(acos(twilight_cos))
                dawn_t = solar_noon_t - twilight_ha * 4 / 1440
                dusk_t = solar_noon_t + twilight_ha * 4 / 1440
            else:
                dawn_t, dusk_t = 0, 1
        elif sunrise_cos < -1:
            sunrise_t, sunset_t = 2, 2  # Eternal daylight
            dawn_t, dusk_t = 0, 1
        else:
            sunrise_t, sunset_t = 3, 3  # Eternal nighttime
            dawn_t, dusk_t = 0, 1
        return dawn_t, sunrise_t, solar_noon_t, sunset_t, dusk_t

    def get_data(self):
        dawn_t, sunrise_t, solar_noon_t, sunset_t, dusk_t = self.calculate()
        dawn = time_from_decimal(dawn_t)
        sunrise = time_from_decimal(sunrise_t)
        solar_noon = time_from_decimal(solar_noon_t)
        sunset = time_from_decimal(sunset_t)
        dusk = time_from_decimal(dusk_t)
        if sunrise_t == 2 or sunset_t == 2:
            sunrise, sunset = "Always daytime today", "Always daytime today"
        elif sunrise_t == 3 or sunset_t == 3:
            sunrise, sunset = "Always nighttime today", "Always nighttime today"
        daylight = sunset_t - sunrise_t
        return solar_noon, sunrise, sunset, dawn, dusk, daylight
