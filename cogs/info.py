import sys
from io import BytesIO

import discord
from discord import Permissions
from discord.ext import commands
from discord.utils import oauth_url

from utils import general, languages, time


class BotInformation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @commands.command(name="source")
    # @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    # async def source(self, ctx: commands.Context):
    #     """ Source codes """
    #     links = "\n<https://github.com/AlexFlipnote/discord_bot.py>\n<https://github.com/AlexFlipnote/birthday.py>"
    #     return await general.send(langs.gls("info_source", langs.gl(ctx)) + links, ctx.channel)

    @commands.command(name="stats", aliases=["info", "about", "status"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def stats(self, ctx: commands.Context):
        """ Bot stats"""
        locale = languages.gl(ctx)
        config = self.bot.config
        version_data = general.get_version()[self.bot.name]
        embed = discord.Embed(colour=general.random_colour())
        embed.title = languages.gls("info_stats_about", locale, self.bot.user, version_data["version"])
        embed.set_thumbnail(url=self.bot.user.avatar_url_as(size=1024))
        owners = "\n".join([str(self.bot.get_user(i)) for i in config["owners"]])
        embed.add_field(name=languages.gls("info_stats_developers", locale), value=f"**{owners}**", inline=True)
        uptime = languages.td_dt(self.bot.uptime, locale, brief=True, suffix=False)
        embed.add_field(name=languages.gls("info_stats_uptime", locale), value=f"**{uptime}**", inline=True)
        embed.add_field(name=languages.gls("info_stats_commands", locale), value=f"**{len(self.bot.commands)}**", inline=True)
        tm, tc, vc, cc = 0, 0, 0, 0
        for guild in self.bot.guilds:
            tm += len(guild.members)
            tc += len(guild.text_channels)
            vc += len(guild.voice_channels)
            cc += len(guild.categories)
        users = len(self.bot.users)
        avg_members = round(tm / len(self.bot.guilds), 1)
        servers = len(self.bot.guilds)
        lm, lu, la = languages.gns(tm, locale), languages.gns(users, locale), languages.gfs(avg_members, locale, 1)
        embed.add_field(name=languages.gls("info_stats_users", locale), value=languages.gls("info_stats_users_data", locale, lm, lu, la), inline=True)
        ls, lt, lc, lv = languages.gns(servers, locale), languages.gns(tc, locale), languages.gns(cc, locale), languages.gns(vc, locale)
        embed.add_field(name=languages.gls("info_stats_servers", locale), value=languages.gls("info_stats_servers_data", locale, ls, lt, lc, lv), inline=True)
        _version = sys.version_info
        version = f"{_version.major}.{_version.minor}.{_version.micro}"
        embed.add_field(name=languages.gls("info_stats_used", locale), inline=True, value=f"**discord.py v{discord.__version__}\nPython v{version}**")
        mv = version_data["version"].split(".")[0]
        fv, mr, lu = languages.gts(time.from_ts(version_data["first_version"], None), locale), \
                     languages.gts(time.from_ts(version_data["major_release"], None), locale), languages.gts(time.from_ts(version_data["last_update"], None), locale)
        embed.add_field(name=languages.gls("info_stats_dates", locale), value=languages.gls("info_stats_dates_data", locale, fv, mr, lu, mv), inline=True)
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
        return await general.send(languages.gls("info_invite_bot", languages.gl(ctx), ctx.author.name, link), ctx.channel)

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


def setup(bot):
    bot.add_cog(BotInformation(bot))
