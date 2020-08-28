from discord.ext import commands

from core.utils import general
from languages import langs


class Placeholder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="placeholder")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def placeholder(self, ctx: commands.Context):
        """ Placeholder """
        locale = langs.gl(ctx)
        return await general.send(langs.gls("placeholder", locale), ctx.channel)


def setup(bot):
    bot.add_cog(Placeholder(bot))
