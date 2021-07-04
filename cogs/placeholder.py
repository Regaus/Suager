from discord.ext import commands

from utils import bot_data, general


class Placeholder(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.command(name="placeholder")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def placeholder(self, ctx: commands.Context):
        """ Placeholder """
        language = self.bot.language(ctx)
        return await general.send(language.string("placeholder"), ctx.channel)


def setup(bot: bot_data.Bot):
    bot.add_cog(Placeholder(bot))
