from discord.ext import commands

from utils import generic


class Placeholder(commands.Cog):
    @commands.command(name="placeholder", hidden=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def placeholder(self, ctx: commands.Context):
        """ Placeholder """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "placeholder"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        return await generic.send("Placeholder", ctx.channel)


def setup(bot):
    bot.add_cog(Placeholder(bot))
