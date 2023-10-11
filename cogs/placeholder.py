from utils import bot_data, commands


class Placeholder(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.command(name="placeholder")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def placeholder(self, ctx: commands.Context):
        """ Placeholder """
        language = ctx.language()
        return await ctx.send(language.string("placeholder"))


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Placeholder(bot))
