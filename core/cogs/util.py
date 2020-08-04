import json
import random
from datetime import datetime, timedelta, timezone
from io import BytesIO

import discord
import pytz
from discord.ext import commands

from core.utils import database, time, general, bases, http
from languages import langs


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database(self.bot.name)

    @commands.command(name="time")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def current_time(self, ctx: commands.Context):
        """ Current time """
        locale = langs.gl(ctx.guild, self.db)
        send = ""
        if ctx.guild.id == 568148147457490954:
            send += langs.gls("util_time_sl", locale, langs.gts(time.now_k(), locale, True, True, False, True, True))
        send += langs.gls("util_time_bot", locale, langs.gts(time.now(self.bot.local_config["timezone"]), locale, True, True, False, True, True))
        send += f"UTC/GMT: **{langs.gts(time.now(None), locale, True, True, False, True, True)}**"
        # send = f"Senko Lair: **{time.time_k(tz=True)}**\n" if self.bot.name == "suager" else ""
        # send += f"Bot Time: **{time.time(self.bot.local_config['timezone'], _tz=True)}**\nUTC/GMT: **{time.time(None, _tz=True)}**"
        data = self.db.fetchrow("SELECT * FROM timezones WHERE uid=?", (ctx.author.id,))
        if data:
            _tzn = data["tz"]
            _tzl = len(_tzn)
            tzn = _tzn.upper() if _tzl <= 3 else _tzn.title()
            send += f"\n{tzn}: **{time.time_output(time.set_tz(time.now(None), data['tz']), tz=True, seconds=True)}**"
        return await general.send(send, ctx.channel)

    @commands.command(name="base", aliases=["bases", "bc"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def base_conversions(self, ctx: commands.Context, conversion: str, base: int, number: str, caps: bool = False):
        """ Convert numbers between bases

        Use "to" to convert decimal (base-10) to a base
        Use "from" to convert from the base to decimal (base-10)
        Caps is optional (use True if you want output to look like "1AA" instead of "1aa") and is ignored for conversions to base 10."""
        if base > 36:
            return await general.send(f"{ctx.author.name}, Bases above 36 are not supported", ctx.channel)
        elif base < 2:
            return await general.send(f"{ctx.author.name}, Bases under 2 are not supported", ctx.channel)
        conversion = conversion.lower()
        value = float(number)
        try:
            if conversion == "to":
                return await general.send(f"{ctx.author.name}: {number} (base 10) -> {bases.to_base_float(value, base, 10, caps)} (base {base})", ctx.channel)
                # return await general.send(f"{ctx.author.name}: {number} (base 10) -> {bases.to_base(number, base, caps)} (base {base})", ctx.channel)
            if conversion == "from":
                if not value.is_integer():
                    return await general.send("Conversion of float numbers to base 10 is currently not supported.", ctx.channel)
                return await general.send(f"{ctx.author.name}: {number:.0f} (base {base}) -> {bases.from_base(number, base)} (base 10)", ctx.channel)
                # return await general.send(f"{ctx.author.name}: {number} (base {base}) -> {bases.from_base(number, base)} (base 10)", ctx.channel)
        except ValueError:
            return await general.send(f"{ctx.author.name}, this number is invalid.", ctx.channel)
        except OverflowError:
            return await general.send(f"{ctx.author.name}, the number specified is too large to convert to an integer.", ctx.channel)
        return await general.send(f"You need to specify either `to` or `from`.", ctx.channel)

    @commands.command(name="settz")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def set_timezone(self, ctx: commands.Context, tz: str):
        """ Set your timezone """
        try:
            data = self.db.fetchrow("SELECT * FROM timezones WHERE uid=?", (ctx.author.id,))
            _tz = pytz.timezone(tz)
            if data:
                self.db.execute("UPDATE timezones SET tz=? WHERE uid=?", (tz, ctx.author.id))
            else:
                self.db.execute("INSERT INTO timezones VALUES (?, ?)", (ctx.author.id, tz))
            return await general.send(f"Your timezone has been set to {_tz}", ctx.channel)
        except pytz.exceptions.UnknownTimeZoneError:
            file = discord.File(BytesIO("\n".join(pytz.all_timezones).encode("utf-8")), filename="timezones.txt")
            return await general.send(f"Timezone `{tz}` was not found. Attached is the list of all pytz timezones", ctx.channel, file=file)

    @commands.command(name="timesince", aliases=["timeuntil"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def time_since(self, ctx: commands.Context, year: int = None, month: int = 1, day: int = 1, hour: int = 0, minute: int = 0, second: int = 0):
        """ Time difference """
        locale = langs.gl(ctx.guild, self.db)
        try:
            now = time.now(None)
            date = datetime(now.year, 1, 1)
            if year is None:
                def dt(_month, _day):
                    return datetime(now.year, _month, _day, tzinfo=timezone.utc)
                dates = [dt(1, 27), dt(3, 17), dt(4, 1), dt(5, 10), dt(5, 13), dt(5, 19), dt(7, 13), dt(10, 1), dt(10, 31), dt(12, 25),
                         datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)]
                for _date in dates:
                    if now < _date:
                        date = _date
                        break
            else:
                date = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
            difference = langs.td_dt(date, locale, accuracy=7, brief=False, suffix=False)  # time.human_timedelta(date, accuracy=7)
            current_time = langs.gts(now, locale, True, False, True, True, True)  # time.time_output(now, True, True, True)
            specified_time = langs.gts(date, locale, True, False, True, True, True)  # time.time_output(date, True, True, True)
            return await general.send(langs.gls("util_timesince", locale, current_time, specified_time, difference), ctx.channel)
            # return await general.send(f"Current time: **{current_time}**\nSpecified time: **{specified_time}**\nDifference: **{difference}**", ctx.channel)
        except Exception as e:
            return await general.send(langs.gls("util_timesince_error", locale, type(e).__name__, str(e)), ctx.channel)
            # return await general.send(f"An error has occurred\n`{type(e).__name__}: {e}`", ctx.channel)

    @commands.command(name="weather")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def weather(self, ctx: commands.Context, *, place: str):
        """ Check weather in a place """
        locale = langs.gl(ctx.guild, self.db)
        lang = "en" if locale.startswith("rsl") else locale.split("_")[0]
        try:
            token = self.bot.config["weather_api_token"]
            bio = await http.get(f"http://api.openweathermap.org/data/2.5/weather?appid={token}&lang={lang}&q={place}", res_method="read")
            data = json.loads(str(bio.decode('utf-8')))
            code = data["cod"]
            if code == 200:
                embed = discord.Embed(colour=random.randint(0, 0xffffff))
                try:
                    country = data['sys']['country'].lower()
                    tz = data['timezone']
                except KeyError:
                    country = ""
                    tz = 0
                # local_time = time.time_output((time.now(None) + timedelta(seconds=tz)), tz=True)
                local_time = langs.gts(time.now(None) + timedelta(seconds=tz), locale)
                if country:
                    country_name = langs.gls(f"z_data_country_{country}", locale)
                    emote = f":flag_{country}: "
                else:
                    country_name = "Not a country"
                    emote = ""
                # country_name = country_converter.convert(names=[country], to="name_short") if country else "Error"
                # if country.lower() == "us":
                #     country_name = "Enslaved Shooting Range"
                embed.title = langs.gls("util_weather_title", locale, data['name'], country_name, emote=emote)
                # embed.title =  f"{emote} Weather in **{data['name']}, {country_name}**"
                embed.description = langs.gls("util_weather_desc", locale, local_time)
                # embed.description = f"Local Time: **{local_time}**"
                weather_icon = data['weather'][0]['icon']
                embed.set_thumbnail(url=f"http://openweathermap.org/img/wn/{weather_icon}@2x.png")
                embed.add_field(name=langs.gls("util_weather_weather", locale), value=data['weather'][0]['description'].capitalize(), inline=True)
                _tk = data['main']['temp']
                _tc = _tk - 273.15
                _tf = _tc * 1.8 + 32
                tk, tc, tf = langs.gfs(_tk, locale, 1), langs.gfs(_tc, locale, 1), langs.gfs(_tf, locale, 1)
                embed.add_field(name=langs.gls("util_weather_temperature", locale), value=f"**{tc}°C** | {tk} K | {tf}°F", inline=True)
                embed.add_field(name=langs.gls("util_weather_pressure", locale), value=f"{langs.gns(data['main']['pressure'], locale)} hPa", inline=True)
                embed.add_field(name=langs.gls("util_weather_humidity", locale), value=langs.gfs(data['main']['humidity'] / 100, locale, 0, True), inline=True)
                _sm = data['wind']['speed']
                _sk = _sm * 3.6
                _sb = _sk / 1.609  # imperial system bad
                # sk, sb = [round(_sk, 1), round(_sb, 1)]
                sm, sk, sb = langs.gfs(_sm, locale, 2), langs.gfs(_sk, locale, 2), langs.gfs(_sb, locale, 2)
                embed.add_field(name=langs.gls("util_weather_wind", locale), value=langs.gls("util_weather_wind_data", locale, sm, sk, sb), inline=True)
                embed.add_field(name=langs.gls("util_weather_clouds", locale), value=langs.gfs(data['clouds']['all'] / 100, locale, 0, True), inline=True)
                sr = data['sys']['sunrise']
                ss = data['sys']['sunset']
                now = time.now(None)
                now_l = now + timedelta(seconds=tz)
                if sr != 0 and ss != 0:
                    srt = time.from_ts(sr + tz, None)
                    sst = time.from_ts(ss + tz, None)
                    # sunrise = srt.strftime('%H:%M')
                    # sunset = sst.strftime('%H:%M')
                    # tar = timeago.format(srt, now_l)  # Time since/until sunrise
                    # tas = timeago.format(sst, now_l)  # Time since/until sunset
                    sr, tr = langs.gts(srt, locale, False, seconds=False), langs.td_dt(srt, locale, source=now_l, accuracy=1, suffix=True)
                    ss, ts = langs.gts(sst, locale, False, seconds=False), langs.td_dt(sst, locale, source=now_l, accuracy=1, suffix=True)
                    embed.add_field(name=langs.gls("util_weather_sunrise", locale), value=f"{sr} | {tr}", inline=True)
                    embed.add_field(name=langs.gls("util_weather_sunset", locale), value=f"{ss} | {ts}", inline=True)
                    # embed.add_field(name="Sunrise", value=f"{sunrise} | {tar}", inline=True)
                    # embed.add_field(name="Sunset", value=f"{sunset} | {tas}", inline=True)
                embed.timestamp = now
            else:
                return await general.send(langs.gls("util_weather_error", locale, place, code, data["message"]), ctx.channel)
                # return await general.send(f"Couldn't get weather for {place}:\n`{code}: {data['message']}`", ctx.channel)
        except Exception as e:
            return await general.send(langs.gls("util_weather_error", locale, place, type(e).__name__, str(e)), ctx.channel)
            # return await general.send(f"Couldn't get weather for {place}:\n`{type(e).__name__}: {e}`", ctx.channel)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="luas")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def luas(self, ctx: commands.Context, *, place: commands.clean_content):
        """ Data for Luas """
        import luas.api
        client = luas.api.LuasClient()
        _place = str(place).title() if len(str(place)) != 3 else str(place)
        data = client.stop_details(_place)
        status = data['status']
        trams = ''
        for i in data['trams']:
            if i['due'] == 'DUE':
                _time = 'DUE'
            else:
                _time = f"{i['due']} mins"
            trams += f"{i['destination']}: {_time}\n"
        return await general.send(f"Data for {_place}:\n{status}\n{trams}", ctx.channel)


def setup(bot):
    bot.add_cog(Utility(bot))
