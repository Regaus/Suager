import random

import discord
from discord.ext import commands

from utils import bot_data, emotes, general


class Ratings(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.command(name="pickle")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def pickle_size(self, ctx, *, who: discord.User = None):
        """ Measure someone's pickle """
        language = self.bot.language(ctx)
        user = who or ctx.author
        random.seed(user.id)
        _result = random.uniform(10, 30)
        custom = {
            self.bot.user.id: 42.0,
            302851022790066185: 30.0,
        }
        if ctx.channel.id != 764528556507922442:
            result = custom.get(user.id, _result)
        else:
            result = 20
            uid1 = 302851022790066185
            uid2 = 622735873137573894
            data1 = self.bot.db.fetchrow("SELECT * FROM counters WHERE uid1=? AND uid2=?", (uid1, uid2))
            data2 = self.bot.db.fetchrow("SELECT * FROM counters WHERE uid1=? AND uid2=?", (uid2, uid1))
            result1, result2 = 0, 0
            counters = ["bang", "ff", "r"]
            for counter in counters:
                result1 += data1[counter]
                result2 += data2[counter]
            result2 += data1["suck"]
            result1 += data2["suck"]
            if user.id == uid1:
                result += result1 * 0.02
                result -= result2 * 0.03
            else:
                result -= result1 * 0.03
                result += result2 * 0.02
            # result = _result
            # if user.id == 622735873137573894:
            #     result += 5 * 2.54
        return await general.send(language.string("ratings_pickle", user.name, language.number(result, precision=2), language.number(result / 2.54, precision=2)), ctx.channel)

    @commands.command(name="rate")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def rate(self, ctx: commands.Context, *, what: str):
        """ Rate something """
        language = self.bot.language(ctx)
        random.seed(what.lower())
        _max = 100
        r = random.randint(0, _max)
        if what.lower() == "senko":
            r = _max
        return await general.send(language.string("ratings_rate", what, language.number(r), language.number(_max)), ctx.channel)

    @commands.command(name="rateuser")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def rate_user(self, ctx: commands.Context, *, who: discord.User = None):
        """ Rate someone """
        language = self.bot.language(ctx)
        who = who or ctx.author
        random.seed(who.id)
        _max = 100
        r1, r2 = _max // 2, _max
        r = random.randint(r1, r2)
        custom = {
            302851022790066185: 100,  # Me
            self.bot.user.id: 100,    # Suager
            517012611573743621: 100,  # Suager Sentient
        }
        result = custom.get(who.id, r)
        return await general.send(language.string("ratings_rate_user", who.name, language.number(result), language.number(_max)), ctx.channel)

    @commands.command(name="babyrate")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def baby_rate(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Chance of 2 users having a baby """
        language = self.bot.language(ctx)
        if user1 == user2:
            return await general.send(language.string("ratings_baby_rate_self"), ctx.channel)
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            return await general.send(language.string("ratings_baby_rate_suager"), ctx.channel)
        if user1.bot or user2.bot:
            return await general.send(language.string("ratings_baby_rate_bot"), ctx.channel)
        _rate = random.random()
        if user1.id == 302851022790066185 or user2.id == 302851022790066185:
            _rate = 0.00
        rate = language.number(_rate, precision=2, percentage=True)
        return await general.send(language.string("ratings_baby_rate", user1.name, user2.name, rate), ctx.channel)

    @commands.command(name="love", aliases=["lovecalc"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def love_calc(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Calculate the amount of love between 2 users """
        language = self.bot.language(ctx)
        if user1 == user2:
            return await general.send(language.string("ratings_baby_rate_self"), ctx.channel)
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            return await general.send(language.string("ratings_love_calc_suager"), ctx.channel)
        if user1.bot ^ user2.bot:
            return await general.send(language.string("ratings_love_calc_bots"), ctx.channel)
        _rate = random.random()
        if (user1.id == 402238370249441281 and user2.id == 593736085327314954) or (user2.id == 402238370249441281 and user1.id == 593736085327314954):
            _rate = 0.00
        if user1.id == 302851022790066185 or user2.id == 302851022790066185:
            check = user2 if user1.id == 302851022790066185 else user1 if user2.id == 302851022790066185 else ctx.author
            _rate = {
                609423646347231282: 0.875,
                517012611573743621: 0.875,
                291665491221807104: 0.75,
                236884090651934721: 0.50,
                667187968145883146: -1.00,
                402238370249441281: -1.00,
            }.get(check.id, 0.00)
        rate = language.number(_rate, precision=2, percentage=True)
        return await general.send(language.string("ratings_love_calc", user1.name, user2.name, rate), ctx.channel)

    @commands.command(name="friends", aliases=["friendship"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def friend_calc(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Calculate how friendly 2 users are """
        language = self.bot.language(ctx)
        if user1 == user2:
            return await general.send(language.string("ratings_friend_self"), ctx.channel)
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            if not (user1.id == 302851022790066185 or user2.id == 302851022790066185):
                return await general.send(language.string("ratings_friend_suager"), ctx.channel)
        rate = language.number(random.random(), precision=2, percentage=True)
        if user1.id == 302851022790066185 or user2.id == 302851022790066185:
            check = user2 if user1.id == 302851022790066185 else user1 if user2.id == 302851022790066185 else ctx.author  # shouldn't be else-ing anyways
            output = await general.send(f"{emotes.Loading} Checking friendship levels...", ctx.channel)
            # Checks whose ID I'll need to determine our friendship with me.
            friendships = {}
            channel: discord.TextChannel = self.bot.get_channel(817733445156732939)  # Load the friendships channel
            async for message in channel.history(limit=None, oldest_first=True):  # Fetch all messages, just in case it's split
                content: str = message.content
                lines = content.splitlines()
                for line in lines:
                    try:
                        line.replace(",", "")  # Shouldn't be any commas to begin with
                        data = line.split("  #", 1)[0]  # Removes the "comment" from the data
                        user_id, value = data.split(": ")  # Gets the user and value from the format
                        friendships[int(user_id)] = float(value)
                    except ValueError:
                        continue  # Ignore the line with an error
            if check.id in friendships:
                _rate = friendships.get(check.id)
                rate = language.number(_rate, precision=2, percentage=True)
                author = check == ctx.author
                return await output.edit(content=f"{'**You** are' if author else f'**{check.name}** is'} **{rate}** friends with **Regaus**.")
            else:
                # rate = "undefined%"
                author = check == ctx.author
                return await output.edit(content=f"The level of friendship between **{'you' if author else check.name}** and **Regaus** is **unknown**.")
        return await general.send(language.string("ratings_friend", user1.name, user2.name, rate), ctx.channel)

    @commands.command(name="hotcalc", aliases=["hotness", "hot"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def hotness(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check how hot someone is """
        language = self.bot.language(ctx)
        user = who or ctx.author
        random.seed(user.id - 1)
        step1 = random.random()
        custom = {
            302851022790066185: 1.00,    # Regaus
            self.bot.user.id:   1.00,    # Suager
            517012611573743621: 1.00,    # Suager Sentient
            291665491221807104: 1.00,    # Leitoxz
            561164743562493952: 0.00,    # zilla
            402238370249441281: 0.00,    # fake
            667187968145883146: 0.00,    # chocolatt
        }
        rate = custom.get(user.id, step1)
        emote = emotes.SadCat if 0 <= rate < 0.5 else emotes.Pog if 0.5 <= rate < 0.75 else emotes.LewdMegumin
        return await general.send(language.string("ratings_hot", user.name, language.number(rate, precision=2, percentage=True), emote), ctx.channel)

    @commands.command(name="iq")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def iq_test(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check Someone's IQ """
        language = self.bot.language(ctx)
        user = who or ctx.author
        random.seed(user.id + 1)
        iq = random.uniform(50, 150)
        if user.id in [302851022790066185, self.bot.user.id]:
            iq = 150.01
        elif user.id == 746173049174229142:
            iq *= 0.5
        elif user.id == 402238370249441281:
            iq *= 0.33
        # elif user.id == 533680271057354762:
        #     iq = -2147483647.0
        ri = language.number(iq, precision=2)
        return await general.send(language.number("ratings_iq", user.name, ri), ctx.channel)


def setup(bot: bot_data.Bot):
    bot.add_cog(Ratings(bot))
