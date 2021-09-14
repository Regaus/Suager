from datetime import time as dt_time
from math import acos, asin, cos, degrees as deg, radians as rad, sin, tan

import discord

from utils import general, languages, time, times, weathers

places = [
    {
        "name": {
            "english": "Village on Virkada",
            "kargadian_kaltarena": "Aa an Viiharan",
        },
        "location": [2172.5, 553.2],
        "language": ["kargadian_kaltarena"],
        "planet": "Virkada",
    },
    {
        "name": {
            "english": "Village of Cold Heat",
            "kargadian_west": "Gar na Kaldan Gartan",
        },
        "location": [1835.2, 24.7],
        "language": ["kargadian_west"],
        "planet": "Virkada",
    },
    {
        "name": {
            "English": "Hot Village",
            "usturian": "Ghazhan Kunemad",
        },
        "location": [2052.0, 560.1],
        "language": ["usturian"],
        "planet": "Virkada",
    },
    {
        "name": {
            "english": "Village of Suttalis",
            "kargadian_west": "Suttaligar",
        },
        "location": [1324.1, 252.9],
        "language": ["kargadian_west"],
        "planet": "Virkada",
    },
    {
        "name": {
            "english": "Virkadan Village",
            "kargadian_west": "Virkadagar",
        },
        "location": [1312.8, 221.5],
        "language": ["kargadian_west"],
        "planet": "Virkada",
    },
    {
        "name": {
            "english": "Virkada Central",
        },
        "location": [1800.0, 900.0],
        "language": ["multiple"],
        "planet": "Virkada",
    },
    {
        "name": {
            "english": "Virkada Southern",
        },
        "location": [1800.0, 1500.0],
        "language": ["tebarian"],
        "planet": "Virkada",
    },
    {
        "name": {
            "english": "Virkadan Tebaria",
            "tebarian": "Virkatebaria",
        },
        "location": [1821.7, 1553.0],
        "language": ["tebarian"],
        "planet": "Virkada",
    },

    {
        "name": {
            "english": "Akkigar",
            "kargadian_east": "Akkigar",
        },
        "location": [2602.1, 313.1],
        "language": ["kargadian_east"],
        "planet": "Kargadia",
        "region": "Na Vadenaran Irrat",
    },
    {
        "name": {
            "english": "Squirrels' City",
            "tebarian": "Bylkangar",
        },
        "location": [2382.3, 1311.8],
        "language": ["tebarian"],
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "english": "Squirrels' Tundra",
            "tebarian": "Na Bylkankaldanpeaskat",
            "kargadian_west": "Na Bylkankaldanpeaskat",
        },
        "location": [2828.2, 1689.3],
        "language": ["tebarian"],
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "english": "Squirrels' Forest",
            "tebarian": "Na Bylkanseivanlias",
            "kargadian_west": "Na Bylkanseivulias",
        },
        "location": [3283.0, 1553.2],
        "language": ["tebarian"],
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "english": "Squirrels' Swamp",
            "tebarian": "Na Bylkantaivead",
            "kargadian_west": "Na Bylkantaivead",
        },
        "location": [3274.3, 1564.4],
        "language": ["tebarian"],
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "english": "The Wild Lands",
            "tebarian": "Na Degan Ihat",
            "kargadian_west": "Na Degaeltat",
        },
        "location": [3539.7, 1536.5],
        "language": ["tebarian"],
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "english": "Ekspi City",
            "kargadian_east": "Ekspigar",
        },
        "location": [2560.4, 317.3],
        "language": ["kargadian_east"],
        "planet": "Kargadia",
        "region": "Na Vadenaran Irrat",
    },
    {
        "name": {
            "english": "Erelltown",
            "kargadian_west": "Erellgar",
        },
        "location": [1275.5, 944.2],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "english": "Erda Desert",
            "kargadian_west": "Erdapeaskat",
        },
        "location": [504.1, 1140.6],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "english": "Hunta Shore",
            "tebarian": "Huntavall",
        },
        "location": [1542.2, 1529.9],
        "language": ["tebarian"],
        "planet": "Kargadia",
        "region": "Na Ihat na Iidain",
    },
    {
        "name": {
            "english": "The Land of the Dead",
            "tebarian": "Na Iha na Sevarddain",
            "kargadian_west": "Na Elta na Sevarddain"
        },
        "location": [2791.5, 1745.7],
        "language": ["tebarian"],
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "english": "Irtangar",
            "kargadian_east": "Irtangar",
        },
        "location": [2731.3, 163.8],
        "language": ["kargadian_east"],
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "english": "Cobbleton",
            "tebarian": "Kaivalgar",
            "kargadian_west": "Kaivalgar",
        },
        "location": [1054.8, 1615.0],
        "language": ["tebarian"],
        "planet": "Kargadia",
        "region": "Na Ihat na Iidain",
    },
    {
        "name": {
            "english": "The Hill of Challenges",
            "tebarian": "Na Kalvus na Advuräin",
            "kargadian_west": "Na Kalvus na Advuräin"
        },
        "location": [2791.5, 1745.7],
        "language": ["tebarian"],
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "english": "Northern End Kargadia",
            "kargadian_west": "Kanerakainead",
        },
        "location": [1015.0, 100.8],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": "Kanernehtivia",
    },
    {
        "name": {
            "english": "Northern Tebaria",
            "tebarian": "Kanertebaria",
            "kargadian_west": "Kanertebaria",
        },
        "location": [666.6, 1515.9],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "english": "Kyomi City",
            "kargadian_east": "Kiomigar",
        },
        "location": [2628.7, 349.0],
        "language": ["kargadian_east"],
        "planet": "Kargadia",
        "region": "Na Vadenaran Irrat",
    },
    {
        "name": {
            "english": "Mountain City",
            "kargadian_west": "Kirtinangar",
        },
        "location": [953.3, 319.2],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": "Na Kirtinnat Lurvun",
    },
    {
        "name": {
            "english": "Kitnagar",
            "kargadian_east": "Kitnagar",
        },
        "location": [3005.5, 1240.0],
        "language": ["kargadian_east"],
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "english": "Squirrels' Temple",
            "tebarian": "Kunval na Bylkain",
            "kargadian_west": "Kunval na Bylkain",
        },
        "location": [2464.0, 1414.1],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "english": "Shamans' Temple",
            "tebarian": "Kunval na Shaivain",
            "kargadian_west": "Kunval na Shaivain",
        },
        "location": [2623.3, 1624.5],
        "language": ["tebarian"],
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "english": "Lilia City",
            "kargadian_west": "Lailagar",
        },
        "location": [1094.0, 126.8],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": "Kanernehtivia",
    },
    {
        "name": {
            "english": "Lakkeaina",
            "kargadian_east": "Lakkeáina",
        },
        "location": [2662.6, 673.6],
        "language": ["kargadian_east"],
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "english": "Leita City",
            "kargadian_west": "Leitagar",
        },
        "location": [335.4, 318.4],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": "Na Irrat",
    },
    {
        "name": {
            "english": "Lersedigar",
            "kargadian_west": "Lersédigar",
        },
        "location": [1417.2, 631.3],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "english": "The Soaring Heights",
            "tebarian": "Na Liidennan Koirantat",
            "kargadian_west": "Na Liidennan Koirantat",
        },
        "location": [317.7, 1664.1],
        "language": ["tebarian"],
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "english": "The Volcano of Shadows",
            "tebarian": "Na Lirrinta Teinain",
            "kargadian_west": "Na Lirkinta Teinain",
        },
        "location": [25.0, 1598.4],
        "language": ["tebarian"],
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "english": "Muruvasaitari",
            "kargadian_east": "Muruvasáitari",
        },
        "location": [2614.2, 526.3],
        "language": ["kargadian_east"],
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "english": "Neikelaa",
            "kargadian_east": "Neikélaa",
        },
        "location": [1960.6, 733.1],
        "language": ["kargadian_east"],
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "english": "Nurvutton",
            "tebarian": "Nurvutgar",
        },
        "location": [2114.1, 1498.2],
        "language": ["tebarian"],
        "planet": "Kargadia",
        "region": "Seanka Tebaria",
    },
    {
        "name": {
            "english": "Orla City",
            "kargadian_west": "Orlagar",
        },
        "location": [342.7, 346.7],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": "Na Irrat",
    },
    {
        "name": {
            "english": "Five's City",
            "kargadian_west": "Pakigar",
        },
        "location": [347.5, 376.0],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": "Na Irrat",
    },
    {
        "name": {
            "english": "Desert City",
            "kargadian_west": "Peaskar",
        },
        "location": [510.0, 642.4],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": "Na Peaskat na Jegittain",
    },
    {
        "name": {
            "english": "Regan Shores",
            "kargadian_west": "Regavall",
        },
        "location": [1295.3, 210.8],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": "Regaazdal",
    },
    {
        "name": {
            "english": "Regaus City",
            "kargadian_west": "Reggar",
        },
        "location": [1236.4, 300.0],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": "Regaazdal",
    },
    {
        "name": {
            "english": "South Pole Kargadia",
            "tebarian": "Seankar Kainead",
            "kargadian_west": "Senankar Kainead",
        },
        "location": [2670.4, 1800.0],
        "language": ["tebarian"],
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "english": "Senko's Lair",
            "kargadian_west": "Senkadar Laikadu",
        },
        "location": [1031.7, 548.6],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": "Senkadar Laikadu",
    },
    {
        "name": {
            "english": "Sentagar",
            "kargadian_west": "Sentagar",
        },
        "location": [1691.2, 495.3],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "english": "Central Tebaria",
            "tebarian": "Sentatebaria",
            "kargadian_west": "Sentatebaria",
        },
        "location": [602.3, 1610.5],
        "language": ["tebarian"],
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "english": "Shiro's Playground",
            "kargadian_west": "Shiradar Koankadu",
        },
        "location": [1145.7, 501.1],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": "Senkadar Laikadu",
    },
    {
        "name": {
            "english": "Shawn City",
            "kargadian_west": "Shonangar",
        },
        "location": [344.1, 347.8],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": "Na Irrat",
    },
    {
        "name": {
            "english": "Steir City",
            "kargadian_west": "Steirigar",
        },
        "location": [305.2, 538.2],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": "Sertanehtivia",
    },
    {
        "name": {
            "english": "Valleys of the Sun",
            "tebarian": "Na Sunovalliat",
            "kargadian_west": "Na Sunonvailantat",
        },
        "location": [157.2, 1462.2],
        "language": ["tebarian"],
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "english": "Suager City",
            "kargadian_west": "Suvagar",
        },
        "location": [1220.0, 293.2],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": "Regaazdal",
    },
    {
        "name": {
            "english": "Tebaria Bridge",
            "tebarian": "Tebarimost",
            "kargadian_west": "Tebarimostus",
        },
        "location": [636.2, 1524.7],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "english": "The Dark Cave",
            "tebarian": "Na Tentar Hintakadu",
            "kargadian_west": "Na Temannar Hintakadu",
        },
        "location": [2877.7, 1579.9],
        "language": ["tebarian"],
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "english": "The Egyptians' Pyramid",
            "kargadian_west": "Na Tevakta na Jegittain",
        },
        "location": [707.7, 624.2],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": "Na Peaskat na Jegittain",
    },
    {
        "name": {
            "english": "The Warm Shores",
            "kargadian_west": "Tevivall",
        },
        "location": [982.3, 576.2],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": "Vadernehtivia",
    },
    {
        "name": {
            "english": "Vaidoks",
            "kargadian_east": "Vaidoks",
        },
        "location": [2754.5, 986.3],
        "language": ["kargadian_east"],
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "english": "Potato City",
            "kargadian_west": "Vintelingar",
        },
        "location": [1485.2, 892.5],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "english": "Equator City",
            "kargadian_west": "Virsetgar",
        },
        "location": [1800.0, 900.0],
        "language": ["kargadian_west"],
        "planet": "Kargadia",
        "region": None,
    },

    {
        "name": {
            "english": "Border City",
            "kargadian_west": "Gar a na Redenan",
            "kargadian_kaltarena": "Serenaanaa"
        },
        "location": [2375.6, 1133.2],
        "language": ["kargadian_kaltarena", "usturian"],
        "planet": "Qevenerus",
        "region": "Kaltarena"
    },
    {
        "name": {
            "english": "Kaltarena City",
            "kargadian_west": "Kaltarena",
            "kargadian_kaltarena": "Haltaren",
            "usturian": "Khupatsad Usturat"
        },
        "location": [2100.0, 655.1],
        "language": ["kargadian_kaltarena", "usturian"],
        "planet": "Qevenerus",
        "region": "Kaltarena"
    },
    {
        "name": {
            "english": "Northern End Kaltarena",
            "kargadian_west": "Kanerar Kainead",
            "kargadian_kaltarena": "Hanerahaane",
        },
        "location": [2283.1, 191.0],
        "language": ["kargadian_kaltarena"],
        "planet": "Qevenerus",
        "region": "Kaltarena"
    },
    {
        "name": {
            "english": "Equatorial Shores",
            "kargadian_west": "Sertavall",
            "kargadian_kaltarena": "Seetaaveşhu",
        },
        "location": [2408.4, 900.0],
        "language": ["kargadian_kaltarena", "usturian"],
        "planet": "Qevenerus",
        "region": "Kaltarena"
    },
]
offsets = {
    "Virkada": -1800.0,
    "Kargadia": -1800.0,  # -843.7 | -343
    "Qevenerus": -2100.0,
}
_times = {
    "Virkada": times.time_virkada,
    "Zeivela": times.time_zeivela,
    "Kargadia": times.time_kargadia,
    "Qevenerus": times.time_qevenerus_ka,

    "Sinvimania": times.time_sinvimania,
    "Hosvalnerus": times.time_hosvalnerus,
    "Kuastall-11": times.time_kuastall_11,
}
lengths = {
    "Virkada": 30.7,
    "Zeivela": 212.16,  # 432 + 1/3
    "Kargadia": 256.0625,  # 512.125
    "Qevenerus": 800.0,

    "Sinvimania": 373.8,
    "Hosvalnerus": 378.5,
    "Kuastall-11": 19384.2,
}
eccentricity = {
    "Virkada": 0.0112,
    "Zeivela": 0.0271,
    "Kargadia": 0.01721,
    "Qevenerus": 0.05172,
}
axial_tilts = {
    "Virkada": 176.2,
    "Zeivela": 23.47,
    "Kargadia": 26.7,
    "Qevenerus": 63.71,
}


class PlaceDoesNotExist(general.RegausError):
    def __init__(self, place):
        super().__init__(text=f"Place not found: {place}")


class Place:
    def __init__(self, place: str):
        self.name = place
        self.now = time.now(None)
        # self.now = time.dt(1686, 11, 21, 11, 55, 21)
        # try:
        self.name, self.names, self.planet, self.lat, self.long, self.tz, self.time, self.local_time, self.region, self.language = self.get_location()
        # except KeyError:
        #     raise PlaceDoesNotExist(place)
        # self.tz = round(round(self.long / (180 / 24)) / 2, 1)
        # self.time = time_function(time.dt(2021, 5, 30), tz=self.tz)
        # self.time = time_function(time.dt(2022, 1, 11))
        self.dt_time = dt_time(self.time.hour, self.time.minute, self.time.second)
        self.sun = Sun(self)
        try:
            self.weathers = weathers.weathers[self.name]
        except KeyError:
            self.weathers = None
        # self.weathers = patterns[self.place]

    def time_info(self):
        return f"Current local time in **{self.name}, {self.planet}**: {self.local_time}"
        # _time = f"{self.time.hour:02d}:{self.time.minute:02d}:{self.time.second:02d}"
        # _date = f"{self.time.day:02d}/{self.time.month:02d}/{self.time.year}"
        # return f"It is currently **{_time}** on **{_date}** in **{self.place}, {self.planet}**"

    def location(self, indent: bool = False, language: languages.Weather = None):
        lat, long = self.lat, self.long
        if language is None:
            language = languages.Weather("english")
        _n, _e, _s, _w = language.data("sides")
        # This allows to translate the N, E, S, W pieces into other languages
        n, e = _n if lat >= 0 else _s, _e if long >= 0 else _w
        if lat < 0:
            lat *= -1
        if long < 0:
            long *= -1
        return f"{lat:>5.2f}°{n}, {long:>6.2f}°{e}" if indent else f"{lat:.2f}°{n}, {long:.2f}°{e}"

    def get_location(self):
        # planet, x, y, *data = places_old[self.place]
        place = None
        _name = self.name.lower()
        for _place in places:
            if _name in [place_name.lower() for place_name in _place["name"].values()]:
                place = _place
                break
        if not place:
            raise PlaceDoesNotExist(self.name)
        planet = place["planet"]
        offset = offsets[planet]
        x, y = place["location"]
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
        if lat in [90, -90]:
            long = 0
        # names = "\n".join(f"{language}: **{name}**" for language, name in place["name"].items())
        name = place["name"]["english"]
        tz = round(long / (360 / 24))
        tz += {
            "Kyomi City": -1,
            "Regan Shores": -1,
            "South Pole Kargadia": 5,
        }.get(name, 0)
        time_function = _times[planet]
        _time = time_function(self.now, tz=tz)
        try:
            region = place["region"]
        except KeyError:
            region = None
        # local_time = f"**{_time.str()}**"
        _languages = place["language"]
        # if planet == "Kargadia":
        #     if language == "West Kargadian":
        #         _local_time = times.time_kargadia(self.now, tz, 'rsl-1k')
        #     elif language == "East Kargadian":
        #         _local_time = times.time_kargadia(self.now, tz, 'rsl-1m')
        #     elif language == "Tebarian":
        #         _local_time = times.time_kargadia(self.now, tz, 'rsl-1i')
        #     else:
        #         _local_time = _time
        #     local_time = f"**{_local_time.str(dow=False, month=False)}**"
        # elif planet == "Qevenerus":
        #     if language == "Kaltarena Kargadian, Usturian":
        #         ka_time = times.time_qevenerus_ka(self.now, tz)
        #         us_time = times.time_qevenerus_us(self.now, tz)
        #         local_time = f"Ka. Kargadian: **{ka_time.str(dow=False, month=False)}**\nUsturian: **{us_time.str(dow=False, month=False)}**"
        #     elif language == "Kaltarena Kargadian":
        #         ka_time = times.time_qevenerus_ka(self.now, tz)
        #         local_time = f"**{ka_time.str(dow=False, month=False)}**"
        local_time = {"any": general.bold(_time.str())}
        if planet != "Virkada":
            for language in _languages:
                _local_time = _time
                if planet == "Kargadia":
                    _local_time = times.time_kargadia(self.now, tz, language)
                elif planet == "Qevenerus":
                    if language == "kargadian_kaltarena":
                        _local_time = times.time_qevenerus_ka(self.now, tz)
                    elif language == "usturian":
                        _local_time = times.time_qevenerus_us(self.now, tz)
                local_time[language] = general.bold(_local_time.str(dow=False, month=False))
        return name, place["name"], planet, lat, long, tz, _time, local_time, region, _languages

    def weather(self):
        if self.weathers is not None:
            # Remove non-ascii stuff like äá to make sure it's only A-Z
            _name = self.name[:8].encode("ascii", "replace").replace(b"?", b"0").replace(b" ", b"0").replace(b"'", b"0")
            _seed0 = int(_name, base=36)
            _seed1 = self.time.ds * 1440  # Seed the day from 1/1/0001, multiplied by 1440 minutes.
            _seed2 = self.time.hour * 60
            seed = _seed0 + _seed1
            seed2 = seed + _seed2

            temp_min, temp_max = self.weathers["temperature"][self.time.month - 1][self.sun.day_part]
            temp = general.random1(temp_min, temp_max, seed)
            # temp_c = round(temp, 1)
            # embed.add_field(name="Temperature", value=f"**{temp_c}°C**", inline=False)

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
            # speed_kmh = round(wind, 1)
            # speed_mps = round(wind / 3.6, 1)
            # embed.add_field(name="Wind speed", value=f"**{speed_kmh} km/h** | {speed_mps} m/s", inline=False)

            humidity_max = self.weathers["humidity_max"][self.time.month - 1]
            humidity_min = self.weathers["humidity_min"][self.time.month - 1]
            humidity = general.random1(humidity_min, humidity_max, seed2)
            # embed.add_field(name="Humidity", value=f"{humidity:.0%}", inline=False)

            rain_chance = self.weathers["rain_chance"][self.time.month - 1]  # [month - 1]
            rain = general.random1(0, 100, seed2) <= rain_chance
            if rain:
                if -2.5 > temp > 2.5:
                    rain_out = "rain" if general.random1(0, 1, seed2 - 3) < 0.5 else "snow"
                else:
                    rain_out = "rain" if temp > 0 else "snow"
                    if temp >= 17.5:
                        thunder_chance = self.weathers["thunderstorms"][self.time.month - 1]
                        if general.random1(0, 1, seed2) < thunder_chance:
                            rain_out = "thunder"
            else:
                cloud_chance = self.weathers["clouds_light"][self.time.month - 1]
                cloud_moderate = self.weathers["clouds_moderate"][self.time.month - 1] + cloud_chance
                overcast = self.weathers["overcast"][self.time.month - 1] + cloud_moderate
                value = general.random1(0, 1, seed2)
                if value < cloud_chance:
                    rain_out = "cloudy1"  # "Slightly cloudy"
                elif cloud_chance < value < cloud_moderate:
                    rain_out = "cloudy2"  # "Cloudy"
                elif cloud_moderate < value < overcast:
                    rain_out = "cloudy3"  # "Overcast"
                else:
                    rain_out = "sunny"
            return temp, wind, humidity, rain_out
        else:
            return None, None, None, None

    def status(self, language: languages.Weather) -> discord.Embed:
        """ Get current weather conditions as Embed """
        temp, wind_kmh, humidity, rain_out = self.weather()
        embed = discord.Embed(colour=general.random_colour())
        # lang_corr = {
        #    "english": "English",
        #      "kargadian_west": "West Kargadian",
        #     "tebarian": "Tebarian"
        # }.get(language.language, "English")
        if language.language == "kargadian_west":
            name = self.names.get(language.language, self.names.get("tebarian", self.name))
        elif language.language == "tebarian":
            name = self.names.get(language.language, self.names.get("kargadian_west", self.name))
        elif language.language == "kargadian_east":
            name = self.names.get(language.language, self.names.get("kargadian_west", self.names.get("tebarian", self.name)))
        else:
            name = self.names.get(language.language, self.name)
        place_name = f"{name}, {self.planet}" if self.region is None else f"{name}, {self.region}, {self.planet}"
        # embed.title = f"Information about **{place_name}**"
        embed.title = language.string("weather78_title", place_name)

        # embed.add_field(name="Time and Location", inline=False,
        #                 value=f"Local time: {self.local_time}\n"
        #                       f"Time zone: **{self.tz:+}:00** (Real offset {self.long / (360 / 24):+.2f} hours)\n"
        #                       f"Location: **{self.location(False)}**")
        lang_names = language.data("languages")
        lt_langs = list(self.local_time.keys())
        if lt_langs == ["any"]:
            local_time = self.local_time["any"]
        else:
            lt_langs.remove("any")
            length = len(lt_langs)
            if length == 1:
                local_time = self.local_time[lt_langs[0]]
            else:
                _local_time = []
                for lang in lt_langs:
                    _local_time.append(f"{lang_names[lang]}: {self.local_time[lang]}")
                local_time = "\n".join(_local_time)
        embed.add_field(name=language.string("weather78_local_time"), value=local_time, inline=False)

        offset1 = f"{self.tz:+}:00"
        offset2_raw = self.long / (360 / 24)
        hours, minutes = divmod(offset2_raw, 1)
        if hours < 0 and minutes != 0:
            hours = int(hours + 1)
            minutes = round((1 - minutes) * 60)
        else:
            hours = int(hours)
            minutes = round(minutes * 60)
        offset2 = f"{hours:+}:{minutes:02d}"
        # embed.add_field(name="Timezone", value=f"**{self.tz:+}:00** (Real offset {self.long / (360 / 24):+.2f} hours)", inline=False)
        embed.add_field(name=language.string("weather78_timezone"), value=language.string("weather78_timezone2", offset1, offset2), inline=False)

        embed.add_field(name=language.string("weather78_location"), value=self.location(indent=False, language=language), inline=False)

        names = "\n".join([f"{lang_names[lang]}: {self.names[lang]}" for lang in self.names])
        embed.add_field(name=language.string("weather78_names"), value=names, inline=False)

        langs = languages.join([lang_names[lang] for lang in self.language], final=language.string("and"))
        embed.add_field(name=language.string("weather78_languages"), value=langs, inline=False)
        if temp is not None:
            # output = f"Temperature: **{temp_c}°C**\n" \
            #          f"Wind speed: **{speed_kmh} km/h** | **{speed_mps} m/s**\n" \
            #          f"Humidity: **{humidity:.0%}**\n" \
            #          f"Sky's mood: **{rain_out}**"
            c = language.number(temp, precision=1)
            f = language.number(temp * 1.8 + 32, precision=1)
            temperature = language.string("temperature", c=c, f=f)
            kmh = language.number(wind_kmh, precision=1)
            mps = language.number(wind_kmh / 3.6, precision=1)
            mph = language.number(wind_kmh / 1.609, precision=1)
            wind = language.string("speed", kmh=kmh, mps=mps, miles=mph)
            humidity = language.number(humidity, precision=0, percentage=True)
            weather_data = language.data("weather78")
            rain = weather_data[rain_out]
            embed.add_field(name=language.string("weather78_weather"), value=language.string("weather78_status", temperature, wind, humidity, rain), inline=False)
        else:
            embed.add_field(name=language.string("weather78_weather"), value=language.string("weather78_weather_none"), inline=False)
        embed.add_field(name=language.string("weather78_sun"), value=self.sun.sun_data_str(language), inline=False)
        # embed.set_footer(text=f"Astronomical season: {self.sun.season.title()}")
        seasons = language.data("seasons")
        embed.set_footer(text=language.string("weather78_season", seasons[self.sun.season]))
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
            "Virkada": 35.17915309446254,  # Let's just say this is where the sun those on Day 1 of the landing
            "Kargadia": 90.0,
            "Qevenerus": 90.0,  # This calculation uses the solar RSL-1h calendar
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
        heading = (solar_time * 360) % 360
        if axial_tilt > 90:
            heading = 360 - heading
        return dawn_t, sunrise_t, solar_noon_t, sunset_t, dusk_t, solar_time, elevation + refraction, season, heading

    def get_data(self):
        dawn_t, sunrise_t, solar_noon_t, sunset_t, dusk_t, solar_time_t, elevation, season, heading = self.calculate()
        dawn = time_from_decimal(dawn_t)
        sunrise = time_from_decimal(sunrise_t)
        solar_noon = time_from_decimal(solar_noon_t)
        sunset = time_from_decimal(sunset_t)
        dusk = time_from_decimal(dusk_t)
        solar_time = time_from_decimal(solar_time_t)
        sun_data = {
            "always_day": False,
            "always_night": False,
            # "day_part": None,
            "dawn": dawn,
            "sunrise": sunrise,
            "noon": solar_noon,
            "sunset": sunset,
            "dusk": dusk,
            "day_length": None,  # in seconds
            "solar_time": solar_time,
            "elevation": round(abs(elevation)),
            "sun_below": elevation < 0,
            "heading": round(heading),
            "direction": int(((heading + 22.5) % 360) / 45)
        }
        if sunrise_t == 2 or sunset_t == 2:
            # sun_data = f"Always daytime today\n\n`Solar noon {solar_noon}`\n"
            sun_data["always_day"] = True
            sun_data["dawn"] = None
            sun_data["sunrise"] = None
            sun_data["sunset"] = None
            sun_data["dusk"] = None
            if elevation < 15:
                if solar_time < solar_noon:
                    day_part = "morning"
                else:
                    day_part = "evening"
            else:
                day_part = "day"
        elif sunrise_t == 3 or sunset_t == 3:
            sun_data["always_night"] = True
            sun_data["sunrise"] = None
            sun_data["sunset"] = None
            if dawn_t != 0 and dusk_t != 1:
                # sun_data = f"Always nighttime today\n\n`Dawn       {dawn}`\n`Solar noon {solar_noon}`\n`Dusk       {dusk}`\n"
                if solar_time < dawn:
                    day_part = "night2"
                elif dawn < solar_time < solar_noon:
                    day_part = "morning"
                elif solar_noon < solar_time < dusk:
                    day_part = "evening"
                else:
                    day_part = "night"
            else:
                sun_data["dawn"] = None
                sun_data["dusk"] = None
                # sun_data = f"Always nighttime today\n\n`Solar noon {solar_noon}`\n"
                if solar_time < solar_noon:
                    day_part = "night2"
                else:
                    day_part = "night"
        else:
            daylight = sunset_t - sunrise_t
            sun_data["day_length"] = daylight * 86400
            # daylight_length = languages.Language("english").delta_int(daylight * 86400, accuracy=2, brief=False, affix=False)
            # _dawn, _dusk = (f"`Dawn       {dawn}`\n", f"`Dusk       {dusk}`\n") if dawn_t != 0 and dusk_t != 1 else ("", "")
            # sun_data = f"{_dawn}`Sunrise    {sunrise}`\n`Solar noon {solar_noon}`\n`Sunset     {sunset}`\n{_dusk}\nLength of day {daylight_length}"
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
        # sun_data["day_part"] = day_part
        # if self.place.lat not in [90, -90]:
        #     sun_data += f"\nTrue solar time {solar_time}"
        # if self.place.lat not in [0, 90]:
        #     parts = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"]
        #     _azimuth = (azimuth + 22.5) % 360
        #     direction = parts[int(_azimuth / 45)]
        #     sun += f"\nThe sun is facing {direction} ({azimuth:.0f}°)"
        # The method seems to be quite inaccurate at low and high latitudes
        # if elevation > 0:
        #     sun_data += f"\nThe sun is {elevation:.0f}° above the horizon"
        # else:
        #     sun_data += f"\nThe sun is {-elevation:.0f}° below the horizon"
        # parts = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"]
        # direction = parts[int(((heading + 22.5) % 360) / 45)]
        # sun_data += f"\nThe sun is due {direction} ({heading:.0f}°)"
        return solar_noon, sunrise, sunset, dawn, dusk, sun_data, day_part, season

    def sun_data_str(self, language: languages.Weather) -> str:
        """ Show all the sun data """
        data = self.sun_data
        sun_data = []
        if data["always_day"]:
            sun_data.append(language.string("sun_always_day"))
        elif data["always_night"]:
            sun_data.append(language.string("sun_always_night"))
        sun = []
        if data["dawn"] is not None:
            sun.append(language.string("sun_dawn", data["dawn"]))
        if data["sunrise"] is not None:
            sun.append(language.string("sun_sunrise", data["sunrise"]))
        if self.place.lat not in [-90, 90]:
            sun.append(language.string("sun_noon", data["noon"]))
        if data["sunset"] is not None:
            sun.append(language.string("sun_sunset", data["sunset"]))
        if data["dusk"] is not None:
            sun.append(language.string("sun_dusk", data["dusk"]))
        if sun:
            sun_data.append("\n".join(sun))
        details = []
        if data["day_length"] is not None:
            details.append(language.string("sun_length", language.delta_int(data["day_length"], accuracy=2, brief=False, affix=False)))
        if self.place.lat not in [-90, 90]:
            details.append(language.string("sun_time", data["solar_time"]))
        if data["sun_below"]:
            details.append(language.string("sun_below", data["elevation"]))
        else:
            details.append(language.string("sun_above", data["elevation"]))
        directions = language.data("directions")
        details.append(language.string("sun_direction", directions[data["direction"]], data["heading"]))
        sun_data.append("\n".join(details))
        return "\n\n".join(sun_data)
