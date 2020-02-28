import json
import random
from datetime import datetime, timedelta

import discord
import country_converter
import timeago
from discord.ext import commands

from utils import time, http


class Utility(commands.Cog):
    @commands.command(name="time")
    async def current_time(self, ctx):
        """ Current time """
        return await ctx.send(f"Current time is: {time.time()}\n"
                              f"If that's not the case for you, git gud and use a proper timezone.")

    @commands.command(name="mctime")
    async def mc_time(self, ctx, month: str = 1, day: int = 1, hour: int = 6, minute: int = 0):
        """ Set time in Minecraft """
        if month == 'random':
            rmo = random.randint(1, 12)
            days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            rd = random.randint(1, days[rmo-1])
            rh = random.randint(1, 23)
            rm = random.randint(1, 59)
            dt = datetime(1, rmo, rd, rh, rm)
        else:
            try:
                dt = datetime(1, int(month), day, hour, minute)
            except Exception as e:
                return await ctx.send(e)
        # rd = relativedelta(datetime(year, month, day, hour, minute), datetime.min)
        rd = dt - datetime.min
        mt = int(round(rd.seconds * 24000 / 86400 + rd.days * 24000)) - 6000
        date = time.time_output(dt)
        return await ctx.send(f"For {date}:\n**/time set {mt}**")

    @commands.command(name="timesince", aliases=["timeuntil"])
    async def time_since(self, ctx, year: int = None, month: int = 1, day: int = 1, hour: int = 0, minute: int = 0,
                         second: int = 0):
        """ Time difference """
        try:
            now = time.now(True)
            date = datetime(now.year, 1, 1)
            if year is None:
                _year = now.year
                dates = [datetime(_year, 1, 27), datetime(_year, 2, 14), datetime(_year, 3, 8),
                         datetime(_year, 3, 17), datetime(_year, 4, 1), datetime(_year, 5, 9),
                         datetime(_year, 6, 12), datetime(_year, 9, 3), datetime(_year, 10, 31),
                         datetime(_year, 12, 25), datetime(_year+1, 1, 1)]
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
            return await ctx.send(f"Current time: **{current_time}**\nSpecified time: **{specified_time}**\n"
                                  f"Result: **{human_timeago}**")
        except Exception as e:
            return await ctx.send(f"There was an error:\n{e}")

    @commands.command(name="weather")
    async def weather(self, ctx, *, _place: commands.clean_content):
        """ Check weather in a place """
        place = str(_place)
        try:
            bio = await http.get("http://api.openweathermap.org/data/2.5/weather?"
                                 f"appid=140e8db87d18e656a628272c48936fd7&q={place}", res_method="read")
            data = json.loads(str(bio.decode('utf-8')))
            embed = discord.Embed(colour=random.randint(0, 0xffffff))
            weather_icon = data['weather'][0]['icon']
            embed.set_thumbnail(url=f"http://openweathermap.org/img/wn/{weather_icon}@2x.png")
            embed.add_field(name="Current weather", value=data['weather'][0]['description'].capitalize(), inline=True)
            _tk = data['main']['temp']
            _tc = _tk - 273.15
            _tf = _tc * 1.8 + 32
            tk, tc, tf = [round(_tk, 1), round(_tc, 1), round(_tf, 1)]
            embed.add_field(name="Current temperature", value=f"**{tc}°C** | {tk}°K | {tf}°F", inline=True)
            embed.add_field(name="Pressure", value=f"{data['main']['pressure']} hPa", inline=True)
            embed.add_field(name="Humidity", value=f"{data['main']['humidity']}%", inline=True)
            sm = data['wind']['speed']
            _sk = sm * 3.6
            _sb = _sk / 1.609  # imperial system bad
            sk, sb = [round(_sk, 1), round(_sb, 1)]
            embed.add_field(name="Wind speed", value=f"**{sm} m/s | {sk} km/h** | {sb} mph", inline=True)
            embed.add_field(name="Cloud cover", value=f"{data['clouds']['all']}%", inline=True)
            tz = data['timezone']
            sr = data['sys']['sunrise']
            ss = data['sys']['sunset']
            if sr != 0 and ss != 0:
                srt = time.from_ts(sr + tz)
                sst = time.from_ts(ss + tz)
                sunrise = srt.strftime('%H:%M')
                sunset = sst.strftime('%H:%M')
                tar = timeago.format(srt)  # Time since/until sunrise
                tas = timeago.format(sst)  # Time since/until sunset
                embed.add_field(name="Sunrise", value=f"{sunrise} | {tar}", inline=True)
                embed.add_field(name="Sunset", value=f"{sunset} | {tas}", inline=True)
            country = data['sys']['country']
            local_time = time.time_output((time.now(True) + timedelta(seconds=tz)))
            country_name = country_converter.convert(names=[country], to="name_short")
            emote = f":flag_{country.lower()}:"
            embed.timestamp = time.now(True)
        except Exception as e:
            return await ctx.send(f"Could not get weather for {place}:\n{e}")
        return await ctx.send(f"{emote} Weather in **{data['name']}, {country_name}**\n"
                              f"Local time: **{local_time}**", embed=embed)

    @commands.command(name="luas")
    async def luas(self, ctx, *, place: commands.clean_content):
        """ Data for Luas """
        import luas.api
        client = luas.api.LuasClient()
        a = str(place).split(" ")
        b = []
        for i in a:
            b.append(i.capitalize())
        _place = " ".join(b)
        data = client.stop_details(_place)
        status = data['status']
        trams = ''
        for i in data['trams']:
            if i['due'] == 'DUE':
                _time = 'DUE'
            else:
                _time = f"{i['due']} mins"
            trams += f"{i['destination']}: {_time}\n"
        return await ctx.send(f"Data available for {_place}:\n{status}\n{trams}")


def setup(bot):
    bot.add_cog(Utility(bot))
