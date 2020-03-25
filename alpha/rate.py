import asyncio
import random

import discord
from discord.ext import commands

from utils import generic, emotes


class Ratings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="rate")
    async def rate(self, ctx, *, what: commands.clean_content):
        """ Rate something """
        random.seed(str(what))
        r = random.randint(0, 1000) / 10
        bad = ["xela", "lidl xela"]
        if str(what).lower() in bad:
            r = 0.0
        return await ctx.send(f"I'd rate {what} a **{r}/100**")

    @commands.command(name="rateuser")
    @commands.guild_only()
    async def rate_user(self, ctx, *, who: discord.Member):
        """ Rate someone """
        random.seed(who.id)
        r1, r2 = [800, 1000]
        if who.id == ctx.author.id:
            return await ctx.send(f"{ctx.author.mention} I like you the way you are! {emotes.AlexPat}")
        r = random.randint(r1, r2) / 10
        _79 = [94762492923748352, 464901058796453899, 246652610747039744]  # Bowser65
        if who.id in _79:
            r = 79.9
        _100 = [302851022790066185, 597373963571691520, 527729196688998415, 411616745451683852, 424472476106489856,
                609423646347231282, 520042197391769610, 568149836927467542]
        # Regaus, Nuriki, Aya, Huggi, canvas, and Suager (incl. Beta and Alpha)
        if who.id in _100:
            r = 100.0
        return await ctx.send(f"I'd rate {who.name} a **{r:.1f}/100**")

    @commands.command(name="babyrate")
    @commands.guild_only()
    async def baby_rate(self, ctx, user1: discord.User, user2: discord.User):
        """ Chance of 2 users having a baby """
        if user1 == user2:
            return await ctx.send("I don't think that's how it works...")
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            return await ctx.send(f"I wasn't programmed for this, {ctx.author.name}...")
        if user1.bot or user2.bot:
            return await ctx.send("Bot's can't feel love...")
        seed = user1.id + user2.id
        random.seed(seed)
        rate = random.randint(0, 100)
        embed = discord.Embed(colour=generic.random_colour(),
                              description=f"The chance of {user1.mention} and {user2.mention} "
                                          f"having a baby is **{rate}**%")
        return await ctx.send(embed=embed)

    @commands.command(name="love", aliases=["lovecalc"])
    @commands.guild_only()
    async def love_calc(self, ctx, user1: discord.User, user2: discord.User):
        """ Calculate the amount of love between 2 users """
        if user1 == user2:
            return await ctx.send("I don't think that's how it works...")
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            return await ctx.send(f"{ctx.author.name}, I'm already t-taken...")
        if user1.bot or user2.bot:
            return await ctx.send("Bot's can't feel love...")
        seed = user1.id - user2.id
        random.seed(seed)
        a = [302851022790066185, 527729196688998415, 411616745451683852]  # Nuriki Cult / Aya and Huggi
        b = [179217986517729280, 191522051943563264]  # Memory and Poro
        c = [302851022790066185, 424472476106489856]  # Canvas
        if user1.id in a and user2.id in a:
            rate = 90
        elif user1.id in b and user2.id in b:
            rate = 100
        elif user1.id in c and user2.id in c:
            rate = 100
        else:
            rate = random.randint(0, 100)
        embed = discord.Embed(colour=generic.random_colour(),
                              description=f"Love level between {user1.mention} and {user2.mention} is **{rate}**%")
        return await ctx.send(embed=embed)

    @commands.command(name="hotcalc", aliases=["hotness", "hot"])
    async def hotness(self, ctx, *, who: discord.User = None):
        """ Check how hot someone is """
        user = who or ctx.author
        random.seed(user.id - 1)
        step1 = int(random.randint(2000, 11700))
        step3 = step1 / 117
        custom = {
            302851022790066185: 99,
            424472476106489856: 99,  # canvas
            527729196688998415: 99,   # Aya
            597373963571691520: 99,   # Nuriki
        }
        step4 = custom.get(user.id, round(step3, 2))
        # step4 = bias.friend_bias(self.db, user)
        # step5 = step3 * step4
        # tep6 = 100 if step5 > 100 else step5
        if 0 < step4 < 33:
            emote = "<:sadcat:620306629124161536>"
        elif 33 <= step4 < 67:
            emote = "<:pog:610583684663345192>"
        else:
            emote = "<:LewdMegumin:679069449701163045>"
        message = await ctx.send(f"{emotes.Loading} Checking how hot {user.name} is...")
        await asyncio.sleep(3)
        return await message.edit(content=f"**{user.name}** is **{step4}%** hot {emote}")

    @commands.command(name="iq")
    async def iq_test(self, ctx, *, who: discord.User = None):
        """ Check Someone's IQ """
        user = who or ctx.author
        random.seed(user.id + 1)
        ri = random.randint(50, 255)
        # b = bias.get_bias(self.db, user)
        if user.id == 682321712779493429:
            ri = 49
        r = ri / 1.17
        msg = await ctx.send(f"{emotes.Loading} Checking {user.name}'s IQ...")
        await asyncio.sleep(3)
        return await msg.edit(content=f"**{user.name}'s** IQ is **{r:,.2f}**")


def setup(bot):
    bot.add_cog(Ratings(bot))
