from datetime import datetime, timezone

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
            if year < 1970:
                return await general.send(f"{emotes.Deny} This command does not work with dates before **1 January 1970**.", ctx.channel)
            dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
        ti = dt.strftime("%A, %d/%m/%Y AD, %H:%M:%S %Z")  # Time IRL
        tk = ss23.date_kargadia(dt)  # Time in Kargadia
        tz = "Placeholder"
        tq = "Placeholder"
        return await general.send(f"Time on Earth: **{ti}**\nTime on Zeivela: **{tz}**\nTime in Kargadia: **{tk}**\nTime on Placeholder: **{tq}**", ctx.channel)


def setup(bot):
    bot.add_cog(SS23(bot))
