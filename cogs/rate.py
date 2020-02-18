import asyncio
import random

import discord
from discord.ext import commands

from utils import bias, generic, emotes, sqlite


class Ratings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite.Database()

    @commands.command(name="rate")
    async def rate(self, ctx, *, what: commands.clean_content):
        """ Rate something """
        random.seed(str(what))
        r = random.randint(0, 1000) / 10
        bad = ["xela", "lidl xela"]
        if str(what).lower() in bad:  # xelA is a meanie, and meanies don't deserve love mmlol
            r = 0.0                   # I don't like LIDL xelA, so it ain't getting any love either
        return await ctx.send(f"I'd rate {what} a {r}/100")

    @commands.command(name="rateuser")
    @commands.guild_only()
    async def rate_user(self, ctx, *, who: discord.Member):
        """ Rate someone """
        random.seed(who.id)
        r1, r2 = [800, 1000]
        if who.id == ctx.author.id:
            return await ctx.send(f"{ctx.author.mention} I like you the way you are! {emotes.AlexPat}")
        r = random.randint(r1, r2) / 10
        if ctx.guild.id == 568148147457490954:
            if ctx.guild.get_role(660880373894610945) in who.roles:
                r /= 3
            if 'arch' in who.name.lower():
                r /= 3
            if who.nick is not None:
                if 'arch' in who.nick.lower():
                    r /= 3
        return await ctx.send(f"I'd rate {who.name} a {r:.1f}/100")

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

    @commands.command(name="hotcalc", aliases=["hotness"])
    async def hotness(self, ctx, *, user: discord.Member = None):
        """ Check how hot someone is """
        user = user or ctx.author
        random.seed(user.id)
        step1 = int(round(random.random() * 100))
        step2 = int(round(random.random() * 20))
        step3 = step1 / (107 + step2) * 100
        step4 = bias.friend_bias(self.db, user)
        step5 = step3 * step4
        step6 = 100 if step5 > 100 else step5
        if 0 < step6 < 33:
            emote = "<:sadcat:620306629124161536>"
        elif 33 <= step6 < 67:
            emote = "<:lul:568168505543753759>"
        else:
            emote = "<:pog:610583684663345192>"
        message = await ctx.send(f"{emotes.Loading} Checking how hot {user.name} is...")
        await asyncio.sleep(3)
        return await message.edit(content=f"**{user.name}** is **{step6:.2f}%** hot {emote}")

    @commands.command(name="iq")
    async def iq_test(self, ctx, *, who: discord.Member = None):
        """ Check Someone's IQ """
        user = who or ctx.author
        random.seed(user.id)
        ri = random.randint(127, 255)
        b = bias.get_bias(self.db, user)
        r = ri * b / 1.17
        msg = await ctx.send(f"{emotes.Loading} Checking {user.name}'s IQ...")
        await asyncio.sleep(3)
        return await msg.edit(content=f"**{user.name}'s** IQ is **{r:,.2f}**")


def setup(bot):
    bot.add_cog(Ratings(bot))
