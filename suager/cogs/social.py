import random
from io import BytesIO

import discord
from discord.ext import commands

from core.cogs.images import image_gen
from core.utils import database, general, http, emotes
from languages import langs
from suager.utils import lists


def is_fucked(something):
    return something == [] or something == lists.error or something == [lists.error]


but_why = "https://cdn.discordapp.com/attachments/610482988123422750/673642028357386241/butwhy.gif"


def give(u1: str, u2: str, emote: str, locale: str) -> str:
    return langs.gls("social_food", locale, u1, u2, emote)
    # return f"**{u2}** just got a {emote} from **{u1}**\n\n(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ {emote}"
    # return generic.gls(locale, "give_food", [u1, u2, emote]) + f"\n\n(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ {emote}"
    # return f"{u2}, you got a {emote} from {u1}\n\n(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ {emote}"


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
        self.db = database.Database(self.bot.name)
        self.insert = f"INSERT INTO counters_new VALUES ({'?, ' * 13}?)"
        self.empty = [0] * 14
        # self.names = ["Redacted", "Social interaction", "Edit this text", "Statuses", "Foods"]
        # n1, n2, n3, n4, n5 = self.names
        # self.keys = {
        #     n1: ["bangs_given", "bangs_received"],
        #     n2: ["bites_given", "bites_received", "cuddles_given", "cuddles_received", "high_fives_given",
        #          "high_fives_received", "hugs_given", "hugs_received", "kisses_given", "kisses_received", "licks_given",
        #          "licks_received", "pats_given", "pats_received", "slaps_given", "slaps_received", "sniffs_given",
        #          "sniffs_received", "pokes_given", "pokes_received", "boops_given", "boops_received"],
        #     n3: ["bad_given", "bad_received", "beaned", "beans_given", "shipped", "ships_built", "trashed", "trash_given"],
        #     n4: ["blushed", "cried", "sleepy", "smiled"],
        #     n5: ["carrots_received", "carrots_eaten", "cookies_received", "cookies_eaten", "fruits_received",
        #          "fruits_eaten", "lemons_received", "lemons_eaten"]
        # }
        # self.key_names = {
        #     n1: ["Redacted", "Redacted"],
        #     n2: ["Bitten others", "Been bitten", "Cuddled others", "Been cuddled", "Gave high fives",
        #          "Received high fives", "Hugged others", "Been hugged", "Kissed others", "Been kissed", "Licked others",
        #          "Been licked", "Gave pats", "Received pats", "Slapped others", "Been slapped", "Sniffed others",
        #          "Been sniffed", "Poked others", "Been poked", "Booped others", "Been booped"],
        #     n3: ["Called others bad", "Been called bad", "Been beaned", "Beaned others", "Been shipped", "Built ships", "Been trashed", "Trashed others"],
        #     n4: ["Blushed", "Cried", "Been sleepy", "Smiled"],
        #     n5: ["Carrots received", "Carrots eaten", "Cookies received", "Cookies eaten", "Fruits received",
        #          "Fruits eaten", "Lemons received", "Lemons eaten"]
        # }

    def data_update(self, uid_give: int, uid_receive: int, key: str, ind: int):
        """ Update database - interactions """
        data_giver = self.db.fetchrow("SELECT * FROM counters_new WHERE uid1=? AND uid2=?", (uid_give, uid_receive))
        data_receive = self.db.fetchrow("SELECT * FROM counters_new WHERE uid1=? AND uid2=?", (uid_receive, uid_give))
        if not data_giver:
            data = self.empty.copy()
            data[0] = uid_give
            data[1] = uid_receive
            data[ind] = 1
            self.db.execute(self.insert, tuple(data))
            number1 = 1
        else:
            n = data_giver[key]
            nu = 1 if n is None else n + 1
            self.db.execute(f"UPDATE counters_new SET {key}=? WHERE uid1=? AND uid2=?", (nu, uid_give, uid_receive))
            n2 = data_giver[key]
            number1 = 1 if n2 is None else n2 + 1
        if not data_receive:
            number2 = 0
        else:
            n2 = data_receive[key]
            number2 = 0 if n2 is None else n2
        return number1, number2  # given, received

    # def data_update2(self, uid: int, gid: int, key: str, ind: int):
    #     """ Update database - statuses """
    #     data_giver = self.db.fetchrow("SELECT * FROM counters_new WHERE uid1=? AND uid2=?", (uid, gid))
    #     if not data_giver:
    #         data = self.empty.copy()
    #         data[0] = uid
    #         data[1] = gid
    #         data[ind] = 1
    #         self.db.execute(self.insert, tuple(data))
    #         number = 1
    #     else:
    #         n = data_giver[key]
    #         number = 1 if n is None else n + 1
    #         self.db.execute(f"UPDATE counters_new SET {key}=? WHERE uid1=? AND uid2=?", (number, uid, gid))
    #     return number

    # def data_update3(self, uid: int, gid: int, key: str, key2: str, ind: int):
    #     """ Update database - foods """
    #     data_giver = self.db.fetchrow("SELECT * FROM counters_new WHERE uid1=? AND uid2=?", (uid, gid))
    #     if not data_giver:
    #         data = self.empty.copy()
    #         data[0] = uid
    #         data[1] = gid
    #         data[ind] = 1
    #         self.db.execute(self.insert, tuple(data))
    #         number = 1
    #     else:
    #         n = data_giver[key]
    #         number = 1 if n is None else n + 1
    #         self.db.execute(f"UPDATE counters_new SET {key}=? WHERE uid1=? AND uid2=?", (number, uid, gid))
    #         n2 = data_giver[key2]
    #         if n2 is None:
    #             n2 = 0
    #         number -= n2
    #     return number

    @commands.command(name="pat", aliases=["pet"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def pat(self, ctx: commands.Context, user: discord.Member):
        """ Pat someone """
        locale = langs.gl(ctx.guild, self.db)
        if is_fucked(self.pat):
            self.pat = await lists.get_images(self.bot, 'p')
        if ctx.author == user:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(emotes.AlexHeart, ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_bot", locale), ctx.channel)
            # return await general.send(f"I don't think {user.name} is going to respond...", ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "pat", 9)
        title, footer = get_data(ctx.author, user, "pat", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        # embed.title = f"**{user.name}** just got a pat from **{ctx.author.name}**"
        embed.set_image(url=random.choice(self.pat))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="hug")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def hug(self, ctx: commands.Context, user: discord.Member):
        """ Hug someone """
        locale = langs.gl(ctx.guild, self.db)
        if is_fucked(self.hug):
            self.hug = await lists.get_images(self.bot, 'h')
        if ctx.author == user:
            return await general.send(langs.gls("social_alone", locale), ctx.channel, embed=discord.Embed(colour=general.random_colour()).set_image(
                url="https://cdn.discordapp.com/attachments/610482988123422750/673641089218904065/selfhug.gif"))
        if user.id == self.bot.user.id:
            return await general.send(emotes.AlexHeart, ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_bot", locale), ctx.channel)
            # return await general.send(f"I don't think {user.name} is going to respond...", ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "hug", 6)
        title, footer = get_data(ctx.author, user, "hug", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        # .title = f"**{user.name}** just got a hug from **{ctx.author.name}**"
        embed.set_image(url=random.choice(self.hug))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="cuddle")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def cuddle(self, ctx: commands.Context, user: discord.Member):
        """ Cuddle someone """
        locale = langs.gl(ctx.guild, self.db)
        if is_fucked(self.cuddle):
            self.cuddle = await lists.get_images(self.bot, 'c')
        if ctx.author == user:
            return await general.send(langs.gls("social_alone", locale), ctx.channel, embed=discord.Embed(colour=general.random_colour()).set_image(
                url="https://cdn.discordapp.com/attachments/610482988123422750/673641089218904065/selfhug.gif"))
        if user.id == self.bot.user.id:
            return await general.send(emotes.AlexHeart, ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_bot", locale), ctx.channel)
            # return await general.send(f"I don't think {user.name} is going to respond...", ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "cuddle", 4)
        title, footer = get_data(ctx.author, user, "cuddle", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        # embed.title = f"**{user.name}** just got cuddled by **{ctx.author.name}**"
        embed.set_image(url=random.choice(self.cuddle))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="lick", aliases=["licc"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def lick(self, ctx: commands.Context, user: discord.Member):
        """ Lick someone """
        locale = langs.gl(ctx.guild, self.db)
        if is_fucked(self.lick):
            self.lick = await lists.get_images(self.bot, 'l')
        if ctx.author == user:
            return await general.send(None, ctx.channel, embed=discord.Embed(colour=general.random_colour()).set_image(
                url="https://cdn.discordapp.com/attachments/610482988123422750/673644219314733106/selflick.gif"))
        if user.id == 302851022790066185:
            return await general.send(langs.gls("social_forbidden", locale), ctx.channel)
            # return await general.send("How about you don't?", ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("social_lick_suager", locale), ctx.channel)
            # return await general.send("Why would you do that?", ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_bot", locale), ctx.channel)
            # return await general.send(f"Why would you lick {user.name}?", ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "lick", 8)
        title, footer = get_data(ctx.author, user, "lick", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        # embed.title = f"**{ctx.author.name}** just licked **{user.name}**"
        embed.set_image(url=random.choice(self.lick))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="kiss", aliases=["kith", "kish"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def kiss(self, ctx: commands.Context, user: discord.Member):
        """ Kiss someone """
        locale = langs.gl(ctx.guild, self.db)
        if is_fucked(self.kiss):
            self.kiss = await lists.get_images(self.bot, 'k')
        if ctx.author == user:
            return await general.send(langs.gls("social_alone", locale), ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("social_kiss_suager", locale), ctx.channel)
            # return await general.send("I am not programmed to feel love.", ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_kiss_bot", locale), ctx.channel)
            # return await general.send("Bots weren't programmed to feel love, though...", ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "kiss", 7)
        title, footer = get_data(ctx.author, user, "kiss", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        # embed.title = f"**{ctx.author.name}** just kissed **{user.name}**"
        embed.set_image(url=random.choice(self.kiss))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="bite")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def bite(self, ctx: commands.Context, user: discord.Member):
        """ Bite someone """
        locale = langs.gl(ctx.guild, self.db)
        if is_fucked(self.bite):
            self.bite = await lists.get_images(self.bot, 'b')
        if ctx.author == user:
            return await general.send(langs.gls("social_slap_self", locale), ctx.channel)
            # return await general.send(f"Self harm bad {emotes.BlobCatPolice}", ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("social_slap_suager", locale, ctx.author.name), ctx.channel)
            # return await general.send(f"We are no longer friends, {ctx.author.name}", ctx.channel)
        if user.id == 302851022790066185:
            return await general.send(langs.gls("social_forbidden", locale), ctx.channel)
            # return await general.send("How about no", ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_slap_bot", locale), ctx.channel)
            # return await general.send(f"What did {user.name} even do to you?", ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "bite", 3)
        title, footer = get_data(ctx.author, user, "bite", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        # embed.title = f"**{ctx.author.name}** just bit **{user.name}**"
        embed.set_image(url=random.choice(self.bite))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="slap")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def slap(self, ctx: commands.Context, user: discord.Member):
        """ Slap someone """
        locale = langs.gl(ctx.guild, self.db)
        if ctx.author == user:
            return await general.send(langs.gls("social_slap_self", locale), ctx.channel)
            # return await general.send(f"Self harm bad {emotes.BlobCatPolice}", ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("social_slap_suager", locale, ctx.author.name), ctx.channel)
            # return await general.send(f"We are no longer friends, {ctx.author.name}", ctx.channel)
        if user.id == 302851022790066185:
            return await general.send(langs.gls("social_forbidden", locale), ctx.channel)
            # return await general.send("You can't do that.", ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_slap_bot", locale), ctx.channel)
            # return await general.send(f"What did {user.name} even do to you?", ctx.channel)
        if is_fucked(self.slap):
            self.slap = await lists.get_images(self.bot, 'v')
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "slap", 10)
        title, footer = get_data(ctx.author, user, "slap", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        # embed.title = f"**{user.name}** just got slapped by **{ctx.author.name}**"
        embed.set_image(url=random.choice(self.slap))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="sniff")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def smell(self, ctx: commands.Context, user: discord.Member):
        """ Sniff someone """
        locale = langs.gl(ctx.guild, self.db)
        if is_fucked(self.smell):
            self.smell = await lists.get_images(self.bot, 'n')
        if ctx.author == user:
            return await general.send(langs.gls("social_poke_self", locale), ctx.channel)
            # return await general.send(f"Why though? {emotes.UmmOK}", ctx.channel)
        if user.id == 302851022790066185:
            return await general.send(langs.gls("social_forbidden", locale), ctx.channel)
            # return await general.send("How about you don't?", ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("social_sniff_suager", locale), ctx.channel)
            # return await general.send(f"Why would you do that?", ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_bot", locale), ctx.channel)
            # return await general.send(f"So how does a bot smell, huh?", ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "sniff", 11)
        title, footer = get_data(ctx.author, user, "sniff", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        # embed.title = f"**{ctx.author.name}** just sniffed **{user.name}**"
        embed.set_image(url=random.choice(self.smell))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="highfive")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def highfive(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a high five """
        locale = langs.gl(ctx.guild, self.db)
        if is_fucked(self.highfive):
            self.highfive = await lists.get_images(self.bot, 'i')
        if ctx.author == user:
            return await general.send(langs.gls("social_alone", locale), ctx.channel)
            # return await general.send("Alone?", ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("social_high_five_suager", locale, ctx.author.name), ctx.channel)
            # return await general.send(f"*High fives {ctx.author.name} back*", ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_bot", locale), ctx.channel)
            # return await general.send(f"I don't think {user.name} is going to respond...", ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "high_five", 5)
        title, footer = get_data(ctx.author, user, "high_five", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        # embed.title = f"**{ctx.author.name}** gave **{user.name}** a high five"
        embed.set_image(url=random.choice(self.highfive))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="poke")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def poke(self, ctx: commands.Context, user: discord.Member):
        """ Poke someone """
        locale = langs.gl(ctx.guild, self.db)
        if is_fucked(self.poke):
            self.poke = await lists.get_images(self.bot, 'P')
        if ctx.author == user:
            return await general.send(langs.gls("social_poke_self", locale), ctx.channel)
            # return await general.send(f"Why though? {emotes.UmmOK}", ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("social_poke_suager", locale, ctx.author.name), ctx.channel)
            # return await general.send(f"What do you want, {ctx.author.name}? {emotes.Wha}", ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_bot", locale), ctx.channel)
            # return await general.send(f"I don't think {user.name} is going to respond...", ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "poke", 12)
        title, footer = get_data(ctx.author, user, "poke", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        # embed.title = f"**{ctx.author.name}** just poked **{user.name}**"
        embed.set_image(url=random.choice(self.poke))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="boop", aliases=["bap"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def boop(self, ctx: commands.Context, user: discord.Member):
        """ Why is this a thing? """
        locale = langs.gl(ctx.guild, self.db)
        if is_fucked(self.boop):
            self.boop = await lists.get_images(self.bot, 'B')
        if ctx.author == user:
            return await general.send(langs.gls("social_poke_self", locale), ctx.channel)
            # return await general.send(f"Why though? {emotes.UmmOK}", ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("social_boop_suager", locale), ctx.channel)
            # return await general.send("Huh?", ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_bot", locale), ctx.channel)
            # return await general.send(f"I don't think {user.name} is going to respond...", ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        given, received = self.data_update(ctx.author.id, user.id, "boop", 13)
        title, footer = get_data(ctx.author, user, "boop", locale, given, received)
        embed.title = title
        embed.set_footer(text=footer)
        # embed.title = f"**{ctx.author.name}** just booped **{user.name}**"
        embed.set_image(url=random.choice(self.boop))
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="bang", aliases=["fuck"], hidden=True)
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def fuck(self, ctx, user: discord.Member):
        """ Bang someone """
        locale = langs.gl(ctx.guild, self.db)
        if not ctx.channel.is_nsfw():
            return await general.send(langs.gls("social_bang_channel", locale), ctx.channel)
            # return await general.send("This command can only be used in **NSFW channels**.", ctx.channel)
        if user.id == 302851022790066185:
            return await general.send(langs.gls("social_forbidden", locale), ctx.channel)
            # return await general.send("You're not allowed to do that.", ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(f"{emotes.Deny} {langs.gls('generic_no', locale)}.", ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_bang_bot", locale), ctx.channel)
            # return await general.send(f"Why would you ever want to do that to a bot {emotes.KannaSpook}", ctx.channel)
        if user == ctx.author:
            return await general.send(emotes.UmmOK, ctx.channel)
        given, received = self.data_update(ctx.author.id, user.id, "bang", 2)
        t1, t2 = ctx.author.name, user.name
        out = langs.gls("social_bang_main", locale, t1, t2)
        _given, _received = langs.plural(given, "generic_times", locale), langs.plural(received, "generic_times", locale)
        counter1 = langs.gls("social_bang_counter", locale, t1, t2, _given)
        counter2 = langs.gls("social_bang_counter", locale, t2, t1, _received)
        # title, footer = get_data(ctx.author, user, "hug", locale, given, received)
        # embed.title = title
        # embed.set_footer(text=footer)
        # out = f"**{ctx.author.name}** is not {ctx.invoked_with}ing **{user.name}**..."
        # if ctx.channel.id == 672535025698209821:
        #     out += f"\nThis has now happened {number} times in this server"
        return await general.send(f"{out}\n{counter1}\n{counter2}", ctx.channel)

    @commands.command(name="ship")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def ship(self, ctx: commands.Context, user1: discord.Member, user2: discord.Member):
        """ Build a ship """
        locale = langs.gl(ctx.guild, self.db)
        pr = False
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            if user1.id != 302851022790066185 and user2.id != 302851022790066185:
                return await general.send(f"{emotes.Deny} {langs.gls('generic_no', locale)}.", ctx.channel)
            pr = True
        if (user1.bot ^ user2.bot) and not pr:
            return await general.send(langs.gls("social_ship_bot", locale), ctx.channel)
            # return await general.send("Bots aren't programmed to feel love to normal users...", ctx.channel)
        if user1 == user2:
            return await general.send(langs.gls("social_alone", locale), ctx.channel)
            # return await general.send("Alone?", ctx.channel)
        av1 = user1.avatar_url_as(size=1024)
        av2 = user2.avatar_url_as(size=1024)
        link = f"https://api.alexflipnote.dev/ship?user={av1}&user2={av2}"
        bio = BytesIO(await http.get(link, res_method="read"))
        if bio is None:
            return await general.send("The image was not generated...", ctx.channel)
        __names = [len(user1.name), len(user2.name)]
        _names = [int(x / 2) for x in __names]
        n1 = user1.name[:_names[0]]
        n2 = user1.name[_names[0]:]
        n3 = user2.name[:_names[1]]
        n4 = user2.name[_names[1]:]
        names = [f"{n1}{n3}", f"{n1}{n4}", f"{n2}{n3}", f"{n2}{n4}", f"{n3}{n1}", f"{n4}{n1}", f"{n3}{n2}", f"{n4}{n2}"]
        message = langs.gls("social_ship", locale)
        # message = "Nice shipping!\nPossible ship names:"
        for i, j in enumerate(names, start=1):
            message += f"\n{langs.gns(i, locale)}) **{j}**"
        # data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        # data_receive1 = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user1.id, ctx.guild.id))
        # data_receive2 = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user2.id, ctx.guild.id))
        # if not data_giver:
        #     data = self.empty.copy()
        #     data[0] = ctx.author.id
        #     data[1] = ctx.guild.id
        #     data[27] = 1
        #     self.db.execute(self.insert, tuple(data))
        # else:
        #     self.db.execute("UPDATE counters SET ships_built=? WHERE uid=? AND gid=?",
        #                     (data_giver["ships_built"] + 1, ctx.author.id, ctx.guild.id))
        # if not data_receive1:
        #     data = self.empty.copy()
        #     data[0] = user1.id
        #     data[1] = ctx.guild.id
        #     data[26] = 1
        #     self.db.execute(self.insert, tuple(data))
        # else:
        #     self.db.execute("UPDATE counters SET shipped=? WHERE uid=? AND gid=?",
        #                     (data_receive1["shipped"] + 1, user1.id, ctx.guild.id))
        # if not data_receive2:
        #     data = self.empty.copy()
        #     data[0] = user2.id
        #     data[1] = ctx.guild.id
        #     data[26] = 1
        #     self.db.execute(self.insert, tuple(data))
        # else:
        #     self.db.execute("UPDATE counters SET shipped=? WHERE uid=? AND gid=?",
        #                     (data_receive2["shipped"] + 1, user2.id, ctx.guild.id))
        return await general.send(message, ctx.channel, file=discord.File(bio, filename="ship.png"))

    @commands.command(name="sleepy")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def sleepy(self, ctx):
        """ You're sleepy """
        locale = langs.gl(ctx.guild, self.db)
        if is_fucked(self.sleepy):
            self.sleepy = await lists.get_images(self.bot, 's')
        embed = discord.Embed(colour=general.random_colour())
        embed.title = langs.gls("social_sleepy", locale, ctx.author.name)
        # embed.title = f"**{ctx.author.name}** is sleepy"
        embed.set_image(url=random.choice(self.sleepy))
        # self.data_update2(ctx.author.id, ctx.guild.id, "sleepy", 30)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="cry")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def cry(self, ctx):
        """ You're crying """
        locale = langs.gl(ctx.guild, self.db)
        if is_fucked(self.cry):
            self.cry = await lists.get_images(self.bot, 'r')
        embed = discord.Embed(colour=general.random_colour())
        embed.title = langs.gls("social_cry", locale, ctx.author.name)
        # embed.title = f"**{ctx.author.name}** is crying"
        embed.set_image(url=random.choice(self.cry))
        # self.data_update2(ctx.author.id, ctx.guild.id, "cried", 29)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="blush")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def blush(self, ctx):
        """ You blush """
        locale = langs.gl(ctx.guild, self.db)
        if is_fucked(self.blush):
            self.blush = await lists.get_images(self.bot, 'u')
        embed = discord.Embed(colour=general.random_colour())
        embed.title = langs.gls("social_blush", locale, ctx.author.name)
        # embed.title = f"**{ctx.author.name}** blushes"
        embed.set_image(url=random.choice(self.blush))
        # self.data_update2(ctx.author.id, ctx.guild.id, "blushed", 28)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="smile")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def smile(self, ctx):
        """ You're smiling """
        locale = langs.gl(ctx.guild, self.db)
        if is_fucked(self.smile):
            self.smile = await lists.get_images(self.bot, 'm')
        embed = discord.Embed(colour=general.random_colour())
        embed.title = langs.gls("social_smile", locale, ctx.author.name)
        # embed.title = f"**{ctx.author.name}** smiles"
        embed.set_image(url=random.choice(self.smile))
        # self.data_update2(ctx.author.id, ctx.guild.id, "smiled", 31)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="bean")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def bean(self, ctx: commands.Context, user: discord.Member):
        """ Bean someone """
        locale = langs.gl(ctx.guild, self.db)
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.id == 302851022790066185:
            return await general.send(langs.gls("social_forbidden", locale), ctx.channel)
            # return await general.send("You're not allowed to do that.", ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("social_forbidden", locale), ctx.channel)
            # return await general.send("You can't do that", ctx.channel)
        if user.id == ctx.guild.owner.id and ctx.author.id != 302851022790066185:
            return await general.send(langs.gls("social_bean_owner", locale), ctx.channel)
            # return await general.send("Imagine trying to bean the server owner, lol", ctx.channel)
        # id1, id2 = ctx.author.id, user.id
        # self.data_update(id1, id2, ctx.guild.id, "beans_given", "beaned", 24, 25)
        # bean = f"{emotes.Allow} **{user.name}** is now dismissed from **{ctx.guild.name}**"
        bean = langs.gls("social_bean", locale, user.name, ctx.guild.name)
        return await general.send(bean, ctx.channel)

    @commands.command(name="bad")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def bad(self, ctx: commands.Context, user: discord.Member):
        """ Bad user """
        locale = langs.gl(ctx.guild, self.db)
        bad_self = False
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.id == 302851022790066185:
            bad_self = True
        elif user.id == self.bot.user.id:
            return await general.send(langs.gls("social_bad_suager", locale), ctx.channel)
            # return await general.send("If I'm bad, why am I still in this server?", ctx.channel)
        if bad_self:
            user = ctx.author
        # if not bad_self:
        #     id1, id2 = ctx.author.id, user.id
        # else:
        #     id1, id2 = -1, ctx.author.id
        #     user = ctx.author
        # self.data_update(id1, id2, ctx.guild.id, "bad_given", "bad_received", 22, 23)
        return await image_gen(ctx, user, "bad", f"bad_{user.id}")

    @commands.command(name="trash")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def trash(self, ctx, user: discord.Member):
        """ Show someone their home """
        locale = langs.gl(ctx.guild, self.db)
        # trash_self = False
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("social_bad_suager", locale), ctx.channel)
            # return await general.send("If I'm trash, why am I still in this server?", ctx.channel)
        a1, a2 = [ctx.author.avatar_url, user.avatar_url]
        if user.id == 302851022790066185:
            a2, a1 = a1, a2
        #     trash_self = True
        # if not trash_self:
        #     id1, id2 = ctx.author.id, user.id
        # else:
        #     id1, id2 = user.id, ctx.author.id
        # self.data_update(id1, id2, ctx.guild.id, "trash_given", "trashed", 26, 27)
        bio = BytesIO(await http.get(f"https://api.alexflipnote.dev/trash?face={a1}&trash={a2}", res_method="read"))
        if bio is None:
            return await general.send("An error occurred...", ctx.channel)
        return await general.send(None, ctx.channel, file=discord.File(bio, filename=f"trash_{user.id}.png"))

    @commands.command(name="cookie")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def cookie(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a cookie """
        locale = langs.gl(ctx.guild, self.db)
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_food_bot", locale), ctx.channel)
        output = give(ctx.author.name, user.name, "🍪", locale)
        # number = self.data_update3(user.id, ctx.guild.id, "cookies_received", "cookies_eaten", 36)
        # output += f"**{user.name}** now has **{number} cookies** in **{ctx.guild.name}**"
        return await general.send(output, ctx.channel)

    @commands.command(name="lemon")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def lemon(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a lemon """
        locale = langs.gl(ctx.guild, self.db)
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_food_bot", locale), ctx.channel)
        output = give(ctx.author.name, user.name, "🍋", locale)
        # number = self.data_update3(user.id, ctx.guild.id, "lemons_received", "lemons_eaten", 40)
        # output += f"**{user.name}** now has **{number} lemons** in **{ctx.guild.name}**"
        return await general.send(output, ctx.channel)

    @commands.command(name="carrot")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def carrot(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a carrot """
        locale = langs.gl(ctx.guild, self.db)
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_food_bot", locale), ctx.channel)
        output = give(ctx.author.name, user.name, "🥕", locale)
        # number = self.data_update3(user.id, ctx.guild.id, "carrots_received", "carrots_eaten", 34)
        # output += f"**{user.name}** now has **{number} carrots** in **{ctx.guild.name}**"
        return await general.send(output, ctx.channel)

    @commands.command(name="fruit")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def fruit_snacks(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a fruit """
        locale = langs.gl(ctx.guild, self.db)
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.bot:
            return await general.send(langs.gls("social_food_bot", locale), ctx.channel)
        # if user.id == self.bot.user.id:
        #     return await general.send("I can't eat normal food...", ctx.channel)
        # if user.bot:
        #     return await general.send("Bots can't eat normal food...", ctx.channel)
        output = give(ctx.author.name, user.name, random.choice(list("🍏🍎🍐🍊🍌🍉🍇🍓🍒🍍")), locale)
        # number = self.data_update3(user.id, ctx.guild.id, "fruits_received", "fruits_eaten", 38)
        # output += f"**{user.name}** now has **{number} fruits** in **{ctx.guild.name}**"
        return await general.send(output, ctx.channel)

    # @commands.command(name="eat")
    # @commands.guild_only()
    # @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    # async def eat_something(self, ctx: commands.Context, what: str):
    #     """ Eat something """
    #     if what == "cookie":
    #         fr, fe = "cookies_received", "cookies_eaten"
    #     elif what == "carrot":
    #         fr, fe = "carrots_received", "carrots_eaten"
    #     elif what == "fruit":
    #         fr, fe = "fruits_received", "fruits_eaten"
    #     elif what == "lemon":
    #         fr, fe = "lemons_received", "lemons_eaten"
    #     else:
    #         return await general.send("You can only eat cookies, carrots, fruits, and lemons.", ctx.channel)
    #     data = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
    #     if not data:
    #         return await general.send(f"You have no {what}s right now...", ctx.channel)
    #     left = data[fr] - data[fe]
    #     if left < 1:
    #         return await general.send(f"You have no {what}s left...", ctx.channel)
    #     left -= 1
    #     self.db.fetchrow(f"UPDATE counters SET {fe}=? WHERE uid=? AND gid=?", (data[fe] + 1, ctx.author.id, ctx.guild.id))
    #     return await general.send(f"**{ctx.author.name}** just ate a **{what}** and has **{left}** left.", ctx.channel)

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

    # @commands.command(name="counters", aliases=["spamstats"])
    # @commands.guild_only()
    # @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    # async def counters(self, ctx: commands.Context, who: discord.Member = None):
    #     """ Check your or someone else's counts! """
    #     user = who or ctx.author
    #     data = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
    #     if not data:
    #         return await ctx.send(f"There is no data available for {user}...")
    #     embed = discord.Embed(colour=general.random_colour())
    #     embed.title = f"Spam stats for **{user.name}** in **{ctx.guild.name}**"
    #     embed.set_thumbnail(url=user.avatar_url_as(static_format="png", size=1024))
    #     for i in range(1, len(self.names) - 1):
    #         value = ""
    #         for j in range(len(self.keys[self.names[i]])):
    #             val = data[self.keys[self.names[i]][j]]
    #             name = self.key_names[self.names[i]][j]
    #             if val is not None and val > 0:
    #                 value += f"{val:,} - {name}\n"
    #         if value == "":
    #             value = "No data available"
    #         embed.add_field(name=self.names[i], inline=False, value=value)
    #     cr, ce = data["carrots_received"], data["carrots_eaten"]
    #     cl = cr - ce
    #     ar, ae = data["cookies_received"], data["cookies_eaten"]
    #     al = ar - ae
    #     fr, fe = data["fruits_received"], data["fruits_eaten"]
    #     fl = fr - fe
    #     lr, le = data["lemons_received"], data["lemons_eaten"]
    #     ll = lr - le
    #     embed.add_field(name=self.names[4], inline=False,
    #                     value=f"{cr:,} carrots received\n{ce:,} carrots eaten\n{cl:,} carrots left\n\n"
    #                           f"{ar:,} cookies received\n{ae:,} cookies eaten\n{al:,} cookies left\n\n"
    #                           f"{fr:,} fruits received\n{fe:,} fruits eaten\n{fl:,} fruits left\n\n"
    #                           f"{lr:,} lemons received\n{le:,} lemons eaten\n{ll:,} lemons left")
    #     return await general.send(None, ctx.channel, embed=embed)


def setup(bot):
    bot.add_cog(Social(bot))
