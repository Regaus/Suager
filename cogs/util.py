import json
import random
import urllib.parse
from datetime import datetime, timedelta
from io import BytesIO

import country_converter
import discord
import pytz
import timeago
from discord.ext import commands

from utils import time, generic, http, database, bases


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

    @commands.command(name="time2", aliases=["timek", "kargadia"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def time_kargadia(self, ctx: commands.Context):
        """ Time in Kargadia """
        return await generic.send(time.date_kargadia(), ctx.channel)

    @commands.command(name="base", aliases=["bases", "bc"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def base_conversions(self, ctx: commands.Context, conversion: str, number: str, base: int, caps: bool = False):
        """ Convert numbers between bases

        Use "to" to convert decimal (base-10) to a base
        Use "from" to convert from the base to decimal (base-10)
        Caps is optional (use True if you want output to look like "1AA" instead of "1aa") and is ignored for conversions to base 10."""
        if base > 36:
            return await generic.send(f"{ctx.author.name}, Bases above 36 are not supported", ctx.channel)
        if conversion == "to":
            return await generic.send(f"{ctx.author.name}: {number} (base 10) -> {bases.to_base(number, base, caps)} (base {base})", ctx.channel)
        if conversion == "from":
            return await generic.send(f"{ctx.author.name}: {number} (base {base}) -> {bases.from_base(number, base)} (base 10)", ctx.channel)

    @commands.command(name="owoify", aliases=["owo", "furry"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def base_conversions(self, ctx: commands.Context, *, string: str):
        """ Converts input into furry language. I'm not sorry. """
        stuff = string.lower()
        words = [["ahh", "murr"], ["are", "is"], ["awesome", "pawsome"], ["awful", "pawful"], ["bite", "nom"], ["bulge", "bulgy-wulgy"],
                 ["butthole", "tailhole"], ["celebrity", "popufur"], ["cheese", "sergal"], ["child", "cub"], ["computer", "protogen"], ["robot", "protogen"],
                 ["cyborg", "protogen"], ["cum", "cummy wummy~"], ["disease", "pathOwOgen"], ["dog", "good boy"], ["dragon", "derg"], ["eat", "vore"],
                 ["fuck", "fluff"], ["father", "daddy"], ["foot", "footpaw"], ["for ", "fur "], ["hand", "paw"], ["hell", "hecc"], ["hyena", "yeen"],
                 ["kiss", "lick"], ["lmao", "hehe~"], ["love", "wuv"], ["mouth", "maw"], ["naughty", "knotty"], ["not", "knot"], ["perfect", "purrfect"],
                 ["persona", "fursona"], ["pervert", "furvert"], ["porn", "yiff"], ["shout", "awoo"], ["source", "sauce"], ["straight", "gay"],
                 ["tale", "tail"], ["the", "teh"], ["that", "dat"], ["these", "dese"], ["this", "dis"], ["those", "dose"], ["toe", "toe bean"],
                 ["with", "wif"], ["you", "chu"], ["your", "ur"], ["you're", "ur"]]
        symbols = [[",", "~"], [";", "~"], [":)", ":3"], [":0", "OwO"], [":d", "UwU"], ["xd", "x3"], ["  ", " uwu "]]
        phrases = [["forgive me", "sorry"], ["i have sinned", "I've been naughty"], ["i've sinned", "I've been naughty"], ["have sex with", "yiff"],
                   ["old person", "greymuzzle"], ["what's this", "OwO what's this"]]
        faces = ["(o´∀`o)", "(#｀ε´)", "(๑•̀ㅁ•́๑)✧", "(*≧m≦*)", "(・`ω´・)", "UwU", "OwO", ">w<", "｡ﾟ( ﾟ^∀^ﾟ)ﾟ｡", "ヾ(｀ε´)ﾉ",
                 "(´• ω •`)", "o(>ω<)o", "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧", "(⁀ᗢ⁀)", "(￣ε￣＠)", "( 〃▽〃)", "(o^ ^o)", "ヾ(*'▽'*)"]
        for word in words:
            stuff = stuff.replace(word[0], word[1])
        for phrase in phrases:
            stuff = stuff.replace(phrase[0], phrase[1])
        for symbol in symbols:
            stuff = stuff.replace(symbol[0], symbol[1])
        output = ""
        for letter in stuff:
            if letter in ["!", "?"]:
                letter += f" {random.choice(faces)}"
            output += letter
        replacements = [["r", "w"], ["l", "w"], ["na", "nya"], ["ne", "nye"], ["ni", "nyi"], ["no", "nyo"], ["nu", "nyu"], ["nyaughty", "naughty"]]
        for thing in replacements:
            output = output.replace(thing[0], thing[1])
        sentences = output.split(".")
        output = ''.join([s.capitalize() for s in sentences])
        i = [[" i ", " I "], ["i've", "I've"], ["i'm", "I'm"]]
        for thing in i:
            output = output.replace(thing[0], thing[1])
        return await generic.send(f"{ctx.author.name}:\n{output}", ctx.channel)

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
            human_timeago = time.human_timedelta(date, accuracy=7)
            current_time = time.time_output(now, True, True, True)
            specified_time = time.time_output(date, True, True, True)
            return await generic.send(generic.gls(locale, "time_since", [current_time, specified_time, human_timeago]), ctx.channel)
        except Exception as e:
            return await generic.send(generic.gls(locale, "time_since_error", [e]), ctx.channel)

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
            bio = await http.get(f"http://api.openweathermap.org/data/2.5/weather?appid={generic.get_config()['weather_key']}&q={place}", res_method="read")
            data = json.loads(str(bio.decode('utf-8')))
            code = data["cod"]
            if code == 200:
                embed = discord.Embed(colour=random.randint(0, 0xffffff))
                country = data['sys']['country']
                tz = data['timezone']
                local_time = time.time_output((time.now(True) + timedelta(seconds=tz)))
                country_name = country_converter.convert(names=[country], to="name_short")
                emote = f":flag_{country.lower()}:"
                embed.title = generic.gls(locale, "weather_output", [emote, data["name"], country_name])
                embed.description = generic.gls(locale, "weather_output2", [local_time])
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
                embed.timestamp = now
            else:
                return await generic.send(generic.gls(locale, "weather_error", [place, code, data["message"]]), ctx.channel)
        except Exception as e:
            return await generic.send(generic.gls(locale, "weather_error", [place, type(e).__name__, e]), ctx.channel)
        return await generic.send(None, ctx.channel, embed=embed)

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

    @commands.command(name="google", aliases=["g"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def google(self, ctx: commands.Context, *, what: str):
        """ Search for something """
        return await generic.send(f"<https://lmgtfy.com/?q={urllib.parse.quote(what)}>", ctx.channel)


def setup(bot):
    bot.add_cog(Utility(bot))
