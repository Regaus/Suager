from discord.ext import commands


class Testing(commands.Cog):
    @commands.command(name="placeholder", hidden=True)
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.user)
    async def placeholder(self, ctx):
        """ Relative Time Delta """
        return await ctx.send("Fuck off, command not in use.")
        # return await ctx.send(string)
        # return await ctx.send("Fuck off, command not in use. " + str(bias.get_bias(sqlite.Database(), user)))


def setup(bot):
    bot.add_cog(Testing(bot))
