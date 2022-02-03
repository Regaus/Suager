import json
import re
from datetime import datetime
from math import ceil

import discord
from discord.ext import commands
from regaus import conworlds, PlaceDoesNotExist, time as time2

from utils import bot_data, conlangs, general, time

longest_city = {
    "Virkada": 15,
    "Kargadia": 19,
    "Qevenerus": 19,
}


class Conworlds(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.command(name="time78", aliases=["t78"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def time78(self, ctx: commands.Context, place_name: str, _date: str = None, _time: str = None):
        """ Times for GA-78
        Date format: `YYYY-MM-DD`
        Time format: `hh:mm` or `hh:mm:ss` (24-hour)

        Example: ..time78 Reggar 2021-07-18 20:00"""
        if _date is None:
            dt = time.now(None)
        else:
            try:
                if not _time:
                    _time = "00:00:00"
                else:
                    _time = _time.replace(".", ":")
                    c = _time.count(":")
                    if c == 1:
                        _time = f"{_time}:00"
                dt = time.set_tz(datetime.strptime(f"{_date} {_time}", "%Y-%m-%d %H:%M:%S"), "UTC")
            except ValueError:
                return await general.send("Failed to convert date. Make sure it is in the format `YYYY-MM-DD hh:mm:ss` (time part optional)", ctx.channel)
        time_earth = self.bot.language2("english").time(dt, short=0, dow=True, seconds=True, tz=False)  # True, False, True, True, False
        output = f"Time on Earth: **{time_earth}**"
        _pre = "on"
        if place_name == "Kargadia":
            _name = _id = "Kargadia"
            place_name = "South Pole Kargadia"
        elif place_name == "Qevenerus":
            _name = _id = "Qevenerus"
            place_name = "Kaltarena Qevenerus"
        elif place_name == "Virkada":
            _name = _id = "Virkada"
            place_name = "Virkada Central"
        else:
            _pre = "in"
            _name = place_name
            _id = None
        place = conworlds.Place(place_name, time2.datetime.from_datetime(dt))
        if _id is None:
            _id = place.id
        output += f"\nTime {_pre} {_id}: **{place.time.strftime('%A, %d %B %Y, %H:%M:%S', 'en')}**"
        return await general.send(output, ctx.channel)

    # @commands.command(name="timelocation", aliases=["tl"])
    # @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    # async def time_location78(self, ctx: commands.Context, *, where: str):
    #     try:
    #         place = conworlds.Place(where)
    #         return await general.send(place.time_info(), ctx.channel)
    #     except PlaceDoesNotExist:
    #         return await general.send(f"Location {where!r} not found.", ctx.channel)

    @commands.group(name="weather78", aliases=["data78", "w78", "d78"], case_insensitive=True, invoke_without_command=True)
    # @commands.is_owner()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def weather78(self, ctx: commands.Context, *, where: str):
        """ Weather for a place in GA78 """
        if ctx.invoked_subcommand is None:
            try:
                language = self.bot.language(ctx)
                if re.search(r"( -lod[012])$", where):
                    lod = int(where[-1])  # 0, 1 or 2
                    where = where[:-6]
                else:
                    # LOD 2 Channel Names: hidden-commands,   secretive-commands, secretive-commands-2
                    if ctx.channel.id in [610482988123422750, 742885168997466196, 753000962297299005]:
                        lod = 2
                    # LOD 1 Channel Names:  secret-room-1,      secret-room-2,      secret-room-3,      secret-room-8,      secret-room-10      Kargadia commands
                    elif ctx.channel.id in [671520521174777869, 672535025698209821, 681647810357362786, 725835449502924901, 798513492697153536, 938582514166034514]:
                        lod = 1
                    else:
                        lod = 0  # All other channels are "untrusted", so default to LOD 0
                place = conworlds.Place(where)
                embed, icon = place.status(language.language, level_of_detail=lod)
                return await general.send(None, ctx.channel, embed=embed, file=icon)
            except PlaceDoesNotExist:
                return await general.send(f"Location {where!r} not found.", ctx.channel)

    @weather78.command(name="list", aliases=["locations", "loc"])
    async def ga78_locations(self, ctx: commands.Context, *, planet: str = "Kargadia"):
        """ See the list of all available locations on a planet """
        _places = []
        _longest = longest_city[planet]
        # for city, data in places.places_old.items():
        for city in conworlds.places:
            if city["planet"] == planet:
                place = conworlds.Place(city["id"])
                _places.append(f"`{place.id:<{_longest}} - {conworlds.format_location(place.lat, place.long, True, 'en')}`")
        if len(_places) <= 25:
            return await general.send(f"Locations in {planet}:\n\n" + "\n".join(_places), ctx.channel)
        else:
            await general.send(f"Locations in {planet}:", ctx.channel)
            for i in range(ceil(len(_places) / 20)):
                j = i * 20
                await general.send("\n".join(_places[j:j + 20]), ctx.channel)

    @commands.command(name="location", aliases=["loc"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def location(self, ctx: commands.Context, *, where: str):
        """ See where a place in GA-78 is located """
        # TODO: Make this also show the map coordinates (rounded off to 1)
        try:
            place = conworlds.Place(where)
            return await general.send(f"{where} - {place.planet} - {conworlds.format_location(place.lat, place.long, False, 'en')}", ctx.channel)
        except PlaceDoesNotExist:
            return await general.send(f"Location {where!r} not found.", ctx.channel)

    @commands.command(name="nlc")
    @commands.is_owner()
    async def ne_world_ll_calc(self, ctx: commands.Context, x: int, z: int, border: int = 100000):
        """ Calculate latitude and local offset of position """
        lat = -z / border * 90  # Latitude value
        long = x / border * 180
        # tzl = 48 / 180
        # tz = round(long / tzl)
        tz = round(long / (360 / 24))
        tzo = (tz * (360 / 24) - long) * -1  # Local Offset
        return await general.send(f"At {x=:,} and {z=:,} (World Border at {border:,}):\nLatitude: {lat:.3f}\nLongitude: {long:.3f} | Local Offset: {tzo:.3f}", ctx.channel)

    @commands.command("rslt")
    @commands.check(lambda ctx: ctx.author.id in [302851022790066185, 236884090651934721, 291665491221807104])
    async def rsl_encode(self, ctx: commands.Context, s: int, *, t: str):
        """ Laikattart Sintuvut """
        if not (1 <= s <= 8700):
            return await general.send("De dejava edea, no maikal, ir te ean kihterasva.", ctx.channel)
        shift = s * 128
        _code = "--code" in t
        code = ""
        # code = rsl_number(s)
        if _code:
            code = conlangs.rsl_number(s, 10, "rsl-1i")
            t = t.replace(" --code", "").replace("--code ", "")
        try:
            text = "".join([chr(ord(letter) + shift) for letter in t])
        except ValueError:
            return await general.send(f"Si valse, alteknaar ka un kudalsan kihteran", ctx.channel)
        return await general.send(f"{code} {text}", ctx.channel)

    @commands.command("rslf")
    @commands.check(lambda ctx: ctx.author.id in [302851022790066185, 236884090651934721, 291665491221807104])
    async def rsl_decode(self, ctx: commands.Context, s: int, *, t: str):
        """ Laikattarad Sintuvuad """
        if not (1 <= s <= 8700):
            return await general.send("De dejava edea, no maikal, ir te ean kihterasva.", ctx.channel)
        shift = s * 128
        text = ""
        for letter in t:
            try:
                a = chr(ord(letter) - shift)
            except ValueError:
                a = chr(0)
            text += a
        return await general.send(text, ctx.channel)

    @commands.command(name="ga78")
    @commands.is_owner()
    async def ga78_info(self, ctx: commands.Context, ss: int = None, p: int = None):
        """ Details on GA-78
         ss = solar system """
        data = json.loads(open("assets/ga78.json").read())
        if ss is None:  # Solar system not specified
            systems = []
            for number, system in data.items():
                systems.append(f"SS-{number}: {system['name']}")
            return await general.send(f"Here is the list of all solar systems. For details on a specific one, enter `{ctx.prefix}{ctx.invoked_with} x` "
                                      f"(replace x with system number)", ctx.channel, embed=discord.Embed(colour=0xff0057, description="\n".join(systems)))
        try:
            system = data[str(ss)]
        except KeyError:
            return await general.send(f"No data is available for SS-{ss}.", ctx.channel)
        if p is None:
            sun = system["sun"]
            output = f"Sun:\nName in RSL-1: {sun['name']}\n"
            mass = sun['mass']  # Mass
            lum = mass ** 3.5   # Luminosity
            d = mass ** 0.74    # Diameter
            st = mass ** 0.505  # Surface temperature
            lt = mass ** -2.5   # Lifetime
            output += f"Mass: {mass:.2f} Solar\nLuminosity: {lum:.2f} Solar\nDiameter: {d:.2f} Solar\nSurface Temp.: {st:.2f} Solar\nLifetime: {lt:.2f} Solar" \
                      f"\n\nPlanets:\n"
            planets = []
            for number, planet in system["planets"].items():
                planets.append(f"{number}) {planet['name']}")
            output += "\n".join(planets)
            return await general.send(f"Here is the data on SS-{ss}. For details on a specific planet, use `{ctx.prefix}{ctx.invoked_with} {ss} x`\n"
                                      f"__Note: Yes, planet numbers start from 2. That is because the star was counted as the number 1.__",
                                      ctx.channel, embed=discord.Embed(colour=0xff0057, description=output))
        try:
            planet = system["planets"][str(p)]
        except KeyError:
            return await general.send(f"No data is available for planet {p} of SS-{ss}.", ctx.channel)
        output = f"Name in RSL-1: {planet['name']}\nLocal name(s): {planet['local']}\n"
        output += f"Distance from sun: {planet['distance']:.2f} AU\nAverage temperature: {planet['temp']:.2f}°C\n"
        day = planet["day"]
        days = day / 24
        year = planet["year"]
        years = year / 365.256
        local = year / days
        output += f"Day length: {day:,.2f} Earth hours ({days:,.2f} Earth days)\n"
        output += f"Year length: {year:,.2f} Earth days ({years:,.2f} Earth years) | {local:,.2f} local solar days"
        return await general.send(f"Information on planet `87.78.{ss}.{p}`:", ctx.channel, embed=discord.Embed(colour=0xff0057, description=output))


def setup(bot: bot_data.Bot):
    bot.add_cog(Conworlds(bot))
