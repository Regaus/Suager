from datetime import datetime, timezone

import discord
from discord.ext import commands

from core.utils import general, time, emotes
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


def setup(bot):
    bot.add_cog(SS23(bot))
