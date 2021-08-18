import json
from datetime import datetime
from math import ceil

import discord
from discord.ext import commands

from utils import bot_data, conlangs, general, places, time, times

longest_city = {
    "Virkada": 20,
    "Kargadia": 22,
    "Qevenerus": 22,
}


class Conworlds(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.command(name="time78", aliases=["t78"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def time78(self, ctx: commands.Context, ss: int, pl: int, _date: str = None, _time: str = None):
        """ Times for GA-78
        Date format: `YYYY-MM-DD`
        Time format: `hh:mm` or `hh:mm:ss` (24-hour)

        Example: ..time78 23 5 2021-07-18 20:00"""
        if ss < 1 or ss > 100:
            return await general.send("The SS number must be between 1 and 100.", ctx.channel)
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
        output = f"Earth - English: **{time_earth}**"
        if ss == 23:
            if pl == 3:
                if dt < time.dt(2004, 1, 28):
                    return await general.send("Time on Virkada is not available before 28th January 2021 AD", ctx.channel)
                output += f"\nVirkada - All: **{times.time_virkada(dt, 0).str()}**"
            elif pl == 4:
                if dt < time.dt(60, 12, 6):
                    return await general.send("Time on Zeivela is not available before 6th December 60 AD", ctx.channel)
                output += f"\nZeivela - Local: **{times.time_zeivela(dt, 0).str()}**"
            elif pl == 5:
                if dt < time.dt(276, 12, 27):
                    return await general.send("Time on Kargadia is not available before 27th December 276 AD", ctx.channel)
                time_earth1k = self.bot.language2("rsl-1k").time(dt, short=0, dow=True, seconds=True, tz=False)
                time_earth1i = self.bot.language2("rsl-1i").time(dt, short=0, dow=True, seconds=True, tz=False)
                time_23_5k = times.time_kargadia(dt, 0, "rsl-1k").str()  # 23.5 Kargadia RSL-1k
                time_23_5i = times.time_kargadia(dt, 0, "rsl-1i").str()  # 23.5 Kargadia RSL-1i
                output += f"\nEarth - W. Kargadian: **{time_earth1k}**" \
                          f"\nEarth - Tebarian: **{time_earth1i}**\n" \
                          f"\nKargadia - W. Kargadian: **{time_23_5k}**" \
                          f"\nKargadia - Tebarian: **{time_23_5i}**"
            elif pl == 6:
                if dt < time.dt(1686, 11, 22):
                    return await general.send("Time on Qevenerus is not available before 22nd November 1686 AD", ctx.channel)
                time_earth1h = self.bot.language2("rsl-1h").time(dt, short=0, dow=True, seconds=True, tz=False)
                output += f"\nEarth - Ka. Kargadian: **{time_earth1h}**\n" \
                          f"\nQevenerus - Ka. Kargadian: **{times.time_qevenerus_ka(dt, 0).str()}**" \
                          f"\nQevenerus - Usturian: **{times.time_qevenerus_us(dt, 0).str()}**" \
                          f"\nQevenerus - Ka. Gestedian: **Placeholder**"
            else:
                return await general.send(f"No time is available for {ss}.{pl} right now.", ctx.channel)
        elif ss == 24:
            if pl == 4:
                if dt < time.dt(476, 1, 28):
                    return await general.send("Time on Sinvimania is not available before 28th January 476 AD", ctx.channel)
                output += f"\nSinvimania - RLC-10: **{times.time_sinvimania(dt, 0).str()}**"
            elif pl == 5:
                if dt < time.dt(171, 7, 2):
                    return await general.send("Time on Hosvalnerus is not available before 2nd July 171 AD", ctx.channel)
                output += f"\nHosvalnerus - Local: **{times.time_hosvalnerus(dt, 0).str()}**"
            elif pl == 11:
                if dt < time.dt(1742, 1, 28):
                    return await general.send("Time on Kuastall is not available before 28th January 1742 AD", ctx.channel)
                output += f"\nKuastall - RSL-1e: **{times.time_kuastall_11(dt).str()}**"
            else:
                return await general.send(f"No time is available for {ss}.{pl} right now.", ctx.channel)
        else:
            output += f"\nNo times are available for SS-{ss}."
        return await general.send(output, ctx.channel)

    @commands.command(name="timelocation", aliases=["tl"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def time_location78(self, ctx: commands.Context, *, where: str):
        try:
            place = places.Place(where)
            return await general.send(place.time_info(), ctx.channel)
        except places.PlaceDoesNotExist:
            return await general.send(f"Location {where!r} not found.", ctx.channel)

    @commands.command(name="weather78", aliases=["data78", "w78", "d78"])
    # @commands.is_owner()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def weather78(self, ctx: commands.Context, *, where: str):
        """ Weather for a place in GA78 """
        try:
            place = places.Place(where)
            embed = place.status()
            return await general.send(None, ctx.channel, embed=embed)
        except places.PlaceDoesNotExist:
            return await general.send(f"Location {where!r} not found.", ctx.channel)

    @commands.command(name="locations", aliases=["location", "loc"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def location(self, ctx: commands.Context, *, where: str):
        """ Locations of Places in GA-78

        Input a planet (e.g. Kargadia) to see list of all locations on the planet
        Input a place to see where it is"""
        # if where:
        if where in ["Virkada", "Zeivela", "Kargadia", "Qevenerus"]:
            _places = []
            _longest = longest_city[where]
            # for city, data in places.places_old.items():
            for city in places.places:
                if city["planet"] == where:
                    place = places.Place(city["name"]["English"])
                    _places.append(f"`{place.name:<{_longest}} - {place.location(True)}`")
            if len(_places) <= 25:
                return await general.send(f"Locations in {where}:\n\n" + "\n".join(_places), ctx.channel)
            else:
                await general.send(f"Locations in {where}:", ctx.channel)
                for i in range(ceil(len(_places) / 20)):
                    j = i * 20
                    await general.send("\n".join(_places[j:j+20]), ctx.channel)
        else:
            try:
                place = places.Place(where)
                return await general.send(f"{where} - {place.planet} - {place.location(False)}", ctx.channel)
            except places.PlaceDoesNotExist:
                return await general.send(f"Location {where!r} not found.", ctx.channel)
        # else:
        #     planets = []
        #     for data in places.places_old.values():
        #         if data[0] not in planets:
        #             planets.append(data[0])
        #     return await general.send("Planets with locations available:\n\n" + "\n".join(planets), ctx.channel)

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
