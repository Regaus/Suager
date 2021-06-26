from discord.ext import commands

from utils import general, languages, times


class Kuastall(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="tbl")
    @commands.guild_only()
    @commands.check(lambda ctx: ctx.author.id in [302851022790066185, 517012611573743621])  # Temporarily lock TBL while it's not finished
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def tbl(self, ctx: commands.Context):
        """ Temval na Bylkain'de Liidennvirkalte v2 """
        if ctx.invoked_subcommand is None:
            # return await ctx.send_help(str(ctx.command))
            # locale = tbl_locale(ctx)
            locale = languages.gl(ctx)
            return await general.send(languages.gls("placeholder", locale), ctx.channel)

    @tbl.command(name="time")
    async def tbl_time(self, ctx: commands.Context):
        """ TBL Time """
        return await general.send("Time in Sentatebaria: " + times.time_kargadia(tz=-8).str(dow=True, era=None, month=False), ctx.channel)
        # return await general.send(ss23.date_kargadia(tz=2, tzn="TBT"), ctx.channel)


def setup(bot):
    bot.add_cog(Kuastall(bot))
