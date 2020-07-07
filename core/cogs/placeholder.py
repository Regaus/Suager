from discord.ext import commands

from core.utils import general


class Placeholder(commands.Cog):
    @commands.command(name="placeholder")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def placeholder(self, ctx: commands.Context):
        """ Placeholder """
        return await general.send("Placeholder", ctx.channel)


def setup(bot):
    bot.add_cog(Placeholder(bot))
