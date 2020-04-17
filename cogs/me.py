import random
import sys
from datetime import datetime

import discord
import psutil
from discord.ext import commands

from cogs import main
from utils import generic, time, lists, prev


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.creation_date = datetime(2020, 3, 2, 18)
        self.birthday = datetime(2018, 12, 6, 1, 2)
        self.type = main.version
        self.banned = [690254056354087047, 694684764074016799]

    @commands.command(name="source")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def source(self, ctx):
        """ Source codes <3 """
        # Do not remove this command, this has to stay due to the GitHub LICENSE.
        # TL:DR, you have to disclose source according to GNU GPL v3.
        # Reference: https://github.com/AlexFlipnote/birthday.py/blob/master/LICENSE
        if ctx.channel.id in self.banned:
            return
        await ctx.send(f"It's these links' fault that **{ctx.bot.user}** even exists and works, "
                       f"and you should check those out if you wanna have your own bot:\n"
                       f"<https://github.com/AlexFlipnote/discord_bot.py>\n"
                       f"<https://github.com/AlexFlipnote/birthday.py>")

    @commands.command(name="stats", aliases=["info", "about", "status"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def stats(self, ctx):
        """ Bot stats"""
        if ctx.channel.id in self.banned:
            return
        async with ctx.typing():
            config = generic.get_config()
            embed = discord.Embed(colour=generic.random_colour())
            uptime = time.timesince(self.bot.uptime)
            process = psutil.Process()
            ram = round(process.memory_info().rss / 1048576, 2)
            process.cpu_percent(interval=1)
            corona = list("corona virus")
            random.shuffle(corona)
            corona_virus = (''.join(corona)).title()
            # when = time.time_output(self.bot.uptime)
            embed.description = random.choice(lists.phrases)
            embed.set_thumbnail(url=self.bot.user.avatar_url)
            owners = len(config["owners"])
            owners_ = ", ".join([str(self.bot.get_user(i)) for i in config["owners"]])
            embed.add_field(name="__Generic__", inline=True,
                            value=f"Developer{'' if owners == 1 else 's'}: **{owners_}**\nUptime: **{uptime}**\n"
                                  f"Conora Virus: **{corona_virus}**")
            tm = 0
            tc, vc, cc = 0, 0, 0
            for guild in self.bot.guilds:
                tm += len(guild.members)
                tc += len(guild.text_channels)
                vc += len(guild.voice_channels)
                cc += len(guild.categories)
            users = len(self.bot.users)
            avg_members = round(tm / len(self.bot.guilds), 1)
            embed.add_field(name="__Counts__", inline=True,
                            value=f"Servers: **{len(self.bot.guilds):,}**\nUsers: **{users:,}**\n"
                                  f"Avg members / server: **{avg_members:,}**\n"
                                  f"Commands: **{len([j.name for j in self.bot.commands])}**")
            files, functions, comments, lines, classes = generic.line_count()
            embed.add_field(name="__Code Stats__", inline=True,
                            value=f"Files: **{files:,}**\nLines: **{lines:,}**\nComments: **{comments:,}**\n"
                                  f"Functions: **{functions:,}**\nClasses: **{classes:,}**")
            cpu = round(process.cpu_percent() / psutil.cpu_count(), 2)
            embed.add_field(name="__Process__", inline=True, value=f"RAM: **{ram} MB**\nCPU: **{cpu}%**")
            embed.add_field(name="__Server Counts__", inline=True,
                            value=f"Members: **{tm:,}**\nText Channels: **{tc:,}**\n"
                                  f"Categories: **{cc:,}**\nVoice Channels: **{vc:,}**")
            _version = sys.version_info
            version = f"{_version.major}.{_version.minor}.{_version.micro}"
            embed.add_field(name="__What I Use__", inline=True,
                            value=f"**discord.py v{discord.__version__}\nPython v{version}**")
            birthday = time.time_output(self.birthday)
            v4_created = time.time_output(self.creation_date)
            last_update = time.time_output(time.from_ts(config["bots"][self.type]["last_update"]))
            embed.add_field(name="__Dates__", inline=False, value=f"Suager Creation: **{birthday}**\nCreation of v4: "
                                                                  f"**{v4_created}**\nLast Update: **{last_update}**")
            embed.title = f"ℹ About **{self.bot.user}** | **v{config['bots'][self.type]['full_version']}**"
            return await ctx.send(embed=embed)

    @commands.command(name="servers", aliases=["guilds"])
    @commands.is_owner()
    async def servers(self, ctx):
        """ The servers the bot is in """
        if ctx.channel.id in self.banned:
            return
        _servers = list(self.bot.guilds)
        message = f"Connected to {len(_servers)} servers:"
        for guild in _servers:
            message += f"\n{guild.name}"
        return await ctx.send(message)

    @commands.command(name="invite")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def invite(self, ctx):
        """ Invite me to your server! """
        if ctx.channel.id in self.banned:
            return
        perms = 470150231
        return await ctx.send(f"{ctx.author.name}, use this link to invite me:\n<https://discordapp.com/oauth2/"
                              f"authorize?permissions={perms}&client_id={self.bot.user.id}&scope=bot>")

    @commands.command(name="botserver")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def my_server(self, ctx):
        """ My server """
        if ctx.channel.id in self.banned:
            return
        if isinstance(ctx.channel, discord.DMChannel) or ctx.guild.id != 568148147457490954:
            return await ctx.send(f"**Here you go {ctx.author.name}\n{generic.invite}**")
        return await ctx.send("This is my how, j'know <3")

    @commands.command(name="ping")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def ping(self, ctx):
        """ Ping Pong """
        if ctx.channel.id in self.banned:
            return
        import time as _time
        t1 = _time.monotonic()
        ws = int(self.bot.latency * 1000)
        msg = await ctx.send(f"<a:loading:651883385878478858> {ctx.author.mention} Pong\n"
                             f"Message Send: undefined\nMessage Edit: undefined\nWS: {ws:,}ms")
        t2 = int((_time.monotonic() - t1) * 1000)
        t2s = _time.monotonic()
        await msg.edit(content=f"<a:loading:651883385878478858> {ctx.author.mention} Pong\n"
                               f"Message Send: {t2:,}ms\nMessage Edit: undefined\nWS: {ws:,}ms")
        t3 = int((_time.monotonic() - t2s) * 1000)
        await msg.edit(content=f"{ctx.author.mention} Pong:\n"
                               f"Message Send: {t2:,}ms\nMessage Edit: {t3:,}ms\nWS: {ws:,}ms")

    @commands.command(name="offline")
    @commands.is_owner()
    async def offline(self, ctx):
        """ Server is offline """
        return await prev.status(ctx, 0)

    @commands.command(name="online")
    @commands.is_owner()
    async def online(self, ctx):
        """ Server is online """
        return await prev.status(ctx, 1)

    @commands.command(name="restart")
    @commands.is_owner()
    async def restart(self, ctx):
        """ Notify of restart incoming... """
        return await prev.status(ctx, 2)


def setup(bot):
    bot.add_cog(Info(bot))
