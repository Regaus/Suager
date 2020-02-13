import discord
from discord.ext import commands

from utils import bias


class Testing(commands.Cog):
    @commands.command(name="placeholder", hidden=True)
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.user)
    async def placeholder(self, ctx, *, who: discord.Member = None):
        """ Relative Time Delta """
        user = who or ctx.author
        return await ctx.send("Fuck off, command not in use. " + str(bias.friend_bias(ctx.bot, user)))


def setup(bot):
    bot.add_cog(Testing(bot))
