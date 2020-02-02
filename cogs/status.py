from discord.ext import commands

from utils import prev


class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx):
        """ Ping Pong """
        import time as _time
        t1 = _time.monotonic()
        ws = int(self.bot.latency * 1000)
        msg = await ctx.send(f"<a:loading:651883385878478858> {ctx.author.mention} Pong\n"
                             f"Message Send: undefined\nMessage Edit: undefined\nWS: {ws:,}ms")
        t2 = int((_time.monotonic() - t1) * 1000)
        await msg.edit(content=f"<a:loading:651883385878478858> {ctx.author.mention} Pong\n"
                               f"Message Send: {t2:,}ms\nMessage Edit: undefined\nWS: {ws:,}ms")
        t3 = int((_time.monotonic() - t1 - (t2/1000)) * 1000)
        await msg.edit(content=f"{ctx.author.mention} Pong:\n"
                               f"Message Send: {t2:,}ms\nMessage Edit: {t3:,}ms\nWS: {ws:,}ms")

    @commands.command(name="offline")
    @commands.is_owner()
    async def offline(self, ctx):
        """ Server is offline """
        return await prev.status(ctx, 0)

    @commands.command(name="online")
    @commands.is_owner()
    async def online(self, ctx):
        """ Server is online """
        return await prev.status(ctx, 1)

    @commands.command(name="restart")
    @commands.is_owner()
    async def restart(self, ctx):
        """ Notify of restart incoming... """
        return await prev.status(ctx, 2)


def setup(bot):
    bot.add_cog(Status(bot))
