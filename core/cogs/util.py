import json
import random
from datetime import datetime, timedelta, timezone
from io import BytesIO

import discord
import pytz
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

from core.utils import arg_parser, bases, emotes, general, http, permissions, time
from languages import langs
from cobble.utils import ss23


def custom_role_enabled(ctx):
    return ctx.guild is not None and ctx.guild.id in [568148147457490954, 430945139142426634, 738425418637639775, 784357864482537473]


async def time_diff(ctx: commands.Context, string: str, multiplier: int):
    locale = langs.gl(ctx)
    delta = time.interpret_time(string) * multiplier
    then, errors = time.add_time(delta)
    if errors:
        return await general.send(f"Error converting time difference: {then}", ctx.channel)
    difference = langs.td_rd(delta, locale, accuracy=7, brief=False, suffix=True)
    time_now = langs.gts(time.now(None), locale, True, False, False, True, False)
    time_then = langs.gts(then, locale, True, False, False, True, False)
    return await general.send(f"Current time: **{time_now}**\nDifference: **{difference}**\nOutput time: **{time_then}**", ctx.channel)


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="time")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def current_time(self, ctx: commands.Context):
        """ Current time """
        locale = langs.gl(ctx)
        send = ""
        if locale == "rsl-1d":
            data = ss23.time_kargadia(time.now(None))
            a = f"{data.day:02d} {data.months[data.month - 1]} {data.year}, {data.hour:02d}:{data.minute:02d}:{data.second:02d}"
            b = langs.gts(time.now(None), locale, True, False, False, True, False)
            send += langs.gls("util_time_sl", locale, b, a)
        elif locale == "rsl-1":
            data = ss23.time_kargadia(time.now(None))
            a = f"{data.day:02d} {data.months[data.month - 1]} {data.year}, {data.hour:02d}:{data.minute:02d}:{data.second:02d}"
            b = langs.gts(time.now(None), locale, True, False, False, True, False)
            d = langs.gts(time.now_sl(), locale, True, False, False, True, False)
            z = time.kargadia_convert(time.now(None))
            m = ["Vahkannun", "Navattun", "Senkavun", "Tevillun", "Leitavun", "Haltavun", "Arhanvun", "Nürivun", "Kovavun", "Eiderrun", "Raivazun", "Suvaghun"]
            c = f"{z.day:02d} {m[z.month % 12]} {z.year}, {z.hour:02d}:{z.minute:02d}:{z.second:02d}"
            send += f"Zymlä (UTC/GMT): **{b}**\n" \
                    f"Senkadar Laikadu (AD): **{d}**\n" \
                    f"Senkadar Laikadu (NE): **{c}**\n" \
                    f"Kargadia: **{a}**"
            # send += langs.gls("util_time_sl", locale, c, a, b)
        elif locale == "rsl-1f":
            a = langs.gts(time.now(None), locale, True, False, False, True, False)
            b = langs.gts(time.now_sl(), locale, True, False, False, True, False)
            c = langs.gts(time.now_k(), locale, True, False, False, True, False)
            data = ss23.time_kargadia(time.now(None))
            d = f"{data.day:02d} {data.months[data.month - 1]} {data.year}, {data.hour:02d}:{data.minute:02d}:{data.second:02d}"
            send += f"Zymlä (UTC/GMT): **{a}**\n" \
                    f"Senkadar Laikadu (AD): **{b}**\n" \
                    f"Senkadar Laikadu (NE): **{c}**\n" \
                    f"Kargadia: **{d}**\n" \
                    f"Kaivaltaavia: **Placeholder**"
        else:
            if ctx.guild.id in [568148147457490954, 738425418637639775]:
                # data = ss23.time_kargadia(time.now(None))
                # a = f"{data.day:02d} {data.months[data.month - 1]} {data.year}, {data.hour:02d}:{data.minute:02d}:{data.second:02d} ST"
                # b = langs.gts(time.now_k(), locale, True, False, False, True, True)
                # send += langs.gls("util_time_sl", locale, b, a)
                send += f"Senko Lair (AD): **{langs.gts(time.now_sl(), locale, True, False, False, True, True)}**\n"
                send += f"Senko Lair (NE): **{langs.gts(time.now_k(), locale, True, False, False, True, True)}**\n"
            send += langs.gls("util_time_bot", locale, langs.gts(time.now(self.bot.local_config["timezone"]), locale, True, False, False, True, True))
            send += f"UTC/GMT: **{langs.gts(time.now(None), locale, True, False, False, True, True)}**"
            data = self.bot.db.fetchrow("SELECT * FROM timezones WHERE uid=?", (ctx.author.id,))
            if data:
                _tzn = data["tz"]
                _tzl = len(_tzn)
                tzn = _tzn.upper() if _tzl <= 3 else _tzn.title()
                send += f"\n{tzn}: **{time.time_output(time.set_tz(time.now(None), data['tz']), tz=True, seconds=True)}**"
        return await general.send(send, ctx.channel)

    @commands.command(name="base", aliases=["bases", "bc"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
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
        try:
            if conversion == "to":
                value = float(number)
                return await general.send(f"{ctx.author.name}: {number} (base 10) -> {bases.to_base_float(value, base, 10, caps)} (base {base})", ctx.channel)
            if conversion == "from":
                if "." in number:
                    return await general.send(f"{ctx.author.name}: {number} (base {base}) -> {bases.from_base_float(number, base, 10)} (base 10)", ctx.channel)
                return await general.send(f"{ctx.author.name}: {number} (base {base}) -> {bases.from_base(number, base)} (base 10)", ctx.channel)
        except ValueError:
            return await general.send(f"{ctx.author.name}, this number is invalid.", ctx.channel)
        except OverflowError:
            return await general.send(f"{ctx.author.name}, the number specified is too large to convert to a proper value.", ctx.channel)
        return await general.send(f"You need to specify either `to` or `from`.", ctx.channel)

    @commands.command(name="settz")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def set_timezone(self, ctx: commands.Context, tz: str):
        """ Set your timezone """
        try:
            data = self.bot.db.fetchrow("SELECT * FROM timezones WHERE uid=?", (ctx.author.id,))
            _tz = pytz.timezone(tz)
            if data:
                self.bot.db.execute("UPDATE timezones SET tz=? WHERE uid=?", (tz, ctx.author.id))
            else:
                self.bot.db.execute("INSERT INTO timezones VALUES (?, ?)", (ctx.author.id, tz))
            return await general.send(f"Your timezone has been set to {_tz}", ctx.channel)
        except pytz.exceptions.UnknownTimeZoneError:
            file = discord.File(BytesIO("\n".join(pytz.all_timezones).encode("utf-8")), filename="timezones.txt")
            return await general.send(f"Timezone `{tz}` was not found. Attached is the list of all pytz timezones", ctx.channel, file=file)

    @commands.command(name="timesince", aliases=["timeuntil"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def time_since(self, ctx: commands.Context, year: int = None, month: int = 1, day: int = 1, hour: int = 0, minute: int = 0, second: int = 0):
        """ Time difference """
        locale = langs.gl(ctx)
        if locale in ["rsl-1d", "rsl-5"]:
            if year is not None and year < 277:
                return await general.send(f"In RSL-1 and RSL-5 locales, this command breaks with dates before **1 January 277 AD**.", ctx.channel)
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
            difference = langs.td_dt(date, locale, accuracy=7, brief=False, suffix=True)  # time.human_timedelta(date, accuracy=7)
            current_time = langs.gts(now, locale, True, False, True, True, True)  # time.time_output(now, True, True, True)
            specified_time = langs.gts(date, locale, True, False, True, True, True)  # time.time_output(date, True, True, True)
            return await general.send(langs.gls("util_timesince", locale, current_time, specified_time, difference), ctx.channel)
        except Exception as e:
            return await general.send(langs.gls("util_timesince_error", locale, type(e).__name__, str(e)), ctx.channel)

    @commands.command(name="timein", aliases=["timeadd"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def time_in(self, ctx: commands.Context, time_period: str):
        """ Check what time it'll be in a specified period """
        return await time_diff(ctx, time_period, 1)

    @commands.command(name="timeago", aliases=["timeremove"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def time_ago(self, ctx: commands.Context, time_period: str):
        """ Check what time it was a specified period ago """
        return await time_diff(ctx, time_period, -1)

    @commands.command(name="weather")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def weather(self, ctx: commands.Context, *, place: str):
        """ Check weather in a place """
        locale = langs.gl(ctx)
        lang = "en" if locale.startswith("rsl") else locale.split("_")[0]
        a = await general.send(f"{emotes.Loading} Loading weather for {place}...", ctx.channel)
        try:
            token = self.bot.config["weather_api_token"]
            bio = await http.get(f"http://api.openweathermap.org/data/2.5/weather?appid={token}&lang={lang}&q={place}", res_method="read")
            await a.delete()
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
                _time_locale = locale if locale not in ["rsl-1d", "rsl-5"] else "en_gb"
                local_time = langs.gts(time.now(None) + timedelta(seconds=tz), _time_locale)
                if country:
                    country_name = langs.gls(f"z_data_country_{country}", locale)
                    emote = f":flag_{country}: "
                else:
                    country_name = "Not a country"
                    emote = ""
                embed.title = langs.gls("util_weather_title", locale, data['name'], country_name, emote=emote)
                embed.description = langs.gls("util_weather_desc", locale, local_time)
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
                    sr, tr = langs.gts(srt, _time_locale, False, seconds=False), langs.td_dt(srt, locale, source=now_l, accuracy=1, suffix=True)
                    ss, ts = langs.gts(sst, _time_locale, False, seconds=False), langs.td_dt(sst, locale, source=now_l, accuracy=1, suffix=True)
                    embed.add_field(name=langs.gls("util_weather_sunrise", locale), value=f"{sr} | {tr}", inline=True)
                    embed.add_field(name=langs.gls("util_weather_sunset", locale), value=f"{ss} | {ts}", inline=True)
                embed.timestamp = now
            else:
                return await general.send(langs.gls("util_weather_error", locale, place, code, data["message"]), ctx.channel)
        except Exception as e:
            return await general.send(langs.gls("util_weather_error", locale, place, type(e).__name__, str(e)), ctx.channel)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="luas")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
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

    @commands.command(name="colour", aliases=["color"])
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def colour(self, ctx: commands.Context, colour: str = "random"):
        """ Information on a colour """
        locale = langs.gl(ctx)
        # async with ctx.typing():
        # c = str(ctx.invoked_with)
        if colour.lower() == "random":
            # _colour = hex(random.randint(0, 0xffffff))[2:] + "ff"
            _colour = f"{random.randint(0, 0xffffff):06x}ff"
            # a = 6
        else:
            try:
                if colour[0] == "#":
                    colour = colour[1:]
                # _colour = hex(int(colour, base=16))[2:]
                a = len(colour)
                if a == 3:
                    d, e, f = colour
                    colour = f"{d}{d}{e}{e}{f}{f}"  # Quality code, yes
                    a = 6
                if a == 6:
                    colour += "ff"
                    a = 8
                if a != 8:
                    return await general.send(langs.gls("images_colour_invalid_value", locale), ctx.channel)
                _colour = f"{int(colour, 16):08x}"
            except Exception as e:
                return await general.send(langs.gls("images_colour_invalid", locale, type(e).__name__, str(e)), ctx.channel)
        # message = await general.send(f"{emotes.Loading} Getting data about colour #{colour}...", ctx.channel)
        # try:
        #     _data = await http.get(f"https://api.alexflipnote.dev/colour/{_colour}", res_method="read",
        #                            headers={"Authorization": self.bot.config["alex_api_token"]})
        #     data = json.loads(_data)
        # except json.JSONDecodeError:
        #     return await general.send("An error occurred with the API. Try again later.", ctx.channel)
        # if a == 3:
        #     d, e, f = colour
        #     g = int(f"{d}{d}{e}{e}{f}{f}", base=16)
        #     embed = discord.Embed(colour=g)
        # else:
        hex_6 = _colour[:6]
        hex_8 = _colour
        int_6 = int(_colour[:6], 16)
        int_8 = int(_colour, 16)
        embed = discord.Embed(colour=int_6, base=16)
        rgba_255 = (int(_colour[0:2], 16), int(_colour[2:4], 16), int(_colour[4:6], 16), int(_colour[6:8], 16))
        rgba_1 = tuple(f"{value / 255:.4f}" for value in rgba_255)
        rgba_1_6 = f"({', '.join(rgba_1[:3])})"
        rgba_1_8 = f"({', '.join(rgba_1)})"
        brightness = sum(rgba_255[:3]) // 3
        red, green, blue, alpha = rgba_255
        # embed.title = langs.gls("images_colour_name", locale, data['name'])
        embed.add_field(name=langs.gls("images_colour_hex", locale), value=f'RGB = #{hex_6}\nRGBA = #{hex_8}', inline=False)
        embed.add_field(name=langs.gls("images_colour_int", locale), value=f'RGB = {int_6}\nRGBA = {int_8}', inline=False)
        embed.add_field(name=langs.gls("images_colour_rgb", locale) + " (0-255)", value=f"RGB = {rgba_255[:3]}\nRGBA = {rgba_255}", inline=False)
        embed.add_field(name=langs.gls("images_colour_rgb", locale) + " (0-1)", value=f"RGB = {rgba_1_6}\nRGBA = {rgba_1_8}", inline=False)
        embed.add_field(name=langs.gls("images_colour_brightness", locale), value=str(brightness), inline=False)
        embed.add_field(name=langs.gls("images_colour_font", locale), inline=False,
                        value="#000000" if (brightness >= 128 and alpha >= 128) or green == 255 else "#ffffff")
        image1 = Image.new(mode="RGBA", size=(512, 512), color=rgba_255)
        bio1 = BytesIO()
        image1.save(bio1, "PNG")
        bio1.seek(0)
        embed.set_thumbnail(url="attachment://colour.png")
        # rows = 3 if alpha in [0, 255] else 4
        rows = 4
        font_size = 48
        size = 256
        try:
            font = ImageFont.truetype("assets/font.ttf", size=font_size)
        except ImportError:
            await general.send(f"{emotes.Deny} It seems that image generation does not work properly here...", ctx.channel)
            font = None
        image2 = Image.new(mode="RGBA", size=(size * 11, size * rows), color=(0, 0, 0, 1))
        up_red, up_green, up_blue = (255 - red) / 10, (255 - green) / 10, (255 - blue) / 10
        down_red, down_green, down_blue = red / 10, green / 10, blue / 10
        alpha_up = (255 - alpha) / 10
        alpha_down = alpha / 10

        def _hex(value: int):
            return f"{value:02X}"
        for i in range(11):
            start2a = (size * i, 0)
            start2b = (size * i, size)
            start2c = (size * i, size * 2)
            start2d = (size * i, size * 3)
            red2a, green2a, blue2a = int(red + up_red * i), int(green + up_green * i), int(blue + up_blue * i)
            red2b, green2b, blue2b = int(red - down_red * i), int(green - down_green * i), int(blue - down_blue * i)
            alpha2c = int(alpha + alpha_up * i)
            alpha2d = int(alpha - alpha_down * i)
            image2a = Image.new(mode="RGBA", size=(size, size), color=(red2a, green2a, blue2a, 255))
            image2b = Image.new(mode="RGBA", size=(size, size), color=(red2b, green2b, blue2b, 255))
            image2c = Image.new(mode="RGBA", size=(size, size), color=(red, green, blue, alpha2c))
            image2d = Image.new(mode="RGBA", size=(size, size), color=(red, green, blue, alpha2d))
            draw2a = ImageDraw.Draw(image2a)
            draw2b = ImageDraw.Draw(image2b)
            draw2c = ImageDraw.Draw(image2c)
            draw2d = ImageDraw.Draw(image2d)
            hex2a = "#" + _hex(red2a) + _hex(green2a) + _hex(blue2a)
            hex2b = "#" + _hex(red2b) + _hex(green2b) + _hex(blue2b)
            hex2c = f"a={alpha2c}"
            hex2d = f"a={alpha2d}"
            width2a, height2a = draw2a.textsize(hex2a, font)
            width2b, height2b = draw2b.textsize(hex2b, font)
            width2c, height2c = draw2c.textsize(hex2c, font)
            width2d, height2d = draw2d.textsize(hex2d, font)
            sum2a = (red2a + green2a + blue2a) // 3
            sum2b = (red2b + green2b + blue2b) // 3
            fill2a = (0, 0, 0, 255) if sum2a >= 128 or green2a == 255 else (255, 255, 255, 255)
            fill2b = (0, 0, 0, 255) if sum2b >= 128 or green2b == 255 else (255, 255, 255, 255)
            fill2c = (0, 0, 0, 255) if (brightness >= 128 and alpha2c >= 128) or green == 255 else (255, 255, 255, 255)
            fill2d = (0, 0, 0, 255) if (brightness >= 128 and alpha2d >= 128) or green == 255 else (255, 255, 255, 255)
            draw2a.text(((size - width2a) // 2, size - height2a - 5), hex2a, fill=fill2a, font=font)
            draw2b.text(((size - width2b) // 2, size - height2b - 5), hex2b, fill=fill2b, font=font)
            draw2c.text(((size - width2c) // 2, size - height2c - 5), hex2c, fill=fill2c, font=font)
            draw2d.text(((size - width2d) // 2, size - height2d - 5), hex2d, fill=fill2d, font=font)
            image2.paste(image2a, start2a)
            image2.paste(image2b, start2b)
            image2.paste(image2c, start2c)
            image2.paste(image2d, start2d)
        bio2 = BytesIO()
        image2.save(bio2, "PNG")
        bio2.seek(0)
        embed.set_image(url="attachment://gradient.png")
        embed.set_footer(text="Gradients go to: 1. white, 2. black, 3. alpha=255, 4. alpha=0")
        # embed.set_thumbnail(url=data["image"])
        # embed.set_image(url=data["image_gradient"])
        return await general.send(None, ctx.channel, embed=embed, files=[discord.File(bio1, "colour.png"), discord.File(bio2, "gradient.png")])
        # return await message.edit(content=None, embed=embed)
        # return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="roll")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def roll(self, ctx: commands.Context, num1: int = 6, num2: int = 1):
        """ Rolls a number between given range """
        locale = langs.gl(ctx)
        if num1 > num2:
            v1, v2 = [num2, num1]
        else:
            v1, v2 = [num1, num2]
        r = random.randint(v1, v2)
        n1, n2, no = langs.gns(v1, locale), langs.gns(v2, locale), langs.gns(r, locale)
        return await general.send(langs.gls("fun_roll", locale, ctx.author.name, n1, n2, no), ctx.channel)

    @commands.command(name="reverse")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def reverse_text(self, ctx: commands.Context, *, text: str):
        """ Reverses text """
        reverse = text[::-1].replace("@", "@\u200B").replace("&", "&\u200B")
        return await general.send(f"🔁 {ctx.author.name}:\n{reverse}", ctx.channel)

    @commands.command(name="dm")
    @commands.check(permissions.is_owner)
    async def dm(self, ctx: commands.Context, user_id: int, *, message: str):
        """ DM a user """
        try:
            await ctx.message.delete()
        except Exception as e:
            await general.send(f"Message deletion failed: `{type(e).__name__}: {e}`", ctx.channel, delete_after=5)
        user = self.bot.get_user(user_id)
        if not user:
            return await general.send(f"Could not find a user with ID {user_id}", ctx.channel)
        try:
            await user.send(message)
            return await general.send(f"✉ Sent DM to {user}", ctx.channel, delete_after=5)
        except discord.Forbidden:
            return await general.send(f"Failed to send DM - the user might have blocked DMs, or be a bot.", ctx.channel)

    @commands.command(name="tell")
    @commands.guild_only()
    @permissions.has_permissions(manage_messages=True)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def tell(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str):
        """ Say something to a channel """
        locale = langs.gl(ctx)
        try:
            await ctx.message.delete()
        except Exception as e:
            await general.send(langs.gls("fun_say_delete_fail", locale, type(e).__name__, str(e)), ctx.channel, delete_after=5)
        if channel.guild != ctx.guild:
            return await general.send(langs.gls("fun_tell_guilds", locale), ctx.channel)
        try:
            await general.send(message, channel, u=True, r=True)
        except Exception as e:
            return await general.send(langs.gls("fun_tell_fail", locale, type(e).__name__, str(e)), ctx.channel)
        return await general.send(langs.gls("fun_tell_success", locale, channel.mention), ctx.channel, delete_after=5)

    @commands.command(name="atell")
    @commands.check(permissions.is_owner)
    async def admin_tell(self, ctx: commands.Context, channel_id: int, *, message: str):
        """ Say something to a channel """
        channel = self.bot.get_channel(channel_id)
        try:
            await ctx.message.delete()
        except Exception as e:
            await general.send(f"Message deletion failed: `{type(e).__name__}: {e}`", ctx.channel, delete_after=5)
        try:
            await general.send(message, channel, u=True, r=True)
        except Exception as e:
            return await general.send(f"{emotes.Deny} Failed to send the message: `{type(e).__name__}: {e}`", ctx.channel)
        return await general.send(f"{emotes.Allow} Successfully sent the message to {channel.mention}", ctx.channel, delete_after=5)

    @commands.command(name="say")
    @commands.check(lambda ctx: not (ctx.author.id == 667187968145883146 and ctx.guild.id == 568148147457490954))
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def say(self, ctx: commands.Context, *, message: str):
        """ Make me speak! """
        locale = langs.gl(ctx)
        try:
            await ctx.message.delete()
        except Exception as e:
            await general.send(langs.gls("fun_say_delete_fail", locale, type(e).__name__, str(e)), ctx.channel, delete_after=5)
        await general.send(f"**{ctx.author}:**\n{message}", ctx.channel)
        return await general.send(langs.gls("fun_say_success", locale), ctx.channel, delete_after=5)

    @commands.command(name="flip", aliases=["coin"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def flip_a_coin(self, ctx: commands.Context):
        """ Flip a coin """
        locale = langs.gl(ctx)
        return await general.send(langs.gls("fun_coin_main", locale, langs.gls(f"fun_coin_{random.choice(['heads', 'tails'])}", locale)), ctx.channel)

    @commands.command(name="vote", aliases=["petition"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def vote(self, ctx: commands.Context, *, question: str):
        """ Start a vote """
        locale = langs.gl(ctx)
        message = await general.send(langs.gls("fun_vote", locale, ctx.author.name, langs.gls(f"fun_vote_{str(ctx.invoked_with).lower()}", locale), question),
                                     ctx.channel)
        await message.add_reaction(emotes.Allow)
        await message.add_reaction(emotes.Meh)
        await message.add_reaction(emotes.Deny)

    @commands.command(name="avatar")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def avatar(self, ctx: commands.Context, *, who: discord.User = None):
        """ Get someone's avatar """
        user = who or ctx.author
        return await general.send(langs.gls("discord_avatar", langs.gl(ctx), user.name, user.avatar_url_as(size=1024, static_format='png')), ctx.channel)

    @commands.command(name="avatar2")
    @commands.is_owner()
    async def avatar_fetch(self, ctx: commands.Context, *who: int):
        """ Fetch and yoink avatars """
        for user in who:
            try:
                await general.send((await self.bot.fetch_user(user)).avatar_url_as(size=1024, static_format="png"), ctx.channel)
            except Exception as e:
                await general.send(f"{user} -> {type(e).__name__}: {e}", ctx.channel)

    @commands.group(name="role", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def role(self, ctx: commands.Context, *, role: discord.Role = None):
        """ Information on roles in the current server """
        if ctx.invoked_subcommand is None:
            locale = langs.gl(ctx)
            if role is None:
                all_roles = ""
                for num, role in enumerate(sorted(ctx.guild.roles, reverse=True), start=1):
                    all_roles += langs.gls("discord_role_list_item", locale, langs.gns(num, locale, 2, False), langs.gns(len(role.members)), role=role)
                data = BytesIO(all_roles.encode('utf-8'))
                return await general.send(langs.gls("discord_role_list", locale, ctx.guild.name), ctx.channel,
                                          file=discord.File(data, filename=f"{time.file_ts('Roles')}"))
            else:
                embed = discord.Embed(colour=role.colour)
                embed.title = langs.gls("discord_role_about", locale, role.name)
                embed.set_thumbnail(url=ctx.guild.icon_url)
                embed.add_field(name=langs.gls("discord_role_name", locale), value=role.name, inline=True)
                embed.add_field(name=langs.gls("discord_role_id", locale), value=str(role.id), inline=True)
                embed.add_field(name=langs.gls("generic_members", locale), value=f"{len(role.members):,}", inline=True)
                embed.add_field(name=langs.gls("discord_role_colour", locale), value=str(role.colour), inline=True)
                embed.add_field(name=langs.gls("discord_role_mentionable", locale), value=langs.yes(role.mentionable, locale), inline=True)
                embed.add_field(name=langs.gls("discord_role_hoisted", locale), value=langs.yes(role.hoist, locale), inline=True)
                embed.add_field(name=langs.gls("discord_role_position", locale), value=langs.gns(role.position, locale), inline=True)
                embed.add_field(name=langs.gls("generic_created_at", locale), value=langs.gts(role.created_at, locale, short=False), inline=True)
                embed.add_field(name=langs.gls("discord_role_default", locale), value=langs.yes(role.is_default(), locale), inline=True)
                return await general.send(None, ctx.channel, embed=embed)

    @role.command(name="members")
    async def role_members(self, ctx: commands.Context, *, role: discord.Role):
        """ List of members who have a certain role """
        members = [a for a in ctx.guild.members if role in a.roles]
        members.sort(key=lambda a: a.name.lower())
        locale = langs.gl(ctx)
        m = ''
        for i in range(len(members)):
            m += f"[{langs.gns(i + 1, locale, 2, False)}] {members[i]}\n"
        rl = len(m)
        send = langs.gls("discord_role_members", locale, ctx.guild.name)
        if rl > 1900:
            async with ctx.typing():
                data = BytesIO(str(m).encode('utf-8'))
                return await general.send(send, ctx.channel, file=discord.File(data, filename=f"{time.file_ts('Role_Members')}"))
        return await general.send(f"{send}\n```ini\n{m}```", ctx.channel)

    @commands.command(name="joinedat")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def joined_at(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Check when someone joined server """
        user = who or ctx.author
        locale = langs.gl(ctx)
        return await general.send(langs.gls("discord_joined_at", locale, user, ctx.guild.name, langs.gts(user.joined_at, locale, short=False)), ctx.channel)

    @commands.command(name="createdat")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def created_at(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check when someone created their account """
        user = who or ctx.author
        locale = langs.gl(ctx)
        return await general.send(langs.gls("discord_created_at", locale, user, langs.gts(user.created_at, locale, short=False)), ctx.channel)

    @commands.command(name="user")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def user(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Get info about user """
        user = who or ctx.author
        locale = langs.gl(ctx)
        embed = discord.Embed(colour=general.random_colour())
        embed.title = langs.gls("discord_user_about", locale, user.name)
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name=langs.gls("discord_user_username", locale), value=user, inline=True)
        embed.add_field(name=langs.gls("discord_user_nickname", locale), value=user.nick, inline=True)
        embed.add_field(name=langs.gls("discord_user_id", locale), value=user.id, inline=True)
        embed.add_field(name=langs.gls("generic_created_at", locale), value=langs.gts(user.created_at, locale, short=False), inline=False)
        embed.add_field(name=langs.gls("discord_user_joined_at", locale), value=langs.gts(user.joined_at, locale, short=False), inline=False)
        if len(user.roles) < 15:
            r = user.roles
            r.sort(key=lambda x: x.position, reverse=True)
            ar = [f"<@&{x.id}>" for x in r if x.id != ctx.guild.default_role.id]
            roles = ', '.join(ar) if ar else langs.gls("generic_none", locale)
            b = len(user.roles) - 1
            roles += langs.gls("discord_user_roles_overall", locale, langs.gns(b, locale))
        else:
            roles = langs.gls("discord_user_roles_many", locale, langs.gns(len(user.roles) - 1))
        embed.add_field(name=langs.gls("discord_user_roles", locale), value=roles, inline=False)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="whois")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def who_is(self, ctx: commands.Context, *, user_id: int):
        """ Get info about a user """
        locale = langs.gl(ctx)
        try:
            user = await self.bot.fetch_user(user_id)
        except discord.NotFound as e:
            return await general.send(langs.gls("events_err_error", locale, "NotFound", str(e)), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        embed.title = langs.gls("discord_user_about", locale, user.name)
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name=langs.gls("discord_user_username", locale), value=user, inline=True)
        embed.add_field(name=langs.gls("discord_user_id", locale), value=user.id, inline=True)
        embed.add_field(name=langs.gls("generic_created_at", locale), value=langs.gts(user.created_at, locale, short=False), inline=True)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="emoji", aliases=["emote"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def emoji(self, ctx: commands.Context, emoji: discord.Emoji):
        """ Information on an emoji """
        locale = langs.gl(ctx)
        e = str(ctx.invoked_with)
        c = langs.gls(f"discord_emoji_{e}", locale)
        embed = discord.Embed(colour=general.random_colour())
        embed.description = langs.gls("discord_emoji", locale, c, emoji.name, emoji.id, langs.yes(emoji.animated, locale), emoji.guild.id,
                                      langs.gts(emoji.created_at, locale, short=False), emoji.url)
        embed.set_image(url=emoji.url)
        return await general.send(f"{ctx.author.name}:", ctx.channel, embed=embed)

    @commands.group(name="server", aliases=["guild"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def server(self, ctx: commands.Context):
        """ Information about the current server """
        if ctx.invoked_subcommand is None:
            locale = langs.gl(ctx)
            bots = sum(1 for member in ctx.guild.members if member.bot)
            bots_amt = bots / ctx.guild.member_count
            embed = discord.Embed(colour=general.random_colour())
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.title = langs.gls("discord_server_about", locale, ctx.guild.name)
            embed.add_field(name=langs.gls("discord_server_name", locale), value=ctx.guild.name, inline=True)
            embed.add_field(name=langs.gls("discord_server_id", locale), value=ctx.guild.id, inline=True)
            embed.add_field(name=langs.gls("discord_server_owner", locale), inline=True, value=f"{ctx.guild.owner}\n({ctx.guild.owner.display_name})")
            embed.add_field(name=langs.gls("generic_members", locale), value=langs.gns(ctx.guild.member_count, locale), inline=True)
            embed.add_field(name=langs.gls("discord_server_bots", locale), inline=True,
                            value=f"{langs.gns(bots, locale)} ({langs.gfs(bots_amt, locale, per=True)})")
            embed.add_field(name=langs.gls("discord_server_region", locale), value=ctx.guild.region, inline=True)
            embed.add_field(name=langs.gls("discord_server_roles", locale), value=langs.gns(len(ctx.guild.roles), locale), inline=True)
            try:
                embed.add_field(name=langs.gls("discord_server_bans", locale), value=langs.gns(len(await ctx.guild.bans()), locale), inline=True)
            except discord.Forbidden:
                embed.add_field(name=langs.gls("discord_server_bans", locale), value=langs.gls("discord_server_bans_denied", locale), inline=True)
            embed.add_field(name=langs.gls("discord_server_verification", locale), inline=True, value=str(ctx.guild.verification_level).capitalize())
            t, c, v = len(ctx.guild.text_channels), len(ctx.guild.categories), len(ctx.guild.voice_channels)
            tc, cc, vc = langs.gns(t, locale), langs.gns(c, locale), langs.gns(v, locale)
            embed.add_field(name=langs.gls("discord_server_channels", locale), value=langs.gls("discord_server_channels_data", locale, tc, cc, vc), inline=True)
            b, bl, bc = langs.gns(ctx.guild.premium_subscription_count, locale), langs.gns(ctx.guild.premium_tier, locale), \
                langs.gns(len(ctx.guild.premium_subscribers), locale)
            embed.add_field(name=langs.gls("discord_server_boosts", locale), value=langs.gls("discord_server_boosts_data", locale, b, bl, bc), inline=True)
            ani = len([emote for emote in ctx.guild.emojis if emote.animated])
            total_emotes = len(ctx.guild.emojis)
            el = ctx.guild.emoji_limit
            na = total_emotes - ani
            n, a, e, t = langs.gns(na, locale), langs.gns(ani, locale), langs.gns(el, locale), langs.gns(total_emotes, locale)
            embed.add_field(name=langs.gls("discord_server_emotes", locale), value=langs.gls("discord_server_emotes_data", locale, n, a, e, t), inline=True)
            ca = ctx.guild.created_at
            ct, cd = langs.gts(ca, locale, short=False), langs.td_dt(ca, locale, suffix=True)
            embed.add_field(name=langs.gls("generic_created_at", locale), value=f"{ct}\n{cd}", inline=False)
            return await general.send(None, ctx.channel, embed=embed)

    @server.command(name="icon", aliases=["avatar"])
    async def server_icon(self, ctx: commands.Context):
        """ Get server icon """
        return await general.send(langs.gls("discord_server_icon", langs.gl(ctx), ctx.guild.name,
                                            ctx.guild.icon_url_as(size=1024, static_format='png')), ctx.channel)

    @server.command(name="banner")
    async def server_banner(self, ctx: commands.Context):
        """ Get server banner """
        link = ctx.guild.banner_url_as(size=4096, format="png")
        locale = langs.gl(ctx)
        if link:
            return await general.send(langs.gls("discord_server_banner", locale, ctx.guild.name, link), ctx.channel)
        else:
            return await general.send(langs.gls("discord_server_banner_none", locale, ctx.guild.name), ctx.channel)

    @server.command(name="invite", aliases=["splash"])
    async def server_invite(self, ctx: commands.Context):
        """ Get server invite splash """
        link = ctx.guild.splash_url_as(size=4096, format="png")
        locale = langs.gl(ctx)
        if link:
            return await general.send(langs.gls("discord_server_inv_bg", locale, ctx.guild.name, link), ctx.channel)
        else:
            return await general.send(langs.gls("discord_server_inv_bg_none", locale, ctx.guild.name), ctx.channel)

    @server.command(name="bots")
    async def server_bots(self, ctx: commands.Context):
        """ Bots in the server """
        bots = [a for a in ctx.guild.members if a.bot]
        locale = langs.gl(ctx)
        m = ''
        for i in range(len(bots)):
            m += f"[{langs.gns(i + 1, locale, 2, False)}] {bots[i]}\n"
        rl = len(m)
        send = langs.gls("discord_server_bots_data", locale, ctx.guild.name)
        if rl > 1900:
            async with ctx.typing():
                data = BytesIO(str(m).encode('utf-8'))
                return await general.send(send, ctx.channel, file=discord.File(data, filename=f"{time.file_ts('Bots')}"))
        return await general.send(f"{send}\n```ini\n{m}```", ctx.channel)

    @commands.command(name="customrole", aliases=["cr"])
    @commands.guild_only()
    @commands.check(custom_role_enabled)
    @commands.cooldown(rate=1, per=30, type=commands.BucketType.user)
    async def custom_role(self, ctx: commands.Context, *, stuff: str):
        """ Custom Role (only in Senko Lair)
        -c/--colour/--color: Set role colour
        -n/--name: Set role name """
        data = self.bot.db.fetchrow("SELECT * FROM custom_role WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not data:
            return await general.send(f"Doesn't seem like you have a custom role in this server, {ctx.author.name}", ctx.channel)
        parser = arg_parser.Arguments()
        parser.add_argument('-c', '--colour', '--color', nargs=1)
        parser.add_argument('-n', '--name', nargs="+")
        args, valid_check = parser.parse_args(stuff)
        if not valid_check:
            return await general.send(args, ctx.channel)
        role = ctx.guild.get_role(data['rid'])
        if args.colour is not None:
            c = args.colour[0]
            a = len(c)
            if c == "random":
                col = general.random_colour()
            else:
                if a == 6 or a == 3:
                    try:
                        col = int(c, base=16)
                    except Exception as e:
                        return await general.send(f"Invalid colour - {type(e).__name__}: {e}", ctx.channel)
                else:
                    return await general.send("Colour must be either 3 or 6 HEX digits long.", ctx.channel)
            colour = discord.Colour(col)
        else:
            colour = role.colour
        try:
            name = ' '.join(args.name)
        except TypeError:
            name = role.name
        try:
            await role.edit(name=name, colour=colour, reason="Custom Role change")
        except Exception as e:
            return await general.send(f"An error occurred while updating custom role: {type(e).__name__}: {e}", ctx.channel)
        return await general.send(f"Successfully updated your custom role, {ctx.author.name}", ctx.channel)

    @commands.command(name="grantrole")
    @commands.guild_only()
    @commands.check(custom_role_enabled)
    # @commands.is_owner()
    @permissions.has_permissions(administator=True)
    async def grant_custom_role(self, ctx: commands.Context, user: discord.Member, role: discord.Role):
        """ Grant custom role """
        already = self.bot.db.fetchrow("SELECT * FROM custom_role WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not already:
            result = self.bot.db.execute("INSERT INTO custom_role VALUES (?, ?, ?)", (user.id, role.id, ctx.guild.id))
            try:
                await user.add_roles(role, reason="Custom Role grant")
                return await general.send(f"Granted {role.name} to {user.name}: {result}", ctx.channel)
            except discord.Forbidden:
                return await general.send(f"{role.name} could not be granted to {user.name}. It has, however, been saved to the database.", ctx.channel)
        else:
            result = self.bot.db.execute("UPDATE custom_role SET rid=? WHERE uid=? AND gid=?", (role.id, user.id, ctx.guild.id))
            return await general.send(f"Updated custom role of {user.name} to {role.name}: {result}", ctx.channel)

    @commands.command(name="remind", aliases=["remindme"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @commands.check(lambda ctx: ctx.bot.name == "suager")
    async def remind_me(self, ctx: commands.Context, duration: str, *, reminder: str):
        """ Set yourself a reminder. """
        delta = time.interpret_time(duration)
        if time.rd_is_above_5y(delta):
            return await general.send("You can't specify a time range above 5 years.", ctx.channel)
        expiry, error = time.add_time(delta)
        if error:
            return await general.send(f"Failed to convert duration: {expiry}", ctx.channel)
        diff = langs.td_rd(delta, "en_gb", accuracy=7, brief=False, suffix=True)
        when = langs.gts(expiry, "en_gb", True, True, False, True, False)
        random_id = general.random_id(ctx)
        self.bot.db.execute("INSERT INTO temporary VALUES (?, ?, ?, ?, ?, ?, ?)", (ctx.author.id, "reminder", expiry, None, reminder, random_id, False))
        return await general.send(f"Okay **{ctx.author.name}**, I will remind you about this **{diff}** ({when})", ctx.channel)

    @commands.command(name="reminders")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.check(lambda ctx: ctx.bot.name == "suager")
    async def reminders(self, ctx: commands.Context):
        """ See a list of your currently active reminders """
        reminders = self.bot.db.fetch("SELECT * FROM temporary WHERE uid=? AND type='reminder' ORDER BY expiry", (ctx.author.id,))
        if not reminders:
            return await general.send(f"You have no reminders active at the moment, {ctx.author.name}.", ctx.channel)
        output = f"**{ctx.author}**, here is the list of your currently active reminders"
        outputs = []
        _reminder = 0
        for reminder in reminders:
            _reminder += 1
            expiry = reminder["expiry"]
            expires_on = langs.gts(expiry, "en_gb", True, True, False, True, False)
            expires_in = langs.td_dt(expiry, "en_gb", accuracy=3, brief=False, suffix=True)
            outputs.append(f"**{_reminder})** {reminder['message']}\nActive for {expires_on}\nReminds {expires_in}")
        output2 = "\n\n".join(outputs)
        try:
            if len(output2) > 1900:
                _data = BytesIO(str(output2).encode('utf-8'))
                return await ctx.author.send(output, file=discord.File(_data, filename=f"{time.file_ts('Reminders')}"))
            else:
                return await ctx.author.send(f"{output}\n{output2}")
        except discord.Forbidden:
            return await general.send("You need to have your DMs open for me to be able to send you the list of your reminders.", ctx.channel)


def setup(bot):
    bot.add_cog(Utility(bot))
