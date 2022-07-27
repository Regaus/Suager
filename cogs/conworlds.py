import json
import re
from math import ceil

import discord
from regaus import conworlds, PlaceDoesNotExist, random_colour, time, version_info

from utils import bot_data, commands, conlangs

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
            dt = time.datetime.now()
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
                dt = time.datetime.combine(date_part, time_part)
            except ValueError:
                return await ctx.send("Failed to convert date. Make sure it is in the format `YYYY-MM-DD hh:mm:ss` (time part optional)")
        # time_earth = self.bot.language2("english").time(dt, short=0, dow=True, seconds=True, tz=False)  # True, False, True, True, False
        time_earth = dt.strftime("%A, %d %B %Y, %H:%M:%S", "en")
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
        place = conworlds.Place(place_name, dt)
        if _id is None:
            _id = place.id
        output += f"\nTime {_pre} {_id}: **{place.time.strftime('%A, %d %B %Y, %H:%M:%S', 'en')}**"
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
                    # LOD 1 Channel Names:  secret-room-1,      secret-room-2,      secret-room-3,      secret-room-8,      secret-room-10      secret-room-13      Kargadia commands,
                    #                       secret-room-14,     secret-room-15,     secret-room-16,     secret-room-17
                    elif ctx.channel.id in [671520521174777869, 672535025698209821, 681647810357362786, 725835449502924901, 798513492697153536, 958489459672891452, 938582514166034514,
                                            965801985716666428, 969720792457822219, 971195522830442527, 972112792624726036]:
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
            return await ctx.send("De tuava eden, var te en de kihteral.")
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
            return await ctx.send(f"Si valse, alteknaar ka un kudalsan kihteran")
        return await ctx.send(f"{code} {text}")

    @commands.command("rslf")
    @commands.check(lambda ctx: ctx.author.id in [302851022790066185, 236884090651934721, 291665491221807104])
    async def rsl_decode(self, ctx: commands.Context, s: int, *, t: str):
        """ Laikattarad Sintuvuad """
        if not (1 <= s <= 8700):
            return await ctx.send("De tuava eden, var te en de kihteral.")
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

    @commands.group(name="citizenship", aliases=["citizen", "kaprofile", "kargadia"], case_insensitive=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def ka_citizenship(self, ctx: commands.Context):
        """ Your Kargadian citizen ID """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @ka_citizenship.command(name="add")
    @commands.is_owner()
    async def ka_citizen_add(self, ctx: commands.Context, _id: int, uid: int, name: str = None, name2: str = None, gender: str = None, birthday: str = None, location: str = None, joined: str = None):
        """ Add a new Kargadian citizen to the database """
        output = self.bot.db.execute("INSERT INTO kargadia(id, uid, name, name2, gender, birthday, has_role, location, joined) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                     (_id, uid, name, name2, gender, birthday, False, location, joined))
        return await ctx.send(output)

    @ka_citizenship.command(name="edit", aliases=["update"])
    @commands.is_owner()
    async def ka_citizen_edit(self, ctx: commands.Context, _id: int, key: str, value: str):
        """ Edit a Kargadian citizen's profile """
        output = self.bot.db.execute(f"UPDATE kargadia SET {key}=? WHERE id=? OR uid=?", (value, _id, _id))
        return await ctx.send(output)

    @ka_citizenship.command(name="delete", aliases=["del", "remove"])
    @commands.is_owner()
    async def ka_citizen_delete(self, ctx: commands.Context, _id: int):
        """ Delete a Kargadian citizen's profile """
        output = self.bot.db.execute("DELETE FROM kargadia WHERE id=?", (_id,))
        return await ctx.send(output)

    @ka_citizenship.command(name="see", aliases=["view", "profile", "id"])
    async def ka_citizen_profile(self, ctx: commands.Context, _user: commands.UserID = None):
        """ See your or someone else's profile """
        language = ctx.language2("en")
        if _user is None:
            _user = ctx.author.id
        # if not (await ctx.bot.is_owner(ctx.author)) and user.id not in [ctx.author.id, 302851022790066185, 609423646347231282, 577608850316853251]:
        #     return await ctx.send("Locked for now - You can only access your own profile, as well as Regaus's, Suager's, and CobbleBot's...")
        data = self.bot.db.fetchrow("SELECT * FROM kargadia WHERE uid=? OR id=?", (_user, _user))
        if not data:
            return await ctx.send("A citizen profile is not available for this user.")

        embed = discord.Embed(colour=random_colour())
        name = data["name"]
        if data["name2"]:
            name += f" {data['name2']}"

        try:
            user = await self.bot.fetch_user(data["uid"])  # Since we don't know if _user is a user ID or a citizen ID
            username = user.name
            embed.set_thumbnail(url=str(user.display_avatar.replace(size=1024, static_format="png")))
        except discord.NotFound:
            username = data["name"]

        embed.title = f"{username}'s Kargadian citizen ID"
        embed.add_field(name="Citizen ID", value=data["id"], inline=True)
        # embed.add_field(name="User ID", value=data["uid"], inline=True)

        genders = {"m": "Male", "f": "Female"}
        embed.add_field(name="Gender", value=genders.get(data["gender"]), inline=True)

        embed.add_field(name="Kargadian Name", value=name, inline=False)

        if data["birthday"]:
            birthday = time.date.from_iso(data["birthday"], time.Kargadia)
            embed.add_field(name="Birthday", value=language.date(birthday, short=1, dow=False, year=True), inline=False)
        else:
            embed.add_field(name="Birthday", value="Unavailable", inline=False)

        if data["location"]:
            embed.add_field(name="Location", value=data["location"], inline=False)
        else:
            embed.add_field(name="Location", value="Unavailable", inline=False)

        joined = time.date.from_iso(data["joined"], time.Earth)
        embed.add_field(name="Joined the cult on", value=language.date(joined, short=1, dow=False, year=True), inline=False)
        return await ctx.send(embed=embed)

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
            username = user.name
        except discord.NotFound:
            username = data["name"]
            user = self.bot.user  # Use the bot's user account so the tz check doesn't fail
        if data["birthday"] is None:
            return await ctx.send(language.string("birthdays_birthday_not_saved", user=username))
        birthday_date = time.date.from_iso(data["birthday"], time.Kargadia)
        birthday = language.date(birthday_date, short=0, dow=False, year=False)
        tz = language.get_timezone(user.id, "Kargadia")
        now = time.datetime.now(tz, time.Kargadia)
        if now.day == birthday_date.day and now.month == birthday_date.month:
            today = "_today"
            delta = None
        else:
            today = ""
            year = now.year + 1 if (now.day > birthday_date.day and now.month == birthday_date.month) or now.month > birthday_date.month else now.year
            delta = language.delta_dt(time.datetime.combine(birthday_date, time.time(), tz).replace(year=year), accuracy=2, brief=False, affix=True)
        if user == ctx.author:
            return await ctx.send(language.string(f"birthdays_birthday_your{today}", date=birthday, delta=delta))
        return await ctx.send(language.string(f"birthdays_birthday_general{today}", user=username, date=birthday, delta=delta))


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Conworlds(bot))
