import random
from io import BytesIO

import discord
from discord.ext import commands

from alpha import main
from alpha.images import image_gen
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
            self.slap, self.blush, self.smile, self.highfive = [lists.error] * 13
        self.type = main.version
        self.banned = [690254056354087047, 694684764074016799]
        self.db = database.Database()
        self.insert = f"INSERT INTO counters VALUES ({'?, ' * 41}?)"
        self.empty = [0] * 42

    @commands.command(name="pat", aliases=["pet"])
    @commands.guild_only()
    async def pat(self, ctx, user: discord.Member):
        """ Pat someone """
        if is_fucked(self.pat):
            self.pat = await lists.get_images(self.bot, 'p')
        if ctx.author == user:
            return await ctx.send("Don't be like that ;-;")
        if user.id == self.bot.user.id:
            return await ctx.send(f"Thanks, {ctx.author.name} :3 {emotes.AlexHeart} {emotes.AlexPat}")
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
    async def hug(self, ctx, user: discord.Member):
        """ Hug someone """
        if is_fucked(self.hug):
            self.hug = await lists.get_images(self.bot, 'h')
        if ctx.author == user:
            return await ctx.send("Alone? ;-;", embed=discord.Embed(colour=generic.random_colour()).set_image(
                url="https://cdn.discordapp.com/attachments/610482988123422750/673641089218904065/selfhug.gif"))
        if user.id == self.bot.user.id:
            return await ctx.send(f"*Hugs {ctx.author.name} back* {emotes.AlexHeart}")
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
    async def cuddle(self, ctx, user: discord.Member):
        """ Cuddle someone """
        if is_fucked(self.cuddle):
            self.cuddle = await lists.get_images(self.bot, 'c')
        if ctx.author == user:
            return await ctx.send("Alone? ;-;")
        if user.id == self.bot.user.id:
            return await ctx.send(f"*Cuddles {ctx.author.name} back* {emotes.AlexHeart}")
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
    async def lick(self, ctx, user: discord.Member):
        """ Lick someone """
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
    async def kiss(self, ctx, user: discord.Member):
        """ Kiss someone """
        if is_fucked(self.kiss):
            self.kiss = await lists.get_images(self.bot, 'k')
        if user == ctx.author:
            return await ctx.send("Alone? ;-;")
        if user.id == self.bot.user.id:
            return await ctx.send(f"Thanks, {ctx.author.name} {emotes.AlexHeart}! "
                                  f"But, I'm a bot... I wasn't programmed to feel love ;-;")
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
    async def bite(self, ctx, user: discord.Member):
        """ Bite someone """
        if is_fucked(self.bite):
            self.bite = await lists.get_images(self.bot, 'b')
        if user == ctx.author:
            return await ctx.send("How are you going to do that?")
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
    async def slap(self, ctx, user: discord.Member = None):
        """ Violence! """
        if ctx.guild.id == 690162603275714574:
            return await ctx.send(f"{emotes.Deny} This command is disabled in this server.")
        if user is None:
            return await ctx.send_help(str(ctx.command))
        if user == ctx.author:
            return await ctx.send(embed=discord.Embed(colour=generic.random_colour()).set_image(url=but_why))
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
    async def bean(self, ctx, user: discord.Member):
        """ Bean someone """
        if user == ctx.author:
            return await ctx.send(f"{emotes.Deny} How are you gonna do that?")
        if user.id == 302851022790066185:
            return await ctx.send(f"{emotes.Deny} {ctx.author.name}, you are not allowed to do that.")
        if user.id == self.bot.user.id:
            return await ctx.send(f"{emotes.Deny} {ctx.author.name}, you can't bean me.")
        if user.id == ctx.guild.owner.id and ctx.author.id != 302851022790066185:
            return await ctx.send(f"{emotes.Deny} Imagine beaning the owner, lol")
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data_giver:
            data = self.empty.copy()
            data[0] = ctx.author.id
            data[1] = ctx.guild.id
            data[24] = 1
            self.db.execute(self.insert, tuple(data))
        else:
            self.db.execute("UPDATE counters SET beans_given=? WHERE uid=? AND gid=?",
                            (data_giver["beans_given"] + 1, ctx.author.id, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = user.id
            data[1] = ctx.guild.id
            data[25] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute("UPDATE counters SET beaned=? WHERE uid=? AND gid=?",
                            (data_receive["beaned"] + 1, user.id, ctx.guild.id))
            number = data_receive["beaned"] + 1
        # embed.set_footer(text=f"{user.name} has now received {number} high five(s) in this server!")
        return await ctx.send(f"{emotes.Allow} {user.name}, you are dismissed from {ctx.guild.name}.\n"
                              f"{user.name} has now been beaned {number} time(s) in this server!")

    @commands.command(name="cookie")
    @commands.guild_only()
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
        else:
            return await ctx.send("You can only eat the following: cookie, carrot, fruit, lemon.")
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
    async def bad(self, ctx, user: discord.Member):
        """ Bad user """
        if user.id == 302851022790066185:
            user = ctx.author
        if user.id == self.bot.user.id:
            return await ctx.send(f"{emotes.AlexHeartBroken}")
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data_giver:
            data = self.empty.copy()
            data[0] = ctx.author.id
            data[1] = ctx.guild.id
            data[22] = 1
            self.db.execute(self.insert, tuple(data))
        else:
            self.db.execute("UPDATE counters SET bad_given=? WHERE uid=? AND gid=?",
                            (data_giver["bad_given"] + 1, ctx.author.id, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = user.id
            data[1] = ctx.guild.id
            data[23] = 1
            self.db.execute(self.insert, tuple(data))
            # number = 1
        else:
            self.db.execute("UPDATE counters SET bad_received=? WHERE uid=? AND gid=?",
                            (data_receive["bad_received"] + 1, user.id, ctx.guild.id))
            # number = data_receive["bad_received"] + 1
        # embed.set_footer(text=f"{user.name} has now received {number} high five(s) in this server!")
        return await image_gen(ctx, user, "bad", f"bad_{user.name.lower()}")

    @commands.command(name="trash")
    async def trash(self, ctx, user: discord.Member):
        """ Show someone their home """
        if user == ctx.author:
            return await ctx.send("Don't call yourself trash")
        if user == ctx.bot.user:
            return await ctx.send(f"You calling me trash? {emotes.AlexHeartBroken}")
        a1, a2 = [ctx.author.avatar_url, user.avatar_url]
        if user.id == 302851022790066185:
            a2, a1 = a1, a2
        bio = BytesIO(await http.get(f"https://api.alexflipnote.dev/trash?face={a1}&trash={a2}",
                                     res_method="read"))
        if bio is None:
            return await ctx.send("Something went wrong, couldn't generate image")
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data_giver:
            data = self.empty.copy()
            data[0] = ctx.author.id
            data[1] = ctx.guild.id
            data[28] = 1
            self.db.execute(self.insert, tuple(data))
        else:
            self.db.execute("UPDATE counters SET trash_given=? WHERE uid=? AND gid=?",
                            (data_giver["trash_given"] + 1, ctx.author.id, ctx.guild.id))
        if not data_receive:
            data = self.empty.copy()
            data[0] = user.id
            data[1] = ctx.guild.id
            data[29] = 1
            self.db.execute(self.insert, tuple(data))
            # number = 1
        else:
            self.db.execute("UPDATE counters SET trashed=? WHERE uid=? AND gid=?",
                            (data_receive["trashed"] + 1, user.id, ctx.guild.id))
            # number = data_receive["trashed"] + 1
        # embed.set_footer(text=f"{user.name} has now received {number} high five(s) in this server!")
        return await ctx.send(file=discord.File(bio, filename=f"trash_{user.name}.png"))

    @commands.command(name="highfive")
    @commands.guild_only()
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
        if generic.get_config()["logs"]:
            # await logs.log_channel(self.bot, 'changes').send('Reloaded KB images')
            logs.save(logs.get_place(self.type, "changes"), "Reloaded KB images")
        return await ctx.send("Successfully reloaded images")

    @commands.command(name="ship")
    @commands.guild_only()
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


def setup(bot):
    bot.add_cog(Social(bot))
