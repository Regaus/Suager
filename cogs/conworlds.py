import json
import re
from math import ceil

import discord
from discord import app_commands
from pytz.tzinfo import DstTzInfo
from regaus import conworlds, PlaceDoesNotExist, random_colour, time, version_info
from thefuzz import process

from utils import bot_data, commands, conlangs, conworlds as conworlds2, views, general, languages, interactions

longest_city = {
    "Virkada": 15,
    "Kargadia": 20,
    "Qevenerus": 19,
}


CITIZEN_LANGUAGES: list[app_commands.Choice[str]] = [  # List of languages which can be used to generate citizens
    app_commands.Choice(name="Nuunvallian (Regaazdallian)", value="re_nu"),
    app_commands.Choice(name="Kaltelan (Regaazdallian)", value="re_kl"),
    app_commands.Choice(name="Munearan (Regaazdallian)", value="re_mu"),
    app_commands.Choice(name="Kovanerran (Regaazdallian)", value="re_kv"),
    app_commands.Choice(name="Vaidanvallian", value="vv"),
    # app_commands.Choice(name="Kaltanazdallian", value="kz"),
]


class Conworlds(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        self.places: list[conworlds.Place] = [conworlds.Place(place["id"]) for place in conworlds.places if place["priority"] < 2]  # Exclude hidden and generated places from showing up as suggestions
        # Partial checks match just the first part of the coordinates, giving autocomplete suggestions for the second value
        self.lat_long_check = re.compile(r"^(-?\d{1,2}\.?\d*),\s?(-?\d{1,3}\.?\d*)$")
        self.partial_lat_long_check = re.compile(r"^(-?\d{1,2}\.?\d*),?\s?$")
        self.coordinate_check = re.compile(r"^c(\d{1,4}\.?\d*),\s?(\d{1,4}\.?\d*)$")
        self.partial_coordinate_check = re.compile(r"^c(\d{1,4}\.?\d*),?\s?$")

    async def place_autocomplete(self, interaction: discord.Interaction, current: str, with_planets: bool, with_coords: bool) -> list[app_commands.Choice[str]]:
        """ Generic autocomplete for place names """
        language = languages.Language.get(interaction, personal=True)
        if with_coords:  # Return some special choices if we match coordinates
            if re.match(self.lat_long_check, current):
                x, y = current.split(",")
                return [app_commands.Choice(name="Coordinates: " + conworlds.format_location(float(x), float(y), indent=False, language=language.language), value=current)]
            elif re.match(self.coordinate_check, current):
                x, y = current[1:].split(",")
                return [app_commands.Choice(name=f"Map coordinates: ({float(x):.2f}, {float(y):.2f})", value=current)]
            elif re.match(self.partial_lat_long_check, current):
                lat = float(current.rstrip().rstrip(","))
                longs = list(range(-180, 181, 15))
                return [app_commands.Choice(name="Coordinates: " + conworlds.format_location(lat, long, indent=False, language=language.language), value=f"{lat},{long}") for long in longs]
            elif re.match(self.partial_coordinate_check, current):
                x = float(current[1:].rstrip().rstrip(","))
                ys = list(range(0, 1801, 100))
                return [app_commands.Choice(name=f"Map coordinates: ({float(x):.2f}, {float(y):.2f})", value=f"c{x},{y}") for y in ys]
        results: list[tuple[str, str, int]] = []
        for place in self.places:
            ratios = (process.default_scorer(current, place.id), process.default_scorer(current, place.names["en"]), process.default_scorer(current, place.names.get(language.language)))
            place_name = place.names.get(language.language, place.names["en"])                               # Fall back to English place name
            location = language.data("weather78_regions").get(place.state, {"_self": place.state})["_self"]  # Fall back to internal state name
            results.append((f"{place_name} ({location})", place.id, max(ratios)))
        if with_planets:
            planets: dict[str, str] = language.data("weather78_planets")
            for key, value in planets.items():  # key = internal name, value = localised name
                if key == "Zeivela":  # Skip Zeivela for now, since there are no settlements on it, nor is there a calendar
                    continue
                ratios = (process.default_scorer(current, key), process.default_scorer(current, value))
                results.append((value, key, max(ratios)))
        results.sort(key=lambda r: r[2], reverse=True)
        return [app_commands.Choice(name=name, value=value) for name, value, _ in results[:25]]

    async def place_name_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """ Autocomplete for commands that use a place name """
        return await self.place_autocomplete(interaction, current, False, False)

    async def place_name_with_planets(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """ Autocomplete for commands that use a place name but can also take in a planet name """
        return await self.place_autocomplete(interaction, current, True, False)

    async def place_name_with_coords(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """ Autocomplete for commands that use a place name but can also take in coordinates """
        return await self.place_autocomplete(interaction, current, False, True)

    @commands.hybrid_command(name="time78", aliases=["t78"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @app_commands.autocomplete(place_name=place_name_with_planets)
    @app_commands.rename(_date="date", _time="time")
    @app_commands.describe(
        place_name="The name of the place for which to look up time. Must be a valid name of a settlement or planet.",
        _date="The date on Earth. Must be in the format \"YYYY-MM-DD\". Defaults to today.",
        _time="The time on Earth. Must be either \"hh:mm\" or \"hh:mm:ss\". If date is specified, defaults to midnight.",
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def time78(self, ctx: commands.Context, place_name: str, _date: str = None, _time: str = None):
        """ Convert time for places in Kargadia and nearby planets
        Date format: `YYYY-MM-DD`
        Time format: `hh:mm` or `hh:mm:ss` (24-hour)

        Example: ..time78 Reggar 2021-07-18 20:00"""
        await ctx.defer(ephemeral=True)
        if _date is None and _time is None:
            dt = time.datetime.now(tz=self.bot.timezone(ctx.author.id, time_class="Earth"))
        else:
            try:
                if not _time:
                    time_part = time.time()  # 0:00:00
                else:
                    _h, _m, *_s = _time.split(":")
                    h, m, s = int(_h), int(_m), int(_s[0]) if _s else 0
                    time_part = time.time(h, m, s, 0, time.utc)
                if not _date:
                    date_part = time.date.today()
                else:
                    _y, _m, _d = _date.split("-")
                    y, m, d = int(_y), int(_m), int(_d)
                    date_part = time.date(y, m, d, time.Earth)
                dt = time.datetime.combine(date_part, time_part, time.utc)
                dt2 = dt.as_timezone(self.bot.timezone(ctx.author.id, time_class="Earth"))
                dt = dt.replace(tz=dt2.tzinfo)
                # _expiry = dt.to_timezone(time.timezone.utc).to_datetime().replace(tzinfo=None)  # convert into a datetime object with null tzinfo
            except ValueError:
                if _time and not _date:
                    message = "Failed to convert time. Make sure it is in the format `hh:mm` or `hh:mm:ss`."
                elif _date and not _time and ctx.interaction:
                    message = "Failed to convert date. Make sure it is in the format `YYYY-MM-DD`."
                elif _date and not _time:
                    message = "Failed to convert date and time. Make sure the date is in the format `YYYY-MM-DD`. If you wish to also specify a time, the overall format is `YYYY-MM-DD hh:mm:ss`."
                else:
                    message = "Failed to convert date and time. Make sure the date is in the format `YYYY-MM-DD` and the time is in the format `hh:mm` or `hh:mm:ss`."
                return await ctx.send(message, ephemeral=True)
        # time_earth = self.bot.language2("english").time(dt, short=0, dow=True, seconds=True, tz=False)  # True, False, True, True, False
        if isinstance(dt.tzinfo, DstTzInfo):
            tz_name = dt.tzinfo._tzname  # type: ignore
        else:
            tz_name = dt.tz_name()
        time_earth = dt.strftime("%A, %d %B %Y, %H:%M:%S ", "en") + tz_name
        output = f"Time on Earth: **{time_earth}**"
        _pre = "on"
        if place_name == "Kargadia":
            _name = "Kargadia"
            place_name = "Virsetgar"
        elif place_name == "Qevenerus":
            _name = "Qevenerus"
            place_name = "Kaltarena Qevenerus"
        elif place_name == "Virkada":
            _name = "Virkada"
            place_name = "Virkada Central"
        else:
            _pre = "in"
            _name = None
        place = conworlds.Place(place_name, dt)
        if _name is None:
            _name = place.name_translation(ctx.language2("en"))
        output += f"\nTime {_pre} {_name}: **{place.time.strftime('%A, %d %B %Y, %H:%M:%S %Z', 'en')}**"
        return await ctx.send(output, ephemeral=True)

    @commands.hybrid_command(name="kaage", aliases=["age"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @app_commands.rename(_date="date")
    @app_commands.describe(_date="The date on which you were born, in YYYY-MM-DD format. Example: 2024-12-09")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def ka_age(self, ctx: commands.Context, _date: str):
        """ Get your Kargadian birthday and age """
        await ctx.defer(ephemeral=True)
        language = ctx.language2("en")
        _y, _m, _d = _date.split("-")
        y, m, d = int(_y), int(_m), int(_d)
        birthday_earth = time.date(y, m, d, time_class=time.Earth)
        birthday_ka = birthday_earth.convert_time_class(time.Kargadia)
        now_ka = time.date.today(time.Kargadia)
        age_rd = time.relativedelta(now_ka, birthday_ka)
        bd1 = language.date(birthday_earth, short=0, dow=False, year=True)
        bd2 = language.date(birthday_ka, short=0, dow=False, year=True)
        age = language.delta_rd(age_rd, accuracy=3, brief=False, affix=False)
        _age = f"\nYou would be **{age}** old on Kargadia" if birthday_earth < time.date.today() else ""  # Only include age information if the specified date is earlier than today
        return await ctx.send(f"Your Earth birthday is: **{bd1}**\nYour Kargadian birthday is: **{bd2}**{_age}", ephemeral=True)

    @commands.hybrid_command(name="weather78", aliases=["data78", "w78", "d78", "place"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @app_commands.autocomplete(where=place_name_autocomplete)
    @app_commands.rename(where="place_name", lod="level_of_detail")
    @app_commands.describe(
        where="The name of the place for which to look up the weather. Must be a valid settlement name",
        lod="The amount of details in the output"
    )
    @app_commands.choices(lod=[
        app_commands.Choice(name="Maximum", value=3),
        app_commands.Choice(name="High", value=2),
        app_commands.Choice(name="Average", value=1),
        app_commands.Choice(name="Minimal", value=0),
    ])
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def weather78(self, ctx: commands.Context, *, where: str, lod: int = None):
        """ Look up the current weather for a place in Kargadia

         To manually change the level of detail, add `-lod0`, `-lod1`, `-lod2`, or `-lod3` after the place name. """
        await ctx.defer(ephemeral=True)
        if re.search(r"( -lod[0-3])$", where):
            lod = int(where[-1])  # one of: 0, 1, 2, 3
            where = where[:-6]
        elif lod is None:
            # LOD 3 Channel Names: secretive-commands
            if ctx.channel.id in [742885168997466196]:
                lod = 3
            # LOD 2 Channel Names:  hidden-commands,  secretive-commands-2
            elif ctx.channel.id in [610482988123422750, 753000962297299005]:
                lod = 2
            # LOD 1 Channel Names:  secret-room-1,      secret-room-2,      secret-room-3,      secret-room-8,      secret-room-10,     secret-room-13,     Kargadia commands,
            #                       secret-room-14,     secret-room-15,     secret-room-16,     secret-room-17      secret-room-18,     secret-room-21,     secret-room-22,
            #                       secret-room-24
            elif ctx.channel.id in [671520521174777869, 672535025698209821, 681647810357362786, 725835449502924901, 798513492697153536, 958489459672891452, 938582514166034514,
                                    965801985716666428, 969720792457822219, 971195522830442527, 972112792624726036, 999750177181147246, 999750231539335338, 999750252775084122,
                                    999750295095623753]:
                lod = 1
            else:
                lod = 0  # All other channels are "untrusted", so default to LOD 0
        language = languages.Language.get(ctx, personal=True)
        try:
            place = conworlds.Place(where)
            embed, icon = place.status(language.language, level_of_detail=lod)
            return await ctx.send(embed=embed, file=icon, ephemeral=True)
        except PlaceDoesNotExist:
            return await ctx.send(language.string("weather78_place_not_found", place=where), ephemeral=True)

    @commands.hybrid_group(name="locations", aliases=["location", "loc"], case_insensitive=True, invoke_without_command=True, fallback="get")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @app_commands.autocomplete(where=place_name_autocomplete)
    @app_commands.rename(where="place_name")
    @app_commands.describe(where="The name of the place for which to look up location details")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def location(self, ctx: commands.Context, *, where: str):
        """ Find where a place in Kargadia is located """
        if ctx.invoked_subcommand is None:
            await ctx.defer(ephemeral=True)
            language = languages.Language.get(ctx, personal=True)
            try:
                place = conworlds.Place(where)
                if int(version_info) >= 4329072128:  # v1.2.8
                    coords = f" ({place.x:.0f}, {place.y:.0f})"
                else:
                    coords = ""
                return await ctx.send(f"{where} - {place.planet} - {conworlds.format_location(place.lat, place.long, False, language.language)}{coords}", ephemeral=True)
            except PlaceDoesNotExist:
                return await ctx.send(language.string("weather78_place_not_found", place=where), ephemeral=True)

    @location.command(name="list", aliases=["locations", "loc"])
    @app_commands.describe(planet="The planet whose places to list")
    @app_commands.choices(planet=[
        app_commands.Choice(name="Kargadia", value="Kargadia"),
        app_commands.Choice(name="Virkada", value="Virkada"),
        # app_commands.Choice(name="Zeivela", value="Zeivela"),
        app_commands.Choice(name="Jevenerus", value="Qevenerus"),
    ])
    async def ga78_locations(self, ctx: commands.Context, *, planet: str = "Kargadia"):
        """ List all available places on a planet """
        async with ctx.typing(ephemeral=True):
            language = languages.Language.get(ctx, personal=True)
            _places = []
            _longest = longest_city[planet]
            # for city, data in places.places_old.items():
            for city in conworlds.places:
                if city["planet"] == planet:
                    if city["priority"] < 2:
                        place = conworlds.Place(city["id"])
                        _places.append(f"`{place.id:<{_longest}} - {conworlds.format_location(place.lat, place.long, True, language.language)}`")
            start = language.string("weather78_locations_list", planet=planet)
            if len(_places) <= 25:
                return await ctx.send(f"{start}\n\n" + "\n".join(_places), ephemeral=True)
            else:
                # await ctx.send(f"Locations on {planet}:", ephemeral=True)
                for i in range(ceil(len(_places) / 20)):
                    j = i * 20
                    await ctx.send((start + "\n" if i == 0 else "") + "\n".join(_places[j:j + 20]), ephemeral=True)
                return

    @commands.hybrid_command(name="distance", aliases=["dist"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @app_commands.autocomplete(origin=place_name_with_coords, destination=place_name_with_coords)
    @app_commands.describe(
        origin="Place name (\"Reggar\"), coordinates (\"60.00,-53.48\"), or map coordinates (\"c1265,300\").",
        destination="Place name (\"Reggar\"), coordinates (\"60.00,-53.48\"), or map coordinates (\"c1265,300\").",
        planet="The planet on which to calculate distance. Only used if origin and destination are both coordinates."
    )
    @app_commands.choices(planet=[
        app_commands.Choice(name="Earth", value="Earth"),
        app_commands.Choice(name="Kargadia", value="Kargadia"),
        app_commands.Choice(name="Virkada", value="Virkada"),
        app_commands.Choice(name="Zeivela", value="Zeivela"),
        app_commands.Choice(name="Jevenerus", value="Qevenerus"),
    ])
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def distance(self, ctx: commands.Context, origin: str, destination: str, planet: str = None):
        """ Calculate the distance between two places in Kargadia
        The distance cannot be calculated if the two places are located on two different planets
        The planet argument is only used for calculations using coordinates instead of place names (defaults to Kargadia if none specified)
        You can mix places and coordinates together if you want

        Example using place name: `..distance Reggar "Rakkan Lintina"`
        Example using coordinates: `..distance "60.00,-53.48" "22.00,-77.48" Kargadia` """
        await ctx.defer(ephemeral=True)

        # Check if the origin is a coordinate or a place name
        try:
            if re.match(self.lat_long_check, origin):
                x, y = origin.split(",")
                lat1, long1 = float(x), float(y)
                planet1 = planet
                name1 = conworlds.format_location(lat1, long1)
            elif re.match(self.coordinate_check, origin):
                x, y = origin[1:].split(",")
                x1, y1 = float(x), float(y)
                lat1, long1 = conworlds.calc_position(x1, y1, planet if planet else "Kargadia")
                planet1 = planet
                name1 = conworlds.format_location(lat1, long1)
            else:
                place1 = conworlds.Place(origin)
                lat1, long1 = place1.lat, place1.long
                planet1 = place1.planet
                name1 = place1.names["en"]
        except ValueError:  # PlaceDoesNotExist and invalid coordinates will both raise a ValueError
            return await ctx.send(f"Location {origin!r} is not a valid place or coordinate.", ephemeral=True)

        # Do the same for the destination
        try:
            if re.match(self.lat_long_check, destination):
                x, y = destination.split(",")
                lat2, long2 = float(x), float(y)
                planet2 = planet
                name2 = conworlds.format_location(lat2, long2)
            elif re.match(self.coordinate_check, destination):
                x, y = destination[1:].split(",")
                x2, y2 = float(x), float(y)
                lat2, long2 = conworlds.calc_position(x2, y2, planet if planet else "Kargadia")
                planet2 = planet
                name2 = conworlds.format_location(lat2, long2)
            else:
                place2 = conworlds.Place(destination)
                lat2, long2 = place2.lat, place2.long
                planet2 = place2.planet
                name2 = place2.names["en"]
        except ValueError:
            return await ctx.send(f"Location {destination!r} is not a valid place or coordinate.", ephemeral=True)

        if planet1 is None and planet2 is not None:
            planet = planet2
        elif planet1 is not None and planet2 is None:
            planet = planet1
        elif planet1 != planet2:
            return await ctx.send(f"These two places are on different planets ({planet1} and {planet2}). Distance cannot be calculated.", ephemeral=True)
        elif planet1 is None and planet2 is None:
            planet = "Kargadia"
        else:
            planet = planet1
        del planet1, planet2

        # try:
        #     radius = radii[planet]
        # except KeyError:
        #     return await ctx.send(f"{planet!r} is not a valid planet.")

        try:
            distance = conworlds2.distance_between_places(lat1, long1, lat2, long2, planet)
        except ValueError as e:
            return await ctx.send(str(e), ephemeral=True)
        metric, imperial = ctx.language2("en").length(distance * 1000, precision=2).split(" | ")
        return await ctx.send(f"The distance between **{name1}** and **{name2}** is **{metric}** (**{imperial}**).", ephemeral=True)

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
        return await ctx.send(f"At {x=:,} and {z=:,} (World Border at {border:,}):\nLatitude: {lat:.3f}\nLongitude: {long:.3f} | Local Offset: {tzo:.3f}")

    @commands.command("rslt")
    @commands.check(lambda ctx: ctx.author.id in [302851022790066185, 236884090651934721, 291665491221807104])
    async def rsl_encode(self, ctx: commands.Context, s: int, *, t: str):
        """ Laikattart Sintuvut """
        if not (1 <= s <= 8700):
            return await ctx.send("De tuava eden, ta te en kihteravas.")
        shift = s * 128
        _code = "--code" in t
        code = ""
        # code = rsl_number(s)
        if _code:
            code = conlangs.rsl_number(s, "ka_re")
            t = t.replace(" --code", "").replace("--code ", "")
        try:
            text = "".join([chr(ord(letter) + shift) for letter in t])
        except ValueError:
            return await ctx.send(f"Si valse, altekaar ka un kudalsan kihteran")
        return await ctx.send(f"{code} {text}")

    @commands.command("rslf")
    @commands.check(lambda ctx: ctx.author.id in [302851022790066185, 236884090651934721, 291665491221807104])
    async def rsl_decode(self, ctx: commands.Context, s: int, *, t: str):
        """ Laikattarad Sintuvuad """
        if not (1 <= s <= 8700):
            return await ctx.send("De tuava eden, ta te en kihteravas.")
        shift = s * 128
        text = ""
        for letter in t:
            try:
                a = chr(ord(letter) - shift)
            except ValueError:
                a = chr(0)
            text += a
        return await ctx.send(text)

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
            return await ctx.send(f"Here is the list of all solar systems. For details on a specific one, enter `{ctx.prefix}{ctx.invoked_with} x` "
                                  f"(replace x with system number)", embed=discord.Embed(colour=0xff0057, description="\n".join(systems)))
        try:
            system = data[str(ss)]
        except KeyError:
            return await ctx.send(f"No data is available for SS-{ss}.")
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
            return await ctx.send(f"Here is the data on SS-{ss}. For details on a specific planet, use `{ctx.prefix}{ctx.invoked_with} {ss} x`\n"
                                  f"__Note: Yes, planet numbers start from 2. That is because the star was counted as the number 1.__",
                                  embed=discord.Embed(colour=0xff0057, description=output))
        try:
            planet = system["planets"][str(p)]
        except KeyError:
            return await ctx.send(f"No data is available for planet {p} of SS-{ss}.")
        output = f"Name in RSL-1: {planet['name']}\nLocal name(s): {planet['local']}\n"
        output += f"Distance from sun: {planet['distance']:.2f} AU\nAverage temperature: {planet['temp']:.2f}°C\n"
        day = planet["day"]
        days = day / 24
        year = planet["year"]
        years = year / 365.256
        local = year / days
        output += f"Day length: {day:,.2f} Earth hours ({days:,.2f} Earth days)\n"
        output += f"Year length: {year:,.2f} Earth days ({years:,.2f} Earth years) | {local:,.2f} local solar days"
        return await ctx.send(f"Information on planet `87.78.{ss}.{p}`:", embed=discord.Embed(colour=0xff0057, description=output))

    async def kargadia_profile_command(self, ctx: commands.Context | discord.Interaction, user_id: int | None):
        """ Wrapper for the Kargadia profile command """
        if isinstance(ctx, discord.Interaction):
            ctx: commands.Context = await commands.Context.from_interaction(ctx)
        await ctx.defer(ephemeral=True)
        language = ctx.language2("en")
        if user_id is None:
            user_id = ctx.author.id
        # if not (await ctx.bot.is_owner(ctx.author)) and user.id not in [ctx.author.id, 302851022790066185, 609423646347231282, 577608850316853251]:
        #     return await ctx.send("Locked for now - You can only access your own profile, as well as Regaus's, Suager's, and CobbleBot's...")
        data = self.bot.db.fetchrow("SELECT * FROM kargadia WHERE uid=? OR id=?", (user_id, user_id))
        if not data:
            return await ctx.send("A citizen profile is not available for this user.", ephemeral=True)

        # 1 - Protected profiles may only be seen by me and the user themselves
        protection_check = ctx.author.id in [302851022790066185, data["uid"]]
        # 2 - Age can only be seen by me and the user themselves within my testing server or in DMs.
        age_check = protection_check and ((ctx.guild is not None and ctx.guild.id == 738425418637639775) or ctx.guild is None)

        if data["protected"] & 1 and not protection_check:  # 1 = Protected, 3 = Protected + Age hidden
            return await ctx.send("You may not view this user's citizen profile.", ephemeral=True)

        embed = discord.Embed(colour=random_colour())
        name = " ".join([n for n in [data["name"], data["name2"], data["name3"]] if n is not None])

        try:
            user = await self.bot.fetch_user(data["uid"])  # Since we don't know if user_id is a user ID or a citizen ID
            username = general.username(user)
            embed.set_thumbnail(url=str(user.display_avatar.replace(size=1024, static_format="png")))
        except discord.NotFound:
            username = data["name"]

        embed.title = f"{username}'s Kargadian Citizen Profile"
        embed.add_field(name="Citizen ID", value=data["id"], inline=True)
        # embed.add_field(name="User ID", value=data["uid"], inline=True)

        embed.add_field(name="Kargadian Name", value=name, inline=False)

        genders = {"m": "Male", "f": "Female", "n": "Non-binary or other", "u": "Unknown"}
        embed.add_field(name="Gender", value=genders.get(data["gender"]), inline=True)

        if data["birthday"]:
            birthday = time.date.from_iso(data["birthday"], time.Kargadia)
            if data["protected"] & 2 and not age_check:  # Age privacy is the "2" bit
                birthday_text = language.date(birthday, short=0, dow=False, year=False)
                embed.add_field(name="Birthday", value=birthday_text, inline=False)
            else:
                birthday_text = language.date(birthday, short=1, dow=False, year=True)
                birthday_time = time.datetime.combine(birthday, time.time(6, 0, 0), tz=language.get_timezone(data["uid"], "Kargadia"))
                age = language.delta_dt(birthday_time, accuracy=2, brief=False, affix=False)
                embed.add_field(name="Birthday and Age", value=f"{birthday_text} - {age}", inline=False)
        else:
            embed.add_field(name="Birthday", value="Unavailable", inline=False)

        if data["location"]:
            try:
                place = conworlds.Place(data["location"])
                location = place.name_translation(language)

                if place.state:
                    regions = language.data("weather78_regions")
                    state_data = regions.get(place.state)
                    state = state_data["_self"] if state_data is not None else place.state
                    location += ", " + state
            except PlaceDoesNotExist:
                location = data["location"]
            embed.add_field(name="Location", value=location, inline=False)
        else:
            embed.add_field(name="Location", value="Unavailable", inline=False)

        if data["joined"]:
            joined = time.date.from_iso(data["joined"], time.Earth)
            embed.add_field(name="Joined the cult on", value=language.date(joined, short=1, dow=False, year=True), inline=False)
        else:
            embed.add_field(name="Joined the cult on", value="Not a cult member", inline=False)
        return await ctx.send(embed=embed, ephemeral=True)

    @commands.hybrid_group(name="kargadian-profile", aliases=["kargadianprofile", "kargadiaprofile", "kargadia", "kp", "citizen", "citizenship", "profile"],
                           case_insensitive=True, invoke_without_command=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def kargadia_profile(self, ctx: commands.Context, _user: commands.UserID = None):
        """ Your Kargadian citizen ID

         When using as a text command, your own profile is shown if you don't specify the user.
         To see someone else's profile, specify either their username/user ID or their Kargadian citizen ID.

         When using as a slash command, use the `check` subcommand to specify either the user or their citizen ID."""
        if ctx.invoked_subcommand is None:
            return await self.kargadia_profile(ctx, _user)

    @kargadia_profile.command(name="check", hidden=True)
    @app_commands.describe(
        user="The user whose profile to check",
        citizen_id="The citizen ID of the user whose profile to check. This field is ignored if a user is specified."
    )
    async def kargadia_profile_check(self, ctx: commands.Context, *, user: discord.User = None, citizen_id: int = None):
        """ Check your or someone else's Kargadian profile """
        if user is None and citizen_id is None:
            _user = None
        elif user is not None:
            _user = user.id
        else:
            _user = citizen_id
        return await self.kargadia_profile_command(ctx, _user)

    @kargadia_profile.command(name="add", with_app_command=False)
    @commands.is_owner()
    async def ka_citizen_add(self, ctx: commands.Context, _id: int, uid: int, name: str = None, name2: str = None, name3: str = None, gender: str = None,
                             birthday: str = None, location: str = None, joined: str = None):
        """ Add a new Kargadian citizen to the database """
        output = self.bot.db.execute("INSERT INTO kargadia(id, uid, protected, name, name2, name3, gender, birthday, has_role, location, joined) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                     (_id, uid, 2, name, name2, name3, gender, birthday, False, location, joined))  # Hide age by default
        return await ctx.send(output)

    @kargadia_profile.command(name="edit", aliases=["update"], with_app_command=False)
    @commands.is_owner()
    async def ka_citizen_edit(self, ctx: commands.Context, _id: int, key: str, value: str):
        """ Edit a Kargadian citizen's profile """
        output = self.bot.db.execute(f"UPDATE kargadia SET {key}=? WHERE id=? OR uid=?", (value, _id, _id))
        return await ctx.send(output)

    @kargadia_profile.command(name="delete", aliases=["del", "remove"], with_app_command=False)
    @commands.is_owner()
    async def ka_citizen_delete(self, ctx: commands.Context, _id: int):
        """ Delete a Kargadian citizen's profile """
        output = self.bot.db.execute("DELETE FROM kargadia WHERE id=?", (_id,))
        return await ctx.send(output)

    @kargadia_profile.group(name="age", aliases=["birthdate", "birthday"])
    async def ka_citizen_age(self, ctx: commands.Context):
        """ Controls for whether your age is shown or not """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @ka_citizen_age.command(name="show", aliases=["enable", "optin"])
    async def ka_citizen_age_enable(self, ctx: commands.Context):
        """ Show your age in your Kargadian profile """
        await ctx.defer(ephemeral=True)
        profile = self.bot.db.fetchrow("SELECT protected FROM kargadia WHERE uid=?", (ctx.author.id,))
        if profile["protected"] & 2:
            self.bot.db.execute("UPDATE kargadia SET protected=protected-2 WHERE uid=?", (ctx.author.id,))
            return await ctx.send("Your age will now be displayed on your Kargadian profile.", ephemeral=True)
        else:
            return await ctx.send("Your age is already being displayed on your Kargadian profile.", ephemeral=True)

    @ka_citizen_age.command(name="hide", aliases=["disable", "optout"])
    async def ka_citizen_age_disable(self, ctx: commands.Context):
        """ Hide your age from your Kargadian profile """
        await ctx.defer(ephemeral=True)
        profile = self.bot.db.fetchrow("SELECT protected FROM kargadia WHERE uid=?", (ctx.author.id,))
        if not profile["protected"] & 2:
            self.bot.db.execute("UPDATE kargadia SET protected=protected+2 WHERE uid=?", (ctx.author.id,))
            return await ctx.send("Your age will no longer be displayed on your Kargadian profile. Note that you can still see your age if you look at your own profile in DMs.", ephemeral=True)
        else:
            return await ctx.send("Your age is already hidden from your Kargadian profile.", ephemeral=True)

    # def check_birthday(self, user_id):
    #     data = self.bot.db.fetchrow(f"SELECT * FROM kargadia WHERE uid=? OR id=?", (user_id, user_id))
    #     return data["birthday"] if data else None

    async def birthday_command(self, ctx: commands.Context | discord.Interaction, _user: int | None):
        """ Wrappper for the birthday command """
        if isinstance(ctx, discord.Interaction):
            ctx: commands.Context = await commands.Context.from_interaction(ctx)
        await ctx.defer(ephemeral=True)
        language = ctx.language()
        if _user is None:
            _user = ctx.author.id
        if _user == self.bot.user.id:
            return await ctx.send(language.string("birthdays_birthday_cobble"), ephemeral=True)
        # has_birthday = self.check_birthday(_user)

        data = self.bot.db.fetchrow(f"SELECT * FROM kargadia WHERE uid=? OR id=?", (_user, _user))
        if data is None:
            return await ctx.send(language.string("birthdays_birthday_not_saved", user=self.bot.get_user(_user)), ephemeral=True)
        try:
            user = await self.bot.fetch_user(data["uid"])  # Since we don't know if _user is a user ID or a citizen ID
            username = general.username(user)
        except discord.NotFound:
            username = data["name"]
            user = self.bot.user  # Use the bot's user account so the tz check doesn't fail
        if data["birthday"] is None:
            return await ctx.send(language.string("birthdays_birthday_not_saved", user=username), ephemeral=True)
        _user = "your" if user == ctx.author else "general"
        birthday_date = time.date.from_iso(data["birthday"], time.Kargadia)
        birthday = language.date(birthday_date, short=0, dow=False, year=False)
        tz = language.get_timezone(user.id, "Kargadia")
        now = time.datetime.now(tz, time.Kargadia)  # - time.timedelta(hours=6)  # Kargadian birthdays pass at 6am, and this is a crutchy way to reflect that here
        birthday_start = time.datetime.combine(birthday_date.replace(year=now.year), time.time(6, 0, 0), tz)
        is_birthday = now > birthday_start and (now - birthday_start) < time.timedelta(days=1)
        if is_birthday:
            return await ctx.send(language.string(f"birthdays_birthday_{_user}_today", user=username, date=birthday), ephemeral=True)
        birthday_start.replace_self(year=now.year)  # Set the date to the current year, then add another one if it's already passed
        if now > birthday_start:
            birthday_start.replace_self(year=now.year + 1)
        # birthday_time = time.datetime.combine(birthday_date, time.time(6, 0, 0), tz)
        delta = language.delta_dt(birthday_start, accuracy=2, brief=False, affix=True)
        earth_time = birthday_start.to_earth_time()  # .to_tz(language.get_timezone(user.id, "Earth"))
        earth = language.time(earth_time, short=1, dow=False, seconds=False, tz=True, at=True, uid=ctx.author.id)
        return await ctx.send(language.string(f"birthdays_birthday_{_user}_ka", user=username, date=birthday, delta=delta, earth=earth), ephemeral=True)

    @commands.command(name="birthday", aliases=['b', 'bd', 'birth', 'day'])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def birthday(self, ctx: commands.Context, *, _user: commands.UserID = None):
        """ Check your or someone else's Kargadian birthday"""
        return await self.birthday_command(ctx, _user)

    @app_commands.command(name="birthday")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @app_commands.describe(
        user="The user whose Kargadian birthday to check",
        citizen_id="The citizen ID of the user whose birthday to check. This field is ignored if a user is specified."
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def birthday_slash(self, interaction: discord.Interaction, *, user: discord.User = None, citizen_id: int = None):
        """ Check your or someone else's Kargadian birthday """
        interactions.log_interaction(interaction)
        if user is None and citizen_id is None:
            _user = None
        elif user is not None:
            _user = user.id
        else:
            _user = citizen_id
        return await self.birthday_command(interaction, _user)

    @commands.hybrid_group(name="generate", aliases=["gen"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def generate(self, ctx: commands.Context):
        """ Generate random Kargadian citizens """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @generate.command(name="names", aliases=["name"])
    @app_commands.describe(language="The language in which the names will be generated. Defaults to Nuunvallian.")
    @app_commands.choices(language=CITIZEN_LANGUAGES)
    async def generate_name(self, ctx: commands.Context, language: str = "re_nu"):
        """ Generate a few random Kargadian names """
        await ctx.defer(ephemeral=True)
        content, error = conworlds2.generate_citizen_names(language)
        message = await ctx.send(content, ephemeral=True)
        if not error:
            view = views.GenerateNamesView(sender=ctx.author, message=message, language=language, ctx=ctx)
            return await message.edit(view=view)

    @generate.command(name="citizen")
    @app_commands.rename(citizen_language="language")
    @app_commands.describe(citizen_language="The native language of the random citizen. Uses a random language if unspecified.")
    @app_commands.choices(citizen_language=CITIZEN_LANGUAGES)
    async def generate_citizen(self, ctx: commands.Context, citizen_language: str = None):
        """ Generate a random Kargadian citizen
        If no language is specified, a random available language will be used """
        await ctx.defer(ephemeral=True)
        embed, error = conworlds2.generate_citizen_embed(citizen_language)
        if error:
            return await ctx.send(content=embed, ephemeral=True)
        else:
            message = await ctx.send(embed=embed, ephemeral=True)
            view = views.GenerateCitizenView(sender=ctx.author, message=message, language=citizen_language, ctx=ctx)
            return await message.edit(view=view)


async def setup(bot: bot_data.Bot):
    cog = Conworlds(bot)
    await bot.add_cog(cog)

    @bot.tree.context_menu(name="Check Kargadian Profile")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def ctx_check_kargadian_profile(interaction: discord.Interaction, user: discord.Member | discord.User):
        """ Context menu to check a user's Kargadian profile """
        interactions.log_interaction(interaction)
        return await cog.kargadia_profile_command(interaction, user.id)

    @bot.tree.context_menu(name="Check Kargadian Birthday")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def ctx_check_birthday(interaction: discord.Interaction, user: discord.Member | discord.User):
        """ Context menu to check a user's birthday """
        interactions.log_interaction(interaction)
        return await cog.birthday_command(interaction, user.id)
