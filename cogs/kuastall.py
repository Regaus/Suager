from regaus import conworlds

from utils import bot_data, commands


class Kuastall(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
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
            language = ctx.language()
            return await ctx.send(language.string("placeholder"))

    @tbl.command(name="time")
    async def tbl_time(self, ctx: commands.Context):
        """ TBL Time """
        return await ctx.send("Time in Sentatebaria: " + conworlds.Place("Sentatebaria").time.strftime('%A, %d %B %Y, %H:%M:%S', 'en'))


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Kuastall(bot))
