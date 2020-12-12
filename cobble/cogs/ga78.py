import os
from datetime import datetime, timezone

import discord
import pyttsx3
from discord.ext import commands

from cobble.utils import ss23, ss24
from core.utils import emotes, general, time


def rsl_number(value: int):
    """ Convert number to RSL-1 """
    limit = int("9" * 36)
    if value > limit:
        return f"Highest allowed number is {limit:,} (1e36 - 1)"
    if value < 0:
        return f"Negative values will not work"
    if value == 0:
        return "deneda"
    one = {0: "", 1: "ukka", 2: "devi", 3: "tei", 4: "sei", 5: "paa", 6: "senki", 7: "ei", 8: "oni", 9: "zehi"}
    teen = {11: "uveri", 12: "deveri", 13: "teveri", 14: "severi", 15: "paveri", 16: "seneri", 17: "eijeri", 18: "overi", 19: "zegheri"}
    ten = {1: "verri", 2: "devveire", 3: "tevveire", 4: "sevveire", 5: "pavveire", 6: "senneire", 7: "evveire", 8: "onneire", 9: "zegheire"}
    hundred = ["arraiki", "arraikädan"]
    exp_1000 = ["kirraa", "kirraadan"]
    exp = ["ugaristu", "devaristu", "tevaristu", "sekaristu", "pakkaristu", "sennaristu", "eijaristu", "onaristu", "zeharistu", "verraristu"]

    def thousand(_val: int):
        _999 = _val % 1000
        _99 = _999 % 100
        _99v = ""
        if _99 < 10:
            _99v = one[_99]
        elif 11 <= _99 < 20:
            _99v = teen[_99]
        else:
            _v, _u = divmod(_99, 10)
            _99v = f"{one[_u]} u {ten[_v]}" if _u > 0 else ten[_v]
        _100 = _999 // 100
        _100v = "" if _100 == 0 else ((f"{one[1]} {hundred[0]}" if _100 == 1 else f"{one[_100]} {hundred[1]}") + (", " if _99 != 0 else ""))
        return _100v + _99v
    _1000 = value % 1000
    outputs = [thousand(_1000)] if _1000 > 0 else []
    large = []
    _value = value
    _range = len(exp)
    for i in range(_range):
        _value //= 1000
        large.append(_value % 1000)
    for i in range(_range):
        val = large[i]
        if val > 0:
            n1, n2 = exp_1000 if i == 0 else ((_name := exp[i - 1]), _name[:-1] + "azan")
            name = n1 if val % 100 == 1 else n2
            outputs.append(f"{thousand(val)}{'r' if val == 1 and i > 0 else ''} {name}")
    return ", ".join(outputs[::-1])


class GA78(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            self.tts = pyttsx3.init()
        except Exception as _:
            del _
            self.tts = None

    @commands.command(name="time23")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def time23(self, ctx: commands.Context, year: int = None, month: int = 1, day: int = 1, hour: int = 0, minute: int = 0, second: int = 0):
        """ Compare times from Earth with SS23 """
        if year is None:
            dt = time.now(None)
        else:
            if year < 1687:
                return await general.send(f"{emotes.Deny} This command does not work with dates before **1 January 1687 AD**.", ctx.channel)
            if year >= 8200:
                return await general.send(f"{emotes.Deny} This command does not work with dates after **31 December 8199 AD, 23:59:59 UTC**", ctx.channel)
            try:
                dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
            except ValueError as e:
                return await general.send(f"{emotes.Deny} {type(e).__name__}: {e}", ctx.channel)
        ti = dt.strftime("%A, %d %B %Y, %H:%M:%S %Z")  # Time IRL
        tk = ss23.date_kargadia(dt)        # Time in Kargadia RSL-1
        tz = ss23.date_zeivela(dt)         # Time on Zeivela RSL-2
        tq = ss23.date_kaltaryna(dt)       # Time in Qevenerus/Kaltaryna RSL-1
        td = ss23.date_kargadia_5(dt)      # Time on Kargadia RSL-5
        td2 = ss23.time_earth_5(dt, True)  # Time on Earth RSL-5 DT
        months_1 = ["Seldan Masailnaran", "Nuannaran", "Seimannaran", "Veisanaran", "Eilannaran", "Havazdallarinnaran",
                    "Sanvaggannaran", "Kailaggannaran", "Semardannaran", "Addanvaran", "Halltuavaran", "Masailnaran"]
        months_5 = ["Chìlderaljanselaljan", "Anveraijanselaljan", "Síldarinselaljan", "Kûstanselaljan",
                    "Vullastenselaljan", "Khavastalgèrinselaljan", "Senkanselaljan", "Dhárelanselaljan",
                    "Silaljanselaljan", "Eijelovvanselaljan", "Haldúvaranselaljan", "Massalanselaljan"]
        tn = time.kargadia_convert(dt)
        tn1 = tn.strftime(f"%A, %d {months_1[tn.month % 12]} %Y, %H:%M:%S %Z")
        tn5 = tn.strftime(f"%A, %d {months_5[tn.month % 12]} %Y, %H:%M:%S %Z")
        return await general.send(f"Time on this Earth (English): **{ti}**\nTime on this Earth (RSL-1_kg): **{tn1}**\n"
                                  f"Time on this Earth (RSL-5 NE): **{tn5}**\nTime on this Earth (RSL-5 DT): **{td2}**\n"
                                  f"Time on 23.4 Zeivela (Local): **{tz}**\n"
                                  f"Time on 23.5 Kargadia (RSL-1_kg): **{tk}**\nTime on 23.5 Kargadia (RSL-5): **{td}**\n"
                                  f"Time on 23.6 Qevenerus (RSL-1_ka): **{tq}**", ctx.channel)

    @commands.command(name="time24")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def time24(self, ctx: commands.Context, year: int = None, month: int = 1, day: int = 1, hour: int = 0, minute: int = 0, second: int = 0):
        """ Compare times from Earth with SS24 """
        if year is None:
            dt = time.now(None)
        else:
            if year < 1743:
                return await general.send(f"{emotes.Deny} This command does not work with dates before **1 January 1743 AD**.", ctx.channel)
            try:
                dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
            except ValueError as e:
                return await general.send(f"{emotes.Deny} {type(e).__name__}: {e}", ctx.channel)
        ti = dt.strftime("%A, %d %B %Y, %H:%M:%S %Z")  # Time IRL
        t24_4_local = ss24.time_sinvimania(dt).str()   # 24.4 Sinvimania Local
        t24_5_local = ss24.time_hosvalnerus(dt).str()  # 24.5 Hosvalnerus local
        t24_11_1 = ss24.time_kuastall_11(dt).str()
        return await general.send(f"Time on this Earth (English): **{ti}**\n"
                                  f"Time on 24.4 Sinvimania (Local Solar): **{t24_4_local}**\n"
                                  f"Time on 24.5 Hosvalnerus (Local): **{t24_5_local}**\n"
                                  f"Time on 24.11 Kuastall-11 (RSL-1_ku): **{t24_11_1}**", ctx.channel)

    @commands.command(name="weather23")
    @commands.is_owner()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def weather23(self, ctx: commands.Context, *, place: str):
        """ Weather in a place in SS23 """
        try:
            weather = ss23.Weather(place.title())
            embed = discord.Embed(colour=general.random_colour())
            embed.title = f"Weather in **{weather.city}, {weather.planet}**"
            embed.description = f"Local Time: **{weather.time_out}**"
            temp_c = round(weather.temperature, 1)
            embed.add_field(name="Temperature", value=f"{temp_c}°C | **placeholder**", inline=False)
            speed_kmh = round(weather.wind_speed, 1)
            if weather.planet == "Kargadia":
                kp_base = 0.8192
                kp_hour = 37.49865756 / 32
                m_name = "ks/h (kp/c)"
            elif weather.planet == "Kaltaryna":
                kp_base = 0.8192
                kp_hour = 51.642812 / 64
                m_name = "ks/h (kp/c)"
            else:
                kp_base = 1
                kp_hour = 1
                m_name = "unknown"
            speed_kpc = round(weather.wind_speed / kp_base * kp_hour, 1)
            embed.add_field(name="Wind Speed", value=f"{speed_kmh} km/h | **{speed_kpc} {m_name}**", inline=False)
            if weather.is_raining:
                rain = "It's raining" if temp_c > 0 else "It's snowing"
            else:
                rain = "It's dry so far"
            embed.add_field(name="Precipitation", value=rain, inline=False)
            embed.timestamp = time.now(None)
            return await general.send(None, ctx.channel, embed=embed)
        except Exception as e:
            if ctx.channel.id == 610482988123422750:
                await general.send(general.traceback_maker(e), ctx.channel)
            return await general.send(f"An error occurred: `{type(e).__name__}: {e}`.\nThe place {place} may not exist.", ctx.channel)

    @commands.command(name="nlc")
    @commands.is_owner()
    async def ne_world_ll_calc(self, ctx: commands.Context, x: int, z: int, border: int = 100000):
        """ Calculate latitude, local offset of position - NEWorld """
        lat = -z / border * 90  # Latitude value
        long = x / border * 180
        tzl = 48 / 180
        tz = round(long / tzl)
        tzo = tz / tzl - long  # Local Offset
        return await general.send(f"At {x=:,} and {z=:,} (World Border at {border:,}):\nLatitude: {lat:.3f}\nLocal Offset: {tzo:.3f}", ctx.channel)

    @commands.command("rslt")
    @commands.check(lambda ctx: ctx.author.id in [302851022790066185, 236884090651934721, 291665491221807104])
    async def rsl_encode(self, ctx: commands.Context, s: int, *, t: str):
        """ Laikattart Sintuvut """
        if not (1 <= s <= 8700):
            return await general.send("De dejava idou, no sa maikazo ir te edou kihtemal. ", ctx.channel)
        shift = s * 128
        code = rsl_number(s)
        try:
            text = "".join([chr(ord(letter) + shift) for letter in t])
        except ValueError:
            return await general.send(f"Sil valse, alteknaar ka uvaar kuarhaavar qeraduar", ctx.channel)
        return await general.send(f"{code} {text}", ctx.channel)

    @commands.command("rslf")
    @commands.check(lambda ctx: ctx.author.id in [302851022790066185, 236884090651934721, 291665491221807104])
    async def rsl_decode(self, ctx: commands.Context, s: int, *, t: str):
        """ Laikattarad Sintuvuad """
        if not (1 <= s <= 8700):
            return await general.send("De dejava idou, no sa maikazo ir te edou kihtemal", ctx.channel)
        shift = s * 128
        text = ""
        for letter in t:
            try:
                a = chr(ord(letter) - shift)
            except ValueError:
                a = chr(0)
            text += a
        return await general.send(text, ctx.channel)

    @commands.command("tts")
    @commands.check(lambda ctx: ctx.author.id in [302851022790066185, 291665491221807104])
    async def tts_command(self, ctx: commands.Context, *, text: str):
        """ Text to Speech """
        if self.tts is not None:
            self.tts.save_to_file(text, "tts.mp3")
            self.tts.runAndWait()
            try:
                await general.send(None, ctx.channel, file=discord.File("tts.mp3"))
            except discord.HTTPException:
                await general.send("The file generated was too large to send...", ctx.channel)
            os.remove("tts.mp3")
        else:
            return await general.send("This command is not available at the moment", ctx.channel)

    @commands.group(name="rsl1", aliases=["rsl"])
    @commands.check(lambda ctx: ctx.channel.id in [610482988123422750, 787340111963881472, 725835449502924901, 742885168997466196]
                    and ctx.author.id in [302851022790066185, 291665491221807104, 230313032956248064])  # me, Leitoxz, Steir
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def rsl1(self, ctx: commands.Context):
        """ RSL-1 data """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @rsl1.command(name="numbers", aliases=["n"])
    async def rsl1_numbers(self, ctx: commands.Context, number: int = None):
        """ Translate a number to RSL-1 """
        if number is None:
            return await general.send(f"This command can translate a number to RSL-1. For example, `{ctx.prefix}rsl1 {ctx.invoked_with} 1` "
                                      f"will translate the number 1 to RSL-1.", ctx.channel)
        return await general.send(f"The RSL-1 for `{number:,}` is `{rsl_number(number)}`.", ctx.channel)

    @rsl1.command(name="phrases", aliases=["p", "d", "words", "w"])
    async def rsl1_words(self, ctx: commands.Context):
        """ Some RSL-1 words and phrases """
        stuff = [
            ["thanks", "hallera"],
            ["please", "kinnelli"],
            ["hello", "liarustu"],
            ["good morning", "hiaran rean"],
            ["good afternoon", "hiaran sean"],
            ["good evening", "hiaran vean"],
            ["good night (greeting)", "hiaran tean"],
            ["good night, sleep well", "hiaran sehlun"],
            ["goodbye", "lankuvurru"],
            ["good luck", "ivjar lettuman"],
            ["idiot, cunt, and other synonyms", "arhaneda"],
            ["I love you", "sa leivaa tu"],
            ["I like you", "sa altikaa tu"],
            ["I hate you", "sa delvaa tu"],
            ["what do you want", "ne kaidas"],
            ["you are cute", "te jas millar/te jas leitakar"],
            ["you are beautiful/hot", "te jas leidannar"],
            ["you are ugly", "te jas arkantar"],
            ["I am 7 years old", "sa ivja 7 kaadazan si"],
            ["yes", "to"],
            ["no", "des"],
            ["die in a fire", "senardar aigynnuri"],
            ["I don't care", "e jat sav vuntevo"],
            ["I couldn't care less", "e ar de maikat sav kuvuntevo vian"],
            ["congrats", "nilkirriza"],
            ["heaven, paradise", "Naivur"],
            ["hell", "Eideru/Eilarru"],
            ["school", "eitaru"],
            ["happy birthday", "kovanan reidesean"],
            ["Happy Halloween", "Kovanan Savainun"],
            ["Happy New Year", "Kovanan Nuan Kaadun"],
            ["Merry Christmas", "Kovanon Raivasten"],
            ["son of a bitch", "seijanseunu"],
            ["fuck off, fuck you", "heilarsa"]
        ]
        stuff.sort(key=lambda x: x[0].lower())
        output = [f'{en} = {rsl}' for en, rsl in stuff]
        return await general.send("An entire dictionary would be hard to make because the language changes over time, but here are some things you can "
                                  "say in RSL-1:\n" + "\n".join(output), ctx.channel)


def setup(bot):
    bot.add_cog(GA78(bot))
