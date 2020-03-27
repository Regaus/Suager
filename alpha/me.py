import random
import sys
from datetime import datetime

import discord
import psutil
from discord.ext import commands

from alpha import main
from utils import generic, time, lists, prev


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.creation_date = datetime(2020, 3, 2, 18)
        self.birthday = datetime(2018, 12, 6, 1, 2)
        self.type = main.version

    @commands.command(name="source")
    async def source(self, ctx):
        """ Source codes <3 """
        # Do not remove this command, this has to stay due to the GitHub LICENSE.
        # TL:DR, you have to disclose source according to GNU GPL v3.
        # Reference: https://github.com/AlexFlipnote/birthday.py/blob/master/LICENSE
        await ctx.send(f"It's these links' fault that **{ctx.bot.user}** even exists and works:\n"
                       f"<https://github.com/AlexFlipnote/discord_bot.py>\n"
                       f"<https://github.com/AlexFlipnote/birthday.py>")

    @commands.command(name="stats", aliases=["info", "about", "status"])
    async def stats(self, ctx):
        """ Bot stats"""
        async with ctx.typing():
            config = generic.get_config()
            embed = discord.Embed(colour=generic.random_colour())
            # uptime = time.human_timedelta(self.bot.uptime, accuracy=3, suffix=True)
            # uptime = time.timedelta(time.now() - self.bot.uptime)
            uptime = time.timesince(self.bot.uptime)
            process = psutil.Process()
            ram = round(process.memory_info().rss / 1048576, 2)
            cpu = process.cpu_percent()
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
            # embed.add_field(name="Uptime", value=f"{when}\n{uptime}", inline=False)
            # embed.add_field(name=f"Developer{'' if owners == 1 else 's'}", value=owners_, inline=False)
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
            # embed.add_field(name="Servers", value=f"{len(self.bot.guilds)} servers", inline=True)
            # embed.add_field(name="Avg. members/server", value=f"{avg_members} members", inline=True)
            # embed.add_field(name="Total users", value=f"{total_members} members\n{users} users")
            # embed.add_field(name="Commands", value=str(len([j.name for j in self.bot.commands])), inline=True)
            files, functions, comments, lines, classes = generic.line_count()
            embed.add_field(name="__Code Stats__", inline=True,
                            value=f"Files: **{files:,}**\nLines: **{lines:,}**\nComments: **{comments:,}**\n"
                                  f"Functions: **{functions:,}**\nClasses: **{classes:,}**")
            cpu = process.cpu_percent(interval=2)
            embed.add_field(name="__Process__", inline=True, value=f"RAM: **{ram} MB**\nCPU: **{cpu}%**")
            # try:
            #     ram_usage = psutil.Process(os.getpid()).memory_full_info().rss / 1024 ** 2
            #     embed.add_field(name="RAM Usage", value=f"{ram_usage:.2f} MB", inline=True)
            # except psutil.AccessDenied:
            #     embed.add_field(name="RAM Usage", value="Access Denied", inline=True)
            embed.add_field(name="__Server Counts__", inline=True,
                            value=f"Members: **{tm:,}**\nText Channels: **{tc:,}**\n"
                                  f"Categories: **{cc:,}**\nVoice Channels: **{vc:,}**")
            _version = sys.version_info
            version = f"{_version.major}.{_version.minor}.{_version.micro}"
            embed.add_field(name="__What I Use__", inline=True,
                            value=f"**discord.py v{discord.__version__}\nPython v{version}**")
            # embed.add_field(name="What I use", value=f"discord.py v{discord.__version__}\n
            # Python v{version}", inline=True)
            # creation_date = datetime(2019, 12, 12, 23, 20)  # As of version 3
            # creation_date = statuses.creation_time
            birthday = time.time_output(self.birthday)
            v4_created = time.time_output(self.creation_date)
            last_update = time.time_output(time.from_ts(config["bots"][self.type]["last_update"]))
            embed.add_field(name="__Dates__", inline=False, value=f"Suager Creation: **{birthday}**\nCreation of v4: "
                                                              f"**{v4_created}**\nLast Update: **{last_update}**")
            embed.title = f"ℹ About **{self.bot.user}** | **v{config['bots'][self.type]['full_version']}**"
            # birthday_ta = time.human_timedelta(self.birthday, accuracy=3)
            # embed.add_field(name="My Birthday", value=f"{birthday}\n{birthday_ta}", inline=False)
            # _created_ago = time.human_timedelta(self.creation_date, accuracy=3)
            # embed.add_field(name="Creation Date (v4)", value=f"{_creation_date}\n{_created_ago}", inline=False)
            # last_update = datetime(2019, 12, 13, 21)
            # _last_update = time.human_timedelta(last_update, accuracy=3)
            # embed.add_field(name="Last Updated", value=f"{__last_update}\n{_last_update}", inline=False)
            return await ctx.send(embed=embed)

    @commands.command(name="servers", aliases=["guilds"])
    @commands.is_owner()
    async def servers(self, ctx):
        """ The servers the bot is in """
        _servers = list(self.bot.guilds)
        message = f"Connected to {len(_servers)} servers:"
        for guild in _servers:
            message += f"\n{guild.name}"
        return await ctx.send(message)

    @commands.command(name="invite")
    async def invite(self, ctx):
        """ Invite me to your server! """
        perms = 470150231
        return await ctx.send(f"{ctx.author.name}, use this link to invite me:\n<https://discordapp.com/oauth2/"
                              f"authorize?permissions={perms}&client_id={self.bot.user.id}&scope=bot>")

    @commands.command(name="botserver")
    async def my_server(self, ctx):
        """ My server """
        if isinstance(ctx.channel, discord.DMChannel) or ctx.guild.id != 568148147457490954:
            return await ctx.send(f"**Here you go {ctx.author.name}\n{generic.invite}**")
        return await ctx.send("This is my how, j'know <3")

    @commands.command(name="ping")
    async def ping(self, ctx):
        """ Ping Pong """
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
