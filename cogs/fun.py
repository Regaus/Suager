import random

import discord
from discord.ext import commands


class Fun(commands.Cog):
    @commands.command(name="rate")
    async def rate(self, ctx, what: commands.clean_content):
        """ Rate something """
        r = random.randint(0, 1000) / 10
        return await ctx.send(f"I'd rate {what} a {r}/100")

    @commands.command(name="rateuser")
    @commands.guild_only()
    async def rate_user(self, ctx, who: discord.Member):
        """ Rate someone """
        r1, r2 = [750, 1000]
        if who.id == ctx.author.id:
            r1, r2 = [950, 1000]
        r = random.randint(r1, r2) / 10
        return await ctx.send(f"I'd rate {who} a {r}/100")


def setup(bot):
    bot.add_cog(Fun(bot))
