import sys
from io import BytesIO

import discord
from discord import Permissions
from discord.utils import oauth_url
from regaus import __version__ as reg_version

from utils import bot_data, commands, general, time


class BotInformation(commands.Cog, name="Bot Information"):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.command(name="stats", aliases=["info", "about", "status"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def stats(self, ctx: commands.Context):
        """ Stats and information about the bot """
        language = self.bot.language(ctx)
        config = self.bot.config
        version_data = general.get_version()[self.bot.name]
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("info_stats_about", self.bot.user, version_data["version"])
        embed.set_thumbnail(url=str(self.bot.user.display_avatar.replace(size=1024)))
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
        _discord = discord.version_info
        dis_version = f"{_discord.major}.{_discord.minor}.{_discord.micro}"
        if _discord.releaselevel != "final":
            dis_version += _discord.releaselevel[0]
        libs_used = f"**Python v{version}**\n**Discord.py v{dis_version}**"
        if self.bot.name == "cobble":
            libs_used += f"\n**Regaus.py v{reg_version}**"
        embed.add_field(name=language.string("info_stats_used"), inline=True, value=libs_used)
        mv = version_data["version"].split(".")[0]
        fv = language.time(time.from_ts(version_data["first_version"], None), short=1, dow=False, seconds=False, tz=True, uid=ctx.author.id)
        mr = language.time(time.from_ts(version_data["major_release"], None), short=1, dow=False, seconds=False, tz=True, uid=ctx.author.id)
        lu = language.time(time.from_ts(version_data["last_update"], None), short=1, dow=False, seconds=False, tz=True, uid=ctx.author.id)
        embed.add_field(name=language.string("info_stats_dates"), value=language.string("info_stats_dates_data", fv, mr, lu, mv), inline=True)
        return await ctx.send(embed=embed)

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
                return await ctx.send(send, file=discord.File(data, filename=f"{time.file_ts('Servers')}"))
        return await ctx.send(f"{send}\n```fix\n{message}```")

    @commands.command(name="invite")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def invite(self, ctx: commands.Context):
        """ Invite me to your own server! """
        language = self.bot.language(ctx)
        perms = 470150358  # Old: 470150231
        # link1 = oauth_url(str(self.bot.user.id), permissions=Permissions(perms), scopes=['bot'])
        # link2 = oauth_url(str(self.bot.user.id), permissions=Permissions(0), scopes=['bot'])
        link3 = oauth_url(str(self.bot.user.id), permissions=Permissions(perms), scopes=['bot', 'applications.commands'])
        link4 = oauth_url(str(self.bot.user.id), permissions=Permissions(0), scopes=['bot', 'applications.commands'])
        embed = discord.Embed()
        embed.title = language.string("info_invite_bot")
        embed.description = language.string("info_invite_bot2", recommended=link3, none=link4)  # We will add new servers with slash support by default, in case I do ever add them
        # embed.add_field(name=language.string("info_invite_text"), value=language.string("info_invite_bot2", recommended=link1, none=link2), inline=False)
        # embed.add_field(name=language.string("info_invite_slash"), value=language.string("info_invite_bot2", recommended=link3, none=link4), inline=False)
        if self.bot.name in ["cobble", "kyomi"]:
            embed.set_footer(text=language.string("info_invite_private"))
        # return await general.send(self.bot.language(ctx).string("info_invite_bot", ctx.author.name, link), ctx.channel)
        return await ctx.send(embed=embed)

    @commands.command(name="ping")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def ping(self, ctx: commands.Context):
        """ Check how slow Discord API is today """
        import time as _time
        ws = int(self.bot.latency * 1000)
        t1 = _time.time()
        r1 = f"Message Send: unknown\nMessage Edit: unknown\nWS Latency: {ws:,}ms"
        msg = await ctx.send(r1)  # u=[ctx.author] - I have no idea why it wanted to allow user mentions... Oh well
        t2 = int((_time.time() - t1) * 1000)
        r2 = f"Message Send: {t2:,}ms\nMessage Edit: unknown\nWS Latency: {ws:,}ms"
        t2s = _time.time()
        await msg.edit(content=r2)
        t3 = int((_time.time() - t2s) * 1000)
        r3 = f"Message Send: {t2:,}ms\nMessage Edit: {t3:,}ms\nWS Latency: {ws:,}ms"
        await msg.edit(content=r3)


class SuagerInformation(BotInformation, name="Bot Information"):
    @commands.command(name="suager", hidden=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def suager(self, ctx: commands.Context):
        return await ctx.send("<a:SenkoWatch2:801408192785547264>")


class CobbleInformation(BotInformation, name="Bot Information"):
    @commands.command(name="cobble", aliases=["kaivallus"], hidden=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def cobble(self, ctx: commands.Context):
        return await ctx.send("Vuu Käivallus. Vu ju zäide, via te av Kaagadian kuvalsen zäivan mäikah <:SenkoWatch:739242217666904165>")


def setup(bot: bot_data.Bot):
    if bot.name == "suager":
        bot.add_cog(SuagerInformation(bot))
    elif bot.name == "cobble":
        bot.add_cog(CobbleInformation(bot))
    else:
        bot.add_cog(BotInformation(bot))
