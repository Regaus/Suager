from datetime import datetime, timezone

import discord
from discord.ext import commands

from core.utils import bases, general, time, emotes
from suager.utils import ss23


class SS23(commands.Cog):
    @commands.command(name="time23", aliases=["timek", "timez", "timess"], hidden=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def time_kargadia(self, ctx: commands.Context, year: int = None, month: int = 1, day: int = 1, hour: int = 0, minute: int = 0, second: int = 0):
        """ Compare times from Earth with other places """
        if year is None:
            dt = time.now(None)
        else:
            if year < 1970 or (year == 1970 and month < 4):
                return await general.send(f"{emotes.Deny} This command does not work with dates before **1 April 1970**.", ctx.channel)
            dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
        ti = dt.strftime("%A, %d/%m/%Y AD, %H:%M:%S %Z")  # Time IRL
        tk = ss23.date_kargadia(dt)  # Time in Kargadia
        tz = ss23.date_zeivela(dt)  # Time on Zeivela
        tq = ss23.date_kaltaryna(dt)  # Time in Kaltaryna
        return await general.send(f"Time on Earth: **{ti}**\nTime on Zeivela: **{tz}**\nTime in Kargadia: **{tk}**\nTime in Kaltaryna: **{tq}**", ctx.channel)

    @commands.command(name="weather23", hidden=True)
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

    @commands.command(name="timetb", hidden=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def time_tbl(self, ctx: commands.Context):
        """ Time in TBL """
        dt = time.now(None)
        ti = dt.strftime("%A, %d/%m/%Y AD, %H:%M:%S %Z")  # Time IRL
        tk = ss23.time_kargadia(dt, tz=2.5, tzn="TBT").str_dec(True, False, True)  # Time in Kargadia
        return await general.send(f"Time on Earth: **{ti}**\nTime in TBL: **{tk}**", ctx.channel)

    @commands.command(name="nlc", hidden=True)
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
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def rsl_numbers(self, ctx: commands.Context, language: int, number: int):
        """ Translates number input into RSL """
        if number < 0:
            return await general.send("Negative numbers are not supported.", ctx.channel)
        if language == 1:
            max_number = int(str(10 ** 24), base=16)
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
            return await general.send(f"RSL-{language} is currently not supported.", ctx.channel)

        def thousand(val: int):
            def less_100(value: int):
                if value == 0:
                    return numbers["0"]
                elif 1 <= value < exp:
                    return numbers["1"][value - 1]
                elif value == exp:
                    return numbers["10"][0]
                elif 16 < value < 32:
                    return numbers["11"][value - 17]
                elif 32 <= value < 256:
                    div, mod = divmod(value, 16)
                    base = numbers["21"][mod - 1] + " " if mod > 0 else ""
                    tens = numbers["10"][div - 1]
                    return f"{base}{tens}"
                else:
                    return "Error"

            def hundreds(value: int):
                ind = 0 if value == 1 else 1 if 1 < value < 8 else 2
                return "" if value < 1 else less_100(value) + f" {numbers['100'][ind]}, "

            return f"{hundreds(val // 256)}{less_100(val % 256)}"

        def large():
            # exponents = [int(str(10 ** val), base=16) for val in [3, 6, 9, 12, 15, 18, 21]]
            values = []
            value = number
            for i in range(7):
                value //= 4096
                values.append(value % 4096)
            outputs = []
            for i in range(7):
                val = values[i]
                if val > 0:
                    n1, n2, n3 = numbers["1000"] if i == 0 else numbers["big"][i - 1]
                    name = n3 if 16 <= val % 256 <= 32 or val % 16 >= 8 else n2 if val % 16 != 1 else n1
                    outputs.append(f"{thousand(val)} {name}, ")
            return "".join(outputs[::-1])

        _number = bases.to_base(number, 16, True)
        # output = f"{hundreds(number // 256)}{less_100(number % 256)}"
        output = f"{large()}{thousand(number % 4096)}"
        return await general.send(f"Base-10: {number:,}\nBase-16: {_number}\nRSL-{language}: {output}", ctx.channel)


def setup(bot):
    bot.add_cog(SS23(bot))
