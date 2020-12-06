import os
from datetime import datetime, timezone

import discord
import pyttsx3
from discord.ext import commands

from core.utils import bases, emotes, general, time
from cobble.utils import ss23, ss24


class SS23(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            self.tts = pyttsx3.init()
        except Exception as _:
            del _
            self.tts = None

    @commands.command(name="time23", aliases=["timek", "timez", "timess"], hidden=True)
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
        months_1 = ["Seldan Masailnar'an", "Nuannar'an", "Seimannar'an", "Veisanar'an", "Eilannar'an", "Havazdallarinnar'an",
                    "Sanvaggannar'an", "Kailaggannar'an", "Semardannar'an", "Addanvar'an", "Halltuavar'an", "Masailnar'an"]
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

    @commands.command(name="time24", hidden=True)
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

    @commands.command(name="weather23", hidden=True)
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

    @commands.command(name="nlc", hidden=True)
    @commands.is_owner()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def ne_world_ll_calc(self, ctx: commands.Context, x: int, z: int, border: int = 100000):
        """ Calculate latitude, local offset of position - NEWorld """
        lat = -z / border * 90  # Latitude value
        long = x / border * 180
        tzl = 48 / 180
        tz = round(long / tzl)
        tzo = tz / tzl - long  # Local Offset
        return await general.send(f"At {x=:,} and {z=:,} (World Border at {border:,}):\nLatitude: {lat:.3f}\nLocal Offset: {tzo:.3f}", ctx.channel)

    @commands.command(name="rsln", hidden=True)
    @commands.is_owner()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def rsl_numbers(self, ctx: commands.Context, language: str, number: int):
        """ Translates number input into RSL """
        if number < 0:
            return await general.send("Negative numbers are not supported.", ctx.channel)
        if language == "1":
            max_number = int(str(10 ** 24), base=16) - 1
            if number > max_number:
                return await general.send(f"The value you entered is above the maximum value translate-able ({max_number:,})", ctx.channel)
            numbers = {
                "0": "des/deneda",
                "1": ["ukka", "devi", "teri", "cegi", "paki", "senki", "ekki", "onni", "zunni", "dovi", "tori", "cogi", "bagi", "soni", "enni"],
                "11": ["uveri", "devuverri", "teruverri", "ceguverri", "pakuverri", "senkuverri", "ekkuverri", "onnuverri",
                       "zunuverri", "dovuverri", "toruverri", "coguverri", "baguverri", "sonuverri", "ennuverri"],
                "10": ["verri", "deveri", "tereri", "ceveri", "paveri", "seneri", "ekeri", "oneri",
                       "zuveri", "doveri", "toreri", "coveri", "baneri", "soneri", "eneri"],
                "21": ["uk u", "dev u", "ter u", "ceg u", "pak u", "senk-u", "ekk-u", "onn-u", "zunn-u", "dov u", "tor u", "cog u", "bag u", "son u", "enn-u"],
                "100": ["setti", "settin", "settar"],
                "1000": ["kiari", "kiarin", "kiarar"],
                "big": [["ugaristu", "ugaristun", "ugaristar"], ["devaristu", "devaristun", "devaristar"], ["teráristu", "teráristun", "teráristar"],
                        ["cegaristu", "cegaristun", "cegaristar"], ["pakaristu", "pakaristun", "pakaristar"], ["senkaristu", "senkaristun", "senkaristar"]]
            }
            exp = 16
        else:
            return await general.send(f"RSL-{language} is currently not supported.\nRSL's available: 1.", ctx.channel)

        def thousand(val: int):
            def less_100(value: int):
                if value == 0:
                    return ""
                elif 1 <= value < exp:
                    return numbers["1"][value - 1]
                elif value == exp:
                    return numbers["10"][0]
                elif exp < value < 2 * exp:
                    return numbers["11"][value - 17]
                elif 2 * exp <= value < exp * exp:
                    div, mod = divmod(value, exp)
                    base = numbers["21"][mod - 1] + " " if mod > 0 else ""
                    tens = numbers["10"][div - 1]
                    return f"{base}{tens}"
                else:
                    return "Error"

            def hundreds(value: int, mod: int):
                ind = 0 if value == 1 else 1 if 1 < value < 8 else 2
                return "" if value < 1 else less_100(value) + f" {numbers['100'][ind]}{', ' if mod != 0 else ''}"

            a, b = divmod(val, exp * exp)
            return f"{hundreds(a, b)}{less_100(b)}"

        def large():
            # exponents = [int(str(10 ** val), base=16) for val in [3, 6, 9, 12, 15, 18, 21]]
            values = []
            value = number
            for i in range(7):
                value //= exp ** 3
                values.append(value % (exp ** 3))
            outputs = []
            for i in range(7):
                val = values[i]
                if val > 0:
                    n1, n2, n3 = numbers["1000"] if i == 0 else numbers["big"][i - 1]
                    name = n3 if exp <= val % (exp ** 2) <= 2 * exp or val % exp >= 8 else n2 if val % exp != 1 else n1
                    outputs.append(f"{thousand(val)} {name}, ")
            return "".join(outputs[::-1])

        _number = bases.to_base(number, exp, True)
        # output = f"{hundreds(number // 256)}{less_100(number % 256)}"
        output = f"{large()}{thousand(number % (exp ** 3))}"
        if number == 0:
            output = numbers["0"]
        return await general.send(f"Base-10: {number:,}\nBase-{exp}: {_number}\nRSL-{language}: {output}", ctx.channel)

    @commands.command("rslt", hidden=True)
    @commands.check(lambda ctx: ctx.author.id in [302851022790066185, 236884090651934721, 291665491221807104])
    async def rsl_encode(self, ctx: commands.Context, s: int, *, t: str):
        """ Laikattart Sintuvut """
        if not (1 <= s <= 256):
            return await general.send("De va edou dejal, no nu so maikal ir te edou kihtemal", ctx.channel)
        encoding = {1: "ukka", 2: "devi", 3: "tei", 4: "seghi", 5: "paki", 6: "seni", 7: "ei", 8: "oni",
                    9: "zegi", 10: "dove", 11: "tore", 12: "seghe", 13: "page", 14: "seine", 15: "eghe", 16: "veire",
                    17: "uveire", 18: "deire", 19: "tevre", 20: "sevre", 21: "pakke", 22: "seire", 23: "eire", 24: "onre",
                    25: "zeire", 26: "dojere", 27: "tovere", 28: "sejere", 29: "paghere", 30: "seinere", 31: "einere", 32: "devveire"}
        u = ["ukka", "devi", "tei", "sei", "paki", "seni", "ei", "oni", "zegi", "dove", "tore", "see", "page", "seine", "ee"]
        v = ["devveire", "tevveire", "seghveire", "pahveire", "senveire", "eiveire", "onveire",
             "zeghveire", "dovveire", "torveire", "seiveire", "paiveire", "seineveire", "eghveire", "ukka aragi"]
        shift = s * 128
        if 1 <= s <= 32:
            code = encoding[s]
        else:
            w, x = divmod(s, 16)
            if x == 0:
                code = v[w - 2]
            else:
                code = f"{u[x - 1]} u {v[w - 2]}"
        text = "".join([chr(ord(letter) + shift) for letter in t])
        return await general.send(f"{code} {text}", ctx.channel)

    @commands.command("rslf", hidden=True)
    @commands.check(lambda ctx: ctx.author.id in [302851022790066185, 236884090651934721, 291665491221807104])
    async def rsl_decode(self, ctx: commands.Context, s: int, *, t: str):
        """ Laikattarad Sintuvuad """
        if not (1 <= s <= 256):
            return await general.send("De va edou dejal, no nu so maikal ir te edou kihtemal", ctx.channel)
        shift = s * 128
        text = ""
        for letter in t:
            try:
                a = chr(ord(letter) - shift)
            except ValueError:
                a = chr(0)
            text += a
        return await general.send(text, ctx.channel)

    @commands.command("tts", hidden=True)
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


def setup(bot):
    bot.add_cog(SS23(bot))
