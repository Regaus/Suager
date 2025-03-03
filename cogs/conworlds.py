import json
import re
from math import ceil

import discord
from pytz.tzinfo import DstTzInfo
from regaus import conworlds, PlaceDoesNotExist, random_colour, time, version_info

from utils import bot_data, commands, conlangs, conworlds as conworlds2, views, general

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
            dt = time.datetime.now(tz=self.bot.timezone(ctx.author.id, time_class="Earth"))
        else:
            try:
                if not _time:
                    time_part = time.time()  # 0:00:00
                else:
                    _h, _m, *_s = _time.split(":")
                    h, m, s = int(_h), int(_m), int(_s[0]) if _s else 0
                    time_part = time.time(h, m, s, 0, time.utc)
                _y, _m, _d = _date.split("-")
                y, m, d = int(_y), int(_m), int(_d)
                date_part = time.date(y, m, d, time.Earth)
                dt = time.datetime.combine(date_part, time_part, time.utc)
                dt2 = dt.as_timezone(self.bot.timezone(ctx.author.id, time_class="Earth"))
                dt.replace_self(tz=dt2.tzinfo)
                _expiry = dt.to_timezone(time.timezone.utc).to_datetime().replace(tzinfo=None)  # convert into a datetime object with null tzinfo
            except ValueError:
                return await ctx.send("Failed to convert date. Make sure it is in the format `YYYY-MM-DD hh:mm:ss` (time part optional)")
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
        return await ctx.send(output)

    @commands.command(name="kaage", aliases=["age"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def ka_age(self, ctx: commands.Context, _date: str):
        """ Get your Kargadian birthday and age """
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
        return await ctx.send(f"Your Earth birthday is: **{bd1}**\nYour Kargadian birthday is: **{bd2}**\nYou would be **{age}** old on Kargadia")

    @commands.group(name="weather78", aliases=["data78", "w78", "d78", "place"], case_insensitive=True, invoke_without_command=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def weather78(self, ctx: commands.Context, *, where: str):
        """ Weather for a place in GA78 """
        if ctx.invoked_subcommand is None:
            try:
                language = self.bot.language(ctx)
                if re.search(r"( -lod[0-3])$", where):
                    lod = int(where[-1])  # one of: 0, 1, 2, 3
                    where = where[:-6]
                else:
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
                place = conworlds.Place(where)
                embed, icon = place.status(language.language, level_of_detail=lod)
                return await ctx.send(embed=embed, file=icon)
            except PlaceDoesNotExist:
                return await ctx.send(f"Location {where!r} not found.")

    @weather78.command(name="list", aliases=["locations", "loc"])
    async def ga78_locations(self, ctx: commands.Context, *, planet: str = "Kargadia"):
        """ See the list of all available locations on a planet """
        _places = []
        _longest = longest_city[planet]
        # for city, data in places.places_old.items():
        for city in conworlds.places:
            if city["planet"] == planet:
                if city["priority"] < 2:
                    place = conworlds.Place(city["id"])
                    _places.append(f"`{place.id:<{_longest}} - {conworlds.format_location(place.lat, place.long, True, 'en')}`")
        if len(_places) <= 25:
            return await ctx.send(f"Locations on {planet}:\n\n" + "\n".join(_places))
        else:
            await ctx.send(f"Locations on {planet}:")
            for i in range(ceil(len(_places) / 20)):
                j = i * 20
                await ctx.send("\n".join(_places[j:j + 20]))

    @commands.command(name="location", aliases=["loc"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def location(self, ctx: commands.Context, *, where: str):
        """ See where a place in GA-78 is located """
        try:
            place = conworlds.Place(where)
            if int(version_info) >= 4329072128:  # v1.2.8
                coords = f" ({place.x:.0f}, {place.y:.0f})"
            else:
                coords = ""
            return await ctx.send(f"{where} - {place.planet} - {conworlds.format_location(place.lat, place.long, False, 'en')}{coords}")
        except PlaceDoesNotExist:
            return await ctx.send(f"Location {where!r} not found.")

    @commands.command(name="distance", aliases=["dist"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def distance(self, ctx: commands.Context, origin: str, destination: str, planet: str = None):
        """ Calculate the distance between two places in SS-23
        The distance cannot be calculated if the two places are located on two different planets
        The planet argument is only used for calculations using coordinates instead of place names (defaults to Kargadia if none specified)
        You can mix places and coordinates together if you want

        Example using place name: `..distance Reggar "Rakkan Lintina"`
        Example using coordinates: `..distance "60.00,-53.48" "22.00,-77.48" Kargadia` """
        lat_long_check = re.compile(r"^(-?\d{1,2}\.?\d*),(\s?)(-?\d{1,3}\.?\d*)$")
        coordinate_check = re.compile(r"^c(\d{1,4}\.?\d*),(\s?)(\d{1,4}\.?\d*)$")

        # Check if the origin is a coordinate or a place name
        try:
            if re.match(lat_long_check, origin):
                x, y = origin.split(",")
                lat1, long1 = float(x), float(y)
                planet1 = planet
                name1 = conworlds.format_location(lat1, long1)
            elif re.match(coordinate_check, origin):
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
            return await ctx.send(f"Location {origin!r} is not a valid place or coordinate.")

        # Do the same for the destination
        try:
            if re.match(lat_long_check, destination):
                x, y = destination.split(",")
                lat2, long2 = float(x), float(y)
                planet2 = planet
                name2 = conworlds.format_location(lat2, long2)
            elif re.match(coordinate_check, destination):
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
            return await ctx.send(f"Location {destination!r} is not a valid place or coordinate.")

        if planet1 is None and planet2 is not None:
            planet = planet2
        elif planet1 is not None and planet2 is None:
            planet = planet1
        elif planet1 != planet2:
            return await ctx.send(f"These two places are on different planets ({planet1} and {planet2}). Distance cannot be calculated.")
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
            return await ctx.send(str(e))
        metric, imperial = ctx.language2("en").length(distance * 1000, precision=2).split(" | ")
        return await ctx.send(f"The distance between **{name1}** and **{name2}** is **{metric}** (**{imperial}**).")

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

    @commands.group(name="kargadiaprofile", aliases=["kargadianprofile", "kargadia", "kp", "citizen", "citizenship", "profile"], case_insensitive=True, invoke_without_command=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def kargadia_profile(self, ctx: commands.Context, _user: commands.UserID = None):
        """ Your Kargadian citizen ID """
        if ctx.invoked_subcommand is None:
            # return await ctx.send_help(ctx.command)
            language = ctx.language2("en")
            if _user is None:
                _user = ctx.author.id
            # if not (await ctx.bot.is_owner(ctx.author)) and user.id not in [ctx.author.id, 302851022790066185, 609423646347231282, 577608850316853251]:
            #     return await ctx.send("Locked for now - You can only access your own profile, as well as Regaus's, Suager's, and CobbleBot's...")
            data = self.bot.db.fetchrow("SELECT * FROM kargadia WHERE uid=? OR id=?", (_user, _user))
            if not data:
                return await ctx.send("A citizen profile is not available for this user.")

            # 1 - Protected profiles may only be seen by me and the user themselves
            protection_check = ctx.author.id in [302851022790066185, data["uid"]]
            # 2 - Age can only be seen by me and the user themselves within my testing server or in DMs.
            age_check = protection_check and ((ctx.guild is not None and ctx.guild.id == 738425418637639775) or ctx.guild is None)

            if data["protected"] & 1 and not protection_check:  # 1 = Protected, 3 = Protected + Age hidden
                return await ctx.send("You may not view this user's citizen profile.")

            embed = discord.Embed(colour=random_colour())
            name = " ".join([n for n in [data["name"], data["name2"], data["name3"]] if n is not None])

            try:
                user = await self.bot.fetch_user(data["uid"])  # Since we don't know if _user is a user ID or a citizen ID
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
            return await ctx.send(embed=embed)

    @kargadia_profile.command(name="add")
    @commands.is_owner()
    async def ka_citizen_add(self, ctx: commands.Context, _id: int, uid: int, name: str = None, name2: str = None, name3: str = None, gender: str = None,
                             birthday: str = None, location: str = None, joined: str = None):
        """ Add a new Kargadian citizen to the database """
        output = self.bot.db.execute("INSERT INTO kargadia(id, uid, protected, name, name2, name3, gender, birthday, has_role, location, joined) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                     (_id, uid, 2, name, name2, name3, gender, birthday, False, location, joined))  # Hide age by default
        return await ctx.send(output)

    @kargadia_profile.command(name="edit", aliases=["update"])
    @commands.is_owner()
    async def ka_citizen_edit(self, ctx: commands.Context, _id: int, key: str, value: str):
        """ Edit a Kargadian citizen's profile """
        output = self.bot.db.execute(f"UPDATE kargadia SET {key}=? WHERE id=? OR uid=?", (value, _id, _id))
        return await ctx.send(output)

    @kargadia_profile.command(name="delete", aliases=["del", "remove"])
    @commands.is_owner()
    async def ka_citizen_delete(self, ctx: commands.Context, _id: int):
        """ Delete a Kargadian citizen's profile """
        output = self.bot.db.execute("DELETE FROM kargadia WHERE id=?", (_id,))
        return await ctx.send(output)

    @kargadia_profile.group(name="age", aliases=["birthdate"])
    async def ka_citizen_age(self, ctx: commands.Context):
        """ Controls for whether your age is shown or not """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @ka_citizen_age.command(name="show", aliases=["enable", "optin"])
    async def ka_citizen_age_enable(self, ctx: commands.Context):
        """ Show your age in your Kargadian profile """
        profile = self.bot.db.fetchrow("SELECT protected FROM kargadia WHERE uid=?", (ctx.author.id,))
        if profile["protected"] & 2:
            self.bot.db.execute("UPDATE kargadia SET protected=protected-2 WHERE uid=?", (ctx.author.id,))
            return await ctx.send("Your age will now be displayed on your Kargadian profile.")
        else:
            return await ctx.send("Your age is already being displayed on your Kargadian profile.")

    @ka_citizen_age.command(name="hide", aliases=["disable", "optout"])
    async def ka_citizen_age_disable(self, ctx: commands.Context):
        """ Hide your age from your Kargadian profile """
        profile = self.bot.db.fetchrow("SELECT protected FROM kargadia WHERE uid=?", (ctx.author.id,))
        if not profile["protected"] & 2:
            self.bot.db.execute("UPDATE kargadia SET protected=protected+2 WHERE uid=?", (ctx.author.id,))
            return await ctx.send("Your age will no longer be displayed on your Kargadian profile. Note that you can still see your age if you look at your profile in DMs.")
        else:
            return await ctx.send("Your age is already hidden from your Kargadian profile.")

    # def check_birthday(self, user_id):
    #     data = self.bot.db.fetchrow(f"SELECT * FROM kargadia WHERE uid=? OR id=?", (user_id, user_id))
    #     return data["birthday"] if data else None

    @commands.command(name="birthday", aliases=['b', 'bd', 'birth', 'day'], invoke_without_command=True)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def birthday(self, ctx: commands.Context, *, _user: commands.UserID = None):
        """ Check out someone's Kargadian birthday"""
        language = ctx.language()
        if _user is None:
            _user = ctx.author.id
        if _user == self.bot.user.id:
            return await ctx.send(language.string("birthdays_birthday_cobble"))
        # has_birthday = self.check_birthday(_user)

        data = self.bot.db.fetchrow(f"SELECT * FROM kargadia WHERE uid=? OR id=?", (_user, _user))
        if data is None:
            return await ctx.send(language.string("birthdays_birthday_not_saved", user=self.bot.get_user(_user)))
        try:
            user = await self.bot.fetch_user(data["uid"])  # Since we don't know if _user is a user ID or a citizen ID
            username = general.username(user)
        except discord.NotFound:
            username = data["name"]
            user = self.bot.user  # Use the bot's user account so the tz check doesn't fail
        if data["birthday"] is None:
            return await ctx.send(language.string("birthdays_birthday_not_saved", user=username))
        _user = "your" if user == ctx.author else "general"
        birthday_date = time.date.from_iso(data["birthday"], time.Kargadia)
        birthday = language.date(birthday_date, short=0, dow=False, year=False)
        tz = language.get_timezone(user.id, "Kargadia")
        now = time.datetime.now(tz, time.Kargadia)  # - time.timedelta(hours=6)  # Kargadian birthdays pass at 6am, and this is a crutchy way to reflect that here
        birthday_start = time.datetime.combine(birthday_date.replace(year=now.year), time.time(6, 0, 0), tz)
        is_birthday = now > birthday_start and (now - birthday_start) < time.timedelta(days=1)
        if is_birthday:
            return await ctx.send(language.string(f"birthdays_birthday_{_user}_today", user=username, date=birthday))
        birthday_start.replace_self(year=now.year)  # Set the date to the current year, then add another one if it's already passed
        if now > birthday_start:
            birthday_start.replace_self(year=now.year + 1)
        # birthday_time = time.datetime.combine(birthday_date, time.time(6, 0, 0), tz)
        delta = language.delta_dt(birthday_start, accuracy=2, brief=False, affix=True)
        earth_time = birthday_start.to_earth_time()  # .to_tz(language.get_timezone(user.id, "Earth"))
        earth = language.time(earth_time, short=1, dow=False, seconds=False, tz=True, at=True, uid=ctx.author.id)
        return await ctx.send(language.string(f"birthdays_birthday_{_user}_ka", user=username, date=birthday, delta=delta, earth=earth))

    @commands.group(name="generate", aliases=["gen"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def generate(self, ctx: commands.Context):
        """ Generate a random Kargadian citizen"""
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @generate.command(name="name", aliases=["names"])
    async def generate_name(self, ctx: commands.Context, language: str = "re_nu"):
        """ Generate a couple random Kargadian names """
        message = await ctx.send(conworlds2.generate_citizen_names(language))
        view = views.GenerateNamesView(sender=ctx.author, message=message, language=language, ctx=ctx)
        await message.edit(view=view)
        return message

    @generate.command(name="citizen")
    async def generate_citizen(self, ctx: commands.Context, citizen_language: str = None):
        """ Generate an entire citizen
        If no language is specified, a random available language will be used """
        embed = await conworlds2.generate_citizen_embed(ctx, citizen_language)

        message = await ctx.send(embed=embed)
        view = views.GenerateCitizenView(sender=ctx.author, message=message, language=citizen_language, ctx=ctx)
        await message.edit(view=view)
        return message


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Conworlds(bot))
