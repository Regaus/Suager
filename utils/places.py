from datetime import time as dt_time
from math import acos, asin, cos, degrees as deg, radians as rad, sin, tan

import discord

from utils import general, languages, time, times, weathers

places = [
    {
        "name": {
            "English": "Village on Virkada",
            "Kaltarena Kargadian": "Aa an Viiharan",
        },
        "location": [2172.5, 553.2],
        "language": "Kaltarena Kargadian",
        "planet": "Virkada",
    },
    {
        "name": {
            "English": "Village of Cold Heat",
            "West Kargadian": "Gar na Kaldan Gartan",
        },
        "location": [1835.2, 24.7],
        "language": "West Kargadian",
        "planet": "Virkada",
    },
    {
        "name": {
            "English": "Hot Village",
            "West Kargadian": "Ghazhan Kunemad",
        },
        "location": [2052.0, 560.1],
        "language": "Usturian",
        "planet": "Virkada",
    },
    {
        "name": {
            "English": "Suttaligar",
            "West Kargadian": "Suttaligar",
        },
        "location": [1324.1, 252.9],
        "language": "West Kargadian",
        "planet": "Virkada",
    },
    {
        "name": {
            "English": "Virkadagar",
            "West Kargadian": "Virkadagar",
        },
        "location": [1312.8, 221.5],
        "language": "West Kargadian",
        "planet": "Virkada",
    },
    {
        "name": {
            "English": "Virkada Central",
        },
        "location": [1800.0, 900.0],
        "language": "Multiple",
        "planet": "Virkada",
    },
    {
        "name": {
            "English": "Virkada Southern",
        },
        "location": [1800.0, 1500.0],
        "language": "Tebarian",
        "planet": "Virkada",
    },
    {
        "name": {
            "English": "Virkadan Tebaria",
            "Tebarian": "Virkatebaria",
        },
        "location": [1821.7, 1553.0],
        "language": "Tebarian",
        "planet": "Virkada",
    },

    {
        "name": {
            "English": "Akkigar",
            "East Kargadian": "Akkigar",
        },
        "location": [2602.1, 313.1],
        "language": "East Kargadian",
        "planet": "Kargadia",
        "region": "Na Vadenaran Irrat",
    },
    {
        "name": {
            "English": "Squirrels' City",
            "Tebarian": "Bylkangar",
        },
        "location": [2382.3, 1311.8],
        "language": "Tebarian",
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "English": "Squirrels' Tundra",
            "Tebarian": "Na Bylkankaldanpeaskat",
            "West Kargadian": "Na Bylkankaldanpeaskat",
        },
        "location": [2828.2, 1689.3],
        "language": "Tebarian",
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "English": "Squirrels' Forest",
            "Tebarian": "Na Bylkanseivanlias",
            "West Kargadian": "Na Bylkanseivulias",
        },
        "location": [3283.0, 1553.2],
        "language": "Tebarian",
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "English": "Squirrels' Swamp",
            "Tebarian": "Na Bylkantaivead",
            "West Kargadian": "Na Bylkantaivead",
        },
        "location": [3274.3, 1564.4],
        "language": "Tebarian",
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "English": "The Wild Lands",
            "Tebarian": "Na Degan Ihat",
            "West Kargadian": "Na Degaeltat",
        },
        "location": [3539.7, 1536.5],
        "language": "Tebarian",
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "English": "Ekspi City",
            "East Kargadian": "Ekspigar",
        },
        "location": [2560.4, 317.3],
        "language": "East Kargadian",
        "planet": "Kargadia",
        "region": "Na Vadenaran Irrat",
    },
    {
        "name": {
            "English": "Erelltown",
            "West Kargadian": "Erellgar",
        },
        "location": [1275.5, 944.2],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "English": "Erda Desert",
            "West Kargadian": "Erdapeaskat",
        },
        "location": [504.1, 1140.6],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "English": "Hunta Shore",
            "Tebarian": "Huntavall",
        },
        "location": [1542.2, 1529.9],
        "language": "Tebarian",
        "planet": "Kargadia",
        "region": "Na Ihat na Iidain",
    },
    {
        "name": {
            "English": "The Land of the Dead",
            "Tebarian": "Na Iha na Sevarddain",
            "West Kargadian": "Na Elta na Sevarddain"
        },
        "location": [2791.5, 1745.7],
        "language": "Tebarian",
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "English": "Irtangar",
            "East Kargadian": "Irtangar",
        },
        "location": [2731.3, 163.8],
        "language": "East Kargadian",
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "English": "The Hill of Challenges",
            "Tebarian": "Na Kalvus na Advuräin",
            "West Kargadian": "Na Kalvus na Advuräin"
        },
        "location": [2791.5, 1745.7],
        "language": "Tebarian",
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "English": "Northern End Kargadia",
            "West Kargadian": "Kanerakainead",
        },
        "location": [1015.0, 100.8],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": "Kanernehtivia",
    },
    {
        "name": {
            "English": "Northern Tebaria",
            "Tebarian": "Kanertebaria",
            "West Kargadian": "Kanertebaria",
        },
        "location": [666.6, 1515.9],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "English": "Kyomi City",
            "East Kargadian": "Kiomigar",
        },
        "location": [2628.7, 349.0],
        "language": "East Kargadian",
        "planet": "Kargadia",
        "region": "Na Vadenaran Irrat",
    },
    {
        "name": {
            "English": "Mountain City",
            "West Kargadian": "Kirtinangar",
        },
        "location": [953.3, 319.2],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": "Na Kirtinnat Lurvun",
    },
    {
        "name": {
            "English": "Kitnagar",
            "East Kargadian": "Kitnagar",
        },
        "location": [3005.5, 1240.0],
        "language": "East Kargadian",
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "English": "Squirrels' Temple",
            "Tebarian": "Kunval na Bylkain",
            "West Kargadian": "Kunval na Bylkain",
        },
        "location": [2464.0, 1414.1],
        "language": "Tebarian",
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "English": "Shamans' Temple",
            "Tebarian": "Kunval na Shaivain",
            "West Kargadian": "Kunval na Shaivain",
        },
        "location": [2623.3, 1624.5],
        "language": "Tebarian",
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "English": "Lakkeaina",
            "East Kargadian": "Lakkeáina",
        },
        "location": [2662.6, 673.6],
        "language": "East Kargadian",
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "English": "Leita City",
            "West Kargadian": "Leitagar",
        },
        "location": [335.4, 318.4],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": "Na Irrat",
    },
    {
        "name": {
            "English": "Lersedigar",
            "West Kargadian": "Lersédigar",
        },
        "location": [1417.2, 631.3],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "English": "The Soaring Heights",
            "Tebarian": "Na Liidennan Koirantat",
            "West Kargadian": "Na Liidennan Koirantat",
        },
        "location": [317.7, 1664.1],
        "language": "Tebarian",
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "English": "The Volcano of Shadows",
            "Tebarian": "Na Lirrinta Teinain",
            "West Kargadian": "Na Lirkinta Teinain",
        },
        "location": [25.0, 1598.4],
        "language": "Tebarian",
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "English": "Muruvasaitari",
            "East Kargadian": "Muruvasáitari",
        },
        "location": [2614.2, 526.3],
        "language": "East Kargadian",
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "English": "Neikelaa",
            "East Kargadian": "Neikélaa",
        },
        "location": [1960.6, 733.1],
        "language": "East Kargadian",
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "English": "Nurvutton",
            "Tebarian": "Nurvutgar",
        },
        "location": [2114.1, 1498.2],
        "language": "Tebarian",
        "planet": "Kargadia",
        "region": "Seanka Tebaria",
    },
    {
        "name": {
            "English": "Orla City",
            "West Kargadian": "Orlagar",
        },
        "location": [342.7, 346.7],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": "Na Irrat",
    },
    {
        "name": {
            "English": "The City of Five",
            "West Kargadian": "Pakigar",
        },
        "location": [347.5, 376.0],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": "Na Irrat",
    },
    {
        "name": {
            "English": "Desert City",
            "West Kargadian": "Peaskar",
        },
        "location": [510.0, 642.4],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": "Na Peaskat na Jegittain",
    },
    {
        "name": {
            "English": "Regan Shores",
            "West Kargadian": "Regavall",
        },
        "location": [1295.3, 210.8],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": "Regaazdal",
    },
    {
        "name": {
            "English": "Rega-City",
            "West Kargadian": "Reggar",
        },
        "location": [1236.4, 300.0],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": "Regaazdal",
    },
    {
        "name": {
            "English": "South Pole Kargadia",
            "Tebarian": "Seankar Kainead",
            "West Kargadian": "Senankar Kainead",
        },
        "location": [2670.4, 1800.0],
        "language": "Tebarian",
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "English": "Senko's Lair",
            "West Kargadian": "Senkadar Laikadu",
        },
        "location": [1031.7, 548.6],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": "Senkadar Laikadu",
    },
    {
        "name": {
            "English": "Sentagar",
            "West Kargadian": "Sentagar",
        },
        "location": [1691.2, 495.3],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "English": "Central Tebaria",
            "Tebarian": "Sentatebaria",
            "West Kargadian": "Sentatebaria",
        },
        "location": [602.3, 1610.5],
        "language": "Tebarian",
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "English": "Shiro's Playground",
            "West Kargadian": "Shiradar Koankadu",
        },
        "location": [1145.7, 501.1],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": "Senkadar Laikadu",
    },
    {
        "name": {
            "English": "Shawn City",
            "West Kargadian": "Shonangar",
        },
        "location": [344.1, 347.8],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": "Na Irrat",
    },
    {
        "name": {
            "English": "Steir City",
            "West Kargadian": "Steirigar",
        },
        "location": [305.2, 538.2],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": "Sertanehtivia",
    },
    {
        "name": {
            "English": "Valleys of the Sun",
            "Tebarian": "Na Sunovalliat",
            "West Kargadian": "Na Sunonvailantat",
        },
        "location": [157.2, 1462.2],
        "language": "Tebarian",
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "English": "Suager City",
            "West Kargadian": "Suvagar",
        },
        "location": [1220.0, 293.2],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": "Regaazdal",
    },
    {
        "name": {
            "English": "Tebaria Bridge",
            "Tebarian": "Tebarimost",
            "West Kargadian": "Tebarimostus",
        },
        "location": [636.2, 1524.7],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "English": "The Dark Cave",
            "Tebarian": "Na Tentar Hintakadu",
            "West Kargadian": "Na Temannar Hintakadu",
        },
        "location": [2877.7, 1579.9],
        "language": "Tebarian",
        "planet": "Kargadia",
        "region": "Na Ihat na TBL'n",
    },
    {
        "name": {
            "English": "The Egyptians' Pyramid",
            "West Kargadian": "Na Tevakta na Jegittain",
        },
        "location": [707.7, 624.2],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": "Na Peaskat na Jegittain",
    },
    {
        "name": {
            "English": "The Warm Shores",
            "West Kargadian": "Tevivall",
        },
        "location": [982.3, 576.2],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": "Vadernehtivia",
    },
    {
        "name": {
            "English": "Vaidoks",
            "East Kargadian": "Vaidoks",
        },
        "location": [2754.5, 986.3],
        "language": "East Kargadian",
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "English": "Potato City",
            "West Kargadian": "Vintelingar",
        },
        "location": [1485.2, 892.5],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": None,
    },
    {
        "name": {
            "English": "Equator City",
            "West Kargadian": "Virsetgar",
        },
        "location": [1800.0, 900.0],
        "language": "West Kargadian",
        "planet": "Kargadia",
        "region": None,
    },

    {
        "name": {
            "English": "Border City",
            "West Kargadian": "Gar a na Redenan",
            "Kaltarena Kargadian": "Serenaanaa"
        },
        "location": [2375.6, 1133.2],
        "language": "Kaltarena Kargadian, Usturian",
        "planet": "Qevenerus",
        "region": "Kaltarena"
    },
    {
        "name": {
            "English": "Kaltarena City",
            "West Kargadian": "Kaltarena",
            "Kaltarena Kargadian": "Haltaren",
            "Usturian": "Khupatsad Usturat"
        },
        "location": [2100.0, 655.1],
        "language": "Kaltarena Kargadian, Usturian",
        "planet": "Qevenerus",
        "region": "Kaltarena"
    },
    {
        "name": {
            "English": "Northern End Kaltarena",
            "West Kargadian": "Kanerar Kainead",
            "Kaltarena Kargadian": "Hanerahaane",
        },
        "location": [2283.1, 191.0],
        "language": "Kaltarena Kargadian",
        "planet": "Qevenerus",
        "region": "Kaltarena"
    },
    {
        "name": {
            "English": "Equatorial Shores",
            "West Kargadian": "Sertavall",
            "Kaltarena Kargadian": "Seetaaveşhu",
        },
        "location": [2408.4, 900.0],
        "language": "Kaltarena Kargadian, Usturian",
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

    def location(self, indent: bool = False):
        lat, long = self.lat, self.long
        n, e = "N" if lat >= 0 else "S", "E" if long >= 0 else "W"
        if lat < 0:
            lat *= -1
        if long < 0:
            long *= -1
        return f"{lat:>5.2f}°{n}, {long:>6.2f}°{e}" if indent else f"{lat:.2f}°{n}, {long:.2f}°{e}"

    def get_location(self):
        # planet, x, y, *data = places_old[self.place]
        place = None
        for _place in places:
            if self.name in _place["name"].values():
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
        names = "\n".join(f"{language}: **{name}**" for language, name in place["name"].items())
        name = place["name"]["English"]
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
        local_time = f"**{_time.str()}**"
        language = place["language"]
        if planet == "Kargadia":
            if language == "West Kargadian":
                _local_time = times.time_kargadia(self.now, tz, 'rsl-1k')
            elif language == "East Kargadian":
                _local_time = times.time_kargadia(self.now, tz, 'rsl-1m')
            elif language == "Tebarian":
                _local_time = times.time_kargadia(self.now, tz, 'rsl-1i')
            else:
                _local_time = _time
            local_time = f"**{_local_time.str(dow=False, month=False)}**"
        elif planet == "Qevenerus":
            if language == "Kaltarena Kargadian, Usturian":
                ka_time = times.time_qevenerus_ka(self.now, tz)
                us_time = times.time_qevenerus_us(self.now, tz)
                local_time = f"Ka. Kargadian: **{ka_time.str(dow=False, month=False)}**\nUsturian: **{us_time.str(dow=False, month=False)}**"
            elif language == "Kaltarena Kargadian":
                ka_time = times.time_qevenerus_ka(self.now, tz)
                local_time = f"**{ka_time.str(dow=False, month=False)}**"

        # if planet == "Virkada":
        #     local_time = f"**{_time.str()}**"
        # _data = len(data)
        # local_names = None
        # if _data == 0:
        #     _local_time = _time
        #     local_time = f"**{_time.str(dow=False, month=False)}**"
        #     region = None
        # else:
        #     lang_region = data[0]
        #     if planet == "Virkada":
        #         _local_time = times.time_virkada(self.now, tz)
        #         local_time = f"**{_local_time.str()}**\nLocal language: **{data[0]}**"
        #         region = "Virkada"
        #     elif planet == "Kargadia":
        #         if lang_region == "Tebaria":
        #             _local_time = times.time_kargadia(self.now, tz, 'rsl-1i')
        #             local_time = f"**{_local_time.str(dow=False, month=False)}**"
        #         elif lang_region in ["Nehtivia", "Nittavia", "Erellia", "Centeria", "Island"]:
        #             _local_time = times.time_kargadia(self.now, tz, 'rsl-1k')
        #             local_time = f"**{_local_time.str(dow=False, month=False)}**"
        #         else:
        #             # Should be RSL-1m: Uses RSL-1k for placeholder, as RSL-1m does not yet exist.
        #             _local_time = times.time_kargadia(self.now, tz, 'rsl-1k')
        #             local_time = f"**{_local_time.str(dow=False, month=False)}**"
        #         region = data[1]
        #     elif planet == "Qevenerus":
        #         if lang_region == "Kaltarena":
        #             _local_time = times.time_qevenerus_ka(self.now, tz)
        #             usturian = times.time_qevenerus_us(self.now, tz)
        #             local_time = f"\nKargadian: **{_local_time.str(dow=False, month=False)}**\n" \
        #                          f"Usturian: **{usturian.str(dow=False, month=False)}**\n" \
        #                          f"Gestedian: **Placeholder**\n"
        #         else:
        #             _local_time = _time
        #             local_time = "Local time unknown... So far."
        #         region = data[0]
        #         local_names = f"Ka. Kargadian: {data[1]}\nUsturian: {data[2]}"
        #     else:
        #         _local_time = _time
        #         local_time = "Local time unknown"
        #         region = None
        return name, names, planet, lat, long, tz, _time, local_time, region, language

    def status(self):
        embed = discord.Embed(colour=general.random_colour())
        place_name = f"{self.name}, {self.planet}" if self.region is None else f"{self.name}, {self.region}, {self.planet}"
        embed.title = f"Information about **{place_name}**"
        # embed.add_field(name="Time and Location", inline=False,
        #                 value=f"Local time: {self.local_time}\n"
        #                       f"Time zone: **{self.tz:+}:00** (Real offset {self.long / (360 / 24):+.2f} hours)\n"
        #                       f"Location: **{self.location(False)}**")
        embed.add_field(name="Local Time", value=self.local_time, inline=False)
        embed.add_field(name="Timezone", value=f"**{self.tz:+}:00** (Real offset {self.long / (360 / 24):+.2f} hours)", inline=False)
        embed.add_field(name="Location", value=self.location(False), inline=False)
        embed.add_field(name="Local Names", value=self.names, inline=False)
        embed.add_field(name="Local Language(s)", value=self.language, inline=False)

        if self.weathers is not None:
            # Remove non-ascii stuff like äá to make sure it's only A-Z
            _name = self.name[:8].encode("ascii", "replace").replace(b"?", b"0").replace(b" ", b"0")
            _seed0 = int(_name, base=36)
            _seed1 = self.time.ds * 1440  # Seed the day from 1/1/0001, multiplied by 1440 minutes.
            _seed2 = self.time.hour * 60
            seed = _seed0 + _seed1
            seed2 = seed + _seed2

            temp_min, temp_max = self.weathers["temperature"][self.time.month - 1][self.sun.day_part]
            temp = general.random1(temp_min, temp_max, seed)
            temp_c = round(temp, 1)
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
            speed_kmh = round(wind, 1)
            speed_mps = round(wind / 3.6, 1)
            # embed.add_field(name="Wind speed", value=f"**{speed_kmh} km/h** | {speed_mps} m/s", inline=False)

            humidity_max = self.weathers["humidity_max"][self.time.month - 1]
            humidity_min = self.weathers["humidity_min"][self.time.month - 1]
            humidity = general.random1(humidity_min, humidity_max, seed2)
            # embed.add_field(name="Humidity", value=f"{humidity:.0%}", inline=False)

            rain_chance = self.weathers["rain_chance"][self.time.month - 1]  # [month - 1]
            rain = general.random1(0, 100, seed2) <= rain_chance
            if rain:
                if -2.5 > temp_c > 2.5:
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
            # embed.add_field(name="Sky's mood", value=rain_out, inline=False)
            output = f"Temperature: **{temp_c}°C**\n" \
                     f"Wind speed: **{speed_kmh} km/h** | **{speed_mps} m/s**\n" \
                     f"Humidity: **{humidity:.0%}**\n" \
                     f"Sky's mood: **{rain_out}**"
            embed.add_field(name="Weather", value=output, inline=False)
        else:
            embed.add_field(name="Weather", value="Weather not available", inline=False)
            # embed.description += "\n\nWeather conditions not available."

        embed.add_field(name="About the Sun", value=self.sun.sun_data, inline=False)
        embed.set_footer(text=f"Astronomical season: {self.sun.season.title()}")
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
        if self.place.lat not in [90, -90]:
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
        parts = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"]
        direction = parts[int(((heading + 22.5) % 360) / 45)]
        sun_data += f"\nThe sun is due {direction} ({heading:.0f}°)"
        return solar_noon, sunrise, sunset, dawn, dusk, sun_data, day_part, season
