import random

import discord
from discord.ext import commands

from core.utils import general, emotes, database
from languages import langs


class Ratings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database(self.bot.name)

    @commands.command(name="pickle")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def pickle_size(self, ctx, *, who: discord.User = None):
        """ Measure someone's pickle """
        locale = langs.gl(ctx.guild, self.db)
        user = who or ctx.author
        random.seed(user.id)
        _result = random.uniform(10, 30)
        custom = {
            self.bot.user.id: 42.0,
            302851022790066185: 29.9
        }
        result = custom.get(user.id, _result)
        return await general.send(langs.gls("ratings_pickle", locale, user.name, langs.gfs(result, locale), langs.gfs(result / 2.54, locale)), ctx.channel)
        # return await general.send(f"**{user.name}**'s pickle size is **{result:.2f}cm ({result / 2.54:.2f}in)**. "
        #                           f"At least the random number generator said so.", ctx.channel)

    @commands.command(name="rate")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def rate(self, ctx: commands.Context, *, what: str):
        """ Rate something """
        locale = langs.gl(ctx.guild, self.db)
        random.seed(what.lower())
        _pl = langs.get_data("_pl", locale)
        _max = int(_pl[2])
        r = random.randint(0, _max)
        if what.lower() == "senko":
            r = _max
        return await general.send(langs.gls("ratings_rate", locale, what, langs.gns(r, locale), langs.gns(_max, locale)), ctx.channel)
        # return await general.send(f"I rate {what} as **undefined/100**\nI literally don't care about what those things are. All I do is execute weird code "
        #                           f"my creator wrote for your entertainment, I don't form opinions on things the way you humans do.", ctx.channel)

    @commands.command(name="rateuser")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def rate_user(self, ctx: commands.Context, *, who: discord.User = None):
        """ Rate someone """
        locale = langs.gl(ctx.guild, self.db)
        who = who or ctx.author
        random.seed(who.id)
        _pl = langs.get_data("_pl", locale)
        _max = int(_pl[2])
        r1, r2 = _max // 2, _max
        r = random.randint(r1, r2)
        custom = {
            302851022790066185: r2,  # Me
            self.bot.user.id: r2,  # Suager
        }
        result = custom.get(who.id, r)
        return await general.send(langs.gls("ratings_rate_user", locale, who.name, langs.gns(result, locale), langs.gns(_max, locale)), ctx.channel)
        # return await general.send(f"I rate **{who.name}** as **undefined/100**\nWhat makes you think I care about you enough to have a rating?", ctx.channel)

    @commands.command(name="babyrate")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def baby_rate(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Chance of 2 users having a baby """
        locale = langs.gl(ctx.guild, self.db)
        if user1 == user2:
            return await general.send(langs.gls("ratings_baby_rate_self", locale), ctx.channel)
            # return await general.send("I don't think that's how it works...", ctx.channel)
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            return await general.send(langs.gls("ratings_baby_rate_suager", locale), ctx.channel)
            # return await general.send("I am not programmed to do things like that...", ctx.channel)
        if user1.bot or user2.bot:
            return await general.send(langs.gls("ratings_baby_rate_bot", locale), ctx.channel)
            # return await general.send("Bots can't do that...", ctx.channel)
        seed = user1.id + user2.id
        random.seed(seed)
        # rate = random.uniform(0, 100)
        rate = langs.gfs(random.random(), locale, 2, True)
        return await general.send(langs.gls("ratings_baby_rate", locale, user1.name, user2.name, rate), ctx.channel)
        # return await general.send(f"The chance of **{user1.name}** and **{user2.name}** having a baby is **{rate:.2f}%**. At least according to the "
        #                           f"random number generator.", ctx.channel)

    @commands.command(name="love", aliases=["lovecalc"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def love_calc(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Calculate the amount of love between 2 users """
        locale = langs.gl(ctx.guild, self.db)
        if user1 == user2:
            return await general.send(langs.gls("ratings_baby_rate_self", locale), ctx.channel)
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            return await general.send(langs.gls("ratings_love_calc_suager", locale), ctx.channel)
            # return await general.send("I am not programmed to feel love.", ctx.channel)
        if user1.bot ^ user2.bot:
            return await general.send(langs.gls("ratings_love_calc_bots", locale), ctx.channel)
            # return await general.send("Bots can't feel love to normal users...", ctx.channel)
        seed = user1.id - user2.id
        random.seed(seed)
        # rate = random.uniform(0, 100)
        rate = langs.gfs(random.random(), locale, 2, True)
        return await general.send(langs.gls("ratings_love_calc", locale, user1.name, user2.name, rate), ctx.channel)
        # return await general.send(f"The love level between **{user1.name}** and **{user2.name}** is **{rate:.2f}%** according to my random number "
        #                           f"generation capabilities.", ctx.channel)

    @commands.command(name="hotcalc", aliases=["hotness", "hot"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def hotness(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check how hot someone is """
        locale = langs.gl(ctx.guild, self.db)
        user = who or ctx.author
        random.seed(user.id - 1)
        # step1 = random.uniform(0, 100)
        step1 = random.random()
        # step1 = 0
        custom = {
            302851022790066185: 1,  # Regaus
            self.bot.user.id: 1,    # Suager
        }
        rate = custom.get(user.id, step1)
        emote = emotes.SadCat if 0 <= rate < 0.5 else emotes.Pog if 0.5 <= rate < 0.75 else emotes.LewdMegumin
        return await general.send(langs.gls("ratings_hot", locale, user.name, langs.gfs(rate, locale, 2, True), emote), ctx.channel)
        # return await general.send(f"**{user.name}** is **{rate:.2f}%** hot {emote}. I'm a bot, I don't see things as \"hot\" like you do.", ctx.channel)

    @commands.command(name="iq")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def iq_test(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check Someone's IQ """
        locale = langs.gl(ctx.guild, self.db)
        user = who or ctx.author
        # if user.bot:
        #     return await general.send(f"**{user.name}**'s IQ is **undefined**. We bots don't measure our intelligence. We don't care.", ctx.channel)
        random.seed(user.id + 1)
        ri = langs.gfs((random.uniform(50, 150) if user.id not in [302851022790066185, self.bot.user.id] else 150.01), locale, 2)
        # r = f"{ri:.2f}"
        # if user.id == 302851022790066185:
        #     r = "150.01"
        return await general.send(langs.gls("ratings_iq", locale, user.name, ri), ctx.channel)
        # return await general.send(f"**{user.name}**'s IQ is probably **{r}**. Maybe not, who cares?", ctx.channel)


def setup(bot):
    bot.add_cog(Ratings(bot))
