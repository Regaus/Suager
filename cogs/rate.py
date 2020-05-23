import random

import discord
from discord.ext import commands

from utils import generic


class Ratings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="rate")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def rate(self, ctx: commands.Context, *, what: str):
        """ Rate something """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "rate"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        random.seed(what)
        r = random.randint(0, 1000) / 10
        # bad = ["xela", "lidl xela"]
        # if str(what).lower() in bad:
        #     r = 0.0
        return await generic.send(generic.gls(locale, "rate", [what, r]), ctx.channel)
        # return await ctx.send(f"I'd rate {what} a **{r}/100**")

    @commands.command(name="rateuser")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def rate_user(self, ctx: commands.Context, *, who: discord.Member):
        """ Rate someone """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "rateuser"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        random.seed(who.id)
        r1, r2 = [50, 100]
        # if who.id == ctx.author.id:
        #     return await ctx.send(f"{ctx.author.mention} I like you the way you are! {emotes.AlexPat}")
        r = round(random.uniform(r1, r2), 1)
        custom = {
            94762492923748352: r1 - 0.1,   # Bowser65
            464901058796453899: r1 - 0.1,  # Foxy / Bowser's bot
            246652610747039744: r1 - 0.1,  # Bowser's alt
            424472476106489856: r1 - 0.1,  # canvas the sour lemon
            302851022790066185: r2,  # Me
            597373963571691520: r2,  # Nuriki
            411616745451683852: r2,  # Huggi
            609423646347231282: r2,  # Suager
            520042197391769610: r2,  # Suager Beta
            568149836927467542: r2,  # Suager Alpha
        }
        # _79 = [94762492923748352, 464901058796453899, 246652610747039744]  # Bowser65
        # if who.id in _79:
        #     r = 79.9
        # _100 = [302851022790066185, 597373963571691520, 527729196688998415, 411616745451683852,
        #         609423646347231282, 520042197391769610, 568149836927467542]
        # Regaus, Nuriki, Aya, Huggi, and Suager (incl. Beta and Alpha)
        # if who.id in _100:
        #     r = 100.0
        result = custom.get(who.id, r)
        return await generic.send(generic.gls(locale, "rate", [who.name, f"{result:.1f}"]), ctx.channel)
        # return await ctx.send(f"I'd rate {who.name} a **{result:.1f}/100**")

    @commands.command(name="babyrate")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def baby_rate(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Chance of 2 users having a baby """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "babyrate"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        if user1 == user2:
            return await generic.send(generic.gls(locale, "lc_same"), ctx.channel)
            # return await ctx.send("I don't think that's how it works...")
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            return await generic.send(generic.gls(locale, "baby_rate_self", [ctx.author.name]), ctx.channel)
            # return await ctx.send(f"I wasn't programmed for this, {ctx.author.name}...")
        if user1.bot or user2.bot:
            return await generic.send(generic.gls(locale, "baby_rate_bot"), ctx.channel)
            # return await ctx.send("Bot's can't feel love...")
        seed = user1.id + user2.id
        random.seed(seed)
        rate = random.randint(0, 100)
        no = [424472476106489856, 302851022790066185]  # Canvas and me
        if user1.id in no and user2.id in no:
            rate = 0
        embed = discord.Embed(colour=generic.random_colour(), description=generic.gls(locale, "baby_rate", [user1.mention, user2.mention, rate]))
        #                       description=f"The chance of {user1.mention} and {user2.mention} "
        #                                   f"having a baby is **{rate}**%")
        return await generic.send(None, ctx.channel, embed=embed)
        # return await ctx.send(embed=embed)

    @commands.command(name="love", aliases=["lovecalc"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def love_calc(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Calculate the amount of love between 2 users """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "love"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        if user1 == user2:
            return await generic.send(generic.gls(locale, "lc_same"), ctx.channel)
            # return await ctx.send("I don't think that's how it works...")
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            return await generic.send(generic.gls(locale, "already_taken", [ctx.author.name]), ctx.channel)
            # return await ctx.send(f"{ctx.author.name}, I'm already t-taken...")
        if user1.bot ^ user2.bot:
            return await generic.send(generic.gls(locale, "bots_love"), ctx.channel)
            # return await ctx.send("Bot's can't feel love...")
        seed = user1.id - user2.id
        random.seed(seed)
        # a = [417390734690484224, 255460743128940547]  # Kyomi and Lucvinhlong
        # b = [179217986517729280, 191522051943563264]  # Memory and Poro
        # if user1.id in a and user2.id in a:
        #     rate = 95
        # elif user1.id in b and user2.id in b:
        #     rate = 100
        # else:
        rate = random.randint(0, 100)
        no = [424472476106489856, 302851022790066185]  # Canvas and me
        if user1.id in no and user2.id in no:
            rate = 0
        embed = discord.Embed(colour=generic.random_colour(), description=generic.gls(locale, "love_calc", [user1.mention, user2.mention, rate]))
        #                       description=f"Love level between {user1.mention} and {user2.mention} is **{rate}**%")
        return await generic.send(None, ctx.channel, embed=embed)
        # return await ctx.send(embed=embed)

    @commands.command(name="hotcalc", aliases=["hotness", "hot"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def hotness(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check how hot someone is """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "hot"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        user = who or ctx.author
        random.seed(user.id - 1)
        # step1 = int(random.randint(2000, 11700))
        step1 = round(random.uniform(17, 100), 2)
        # step3 = step1 / 117
        custom = {
            302851022790066185: 99.99,
            # 527729196688998415: 99.97,   # Aya
            597373963571691520: 99.99,   # Nuriki
        }
        step4 = custom.get(user.id, step1)
        # step4 = bias.friend_bias(self.db, user)
        # step5 = step3 * step4
        # tep6 = 100 if step5 > 100 else step5
        if 0 < step4 < 50:
            emote = "<:sadcat:620306629124161536>"
        elif 50 <= step4 < 75:
            emote = "<:pog:610583684663345192>"
        else:
            emote = "<:LewdMegumin:679069449701163045>"
        return await generic.send(generic.gls(locale, "hot_calc", [user.name, step4, emote]), ctx.channel)
        # message = await ctx.send(f"{emotes.Loading} Checking how hot {user.name} is...")
        # await asyncio.sleep(3)
        # return await message.edit(content=f"**{user.name}** is **{step4}%** hot {emote}")

    @commands.command(name="iq")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def iq_test(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check Someone's IQ """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "iq"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        user = who or ctx.author
        random.seed(user.id + 1)
        ri = random.randint(75, 175)
        # b = bias.get_bias(self.db, user)
        if user.id == 302851022790066185:
            ri = 151
        if user.id == self.bot.user.id:
            ri = 2147483647 * 1.17
        r = ri / 1.17
        return await generic.send(generic.gls(locale, "iq", [user.name, f"{r:,.2f}"]), ctx.channel)
        # msg = await ctx.send(f"{emotes.Loading} Checking {user.name}'s IQ...")
        # await asyncio.sleep(3)
        # return await msg.edit(content=f"**{user.name}'s** IQ is **{r:,.2f}**")


def setup(bot):
    bot.add_cog(Ratings(bot))
