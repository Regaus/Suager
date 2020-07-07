import sys
from io import BytesIO

import discord
from discord.ext import commands

from core.utils import general, time


class BotInformation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="source")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def source(self, ctx: commands.Context):
        """ Source codes """
        return await general.send("There are the links you can use if you want to make your own bot\n<https://github.com/AlexFlipnote/discord_bot.py>\n"
                                  "<https://github.com/AlexFlipnote/birthday.py>", ctx.channel)

    @commands.command(name="stats", aliases=["info", "about", "status"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def stats(self, ctx: commands.Context):
        """ Bot stats"""
        config = self.bot.config
        local_config = self.bot.local_config
        embed = discord.Embed(colour=general.random_colour())
        uptime = time.human_timedelta(self.bot.uptime, brief=True, suffix=False)
        start_time = time.human_timedelta(self.bot.start_time, brief=True)
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        owners = "\n".join([str(self.bot.get_user(i)) for i in config["owners"]])
        admins = "\n".join([str(self.bot.get_user(i)) for i in local_config["admins"]])
        embed.add_field(name="Developers",  value=f"**{owners}**", inline=True)
        embed.add_field(name="Admins",  value=f"**{admins}**" if admins else "None", inline=True)
        embed.add_field(name="Uptime", value=f"Boot time: **{start_time}**\nUptime: **{uptime}**")
        tm, tc, vc, cc = 0, 0, 0, 0
        for guild in self.bot.guilds:
            tm += len(guild.members)
            tc += len(guild.text_channels)
            vc += len(guild.voice_channels)
            cc += len(guild.categories)
        users = len(self.bot.users)
        avg_members = round(tm / len(self.bot.guilds), 1)
        servers = len(self.bot.guilds)
        command = len(self.bot.commands)  # command amount
        embed.add_field(name="Counters", value=f"Commands: **{command}**\nServers: **{servers:,}**\nUsers: **{users:,}**\nAvg. Members: **{avg_members}**")
        embed.add_field(name="Server counters", value=f"Members: **{tm:,}**\nText channels: **{tc:,}**\nCategories: **{cc:,}**\nVoice channels: **{vc:,}**")
        _version = sys.version_info
        version = f"{_version.major}.{_version.minor}.{_version.micro}"
        embed.add_field(name="What I Use", inline=True, value=f"**discord.py v{discord.__version__}\nPython v{version}**")
        first_version = time.time_output(time.from_ts(local_config["first_version"], None), tz=True)
        major_release = time.time_output(time.from_ts(local_config["major_release"], None), tz=True)
        last_update = time.time_output(time.from_ts(local_config["last_update"], None), tz=True)
        mv = local_config["version"].split(".")[0]
        embed.add_field(name="Dates", value=f"First version: **{first_version}**\nRelease v{mv}.0: **{major_release}**\nLast update: **{last_update}**")
        embed.title = f"ℹ About {local_config['name']} | {self.bot.user} | v{local_config['version']}"
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
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def invite(self, ctx: commands.Context):
        """ Invite me to your own server! """
        perms = 470150231
        return await general.send(f"{ctx.author.name}, use this link to invite me to your server:\n<https://discordapp.com/oauth2/authorize?permissions="
                                  f"{perms}&client_id={self.bot.user.id}&scope=bot>", ctx.channel)

    @commands.command(name="botserver")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def my_server(self, ctx: commands.Context):
        """ Get an invite to my server """
        if isinstance(ctx.channel, discord.DMChannel) or ctx.guild.id != self.bot.local_config["home_server_id"]:
            invite = self.bot.local_config["home_invite"]
            if invite:
                try:
                    await ctx.author.send(f"{ctx.author.name}, here is an invite to my server")
                    await ctx.author.send(invite)
                    try:
                        await ctx.message.add_reaction("✉")
                    except discord.Forbidden:
                        pass
                except discord.Forbidden:
                    return await general.send("Failed to send you the invite", ctx.channel)
            else:
                return await general.send("This bot has no server invite set up.", ctx.channel)
        else:
            return await general.send("But this is my home already!", ctx.channel)

    @commands.command(name="ping")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def ping(self, ctx: commands.Context):
        """ Ping Pong """
        import time as _time
        ws = int(self.bot.latency * 1000)
        r1 = f"Message Send: undefined\nMessage Edit: undefined\nWS Latency: {ws:,}ms"
        t1 = _time.monotonic()
        msg = await general.send(r1, ctx.channel, u=[ctx.author])
        t2 = int((_time.monotonic() - t1) * 1000)
        r2 = f"Message Send: {t2:,}ms\nMessage Edit: undefined\nWS Latency: {ws:,}ms"
        t2s = _time.monotonic()
        await msg.edit(content=r2)
        t3 = int((_time.monotonic() - t2s) * 1000)
        r3 = f"Message Send: {t2:,}ms\nMessage Edit: {t3:,}ms\nWS Latency: {ws:,}ms"
        await msg.edit(content=r3)


def setup(bot):
    bot.add_cog(BotInformation(bot))
