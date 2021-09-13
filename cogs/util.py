import json
import random
import re
from datetime import datetime, timedelta, timezone
from io import BytesIO

import discord
import pytz
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

from utils import arg_parser, bases, bot_data, emotes, general, http, permissions, time, times


def custom_role_enabled(ctx):
    return ctx.guild is not None and ctx.guild.id in [568148147457490954, 430945139142426634, 738425418637639775, 784357864482537473, 759095477979054081]


async def time_diff(ctx: commands.Context, string: str, multiplier: int):
    language = ctx.bot.language(ctx)
    try:
        delta = time.interpret_time(string) * multiplier
        then, errors = time.add_time(delta)
        if errors:
            return await general.send(language.string("util_timediff_error", then), ctx.channel)
            # return await general.send(f"Error converting time difference: {then}", ctx.channel)
    except (ValueError, OverflowError) as e:
        return await general.send(language.string("util_timediff_error", f"{type(e).__name__}: {str(e)}"), ctx.channel)
    difference = language.delta_rd(delta, accuracy=7, brief=False, affix=True)
    time_now = language.time(time.now(None), short=0, dow=False, seconds=True, tz=False)
    time_then = language.time(then, short=0, dow=False, seconds=True, tz=False)
    return await general.send(language.string("util_timediff", time_now, difference, time_then), ctx.channel)
    # return await general.send(f"Current time: **{time_now}**\nDifference: **{difference}**\nOutput time: **{time_then}**", ctx.channel)


class Utility(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.command(name="time")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def current_time(self, ctx: commands.Context):
        """ Current time """
        language = self.bot.language(ctx)
        send = ""
        # if language.language in ["kargadian_west", "tebarian"]:
        #     a = times.time_kargadia(time.now(None)).str(dow=True, era=False, month=False)
        #     b = language.time(time.now(None), short=0, dow=True, seconds=True, tz=False)
        #     d = language.time(time.now_k(), short=0, dow=True, seconds=True, tz=False)
        #     send += f"Zymlä: **{b}**\n" \
        #             f"S. Laikadu: **{d}**\n" \
        #             f"Kargadia: **{a}**"
        # else:
        send += language.string("util_time_bot", language.time(time.now(self.bot.local_config["timezone"]), short=0, dow=True, seconds=True, tz=False))
        send += f"UTC/GMT: **{language.time(time.now(None), short=0, dow=True, seconds=True, tz=False)}**"
        if ctx.guild is not None and ctx.guild.id in [568148147457490954, 738425418637639775]:
            send += f"\nSenko Lair: **{language.time(time.now_sl(), short=0, dow=True, seconds=True, tz=False)}**"  # \n" \
            # f"Senko Lair Time (NE): **{langs.gts(time.now_k(), locale, True, False, False, True, False)}**"
        data = self.bot.db.fetchrow("SELECT * FROM timezones WHERE uid=?", (ctx.author.id,))
        if data:
            send += language.string("util_time_custom", language.time(time.set_tz(time.now(None), data['tz']), short=0, dow=True, seconds=True, tz=False))
            # send += f"\nYour time: **{langs.gts(time.set_tz(time.now(None), data['tz']), locale, True, False, True, True, False)}**"
        return await general.send(send, ctx.channel)

    @commands.command(name="base", aliases=["bases", "bc"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def base_conversions(self, ctx: commands.Context, number: str, conversion: str, base: int, caps: bool = False):
        """ Convert numbers between bases

        Use "to" to convert decimal (base-10) to a base
        Use "from" to convert from the base to decimal (base-10)
        Caps argument is optional (use True if you want output to look like "1AA" instead of "1aa") and is ignored for conversions to decimal."""
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
    async def set_timezone(self, ctx: commands.Context, tz: str = None):
        """ Set your timezone """
        language = self.bot.language(ctx)
        if tz is None:
            self.bot.db.execute("DELETE FROM timezones WHERE uid=?", (ctx.author.id,))
            return await general.send(language.string("util_time_tz_reset"), ctx.channel)
        try:
            data = self.bot.db.fetchrow("SELECT * FROM timezones WHERE uid=?", (ctx.author.id,))
            _tz = pytz.timezone(tz)
            if data:
                self.bot.db.execute("UPDATE timezones SET tz=? WHERE uid=?", (tz, ctx.author.id))
            else:
                self.bot.db.execute("INSERT INTO timezones VALUES (?, ?)", (ctx.author.id, tz))
            return await general.send(language.string("util_time_tz", _tz), ctx.channel)
            # return await general.send(f"Your timezone has been set to {_tz}", ctx.channel)
        except pytz.exceptions.UnknownTimeZoneError:
            file = discord.File(BytesIO("\n".join(pytz.all_timezones).encode("utf-8")), filename="timezones.txt")
            return await general.send(language.string("util_time_tz_error", tz), ctx.channel, file=file)
            # return await general.send(f"Timezone `{tz}` was not found. Attached is the list of all pytz timezones", ctx.channel, file=file)

    @commands.command(name="timesince", aliases=["timeuntil"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def time_since(self, ctx: commands.Context, year: int = None, month: int = 1, day: int = 1, hour: int = 0, minute: int = 0, second: int = 0):
        """ Time difference
        If you don't specify any time, it will simply default to an arbitrary date within the near future"""
        language = self.bot.language(ctx)
        # if locale in ["rsl-1d", "rsl-5"]:
        #     if year is not None and year < 277:
        #         return await general.send(f"In RSL-1d and RSL-5 locales, this command breaks with dates before **1 January 277 AD**.", ctx.channel)
        try:
            now = time.now(None)
            date = datetime(now.year, 1, 1)
            if year is None:
                def dt(_month, _day):
                    return datetime(now.year, _month, _day, tzinfo=timezone.utc)
                dates = [dt(1, 3), dt(1, 27), dt(3, 17), dt(4, 1), dt(4, 11), dt(4, 17), dt(5, 13), dt(6, 20), dt(6, 25), dt(7, 27),
                         dt(8, 8), dt(9, 27), dt(10, 3), dt(10, 22), dt(10, 31), dt(11, 19), dt(12, 5), dt(12, 25),
                         datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)]
                for _date in dates:
                    if now < _date:
                        date = _date
                        break
            else:
                date = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
            difference = language.delta_dt(date, accuracy=7, brief=False, affix=True)  # time.human_timedelta(date, accuracy=7)
            current_time = language.time(now, short=0, dow=False, seconds=True, tz=False)  # time.time_output(now, True, True, True)
            specified_time = language.time(date, short=0, dow=False, seconds=True, tz=False)  # time.time_output(date, True, True, True)
            return await general.send(language.string("util_timesince", current_time, specified_time, difference), ctx.channel)
        except Exception as e:
            return await general.send(language.string("util_timesince_error", type(e).__name__, str(e)), ctx.channel)

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
        language = self.bot.language(ctx)
        lang = "en" if language.data("_conlang") is not False else language.string("_short")
        a = await general.send(f"{emotes.Loading} Loading weather for {place}...", ctx.channel)
        try:
            token = self.bot.config["weather_api_token"]
            bio = await http.get(f"http://api.openweathermap.org/data/2.5/weather?appid={token}&lang={lang}&q={place}", res_method="read")
            await a.delete()
            data = json.loads(str(bio.decode('utf-8')))
            code = data['cod']
            if code == 200:
                embed = discord.Embed(colour=random.randint(0, 0xffffff))
                try:
                    country = data['sys']['country'].lower()
                except KeyError:
                    country = ""
                try:
                    tz = data['timezone']
                except KeyError:
                    tz = 0
                # _time_locale = locale if locale not in ["rsl-1d", "rsl-5"] else "english"
                # local_time = languages.gts(time.now(None) + timedelta(seconds=tz), _time_locale)
                local_time = language.time(time.now(None) + timedelta(seconds=tz), short=1, dow=False, seconds=False, tz=False)
                if country:
                    country_name = language.string(f"z_data_country_{country}")
                    emote = f":flag_{country}: "
                else:
                    country_name = "Not a country"
                    emote = ""
                embed.title = language.string("util_weather_title", data['name'], country_name, emote=emote)
                embed.description = language.string("util_weather_desc", local_time)
                weather_icon = data['weather'][0]['icon']
                embed.set_thumbnail(url=f"http://openweathermap.org/img/wn/{weather_icon}@2x.png")
                embed.add_field(name=language.string("util_weather_weather"), value=data['weather'][0]['description'].capitalize(), inline=False)
                _tk = data['main']['temp']
                _tc = _tk - 273.15
                _tf = _tc * 1.8 + 32
                tk, tc, tf = language.number(_tk, precision=1), language.number(_tc, precision=1), language.number(_tf, precision=1)
                embed.add_field(name=language.string("util_weather_temperature"), value=f"**{tc}°C** | {tk} K | {tf}°F", inline=False)
                try:
                    _tk = data['main']['feels_like']
                    _tc = _tk - 273.15
                    _tf = _tc * 1.8 + 32
                    tk, tc, tf = language.number(_tk, precision=1), language.number(_tc, precision=1), language.number(_tf, precision=1)
                    embed.add_field(name=language.string("util_weather_temperature2"), value=f"**{tc}°C** | {tk} K | {tf}°F", inline=False)
                except KeyError:
                    pass
                try:
                    pressure = data['main']['grnd_level']
                except KeyError:
                    pressure = data['main']['pressure']
                embed.add_field(name=language.string("util_weather_pressure"), value=f"{language.number(pressure)} hPa", inline=False)
                embed.add_field(name=language.string("util_weather_humidity"), value=language.number(data['main']['humidity'] / 100, precision=0, percentage=True), inline=False)
                _sm = data['wind']['speed']
                _sk = _sm * 3.6
                _sb = _sk / 1.609  # imperial system bad
                sm, sk, sb = language.number(_sm, precision=2), language.number(_sk, precision=2), language.number(_sb, precision=2)
                embed.add_field(name=language.string("util_weather_wind"), value=language.string("util_weather_wind_data", sm, sk, sb), inline=False)
                embed.add_field(name=language.string("util_weather_clouds"), value=language.number(data['clouds']['all'] / 100, precision=0, percentage=True), inline=False)
                sr = data['sys']['sunrise']
                ss = data['sys']['sunset']
                now = time.now(None)
                now_l = now + timedelta(seconds=tz)
                if sr != 0 and ss != 0:
                    srt = time.from_ts(sr + tz, None)
                    sst = time.from_ts(ss + tz, None)
                    sr, tr = language.time2(srt, seconds=False, tz=False), language.delta_dt(srt, source=now_l, accuracy=2, brief=True, affix=True)
                    ss, ts = language.time2(sst, seconds=False, tz=False), language.delta_dt(sst, source=now_l, accuracy=2, brief=True, affix=True)
                    embed.add_field(name=language.string("util_weather_sunrise"), value=f"{sr} | {tr}", inline=False)
                    embed.add_field(name=language.string("util_weather_sunset"), value=f"{ss} | {ts}", inline=False)
                try:
                    lat, long = data['coord']['lat'], data['coord']['lon']
                    n, e = "N" if lat >= 0 else "S", "E" if long >= 0 else "W"
                    if lat < 0:
                        lat *= -1
                    if long < 0:
                        long *= -1
                    embed.add_field(name=language.string("util_weather_location"), value=f"{language.number(lat)}°{n}, {language.number(long)}°{e}", inline=False)
                except KeyError:
                    pass
                embed.timestamp = now
            else:
                return await general.send(language.string("util_weather_error", place, code, data["message"]), ctx.channel)
        except Exception as e:
            return await general.send(language.string("util_weather_error", place, type(e).__name__, str(e)), ctx.channel)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="colour", aliases=["color"])
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def colour(self, ctx: commands.Context, colour: str = "random"):
        """ Information on a colour """
        language = self.bot.language(ctx)
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
                    return await general.send(language.string("images_colour_invalid_value"), ctx.channel)
                _colour = f"{int(colour, 16):06x}"
            except Exception as e:
                return await general.send(language.string("images_colour_invalid", type(e).__name__, str(e)), ctx.channel)
        hex_6 = _colour[:6]
        int_6 = int(_colour[:6], 16)
        embed = discord.Embed(colour=int_6, base=16)
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
            font = ImageFont.truetype("assets/font.ttf", size=font_size)
        except ImportError:
            await general.send(f"{emotes.Deny} It seems that image generation does not work properly here...", ctx.channel)
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
            width2a, height2a = draw2a.textsize(hex2a, font)
            width2b, height2b = draw2b.textsize(hex2b, font)
            sum2a = (red2a + green2a + blue2a) // 3
            sum2b = (red2b + green2b + blue2b) // 3
            fill2a = (0, 0, 0, 255) if sum2a >= 128 or green2a >= 224 else (255, 255, 255, 255)
            fill2b = (0, 0, 0, 255) if sum2b >= 128 or green2b >= 224 else (255, 255, 255, 255)
            draw2a.text(((size - width2a) // 2, size - height2a - 5), hex2a, fill=fill2a, font=font)
            draw2b.text(((size - width2b) // 2, size - height2b - 5), hex2b, fill=fill2b, font=font)
            image2.paste(image2a, start2a)
            image2.paste(image2b, start2b)
        bio2 = BytesIO()
        image2.save(bio2, "PNG")
        bio2.seek(0)
        embed.set_image(url="attachment://gradient.png")
        return await general.send(None, ctx.channel, embed=embed, files=[discord.File(bio1, "colour.png"), discord.File(bio2, "gradient.png")])

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
        return await general.send(language.string("fun_roll", ctx.author.name, n1, n2, no), ctx.channel)

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
        language = self.bot.language(ctx)
        try:
            await ctx.message.delete()
        except Exception as e:
            await general.send(language.string("fun_say_delete_fail", type(e).__name__, str(e)), ctx.channel, delete_after=5)
        if channel.guild != ctx.guild:
            return await general.send(language.string("fun_tell_guilds"), ctx.channel)
        try:
            await general.send(message, channel, u=True, r=True)
        except Exception as e:
            return await general.send(language.string("fun_tell_fail", type(e).__name__, str(e)), ctx.channel)
        return await general.send(language.string("fun_tell_success", channel.mention), ctx.channel, delete_after=5)

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

    # @commands.command(name="say")
    # @commands.check(lambda ctx: not (ctx.author.id == 667187968145883146 and ctx.guild.id == 568148147457490954))
    # @commands.guild_only()
    # @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    # async def say(self, ctx: commands.Context, *, message: str):
    #     """ Make me speak! """
    #     language = self.bot.language(ctx)
    #     try:
    #         await ctx.message.delete()
    #     except Exception as e:
    #         await general.send(language.string("fun_say_delete_fail", type(e).__name__, str(e)), ctx.channel, delete_after=5)
    #     await general.send(f"**{ctx.author}:**\n{message}", ctx.channel)
    #     return await general.send(language.string("fun_say_success"), ctx.channel, delete_after=5)

    @commands.command(name="vote", aliases=["petition"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def vote(self, ctx: commands.Context, *, question: str):
        """ Start a vote """
        language = self.bot.language(ctx)
        if self.bot.name == "suager":
            if re.compile(r"^(\d{4}) (yes|neutral|no)$").search(question):  # If the vote question is something like "1337 yes" - checks if someone is trying to vote for a poll
                if ctx.guild is not None and ctx.guild.id == 869975256566210641:
                    await general.send(language.string("fun_vote_poll_question2", ctx.prefix, question), ctx.channel)
                else:
                    await general.send(language.string("fun_vote_poll_question", ctx.prefix, question), ctx.channel)
        message = await general.send(language.string("fun_vote", ctx.author.name, language.string(f"fun_vote_{str(ctx.invoked_with).lower()}"), question), ctx.channel)
        await message.add_reaction(emotes.Allow)
        await message.add_reaction(emotes.Meh)
        await message.add_reaction(emotes.Deny)

    @commands.command(name="avatar", aliases=["av"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def avatar(self, ctx: commands.Context, *, who: discord.User = None):
        """ Get someone's avatar """
        user = who or ctx.author
        return await general.send(self.bot.language(ctx).string("discord_avatar", user.name, user.avatar_url_as(size=1024, static_format='png')), ctx.channel)

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
            language = self.bot.language(ctx)
            if role is None:
                all_roles = ""
                for num, role in enumerate(sorted(ctx.guild.roles, reverse=True), start=1):
                    all_roles += language.string("discord_role_list_item", f"{num:02d}", language.number(len(role.members)), role=role)
                data = BytesIO(all_roles.encode('utf-8'))
                return await general.send(language.string("discord_role_list", ctx.guild.name), ctx.channel, file=discord.File(data, filename=f"{time.file_ts('Roles')}"))
            else:
                embed = discord.Embed(colour=role.colour)
                embed.title = language.string("discord_role_about", role.name)
                embed.set_thumbnail(url=ctx.guild.icon_url_as(size=1024))
                embed.add_field(name=language.string("discord_role_name"), value=role.name, inline=True)
                embed.add_field(name=language.string("discord_role_id"), value=str(role.id), inline=True)
                embed.add_field(name=language.string("generic_members"), value=language.number(len(role.members)), inline=True)
                embed.add_field(name=language.string("discord_role_colour"), value=str(role.colour), inline=True)
                embed.add_field(name=language.string("discord_role_mentionable"), value=language.yes(role.mentionable), inline=True)
                embed.add_field(name=language.string("discord_role_hoisted"), value=language.yes(role.hoist), inline=True)
                embed.add_field(name=language.string("discord_role_position"), value=language.number(role.position), inline=True)
                embed.add_field(name=language.string("generic_created_at"), value=language.time(role.created_at, short=0, dow=False, seconds=False, tz=False), inline=True)
                embed.add_field(name=language.string("discord_role_default"), value=language.yes(role.is_default()), inline=True)
                return await general.send(None, ctx.channel, embed=embed)

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
        send = language.string("discord_role_members", ctx.guild.name)
        if rl > 1900:
            async with ctx.typing():
                data = BytesIO(str(m).encode('utf-8'))
                return await general.send(send, ctx.channel, file=discord.File(data, filename=f"{time.file_ts('Role_Members')}"))
        return await general.send(f"{send}\n```ini\n{m}```", ctx.channel)

    @commands.command(name="joinedat", aliases=["joindate", "jointime"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def joined_at(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Check when someone joined server """
        user = who or ctx.author
        language = self.bot.language(ctx)
        return await general.send(language.string("discord_joined_at", user, ctx.guild.name, language.time(user.joined_at, short=0, dow=False, seconds=False, tz=False)), ctx.channel)

    @commands.command(name="createdat")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def created_at(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check when someone created their account """
        user = who or ctx.author
        language = self.bot.language(ctx)
        return await general.send(language.string("discord_created_at", user, language.time(user.created_at, short=0, dow=False, seconds=False, tz=False)), ctx.channel)

    @commands.command(name="user")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def user(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Get info about user """
        user = who or ctx.author
        language = self.bot.language(ctx)
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("discord_user_about", user.name)
        embed.set_thumbnail(url=user.avatar_url_as(size=1024))
        embed.add_field(name=language.string("discord_user_username"), value=user, inline=True)
        embed.add_field(name=language.string("discord_user_nickname"), value=user.nick, inline=True)
        embed.add_field(name=language.string("discord_user_id"), value=user.id, inline=True)
        embed.add_field(name=language.string("generic_created_at"), value=language.time(user.created_at, short=0, dow=False, seconds=False, tz=False), inline=False)
        embed.add_field(name=language.string("discord_user_joined_at"), value=language.time(user.joined_at, short=0, dow=False, seconds=False, tz=False), inline=False)
        if len(user.roles) < 15:
            r = user.roles
            r.sort(key=lambda x: x.position, reverse=True)
            ar = [f"<@&{x.id}>" for x in r if x.id != ctx.guild.default_role.id]
            roles = ', '.join(ar) if ar else language.string("generic_none")
            b = len(user.roles) - 1
            roles += language.string("discord_user_roles_overall", language.number(b))
        else:
            roles = language.string("discord_user_roles_many", language.number(len(user.roles) - 1))
        embed.add_field(name=language.string("discord_user_roles"), value=roles, inline=False)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="whois")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def who_is(self, ctx: commands.Context, *, user_id: int):
        """ Get info about a user """
        language = self.bot.language(ctx)
        try:
            user = await self.bot.fetch_user(user_id)
        except discord.NotFound as e:
            return await general.send(language.string("events_err_error", "NotFound", str(e)), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("discord_user_about", user.name)
        embed.set_thumbnail(url=str(user.avatar_url_as(size=1024)))
        embed.add_field(name=language.string("discord_user_username"), value=str(user), inline=True)
        embed.add_field(name=language.string("discord_user_id"), value=str(user.id), inline=True)
        embed.add_field(name=language.string("generic_created_at"), value=language.time(user.created_at, short=0, dow=False, seconds=False, tz=False), inline=True)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="emoji", aliases=["emote"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def emoji(self, ctx: commands.Context, emoji: discord.Emoji):
        """ Information on an emoji """
        language = self.bot.language(ctx)
        e = str(ctx.invoked_with)
        c = language.string(f"discord_emoji_{e}")
        embed = discord.Embed(colour=general.random_colour())
        embed.description = language.string("discord_emoji", c, emoji.name, emoji.id, language.yes(emoji.animated), emoji.guild.id,
                                            language.time(emoji.created_at, short=0, dow=False, seconds=False, tz=False), emoji.url)
        embed.set_image(url=emoji.url)
        return await general.send(f"{ctx.author.name}:", ctx.channel, embed=embed)

    @commands.group(name="server", aliases=["guild"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def server(self, ctx: commands.Context):
        """ Information about the current server """
        if ctx.invoked_subcommand is None:
            language = self.bot.language(ctx)
            bots = sum(1 for member in ctx.guild.members if member.bot)
            bots_amt = bots / ctx.guild.member_count
            embed = discord.Embed(colour=general.random_colour())
            embed.set_thumbnail(url=ctx.guild.icon_url_as(size=1024))
            embed.title = language.string("discord_server_about", ctx.guild.name)
            embed.add_field(name=language.string("discord_server_name"), value=ctx.guild.name, inline=True)
            embed.add_field(name=language.string("discord_server_id"), value=ctx.guild.id, inline=True)
            embed.add_field(name=language.string("discord_server_owner"), inline=True, value=f"{ctx.guild.owner}\n({ctx.guild.owner.display_name})")
            embed.add_field(name=language.string("generic_members"), value=language.number(ctx.guild.member_count), inline=True)
            embed.add_field(name=language.string("discord_server_bots"), value=f"{language.number(bots)} ({language.number(bots_amt, percentage=True)})", inline=True)
            embed.add_field(name=language.string("discord_server_region"), value=ctx.guild.region, inline=True)
            embed.add_field(name=language.string("discord_server_roles"), value=language.number(len(ctx.guild.roles)), inline=True)
            try:
                embed.add_field(name=language.string("discord_server_bans"), value=language.number(len(await ctx.guild.bans())), inline=True)
            except discord.Forbidden:
                pass  # Just don't show the field at all if it can't be accessed
                # embed.add_field(name=languages.gls("discord_server_bans", locale), value=languages.gls("discord_server_bans_denied", locale), inline=True)
            embed.add_field(name=language.string("discord_server_verification"), inline=True, value=str(ctx.guild.verification_level).capitalize())
            t, c, v = len(ctx.guild.text_channels), len(ctx.guild.categories), len(ctx.guild.voice_channels)
            tc, cc, vc = language.number(t), language.number(c), language.number(v)
            embed.add_field(name=language.string("discord_server_channels"), value=language.string("discord_server_channels_data", tc, cc, vc), inline=True)
            b, bl, bc = language.number(ctx.guild.premium_subscription_count), language.number(ctx.guild.premium_tier), language.number(len(ctx.guild.premium_subscribers))
            embed.add_field(name=language.string("discord_server_boosts"), value=language.string("discord_server_boosts_data", b, bl, bc), inline=True)
            ani = len([emote for emote in ctx.guild.emojis if emote.animated])
            total_emotes = len(ctx.guild.emojis)
            el = ctx.guild.emoji_limit
            na = total_emotes - ani
            n, a, e, t = language.number(na), language.number(ani), language.number(el), language.number(total_emotes)
            embed.add_field(name=language.string("discord_server_emotes"), value=language.string("discord_server_emotes_data", n, a, e, t), inline=True)
            ca = ctx.guild.created_at
            ct, cd = language.time(ca, short=0, dow=False, seconds=False, tz=False), language.delta_dt(ca, accuracy=3, brief=False, affix=True)
            embed.add_field(name=language.string("generic_created_at"), value=f"{ct}\n{cd}", inline=False)
            return await general.send(None, ctx.channel, embed=embed)

    @server.command(name="icon", aliases=["avatar"])
    async def server_icon(self, ctx: commands.Context):
        """ Get server icon """
        return await general.send(self.bot.language(ctx).string("discord_server_icon", ctx.guild.name, ctx.guild.icon_url_as(size=1024, static_format='png')), ctx.channel)

    @server.command(name="banner")
    async def server_banner(self, ctx: commands.Context):
        """ Get server banner """
        link = ctx.guild.banner_url_as(size=4096, format="png")
        language = self.bot.language(ctx)
        if link:
            return await general.send(language.string("discord_server_banner", ctx.guild.name, link), ctx.channel)
        else:
            return await general.send(language.string("discord_server_banner_none", ctx.guild.name), ctx.channel)

    @server.command(name="invitebg", aliases=["invite", "splash"])
    async def server_invite(self, ctx: commands.Context):
        """ Get server invite splash """
        link = ctx.guild.splash_url_as(size=4096, format="png")
        language = self.bot.language(ctx)
        if link:
            return await general.send(language.string("discord_server_inv_bg", ctx.guild.name, link), ctx.channel)
        else:
            return await general.send(language.string("discord_server_inv_bg_none", ctx.guild.name), ctx.channel)

    @server.command(name="bots")
    async def server_bots(self, ctx: commands.Context):
        """ Bots in the server """
        bots = [a for a in ctx.guild.members if a.bot]
        language = self.bot.language(ctx)
        m = ''
        for i in range(len(bots)):
            m += f"[{i + 1:02d}] {bots[i]}\n"
        rl = len(m)
        send = language.string("discord_server_bots_data", ctx.guild.name)
        if rl > 1900:
            async with ctx.typing():
                data = BytesIO(str(m).encode('utf-8'))
                return await general.send(send, ctx.channel, file=discord.File(data, filename=f"{time.file_ts('Bots')}"))
        return await general.send(f"{send}\n```ini\n{m}```", ctx.channel)

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
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)

        args, valid_check = parser.parse_args(args)
        if not valid_check:
            return await general.send(args, ctx.channel)
        if self.bot.name == "kyomi":
            if args.author:
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        if args.title:
            embed.title = " ".join(args.title).replace("\\n", "\n")
            if len(embed.title) > 256:
                return await general.send("Embed title cannot be longer than 256 characters. Blame discord.", ctx.channel)
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
                    return await general.send(f"Invalid colour - {type(e).__name__}: {e}", ctx.channel)
            else:
                return await general.send("Colour must be either 3 or 6 HEX digits long.", ctx.channel)
            embed.colour = col
        return await general.send(None, ctx.channel, embed=embed)


class Reminders(Utility, name="Utility"):
    @commands.command(name="remind", aliases=["remindme"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def remind_me(self, ctx: commands.Context, duration: str, *, reminder: str):
        """ Set yourself a reminder.

        Example: //remind 2d12h Insert something interesting here"""
        language = self.bot.language(ctx)
        delta = time.interpret_time(duration)
        if time.rd_is_above_5y(delta):
            return await general.send(language.string("util_reminders_limit"), ctx.channel)
            # return await general.send("You can't specify a time range above 5 years.", ctx.channel)
        expiry, error = time.add_time(delta)
        if error:
            return await general.send(language.string("util_reminders_error"), ctx.channel)
            # return await general.send(f"Failed to convert duration: {expiry}", ctx.channel)
        diff = language.delta_rd(delta, accuracy=7, brief=False, affix=True)
        when = language.time(expiry, short=1, dow=False, seconds=True, tz=False)
        random_id = general.random_id()
        while self.bot.db.fetch("SELECT entry_id FROM temporary WHERE entry_id=?", (random_id,)):
            random_id = general.random_id()
        self.bot.db.execute("INSERT INTO temporary VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (ctx.author.id, "reminder", expiry, None, reminder, random_id, False, self.bot.name))
        return await general.send(language.string("util_reminders_success", ctx.author.name, diff, when), ctx.channel)
        # return await general.send(f"Okay **{ctx.author.name}**, I will remind you about this **{diff}** ({when} UTC)", ctx.channel)

    @commands.group(name="reminders")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def reminders(self, ctx: commands.Context):
        """ See a list of your currently active reminders, and modify them """
        if ctx.invoked_subcommand is None:
            language = self.bot.language(ctx)
            reminders = self.bot.db.fetch("SELECT * FROM temporary WHERE uid=? AND type='reminder' AND bot=? ORDER BY expiry", (ctx.author.id, self.bot.name))
            if not reminders:
                return await general.send(language.string("util_reminders_none", ctx.author.name), ctx.channel)
                # return await general.send(f"You have no reminders active at the moment, {ctx.author.name}.", ctx.channel)
            output = language.string("util_reminders_list", ctx.author)
            # output = f"**{ctx.author}**, here is the list of your currently active reminders"
            outputs = []
            _reminder = 0
            for reminder in reminders:
                _reminder += 1
                expiry = reminder["expiry"]
                expires_on = language.time(expiry, short=1, dow=False, seconds=True, tz=False)
                expires_in = language.delta_dt(expiry, accuracy=3, brief=False, affix=True)
                outputs.append(language.string("util_reminders_item", _reminder, reminder["message"], reminder["entry_id"], expires_on, expires_in))
                # outputs.append(f"**{_reminder})** {reminder['message']}\nActive for {expires_on}\nReminds {expires_in}")
            output2 = "\n\n".join(outputs)
            try:
                try:  # Try to tell the user to check DMs
                    if permissions.can_react(ctx):
                        await ctx.message.add_reaction(chr(0x2709))
                except discord.Forbidden:
                    pass
                if len(output2) > 1900:
                    _data = BytesIO(str(output2).encode('utf-8'))
                    return await ctx.author.send(output, file=discord.File(_data, filename=f"{time.file_ts('Reminders')}"))
                else:
                    return await ctx.author.send(f"{output}\n\n{output2}")
            except discord.Forbidden:
                return await general.send(language.string("util_reminders_dms"), ctx.channel)
                # return await general.send("You need to have your DMs open for me to be able to send you the list of your reminders.", ctx.channel)

    @reminders.command(name="edit")
    async def reminders_edit(self, ctx: commands.Context, reminder_id: int, *, args: str):
        """ Edit a reminder
        -m/--message/--text: Edit the reminder's text
        -t/--time/--expiry: Edit when you want to be reminded (Format: `YYYY-MM-DD hh:mm:ss`)
        Time part optional, and may be just `hh:mm`. Time must be in 24-hour format.

        Example: //reminders edit 1048576 --time 2021-06-08 17:00:00 --message Insert something interesting here"""
        language = self.bot.language(ctx)
        reminder = self.bot.db.fetchrow("SELECT * FROM temporary WHERE entry_id=? AND uid=? AND type='reminder'", (reminder_id, ctx.author.id))
        if not reminder:
            return await general.send(language.string("util_reminders_edit_none", reminder_id), ctx.channel)
        parser = arg_parser.Arguments()
        parser.add_argument('-m', '--message', '--text', nargs="+")
        parser.add_argument('-t', '--time', '--expiry', nargs="+")
        args, valid_check = parser.parse_args(args)
        if not valid_check:
            return await general.send(args, ctx.channel)
        message = args.message
        _message = " ".join(message) if message else reminder["message"]
        _expiry = reminder["expiry"]
        if args.time is not None:
            _datetime = args.time
            if len(_datetime) == 1:
                _date, _time = _datetime[0], "00:00:00"
            elif len(_datetime) == 2:
                _date, _time = _datetime
                _time = _time.replace(".", ":")
                c = _time.count(":")
                if c == 1:
                    _time = f"{_time}:00"
            else:
                return await general.send(language.string("util_reminders_edit_time2"), ctx.channel)
            try:
                _expiry = datetime.strptime(f"{_date} {_time}", "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return await general.send(language.string("util_reminders_edit_time"), ctx.channel)
        expiry = language.time(_expiry, short=1, dow=False, seconds=True, tz=False)
        self.bot.db.execute("UPDATE temporary SET message=?, expiry=? WHERE entry_id=?", (_message, _expiry, reminder_id))
        return await general.send(language.string("util_reminders_edit", reminder_id, _message, expiry), ctx.channel)

    @reminders.command(name="delete", aliases=["remove", "cancel"])
    async def reminders_delete(self, ctx: commands.Context, reminder_id: int):
        """ Delete a reminder """
        language = self.bot.language(ctx)
        reminder = self.bot.db.fetchrow("SELECT * FROM temporary WHERE entry_id=? AND uid=? AND type='reminder'", (reminder_id, ctx.author.id))
        if not reminder:
            return await general.send(language.string("util_reminders_edit_none", reminder_id), ctx.channel)
        self.bot.db.execute("DELETE FROM temporary WHERE entry_id=? AND uid=?", (reminder_id, ctx.author.id))
        return await general.send(language.string("util_reminders_delete", reminder_id), ctx.channel)


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
                if c.startswith("#"):
                    c = c[1:]
                    a = len(c)
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
    @permissions.has_permissions(administrator=True)
    async def grant_custom_role(self, ctx: commands.Context, user: discord.Member, role: discord.Role):
        """ Grant custom role """
        already = self.bot.db.fetchrow("SELECT * FROM custom_role WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not already:
            self.bot.db.execute("INSERT INTO custom_role VALUES (?, ?, ?)", (user.id, role.id, ctx.guild.id))
            try:
                await user.add_roles(role, reason="Custom Role grant")
                return await general.send(f"Granted {role.name} to {user.name}", ctx.channel)
            except discord.Forbidden:
                return await general.send(f"{role.name} could not be granted to {user.name}. It has, however, been saved to the database.", ctx.channel)
        else:
            self.bot.db.execute("UPDATE custom_role SET rid=? WHERE uid=? AND gid=?", (role.id, user.id, ctx.guild.id))
            return await general.send(f"Updated custom role of {user.name} to {role.name}", ctx.channel)


class UtilityCobble(Utility, name="Utility"):
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


def setup(bot: bot_data.Bot):
    if bot.name == "suager":
        bot.add_cog(UtilitySuager(bot))
    elif bot.name == "kyomi":
        bot.add_cog(Reminders(bot))
    elif bot.name == "cobble":
        bot.add_cog(UtilityCobble(bot))
    else:
        bot.add_cog(Utility(bot))
