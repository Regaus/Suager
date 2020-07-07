import random

import discord
from discord.ext import commands

from core.utils import general, emotes


class Ratings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="pickle")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def pickle_size(self, ctx, *, who: discord.User = None):
        """ Measure someone's pickle """
        user = who or ctx.author
        random.seed(user.id)
        _result = random.uniform(10, 30)
        custom = {
            self.bot.user.id: 42.0,
            302851022790066185: 29.9
        }
        result = custom.get(user.id, _result)
        return await general.send(f"**{user.name}**'s pickle size is **{result:.2f}cm ({result / 2.54:.2f}in)**", ctx.channel)

    @commands.command(name="rate")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def rate(self, ctx: commands.Context, *, what: str):
        """ Rate something """
        random.seed(what.lower())
        r = random.uniform(0, 100)
        if what.lower() == "senko":
            r = 100
        return await general.send(f"I rate {what} as **{r:.2f}/100**", ctx.channel)

    @commands.command(name="rateuser")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def rate_user(self, ctx: commands.Context, *, who: discord.User):
        """ Rate someone """
        random.seed(who.id)
        r1, r2 = [50, 100]
        r = random.uniform(r1, r2)
        custom = {
            424472476106489856: r1 - 0.1,  # canvas the sour lemon
            302851022790066185: r2,  # Me
            597373963571691520: r2,  # Nuriki
            self.bot.user.id: r2,  # Suager
        }
        result = custom.get(who.id, r)
        return await general.send(f"I rate **{who.name}** as **{result:.2f}/100**", ctx.channel)

    @commands.command(name="babyrate")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def baby_rate(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Chance of 2 users having a baby """
        if user1 == user2:
            return await general.send("I don't think that's how it works...", ctx.channel)
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            return await general.send("I am not programmed to do things like that...", ctx.channel)
        if user1.bot or user2.bot:
            return await general.send("Bots can't do that...", ctx.channel)
        seed = user1.id + user2.id
        random.seed(seed)
        rate = random.uniform(0, 100)
        return await general.send(f"The chance of **{user1.name}** and **{user2.name}** having a baby is **{rate:.2f}%**", ctx.channel)

    @commands.command(name="love", aliases=["lovecalc"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def love_calc(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Calculate the amount of love between 2 users """
        if user1 == user2:
            return await general.send("I don't think that's how it works...", ctx.channel)
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            return await general.send("I don't feel love to normal users...", ctx.channel)
        if user1.bot ^ user2.bot:
            return await general.send("Bots can't feel love to normal users...", ctx.channel)
        seed = user1.id - user2.id
        random.seed(seed)
        rate = random.uniform(0, 100)
        return await general.send(f"The love level between **{user1.name}** and **{user2.name}** is **{rate:.2f}%**", ctx.channel)

    @commands.command(name="hotcalc", aliases=["hotness", "hot"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def hotness(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check how hot someone is """
        user = who or ctx.author
        random.seed(user.id - 1)
        step1 = random.uniform(0, 100)
        custom = {
            302851022790066185: 100,
            597373963571691520: 100,   # Nuriki
            self.bot.user.id: 100,   # Suager
        }
        rate = custom.get(user.id, step1)
        emote = emotes.SadCat if 0 < rate < 50 else emotes.Pog if 50 <= rate < 75 else emotes.LewdMegumin
        return await general.send(f"**{user.name}** is **{rate:.2f}%** hot {emote}", ctx.channel)

    @commands.command(name="iq")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def iq_test(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check Someone's IQ """
        user = who or ctx.author
        random.seed(user.id + 1)
        ri = random.uniform(50, 150)
        r = f"{ri:.2f}"
        if user.id == 302851022790066185:
            r = "151.00"
        if user.id == self.bot.user.id:
            r = "Infinite"
        return await general.send(f"**{user.name}**'s IQ is **{r}**", ctx.channel)


def setup(bot):
    bot.add_cog(Ratings(bot))
