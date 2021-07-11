import sys
from io import BytesIO

import discord
from discord import Permissions
from discord.ext import commands
from discord.utils import oauth_url

from utils import bot_data, general, time


class BotInformation(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.command(name="stats", aliases=["info", "about", "status"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def stats(self, ctx: commands.Context):
        """ Bot stats"""
        language = self.bot.language(ctx)
        config = self.bot.config
        version_data = general.get_version()[self.bot.name]
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("info_stats_about", self.bot.user, version_data["version"])
        embed.set_thumbnail(url=self.bot.user.avatar_url_as(size=1024))
        owners = "\n".join([str(self.bot.get_user(i)) for i in config["owners"]])
        embed.add_field(name=language.string("info_stats_developers"), value=f"**{owners}**", inline=True)
        if self.bot.uptime is None:
            uptime = "Unknown"
        else:
            uptime = language.delta_dt(self.bot.uptime, accuracy=3, brief=True, affix=False)
        embed.add_field(name=language.string("info_stats_uptime"), value=f"**{uptime}**", inline=True)
        embed.add_field(name=language.string("info_stats_commands"), value=f"**{len(self.bot.commands)}**", inline=True)
        tm, tc, vc, cc = 0, 0, 0, 0
        for guild in self.bot.guilds:
            tm += len(guild.members)
            tc += len(guild.text_channels)
            vc += len(guild.voice_channels)
            cc += len(guild.categories)
        users = len(self.bot.users)
        avg_members = round(tm / len(self.bot.guilds), 1)
        servers = len(self.bot.guilds)
        lm, lu, la = language.number(tm), language.number(users), language.number(avg_members, precision=1)
        if self.bot.name == "kyomi":
            embed.add_field(name=language.string("info_stats_users"), value=language.string("info_stats_users_data2", lm, lu), inline=True)
        else:
            embed.add_field(name=language.string("info_stats_users"), value=language.string("info_stats_users_data", lm, lu, la), inline=True)
        ls, lt, lc, lv = language.number(servers), language.number(tc), language.number(cc), language.number(vc)
        embed.add_field(name=language.string("info_stats_servers"), value=language.string("info_stats_servers_data", ls, lt, lc, lv), inline=True)
        _version = sys.version_info
        version = f"{_version.major}.{_version.minor}.{_version.micro}"
        embed.add_field(name=language.string("info_stats_used"), inline=True, value=f"**discord.py v{discord.__version__}\nPython v{version}**")
        mv = version_data["version"].split(".")[0]
        fv = language.time(time.from_ts(version_data["first_version"], None), short=1, dow=False, seconds=False, tz=False)
        mr = language.time(time.from_ts(version_data["major_release"], None), short=1, dow=False, seconds=False, tz=False)
        lu = language.time(time.from_ts(version_data["last_update"], None), short=1, dow=False, seconds=False, tz=False)
        embed.add_field(name=language.string("info_stats_dates"), value=language.string("info_stats_dates_data", fv, mr, lu, mv), inline=True)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="servers", aliases=["guilds"])
    @commands.is_owner()
    async def servers(self, ctx: commands.Context):
        """ The servers the bot is in """
        _servers = list(self.bot.guilds)
        _servers.sort(key=lambda _guild: _guild.name.lower())
        message = ""
        for guild in _servers:
            message += f"{guild.id} | {guild.name}\n"
        rl = len(message)
        send = f"Connected to {len(_servers)} servers:"
        if rl > 1900:
            async with ctx.typing():
                data = BytesIO(str(message).encode('utf-8'))
                return await general.send(send, ctx.channel, file=discord.File(data, filename=f"{time.file_ts('Servers')}"))
        return await general.send(f"{send}\n```fix\n{message}```", ctx.channel)

    @commands.command(name="invite")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def invite(self, ctx: commands.Context):
        """ Invite me to your own server! """
        perms = 470150358  # Old: 470150231
        # link = f"\n<https://discordapp.com/oauth2/authorize?permissions={perms}&client_id={self.bot.user.id}&scope=bot>"
        link = f"<{oauth_url(str(self.bot.user.id), Permissions(perms))}>"
        return await general.send(self.bot.language(ctx).string("info_invite_bot", ctx.author.name, link), ctx.channel)

    @commands.command(name="ping")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def ping(self, ctx: commands.Context):
        """ Check how slow Discord API is today """
        import time as _time
        ws = int(self.bot.latency * 1000)
        t1 = _time.time()
        r1 = f"Message Send: unknown\nMessage Edit: unknown\nWS Latency: {ws:,}ms"
        msg = await general.send(r1, ctx.channel, u=[ctx.author])
        t2 = int((_time.time() - t1) * 1000)
        r2 = f"Message Send: {t2:,}ms\nMessage Edit: unknown\nWS Latency: {ws:,}ms"
        t2s = _time.time()
        await msg.edit(content=r2)
        t3 = int((_time.time() - t2s) * 1000)
        r3 = f"Message Send: {t2:,}ms\nMessage Edit: {t3:,}ms\nWS Latency: {ws:,}ms"
        await msg.edit(content=r3)


def setup(bot: bot_data.Bot):
    bot.add_cog(BotInformation(bot))
