from discord.ext import commands


class Testing(commands.Cog):
    @commands.command(name="placeholder", hidden=True)
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.user)
    async def placeholder(self, ctx):
        """ Placeholder """
        return await ctx.send("Fuck off, command not in use.")


def setup(bot):
    bot.add_cog(Testing(bot))
