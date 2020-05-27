import json
import random
from datetime import datetime, timedelta
from io import BytesIO

import country_converter
import discord
import pytz
import timeago
from discord.ext import commands

from utils import time, generic, http, database


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database()

    @commands.command(name="time")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def current_time(self, ctx: commands.Context):
        """ Current time """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "time"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        send = generic.gls(locale, "time_command", [time.time(tz=True), time.time_k(tz=True), ctx.author.name, time.time(True, tz=True)])
        data = self.db.fetchrow("SELECT * FROM timezones WHERE uid=?", (ctx.author.id,))
        if data:
            _tzn = data["tz"]
            _tzl = len(_tzn)
            tzn = _tzn.upper() if _tzl <= 3 else _tzn.title()
            send += generic.gls(locale, "time_local", [tzn, time.time_output(time.set_tz(time.now(True), data["tz"]), tz=True, seconds=True)])
        return await generic.send(send, ctx.channel)
        # return await ctx.send(f"It is **{time.time()}** for me and therefore the world, {ctx.author.name}.")

    @commands.command(name="settz")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def set_timezone(self, ctx: commands.Context, tz: str):
        """ Set your timezone """
        locale = generic.get_lang(ctx.guild)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        try:
            data = self.db.fetchrow("SELECT * FROM timezones WHERE uid=?", (ctx.author.id,))
            _tz = pytz.timezone(tz)
            if data:
                ret = self.db.execute("UPDATE timezones SET tz=? WHERE uid=?", (tz, ctx.author.id))
            else:
                ret = self.db.execute("INSERT INTO timezones VALUES (?, ?)", (ctx.author.id, tz))
            return await generic.send(generic.gls(locale, "tz_set", [ctx.author.name, tz, ret]), ctx.channel)
        except pytz.exceptions.UnknownTimeZoneError:
            file = discord.File(BytesIO("\n".join(pytz.all_timezones).encode("utf-8")), filename="timezones.txt")
            return await generic.send(generic.gls(locale, "tz_invalid", [tz]), ctx.channel, file=file)

    @commands.command(name="timesince", aliases=["timeuntil"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def time_since(self, ctx: commands.Context, year: int = None, month: int = 1, day: int = 1, hour: int = 0, minute: int = 0, second: int = 0):
        """ Time difference """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "timesince"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        try:
            now = time.now(True)
            date = datetime(now.year, 1, 1)
            if year is None:
                _year = now.year
                dates = [datetime(_year, 1, 27), datetime(_year, 2, 14), datetime(_year, 3, 8),
                         datetime(_year, 3, 17), datetime(_year, 4, 1), datetime(_year, 5, 9),
                         datetime(_year, 6, 12), datetime(_year, 9, 3), datetime(_year, 10, 31),
                         datetime(_year, 12, 25), datetime(_year + 1, 1, 1)]
                for _date in dates:
                    if now < _date:
                        date = _date
                        break
            else:
                date = datetime(year, month, day, hour, minute, second)
            # human_timeago = time.time_ago(date, now)
            human_timeago = time.human_timedelta(date, accuracy=7)
            current_time = time.time_output(now, True, True, True)
            specified_time = time.time_output(date, True, True, True)
            return await generic.send(generic.gls(locale, "time_since", [current_time, specified_time, human_timeago]), ctx.channel)
            # return await ctx.send(f"Current time: **{current_time}**\nSpecified time: **{specified_time}**\n"
            #                       f"Result: **{human_timeago}**")
        except Exception as e:
            return await generic.send(generic.gls(locale, "time_since_error", [e]), ctx.channel)
            # return await ctx.send(f"There was an error:\n{e}")

    @commands.command(name="weather")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def weather(self, ctx: commands.Context, *, _place: commands.clean_content):
        """ Check weather in a place """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "weather"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        place = str(_place)
        try:
            bio = await http.get("http://api.openweathermap.org/data/2.5/weather?"
                                 f"appid=140e8db87d18e656a628272c48936fd7&q={place}", res_method="read")
            data = json.loads(str(bio.decode('utf-8')))
            embed = discord.Embed(colour=random.randint(0, 0xffffff))
            weather_icon = data['weather'][0]['icon']
            embed.set_thumbnail(url=f"http://openweathermap.org/img/wn/{weather_icon}@2x.png")
            embed.add_field(name=generic.gls(locale, "current_weather"), value=data['weather'][0]['description'].capitalize(), inline=True)
            _tk = data['main']['temp']
            _tc = _tk - 273.15
            _tf = _tc * 1.8 + 32
            tk, tc, tf = [round(_tk, 1), round(_tc, 1), round(_tf, 1)]
            embed.add_field(name=generic.gls(locale, "temperature"), value=f"**{tc}°C** | {tk}°K | {tf}°F", inline=True)
            embed.add_field(name=generic.gls(locale, "pressure"), value=f"{data['main']['pressure']} hPa", inline=True)
            embed.add_field(name=generic.gls(locale, "humidity"), value=f"{data['main']['humidity']}%", inline=True)
            sm = data['wind']['speed']
            _sk = sm * 3.6
            _sb = _sk / 1.609  # imperial system bad
            sk, sb = [round(_sk, 1), round(_sb, 1)]
            embed.add_field(name=generic.gls(locale, "wind_speed"), value=f"**{sm} m/s | {sk} km/h** | {sb} mph", inline=True)
            embed.add_field(name=generic.gls(locale, "cloud_cover"), value=f"{data['clouds']['all']}%", inline=True)
            tz = data['timezone']
            sr = data['sys']['sunrise']
            ss = data['sys']['sunset']
            now = time.now(True)
            now_l = now + timedelta(seconds=tz)
            if sr != 0 and ss != 0:
                srt = time.from_ts(sr + tz, True)
                sst = time.from_ts(ss + tz, True)
                sunrise = srt.strftime('%H:%M')
                sunset = sst.strftime('%H:%M')
                tar = timeago.format(srt, now_l, locale=locale)  # Time since/until sunrise
                tas = timeago.format(sst, now_l, locale=locale)  # Time since/until sunset
                embed.add_field(name=generic.gls(locale, "sunrise"), value=f"{sunrise} | {tar}", inline=True)
                embed.add_field(name=generic.gls(locale, "sunset"), value=f"{sunset} | {tas}", inline=True)
            country = data['sys']['country']
            local_time = time.time_output((time.now(True) + timedelta(seconds=tz)))
            country_name = country_converter.convert(names=[country], to="name_short")
            emote = f":flag_{country.lower()}:"
            embed.timestamp = now
        except Exception as e:
            return await generic.send(generic.gls(locale, "weather_error", [place, type(e).__name__, e]), ctx.channel)
            # return await ctx.send(f"Could not get weather for {place}:\n{e}")
        return await generic.send(generic.gls(locale, "weather_output", [emote, data["name"], country_name, local_time]), ctx.channel, embed=embed)
        # return await ctx.send(f"{emote} Weather in **{data['name']}, {country_name}**\n"
        #                       f"Local time: **{local_time}**", embed=embed)

    @commands.command(name="luas")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def luas(self, ctx: commands.Context, *, place: commands.clean_content):
        """ Data for Luas """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "luas"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
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
        return await generic.send(generic.gls(locale, "luas", [_place, status, trams]), ctx.channel)
        # return await ctx.send(f"Data available for {_place}:\n{status}\n{trams}")


def setup(bot):
    bot.add_cog(Utility(bot))
