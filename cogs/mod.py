from __future__ import annotations

import json
import re
from io import BytesIO

import discord
from discord.ext import commands

from utils import bot_data, general, logger, permissions, time
from utils.languages import FakeContext


async def do_removal(ctx: commands.Context, limit: int, predicate, *, before: int = None, after: int = None, message: bool = True):
    language = ctx.bot.language(ctx)
    if limit > 2000:
        return await general.send(language.string("mod_purge_max"), ctx.channel)
        # return await general.send(f"Too many messages to search given ({limit:,}/2,000)", ctx.channel)
    if before is None:
        before = ctx.message
    else:
        before = discord.Object(id=before)
    if after is not None:
        after = discord.Object(id=after)
    _message = None  # if message = False
    if message is True:
        _message = await general.send(language.string("mod_purge_loading"), ctx.channel)
    try:
        deleted = await ctx.channel.purge(limit=limit, before=before, after=after, check=predicate)
    except discord.Forbidden:
        return await general.send(language.string("mod_purge_forbidden"), ctx.channel)
        # return await general.send("I don't have the permissions to delete messages", ctx.channel)
    # except discord.HTTPException as e:
    except Exception as e:
        return await general.send(language.string("mod_purge_error", type(e).__name__, str(e)), ctx.channel)
        # return await general.send(f"An error has occurred: `{type(e).__name__}: {e}`\nTry a smaller search?", ctx.channel)
    _deleted = len(deleted)
    if message is True:
        await _message.delete()
        return await general.send(language.string("mod_purge", language.number(_deleted)), ctx.channel, delete_after=10)
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


async def send_mod_dm(bot: bot_data.Bot, ctx: commands.Context | FakeContext, user: discord.User | discord.Member,
                      action: str, reason: str, duration: str = None, auto: bool = False, original_warning: str = None):
    """ Try to send the user a DM that they've been warned/muted/kicked/banned """
    try:
        _data = bot.db.fetchrow("SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        data = json.loads(_data["data"])
        mod_dms = data["mod_dms"]
        if action == ["warn", "pardon"]:
            key = "warn"
        elif action in ["mute", "unmute"]:
            key = "mute"
        elif action == "kick":
            key = "kick"
        elif action in ["ban", "unban"]:
            key = "ban"
        else:
            raise ValueError(f"Invalid action {action} specified")
        enabled = mod_dms[key]
    except (IndexError, KeyError):
        return  # If the settings can't be read, assume it's disabled
    if not enabled:
        return  # DMs for this action are disabled
    # if not hasattr(ctx, "author"):
    #     author = bot.user
    # else:
    #     author = ctx.author
    language = bot.language(ctx)
    if action == "pardon":
        # When a warning is pardoned manually, it will show the original warning as `[ID] Warning text`
        text = language.string("mod_dms_pardon", server=ctx.guild, reason=reason, original_warning=original_warning)
    elif action == "mute" and duration is not None:
        # The duration is already converted into str by the mute command
        text = language.string("mod_dms_mute_temp", server=ctx.guild, reason=reason, duration=duration)
    elif action == "unmute" and auto:
        text = language.string("mod_dms_unmute_expired", server=ctx.guild)
    else:
        string = f"mod_dms_{action}"
        text = language.string(string, server=ctx.guild, reason=reason)
    try:
        return await user.send(text)
    except Exception as e:
        message = f"{time.time()} > {bot.full_name} > Mod DMs > Failed to send DM to {user} - {type(e).__name__}: {e}"
        general.print_error(message)
        logger.log(bot.name, "moderation", message)


async def send_mod_log(bot: bot_data.Bot, ctx: commands.Context | FakeContext, user: discord.User | discord.Member, author: discord.User | discord.Member,
                       entry_id: int, action: str, reason: str, duration: str = None, original_warning: str = None):
    """ Try to send a mod log message about the punishment """
    try:
        _data = bot.db.fetchrow("SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        data = json.loads(_data["data"])
        mod_logs = data["mod_logs"]
        if action in ["warn", "pardon"]:
            key = "warn"
        elif action in ["mute", "unmute"]:
            key = "mute"
        elif action == "kick":
            key = "kick"
        elif action in ["ban", "unban"]:
            key = "ban"
        elif action == "roles":
            raise ValueError("Roles are not handled by this function")
        else:
            raise ValueError(f"Invalid action {action} specified")
        enabled: int = mod_logs[key]
    except (IndexError, KeyError):
        return  # If the settings can't be read, assume it's disabled
    if not enabled:
        return  # If the value is zero, then it's disabled
    channel: discord.TextChannel = bot.get_channel(enabled)
    language = bot.language(ctx)
    embed = discord.Embed()
    embed.title = language.string(f"mod_logs_{action}")
    colours = {
        "warn": general.yellow,
        "pardon": general.green,
        "mute": general.red2,
        "unmute": general.green,
        "kick": general.red,
        "ban": general.red,
        "unban": general.green2
    }
    embed.colour = colours[action]
    embed.description = language.string("mod_logs_description", punished=user, responsible=author, reason=reason)
    if duration:
        embed.description += language.string("mod_logs_description_duration", duration=duration)
    if action == "pardon":
        embed.description += language.string("mod_logs_description_pardon", original_warning=original_warning)
    embed.set_footer(text=language.string("mod_logs_case", id=entry_id))
    embed.timestamp = time.now()
    try:
        return await general.send(None, channel, embed=embed)
    except Exception as e:
        message = f"{time.time()} > {bot.full_name} > Mod Logs > Case ID {entry_id} - Failed to send message to log channel - {type(e).__name__}: {e}"
        general.print_error(message)
        logger.log(bot.name, "moderation", message)


class Moderation(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        # self.admins = self.bot.config["owners"]

    @commands.command(name="kick")
    @commands.guild_only()
    @commands.check(lambda ctx: ctx.guild.id != 869975256566210641)
    @permissions.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick_user(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        """ Kick a user from the server """
        language = self.bot.language(ctx)
        reason = reason[:400] if reason else language.string("mod_reason_none")
        if member == ctx.author:
            return await general.send(language.string("mod_kick_self"), ctx.channel)
        elif member.id == ctx.guild.owner.id:
            return await general.send(language.string("mod_kick_owner"), ctx.channel)
        elif (member.top_role.position >= ctx.author.top_role.position) and ctx.author != ctx.guild.owner:
            return await general.send(language.string("mod_kick_forbidden"), ctx.channel)
        elif member.id == self.bot.user.id:
            return await general.send(language.string("mod_ban_suager", ctx.author.name), ctx.channel)
        try:
            user = str(member)
            # TODO: Make sure we can kick the user *before* sending the message, so it wouldn't look stupid if this fails...
            await send_mod_dm(self.bot, ctx, member, "kick", reason, None)
            await member.kick(reason=general.reason(ctx.author, reason))
            reason_log = general.reason(ctx.author, reason)
            self.bot.db.execute("UPDATE punishments SET handled=3 WHERE uid=? AND gid=? AND action='mute' AND handled=0 AND bot=?", (member.id, ctx.guild.id, self.bot.name))
            self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (member.id, ctx.guild.id, "kick", ctx.author.id, reason_log, False, time.now2(), 1, self.bot.name))
            entry_id = self.bot.db.db.lastrowid
            await send_mod_log(self.bot, ctx, member, ctx.author, entry_id, "kick", reason_log, None)
            return await general.send(language.string("mod_kick", user, reason), ctx.channel)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="ban")
    @commands.guild_only()
    @commands.check(lambda ctx: ctx.guild.id != 869975256566210641)
    @permissions.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_user(self, ctx: commands.Context, member: MemberID, *, reason: str = None):
        """ Ban a user from the server """
        language = self.bot.language(ctx)
        reason = reason[:400] if reason else language.string("mod_reason_none")
        if member == ctx.author.id:
            return await general.send(language.string("mod_ban_self"), ctx.channel)
        elif member == ctx.guild.owner.id:
            return await general.send(language.string("mod_ban_owner"), ctx.channel)
        elif (them := ctx.guild.get_member(member)) is not None and (them.top_role.position >= ctx.author.top_role.position) and ctx.author != ctx.guild.owner:
            return await general.send(language.string("mod_ban_forbidden"), ctx.channel)
        elif member == self.bot.user.id:
            return await general.send(language.string("mod_ban_suager", ctx.author.name), ctx.channel)
        try:
            # TODO: Make sure we can ban the user *before* sending the message, so it wouldn't look stupid if this fails...
            # TODO: Check if the user is already banned from the server
            user: discord.User = await self.bot.fetch_user(member)
            await send_mod_dm(self.bot, ctx, user, "ban", reason, None)
            await ctx.guild.ban(discord.Object(id=member), reason=general.reason(ctx.author, reason))
            reason_log = general.reason(ctx.author, reason)
            self.bot.db.execute("UPDATE punishments SET handled=3 WHERE uid=? AND gid=? AND action='mute' AND handled=0 AND bot=?", (member, ctx.guild.id, self.bot.name))
            self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (member, ctx.guild.id, "ban", ctx.author.id, reason_log, False, time.now2(), 1, self.bot.name))
            entry_id = self.bot.db.db.lastrowid
            await send_mod_log(self.bot, ctx, user, ctx.author, entry_id, "ban", reason_log, None)
            return await general.send(language.string("mod_ban", member, user, reason), ctx.channel)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="massban")
    @commands.guild_only()
    @commands.check(lambda ctx: ctx.guild.id != 869975256566210641)
    @permissions.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def mass_ban(self, ctx: commands.Context, reason: str, *who: MemberID):
        """ Mass ban users from the server """
        language = self.bot.language(ctx)
        reason = reason[:400] if reason else language.string("mod_reason_none")
        if ctx.author.id in who:
            return await general.send(language.string("mod_ban_self"), ctx.channel)
        else:
            for member in who:
                if member == self.bot.user.id:
                    return await general.send(language.string("mod_ban_suager", ctx.author.name), ctx.channel)
                if member == ctx.guild.owner.id:
                    return await general.send(language.string("mod_ban_owner"), ctx.channel)
                elif (them := ctx.guild.get_member(member)) is not None and (them.top_role.position >= ctx.author.top_role.position) and ctx.author != ctx.guild.owner:
                    return await general.send(language.string("mod_ban_forbidden"), ctx.channel)
        banned = 0
        failed = 0
        for member in who:
            try:
                # TODO: Make sure we can ban the user *before* sending the message, so it wouldn't look stupid if this fails...
                # TODO: Check if the user is already banned from the server
                user: discord.User = await self.bot.fetch_user(member)
                await send_mod_dm(self.bot, ctx, user, "ban", reason, None)
                await ctx.guild.ban(user, reason=general.reason(ctx.author, reason))
                reason_log = general.reason(ctx.author, reason)
                self.bot.db.execute("UPDATE punishments SET handled=3 WHERE uid=? AND gid=? AND action='mute' AND handled=0 AND bot=?", (member, ctx.guild.id, self.bot.name))
                self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                    (member, ctx.guild.id, "ban", ctx.author.id, reason_log, False, time.now2(), 1, self.bot.name))
                entry_id = self.bot.db.db.lastrowid
                await send_mod_log(self.bot, ctx, user, ctx.author, entry_id, "ban", reason_log, None)
                banned += 1
            except Exception as e:
                failed += 1
                await general.send(f"`{member}` - {type(e).__name__}: {e}", ctx.channel)
        total = banned + failed
        return await general.send(language.string("mod_ban_mass", reason, language.number(total), language.number(banned), language.number(failed)), ctx.channel)

    @commands.command(name="unban")
    @commands.guild_only()
    @commands.check(lambda ctx: ctx.guild.id != 869975256566210641)
    @permissions.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban_user(self, ctx: commands.Context, member: MemberID, *, reason: str = None):
        """ Unban a user """
        language = self.bot.language(ctx)
        reason = reason[:400] if reason else language.string("mod_reason_none")
        try:
            await ctx.guild.unban(discord.Object(id=member), reason=general.reason(ctx.author, reason))
            user = await self.bot.fetch_user(member)
            await send_mod_dm(self.bot, ctx, user, "unban", reason, None)
            reason_log = general.reason(ctx.author, reason)
            self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (member, ctx.guild.id, "unban", ctx.author.id, reason_log, False, time.now2(), 1, self.bot.name))
            entry_id = self.bot.db.db.lastrowid
            await send_mod_log(self.bot, ctx, user, ctx.author, entry_id, "unban", reason_log, None)
            return await general.send(language.string("mod_unban", member, user, reason), ctx.channel)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="nickname", aliases=["nick"])
    @commands.guild_only()
    @permissions.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nickname_user(self, ctx: commands.Context, member: discord.Member, *, name: str = None):
        """ Sets a user's nickname """
        language = self.bot.language(ctx)
        try:
            if member.id == ctx.guild.owner.id:
                return await general.send(language.string("mod_nick_owner"), ctx.channel)
            if (member.top_role.position >= ctx.author.top_role.position and member != ctx.author) and ctx.author != ctx.guild.owner:
                return await general.send(language.string("mod_nick_forbidden2"), ctx.channel)
            await member.edit(nick=name, reason=general.reason(ctx.author, "Changed by command"))
            if name is None:
                message = language.string("mod_nick_reset", member)
            else:
                message = language.string("mod_nick", member, name)
            return await general.send(message, ctx.channel)
        except discord.Forbidden:
            return await general.send(language.string("mod_nick_forbidden"), ctx.channel)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="nicknameme", aliases=["nickme", "nameme"])
    @commands.guild_only()
    @permissions.has_permissions(change_nickname=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nickname_self(self, ctx: commands.Context, *, name: str = None):
        """ Change your own nickname """
        language = self.bot.language(ctx)
        try:
            if ctx.author.id == ctx.guild.owner.id:
                return await general.send(language.string("mod_nick_owner"), ctx.channel)
            await ctx.author.edit(nick=name, reason=general.reason(ctx.author, "Changed by command"))
            if name is None:
                message = language.string("mod_nick_self_reset")
            else:
                message = language.string("mod_nick_self", name)
            return await general.send(message, ctx.channel)
        except discord.Forbidden:
            return await general.send(language.string("mod_nick_forbidden"), ctx.channel)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="mute")
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    @commands.bot_has_permissions(manage_roles=True)
    # @commands.check(lambda ctx: ctx.bot.name == "suager")
    async def mute_user(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        """ Mute a user """
        language = self.bot.language(ctx)
        reason = reason[:400] if reason else language.string("mod_reason_none")
        if member.id == self.bot.user.id:
            return await general.send(language.string("mod_mute_suager"), ctx.channel)
        if member == ctx.author:
            return await general.send(language.string("mod_mute_self"), ctx.channel)
        _reason = general.reason(ctx.author, reason)
        _data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not _data:
            return await general.send(language.string("mod_mute_role2", ctx.prefix), ctx.channel)
        data = json.loads(_data["data"])
        try:
            mute_role_id = data["mute_role"]
        except KeyError:
            return await general.send(language.string("mod_mute_role"), ctx.channel)
        mute_role = ctx.guild.get_role(mute_role_id)
        if not mute_role:
            return await general.send(language.string("mod_mute_role"), ctx.channel)
        try:
            await member.add_roles(mute_role, reason=_reason)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)
        out = language.string("mod_mute", member, reason)
        # exists = self.bot.db.fetchrow("SELECT * FROM temporary WHERE uid=? AND gid=? AND bot=? AND type='mute'", (member.id, ctx.guild.id, self.bot.name))
        _duration = reason.split(" ")[0]
        delta = time.interpret_time(_duration)
        expiry, error = time.add_time(delta)
        if time.rd_is_above_5y(delta):
            await general.send(language.string("mod_mute_limit"), ctx.channel, delete_after=15)
            error = True
        if not error:
            # if exists is not None:
            #     self.bot.db.execute("UPDATE temporary SET expiry=? WHERE entry_id=?", (expiry, exists["entry_id"]))
            # else:
            #     random_id = general.random_id()
            #     while self.bot.db.fetchrow("SELECT entry_id FROM temporary WHERE entry_id=?", (random_id,)):
            #         random_id = general.random_id()
            #     self.bot.db.execute("INSERT INTO temporary VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (member.id, "mute", expiry, ctx.guild.id, None, random_id, 0, self.bot.name))

            # Overwrite all older still active mutes as 5 ("Handled Otherwise")
            reason = " ".join(reason.split(" ")[1:])
            reason = reason or language.string("mod_reason_none")
            reason_log = general.reason(ctx.author, reason)
            self.bot.db.execute("UPDATE punishments SET handled=5 WHERE uid=? AND gid=? AND action='mute' AND handled=0 AND bot=?", (member.id, ctx.guild.id, self.bot.name))
            self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (member.id, ctx.guild.id, "mute", ctx.author.id, reason_log, True, expiry, 0, self.bot.name))
            entry_id = self.bot.db.db.lastrowid
            duration = language.delta_rd(delta, accuracy=7, brief=False, affix=False)
            out = language.string("mod_mute_timed", member, duration, reason)
            await send_mod_dm(self.bot, ctx, member, "mute", reason, duration)
            await send_mod_log(self.bot, ctx, member, ctx.author, entry_id, "mute", reason_log, duration)
        else:
            # if exists is not None:
            #     self.bot.db.execute("DELETE FROM temporary WHERE entry_id=?", (exists['entry_id'],))
            reason_log = general.reason(ctx.author, reason)
            self.bot.db.execute("UPDATE punishments SET handled=5 WHERE uid=? AND gid=? AND action='mute' AND handled=0 AND bot=?", (member.id, ctx.guild.id, self.bot.name))
            self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (member.id, ctx.guild.id, "mute", ctx.author.id, reason_log, False, time.now2(), 0, self.bot.name))
            entry_id = self.bot.db.db.lastrowid
            await send_mod_dm(self.bot, ctx, member, "mute", reason, None)
            await send_mod_log(self.bot, ctx, member, ctx.author, entry_id, "mute", reason_log, None)
        return await general.send(out, ctx.channel)

    @commands.command(name="unmute")
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    @commands.bot_has_permissions(manage_roles=True)
    # @commands.check(lambda ctx: ctx.bot.name == "suager")
    async def unmute_user(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        """ Unmute a user """
        language = self.bot.language(ctx)
        reason = reason[:400] if reason else language.string("mod_reason_none")
        if member == ctx.author:
            return await general.send(language.string("mod_unmute_self"), ctx.channel)
            # return await general.send(f"Imagine trying to unmute yourself {emotes.BlobCatPolice}", ctx.channel)
        _reason = general.reason(ctx.author, reason)
        _data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not _data:
            return await general.send(language.string("mod_mute_role2", ctx.prefix), ctx.channel)
            # return await general.send(f"This server does not seem to have a mute role set. Use `{ctx.prefix}settings` to set one.", ctx.channel)
        data = json.loads(_data["data"])
        try:
            mute_role_id = data["mute_role"]
        except KeyError:
            return await general.send(language.string("mod_mute_role"), ctx.channel)
            # return await general.send("This server has no mute role set, or it no longer exists.", ctx.channel)
        mute_role = ctx.guild.get_role(mute_role_id)
        if not mute_role:
            return await general.send(language.string("mod_mute_role"), ctx.channel)
            # return await general.send("This server has no mute role set, or it no longer exists.", ctx.channel)
        if mute_role not in member.roles:
            return await general.send(language.string("mod_unmute_already"), ctx.channel)
        try:
            await member.remove_roles(mute_role, reason=_reason)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)
        # self.bot.db.execute("DELETE FROM temporary WHERE uid=? AND type='mute' AND gid=? AND bot=?", (member.id, ctx.guild.id, self.bot.name))
        reason_log = general.reason(ctx.author, reason)
        self.bot.db.execute("UPDATE punishments SET handled=4 WHERE uid=? AND gid=? AND action='mute' AND handled=0 AND bot=?", (member.id, ctx.guild.id, self.bot.name))
        self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (member.id, ctx.guild.id, "unmute", ctx.author.id, reason_log, False, time.now2(), 1, self.bot.name))
        entry_id = self.bot.db.db.lastrowid
        await send_mod_dm(self.bot, ctx, member, "unmute", reason, None)
        await send_mod_log(self.bot, ctx, member, ctx.author, entry_id, "unmute", reason_log, None)
        return await general.send(language.string("mod_unmute", member, reason), ctx.channel)
        # return await general.send(f"{emotes.Allow} Successfully unmuted **{member}** for **{reason}**", ctx.channel)

    @commands.command(name="mutes", aliases=["punishments"])
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    # @commands.check(lambda ctx: ctx.bot.name == "suager")
    async def mute_list(self, ctx: commands.Context):
        """ See a list of the currently active temporary mutes """
        language = self.bot.language(ctx)
        mutes = self.bot.db.fetch("SELECT * FROM temporary WHERE gid=? AND type='mute' ORDER BY expiry", (ctx.guild.id,))
        if not mutes:
            return await general.send(language.string("mod_mute_list_none", ctx.guild.name), ctx.channel)
        output = language.string("mod_mute_list", ctx.guild.name)
        outputs = []
        _mute = 0
        for mute in mutes:
            _mute += 1
            expiry = mute["expiry"]
            expires_on = language.time(expiry, short=1, dow=False, seconds=True, tz=False)
            expires_in = language.delta_dt(expiry, accuracy=3, brief=False, affix=True)
            who = ctx.guild.get_member(mute["uid"])
            outputs.append(language.string("mod_mute_list_item", language.number(_mute, commas=False), who, expires_on, expires_in))
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
        language = self.bot.language(ctx)
        loop = [f"{i} ({i.id})" for i in ctx.guild.members if search.lower() in i.name.lower()]  # and not i.bot
        await general.pretty_results(ctx, "name", language.string("mod_find", language.number(len(loop)), search), loop)
        # f"Found **{len(loop)}** on your search for **{search}**"

    @find.command(name="nickname", aliases=["nick"])
    async def find_nickname(self, ctx: commands.Context, *, search: str):
        """Finds members whose nickname fits the search string"""
        language = self.bot.language(ctx)
        loop = [f"{i.nick} | {i} ({i.id})" for i in ctx.guild.members if i.nick if (search.lower() in i.nick.lower())]  # and not i.bot
        await general.pretty_results(ctx, "name", language.string("mod_find", language.number(len(loop)), search), loop)

    @find.command(name="discriminator", aliases=["disc"])
    async def find_discriminator(self, ctx: commands.Context, *, search: str):
        """Finds members whose discriminator is the same as the search"""
        language = self.bot.language(ctx)
        if len(search) != 4 or not re.compile("^[0-9]*$").search(search):
            return await general.send(language.string("mod_find_disc"), ctx.channel)
        loop = [f"{i} ({i.id})" for i in ctx.guild.members if search == i.discriminator]
        await general.pretty_results(ctx, "discriminator", language.string("mod_find", language.number(len(loop)), search), loop)

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
            return await general.send(self.bot.language(ctx).string("mod_purge_user"), ctx.channel)
        await do_removal(ctx, search, lambda e: e.author == user)

    @prune.command(name="contains")
    async def prune_contains(self, ctx: commands.Context, substring: str = None, search: int = 100):
        """Removes all messages containing a substring.
        The substring must be at least 3 characters long."""
        if substring is None or len(substring) < 3:
            return await general.send(self.bot.language(ctx).string("mod_purge_substring"), ctx.channel)
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
        language = self.bot.language(ctx)
        if search > 2000:
            return await general.send(language.string("mod_purge_max", language.number(search)), ctx.channel)
            # return await ctx.send(f'Too many messages to search for ({search:,}/2000)')
        total_reactions = 0
        async for message in ctx.history(limit=search, before=ctx.message):
            if len(message.reactions):
                total_reactions += sum(r.count for r in message.reactions)
                await message.clear_reactions()
        return await general.send(language.string("mod_purge_reactions", language.number(total_reactions)), ctx.channel)
        # await general.send(f"🚮 Successfully removed {total_reactions:,} reactions.", ctx.channel)


class ModerationKyomi(Moderation, name="Moderation"):
    designs = [
        "<nick> // 32",
        "✧🌙<nick>🍰⊹˚ // 27",
        "✧🍓❏<nick>🍰₊˚⊹ // 25",
        "✎🍪✦<nick>🍦୨୧ // 26",
        "✎🥮<nick>🍯✦꒦︶ // 26",
        "☆🧁୨୧<nick>🍦‧₊˚. // 23",
        "✧₊˚🍰⌇<nick>🌙⋆｡˚ // 23",
        "⁀➷✧🔮<nick>🌙✦ˎˊ˗ // 23",
        "⁀➷✦🔮⌇<nick>🍩ˎˊ˗ // 23",
        "✰🍯ꔫ<nick>🥞✦ // 27",
        "╭╯🍩⁺˖˚<nick>🍦୨୧ // 23"
    ]

    @commands.command(name="nickname", aliases=["nick"])
    @commands.guild_only()
    @permissions.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nickname_user(self, ctx: commands.Context, member: discord.Member, design: int, *, name: str = None):
        """ Sets a user's nickname """
        language = self.bot.language(ctx)
        try:
            if member.id == ctx.guild.owner.id:
                return await general.send(language.string("mod_nick_owner"), ctx.channel)
            if (member.top_role.position >= ctx.author.top_role.position and member != ctx.author) and ctx.author != ctx.guild.owner:
                return await general.send(language.string("mod_nick_forbidden2"), ctx.channel)
            name = name or member.name
            _design, length = self.designs[design - 1].split(" // ")
            name = _design.replace('<nick>', name[:int(length)])
            await member.edit(nick=name, reason=general.reason(ctx.author, "Changed by command"))
            message = language.string("mod_nick", member, name)
            return await general.send(message, ctx.channel)
        except discord.Forbidden:
            return await general.send(language.string("mod_nick_forbidden"), ctx.channel)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="nicknameme", aliases=["nickme", "nameme"])
    @commands.guild_only()
    @permissions.has_permissions(change_nickname=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nickname_self(self, ctx: commands.Context, design: int, *, name: str = None):
        """ Change your own nickname """
        language = self.bot.language(ctx)
        try:
            if ctx.author.id == ctx.guild.owner.id:
                return await general.send(language.string("mod_nick_owner"), ctx.channel)
            name = name or ctx.author.name
            _design, length = self.designs[design - 1].split(" // ")
            name = _design.replace('<nick>', name[:int(length)])
            await ctx.author.edit(nick=name, reason=general.reason(ctx.author, "Changed by command"))
            message = language.string("mod_nick_self", name)
            return await general.send(message, ctx.channel)
        except IndexError:
            return await general.send(f"Nickname design {design} is not available.", ctx.channel)
        except discord.Forbidden:
            return await general.send(language.string("mod_nick_forbidden"), ctx.channel)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="nicknamedesign", aliases=["nickdesign", "design"])
    @commands.guild_only()
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nickname_design(self, ctx: commands.Context, design: int):
        """ Change your nickname design
        Example: `m!nickdesign 7`"""
        language = self.bot.language(ctx)
        try:
            if ctx.author.id == ctx.guild.owner.id:
                return await general.send(language.string("mod_nick_owner"), ctx.channel)
            _design, length = self.designs[design - 1].split(" // ")
            name = _design.replace('<nick>', ctx.author.name[:int(length)])
            await ctx.author.edit(nick=name, reason=general.reason(ctx.author, "Changed by command"))
            message = language.string("mod_nick_self", name)
            return await general.send(message, ctx.channel)
        except IndexError:
            return await general.send(f"Nickname design {design} is not available.", ctx.channel)
        except discord.Forbidden:
            return await general.send(language.string("mod_nick_forbidden"), ctx.channel)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="nicknamedesigns", aliases=["nickdesigns", "designs"])
    async def nickname_designs(self, ctx: commands.Context):
        """ See all nickname designs in the server """
        # await ctx.send(str([32 - (len(x) - 6) for x in self.designs]))
        output = "Here are the designs available in Midnight Dessert:\n\n"
        for i, _design in enumerate(self.designs, start=1):
            design, length = _design.split(" // ")
            output += f"{i}) {design.replace('<nick>', ctx.author.name[:int(length)])}\n"
        output += "\nUse `m!nickdesigns` to see the nicknames applied to your username\n" \
                  "\nUse `m!nickdesign <design_number>` to apply a design to your name\n" \
                  "  - Note: This command will use your username (and therefore reset any nickname you have)\n" \
                  "  - If you want to have a nickname, use `m!nickme`\n" \
                  "  - Example: `m!nickdesign 7`\n" \
                  "\nUse `m!nickme <design_number> <nickname>` to apply a design to a nickname of your choice\n" \
                  "  - Note: Requires permission to change your nickname\n" \
                  f"  - Example: `m!nickme 7 {ctx.author.name}`\n" \
                  "\nNote: If you boost this server, you will get a special nickname design. It is not included here, " \
                  "so if you change it, only the admins will be able to change it back.\n" \
                  "\nWarning: these designs are NF2U, you may not copy these for your own servers."
        return await general.send(output, ctx.channel)


def setup(bot: bot_data.Bot):
    if bot.name == "kyomi":
        bot.add_cog(ModerationKyomi(bot))
    else:
        bot.add_cog(Moderation(bot))
