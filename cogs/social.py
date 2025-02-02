import random

import discord
from discord import app_commands

from utils import bot_data, commands, emotes, general, languages, lists, interactions


def is_broken(something):
    return something == [] or something == lists.error or something == [lists.error]


but_why = "https://cdn.discordapp.com/attachments/610482988123422750/673642028357386241/butwhy.gif"


class Social(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        self.pat, self.hug, self.kiss, self.lick, self.cuddle, self.bite, self.sleepy, self.smell, self.cry, self.slap, self.blush, self.smile, self.high_five, \
            self.poke, self.boop, self.tickle, self.laugh, self.dance, self.smug, self.nibble, self.feed, self.handhold, self.tuck, self.wave = [[lists.error]] * 24
        db_columns = 26
        # noinspection SqlInsertValues
        self.insert = f"INSERT INTO counters VALUES ({'?, ' * (db_columns - 1)}?)"
        self.empty = [0, 0, self.bot.name] + [0] * (db_columns - 3)
        # Locked:      chocolatt,          racc
        self.locked = [667187968145883146, 746173049174229142]
        # Unlocked:      Leitoxz,            Wight
        self.unlocked = [291665491221807104, 505486500314611717]
        # Protected:      Regaus,             Suager,             Suager Sentient,    CobbleBot,          Mizuki
        self.protected = [302851022790066185, 609423646347231282, 517012611573743621, 577608850316853251, 854877153866678333]

    @commands.Cog.listener()
    async def on_ready(self):
        await self.load_images()

    def data_update(self, uid_give: int, uid_receive: int, key: str, ind: int):
        """ Update database - interactions """
        data_giver = self.bot.db.fetchrow("SELECT * FROM counters WHERE uid1=? AND uid2=? AND bot=?", (uid_give, uid_receive, self.bot.name))
        data_receive = self.bot.db.fetchrow("SELECT * FROM counters WHERE uid1=? AND uid2=? AND bot=?", (uid_receive, uid_give, self.bot.name))
        if not data_giver:
            data = self.empty.copy()
            data[0] = uid_give
            data[1] = uid_receive
            data[ind] = 1
            self.bot.db.execute(self.insert, tuple(data))
            number1 = 1
        else:
            n = data_giver[key]
            nu = 1 if n is None else n + 1
            self.bot.db.execute(f"UPDATE counters SET {key}=? WHERE uid1=? AND uid2=? AND bot=?", (nu, uid_give, uid_receive, self.bot.name))
            n2 = data_giver[key]
            number1 = 1 if n2 is None else n2 + 1
        if not data_receive:
            number2 = 0
        else:
            n2 = data_receive[key]
            number2 = 0 if n2 is None else n2
        return number1, number2  # given, received

    @staticmethod
    def get_data(author: discord.Member, target: discord.Member, action: str, language: languages.Language, given: int, received: int):
        # Correct cases
        author_case: str = "nominative"
        target_case: str = "accusative"
        if language.language == "en" and action in ["pat", "feed", "high_five"]:
            target_case = "dative"
        if language.is_in_family("kai", "ka_ne"):
            if action in ["handhold", "wave"]:
                target_case = "genitive"
            elif action in ["feed", "high_five"]:
                target_case = "dative"
                if action == "feed" and given == 1 and received >= 5:  # x finally shared food with y
                    target_case = "genitive"
            elif action == "nsfw_suck" and ((given == 1 and received >= 5) or received == 0):  # x returned y the favour
                target_case = "dative"

        # Get names adapted to the given case
        author_name = general.username(author)
        target_name = general.username(target)
        a1, a2 = language.case(author_name, author_case), language.case(target_name, author_case)
        t1, t2 = language.case(target_name, target_case), language.case(author_name, target_case)

        # Generate title
        title = language.string(f"social_{action}", author=a1, target=t1)

        # Footer line 1: "Author has x'd Target x times"
        counter_diff = given - received  # How many more times the author did the action than the target
        threshold = max((given + received) // 20, 5)  # The difference required for the "only" response to show up: 5% of the sum of the counters (100 each -> diff 10); value has to be at least 5
        if given == 1 and received >= 5:
            # This string is used if the user only did the action for the first time, while the other has done it 5 or more times:
            # "Author has finally x'd Target back"
            footer1 = language.string(f"social_{action}_finally", author=a1, target=t1, frequency=language.frequency(given))
        elif counter_diff <= -threshold:
            # This string is used if the author did the action 5+ times less than the target
            # "Author has only x'd Target x times"
            footer1 = language.string(f"social_{action}_frequency_only", author=a1, target=t1, frequency=language.frequency(given))
        else:
            # Default string: "Author has x'd Target x times"
            footer1 = language.string(f"social_{action}_frequency", author=a1, target=t1, frequency=language.frequency(given))

        # Footer line 2: "Target has x'd Author x times"
        if received == 0:
            # These strings are used if the target has never returned the action to the user
            if given == 1:
                # This is the first time the author did the action
                # "Target has not x'd Author back yet"
                footer2 = language.string(f"social_{action}_never1", author=a2, target=t2)
            elif given in range(2, 5):
                # The author did the action 2, 3, or 4 times
                # "Target has not x'd Author back so far"
                footer2 = language.string(f"social_{action}_never2", author=a2, target=t2)
            else:
                # The author did the action 5 or more times
                # "Target has still not x'd Author back so far"
                footer2 = language.string(f"social_{action}_never5", author=a2, target=t2)
            # footer2 = language.string(f"social_{action}_never", author=a2, target=t2)
        else:
            if counter_diff >= threshold:
                # This string is used if the author did the action 5+ times more than the target
                # "Target has only x'd Author back x times"
                footer2 = language.string(f"social_{action}_frequency_only_back", author=a2, target=t2, frequency=language.frequency(received))
            elif counter_diff <= -threshold:
                # This string is used if the author did the action 5+ times less than the target
                # "Target has x'd Author x times"
                footer2 = language.string(f"social_{action}_frequency", author=a2, target=t2, frequency=language.frequency(received))
            else:
                # Default string: "Target has x'd Author back x times"
                footer2 = language.string(f"social_{action}_frequency_back", author=a2, target=t2, frequency=language.frequency(received))
        return title, f"{footer1}\n{footer2}"

    # Command wrappers for text and slash commands
    async def pat_command(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a pat """
        language = self.bot.language(ctx)
        # TODO: Try to find a way to block these commands from running in a user-install context without Use External Apps permission
        # if ctx.interaction.is_user_integration() and not ctx.permissions.use_external_apps:
        #     raise errors.ExternalAppPermissionRequired()
        if is_broken(self.pat):
            self.pat = await lists.get_images(self.bot, "pat")
        if ctx.author == user:
            return await ctx.send(emotes.Pat13)
        if user.id == self.bot.user.id:
            return await ctx.send(emotes.Hug33)
        if user.bot:
            return await ctx.send(language.string("social_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "pat", 9)
        title, footer = self.get_data(ctx.author, user, "pat", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.pat))
        return await ctx.send(embed=embed)

    async def hug_command(self, ctx: commands.Context, user: discord.Member):
        """ Hug someone """
        language = self.bot.language(ctx)
        if is_broken(self.hug):
            self.hug = await lists.get_images(self.bot, "hug")
        if ctx.author == user:
            return await ctx.send(language.string("social_alone"), embed=discord.Embed(colour=general.random_colour()).set_image(
                url="https://cdn.discordapp.com/attachments/610482988123422750/673641089218904065/selfhug.gif"))
        if user.id == self.bot.user.id:
            return await ctx.send(emotes.Hug29)
        if user.bot:
            return await ctx.send(language.string("social_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "hug", 6)
        title, footer = self.get_data(ctx.author, user, "hug", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.hug))
        return await ctx.send(embed=embed)

    async def cuddle_command(self, ctx: commands.Context, user: discord.Member):
        """ Cuddle someone """
        language = self.bot.language(ctx)
        if is_broken(self.cuddle):
            self.cuddle = await lists.get_images(self.bot, "cuddle")
        if ctx.author == user:
            return await ctx.send(language.string("social_alone"), embed=discord.Embed(colour=general.random_colour()).set_image(
                url="https://cdn.discordapp.com/attachments/610482988123422750/673641089218904065/selfhug.gif"))
        if user.id == self.bot.user.id:
            return await ctx.send(emotes.Hug17)
        if user.bot:
            return await ctx.send(language.string("social_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "cuddle", 4)
        title, footer = self.get_data(ctx.author, user, "cuddle", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.cuddle))
        return await ctx.send(embed=embed)

    async def lick_command(self, ctx: commands.Context, user: discord.Member):
        """ Lick someone """
        language = self.bot.language(ctx)
        if is_broken(self.lick):
            self.lick = await lists.get_images(self.bot, "lick")
        if ctx.author == user:
            return await ctx.send(embed=discord.Embed(colour=general.random_colour()).set_image(
                url="https://cdn.discordapp.com/attachments/610482988123422750/673644219314733106/selflick.gif"))
        if user.id in self.protected and ctx.author.id in self.locked:
            return await ctx.send(language.string("social_forbidden"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_lick_suager"))
        if user.bot:
            return await ctx.send(language.string("social_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "lick", 8)
        title, footer = self.get_data(ctx.author, user, "lick", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.lick))
        return await ctx.send(embed=embed)

    async def kiss_command(self, ctx: commands.Context, user: discord.Member):
        """ Kiss someone """
        language = self.bot.language(ctx)
        if is_broken(self.kiss):
            self.kiss = await lists.get_images(self.bot, "kiss")
        if ctx.channel.id in [725835449502924901, 969720792457822219]:
            choice = lists.kl
        else:
            choice = self.kiss
        if ctx.author == user:
            return await ctx.send(language.string("social_alone"))
        if user.id in self.protected and ctx.author.id in self.locked:
            return await ctx.send(language.string("social_forbidden"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_kiss_suager"))
        if user.bot:
            return await ctx.send(language.string("social_kiss_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "kiss", 7)
        title, footer = self.get_data(ctx.author, user, "kiss", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(choice))
        return await ctx.send(embed=embed)

    async def handhold_command(self, ctx: commands.Context, user: discord.Member):
        """ Hold someone's hand """
        language = self.bot.language(ctx)
        if is_broken(self.handhold):
            self.handhold = await lists.get_images(self.bot, "handhold")
        if ctx.author == user:
            return await ctx.send(language.string("social_handhold_self"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_handhold_suager"))
        if user.id in self.protected and ctx.author.id in self.locked:
            return await ctx.send(language.string("social_forbidden"))
        if user.bot:
            return await ctx.send(language.string("social_handhold_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "handhold", 23)
        title, footer = self.get_data(ctx.author, user, "handhold", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.handhold))
        return await ctx.send(embed=embed)

    async def bite_command(self, ctx: commands.Context, user: discord.Member):
        """ Bite someone """
        language = self.bot.language(ctx)
        if is_broken(self.bite):
            self.bite = await lists.get_images(self.bot, "bite")
        if ctx.author == user:
            return await ctx.send(language.string("social_slap_self"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_slap_suager", author=language.case(general.username(ctx.author), "vocative")))
        if user.id in self.protected and ctx.author.id in self.locked:
            return await ctx.send(language.string("social_forbidden"))
        if user.bot:
            return await ctx.send(language.string("social_slap_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "bite", 3)
        title, footer = self.get_data(ctx.author, user, "bite", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.bite))
        return await ctx.send(embed=embed)

    async def nibble_command(self, ctx: commands.Context, user: discord.Member):
        """ Nibble someone """
        language = self.bot.language(ctx)
        if is_broken(self.nibble):
            self.nibble = await lists.get_images(self.bot, "nibble")
        if ctx.author == user:
            return await ctx.send(language.string("social_nibble_self"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_nibble_suager"))
        if user.id in self.protected and ctx.author.id in self.locked:
            return await ctx.send(language.string("social_forbidden"))
        if user.bot:
            return await ctx.send(language.string("social_nibble_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "nibble", 21)
        title, footer = self.get_data(ctx.author, user, "nibble", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.nibble))
        return await ctx.send(embed=embed)

    async def slap_command(self, ctx: commands.Context, user: discord.Member):
        """ Slap someone """
        language = self.bot.language(ctx)
        if is_broken(self.slap):
            self.slap = await lists.get_images(self.bot, "slap")
        if ctx.author == user:
            return await ctx.send(language.string("social_slap_self"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_slap_suager", author=language.case(general.username(ctx.author), "vocative")))
        # if user.id == 302851022790066185 and ctx.author.id == 236884090651934721:
        #     return await ctx.send(f"{emotes.KannaSpook} How dare you")
        if user.id in self.protected and ctx.author.id in self.locked:
            return await ctx.send(language.string("social_forbidden"))
        if user.bot:
            return await ctx.send(language.string("social_slap_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "slap", 10)
        title, footer = self.get_data(ctx.author, user, "slap", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.slap))
        return await ctx.send(embed=embed)

    async def sniff_command(self, ctx: commands.Context, user: discord.Member):
        """ Sniff someone """
        language = self.bot.language(ctx)
        if is_broken(self.smell):
            self.smell = await lists.get_images(self.bot, "sniff")
        if ctx.author == user:
            return await ctx.send(language.string("social_poke_self"))
        if user.id in self.protected and ctx.author.id in self.locked:
            return await ctx.send(language.string("social_forbidden"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_sniff_suager"))
        if user.bot:
            return await ctx.send(language.string("social_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "sniff", 11)
        title, footer = self.get_data(ctx.author, user, "sniff", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.smell))
        return await ctx.send(embed=embed)

    async def highfive_command(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a high five """
        language = self.bot.language(ctx)
        if is_broken(self.high_five):
            self.high_five = await lists.get_images(self.bot, "highfive")
        if ctx.author == user:
            return await ctx.send(language.string("social_alone"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_high_five_suager", author=language.case(general.username(ctx.author), "high_five")))
        if user.bot:
            return await ctx.send(language.string("social_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "high_five", 5)
        title, footer = self.get_data(ctx.author, user, "high_five", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.high_five))
        return await ctx.send(embed=embed)

    async def feed_command(self, ctx: commands.Context, user: discord.Member):
        """ Feed someone """
        language = self.bot.language(ctx)
        if is_broken(self.feed):
            self.feed = await lists.get_images(self.bot, "feed")
        if ctx.author == user:
            return await ctx.send(language.string("social_feed_self"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_food_suager"))
        if user.id in self.protected and ctx.author.id in self.locked:
            return await ctx.send(language.string("social_forbidden"))
        if user.bot:
            return await ctx.send(language.string("social_food_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "feed", 22)
        title, footer = self.get_data(ctx.author, user, "feed", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.feed))
        return await ctx.send(embed=embed)

    async def poke_command(self, ctx: commands.Context, user: discord.Member):
        """ Poke someone """
        language = self.bot.language(ctx)
        if is_broken(self.poke):
            self.poke = await lists.get_images(self.bot, "poke")
        if ctx.author == user:
            return await ctx.send(language.string("social_poke_self"))
        if user.id in self.protected and ctx.author.id in self.locked:
            return await ctx.send(language.string("social_forbidden"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_poke_suager", author=language.case(general.username(ctx.author), "vocative")))
        if user.bot:
            return await ctx.send(language.string("social_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "poke", 12)
        title, footer = self.get_data(ctx.author, user, "poke", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.poke))
        return await ctx.send(embed=embed)

    async def boop_command(self, ctx: commands.Context, user: discord.Member):
        """ Boop someone """
        language = self.bot.language(ctx)
        if is_broken(self.boop):
            self.boop = await lists.get_images(self.bot, "boop")
        if ctx.author == user:
            return await ctx.send(language.string("social_poke_self"))
        if user.id in self.protected and ctx.author.id in self.locked:
            return await ctx.send(language.string("social_forbidden"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_boop_suager"))
        if user.bot:
            return await ctx.send(language.string("social_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "boop", 13)
        title, footer = self.get_data(ctx.author, user, "boop", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.boop))
        return await ctx.send(embed=embed)

    async def tickle_command(self, ctx: commands.Context, user: discord.Member):
        """ Tickle someone """
        language = self.bot.language(ctx)
        if is_broken(self.tickle):
            self.tickle = await lists.get_images(self.bot, "tickle")
        if ctx.author == user:
            return await ctx.send(language.string("social_poke_self"))
        if user.id in self.protected and ctx.author.id in self.locked:
            return await ctx.send(language.string("social_forbidden"))
        # if user.id in self.protected and ctx.author.id not in self.unlocked:
        #     return await ctx.send(language.string("social_tickle_regaus", author=language.case(ctx.author.name, "vocative")))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_tickle_suager"))
        if user.bot:
            return await ctx.send(language.string("social_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "tickle", 14)
        title, footer = self.get_data(ctx.author, user, "tickle", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.tickle))
        return await ctx.send(embed=embed)

    async def punch_command(self, ctx: commands.Context, user: discord.Member):
        """ Punch someone """
        language = self.bot.language(ctx)
        if ctx.author == user:
            return await ctx.send(language.string("social_slap_self"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_slap_suager", author=language.case(general.username(ctx.author), "vocative")))
        # if user.id == 302851022790066185 and ctx.author.id == 236884090651934721:
        #     return await ctx.send(f"{emotes.KannaSpook} How dare you")
        if user.id in self.protected and ctx.author.id in self.locked:
            return await ctx.send(language.string("social_forbidden"))
        # if user.id in self.protected and ctx.author.id not in self.unlocked:
        #     return await ctx.send(language.string("social_kill_regaus", author=language.case(ctx.author.name, "vocative")))
        if user.bot:
            return await ctx.send(language.string("social_slap_bot"))
        given, received = self.data_update(ctx.author.id, user.id, "punch", 15)
        title, footer = self.get_data(ctx.author, user, "punch", language, given, received)
        return await ctx.send(f"{title}\n{footer}")

    async def tuck_command(self, ctx: commands.Context, user: discord.Member):
        """ Tuck someone into bed """
        language = self.bot.language(ctx)
        if is_broken(self.tuck):
            self.tuck = await lists.get_images(self.bot, "tuck")
        if ctx.author == user:
            return await ctx.send(language.string("social_tuck_self"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_tuck_suager"))
        if user.bot:
            return await ctx.send(language.string("social_tuck_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "tuck", 24)
        title, footer = self.get_data(ctx.author, user, "tuck", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.tuck))
        return await ctx.send(embed=embed)

    async def wave_command(self, ctx: commands.Context, user: discord.Member):
        """ Wave at someone """
        language = self.bot.language(ctx)
        if is_broken(self.wave):
            self.wave = await lists.get_images(self.bot, "wave")
        if ctx.author == user:
            return await ctx.send(language.string("social_wave_self"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_wave_suager"))
        if user.bot:
            return await ctx.send(language.string("social_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "wave", 25)
        title, footer = self.get_data(ctx.author, user, "wave", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.wave))
        return await ctx.send(embed=embed)

    async def bean_command(self, ctx: commands.Context, user: discord.Member):
        """ Bean someone """
        language = self.bot.language(ctx)
        if user == ctx.author:
            return await ctx.send(emotes.Pat13)
        if user.id in self.protected and ctx.author.id in self.locked:
            return await ctx.send(language.string("social_forbidden"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_forbidden"))
        if user.id == ctx.guild.owner.id:
            return await ctx.send(language.string("social_bean_owner"))
        bean = language.string("social_bean", target=general.username(user), server=ctx.guild.name)
        return await ctx.send(bean)

    async def kill_command(self, ctx: commands.Context, user: discord.Member):
        """ Kill someone """
        language = self.bot.language(ctx)
        if ctx.author == user:
            return await ctx.send(language.string("social_slap_self"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_kill_suager", author=language.case(general.username(ctx.author), "vocative")))
        if user.id in self.protected and ctx.author.id not in self.unlocked:
            return await ctx.send(language.string("social_kill_regaus", author=language.case(general.username(ctx.author), "vocative")))
        if user.bot:
            return await ctx.send(language.string("social_slap_bot"))
        # Anti-Kill Insurance: Caffey
        if user.id in [249141823778455552]:
            given, received = self.data_update(ctx.bot.user.id, ctx.author.id, "kill", 18)
            return await ctx.send(language.string("social_kill_insurance", frequency=language.frequency(given)))
        given, received = self.data_update(ctx.author.id, user.id, "kill", 18)
        title, footer = self.get_data(ctx.author, user, "kill", language, given, received)
        return await ctx.send(f"{title}\n{footer}")

    async def sleepy_command(self, ctx: commands.Context):
        """ You are sleepy """
        language = self.bot.language(ctx)
        if is_broken(self.sleepy):
            self.sleepy = await lists.get_images(self.bot, "sleepy")
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_sleepy", author=general.username(ctx.author))
        embed.set_image(url=random.choice(self.sleepy))
        return await ctx.send(embed=embed)

    async def cry_command(self, ctx: commands.Context):
        """ You are crying """
        language = self.bot.language(ctx)
        if is_broken(self.cry):
            self.cry = await lists.get_images(self.bot, "cry")
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_cry", author=general.username(ctx.author))
        embed.set_image(url=random.choice(self.cry))
        return await ctx.send(embed=embed)

    async def blush_command(self, ctx: commands.Context):
        """ You are blushing """
        language = self.bot.language(ctx)
        if is_broken(self.blush):
            self.blush = await lists.get_images(self.bot, "blush")
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_blush", author=general.username(ctx.author))
        embed.set_image(url=random.choice(self.blush))
        return await ctx.send(embed=embed)

    async def smile_command(self, ctx: commands.Context):
        """ You are smile """
        language = self.bot.language(ctx)
        if is_broken(self.smile):
            self.smile = await lists.get_images(self.bot, "smile")
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_smile", author=general.username(ctx.author))
        embed.set_image(url=random.choice(self.smile))
        return await ctx.send(embed=embed)

    async def laugh_command(self, ctx: commands.Context, at: discord.Member):
        """ You are laugh """
        language = self.bot.language(ctx)
        if is_broken(self.laugh):
            self.laugh = await lists.get_images(self.bot, "laugh")
        embed = discord.Embed(colour=general.random_colour())
        embed.set_image(url=random.choice(self.laugh))
        if at is None:
            embed.title = language.string("social_laugh", author=general.username(ctx.author))
        else:
            if at == ctx.author:
                embed.title = language.string("social_laugh_at_self", author=general.username(ctx.author))
            if at.id == self.bot.user.id:
                return await ctx.send(language.string("social_laugh_at_suager"))
            embed.title = language.string("social_laugh_at", author=general.username(ctx.author), target=language.case(general.username(at), "laugh_at"))
        return await ctx.send(embed=embed)

    async def smug_command(self, ctx: commands.Context):
        """ You are smug """
        language = self.bot.language(ctx)
        if is_broken(self.smug):
            self.smug = await lists.get_images(self.bot, "smug")
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_smug", author=general.username(ctx.author))
        embed.set_image(url=random.choice(self.smug))
        return await ctx.send(embed=embed)

    async def dance_command(self, ctx: commands.Context):
        """ You are dancing """
        language = self.bot.language(ctx)
        if is_broken(self.dance):
            self.dance = await lists.get_images(self.bot, "dance")
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_dance", author=general.username(ctx.author))
        embed.set_image(url=random.choice(self.dance))
        return await ctx.send(embed=embed)

    async def food_command(self, ctx: commands.Context, user: discord.Member, emote: str):
        """ Wrapper for commands that give the member something """
        language = self.bot.language(ctx)
        if user == ctx.author:
            return await ctx.send(language.string("social_food_self"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_food_suager"))
        if user.bot:
            return await ctx.send(language.string("social_food_bot"))
        output = language.string("social_food", author=language.case(general.username(ctx.author), "nominative"), target=language.case(general.username(user), "dative"), item=emote)
        return await ctx.send(output)

    async def cookie_command(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a cookie """
        return await self.food_command(ctx, user, "🍪")

    async def lemon_command(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a lemon """
        return await self.food_command(ctx, user, "🍋")

    async def carrot_command(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a carrot """
        return await self.food_command(ctx, user, "🥕")

    async def fruit_command(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a fruit """
        return await self.food_command(ctx, user, random.choice(list("🍏🍎🍐🍊🍌🍉🍇🍓🍒🍍")))

    async def pineapple_command(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a pineapple """
        return await self.food_command(ctx, user, "🍍")

    async def cheese_command(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a cheese """
        return await self.food_command(ctx, user, "🧀")

    async def monkey_command(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a monkey """
        return await self.food_command(ctx, user, "🐒")

    # Actual text- and slash commands
    @commands.command(name="pat", aliases=["pet", "headpat"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_pat(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a headpat """
        return await self.pat_command(ctx, user)

    @commands.command(name="hug")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_hug(self, ctx: commands.Context, user: discord.Member):
        """ Hug someone """
        return await self.hug_command(ctx, user)

    @commands.command(name="cuddle", aliases=["snuggle"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_cuddle(self, ctx: commands.Context, user: discord.Member):
        """ Cuddle someone """
        return await self.cuddle_command(ctx, user)

    @commands.command(name="lick")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_lick(self, ctx: commands.Context, user: discord.Member):
        """ Lick someone """
        return await self.lick_command(ctx, user)

    @commands.command(name="kiss")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_kiss(self, ctx: commands.Context, user: discord.Member):
        """ Kiss someone """
        return await self.kiss_command(ctx, user)

    @commands.command(name="handhold", aliases=["holdhand", "hold", "hand", "hh"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_handhold(self, ctx: commands.Context, user: discord.Member):
        """ Hold someone's hand """
        return await self.handhold_command(ctx, user)

    @commands.command(name="bite")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_bite(self, ctx: commands.Context, user: discord.Member):
        """ Bite someone """
        return await self.bite_command(ctx, user)

    @commands.command(name="nibble", aliases=["nom"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_nibble(self, ctx: commands.Context, user: discord.Member):
        """ Nibble someone """
        return await self.nibble_command(ctx, user)

    @commands.command(name="slap")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_slap(self, ctx: commands.Context, user: discord.Member):
        """ Slap someone """
        return await self.slap_command(ctx, user)

    @commands.command(name="sniff")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_smell(self, ctx: commands.Context, user: discord.Member):
        """ Sniff someone """
        return await self.sniff_command(ctx, user)

    @commands.command(name="highfive")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_high_five(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a high five """
        return await self.highfive_command(ctx, user)

    @commands.command(name="feed")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_feed(self, ctx: commands.Context, user: discord.Member):
        """ Give someone food """
        return await self.feed_command(ctx, user)

    @commands.command(name="poke")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_poke(self, ctx: commands.Context, user: discord.Member):
        """ Poke someone """
        return await self.poke_command(ctx, user)

    @commands.command(name="boop")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_boop(self, ctx: commands.Context, user: discord.Member):
        """ Boop someone """
        return await self.boop_command(ctx, user)

    @commands.command(name="tickle")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_tickle(self, ctx: commands.Context, user: discord.Member):
        """ Tickle someone """
        return await self.tickle_command(ctx, user)

    @commands.command(name="punch")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def text_punch(self, ctx: commands.Context, user: discord.Member):
        """ Punch someone """
        return await self.punch_command(ctx, user)

    @commands.command(name="tuck", aliases=["tuckin"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_tuck(self, ctx: commands.Context, user: discord.Member):
        """ Tuck someone into bed """
        return await self.tuck_command(ctx, user)

    @commands.command(name="wave", aliases=["waveat"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_wave(self, ctx: commands.Context, user: discord.Member):
        """ Wave at someone """
        return await self.wave_command(ctx, user)

    @commands.command(name="bean")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def text_bean(self, ctx: commands.Context, user: discord.Member):
        """ Bean (fake-ban) someone """
        return await self.bean_command(ctx, user)

    @commands.command(name="kill")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def text_kill(self, ctx: commands.Context, user: discord.Member):
        """ Kill someone """
        return await self.kill_command(ctx, user)

    @commands.command(name="sleepy")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_sleepy(self, ctx: commands.Context):
        """ Show that you are sleepy """
        return await self.sleepy_command(ctx)

    @commands.command(name="cry")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_cry(self, ctx: commands.Context):
        """ Show that you are crying """
        return await self.cry_command(ctx)

    @commands.command(name="blush")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_blush(self, ctx: commands.Context):
        """ Show that you are blushing """
        return await self.blush_command(ctx)

    @commands.command(name="smile")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_smile(self, ctx: commands.Context):
        """ Show that you are smiling """
        return await self.smile_command(ctx)

    @commands.command(name="laugh")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def text_laugh(self, ctx: commands.Context, at: discord.Member = None):
        """ Laugh at something or someone """
        return await self.laugh_command(ctx, at)

    @commands.command(name="smug")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def text_smug(self, ctx: commands.Context):
        """ What have you done? """
        return await self.smug_command(ctx)

    @commands.command(name="dance")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def text_dance(self, ctx: commands.Context):
        """ Show that you are dancing """
        return await self.dance_command(ctx)

    @commands.command(name="cookie")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def text_cookie(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a cookie """
        return await self.cookie_command(ctx, user)

    @commands.command(name="lemon")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def text_lemon(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a lemon """
        return await self.lemon_command(ctx, user)

    @commands.command(name="carrot")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def text_carrot(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a carrot """
        return await self.carrot_command(ctx, user)

    @commands.command(name="fruit")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def text_fruit_snacks(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a fruit """
        return await self.fruit_command(ctx, user)

    @commands.command(name="pineapple")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def text_pineapple(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a pineapple """
        return await self.pineapple_command(ctx, user)

    @commands.command(name="cheese")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def text_cheese(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a piece of cheese """
        return await self.cheese_command(ctx, user)

    @commands.command(name="monke", aliases=["monkey"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def text_monkey(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a monke """
        return await self.monkey_command(ctx, user)

    @commands.slash_group(name="social")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def slash_social(self):
        """ Commands for social interactions """
        pass

    @slash_social.command(name="pat")
    @app_commands.describe(member="The member you wish to headpat")
    async def slash_pat(self, interaction: discord.Interaction, member: discord.Member):
        """ Give someone a headpat """
        return await interactions.slash_command(self.pat_command, interaction, member)

    @slash_social.command(name="hug")
    @app_commands.describe(member="The member you wish to hug")
    async def slash_hug(self, interaction: discord.Interaction, member: discord.Member):
        """ Hug someone """
        return await interactions.slash_command(self.hug_command, interaction, member)

    @slash_social.command(name="cuddle")
    @app_commands.describe(member="The member you wish to cuddle")
    async def slash_cuddle(self, interaction: discord.Interaction, member: discord.Member):
        """ Cuddle someone """
        return await interactions.slash_command(self.cuddle_command, interaction, member)

    @slash_social.command(name="lick")
    @app_commands.describe(member="The member you wish to lick")
    async def slash_lick(self, interaction: discord.Interaction, member: discord.Member):
        """ Lick someone """
        return await interactions.slash_command(self.lick_command, interaction, member)

    @slash_social.command(name="kiss")
    @app_commands.describe(member="The member you wish to kiss")
    async def slash_kiss(self, interaction: discord.Interaction, member: discord.Member):
        """ Kiss someone """
        return await interactions.slash_command(self.kiss_command, interaction, member)

    @slash_social.command(name="handhold")
    @app_commands.describe(member="The member whose hand you wish to hold")
    async def slash_handhold(self, interaction: discord.Interaction, member: discord.Member):
        """ Hold someone's hand """
        return await interactions.slash_command(self.handhold_command, interaction, member)

    @slash_social.command(name="bite")
    @app_commands.describe(member="The member you wish to bite")
    async def slash_bite(self, interaction: discord.Interaction, member: discord.Member):
        """ Bite someone """
        return await interactions.slash_command(self.bite_command, interaction, member)

    @slash_social.command(name="nibble")
    @app_commands.describe(member="The member you wish to nibble")
    async def slash_nibble(self, interaction: discord.Interaction, member: discord.Member):
        """ Nibble someone """
        return await interactions.slash_command(self.nibble_command, interaction, member)

    @slash_social.command(name="slap")
    @app_commands.describe(member="The member you wish to slap")
    async def slash_slap(self, interaction: discord.Interaction, member: discord.Member):
        """ Slap someone """
        return await interactions.slash_command(self.slap_command, interaction, member)

    @slash_social.command(name="sniff")
    @app_commands.describe(member="The member you wish to sniff")
    async def slash_sniff(self, interaction: discord.Interaction, member: discord.Member):
        """ Sniff someone """
        return await interactions.slash_command(self.sniff_command, interaction, member)

    @slash_social.command(name="highfive")
    @app_commands.describe(member="The member you wish to give a high five to")
    async def slash_highfive(self, interaction: discord.Interaction, member: discord.Member):
        """ Give someone a high five """
        return await interactions.slash_command(self.highfive_command, interaction, member)

    @slash_social.command(name="feed")
    @app_commands.describe(member="The member you wish to give food to")
    async def slash_feed(self, interaction: discord.Interaction, member: discord.Member):
        """ Give someone food """
        return await interactions.slash_command(self.feed_command, interaction, member)

    @slash_social.command(name="poke")
    @app_commands.describe(member="The member you wish to poke")
    async def slash_poke(self, interaction: discord.Interaction, member: discord.Member):
        """ Poke someone """
        return await interactions.slash_command(self.poke_command, interaction, member)

    @slash_social.command(name="boop")
    @app_commands.describe(member="The member you wish to boop")
    async def slash_boop(self, interaction: discord.Interaction, member: discord.Member):
        """ Boop someone """
        return await interactions.slash_command(self.boop_command, interaction, member)

    @slash_social.command(name="tickle")
    @app_commands.describe(member="The member you wish to tickle")
    async def slash_tickle(self, interaction: discord.Interaction, member: discord.Member):
        """ Tickle someone """
        return await interactions.slash_command(self.tickle_command, interaction, member)

    @slash_social.command(name="punch")
    @app_commands.describe(member="The member you wish to punch")
    async def slash_punch(self, interaction: discord.Interaction, member: discord.Member):
        """ Punch someone """
        return await interactions.slash_command(self.punch_command, interaction, member)

    @slash_social.command(name="tuck")
    @app_commands.describe(member="The member you wish to tuck into bed")
    async def slash_tuck(self, interaction: discord.Interaction, member: discord.Member):
        """ Tuck someone into bed """
        return await interactions.slash_command(self.sniff_command, interaction, member)

    @slash_social.command(name="wave")
    @app_commands.describe(member="The member you wish to wave at")
    async def slash_wave(self, interaction: discord.Interaction, member: discord.Member):
        """ Wave at someone """
        return await interactions.slash_command(self.wave_command, interaction, member)

    @slash_social.command(name="bean")
    @app_commands.describe(member="The member you wish to bean")
    async def slash_bean(self, interaction: discord.Interaction, member: discord.Member):
        """ Bean (fake-ban) someone """
        return await interactions.slash_command(self.bean_command, interaction, member)

    @slash_social.command(name="kill")
    @app_commands.describe(member="The member you wish to kill")
    async def slash_kill(self, interaction: discord.Interaction, member: discord.Member):
        """ Kill someone """
        return await interactions.slash_command(self.kill_command, interaction, member)

    @commands.slash_group(name="emotion")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def slash_emotion(self):
        """ Commands for showing certain emotion by yourself """
        pass

    @slash_emotion.command(name="sleepy")
    async def slash_sleepy(self, interaction: discord.Interaction):
        """ Show that you are sleepy """
        return await interactions.slash_command(self.sleepy_command, interaction)

    @slash_emotion.command(name="cry")
    async def slash_cry(self, interaction: discord.Interaction):
        """ Show that you are crying """
        return await interactions.slash_command(self.cry_command, interaction)

    @slash_emotion.command(name="blush")
    async def slash_blush(self, interaction: discord.Interaction):
        """ Show that you are blushing """
        return await interactions.slash_command(self.blush_command, interaction)

    @slash_emotion.command(name="smile")
    async def slash_smile(self, interaction: discord.Interaction):
        """ Show that you are smiling """
        return await interactions.slash_command(self.smile_command, interaction)

    @slash_emotion.command(name="laugh")
    @app_commands.describe(member="The member you wish to laugh at")
    async def slash_laugh(self, interaction: discord.Interaction, member: discord.Member = None):
        """ Laugh at something or someone """
        return await interactions.slash_command(self.laugh_command, interaction, member)

    @slash_emotion.command(name="smug")
    async def slash_smug(self, interaction: discord.Interaction):
        """ What have you done? """
        return await interactions.slash_command(self.smug_command, interaction)

    @slash_emotion.command(name="dance")
    async def slash_dance(self, interaction: discord.Interaction):
        """ Show that you are dance """
        return await interactions.slash_command(self.dance_command, interaction)

    @commands.slash_group(name="give")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def slash_give(self):
        """ Commands for giving someone something """
        pass

    @slash_give.command(name="cookie")
    @app_commands.describe(member="The member you wish to give a cookie to")
    async def slash_cookie(self, interaction: discord.Interaction, member: discord.Member):
        """ Give someone a cookie """
        return await interactions.slash_command(self.cookie_command, interaction, member)

    @slash_give.command(name="lemon")
    @app_commands.describe(member="The member you wish to give a lemon to")
    async def slash_lemon(self, interaction: discord.Interaction, member: discord.Member):
        """ Give someone a lemon """
        return await interactions.slash_command(self.lemon_command, interaction, member)

    @slash_give.command(name="carrot")
    @app_commands.describe(member="The member you wish to give a carrot to")
    async def slash_carrot(self, interaction: discord.Interaction, member: discord.Member):
        """ Give someone a carrot """
        return await interactions.slash_command(self.carrot_command, interaction, member)

    @slash_give.command(name="fruit")
    @app_commands.describe(member="The member you wish to give a fruit to")
    async def slash_fruit(self, interaction: discord.Interaction, member: discord.Member):
        """ Give someone a fruit """
        return await interactions.slash_command(self.fruit_command, interaction, member)

    @slash_give.command(name="pineapple")
    @app_commands.describe(member="The member you wish to give a pineapple to")
    async def slash_pineapple(self, interaction: discord.Interaction, member: discord.Member):
        """ Give someone a pineapple """
        return await interactions.slash_command(self.pineapple_command, interaction, member)

    @slash_give.command(name="cheese")
    @app_commands.describe(member="The member you wish to give a piece of cheese to")
    async def slash_cheese(self, interaction: discord.Interaction, member: discord.Member):
        """ Give someone a piece of cheese """
        return await interactions.slash_command(self.cheese_command, interaction, member)

    @slash_give.command(name="monke")
    @app_commands.describe(member="The member you wish to give a monke to")
    async def slash_monkey(self, interaction: discord.Interaction, member: discord.Member):
        """ Give someone a monke """
        return await interactions.slash_command(self.monkey_command, interaction, member)

    async def load_images(self):
        """ Load all images, so we won't have to do it during runtime"""
        self.bite      = await lists.get_images(self.bot, "bite")      # noqa: E221
        self.blush     = await lists.get_images(self.bot, "blush")     # noqa: E221
        self.boop      = await lists.get_images(self.bot, "boop")      # noqa: E221
        self.cry       = await lists.get_images(self.bot, "cry")       # noqa: E221
        self.cuddle    = await lists.get_images(self.bot, "cuddle")    # noqa: E221
        self.dance     = await lists.get_images(self.bot, "dance")     # noqa: E221
        self.feed      = await lists.get_images(self.bot, "feed")      # noqa: E221
        self.high_five = await lists.get_images(self.bot, "highfive")  # noqa: E221
        self.hug       = await lists.get_images(self.bot, "hug")       # noqa: E221
        self.kiss      = await lists.get_images(self.bot, "kiss")      # noqa: E221
        self.laugh     = await lists.get_images(self.bot, "laugh")     # noqa: E221
        self.lick      = await lists.get_images(self.bot, "lick")      # noqa: E221
        self.nibble    = await lists.get_images(self.bot, "nibble")    # noqa: E221
        self.pat       = await lists.get_images(self.bot, "pat")       # noqa: E221
        self.poke      = await lists.get_images(self.bot, "poke")      # noqa: E221
        self.slap      = await lists.get_images(self.bot, "slap")      # noqa: E221
        self.sleepy    = await lists.get_images(self.bot, "sleepy")    # noqa: E221
        self.smell     = await lists.get_images(self.bot, "sniff")     # noqa: E221
        self.smile     = await lists.get_images(self.bot, "smile")     # noqa: E221
        self.smug      = await lists.get_images(self.bot, "smug")      # noqa: E221
        self.tickle    = await lists.get_images(self.bot, "tickle")    # noqa: E221
        self.handhold  = await lists.get_images(self.bot, "handhold")  # noqa: E221
        self.tuck      = await lists.get_images(self.bot, "tuck")      # noqa: E221
        self.wave      = await lists.get_images(self.bot, "wave")      # noqa: E221

    @commands.command(name="reloadimages", aliases=["ri"])
    @commands.is_owner()
    async def reload_images(self, ctx: commands.Context):
        """ Reload all images """
        await self.load_images()
        return await ctx.send("Successfully reloaded images")


class SocialSuager(Social, name="Social"):
    async def fuck_command(self, ctx: commands.Context, user: discord.Member):
        """ Have sexual intercourse with someone """
        language = self.bot.language(ctx)
        if user.id in self.protected and ctx.author.id not in self.unlocked:
            return await ctx.send(language.string("social_forbidden"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_nsfw_fuck_suager"))
        if user.bot:
            return await ctx.send(language.string("social_nsfw_fuck_bot"))
        if user == ctx.author:
            return await ctx.send(emotes.UmmOK)
        given, received = self.data_update(ctx.author.id, user.id, "bang", 16)
        title, footer = self.get_data(ctx.author, user, "nsfw_fuck", language, given, received)
        return await ctx.send(f"{title}\n{footer}")

    async def suck_command(self, ctx: commands.Context, user: discord.Member):
        """ Suck someone off """
        language = self.bot.language(ctx)
        if user.id in self.protected and ctx.author.id in self.locked:
            return await ctx.send(language.string("social_forbidden"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_nsfw_fuck_suager"))
        if user.bot:
            return await ctx.send(language.string("social_nsfw_fuck_bot"))
        if user == ctx.author:
            return await ctx.send(emotes.UmmOK)
        given, received = self.data_update(ctx.author.id, user.id, "suck", 17)
        title, footer = self.get_data(ctx.author, user, "nsfw_suck", language, given, received)
        return await ctx.send(f"{title}\n{footer}")

    async def face_fuck_command(self, ctx: commands.Context, user: discord.Member):
        """ Face-fuck someone """
        language = self.bot.language(ctx)
        if user.id in self.protected and ctx.author.id not in self.unlocked:
            return await ctx.send(language.string("social_forbidden"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_nsfw_fuck_suager"))
        if user.bot:
            return await ctx.send(language.string("social_nsfw_fuck_bot"))
        if user == ctx.author:
            return await ctx.send(emotes.UmmOK)
        given, received = self.data_update(ctx.author.id, user.id, "ff", 19)
        title, footer = self.get_data(ctx.author, user, "nsfw_face_fuck", language, given, received)
        return await ctx.send(f"{title}\n{footer}")

    async def threesome_command(self, ctx: commands.Context, user1: discord.Member, user2: discord.Member):
        """ Have a threesome """
        language = ctx.language()
        if user1 == user2:
            return await ctx.send(language.string("social_nsfw_threesome_duplicate"))
        for user in (user1, user2):
            if user.id in self.protected and ctx.author.id not in self.unlocked:
                return await ctx.send(language.string("social_forbidden"))
            if user.id == self.bot.user.id:
                return await ctx.send(language.string("social_nsfw_fuck_suager"))
            if user.bot:
                return await ctx.send(language.string("social_nsfw_fuck_bot"))
            if user == ctx.author:
                return await ctx.send(emotes.UmmOK)
        # No counters for this command, at least currently
        author = language.case(general.username(ctx.author), "nominative")
        target_case = "accusative"
        if language.is_in_family("kai"):  # -> "ka target'n"
            target_case = "genitive"
        elif language.is_in_family("ru"):
            target_case = "instrumental"
        target1 = language.case(general.username(user1), target_case)
        target2 = language.case(general.username(user2), target_case)
        return await ctx.send(language.string("social_nsfw_threesome", author=author, target1=target1, target2=target2))

    @commands.command(name="fuck", aliases=["bang"], nsfw=True)
    @commands.is_nsfw()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def text_fuck(self, ctx: commands.Context, user: discord.Member):
        """ Have sexual intercourse with someone """
        return await self.fuck_command(ctx, user)

    @commands.command(name="suck", nsfw=True)
    @commands.is_nsfw()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def suck(self, ctx: commands.Context, user: discord.Member):
        """ Suck someone off """
        return await self.suck_command(ctx, user)

    @commands.command(name="facefuck", aliases=["ff"], nsfw=True)
    @commands.is_nsfw()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def face_fuck(self, ctx: commands.Context, user: discord.Member):
        """ Face-fuck someone """
        return await self.face_fuck_command(ctx, user)

    @commands.command(name="threesome", nsfw=True)
    @commands.is_nsfw()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def threesome(self, ctx: commands.Context, user1: discord.Member, user2: discord.Member):
        """ Have a threesome with two other people """
        return await self.threesome_command(ctx, user1, user2)

    @commands.slash_group(name="social-nsfw", nsfw=True)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def slash_nsfw(self):
        """ Naughty social interactions """
        pass

    @slash_nsfw.command(name="fuck")
    @app_commands.describe(member="The member you wish to fuck")
    async def slash_fuck(self, interaction: discord.Interaction, member: discord.Member):
        """ Have sexual intercourse with someone """
        return await interactions.slash_command(self.fuck_command, interaction, member)

    @slash_nsfw.command(name="suck")
    @app_commands.describe(member="The member you wish to suck off")
    async def slash_suck(self, interaction: discord.Interaction, member: discord.Member):
        """ Suck someone off """
        return await interactions.slash_command(self.suck_command, interaction, member)

    @slash_nsfw.command(name="facefuck")
    @app_commands.describe(member="The member you wish to face-fuck")
    async def slash_face_fuck(self, interaction: discord.Interaction, member: discord.Member):
        """ Face-fuck someone """
        return await interactions.slash_command(self.face_fuck_command, interaction, member)

    @slash_nsfw.command(name="threesome")
    @app_commands.describe(member1="The first member you wish to have a threesome with", member2="The second member you wish to have a threesome with")
    async def slash_threesome(self, interaction: discord.Interaction, member1: discord.Member, member2: discord.Member):
        """ Have a threesome with two other people """
        return await interactions.slash_command(self.threesome_command, interaction, member1, member2)


async def setup(bot: bot_data.Bot):
    if bot.name == "suager":
        await bot.add_cog(SocialSuager(bot))
    else:
        cog = Social(bot)
        await bot.add_cog(cog)
        bot.remove_command("kill")  # Apparently deleting a command is a Level 10 difficulty task...
        cog.slash_social.remove_command("kill")
