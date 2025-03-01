from __future__ import annotations

import json
import random
from datetime import timedelta
from io import BytesIO

import discord
import pytz
from PIL import Image, ImageDraw, ImageFont
from regaus import conworlds, time as time2

from utils import arg_parser, bases, bot_data, commands, emotes, general, http, images, permissions, time


def custom_role_enabled(ctx):
    return ctx.guild is not None and ctx.guild.id in [568148147457490954, 430945139142426634, 738425418637639775, 784357864482537473, 759095477979054081]


class Utility(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.command(name="time")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def current_time(self, ctx: commands.Context, *, user: discord.User = None):
        """ Current time - input another user to see their local time """
        language = self.bot.language(ctx)
        user = user or ctx.author
        if self.bot.name == "cobble":
            place = conworlds.Place("Virsetgar")
            now = time2.datetime.now(place.tz, time2.Kargadia)
            # Try to get the local language name for Virsetgar
            start = None
            for _lang in language.fallbacks(place.languages):
                start = place.names.get(_lang)
                if start is not None:
                    break
            if start is None:
                start = "Virsetgar"
            utc_name = f"Current time in {start}"
        else:
            now = time2.datetime.now()
            utc_name = language.string("util_time_utc")
        embed = discord.Embed(colour=general.random_colour(), title=language.string("util_time_current"))
        utc_time = language.time(now, short=0, dow=True, seconds=True, tz=True)
        own_time = language.time(now, short=0, dow=True, seconds=True, tz=True, uid=ctx.author.id)
        user_time = language.time(now, short=0, dow=True, seconds=True, tz=True, uid=user.id)
        embed.add_field(name=utc_name, value=utc_time, inline=False)
        embed.add_field(name=language.string("util_time_your"), value=own_time, inline=False)
        if user.id != ctx.author.id:
            embed.add_field(name=language.string("util_time_user", user=general.username(user)), value=user_time, inline=False)
        # send = f"{start}: **{language.time(now, short=0, dow=True, seconds=True, tz=True)}**"
        # if user.id == ctx.author.id:
        #     send += language.string("util_time_custom", time=language.time(now, short=0, dow=True, seconds=True, tz=True, uid=ctx.author.id))
        # else:
        #     send += language.string("util_time_custom2", user=general.username(user), time=language.time(now, short=0, dow=True, seconds=True, tz=True, uid=user.id))
        return await ctx.send(embed=embed)

    @commands.command(name="base", aliases=["bases", "bc"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    # async def base_conversions(self, ctx: commands.Context, number: str, conversion: str, base: int, caps: bool = False):
    async def base_conversions(self, ctx: commands.Context, base_from: int, base_to: int, number: str, float_precision: int = 5, caps: str = ""):
        """ Convert numbers between bases

        The float precision argument controls how many places after the dot will be shown
        Write `"caps"` after the number if you want letters outputted in uppercase (ie. "1AA" instead of "1aa" for bases 11 and up)
        Usage example: `//base 10 16 420.69 5 caps` will convert 420.69 from decimal to hexadecimal with precision of 5 places (420.69 -> 1A4.B0A3D)"""
        if not (2 <= base_from <= 36):
            return await ctx.send("The base value must be between 2 and 36...")
        if not (2 <= base_to <= 36):
            return await ctx.send("The base value must be between 2 and 36...")
        if not (0 <= float_precision <= 100):
            return await ctx.send("The precision must be between 0 and 100...")
        try:
            float_conv = "." in number
            if base_from == 10:
                mid = float(number) if float_conv else int(number, base=10)
            else:
                mid = bases.from_base_float(number, base_from, 160) if float_conv else bases.from_base(number, base_from)
            caps = caps.lower() == "caps"
            end = bases.to_base_float(mid, base_to, float_precision, caps) if float_conv else bases.to_base(mid, base_to, caps)
            return await ctx.send(f"{general.username(ctx.author)}: {number} (base {base_from}) -> {end} (base {base_to})")
        except ValueError:
            return await ctx.send(f"{general.username(ctx.author)}, this number is invalid.")
        except OverflowError:
            return await ctx.send(f"{general.username(ctx.author)}, the number specified is too large to convert to a proper value.")

    @commands.command(name="settz", aliases=["tz", "settimezone", "timezone"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def set_timezone(self, ctx: commands.Context, tz: str = None):
        """ Set your timezone - Use "reset" to reset your timezone """
        language = self.bot.language(ctx)
        if tz is None or tz.lower() == "help":
            return await ctx.send(language.string("util_time_tz_help", command=ctx.clean_prefix + ctx.invoked_with))
        elif tz.lower() == "reset":
            self.bot.db.execute("DELETE FROM timezones WHERE uid=?", (ctx.author.id,))
            return await ctx.send(language.string("util_time_tz_reset"))
        elif tz.lower() == "list":
            file = discord.File(BytesIO("\n".join(pytz.all_timezones).encode("utf-8")), filename="timezones.txt")
            return await ctx.send(language.string("util_time_tz_list"), file=file)
        elif len(tz) == 2:
            def human_offset(_zone):
                return time2.format_offset(offset(_zone))

            def offset(_zone):
                return pytz.timezone(_zone).utcoffset(now)

            try:
                country = language.string(f"country_{tz}")
                now = time.now2()
                timezones = "\n".join([f"`{human_offset(zone)} {zone}`" for zone in sorted(pytz.country_timezones[tz.upper()], key=offset, reverse=True)])
                return await ctx.send(language.string("util_time_tz_country", country=country, timezones=timezones, command=ctx.clean_prefix + ctx.invoked_with))
            except KeyError:
                return await ctx.send(language.string("util_time_tz_country_none", country=tz))
        try:
            data = self.bot.db.fetchrow("SELECT * FROM timezones WHERE uid=?", (ctx.author.id,))
            _tz = pytz.timezone(tz)
            if data:
                self.bot.db.execute("UPDATE timezones SET tz=? WHERE uid=?", (tz, ctx.author.id))
            else:
                self.bot.db.execute("INSERT INTO timezones VALUES (?, ?)", (ctx.author.id, tz))
            return await ctx.send(language.string("util_time_tz", tz=str(_tz), command=ctx.clean_prefix + ctx.invoked_with))
            # return await general.send(f"Your timezone has been set to {_tz}", ctx.channel)
        except pytz.UnknownTimeZoneError:
            return await ctx.send(language.string("util_time_tz_error", tz=tz, command=ctx.clean_prefix + ctx.invoked_with))
            # file = discord.File(BytesIO("\n".join(pytz.all_timezones).encode("utf-8")), filename="timezones.txt")
            # return await ctx.send(language.string("util_time_tz_error", tz=tz), file=file)
            # return await general.send(f"Timezone `{tz}` was not found. Attached is the list of all pytz timezones", ctx.channel, file=file)

    @commands.command(name="timesince", aliases=["timeuntil"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def time_since(self, ctx: commands.Context, _date: str = None, _time: str = None):
        """ Time difference
        If you don't specify any time, it will simply default to an arbitrary date within the near future"""
        language = self.bot.language(ctx)
        try:
            now = time2.datetime.now()
            date = time2.datetime(now.year, 1, 1)
            tz = self.bot.timezone(ctx.author.id, "Earth")
            if _date is None:
                def dt(_month, _day):
                    return time2.datetime(now.year, _month, _day, tz=tz)
                dates = [dt(1, 27), dt(3, 17), dt(4, 1), dt(4, 17), dt(5, 13), dt(8, 8), dt(10, 31), dt(11, 19), dt(12, 5),
                         time2.datetime(now.year + 1, 1, 1, tz=tz)]
                for _date in dates:
                    if now < _date:
                        date = _date
                        break
            else:
                try:
                    if not _time:
                        time_part = time2.time()  # 0:00:00
                    else:
                        _h, _m, *_s = _time.split(":")
                        h, m, s = int(_h), int(_m), int(_s[0]) if _s else 0
                        time_part = time2.time(h, m, s, 0, time2.utc)
                    _y, _m, _d = _date.split("-")
                    y, m, d = int(_y), int(_m), int(_d)
                    date_part = time2.date(y, m, d, time2.Earth)
                    date = time2.datetime.combine(date_part, time_part, time2.utc)
                    date2 = date.as_timezone(tz)
                    date = date.replace(tz=date2.tzinfo)
                except ValueError:
                    return await ctx.send("Failed to convert date. Make sure it is in the format `YYYY-MM-DD hh:mm:ss` (time part optional)")
            difference = language.delta_dt(date, accuracy=7, brief=False, affix=True)
            current_time = language.time(now, short=0, dow=False, seconds=True, tz=True, uid=ctx.author.id)
            specified_time = language.time(date, short=0, dow=False, seconds=True, tz=True, uid=ctx.author.id)
            return await ctx.send(language.string("util_timesince", now=current_time, then=specified_time, delta=difference))
        except Exception as e:
            return await ctx.send(language.string("util_timesince_error", err=f"{type(e).__name__}: {str(e)}"))

    @staticmethod
    async def time_diff(ctx: commands.Context, string: str, multiplier: int):
        language = ctx.language()
        try:
            # _delta = time.interpret_time(string) * multiplier
            # delta = time2.relativedelta(years=_delta.years, months=_delta.months, days=_delta.days, hours=_delta.hours, minutes=_delta.minutes, seconds=_delta.seconds)
            delta = time.interpret_time(string, time2.relativedelta, time2.Earth) * multiplier
            now = time2.datetime.now()
            then = now + delta
        except (ValueError, OverflowError) as e:
            return await ctx.send(language.string("util_timediff_error", err=f"{type(e).__name__}: {str(e)}"))
        difference = language.delta_rd(delta, accuracy=7, brief=False, affix=True)
        time_now = language.time(now, short=0, dow=False, seconds=True, tz=True, uid=ctx.author.id)
        time_then = language.time(then, short=0, dow=False, seconds=True, tz=True, uid=ctx.author.id)
        return await ctx.send(language.string("util_timediff", now=time_now, delta=difference, then=time_then))

    @commands.command(name="timein")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def time_in(self, ctx: commands.Context, time_period: str):
        """ Check what time it'll be in a specified period """
        return await self.time_diff(ctx, time_period, 1)

    @commands.command(name="timeago")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def time_ago(self, ctx: commands.Context, time_period: str, time_class: str = None):
        """ Check what time it was a specified period ago """
        return await self.time_diff(ctx, time_period, -1)

    @commands.command(name="weather")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def weather(self, ctx: commands.Context, *, place: str):
        """ Check weather in a place """
        language = self.bot.language(ctx)
        lang = "en" if language.data("_conlang") else language.string("_short")
        a = await ctx.send(f"{emotes.Loading} Loading weather for {place}...")
        try:
            token = self.bot.config["weather_api_token"]
            bio = await http.get(f"http://api.openweathermap.org/data/2.5/weather?appid={token}&lang={lang}&q={place}", res_method="read")
            await a.delete()
            data = json.loads(str(bio.decode("utf-8")))
            code = data["cod"]
            if code == 200:
                embed = discord.Embed(colour=random.randint(0, 0xffffff))
                try:
                    country = data["sys"]["country"].lower()
                except KeyError:
                    country = ""
                try:
                    tz = data["timezone"]
                except KeyError:
                    tz = 0
                # _time_locale = locale if locale not in ["rsl-1d", "rsl-5"] else "english"
                # local_time = languages.gts(time.now(None) + timedelta(seconds=tz), _time_locale)
                local_time = language.time(time.now(None) + timedelta(seconds=tz), short=1, dow=False, seconds=False, tz=False)
                if country:
                    country_name = language.string(f"country_{country}")
                    emote = f":flag_{country}: "
                else:
                    country_name = "Unknown country"
                    emote = ""
                embed.title = language.string("util_weather_title", place=data["name"], country=country_name, emote=emote)
                embed.description = language.string("util_weather_desc", time=local_time)
                weather_icon = data["weather"][0]["icon"]
                embed.set_thumbnail(url=f"http://openweathermap.org/img/wn/{weather_icon}@2x.png")
                embed.add_field(name=language.string("util_weather_weather"), value=data['weather'][0]['description'].capitalize(), inline=False)
                # _tk = data['main']['temp']
                # _tc = _tk - 273.15
                # _tf = _tc * 1.8 + 32
                # tk, tc, tf = language.number(_tk, precision=1), language.number(_tc, precision=1), language.number(_tf, precision=1)
                # embed.add_field(name=language.string("util_weather_temperature"), value=f"**{tc}°C** | {tk} K | {tf}°F", inline=False)
                embed.add_field(name=language.string("util_weather_temperature"), value=general.bold(language.temperature(data["main"]["temp"] - 273.15, precision=1)), inline=False)
                try:
                    # _tk = data["main"]["feels_like"]
                    # _tc = _tk - 273.15
                    # _tf = _tc * 1.8 + 32
                    # tk, tc, tf = language.number(_tk, precision=1), language.number(_tc, precision=1), language.number(_tf, precision=1)
                    # embed.add_field(name=language.string("util_weather_temperature2"), value=f"**{tc}°C** | {tk} K | {tf}°F", inline=False)
                    embed.add_field(name=language.string("util_weather_temperature2"), value=language.temperature(data["main"]["feels_like"] - 273.15, precision=1), inline=False)
                except KeyError:
                    pass
                try:
                    pressure = data["main"]["grnd_level"]
                except KeyError:
                    pressure = data["main"]["pressure"]
                embed.add_field(name=language.string("util_weather_pressure"), value=general.bold(f"{language.number(pressure)} hPa"), inline=False)
                embed.add_field(name=language.string("util_weather_humidity"), value=general.bold(language.number(data["main"]["humidity"] / 100, precision=0, percentage=True)), inline=False)
                # _sm = data["wind"]["speed"]
                # _sk = _sm * 3.6
                # _sb = _sk / 1.609  # imperial system bad
                # sm, sk, sb = language.number(_sm, precision=2), language.number(_sk, precision=2), language.number(_sb, precision=2)
                # embed.add_field(name=language.string("util_weather_wind"), value=language.string("util_weather_wind_data", sm, sk, sb), inline=False)
                embed.add_field(name=language.string("util_weather_wind"), value=general.bold(language.speed(data["wind"]["speed"] * 3.6, precision=2)), inline=False)
                embed.add_field(name=language.string("util_weather_clouds"), value=general.bold(language.number(data["clouds"]["all"] / 100, precision=0, percentage=True)), inline=False)
                sr = data["sys"]["sunrise"]
                ss = data["sys"]["sunset"]
                now = time.now(None)
                now_l = now + timedelta(seconds=tz)
                if sr != 0 and ss != 0:
                    srt = time.from_ts(sr + tz, None)
                    sst = time.from_ts(ss + tz, None)
                    sr, tr = language.time2(srt, seconds=False, tz=False), language.delta_dt(srt, source=now_l, accuracy=2, brief=True, affix=True)
                    ss, ts = language.time2(sst, seconds=False, tz=False), language.delta_dt(sst, source=now_l, accuracy=2, brief=True, affix=True)
                    embed.add_field(name=language.string("util_weather_sunrise"), value=f"**{sr}** | {tr}", inline=False)
                    embed.add_field(name=language.string("util_weather_sunset"), value=f"**{ss}** | {ts}", inline=False)
                try:
                    lat, long = data["coord"]["lat"], data["coord"]["lon"]
                    n, e = "N" if lat >= 0 else "S", "E" if long >= 0 else "W"
                    if lat < 0:
                        lat *= -1
                    if long < 0:
                        long *= -1
                    embed.add_field(name=language.string("util_weather_location"), value=f"{language.number(lat, precision=2)}°{n}, {language.number(long, precision=2)}°{e}", inline=False)
                except KeyError:
                    pass
                embed.timestamp = now
            else:
                return await ctx.send(language.string("util_weather_error", place=place, err=f"{code}: {data['message']}"))
        except Exception as e:
            return await ctx.send(language.string("util_weather_error", place=place, err=f"{type(e).__name__}: {str(e)}"))
        return await ctx.send(embed=embed)

    @commands.command(name="colour", aliases=["color"])
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def colour(self, ctx: commands.Context, *, colour: str = "random"):
        """ Information on a colour """
        language = self.bot.language(ctx)
        if colour.endswith(" -i"):
            colour = colour[:-3]
            image_only = True
        else:
            image_only = False

        if colour.lower() == "random":
            _colour = f"{random.randint(0, 0xffffff):06x}"
        else:
            try:
                if colour[0] == "#":
                    colour = colour[1:]
                a = len(colour)
                if a == 3:
                    d, e, f = colour
                    colour = f"{d}{d}{e}{e}{f}{f}"
                    a = 6
                if a != 6:
                    return await ctx.send(language.string("images_colour_invalid_value"))
                _colour = f"{int(colour, 16):06x}"
            except Exception as e:
                return await ctx.send(language.string("images_colour_invalid", err=f"{type(e).__name__}: {str(e)}"))

        if image_only:
            rgba_255 = (int(_colour[0:2], 16), int(_colour[2:4], 16), int(_colour[4:6], 16))
            image1 = Image.new(mode="RGBA", size=(512, 512), color=rgba_255)
            bio1 = BytesIO()
            image1.save(bio1, "PNG")
            bio1.seek(0)
            return await ctx.send(file=discord.File(bio1, "colour.png"))

        hex_6 = _colour[:6]
        int_6 = int(_colour[:6], 16)
        embed = discord.Embed(colour=int_6)
        rgba_255 = (int(_colour[0:2], 16), int(_colour[2:4], 16), int(_colour[4:6], 16))
        rgba_1 = tuple(f"{value / 255:.4f}" for value in rgba_255)
        brightness = sum(rgba_255) // 3
        red, green, blue = rgba_255
        embed.add_field(name=language.string("images_colour_hex"), value=f'#{hex_6}', inline=False)
        embed.add_field(name=language.string("images_colour_int"), value=str(int_6), inline=False)
        embed.add_field(name=language.string("images_colour_rgb") + " (0-255)", value=str(rgba_255), inline=False)
        embed.add_field(name=language.string("images_colour_rgb") + " (0-1)", value=str(rgba_1).replace("'", ""), inline=False)
        embed.add_field(name=language.string("images_colour_brightness"), value=str(brightness), inline=False)
        embed.add_field(name=language.string("images_colour_font"), inline=False, value="#000000" if brightness >= 128 or green >= 224 else "#ffffff")
        image1 = Image.new(mode="RGBA", size=(512, 512), color=rgba_255)
        bio1 = BytesIO()
        image1.save(bio1, "PNG")
        bio1.seek(0)
        embed.set_thumbnail(url="attachment://colour.png")
        rows = 2  # 4
        font_size = 48
        size = 256
        try:
            font = ImageFont.truetype(images.font_files["jetbrains mono"], size=font_size)
        except ImportError:
            await ctx.send(f"{emotes.Deny} It seems that image generation does not work properly here...")
            font = None
        image2 = Image.new(mode="RGBA", size=(size * 11, size * rows), color=(0, 0, 0, 1))
        up_red, up_green, up_blue = (255 - red) / 10, (255 - green) / 10, (255 - blue) / 10
        down_red, down_green, down_blue = red / 10, green / 10, blue / 10

        def _hex(value: int):
            return f"{value:02X}"

        for i in range(11):
            start2a = (size * i, 0)
            start2b = (size * i, size)
            red2a, green2a, blue2a = int(red + up_red * i), int(green + up_green * i), int(blue + up_blue * i)
            red2b, green2b, blue2b = int(red - down_red * i), int(green - down_green * i), int(blue - down_blue * i)
            image2a = Image.new(mode="RGBA", size=(size, size), color=(red2a, green2a, blue2a, 255))
            image2b = Image.new(mode="RGBA", size=(size, size), color=(red2b, green2b, blue2b, 255))
            draw2a = ImageDraw.Draw(image2a)
            draw2b = ImageDraw.Draw(image2b)
            hex2a = "#" + _hex(red2a) + _hex(green2a) + _hex(blue2a)
            hex2b = "#" + _hex(red2b) + _hex(green2b) + _hex(blue2b)
            # width2a, height2a = draw2a.textsize(hex2a, font)
            # width2b, height2b = draw2b.textsize(hex2b, font)
            sum2a = (red2a + green2a + blue2a) // 3
            sum2b = (red2b + green2b + blue2b) // 3
            fill2a = (0, 0, 0, 255) if sum2a >= 128 or green2a >= 224 else (255, 255, 255, 255)
            fill2b = (0, 0, 0, 255) if sum2b >= 128 or green2b >= 224 else (255, 255, 255, 255)
            draw2a.text((size // 2, size), hex2a, font=font, fill=fill2a, anchor="md")
            draw2b.text((size // 2, size), hex2b, font=font, fill=fill2b, anchor="md")
            # draw2a.text(((size - width2a) // 2, size - height2a - 5), hex2a, fill=fill2a, font=font)
            # draw2b.text(((size - width2b) // 2, size - height2b - 5), hex2b, fill=fill2b, font=font)
            image2.paste(image2a, start2a)
            image2.paste(image2b, start2b)

        bio2 = BytesIO()
        image2.save(bio2, "PNG")
        bio2.seek(0)
        embed.set_image(url="attachment://gradient.png")
        return await ctx.send(embed=embed, files=[discord.File(bio1, "colour.png"), discord.File(bio2, "gradient.png")])

    @commands.command(name="roll")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def roll(self, ctx: commands.Context, num1: int = 6, num2: int = 1):
        """ Rolls a number between given range """
        language = self.bot.language(ctx)
        if num1 > num2:
            v1, v2 = [num2, num1]
        else:
            v1, v2 = [num1, num2]
        r = random.randint(v1, v2)
        n1, n2, no = language.number(v1), language.number(v2), language.number(r)
        return await ctx.send(language.string("fun_roll", name=general.username(ctx.author), num1=n1, num2=n2, output=no))

    @commands.command(name="reverse")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def reverse_text(self, ctx: commands.Context, *, text: str):
        """ Reverses text """
        reverse = text[::-1].replace("@", "@\u200B").replace("&", "&\u200B")
        return await ctx.send(f"🔁 {general.username(ctx.author)}:\n{reverse}")

    @commands.command(name="dm")
    @commands.is_owner()
    async def dm(self, ctx: commands.Context, user_id: int, *, message: str):
        """ DM a user """
        try:
            await ctx.message.delete()
        except Exception as e:
            await ctx.send(f"Message deletion failed: `{type(e).__name__}: {e}`", delete_after=5)
        user = self.bot.get_user(user_id)
        if not user:
            return await ctx.send(f"Could not find a user with ID {user_id}")
        try:
            await user.send(message)
            return await ctx.send(f"✉ Sent DM to {user}", delete_after=5)
        except discord.Forbidden:
            return await ctx.send(f"Failed to send DM - the user might have blocked DMs, or be a bot.")

    @commands.command(name="tell")
    @commands.guild_only()
    @permissions.has_permissions(manage_messages=True)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def tell(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str):
        """ Say something to a channel """
        language = self.bot.language(ctx)
        try:
            await ctx.message.delete()
        except Exception as e:
            await ctx.send(language.string("fun_say_delete_fail", err=f"{type(e).__name__}: {str(e)}"), delete_after=5)
        if channel.guild != ctx.guild:
            return await ctx.send(language.string("fun_tell_guilds"))
        try:
            await channel.send(message)
        except Exception as e:
            return await ctx.send(language.string("fun_tell_fail", err=f"{type(e).__name__}: {str(e)}"))
        return await ctx.send(language.string("fun_tell_success", channel=channel.mention), delete_after=5)

    @commands.command(name="atell")
    @commands.is_owner()
    async def admin_tell(self, ctx: commands.Context, channel_id: int, *, message: str):
        """ Say something to a channel """
        channel = self.bot.get_channel(channel_id)
        try:
            await ctx.message.delete()
        except Exception as e:
            await ctx.send(f"Message deletion failed: `{type(e).__name__}: {e}`", delete_after=5)
        try:
            await channel.send(message)
        except Exception as e:
            return await ctx.send(f"{emotes.Deny} Failed to send the message: `{type(e).__name__}: {e}`")
        return await ctx.send(f"{emotes.Allow} Successfully sent the message to {channel.mention}", delete_after=5)

    @commands.command(name="vote")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def vote(self, ctx: commands.Context, *, text: str):
        """ Start a vote """
        language = self.bot.language(ctx)
        message = await ctx.send(language.string("fun_vote", name=general.username(ctx.author), text=text))
        await message.add_reaction(emotes.Allow)
        await message.add_reaction(emotes.Meh)
        await message.add_reaction(emotes.Deny)

    @commands.command(name="avatar", aliases=["av"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def avatar(self, ctx: commands.Context, *, who: discord.User = None):
        """ Get someone's avatar """
        user: discord.User | discord.Member = who or ctx.author
        return await ctx.send(self.bot.language(ctx).string("discord_avatar", user=general.username(user), avatar=str(user.display_avatar.replace(size=4096, static_format='png'))))

    @commands.command(name="avatar2", aliases=["av2", "a2", "ay"])
    @commands.is_owner()
    async def avatar_fetch(self, ctx: commands.Context, *users: int):
        """ Fetch and yoink avatars """
        for user in users:
            try:
                await ctx.send(str((await self.bot.fetch_user(user)).display_avatar.replace(size=4096, static_format="png")))
            except Exception as e:
                await ctx.send(f"{user} -> {type(e).__name__}: {e}")

    @commands.command(name="avatar3", aliases=["av3", "a3", "ag"])
    @commands.is_owner()
    async def avatar_guild(self, ctx: commands.Context, user_id: int, guild_id: int):
        """ Try to get a member's guild avatar """
        guild: discord.Guild = self.bot.get_guild(guild_id)
        if not guild:
            return await ctx.send(f"Guild {guild_id} was not found...")
        member: discord.Member = guild.get_member(user_id)
        if not member:
            return await ctx.send(f"Member {user_id} is not in {guild.name}...")
        avatar = member.guild_avatar
        if not avatar:
            return await ctx.send(f"{member} does not have a guild avatar in {guild.name}...")
        return await ctx.send(f"**{member}**'s avatar in **{guild.name}**:\n{avatar.replace(size=4096, static_format='png')}")

    @commands.group(name="role", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def role(self, ctx: commands.Context, *, role: discord.Role = None):
        """ Information on roles in the current server """
        if ctx.invoked_subcommand is None:
            language = self.bot.language(ctx)
            if role is None:
                all_roles = ""
                for num, role in enumerate(sorted(ctx.guild.roles, reverse=True), start=1):
                    all_roles += language.string("discord_role_list_item", i=f"{num:02d}", members=language.number(len(role.members)), role=role)
                data = BytesIO(all_roles.encode('utf-8'))
                return await ctx.send(language.string("discord_role_list", server=ctx.guild.name), file=discord.File(data, filename=f"{time.file_ts('Roles')}"))
            else:
                embed = discord.Embed(colour=role.colour)
                embed.title = language.string("discord_role_about", role=role.name)
                if ctx.guild.icon:
                    embed.set_thumbnail(url=str(ctx.guild.icon.replace(size=1024, static_format="png")))
                embed.add_field(name=language.string("discord_role_name"), value=role.name, inline=True)
                embed.add_field(name=language.string("discord_role_id"), value=str(role.id), inline=True)
                embed.add_field(name=language.string("discord_members"), value=language.number(len(role.members)), inline=True)
                embed.add_field(name=language.string("discord_role_colour"), value=str(role.colour), inline=True)
                embed.add_field(name=language.string("discord_role_mentionable"), value=language.yes(role.mentionable), inline=True)
                embed.add_field(name=language.string("discord_role_hoisted"), value=language.yes(role.hoist), inline=True)
                embed.add_field(name=language.string("discord_role_position"), value=language.number(role.position), inline=True)
                embed.add_field(name=language.string("discord_created_at"), value=language.time(role.created_at, short=0, dow=False, seconds=False, tz=True, at=True, uid=ctx.author.id), inline=True)
                embed.add_field(name=language.string("discord_role_default"), value=language.yes(role.is_default()), inline=True)
                return await ctx.send(embed=embed)

    @role.command(name="members")
    async def role_members(self, ctx: commands.Context, *, role: discord.Role):
        """ List of members who have a certain role """
        members = [a for a in ctx.guild.members if role in a.roles]
        members.sort(key=lambda a: a.name.lower())
        language = self.bot.language(ctx)
        m = ''
        for i in range(len(members)):
            m += f"[{i + 1:02d}] {members[i]}\n"
        rl = len(m)
        send = language.string("discord_role_members", role=role.name)
        if rl > 1900:
            async with ctx.typing():
                data = BytesIO(str(m).encode('utf-8'))
                return await ctx.send(send, file=discord.File(data, filename=f"{time.file_ts('Role_Members')}"))
        return await ctx.send(f"{send}\n```ini\n{m}```")

    @commands.command(name="joinedat", aliases=["joindate", "jointime"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def joined_at(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Check when someone joined server """
        user = who or ctx.author
        language = self.bot.language(ctx)
        return await ctx.send(language.string("discord_command_joined_at", user=user, server=ctx.guild.name,
                                              time=language.time(user.joined_at, short=0, dow=False, seconds=False, tz=True, at=True, uid=ctx.author.id)))

    @commands.command(name="createdat")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def created_at(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check when someone created their account """
        user = who or ctx.author
        language = self.bot.language(ctx)
        return await ctx.send(language.string("discord_command_created_at", user=user, time=language.time(user.created_at, short=0, dow=False, seconds=False, tz=True, at=True, uid=ctx.author.id)))

    @commands.command(name="user")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def user(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Get info about user """
        user: discord.Member = who or ctx.author
        language = self.bot.language(ctx)
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("discord_user_about", name=general.username(user))
        embed.set_thumbnail(url=str(user.display_avatar.replace(size=1024, static_format="png")))
        embed.add_field(name=language.string("discord_user_username"), value=user.name, inline=True)
        embed.add_field(name=language.string("discord_user_display_name"), value=user.global_name, inline=True)
        embed.add_field(name=language.string("discord_user_nickname"), value=user.nick, inline=True)
        embed.add_field(name=language.string("discord_user_id"), value=str(user.id), inline=True)
        embed.add_field(name=language.string("discord_created_at"), value=language.time(user.created_at, short=0, dow=False, seconds=False, tz=True, at=True, uid=ctx.author.id), inline=False)
        embed.add_field(name=language.string("discord_user_joined_at"), value=language.time(user.joined_at, short=0, dow=False, seconds=False, tz=True, at=True, uid=ctx.author.id), inline=False)
        if len(user.roles) < 15:
            r = user.roles
            r.sort(key=lambda x: x.position, reverse=True)
            ar = [f"<@&{x.id}>" for x in r if x.id != ctx.guild.default_role.id]
            roles = ', '.join(ar) if ar else language.string("generic_none")
            b = len(user.roles) - 1
            roles += language.string("discord_user_roles_overall", total=language.number(b))
        else:
            roles = language.string("discord_user_roles_many", total=language.number(len(user.roles) - 1))
        embed.add_field(name=language.string("discord_user_roles"), value=roles, inline=False)
        return await ctx.send(embed=embed)

    @commands.command(name="whois")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def who_is(self, ctx: commands.Context, *, user_id: int):
        """ Get info about a user """
        language = self.bot.language(ctx)
        try:
            user = await self.bot.fetch_user(user_id)
        except discord.NotFound:
            return await ctx.send(language.string("events_error_not_found_user", value=user_id))
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("discord_user_about", name=user.name)
        embed.set_thumbnail(url=str(user.display_avatar.replace(size=1024, static_format="png")))
        embed.add_field(name=language.string("discord_user_username"), value=user.name, inline=True)
        embed.add_field(name=language.string("discord_user_display_name"), value=user.global_name, inline=True)
        embed.add_field(name=language.string("discord_user_id"), value=str(user.id), inline=True)
        embed.add_field(name=language.string("discord_created_at"), value=language.time(user.created_at, short=0, dow=False, seconds=False, tz=True, at=True, uid=ctx.author.id), inline=True)
        return await ctx.send(embed=embed)

    @commands.command(name="emoji", aliases=["emote"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def emoji(self, ctx: commands.Context, emoji: discord.Emoji):
        """ Information on an emoji """
        language = self.bot.language(ctx)
        embed = discord.Embed(colour=general.random_colour())
        server = f"{emoji.guild.name} ({emoji.guild.id})"
        embed.description = language.string("discord_emoji", name=emoji.name, id=emoji.id, animated=language.yes(emoji.animated), server=server,
                                            created_at=language.time(emoji.created_at, short=0, dow=False, seconds=False, tz=True, uid=ctx.author.id), url=emoji.url)
        embed.set_image(url=emoji.url)
        return await ctx.send(f"{general.username(ctx.author)}:", embed=embed)

    @commands.group(name="server", aliases=["guild"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def server(self, ctx: commands.Context, guild: discord.Guild = None):
        """ Information about the current server """
        if ctx.invoked_subcommand is None:
            guild: discord.Guild = guild or ctx.guild
            language = self.bot.language(ctx)
            bots = sum(1 for member in guild.members if member.bot)
            bots_amt = bots / guild.member_count
            embed = discord.Embed(colour=general.random_colour())
            if ctx.guild.icon:
                embed.set_thumbnail(url=str(guild.icon.replace(size=1024, static_format="png")))
            embed.title = language.string("discord_server_about", server=guild.name)
            embed.add_field(name=language.string("discord_server_name"), value=guild.name, inline=True)
            embed.add_field(name=language.string("discord_server_id"), value=guild.id, inline=True)
            embed.add_field(name=language.string("discord_server_owner"), inline=True, value=f"{guild.owner}\n({guild.owner.display_name})")
            embed.add_field(name=language.string("discord_members"), value=language.number(guild.member_count), inline=True)
            embed.add_field(name=language.string("discord_server_bots"), value=f"{language.number(bots)} ({language.number(bots_amt, percentage=True)})", inline=True)
            embed.add_field(name=language.string("discord_server_region"), value="Deprecated", inline=True)
            embed.add_field(name=language.string("discord_server_roles"), value=language.number(len(guild.roles)), inline=True)
            try:
                embed.add_field(name=language.string("discord_server_bans"), value=language.number(len([_ async for _ in ctx.guild.bans(limit=None)])), inline=True)
            except discord.Forbidden:
                embed.add_field(name=language.string("discord_server_bans"), value=language.string("discord_server_bans_denied"), inline=True)
            embed.add_field(name=language.string("discord_server_verification"), inline=True, value=str(guild.verification_level).capitalize())
            t, c, v = len(guild.text_channels), len(guild.categories), len(guild.voice_channels)
            tc, cc, vc = language.number(t), language.number(c), language.number(v)
            embed.add_field(name=language.string("discord_server_channels"), value=language.string("discord_server_channels_data", text=tc, cats=cc, voice=vc), inline=True)
            b, bl, bc = language.number(guild.premium_subscription_count), language.number(guild.premium_tier), language.number(len(guild.premium_subscribers))
            embed.add_field(name=language.string("discord_server_boosts"), value=language.string("discord_server_boosts_data", boosts=b, level=bl, users=bc), inline=True)
            ani = len([emote for emote in guild.emojis if emote.animated])
            total_emotes = len(guild.emojis)
            el = guild.emoji_limit
            na = total_emotes - ani
            n, a, e, t = language.number(na), language.number(ani), language.number(el), language.number(total_emotes)
            embed.add_field(name=language.string("discord_server_emotes"), value=language.string("discord_server_emotes_data", static=n, ani=a, limit=e, total=t), inline=True)
            ca = guild.created_at
            ct, cd = language.time(ca, short=0, dow=False, seconds=False, tz=True, at=True, uid=ctx.author.id), language.delta_dt(ca, accuracy=3, brief=False, affix=True)
            embed.add_field(name=language.string("discord_created_at"), value=f"{ct}\n{cd}", inline=False)
            return await ctx.send(embed=embed)

    @server.command(name="icon", aliases=["avatar"])
    async def server_icon(self, ctx: commands.Context):
        """ Get server icon """
        language = ctx.language()
        if ctx.guild.icon:
            return await ctx.send(language.string("discord_server_icon", server=ctx.guild.name, url=str(ctx.guild.icon.replace(size=4096, static_format='png'))))
        else:
            return await ctx.send(language.string("discord_server_icon_none", server=ctx.guild.name))

    @server.command(name="banner")
    async def server_banner(self, ctx: commands.Context):
        """ Get server banner """
        language = self.bot.language(ctx)
        if ctx.guild.banner:
            return await ctx.send(language.string("discord_server_banner", server=ctx.guild.name, url=str(ctx.guild.banner.replace(size=4096, static_format="png"))))
        else:
            return await ctx.send(language.string("discord_server_banner_none", server=ctx.guild.name))

    @server.command(name="invitebg", aliases=["invite", "splash"])
    async def server_invite(self, ctx: commands.Context):
        """ Get server invite splash """
        language = self.bot.language(ctx)
        if ctx.guild.splash:
            return await ctx.send(language.string("discord_server_inv_bg", server=ctx.guild.name, url=str(ctx.guild.splash.replace(size=4096, static_format="png"))))
        else:
            return await ctx.send(language.string("discord_server_inv_bg_none", server=ctx.guild.name))

    @server.command(name="bots")
    async def server_bots(self, ctx: commands.Context):
        """ Bots in the server """
        bots = [a for a in ctx.guild.members if a.bot]
        language = self.bot.language(ctx)
        m = ''
        for i in range(len(bots)):
            m += f"[{i + 1:02d}] {bots[i]}\n"
        rl = len(m)
        send = language.string("discord_server_bots_data", server=ctx.guild.name)
        if rl > 1900:
            async with ctx.typing():
                data = BytesIO(str(m).encode('utf-8'))
                return await ctx.send(send, file=discord.File(data, filename=f"{time.file_ts('Bots')}"))
        return await ctx.send(f"{send}\n```ini\n{m}```")

    @commands.command(name="embed")
    @permissions.has_permissions(embed_links=True)
    @commands.bot_has_permissions(embed_links=True)
    async def embed_creator(self, ctx: commands.Context, *, args: str):
        """ Create a custom embed
        -t/--title: Embed's title text
        -d/--description: Embed's description text
        -f/--footer: Embed's footer text
        -th/--thumbnail: URL to embed's thumbnail
        -i/--image: URL to embed's image
        -c/--colour: A hex code for embed's colour

        All of the arguments are optional, so if you don't fill them they will simply be empty.
        Use "\n" to add newlines - The current implementation of the code doesn't insert them otherwise
        Example: //embed --title Good evening --description Some very interesting text --colour ff0057"""
        embed = discord.Embed()
        parser = arg_parser.Arguments()
        parser.add_argument('-t', '--title', nargs="+")
        parser.add_argument('-d', '--description', nargs="+")
        parser.add_argument('-f', '--footer', nargs="+")
        parser.add_argument('-th', '--thumbnail', nargs=1)
        parser.add_argument('-i', '--image', nargs=1)
        parser.add_argument('-c', '--colour', nargs=1)
        if self.bot.name == "kyomi":
            parser.add_argument('-a', '--author', action='store_true')
        else:
            embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)

        args, valid_check = parser.parse_args(args)
        if not valid_check:
            return await ctx.send(args)
        if self.bot.name == "kyomi":
            if args.author:
                embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
        if args.title:
            embed.title = " ".join(args.title).replace("\\n", "\n")
            if len(embed.title) > 256:
                return await ctx.send("Embed title cannot be longer than 256 characters. Blame discord.")
        if args.description:
            embed.description = " ".join(args.description).replace("\\n", "\n")
        if args.footer:
            embed.set_footer(text=" ".join(args.footer).replace("\\n", "\n"))
        if args.thumbnail:
            embed.set_thumbnail(url=args.thumbnail[0])
        if args.image:
            embed.set_image(url=args.image[0])
        if args.colour:
            colour = args.colour[0]
            a = len(colour)
            if colour.startswith("#"):
                colour = colour[1:]
                a = len(colour)
            if a == 6 or a == 3:
                try:
                    col = int(colour, base=16)
                except Exception as e:
                    return await ctx.send(f"Invalid colour - {type(e).__name__}: {e}")
            else:
                return await ctx.send("Colour must be either 3 or 6 HEX digits long.")
            embed.colour = col
        return await ctx.send(embed=embed)


class Reminders(Utility, name="Utility"):
    @commands.command(name="remind", aliases=["remindme"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def remind_me(self, ctx: commands.Context, duration: str, *, reminder: str):
        """ Set yourself a reminder.

        Example: //remind 2d12h Insert something interesting here"""
        language = self.bot.language(ctx)
        delta = time.interpret_time(duration)
        if time.rd_is_above_5y(delta):
            return await ctx.send(language.string("util_reminders_limit"))
            # return await general.send("You can't specify a time range above 5 years.", ctx.channel)
        expiry, error = time.add_time(delta)
        if error:
            return await ctx.send(language.string("util_reminders_error", err=expiry))
            # return await general.send(f"Failed to convert duration: {expiry}", ctx.channel)
        diff = language.delta_rd(delta, accuracy=7, brief=False, affix=True)
        when = language.time(expiry, short=1, dow=False, seconds=True, tz=True, uid=ctx.author.id, at=True)
        # random_id = general.random_id()
        # while self.bot.db.fetch("SELECT entry_id FROM temporary WHERE entry_id=?", (random_id,)):
        #     random_id = general.random_id()
        # self.bot.db.execute("INSERT INTO temporary VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (ctx.author.id, "reminder", expiry, None, reminder, random_id, False, self.bot.name))
        self.bot.db.execute("INSERT INTO reminders(uid, expiry, message, handled, bot) VALUES (?, ?, ?, ?, ?)", (ctx.author.id, expiry, reminder, 0, self.bot.name))
        return await ctx.send(language.string("util_reminders_success", author=general.username(ctx.author), delta=diff, time=when, p=ctx.prefix))
        # return await general.send(f"Okay **{ctx.author.name}**, I will remind you about this **{diff}** ({when} UTC)", ctx.channel)

    @commands.group(name="reminders", aliases=["reminder"])
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def reminders(self, ctx: commands.Context):
        """ See a list of your currently active reminders, and modify them """
        if ctx.invoked_subcommand is None:
            language = self.bot.language(ctx)
            # reminders = self.bot.db.fetch("SELECT * FROM temporary WHERE uid=? AND type='reminder' AND bot=? ORDER BY expiry", (ctx.author.id, self.bot.name))
            reminders = self.bot.db.fetch("SELECT * FROM reminders WHERE uid=? AND bot=? ORDER BY expiry", (ctx.author.id, self.bot.name))
            if not reminders:
                return await ctx.send(language.string("util_reminders_none", author=general.username(ctx.author)))
                # return await general.send(f"You have no reminders active at the moment, {ctx.author.name}.", ctx.channel)
            output = language.string("util_reminders_list", author=general.username(ctx.author))
            # output = f"**{ctx.author}**, here is the list of your currently active reminders"
            outputs = []
            _reminder = 0
            for reminder in reminders:
                _reminder += 1
                expiry = reminder["expiry"]
                expires_on = language.time(expiry, short=1, dow=False, seconds=True, tz=True, at=True, uid=ctx.author.id)
                expires_in = language.delta_dt(expiry, accuracy=3, brief=False, affix=True)
                outputs.append(language.string("util_reminders_item", i=_reminder, message=reminder["message"], id=reminder["id"], time=expires_on, delta=expires_in))
                # outputs.append(f"**{_reminder})** {reminder['message']}\nActive for {expires_on}\nReminds {expires_in}")
            output2 = "\n\n".join(outputs)
            output3 = language.string("util_reminders_list_end", p=ctx.prefix)
            if len(output2) > 1900:
                _data = BytesIO(str(output2).encode('utf-8'))
                return await ctx.send(output + output3, file=discord.File(_data, filename=f"{time.file_ts('Reminders')}"))
            else:
                return await ctx.send(f"{output}\n\n{output2}{output3}")

    @reminders.command(name="edit")
    async def reminders_edit(self, ctx: commands.Context, reminder_id: int, *, args: str):
        """ Edit a reminder
        -m/--message/--text: Edit the reminder's text
        -t/--time/--expiry: Edit when you want to be reminded (Format: `YYYY-MM-DD hh:mm:ss`)
        Time part optional, and may be just `hh:mm`. Time must be in 24-hour format.

        Example: //reminders edit 1048576 --time 2021-06-08 17:00:00 --message Insert something interesting here"""
        language = self.bot.language(ctx)
        reminder = self.bot.db.fetchrow("SELECT * FROM reminders WHERE id=? AND uid=? AND bot=?", (reminder_id, ctx.author.id, self.bot.name))
        if not reminder:
            return await ctx.send(language.string("util_reminders_edit_none", id=reminder_id))
        parser = arg_parser.Arguments()
        parser.add_argument('-m', '--message', '--text', nargs="+")
        parser.add_argument('-t', '--time', '--expiry', nargs="+")
        args, valid_check = parser.parse_args(args)
        if not valid_check:
            return await ctx.send(args)
        message = args.message
        _message = " ".join(message) if message else reminder["message"]
        _expiry = reminder["expiry"]
        if args.time is not None:
            _datetime = args.time
            try:
                if len(_datetime) == 1:
                    _date, time_part = _datetime[0], time2.time()  # 0:00:00
                elif len(_datetime) == 2:
                    _date, _time = _datetime
                    _time = _time.replace(".", ":")
                    # c = _time.count(":")
                    # if c == 1:
                    #     _time = f"{_time}:00"
                    _h, _m, *_s = _time.split(":")
                    h, m, s = int(_h), int(_m), int(_s[0]) if _s else 0
                    time_part = time2.time(h, m, s, 0, time2.utc)
                else:
                    return await ctx.send(language.string("util_reminders_edit_time2"))

                _date = _date.replace(".", "-").replace("/", "-")
                _y, _m, _d = _date.split("-")
                y, m, d = int(_y), int(_m), int(_d)
                date_part = time2.date(y, m, d, time2.Earth)

                _expiry = time2.datetime.combine(date_part, time_part, time2.utc)
                _expiry2 = _expiry.as_timezone(self.bot.timezone(ctx.author.id))
                _expiry.replace_self(tz=_expiry2.tzinfo)
                _expiry = _expiry.to_timezone(time2.timezone.utc).to_datetime().replace(tzinfo=None)  # convert into a datetime object with null tzinfo
                # _expiry = datetime.strptime(f"{_date} {_time}", "%Y-%m-%d %H:%M:%S")
                # _expiry = _expiry.replace(tzinfo=self.bot.timezone(ctx.author.id)).astimezone(time2.timezone.utc).replace(tzinfo=None)
            except ValueError:
                return await ctx.send(language.string("util_reminders_edit_time"))
        expiry = language.time(_expiry, short=1, dow=False, seconds=True, tz=True, at=True, uid=ctx.author.id)
        self.bot.db.execute("UPDATE reminders SET message=?, expiry=? WHERE id=?", (_message, _expiry, reminder_id))
        return await ctx.send(language.string("util_reminders_edit", id=reminder_id, message=_message, time=expiry))

    @reminders.command(name="delete", aliases=["del", "remove", "cancel"])
    async def reminders_delete(self, ctx: commands.Context, reminder_id: int):
        """ Delete a reminder """
        language = self.bot.language(ctx)
        reminder = self.bot.db.fetchrow("SELECT * FROM reminders WHERE id=? AND uid=? AND bot=?", (reminder_id, ctx.author.id, self.bot.name))
        if not reminder:
            return await ctx.send(language.string("util_reminders_edit_none", id=reminder_id))
        self.bot.db.execute("DELETE FROM reminders WHERE id=? AND uid=?", (reminder_id, ctx.author.id))
        return await ctx.send(language.string("util_reminders_delete", id=reminder_id))


class UtilitySuager(Reminders, name="Utility"):
    @commands.command(name="customrole", aliases=["cr"])
    @commands.guild_only()
    @commands.check(custom_role_enabled)
    @commands.cooldown(rate=1, per=20, type=commands.BucketType.user)
    async def custom_role(self, ctx: commands.Context, *, stuff: str):
        """ Set up your custom role
        -c/--colour/--color: Set role colour
        -n/--name: Set role name

        Example: //customrole --name Role Name --colour ff0057"""
        data = self.bot.db.fetchrow("SELECT * FROM custom_role WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not data:
            return await ctx.send(f"Doesn't seem like you have a custom role in this server, {general.username(ctx.author)}")
        parser = arg_parser.Arguments()
        parser.add_argument('-c', '--colour', '--color', nargs=1)
        parser.add_argument('-n', '--name', nargs="+")
        args, valid_check = parser.parse_args(stuff)
        if not valid_check:
            return await ctx.send(args)
        role = ctx.guild.get_role(data['rid'])
        if args.colour is not None:
            c = args.colour[0]
            a = len(c)
            if c == "random":
                col = general.random_colour()
            else:
                if c.startswith("#"):
                    c = c[1:]
                    a = len(c)
                if a == 6 or a == 3:
                    try:
                        col = int(c, base=16)
                    except Exception as e:
                        return await ctx.send(f"Invalid colour - {type(e).__name__}: {e}")
                else:
                    return await ctx.send("Colour must be either 3 or 6 HEX digits long.")
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
            return await ctx.send(f"An error occurred while updating custom role: {type(e).__name__}: {e}")
        return await ctx.send(f"Successfully updated your custom role, {general.username(ctx.author)}")

    @commands.command(name="grantrole")
    @commands.guild_only()
    @commands.check(custom_role_enabled)
    @permissions.has_permissions(administrator=True)
    async def grant_custom_role(self, ctx: commands.Context, user: discord.Member, role: discord.Role):
        """ Grant custom role """
        already = self.bot.db.fetchrow("SELECT * FROM custom_role WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not already:
            self.bot.db.execute("INSERT INTO custom_role VALUES (?, ?, ?)", (user.id, role.id, ctx.guild.id))
            try:
                await user.add_roles(role, reason="Custom Role grant")
                return await ctx.send(f"Granted {role.name} to {general.username(ctx.author)}")
            except discord.Forbidden:
                return await ctx.send(f"{role.name} could not be granted to {general.username(ctx.author)}. It has, however, been saved to the database.")
        else:
            self.bot.db.execute("UPDATE custom_role SET rid=? WHERE uid=? AND gid=?", (role.id, user.id, ctx.guild.id))
            return await ctx.send(f"Updated custom role of {general.username(ctx.author)} to {role.name}")


class UtilityCobble(Utility, name="Utility"):
    @commands.command(name="timesince", aliases=["timeuntil"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def time_since(self, ctx: commands.Context, _date: str = None, _time: str = None, _time_class: str = "Kargadia"):
        """ Time difference
        If you don't specify any time, it will simply default to an arbitrary date within the near future"""
        language = self.bot.language(ctx)
        try:
            # if not _time_class:
            #     time_class = time2.Earth
            # else:
            try:
                time_class = getattr(time2, _time_class)
            except AttributeError:
                return await ctx.send("Time class not found...")
            else:
                if not issubclass(time_class, time2.Earth):
                    return await ctx.send("Invalid time class specified...")
            now = time2.datetime.now(time_class=time_class)
            date = time2.datetime(now.year, 1, 1, time_class=time_class)
            tz = self.bot.timezone(ctx.author.id, _time_class)
            if _date is None and _time_class == "Kargadia":
                def dt(_month, _day):
                    return time2.datetime(now.year, _month, _day, tz=tz, time_class=time_class)
                dates = [dt(1, 6), dt(3, 12), dt(4, 8), dt(7, 9), dt(8, 11), dt(11, 2), dt(14, 1), dt(16, 5),
                         time2.datetime(now.year + 1, 1, 1, tz=tz, time_class=time_class)]
                for _date in dates:
                    if now < _date:
                        date = _date
                        break
            else:
                try:
                    if not _time:
                        time_part = time2.time()  # 0:00:00
                    else:
                        _h, _m, *_s = _time.split(":")
                        h, m, s = int(_h), int(_m), int(_s[0]) if _s else 0
                        time_part = time2.time(h, m, s, 0, time2.utc)
                    _y, _m, _d = _date.split("-")
                    y, m, d = int(_y), int(_m), int(_d)
                    date_part = time2.date(y, m, d, time_class)
                    # The funky timezone behaviour isn't needed here because this won't interact with pytz timezones
                    date = time2.datetime.combine(date_part, time_part, tz)
                except ValueError:
                    return await ctx.send("Failed to convert date. Make sure it is in the format `YYYY-MM-DD hh:mm:ss` (time part optional)")
            difference = language.delta_dt(date, accuracy=7, brief=False, affix=True)
            current_time = language.time(now, short=0, dow=False, seconds=True, tz=True, uid=ctx.author.id)
            specified_time = language.time(date, short=0, dow=False, seconds=True, tz=True, uid=ctx.author.id)
            return await ctx.send(language.string("util_timesince", now=current_time, then=specified_time, delta=difference))
        except Exception as e:
            # await ctx.send(general.traceback_maker(e))
            return await ctx.send(language.string("util_timesince_error", err=f"{type(e).__name__}: {str(e)}"))

    @staticmethod
    async def time_diff(ctx: commands.Context, string: str, multiplier: int, _time_class: str = None):
        language = ctx.language()
        if not _time_class:
            time_class = time2.Kargadia
        else:
            try:
                time_class = getattr(time2, _time_class)
            except AttributeError:
                return await ctx.send("Time class not found")
            else:
                if not issubclass(time_class, time2.Earth):
                    return await ctx.send("Invalid time class specified")
        try:
            delta = time.interpret_time(string, time2.relativedelta, time_class) * multiplier
            # delta = time2.relativedelta(years=_delta.years, months=_delta.months, days=_delta.days, hours=_delta.hours, minutes=_delta.minutes, seconds=_delta.seconds, time_class=time_class)
            now = time2.datetime.now(time_class=time_class)
            then = now + delta
        except (ValueError, OverflowError) as e:
            return await ctx.send(language.string("util_timediff_error", err=f"{type(e).__name__}: {str(e)}"))
        difference = language.delta_rd(delta, accuracy=7, brief=False, affix=True)
        time_now = language.time(now, short=0, dow=False, seconds=True, tz=True, uid=ctx.author.id)
        time_then = language.time(then, short=0, dow=False, seconds=True, tz=True, uid=ctx.author.id)
        return await ctx.send(language.string("util_timediff", now=time_now, delta=difference, then=time_then))

    @commands.command(name="timein")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def time_in(self, ctx: commands.Context, time_period: str, time_class: str = "Kargadia"):
        """ Check what time it'll be in a specified period """
        return await self.time_diff(ctx, time_period, 1, time_class)

    @commands.command(name="timeago")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def time_ago(self, ctx: commands.Context, time_period: str, time_class: str = "Kargadia"):
        """ Check what time it was a specified period ago """
        return await self.time_diff(ctx, time_period, -1, time_class)

    @commands.command(name="times", aliases=["time2", "timeconvert", "convert"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def time_convert(self, ctx: commands.Context, _time_class1: str = "Earth", _time_class2: str = "Kargadia", _date: str = None, _time: str = None):
        """ Convert times between different calendars

        Example: `..times Kargadia Earth 2152-08-11 12:00:00` would output 10 August 2022 18:59:58
        Leave the command empty to convert to the current time on Kargadia
        Only specify the two calendars if you want to see the current time in a specific time class """
        language = ctx.language2("en")
        try:
            time_class1 = getattr(time2, _time_class1)
        except AttributeError:
            return await ctx.send("Time class 1 not found")
        else:
            if not issubclass(time_class1, time2.Earth):
                return await ctx.send("Invalid time class 1 specified")

        try:
            time_class2 = getattr(time2, _time_class2)
        except AttributeError:
            return await ctx.send("Time class 2 not found")
        else:
            if not issubclass(time_class2, time2.Earth):
                return await ctx.send("Invalid time class 2 specified")

        if not _date:
            date1 = time2.datetime.now(time2.timezone.utc, time_class1)
        else:
            try:
                if not _time:
                    time_part = time2.time()  # 0:00:00
                else:
                    _h, _m, *_s = _time.split(":")
                    h, m, s = int(_h), int(_m), int(_s[0]) if _s else 0
                    time_part = time2.time(h, m, s, 0, time2.utc)
                _y, _m, _d = _date.split("-")
                y, m, d = int(_y), int(_m), int(_d)
                date_part = time2.date(y, m, d, time_class1)
                date1 = time2.datetime.combine(date_part, time_part, time2.utc)
                date1b = date1.as_timezone(self.bot.timezone(ctx.author.id, _time_class1))
                date1.replace_self(tz=date1b.tzinfo)
                # date1 = time2.datetime.combine(date_part, time_part, language.get_timezone(ctx.author.id, _time_class1)).to_timezone(time2.timezone.utc)
            except ValueError:
                return await ctx.send("Failed to convert date. Make sure it is in the format `YYYY-MM-DD hh:mm:ss` (time part optional)")
        date2 = date1.convert_time_class(time_class2, False)
        out1 = language.time(date1, short=0, dow=True, seconds=True, tz=True, uid=ctx.author.id)
        out2 = language.time(date2, short=0, dow=True, seconds=True, tz=True, uid=ctx.author.id)
        return await ctx.send(f"{_time_class1}: **{out1}**\n{_time_class2}: **{out2}**")


async def setup(bot: bot_data.Bot):
    if bot.name == "suager":
        await bot.add_cog(UtilitySuager(bot))
    elif bot.name == "kyomi":
        await bot.add_cog(Reminders(bot))
    elif bot.name == "cobble":
        await bot.add_cog(UtilityCobble(bot))
    else:
        await bot.add_cog(Utility(bot))
