import random

import discord
from discord.ext import commands

from utils import generic


class Fun(commands.Cog):
    @commands.command(name="rate")
    async def rate(self, ctx, *, what: commands.clean_content):
        """ Rate something """
        r = random.randint(0, 1000) / 10
        if str(what).lower() == "xela":
            r = 0.0
        return await ctx.send(f"I'd rate {what} a {r}/100")

    @commands.command(name="rateuser")
    @commands.guild_only()
    async def rate_user(self, ctx, who: discord.Member):
        """ Rate someone """
        random.seed(who.id)
        r1, r2 = [750, 1000]
        if who.id == ctx.author.id:
            r1, r2 = [950, 1000]
        r = random.randint(r1, r2) / 10
        return await ctx.send(f"I'd rate {who} a {r}/100")

    @commands.command(name="pingspam", hidden=True)
    @commands.guild_only()
    async def ping_spam(self, ctx, who: discord.Member, times: int, *, message: str = None):
        """ Ping Spam """
        if who.id == 302851022790066185:
            return await ctx.send("Nah, not Regaus. :^)")
        if ctx.channel.id != 674338147689168897:
            return await ctx.send("Nah, <#674338147689168897> only.")
        if times > 15000:
            return await ctx.send("Nah, only up to 15k.")
        add = f"\nMessage from {ctx.author.name}: {message}" if message is not None else ''
        try:
            for i in range(1, times+1):
                await ctx.send(f"{who.mention} - Get pinged! ({i}/{times}){add}")
        except Exception as e:
            return await ctx.send(f"An error has occurred... {e}")
        return await ctx.send(f"{ctx.author.mention} - I'm done torturing {who.name}, you motherfucker")

    @commands.command(name="babyrate")
    @commands.guild_only()
    async def baby_rate(self, ctx, user1: discord.Member, user2: discord.Member):
        """ Chance of 2 users having a baby """
        seed = user1.id + user2.id
        random.seed(seed)
        rate = random.randint(0, 100)
        embed = discord.Embed(colour=generic.random_colour(),
                              description=f"The chance of {user1.mention} and {user2.mention} "
                                          f"having a baby is **{rate}**%")
        return await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Fun(bot))
