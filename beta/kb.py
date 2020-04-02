import random
from io import BytesIO

import discord
from discord.ext import commands

from beta import main
from beta.images import image_gen
from utils import lists, emotes, generic, logs, http


def is_fucked(something):
    return something == [] or something == lists.error or something == [lists.error]


but_why = "https://cdn.discordapp.com/attachments/610482988123422750/673642028357386241/butwhy.gif"


def give(u1: str, u2: str, emote: str):
    return f"{u2}, you got a {emote} from {u1}\n\n(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ {emote}"


class Social(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pat, self.hug, self.kiss, self.lick, self.cuddle, self.bite, self.sleepy, self.smell, self.cry, \
            self.slap, self.blush, self.smile = [lists.error] * 12
        self.type = main.version

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
        return await ctx.send(embed=embed)

    @commands.command(name="lick", aliases=["licc"])
    @commands.guild_only()
    async def lick(self, ctx, user: discord.Member):
        """ Lick someone """
        if is_fucked(self.lick):
            self.lick = await lists.get_images(self.bot, 'l')
        if ctx.guild.id == 679055998186553344:  # Rosey's server
            if user.id == 302851022790066185:  # Regaus
                if ctx.author.id != 424472476106489856:  # Canvas
                    canvas = ctx.guild.get_member(424472476106489856)
                    return await ctx.send(f"Only {canvas.display_name} is allowed to lick {user.display_name}.")
            if user.id == 424472476106489856:  # Canvas
                if ctx.author.id != 302851022790066185:  # Regaus
                    regaus = ctx.guild.get_member(302851022790066185)
                    return await ctx.send(f"Only {regaus.display_name} is allowed to lick {user.display_name}.")
        embed = discord.Embed(colour=generic.random_colour())
        if user == ctx.author:
            return await ctx.send(embed=embed.set_image(
                url="https://cdn.discordapp.com/attachments/610482988123422750/673644219314733106/selflick.gif"))
        if user.id == self.bot.user.id:
            return await ctx.send(f"W-why did you lick me, {ctx.author.name}?", embed=embed.set_image(url=but_why))
        embed.description = f"**{user.name}** was licked by **{ctx.author.name}**"
        embed.set_image(url=random.choice(self.lick))
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
        if ctx.guild.id == 679055998186553344:  # Rosey's server
            if user.id == 302851022790066185:  # Regaus
                if ctx.author.id != 424472476106489856:  # Canvas
                    canvas = ctx.guild.get_member(424472476106489856)
                    return await ctx.send(f"Only {canvas.display_name} is allowed to do that.")
            if user.id == 424472476106489856:  # Canvas
                if ctx.author.id != 302851022790066185:  # Regaus
                    regaus = ctx.guild.get_member(302851022790066185)
                    return await ctx.send(f"Only {regaus.display_name} is allowed to do that.")
            if ctx.author.id == 424472476106489856:  # Canvas
                if user.id != 302851022790066185:  # Regaus
                    return await ctx.send(f"{emotes.Deny} you allowed to do that, {ctx.author.name}.")
        embed = discord.Embed(colour=generic.random_colour())
        embed.description = f"**{user.name}** was kissed by **{ctx.author.name}**"
        embed.set_image(url=random.choice(self.kiss))
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
        return await ctx.send(embed=embed)

    @commands.command(name="slap", aliases=["kill", "shoot", "punch", "hit"])
    @commands.guild_only()
    async def slap(self, ctx, user: discord.Member):
        """ Violence! """
        if ctx.guild.id == 690162603275714574:
            return await ctx.send("This command has been disabled in this server.")
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
        return await ctx.send(embed=embed)

    @commands.command(name="bang", aliases=["fuck"], hidden=True)
    @commands.guild_only()
    async def fuck(self, ctx, user: discord.Member = None):
        """ Bang someone """
        if ctx.guild.id == 690162603275714574:
            return await ctx.send("This command has been disabled in this server.")
        if user is None:
            return await ctx.send_help(str(ctx.command))
        if user.id == self.bot.user.id:
            return await ctx.send("No. I'm taken, find someone else.")
        if user == ctx.author:
            return await ctx.send("How are you going to do that?")
        if ctx.guild.id == 679055998186553344:
            if user.id == 302851022790066185 and ctx.author.id != 424472476106489856:
                return await ctx.send(f"{emotes.Deny} Nope, you are not allowed to do that.")
            if user.id == 424472476106489856 and ctx.author.id != 302851022790066185:
                return await ctx.send(f"{emotes.Deny} Nope, you are not allowed to do that.")
        return await ctx.send(f"{emotes.Scary} {emotes.NotLikeThis} {ctx.author.name} is now "
                              f"{ctx.invoked_with}ing {user.name}...")

    @commands.command(name="bean")
    @commands.guild_only()
    async def bean(self, ctx, user: discord.Member):
        """ Bean someone """
        return await ctx.send(f"{emotes.Licc} Successfully beaned {user.name}")

    @commands.command(name="cookie")
    @commands.guild_only()
    async def cookie(self, ctx, user: discord.Member):
        """ Give someone a cookie """
        if user == ctx.author:
            return await ctx.send(f"Don't be greedy, {ctx.author.name}! Share it!")
        output = give(ctx.author.name, user.name, ":cookie:")
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
        return await ctx.send(output)

    @commands.command(name="bad")
    async def bad(self, ctx, user: discord.Member):
        """ Bad user """
        if user.id == 302851022790066185:
            user = ctx.author
        if user.id == self.bot.user.id:
            return await ctx.send(f"{emotes.AlexHeartBroken}")
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
        return await ctx.send(file=discord.File(bio, filename=f"trash_{user.name}.png"))

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
        if generic.get_config()["logs"]:
            # await logs.log_channel(self.bot, 'changes').send('Reloaded KB images')
            logs.save(logs.get_place(self.type, "changes"), "Reloaded KB images")
        return await ctx.send("Successfully reloaded images")

    @commands.command(name="ship")
    @commands.guild_only()
    async def ship(self, ctx, user1: discord.Member, user2: discord.Member):
        """ Build a ship """
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
        message = f"Nice shipping there!\nShip names: **{name}** or **{name2}**"
        return await ctx.send(message, file=discord.File(bio, filename=f"shipping_services.png"))

    @commands.command(name="dab", hidden=True)
    async def dab(self, ctx):
        """ Dab """
        return await ctx.send("No")


def setup(bot):
    bot.add_cog(Social(bot))
