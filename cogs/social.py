import random

import discord

from utils import bot_data, commands, emotes, general, languages, lists


def is_broken(something):
    return something == [] or something == lists.error or something == [lists.error]


but_why = "https://cdn.discordapp.com/attachments/610482988123422750/673642028357386241/butwhy.gif"


def get_data(author: discord.Member, target: discord.Member, action: str, language: languages.Language, given: int, received: int):
    # Correct cases
    author_case: str = "nominative"
    target_case: str = "accusative"
    if language.language == "en" and action in ["pat", "feed", "high_five"]:
        target_case = "dative"
    if language.is_in_family("ka_wk"):
        if action in ["handhold"]:
            target_case = "genitive"
        elif action in ["feed", "high_five"]:
            target_case = "dative"

    # Get names adapted to the given case
    a1, a2 = language.case(author.name, author_case), language.case(target.name, author_case)
    t1, t2 = language.case(target.name, target_case), language.case(author.name, target_case)

    # Generate title
    title = language.string(f"social_{action}", author=a1, target=t1)

    # Footer line 1: "Author has x'd Target x times"
    if given > 0:
        footer1 = language.string(f"social_{action}_frequency", author=a1, target=t1, frequency=language.frequency(given))
    else:
        footer1 = language.string(f"social_{action}_never", author=a1, target=t1)

    # Footer line 2: "Target has x'd Author x times"
    if received > 0:
        footer2 = language.string(f"social_{action}_frequency", author=a2, target=t2, frequency=language.frequency(received))
    else:
        footer2 = language.string(f"social_{action}_never", author=a2, target=t2)
    return title, f"{footer1}\n{footer2}"


class Social(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        self.pat, self.hug, self.kiss, self.lick, self.cuddle, self.bite, self.sleepy, self.smell, self.cry, self.slap, self.blush, self.smile, self.high_five, \
            self.poke, self.boop, self.tickle, self.laugh, self.dance, self.smug, self.nibble, self.feed, self.handhold, self.tuck = [lists.error] * 23
        db_columns = 25
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

    @commands.command(name="pat", aliases=["pet"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def pat(self, ctx: commands.Context, user: discord.Member):
        """ Pat someone """
        language = self.bot.language(ctx)
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
        title, footer = get_data(ctx.author, user, "pat", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.pat))
        return await ctx.send(embed=embed)

    @commands.command(name="hug")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def hug(self, ctx: commands.Context, user: discord.Member):
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
        title, footer = get_data(ctx.author, user, "hug", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.hug))
        return await ctx.send(embed=embed)

    @commands.command(name="cuddle", aliases=["snuggle"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def cuddle(self, ctx: commands.Context, user: discord.Member):
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
        title, footer = get_data(ctx.author, user, "cuddle", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.cuddle))
        return await ctx.send(embed=embed)

    @commands.command(name="lick", aliases=["licc"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def lick(self, ctx: commands.Context, user: discord.Member):
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
        title, footer = get_data(ctx.author, user, "lick", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.lick))
        return await ctx.send(embed=embed)

    @commands.command(name="kiss")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def kiss(self, ctx: commands.Context, user: discord.Member):
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
        title, footer = get_data(ctx.author, user, "kiss", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(choice))
        return await ctx.send(embed=embed)

    @commands.command(name="handhold", aliases=["holdhand", "hold", "hand", "hh"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def handhold(self, ctx: commands.Context, user: discord.Member):
        """ Hold someone's hands """
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
        title, footer = get_data(ctx.author, user, "handhold", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.handhold))
        return await ctx.send(embed=embed)

    @commands.command(name="bite")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def bite(self, ctx: commands.Context, user: discord.Member):
        """ Bite someone """
        language = self.bot.language(ctx)
        if is_broken(self.bite):
            self.bite = await lists.get_images(self.bot, "bite")
        if ctx.author == user:
            return await ctx.send(language.string("social_slap_self"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_slap_suager", author=language.case(ctx.author.name, "vocative")))
        if user.id in self.protected and ctx.author.id in self.locked:
            return await ctx.send(language.string("social_forbidden"))
        if user.bot:
            return await ctx.send(language.string("social_slap_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "bite", 3)
        title, footer = get_data(ctx.author, user, "bite", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.bite))
        return await ctx.send(embed=embed)

    @commands.command(name="nibble", aliases=["nom"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def nibble(self, ctx: commands.Context, user: discord.Member):
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
        title, footer = get_data(ctx.author, user, "nibble", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.nibble))
        return await ctx.send(embed=embed)

    @commands.command(name="slap")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def slap(self, ctx: commands.Context, user: discord.Member):
        """ Slap someone """
        language = self.bot.language(ctx)
        if is_broken(self.slap):
            self.slap = await lists.get_images(self.bot, "slap")
        if ctx.author == user:
            return await ctx.send(language.string("social_slap_self"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_slap_suager", author=language.case(ctx.author.name, "vocative")))
        # if user.id == 302851022790066185 and ctx.author.id == 236884090651934721:
        #     return await ctx.send(f"{emotes.KannaSpook} How dare you")
        if user.id in self.protected and ctx.author.id in self.locked:
            return await ctx.send(language.string("social_forbidden"))
        if user.bot:
            return await ctx.send(language.string("social_slap_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "slap", 10)
        title, footer = get_data(ctx.author, user, "slap", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.slap))
        return await ctx.send(embed=embed)

    @commands.command(name="sniff")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def smell(self, ctx: commands.Context, user: discord.Member):
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
        title, footer = get_data(ctx.author, user, "sniff", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.smell))
        return await ctx.send(embed=embed)

    @commands.command(name="highfive")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def high_five(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a high five """
        language = self.bot.language(ctx)
        if is_broken(self.high_five):
            self.high_five = await lists.get_images(self.bot, "highfive")
        if ctx.author == user:
            return await ctx.send(language.string("social_alone"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_high_five_suager", author=language.case(ctx.author.name, "high_five")))
        if user.bot:
            return await ctx.send(language.string("social_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "high_five", 5)
        title, footer = get_data(ctx.author, user, "high_five", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.high_five))
        return await ctx.send(embed=embed)

    @commands.command(name="feed")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def feed(self, ctx: commands.Context, user: discord.Member):
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
        title, footer = get_data(ctx.author, user, "feed", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.feed))
        return await ctx.send(embed=embed)

    @commands.command(name="poke")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def poke(self, ctx: commands.Context, user: discord.Member):
        """ Poke someone """
        language = self.bot.language(ctx)
        if is_broken(self.poke):
            self.poke = await lists.get_images(self.bot, "poke")
        if ctx.author == user:
            return await ctx.send(language.string("social_poke_self"))
        if user.id in self.protected and ctx.author.id in self.locked:
            return await ctx.send(language.string("social_forbidden"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_poke_suager", author=language.case(ctx.author.name, "vocative")))
        if user.bot:
            return await ctx.send(language.string("social_bot"))
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "poke", 12)
        title, footer = get_data(ctx.author, user, "poke", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.poke))
        return await ctx.send(embed=embed)

    @commands.command(name="boop")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def boop(self, ctx: commands.Context, user: discord.Member):
        """ Why is this a thing? """
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
        title, footer = get_data(ctx.author, user, "boop", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.boop))
        return await ctx.send(embed=embed)

    @commands.command(name="tickle")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def tickle(self, ctx: commands.Context, user: discord.Member):
        """ How dare you """
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
        title, footer = get_data(ctx.author, user, "tickle", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.tickle))
        return await ctx.send(embed=embed)

    @commands.command(name="punch")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def punch(self, ctx: commands.Context, user: discord.Member):
        """ Punch someone """
        language = self.bot.language(ctx)
        if ctx.author == user:
            return await ctx.send(language.string("social_slap_self"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_slap_suager", author=language.case(ctx.author.name, "vocative")))
        # if user.id == 302851022790066185 and ctx.author.id == 236884090651934721:
        #     return await ctx.send(f"{emotes.KannaSpook} How dare you")
        if user.id in self.protected and ctx.author.id in self.locked:
            return await ctx.send(language.string("social_forbidden"))
        # if user.id in self.protected and ctx.author.id not in self.unlocked:
        #     return await ctx.send(language.string("social_kill_regaus", author=language.case(ctx.author.name, "vocative")))
        if user.bot:
            return await ctx.send(language.string("social_slap_bot"))
        given, received = self.data_update(ctx.author.id, user.id, "punch", 15)
        title, footer = get_data(ctx.author, user, "punch", language, given, received)
        return await ctx.send(f"{title}\n{footer}")

    @commands.command(name="tuck", aliases=["tuckin"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def tuck(self, ctx: commands.Context, user: discord.Member):
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
        title, footer = get_data(ctx.author, user, "tuck", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.tuck))
        return await ctx.send(embed=embed)

    @commands.command(name="sleepy")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def sleepy(self, ctx: commands.Context):
        """ You're sleepy """
        language = self.bot.language(ctx)
        if is_broken(self.sleepy):
            self.sleepy = await lists.get_images(self.bot, "sleepy")
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_sleepy", author=ctx.author.name)
        embed.set_image(url=random.choice(self.sleepy))
        return await ctx.send(embed=embed)

    @commands.command(name="cry")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def cry(self, ctx: commands.Context):
        """ You're crying """
        language = self.bot.language(ctx)
        if is_broken(self.cry):
            self.cry = await lists.get_images(self.bot, "cry")
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_cry", author=ctx.author.name)
        embed.set_image(url=random.choice(self.cry))
        return await ctx.send(embed=embed)

    @commands.command(name="blush")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def blush(self, ctx: commands.Context):
        """ You blush """
        language = self.bot.language(ctx)
        if is_broken(self.blush):
            self.blush = await lists.get_images(self.bot, "blush")
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_blush", author=ctx.author.name)
        embed.set_image(url=random.choice(self.blush))
        return await ctx.send(embed=embed)

    @commands.command(name="smile")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def smile(self, ctx: commands.Context):
        """ You're smiling """
        language = self.bot.language(ctx)
        if is_broken(self.smile):
            self.smile = await lists.get_images(self.bot, "smile")
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_smile", author=ctx.author.name)
        embed.set_image(url=random.choice(self.smile))
        return await ctx.send(embed=embed)

    @commands.command(name="laugh")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def laugh(self, ctx: commands.Context, at: discord.User = None):
        """ Haha funny """
        language = self.bot.language(ctx)
        if is_broken(self.laugh):
            self.laugh = await lists.get_images(self.bot, "laugh")
        embed = discord.Embed(colour=general.random_colour())
        embed.set_image(url=random.choice(self.laugh))
        if at is None:
            embed.title = language.string("social_laugh", author=ctx.author.name)
        else:
            if at == ctx.author:
                embed.title = language.string("social_laugh_at_self", author=ctx.author.name)
            if at.id == self.bot.user.id:
                return await ctx.send(language.string("social_laugh_at_suager"))
            embed.title = language.string("social_laugh_at", author=ctx.author.name, target=language.case(at.name, "laugh_at"))
        return await ctx.send(embed=embed)

    @commands.command(name="smug")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def smug(self, ctx: commands.Context):
        """ What have you done """
        language = self.bot.language(ctx)
        if is_broken(self.smug):
            self.smug = await lists.get_images(self.bot, "smug")
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_smug", author=ctx.author.name)
        embed.set_image(url=random.choice(self.smug))
        return await ctx.send(embed=embed)

    @commands.command(name="dance")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def dance(self, ctx: commands.Context):
        """ You're dancing """
        language = self.bot.language(ctx)
        if is_broken(self.dance):
            self.dance = await lists.get_images(self.bot, "dance")
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_dance", author=ctx.author.name)
        embed.set_image(url=random.choice(self.dance))
        return await ctx.send(embed=embed)

    @commands.command(name="bean")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def bean(self, ctx: commands.Context, user: discord.Member):
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
        bean = language.string("social_bean", target=user.name, server=ctx.guild.name)
        return await ctx.send(bean)

    async def food_command(self, ctx: commands.Context, user: discord.Member, emote: str, language: languages.Language):
        if user == ctx.author:
            return await ctx.send(language.string("social_food_self"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_food_suager"))
        if user.bot:
            return await ctx.send(language.string("social_food_bot"))
        output = language.string("social_food", author=language.case(ctx.author.name, "nominative"), target=language.case(user.name, "dative"), item=emote)
        return await ctx.send(output)

    @commands.command(name="cookie")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def cookie(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a cookie """
        language = self.bot.language(ctx)
        return await self.food_command(ctx, user, "🍪", language)

    @commands.command(name="lemon")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def lemon(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a lemon """
        language = self.bot.language(ctx)
        return await self.food_command(ctx, user, "🍋", language)

    @commands.command(name="carrot")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def carrot(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a carrot """
        language = self.bot.language(ctx)
        return await self.food_command(ctx, user, "🥕", language)

    @commands.command(name="fruit")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def fruit_snacks(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a fruit """
        language = self.bot.language(ctx)
        return await self.food_command(ctx, user, random.choice(list("🍏🍎🍐🍊🍌🍉🍇🍓🍒🍍")), language)

    @commands.command(name="pineapple")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def pineapple(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a pineapple """
        language = self.bot.language(ctx)
        return await self.food_command(ctx, user, "🍍", language)

    @commands.command(name="cheese")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def cheese(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a piece of cheese """
        language = self.bot.language(ctx)
        return await self.food_command(ctx, user, "🧀", language)

    @commands.command(name="monke", aliases=["monkey"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def monkey(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a monke """
        language = self.bot.language(ctx)
        return await self.food_command(ctx, user, "🐒", language)

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

    @commands.command(name="reloadimages", aliases=["ri"])
    @commands.is_owner()
    async def reload_images(self, ctx: commands.Context):
        """ Reload all images """
        await self.load_images()
        return await ctx.send("Successfully reloaded images")


class SocialSuager(Social, name="Social"):
    @commands.command(name="kill")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def kill(self, ctx: commands.Context, user: discord.Member):
        """ Kill someone """
        language = self.bot.language(ctx)
        if ctx.author == user:
            return await ctx.send(language.string("social_slap_self"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_kill_suager", author=language.case(ctx.author.name, "vocative")))
        if user.id in self.protected and ctx.author.id not in self.unlocked:
            return await ctx.send(language.string("social_kill_regaus", author=language.case(ctx.author.name, "vocative")))
        # Anti-Kill Insurance: Caffey
        if user.id in [249141823778455552]:
            given, received = self.data_update(ctx.bot.user.id, ctx.author.id, "kill", 18)
            return await ctx.send(language.string("social_kill_insurance", frequency=language.frequency(given)))
        if user.bot:
            return await ctx.send(language.string("social_slap_bot"))
        given, received = self.data_update(ctx.author.id, user.id, "kill", 18)
        title, footer = get_data(ctx.author, user, "kill", language, given, received)
        return await ctx.send(f"{title}\n{footer}")

    @commands.command(name="bang", aliases=["fuck"])
    @commands.guild_only()
    @commands.is_nsfw()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def fuck(self, ctx: commands.Context, user: discord.Member):
        """ Bang someone """
        language = self.bot.language(ctx)
        if user.id in self.protected and ctx.channel.id != 764528556507922442:
            return await ctx.send(language.string("social_forbidden"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_bang_suager"))
        if user.bot:
            return await ctx.send(language.string("social_bang_bot"))
        if user == ctx.author:
            return await ctx.send(emotes.UmmOK)
        given, received = self.data_update(ctx.author.id, user.id, "bang", 16)
        title, footer = get_data(ctx.author, user, "bang", language, given, received)
        return await ctx.send(f"{title}\n{footer}")

    @commands.command(name="suck", aliases=["succ"])
    @commands.guild_only()
    @commands.is_nsfw()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def suck(self, ctx: commands.Context, user: discord.Member):
        """ Suck someone off """
        language = self.bot.language(ctx)
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_bang_suager"))
        if user.bot:
            return await ctx.send(language.string("social_bang_bot"))
        if user.id in self.protected and ctx.author.id in self.locked:
            return await ctx.send(language.string("social_forbidden"))
        if user == ctx.author:
            return await ctx.send(emotes.UmmOK)
        given, received = self.data_update(ctx.author.id, user.id, "suck", 17)
        t1, t2 = ctx.author.name, user.name
        _given, _received = language.frequency(given), language.frequency(received)
        return await ctx.send(f"**{t1}** is now sucking **{t2}** off...\n{t1} did that to {t2} {_given}\n{t2} did that to {t1} {_received}")

    @commands.command(name="facefuck", aliases=["ff"])
    @commands.guild_only()
    @commands.is_nsfw()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def face_fuck(self, ctx: commands.Context, user: discord.User):
        """ Face-fuck someone """
        language = self.bot.language(ctx)
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("social_bang_suager"))
        if user.bot:
            return await ctx.send(language.string("social_bang_bot"))
        if user == ctx.author:
            return await ctx.send(emotes.UmmOK)
        if user.id in self.protected and ctx.channel.id != 764528556507922442:
            return await ctx.send(language.string('social_forbidden'))
        given, received = self.data_update(ctx.author.id, user.id, "ff", 19)
        t1, t2 = ctx.author.name, user.name
        _given, _received = language.frequency(given), language.frequency(received)
        return await ctx.send(f"**{t1}** is now face-fucking **{t2}**...\n{t1} face-fucked {t2} {_given}\n{t2} face-fucked {t1} {_received}")


async def setup(bot: bot_data.Bot):
    if bot.name == "suager":
        await bot.add_cog(SocialSuager(bot))
    else:
        await bot.add_cog(Social(bot))
