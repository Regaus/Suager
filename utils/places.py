from datetime import time as dt_time
from math import acos, asin, cos, degrees as deg, radians as rad, sin, tan

import discord

from utils import general, languages, time, times

places = {
    "Akkigar":             ["Kargadia", 2602.1,  313.1, "Verlennia", "Na Vadenaran Irrat"],
    "Bylkangar":           ["Kargadia", 2382.3, 1311.8, "Tebaria",   "TBL"],
    "Bylkankaldanpeaskat": ["Kargadia", 2828.2, 1689.3, "Tebaria",   "TBL"],
    "Bylkanseivanlias":    ["Kargadia", 3283.0, 1553.2, "Tebaria",   "TBL"],
    "Bylkantaivead":       ["Kargadia", 3274.3, 1564.4, "Tebaria",   "TBL"],
    "Degan Ihat":          ["Kargadia", 3539.7, 1536.5, "Tebaria",   "TBL"],
    "Ekspigar":            ["Kargadia", 2560.4,  317.3, "Verlennia", "Na Vadenaran Irrat"],
    "Erellgar":            ["Kargadia", 1275.5,  944.2, "Erellia",   None],
    "Erdapeaskat":         ["Kargadia",  504.1, 1140.6, "Nittavia",  None],
    "Huntavall":           ["Kargadia", 1545.2, 1529.9, "Tebaria",   "Na Ihat na Iidian"],
    "Iha na Sevarddain":   ["Kargadia", 2791.5, 1745.7, "Tebaria",   "TBL"],
    "Irtangar":            ["Kargadia", 2731.3,  163.8, "Verlennia", None],
    "Kaivus na Advuräin":  ["Kargadia", 2510.2, 1515.1, "Tebaria",   "TBL"],
    "Kanerakainead":       ["Kargadia", 1015.0,  100.8, "Nehtivia",  "Kanernehtivia"],
    "Kanertebaria":        ["Kargadia",  666.6, 1515.9, "Island",    "TBL"],
    "Kiomigar":            ["Kargadia", 2628.7,  349.0, "Verlennia", "Na Vadenaran Irrat"],
    "Kirtinangar":         ["Kargadia",  953.3,  319.2, "Nehtivia",  "Na Kirtinnat Lurvun"],
    "Kitnagar":            ["Kargadia", 3005.5, 1240.0, "Inhattia",  None],
    "Kunval na Bylkain":   ["Kargadia", 2464.0, 1414.1, "Tebaria",   "TBL"],
    "Kunval na Shaivain":  ["Kargadia", 2623.3, 1624.5, "Tebaria",   "TBL"],
    "Lakkeaina":           ["Kargadia", 2662.6,  673.6, "Inhattia",  None],
    "Leitagar":            ["Kargadia",  335.4,  318.4, "Nehtivia",  "Na Irrat"],
    "Lersedigar":          ["Kargadia", 1417.2,  631.3, "Erellia",   None],
    "Liidennan Koirantat": ["Kargadia",  317.7, 1664.1, "Tebaria",   "TBL"],
    "Lirrinta Teinain":    ["Kargadia",   25.0, 1598.4, "Tebaria",   "TBL"],
    "Muruvasaitari":       ["Kargadia", 2614.2,  526.3, "Inhattia",  None],
    "Neikelaa":            ["Kargadia", 1960.6,  733.1, "Centeria",  None],
    "Nurvutgar":           ["Kargadia", 2114.1, 1498.2, "Tebaria",   "Seanka Tebaria"],
    "Orlagar":             ["Kargadia",  342.7,  346.7, "Nehtivia",  "Na Irrat"],
    "Pakigar":             ["Kargadia",  347.5,  376.0, "Nehtivia",  "Na Irrat"],
    "Peaskar":             ["Kargadia",  510.0,  642.4, "Nehtivia",  "Na Peaskat na Jegittain"],
    "Regavall":            ["Kargadia", 1295.3,  210.8, "Nehtivia",  "Regaazdall"],
    "Reggar":              ["Kargadia", 1236.4,  300.0, "Nehtivia",  "Regaazdall"],
    "Seankar Kainead":     ["Kargadia", 2670.4, 1800.0, "Tebaria",   "TBL"],
    "Senkadar Laikadu":    ["Kargadia", 1031.7,  548.6, "Erellia",   "Senkadar Laikadu"],
    "Sentagar":            ["Kargadia", 1691.2,  495.3, "Centeria",  None],
    "Sentatebaria":        ["Kargadia",  602.3, 1610.5, "Tebaria",   "TBL"],
    "Shiradar Koankadu":   ["Kargadia", 1145.7,  501.1, "Erellia",   "Senkadar Laikadu"],
    "Shonangar":           ["Kargadia",  344.1,  347.8, "Nehtivia",  "Na Irrat"],
    "Steirigar":           ["Kargadia",  305.2,  538.2, "Nehtivia",  "Sertanehtivia"],
    "Sunovalliat":         ["Kargadia",  157.2, 1462.2, "Tebaria",   "TBL"],
    "Tebarimostus":        ["Kargadia",  636.2, 1524.7, "Nittavia",  "TBL"],
    "Tentar Hintakadu":    ["Kargadia", 2877.7, 1579.9, "Tebaria",   "TBL"],
    "Tevakta Jegittain":   ["Kargadia",  707.7,  624.2, "Nehtivia",  "Na Peaskat na Jegittain"],
    "Tevivall":            ["Kargadia",  982.3,  576.2, "Nehtivia",  "Vadernehtivia"],
    "Vaidoks":             ["Kargadia", 2754.5,  986.3, "Inhattia",  None],
    "Vintelingar":         ["Kargadia", 1485.2,  892.5, "Island",    None],
    "Virsetgar":           ["Kargadia", 1800.0,  900.0, "Centeria",  None],

    "Kaltarena":           ["Qevenerus", 2100.0,  655.1, "Kaltarena"],
}
offsets = {
    "Kargadia": -1800.0,  # -843.7 | -343
    "Qevenerus": -2100.0,
}
_times = {
    "Zeivela": times.time_zeivela,
    "Kargadia": times.time_kargadia,
    "Qevenerus": times.time_kaltaryna,

    "Sinvimania": times.time_sinvimania,
    "Hosvalnerus": times.time_hosvalnerus,
    "Kuastall-11": times.time_kuastall_11,
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
    "Qevenerus": 0.1016,
}
axial_tilts = {
    "Zeivela": 23.47,
    "Kargadia": 26.7,
    "Qevenerus": 63.71,
}
weathers = {
    "Reggar": {
        "temperature": [
            {  # 1 - Spring
                "morning": [-2.0, 5.0],
                "day": [3.5, 11.0],
                "evening": [2.5, 11.0],
                "night": [1.0, 7.5],
                "night2": [-4.0, 3.0],
            },
            {  # 2 - Spring
                "morning": [2.5, 8.0],
                "day": [5.0, 13.0],
                "evening": [7.5, 12.5],
                "night": [6.0, 14.5],
                "night2": [3.5, 11.5],
            },
            {  # 3 - Spring
                "morning": [5.5, 13.5],
                "day": [10.0, 18.5],
                "evening": [11.5, 18.5],
                "night": [11.0, 16.0],
                "night2": [5.0, 12.0],
            },
            {  # 4 - Spring
                "morning": [7.5, 15.5],
                "day": [12.0, 19.5],
                "evening": [13.5, 19.5],
                "night": [12.0, 17.0],
                "night2": [5.0, 14.0],
            },
            {  # 5 - Summer
                "morning": [11.5, 20.0],
                "day": [16.0, 27.0],
                "evening": [19.0, 27.0],
                "night": [12.0, 17.0],
                "night2": [5.0, 14.0],
            },
            {  # 6 - Summer
                "morning": [15.0, 21.0],
                "day": [20.0, 30.0],
                "evening": [20.0, 28.0],
                "night": [14.0, 23.0],
                "night2": [11.0, 21.0],
            },
            {  # 7 - Summer
                "morning": [14.0, 22.0],
                "day": [19.0, 32.0],
                "evening": [19.3, 29.0],
                "night": [13.0, 25.0],
                "night2": [11.0, 19.0],
            },
            {  # 8 - Summer
                "morning": [12.2, 19.5],
                "day": [17.5, 25.0],
                "evening": [17.5, 23.0],
                "night": [11.0, 19.0],
                "night2": [11.0, 21.0],
            },
            {  # 9 - Autumn
                "morning": [7.5, 15.0],
                "day": [10.0, 20.0],
                "evening": [9.0, 17.0],
                "night": [6.8, 15.5],
                "night2": [5.0, 12.0],
            },
            {  # 10 - Autumn
                "morning": [0.5, 9.0],
                "day": [3.0, 13.0],
                "evening": [2.0, 13.5],
                "night": [1.0, 7.0],
                "night2": [-1.0, 7.0],
            },
            {  # 11 - Autumn
                "morning": [-4.0, 5.0],
                "day": [-2.0, 7.0],
                "evening": [-1.5, 5.5],
                "night": [-4.0, 3.0],
                "night2": [-6.0, 2.0],
            },
            {  # 12 - Autumn
                "morning": [-7.0, 1.0],
                "day": [-5.5, 2.0],
                "evening": [-5.5, 1.5],
                "night": [-6.7, 0.0],
                "night2": [-9.0, -1.0],
            },
            {  # 13 - Winter
                "morning": [-11.0, -4.0],
                "day": [-10.5, -2.0],
                "evening": [-9.5, -1.5],
                "night": [-10.5, -2.0],
                "night2": [-12.0, -5.0],
            },
            {  # 14 - Winter
                "morning": [-20.0, -7.5],
                "day": [-18.5, -6.0],
                "evening": [-19.0, -6.0],
                "night": [-21.0, -8.0],
                "night2": [-22.0, -11.0],
            },
            {  # 15 - Winter
                "morning": [-12.0, -2.5],
                "day": [-9.7, 0.0],
                "evening": [-10.0, -0.5],
                "night": [-12.0, -3.0],
                "night2": [-14.0, -5.0],
            },
            {  # 16 - Winter
                "morning": [-6.0, 3.0],
                "day": [-2.2, 7.0],
                "evening": [-2.0, 6.5],
                "night": [-3.0, 3.5],
                "night2": [-5.0, 2.0],
            }
        ],
        # Seasons:          <--    Spring       --> <--    Summer       --> <--    Autumn       --> <--    Winter       -->
        "rain_chance":     [0.40, 0.37, 0.32, 0.27, 0.20, 0.14, 0.13, 0.15, 0.17, 0.27, 0.39, 0.45, 0.43, 0.42, 0.41, 0.41],
        "thunderstorms":   [0.00, 0.00, 0.00, 0.02, 0.15, 0.40, 0.50, 0.47, 0.27, 0.05, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
        "clouds_light":    [0.12, 0.10, 0.12, 0.11, 0.11, 0.12, 0.11, 0.13, 0.11, 0.12, 0.13, 0.15, 0.15, 0.15, 0.15, 0.15],
        "clouds_moderate": [0.15, 0.15, 0.17, 0.17, 0.19, 0.19, 0.19, 0.18, 0.20, 0.20, 0.20, 0.19, 0.10, 0.10, 0.10, 0.10],
        "overcast":        [0.13, 0.16, 0.17, 0.19, 0.20, 0.22, 0.24, 0.27, 0.30, 0.32, 0.33, 0.32, 0.15, 0.07, 0.07, 0.11],
        "humidity_max":    [0.78, 0.68, 0.62, 0.55, 0.47, 0.50, 0.49, 0.50, 0.51, 0.55, 0.60, 0.70, 0.75, 0.85, 0.95, 0.86],
        "humidity_min":    [0.60, 0.45, 0.30, 0.20, 0.10, 0.10, 0.10, 0.10, 0.20, 0.35, 0.50, 0.57, 0.60, 0.78, 0.80, 0.70],
        "wind": [5, 30],
        "wind_storms": {
            "probability": [0.11, 0.09, 0.06, 0.05, 0.04, 0.04, 0.04, 0.04, 0.05, 0.07, 0.09, 0.11, 0.13, 0.15, 0.16, 0.13],
            "severity": [1.7, 3.0],
            "limit": 75
        }
    }
}


class PlaceDoesNotExist(general.RegausError):
    def __init__(self, place):
        super().__init__(text=f"Place not found: {place}")


class Place:
    def __init__(self, place: str):
        self.place = place
        self.now = time.now(None)
        try:
            self.planet, self.lat, self.long, self.tz, self.time, self.local_time, self._local_time, self.region = self.get_location()
        except KeyError:
            raise PlaceDoesNotExist(place)
        # self.tz = round(round(self.long / (180 / 24)) / 2, 1)
        # self.time = time_function(time.dt(2021, 5, 30), tz=self.tz)
        # self.time = time_function(time.dt(2022, 1, 11))
        self.dt_time = dt_time(self.time.hour, self.time.minute, self.time.second)
        self.sun = Sun(self)
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
        planet, x, y, *data = places[self.place]
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
        tz = round(long / (360 / 24))
        tz += {
            "Kiomigar": -1,
            "Regavall": -1,
        }.get(self.place, 0)
        time_function = _times[planet]
        _time = time_function(self.now, tz=tz)
        _data = len(data)
        if _data == 0:
            _local_time = self.time
            local_time = f"Local time: **{self.time.str(dow=False, month=False)}**\n"
            region = None
        else:
            lang_region = data[0]
            if planet == "Kargadia":
                if lang_region == "Tebaria":
                    _local_time = times.time_kargadia(self.now, tz, 'rsl-1i')
                    local_time = f"Local time: **{_local_time.str(dow=False, month=False)}**"
                elif lang_region in ["Nehtivia", "Nittavia", "Erellia", "Centeria", "Island"]:
                    _local_time = times.time_kargadia(self.now, tz, 'rsl-1k')
                    local_time = f"Local time: **{_local_time.str(dow=False, month=False)}**"
                else:
                    # Should be RSL-1m: Uses RSL-1k for placeholder, as RSL-1m does not yet exist.
                    _local_time = times.time_kargadia(self.now, tz, 'rsl-1k')
                    local_time = f"Local time: **{_local_time.str(dow=False, month=False)}**"
                region = data[1]
            elif planet == "Qevenerus":
                if lang_region == "Kaltarena":
                    _local_time = times.time_kaltaryna(self.now, tz)
                    local_time = f"Local time (Kaltarenian RSL-1): **{_local_time.str(dow=False, month=False)}**\n" \
                                 f"Local time (Kaltarenian RL-2): Placeholder\n" \
                                 f"Local time (Kaltarena Gestedian): Placeholder"
                else:
                    _local_time = self.time
                    local_time = "Local time unknown... So far."
                region = data[0]
            else:
                _local_time = self.time
                local_time = "Local time unknown"
                region = None
        return planet, lat, long, tz, _time, local_time, _local_time, region

    def status(self):
        embed = discord.Embed(colour=general.random_colour())
        place_name = f"{self.place}, {self.planet}" if self.region is None else f"{self.place}, {self.region}, {self.planet}"
        embed.title = f"Weather in **{place_name}**"
        embed.description = f"{self.local_time}\n" \
                            f"Time zone: {self.tz:+}:00 (Real offset {self.long / (360 / 24):+.2f} hours)\n" \
                            f"Location: {self.location(False)}"

        if self.weathers is not None:
            # Remove non-ascii stuff like äá to make sure it's only A-Z
            _name = self.place[:8].encode("ascii", "replace").replace(b"?", b"0").replace(b" ", b"0")
            _seed0 = int(_name, base=36)
            _seed1 = self.time.ds * 1440  # Seed the day from 1/1/0001, multiplied by 1440 minutes.
            _seed2 = self.time.hour * 60
            seed = _seed0 + _seed1
            seed2 = seed + _seed2

            temp_min, temp_max = self.weathers["temperature"][self.time.month - 1][self.sun.day_part]
            temp = general.random1(temp_min, temp_max, seed)
            temp_c = round(temp, 1)
            embed.add_field(name="Temperature", value=f"**{temp_c}°C**", inline=False)

            wind_min, wind_max = self.weathers["wind"]
            wind = general.random1(wind_min, wind_max, seed2)
            # wind_max: int = self.weathers["wind_max"]
            # if wind > wind_max:
            #     wind = wind_max
            storms = self.weathers["wind_storms"]
            storm_probability = storms["probability"][self.time.month - 1]
            storm = general.random1(0, 1, seed2 - 1)
            if storm < storm_probability:
                severity_min, severity_max = storms["severity"]
                wind *= general.random1(severity_min, severity_max, seed2 - 2)
                limit = storms["limit"]
                if wind > limit:
                    wind = limit
            if wind < 0:
                wind = 0
            speed_kmh = round(wind, 1)
            speed_mps = round(wind / 3.6, 1)
            embed.add_field(name="Wind speed", value=f"**{speed_kmh} km/h** | {speed_mps} m/s", inline=False)

            humidity_max = self.weathers["humidity_max"][self.time.month - 1]
            humidity_min = self.weathers["humidity_min"][self.time.month - 1]
            humidity = general.random1(humidity_min, humidity_max, seed2)
            embed.add_field(name="Humidity", value=f"{humidity:.0%}", inline=False)

            rain_chance = self.weathers["rain_chance"][self.time.month - 1]  # [month - 1]
            rain = general.random1(0, 100, seed2) <= rain_chance
            if rain:
                if -3 > temp_c > 3:
                    rain_out = "Rain" if general.random1(0, 1, seed2 - 3) < 0.5 else "Snow"
                else:
                    rain_out = "Rain" if temp_c > 0 else "Snow"
                    if temp_c >= 17.5:
                        thunder_chance = self.weathers["thunderstorms"][self.time.month - 1]
                        if general.random1(0, 1, seed2) < thunder_chance:
                            rain_out = "Thunder"
            else:
                cloud_chance = self.weathers["clouds_light"][self.time.month - 1]
                cloud_moderate = self.weathers["clouds_moderate"][self.time.month - 1] + cloud_chance
                overcast = self.weathers["overcast"][self.time.month - 1] + cloud_moderate
                value = general.random1(0, 1, seed2)
                if value < cloud_chance:
                    rain_out = "Slightly cloudy"
                elif cloud_chance < value < cloud_moderate:
                    rain_out = "Cloudy"
                elif cloud_moderate < value < overcast:
                    rain_out = "Overcast"
                else:
                    rain_out = "Sunny"
            embed.add_field(name="Sky's mood", value=rain_out, inline=False)
        else:
            embed.description += "\n\nWeather conditions not available."

        embed.add_field(name="About the Sun", value=self.sun.sun_data, inline=False)
        embed.set_footer(text=f"Current season: {self.sun.season.title()}")
        embed.timestamp = self.now
        return embed


def time_from_decimal(day_part: float) -> dt_time:
    if day_part == 1:
        return dt_time(23, 59, 59, 999999)
    seconds = int((day_part % 1) * 86400)
    h, ms = divmod(seconds, 3600)
    m, s = divmod(ms, 60)
    return dt_time(h, m, s)


def time_to_decimal(_time) -> float:  # types: dt_time, TimeSolar, etc.
    return _time.hour / 24 + _time.minute / 1440 + _time.second / 86400


class Sun:
    def __init__(self, place: Place):
        self.place = place
        self.solar_noon, self.sunrise, self.sunset, self.dawn, self.dusk, self.sun_data, self.day_part, self.season = self.get_data()

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
        ecliptic_longitude = (mean_anomaly + equation_of_centre + 180 + (90 - coefficient)) % 360  # degrees
        seasons = ["spring", "summer", "autumn", "winter"] if self.place.lat >= 0 else ["autumn", "winter", "spring", "summer"]
        season = seasons[int(ecliptic_longitude / 90)]
        axial_tilt = axial_tilts[self.place.planet]  # Axial tilt (obliquity) of the planet, in degrees
        declination = deg(asin(sin(rad(ecliptic_longitude)) * sin(rad(axial_tilt))))  # Declination of the sun, degrees
        # (720 - 4 * self.place.long - eq_of_time + self.place.tz * 60) / 1440
        solar_time_change = 0.0053 * sin(rad(mean_anomaly)) - 0.0069 * sin(rad(2 * ecliptic_longitude)) - self.place.long / 360 + self.place.tz / 24
        solar_time = (days % 1 - solar_time_change + self.place.tz / 24) % 1
        solar_noon_t = 0.5 + solar_time_change  # Fraction of the day

        def hour_angle_cos(_zenith: float):
            return (sin(rad(_zenith) - sin(rad(self.place.lat)) * sin(rad(declination)))) / (cos(rad(self.place.lat)) * cos(rad(declination)))

        # Calculate sunrise/set and twilight times
        sunrise_cos = hour_angle_cos(-0.833)
        twilight_cos = hour_angle_cos(-6)
        if -1 <= sunrise_cos <= 1:
            sunrise_ha = deg(acos(sunrise_cos))  # Sunrise Hour Angle
            sunrise_t = solar_noon_t - sunrise_ha * 4 / 1440
            sunset_t = solar_noon_t + sunrise_ha * 4 / 1440
            if -1 <= twilight_cos <= 1:
                twilight_ha = deg(acos(twilight_cos))  # Twilight Hour Angle
                dawn_t = solar_noon_t - twilight_ha * 4 / 1440
                dusk_t = solar_noon_t + twilight_ha * 4 / 1440
            else:
                dawn_t, dusk_t = 0, 1
        elif sunrise_cos < -1:
            sunrise_t, sunset_t = 2, 2  # Eternal daylight
            dawn_t, dusk_t = 0, 1
        else:
            sunrise_t, sunset_t = 3, 3  # Eternal nighttime
            if -1 <= twilight_cos <= 1:
                twilight_ha = deg(acos(twilight_cos))
                dawn_t = solar_noon_t - twilight_ha * 4 / 1440
                dusk_t = solar_noon_t + twilight_ha * 4 / 1440
            else:
                dawn_t, dusk_t = 0, 1

        # Calculate position of the sun (elevation and azimuth)
        hour_angle = solar_time * 360 - 180  # degrees
        zenith = deg(acos(sin(rad(self.place.lat)) * sin(rad(declination)) + cos(rad(self.place.lat)) * cos(rad(declination)) * cos(rad(hour_angle))))  # degrees
        elevation = 90 - zenith  # degrees
        if elevation > 85:
            refraction = 0
        elif elevation > 5:
            refraction = 58.1 / tan(rad(elevation)) - 0.07 / (tan(rad(elevation)) ** 3) + 0.000086 / (tan(rad(elevation)) ** 5)
        elif elevation > -0.575:
            refraction = 1735 + elevation * (-518.2 + elevation * (103.4 + elevation * (-12.79 + elevation * 0.711)))
        else:
            refraction = -20.772 / tan(rad(elevation))
        refraction /= 3600
        # if self.place.lat in [0, 90]:
        #     azimuth = -1
        # else:
        #     azimuth_equation = deg(acos(((sin(rad(self.place.lat)) * cos(rad(zenith))) - sin(rad(declination))) / (cos(rad(self.place.lat)) * sin(rad(zenith)))))
        #     if hour_angle > 0:
        #         azimuth = (azimuth_equation + 180) % 360
        #     else:
        #         azimuth = (540 - azimuth_equation) % 360
        return dawn_t, sunrise_t, solar_noon_t, sunset_t, dusk_t, solar_time, elevation + refraction, season  # , azimuth

    def get_data(self):
        dawn_t, sunrise_t, solar_noon_t, sunset_t, dusk_t, solar_time_t, elevation, season = self.calculate()
        dawn = time_from_decimal(dawn_t)
        sunrise = time_from_decimal(sunrise_t)
        solar_noon = time_from_decimal(solar_noon_t)
        sunset = time_from_decimal(sunset_t)
        dusk = time_from_decimal(dusk_t)
        solar_time = time_from_decimal(solar_time_t)
        if sunrise_t == 2 or sunset_t == 2:
            sun_data = f"Always daytime today\n\n`Solar noon {solar_noon}`\n"
            if elevation < 15:
                if solar_time < solar_noon:
                    day_part = "morning"
                else:
                    day_part = "evening"
            else:
                day_part = "day"
        elif sunrise_t == 3 or sunset_t == 3:
            if dawn_t != 0 and dusk_t != 1:
                sun_data = f"Always nighttime today\n\n`Dawn       {dawn}`\n`Solar noon {solar_noon}`\n`Dusk       {dusk}`\n"
                if solar_time < dawn:
                    day_part = "night2"
                elif dawn < solar_time < solar_noon:
                    day_part = "morning"
                elif solar_noon < solar_time < dusk:
                    day_part = "evening"
                else:
                    day_part = "night"
            else:
                sun_data = f"Always nighttime today\n\n`Solar noon {solar_noon}`\n"
                if solar_time < solar_noon:
                    day_part = "night2"
                else:
                    day_part = "night"
        else:
            daylight = sunset_t - sunrise_t
            daylight_length = languages.Language("english").delta_int(daylight * 86400, accuracy=2, brief=False, affix=False)
            _dawn, _dusk = (f"`Dawn       {dawn}`\n", f"`Dusk       {dusk}`\n") if dawn_t != 0 and dusk_t != 1 else ("", "")
            sun_data = f"{_dawn}`Sunrise    {sunrise}`\n`Solar noon {solar_noon}`\n`Sunset     {sunset}`\n{_dusk}\nLength of day {daylight_length}"
            morning_end = time_from_decimal(solar_noon_t - daylight / 4)
            evening_start = time_from_decimal(solar_noon_t + daylight / 4)
            if solar_time < dawn:
                day_part = "night2"   # In an equal day: midnight-5:30am
            elif dawn < solar_time < morning_end:
                day_part = "morning"  # In an equal day: 5:30am-9am
            elif morning_end < solar_time < evening_start:
                day_part = "day"      # In an equal day: 9am-3pm
            elif evening_start < solar_time < dusk:
                day_part = "evening"  # In an equal day: 3pm-6:30pm
            else:
                day_part = "night"    # In an equal day: 6:30pm-midnight
        sun_data += f"\nTrue solar time {solar_time}"
        # if self.place.lat not in [0, 90]:
        #     parts = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"]
        #     _azimuth = (azimuth + 22.5) % 360
        #     direction = parts[int(_azimuth / 45)]
        #     sun += f"\nThe sun is facing {direction} ({azimuth:.0f}°)"
        # The method seems to be quite inaccurate at low and high latitudes
        if elevation > 0:
            sun_data += f"\nThe sun is {elevation:.0f}° above the horizon"
        else:
            sun_data += f"\nThe sun is {-elevation:.0f}° below the horizon"
        return solar_noon, sunrise, sunset, dawn, dusk, sun_data, day_part, season
