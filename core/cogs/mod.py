import json
import re
from io import BytesIO

import discord
from discord.ext import commands

from core.utils import general, permissions, time
from languages import langs


async def do_removal(ctx: commands.Context, limit: int, predicate, *, before: int = None, after: int = None, message: bool = True):
    locale = langs.gl(ctx)
    if limit > 2000:
        return await general.send(langs.gls("mod_purge_max", locale), ctx.channel)
        # return await general.send(f"Too many messages to search given ({limit:,}/2,000)", ctx.channel)
    if before is None:
        before = ctx.message
    else:
        before = discord.Object(id=before)
    if after is not None:
        after = discord.Object(id=after)
    _message = None  # if message = False
    if message is True:
        _message = await general.send(langs.gls("mod_purge_loading", locale), ctx.channel)
    try:
        deleted = await ctx.channel.purge(limit=limit, before=before, after=after, check=predicate)
    except discord.Forbidden:
        return await general.send(langs.gls("mod_purge_forbidden", locale), ctx.channel)
        # return await general.send("I don't have the permissions to delete messages", ctx.channel)
    # except discord.HTTPException as e:
    except Exception as e:
        return await general.send(langs.gls("mod_purge_error", locale, type(e).__name__, str(e)), ctx.channel)
        # return await general.send(f"An error has occurred: `{type(e).__name__}: {e}`\nTry a smaller search?", ctx.channel)
    _deleted = len(deleted)
    if message is True:
        await _message.delete()
        return await general.send(langs.gls("mod_purge", locale, langs.gns(_deleted, locale)), ctx.channel, delete_after=10)
        # await general.send(f"🚮 Successfully removed {_deleted:,} messages", ctx.channel, delete_after=10)


class MemberID(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            m = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                return int(argument, base=10)
            except ValueError:
                raise commands.BadArgument(f"{argument} is not a valid member or member ID.") from None
        else:
            return m.id


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # self.admins = self.bot.config["owners"]

    @commands.command(name="kick")
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick_user(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        """ Kick a user from the server """
        locale = langs.gl(ctx)
        if member == ctx.author:
            return await general.send(langs.gls("mod_kick_self", locale), ctx.channel)
            # return await general.send(f"Self harm bad {emotes.BlobCatPolice}", ctx.channel)
        elif member.id == ctx.guild.owner.id:
            return await general.send(langs.gls("mod_kick_owner", locale), ctx.channel)
            # return await general.send("Imagine trying to kick the server's owner, lol", ctx.channel)
        elif (member.top_role.position >= ctx.author.top_role.position) and ctx.author != ctx.guild.owner:
            return await general.send(langs.gls("mod_kick_forbidden", locale), ctx.channel)
            # return await general.send("You can't kick a member whose top role is equal to or is above yours.", ctx.channel)
        # elif member.id in self.admins:
        #     return await general.send("I can't kick my owners or admins...", ctx.channel)
        elif member.id == self.bot.user.id:
            return await general.send(langs.gls("mod_ban_suager", locale, ctx.author.name), ctx.channel)
            # return await general.send(f"We are not friends anymore, {ctx.author.name}.", ctx.channel)
        try:
            user = str(member)
            await member.kick(reason=general.reason(ctx.author, reason))
            return await general.send(langs.gls("mod_kick", locale, user, reason), ctx.channel)
            # return await general.send(f"{emotes.Allow} Successfully kicked **{user}** for {reason}", ctx.channel)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="ban")
    @commands.guild_only()
    @permissions.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_user(self, ctx: commands.Context, member: MemberID, *, reason: str = None):
        """ Ban a user from the server """
        locale = langs.gl(ctx)
        if member == ctx.author.id:
            return await general.send(langs.gls("mod_ban_self", locale), ctx.channel)
            # return await general.send(f"Self harm bad {emotes.BlobCatPolice}", ctx.channel)
        elif member == ctx.guild.owner.id:
            return await general.send(langs.gls("mod_ban_owner", locale), ctx.channel)
            # return await general.send("Imagine trying to ban the server's owner, lol", ctx.channel)
        elif (them := ctx.guild.get_member(member)) is not None and (them.top_role.position >= ctx.author.top_role.position) and ctx.author != ctx.guild.owner:
            return await general.send(langs.gls("mod_ban_forbidden", locale), ctx.channel)
            # return await general.send("You can't ban a member whose top role is equal to or is above yours.", ctx.channel)
        # elif member in self.admins:
        #     return await general.send("I can't ban my owners or admins...", ctx.channel)
        elif member == self.bot.user.id:
            return await general.send(langs.gls("mod_ban_suager", locale, ctx.author.name), ctx.channel)
            # return await general.send(f"We are not friends anymore, {ctx.author.name}.", ctx.channel)
        try:
            user = await self.bot.fetch_user(member)
            await ctx.guild.ban(discord.Object(id=member), reason=general.reason(ctx.author, reason))
            return await general.send(langs.gls("mod_ban", locale, member, user, reason), ctx.channel)
            # return await general.send(f"{emotes.Allow} Successfully banned **{member} ({user})** for **{reason}**", ctx.channel)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="massban")
    @commands.guild_only()
    @permissions.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def mass_ban(self, ctx: commands.Context, reason: str, *who: MemberID):
        """ Mass ban users from the server """
        locale = langs.gl(ctx)
        if ctx.author.id in who:
            return await general.send(langs.gls("mod_ban_self", locale), ctx.channel)
            # return await general.send(f"Self harm bad {emotes.BlobCatPolice}", ctx.channel)
        else:
            for member in who:
                # if member in self.admins:
                #     return await general.send("I can't ban my owners or admins...", ctx.channel)
                if member == self.bot.user.id:
                    return await general.send(langs.gls("mod_ban_suager", locale, ctx.author.name), ctx.channel)
                    # return await general.send(f"We are not friends anymore, {ctx.author.name}.", ctx.channel)
                if member == ctx.guild.owner.id:
                    return await general.send(langs.gls("mod_ban_owner", locale), ctx.channel)
                    # return await general.send("Imagine trying to ban the server's owner, lol", ctx.channel)
                elif (them := ctx.guild.get_member(member)) is not None and (them.top_role.position >= ctx.author.top_role.position) and ctx.author != ctx.guild.owner:
                    return await general.send(langs.gls("mod_ban_forbidden", locale), ctx.channel)
                    # return await general.send("You can't ban a member whose top role is equal to or is above yours.", ctx.channel)
        banned = 0
        failed = 0
        for member in who:
            try:
                await ctx.guild.ban(discord.Object(id=member), reason=general.reason(ctx.author, reason))
                banned += 1
            except Exception as e:
                failed += 1
                await general.send(f"`{member}` - {type(e).__name__}: {e}", ctx.channel)
        total = banned + failed
        return await general.send(langs.gls("mod_ban_mass", locale, reason, langs.gns(total, locale), langs.gns(banned, locale), langs.gns(failed, locale)), ctx.channel)
        # return await general.send(f"Mass-banned **{total} users** for {reason}:\n{emotes.Allow} Successful: **{banned}**\n"
        #                           f"{emotes.Deny} Failed: **{failed}**", ctx.channel)

    @commands.command(name="unban")
    @commands.guild_only()
    @permissions.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban_user(self, ctx: commands.Context, member: MemberID, *, reason: str = None):
        """ Unban a user """
        locale = langs.gl(ctx)
        try:
            await ctx.guild.unban(discord.Object(id=member), reason=general.reason(ctx.author, reason))
            user = await self.bot.fetch_user(member)
            return await general.send(langs.gls("mod_unban", locale, member, user, reason), ctx.channel)
            # return await general.send(f"{emotes.Allow} Successfully unbanned **{member} ({user})** for {reason}", ctx.channel)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="nickname", aliases=["nick"])
    @commands.guild_only()
    @permissions.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nickname_user(self, ctx: commands.Context, member: discord.Member, *, name: str = None):
        """ Sets a user's nickname """
        locale = langs.gl(ctx)
        try:
            if member.id == ctx.guild.owner.id:
                return await general.send(langs.gls("mod_nick_owner", locale), ctx.channel)
                # return await general.send("The server owner's nickname can't be edited.", ctx.channel)
            if (member.top_role.position >= ctx.author.top_role.position and member != ctx.author) and ctx.author != ctx.guild.owner:
                return await general.send(langs.gls("mod_nick_forbidden2", locale), ctx.channel)
                # return await general.send("You can't change the nickname of a member whose top role is equal to or is above yours.", ctx.channel)
            await member.edit(nick=name, reason=general.reason(ctx.author, "Changed by command"))
            if name is None:
                message = langs.gls("mod_nick_reset", locale, member)
                # message = f"Reset **{member}**'s nickname"
            else:
                message = langs.gls("mod_nick", locale, member, name)
                # message = f"Changed **{member}**'s nickname to **{name}**"
            return await general.send(message, ctx.channel)
        except discord.Forbidden:
            return await general.send(langs.gls("mod_nick_forbidden", locale), ctx.channel)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="nicknameme", aliases=["nickme", "nameme"])
    @commands.guild_only()
    @permissions.has_permissions(change_nickname=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nickname_self(self, ctx: commands.Context, *, name: str = None):
        """ Change your own nickname """
        locale = langs.gl(ctx)
        try:
            if ctx.author.id == ctx.guild.owner.id:
                return await general.send(langs.gls("mod_nick_owner", locale), ctx.channel)
                # return await general.send("I can't change the server owner's nickname.", ctx.channel)
            await ctx.author.edit(nick=name, reason=general.reason(ctx.author, "Changed by command"))
            if name is None:
                message = langs.gls("mod_nick_self_reset", locale)
                # message = f"Reset your nickname"
            else:
                message = langs.gls("mod_nick_self", locale, name)
                # message = f"Changed your nickname to **{name}**"
            return await general.send(message, ctx.channel)
        except discord.Forbidden:
            return await general.send(langs.gls("mod_nick_forbidden", locale), ctx.channel)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="mute")
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.check(lambda ctx: ctx.bot.name == "suager")
    async def mute_user(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        """ Mute a user """
        locale = langs.gl(ctx)
        reason = reason or langs.gls("mod_reason_none", locale)
        if member.id == self.bot.user.id:
            return await general.send(langs.gls("mod_mute_suager", locale), ctx.channel)
            # return await general.send("Why did you bring me to this server... just to mute me?", ctx.channel)
        if member == ctx.author:
            return await general.send(langs.gls("mod_mute_self", locale), ctx.channel)
            # return await general.send(f"Self harm bad {emotes.BlobCatPolice}", ctx.channel)
        # if (member.top_role.position >= ctx.author.top_role.position) and ctx.author != ctx.guild.owner:  # and ctx.guild.id not in [784357864482537473]:
        #     return await general.send("You aren't supposed to mute people above you.", ctx.channel)
        _reason = general.reason(ctx.author, reason)
        _data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not _data:
            return await general.send(langs.gls("mod_mute_role2", locale, ctx.prefix), ctx.channel)
            # return await general.send(f"This server does not seem to have a mute role set. Use `{ctx.prefix}settings` to set one.", ctx.channel)
        data = json.loads(_data["data"])
        try:
            mute_role_id = data["mute_role"]
        except KeyError:
            return await general.send(langs.gls("mod_mute_role", locale), ctx.channel)
            # return await general.send("This server has no mute role set, or it no longer exists.", ctx.channel)
        mute_role = ctx.guild.get_role(mute_role_id)
        if not mute_role:
            return await general.send(langs.gls("mod_mute_role", locale), ctx.channel)
            # return await general.send("This server has no mute role set, or it no longer exists.", ctx.channel)
        try:
            await member.add_roles(mute_role, reason=_reason)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)
        out = langs.gls("mod_mute", locale, member, reason)
        # out = f"{emotes.Allow} Successfully muted **{member}** for **{reason}**"
        if reason is not None:
            _duration = reason.split(" ")[0]
            delta = time.interpret_time(_duration)
            expiry, error = time.add_time(delta)
            if time.rd_is_above_5y(delta):
                await general.send(langs.gls("mod_mute_limit", locale), ctx.channel)
                # await general.send("You can't specify a time range above 5 years. Making mute permanent...", ctx.channel)
                error = True
            # Quietly ignore any errors, since it's probably someone fucking around, or it's not a duration to begin with
            # await general.send(f"Failed to convert duration: {expiry} | Making mute permanent...", ctx.channel)
            if not error:
                random_id = general.random_id()
                while self.bot.db.fetch("SELECT entry_id FROM temporary WHERE entry_id=?", (random_id,)):
                    random_id = general.random_id()
                self.bot.db.execute("INSERT INTO temporary VALUES (?, ?, ?, ?, ?, ?, ?)", (member.id, "mute", expiry, ctx.guild.id, None, random_id, 0))
                duration = langs.td_rd(delta, "en", accuracy=7, brief=False, suffix=False)
                reason = " ".join(reason.split(" ")[1:])
                if not reason:
                    reason = langs.gls("mod_reason_none", locale)
                out = langs.gls("mod_mute_timed", locale, member, duration, reason)
                # out = f"{emotes.Allow} Successfully muted **{member}** for **{duration}** for **{reason}**"
        return await general.send(out, ctx.channel)

    @commands.command(name="unmute")
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.check(lambda ctx: ctx.bot.name == "suager")
    async def unmute_user(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        """ Unmute a user """
        locale = langs.gl(ctx)
        reason = reason or langs.gls("mod_reason_none", locale)
        if member == ctx.author:
            return await general.send(langs.gls("mod_unmute_self", locale), ctx.channel)
            # return await general.send(f"Imagine trying to unmute yourself {emotes.BlobCatPolice}", ctx.channel)
        _reason = general.reason(ctx.author, reason)
        _data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not _data:
            return await general.send(langs.gls("mod_mute_role2", locale, ctx.prefix), ctx.channel)
            # return await general.send(f"This server does not seem to have a mute role set. Use `{ctx.prefix}settings` to set one.", ctx.channel)
        data = json.loads(_data["data"])
        try:
            mute_role_id = data["mute_role"]
        except KeyError:
            return await general.send(langs.gls("mod_mute_role", locale), ctx.channel)
            # return await general.send("This server has no mute role set, or it no longer exists.", ctx.channel)
        mute_role = ctx.guild.get_role(mute_role_id)
        if not mute_role:
            return await general.send(langs.gls("mod_mute_role", locale), ctx.channel)
            # return await general.send("This server has no mute role set, or it no longer exists.", ctx.channel)
        try:
            await member.remove_roles(mute_role, reason=_reason)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)
        self.bot.db.execute("DELETE FROM temporary WHERE uid=? AND type='mute' AND gid=?", (member.id, ctx.guild.id))
        return await general.send(langs.gls("mod_unmute", locale, member, reason), ctx.channel)
        # return await general.send(f"{emotes.Allow} Successfully unmuted **{member}** for **{reason}**", ctx.channel)

    @commands.command(name="mutes", aliases=["punishments"])
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    @commands.check(lambda ctx: ctx.bot.name == "suager")
    async def mute_list(self, ctx: commands.Context):
        """ See a list of the currently active temporary mutes """
        locale = langs.gl(ctx)
        reminders = self.bot.db.fetch("SELECT * FROM temporary WHERE gid=? AND type='mute' ORDER BY expiry", (ctx.guild.id,))
        if not reminders:
            return await general.send(langs.gls("mod_mute_list_none", locale, ctx.guild.name), ctx.channel)
            # return await general.send(f"No one is temporarily muted at the moment in {ctx.guild.name}.", ctx.channel)
        output = langs.gls("mod_mute_list", locale, ctx.guild.name)
        # output = f"List of currently active temporary mutes in **{ctx.guild.name}**"
        outputs = []
        _reminder = 0
        for reminder in reminders:
            _reminder += 1
            expiry = reminder["expiry"]
            expires_on = langs.gts(expiry, "en", True, True, False, True, False)
            expires_in = langs.td_dt(expiry, "en", accuracy=3, brief=False, suffix=True)
            who = self.bot.get_user(reminder["uid"])
            outputs.append(langs.gls("mod_mute_list_item", locale, langs.gns(_reminder, locale, commas=False), who, expires_on, expires_in))
            # outputs.append(f"**{_reminder})** {who}\nMuted until {expires_on}\nExpires {expires_in}")
        output2 = "\n\n".join(outputs)
        if len(output2) > 1900:
            _data = BytesIO(str(output2).encode('utf-8'))
            return await general.send(output, ctx.channel, file=discord.File(_data, filename=time.file_ts('Mutes')))
        else:
            return await general.send(f"{output}\n{output2}", ctx.channel)

    @commands.group(name="find")
    @commands.guild_only()
    @permissions.has_permissions(ban_members=True)
    async def find(self, ctx: commands.Context):
        """ Finds a server member within your search term """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    # @find.command(name="playing")
    # async def find_playing(self, ctx: commands.Context, *, search: str):
    #     loop = [f"{i} | {i.activity.name} ({i.id})" for i in ctx.guild.members if i.activity if (search.lower() in i.activity.name.lower()) and (not i.bot)]
    #     await general.pretty_results(ctx, "playing", f"Found **{len(loop)}** on your search for **{search}**", loop)

    @find.command(name="username", aliases=["name"])
    async def find_name(self, ctx: commands.Context, *, search: str):
        """Finds members whose username fits the search string"""
        loop = [f"{i} ({i.id})" for i in ctx.guild.members if search.lower() in i.name.lower()]  # and not i.bot
        await general.pretty_results(ctx, "name", langs.gls("mod_find", langs.gl(ctx), langs.gns(len(loop), langs.gl(ctx)), search), loop)
        # f"Found **{len(loop)}** on your search for **{search}**"

    @find.command(name="nickname", aliases=["nick"])
    async def find_nickname(self, ctx: commands.Context, *, search: str):
        """Finds members whose nickname fits the search string"""
        loop = [f"{i.nick} | {i} ({i.id})" for i in ctx.guild.members if i.nick if (search.lower() in i.nick.lower())]  # and not i.bot
        await general.pretty_results(ctx, "name", langs.gls("mod_find", langs.gl(ctx), langs.gns(len(loop), langs.gl(ctx)), search), loop)

    @find.command(name="discriminator", aliases=["disc"])
    async def find_discriminator(self, ctx: commands.Context, *, search: str):
        """Finds members whose discriminator is the same as the search"""
        if len(search) != 4 or not re.compile("^[0-9]*$").search(search):
            return await general.send(langs.gls("mod_find_disc", langs.gl(ctx)), ctx.channel)
        loop = [f"{i} ({i.id})" for i in ctx.guild.members if search == i.discriminator]
        await general.pretty_results(ctx, "discriminator", langs.gls("mod_find", langs.gl(ctx), langs.gns(len(loop), langs.gl(ctx)), search), loop)

    @commands.group(name="purge", aliases=["prune", "delete"])
    @commands.guild_only()
    @permissions.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    async def prune(self, ctx: commands.Context):
        """ Removes messages from the current server. """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @prune.command(name="embeds")
    async def prune_embeds(self, ctx: commands.Context, search: int = 100):
        """Removes messages that have embeds in them."""
        await do_removal(ctx, search, lambda e: len(e.embeds))

    @prune.command(name="files")
    async def prune_files(self, ctx: commands.Context, search: int = 100):
        """Removes messages that have attachments in them."""
        await do_removal(ctx, search, lambda e: len(e.attachments))

    @prune.command(name="mentions")
    async def prune_mentions(self, ctx: commands.Context, search: int = 100):
        """Removes messages that have mentions in them."""
        await do_removal(ctx, search, lambda e: len(e.mentions) or len(e.role_mentions))

    @prune.command(name="images")
    async def prune_images(self, ctx: commands.Context, search: int = 100):
        """Removes messages that have embeds or attachments."""
        await do_removal(ctx, search, lambda e: len(e.embeds) or len(e.attachments))

    @prune.command(name="all")
    async def prune_all(self, ctx: commands.Context, search: int = 100):
        """Removes all messages."""
        await do_removal(ctx, search, lambda e: True)

    @prune.command(name="user")
    async def prune_user(self, ctx: commands.Context, user: discord.User = None, search: int = 100):
        """Removes all messages by the member."""
        if user is None:
            return await general.send(langs.gls("mod_purge_user", langs.gl(ctx)), ctx.channel)
        await do_removal(ctx, search, lambda e: e.author == user)

    @prune.command(name="contains")
    async def prune_contains(self, ctx: commands.Context, substring: str = None, search: int = 100):
        """Removes all messages containing a substring.
        The substring must be at least 3 characters long."""
        if substring is None or len(substring) < 3:
            return await general.send(langs.gls("mod_purge_substring", langs.gl(ctx)), ctx.channel)
            # await ctx.send('The substring length must be at least 3 characters.')
        else:
            await do_removal(ctx, search, lambda e: substring in e.content)

    @prune.command(name="bots")
    async def prune_bots(self, ctx: commands.Context, search: int = 100, prefix: str = None):
        """Removes a bot user's messages and messages with their optional prefix."""
        get_prefix = prefix if prefix else self.bot.local_config["prefixes"]

        def predicate(m):
            return (m.webhook_id is None and m.author.bot) or m.content.startswith(tuple(get_prefix))
        await do_removal(ctx, search, predicate)

    @prune.command(name="users")
    async def prune_users(self, ctx: commands.Context, search: int = 100):
        """Removes only user messages."""
        def predicate(m):
            return m.author.bot is False
        await do_removal(ctx, search, predicate)

    @prune.command(name="after")
    async def prune_users(self, ctx: commands.Context, message_id: int):
        """Removes all messages after a message ID (up to 2,000 messages in the past)."""
        await do_removal(ctx, 2000, lambda e: True, after=message_id)

    @prune.command(name="emojis", aliases=["emotes"])
    async def prune_emoji(self, ctx: commands.Context, search: int = 100):
        """Removes all messages containing custom emoji."""
        # custom_emoji = re.compile(r'<(?:a)?:(\w+):(\d+)>')
        custom_emoji = re.compile(r'<a?:(\w+):(\d{17,18})>')

        def predicate(m):
            return custom_emoji.search(m.content)
        await do_removal(ctx, search, predicate)

    @prune.command(name="reactions")
    async def prune_reactions(self, ctx: commands.Context, search: int = 100):
        """Removes all reactions from messages that have them."""
        locale = langs.gl(ctx)
        if search > 2000:
            return await general.send(langs.gls("mod_purge_max", locale, langs.gns(search, locale)), ctx.channel)
            # return await ctx.send(f'Too many messages to search for ({search:,}/2000)')
        total_reactions = 0
        async for message in ctx.history(limit=search, before=ctx.message):
            if len(message.reactions):
                total_reactions += sum(r.count for r in message.reactions)
                await message.clear_reactions()
        return await general.send(langs.gls("mod_purge_reactions", locale, langs.gns(total_reactions, locale)), ctx.channel)
        # await general.send(f"🚮 Successfully removed {total_reactions:,} reactions.", ctx.channel)


def setup(bot):
    bot.add_cog(Moderation(bot))
