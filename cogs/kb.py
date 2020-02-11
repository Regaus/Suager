# KawaiiBot except with images I liked mmlol
# Ah yes, LIDL KawaiiBot
import random

import discord
from discord.ext import commands

from utils import lists, emotes, generic, logs


def is_fucked(something):
    return something == [] or something == lists.error or something == [lists.error]


but_why = "https://cdn.discordapp.com/attachments/610482988123422750/673642028357386241/butwhy.gif"


class KawaiiBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pat, self.hug, self.kiss, self.lick, self.cuddle, self.bite = [lists.error] * 6

    @commands.command(name="pat")
    @commands.guild_only()
    async def pat(self, ctx, user: discord.Member):
        """ Pat someone """
        if is_fucked(self.pat):
            self.pat = await lists.get_images(self.bot, 'p')
        if ctx.author == user:
            return await ctx.send("Don't be like that ;-;")
        if user.id == self.bot.user.id:
            return await ctx.send(f"Thanks, {ctx.author.name} :3 {emotes.AlexHeart}")
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

    @commands.command(name="lick")
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
            return await ctx.send(f"w-why did you lick me, {ctx.author.name}", embed=embed.set_image(url=but_why))
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
            return await ctx.send(f"Thanks {ctx.author.name} {emotes.AlexHeart}. "
                                  f"But, I'm a bot... I wasn't programmed to feel love")
        embed = discord.Embed(colour=generic.random_colour())
        embed.description = f"**{user.name}** was kissed by **{ctx.author.name}**"
        embed.set_image(url=random.choice(self.kiss))
        return await ctx.send(embed=embed)

    @commands.command(name="bite")
    @commands.guild_only()
    async def bite(self, ctx, user: discord.Member):
        """ Bite someone """
        if is_fucked(self.kiss):
            self.kiss = await lists.get_images(self.bot, 'k')
        if user == ctx.author:
            return await ctx.send("How are you going to do that?")
        if user.id == self.bot.user.id:
            return await ctx.send(f"Ow.. why'd you bite me, {ctx.author.name}?")
        embed = discord.Embed(colour=generic.random_colour())
        embed.description = f"**{user.name}** was bitten by **{ctx.author.name}**"
        embed.set_image(url=random.choice(self.kiss))
        return await ctx.send(embed=embed)

    @commands.command(name="slap")
    @commands.guild_only()
    async def slap(self, ctx, user: discord.Member):
        """ Violence! """
        if user == ctx.author:
            return await ctx.send(embed=discord.Embed(colour=generic.random_colour()).set_image(url=but_why))
        if user.id == self.bot.user.id:
            return await ctx.send(f"{ctx.author.name}, we can no longer be friends. ;-; {emotes.AlexHeartBroken}")
        return await ctx.send(f"Violence is never the answer, {ctx.author.name}!")

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
        if generic.get_config().logs:
            await logs.log_channel(self.bot, 'changes').send('Reloaded KawaiiBot images')
        return await ctx.send("Successfully reloaded images")


def setup(bot):
    bot.add_cog(KawaiiBot(bot))
