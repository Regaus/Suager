import json
from io import BytesIO

import discord
from discord.ext import commands

from utils import database, permissions, generic, time, argparser, http
from utils.generic import settings_template


class Discord(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database()

    @commands.group(name="settings")
    @commands.guild_only()
    @permissions.has_permissions(manage_guild=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def settings(self, ctx: commands.Context):
        """ Server settings """
        if ctx.invoked_subcommand is None:
            data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
            if data:
                try:
                    send = BytesIO(data['data'].encode('utf-8'))
                except AttributeError:
                    send = BytesIO(data['data'])
                return await generic.send(
                    generic.gls(generic.get_lang(ctx.guild), "settings_current", [ctx.guild.name, ctx.prefix]),
                    ctx.channel, file=discord.File(send, filename=time.file_ts("Settings", "json")))
                # return await ctx.send(f"Current settings for {ctx.guild.name}\n"
                #                       f"Use {ctx.prefix}settings template for the template.",
                #                       file=discord.File(send, filename=time.file_ts("Settings", "json")))
            else:
                send = BytesIO(json.dumps(settings_template.copy(), indent=4).encode('utf-8'))
                return await generic.send(
                    generic.gls(generic.get_lang(ctx.guild), "settings_template", [ctx.prefix]), ctx.channel,
                    file=discord.File(send, filename=time.file_ts("SettingsTemplate", "json"))
                )
                # return await ctx.send(f"Here's the settings template for you.\nUpload with {ctx.prefix}settings
                # upload", file=discord.File(send, filename=time.file_ts("SettingsTemplate", "json")))

    @settings.command(name="template")
    async def settings_template(self, ctx: commands.Context):
        """ Settings template """
        # s = settings_template.copy()
        send = BytesIO(json.dumps(settings_template.copy(), indent=4).encode('utf-8'))
        return await generic.send(
            generic.gls(generic.get_lang(ctx.guild), "settings_template_detailed", [ctx.prefix]), ctx.channel,
            file=discord.File(send, filename=time.file_ts("SettingsTemplate", "json"))
        )
        # return await ctx.send(f"Here's the settings template for you.\nUpload with {ctx.prefix}settings upload\n"
        #                       f"For leveling, [USER] will show user's name, and [MENTION] will @mention them",
        #                       file=discord.File(send, filename=time.file_ts("SettingsTemplate", "json")))

    @settings.command(name="upload")
    async def settings_upload(self, ctx: commands.Context):
        """ Upload cogs server settings """
        ma = ctx.message.attachments
        if len(ma) == 1:
            name = ma[0].filename
            if not name.endswith('json'):
                return await generic.send(generic.gls(generic.get_lang(ctx.guild), "settings_upload_no1"), ctx.channel)
                # return await ctx.send("This must be a JSON file")
            try:
                stuff = await ma[0].read()
            except discord.HTTPException or discord.NotFound:
                return await generic.send(generic.gls(generic.get_lang(ctx.guild), "settings_upload_no2"), ctx.channel)
                # return await ctx.send("There was an error getting the file.")
        else:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "settings_upload_no3"), ctx.channel)
            # return await ctx.send("There must be exactly one JSON file.")
        try:
            json.loads(stuff)
        except Exception as e:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "settings_upload_no4",
                                                  [f"{type(e).__name__}: {e}"]), ctx.channel)
            # return await ctx.send(f"Error loading file:\n{type(e).__name__}: {e}")
        data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            res = self.db.execute(f"UPDATE settings SET data=? WHERE gid=?",
                                  (stuff, ctx.guild.id))
        else:
            res = self.db.execute(f"INSERT INTO settings VALUES (?, ?)",
                                  (ctx.guild.id, stuff))
        return await generic.send(generic.gls(generic.get_lang(ctx.guild), "settings_upload_yes", [res]), ctx.channel)
        # return await ctx.send(f"Settings have been updated\n{res}")

    @commands.command(name="emojis")
    @commands.is_owner()
    async def get_all_emotes(self, ctx: commands.Context):
        """ Yoink all emotes """
        channel = self.bot.get_channel(676154789159239740)
        await generic.send(f"This stash of emotes was made on {time.time()}", channel)
        # await channel.send(f"This stash of emotes was made on {time.time()}")
        for guild in self.bot.guilds:
            emotes = sorted([e for e in guild.emojis if len(e.roles) == 0 and e.available], key=lambda e: e.name)
            paginator = commands.Paginator(suffix='', prefix='')
            for emote in emotes:
                paginator.add_line(f'{emote.name} = "`{emote}`"')
            await generic.send(f"Next lot -> {guild.name}\n\n\n", channel)
            # await channel.send(f"Next lot -> {guild.name}\n\n\n")
            for page in paginator.pages:
                await generic.send(page, channel)
                # await channel.send(page)
        return await generic.send(f"Done yoinking emotes, {ctx.author.mention}, you may fuck off now.", ctx.channel, u=True)
        # return await ctx.send(f"Done yoinking emotes, {ctx.author.mention}, you may fuck off now.")

    @commands.command(name="emojis2")
    @commands.is_owner()
    async def get_all_emotes2(self, ctx: commands.Context):
        """ Yoink all emotes images """
        channel = self.bot.get_channel(712703923793952780)
        await generic.send("Yoinking emotes...", ctx.channel)
        await generic.send(f"This stash of emotes was made on {time.time()}", channel)
        # await channel.send(f"This stash of emotes was made on {time.time()}")
        for guild in self.bot.guilds:
            # len(e.roles) == 0 and
            emotes = sorted([e for e in guild.emojis if e.available], key=lambda e: e.name)
            # paginator = commands.Paginator(suffix='', prefix='')
            # for emote in emotes:
            #     paginator.add_line(f'{emote.name} = "`{emote}`"')
            await generic.send(f"Next lot -> {guild.name}\n\n\n", channel)
            for emote in emotes:
                # embed = discord.Embed(colour=generic.random_colour())
                # embed.set_image(url=emote.url)
                bio = BytesIO(await http.get(str(emote.url), res_method="read"))
                ext = "gif" if emote.animated else "png"
                await generic.send(f"{emote.name} - {emote.id}", channel, file=discord.File(bio, filename=f"{emote.name}_{emote.id}.{ext}"))
            # # await channel.send(f"Next lot -> {guild.name}\n\n\n")
            # for page in paginator.pages:
            #     await generic.send(page, channel)
            #     # await channel.send(page)
        return await generic.send(f"Done yoinking emotes, {ctx.author.mention}, you may fuck off now.", ctx.channel, u=True)
        # return await ctx.send(f"Done yoinking emotes, {ctx.author.mention}, you may fuck off now.")

    @commands.command(name="avatar")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def avatar(self, ctx: commands.Context, *, who: discord.User = None):
        """ Get someone's avatar """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "avatar"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        # if ctx.channel.id in self.banned:
        #     return
        user = who or ctx.author
        return await generic.send(generic.gls(locale, "avatar", [user.name, user.avatar_url_as(size=1024, static_format="png")]), ctx.channel)
        # return await ctx.send(f"Avatar to **{user.name}**\n{user.avatar_url_as(size=1024, static_format='png')}")

    @commands.command(name="roles")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def roles(self, ctx: commands.Context):
        """ Get all roles in current server """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "roles"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        all_roles = ""
        for num, role in enumerate(sorted(ctx.guild.roles, reverse=True), start=1):
            all_roles += f"[{str(num).zfill(2)}] {role.id}\t{role.name}\t[ Users: {len(role.members)} ]\r\n"
        data = BytesIO(all_roles.encode('utf-8'))
        return await generic.send(generic.gls(locale, "roles_in_server", [ctx.guild.name]), ctx.channel,
                                  file=discord.File(data, filename=f"{time.file_ts('Roles')}"))
        # return await ctx.send(content=f"Roles in **{ctx.guild.name}**",
        #                       file=discord.File(data, filename=f"{time.file_ts('Roles')}"))

    @commands.command(name="joinedat")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def joined_at(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Check when someone joined server """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "joinedat"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        user = who or ctx.author
        return await generic.send(generic.gls(locale, "user_joined_at", [user, ctx.guild.name, time.time_output(user.joined_at)]), ctx.channel)
        # return await ctx.send(f"**{user}** joined **{ctx.guild.name}** on {time.time_output(user.joined_at)}")

    @commands.command(name="user")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def user(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Get info about user """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "user"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        user = who or ctx.author
        embed = discord.Embed(colour=generic.random_colour())
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name=generic.gls(locale, "username"), value=user, inline=True)
        embed.add_field(name=generic.gls(locale, "nickname"), value=user.nick, inline=True)
        embed.add_field(name=generic.gls(locale, "user_id"), value=user.id, inline=True)
        embed.add_field(name=generic.gls(locale, "created_at"), value=time.time_output(user.created_at), inline=True)
        embed.add_field(name=generic.gls(locale, "joined_at"), value=time.time_output(user.joined_at), inline=True)
        embed.add_field(name=generic.gls(locale, "current_status"), value=str(user.status), inline=True)
        try:
            a = list(user.activities)
            if not a:
                embed.add_field(name="Current activity", value="None", inline=False)
            else:
                b = a[0]
                if b.type == discord.ActivityType.custom:
                    e = f"{b.emoji} " if b.emoji is not None else ''
                    n = b.name if b.name is not None else ''
                    embed.add_field(name=generic.gls(locale, "current_activity"), value=f"Custom Status:\n{e}{n}", inline=False)
                elif b.type == discord.ActivityType.streaming:
                    c = b.platform
                    d = b.name if b.name else ''
                    e = f" {b.game} " if b.game else ''
                    embed.add_field(name=generic.gls(locale, "current_activity"), value=f"Streaming {e} on {c}\n{d}", inline=False)
                elif b.type == discord.ActivityType.playing:
                    embed.add_field(name=generic.gls(locale, "current_activity"), value=f"Playing {b.name}", inline=False)
                elif b.type == discord.ActivityType.listening:
                    embed.add_field(name=generic.gls(locale, "current_activity"), inline=False,
                                    value=f"Listening to {b.name}\n{b.title} by {', '.join(b.artists)} - {b.album}")
            # embed.add_field(name="Activity", value=who.activity)
        except AttributeError:
            embed.add_field(name=generic.gls(locale, "current_activity"), value=generic.gls(locale, "no"), inline=False)
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
        embed.add_field(name=generic.gls(locale, "roles"), value=roles, inline=False)
        return await generic.send(generic.gls(locale, "about_user", [user]), ctx.channel, embed=embed)
        # await ctx.send(f"", embed=embed)

    @commands.command(name="emoji", aliases=["emote"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def emoji(self, ctx: commands.Context, emoji: discord.Emoji):
        """ View bigger version of a Custom Emoji """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "emoji"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        return await generic.send(f"{ctx.author.name}:", ctx.channel, embed=discord.Embed(
            description=generic.gls(locale, "emoji_desc", [emoji.name, emoji.id, emoji.animated, emoji.guild.name, time.time_output(emoji.created_at),
                                                           emoji.url]), colour=generic.random_colour()
        ).set_image(url=emoji.url).set_author(name=ctx.author, icon_url=ctx.author.avatar_url))
        # return await ctx.send(f"{ctx.author.name}:", embed=discord.Embed(
        #     description=f"Name: {emoji.name}\nID: {emoji.id}\nAnimated: {emoji.animated}\nServer: {emoji.guild.name}\n"
        #                 f"Created: {time.time_output(emoji.created_at)}\n[Copy Link]({emoji.url})",
        #     colour=generic.random_colour()).set_image(url=emoji.url).set_author(
        #     name=ctx.author, icon_url=ctx.author.avatar_url))

    @commands.command(name="customrole", aliases=["cr"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=30, type=commands.BucketType.user)
    async def custom_role(self, ctx: commands.Context, *, stuff: str):
        """ Custom Role (only in supported servers)

         Arguments:
        -c/--colour/--color: Set role colour
        -n/--name: Set role name """
        if ctx.guild.id in generic.config["custom_role"]:
            data = self.db.fetchrow("SELECT * FROM custom_role WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
            if not data:
                return await generic.send(f"Doesn't seem like you have a custom role in this server, {ctx.author.name}", ctx.channel)
                # return await ctx.send(f"Doesn't seem like you have a custom role, {ctx.author.name}")
            parser = argparser.Arguments()
            # parser.add_argument('input', nargs="+", default=None)
            parser.add_argument('-c', '--colour', '--color', nargs=1)
            parser.add_argument('-n', '--name', nargs="+")

            args, valid_check = parser.parse_args(stuff)
            if not valid_check:
                return await generic.send(args, ctx.channel)
                # return await ctx.send(args)

            role = ctx.guild.get_role(data['rid'])

            if args.colour is not None:
                c = args.colour[0]
                a = len(c)
                if c == "random":
                    col = generic.random_colour()
                else:
                    if a == 6 or a == 3:
                        try:
                            col = int(c, base=16)
                        except Exception as e:
                            return await generic.send(f"Invalid colour - {type(e).__name__}: {e}", ctx.channel)
                            # return await ctx.send(f"Invalid colour - {type(e).__name__}: {e}")
                    else:
                        return await generic.send("Colour must be either 3 or 6 HEX digits long.", ctx.channel)
                        # return await ctx.send("Colour must be either 3 or 6 HEX digits long.")
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
                return await generic.send(f"An error occurred while updating custom role: {type(e).__name__}: {e}", ctx.channel)
                # return await ctx.send(f"An error occurred while updating custom role: {type(e).__name__}: {e}")
            return await generic.send(f"Successfully updated your custom role, {ctx.author.name}", ctx.channel)
            # return await ctx.send(f"Successfully updated your custom role, {ctx.author.name}")
        else:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "cr_not_available"), ctx.channel)
            # return await generic.send(generic.gls(generic.get_lang(ctx.guild), "only_in_senko_lair"), ctx.channel)
            # return await ctx.send("This command is only available in Senko Lair.")

    @commands.command(name="grantrole")
    @commands.guild_only()
    # @commands.is_owner()
    @permissions.has_permissions(administrator=True)
    async def grant_custom_role(self, ctx: commands.Context, user: discord.Member, role: discord.Role):
        """ Grant custom role """
        if ctx.guild.id in generic.config["custom_role"]:
            # if ctx.guild.id == 568148147457490954:
            already = self.db.fetchrow("SELECT * FROM custom_role WHERE uid=?, gid=?", (user.id, ctx.guild.id))
            if not already:
                result = self.db.execute("INSERT INTO custom_role VALUES (?, ?, ?)", (user.id, role.id, ctx.guild.id))
                await user.add_roles(role, reason="Custom Role grant")
                return await generic.send(f"Granted {role.name} to {user.name}: {result}", ctx.channel)
                # return await ctx.send(f"Granted {role.name} to {user.name}: {result}")
            else:
                result = self.db.execute("UPDATE custom_role SET rid=? WHERE uid=? AND gid=?", (role.id, user.id, ctx.guild.id))
                return await generic.send(f"Updated custom role of {user.name} to {role.name}: {result}", ctx.channel)
                # return await ctx.send(f"Updated custom role of {user.name} to {role.name}: {result}")
        else:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "cr_not_available"), ctx.channel)
            # return await ctx.send("This is only available in Senko Lair")

    @commands.group(name="server", aliases=["guild"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def server(self, ctx: commands.Context):
        """ Check info about current server """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "server"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        # if ctx.channel.id in self.banned:
        #     return
        if ctx.invoked_subcommand is None:
            bots = sum(1 for member in ctx.guild.members if member.bot)
            embed = discord.Embed(colour=generic.random_colour())
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.add_field(name=generic.gls(locale, "server_name"), value=ctx.guild.name, inline=True)
            embed.add_field(name=generic.gls(locale, "server_id"), value=ctx.guild.id, inline=True)
            embed.add_field(name=generic.gls(locale, "owner"), inline=True,
                            value=f"{ctx.guild.owner}\n({ctx.guild.owner.display_name})")
            embed.add_field(name=generic.gls(locale, "members"), value=ctx.guild.member_count, inline=True)
            embed.add_field(name=generic.gls(locale, "bots"), value=str(bots), inline=True)
            embed.add_field(name=generic.gls(locale, "region"), value=ctx.guild.region, inline=True)
            embed.add_field(name=generic.gls(locale, "roles"), value=str(len(ctx.guild.roles)), inline=True)
            try:
                embed.add_field(name=generic.gls(locale, "ban_count"), value=str(len(await ctx.guild.bans())), inline=True)
            except discord.Forbidden:
                embed.add_field(name=generic.gls(locale, "ban_count"), value=generic.gls(locale, "access_denied"), inline=True)
            embed.add_field(name=generic.gls(locale, "verification_level"), inline=True, value=generic.gls(locale, str(ctx.guild.verification_level)))
            embed.add_field(name=generic.gls(locale, "channels"), inline=True,
                            value=generic.gls(locale, "channels2", [len(ctx.guild.text_channels), len(ctx.guild.categories), len(ctx.guild.voice_channels)]))
            embed.add_field(name=generic.gls(locale, "boosts"), inline=True,
                            value=generic.gls(locale, "boosts2", [ctx.guild.premium_subscription_count, ctx.guild.premium_tier,
                                                                  len(ctx.guild.premium_subscribers)]))
            ani_emotes = len([emote for emote in ctx.guild.emojis if emote.animated])
            total_emotes = len(ctx.guild.emojis)
            embed.add_field(name=generic.gls(locale, "emotes"), inline=True,
                            value=generic.gls(locale, "emotes2", [ctx.guild.emoji_limit, ani_emotes, total_emotes - ani_emotes, total_emotes]))
            # value=f"{len(ctx.guild.text_channels)} text channels\n"
            #       f"{len(ctx.guild.categories)} categories\n"
            #       f"{len(ctx.guild.voice_channels)} voice channels")
            embed.add_field(name=generic.gls(locale, "created_at"), inline=False,  # value=generic.gls(locale, "server_ca"))
                            value=f"{time.time_output(ctx.guild.created_at)} - "
                                  f"{time.human_timedelta(ctx.guild.created_at)}")
            return await generic.send(generic.gls(locale, "about_server", [ctx.guild.name]), ctx.channel, embed=embed)
            # return await ctx.send(f"About **{ctx.guild.name}**", embed=embed)

    @server.command(name="icon", aliases=["avatar"])
    async def server_icon(self, ctx: commands.Context):
        """ Get server icon """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "server"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        return await generic.send(generic.gls(locale, "server_icon", [ctx.guild.name, ctx.guild.icon_url_as(size=1024, static_format="png")]), ctx.channel)
        # return await ctx.send(f"Icon of **{ctx.guild.name}**:\n{ctx.guild.icon_url_as(size=1024)}")

    @server.command(name="banner")
    async def server_banner(self, ctx: commands.Context):
        """ Get server banner """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "server"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        link = ctx.guild.banner_url_as(size=4096, format="png")
        if link:
            return await generic.send(generic.gls(locale, "server_banner", [ctx.guild.name, link]), ctx.channel)
        else:
            return await generic.send(generic.gls(locale, "server_banner_none", [ctx.guild.name]), ctx.channel)
        # return await generic.send(generic.gls(locale, "server_banner", [ctx.guild.name, ctx.guild.banner_url_as(size=4096, format="png")]), ctx.channel)
        # return await ctx.send(f"Icon of **{ctx.guild.name}**:\n{ctx.guild.icon_url_as(size=1024)}")

    @server.command(name="invite", aliases=["splash"])
    async def server_invite(self, ctx: commands.Context):
        """ Get server invite splash """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "server"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        link = ctx.guild.splash_url_as(size=4096, format="png")
        if link:
            return await generic.send(generic.gls(locale, "server_splash", [ctx.guild.name, link]), ctx.channel)
        else:
            return await generic.send(generic.gls(locale, "server_splash_none", [ctx.guild.name]), ctx.channel)
        # return await ctx.send(f"Icon of **{ctx.guild.name}**:\n{ctx.guild.icon_url_as(size=1024)}")

    @server.command(name="bots")
    async def server_bots(self, ctx: commands.Context):
        """ Bots in servers """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "server"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        bots = [a for a in ctx.guild.members if a.bot]
        m = ''
        for i in range(len(bots)):
            n = str(i+1) if i >= 9 else f"0{i+1}"
            m += f"[{n}] {bots[i]}\n"
        return await generic.send(generic.gls(locale, "bots_in_server", [ctx.guild.name, m]), ctx.channel)
        # return await ctx.send(f"Bots in **{ctx.guild.name}**: ```ini\n{m}```")

    @server.command(name="status")
    async def server_status(self, ctx: commands.Context):
        """ Server status """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "server"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
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
        embed = discord.Embed(colour=generic.random_colour(), description=generic.gls(locale, "status_of_users", [ctx.guild.name]))
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(name=generic.gls(locale, "total_members"), value=f"{m:,}", inline=False)
        e1, e2, e3, e4 = "<:online:679052892514287635>", "<:idle:679052892828598303>", "<:dnd:679052892782723114> ", \
                         "<:offline:679052892782592033>"
        a1, a2, a3, a4, a5 = "🎮", "<:streaming:679055367346323478>", "<:listening:679055367396917250> ", \
                             "<:pikathink:674330001151229963>", "<:awoogoodnight:613410343359873054>"
        po, pi, pd, pn = so / m * 100, si / m * 100, sd / m * 100, sn / m * 100
        embed.add_field(name=generic.gls(locale, "status"), inline=False,
                        value=generic.gls(locale, "status2", [e1, f"{so:,}", f"{po:.2f}", f"{mo:,}", f"{do:,}", f"{wo:,}", e2, f"{si:,}",
                                                              f"{pi:.2f}", f"{mi:,}", f"{di:,}", f"{wi:,}", e3, f"{sd:,}", f"{pd:.2f}", f"{md:,}",
                                                              f"{dd:,}", f"{wd:,}", e4, f"{sn:,}", f"{pn:.2f}"]))
        # embed.add_field(name="Status", inline=False, value=f"{e1} Online: {so:,} - {po:.2f}%, of which:\n"
        #                                                    f"Mobile: {mo:,} | Desktop: {do:,} | Web: {wo:,}\n\n"
        #                                                    f"{e2} Idle: {si:,} - {pi:.2f}%, of which:\n"
        #                                                    f"Mobile: {mi:,} | Desktop: {di:,} | Web: {wi:,}\n\n"
        #                                                    f"{e3} Dungeons and Dragons: {sd:,} - {pd:.2f}%, of which:\n"
        #                                                    f"Mobile: {md:,} | Desktop: {dd:,} | Web: {wd:,}\n\n"
        #                                                    f"{e4} Offline: {sn:,} - {pn:.2f}%")
        o = m - sn
        apg, apt, apl, apc, apn = ag / o * 100, at / o * 100, al / o * 100, ac / o * 100, an / o * 100
        embed.add_field(name=generic.gls(locale, "activities"), inline=False,
                        value=generic.gls(locale, "activities2", [f"{o:,}", a1, f"{ag:,}", f"{apg:.2f}", a4, f"{ac:,}", f"{apc:.2f}", a2, f"{at:,}",
                                                                  f"{apt:.2f}", a3, f"{al:,}", f"{apl:.2f}", a5, f"{an:,}", f"{apn:.2f}"]))
        # embed.add_field(name="Activities", inline=False, value=f"Out of {o:,} people online:\n"
        #                                                        f"{a1} Playing a game: {ag:,} - {apg:.2f}%\n"
        #                                                        f"{a4} Playing Custom Status: {ac:,} - {apc:.2f}%\n"
        #                                                        f"{a2} Streaming: {at:,} - {apt:.2f}%\n"
        #                                                        f"{a3} Listening: {al:,} - {apl:.2f}%\n"
        #                                                        f"{a5} Doing nothing: {an:,} - {apn:.2f}%")
        # return await ctx.send(embed=embed)
        return await generic.send(None, ctx.channel, embed=embed)

    @commands.command(name="prefix")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def prefix(self, ctx: commands.Context):
        """ Server prefixes """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "prefix"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        _data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        # _data = self.db.fetchrow(f"SELECT * FROM data_{self.type} WHERE type=? AND id=?", ("settings", ctx.guild.id))
        if not _data:
            dp = generic.get_config()["prefixes"]
            cp = None
            dp.append(self.bot.user.mention)
        else:
            data = json.loads(_data['data'])
            dp = generic.get_config()["prefixes"] if data['use_default'] else []
            cp = data['prefixes']
            dp.append(self.bot.user.mention)
        embed = discord.Embed(colour=generic.random_colour())
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(name=generic.gls(locale, "default_prefixes"), value='\n'.join(dp), inline=True)
        if cp is not None and cp != []:
            embed.add_field(name=generic.gls(locale, "custom_prefixes"), value='\n'.join(cp), inline=True)
        return await generic.send(generic.gls(locale, "server_prefixes", [ctx.guild.name]), ctx.channel, embed=embed)
        # return await ctx.send(f"Prefixes for {ctx.guild.name}", embed=embed)


def setup(bot):
    bot.add_cog(Discord(bot))
