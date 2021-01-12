import random

import discord
from discord.ext import commands

from core.utils import emotes, general
from languages import langs


class Ratings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="pickle")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def pickle_size(self, ctx, *, who: discord.User = None):
        """ Measure someone's pickle """
        locale = langs.gl(ctx)
        user = who or ctx.author
        random.seed(user.id)
        _result = random.uniform(10, 30)
        custom = {
            self.bot.user.id: 42.0,
            302851022790066185: 29.9,
            746173049174229142: 0.0
        }
        result = custom.get(user.id, _result)
        return await general.send(langs.gls("ratings_pickle", locale, user.name, langs.gfs(result, locale), langs.gfs(result / 2.54, locale)), ctx.channel)

    @commands.command(name="rate")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def rate(self, ctx: commands.Context, *, what: str):
        """ Rate something """
        locale = langs.gl(ctx)
        random.seed(what.lower())
        _max = 100
        r = random.randint(0, _max)
        if what.lower() == "senko":
            r = _max
        return await general.send(langs.gls("ratings_rate", locale, what, langs.gns(r, locale), langs.gns(_max, locale)), ctx.channel)

    @commands.command(name="rateuser")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def rate_user(self, ctx: commands.Context, *, who: discord.User = None):
        """ Rate someone """
        locale = langs.gl(ctx)
        who = who or ctx.author
        random.seed(who.id)
        # _pl = langs.get_data("_pl", locale)
        # _max = int(_pl[2])
        _max = 100
        r1, r2 = _max // 2, _max
        r = random.randint(r1, r2)
        custom = {
            302851022790066185: r2,  # Me
            self.bot.user.id: r2,    # Suager
            291665491221807104: r2,  # Leitoxz
            746173049174229142: 0    # racc
        }
        result = custom.get(who.id, r)
        return await general.send(langs.gls("ratings_rate_user", locale, who.name, langs.gns(result, locale), langs.gns(_max, locale)), ctx.channel)

    @commands.command(name="babyrate")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def baby_rate(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Chance of 2 users having a baby """
        locale = langs.gl(ctx)
        if user1 == user2:
            return await general.send(langs.gls("ratings_baby_rate_self", locale), ctx.channel)
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            return await general.send(langs.gls("ratings_baby_rate_suager", locale), ctx.channel)
        if user1.bot or user2.bot:
            return await general.send(langs.gls("ratings_baby_rate_bot", locale), ctx.channel)
        seed = user1.id + user2.id
        random.seed(seed)
        # rate = random.uniform(0, 100)
        rate = langs.gfs(random.random(), locale, 2, True)
        return await general.send(langs.gls("ratings_baby_rate", locale, user1.name, user2.name, rate), ctx.channel)

    @commands.command(name="love", aliases=["lovecalc"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def love_calc(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Calculate the amount of love between 2 users """
        locale = langs.gl(ctx)
        if user1 == user2:
            return await general.send(langs.gls("ratings_baby_rate_self", locale), ctx.channel)
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            return await general.send(langs.gls("ratings_love_calc_suager", locale), ctx.channel)
        if user1.bot ^ user2.bot:
            return await general.send(langs.gls("ratings_love_calc_bots", locale), ctx.channel)
        seed = user1.id - user2.id
        random.seed(seed)
        rate = langs.gfs(random.random(), locale, 2, True)
        if (user1.id == 291665491221807104 and user2.id == 302851022790066185) or (user2.id == 291665491221807104 and user1.id == 302851022790066185):
            rate = langs.gfs(1.0, locale, 2, True)
        return await general.send(langs.gls("ratings_love_calc", locale, user1.name, user2.name, rate), ctx.channel)

    @commands.command(name="hotcalc", aliases=["hotness", "hot"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def hotness(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check how hot someone is """
        locale = langs.gl(ctx)
        user = who or ctx.author
        random.seed(user.id - 1)
        step1 = random.random()
        custom = {
            302851022790066185: 1,       # Regaus
            self.bot.user.id: 1,         # Suager
            291665491221807104: 1,       # Leitoxz
            746173049174229142: 0        # racc
        }
        rate = custom.get(user.id, step1)
        emote = emotes.SadCat if 0 <= rate < 0.5 else emotes.Pog if 0.5 <= rate < 0.75 else emotes.LewdMegumin
        return await general.send(langs.gls("ratings_hot", locale, user.name, langs.gfs(rate, locale, 2, True), emote), ctx.channel)

    @commands.command(name="iq")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def iq_test(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check Someone's IQ """
        locale = langs.gl(ctx)
        user = who or ctx.author
        random.seed(user.id + 1)
        iq = random.uniform(50, 150)
        if user.id in [302851022790066185, self.bot.user.id]:
            iq = 150.01
        elif user.id == 746173049174229142:
            iq = 0.0
        # elif user.id == 533680271057354762:
        #     iq = -2147483647.0
        ri = langs.gfs(iq, locale, 2)
        return await general.send(langs.gls("ratings_iq", locale, user.name, ri), ctx.channel)


def setup(bot):
    bot.add_cog(Ratings(bot))
