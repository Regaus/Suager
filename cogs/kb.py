import random
from io import BytesIO

import discord
from discord.ext import commands

from cogs import main
from cogs.images import image_gen
from utils import lists, emotes, generic, logs, http, database


def is_fucked(something):
    return something == [] or something == lists.error or something == [lists.error]


but_why = "https://cdn.discordapp.com/attachments/610482988123422750/673642028357386241/butwhy.gif"


def give(u1: str, u2: str, emote: str):
    return f"{u2}, you got a {emote} from {u1}\n\n(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ {emote}"


class Social(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pat, self.hug, self.kiss, self.lick, self.cuddle, self.bite, self.sleepy, self.smell, self.cry, \
            self.slap, self.blush, self.smile, self.highfive, self.poke, self.boop = [lists.error] * 15
        self.type = main.version
        self.banned = [690254056354087047, 694684764074016799]
        self.db = database.Database()
        self.insert = f"INSERT INTO counters VALUES ({'?, ' * 45}?)"
        self.empty = [0] * 46

    @commands.command(name="pat", aliases=["pet"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def pat(self, ctx, user: discord.Member):
        """ Pat someone """
        if is_fucked(self.pat):
            self.pat = await lists.get_images(self.bot, 'p')
        if ctx.author == user:
            return await ctx.send("Don't be like that ;-;")
        if user.id == self.bot.user.id:
            return await ctx.send(f"Thanks, {ctx.author.name} :3 {emotes.AlexHeart} {emotes.AlexPat}")
        if user.id == 424472476106489856 and ctx.author.id not in [689158123352883340]:
            return await ctx.send(f"{emotes.Deny} Those who kill Regaus deserve no love.")
        embed = discord.Embed(colour=generic.random_colour())
        embed.description = f"**{user.name}** got a pat from **{ctx.author.name}**"
        embed.set_image(url=random.choice(self.pat))
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data_giver:
            data = self.empty.copy()
            data[0] = ctx.author.id
            data[1] = ctx.guild.id
            data[16] = 1
            self.db.execute(self.insert, tuple(data))
        else:
            self.db.execute("UPDATE counters SET pats_given=? WHERE uid=? AND gid=?",
                            (data_giver["pats_given"] + 1, ctx.author.id, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = user.id
            data[1] = ctx.guild.id
            data[17] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute("UPDATE counters SET pats_received=? WHERE uid=? AND gid=?",
                            (data_receive["pats_received"] + 1, user.id, ctx.guild.id))
            number = data_receive["pats_received"] + 1
        embed.set_footer(text=f"{user.name} has now received {number} pat(s) in this server!")
        return await ctx.send(embed=embed)

    @commands.command(name="hug")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def hug(self, ctx, user: discord.Member):
        """ Hug someone """
        if is_fucked(self.hug):
            self.hug = await lists.get_images(self.bot, 'h')
        if ctx.author == user:
            return await ctx.send("Alone? ;-;", embed=discord.Embed(colour=generic.random_colour()).set_image(
                url="https://cdn.discordapp.com/attachments/610482988123422750/673641089218904065/selfhug.gif"))
        if user.id == self.bot.user.id:
            return await ctx.send(f"*Hugs {ctx.author.name} back* {emotes.AlexHeart}")
        if user.id == 424472476106489856 and ctx.author.id not in [417390734690484224, 689158123352883340]:
            return await ctx.send(f"{emotes.Deny} Those who kill Regaus deserve no love.")
        embed = discord.Embed(colour=generic.random_colour())
        embed.description = f"**{user.name}** got a hug from **{ctx.author.name}**"
        embed.set_image(url=random.choice(self.hug))
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data_giver:
            data = self.empty.copy()
            data[0] = ctx.author.id
            data[1] = ctx.guild.id
            data[10] = 1
            self.db.execute(self.insert, tuple(data))
        else:
            self.db.execute("UPDATE counters SET hugs_given=? WHERE uid=? AND gid=?",
                            (data_giver["hugs_given"] + 1, ctx.author.id, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = user.id
            data[1] = ctx.guild.id
            data[11] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute("UPDATE counters SET hugs_received=? WHERE uid=? AND gid=?",
                            (data_receive["hugs_received"] + 1, user.id, ctx.guild.id))
            number = data_receive["hugs_received"] + 1
        embed.set_footer(text=f"{user.name} has now received {number} hug(s) in this server!")
        return await ctx.send(embed=embed)

    @commands.command(name="cuddle")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def cuddle(self, ctx, user: discord.Member):
        """ Cuddle someone """
        if is_fucked(self.cuddle):
            self.cuddle = await lists.get_images(self.bot, 'c')
        if ctx.author == user:
            return await ctx.send("Alone? ;-;")
        if user.id == self.bot.user.id:
            return await ctx.send(f"*Cuddles {ctx.author.name} back* {emotes.AlexHeart}")
        if user.id == 424472476106489856 and ctx.author.id not in [417390734690484224, 689158123352883340]:
            return await ctx.send(f"{emotes.Deny} Those who kill Regaus deserve no love.")
        embed = discord.Embed(colour=generic.random_colour())
        embed.description = f"**{user.name}** got a cuddle from **{ctx.author.name}**"
        embed.set_image(url=random.choice(self.cuddle))
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data_giver:
            data = self.empty.copy()
            data[0] = ctx.author.id
            data[1] = ctx.guild.id
            data[6] = 1
            self.db.execute(self.insert, tuple(data))
        else:
            self.db.execute("UPDATE counters SET cuddles_given=? WHERE uid=? AND gid=?",
                            (data_giver["cuddles_given"] + 1, ctx.author.id, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = user.id
            data[1] = ctx.guild.id
            data[7] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute("UPDATE counters SET cuddles_received=? WHERE uid=? AND gid=?",
                            (data_receive["cuddles_received"] + 1, user.id, ctx.guild.id))
            number = data_receive["cuddles_received"] + 1
        embed.set_footer(text=f"{user.name} has now received {number} cuddle(s) in this server!")
        return await ctx.send(embed=embed)

    @commands.command(name="lick", aliases=["licc"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def lick(self, ctx, user: discord.Member = None):
        """ Lick someone """
        if ctx.guild.id == 690162603275714574:
            return await ctx.send(f"{emotes.Deny} This command is disabled in this server due to a number of "
                                  f"complaints from members.")
        if user is None:
            return await ctx.send_help(str(ctx.command))
        if is_fucked(self.lick):
            self.lick = await lists.get_images(self.bot, 'l')
        embed = discord.Embed(colour=generic.random_colour())
        if user == ctx.author:
            return await ctx.send(embed=embed.set_image(
                url="https://cdn.discordapp.com/attachments/610482988123422750/673644219314733106/selflick.gif"))
        if user.id == self.bot.user.id:
            return await ctx.send(f"W-why did you lick me, {ctx.author.name}?", embed=embed.set_image(url=but_why))
        embed.description = f"**{user.name}** was licked by **{ctx.author.name}**"
        embed.set_image(url=random.choice(self.lick))
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data_giver:
            data = self.empty.copy()
            data[0] = ctx.author.id
            data[1] = ctx.guild.id
            data[14] = 1
            self.db.execute(self.insert, tuple(data))
        else:
            self.db.execute("UPDATE counters SET licks_given=? WHERE uid=? AND gid=?",
                            (data_giver["licks_given"] + 1, ctx.author.id, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = user.id
            data[1] = ctx.guild.id
            data[15] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute("UPDATE counters SET licks_received=? WHERE uid=? AND gid=?",
                            (data_receive["licks_received"] + 1, user.id, ctx.guild.id))
            number = data_receive["licks_received"] + 1
        embed.set_footer(text=f"{user.name} has now received {number} lick(s) in this server!")
        return await ctx.send(embed=embed)

    @commands.command(name="kiss")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def kiss(self, ctx, user: discord.Member):
        """ Kiss someone """
        if is_fucked(self.kiss):
            self.kiss = await lists.get_images(self.bot, 'k')
        if user == ctx.author:
            return await ctx.send("Alone? ;-;")
        if user.id == self.bot.user.id:
            return await ctx.send(f"Thanks, {ctx.author.name} {emotes.AlexHeart}! "
                                  f"But, I'm a bot... I wasn't programmed to feel love ;-;")
        if user.id == 424472476106489856 and ctx.author.id not in [689158123352883340]:
            return await ctx.send(f"{emotes.Deny} Those who kill Regaus deserve no love.")
        embed = discord.Embed(colour=generic.random_colour())
        embed.description = f"**{user.name}** was kissed by **{ctx.author.name}**"
        embed.set_image(url=random.choice(self.kiss))
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data_giver:
            data = self.empty.copy()
            data[0] = ctx.author.id
            data[1] = ctx.guild.id
            data[12] = 1
            self.db.execute(self.insert, tuple(data))
        else:
            self.db.execute("UPDATE counters SET kisses_given=? WHERE uid=? AND gid=?",
                            (data_giver["kisses_given"] + 1, ctx.author.id, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = user.id
            data[1] = ctx.guild.id
            data[13] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute("UPDATE counters SET kisses_received=? WHERE uid=? AND gid=?",
                            (data_receive["kisses_received"] + 1, user.id, ctx.guild.id))
            number = data_receive["kisses_received"] + 1
        embed.set_footer(text=f"{user.name} has now received {number} kiss(es) in this server!")
        return await ctx.send(embed=embed)

    @commands.command(name="bite")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def bite(self, ctx, user: discord.Member = None):
        """ Bite someone """
        if ctx.guild.id == 690162603275714574:
            return await ctx.send(f"{emotes.Deny} This command is disabled in this server.")
        if user is None:
            return await ctx.send_help(str(ctx.command))
        if is_fucked(self.bite):
            self.bite = await lists.get_images(self.bot, 'b')
        if user == ctx.author:
            return await ctx.send(f"{emotes.Deny} Self harm bad")
        if user.id in generic.get_config()["owners"]:
            return await ctx.send(f"{emotes.Deny} {ctx.author.name}, you are not allowed to do that.")
        if user.id == self.bot.user.id:
            return await ctx.send(f"Ow.. why would you bite me, {ctx.author.name}? "
                                  f"It h-hurts ;-; {emotes.AlexHeartBroken}")
        embed = discord.Embed(colour=generic.random_colour())
        embed.description = f"**{user.name}** was bitten by **{ctx.author.name}**"
        embed.set_image(url=random.choice(self.bite))
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data_giver:
            data = self.empty.copy()
            data[0] = ctx.author.id
            data[1] = ctx.guild.id
            data[4] = 1
            self.db.execute(self.insert, tuple(data))
        else:
            self.db.execute("UPDATE counters SET bites_given=? WHERE uid=? AND gid=?",
                            (data_giver["bites_given"] + 1, ctx.author.id, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = user.id
            data[1] = ctx.guild.id
            data[5] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute("UPDATE counters SET bites_received=? WHERE uid=? AND gid=?",
                            (data_receive["bites_received"] + 1, user.id, ctx.guild.id))
            number = data_receive["bites_received"] + 1
        embed.set_footer(text=f"{user.name} has now got bitten {number} time(s) in this server!")
        return await ctx.send(embed=embed)

    @commands.command(name="sleepy")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def sleepy(self, ctx):
        """ You're sleepy """
        if is_fucked(self.sleepy):
            self.sleepy = await lists.get_images(self.bot, 's')
        embed = discord.Embed(colour=generic.random_colour())
        embed.description = f"**{ctx.author.name}** is sleepy..."
        embed.set_image(url=random.choice(self.sleepy))
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not data_giver:
            data = self.empty.copy()
            data[0] = ctx.author.id
            data[1] = ctx.guild.id
            data[32] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute("UPDATE counters SET sleepy=? WHERE uid=? AND gid=?",
                            (data_giver["sleepy"] + 1, ctx.author.id, ctx.guild.id))
            number = data_giver["sleepy"] + 1
        embed.set_footer(text=f"{ctx.author.name} has now been sleepy {number} time(s) in this server!")
        return await ctx.send(embed=embed)

    @commands.command(name="cry")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def cry(self, ctx):
        """ You're crying """
        if is_fucked(self.cry):
            self.cry = await lists.get_images(self.bot, 'r')
        embed = discord.Embed(colour=generic.random_colour())
        embed.description = f"**{ctx.author.name}** is crying"
        embed.set_image(url=random.choice(self.cry))
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not data_giver:
            data = self.empty.copy()
            data[0] = ctx.author.id
            data[1] = ctx.guild.id
            data[31] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute("UPDATE counters SET cried=? WHERE uid=? AND gid=?",
                            (data_giver["cried"] + 1, ctx.author.id, ctx.guild.id))
            number = data_giver["cried"] + 1
        embed.set_footer(text=f"{ctx.author.name} has now cried {number} time(s) in this server!")
        return await ctx.send(embed=embed)

    @commands.command(name="blush")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def blush(self, ctx):
        """ You blush """
        if is_fucked(self.blush):
            self.blush = await lists.get_images(self.bot, 'u')
        embed = discord.Embed(colour=generic.random_colour())
        embed.description = f"**{ctx.author.name}** blushes"
        embed.set_image(url=random.choice(self.blush))
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not data_giver:
            data = self.empty.copy()
            data[0] = ctx.author.id
            data[1] = ctx.guild.id
            data[30] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute("UPDATE counters SET blushed=? WHERE uid=? AND gid=?",
                            (data_giver["blushed"] + 1, ctx.author.id, ctx.guild.id))
            number = data_giver["blushed"] + 1
        embed.set_footer(text=f"{ctx.author.name} has now blushed {number} time(s) in this server!")
        return await ctx.send(embed=embed)

    @commands.command(name="smile")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def smile(self, ctx):
        """ You smile """
        if is_fucked(self.smile):
            self.smile = await lists.get_images(self.bot, 'm')
        embed = discord.Embed(colour=generic.random_colour())
        embed.description = f"**{ctx.author.name}** smiles"
        embed.set_image(url=random.choice(self.smile))
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not data_giver:
            data = self.empty.copy()
            data[0] = ctx.author.id
            data[1] = ctx.guild.id
            data[33] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute("UPDATE counters SET smiled=? WHERE uid=? AND gid=?",
                            (data_giver["smiled"] + 1, ctx.author.id, ctx.guild.id))
            number = data_giver["smiled"] + 1
        embed.set_footer(text=f"{ctx.author.name} has now smiled {number} time(s) in this server!")
        return await ctx.send(embed=embed)

    @commands.command(name="slap", aliases=["kill", "shoot", "punch", "hit"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def slap(self, ctx, user: discord.Member = None):
        """ Violence! """
        if ctx.guild.id == 690162603275714574:
            return await ctx.send(f"{emotes.Deny} This command is disabled in this server.")
        if user is None:
            return await ctx.send_help(str(ctx.command))
        if user == ctx.author:
            return await ctx.send(f"{emotes.Deny} Self harm bad",
                                  embed=discord.Embed(colour=generic.random_colour()).set_image(url=but_why))
        if user.id in generic.get_config()["owners"]:
            return await ctx.send(f"{emotes.Deny} You are not allowed to do that, {ctx.author.name}")
        if user.id == self.bot.user.id:
            return await ctx.send(f"{ctx.author.name}, we can no longer be friends. ;-; {emotes.AlexHeartBroken}")
        if ctx.invoked_with == "slap":
            if is_fucked(self.slap):
                self.slap = await lists.get_images(self.bot, 'v')
            embed = discord.Embed(colour=generic.random_colour())
            embed.description = f"**{user.name}** was slapped by **{ctx.author.name}**"
            embed.set_image(url=random.choice(self.slap))
            data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
            data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
            if not data_giver:
                data = self.empty.copy()
                data[0] = ctx.author.id
                data[1] = ctx.guild.id
                data[18] = 1
                self.db.execute(self.insert, tuple(data))
            else:
                self.db.execute("UPDATE counters SET slaps_given=? WHERE uid=? AND gid=?",
                                (data_giver["slaps_given"] + 1, ctx.author.id, ctx.guild.id))
            if not data_receive:
                data = self.empty.copy()
                data[0] = user.id
                data[1] = ctx.guild.id
                data[19] = 1
                self.db.execute(self.insert, tuple(data))
                number = 1
            else:
                self.db.execute("UPDATE counters SET slaps_received=? WHERE uid=? AND gid=?",
                                (data_receive["slaps_received"] + 1, user.id, ctx.guild.id))
                number = data_receive["slaps_received"] + 1
            embed.set_footer(text=f"{user.name} has now got slapped {number} time(s) in this server!")
        else:
            embed = None
        return await ctx.send(f"Violence is never the answer, {ctx.author.name}!", embed=embed)

    @commands.command(name="smell", aliases=["sniff"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def smell(self, ctx, user: discord.Member):
        """ Smell/sniff someone """
        if is_fucked(self.smell):
            self.smell = await lists.get_images(self.bot, 'n')
        if user == ctx.author:
            return await ctx.send("How are you going to do that?")
        if user.id == self.bot.user.id:
            return await ctx.send(f"Why are you {ctx.invoked_with}ing me, {ctx.author.name}? ")
        embed = discord.Embed(colour=generic.random_colour())
        embed.description = f"**{user.name}** was {ctx.invoked_with}ed by **{ctx.author.name}**"
        embed.set_image(url=random.choice(self.smell))
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data_giver:
            data = self.empty.copy()
            data[0] = ctx.author.id
            data[1] = ctx.guild.id
            data[20] = 1
            self.db.execute(self.insert, tuple(data))
        else:
            self.db.execute("UPDATE counters SET sniffs_given=? WHERE uid=? AND gid=?",
                            (data_giver["sniffs_given"] + 1, ctx.author.id, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = user.id
            data[1] = ctx.guild.id
            data[21] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute("UPDATE counters SET sniffs_received=? WHERE uid=? AND gid=?",
                            (data_receive["sniffs_received"] + 1, user.id, ctx.guild.id))
            number = data_receive["sniffs_received"] + 1
        embed.set_footer(text=f"{user.name} has now got {ctx.invoked_with}ed {number} time(s) in this server!")
        return await ctx.send(embed=embed)

    @commands.command(name="bang", aliases=["fuck"], hidden=True)
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def fuck(self, ctx, user: discord.Member = None):
        """ Bang someone """
        if ctx.guild.id == 690162603275714574:
            return
        if user is None:
            return await ctx.send_help(str(ctx.command))
        if user.id == self.bot.user.id:
            return await ctx.send("No. I'm taken, find someone else.")
        if user == ctx.author:
            return await ctx.send("How are you going to do that?")
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data_giver:
            data = self.empty.copy()
            data[0] = ctx.author.id
            data[1] = ctx.guild.id
            data[2] = 1
            self.db.execute(self.insert, tuple(data))
        else:
            self.db.execute("UPDATE counters SET bangs_given=? WHERE uid=? AND gid=?",
                            (data_giver["bangs_given"] + 1, ctx.author.id, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = user.id
            data[1] = ctx.guild.id
            data[3] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute("UPDATE counters SET bangs_received=? WHERE uid=? AND gid=?",
                            (data_receive["bangs_received"] + 1, user.id, ctx.guild.id))
            number = data_receive["bangs_received"] + 1
        # embed.set_footer(text=f"{user.name} has now got {ctx.invoked_with}ed {number} time(s) in this server!")
        return await ctx.send(f"{emotes.Scary} {emotes.NotLikeThis} {ctx.author.name} is now "
                              f"{ctx.invoked_with}ing {user.name}...\n{user.name} has now got {ctx.invoked_with}ed "
                              f"{number} time(s) in this server!")

    @commands.command(name="bean")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def bean(self, ctx, user: discord.Member):
        """ Bean someone """
        bean_self = False
        if user == ctx.author:
            return await ctx.send(f"{emotes.Deny} How are you gonna do that?")
        if user.id == 302851022790066185:
            # return await ctx.send(f"{emotes.Deny} {ctx.author.name}, you are not allowed to do that.")
            bean_self = True
        if user.id == self.bot.user.id:
            # return await ctx.send(f"{emotes.Deny} {ctx.author.name}, you can't bean me.")
            bean_self = True
        if user.id == ctx.guild.owner.id and ctx.author.id != 302851022790066185:
            return await ctx.send(f"{emotes.Deny} Imagine beaning the owner, lol")
        if ctx.author.id == 424472476106489856:
            bean_self = True
        if not bean_self:
            id1, id2 = ctx.author.id, user.id
            index1, index2 = 24, 25
        else:
            id1, id2 = user.id, ctx.author.id
            index1, index2 = 25, 24
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (id1, ctx.guild.id))
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (id2, ctx.guild.id))
        if not data_giver:
            data = self.empty.copy()
            data[0] = id1
            data[1] = ctx.guild.id
            data[index1] = 1
            self.db.execute(self.insert, tuple(data))
        else:
            self.db.execute("UPDATE counters SET beans_given=? WHERE uid=? AND gid=?",
                            (data_giver["beans_given"] + 1, id1, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = id2
            data[1] = ctx.guild.id
            data[index2] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute("UPDATE counters SET beaned=? WHERE uid=? AND gid=?",
                            (data_receive["beaned"] + 1, id2, ctx.guild.id))
            number = data_receive["beaned"] + 1
        # embed.set_footer(text=f"{user.name} has now received {number} high five(s) in this server!")
        if not bean_self:
            bean = f"{emotes.Allow} {user.name}, you are dismissed from {ctx.guild.name}.\n" \
                   f"{user.name} has now been beaned {number} time(s) in this server!"
        else:
            bean = f"{emotes.Deny} {ctx.author.name}, you are dismissed from {ctx.guild.name}."
        return await ctx.send(bean)

    @commands.command(name="cookie")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def cookie(self, ctx, user: discord.Member):
        """ Give someone a cookie """
        if user == ctx.author:
            return await ctx.send(f"Don't be greedy, {ctx.author.name}! Share it!")
        if ctx.guild.id == 690162603275714574:  # OtakuTalk
            roles = [r.id for r in user.roles]
            if 696468113675255888 in roles:  # lemon squad
                return await ctx.send(f"Sour lemons like {user.name} don't deserve our cookies.")
        output = give(ctx.author.name, user.name, ":cookie:")
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = user.id
            data[1] = ctx.guild.id
            data[36] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute("UPDATE counters SET cookies_received=? WHERE uid=? AND gid=?",
                            (data_receive["cookies_received"] + 1, user.id, ctx.guild.id))
            number = data_receive["cookies_received"] + 1 - data_receive["cookies_eaten"]
        output += f"\n{user.name} now has {number} cookie(s) in this server!"
        return await ctx.send(output)

    @commands.command(name="lemon")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def lemon(self, ctx, user: discord.Member):
        """ Give someone a lemon """
        if user == ctx.author:
            return await ctx.send(f"Don't be greedy, {ctx.author.name}! Share it!")
        if ctx.guild.id == 690162603275714574:  # OtakuTalk
            roles = [r.id for r in user.roles]
            if 695246056945877053 in roles:  # Cookie Army
                return await ctx.send("You can't give lemons to a cookie.")
        output = give(ctx.author.name, user.name, ":lemon:")
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = user.id
            data[1] = ctx.guild.id
            data[40] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute("UPDATE counters SET lemons_received=? WHERE uid=? AND gid=?",
                            (data_receive["lemons_received"] + 1, user.id, ctx.guild.id))
            number = data_receive["lemons_received"] + 1 - data_receive["lemons_eaten"]
        output += f"\n{user.name} now has {number} lemon(s) in this server!"
        return await ctx.send(output)

    @commands.command(name="carrot")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def carrot(self, ctx, user: discord.Member):
        """ Give someone a carrot """
        if user == ctx.author:
            return await ctx.send(f"Don't be greedy, {ctx.author.name}! Share it!")
        output = give(ctx.author.name, user.name, ":carrot:")
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = user.id
            data[1] = ctx.guild.id
            data[34] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute("UPDATE counters SET carrots_received=? WHERE uid=? AND gid=?",
                            (data_receive["carrots_received"] + 1, user.id, ctx.guild.id))
            number = data_receive["carrots_received"] + 1 - data_receive["carrots_eaten"]
        output += f"\n{user.name} now has {number} carrot(s) in this server!"
        return await ctx.send(output)

    @commands.command(name="fruit", aliases=["fruitsnacks"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def fruit_snacks(self, ctx, user: discord.Member):
        """ Give someone a fruit snack """
        if user == ctx.author:
            return await ctx.send(f"Don't be greedy, {ctx.author.name}! Share it!")
        output = give(ctx.author.name, user.name, random.choice(
            [":green_apple:", ":apple:", ":pear:", ":tangerine:", ":banana:", ":watermelon:", ":grapes:",
             ":strawberry:", ":cherries:", ":pineapple:"]))
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = user.id
            data[1] = ctx.guild.id
            data[38] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute("UPDATE counters SET fruits_received=? WHERE uid=? AND gid=?",
                            (data_receive["fruits_received"] + 1, user.id, ctx.guild.id))
            number = data_receive["fruits_received"] + 1 - data_receive["fruits_eaten"]
        output += f"\n{user.name} now has {number} fruit(s) in this server!"
        return await ctx.send(output)

    @commands.command(name="eat")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def eat_something(self, ctx, what: str):
        """ Eat something """
        if what == "cookie":
            fr, fe = "cookies_received", "cookies_eaten"
        elif what == "carrot":
            fr, fe = "carrots_received", "carrots_eaten"
        elif what == "fruit":
            fr, fe = "fruits_received", "fruits_eaten"
        elif what == "lemon":
            fr, fe = "lemons_received", "lemons_eaten"
        elif what.lower() in ["<@273916273732222979>", "<@!273916273732222979>", "adde", "adde the chicken noodle"]:
            return await ctx.send(f"{ctx.author.name} just ate a piece of Adde the Chicken Noodle.")
        else:
            return await ctx.send("You can only eat the following: cookie, carrot, fruit, lemon, and "
                                  "Adde the Chicken Noodle.")
        data = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not data:
            return await ctx.send(f"You don't have any {what}s right now...")
        left = data[fr] - data[fe]
        if left < 1:
            return await ctx.send(f"You don't have any {what}s left...")
        left -= 1
        self.db.fetchrow(f"UPDATE counters SET {fe}=? WHERE uid=? AND gid=?",
                         (data[fe] + 1, ctx.author.id, ctx.guild.id))
        return await ctx.send(f"{ctx.author.name} just ate a {what}. You have {left} left.")

    @commands.command(name="bad")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
    async def bad(self, ctx, user: discord.Member):
        """ Bad user """
        bad_self = False
        if user.id == 302851022790066185:
            bad_self = True
        elif ctx.author.id == 424472476106489856:
            bad_self = True
        if not bad_self:
            id1, id2 = ctx.author.id, user.id
            index1, index2 = 22, 23
        else:
            id1, id2 = user.id, ctx.author.id
            index1, index2 = 23, 22
            user = ctx.author
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (id1, ctx.guild.id))
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (id2, ctx.guild.id))
        if user.id == self.bot.user.id:
            return await ctx.send(f"{emotes.AlexHeartBroken}")
        if not data_giver:
            data = self.empty.copy()
            data[0] = id1
            data[1] = ctx.guild.id
            data[index1] = 1
            self.db.execute(self.insert, tuple(data))
        else:
            self.db.execute("UPDATE counters SET bad_given=? WHERE uid=? AND gid=?",
                            (data_giver["bad_given"] + 1, id1, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = id2
            data[1] = ctx.guild.id
            data[index2] = 1
            self.db.execute(self.insert, tuple(data))
            # number = 1
        else:
            self.db.execute("UPDATE counters SET bad_received=? WHERE uid=? AND gid=?",
                            (data_receive["bad_received"] + 1, id2, ctx.guild.id))
            # number = data_receive["bad_received"] + 1
        # embed.set_footer(text=f"{user.name} has now received {number} high five(s) in this server!")
        return await image_gen(ctx, user, "bad", f"bad_{user.name.lower()}")

    @commands.command(name="trash")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
    async def trash(self, ctx, user: discord.Member):
        """ Show someone their home """
        trash_self = False
        if user == ctx.author:
            return await ctx.send("Don't call yourself trash")
        if user == ctx.bot.user:
            return await ctx.send(f"You dare calling me trash? {emotes.AlexHeartBroken}")
        a1, a2 = [ctx.author.avatar_url, user.avatar_url]
        if user.id == 302851022790066185:
            a2, a1 = a1, a2
            trash_self = True
        elif ctx.author.id == 424472476106489856:
            a2, a1 = a1, a2
            trash_self = True
        if not trash_self:
            id1, id2 = ctx.author.id, user.id
            index1, index2 = 28, 29
        else:
            id1, id2 = user.id, ctx.author.id
            index1, index2 = 23, 22
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (id1, ctx.guild.id))
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (id2, ctx.guild.id))
        bio = BytesIO(await http.get(f"https://api.alexflipnote.dev/trash?face={a1}&trash={a2}",
                                     res_method="read"))
        if bio is None:
            return await ctx.send("Something went wrong, couldn't generate image")
        if not data_giver:
            data = self.empty.copy()
            data[0] = id1
            data[1] = ctx.guild.id
            data[index1] = 1
            self.db.execute(self.insert, tuple(data))
        else:
            self.db.execute("UPDATE counters SET trash_given=? WHERE uid=? AND gid=?",
                            (data_giver["trash_given"] + 1, id1, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = id2
            data[1] = ctx.guild.id
            data[index2] = 1
            self.db.execute(self.insert, tuple(data))
            # number = 1
        else:
            self.db.execute("UPDATE counters SET trashed=? WHERE uid=? AND gid=?",
                            (data_receive["trashed"] + 1, id2, ctx.guild.id))
            # number = data_receive["trashed"] + 1
        # embed.set_footer(text=f"{user.name} has now received {number} high five(s) in this server!")
        return await ctx.send(file=discord.File(bio, filename=f"trash_{user.name}.png"))

    @commands.command(name="highfive")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def high_five(self, ctx, user: discord.Member):
        """ High five someone """
        if is_fucked(self.highfive):
            self.highfive = await lists.get_images(self.bot, 'i')
        if user == ctx.author:
            return await ctx.send("How are you going to do that?")
        if user.id == self.bot.user.id:
            return await ctx.send(f"*High fives {ctx.author.name} back*")
        embed = discord.Embed(colour=generic.random_colour())
        embed.description = f"**{user.name}** got a high five from **{ctx.author.name}**"
        embed.set_image(url=random.choice(self.highfive))
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data_giver:
            data = self.empty.copy()
            data[0] = ctx.author.id
            data[1] = ctx.guild.id
            data[8] = 1
            self.db.execute(self.insert, tuple(data))
        else:
            self.db.execute("UPDATE counters SET high_fives_given=? WHERE uid=? AND gid=?",
                            (data_giver["high_fives_given"] + 1, ctx.author.id, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = user.id
            data[1] = ctx.guild.id
            data[9] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute("UPDATE counters SET high_fives_received=? WHERE uid=? AND gid=?",
                            (data_receive["high_fives_received"] + 1, user.id, ctx.guild.id))
            number = data_receive["high_fives_received"] + 1
        embed.set_footer(text=f"{user.name} has now received {number} high five(s) in this server!")
        return await ctx.send(embed=embed)

    @commands.command(name="poke")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def poke(self, ctx, user: discord.Member):
        """ Poke someone """
        if is_fucked(self.poke):
            self.poke = await lists.get_images(self.bot, 'P')
        if user == ctx.author:
            return await ctx.send(f"{emotes.Deny} How are you going to do that?")
        if user.id == self.bot.user.id:
            return await ctx.send(f"Why did you poke me, {ctx.author.name}?")
        embed = discord.Embed(colour=generic.random_colour())
        embed.description = f"**{user.name}** got poked by **{ctx.author.name}**"
        embed.set_image(url=random.choice(self.poke))
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data_giver:
            data = self.empty.copy()
            data[0] = ctx.author.id
            data[1] = ctx.guild.id
            data[42] = 1
            self.db.execute(self.insert, tuple(data))
        else:
            pg = data_giver["pokes_given"]
            if pg is None:
                pg = 1
            else:
                pg = pg + 1
            self.db.execute("UPDATE counters SET pokes_given=? WHERE uid=? AND gid=?",
                            (pg, ctx.author.id, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = user.id
            data[1] = ctx.guild.id
            data[43] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            pr = data_receive["pokes_received"]
            if pr is None:
                pr = 1
            else:
                pr = pr + 1
            self.db.execute("UPDATE counters SET pokes_received=? WHERE uid=? AND gid=?",
                            (pr, user.id, ctx.guild.id))
            number = pr
        embed.set_footer(text=f"{user.name} has now been poked {number} time(s) in this server!")
        return await ctx.send(embed=embed)

    @commands.command(name="boop", aliases=["bap"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def boop(self, ctx, user: discord.Member):
        """ I hate you... """
        if is_fucked(self.boop):
            self.boop = await lists.get_images(self.bot, 'B')
        if user == ctx.author:
            return await ctx.send(f"{emotes.Deny} How are you going to do that?")
        if user.id == self.bot.user.id:
            return await ctx.send(f"Why though, {ctx.author.name}?")
        embed = discord.Embed(colour=generic.random_colour())
        embed.description = f"**{user.name}** got booped by **{ctx.author.name}**"
        embed.set_image(url=random.choice(self.boop))
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data_giver:
            data = self.empty.copy()
            data[0] = ctx.author.id
            data[1] = ctx.guild.id
            data[44] = 1
            self.db.execute(self.insert, tuple(data))
        else:
            bg = data_giver["boops_given"]
            if bg is None:
                bg = 1
            else:
                bg = bg + 1
            self.db.execute("UPDATE counters SET boops_given=? WHERE uid=? AND gid=?",
                            (bg, ctx.author.id, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = user.id
            data[1] = ctx.guild.id
            data[45] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            br = data_receive["boops_received"]
            if br is None:
                br = 1
            else:
                br = br + 1
            self.db.execute("UPDATE counters SET boops_received=? WHERE uid=? AND gid=?",
                            (br, user.id, ctx.guild.id))
            number = br
        embed.set_footer(text=f"{user.name} has now been booped {number} time(s) in this server!")
        return await ctx.send(embed=embed)

    @commands.command(name="reloadimages")
    @commands.is_owner()
    async def reload_images(self, ctx):
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
        if generic.get_config()["logs"]:
            # await logs.log_channel(self.bot, 'changes').send('Reloaded KB images')
            logs.save(logs.get_place(self.type, "changes"), "Reloaded KB images")
        return await ctx.send("Successfully reloaded images")

    @commands.command(name="ship")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
    async def ship(self, ctx, user1: discord.Member = None, user2: discord.Member = None):
        """ Build a ship """
        if user1 is None or user2 is None:
            return await ctx.send_help(str(ctx.command))
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            return await ctx.send(f"Sorry, but I wasn't programmed to feel love :( {emotes.AlexHeartBroken}")
        if user1.bot or user2.bot:
            return await ctx.send(f"Bots can't be shipped, they can't love :( {emotes.AlexHeartBroken}")
        if user1 == user2:
            return await ctx.send("I don't think that's how it works")
        ls = [94762492923748352, 246652610747039744]
        if user1.id in ls or user2.id in ls:
            return await ctx.send("These 2 users cannot be shipped together.")
        av1 = user1.avatar_url_as(size=1024)
        av2 = user2.avatar_url_as(size=1024)
        link = f"https://api.alexflipnote.dev/ship?user={av1}&user2={av2}"
        bio = BytesIO(await http.get(link, res_method="read"))
        if bio is None:
            return await ctx.send("Something went wrong, couldn't generate image")
        __names = [len(user1.name), len(user2.name)]
        _names = [int(x / 2) for x in __names]
        names = [user1.name[:_names[0]], user2.name[_names[1]:]]
        name = ''.join(names)
        names2 = [user2.name[:_names[1]], user1.name[_names[0]:]]
        name2 = ''.join(names2)
        message = f"Nice shipping there!\nShip names: **{name}** or **{name2}**\n"
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        data_receive1 = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user1.id, ctx.guild.id))
        data_receive2 = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user2.id, ctx.guild.id))
        if not data_giver:
            data = self.empty.copy()
            data[0] = ctx.author.id
            data[1] = ctx.guild.id
            data[27] = 1
            self.db.execute(self.insert, tuple(data))
            number3 = 1
        else:
            self.db.execute("UPDATE counters SET ships_built=? WHERE uid=? AND gid=?",
                            (data_giver["ships_built"] + 1, ctx.author.id, ctx.guild.id))
            number3 = data_giver["ships_built"] + 1
        if not data_receive1:
            data = self.empty.copy()
            data[0] = user1.id
            data[1] = ctx.guild.id
            data[26] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute("UPDATE counters SET shipped=? WHERE uid=? AND gid=?",
                            (data_receive1["shipped"] + 1, user1.id, ctx.guild.id))
            number = data_receive1["shipped"] + 1
        if not data_receive2:
            data = self.empty.copy()
            data[0] = user2.id
            data[1] = ctx.guild.id
            data[26] = 1
            self.db.execute(self.insert, tuple(data))
            number2 = 1
        else:
            self.db.execute("UPDATE counters SET shipped=? WHERE uid=? AND gid=?",
                            (data_receive2["shipped"] + 1, user2.id, ctx.guild.id))
            number2 = data_receive2["shipped"] + 1
        message += f"\n{user1.name} has now been shipped {number} time(s) in this server!"
        message += f"\n{user2.name} has now been shipped {number2} time(s) in this server!"
        message += f"\n{ctx.author.name} has now built {number3} ship(s) in this server!"
        return await ctx.send(message, file=discord.File(bio, filename=f"shipping_services.png"))

    @commands.command(name="counters", aliases=["spamstats"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
    async def counters(self, ctx, who: discord.Member = None):
        """ Check your or someone else's counts! """
        if ctx.channel.id in self.banned:
            return
        user = who or ctx.author
        data = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data:
            return await ctx.send("It doesn't seem I have anything saved for you...")
        embed = discord.Embed(colour=generic.random_colour())
        embed.set_thumbnail(url=user.avatar_url_as(static_format="png", size=1024))
        value = f"{data['bites_given']:,} - Times bit someone\n" \
                f"{data['bites_received']:,} - Times bitten\n" \
                f"{data['cuddles_given']:,} - Cuddles given\n" \
                f"{data['cuddles_received']:,} - Cuddles received\n" \
                f"{data['high_fives_given']:,} - High fives given\n" \
                f"{data['high_fives_received']:,} - High fives received\n" \
                f"{data['hugs_given']:,} - Hugs given\n" \
                f"{data['hugs_received']:,} - Hugs received\n" \
                f"{data['kisses_given']:,} - Kisses given\n" \
                f"{data['kisses_received']:,} - Kisses received\n" \
                f"{data['licks_given']:,} - Licked others\n" \
                f"{data['licks_received']:,} - Gotten licked\n" \
                f"{data['pats_given']:,} - Pats given\n" \
                f"{data['pats_received']:,} - Pats received\n" \
                f"{data['slaps_given']:,} - Slaps given\n" \
                f"{data['slaps_received']:,} - Slaps received\n" \
                f"{data['sniffs_given']:,} - Sniffed others\n" \
                f"{data['sniffs_received']:,} - Gotten sniffed\n"
        if data["pokes_given"] is not None:
            value += f"{data['pokes_given']:,} - Poked others\n"
        if data["pokes_received"] is not None:
            value += f"{data['pokes_received']:,} - Gotten poked\n"
        if data["boops_given"] is not None:
            value += f"{data['boops_given']:,} - Booped others\n"
        if data["boops_received"] is not None:
            value += f"{data['boops_received']:,} - Gotten booped"
        embed.add_field(name="Social", inline=False,
                        value=value)
        if ctx.guild.id != 690162603275714574:
            embed.add_field(name=f"{emotes.NotLikeThis} Scary stuff", inline=False,
                            value=f"{data['bangs_received']:,} time(s) got banged\n"
                                  f"{data['bangs_given']:,} time(s) banged others")
        embed.add_field(name="Edit This Text", inline=False,
                        value=f"{data['bad_given']:,} - Called others bad\n"
                              f"{data['bad_received']:,} - Gotten called bad\n"
                              f"{data['beaned']:,} - Gotten beaned\n"
                              f"{data['beans_given']:,} - Beaned others\n"
                              f"{data['shipped']:,} - Gotten shipped\n"
                              f"{data['ships_built']:,} - Ships built\n"
                              f"{data['trashed']:,} - Gotten called trash\n"
                              f"{data['trash_given']:,} - Called others trash")
        embed.add_field(name="Statuses", inline=False,
                        value=f"{data['blushed']:,} time(s) blushed\n"
                              f"{data['cried']:,} time(s) cried\n"
                              f"{data['sleepy']:,} time(s) been sleepy\n"
                              f"{data['smiled']:,} time(s) smiled")
        cr, ce = data["carrots_received"], data["carrots_eaten"]
        cl = cr - ce
        ar, ae = data["cookies_received"], data["cookies_eaten"]
        al = ar - ae
        fr, fe = data["fruits_received"], data["fruits_eaten"]
        fl = fr - fe
        lr, le = data["lemons_received"], data["lemons_eaten"]
        ll = lr - le
        embed.add_field(name="Foods", inline=False,
                        value=f"{cr:,} carrots received\n{ce:,} carrots eaten\n{cl:,} carrots left\n\n"
                              f"{ar:,} cookies received\n{ae:,} cookies eaten\n{al:,} cookies left\n\n"
                              f"{fr:,} fruits received\n{fe:,} fruits eaten\n{fl:,} fruits left\n\n"
                              f"{lr:,} lemons received\n{le:,} lemons eaten\n{ll:,} lemons left")
        return await ctx.send(f"Spam stats for {user.name} in {ctx.guild.name}", embed=embed)

    @commands.command(name="top")
    @commands.guild_only()
    async def top_counters(self, ctx):
        """ Top counters """
        if ctx.channel.id in self.banned:
            return
        keys = [["bangs_given", "bangs_received"],
                ["bites_given", "bites_received", "cuddles_given", "cuddles_received", "high_fives_given",
                 "high_fives_received", "hugs_given", "hugs_received", "kisses_given", "kisses_received", "licks_given",
                 "licks_received", "pats_given", "pats_received", "slaps_given", "slaps_received", "sniffs_given",
                 "sniffs_received", "pokes_given", "pokes_received", "boops_given", "boops_received"],
                ["bad_given", "bad_received", "beaned", "beans_given", "shipped", "ships_built", "trashed",
                 "trash_given"], ["blushed", "cried", "sleepy", "smiled"],
                ["carrots_received", "carrots_eaten", "cookies_received", "cookies_eaten", "fruits_received",
                 "fruits_eaten", "lemons_received", "lemons_eaten"]]
        names = ["Scary stuff", "Social", "<Name>", "Statuses", "Food"]
        all_keys = []
        for k in keys:
            for i in k:
                all_keys.append(i)
        length = len(keys)
        embed = discord.Embed(colour=generic.random_colour())
        embed.set_thumbnail(url=ctx.guild.icon_url_as(static_format="png", size=1024))
        for i in range(length):
            if i == 0 and ctx.guild.id == 690162603275714574:
                continue
            name = names[i]
            local_keys = keys[i]
            data = []
            for key in local_keys:
                data.append(self.db.fetchrow(f"SELECT uid, {key} FROM counters WHERE gid={ctx.guild.id} ORDER BY "
                                             f"{key} DESC LIMIT 1"))
            output = ""
            _range = len(data)
            for j in range(_range):
                key = local_keys[j]
                key_name = local_keys[j].replace("_", " ")
                key_name = key_name.title()
                d = data[j]
                if d is not None:
                    if d[key] is not None and d[key] > 0:
                        output += f"{key_name}: {d[key]:,} - <@{d['uid']}>\n"
            if output == "":
                output = "No data available"
            embed.add_field(name=name, value=output, inline=False)
        return await ctx.send(f"Top spammers in {ctx.guild.name}", embed=embed)


def setup(bot):
    bot.add_cog(Social(bot))
