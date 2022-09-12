import random

import discord

from utils import bot_data, commands, emotes


class Ratings(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.command(name="pickle")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def pickle_size(self, ctx: commands.Context, *, who: discord.User = None):
        """ Measure someone's pickle """
        language = self.bot.language(ctx)
        user = who or ctx.author
        # My bots - don't output a numer at all
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("ratings_pickle_suager"))
        elif user.id in [609423646347231282, 577608850316853251, 854877153866678333]:
            return await ctx.send(language.string("ratings_pickle_suager2"))
        random.seed(user.id + 11)  # Gives me desired values
        result = random.uniform(2.54, 20.32)
        # custom = {
        #     self.bot.user.id: 42.0,
        #     302851022790066185: 30.0,
        # }
        # result = custom.get(user.id, _result)
        return await ctx.send(language.string("ratings_pickle", user=user.name, value=language.length(result / 100, precision=2, force_size=1)))  # The Length converter uses the value in metres

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
        return await ctx.send(language.string("ratings_rate", thing=what, value=language.number(r)))

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
        return await ctx.send(language.string("ratings_rate_user", user=who.name, value=language.number(result)))

    @commands.command(name="babyrate")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def baby_rate(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Chance of 2 users having a baby """
        language = self.bot.language(ctx)
        if user1 == user2:
            return await ctx.send(language.string("ratings_baby_rate_self"))
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            return await ctx.send(language.string("ratings_baby_rate_suager"))
        if user1.bot or user2.bot:
            return await ctx.send(language.string("ratings_baby_rate_bot"))
        _rate = random.random()
        if user1.id == 302851022790066185 or user2.id == 302851022790066185:
            _rate = 0.00
        rate = language.number(_rate, precision=2, percentage=True)
        return await ctx.send(language.string("ratings_baby_rate", name1=user1.name, name2=user2.name, value=rate))

    @commands.command(name="love", aliases=["lovecalc"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def love_calc(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Calculate the amount of love between 2 users """
        language = self.bot.language(ctx)
        if user1 == user2:
            return await ctx.send(language.string("ratings_baby_rate_self"))
        if (user1.id == self.bot.user.id and user2.id != 302851022790066185) or (user2.id == self.bot.user.id and user1.id != 302851022790066185):
            return await ctx.send(language.string("ratings_love_calc_suager"))
        if user1.bot ^ user2.bot:
            return await ctx.send(language.string("ratings_love_calc_bots"))
        _rate = random.random()
        # if (user1.id == 402238370249441281 and user2.id == 593736085327314954) or (user2.id == 402238370249441281 and user1.id == 593736085327314954):
        #     _rate = 0.00
        if user1.id == 302851022790066185 or user2.id == 302851022790066185:
            check = user2 if user1.id == 302851022790066185 else user1 if user2.id == 302851022790066185 else ctx.author
            _rate = {
                609423646347231282: 0.875,
                517012611573743621: 0.875,
                577608850316853251: 0.85,
                505486500314611717: 0.80,
                291665491221807104: 0.65,
                236884090651934721: 0.50,
                667187968145883146: -1.00,
            }.get(check.id, 0.00)
        rate = language.number(_rate, precision=2, percentage=True)
        return await ctx.send(language.string("ratings_love_calc", name1=user1.name, name2=user2.name, value=rate))

    @commands.command(name="friends", aliases=["friendship"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def friend_calc(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Calculate how friendly 2 users are """
        language = self.bot.language(ctx)
        if user1 == user2:
            return await ctx.send(language.string("ratings_friend_self"))
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            if not (user1.id == 302851022790066185 or user2.id == 302851022790066185):
                return await ctx.send(language.string("ratings_friend_suager"))
        rate = language.number(random.random(), precision=2, percentage=True)
        if user1.id == 302851022790066185 or user2.id == 302851022790066185:
            check = user2 if user1.id == 302851022790066185 else user1 if user2.id == 302851022790066185 else ctx.author  # shouldn't be else-ing anyways
            output = await ctx.send(f"{emotes.Loading} Checking friendship levels...")
            # Checks whose ID I'll need to determine our friendship with me.
            friendships = {}
            channel = self.bot.get_channel(817733445156732939)  # Load the friendships channel
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
                return await output.edit(content=f"The level of friendship between **{'you' if author else check.name}** and **Regaus** is unknown...")
        return await ctx.send(language.string("ratings_friend", name1=user1.name, name2=user2.name, value=rate))

    @commands.command(name="hotcalc", aliases=["hotness", "hot"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def hotness(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check how hot someone is """
        language = self.bot.language(ctx)
        user = who or ctx.author
        random.seed(user.id - 1)
        step1 = random.random()
        custom = {
            self.bot.user.id:   1.00,    # Suager
            517012611573743621: 1.00,    # Suager Sentient
            302851022790066185: 0.95,    # Regaus
            291665491221807104: 0.85,    # Leitoxz
            505486500314611717: 0.85,    # Wight
            667187968145883146: 0.00,    # chocolatt
        }
        rate = custom.get(user.id, step1)
        emote = emotes.SadCat if 0 <= rate < 0.5 else emotes.Pog if 0.5 <= rate < 0.75 else emotes.LewdMegumin
        return await ctx.send(language.string("ratings_hot", user=user.name, value=language.number(rate, precision=2, percentage=True), emote=emote))

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
        return await ctx.send(language.string("ratings_iq", user=user.name, value=ri))


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Ratings(bot))
