import random

import discord
from discord import app_commands

from utils import bot_data, commands, emotes, interactions
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

    async def pickle_command(self, ctx: commands.Context, user: discord.User = None):
        """ Measure someone's pickle size """
        language = self.bot.language(ctx)
        user = user or ctx.author
        # My bots - don't output a number at all
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("ratings_pickle_suager"))
        elif user.id in self.protected:
            return await ctx.send(language.string("ratings_pickle_suager2"))
        random.seed(user.id + 545148631)  # Achieves maximum trolling
        result = random.uniform(1.27, 25.40)  # Until 2024-02-10: 2.54, 20.32
        # The Length converter uses the value in metres, so we need to divide by 100. Force size to 1 to make sure we get a response as "x cm, x in"
        return await ctx.send(language.string("ratings_pickle", user=username(user), value=language.length(result / 100, precision=2, force_size=1)))

    async def rate_thing_command(self, ctx: commands.Context, item: str):
        """ Rate something """
        language = self.bot.language(ctx)
        random.seed(item.lower())
        r = random.randint(0, 100)
        if item.lower() == "senko":
            r = 100
        return await ctx.send(language.string("ratings_rate", thing=item, value=language.number(r)))

    async def rate_user_command(self, ctx: commands.Context, user: discord.User = None):
        """ Rate someone """
        language = self.bot.language(ctx)
        user = user or ctx.author
        random.seed(user.id)
        r = random.randint(0, 100)
        custom = {
            302851022790066185:  100,  # Me
            self.bot.user.id:    100,  # Suager
            517012611573743621:  100,  # Suager Sentient
            1082073312156459048: 100,  # Wight Apocalypse
        }
        result = custom.get(user.id, r)
        return await ctx.send(language.string("ratings_rate_user", user=username(user), value=language.number(result)))

    async def baby_rate_command(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Rate the chance of two users having a baby """
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

    async def love_calc_command(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Calculate the level of love between two users """
        language = self.bot.language(ctx)
        if user1 == user2:
            return await ctx.send(language.string("ratings_baby_rate_self"))
        # This rejects values where a bot is mentioned together with another bot of mine, but that's something to look at another time
        bots_and_not_me = (user1.id in self.protected and user2.id != 302851022790066185) or (user2.id in self.protected and user1.id != 302851022790066185)
        if bots_and_not_me:
            return await ctx.send(language.string("ratings_love_calc_suager"))
        if (user1.bot ^ user2.bot) and bots_and_not_me:  # Reject if only one of the users is a bot, unless it's a protected member + me
            return await ctx.send(language.string("ratings_love_calc_bots"))
        _rate = random.random()
        if user1.id == 302851022790066185 or user2.id == 302851022790066185:
            other = user1 if user2.id == 302851022790066185 else user2
            _rate = {
                self.bot.user.id:    1.00,  # Suager
                517012611573743621:  1.00,  # Suager Sentient
                1082073312156459048: 0.97,  # Wight Apocalypse
            }.get(other.id, 0.00)
        rate = language.number(_rate, precision=2, percentage=True)
        return await ctx.send(language.string("ratings_love_calc", name1=username(user1), name2=username(user2), value=rate))

    async def friend_calc_command(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Calculate the level of friendship between two users """
        language = self.bot.language(ctx)
        if user1 == user2:
            return await ctx.send(language.string("ratings_friend_self"))
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            if not (user1.id == 302851022790066185 or user2.id == 302851022790066185):
                return await ctx.send(language.string("ratings_friend_suager"))
        _rate = random.random()
        if user1.id == 302851022790066185 or user2.id == 302851022790066185:
            other = user1 if user2.id == 302851022790066185 else user2
            _rate = {
                self.bot.user.id:    1.0000,  # Suager
                517012611573743621:  1.0000,  # Suager Sentient
                1082073312156459048: 0.9750,  # Wight Apocalypse
            }.get(other.id, _rate)
        rate = language.number(_rate, precision=2, percentage=True)
        return await ctx.send(language.string("ratings_friend", name1=username(user1), name2=username(user2), value=rate))

    async def hotness_command(self, ctx: commands.Context, user: discord.User = None):
        """ Check how hot someone is """
        language = self.bot.language(ctx)
        user = user or ctx.author
        random.seed(user.id - 1)
        step1 = random.random()
        custom = {
            self.bot.user.id:    1.00,  # Suager
            517012611573743621:  1.00,  # Suager Sentient
            302851022790066185:  0.95,  # Regaus
            1082073312156459048: 0.95,  # Wight Apocalypse
        }
        rate = custom.get(user.id, step1)
        emote = emotes.SadCat if 0 <= rate < 0.4 else emotes.Pog if 0.4 <= rate < 0.7 else emotes.LewdMegumin
        return await ctx.send(language.string("ratings_hot", user=username(user), value=language.number(rate, precision=2, percentage=True), emote=emote))

    async def iq_test_command(self, ctx: commands.Context, user: discord.User = None):
        """ Check someone's IQ level """
        language = self.bot.language(ctx)
        user = user or ctx.author
        random.seed(user.id + 1)
        iq = random.gauss(100, 15)
        if user.id in self.protected + [302851022790066185]:
            iq = 160
        iq_out = language.number(iq, precision=2)
        return await ctx.send(language.string("ratings_iq", user=username(user), value=iq_out))

    @commands.command(name="pickle")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def text_pickle_size(self, ctx: commands.Context, *, user: discord.User = None):
        """ Measure someone's pickle size """
        return await self.pickle_command(ctx, user)

    @commands.group(name="rate", case_insensitive=True)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def text_rate(self, ctx: commands.Context):
        """ Rate something or someone """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @text_rate.command(name="thing", aliases=["item", "something"])
    async def text_rate_thing(self, ctx: commands.Context, *, thing: str):
        """ Rate something """
        return await self.rate_thing_command(ctx, thing)

    @text_rate.command(name="user", aliases=["member", "person", "someone"])
    async def text_rate_user(self, ctx: commands.Context, *, user: discord.User = None):
        """ Rate someone """
        return await self.rate_user_command(ctx, user)

    @commands.command(name="babyrate")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def text_baby_rate(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Rate the chance of two users having a baby """
        return await self.baby_rate_command(ctx, user1, user2)

    @commands.command(name="love", aliases=["lovecalc"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def text_love_calc(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Calculate the level of love between two users """
        return await self.love_calc_command(ctx, user1, user2)

    @commands.command(name="friends", aliases=["friendship"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def text_friend_calc(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Calculate the level of friendship between two users """
        return await self.friend_calc_command(ctx, user1, user2)

    @commands.command(name="hotness", aliases=["hotcalc", "hot"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def text_hotness(self, ctx: commands.Context, *, user: discord.User = None):
        """ Check how hot someone is """
        return await self.hotness_command(ctx, user)

    @commands.command(name="iq")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def text_iq_test(self, ctx: commands.Context, *, user: discord.User = None):
        """ Check someone's IQ level """
        return await self.iq_test_command(ctx, user)

    @commands.slash_group(name="ratings")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def slash_ratings(self, interaction: discord.Interaction):
        """ Rate things """
        pass

    @slash_ratings.command(name="pickle")
    @app_commands.describe(user="The user whose pickle size you want to check")
    async def slash_pickle(self, interaction: discord.Interaction, user: discord.User = None):
        """ Measure someone's pickle size """
        return await interactions.slash_command(self.pickle_command, interaction, user)

    @slash_ratings.group(name="rate")
    async def slash_rate(self, interaction: discord.Interaction):
        """ Rate something or someone """
        pass

    @slash_rate.command(name="thing")
    @app_commands.describe(thing="The thing you want to rate")
    async def slash_rate_thing(self, interaction: discord.Interaction, thing: str):
        """ Rate something """
        return await interactions.slash_command(self.rate_thing_command, interaction, thing)

    @slash_rate.command(name="user")
    @app_commands.describe(user="The user you want to rate")
    async def slash_rate_user(self, interaction: discord.Interaction, user: discord.User = None):
        """ Rate someone """
        return await interactions.slash_command(self.rate_user_command, interaction, user)

    @slash_ratings.command(name="babyrate")
    @app_commands.describe(user1="The first user to check the chances for", user2="The second user to checking the chances for")
    async def slash_baby_rate(self, interaction: discord.Interaction, user1: discord.User, user2: discord.User):
        """ Rate the chance of two users having a baby """
        return await interactions.slash_command(self.baby_rate_command, interaction, user1, user2)  # type: ignore

    @slash_ratings.command(name="love")
    @app_commands.describe(user1="The first user to check the love rate for", user2="The second user to check the love rate for")
    async def slash_love_calc(self, interaction: discord.Interaction, user1: discord.User, user2: discord.User):
        """ Calculate the level of love between two users """
        return await interactions.slash_command(self.love_calc_command, interaction, user1, user2)  # type: ignore

    @slash_ratings.command(name="friends")
    @app_commands.describe(user1="The first user to check the love rate for", user2="The second user to check the love rate for")
    async def slash_friend_calc(self, interaction: discord.Interaction, user1: discord.User, user2: discord.User):
        """ Calculate the level of friendship between two users """
        return await interactions.slash_command(self.friend_calc_command, interaction, user1, user2)  # type: ignore

    @slash_ratings.command(name="hotness")
    @app_commands.describe(user="The user whose hotness you want to check")
    async def slash_hotness_calc(self, interaction: discord.Interaction, user: discord.User = None):
        """ Check how hot someone is """
        return await interactions.slash_command(self.hotness_command, interaction, user)

    @slash_ratings.command(name="iq")
    @app_commands.describe(user="The user whose IQ you want to check")
    async def slash_iq_calc(self, interaction: discord.Interaction, user: discord.User = None):
        """ Check someone's IQ level """
        return await interactions.slash_command(self.iq_test_command, interaction, user)


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Ratings(bot))
