from io import BytesIO

import discord
from discord.ext import commands

from core.utils import general, time


class Discord(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="avatar")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def avatar(self, ctx: commands.Context, *, who: discord.User = None):
        """ Get someone's avatar """
        user = who or ctx.author
        return await general.send(f"ℹ Avatar for **{user.name}**\n{user.avatar_url_as(size=1024, static_format='png')}", ctx.channel)

    @commands.group(name="role")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def role(self, ctx: commands.Context, *, role: discord.Role = None):
        """ Information on roles in the current server """
        if ctx.invoked_subcommand is None:
            if role is None:
                all_roles = ""
                for num, role in enumerate(sorted(ctx.guild.roles, reverse=True), start=1):
                    all_roles += f"[{num:02d}] {role.id}\t{role.name}\t[Users: {len(role.members)}]\r\n"
                data = BytesIO(all_roles.encode('utf-8'))
                return await general.send(f"ℹ Roles in **{ctx.guild.name}**", ctx.channel, file=discord.File(data, filename=f"{time.file_ts('Roles')}"))
            else:
                embed = discord.Embed(colour=role.colour)
                embed.title = f"ℹ About role {role.name}"
                embed.set_thumbnail(url=ctx.guild.icon_url)
                embed.add_field(name="Role Name", value=role.name, inline=True)
                embed.add_field(name="Role ID", value=str(role.id), inline=True)
                embed.add_field(name="Members", value=f"{len(role.members):,}", inline=True)
                embed.add_field(name="Role Colour", value=str(role.colour), inline=True)
                embed.add_field(name="Mentionable", value=role.mentionable, inline=True)
                embed.add_field(name="Hoisted", value=role.hoist, inline=True)
                embed.add_field(name="Role Position", value=role.position, inline=True)
                embed.add_field(name="Created at", value=time.time_output(role.created_at), inline=True)
                embed.add_field(name="Default Role", value=role.is_default(), inline=True)
                return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="joinedat")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def joined_at(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Check when someone joined server """
        user = who or ctx.author
        return await general.send(f"**{user.name}** joined **{ctx.guild.name}** at **{time.time_output(user.joined_at)}**", ctx.channel)

    @commands.command(name="createdat")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def created_at(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check when someone created their account """
        user = who or ctx.author
        return await general.send(f"**{user.name}** created their account at **{time.time_output(user.created_at)}**", ctx.channel)

    @commands.command(name="user")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def user(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Get info about user """
        user = who or ctx.author
        embed = discord.Embed(colour=general.random_colour())
        embed.title = f"ℹ About user {user.name}"
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
                    embed.add_field(name="Current activity", value=f"Streaming{e}on {c}\n{d}", inline=False)
                elif b.type == discord.ActivityType.playing:
                    embed.add_field(name="Current activity", value=f"Playing {b.name}", inline=False)
                elif b.type == discord.ActivityType.listening:
                    embed.add_field(name="Current activity", inline=False, value=f"Listening to {b.name}\n{b.title} by {', '.join(b.artists)} - {b.album}")
        except AttributeError:
            embed.add_field(name="Current activity", value="Unknown", inline=False)
        if len(user.roles) < 15:
            r = user.roles
            r.sort(key=lambda x: x.position, reverse=True)
            ar = [f"<@&{x.id}>" for x in r if x.id != ctx.guild.default_role.id]
            roles = ', '.join(ar) if ar else 'None'
            b = len(user.roles) - 1
            roles += f"\n({b} overall)"
        else:
            roles = f"There's {len(user.roles) - 1} of them"
        embed.add_field(name="Roles", value=roles, inline=False)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="emoji", aliases=["emote"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def emoji(self, ctx: commands.Context, emoji: discord.Emoji):
        """ Information on an emoji """
        e = str(ctx.invoked_with)
        c = e.capitalize()
        embed = discord.Embed(colour=general.random_colour())
        embed.description = f"{c} name: {emoji.name}\n{c} ID: {emoji.id}\nAnimated: {emoji.animated}\nServer: {emoji.guild.id}\n" \
                            f"Created at: {time.time_output(emoji.created_at, tz=True)}\n[Emoji URL]({emoji.url})"
        embed.set_image(url=emoji.url)
        return await general.send(f"{ctx.author.name}:", ctx.channel, embed=embed)

    @commands.group(name="server", aliases=["guild"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def server(self, ctx: commands.Context):
        """ Information about the current server """
        if ctx.invoked_subcommand is None:
            bots = sum(1 for member in ctx.guild.members if member.bot)
            bots_amt = bots / ctx.guild.member_count * 100
            embed = discord.Embed(colour=general.random_colour())
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.title = f"ℹ About server {ctx.guild.name}"
            embed.add_field(name="Server name", value=ctx.guild.name, inline=True)
            embed.add_field(name="Server ID", value=ctx.guild.id, inline=True)
            embed.add_field(name="Server Owner", inline=True, value=f"{ctx.guild.owner}\n({ctx.guild.owner.display_name})")
            embed.add_field(name="Member Count", value=f"{ctx.guild.member_count:,}", inline=True)
            embed.add_field(name="Bots Count", value=f"{bots:,} [{bots_amt:.2f}%]", inline=True)
            embed.add_field(name="Server Region", value=ctx.guild.region, inline=True)
            embed.add_field(name="Role Count", value=f"{len(ctx.guild.roles):,}", inline=True)
            try:
                embed.add_field(name="Ban Count", value=f"{len(await ctx.guild.bans()):,}", inline=True)
            except discord.Forbidden:
                embed.add_field(name="Ban Count", value="Access Denied", inline=True)
            embed.add_field(name="Verification Level", inline=True, value=str(ctx.guild.verification_level).capitalize())
            embed.add_field(name="Channels", inline=True, value=f"Text channels: {len(ctx.guild.text_channels)}\nCategories: {len(ctx.guild.categories)}\n"
                                                                f"Voice channels:{len(ctx.guild.voice_channels)}")
            embed.add_field(name="Boosts", inline=True, value=f"Boosts: {ctx.guild.premium_subscription_count} - Level {ctx.guild.premium_tier}\n"
                                                              f"Boosters: {len(ctx.guild.premium_subscribers)}")
            ani = len([emote for emote in ctx.guild.emojis if emote.animated])
            total_emotes = len(ctx.guild.emojis)
            el = ctx.guild.emoji_limit
            na = total_emotes - ani
            embed.add_field(name="Emotes", inline=True, value=f"{na}/{el} Non-animated\n{ani}/{el} Animated\n{total_emotes} Total")
            ca = ctx.guild.created_at
            embed.add_field(name="Created at", inline=False, value=f"{time.time_output(ca, tz=True)} - {time.human_timedelta(ca)}")
            return await general.send(None, ctx.channel, embed=embed)

    @server.command(name="icon", aliases=["avatar"])
    async def server_icon(self, ctx: commands.Context):
        """ Get server icon """
        return await general.send(f"ℹ Icon for **{ctx.guild.name}**\n{ctx.guild.icon_url_as(size=1024, static_format='png')}", ctx.channel)

    @server.command(name="banner")
    async def server_banner(self, ctx: commands.Context):
        """ Get server banner """
        link = ctx.guild.banner_url_as(size=4096, format="png")
        if link:
            return await general.send(f"ℹ Banner for **{ctx.guild.name}**\n{link}", ctx.channel)
        else:
            return await general.send(f"{ctx.guild.name} has no banner", ctx.channel)

    @server.command(name="invite", aliases=["splash"])
    async def server_invite(self, ctx: commands.Context):
        """ Get server invite splash """
        link = ctx.guild.splash_url_as(size=4096, format="png")
        if link:
            return await general.send(f"ℹ Invite background for **{ctx.guild.name}**\n{link}", ctx.channel)
        else:
            return await general.send(f"{ctx.guild.name} has no invite background", ctx.channel)

    @server.command(name="bots")
    async def server_bots(self, ctx: commands.Context):
        """ Bots in the server """
        bots = [a for a in ctx.guild.members if a.bot]
        m = ''
        for i in range(len(bots)):
            m += f"[{i + 1:02d}] {bots[i]}\n"
        rl = len(m)
        send = f"ℹ Bots in **{ctx.guild.name}**"
        if rl > 1900:
            async with ctx.typing():
                data = BytesIO(str(m).encode('utf-8'))
                return await general.send(send, ctx.channel, file=discord.File(data, filename=f"{time.file_ts('Bots')}"))
        return await general.send(f"{send}\n```fix\n{m}```", ctx.channel)

    @server.command(name="status")
    async def server_status(self, ctx: commands.Context):
        """ Server members' status """
        so, si, sd, sn = 0, 0, 0, 0
        mo, mi, md, do, di, dd, wo, wi, wd = 0, 0, 0, 0, 0, 0, 0, 0, 0
        al, ag, at, ac, an = 0, 0, 0, 0, 0
        m = 0
        for member in ctx.guild.members:
            m += 1
            s, s1, s2, s3 = member.status, member.mobile_status, member.desktop_status, member.web_status
            so += 1 if s == discord.Status.online else 0
            mo += 1 if s1 == discord.Status.online else 0
            do += 1 if s2 == discord.Status.online else 0
            wo += 1 if s3 == discord.Status.online else 0
            si += 1 if s == discord.Status.idle else 0
            mi += 1 if s1 == discord.Status.idle else 0
            di += 1 if s2 == discord.Status.idle else 0
            wi += 1 if s3 == discord.Status.idle else 0
            sd += 1 if s == discord.Status.dnd else 0
            md += 1 if s1 == discord.Status.dnd else 0
            dd += 1 if s2 == discord.Status.dnd else 0
            wd += 1 if s3 == discord.Status.dnd else 0
            if s == discord.Status.offline:
                sn += 1
            else:
                activities = list(member.activities)
                if not activities:
                    an += 1
                else:
                    for a in activities:
                        ac += 1 if a.type == discord.ActivityType.custom else 0
                        at += 1 if a.type == discord.ActivityType.streaming else 0
                        ag += 1 if a.type == discord.ActivityType.playing else 0
                        al += 1 if a.type == discord.ActivityType.listening else 0
        embed = discord.Embed(colour=general.random_colour(), title=f"Status of members for {ctx.guild.name}")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(name="Total member count", value=f"{m:,}", inline=False)
        e1, e2, e3, e4 = "<:online:679052892514287635>", "<:idle:679052892828598303>", "<:dnd:679052892782723114> ", \
                         "<:offline:679052892782592033>"
        a1, a2, a3, a4, a5 = "🎮", "<:streaming:679055367346323478>", "<:listening:679055367396917250> ", \
                             "<:pikathink:674330001151229963>", "<:GoodNight:713168586512007189>"
        po, pi, pd, pn = so / m * 100, si / m * 100, sd / m * 100, sn / m * 100
        embed.add_field(name="Status", inline=False, value=f"{e1} Online: {so:,} - {po:.2f}%, of which:\nMobile: {mo:,} | Desktop: {do:,} | Web: {wo:,}\n\n"
                                                           f"{e2} Idle: {si:,} - {pi:.2f}%, of which:\nMobile: {mi:,} | Desktop: {di:,} | Web: {wi:,}\n\n"
                                                           f"{e3} Dungeons and Dragons: {sd:,} - {pd:.2f}%, of which:\nMobile: {md:,} | Desktop: {dd:,} | "
                                                           f"Web: {wd:,}\n\n{e4} Offline: {sn:,} - {pn:.2f}%")
        o = m - sn
        apg, apt, apl, apc, apn = ag / o * 100, at / o * 100, al / o * 100, ac / o * 100, an / o * 100
        embed.add_field(name="Activity", inline=False, value=f"Out of {o:,} people online:\n{a1} Playing a game: {ag:,} - {apg:.2f}%\n"
                                                             f"{a4} Custom Status: {ac:,} - {apc:.2f}%\n{a2} Streaming: {at:,} - {apt:.2f}%\n"
                                                             f"{a3} Listening: {al:,} - {apl:.2f}%\n{a5} Doing nothing: {an:,} - {apn:.2f}%")
        return await general.send(None, ctx.channel, embed=embed)


def setup(bot):
    bot.add_cog(Discord(bot))
