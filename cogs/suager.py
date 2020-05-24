import random
import sys
from datetime import datetime, timezone as tz

import discord
import psutil
from discord.ext import commands

from utils import generic, time, lists


class Suager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # self.creation_date = datetime(2020, 3, 2, 18)  # this was v4
        self.creation_date = datetime(2020, 12, 31, 23, 59, 59, tzinfo=tz.utc)  # Date of creation of v5 (placeholder) || Note to self: make this time be in UTC
        self.birthday = datetime(2018, 12, 6, 1, 2, tzinfo=tz.utc)  # Date when the user was created

    @commands.command(name="source")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def source(self, ctx: commands.Context):
        """ Source codes <3 """
        # Do not remove this command, this has to stay due to the GitHub LICENSE.
        # TL:DR, you have to disclose source according to GNU GPL v3.
        # Reference: https://github.com/AlexFlipnote/birthday.py/blob/master/LICENSE
        locale = generic.get_lang(ctx.guild)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        return await generic.send(generic.gls(locale, "source") + "\n<https://github.com/AlexFlipnote/discord_bot.py>\n"
                                                                  "<https://github.com/AlexFlipnote/birthday.py>", ctx.channel)

    @commands.command(name="stats", aliases=["info", "about", "status"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def stats(self, ctx: commands.Context):
        """ Bot stats"""
        locale = generic.get_lang(ctx.guild)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        async with ctx.typing():
            config = generic.get_config()
            embed = discord.Embed(colour=generic.random_colour())
            uptime = time.timesince(self.bot.uptime)
            process = psutil.Process()
            ram = round(process.memory_info().rss / 1048576, 2)
            process.cpu_percent(interval=1)
            embed.description = random.choice(lists.phrases)
            embed.set_thumbnail(url=self.bot.user.avatar_url)
            owners = ", ".join([str(self.bot.get_user(i)) for i in config["owners"]])
            embed.add_field(name=generic.gls(locale, "generic"), inline=True, value=generic.gls(locale, "generic_info", [owners, uptime]))
            tm = 0
            tc, vc, cc = 0, 0, 0
            for guild in self.bot.guilds:
                tm += len(guild.members)
                tc += len(guild.text_channels)
                vc += len(guild.voice_channels)
                cc += len(guild.categories)
            users = len(self.bot.users)
            avg_members = round(tm / len(self.bot.guilds), 1)
            servers = len(self.bot.guilds)
            embed.add_field(name=generic.gls(locale, "counts"), inline=True,
                            value=generic.gls(locale, "counts_info", [f"{servers:,}", f"{users:,}", f"{avg_members:,}",
                                                                      len([j.name for j in self.bot.commands])]))
            files, functions, comments, lines, classes = generic.line_count()
            embed.add_field(name=generic.gls(locale, "code_stats"), inline=True,
                            value=generic.gls(locale, "code_stats_info", [f"{files:,}", f"{lines:,}", f"{comments:,}", f"{functions:,}", f"{classes:,}"]))
            cpu = round(process.cpu_percent() / psutil.cpu_count(), 2)
            embed.add_field(name=generic.gls(locale, "process"), inline=True, value=generic.gls(locale, "process_info", [ram, cpu]))
            embed.add_field(name=generic.gls(locale, "counts2"), inline=True,
                            value=generic.gls(locale, "counts2_info", [f"{tm:,}", f"{tc:,}", f"{cc:,}", f"{vc:,}"]))
            _version = sys.version_info
            version = f"{_version.major}.{_version.minor}.{_version.micro}"
            embed.add_field(name=generic.gls(locale, "what_i_use"), inline=True, value=f"**discord.py v{discord.__version__}\nPython v{version}**")
            birthday = time.time_output(self.birthday, tz=True)
            v5_created = time.time_output(self.creation_date, tz=True)
            last_update = time.time_output(time.from_ts(config["last_update"], True), tz=True)
            embed.add_field(name=generic.gls(locale, "dates"), inline=False, value=generic.gls(locale, "dates_info", [birthday, v5_created, last_update]))
            embed.title = generic.gls(locale, "about_suager", [str(self.bot.user), config["full_version"]])
            return await generic.send(None, ctx.channel, embed=embed)
            # return await ctx.send(embed=embed)

    @commands.command(name="servers", aliases=["guilds"])
    @commands.is_owner()
    async def servers(self, ctx: commands.Context):
        """ The servers the bot is in """
        _servers = list(self.bot.guilds)
        message = f"Connected to {len(_servers)} servers:"
        for guild in _servers:
            message += f"\n{guild.name}"
        return await generic.send(message, ctx.channel)
        # return await ctx.send(message)

    @commands.command(name="invite")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def invite(self, ctx: commands.Context):
        """ Invite me to your own server! """
        locale = generic.get_lang(ctx.guild)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        perms = 470150231
        return await generic.send(generic.gls(locale, "invite_bot", [ctx.author.name, perms, self.bot.user.id]), ctx.channel)
        # return await ctx.send(f"{ctx.author.name}, use this link to invite me:\n<https://discordapp.com/oauth2/"
        #                       f"authorize?permissions={perms}&client_id={self.bot.user.id}&scope=bot>")

    @commands.command(name="botserver")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def my_server(self, ctx: commands.Context):
        """ Get an invite to my server """
        locale = generic.get_lang(ctx.guild)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        if isinstance(ctx.channel, discord.DMChannel) or ctx.guild.id != 568148147457490954:
            try:
                await ctx.author.send(generic.gls(locale, "invite_to_sl", [ctx.author.name]))
                await ctx.author.send(generic.invite)
                return await ctx.message.add_reaction("✉")
            except discord.Forbidden:
                return await generic.send(generic.gls(locale, "invite_to_sl_failed"), ctx.channel)
            # return await ctx.send(f"**Here you go {ctx.author.name}\n{generic.invite}**")
        return await generic.send("But this is my home already!", ctx.channel)
        # return await ctx.send("This is my how, j'know <3")

    @commands.command(name="ping")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def ping(self, ctx: commands.Context):
        """ Ping Pong """
        locale = generic.get_lang(ctx.guild)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        import time as _time
        t1 = _time.monotonic()
        ws = int(self.bot.latency * 1000)
        r1 = generic.gls(locale, "ping1", [ctx.author.mention, f"{ws:,}"])
        msg = await generic.send(r1, ctx.channel, u=[ctx.author])
        # msg = await ctx.send(f"<a:loading:651883385878478858> {ctx.author.mention} Pong\n"
        #                      f"Message Send: undefined\nMessage Edit: undefined\nWS: {ws:,}ms")
        t2 = int((_time.monotonic() - t1) * 1000)
        t2s = _time.monotonic()
        r2 = generic.gls(locale, "ping2", [ctx.author.mention, f"{ws:,}", f"{t2:,}"])
        await msg.edit(content=r2)
        # await msg.edit(content=f"<a:loading:651883385878478858> {ctx.author.mention} Pong\n"
        #                        f"Message Send: {t2:,}ms\nMessage Edit: undefined\nWS: {ws:,}ms")
        t3 = int((_time.monotonic() - t2s) * 1000)
        r3 = generic.gls(locale, "ping3", [ctx.author.mention, f"{ws:,}", f"{t2:,}", f"{t3:,}"])
        await msg.edit(content=r3)
        # await msg.edit(content=f"{ctx.author.mention} Pong:\n"
        #                        f"Message Send: {t2:,}ms\nMessage Edit: {t3:,}ms\nWS: {ws:,}ms")


def setup(bot):
    bot.add_cog(Suager(bot))
