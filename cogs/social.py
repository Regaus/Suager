import random
from io import BytesIO

import discord
from discord.ext import commands

from cogs.images import image_gen
from utils import lists, database, generic, logs, http


def is_fucked(something):
    return something == [] or something == lists.error or something == [lists.error]


but_why = "https://cdn.discordapp.com/attachments/610482988123422750/673642028357386241/butwhy.gif"


def give(u1: str, u2: str, locale: str, emote: str) -> str:
    return generic.gls(locale, "give_food", [u1, u2, emote]) + f"\n\n(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ {emote}"
    # return f"{u2}, you got a {emote} from {u1}\n\n(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ {emote}"


class Social(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pat, self.hug, self.kiss, self.lick, self.cuddle, self.bite, self.sleepy, self.smell, self.cry, \
            self.slap, self.blush, self.smile, self.highfive, self.poke, self.boop = [lists.error] * 15
        self.db = database.Database()
        self.insert = f"INSERT INTO counters VALUES ({'?, ' * 45}?)"
        self.empty = [0] * 46
        self.names = ["Naughty stuff", "Social interaction", "Edit this text", "Statuses", "Foods"]
        n1, n2, n3, n4, n5 = self.names
        self.keys = {
            n1: ["bangs_given", "bangs_received"],
            n2: ["bites_given", "bites_received", "cuddles_given", "cuddles_received", "high_fives_given",
                 "high_fives_received", "hugs_given", "hugs_received", "kisses_given", "kisses_received", "licks_given",
                 "licks_received", "pats_given", "pats_received", "slaps_given", "slaps_received", "sniffs_given",
                 "sniffs_received", "pokes_given", "pokes_received", "boops_given", "boops_received"],
            n3: ["bad_given", "bad_received", "beaned", "beans_given", "shipped", "ships_built", "trashed", "trash_given"],
            n4: ["blushed", "cried", "sleepy", "smiled"],
            n5: ["carrots_received", "carrots_eaten", "cookies_received", "cookies_eaten", "fruits_received",
                 "fruits_eaten", "lemons_received", "lemons_eaten"]
        }
        self.key_names = {
            n1: ["Banged others", "Been banged"],
            n2: ["Bitten others", "Been bitten", "Cuddled others", "Been cuddled", "Gave high fives",
                 "Received high fives", "Hugged others", "Been hugged", "Kissed others", "Been kissed", "Licked others",
                 "Been licked", "Gave pats", "Received pats", "Slapped others", "Been slapped", "Sniffed others",
                 "Been sniffed", "Poked others", "Been poked", "Booped others", "Been booped"],
            n3: ["Called others bad", "Been called bad", "Been beaned", "Beaned others", "Been shipped", "Built ships", "Been trashed", "Trashed others"],
            n4: ["Blushed", "Cried", "Been sleepy", "Smiled"],
            n5: ["Carrots received", "Carrots eaten", "Cookies received", "Cookies eaten", "Fruits received",
                 "Fruits eaten", "Lemons received", "Lemons eaten"]
        }

    def data_update(self, uid_give: int, uid_receive: int, gid: int, key_g: str, key_r: str, in_g: int, in_r: int):
        """ Update database """
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (uid_give, gid))
        data_receive = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (uid_receive, gid))
        if not data_giver:
            data = self.empty.copy()
            data[0] = uid_give
            data[1] = gid
            data[in_g] = 1
            self.db.execute(self.insert, tuple(data))
        else:
            self.db.execute(f"UPDATE counters SET {key_g}=? WHERE uid=? AND gid=?",
                            (data_giver[key_g] + 1, uid_give, gid))
        if not data_receive:
            data = self.empty.copy()
            data[0] = uid_receive
            data[1] = gid
            data[in_r] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute(f"UPDATE counters SET {key_r}=? WHERE uid=? AND gid=?",
                            (data_receive[key_r] + 1, uid_receive, gid))
            number = data_receive[key_r] + 1
        return number

    def data_update2(self, uid: int, gid: int, key: str, ind: int):
        """ Update database """
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (uid, gid))
        if not data_giver:
            data = self.empty.copy()
            data[0] = uid
            data[1] = gid
            data[ind] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute(f"UPDATE counters SET {key}=? WHERE uid=? AND gid=?",
                            (data_giver[key] + 1, uid, gid))
            number = data_giver[key] + 1
        return number

    def data_update3(self, uid: int, gid: int, key: str, key2: str, ind: int):
        """ Update database """
        data_giver = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (uid, gid))
        if not data_giver:
            data = self.empty.copy()
            data[0] = uid
            data[1] = gid
            data[ind] = 1
            self.db.execute(self.insert, tuple(data))
            number = 1
        else:
            self.db.execute(f"UPDATE counters SET {key}=? WHERE uid=? AND gid=?",
                            (data_giver[key] + 1, uid, gid))
            number = data_giver[key] + 1 - data_giver[key2]
        return number

    @commands.command(name="pat", aliases=["pet"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def pat(self, ctx: commands.Context, user: discord.Member):
        """ Pat someone """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "pat"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if is_fucked(self.pat):
            self.pat = await lists.get_images(self.bot, 'p')
        if ctx.author == user:
            return await generic.send(generic.gls(locale, "pat_self"), ctx.channel)
            # return await ctx.send("Don't be like that ;-;")
        if user.id == self.bot.user.id:
            return await generic.send(generic.gls(locale, "pat_suager", [ctx.author.name]), ctx.channel)
            # return await ctx.send(f"Thanks, {ctx.author.name} :3 {emotes.AlexHeart} {emotes.AlexPat}")
        if user.bot:
            return await generic.send(generic.gls(locale, "inter_bot", [user.name]), ctx.channel)
        # if user.id in generic.love_locks and ctx.author.id not in generic.love_exceptions:
        if generic.is_love_locked(user, ctx.author):
            return await generic.send(generic.gls(locale, "love_locked", [user.name]), ctx.channel)
        # if user.id == 424472476106489856 and ctx.author.id not in [689158123352883340]:
        #     return await ctx.send(f"{emotes.Deny} Those who kill Regaus deserve no love.")
        embed = discord.Embed(colour=generic.random_colour())
        number = self.data_update(ctx.author.id, user.id, ctx.guild.id, "pats_given", "pats_received", 16, 17)
        embed.description = generic.gls(locale, "pat", [user.name, ctx.author.name])
        # embed.description = f"**{user.name}** got a pat from **{ctx.author.name}**"
        embed.set_image(url=random.choice(self.pat))
        if ctx.guild.id in generic.counter_locks:
            embed.set_footer(text=generic.gls(locale, "counters_disabled", [ctx.prefix]))
        else:
            embed.set_footer(text=generic.gls(locale, "pat2", [user.name, number]))
        # embed.set_footer(text=f"{user.name} has now received {number} pat(s) in this server!")
        return await generic.send(None, ctx.channel, embed=embed)
        # return await ctx.send(embed=embed)

    @commands.command(name="hug")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def hug(self, ctx: commands.Context, user: discord.Member):
        """ Hug someone """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "hug"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if is_fucked(self.hug):
            self.hug = await lists.get_images(self.bot, 'h')
        if ctx.author == user:
            return await generic.send(generic.gls(locale, "alone"), ctx.channel, embed=discord.Embed(colour=generic.random_colour()).set_image(
                url="https://cdn.discordapp.com/attachments/610482988123422750/673641089218904065/selfhug.gif"))
        if user.id == self.bot.user.id:
            return await generic.send(generic.gls(locale, "hug_suager", [ctx.author.name]), ctx.channel)
        if user.bot:
            return await generic.send(generic.gls(locale, "inter_bot", [user.name]), ctx.channel)
        # if user.id in generic.love_locks and ctx.author.id not in generic.love_exceptions:
        if generic.is_love_locked(user, ctx.author):
            return await generic.send(generic.gls(locale, "love_locked", [user.name]), ctx.channel)
        embed = discord.Embed(colour=generic.random_colour())
        number = self.data_update(ctx.author.id, user.id, ctx.guild.id, "hugs_given", "hugs_received", 10, 11)
        embed.description = generic.gls(locale, "hug", [user.name, ctx.author.name])
        embed.set_image(url=random.choice(self.hug))
        if ctx.guild.id in generic.counter_locks:
            embed.set_footer(text=generic.gls(locale, "counters_disabled", [ctx.prefix]))
        else:
            embed.set_footer(text=generic.gls(locale, "hug2", [user.name, number]))
        return await generic.send(None, ctx.channel, embed=embed)

    @commands.command(name="cuddle")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def cuddle(self, ctx: commands.Context, user: discord.Member):
        """ Cuddle someone """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "cuddle"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if is_fucked(self.cuddle):
            self.cuddle = await lists.get_images(self.bot, 'c')
        if ctx.author == user:
            return await generic.send(generic.gls(locale, "alone"), ctx.channel, embed=discord.Embed(colour=generic.random_colour()).set_image(
                url="https://cdn.discordapp.com/attachments/610482988123422750/673641089218904065/selfhug.gif"))
        if user.id == self.bot.user.id:
            return await generic.send(generic.gls(locale, "cuddle_suager", [ctx.author.name]), ctx.channel)
        if user.bot:
            return await generic.send(generic.gls(locale, "inter_bot", [user.name]), ctx.channel)
        # if user.id in generic.love_locks and ctx.author.id not in generic.love_exceptions:
        if generic.is_love_locked(user, ctx.author):
            return await generic.send(generic.gls(locale, "love_locked", [user.name]), ctx.channel)
        embed = discord.Embed(colour=generic.random_colour())
        number = self.data_update(ctx.author.id, user.id, ctx.guild.id, "cuddles_given", "cuddles_received", 6, 7)
        embed.description = generic.gls(locale, "cuddle", [user.name, ctx.author.name])
        embed.set_image(url=random.choice(self.cuddle))
        if ctx.guild.id in generic.counter_locks:
            embed.set_footer(text=generic.gls(locale, "counters_disabled", [ctx.prefix]))
        else:
            embed.set_footer(text=generic.gls(locale, "cuddle2", [user.name, number]))
        return await generic.send(None, ctx.channel, embed=embed)

    @commands.command(name="lick")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def lick(self, ctx: commands.Context, user: discord.Member):
        """ Lick someone """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "lick"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if is_fucked(self.lick):
            self.lick = await lists.get_images(self.bot, 'l')
        if ctx.author == user:
            return await generic.send(generic.gls(locale, "alone"), ctx.channel, embed=discord.Embed(colour=generic.random_colour()).set_image(
                url="https://cdn.discordapp.com/attachments/610482988123422750/673644219314733106/selflick.gif"))
        if user.id == self.bot.user.id:
            return await generic.send(generic.gls(locale, "lick_suager", [ctx.author.name]), ctx.channel)
        if user.bot:
            return await generic.send(generic.gls(locale, "lick_bot", [user.name]), ctx.channel)
        # if user.id in generic.love_locks and ctx.author.id not in generic.love_exceptions:
        #     return await generic.send(generic.gls(locale, "love_locked", [ctx.author.name]), ctx.channel)
        embed = discord.Embed(colour=generic.random_colour())
        number = self.data_update(ctx.author.id, user.id, ctx.guild.id, "licks_given", "licks_received", 14, 15)
        embed.description = generic.gls(locale, "lick", [user.name, ctx.author.name])
        embed.set_image(url=random.choice(self.lick))
        if ctx.guild.id in generic.counter_locks:
            embed.set_footer(text=generic.gls(locale, "counters_disabled", [ctx.prefix]))
        else:
            embed.set_footer(text=generic.gls(locale, "lick2", [user.name, number]))
        return await generic.send(None, ctx.channel, embed=embed)

    @commands.command(name="kiss")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def kiss(self, ctx: commands.Context, user: discord.Member):
        """ Kiss someone """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "kiss"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if is_fucked(self.kiss):
            self.kiss = await lists.get_images(self.bot, 'k')
        if ctx.author == user:
            return await generic.send(generic.gls(locale, "alone"), ctx.channel)
        if user.id == self.bot.user.id:
            return await generic.send(generic.gls(locale, "kiss_suager", [ctx.author.name]), ctx.channel)
        if user.bot:
            return await generic.send(generic.gls(locale, "kiss_bot", [user.name]), ctx.channel)
        # if user.id in generic.love_locks and ctx.author.id not in generic.love_exceptions:
        if generic.is_love_locked(user, ctx.author):
            return await generic.send(generic.gls(locale, "love_locked", [user.name]), ctx.channel)
        embed = discord.Embed(colour=generic.random_colour())
        number = self.data_update(ctx.author.id, user.id, ctx.guild.id, "kisses_given", "kisses_received", 12, 13)
        embed.description = generic.gls(locale, "kiss", [user.name, ctx.author.name])
        embed.set_image(url=random.choice(self.kiss))
        if ctx.guild.id in generic.counter_locks:
            embed.set_footer(text=generic.gls(locale, "counters_disabled", [ctx.prefix]))
        else:
            embed.set_footer(text=generic.gls(locale, "kiss2", [user.name, number]))
        return await generic.send(None, ctx.channel, embed=embed)

    @commands.command(name="bite")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def bite(self, ctx: commands.Context, user: discord.Member):
        """ Bite someone """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "bite"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if is_fucked(self.bite):
            self.bite = await lists.get_images(self.bot, 'b')
        if ctx.author == user:
            return await generic.send(generic.gls(locale, "self_harm_bad"), ctx.channel)
        if user.id == self.bot.user.id:
            generic.heresy(ctx.author.id)
            return await generic.send(generic.gls(locale, "bite_suager", [ctx.author.name]), ctx.channel)
        if user.id == 302851022790066185:
            generic.heresy(ctx.author.id)
            return await generic.send(generic.gls(locale, "not_allowed", [ctx.author.name]), ctx.channel)
        if user.bot:
            return await generic.send(generic.gls(locale, "bite_bot", [user.name]), ctx.channel)
        embed = discord.Embed(colour=generic.random_colour())
        number = self.data_update(ctx.author.id, user.id, ctx.guild.id, "bites_given", "bites_received", 4, 5)
        embed.description = generic.gls(locale, "bite", [user.name, ctx.author.name])
        embed.set_image(url=random.choice(self.bite))
        if ctx.guild.id in generic.counter_locks:
            embed.set_footer(text=generic.gls(locale, "counters_disabled", [ctx.prefix]))
        else:
            embed.set_footer(text=generic.gls(locale, "bite2", [user.name, number]))
        return await generic.send(None, ctx.channel, embed=embed)

    @commands.command(name="slap", aliases=["kill", "shoot", "punch", "hit"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def slap(self, ctx: commands.Context, user: discord.Member):
        """ Slap someone """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "slap"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.author == user:
            return await generic.send(generic.gls(locale, "self_harm_bad"), ctx.channel)
        if user.id == self.bot.user.id:
            generic.heresy(ctx.author.id)
            return await generic.send(generic.gls(locale, "slap_suager", [ctx.author.name]), ctx.channel)
        if user.id == 302851022790066185:
            generic.heresy(ctx.author.id)
            return await generic.send(generic.gls(locale, "not_allowed", [ctx.author.name]), ctx.channel)
        if user.bot:
            return await generic.send(generic.gls(locale, "slap_bot", [user.name]), ctx.channel)
        if ctx.invoked_with == "slap":
            if is_fucked(self.slap):
                self.slap = await lists.get_images(self.bot, 'v')
            embed = discord.Embed(colour=generic.random_colour())
            number = self.data_update(ctx.author.id, user.id, ctx.guild.id, "slaps_given", "slaps_received", 18, 19)
            embed.description = generic.gls(locale, "slap", [user.name, ctx.author.name])
            embed.set_image(url=random.choice(self.slap))
            if ctx.guild.id in generic.counter_locks:
                embed.set_footer(text=generic.gls(locale, "counters_disabled", [ctx.prefix]))
            else:
                embed.set_footer(text=generic.gls(locale, "slap2", [user.name, number]))
        else:
            embed = None
        return await generic.send(generic.gls(locale, "slap_bad", [ctx.author.name]), ctx.channel, embed=embed)

    @commands.command(name="smell", aliases=["sniff"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def smell(self, ctx: commands.Context, user: discord.Member):
        """ Smell/sniff someone """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "smell"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if is_fucked(self.smell):
            self.smell = await lists.get_images(self.bot, 'n')
        if ctx.author == user:
            return await generic.send(generic.gls(locale, "how_are_you_gonna"), ctx.channel)
        if user.id == self.bot.user.id:
            return await generic.send(generic.gls(locale, "smell_suager", [ctx.author.name]), ctx.channel)
        if user.bot:
            return await generic.send(generic.gls(locale, "smell_bot", [user.name]), ctx.channel)
        embed = discord.Embed(colour=generic.random_colour())
        number = self.data_update(ctx.author.id, user.id, ctx.guild.id, "sniffs_given", "sniffs_received", 20, 21)
        s = generic.gls(locale, f"{ctx.invoked_with}ed")
        embed.description = generic.gls(locale, "smell", [user.name, ctx.author.name, s])
        embed.set_image(url=random.choice(self.smell))
        if ctx.guild.id in generic.counter_locks:
            embed.set_footer(text=generic.gls(locale, "counters_disabled", [ctx.prefix]))
        else:
            embed.set_footer(text=generic.gls(locale, "smell2", [user.name, number, s]))
        return await generic.send(None, ctx.channel, embed=embed)

    @commands.command(name="highfive")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def highfive(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a high five """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "highfive"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if is_fucked(self.highfive):
            self.highfive = await lists.get_images(self.bot, 'i')
        if ctx.author == user:
            return await generic.send(generic.gls(locale, "how_are_you_gonna"), ctx.channel)
        if user.id == self.bot.user.id:
            return await generic.send(generic.gls(locale, "highfive_suager", [ctx.author.name]), ctx.channel)
        if user.bot:
            return await generic.send(generic.gls(locale, "highfive_bot", [user.name]), ctx.channel)
        embed = discord.Embed(colour=generic.random_colour())
        number = self.data_update(ctx.author.id, user.id, ctx.guild.id, "high_fives_given", "high_fives_received", 8, 9)
        embed.description = generic.gls(locale, "highfive", [user.name, ctx.author.name])
        embed.set_image(url=random.choice(self.highfive))
        if ctx.guild.id in generic.counter_locks:
            embed.set_footer(text=generic.gls(locale, "counters_disabled", [ctx.prefix]))
        else:
            embed.set_footer(text=generic.gls(locale, "highfive2", [user.name, number]))
        return await generic.send(None, ctx.channel, embed=embed)

    @commands.command(name="poke")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def poke(self, ctx: commands.Context, user: discord.Member):
        """ Poke someone """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "poke"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if is_fucked(self.poke):
            self.poke = await lists.get_images(self.bot, 'P')
        if ctx.author == user:
            return await generic.send(generic.gls(locale, "how_are_you_gonna"), ctx.channel)
        if user.id == self.bot.user.id:
            return await generic.send(generic.gls(locale, "poke_suager", [ctx.author.name]), ctx.channel)
        if user.bot:
            return await generic.send(generic.gls(locale, "poke_bot", [user.name]), ctx.channel)
        embed = discord.Embed(colour=generic.random_colour())
        number = self.data_update(ctx.author.id, user.id, ctx.guild.id, "pokes_given", "pokes_received", 42, 43)
        embed.description = generic.gls(locale, "poke", [user.name, ctx.author.name])
        embed.set_image(url=random.choice(self.poke))
        if ctx.guild.id in generic.counter_locks:
            embed.set_footer(text=generic.gls(locale, "counters_disabled", [ctx.prefix]))
        else:
            embed.set_footer(text=generic.gls(locale, "poke2", [user.name, number]))
        return await generic.send(None, ctx.channel, embed=embed)

    @commands.command(name="boop", aliases=["bap"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def boop(self, ctx: commands.Context, user: discord.Member):
        """ Why is this a thing? """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "boop"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if is_fucked(self.boop):
            self.boop = await lists.get_images(self.bot, 'B')
        if ctx.author == user:
            return await generic.send(generic.gls(locale, "how_are_you_gonna"), ctx.channel)
        if user.id == self.bot.user.id:
            return await generic.send(generic.gls(locale, "poke_suager", [ctx.author.name]), ctx.channel)
        if user.bot:
            return await generic.send(generic.gls(locale, "boop_bot", [user.name]), ctx.channel)
        embed = discord.Embed(colour=generic.random_colour())
        number = self.data_update(ctx.author.id, user.id, ctx.guild.id, "boops_given", "boops_received", 44, 45)
        embed.description = generic.gls(locale, "boop", [user.name, ctx.author.name])
        embed.set_image(url=random.choice(self.boop))
        if ctx.guild.id in generic.counter_locks:
            embed.set_footer(text=generic.gls(locale, "counters_disabled", [ctx.prefix]))
        else:
            embed.set_footer(text=generic.gls(locale, "boop2", [user.name, number]))
        return await generic.send(None, ctx.channel, embed=embed)

    @commands.command(name="ship")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def ship(self, ctx: commands.Context, user1: discord.Member, user2: discord.Member):
        """ Build a ship """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "ship"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        pr = False
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            if user1.id != 302851022790066185 and user2.id != 302851022790066185:
                return await generic.send(generic.gls(locale, "ship_suager"), ctx.channel)
            pr = True
            # return await ctx.send(f"Sorry, but I wasn't programmed to feel love :( {emotes.AlexHeartBroken}")
        if (user1.bot ^ user2.bot) and not pr:
            return await generic.send(generic.gls(locale, "bots_love"), ctx.channel)
            # return await ctx.send(f"Bots can't be shipped, they can't love :( {emotes.AlexHeartBroken}")
        if user1 == user2:
            return await generic.send(generic.gls(locale, "ship_self"), ctx.channel)
            # return await ctx.send("I don't think that's how it works")
        # ls = [94762492923748352, 246652610747039744]
        # if user1.id in ls or user2.id in ls:
        #     return await ctx.send("These 2 users cannot be shipped together.")
        av1 = user1.avatar_url_as(size=1024)
        av2 = user2.avatar_url_as(size=1024)
        link = f"https://api.alexflipnote.dev/ship?user={av1}&user2={av2}"
        bio = BytesIO(await http.get(link, res_method="read"))
        if bio is None:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "image_not_created"), ctx.channel)
            # return await ctx.send("Something went wrong, couldn't generate image")
        __names = [len(user1.name), len(user2.name)]
        _names = [int(x / 2) for x in __names]
        names = [user1.name[:_names[0]], user2.name[_names[1]:]]
        name = ''.join(names)
        names2 = [user2.name[:_names[1]], user1.name[_names[0]:]]
        name2 = ''.join(names2)
        message = generic.gls(locale, "ship", [name, name2])
        # message = f"Nice shipping there!\nShip names: **{name}** or **{name2}**\n"
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
        # message += f"\n{user1.name} has now been shipped {number} time(s) in this server!"
        # message += f"\n{user2.name} has now been shipped {number2} time(s) in this server!"
        # message += f"\n{ctx.author.name} has now built {number3} ship(s) in this server!"
        if ctx.guild.id in generic.counter_locks:
            message += "\n" + generic.gls(locale, "counters_disabled", [ctx.prefix])
        else:
            message += generic.gls(locale, "ship2", [user1.name, number])
            message += generic.gls(locale, "ship2", [user2.name, number2])
            message += generic.gls(locale, "ship3", [ctx.author.name, number3])
        return await generic.send(message, ctx.channel, file=discord.File(bio, filename="ship.png"))
        # return await ctx.send(message, file=discord.File(bio, filename=f"shipping_services.png"))

    @commands.command(name="sleepy")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def sleepy(self, ctx):
        """ You're sleepy """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "sleepy"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if is_fucked(self.sleepy):
            self.sleepy = await lists.get_images(self.bot, 's')
        embed = discord.Embed(colour=generic.random_colour())
        embed.description = generic.gls(locale, "sleepy", [ctx.author.name])
        # embed.description = f"**{ctx.author.name}** is sleepy..."
        embed.set_image(url=random.choice(self.sleepy))
        number = self.data_update2(ctx.author.id, ctx.guild.id, "sleepy", 32)
        if ctx.guild.id in generic.counter_locks:
            embed.set_footer(text=generic.gls(locale, "counters_disabled", [ctx.prefix]))
        else:
            embed.set_footer(text=generic.gls(locale, "sleepy2", [ctx.author.name, number]))
        # embed.set_footer(text=f"{ctx.author.name} has now been sleepy {number} time(s) in this server!")
        return await generic.send(None, ctx.channel, embed=embed)
        # return await ctx.send(embed=embed)

    @commands.command(name="cry")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def cry(self, ctx):
        """ You're crying """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "cry"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if is_fucked(self.cry):
            self.cry = await lists.get_images(self.bot, 'r')
        embed = discord.Embed(colour=generic.random_colour())
        embed.description = generic.gls(locale, "cry", [ctx.author.name])
        # embed.description = f"**{ctx.author.name}** is sleepy..."
        embed.set_image(url=random.choice(self.cry))
        number = self.data_update2(ctx.author.id, ctx.guild.id, "cried", 31)
        if ctx.guild.id in generic.counter_locks:
            embed.set_footer(text=generic.gls(locale, "counters_disabled", [ctx.prefix]))
        else:
            embed.set_footer(text=generic.gls(locale, "cry2", [ctx.author.name, number]))
        # embed.set_footer(text=f"{ctx.author.name} has now been sleepy {number} time(s) in this server!")
        return await generic.send(None, ctx.channel, embed=embed)
        # return await ctx.send(embed=embed)

    @commands.command(name="blush")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def blush(self, ctx):
        """ You blush """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "blush"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if is_fucked(self.blush):
            self.blush = await lists.get_images(self.bot, 'u')
        embed = discord.Embed(colour=generic.random_colour())
        embed.description = generic.gls(locale, "blush", [ctx.author.name])
        # embed.description = f"**{ctx.author.name}** is sleepy..."
        embed.set_image(url=random.choice(self.blush))
        number = self.data_update2(ctx.author.id, ctx.guild.id, "blushed", 30)
        if ctx.guild.id in generic.counter_locks:
            embed.set_footer(text=generic.gls(locale, "counters_disabled", [ctx.prefix]))
        else:
            embed.set_footer(text=generic.gls(locale, "blush2", [ctx.author.name, number]))
        # embed.set_footer(text=f"{ctx.author.name} has now been sleepy {number} time(s) in this server!")
        return await generic.send(None, ctx.channel, embed=embed)
        # return await ctx.send(embed=embed)

    @commands.command(name="smile")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def smile(self, ctx):
        """ You're smiling """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "smile"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if is_fucked(self.smile):
            self.smile = await lists.get_images(self.bot, 'm')
        embed = discord.Embed(colour=generic.random_colour())
        embed.description = generic.gls(locale, "smile", [ctx.author.name])
        # embed.description = f"**{ctx.author.name}** is sleepy..."
        embed.set_image(url=random.choice(self.smile))
        number = self.data_update2(ctx.author.id, ctx.guild.id, "smiled", 33)
        if ctx.guild.id in generic.counter_locks:
            embed.set_footer(text=generic.gls(locale, "counters_disabled", [ctx.prefix]))
        else:
            embed.set_footer(text=generic.gls(locale, "smile2", [ctx.author.name, number]))
        # embed.set_footer(text=f"{ctx.author.name} has now been sleepy {number} time(s) in this server!")
        return await generic.send(None, ctx.channel, embed=embed)
        # return await ctx.send(embed=embed)

    @commands.command(name="bang", aliases=["fuck"], hidden=True)
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def fuck(self, ctx, user: discord.Member):
        """ Bang someone """
        locale = generic.get_lang(ctx.guild)
        if not ctx.channel.is_nsfw():
            return await generic.send(generic.gls(locale, "channel_must_be_nsfw"), ctx.channel)
        if generic.is_locked(ctx.guild, "bang"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if user.id == self.bot.user.id:
            return await generic.send(generic.gls(locale, "bang_suager"), ctx.channel)
            # return await ctx.send("No. I'm taken, find someone else.")
        if user == ctx.author:
            return await generic.send(generic.gls(locale, "how_are_you_gonna"), ctx.channel)
            # return await ctx.send("How are you going to do that?")
        number = self.data_update(ctx.author.id, user.id, ctx.guild.id, "bangs_given", "bangs_received", 2, 3)
        out = generic.gls(locale, "bang_out", [ctx.author.name, user.name, generic.gls(locale, ctx.invoked_with)])
        if ctx.guild.id not in generic.counter_locks:
            out += generic.gls(locale, "bang_counter", [user.name, number, generic.gls(locale, ctx.invoked_with)])
        return await generic.send(out, ctx.channel)
        # embed.set_footer(text=f"{user.name} has now got {ctx.invoked_with}ed {number} time(s) in this server!")
        # return await ctx.send(f"{emotes.Scary} {emotes.NotLikeThis} {ctx.author.name} is now "
        #                       f"{ctx.invoked_with}ing {user.name}...\n{user.name} has now got {ctx.invoked_with}ed "
        #                       f"{number} time(s) in this server!")

    @commands.command(name="bean")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def bean(self, ctx: commands.Context, user: discord.Member):
        """ Bean someone """
        # bean_self = False
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "bean"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if user == ctx.author:
            return await generic.send(generic.gls(locale, "how_are_you_gonna"), ctx.channel)
            # return await ctx.send(f"{emotes.Deny} How are you gonna do that?")
        if user.id == 302851022790066185:
            return await generic.send(generic.gls(locale, "bean_not_allowed"), ctx.channel)
            # return await ctx.send(f"{emotes.Deny} {ctx.author.name}, you are not allowed to do that.")
            # bean_self = True
        if user.id == self.bot.user.id:
            return await generic.send(generic.gls(locale, "bean_suager"), ctx.channel)
            # return await ctx.send(f"{emotes.Deny} {ctx.author.name}, you can't bean me.")
            # bean_self = True
        if user.id == ctx.guild.owner.id and ctx.author.id != 302851022790066185:
            return await generic.send(generic.gls(locale, "bean_owner"), ctx.channel)
            # return await ctx.send(f"{emotes.Deny} Imagine beaning the owner, lol")
        bean_self = ctx.author.id in generic.bad_locks
        if not bean_self:
            id1, id2 = ctx.author.id, user.id
            # index1, index2 = 24, 25
        else:
            id1, id2 = -1, ctx.author.id
            # index1, index2 = 25, 24
        number = self.data_update(id1, id2, ctx.guild.id, "beans_given", "beaned", 24, 25)
        # embed.set_footer(text=f"{user.name} has now received {number} high five(s) in this server!")
        if not bean_self:
            bean = generic.gls(locale, "bean", [user.name, ctx.guild.name])
            if ctx.guild.id not in generic.counter_locks:
                bean += generic.gls(locale, "bean3", [user.name, number])
            # bean = f"{emotes.Allow} {user.name}, you are dismissed from {ctx.guild.name}.\n" \
            #        f"{user.name} has now been beaned {number} time(s) in this server!"
        else:
            bean = generic.gls(locale, "bean2", [ctx.author.name, ctx.guild.name])
            # bean = f"{emotes.Deny} {ctx.author.name}, you are dismissed from {ctx.guild.name}."
        return await generic.send(bean, ctx.channel)
        # return await ctx.send(bean)

    @commands.command(name="bad")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def bad(self, ctx: commands.Context, user: discord.Member):
        """ Bad user """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "bad"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        bad_self = False
        if user == ctx.author:
            return await generic.send(generic.gls(locale, "bad_self"), ctx.channel)
        if user.id == 302851022790066185:
            bad_self = True
            generic.heresy(ctx.author.id)
        # elif ctx.author.id == 424472476106489856:
        elif ctx.author.id in generic.bad_locks:
            bad_self = True
        elif user.id == self.bot.user.id:
            generic.heresy(ctx.author.id)
            return await generic.send(generic.gls(locale, "bad_suager"), ctx.channel)
        if not bad_self:
            id1, id2 = ctx.author.id, user.id
            # index1, index2 = 22, 23
        else:
            id1, id2 = -1, ctx.author.id
            # index1, index2 = 23, 22
            user = ctx.author
        self.data_update(id1, id2, ctx.guild.id, "bad_given", "bad_received", 22, 23)
        # number = data_receive["bad_received"] + 1
        # embed.set_footer(text=f"{user.name} has now received {number} high five(s) in this server!")
        return await image_gen(ctx, user, "bad", f"bad_{user.name.lower()}")

    @commands.command(name="trash")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def trash(self, ctx, user: discord.Member):
        """ Show someone their home """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "trash"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        trash_self = False
        if user == ctx.author:
            return await generic.send(generic.gls(locale, "bad_self"), ctx.channel)
            # return await ctx.send("Don't call yourself trash")
        if user.id == self.bot.user.id:
            generic.heresy(ctx.author.id)
            return await generic.send(generic.gls(locale, "bad_suager"), ctx.channel)
            # return await ctx.send(f"You dare calling me trash? {emotes.AlexHeartBroken}")
        a1, a2 = [ctx.author.avatar_url, user.avatar_url]
        if user.id == 302851022790066185:
            generic.heresy(ctx.author.id)
            a2, a1 = a1, a2
            trash_self = True
        # elif ctx.author.id == 424472476106489856:
        elif ctx.author.id in generic.bad_locks:
            a2, a1 = a1, a2
            trash_self = True
        if not trash_self:
            id1, id2 = ctx.author.id, user.id
            # index1, index2 = 28, 29
        else:
            id1, id2 = user.id, ctx.author.id
            # index1, index2 = 23, 22
        self.data_update(id1, id2, ctx.guild.id, "trash_given", "trashed", 28, 29)
        bio = BytesIO(await http.get(f"https://api.alexflipnote.dev/trash?face={a1}&trash={a2}", res_method="read"))
        if bio is None:
            return await generic.send(generic.gls(locale, "image_not_created"), ctx.channel)
            # return await ctx.send("Something went wrong, couldn't generate image")
        # embed.set_footer(text=f"{user.name} has now received {number} high five(s) in this server!")
        return await generic.send(None, ctx.channel, file=discord.File(bio, filename=f"trash_{user.name.lower()}.png"))
        # return await ctx.send(file=discord.File(bio, filename=f"trash_{user.name}.png"))

    @commands.command(name="cookie")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def cookie(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a cookie """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "cookie"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if user == ctx.author:
            return await generic.send(generic.gls(locale, "no_greedy", [ctx.author.name]), ctx.channel)
            # return await ctx.send(f"Don't be greedy, {ctx.author.name}! Share it!")
        # if ctx.guild.id == 690162603275714574:  # OtakuTalk
        #     roles = [r.id for r in user.roles]
        #     if 696468113675255888 in roles:  # lemon squad
        #         return await ctx.send(f"Sour lemons like {user.name} don't deserve our cookies.")
        output = give(ctx.author.name, user.name, locale, "🍪")
        number = self.data_update3(user.id, ctx.guild.id, "cookies_received", "cookies_eaten", 36)
        output += generic.gls(locale, "food_counter", [user.name, number, generic.gls(locale, "cookie_plural")])
        # output += f"\n{user.name} now has {number} cookie(s) in this server!"
        return await generic.send(output, ctx.channel)
        # return await ctx.send(output)

    @commands.command(name="lemon")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def lemon(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a lemon """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "lemon"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if user == ctx.author:
            return await generic.send(generic.gls(locale, "no_greedy", [ctx.author.name]), ctx.channel)
            # return await ctx.send(f"Don't be greedy, {ctx.author.name}! Share it!")
        # if ctx.guild.id == 690162603275714574:  # OtakuTalk
        #     roles = [r.id for r in user.roles]
        #     if 695246056945877053 in roles:  # Cookie Army
        #         return await ctx.send("You can't give lemons to a cookie.")
        output = give(ctx.author.name, user.name, locale, "🍋")
        number = self.data_update3(user.id, ctx.guild.id, "lemons_received", "lemons_eaten", 40)
        output += generic.gls(locale, "food_counter", [user.name, number, generic.gls(locale, "lemon_plural")])
        # output += f"\n{user.name} now has {number} lemon(s) in this server!"
        return await generic.send(output, ctx.channel)
        # return await ctx.send(output)

    @commands.command(name="carrot")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def carrot(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a carrot """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "carrot"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if user == ctx.author:
            return await generic.send(generic.gls(locale, "no_greedy", [ctx.author.name]), ctx.channel)
            # return await ctx.send(f"Don't be greedy, {ctx.author.name}! Share it!")
        output = give(ctx.author.name, user.name, locale, "🥕")
        number = self.data_update3(user.id, ctx.guild.id, "carrots_received", "carrots_eaten", 34)
        output += generic.gls(locale, "food_counter", [user.name, number, generic.gls(locale, "carrot_plural")])
        # output += f"\n{user.name} now has {number} carrot(s) in this server!"
        return await generic.send(output, ctx.channel)
        # return await ctx.send(output)

    @commands.command(name="fruit", aliases=["fruitsnacks"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def fruit_snacks(self, ctx: commands.Context, user: discord.Member):
        """ Give someone a fruit snack """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "fruit"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if user == ctx.author:
            return await generic.send(generic.gls(locale, "no_greedy", [ctx.author.name]), ctx.channel)
            # return await ctx.send(f"Don't be greedy, {ctx.author.name}! Share it!")
        output = give(ctx.author.name, user.name, locale, random.choice(list("🍏🍎🍐🍊🍌🍉🍇🍓🍒🍍")))
        number = self.data_update3(user.id, ctx.guild.id, "fruits_received", "fruits_eaten", 38)
        output += generic.gls(locale, "food_counter", [user.name, number, generic.gls(locale, "fruit_plural")])
        # output += f"\n{user.name} now has {number} fruit(s) in this server!"
        return await generic.send(output, ctx.channel)
        # return await ctx.send(output)

    @commands.command(name="eat")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def eat_something(self, ctx: commands.Context, what: str):
        """ Eat something """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "eat"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if what == "cookie":
            fr, fe = "cookies_received", "cookies_eaten"
        elif what == "carrot":
            fr, fe = "carrots_received", "carrots_eaten"
        elif what == "fruit":
            fr, fe = "fruits_received", "fruits_eaten"
        elif what == "lemon":
            fr, fe = "lemons_received", "lemons_eaten"
        # elif what.lower() in ["<@273916273732222979>", "<@!273916273732222979>", "adde", "adde the chicken noodle"]:
        #     return await ctx.send(f"{ctx.author.name} just ate a piece of Adde the Chicken Noodle.")
        else:
            return await generic.send(generic.gls(locale, "eat_allowed"), ctx.channel)
            # return await ctx.send("You can only eat the following: cookie, carrot, fruit, lemon, and "
            #                       "Adde the Chicken Noodle.")
        data = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        wp, ws = generic.gls(locale, f"{what}_plural"), generic.gls(locale, f"{what}_singular")
        if not data:
            return await generic.send(generic.gls(locale, "eat_none", [wp]), ctx.channel)
            # return await ctx.send(f"You don't have any {what}s right now...")
        left = data[fr] - data[fe]
        if left < 1:
            return await generic.send(generic.gls(locale, "eat_none_left", [wp]), ctx.channel)
            # return await ctx.send(f"You don't have any {what}s left...")
        left -= 1
        self.db.fetchrow(f"UPDATE counters SET {fe}=? WHERE uid=? AND gid=?",
                         (data[fe] + 1, ctx.author.id, ctx.guild.id))
        return await generic.send(generic.gls(locale, "eat", [ctx.author.name, ws, left]), ctx.channel)
        # return await ctx.send(f"{ctx.author.name} just ate a {what}. You have {left} left.")

    @commands.command(name="reloadimages")
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
        if generic.get_config()["logs"]:
            # await logs.log_channel(self.bot, 'changes').send('Reloaded KB images')
            logs.log("changes", "Reloaded Social images")
        return await generic.send("Successfully reloaded images", ctx.channel)
        # return await ctx.send("Successfully reloaded images")

    @commands.command(name="counters", aliases=["spamstats"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def counters(self, ctx: commands.Context, who: discord.Member = None):
        """ Check your or someone else's counts! """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "counters"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        user = who or ctx.author
        data = self.db.fetchrow("SELECT * FROM counters WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data:
            return await ctx.send("It doesn't seem I have anything saved for you...")
        embed = discord.Embed(colour=generic.random_colour())
        embed.set_thumbnail(url=user.avatar_url_as(static_format="png", size=1024))
        for i in range(len(self.names) - 1):
            if i == 0 and generic.is_locked(ctx.guild, "bang"):
                continue
            value = ""
            for j in range(len(self.keys[self.names[i]])):
                val = data[self.keys[self.names[i]][j]]
                name = self.key_names[self.names[i]][j]
                if val is not None and val > 0:
                    value += f"{val:,} - {name}\n"
            if value == "":
                value = "No data available"
            embed.add_field(name=self.names[i], inline=False, value=value)
        cr, ce = data["carrots_received"], data["carrots_eaten"]
        cl = cr - ce
        ar, ae = data["cookies_received"], data["cookies_eaten"]
        al = ar - ae
        fr, fe = data["fruits_received"], data["fruits_eaten"]
        fl = fr - fe
        lr, le = data["lemons_received"], data["lemons_eaten"]
        ll = lr - le
        embed.add_field(name=self.names[4], inline=False,
                        value=f"{cr:,} carrots received\n{ce:,} carrots eaten\n{cl:,} carrots left\n\n"
                              f"{ar:,} cookies received\n{ae:,} cookies eaten\n{al:,} cookies left\n\n"
                              f"{fr:,} fruits received\n{fe:,} fruits eaten\n{fl:,} fruits left\n\n"
                              f"{lr:,} lemons received\n{le:,} lemons eaten\n{ll:,} lemons left")
        return await generic.send(generic.gls(locale, "spam_stats", [user.name, ctx.guild.name]), ctx.channel, embed=embed)
        # return await ctx.send(f"Spam stats for {user.name} in {ctx.guild.name}", embed=embed)

    @commands.command(name="top")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def top_counters(self, ctx):
        """ Top counters """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "top"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        embed = discord.Embed(colour=generic.random_colour())
        embed.set_thumbnail(url=ctx.guild.icon_url_as(static_format="png", size=1024))
        for i in range(len(self.names)):
            if i == 0 and (generic.is_locked(ctx.guild, "bang") or ctx.guild.id == 568148147457490954):
                continue
            name = self.names[i]
            local_keys = self.keys[self.names[i]]
            data = []
            for key in local_keys:
                data.append(self.db.fetchrow(f"SELECT uid, {key} FROM counters WHERE gid={ctx.guild.id} ORDER BY {key} DESC LIMIT 1"))
            output = ""
            _range = len(data)
            for j in range(_range):
                key = local_keys[j]
                key_name = self.key_names[self.names[i]][j]
                # key_name = local_keys[j].replace("_", " ")
                # key_name = key_name.title()
                d = data[j]
                if d is not None:
                    if d[key] is not None and d[key] > 0:
                        output += f"{key_name}: {d[key]:,} - <@{d['uid']}>\n"
            if output == "":
                output = "No data available"
            embed.add_field(name=name, value=output, inline=False)
        return await generic.send(generic.gls(locale, "top_counters", [ctx.guild.name]), ctx.channel, embed=embed)
        # return await ctx.send(f"Top spammers in {ctx.guild.name}", embed=embed)


def setup(bot):
    bot.add_cog(Social(bot))
