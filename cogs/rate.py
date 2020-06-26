import random

import discord
from discord.ext import commands

from utils import generic, emotes


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
        random.seed(what.lower())
        r = random.uniform(0, 100)
        if what.lower() == "senko":
            r = 100
        return await generic.send(generic.gls(locale, "rate", [what, f"{r:.1f}"]), ctx.channel)

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
        result = custom.get(who.id, r)
        return await generic.send(generic.gls(locale, "rate", [who.name, f"{result:.1f}"]), ctx.channel)

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
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            return await generic.send(generic.gls(locale, "baby_rate_self", [ctx.author.name]), ctx.channel)
        if user1.bot or user2.bot:
            return await generic.send(generic.gls(locale, "baby_rate_bot"), ctx.channel)
        seed = user1.id + user2.id
        random.seed(seed)
        rate = random.randint(0, 100)
        no = [424472476106489856, 302851022790066185]  # Canvas and me
        if user1.id in no and user2.id in no:
            rate = 0
        embed = discord.Embed(colour=generic.random_colour(), description=generic.gls(locale, "baby_rate", [user1.mention, user2.mention, rate]))
        return await generic.send(None, ctx.channel, embed=embed)

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
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            return await generic.send(generic.gls(locale, "already_taken", [ctx.author.name]), ctx.channel)
        if user1.bot ^ user2.bot:
            return await generic.send(generic.gls(locale, "bots_love"), ctx.channel)
        seed = user1.id - user2.id
        random.seed(seed)
        rate = random.randint(0, 100)
        no = [424472476106489856, 302851022790066185]  # Canvas and me
        if user1.id in no and user2.id in no:
            rate = 0
        embed = discord.Embed(colour=generic.random_colour(), description=generic.gls(locale, "love_calc", [user1.mention, user2.mention, rate]))
        return await generic.send(None, ctx.channel, embed=embed)

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
        step1 = round(random.uniform(0, 100), 2)
        custom = {
            302851022790066185: 100,
            597373963571691520: 100,   # Nuriki
            609423646347231282: 100,   # Suager
        }
        step4 = custom.get(user.id, step1)
        if 0 < step4 < 50:
            emote = emotes.SadCat
        elif 50 <= step4 < 75:
            emote = emotes.Pog
        else:
            emote = emotes.LewdMegumin
        return await generic.send(generic.gls(locale, "hot_calc", [user.name, step4, emote]), ctx.channel)

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
        if user.id == 302851022790066185:
            ri = 151
        if user.id == self.bot.user.id:
            ri = 2147483647 * 1.17
        r = ri / 1.17
        return await generic.send(generic.gls(locale, "iq", [user.name, f"{r:,.2f}"]), ctx.channel)


def setup(bot):
    bot.add_cog(Ratings(bot))
