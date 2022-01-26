import random

import discord
from discord.ext import commands

from utils import bot_data, emotes, general, languages, lists


def is_fucked(something):
    return something == [] or something == lists.error or something == [lists.error]


but_why = "https://cdn.discordapp.com/attachments/610482988123422750/673642028357386241/butwhy.gif"


def give(author: str, target: str, emote: str, language: languages.Language) -> str:
    return language.string("social_food", author=language.case(author, "nominative"), target=language.case(target, "dative"), item=emote)


def get_data(author: discord.Member, target: discord.Member, action: str, language: languages.Language, given: int, received: int):
    # _given, _received = language.plural(given, "generic_times"), language.plural(received, "generic_times")
    a1, a2 = language.case(author.name, "nominative"), language.case(target.name, "nominative")
    t1, t2 = language.case(target.name, "accusative"), language.case(author.name, "accusative")
    title = language.string(f"social_{action}", author=a1, target=t1)
    if given > 0:
        footer1 = language.string(f"social_{action}_frequency", author=a1, target=t1, frequency=language.frequency(given))
    else:
        footer1 = language.string(f"social_{action}_never", author=a1, target=t1)
    if received > 0:
        footer2 = language.string(f"social_{action}_frequency", author=a2, target=t2, frequency=language.frequency(received))
    else:
        footer2 = language.string(f"social_{action}_never", author=a2, target=t2)
    return title, f"{footer1}\n{footer2}"


class Social(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        self.pat, self.hug, self.kiss, self.lick, self.cuddle, self.bite, self.sleepy, self.smell, self.cry, self.slap, self.blush, self.smile, self.high_five, \
            self.poke, self.boop, self.tickle, self.laugh, self.dance = [lists.error] * 18
        self.insert = f"INSERT INTO counters VALUES ({'?, ' * 19}?)"
        self.empty = [0] * 20
        self.locked = [667187968145883146, 746173049174229142]
        self.unlocked = [291665491221807104]

    def data_update(self, uid_give: int, uid_receive: int, key: str, ind: int):
        """ Update database - interactions """
        data_giver = self.bot.db.fetchrow("SELECT * FROM counters WHERE uid1=? AND uid2=?", (uid_give, uid_receive))
        data_receive = self.bot.db.fetchrow("SELECT * FROM counters WHERE uid1=? AND uid2=?", (uid_receive, uid_give))
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
            self.bot.db.execute(f"UPDATE counters SET {key}=? WHERE uid1=? AND uid2=?", (nu, uid_give, uid_receive))
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
        if is_fucked(self.pat):
            self.pat = await lists.get_images(self.bot, 'p')
        if ctx.author == user:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(emotes.AlexHeart, ctx.channel)
        if user.bot:
            return await general.send(language.string("social_bot"), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "pat", 9)
        title, footer = get_data(ctx.author, user, "pat", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.pat))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="hug")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def hug(self, ctx: commands.Context, user: discord.Member):
        """ Hug someone """
        language = self.bot.language(ctx)
        if is_fucked(self.hug):
            self.hug = await lists.get_images(self.bot, 'h')
        if ctx.author == user:
            return await general.send(language.string("social_alone"), ctx.channel, embed=discord.Embed(colour=general.random_colour()).set_image(
                url="https://cdn.discordapp.com/attachments/610482988123422750/673641089218904065/selfhug.gif"))
        if user.id == self.bot.user.id:
            return await general.send(emotes.AlexHeart, ctx.channel)
        if user.bot:
            return await general.send(language.string("social_bot"), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "hug", 6)
        title, footer = get_data(ctx.author, user, "hug", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.hug))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="cuddle", aliases=["snuggle"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def cuddle(self, ctx: commands.Context, user: discord.Member):
        """ Cuddle someone """
        language = self.bot.language(ctx)
        if is_fucked(self.cuddle):
            self.cuddle = await lists.get_images(self.bot, 'c')
        if ctx.author == user:
            return await general.send(language.string("social_alone"), ctx.channel, embed=discord.Embed(colour=general.random_colour()).set_image(
                url="https://cdn.discordapp.com/attachments/610482988123422750/673641089218904065/selfhug.gif"))
        if user.id == self.bot.user.id:
            return await general.send(emotes.AlexHeart, ctx.channel)
        if user.bot:
            return await general.send(language.string("social_bot"), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "cuddle", 4)
        title, footer = get_data(ctx.author, user, "cuddle", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.cuddle))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="lick", aliases=["licc"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def lick(self, ctx: commands.Context, user: discord.Member):
        """ Lick someone """
        language = self.bot.language(ctx)
        if is_fucked(self.lick):
            self.lick = await lists.get_images(self.bot, 'l')
        if ctx.author == user:
            return await general.send(None, ctx.channel, embed=discord.Embed(colour=general.random_colour()).set_image(
                url="https://cdn.discordapp.com/attachments/610482988123422750/673644219314733106/selflick.gif"))
        if user.id == 302851022790066185 and ctx.author.id in self.locked:
            return await general.send(language.string("social_forbidden"), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(language.string("social_lick_suager"), ctx.channel)
        if user.bot:
            return await general.send(language.string("social_bot"), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "lick", 8)
        title, footer = get_data(ctx.author, user, "lick", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.lick))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="kiss")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def kiss(self, ctx: commands.Context, user: discord.Member):
        """ Kiss someone """
        language = self.bot.language(ctx)
        if is_fucked(self.kiss):
            self.kiss = await lists.get_images(self.bot, 'k')
        if ctx.channel.id == 725835449502924901:
            choice = lists.kl
        else:
            choice = self.kiss
        if ctx.author == user:
            return await general.send(language.string("social_alone"), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(language.string("social_kiss_suager"), ctx.channel)
        if user.bot:
            return await general.send(language.string("social_kiss_bot"), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "kiss", 7)
        title, footer = get_data(ctx.author, user, "kiss", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(choice))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="bite")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def bite(self, ctx: commands.Context, user: discord.Member):
        """ Bite someone """
        language = self.bot.language(ctx)
        if is_fucked(self.bite):
            self.bite = await lists.get_images(self.bot, 'b')
        if ctx.author == user:
            return await general.send(language.string("social_slap_self"), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(language.string("social_slap_suager", author=language.case(ctx.author.name, "vocative")), ctx.channel)
        if user.id == 302851022790066185 and ctx.author.id not in self.unlocked:
            return await general.send(language.string("social_forbidden"), ctx.channel)
        if user.bot:
            return await general.send(language.string("social_slap_bot"), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "bite", 3)
        title, footer = get_data(ctx.author, user, "bite", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.bite))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="slap")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def slap(self, ctx: commands.Context, user: discord.Member):
        """ Slap someone """
        language = self.bot.language(ctx)
        if ctx.author == user:
            return await general.send(language.string("social_slap_self"), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(language.string("social_slap_suager", author=language.case(ctx.author.name, "vocative")), ctx.channel)
        if user.id == 302851022790066185 and ctx.author.id == 236884090651934721:
            return await general.send(f"{emotes.KannaSpook} How dare you", ctx.channel)
        if user.id == 302851022790066185 and ctx.author.id not in self.unlocked:  # and ctx.author.id in self.locked:
            return await general.send(language.string("social_forbidden"), ctx.channel)
        if user.bot:
            return await general.send(language.string("social_slap_bot"), ctx.channel)
        if is_fucked(self.slap):
            self.slap = await lists.get_images(self.bot, 'v')
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "slap", 10)
        title, footer = get_data(ctx.author, user, "slap", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.slap))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="sniff")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def smell(self, ctx: commands.Context, user: discord.Member):
        """ Sniff someone """
        language = self.bot.language(ctx)
        if is_fucked(self.smell):
            self.smell = await lists.get_images(self.bot, 'n')
        if ctx.author == user:
            return await general.send(language.string("social_poke_self"), ctx.channel)
        if user.id == 302851022790066185 and ctx.author.id in self.locked:
            return await general.send(language.string("social_forbidden"), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(language.string("social_sniff_suager"), ctx.channel)
        if user.bot:
            return await general.send(language.string("social_bot"), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "sniff", 11)
        title, footer = get_data(ctx.author, user, "sniff", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.smell))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="highfive")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def high_five(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a high five """
        language = self.bot.language(ctx)
        if is_fucked(self.high_five):
            self.high_five = await lists.get_images(self.bot, 'i')
        if ctx.author == user:
            return await general.send(language.string("social_alone"), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(language.string("social_high_five_suager", author=language.case(ctx.author.name, "high_five")), ctx.channel)
        if user.bot:
            return await general.send(language.string("social_bot"), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "high_five", 5)
        title, footer = get_data(ctx.author, user, "high_five", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.high_five))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="poke")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def poke(self, ctx: commands.Context, user: discord.Member):
        """ Poke someone """
        language = self.bot.language(ctx)
        if is_fucked(self.poke):
            self.poke = await lists.get_images(self.bot, 'P')
        if ctx.author == user:
            return await general.send(language.string("social_poke_self"), ctx.channel)
        if user.id == 302851022790066185 and ctx.author.id in self.locked:
            return await general.send(language.string("social_forbidden"), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(language.string("social_poke_suager", author=language.case(ctx.author.name, "vocative")), ctx.channel)
        if user.bot:
            return await general.send(language.string("social_bot"), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "poke", 12)
        title, footer = get_data(ctx.author, user, "poke", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.poke))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="boop")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def boop(self, ctx: commands.Context, user: discord.Member):
        """ Why is this a thing? """
        language = self.bot.language(ctx)
        if is_fucked(self.boop):
            self.boop = await lists.get_images(self.bot, 'B')
        if ctx.author == user:
            return await general.send(language.string("social_poke_self"), ctx.channel)
        if user.id == 302851022790066185 and ctx.author.id in self.locked:
            return await general.send(language.string("social_forbidden"), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(language.string("social_boop_suager"), ctx.channel)
        if user.bot:
            return await general.send(language.string("social_bot"), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "boop", 13)
        title, footer = get_data(ctx.author, user, "boop", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.boop))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="tickle")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def tickle(self, ctx: commands.Context, user: discord.Member):
        """ How dare you """
        language = self.bot.language(ctx)
        if is_fucked(self.tickle):
            self.tickle = await lists.get_images(self.bot, 't')
        if ctx.author == user:
            return await general.send(language.string("social_poke_self"), ctx.channel)
        if user.id == 302851022790066185 and ctx.author.id not in self.unlocked:
            return await general.send(language.string("social_tickle_regaus", author=language.case(ctx.author.name, "vocative")), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(language.string("social_tickle_suager"), ctx.channel)
        if user.bot:
            return await general.send(language.string("social_bot"), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "tickle", 15)
        title, footer = get_data(ctx.author, user, "tickle", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.tickle))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="punch")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def punch(self, ctx: commands.Context, user: discord.Member):
        """ Punch someone """
        language = self.bot.language(ctx)
        if ctx.author == user:
            return await general.send(language.string("social_slap_self"), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(language.string("social_slap_suager", author=language.case(ctx.author.name, "vocative")), ctx.channel)
        if user.id == 302851022790066185 and ctx.author.id == 236884090651934721:
            return await general.send(f"{emotes.KannaSpook} How dare you", ctx.channel)
        if user.id == 302851022790066185 and ctx.author.id not in self.unlocked:
            return await general.send(language.string("social_kill_regaus", author=language.case(ctx.author.name, "vocative")), ctx.channel)
        if user.bot:
            return await general.send(language.string("social_slap_bot"), ctx.channel)
        given, received = self.data_update(ctx.author.id, user.id, "punch", 16)
        title, footer = get_data(ctx.author, user, "punch", language, given, received)
        return await general.send(f"{title}\n{footer}", ctx.channel)

    @commands.command(name="sleepy")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def sleepy(self, ctx):
        """ You're sleepy """
        language = self.bot.language(ctx)
        if is_fucked(self.sleepy):
            self.sleepy = await lists.get_images(self.bot, 's')
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_sleepy", author=ctx.author.name)
        embed.set_image(url=random.choice(self.sleepy))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="cry")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def cry(self, ctx):
        """ You're crying """
        language = self.bot.language(ctx)
        if is_fucked(self.cry):
            self.cry = await lists.get_images(self.bot, 'r')
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_cry", author=ctx.author.name)
        embed.set_image(url=random.choice(self.cry))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="blush")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def blush(self, ctx):
        """ You blush """
        language = self.bot.language(ctx)
        if is_fucked(self.blush):
            self.blush = await lists.get_images(self.bot, 'u')
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_blush", author=ctx.author.name)
        embed.set_image(url=random.choice(self.blush))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="smile")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def smile(self, ctx):
        """ You're smiling """
        language = self.bot.language(ctx)
        if is_fucked(self.smile):
            self.smile = await lists.get_images(self.bot, 'm')
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_smile", author=ctx.author.name)
        embed.set_image(url=random.choice(self.smile))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="laugh")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def laugh(self, ctx, at: discord.User = None):
        """ Haha funny """
        language = self.bot.language(ctx)
        if is_fucked(self.laugh):
            self.laugh = await lists.get_images(self.bot, 'L')
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_laugh", author=ctx.author.name) if at is None else language.string("social_laugh_at", author=ctx.author.name, target=language.case(at.name, "at"))
        embed.set_image(url=random.choice(self.laugh))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="dance")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def dance(self, ctx):
        """ You're dancing """
        language = self.bot.language(ctx)
        if is_fucked(self.dance):
            self.dance = await lists.get_images(self.bot, 'd')
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_dance", author=ctx.author.name)
        embed.set_image(url=random.choice(self.dance))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="bean")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def bean(self, ctx: commands.Context, user: discord.Member):
        """ Bean someone """
        language = self.bot.language(ctx)
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.id == 302851022790066185 and ctx.author.id in self.locked:
            return await general.send(language.string("social_forbidden"), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(language.string("social_forbidden"), ctx.channel)
        if user.id == ctx.guild.owner.id:
            return await general.send(language.string("social_bean_owner"), ctx.channel)
        bean = language.string("social_bean", user.name, ctx.guild.name)
        return await general.send(bean, ctx.channel)

    @commands.command(name="cookie")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def cookie(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a cookie """
        language = self.bot.language(ctx)
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.bot:
            return await general.send(language.string("social_food_bot"), ctx.channel)
        output = give(ctx.author.name, user.name, "🍪", language)
        return await general.send(output, ctx.channel)

    @commands.command(name="lemon")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def lemon(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a lemon """
        language = self.bot.language(ctx)
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.bot:
            return await general.send(language.string("social_food_bot"), ctx.channel)
        output = give(ctx.author.name, user.name, "🍋", language)
        return await general.send(output, ctx.channel)

    @commands.command(name="carrot")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def carrot(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a carrot """
        language = self.bot.language(ctx)
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.bot:
            return await general.send(language.string("social_food_bot"), ctx.channel)
        output = give(ctx.author.name, user.name, "🥕", language)
        return await general.send(output, ctx.channel)

    @commands.command(name="fruit")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def fruit_snacks(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a fruit """
        language = self.bot.language(ctx)
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.bot:
            return await general.send(language.string("social_food_bot"), ctx.channel)
        output = give(ctx.author.name, user.name, random.choice(list("🍏🍎🍐🍊🍌🍉🍇🍓🍒🍍")), language)
        return await general.send(output, ctx.channel)

    @commands.command(name="pineapple")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def pineapple(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a pineapple """
        language = self.bot.language(ctx)
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.bot:
            return await general.send(language.string("social_food_bot"), ctx.channel)
        output = give(ctx.author.name, user.name, "🍍", language)
        return await general.send(output, ctx.channel)

    @commands.command(name="monke", aliases=["monkey"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def monkey(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a monke """
        language = self.bot.language(ctx)
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.bot:
            return await general.send(language.string("social_food_bot"), ctx.channel)
        output = give(ctx.author.name, user.name, "🐒", language)
        return await general.send(output, ctx.channel)

    @commands.command(name="reloadimages", aliases=["ri"])
    @commands.is_owner()
    async def reload_images(self, ctx: commands.Context):
        """ Reload all images """
        self.bite = await lists.get_images(self.bot, 'b')
        self.blush = await lists.get_images(self.bot, 'u')
        self.boop = await lists.get_images(self.bot, 'B')
        self.cry = await lists.get_images(self.bot, 'r')
        self.cuddle = await lists.get_images(self.bot, 'c')
        self.dance = await lists.get_images(self.bot, 'd')
        self.high_five = await lists.get_images(self.bot, 'i')
        self.hug = await lists.get_images(self.bot, 'h')
        self.kiss = await lists.get_images(self.bot, 'k')
        self.laugh = await lists.get_images(self.bot, 'L')
        self.lick = await lists.get_images(self.bot, 'l')
        self.pat = await lists.get_images(self.bot, 'p')
        self.poke = await lists.get_images(self.bot, 'P')
        self.slap = await lists.get_images(self.bot, 'v')
        self.sleepy = await lists.get_images(self.bot, 's')
        self.smell = await lists.get_images(self.bot, 'n')
        self.smile = await lists.get_images(self.bot, 'm')
        self.tickle = await lists.get_images(self.bot, 't')
        return await general.send("Successfully reloaded images", ctx.channel)


class SocialSuager(Social, name="Social"):
    @commands.command(name="kill")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def kill(self, ctx: commands.Context, user: discord.Member):
        """ Kill someone """
        language = self.bot.language(ctx)
        if ctx.author == user:
            return await general.send(language.string("social_slap_self"), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(language.string("social_slap_suager", author=language.case(ctx.author.name, "vocative")), ctx.channel)
        if user.id == 302851022790066185 and ctx.author.id not in self.unlocked:
            return await general.send(language.string("social_kill_regaus", author=language.case(ctx.author.name, "vocative")), ctx.channel)
        if user.bot:
            return await general.send(language.string("social_slap_bot"), ctx.channel)
        given, received = self.data_update(ctx.author.id, user.id, "kill", 17)
        title, footer = get_data(ctx.author, user, "kill", language, given, received)
        # title = language.string("social_kill", ctx.author.name, user.name)
        # base = language.string("social_kill_counter", ctx.author.name, user.name)
        # base2 = language.string("social_kill_counter", user.name, ctx.author.name)
        # _given, _received = language.plural(given, "generic_times"), language.plural(received, "generic_times")
        # footer = f"{base} {_given}\n{base2} {_received}"
        return await general.send(f"{title}\n{footer}", ctx.channel)

    @commands.command(name="bang", aliases=["fuck"])
    @commands.guild_only()
    @commands.check(lambda ctx: type(ctx.channel) != discord.DMChannel and (ctx.channel.is_nsfw() or ctx.channel.id == 764528556507922442))
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def fuck(self, ctx: commands.Context, user: discord.Member):
        """ Bang someone """
        language = self.bot.language(ctx)
        if user.id == 302851022790066185 and ctx.channel.id != 764528556507922442:
            return await general.send(language.string("social_forbidden"), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(f"{emotes.Deny} {language.string('generic_no')}.", ctx.channel)
        if user.bot:
            return await general.send(language.string("social_bang_bot"), ctx.channel)
        if user == ctx.author:
            return await general.send(emotes.UmmOK, ctx.channel)
        given, received = self.data_update(ctx.author.id, user.id, "bang", 2)
        title, footer = get_data(ctx.author, user, "bang", language, given, received)
        # t1, t2 = ctx.author.name, user.name
        # out = language.string("social_bang_main", t1, t2)
        # _given, _received = language.plural(given, "generic_times"), language.plural(received, "generic_times")
        # counter1 = language.string("social_bang_counter", t1, t2, _given)
        # counter2 = language.string("social_bang_counter", t2, t1, _received)
        return await general.send(f"{title}\n{footer}", ctx.channel)

    @commands.command(name="suck", aliases=["succ"])
    @commands.guild_only()
    @commands.check(lambda ctx: type(ctx.channel) != discord.DMChannel and (ctx.channel.is_nsfw() or ctx.channel.id == 764528556507922442))
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def suck(self, ctx: commands.Context, user: discord.Member):
        """ Succ someone off """
        language = self.bot.language(ctx)
        if user.id == self.bot.user.id:
            return await general.send(f"{emotes.Deny} {language.string('generic_no')}.", ctx.channel)
        if user.bot:
            return await general.send(language.string("social_bang_bot"), ctx.channel)
        if user == ctx.author:
            return await general.send(emotes.UmmOK, ctx.channel)
        given, received = self.data_update(ctx.author.id, user.id, "suck", 14)
        t1, t2 = ctx.author.name, user.name
        _given, _received = language.frequency(given), language.frequency(received)
        return await general.send(f"**{t1}** is now sucking **{t2}** off...\n{t1} did that to {t2} {_given}\n{t2} did that to {t1} {_received}", ctx.channel)

    @commands.command(name="facefuck", aliases=["ff"])
    @commands.guild_only()
    @commands.check(lambda ctx: type(ctx.channel) != discord.DMChannel and (ctx.channel.is_nsfw() or ctx.channel.id == 764528556507922442))
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def face_fuck(self, ctx: commands.Context, user: discord.User):
        """ Face-fuck someone """
        language = self.bot.language(ctx)
        if user.id == self.bot.user.id:
            return await general.send(f"{emotes.Deny} {language.string('generic_no')}.", ctx.channel)
        if user.bot:
            return await general.send(language.string("social_bang_bot"), ctx.channel)
        if user == ctx.author:
            return await general.send(emotes.UmmOK, ctx.channel)
        if user.id == 302851022790066185 and ctx.channel.id != 764528556507922442:
            return await general.send(language.string('social_forbidden'), ctx.channel)
        given, received = self.data_update(ctx.author.id, user.id, "ff", 18)
        t1, t2 = ctx.author.name, user.name
        _given, _received = language.frequency(given), language.frequency(received)
        return await general.send(f"**{t1}** is now face-fucking **{t2}**...\n{t1} face-fucked {t2} {_given}\n{t2} face-fucked {t1} {_received}", ctx.channel)


def setup(bot: bot_data.Bot):
    if bot.name == "suager":
        bot.add_cog(SocialSuager(bot))
    else:
        bot.add_cog(Social(bot))
