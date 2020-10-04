import random

import discord
from discord.ext import commands

from core.utils import emotes, general
from languages import langs
from suager.utils import lists


def is_fucked(something):
    return something == [] or something == lists.error or something == [lists.error]


but_why = "https://cdn.discordapp.com/attachments/610482988123422750/673642028357386241/butwhy.gif"


def give(u1: str, u2: str, emote: str, locale: str) -> str:
    return langs.gls("social_food", locale, u1, u2, emote)


def get_data(author: discord.Member, target: discord.Member, action: str, locale: str, given: int, received: int):
    _given, _received = langs.plural(given, "generic_times", locale), langs.plural(received, "generic_times", locale)
    title = langs.gls(f"social_{action}", locale, author.name, target.name)
    title2 = langs.gls(f"social_{action}", locale, target.name, author.name)
    return title, f"{title} {_given}\n{title2} {_received}"


class Social(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pat, self.hug, self.kiss, self.lick, self.cuddle, self.bite, self.sleepy, self.smell, self.cry, self.slap, self.blush, self.smile, self.highfive, \
            self.poke, self.boop = [lists.error] * 15
        self.insert = f"INSERT INTO counters_new VALUES ({'?, ' * 14}?)"
        self.empty = [0] * 15

    def data_update(self, uid_give: int, uid_receive: int, key: str, ind: int):
        """ Update database - interactions """
        data_giver = self.bot.db.fetchrow("SELECT * FROM counters_new WHERE uid1=? AND uid2=?", (uid_give, uid_receive))
        data_receive = self.bot.db.fetchrow("SELECT * FROM counters_new WHERE uid1=? AND uid2=?", (uid_receive, uid_give))
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
            self.bot.db.execute(f"UPDATE counters_new SET {key}=? WHERE uid1=? AND uid2=?", (nu, uid_give, uid_receive))
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
        locale = langs.gl(ctx)
        if is_fucked(self.pat):
            self.pat = await lists.get_images(self.bot, 'p')
        if ctx.author == user:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(emotes.AlexHeart, ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_bot", locale), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "pat", 9)
        title, footer = get_data(ctx.author, user, "pat", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.pat))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="hug")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def hug(self, ctx: commands.Context, user: discord.Member):
        """ Hug someone """
        locale = langs.gl(ctx)
        if is_fucked(self.hug):
            self.hug = await lists.get_images(self.bot, 'h')
        if ctx.author == user:
            return await general.send(langs.gls("social_alone", locale), ctx.channel, embed=discord.Embed(colour=general.random_colour()).set_image(
                url="https://cdn.discordapp.com/attachments/610482988123422750/673641089218904065/selfhug.gif"))
        if user.id == self.bot.user.id:
            return await general.send(emotes.AlexHeart, ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_bot", locale), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "hug", 6)
        title, footer = get_data(ctx.author, user, "hug", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.hug))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="cuddle")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def cuddle(self, ctx: commands.Context, user: discord.Member):
        """ Cuddle someone """
        locale = langs.gl(ctx)
        if is_fucked(self.cuddle):
            self.cuddle = await lists.get_images(self.bot, 'c')
        if ctx.author == user:
            return await general.send(langs.gls("social_alone", locale), ctx.channel, embed=discord.Embed(colour=general.random_colour()).set_image(
                url="https://cdn.discordapp.com/attachments/610482988123422750/673641089218904065/selfhug.gif"))
        if user.id == self.bot.user.id:
            return await general.send(emotes.AlexHeart, ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_bot", locale), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "cuddle", 4)
        title, footer = get_data(ctx.author, user, "cuddle", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.cuddle))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="lick", aliases=["licc"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def lick(self, ctx: commands.Context, user: discord.Member):
        """ Lick someone """
        locale = langs.gl(ctx)
        if is_fucked(self.lick):
            self.lick = await lists.get_images(self.bot, 'l')
        if ctx.author == user:
            return await general.send(None, ctx.channel, embed=discord.Embed(colour=general.random_colour()).set_image(
                url="https://cdn.discordapp.com/attachments/610482988123422750/673644219314733106/selflick.gif"))
        if user.id == 302851022790066185:
            return await general.send(langs.gls("social_forbidden", locale), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("social_lick_suager", locale), ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_bot", locale), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "lick", 8)
        title, footer = get_data(ctx.author, user, "lick", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.lick))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="kiss", aliases=["kith", "kish"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def kiss(self, ctx: commands.Context, user: discord.Member):
        """ Kiss someone """
        locale = langs.gl(ctx)
        if is_fucked(self.kiss):
            self.kiss = await lists.get_images(self.bot, 'k')
        if ctx.author == user:
            return await general.send(langs.gls("social_alone", locale), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("social_kiss_suager", locale), ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_kiss_bot", locale), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "kiss", 7)
        title, footer = get_data(ctx.author, user, "kiss", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.kiss))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="bite")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def bite(self, ctx: commands.Context, user: discord.Member):
        """ Bite someone """
        locale = langs.gl(ctx)
        if is_fucked(self.bite):
            self.bite = await lists.get_images(self.bot, 'b')
        if ctx.author == user:
            return await general.send(langs.gls("social_slap_self", locale), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("social_slap_suager", locale, ctx.author.name), ctx.channel)
        if user.id == 302851022790066185:
            return await general.send(langs.gls("social_forbidden", locale), ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_slap_bot", locale), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "bite", 3)
        title, footer = get_data(ctx.author, user, "bite", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.bite))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="slap")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def slap(self, ctx: commands.Context, user: discord.Member):
        """ Slap someone """
        locale = langs.gl(ctx)
        if ctx.author == user:
            return await general.send(langs.gls("social_slap_self", locale), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("social_slap_suager", locale, ctx.author.name), ctx.channel)
        if user.id == 302851022790066185:
            return await general.send(langs.gls("social_forbidden", locale), ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_slap_bot", locale), ctx.channel)
        if is_fucked(self.slap):
            self.slap = await lists.get_images(self.bot, 'v')
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "slap", 10)
        title, footer = get_data(ctx.author, user, "slap", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.slap))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="sniff")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def smell(self, ctx: commands.Context, user: discord.Member):
        """ Sniff someone """
        locale = langs.gl(ctx)
        if is_fucked(self.smell):
            self.smell = await lists.get_images(self.bot, 'n')
        if ctx.author == user:
            return await general.send(langs.gls("social_poke_self", locale), ctx.channel)
        if user.id == 302851022790066185:
            return await general.send(langs.gls("social_forbidden", locale), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("social_sniff_suager", locale), ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_bot", locale), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "sniff", 11)
        title, footer = get_data(ctx.author, user, "sniff", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.smell))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="highfive")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def highfive(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a high five """
        locale = langs.gl(ctx)
        if is_fucked(self.highfive):
            self.highfive = await lists.get_images(self.bot, 'i')
        if ctx.author == user:
            return await general.send(langs.gls("social_alone", locale), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("social_high_five_suager", locale, ctx.author.name), ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_bot", locale), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "high_five", 5)
        title, footer = get_data(ctx.author, user, "high_five", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.highfive))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="poke")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def poke(self, ctx: commands.Context, user: discord.Member):
        """ Poke someone """
        locale = langs.gl(ctx)
        if is_fucked(self.poke):
            self.poke = await lists.get_images(self.bot, 'P')
        if ctx.author == user:
            return await general.send(langs.gls("social_poke_self", locale), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("social_poke_suager", locale, ctx.author.name), ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_bot", locale), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "poke", 12)
        title, footer = get_data(ctx.author, user, "poke", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.poke))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="boop", aliases=["bap"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def boop(self, ctx: commands.Context, user: discord.Member):
        """ Why is this a thing? """
        locale = langs.gl(ctx)
        if is_fucked(self.boop):
            self.boop = await lists.get_images(self.bot, 'B')
        if ctx.author == user:
            return await general.send(langs.gls("social_poke_self", locale), ctx.channel)
        if user.id == 302851022790066185:
            return await general.send(langs.gls("social_forbidden", locale), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("social_boop_suager", locale), ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_bot", locale), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "boop", 13)
        title, footer = get_data(ctx.author, user, "boop", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        embed.set_image(url=random.choice(self.boop))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="bang", aliases=["fuck"], hidden=True)
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def fuck(self, ctx, user: discord.Member):
        """ Bang someone """
        locale = langs.gl(ctx)
        if not ctx.channel.is_nsfw():
            return await general.send(langs.gls("social_bang_channel", locale), ctx.channel)
        if user.id == 302851022790066185:
            return await general.send(langs.gls("social_forbidden", locale), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(f"{emotes.Deny} {langs.gls('generic_no', locale)}.", ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_bang_bot", locale), ctx.channel)
        if user == ctx.author:
            return await general.send(emotes.UmmOK, ctx.channel)
        lolis = [418151634087182359, 430891116318031872]
        if ctx.author.id in lolis:
            return await general.send(f"No futa lolis {emotes.KannaSpook}", ctx.channel)
        elif user.id in lolis and ctx.channel.id != 671520521174777869:
            return await general.send(langs.gls("social_forbidden", locale), ctx.channel)
        given, received = self.data_update(ctx.author.id, user.id, "bang", 2)
        t1, t2 = ctx.author.name, user.name
        out = langs.gls("social_bang_main", locale, t1, t2)
        _given, _received = langs.plural(given, "generic_times", locale), langs.plural(received, "generic_times", locale)
        counter1 = langs.gls("social_bang_counter", locale, t1, t2, _given)
        counter2 = langs.gls("social_bang_counter", locale, t2, t1, _received)
        return await general.send(f"{out}\n{counter1}\n{counter2}", ctx.channel)

    @commands.command(name="suck", aliases=["succ"], hidden=True)
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def suck(self, ctx, user: discord.Member):
        """ Succ someone """
        locale = langs.gl(ctx)
        if not ctx.channel.is_nsfw():
            return await general.send(langs.gls("social_bang_channel", locale), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(f"{emotes.Deny} {langs.gls('generic_no', locale)}.", ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_bang_bot", locale), ctx.channel)
        if user == ctx.author:
            return await general.send(emotes.UmmOK, ctx.channel)
        given, received = self.data_update(ctx.author.id, user.id, "suck", 14)
        t1, t2 = ctx.author.name, user.name
        out = langs.gls("social_suck_main", locale, t1, t2)
        _given, _received = langs.plural(given, "generic_times", locale), langs.plural(received, "generic_times", locale)
        counter1 = langs.gls("social_suck_counter", locale, t1, t2, _given)
        counter2 = langs.gls("social_suck_counter", locale, t2, t1, _received)
        return await general.send(f"{out}\n{counter1}\n{counter2}", ctx.channel)

    @commands.command(name="sleepy")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def sleepy(self, ctx):
        """ You're sleepy """
        locale = langs.gl(ctx)
        if is_fucked(self.sleepy):
            self.sleepy = await lists.get_images(self.bot, 's')
        embed = discord.Embed(colour=general.random_colour())
        embed.title = langs.gls("social_sleepy", locale, ctx.author.name)
        embed.set_image(url=random.choice(self.sleepy))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="cry")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def cry(self, ctx):
        """ You're crying """
        locale = langs.gl(ctx)
        if is_fucked(self.cry):
            self.cry = await lists.get_images(self.bot, 'r')
        embed = discord.Embed(colour=general.random_colour())
        embed.title = langs.gls("social_cry", locale, ctx.author.name)
        embed.set_image(url=random.choice(self.cry))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="blush")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def blush(self, ctx):
        """ You blush """
        locale = langs.gl(ctx)
        if is_fucked(self.blush):
            self.blush = await lists.get_images(self.bot, 'u')
        embed = discord.Embed(colour=general.random_colour())
        embed.title = langs.gls("social_blush", locale, ctx.author.name)
        embed.set_image(url=random.choice(self.blush))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="smile")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def smile(self, ctx):
        """ You're smiling """
        locale = langs.gl(ctx)
        if is_fucked(self.smile):
            self.smile = await lists.get_images(self.bot, 'm')
        embed = discord.Embed(colour=general.random_colour())
        embed.title = langs.gls("social_smile", locale, ctx.author.name)
        embed.set_image(url=random.choice(self.smile))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="bean")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def bean(self, ctx: commands.Context, user: discord.Member):
        """ Bean someone """
        locale = langs.gl(ctx)
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.id == 302851022790066185:
            return await general.send(langs.gls("social_forbidden", locale), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("social_forbidden", locale), ctx.channel)
        if user.id == ctx.guild.owner.id and ctx.author.id != 302851022790066185:
            return await general.send(langs.gls("social_bean_owner", locale), ctx.channel)
        bean = langs.gls("social_bean", locale, user.name, ctx.guild.name)
        return await general.send(bean, ctx.channel)

    @commands.command(name="cookie")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def cookie(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a cookie """
        locale = langs.gl(ctx)
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_food_bot", locale), ctx.channel)
        output = give(ctx.author.name, user.name, "🍪", locale)
        return await general.send(output, ctx.channel)

    @commands.command(name="lemon")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def lemon(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a lemon """
        locale = langs.gl(ctx)
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_food_bot", locale), ctx.channel)
        output = give(ctx.author.name, user.name, "🍋", locale)
        return await general.send(output, ctx.channel)

    @commands.command(name="carrot")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def carrot(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a carrot """
        locale = langs.gl(ctx)
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_food_bot", locale), ctx.channel)
        output = give(ctx.author.name, user.name, "🥕", locale)
        return await general.send(output, ctx.channel)

    @commands.command(name="fruit")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def fruit_snacks(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a fruit """
        locale = langs.gl(ctx)
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_food_bot", locale), ctx.channel)
        output = give(ctx.author.name, user.name, random.choice(list("🍏🍎🍐🍊🍌🍉🍇🍓🍒🍍")), locale)
        return await general.send(output, ctx.channel)

    @commands.command(name="reloadimages", aliases=["ri"])
    @commands.is_owner()
    async def reload_images(self, ctx: commands.Context):
        """ Reload all images """
        self.pat = await lists.get_images(self.bot, 'p')
        self.hug = await lists.get_images(self.bot, 'h')
        self.kiss = await lists.get_images(self.bot, 'k')
        self.lick = await lists.get_images(self.bot, 'l')
        self.cuddle = await lists.get_images(self.bot, 'c')
        self.bite = await lists.get_images(self.bot, 'b')
        self.sleepy = await lists.get_images(self.bot, 's')
        self.smell = await lists.get_images(self.bot, 'n')
        self.cry = await lists.get_images(self.bot, 'r')
        self.slap = await lists.get_images(self.bot, 'v')
        self.blush = await lists.get_images(self.bot, 'u')
        self.highfive = await lists.get_images(self.bot, 'i')
        self.smile = await lists.get_images(self.bot, 'm')
        self.poke = await lists.get_images(self.bot, 'P')
        self.boop = await lists.get_images(self.bot, 'B')
        return await general.send("Successfully reloaded images", ctx.channel)


def setup(bot):
    bot.add_cog(Social(bot))
