import random

import discord
from discord.ext import commands

from utils import bot_data, emotes, general, languages, lists_suager


def is_fucked(something):
    return something == [] or something == lists_suager.error or something == [lists_suager.error]


but_why = "https://cdn.discordapp.com/attachments/610482988123422750/673642028357386241/butwhy.gif"


def give(u1: str, u2: str, emote: str, language: languages.Language) -> str:
    return language.string("social_food", u1, u2, emote)


def get_data(author: discord.Member, target: discord.Member, action: str, language: languages.Language, given: int, received: int):
    _given, _received = language.plural(given, "generic_times"), language.plural(received, "generic_times")
    title = language.string(f"social_{action}", author.name, target.name)
    title2 = language.string(f"social_{action}", target.name, author.name)
    return title, f"{title} {_given}\n{title2} {_received}"


class Social(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        self.pat, self.hug, self.kiss, self.lick, self.cuddle, self.bite, self.sleepy, self.smell, self.cry, self.slap, self.blush, self.smile, self.highfive, \
            self.poke, self.boop, self.tickle, self.laugh, self.dance = [lists_suager.error] * 18
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
            self.pat = await lists_suager.get_images(self.bot, 'p')
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
            self.hug = await lists_suager.get_images(self.bot, 'h')
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
            self.cuddle = await lists_suager.get_images(self.bot, 'c')
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
            self.lick = await lists_suager.get_images(self.bot, 'l')
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
            self.kiss = await lists_suager.get_images(self.bot, 'k')
        if ctx.channel.id == 725835449502924901:
            choice = lists_suager.kl
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
            self.bite = await lists_suager.get_images(self.bot, 'b')
        if ctx.author == user:
            return await general.send(language.string("social_slap_self"), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(language.string("social_slap_suager", ctx.author.name), ctx.channel)
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
            return await general.send(language.string("social_slap_suager", ctx.author.name), ctx.channel)
        if user.id == 302851022790066185 and ctx.author.id in [236884090651934721]:
            return await general.send(f"{emotes.KannaSpook} How dare you", ctx.channel)
        if user.id == 302851022790066185 and ctx.author.id not in self.unlocked:  # and ctx.author.id in self.locked:
            return await general.send(language.string("social_forbidden"), ctx.channel)
        if user.bot:
            return await general.send(language.string("social_slap_bot"), ctx.channel)
        if is_fucked(self.slap):
            self.slap = await lists_suager.get_images(self.bot, 'v')
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
            self.smell = await lists_suager.get_images(self.bot, 'n')
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
    async def highfive(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a high five """
        language = self.bot.language(ctx)
        if is_fucked(self.highfive):
            self.highfive = await lists_suager.get_images(self.bot, 'i')
        if ctx.author == user:
            return await general.send(language.string("social_alone"), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(language.string("social_high_five_suager", ctx.author.name), ctx.channel)
        if user.bot:
            return await general.send(language.string("social_bot"), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "high_five", 5)
        title, footer = get_data(ctx.author, user, "high_five", language, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.highfive))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="poke")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def poke(self, ctx: commands.Context, user: discord.Member):
        """ Poke someone """
        language = self.bot.language(ctx)
        if is_fucked(self.poke):
            self.poke = await lists_suager.get_images(self.bot, 'P')
        if ctx.author == user:
            return await general.send(language.string("social_poke_self"), ctx.channel)
        if user.id == 302851022790066185 and ctx.author.id in self.locked:  # and ctx.author.id in self.locked:
            return await general.send(language.string("social_forbidden"), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(language.string("social_poke_suager", ctx.author.name), ctx.channel)
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
            self.boop = await lists_suager.get_images(self.bot, 'B')
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
            self.tickle = await lists_suager.get_images(self.bot, 't')
        if ctx.author == user:
            return await general.send(language.string("social_poke_self"), ctx.channel)
        if user.id == 302851022790066185 and ctx.author.id not in self.unlocked:
            return await general.send(language.string("social_tickle_regaus"), ctx.channel)
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
            return await general.send(language.string("social_slap_suager", ctx.author.name), ctx.channel)
        if user.id == 302851022790066185 and ctx.author.id in [236884090651934721]:
            return await general.send(f"{emotes.KannaSpook} How dare you", ctx.channel)
        if user.id == 302851022790066185 and ctx.author.id not in self.unlocked:
            return await general.send(language.string("social_kill_regaus", ctx.author.id), ctx.channel)
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
            self.sleepy = await lists_suager.get_images(self.bot, 's')
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_sleepy", ctx.author.name)
        embed.set_image(url=random.choice(self.sleepy))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="cry")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def cry(self, ctx):
        """ You're crying """
        language = self.bot.language(ctx)
        if is_fucked(self.cry):
            self.cry = await lists_suager.get_images(self.bot, 'r')
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_cry", ctx.author.name)
        embed.set_image(url=random.choice(self.cry))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="blush")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def blush(self, ctx):
        """ You blush """
        language = self.bot.language(ctx)
        if is_fucked(self.blush):
            self.blush = await lists_suager.get_images(self.bot, 'u')
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_blush", ctx.author.name)
        embed.set_image(url=random.choice(self.blush))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="smile")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def smile(self, ctx):
        """ You're smiling """
        language = self.bot.language(ctx)
        if is_fucked(self.smile):
            self.smile = await lists_suager.get_images(self.bot, 'm')
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_smile", ctx.author.name)
        embed.set_image(url=random.choice(self.smile))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="laugh")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def laugh(self, ctx, at: discord.User = None):
        """ Haha funny """
        language = self.bot.language(ctx)
        if is_fucked(self.laugh):
            self.laugh = await lists_suager.get_images(self.bot, 'L')
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_laugh", ctx.author.name) if at is None else language.string("social_laugh_at", ctx.author.name, at.name)
        embed.set_image(url=random.choice(self.laugh))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="dance")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def dance(self, ctx):
        """ You're dancing """
        language = self.bot.language(ctx)
        if is_fucked(self.dance):
            self.dance = await lists_suager.get_images(self.bot, 'd')
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("social_dance", ctx.author.name)
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
        if user.id == 302851022790066185 and ctx.author.id not in self.unlocked:
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
        self.pat = await lists_suager.get_images(self.bot, 'p')
        self.hug = await lists_suager.get_images(self.bot, 'h')
        self.kiss = await lists_suager.get_images(self.bot, 'k')
        self.lick = await lists_suager.get_images(self.bot, 'l')
        self.cuddle = await lists_suager.get_images(self.bot, 'c')
        self.bite = await lists_suager.get_images(self.bot, 'b')
        self.sleepy = await lists_suager.get_images(self.bot, 's')
        self.smell = await lists_suager.get_images(self.bot, 'n')
        self.cry = await lists_suager.get_images(self.bot, 'r')
        self.slap = await lists_suager.get_images(self.bot, 'v')
        self.blush = await lists_suager.get_images(self.bot, 'u')
        self.highfive = await lists_suager.get_images(self.bot, 'i')
        self.smile = await lists_suager.get_images(self.bot, 'm')
        self.poke = await lists_suager.get_images(self.bot, 'P')
        self.boop = await lists_suager.get_images(self.bot, 'B')
        self.tickle = await lists_suager.get_images(self.bot, 't')
        self.laugh = await lists_suager.get_images(self.bot, 'L')
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
            return await general.send(language.string("social_slap_suager", ctx.author.name), ctx.channel)
        if user.id == 302851022790066185 and ctx.author.id not in self.unlocked:
            return await general.send(language.string("social_kill_regaus", ctx.author.name), ctx.channel)
        if user.bot:
            return await general.send(language.string("social_slap_bot"), ctx.channel)
        given, received = self.data_update(ctx.author.id, user.id, "kill", 17)
        title = language.string("social_kill", ctx.author.name, user.name)
        base = language.string("social_kill_counter", ctx.author.name, user.name)
        base2 = language.string("social_kill_counter", user.name, ctx.author.name)
        _given, _received = language.plural(given, "generic_times"), language.plural(received, "generic_times")
        footer = f"{base} {_given}\n{base2} {_received}"
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
        lolis = [418151634087182359, 430891116318031872]
        if ctx.author.id in lolis:
            return await general.send(f"No futa lolis {emotes.KannaSpook}", ctx.channel)
        elif user.id in lolis and ctx.channel.id != 671520521174777869:
            return await general.send(language.string("social_forbidden"), ctx.channel)
        given, received = self.data_update(ctx.author.id, user.id, "bang", 2)
        t1, t2 = ctx.author.name, user.name
        out = language.string("social_bang_main", t1, t2)
        _given, _received = language.plural(given, "generic_times"), language.plural(received, "generic_times")
        counter1 = language.string("social_bang_counter", t1, t2, _given)
        counter2 = language.string("social_bang_counter", t2, t1, _received)
        return await general.send(f"{out}\n{counter1}\n{counter2}", ctx.channel)

    @commands.command(name="rape")
    @commands.guild_only()
    @commands.check(lambda ctx: ctx.channel.id in [764528556507922442, 753000962297299005])
    async def rape(self, ctx: commands.Context, user: discord.Member):
        """ Rape someone """
        language = self.bot.language(ctx)
        if user.id == self.bot.user.id:
            return await general.send(f"{emotes.Deny} {language.string('generic_no')}.", ctx.channel)
        if user == ctx.author:
            return await general.send(emotes.UmmOK, ctx.channel)
        if user.id == 302851022790066185 and ctx.channel.id != 764528556507922442:
            return await general.send(language.string('social_forbidden'), ctx.channel)
        given, received = self.data_update(ctx.author.id, user.id, "r", 19)
        t1, t2 = ctx.author.name, user.name
        out = f"**{t1}** is now raping **{t2}**..."
        _given, _received = language.plural(given, "generic_times"), language.plural(received, "generic_times")
        counter1, counter2 = f"{t1} raped {t2} {_given}", f"{t2} raped {t1} {_received}"
        return await general.send(f"{out}\n{counter1}\n{counter2}", ctx.channel)

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
        _given, _received = language.plural(given, "generic_times"), language.plural(received, "generic_times")
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
        _given, _received = language.plural(given, "generic_times"), language.plural(received, "generic_times")
        return await general.send(f"**{t1}** is now face-fucking **{t2}**...\n{t1} face-fucked {t2} {_given}\n{t2} face-fucked {t1} {_received}", ctx.channel)

    @commands.command(name="fc", aliases=["ic"])
    @commands.check(lambda ctx: ctx.channel.id in [672535025698209821, 764528556507922442, 753000962297299005])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def inside_counter(self, ctx: commands.Context):
        """ Count how many times you've been inside each other """
        uid1 = 302851022790066185
        uid2 = 236884090651934721 if ctx.channel.id in [672535025698209821, 753000962297299005] else 622735873137573894
        data1 = self.bot.db.fetchrow("SELECT * FROM counters WHERE uid1=? AND uid2=?", (uid1, uid2))
        data2 = self.bot.db.fetchrow("SELECT * FROM counters WHERE uid1=? AND uid2=?", (uid2, uid1))
        result1, result2 = 0, 0
        counters = ["bang", "ff", "r"]
        for counter in counters:
            result1 += data1[counter]
            result2 += data2[counter]
        result2 += data1["suck"]
        result1 += data2["suck"]
        name1, name2 = self.bot.get_user(uid1), self.bot.get_user(uid2)
        return await general.send(f"{name1} has been inside {name2} {result1} times\n{name2} has been inside {name1} {result2} times", ctx.channel)


def setup(bot: bot_data.Bot):
    if bot.name == "suager":
        bot.add_cog(SocialSuager(bot))
    else:
        bot.add_cog(Social(bot))
