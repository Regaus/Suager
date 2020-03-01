import os
import random
import sys
from datetime import datetime

import discord
import psutil
from discord.ext import commands

from utils import generic, time, lists


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.creation_date = datetime(2020, 3, 2, 18)
        self.birthday = datetime(2018, 12, 6, 1, 2)

    @commands.command(name="source")
    async def source(self, ctx):
        """ Source codes <3 """
        # Do not remove this command, this has to stay due to the GitHub LICENSE.
        # TL:DR, you have to disclose source according to GNU GPL v3.
        # Reference: https://github.com/AlexFlipnote/birthday.py/blob/master/LICENSE
        await ctx.send(f"These links are at fault for the fact that **{ctx.bot.user}** works:\n"
                       f"<https://github.com/AlexFlipnote/discord_bot.py>\n"
                       f"<https://github.com/AlexFlipnote/birthday.py>")

    @commands.command(name="stats", aliases=["info", "about", "status"])
    async def stats(self, ctx):
        """ Bot stats"""
        config = generic.get_config()
        embed = discord.Embed(colour=generic.random_colour())
        uptime = time.human_timedelta(self.bot.uptime, accuracy=3, suffix=True)
        when = time.time_output(self.bot.uptime)
        embed.description = random.choice(lists.phrases)
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.add_field(name="Last Boot", value=f"{when}\n{uptime}", inline=False)
        owners = len(config.owners)
        owners_ = ", ".join([str(self.bot.get_user(i)) for i in config.owners])
        embed.add_field(name=f"Developer{'' if owners == 1 else 's'}", value=owners_, inline=False)
        # owners = len(self.config.owners)
        # owners_ = ", ".join([str(self.bot.get_user(i)) for i in self.config.owners])
        # embed.add_field(name=f"Developer{'' if owners == 1 else 's'}", value=owners_, inline=True)
        total_members = 0
        for guild in self.bot.guilds:
            total_members += len(guild.members)
        users = len(self.bot.users)
        avg_members = round(total_members / len(self.bot.guilds), 1)
        embed.add_field(name="Servers", value=f"{len(self.bot.guilds)} servers", inline=True)
        embed.add_field(name="Avg. members/server", value=f"{avg_members} members", inline=True)
        embed.add_field(name="Total users", value=f"{total_members} members\n{users} users")
        embed.add_field(name="Commands", value=str(len([j.name for j in self.bot.commands])), inline=True)
        try:
            ram_usage = psutil.Process(os.getpid()).memory_full_info().rss / 1024 ** 2
            embed.add_field(name="RAM Usage", value=f"{ram_usage:.2f} MB", inline=True)
        except psutil.AccessDenied:
            embed.add_field(name="RAM Usage", value="Access Denied", inline=True)
        _version = sys.version_info
        version = f"{_version.major}.{_version.minor}.{_version.micro}"
        embed.add_field(name="What I use", value=f"discord.py v{discord.__version__}\nPython v{version}", inline=True)
        # creation_date = datetime(2019, 12, 12, 23, 20)  # As of version 3
        # creation_date = statuses.creation_time
        birthday = time.time_output(self.birthday)
        birthday_ta = time.human_timedelta(self.birthday, accuracy=3)
        embed.add_field(name="My Birthday", value=f"{birthday}\n{birthday_ta}", inline=False)
        _creation_date = time.time_output(self.creation_date)
        _created_ago = time.human_timedelta(self.creation_date, accuracy=3)
        embed.add_field(name="Creation Date (v4)", value=f"{_creation_date}\n{_created_ago}", inline=False)
        # last_update = datetime(2019, 12, 13, 21)
        last_update = datetime.fromtimestamp(config.last_update)
        __last_update = time.time_output(last_update)
        _last_update = time.human_timedelta(last_update, accuracy=3)
        embed.add_field(name="Last Updated", value=f"{__last_update}\n{_last_update}", inline=False)
        return await ctx.send(content=f"ℹ About **{self.bot.user}** | **v{config.full_version}**", embed=embed)

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


def setup(bot):
    bot.add_cog(Info(bot))
