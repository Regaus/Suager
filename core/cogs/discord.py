from io import BytesIO

import discord
from discord.ext import commands

from core.utils import arg_parser, database, general, time
from languages import langs


def is_senko_lair(ctx):
    return ctx.guild.id == 568148147457490954


def get_attr(cls, attr):
    return getattr(cls, attr) if hasattr(cls, attr) else "undefined"


class Discord(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database(self.bot.name)

    @commands.command(name="avatar")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def avatar(self, ctx: commands.Context, *, who: discord.User = None):
        """ Get someone's avatar """
        user = who or ctx.author
        return await general.send(langs.gls("discord_avatar", langs.gl(ctx.guild, self.db), user.name, user.avatar_url_as(size=1024, static_format='png')),
                                  ctx.channel)

    @commands.command(name="avatar2")
    @commands.is_owner()
    async def avatar_fetch(self, ctx: commands.Context, *who: int):
        """ Fetch and yoink avatars """
        for user in who:
            try:
                await general.send((await self.bot.fetch_user(user)).avatar_url_as(size=1024, static_format="png"), ctx.channel)
            except Exception as e:
                await general.send(f"{user} -> {type(e).__name__}: {e}", ctx.channel)

    @commands.group(name="role")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def role(self, ctx: commands.Context, *, role: discord.Role = None):
        """ Information on roles in the current server """
        if ctx.invoked_subcommand is None:
            locale = langs.gl(ctx.guild, self.db)
            if role is None:
                all_roles = ""
                for num, role in enumerate(sorted(ctx.guild.roles, reverse=True), start=1):
                    all_roles += langs.gls("discord_role_list_item", locale, langs.gns(num, locale, 2, False), langs.gns(len(role.members)), role=role)
                    # all_roles += f"[{num:02d}] {role.id}\t{role.name}\t[Users: {len(role.members)}]\r\n"
                data = BytesIO(all_roles.encode('utf-8'))
                return await general.send(langs.gls("discord_role_list", locale, ctx.guild.name), ctx.channel,
                                          file=discord.File(data, filename=f"{time.file_ts('Roles')}"))
            else:
                embed = discord.Embed(colour=role.colour)
                embed.title = langs.gls("discord_role_about", locale, role.name)
                # embed.title = f"ℹ About role {role.name}"
                embed.set_thumbnail(url=ctx.guild.icon_url)
                embed.add_field(name=langs.gls("discord_role_name", locale), value=role.name, inline=True)
                embed.add_field(name=langs.gls("discord_role_id", locale), value=str(role.id), inline=True)
                embed.add_field(name=langs.gls("generic_members", locale), value=f"{len(role.members):,}", inline=True)
                embed.add_field(name=langs.gls("discord_role_colour", locale), value=str(role.colour), inline=True)
                embed.add_field(name=langs.gls("discord_role_mentionable", locale), value=langs.yes(role.mentionable, locale), inline=True)
                embed.add_field(name=langs.gls("discord_role_hoisted", locale), value=langs.yes(role.hoist, locale), inline=True)
                embed.add_field(name=langs.gls("discord_role_position", locale), value=langs.gns(role.position, locale), inline=True)
                embed.add_field(name=langs.gls("generic_created_at", locale), value=langs.gts(role.created_at, locale, short=False), inline=True)
                embed.add_field(name=langs.gls("discord_role_default", locale), value=langs.yes(role.is_default(), locale), inline=True)
                return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="joinedat")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def joined_at(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Check when someone joined server """
        user = who or ctx.author
        locale = langs.gl(ctx.guild, self.db)
        return await general.send(langs.gls("discord_joined_at", locale, user, ctx.guild.name, langs.gts(user.joined_at, locale, short=False)), ctx.channel)
        # return await general.send(f"**{user.name}** joined **{ctx.guild.name}** at **{time.time_output(user.joined_at)}**", ctx.channel)

    @commands.command(name="createdat")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def created_at(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check when someone created their account """
        user = who or ctx.author
        locale = langs.gl(ctx.guild, self.db)
        return await general.send(langs.gls("discord_created_at", locale, user, langs.gts(user.joined_at, locale, short=False)), ctx.channel)

    @commands.command(name="user")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def user(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Get info about user """
        user = who or ctx.author
        locale = langs.gl(ctx.guild, self.db)
        embed = discord.Embed(colour=general.random_colour())
        embed.title = langs.gls("discord_user_about", locale, user.name)
        # embed.title = f"ℹ About user {user.name}"
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name=langs.gls("discord_user_username", locale), value=user, inline=True)
        embed.add_field(name=langs.gls("discord_user_nickname", locale), value=user.nick, inline=True)
        embed.add_field(name=langs.gls("discord_user_id", locale), value=user.id, inline=True)
        embed.add_field(name=langs.gls("generic_created_at", locale), value=langs.gts(user.created_at, locale, short=False), inline=True)
        embed.add_field(name=langs.gls("discord_user_joined_at", locale), value=langs.gts(user.joined_at, locale, short=False), inline=True)
        embed.add_field(name=langs.gls("discord_user_status", locale), value=langs.gls(f"discord_status_{user.status}", locale), inline=True)
        try:
            # a = list(user.activities)
            b = user.activity
            # if not a:
            if b is None:
                embed.add_field(name=langs.gls("discord_user_activity", locale), value=langs.gls("generic_none", locale), inline=False)
            else:
                # b = a[0]
                if b.type == discord.ActivityType.custom:
                    e = f"{b.emoji} " if b.emoji is not None else ''
                    n = b.name if b.name is not None else ''
                    embed.add_field(name=langs.gls("discord_user_activity", locale), value=langs.gls("discord_user_custom_status", locale, e, n), inline=False)
                elif b.type == discord.ActivityType.streaming:
                    # c = b.platform
                    c = get_attr(b, "platform")
                    d = b.name if b.name else ''
                    # e = f" {b.game} " if b.game else ''
                    e = f" {e} " if (e := get_attr(b, "game")) else ""
                    embed.add_field(name=langs.gls("discord_user_activity", locale), value=langs.gls("discord_user_streaming", locale, c, d, e), inline=False)
                elif b.type == discord.ActivityType.playing:
                    embed.add_field(name=langs.gls("discord_user_activity", locale), value=langs.gls("discord_user_playing", locale, b.name), inline=False)
                elif b.type == discord.ActivityType.listening:
                    c = b.name
                    # d = b.title
                    # e = ", ".join(b.artists)
                    # f = b.album
                    d = get_attr(b, "title")
                    e = ", ".join(e) if (e := get_attr(b, "artists")) else e
                    f = get_attr(b, "album")
                    embed.add_field(name=langs.gls("discord_user_activity", locale), inline=False,
                                    value=langs.gls("discord_user_listening", locale, c, d, e, f))
                elif b.type == discord.ActivityType.watching:
                    embed.add_field(name=langs.gls("discord_user_activity", locale), value=langs.gls("discord_user_watching", locale, b.name), inline=False)
        except AttributeError:
            embed.add_field(name=langs.gls("discord_user_activity", locale), value=langs.gls("generic_unknown", locale), inline=False)
        if len(user.roles) < 15:
            r = user.roles
            r.sort(key=lambda x: x.position, reverse=True)
            ar = [f"<@&{x.id}>" for x in r if x.id != ctx.guild.default_role.id]
            roles = ', '.join(ar) if ar else langs.gls("generic_none", locale)
            b = len(user.roles) - 1
            roles += langs.gls("discord_user_roles_overall", locale, langs.gns(b, locale))
            # roles += f"\n({b} overall)"
        else:
            roles = langs.gls("discord_user_roles_many", locale, langs.gns(len(user.roles) - 1))
            # roles = f"There's {len(user.roles) - 1} of them"
        embed.add_field(name=langs.gls("discord_user_roles", locale), value=roles, inline=False)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="whois")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def who_is(self, ctx: commands.Context, *, user_id: int):
        """ Get info about a user """
        locale = langs.gl(ctx.guild, self.db)
        try:
            user = await self.bot.fetch_user(user_id)
        except discord.NotFound as e:
            return await general.send(langs.gls("events_err_error", locale, "NotFound", str(e)), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        embed.title = langs.gls("discord_user_about", locale, user.name)
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name=langs.gls("discord_user_username", locale), value=user, inline=True)
        embed.add_field(name=langs.gls("discord_user_id", locale), value=user.id, inline=True)
        embed.add_field(name=langs.gls("generic_created_at", locale), value=langs.gts(user.created_at, locale, short=False), inline=True)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="emoji", aliases=["emote"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def emoji(self, ctx: commands.Context, emoji: discord.Emoji):
        """ Information on an emoji """
        locale = langs.gl(ctx.guild, self.db)
        e = str(ctx.invoked_with)
        c = langs.gls(f"discord_emoji_{e}", locale)
        embed = discord.Embed(colour=general.random_colour())
        embed.description = langs.gls("discord_emoji", locale, c, emoji.name, emoji.id, langs.yes(emoji.animated, locale), emoji.guild.id,
                                      langs.gts(emoji.created_at, locale, short=False), emoji.url)
        # embed.description = f"{c} name: {emoji.name}\n{c} ID: {emoji.id}\nAnimated: {emoji.animated}\nServer: {emoji.guild.id}\n" \
        #                     f"Created at: {time.time_output(emoji.created_at, tz=True)}\n[Emoji URL]({emoji.url})"
        embed.set_image(url=emoji.url)
        return await general.send(f"{ctx.author.name}:", ctx.channel, embed=embed)

    @commands.group(name="server", aliases=["guild"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def server(self, ctx: commands.Context):
        """ Information about the current server """
        if ctx.invoked_subcommand is None:
            locale = langs.gl(ctx.guild, self.db)
            bots = sum(1 for member in ctx.guild.members if member.bot)
            bots_amt = bots / ctx.guild.member_count
            embed = discord.Embed(colour=general.random_colour())
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.title = langs.gls("discord_server_about", locale, ctx.guild.name)
            # embed.title = f"ℹ About server {ctx.guild.name}"
            embed.add_field(name=langs.gls("discord_server_name", locale), value=ctx.guild.name, inline=True)
            embed.add_field(name=langs.gls("discord_server_id", locale), value=ctx.guild.id, inline=True)
            embed.add_field(name=langs.gls("discord_server_owner", locale), inline=True, value=f"{ctx.guild.owner}\n({ctx.guild.owner.display_name})")
            embed.add_field(name=langs.gls("generic_members", locale), value=langs.gns(ctx.guild.member_count, locale), inline=True)
            embed.add_field(name=langs.gls("discord_server_bots", locale), inline=True,
                            value=f"{langs.gns(bots, locale)} ({langs.gfs(bots_amt, locale, per=True)})")
            embed.add_field(name=langs.gls("discord_server_region", locale), value=ctx.guild.region, inline=True)
            embed.add_field(name=langs.gls("discord_server_roles", locale), value=langs.gns(len(ctx.guild.roles), locale), inline=True)
            try:
                embed.add_field(name=langs.gls("discord_server_bans", locale), value=langs.gns(len(await ctx.guild.bans()), locale), inline=True)
            except discord.Forbidden:
                embed.add_field(name=langs.gls("discord_server_bans", locale), value=langs.gls("discord_server_bans_denied", locale), inline=True)
            embed.add_field(name=langs.gls("discord_server_verification", locale), inline=True, value=str(ctx.guild.verification_level).capitalize())
            t, c, v = len(ctx.guild.text_channels), len(ctx.guild.categories), len(ctx.guild.voice_channels)
            tc, cc, vc = langs.gns(t, locale), langs.gns(c, locale), langs.gns(v, locale)
            embed.add_field(name=langs.gls("discord_server_channels", locale), value=langs.gls("discord_server_channels_data", locale, tc, cc, vc), inline=True)
            # embed.add_field(name="Channels", inline=True, value=f"Text channels: {len(ctx.guild.text_channels)}\nCategories: {len(ctx.guild.categories)}\n"
            #                                                     f"Voice channels:{len(ctx.guild.voice_channels)}")
            b, bl, bc = langs.gns(ctx.guild.premium_subscription_count, locale), langs.gns(ctx.guild.premium_tier, locale), \
                langs.gns(len(ctx.guild.premium_subscribers), locale)
            embed.add_field(name=langs.gls("discord_server_boosts", locale), value=langs.gls("discord_server_boosts_data", locale, b, bl, bc), inline=True)
            # embed.add_field(name="Boosts", inline=True, value=f"Boosts: {ctx.guild.premium_subscription_count} - Level {ctx.guild.premium_tier}\n"
            #                                                   f"Boosters: {len(ctx.guild.premium_subscribers)}")
            ani = len([emote for emote in ctx.guild.emojis if emote.animated])
            total_emotes = len(ctx.guild.emojis)
            el = ctx.guild.emoji_limit
            na = total_emotes - ani
            n, a, e, t = langs.gns(na, locale), langs.gns(ani, locale), langs.gns(el, locale), langs.gns(total_emotes, locale)
            embed.add_field(name=langs.gls("discord_server_emotes", locale), value=langs.gls("discord_server_emotes_data", locale, n, a, e, t), inline=True)
            # embed.add_field(name="Emotes", inline=True, value=f"{na}/{el} Non-animated\n{ani}/{el} Animated\n{total_emotes} Total")
            ca = ctx.guild.created_at
            ct, cd = langs.gts(ca, locale, short=False), langs.td_dt(ca, locale, suffix=True)
            embed.add_field(name=langs.gls("generic_created_at", locale), value=f"{ct}\n{cd}", inline=False)
            return await general.send(None, ctx.channel, embed=embed)

    @server.command(name="icon", aliases=["avatar"])
    async def server_icon(self, ctx: commands.Context):
        """ Get server icon """
        return await general.send(langs.gls("discord_server_icon", langs.gl(ctx.guild, self.db), ctx.guild.name,
                                            ctx.guild.icon_url_as(size=1024, static_format='png')), ctx.channel)

    @server.command(name="banner")
    async def server_banner(self, ctx: commands.Context):
        """ Get server banner """
        link = ctx.guild.banner_url_as(size=4096, format="png")
        locale = langs.gl(ctx.guild, self.db)
        if link:
            return await general.send(langs.gls("discord_server_banner", locale, ctx.guild.name, link), ctx.channel)
        else:
            return await general.send(langs.gls("discord_server_banner_none", locale, ctx.guild.name), ctx.channel)

    @server.command(name="invite", aliases=["splash"])
    async def server_invite(self, ctx: commands.Context):
        """ Get server invite splash """
        link = ctx.guild.splash_url_as(size=4096, format="png")
        locale = langs.gl(ctx.guild, self.db)
        if link:
            return await general.send(langs.gls("discord_server_inv_bg", locale, ctx.guild.name, link), ctx.channel)
        else:
            return await general.send(langs.gls("discord_server_inv_bg_none", locale, ctx.guild.name), ctx.channel)

    @server.command(name="bots")
    async def server_bots(self, ctx: commands.Context):
        """ Bots in the server """
        bots = [a for a in ctx.guild.members if a.bot]
        locale = langs.gl(ctx.guild, self.db)
        m = ''
        for i in range(len(bots)):
            m += f"[{langs.gns(i + 1, locale, 2, False)}] {bots[i]}\n"
        rl = len(m)
        send = langs.gls("discord_server_bots_data", locale, ctx.guild.name)
        if rl > 1900:
            async with ctx.typing():
                data = BytesIO(str(m).encode('utf-8'))
                return await general.send(send, ctx.channel, file=discord.File(data, filename=f"{time.file_ts('Bots')}"))
        return await general.send(f"{send}\n```fix\n{m}```", ctx.channel)

    @server.command(name="status")
    async def server_status(self, ctx: commands.Context):
        """ Server members' status """
        locale = langs.gl(ctx.guild, self.db)
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
        embed = discord.Embed(colour=general.random_colour(), title=langs.gls("discord_server_status", locale, ctx.guild.name))
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(name=langs.gls("discord_server_status_members", locale), value=f"{m:,}", inline=False)
        e1, e2, e3, e4 = "<:online:679052892514287635>", "<:idle:679052892828598303>", "<:dnd:679052892782723114> ", \
                         "<:offline:679052892782592033>"
        a1, a2, a3, a4, a5 = "🎮", "<:streaming:679055367346323478>", "<:listening:679055367396917250> ", \
                             "<:pikathink:674330001151229963>", "<:GoodNight:713168586512007189>"
        lo, li, ld, ln = langs.gns(so, locale), langs.gns(si, locale), langs.gns(sd, locale), langs.gns(sn, locale)
        lom, lod, low, lim, lid, liw, ldm, ldd, ldw = langs.gns(mo, locale), langs.gns(do, locale), langs.gns(wo, locale), langs.gns(mi, locale), \
            langs.gns(di, locale), langs.gns(wi, locale), langs.gns(md, locale), langs.gns(dd, locale), langs.gns(wd, locale)
        po, pi, pd, pn = langs.gfs(so / m, locale, 2, True), langs.gfs(si / m, locale, 2, True), langs.gfs(sd / m, locale, 2, True), \
            langs.gfs(sn / m, locale, 2, True)
        o = m - sn
        os = langs.gns(o, locale)
        lag, lac, lat, lal, lan = langs.gns(ag, locale), langs.gns(ac, locale), langs.gns(at, locale), langs.gns(al, locale), langs.gns(an, locale)
        apg, apt, apl, apc, apn = langs.gfs(ag / m, locale, 2, True), langs.gfs(at / m, locale, 2, True), langs.gfs(al / m, locale, 2, True), \
            langs.gfs(ac / m, locale, 2, True), langs.gfs(an / m, locale, 2, True)
        embed.add_field(name=langs.gls("discord_server_status_status", locale), inline=False,
                        value=langs.gls("discord_server_status_status_data", locale, e1, lo, po, lom, lod, low, e2, li, pi, lim, lid, liw, e3, ld, pd, ldm,
                                        ldd, ldw, e4, ln, pn))
        #                 value=f"{e1} Online: {so:,} - {po:.2f}%, of which:\nMobile: {mo:,} | Desktop: {do:,} | Web: {wo:,}\n\n{e2} Idle: {si:,} - {pi:.2f}%, "
        #                       f"of which:\nMobile: {mi:,} | Desktop: {di:,} | Web: {wi:,}\n\n{e3} Dungeons and Dragons: {sd:,} - {pd:.2f}%, of which:\n"
        #                       f"Mobile: {md:,} | Desktop: {dd:,} | Web: {wd:,}\n\n{e4} Offline: {sn:,} - {pn:.2f}%")
        embed.add_field(name=langs.gls("discord_server_status_activity", locale), inline=False,
                        value=langs.gls("discord_server_status_activity_data", locale, os, a1, lag, apg, a4, lac, apc, a2, at, apt, a3, al, apl, a5, an, apn))
        #                 value=f"Out of {o:,} people online:\n{a1} Playing a game: {ag:,} - {apg:.2f}%\n{a4} Custom Status: {ac:,} - {apc:.2f}%\n{a2} "
        #                       f"Streaming: {at:,} - {apt:.2f}%\n{a3} Listening: {al:,} - {apl:.2f}%\n{a5} Doing nothing: {an:,} - {apn:.2f}%")
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="customrole", aliases=["cr"])
    @commands.guild_only()
    @commands.check(is_senko_lair)
    @commands.cooldown(rate=1, per=30, type=commands.BucketType.user)
    async def custom_role(self, ctx: commands.Context, *, stuff: str):
        """ Custom Role (only in Senko Lair)
        -c/--colour/--color: Set role colour
        -n/--name: Set role name """
        data = self.db.fetchrow("SELECT * FROM custom_role WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not data:
            return await general.send(f"Doesn't seem like you have a custom role in this server, {ctx.author.name}", ctx.channel)
        parser = arg_parser.Arguments()
        parser.add_argument('-c', '--colour', '--color', nargs=1)
        parser.add_argument('-n', '--name', nargs="+")
        args, valid_check = parser.parse_args(stuff)
        if not valid_check:
            return await general.send(args, ctx.channel)
        role = ctx.guild.get_role(data['rid'])
        if args.colour is not None:
            c = args.colour[0]
            a = len(c)
            if c == "random":
                col = general.random_colour()
            else:
                if a == 6 or a == 3:
                    try:
                        col = int(c, base=16)
                    except Exception as e:
                        return await general.send(f"Invalid colour - {type(e).__name__}: {e}", ctx.channel)
                else:
                    return await general.send("Colour must be either 3 or 6 HEX digits long.", ctx.channel)
            colour = discord.Colour(col)
        else:
            colour = role.colour
        try:
            name = ' '.join(args.name)
        except TypeError:
            name = role.name
        try:
            await role.edit(name=name, colour=colour, reason="Custom Role change")
        except Exception as e:
            return await general.send(f"An error occurred while updating custom role: {type(e).__name__}: {e}", ctx.channel)
        return await general.send(f"Successfully updated your custom role, {ctx.author.name}", ctx.channel)

    @commands.command(name="grantrole")
    @commands.guild_only()
    @commands.is_owner()
    async def grant_custom_role(self, ctx: commands.Context, user: discord.Member, role: discord.Role):
        """ Grant custom role """
        already = self.db.fetchrow("SELECT * FROM custom_role WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not already:
            result = self.db.execute("INSERT INTO custom_role VALUES (?, ?, ?)", (user.id, role.id, ctx.guild.id))
            await user.add_roles(role, reason="Custom Role grant")
            return await general.send(f"Granted {role.name} to {user.name}: {result}", ctx.channel)
        else:
            result = self.db.execute("UPDATE custom_role SET rid=? WHERE uid=? AND gid=?", (role.id, user.id, ctx.guild.id))
            return await general.send(f"Updated custom role of {user.name} to {role.name}: {result}", ctx.channel)


def setup(bot):
    bot.add_cog(Discord(bot))
