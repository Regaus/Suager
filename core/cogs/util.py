import json
import random
from datetime import datetime, timedelta, timezone
from io import BytesIO

import country_converter
import discord
import pytz
import timeago
from discord.ext import commands

from core.utils import database, time, general, bases, http


is_suager = {"s": True}


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database(self.bot.name)
        is_suager['s'] = self.bot.name != "suager"

    @commands.command(name="time")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def current_time(self, ctx: commands.Context):
        """ Current time """
        send = f"Senko Lair: **{time.time_k(tz=True)}**\n" if self.bot.name == "suager" else ""
        send += f"Bot Time: **{time.time(self.bot.local_config['timezone'], _tz=True)}**\nUTC/GMT: **{time.time(None, _tz=True)}**"
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
        try:
            if conversion == "to":
                return await general.send(f"{ctx.author.name}: {number} (base 10) -> {bases.to_base(number, base, caps)} (base {base})", ctx.channel)
            if conversion == "from":
                return await general.send(f"{ctx.author.name}: {number} (base {base}) -> {bases.from_base(number, base)} (base 10)", ctx.channel)
        except ValueError:
            return await general.send(f"{ctx.author.name}, this number is invalid.", ctx.channel)

    @commands.command(name="owoify", aliases=["owo", "furry"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def owo(self, ctx: commands.Context, *, string: str):
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
                letter = f" {random.choice(faces)}"
            output += letter
        replacements = [["r", "w"], ["l", "w"], ["na", "nya"], ["ne", "nye"], ["ni", "nyi"], ["no", "nyo"], ["nu", "nyu"], ["nyaughty", "naughty"]]
        for thing in replacements:
            output = output.replace(thing[0], thing[1])
        sentences = output.split(".")
        output = ''.join([s.capitalize() for s in sentences])
        i = [[" i ", " I "], ["i've", "I've"], ["i'm", "I'm"]]
        for thing in i:
            output = output.replace(thing[0], thing[1])
        return await general.send(f"{ctx.author.name}:\n{output}", ctx.channel)

    @commands.command(name="neon", hidden=is_suager['s'])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def neon(self, ctx: commands.Context, *, string: str):
        """ Converts letters into neon emotes """
        if not is_suager['s']:
            letters_normal = list("NABCDEFGHIJKLMOPQRSTUVWXYZ")
            letters_neon = ["<a:NN:728657376189874237>", "<a:NA:728657101827866686>", "<a:NB:728657148917317664>", "<a:NC:728657170484166788>",
                            "<a:ND:728657191732641922>", "<a:NE:728657211089223831>", "<a:NF:728657228160041081>", "<a:NG:728657247516753971>",
                            "<a:NH:728657267318325309>", "<a:NI:728657284284153977>", "<a:NJ:728657300683882516>", "<a:NK:728657317356240917>",
                            "<a:NL:728657333495922869>", "<a:NM:728657350981845063>", "<a:NO:728657397672837212>", "<a:NP:728657410784231530>",
                            "<a:NQ:728657428757086281>", "<a:NR:728657504162021427>", "<a:NS:728657516199936082>", "<a:NT:728657531936833606>",
                            "<a:NU:728657547472404660>", "<a:NV:728657575813447750>", "<a:NW:728657593882509343>", "<a:NX:728657655685447752>",
                            "<a:NY:728657683254607963>", "<a:NZ:728658033080533083>"]
            output = string.upper()
            for i in range(26):
                output = output.replace(letters_normal[i], letters_neon[i])
            if len(output) > 1950:
                return await general.send(f"{ctx.author.name}, the output text is too long. Try a shorter input.", ctx.channel)
            return await general.send(f"{ctx.author.name}:\n{output}", ctx.channel)

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
            human_timeago = time.human_timedelta(date, accuracy=7)
            current_time = time.time_output(now, True, True, True)
            specified_time = time.time_output(date, True, True, True)
            return await general.send(f"Current time: **{current_time}**\nSpecified time: **{specified_time}**\nDifference: **{human_timeago}**", ctx.channel)
        except Exception as e:
            return await general.send(f"An error has occurred\n`{type(e).__name__}: {e}`", ctx.channel)

    @commands.command(name="weather")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def weather(self, ctx: commands.Context, *, place: str):
        """ Check weather in a place """
        try:
            token = self.bot.config["weather_api_token"]
            bio = await http.get(f"http://api.openweathermap.org/data/2.5/weather?appid={token}&q={place}", res_method="read")
            data = json.loads(str(bio.decode('utf-8')))
            code = data["cod"]
            if code == 200:
                embed = discord.Embed(colour=random.randint(0, 0xffffff))
                try:
                    country = data['sys']['country']
                    tz = data['timezone']
                except KeyError:
                    country = ""
                    tz = 0
                local_time = time.time_output((time.now(None) + timedelta(seconds=tz)), tz=True)
                country_name = country_converter.convert(names=[country], to="name_short") if country else "Error"
                if country.lower() == "us":
                    country_name = "Enslaved Shooting Range"
                emote = f":flag_{country.lower()}:"
                embed.title = f"{emote} Weather in **{data['name']}, {country_name}**"
                embed.description = f"Local Time: **{local_time}**"
                weather_icon = data['weather'][0]['icon']
                embed.set_thumbnail(url=f"http://openweathermap.org/img/wn/{weather_icon}@2x.png")
                embed.add_field(name="Current Weather", value=data['weather'][0]['description'].capitalize(), inline=True)
                _tk = data['main']['temp']
                _tc = _tk - 273.15
                _tf = _tc * 1.8 + 32
                tk, tc, tf = [round(_tk, 1), round(_tc, 1), round(_tf, 1)]
                embed.add_field(name="Temperature", value=f"**{tc}°C** | {tk}°K | {tf}°F", inline=True)
                embed.add_field(name="Pressure", value=f"{data['main']['pressure']} hPa", inline=True)
                embed.add_field(name="Humidity", value=f"{data['main']['humidity']}%", inline=True)
                sm = data['wind']['speed']
                _sk = sm * 3.6
                _sb = _sk / 1.609  # imperial system bad
                sk, sb = [round(_sk, 1), round(_sb, 1)]
                embed.add_field(name="Wind Speed", value=f"**{sm} m/s | {sk} km/h** | {sb} mph", inline=True)
                embed.add_field(name="Cloud Cover", value=f"{data['clouds']['all']}%", inline=True)
                sr = data['sys']['sunrise']
                ss = data['sys']['sunset']
                now = time.now(None)
                now_l = now + timedelta(seconds=tz)
                if sr != 0 and ss != 0:
                    srt = time.from_ts(sr + tz, None)
                    sst = time.from_ts(ss + tz, None)
                    sunrise = srt.strftime('%H:%M')
                    sunset = sst.strftime('%H:%M')
                    tar = timeago.format(srt, now_l)  # Time since/until sunrise
                    tas = timeago.format(sst, now_l)  # Time since/until sunset
                    embed.add_field(name="Sunrise", value=f"{sunrise} | {tar}", inline=True)
                    embed.add_field(name="Sunset", value=f"{sunset} | {tas}", inline=True)
                embed.timestamp = now
            else:
                return await general.send(f"Couldn't get weather for {place}:\n`{code}: {data['message']}`", ctx.channel)
        except Exception as e:
            return await general.send(f"Couldn't get weather for {place}:\n`{type(e).__name__}: {e}`", ctx.channel)
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
