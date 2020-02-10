from discord.ext import commands

from utils import bias


class Testing(commands.Cog):
    @commands.command(name="placeholder", hidden=True)
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def placeholder(self, ctx):
        """ Relative Time Delta """
        return await ctx.send("Fuck off, command not in use. " + str(bias.friend_bias(ctx.bot, ctx.author)))


def setup(bot):
    bot.add_cog(Testing(bot))
