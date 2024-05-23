import random

import discord

from utils import bot_data, commands, emotes
from utils.general import username


class Ratings(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        # No pickle output: Suager,           CobbleBot,          Mizuki,             Pretender,          Timetables,
        #                 Suager Dev,         CobbleBot Dev,      Mizuki Dev,         Pretender Dev,      Timetables Dev,
        #                 Suager Sentient,    Suager v3,          Mochi (Mizuki 2),   Matsu (Mizuki 3)
        self.protected = [609423646347231282, 577608850316853251, 854877153866678333, 999361135079866398, 1043687546825232498,
                          568149836927467542, 610040320280887296, 854870340189945856, 999493343333593108, 1043688320196169798,
                          517012611573743621, 520042197391769610, 976254020853329961, 976257132963958795]

    @commands.command(name="pickle")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def pickle_size(self, ctx: commands.Context, *, who: discord.User = None):
        """ Measure someone's pickle """
        language = self.bot.language(ctx)
        user = who or ctx.author
        # My bots - don't output a number at all
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("ratings_pickle_suager"))
        elif user.id in self.protected:
            return await ctx.send(language.string("ratings_pickle_suager2"))
        random.seed(user.id + 545148631)  # Achieves maximum trolling
        result = random.uniform(1.27, 25.40)  # Until 2024-02-10: 2.54, 20.32
        # custom = {
        #     self.bot.user.id: 42.0,
        #     302851022790066185: 30.0,
        # }
        # result = custom.get(user.id, _result)
        # The Length converter uses the value in metres, so we need to divide by 100. Force size to 1 to make sure we get a response as "x cm, x in"
        return await ctx.send(language.string("ratings_pickle", user=username(user), value=language.length(result / 100, precision=2, force_size=1)))

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
        return await ctx.send(language.string("ratings_rate_user", user=username(who), value=language.number(result)))

    @commands.command(name="babyrate")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def baby_rate(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Chance of 2 users having a baby """
        language = self.bot.language(ctx)
        if user1 == user2:
            return await ctx.send(language.string("ratings_baby_rate_self"))
        if user1.id in self.protected or user2.id in self.protected:  # This rejects the command for all my bots at once
            return await ctx.send(language.string("ratings_baby_rate_suager"))  # "Don't think about it"
        if user1.bot or user2.bot:
            return await ctx.send(language.string("ratings_baby_rate_bot"))
        _rate = random.random()
        if user1.id == 302851022790066185 or user2.id == 302851022790066185:
            _rate = 0.00
        rate = language.number(_rate, precision=2, percentage=True)
        return await ctx.send(language.string("ratings_baby_rate", name1=username(user1), name2=username(user2), value=rate))

    @commands.command(name="love", aliases=["lovecalc"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def love_calc(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Calculate the amount of love between 2 users """
        # True if one of my bots is mentioned and user2 is not Regaus
        # This rejects values where a bot is mentioned together with another bot of mine, but that's something to look at another time
        bots_and_not_me = (user1.id in self.protected and user2.id != 302851022790066185) or (user2.id in self.protected and user1.id != 302851022790066185)

        language = self.bot.language(ctx)
        if user1 == user2:
            return await ctx.send(language.string("ratings_baby_rate_self"))
        if bots_and_not_me:
            return await ctx.send(language.string("ratings_love_calc_suager"))
        if (user1.bot ^ user2.bot) and bots_and_not_me:  # Reject if only one of the users is a bot, unless it's a protected member + me
            return await ctx.send(language.string("ratings_love_calc_bots"))
        _rate = random.random()
        # if (user1.id == 402238370249441281 and user2.id == 593736085327314954) or (user2.id == 402238370249441281 and user1.id == 593736085327314954):
        #     _rate = 0.00
        if user1.id == 302851022790066185 or user2.id == 302851022790066185:
            check = user2 if user1.id == 302851022790066185 else user1 if user2.id == 302851022790066185 else ctx.author
            _rate = {
                609423646347231282:  1.00,  # Suager
                568149836927467542:  1.00,  # Suager Dev
                520042197391769610:  1.00,  # Suager v3
                517012611573743621:  1.00,  # Suager Sentient
                577608850316853251:  1.00,  # CobbleBot
                610040320280887296:  1.00,  # CobbleBot

                505486500314611717:  0.97,  # Wight's deleted account
                1082073312156459048: 0.97,  # Wight Apocalypse

                291665491221807104:  0.65,  # Leitoxz
                428926748655222794:  0.50,  # Lehti
                236884090651934721:  0.50,  # Miyamura

                999361135079866398:  0.40,  # Pretender
                999493343333593108:  0.40,  # Pretender Dev
                1043687546825232498: 0.40,  # Timetables
                1043688320196169798: 0.40,  # Timetables Dev
                854877153866678333:  0.30,  # Mizuki
                854870340189945856:  0.30,  # Mizuki Dev
                976254020853329961:  0.20,  # Mochi (Mizuki 2)
                976257132963958795:  0.20,  # Matsu (Mizuki 3)

                456237985260765185:  0.17,  # Dyoza
                667187968145883146: -1.00,  # chocolatt
            }.get(check.id, 0.00)
        rate = language.number(_rate, precision=2, percentage=True)
        return await ctx.send(language.string("ratings_love_calc", name1=username(user1), name2=username(user2), value=rate))

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
        # If I'm not mention, return a value normally
        if not (user1.id == 302851022790066185 or user2.id == 302851022790066185):
            return await ctx.send(language.string("ratings_friend", name1=username(user1), name2=username(user2), value=rate))
        check = user2 if user1.id == 302851022790066185 else user1 if user2.id == 302851022790066185 else ctx.author  # shouldn't be else-ing anyways
        author = check == ctx.author
        # output = await ctx.send(f"{emotes.Loading} Checking friendship levels...")
        # Checks whose ID I'll need to determine our friendship with me.
        friendships = {
            609423646347231282:  1.0000,  # Suager
            568149836927467542:  1.0000,  # Suager Dev
            520042197391769610:  1.0000,  # Suager v3
            517012611573743621:  1.0000,  # Suager Sentient
            577608850316853251:  1.0000,  # CobbleBot
            610040320280887296:  1.0000,  # CobbleBot

            505486500314611717:  0.9750,  # Wight's deleted account
            1082073312156459048: 0.9750,  # Wight Apocalypse

            999361135079866398:  0.9000,  # Pretender
            999493343333593108:  0.9000,  # Pretender Dev
            1043687546825232498: 0.9000,  # Timetables
            1043688320196169798: 0.9000,  # Timetables Dev
            854877153866678333:  0.9000,  # Mizuki
            854870340189945856:  0.9000,  # Mizuki Dev
            976254020853329961:  0.8700,  # Mochi (Mizuki 2)
            976257132963958795:  0.8700,  # Matsu (Mizuki 3)

            291665491221807104:  0.8500,  # Leitoxz
            942829514457755738:  0.7250,  # Nova
            236884090651934721:  0.7000,  # Miyamura
            581206591051923466:  0.6700,  # Midnight
            659879737509937152:  0.6700,  # LostCandle
            428926748655222794:  0.6400,  # Lehti
            393401882858487808:  0.5900,  # Kgaim/Micah
            1007129674704498708: 0.5900,  # Rexy
            437348705901871114:  0.5800,  # Halimat

            667187968145883146: -1.0000,  # chocolatt
        }
        # channel = self.bot.get_channel(817733445156732939)  # Load the friendships channel
        # async for message in channel.history(limit=None, oldest_first=True):  # Fetch all messages, just in case it's split
        #     content: str = message.content
        #     lines = content.splitlines()
        #     for line in lines:
        #         try:
        #             line.replace(",", "")  # Shouldn't be any commas to begin with
        #             data = line.split("  #", 1)[0]  # Removes the "comment" from the data
        #             user_id, value = data.split(": ")  # Gets the user and value from the format
        #             friendships[int(user_id)] = float(value)
        #         except ValueError:
        #             continue  # Ignore the line with an error
        other = "you" if author else username(check)
        if check.id in friendships:
            _rate = friendships.get(check.id)
            rate = language.number(_rate, precision=2, percentage=True)
            return await ctx.send(f"The level of friendship between **{other}** and **Regaus** is **{rate}**.")
            # return await output.edit(content=f"{'**You** are' if author else f'**{username(check)}** is'} **{rate}** friends with **Regaus**.")
        else:
            # rate = "undefined%"
            return await ctx.send(f"The level of friendship between **{other}** and **Regaus** is not known to me.")
            # return await output.edit(content=f"The level of friendship between **{'you' if author else username(check)}** and **Regaus** is unknown...")

    @commands.command(name="hotcalc", aliases=["hotness", "hot"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def hotness(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check how hot someone is """
        language = self.bot.language(ctx)
        user = who or ctx.author
        random.seed(user.id - 1)
        step1 = random.random()
        custom = {
            self.bot.user.id:    1.00,  # The bot itself (if happens to not be Suager)
            609423646347231282:  1.00,  # Suager
            568149836927467542:  1.00,  # Suager Dev
            520042197391769610:  1.00,  # Suager v3
            517012611573743621:  1.00,  # Suager Sentient
            577608850316853251:  1.00,  # CobbleBot
            610040320280887296:  1.00,  # CobbleBot
            302851022790066185:  0.95,  # Regaus
            505486500314611717:  0.95,  # Wight's deleted account
            1082073312156459048: 0.95,  # Wight Apocalypse
            291665491221807104:  0.85,  # Leitoxz
            667187968145883146:  0.00,  # chocolatt
        }
        rate = custom.get(user.id, step1)
        emote = emotes.SadCat if 0 <= rate < 0.4 else emotes.Pog if 0.4 <= rate < 0.7 else emotes.LewdMegumin
        return await ctx.send(language.string("ratings_hot", user=username(user), value=language.number(rate, precision=2, percentage=True), emote=emote))

    @commands.command(name="iq")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def iq_test(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check Someone's IQ """
        language = self.bot.language(ctx)
        user = who or ctx.author
        random.seed(user.id + 1)
        iq = random.uniform(50, 150)
        if user.id in self.protected + [302851022790066185]:  # [302851022790066185, self.bot.user.id]:
            iq = 150.01
        # elif user.id == 746173049174229142:
        #     iq *= 0.5
        # elif user.id == 402238370249441281:
        #     iq *= 0.33
        # elif user.id == 533680271057354762:
        #     iq = -2147483647.0
        ri = language.number(iq, precision=2)
        return await ctx.send(language.string("ratings_iq", user=username(user), value=ri))


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Ratings(bot))
