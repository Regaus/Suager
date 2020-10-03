import sys
from io import BytesIO

import discord
from discord.ext import commands

from core.utils import general, time
from languages import langs


class BotInformation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="source")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def source(self, ctx: commands.Context):
        """ Source codes """
        links = "\n<https://github.com/AlexFlipnote/discord_bot.py>\n<https://github.com/AlexFlipnote/birthday.py>"
        return await general.send(langs.gls("info_source", langs.gl(ctx)) + links, ctx.channel)

    @commands.command(name="stats", aliases=["info", "about", "status"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def stats(self, ctx: commands.Context):
        """ Bot stats"""
        locale = langs.gl(ctx)
        config = self.bot.config
        local_config = self.bot.local_config
        embed = discord.Embed(colour=general.random_colour())
        embed.title = langs.gls("info_stats_about", locale, self.bot.user, local_config["version"])
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        owners = "\n".join([str(self.bot.get_user(i)) for i in config["owners"]])
        embed.add_field(name=langs.gls("info_stats_developers", locale),  value=f"**{owners}**", inline=True)
        uptime = langs.td_dt(self.bot.uptime, locale, brief=True, suffix=False)
        embed.add_field(name=langs.gls("info_stats_uptime", locale), value=f"**{uptime}**", inline=True)
        embed.add_field(name=langs.gls("info_stats_commands", locale), value=f"**{len(self.bot.commands)}**", inline=True)
        tm, tc, vc, cc = 0, 0, 0, 0
        for guild in self.bot.guilds:
            tm += len(guild.members)
            tc += len(guild.text_channels)
            vc += len(guild.voice_channels)
            cc += len(guild.categories)
        users = len(self.bot.users)
        avg_members = round(tm / len(self.bot.guilds), 1)
        servers = len(self.bot.guilds)
        lm, lu, la = langs.gns(tm, locale), langs.gns(users, locale), langs.gfs(avg_members, locale, 1)
        embed.add_field(name=langs.gls("info_stats_users", locale), value=langs.gls("info_stats_users_data", locale, lm, lu, la), inline=True)
        ls, lt, lc, lv = langs.gns(servers, locale), langs.gns(tc, locale), langs.gns(cc, locale), langs.gns(vc, locale)
        embed.add_field(name=langs.gls("info_stats_servers", locale), value=langs.gls("info_stats_servers_data", locale, ls, lt, lc, lv), inline=True)
        _version = sys.version_info
        version = f"{_version.major}.{_version.minor}.{_version.micro}"
        embed.add_field(name=langs.gls("info_stats_used", locale), inline=True, value=f"**discord.py v{discord.__version__}\nPython v{version}**")
        mv = local_config["version"].split(".")[0]
        fv, mr, lu = langs.gts(time.from_ts(local_config["first_version"], None), locale), \
            langs.gts(time.from_ts(local_config["major_release"], None), locale), langs.gts(time.from_ts(local_config["last_update"], None), locale)
        embed.add_field(name=langs.gls("info_stats_dates", locale), value=langs.gls("info_stats_dates_data", locale, fv, mr, lu, mv), inline=True)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="servers", aliases=["guilds"])
    @commands.is_owner()
    async def servers(self, ctx: commands.Context):
        """ The servers the bot is in """
        _servers = list(self.bot.guilds)
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
        perms = 470150231
        link = f"\n<https://discordapp.com/oauth2/authorize?permissions={perms}&client_id={self.bot.user.id}&scope=bot>"
        return await general.send(langs.gls("info_invite_bot", langs.gl(ctx), ctx.author.name) + link, ctx.channel)

    @commands.command(name="botserver")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def my_server(self, ctx: commands.Context):
        """ Get an invite to my server """
        locale = langs.gl(ctx)
        if isinstance(ctx.channel, discord.DMChannel) or ctx.guild.id != self.bot.local_config["home_server_id"]:
            invite = self.bot.local_config["home_invite"]
            if invite:
                try:
                    await ctx.author.send(langs.gls("info_server", locale, ctx.author.name))
                    await ctx.author.send(invite)
                    try:
                        await ctx.message.add_reaction("✉")
                    except discord.Forbidden:
                        pass
                except discord.Forbidden:
                    return await general.send(langs.gls("info_server_failed", locale), ctx.channel)
            else:
                return await general.send(langs.gls("info_server_none", locale), ctx.channel)
        else:
            return await general.send(langs.gls("info_server_home", locale), ctx.channel)

    @commands.command(name="ping")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def ping(self, ctx: commands.Context):
        """ Ping Pong """
        import time as _time
        locale = langs.gl(ctx)
        ws = int(self.bot.latency * 1000)
        r1 = langs.gls("info_ping_1", locale, langs.gns(ws))
        t1 = _time.monotonic()
        msg = await general.send(r1, ctx.channel, u=[ctx.author])
        t2 = int((_time.monotonic() - t1) * 1000)
        r2 = langs.gls("info_ping_2", locale, langs.gns(ws), langs.gns(t2))
        t2s = _time.monotonic()
        await msg.edit(content=r2)
        t3 = int((_time.monotonic() - t2s) * 1000)
        r3 = langs.gls("info_ping_3", locale, langs.gns(ws), langs.gns(t2), langs.gns(t3))
        await msg.edit(content=r3)


def setup(bot):
    bot.add_cog(BotInformation(bot))
