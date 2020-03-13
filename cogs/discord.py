import json
from io import BytesIO

import discord
from discord.ext import commands

from utils import generic, time, permissions, sqlite
from utils.generic import random_colour

prefix_template = {'prefixes': [], 'default': True}
settings_template = {
    'prefixes': [],
    'use_default': True,
    'leveling': {
        'enabled': True,
        'xp_multiplier': 1.0,
        'level_up_message': "[MENTION] is now level **[LEVEL]**! <a:forsendiscosnake:613403121686937601>",
        'ignored_channels': [],
        'announce_channel': 0,
        'rewards': [
            {'level': 2501, 'role': 12345},
            {'level': 2502, 'role': 67890}
        ]
    }
}


class Discord(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite.Database()

    @commands.group(name="server", aliases=["guild"])
    @commands.guild_only()
    async def server(self, ctx):
        """ Check info about current server """
        if ctx.invoked_subcommand is None:
            bots = sum(1 for member in ctx.guild.members if member.bot)
            embed = discord.Embed(colour=generic.random_colour())
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.add_field(name="Server name", value=ctx.guild.name, inline=True)
            embed.add_field(name="Server ID", value=ctx.guild.id, inline=True)
            embed.add_field(name="Owner", inline=True,
                            value=f"{ctx.guild.owner}\n({ctx.guild.owner.display_name})")
            embed.add_field(name="Members", value=ctx.guild.member_count, inline=True)
            embed.add_field(name="Bots", value=str(bots), inline=True)
            embed.add_field(name="Region", value=ctx.guild.region, inline=True)
            embed.add_field(name="Roles", value=str(len(ctx.guild.roles)), inline=True)
            try:
                embed.add_field(name="Bans", value=str(len(await ctx.guild.bans())), inline=True)
            except discord.Forbidden:
                embed.add_field(name="Bans", value="Unknown - Access Denied", inline=True)
            embed.add_field(name="Channels", inline=True,
                            value=f"{len(ctx.guild.text_channels)} text channels\n"
                                  f"{len(ctx.guild.categories)} categories\n"
                                  f"{len(ctx.guild.voice_channels)} voice channels")
            embed.add_field(name="Created at", inline=False,
                            value=f"{time.time_output(ctx.guild.created_at)} - "
                                  f"{time.human_timedelta(ctx.guild.created_at)}")
            return await ctx.send(f"About **{ctx.guild.name}**", embed=embed)

    @server.command(name="icon", aliases=["avatar"])
    async def server_icon(self, ctx):
        """ Get server icon """
        return await ctx.send(f"Icon of **{ctx.guild.name}**:\n{ctx.guild.icon_url_as(size=1024)}")

    @server.command(name="bots")
    async def server_bots(self, ctx):
        """ Bots in servers """
        bots = [a for a in ctx.guild.members if a.bot]
        m = ''
        for i in range(len(bots)):
            n = str(i+1) if i >= 9 else f"0{i+1}"
            m += f"[{n}] {bots[i]}\n"
        return await ctx.send(f"Bots in **{ctx.guild.name}**: ```ini\n{m}```")

    @server.command(name="status")
    async def server_status(self, ctx):
        """ Server status """
        so, si, sd, sn = 0, 0, 0, 0
        mo, mi, md, do, di, dd, wo, wi, wd = 0, 0, 0, 0, 0, 0, 0, 0, 0
        al, ag, at, ac, an = 0, 0, 0, 0, 0
        m = 0
        for member in ctx.guild.members:
            m += 1
            s, s1, s2, s3 = member.status, member.mobile_status, member.desktop_status, member.web_status
            if s == discord.Status.online:
                so += 1
            if s1 == discord.Status.online:
                mo += 1
            if s2 == discord.Status.online:
                do += 1
            if s3 == discord.Status.online:
                wo += 1
            if s == discord.Status.idle:
                si += 1
            if s1 == discord.Status.idle:
                mi += 1
            if s2 == discord.Status.idle:
                di += 1
            if s3 == discord.Status.idle:
                wi += 1
            if s == discord.Status.dnd:
                sd += 1
            if s1 == discord.Status.dnd:
                md += 1
            if s2 == discord.Status.dnd:
                dd += 1
            if s3 == discord.Status.dnd:
                wd += 1
            if s == discord.Status.offline:
                sn += 1
            else:
                activities = list(member.activities)
                if not activities:
                    an += 1
                else:
                    for a in activities:
                        if a.type == discord.ActivityType.custom:
                            ac += 1
                        if a.type == discord.ActivityType.streaming:
                            at += 1
                        if a.type == discord.ActivityType.playing:
                            ag += 1
                        if a.type == discord.ActivityType.listening:
                            al += 1
        embed = discord.Embed(colour=random_colour(), description=f"Status of users in {ctx.guild.name}")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(name="Total members", value=f"{m:,}", inline=False)
        e1, e2, e3, e4 = "<:online:679052892514287635>", "<:idle:679052892828598303>", "<:dnd:679052892782723114> ", \
                         "<:offline:679052892782592033>"
        a1, a2, a3, a4, a5 = "🎮", "<:streaming:679055367346323478>", "<:listening:679055367396917250> ", \
                             "<:pikathink:674330001151229963>", "<:awoogoodnight:613410343359873054>"
        po, pi, pd, pn = so / m * 100, si / m * 100, sd / m * 100, sn / m * 100
        embed.add_field(name="Status", inline=False, value=f"{e1} Online: {so:,} - {po:.2f}%, of which:\n"
                                                           f"Mobile: {mo:,}\nDesktop: {do:,}\nWeb: {wo:,}\n\n"
                                                           f"{e2} Idle: {si:,} - {pi:.2f}%, of which:\n"
                                                           f"Mobile: {mi:,}\nDesktop: {di:,}\nWeb: {wi:,}\n\n"
                                                           f"{e3} Dungeons and Dragons: {sd:,} - {pd:.2f}%, of which:\n"
                                                           f"Mobile: {md:,}\nDesktop: {dd:,}\nWeb: {wd:,}\n\n"
                                                           f"{e4} Offline: {sn:,} - {pn:.2f}%")
        o = m - sn
        apg, apt, apl, apc, apn = ag / o * 100, at / o * 100, al / o * 100, ac / o * 100, an / o * 100
        embed.add_field(name="Activities", inline=False, value=f"Out of {o:,} people online:\n"
                                                               f"{a1} Playing a game: {ag:,} - {apg:.2f}%\n"
                                                               f"{a4} Playing Custom Status: {ac:,} - {apc:.2f}%\n"
                                                               f"{a2} Streaming: {at:,} - {apt:.2f}%\n"
                                                               f"{a3} Listening: {al:,} - {apl:.2f}%\n"
                                                               f"{a5} Doing nothing: {an:,} - {apn:.2f}%")
        return await ctx.send(embed=embed)

    @commands.command(name="prefix")
    @commands.guild_only()
    async def prefix(self, ctx):
        """ Server prefixes """
        _data = self.db.fetchrow("SELECT * FROM data WHERE type=? AND id=?", ("settings", ctx.guild.id))
        if not _data:
            dp = generic.get_config().prefix
            cp = None
        else:
            data = json.loads(_data['data'])
            dp = generic.get_config().prefix if data['use_default'] else []
            cp = data['prefixes']
            dp.append(self.bot.user.mention)
        embed = discord.Embed(colour=random_colour())
        embed.add_field(name="Default Prefixes", value='\n'.join(dp), inline=True)
        if cp is not None and cp != []:
            embed.add_field(name="Custom Prefixes", value='\n'.join(cp), inline=True)
        return await ctx.send(f"Prefixes for {ctx.guild.name}", embed=embed)

    @commands.group(name="settings")
    @commands.guild_only()
    @permissions.has_permissions(manage_server=True)
    async def settings(self, ctx):
        """ Server settings """
        if ctx.invoked_subcommand is None:
            data = self.db.fetchrow("SELECT * FROM data WHERE type=? AND id=?", ("settings", ctx.guild.id))
            if data:
                send = BytesIO(data['data'])
                return await ctx.send(f"Current settings for {ctx.guild.name}\n"
                                      f"Use {ctx.prefix}settings template for the template.",
                                      file=discord.File(send, filename=time.file_ts("Settings", "json")))
            else:
                send = BytesIO(json.dumps(settings_template.copy(), indent=4).encode('utf-8'))
                return await ctx.send(f"Here's the settings template for you.\nUpload with {ctx.prefix}settings upload",
                                      file=discord.File(send, filename=time.file_ts("SettingsTemplate", "json")))

    @settings.command(name="template")
    async def settings_template(self, ctx):
        """ Settings template """
        send = BytesIO(json.dumps(settings_template.copy(), indent=4).encode('utf-8'))
        return await ctx.send(f"Here's the settings template for you.\nUpload with {ctx.prefix}settings upload\n"
                              f"For leveling, [USER] will show user's name, and [MENTION] will @mention them",
                              file=discord.File(send, filename=time.file_ts("SettingsTemplate", "json")))

    @settings.command(name="upload")
    async def settings_upload(self, ctx):
        """ Upload new server settings """
        ma = ctx.message.attachments
        if len(ma) == 1:
            name = ma[0].filename
            if not name.endswith('json'):
                return await ctx.send("This must be a JSON file")
            try:
                stuff = await ma[0].read()
            except discord.HTTPException or discord.NotFound:
                return await ctx.send("There was an error getting the file.")
        else:
            return await ctx.send("There must be exactly one JSON file.")
        try:
            json.loads(stuff)
        except Exception as e:
            return await ctx.send(f"Error loading file:\n{type(e).__name__}: {e}")
        data = self.db.fetchrow("SELECT * FROM data WHERE type=? AND id=?", ("settings", ctx.guild.id))
        if data:
            res = self.db.execute("UPDATE data SET data=? WHERE type=? AND id=?", (stuff, "settings", ctx.guild.id))
        else:
            res = self.db.execute("INSERT INTO data VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (ctx.guild.id, "settings", stuff, False, None, None, None))
        return await ctx.send(f"Settings have been updated\n{res}")

    @commands.command(name="emojis")
    @commands.is_owner()
    async def get_all_emotes(self, ctx):
        """ Yoink all emotes """
        channel = self.bot.get_channel(676154789159239740)
        await channel.send(f"This stash of emotes was made on {time.time()}")
        for guild in self.bot.guilds:
            emotes = sorted([e for e in guild.emojis if len(e.roles) == 0 and e.available], key=lambda e: e.name)
            paginator = commands.Paginator(suffix='', prefix='')
            for emote in emotes:
                paginator.add_line(f'{emote.name} = "`{emote}`"')
            await channel.send(f"Next lot -> {guild.name}\n\n\n")
            for page in paginator.pages:
                await channel.send(page)
        return await ctx.send(f"Done yoinking emotes, {ctx.author.mention}, you may fuck off now.")

    @commands.command(name="avatar")
    async def avatar(self, ctx, *, who: discord.User = None):
        """ Get someone's avatar """
        user = who or ctx.author
        return await ctx.send(f"Avatar to **{user.name}**\n{user.avatar_url_as(size=1024)}")

    @commands.command(name="roles")
    @commands.guild_only()
    async def roles(self, ctx):
        """ Get all roles in current server """
        all_roles = ""
        for num, role in enumerate(sorted(ctx.guild.roles, reverse=True), start=1):
            all_roles += f"[{str(num).zfill(2)}] {role.id}\t{role.name}\t[ Users: {len(role.members)} ]\r\n"
        data = BytesIO(all_roles.encode('utf-8'))
        return await ctx.send(content=f"Roles in **{ctx.guild.name}**",
                              file=discord.File(data, filename=f"{time.file_ts('Roles')}"))

    @commands.command(name="joinedat")
    async def joined_at(self, ctx, *, who: discord.Member = None):
        """ Check when someone joined server """
        user = who or ctx.author
        return await ctx.send(f"**{user}** joined **{ctx.guild.name}** on {time.time_output(user.joined_at)}")

    @commands.command(name="user")
    @commands.guild_only()
    async def user(self, ctx, *, who: discord.Member = None):
        """ Get info about user """
        user = who or ctx.author
        embed = discord.Embed(colour=generic.random_colour())
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name="Username", value=user, inline=True)
        embed.add_field(name="Nickname", value=user.nick, inline=True)
        embed.add_field(name="User ID", value=user.id, inline=True)
        embed.add_field(name="Created at", value=time.time_output(user.created_at), inline=True)
        embed.add_field(name="Joined at", value=time.time_output(user.joined_at), inline=True)
        embed.add_field(name="Current status", value=str(user.status), inline=True)
        try:
            a = list(user.activities)
            if not a:
                embed.add_field(name="Current activity", value="None", inline=False)
            else:
                b = a[0]
                if b.type == discord.ActivityType.custom:
                    e = f"{b.emoji} " if b.emoji is not None else ''
                    n = b.name if b.name is not None else ''
                    embed.add_field(name="Current activity", value=f"Custom Status:\n{e}{n}", inline=False)
                elif b.type == discord.ActivityType.streaming:
                    c = b.platform
                    d = b.name if b.name else ''
                    e = f" {b.game} " if b.game else ''
                    embed.add_field(name="Current activity", value=f"Streaming {e} on {c}\n{d}", inline=False)
                elif b.type == discord.ActivityType.playing:
                    embed.add_field(name="Current activity", value=f"Playing {b.name}", inline=False)
                elif b.type == discord.ActivityType.listening:
                    embed.add_field(name="Current activity", inline=False,
                                    value=f"Listening to {b.name}\n{b.title} by {', '.join(b.artists)} - {b.album}")
            # embed.add_field(name="Activity", value=who.activity)
        except AttributeError:
            embed.add_field(name="Current activity", value="None", inline=False)
        if len(user.roles) < 15:
            r = user.roles
            r.sort(key=lambda x: x.position, reverse=True)
            # roles = ', '.join([f"<@&{x.id}>" for x in user.roles if x is not ctx.guild.default_role]) \
            #     if len(user.roles) > 1 else 'None' + f"\n({len(user.roles)} roles overall)"
            ar = [f"<@&{x.id}>" for x in r if x.id != ctx.guild.default_role.id]
            roles = ', '.join(ar) if ar else 'None'
            b = len(user.roles) - 1
            roles += f"\n({b} role{'s' if b != 1 else ''} overall)"
        else:
            roles = f"There's {len(user.roles) - 1} of them"
        embed.add_field(name="Roles", value=roles, inline=False)
        await ctx.send(f"ℹ About **{user}**", embed=embed)

    @commands.command(name="emoji", aliases=["emote"])
    @commands.cooldown(rate=3, per=5, type=commands.BucketType.user)
    async def emoji(self, ctx, emoji: discord.Emoji):
        """ View bigger version of a Custom Emoji """
        return await ctx.send(f"Blame {ctx.author.name} for this", embed=discord.Embed(
            description=f"Name: {emoji.name}\nAnimated: {emoji.animated}\nServer: {emoji.guild.name}\n"
                        f"Created: {time.time_output(emoji.created_at)}\n[Copy Link]({emoji.url})",
            colour=generic.random_colour()).set_image(url=emoji.url).set_author(
            name=ctx.author, icon_url=ctx.author.avatar_url).set_footer(text="Or you could've used discord for PC"))


def setup(bot):
    bot.add_cog(Discord(bot))
