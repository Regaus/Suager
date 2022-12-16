from __future__ import annotations

import json
import re
from io import BytesIO
from typing import Literal, Union

import discord

from utils import bot_data, commands, general, logger, permissions, settings, time
from utils.languages import Language


async def do_removal(ctx: commands.Context, limit: int, predicate, *, before: int = None, after: int = None, message: bool = True):
    language = ctx.bot.language(ctx)
    if limit > 2000:
        return await ctx.send(language.string("mod_purge_max", given=limit))
        # return await general.send(f"Too many messages to search given ({limit:,}/2,000)", ctx.channel)
    if before is None:
        before = ctx.message
    else:
        before = discord.Object(id=before)
    if after is not None:
        after = discord.Object(id=after)
    _message = None  # if message = False
    if message is True:
        _message = await ctx.send(language.string("mod_purge_loading"))
    try:
        deleted = await ctx.channel.purge(limit=limit, before=before, after=after, check=predicate)
    except discord.Forbidden:
        return await ctx.send(language.string("mod_purge_forbidden"))
        # return await general.send("I don't have the permissions to delete messages", ctx.channel)
    # except discord.HTTPException as e:
    except Exception as e:
        return await ctx.send(language.string("mod_purge_error", err=f"{type(e).__name__}: {str(e)}"))
        # return await general.send(f"An error has occurred: `{type(e).__name__}: {e}`\nTry a smaller search?", ctx.channel)
    _deleted = len(deleted)
    if message is True:
        await _message.delete()
        return await ctx.send(language.string("mod_purge", total=language.number(_deleted)), delete_after=10)
        # await general.send(f"🚮 Successfully removed {_deleted:,} messages", ctx.channel, delete_after=10)


async def send_mod_dm(bot: bot_data.Bot, ctx: commands.Context | commands.FakeContext, user: discord.User | discord.Member,
                      action: str, reason: str, duration: str = None, auto: bool = False, original_warning: str = None):
    """ Try to send the user a DM that they've been warned/muted/kicked/banned """
    try:
        _data = bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, bot.name))
        if not _data:
            return  # No data found means disabled
        data = json.loads(_data["data"])
        mod_dms = data["mod_dms"]
        if action in ["warn", "pardon"]:
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
        if original_warning is not None:
            # When a warning is pardoned manually, it will show the original warning as `[ID] Warning text`
            text = language.string("mod_dms_pardon", server=ctx.guild, reason=reason, original_warning=original_warning)
        else:
            # If no "original warning" is provided, that is treated as all warnings being pardoned
            text = language.string("mod_dms_pardon_all", server=ctx.guild, reason=reason)
    elif action == "mute" and auto:  # This happens if the person reached enough warnings
        # The "reason" parameter will carry the amount of warnings reached as a prepared string
        if duration is None:
            text = language.string("mod_dms_warn_muted2", server=ctx.guild, warnings=reason)
        else:
            text = language.string("mod_dms_warn_muted", server=ctx.guild, warnings=reason, duration=duration)
    elif action == "warn" and duration is not None:
        text = language.string("mod_dms_warn_temp", server=ctx.guild, reason=reason, duration=duration)
    elif action == "mute" and duration is not None:
        text = language.string("mod_dms_mute_temp", server=ctx.guild, reason=reason, duration=duration)  # The duration is already converted into str by the mute command
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
        logger.log(bot.name, "errors", message)


async def send_mod_log(bot: bot_data.Bot, ctx: commands.Context | commands.FakeContext, user: discord.User | discord.Member, author: discord.User | discord.Member | discord.ClientUser,
                       entry_id: int, action: str, reason: str, duration: str = None, original_warning: str = None):
    """ Try to send a mod log message about the punishment """
    try:
        _data = bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, bot.name))
        if not _data:
            return  # No data found means disabled
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
    channel = bot.get_channel(enabled)
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
    punished = f"{user} ({user.id})"
    responsible = f"{author} ({author.id})"
    embed.description = language.string("mod_logs_description", punished=punished, responsible=responsible, reason=reason)
    if duration:
        embed.description += language.string("mod_logs_description_duration", duration=duration)
    if action == "pardon":
        if original_warning is not None:
            # When a warning is pardoned manually, it will show the original warning as `[ID] Warning text`
            embed.description += language.string("mod_logs_description_pardon", original_warning=original_warning)
        else:
            # If no "original warning" is provided, that is treated as all warnings being pardoned
            embed.title = language.string("mod_logs_pardon_all")
    embed.set_footer(text=language.string("mod_logs_case", id=entry_id))
    embed.timestamp = time.now()
    try:
        return await channel.send(embed=embed)
    except Exception as e:
        message = f"{time.time()} > {bot.full_name} > Mod Logs > Case ID {entry_id} - Failed to send message to log channel - {type(e).__name__}: {e}"
        general.print_error(message)
        logger.log(bot.name, "moderation", message)
        logger.log(bot.name, "errors", message)


class Moderation(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        # self.admins = self.bot.config["owners"]

        # Regex for a discord invite link
        self.discord_link = re.compile(r"(https://discord\.gg/\S+)|(https://discord(?:app)?\.com/invite/\S+)")

        # Formats for images and videos, that are allowed to be used in image-only channels
        # I might adjust this as time goes on, if we find file formats that might not be as popular but still images/videos
        self.image_formats = ["jpg", "jpeg", "jfif", "png", "gif", "webp", "tiff", "psd", "pdn",
                              "mp4", "mov", "wmv", "avi", "flv", "mkv", "webm"]
        self.image_link = re.compile(r"https?://\S+")
        self.exceptions = ["https://tenor.com/", "https://imgur.com/", "https://youtu.be/", "https://www.youtube.com/watch?"]

    @commands.Cog.listener(name="on_message")
    async def on_message(self, ctx: discord.Message):
        """ This event will be used for auto-moderation features, unless I decide to split them in the future """
        if ctx.author.bot:  # Ignore bots for image-only and anti-ads... I don't think bots would be sending discord links anyways
            return
        if self.bot.name in ["suager", "kyomi"]:
            # Load settings json
            _data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
            if not _data:
                return  # No data found means disabled
            data = json.loads(_data["data"])

            # Image-only channels
            # Note: With this implementation, it does not prevent bot commands from being run in such channels, although the input would still get deleted.
            # The only way to fix that would be to run this check before the message is scanned for commands in bot_data
            async def do_image_only():
                image_only = data["image_only"]
                if ctx.channel.id in image_only["channels"]:
                    valid = False
                    # Scan if either there is a valid image file, or if there is a valid image link
                    if ctx.attachments:
                        # Bitwise or: change to True if valid, else keep at current value
                        valid |= any(any(att.filename.endswith(ext) for ext in self.image_formats) for att in ctx.attachments)
                    if links := re.findall(self.image_link, ctx.content):  # If there are any links present
                        valid |= any((any(link.endswith(ext) for ext in self.image_formats) or any(link.startswith(exc) for exc in self.exceptions)) for link in links)

                    if not valid:
                        try:
                            await ctx.delete()
                            await ctx.channel.send("This channel is image-only. No valid image file or link was found.", delete_after=10)
                        except (discord.Forbidden, discord.HTTPException):
                            if permissions.can_send(ctx):
                                await ctx.reply("This message does not contain a valid image file, but I seem to be unable to delete it...")
                # If the channel doesn't qualify for image-only, do nothing and go to the next section

            if "image_only" in data:
                try:
                    await do_image_only()
                except Exception as e:
                    general.log_error(self.bot, f"{time.time()} > {self.bot.full_name} > Moderation > Image-only channels > {type(e).__name__}: {str(e)}")
                    # print(general.traceback_maker(e, code_block=False))

            # Anti-ads
            async def do_anti_ads():
                anti_ads = data["anti_ads"]
                if not anti_ads["enabled"]:
                    return
                # Channel is in whitelist or channel is not in blacklist
                channel_valid = (anti_ads["whitelist"] and ctx.channel.id in anti_ads["channels"]) or (not anti_ads["whitelist"] and ctx.channel.id not in anti_ads["channels"])
                if not channel_valid:
                    return
                matches = re.findall(self.discord_link, ctx.content)
                if matches:
                    message = None   # Just have this so the IDE doesn't complain, but this shouldn't ever be None.
                    try:
                        await ctx.delete()
                        message = await ctx.channel.send(f"{ctx.author.mention} It would be preferable if you don't advertise here...", delete_after=20)
                    except (discord.Forbidden, discord.HTTPException):
                        if permissions.can_send(ctx):
                            message = await ctx.reply("This message contains an advertisement, but I seem to be unable to delete it...")

                    # Now we will try to warn the person
                    # Generate a context from our response message, just so that the author is set to us
                    response_ctx: commands.Context = await self.bot.get_context(message, cls=commands.Context)  # type: ignore
                    language = response_ctx.language()
                    warn_settings, missing = self.get_warn_settings(response_ctx, language)
                    if missing:
                        await ctx.send(missing)

                    _, delta, expiry, error = await self.get_duration(response_ctx, anti_ads.get("warning", ""), language)
                    reason = "[Automatic] Advertising"
                    # We don't need to clutter the chat with the statement that the person has been muted, that should be obvious enough to begin with
                    if not error:
                        duration = language.delta_rd(delta, accuracy=7, brief=False, affix=False, case="for")
                        # out = language.string("mod_warn_timed", user=ctx.author, duration=duration, reason=reason)
                        await self.warn_user(response_ctx, ctx.author, warn_settings, reason, language, expiry, duration)
                    else:
                        # out = language.string("mod_warn", user=ctx.author, reason=reason)
                        await self.warn_user(response_ctx, ctx.author, warn_settings, reason, language, None, None)

            if "anti_ads" in data:
                try:
                    await do_anti_ads()
                except Exception as e:
                    general.log_error(self.bot, f"{time.time()} > {self.bot.full_name} > Moderation > Anti-ads > {type(e).__name__}: {str(e)}")

    def kick_check(self, ctx: commands.Context, member: discord.Member, language: Language):
        if member == ctx.author:
            return language.string("mod_kick_self")
        elif member.id == ctx.guild.owner.id:
            return language.string("mod_kick_owner")
        elif (member.top_role.position >= ctx.author.top_role.position) and ctx.author != ctx.guild.owner:
            return language.string("mod_kick_forbidden", member=member)
        elif member.top_role.position >= ctx.guild.me.top_role.position:  # The bot can't bypass this unless it's the guild owner, which is unlikely
            return language.string("mod_kick_forbidden2", member=member)
        elif member.id == self.bot.user.id:
            return language.string("mod_ban_suager", author=ctx.author.name)
        return True

    async def kick_user(self, ctx: commands.Context, member: discord.Member, reason: str):
        await send_mod_dm(self.bot, ctx, member, "kick", reason, None)
        await member.kick(reason=general.reason(ctx.author, reason))
        self.bot.db.execute("UPDATE punishments SET handled=3 WHERE uid=? AND gid=? AND action='mute' AND handled=0 AND bot=?", (member.id, ctx.guild.id, self.bot.name))
        self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (member.id, ctx.guild.id, "kick", ctx.author.id, reason, False, time.now2(), 1, self.bot.name))
        entry_id = self.bot.db.db.lastrowid
        await send_mod_log(self.bot, ctx, member, ctx.author, entry_id, "kick", reason, None)

    @commands.command(name="kick")
    @commands.guild_only()
    @commands.check(lambda ctx: ctx.guild.id != 869975256566210641)
    @permissions.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        """ Kick a user from the server """
        language = self.bot.language(ctx)
        reason = reason[:400] if reason else language.string("mod_reason_none")
        try:
            kick_check = self.kick_check(ctx, member, language)
            if kick_check is not True:
                return await ctx.send(kick_check)
            await self.kick_user(ctx, member, reason)
            return await ctx.send(language.string("mod_kick", user=member, reason=reason))
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")

    @commands.command(name="masskick")
    @commands.guild_only()
    @commands.check(lambda ctx: ctx.guild.id != 869975256566210641)
    @permissions.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def mass_kick(self, ctx: commands.Context, members: commands.Greedy[commands.MemberID], *, reason: str = None):
        """ Mass kick users from the server """
        language = self.bot.language(ctx)
        reason = reason[:400] if reason else language.string("mod_reason_none")
        kicked = 0
        failed = 0
        for member_id in members:
            success = False
            try:
                member: discord.Member = ctx.guild.get_member(member_id)  # type: ignore
                if member is None:
                    await ctx.send(language.string("mod_kick_none", id=member_id))
                    continue
                kick_check = self.kick_check(ctx, member, language)
                if kick_check is not True:
                    return await ctx.send(kick_check)
                await self.kick_user(ctx, member, reason)
                kicked += 1
                success = True
            except Exception as e:
                await ctx.send(f"`{member_id}` - {type(e).__name__}: {e}")
            finally:
                if not success:
                    failed += 1
        total = kicked + failed
        if failed:
            output = language.string("mod_kick_mass2", reason=reason, total=language.number(total), banned=language.number(kicked), failed=language.number(failed))
        else:
            output = language.string("mod_kick_mass", reason=reason, total=language.number(total))
        return await ctx.send(output)

    def ban_check(self, ctx: commands.Context, user: commands.MemberID, language: Language):
        member = ctx.guild.get_member(user)  # type: ignore
        if user == ctx.author.id:
            return language.string("mod_ban_self")
        elif user == ctx.guild.owner.id:
            return language.string("mod_ban_owner")
        elif member is not None and (member.top_role.position >= ctx.author.top_role.position) and ctx.author != ctx.guild.owner:
            return language.string("mod_ban_forbidden", member=member)
        elif member is not None and (member.top_role.position >= ctx.guild.me.top_role.position):  # The bot can't bypass this unless it's the guild owner, which is unlikely
            return language.string("mod_ban_forbidden2", member=member)
        elif user == self.bot.user.id:
            return language.string("mod_ban_suager", author=ctx.author.name)
        return True

    @staticmethod
    async def is_already_banned(ctx: commands.Context, user: discord.User):
        try:
            await ctx.guild.fetch_ban(user)
            return True
        except discord.NotFound:
            return False

    async def ban_user(self, ctx: commands.Context, user: discord.User, reason: str):
        await send_mod_dm(self.bot, ctx, user, "ban", reason, None)
        await ctx.guild.ban(user, reason=general.reason(ctx.author, reason))
        self.bot.db.execute("UPDATE punishments SET handled=3 WHERE uid=? AND gid=? AND action='mute' AND handled=0 AND bot=?", (user.id, ctx.guild.id, self.bot.name))
        self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (user.id, ctx.guild.id, "ban", ctx.author.id, reason, False, time.now2(), 1, self.bot.name))
        entry_id = self.bot.db.db.lastrowid
        await send_mod_log(self.bot, ctx, user, ctx.author, entry_id, "ban", reason, None)

    @commands.command(name="ban")
    @commands.guild_only()
    @commands.check(lambda ctx: ctx.guild.id != 869975256566210641)
    @permissions.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: commands.MemberID, *, reason: str = None):
        """ Ban a user from the server """
        language = ctx.language()
        reason = reason[:400] if reason else language.string("mod_reason_none")
        try:
            ban_check = self.ban_check(ctx, member, language)
            if ban_check is not True:
                return await ctx.send(ban_check)
            user: discord.User = await self.bot.fetch_user(member)  # type: ignore
            if user is None:
                return await ctx.send(language.string("mod_ban_none", id=member))
            if await self.is_already_banned(ctx, user):
                return await ctx.send(language.string("mod_ban_already", member=user))
            await self.ban_user(ctx, user, reason)
            return await ctx.send(language.string("mod_ban", user=member, id=user, reason=reason))
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")

    @commands.command(name="massban")
    @commands.guild_only()
    @commands.check(lambda ctx: ctx.guild.id != 869975256566210641)
    @permissions.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def mass_ban(self, ctx: commands.Context, members: commands.Greedy[commands.MemberID], *, reason: str = None):
        """ Mass ban users from the server """
        language = self.bot.language(ctx)
        reason = reason[:400] if reason else language.string("mod_reason_none")
        if ctx.author.id in members:
            return await ctx.send(language.string("mod_ban_self"))
        else:
            banned = 0
            failed = 0
            for member in members:
                success = False
                try:
                    ban_check = self.ban_check(ctx, member, language)
                    if ban_check is not True:
                        await ctx.send(ban_check)
                        continue
                    user: discord.User = await self.bot.fetch_user(member)  # type: ignore
                    if user is None:
                        await ctx.send(language.string("mod_ban_none", id=member))
                        continue
                    if await self.is_already_banned(ctx, user):
                        await ctx.send(language.string("mod_ban_already", member=user))
                        continue
                    await self.ban_user(ctx, user, reason)
                    banned += 1
                    success = True
                except Exception as e:
                    await ctx.send(f"`{member}` - {type(e).__name__}: {e}")
                finally:
                    if not success:
                        failed += 1
        total = banned + failed
        if failed:
            output = language.string("mod_ban_mass2", reason=reason, total=language.number(total), banned=language.number(banned), failed=language.number(failed))
        else:
            output = language.string("mod_ban_mass", reason=reason, total=language.number(total))
        return await ctx.send(output)

    async def unban_user(self, ctx: commands.Context, user: discord.User, reason: str):
        await ctx.guild.unban(user, reason=general.reason(ctx.author, reason))
        await send_mod_dm(self.bot, ctx, user, "unban", reason, None)
        self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (user.id, ctx.guild.id, "unban", ctx.author.id, reason, False, time.now2(), 1, self.bot.name))
        entry_id = self.bot.db.db.lastrowid
        await send_mod_log(self.bot, ctx, user, ctx.author, entry_id, "unban", reason, None)

    @commands.command(name="unban")
    @commands.guild_only()
    @commands.check(lambda ctx: ctx.guild.id != 869975256566210641)
    @permissions.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, member: commands.MemberID, *, reason: str = None):
        """ Unban a user """
        language = self.bot.language(ctx)
        reason = reason[:400] if reason else language.string("mod_reason_none")
        try:
            user = await self.bot.fetch_user(member)  # type: ignore
            if user is None:
                return await ctx.send(language.string("mod_ban_none", id=member))
            if not await self.is_already_banned(ctx, user):
                return await ctx.send(language.string("mod_unban_already", member=user))
            await self.unban_user(ctx, user, reason)
            return await ctx.send(language.string("mod_unban", user=member, id=user, reason=reason))
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")

    @commands.command(name="massunban")
    @commands.guild_only()
    @commands.check(lambda ctx: ctx.guild.id != 869975256566210641)
    @permissions.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def mass_unban(self, ctx: commands.Context, members: commands.Greedy[commands.MemberID], *, reason: str = None):
        """ Mass unban users from the server """
        language = self.bot.language(ctx)
        reason = reason[:400] if reason else language.string("mod_reason_none")
        banned = 0
        failed = 0
        for member in members:
            success = False
            try:
                user: discord.User = await self.bot.fetch_user(member)  # type: ignore
                if user is None:
                    await ctx.send(language.string("mod_ban_none", id=member))
                    continue
                if not await self.is_already_banned(ctx, user):
                    await ctx.send(language.string("mod_unban_already", member=user))
                    continue
                await self.unban_user(ctx, user, reason)
                banned += 1
                success = True
            except Exception as e:
                await ctx.send(f"`{member}` - {type(e).__name__}: {e}")
            finally:
                if not success:
                    failed += 1
        total = banned + failed
        if failed:
            output = language.string("mod_unban_mass2", reason=reason, total=language.number(total), banned=language.number(banned), failed=language.number(failed))
        else:
            output = language.string("mod_unban_mass", reason=reason, total=language.number(total))
        return await ctx.send(output)

    def mute_role(self, ctx: commands.Context, language: Language):
        _data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if not _data:
            return language.string("mod_mute_role2", p=ctx.prefix)
        data = json.loads(_data["data"])
        try:
            mute_role_id = data["mute_role"]
        except KeyError:
            return language.string("mod_mute_role")
        mute_role = ctx.guild.get_role(mute_role_id)
        if not mute_role:
            return language.string("mod_mute_role")
        return mute_role

    def mute_check(self, ctx: commands.Context, member: discord.Member, language: Language):
        if member.id == ctx.author.id:
            return language.string("mod_mute_self")
        elif member.id == self.bot.user.id:
            return language.string("mod_mute_suager")
        return True

    @staticmethod
    async def get_duration(ctx: commands.Context, reason: str, language: Language):
        reason = reason[:400] if reason else language.string("mod_reason_none")
        _duration = reason.split(" ")[0]
        delta = time.interpret_time(_duration)
        expiry, error = time.add_time(delta)
        if time.rd_is_above_5y(delta):
            await ctx.send(language.string("mod_mute_limit"), delete_after=15)
            error = True
        return reason, delta, expiry, error

    async def mute_user_generic(self, ctx: commands.Context, member: discord.Member, mute_role: discord.Role, reason: str):
        try:
            await member.add_roles(mute_role, reason=reason)
        except Exception as e:
            await ctx.send(ctx.language().string("mod_mute_error", error=f"{type(e).__name__}: {e}"))
            raise e
        # Overwrite all older still active mutes as 5 ("Handled Otherwise")
        self.bot.db.execute("UPDATE punishments SET handled=5 WHERE uid=? AND gid=? AND action='mute' AND handled=0 AND bot=?", (member.id, ctx.guild.id, self.bot.name))

    async def mute_user_temporary(self, ctx: commands.Context, member: discord.Member, mute_role: discord.Role, reason: str, expiry: time.datetime, duration: str):
        await self.mute_user_generic(ctx, member, mute_role, general.reason(ctx.author, reason))
        self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (member.id, ctx.guild.id, "mute", ctx.author.id, reason, True, expiry, 0, self.bot.name))
        entry_id = self.bot.db.db.lastrowid
        await send_mod_dm(self.bot, ctx, member, "mute", reason, duration)
        await send_mod_log(self.bot, ctx, member, ctx.author, entry_id, "mute", reason, duration)

    async def mute_user_permanent(self, ctx: commands.Context, member: discord.Member, mute_role: discord.Role, reason: str):
        await self.mute_user_generic(ctx, member, mute_role, general.reason(ctx.author, reason))
        self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (member.id, ctx.guild.id, "mute", ctx.author.id, reason, False, time.now2(), 0, self.bot.name))
        entry_id = self.bot.db.db.lastrowid
        await send_mod_dm(self.bot, ctx, member, "mute", reason, None)
        await send_mod_log(self.bot, ctx, member, ctx.author, entry_id, "mute", reason, None)

    @commands.command(name="mute")
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def mute(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        """ Mute someone

        You can specify the duration of the mute before the reason
        `//mute @someone 7d This will be a temporary mute`
        `//mute @someone This will be a permanent mute`"""
        language = self.bot.language(ctx)
        mute_role = self.mute_role(ctx, language)
        if not isinstance(mute_role, discord.Role):
            return await ctx.send(mute_role)
        mute_check = self.mute_check(ctx, member, language)
        if mute_check is not True:
            return await ctx.send(mute_check)
        reason, delta, expiry, error = await self.get_duration(ctx, reason, language)
        if not error:
            reason = " ".join(reason.split(" ")[1:])
            reason = reason or language.string("mod_reason_none")
            duration = language.delta_rd(delta, accuracy=7, brief=False, affix=False, case="for")
            out = language.string("mod_mute_timed", user=member, duration=duration, reason=reason)
            await self.mute_user_temporary(ctx, member, mute_role, reason, expiry, duration)
        else:
            out = language.string("mod_mute", user=member, reason=reason)
            await self.mute_user_permanent(ctx, member, mute_role, reason)
        return await ctx.send(out)

    @commands.command(name="massmute")
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def mass_mute(self, ctx: commands.Context, members: commands.Greedy[commands.MemberID], *, reason: str = None):
        """ Mass-mute multiple members """
        language = self.bot.language(ctx)
        mute_role = self.mute_role(ctx, language)
        if not isinstance(mute_role, discord.Role):
            return await ctx.send(mute_role)
        reason, delta, expiry, error = await self.get_duration(ctx, reason, language)
        duration = None
        if not error:
            reason = " ".join(reason.split(" ")[1:])
            reason = reason or language.string("mod_reason_none")
            duration = language.delta_rd(delta, accuracy=7, brief=False, affix=False, case="for")
        muted, failed = 0, 0
        for member_id in members:
            success = False
            try:
                member: discord.Member = ctx.guild.get_member(member_id)  # type: ignore
                if member is None:
                    await ctx.send(language.string("mod_kick_none", id=member_id))
                    continue
                mute_check = self.mute_check(ctx, member, language)
                if mute_check is not True:
                    await ctx.send(mute_check)
                    continue
                if not error:
                    await self.mute_user_temporary(ctx, member, mute_role, reason, expiry, duration)
                else:
                    await self.mute_user_permanent(ctx, member, mute_role, reason)
                muted += 1
                success = True
            except Exception as e:
                await ctx.send(f"`{member_id}` - {type(e).__name__}: {e}")
            finally:
                if not success:
                    failed += 1
        total = muted + failed
        timed = "_timed" if not error else ""
        if failed:
            output = language.string("mod_mute_mass2" + timed, reason=reason, total=language.number(total), banned=language.number(muted), failed=language.number(failed), duration=duration)
        else:
            output = language.string("mod_mute_mass" + timed, reason=reason, total=language.number(total), duration=duration)
        return await ctx.send(output)

    @staticmethod
    def unmute_check(ctx: commands.Context, member: discord.Member, mute_role: discord.Role, language: Language):
        if member.id == ctx.author.id:
            return language.string("mod_unmute_self")
        if mute_role not in member.roles:
            return language.string("mod_unmute_already")
        return True

    async def unmute_user(self, ctx: commands.Context, member: discord.Member, mute_role: discord.Role, reason: str):
        try:
            await member.remove_roles(mute_role, reason=general.reason(ctx.author, reason))
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")
        self.bot.db.execute("UPDATE punishments SET handled=4 WHERE uid=? AND gid=? AND action='mute' AND handled=0 AND bot=?", (member.id, ctx.guild.id, self.bot.name))
        self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (member.id, ctx.guild.id, "unmute", ctx.author.id, reason, False, time.now2(), 1, self.bot.name))
        entry_id = self.bot.db.db.lastrowid
        await send_mod_dm(self.bot, ctx, member, "unmute", reason, None)
        await send_mod_log(self.bot, ctx, member, ctx.author, entry_id, "unmute", reason, None)

    @commands.command(name="unmute")
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def unmute(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        """ Unmute someone """
        language = self.bot.language(ctx)
        reason = reason[:400] if reason else language.string("mod_reason_none")
        mute_role = self.mute_role(ctx, language)
        if not isinstance(mute_role, discord.Role):
            return await ctx.send(mute_role)
        mute_check = self.unmute_check(ctx, member, mute_role, language)
        if mute_check is not True:
            return await ctx.send(mute_check)
        await self.unmute_user(ctx, member, mute_role, reason)
        return await ctx.send(language.string("mod_unmute", user=member, reason=reason))

    @commands.command(name="massunmute")
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def mass_unmute(self, ctx: commands.Context, members: commands.Greedy[commands.MemberID], *, reason: str = None):
        """ Mass-unmute multiple members """
        language = self.bot.language(ctx)
        reason = reason[:400] if reason else language.string("mod_reason_none")
        mute_role = self.mute_role(ctx, language)
        if not isinstance(mute_role, discord.Role):
            return await ctx.send(mute_role)
        muted, failed = 0, 0
        for member_id in members:
            success = False
            try:
                member: discord.Member = ctx.guild.get_member(member_id)  # type: ignore
                if member is None:
                    await ctx.send(language.string("mod_kick_none", id=member_id))
                    continue
                mute_check = self.unmute_check(ctx, member, mute_role, language)
                if mute_check is not True:
                    await ctx.send(mute_check)
                    continue
                await self.unmute_user(ctx, member, mute_role, reason)
                muted += 1
                success = True
            except Exception as e:
                await ctx.send(f"`{member_id}` - {type(e).__name__}: {e}")
            finally:
                if not success:
                    failed += 1
        total = muted + failed
        if failed:
            output = language.string("mod_unmute_mass2", reason=reason, total=language.number(total), banned=language.number(muted), failed=language.number(failed))
        else:
            output = language.string("mod_unmute_mass", reason=reason, total=language.number(total))
        return await ctx.send(output)

    @commands.command(name="mutes")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    async def mute_list(self, ctx: commands.Context):
        """ See a list of the currently active mutes """
        language = self.bot.language(ctx)

        # This also has the side effect of showing active permanent mutes first, as their "expiry" value is set to the time the mute was issued, which is in the past.
        mutes = self.bot.db.fetch("SELECT * FROM punishments WHERE gid=? AND action='mute' AND handled=0 ORDER BY expiry", (ctx.guild.id,))
        if not mutes:
            return await ctx.send(language.string("mod_mute_list_none", server=ctx.guild.name))
        output = language.string("mod_mute_list", server=ctx.guild.name)
        outputs = []
        _mute = 0
        for mute in mutes:
            _mute += 1
            who = ctx.guild.get_member(mute["uid"])
            expiry = mute["expiry"]
            i = language.number(_mute, commas=False)
            case_id = language.number(mute["id"], commas=False)
            if mute["temp"]:
                expires_on = language.time(expiry, short=1, dow=False, seconds=True, tz=True, at=True, uid=ctx.author.id)
                expires_in = language.delta_dt(expiry, accuracy=3, brief=False, affix=True)
                outputs.append(language.string("mod_mute_list_item", i=i, id=case_id, who=who, time=expires_on, delta=expires_in))
            else:
                delta = language.delta_dt(expiry, accuracy=3, brief=False, affix=False, case="for")
                outputs.append(language.string("mod_mute_list_item2", i=i, id=case_id, who=who, delta=delta))
        output2 = "\n\n".join(outputs)
        if len(output2) > 1900:
            _data = BytesIO(str(output2).encode('utf-8'))
            return await ctx.send(output, file=discord.File(_data, filename=time.file_ts('Mutes')))
        else:
            return await ctx.send(f"{output}\n{output2}")

    @property
    def settings_template(self) -> dict:
        return {
            "suager": settings.template_suager,
            "cobble": settings.template_cobble,
            "kyomi":  settings.template_mizuki,
        }.get(self.bot.name)

    def get_warn_settings(self, ctx: commands.Context, language: Language):
        _data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if not _data:
            return self.settings_template["warnings"], language.string("mod_warn_settings", ctx.prefix)
        data = json.loads(_data["data"])
        try:
            return data["warnings"], None
        except KeyError:
            return self.settings_template["warnings"], language.string("mod_warn_settings", ctx.prefix)

    @staticmethod
    def warn_check(ctx: commands.Context, member: discord.Member, language: Language):
        if member.id == ctx.author.id:
            return language.string("mod_warn_self")
        # I think they should be allowed to warn the bot if they so wish, it wouldn't really affect much...
        return True

    def get_warn_count(self, uid: int, gid: int):
        """ Return the total amount of non-expire warnings against this user """
        return len(self.bot.db.fetch("SELECT * FROM punishments WHERE uid=? AND gid=? AND bot=? AND action='warn' AND handled=0", (uid, gid, self.bot.name)))

    async def warn_user(self, ctx: commands.Context, member: discord.Member, warn_settings: dict, reason: str, language: Language, expiry: time.datetime = None, duration: str = None):
        if expiry and duration:
            self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (member.id, ctx.guild.id, "warn", ctx.author.id, reason, True, expiry, 0, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (member.id, ctx.guild.id, "warn", ctx.author.id, reason, False, time.now2(), 0, self.bot.name))
        entry_id = self.bot.db.db.lastrowid
        await send_mod_dm(self.bot, ctx, member, "warn", reason, duration)
        await send_mod_log(self.bot, ctx, member, ctx.author, entry_id, "warn", reason, duration)
        required_warnings = warn_settings["required_to_mute"]  # How many warnings the user has to achieve to get muted
        current_warnings = self.get_warn_count(member.id, ctx.guild.id)  # How many warnings the user now has
        if current_warnings >= required_warnings:  # The user will now be muted
            scaling_power = current_warnings - required_warnings  # 3rd warn at 3 required = scaling ** 0 == length * 1
            delta = time.interpret_time(warn_settings["mute_length"])
            delta = time.relativedelta(seconds=((time.datetime.min + delta) - time.datetime.min).total_seconds() * warn_settings["scaling"] ** scaling_power)  # type: ignore
            # delta *= warn_settings["scaling"] ** scaling_power
            expiry, error = time.add_time(delta)
            if time.rd_is_above_5y(delta):
                error = True  # If the mute length exceeds 5 years, we will warn the user, but I don't think we need to notify that since it's not too likely to ever happen anyways
            mute_role = self.mute_role(ctx, language)
            try:  # Mute the user
                await self.mute_user_generic(ctx, member, mute_role, reason)
            except Exception as _:  # Couldn't mute the user, so no point in continuing on with the DM and logs
                type(_)  # Makes pycharm think that the exception is actually used somewhere
                return  # Anyone with enough braincells should be able to guess that the muting is related to the person getting too many warnings...
            warnings = language.plural(current_warnings, "mod_warn_word", precision=0, commas=True, case="accusative")
            mute_reason = language.string("mod_mute_auto_reason", warnings=warnings)
            if not error:
                mute_duration = language.delta_rd(delta, accuracy=7, brief=False, affix=False, case="for")
                self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                    (member.id, ctx.guild.id, "mute", self.bot.user.id, mute_reason, True, expiry, 0, self.bot.name))
            else:
                mute_duration = None
                self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                    (member.id, ctx.guild.id, "mute", self.bot.user.id, mute_reason, False, time.now2(), 0, self.bot.name))
            entry_id = self.bot.db.db.lastrowid
            await send_mod_dm(self.bot, ctx, member, "mute", warnings, mute_duration, True)
            await send_mod_log(self.bot, ctx, member, ctx.author, entry_id, "mute", mute_reason, mute_duration)

    @commands.command(name="warn", aliases=["warning"])
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        """ Warn a user

        You can specify the duration of the warning before the reason
        `//warn @someone 7d This will be a temporary warning`
        `//warn @someone This will be a permanent warning`"""
        language = ctx.language()
        warn_settings, missing = self.get_warn_settings(ctx, language)
        if missing:
            await ctx.send(missing)
        warn_check = self.warn_check(ctx, member, language)
        if warn_check is not True:
            return await ctx.send(warn_check)
        reason, delta, expiry, error = await self.get_duration(ctx, reason, language)
        if not error:
            reason = " ".join(reason.split(" ")[1:])
            reason = reason or language.string("mod_reason_none")
            duration = language.delta_rd(delta, accuracy=7, brief=False, affix=False, case="for")
            out = language.string("mod_warn_timed", user=member, duration=duration, reason=reason)
            await self.warn_user(ctx, member, warn_settings, reason, language, expiry, duration)
        else:
            out = language.string("mod_warn", user=member, reason=reason)
            await self.warn_user(ctx, member, warn_settings, reason, language, None, None)
        return await ctx.send(out)

    @commands.command(name="masswarn")
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    async def mass_warn(self, ctx: commands.Context, members: commands.Greedy[commands.MemberID], *, reason: str = None):
        """ Mass-warn multiple users """
        language = self.bot.language(ctx)
        warn_settings, missing = self.get_warn_settings(ctx, language)
        if missing:
            await ctx.send(missing)
        reason, delta, expiry, error = await self.get_duration(ctx, reason, language)
        duration = None
        if not error:
            reason = " ".join(reason.split(" ")[1:])
            reason = reason or language.string("mod_reason_none")
            duration = language.delta_rd(delta, accuracy=7, brief=False, affix=False)
        warned, failed = 0, 0
        for member_id in members:
            success = False
            try:
                member: discord.Member = ctx.guild.get_member(member_id)  # type: ignore
                if member is None:
                    await ctx.send(language.string("mod_kick_none", id=member_id))
                    continue
                warn_check = self.warn_check(ctx, member, language)
                if warn_check is not True:
                    return await ctx.send(warn_check)
                await self.warn_user(ctx, member, warn_settings, reason, language, expiry, duration)
                warned += 1
                success = True
            except Exception as e:
                await ctx.send(f"`{member_id}` - {type(e).__name__}: {e}")
            finally:
                if not success:
                    failed += 1
        total = warned + failed
        timed = "_timed" if not error else ""
        if failed:
            output = language.string("mod_warn_mass2" + timed, reason=reason, total=language.number(total), banned=language.number(warned), failed=language.number(failed), duration=duration)
        else:
            output = language.string("mod_warn_mass" + timed, reason=reason, total=language.number(total), duration=duration)
        return await ctx.send(output)

    @staticmethod
    def pardon_check(ctx: commands.Context, member: discord.Member, language: Language):
        if member.id == ctx.author.id:
            return language.string("mod_pardon_self")
        return True

    async def pardon_user(self, ctx: commands.Context, member: discord.Member, warning_id: Union[int, Literal["all"]], reason: str, language: Language):
        if warning_id == "all":
            self.bot.db.execute("UPDATE punishments SET handled=4 WHERE uid=? AND gid=? AND action='warn' AND handled=0 AND bot=?", (member.id, ctx.guild.id, self.bot.name))
            reason_log = reason  # No reason to attach
            original_warning = None
        else:
            output = self.bot.db.execute("UPDATE punishments SET handled=4 WHERE uid=? AND gid=? AND action='warn' AND id=? AND handled=0 AND bot=?",
                                         (member.id, ctx.guild.id, warning_id, self.bot.name))
            if output == "UPDATE 0":  # nothing was changed, meaning the warning was not pardoned
                return await ctx.send(language.string("mod_pardon_fail", warning=warning_id))
            reason_log = f"[{warning_id}] {reason}"
            warning = self.bot.db.fetchrow("SELECT reason FROM punishments WHERE id=?", (warning_id,))
            original_warning = f"[{warning_id}] {warning['reason']}"
        self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (member.id, ctx.guild.id, "pardon", ctx.author.id, reason_log, False, time.now2(), 1, self.bot.name))
        entry_id = self.bot.db.db.lastrowid
        await send_mod_dm(self.bot, ctx, member, "pardon", reason, original_warning=original_warning)
        await send_mod_log(self.bot, ctx, member, ctx.author, entry_id, "warn", reason, original_warning=original_warning)

    @commands.command(name="pardon", aliases=["forgive", "unwarn"])
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    async def pardon(self, ctx: commands.Context, member: discord.Member, warning_id: Union[int, Literal["all"]], *, reason: str = None):
        """ Remove someone's warning

        Specific warning: `//pardon @someone 7 Reason here`
        Remove all warnings: `//pardon @someone all Reason here`"""
        language = ctx.language()
        reason = reason or language.string("mod_reason_none")
        pardon_check = self.pardon_check(ctx, member, language)
        if pardon_check is not True:
            return await ctx.send(pardon_check)
        ret = await self.pardon_user(ctx, member, warning_id, reason, language)
        if ret is None:  # Since the function "returns" the await ctx.send() of the error message, we can test if that did not happen
            if warning_id == "all":
                return await ctx.send(language.string("mod_pardon_all", user=member, reason=reason))
            return await ctx.send(language.string("mod_pardon", user=member, warning=warning_id, reason=reason))

    @commands.command(name="warns", aliases=["warnings"])
    @commands.guild_only()
    async def warns_list(self, ctx: commands.Context, *, member: discord.Member = None):
        """ See your or someone else's list of currently active warnings """
        member = member or ctx.author
        language = self.bot.language(ctx)
        # This also has the side effect of showing active permanent warnings first, as their "expiry" value is set to the time the mute was issued, which is in the past.
        warns = self.bot.db.fetch("SELECT * FROM punishments WHERE uid=? AND gid=? AND action='warn' AND handled=0 ORDER BY expiry", (member.id, ctx.guild.id))
        if not warns:
            return await ctx.send(language.string("mod_warn_list_none", user=member.name))
        output = language.string("mod_warn_list", user=member.name, server=ctx.guild.name)
        outputs = []
        for item, warning in enumerate(warns, start=1):
            text = general.reason(ctx.guild.get_member(warning["author"]), warning["reason"])
            expiry = warning["expiry"]
            i = language.number(item, commas=False)
            case_id = language.number(warning["id"], commas=False)
            if warning["temp"]:
                expires_on = language.time(expiry, short=1, dow=False, seconds=True, tz=True, at=False, uid=ctx.author.id)
                expires_in = language.delta_dt(expiry, accuracy=3, brief=False, affix=True)
                outputs.append(language.string("mod_warn_list_item", i=i, id=case_id, text=text, time=expires_on, delta=expires_in))
            else:
                delta = language.delta_dt(expiry, accuracy=3, brief=False, affix=True)
                outputs.append(language.string("mod_warn_list_item2", i=i, id=case_id, text=text, delta=delta))
        output2 = "\n\n".join(outputs)
        if len(output2) > 1900:
            _data = BytesIO(str(output2).encode('utf-8'))
            return await ctx.send(output, file=discord.File(_data, filename=time.file_ts('Warnings')))
        else:
            return await ctx.send(f"{output}\n{output2}")

    @commands.command(name="modlog", aliases=["punishments", "infractions"])
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    async def mod_log(self, ctx: commands.Context, *, member: discord.Member = None):
        """ See the log of all punishments ever applied against the user in this server """
        member = member or ctx.author
        language = self.bot.language(ctx)
        # Show all actions taken against the user, in chronological order (ie. sorted by punishment ID)
        punishments = self.bot.db.fetch("SELECT * FROM punishments WHERE uid=? AND gid=? ORDER BY id", (member.id, ctx.guild.id))
        if not punishments:
            return await ctx.send(language.string("mod_log_none", user=member.name))
        output = language.string("mod_log", user=member.name, server=ctx.guild.name)
        outputs = []
        for item, entry in enumerate(punishments, start=1):
            author = ctx.guild.get_member(entry["author"])
            extra = ""
            if entry["action"] == "pardon":
                warning_s, reason = entry["reason"].split(" ", 1)
                try:
                    warning_id = int(warning_s[1:-1])
                    warning = self.bot.db.fetchrow("SELECT reason FROM punishments WHERE id=?", (warning_id,))
                    original_warning = f"[{warning_id}] {warning['reason']}"
                    text = language.string("mod_log_pardon", author=author, reason=reason)
                    extra = language.string("mod_log_item_pardon", warning=original_warning)
                except ValueError:
                    text = language.string("mod_log_pardon_all", author=author, reason=entry["reason"])
            else:
                text = language.string(f"mod_log_{entry['action']}", author=author, reason=entry["reason"])
            i = language.number(item, commas=False)
            case_id = language.number(entry["id"], commas=False)
            expiry = language.time(entry["expiry"], short=1, dow=False, seconds=True, tz=True, at=True, uid=ctx.author.id)
            delta = language.delta_dt(entry["expiry"], accuracy=3, brief=False, affix=True)
            if entry["temp"]:
                key = "mod_log_item_time2" if time.now2() > entry["expiry"] else "mod_log_item_time3"
            else:
                key = "mod_log_item_time"
            base = language.string("mod_log_item_base", i=i, id=case_id, text=text)
            times = language.string(key, time=expiry, delta=delta)
            outputs.append(base + extra + times)
        output2 = "\n\n".join(outputs)
        if len(output2) > 1900:
            _data = BytesIO(str(output2).encode('utf-8'))
            return await ctx.send(output, file=discord.File(_data, filename=time.file_ts('Punishments')))
        else:
            return await ctx.send(f"{output}\n{output2}")

    @commands.command(name="nickname", aliases=["nick"])
    @commands.guild_only()
    @permissions.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nickname_user(self, ctx: commands.Context, member: discord.Member, *, name: str = None):
        """ Sets a user's nickname """
        language = self.bot.language(ctx)
        try:
            if member.id == ctx.guild.owner.id:
                return await ctx.send(language.string("mod_nick_owner"))
            if (member.top_role.position >= ctx.author.top_role.position and member != ctx.author) and ctx.author != ctx.guild.owner:
                return await ctx.send(language.string("mod_nick_forbidden2"))
            await member.edit(nick=name, reason=general.reason(ctx.author, "Changed by command"))
            if name is None:
                message = language.string("mod_nick_reset", user=member)
            else:
                message = language.string("mod_nick", user=member, name=name)
            return await ctx.send(message)
        except discord.Forbidden:
            return await ctx.send(language.string("mod_nick_forbidden"))
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")

    @commands.command(name="nicknameme", aliases=["nickme", "nameme"])
    @commands.guild_only()
    @permissions.has_permissions(change_nickname=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nickname_self(self, ctx: commands.Context, *, name: str = None):
        """ Change your own nickname """
        language = self.bot.language(ctx)
        try:
            if ctx.author.id == ctx.guild.owner.id:
                return await ctx.send(language.string("mod_nick_owner"))
            await ctx.author.edit(nick=name, reason=general.reason(ctx.author, "Changed by command"))
            if name is None:
                message = language.string("mod_nick_self_reset")
            else:
                message = language.string("mod_nick_self", name=name)
            return await ctx.send(message)
        except discord.Forbidden:
            return await ctx.send(language.string("mod_nick_forbidden"))
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")

    @commands.group(name="find")
    @commands.guild_only()
    @permissions.has_permissions(ban_members=True)
    async def find(self, ctx: commands.Context):
        """ Finds a server member within your search term """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @find.command(name="username", aliases=["name"])
    async def find_name(self, ctx: commands.Context, *, search: str):
        """Finds members whose username fits the search string"""
        language = self.bot.language(ctx)
        loop = [f"{i} ({i.id})" for i in ctx.guild.members if search.lower() in i.name.lower()]  # and not i.bot
        await general.pretty_results(ctx, "name", language.string("mod_find", results=language.number(len(loop)), search=search), loop)

    @find.command(name="nickname", aliases=["nick"])
    async def find_nickname(self, ctx: commands.Context, *, search: str):
        """Finds members whose nickname fits the search string"""
        language = self.bot.language(ctx)
        loop = [f"{i.nick} | {i} ({i.id})" for i in ctx.guild.members if i.nick if (search.lower() in i.nick.lower())]  # and not i.bot
        await general.pretty_results(ctx, "name", language.string("mod_find", results=language.number(len(loop)), search=search), loop)

    @find.command(name="discriminator", aliases=["disc"])
    async def find_discriminator(self, ctx: commands.Context, *, search: str):
        """Finds members whose discriminator is the same as the search"""
        language = self.bot.language(ctx)
        if len(search) != 4 or not re.compile(r"^\d*$").search(search):
            return await ctx.send(language.string("mod_find_disc"))
        loop = [f"{i} ({i.id})" for i in ctx.guild.members if search == i.discriminator]
        await general.pretty_results(ctx, "discriminator", language.string("mod_find", results=language.number(len(loop)), search=search), loop)

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
            return await ctx.send(self.bot.language(ctx).string("mod_purge_user"))
        await do_removal(ctx, search, lambda e: e.author == user)

    @prune.command(name="contains")
    async def prune_contains(self, ctx: commands.Context, substring: str = None, search: int = 100):
        """Removes all messages containing a substring.
        The substring must be at least 3 characters long."""
        if substring is None or len(substring) < 3:
            return await ctx.send(self.bot.language(ctx).string("mod_purge_substring"))
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
            return await ctx.send(language.string("mod_purge_max", given=language.number(search)))
            # return await ctx.send(f'Too many messages to search for ({search:,}/2000)')
        total_reactions = 0
        async for message in ctx.history(limit=search, before=ctx.message):
            if len(message.reactions):
                total_reactions += sum(r.count for r in message.reactions)
                await message.clear_reactions()
        return await ctx.send(language.string("mod_purge_reactions", total=language.number(total_reactions)))
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
                return await ctx.send(language.string("mod_nick_owner"))
            if (member.top_role.position >= ctx.author.top_role.position and member != ctx.author) and ctx.author != ctx.guild.owner:
                return await ctx.send(language.string("mod_nick_forbidden2"))
            name = name or member.name
            _design, length = self.designs[design - 1].split(" // ")
            name = _design.replace('<nick>', name[:int(length)])
            await member.edit(nick=name, reason=general.reason(ctx.author, "Changed by command"))
            message = language.string("mod_nick", user=member, name=name)
            return await ctx.send(message)
        except discord.Forbidden:
            return await ctx.send(language.string("mod_nick_forbidden"))
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")

    @commands.command(name="nicknameme", aliases=["nickme", "nameme"])
    @commands.guild_only()
    @permissions.has_permissions(change_nickname=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nickname_self(self, ctx: commands.Context, design: int, *, name: str = None):
        """ Change your own nickname """
        language = self.bot.language(ctx)
        try:
            if ctx.author.id == ctx.guild.owner.id:
                return await ctx.send(language.string("mod_nick_owner"))
            name = name or ctx.author.name
            _design, length = self.designs[design - 1].split(" // ")
            name = _design.replace('<nick>', name[:int(length)])
            await ctx.author.edit(nick=name, reason=general.reason(ctx.author, "Changed by command"))
            message = language.string("mod_nick_self", name=name)
            return await ctx.send(message)
        except IndexError:
            return await ctx.send(f"Nickname design {design} is not available.")
        except discord.Forbidden:
            return await ctx.send(language.string("mod_nick_forbidden"))
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")

    @commands.command(name="nicknamedesign", aliases=["nickdesign", "design"])
    @commands.guild_only()
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nickname_design(self, ctx: commands.Context, design: int):
        """ Change your nickname design
        Example: `m!nickdesign 7`"""
        language = self.bot.language(ctx)
        try:
            if ctx.author.id == ctx.guild.owner.id:
                return await ctx.send(language.string("mod_nick_owner"))
            _design, length = self.designs[design - 1].split(" // ")
            name = _design.replace('<nick>', ctx.author.name[:int(length)])
            await ctx.author.edit(nick=name, reason=general.reason(ctx.author, "Changed by command"))
            message = language.string("mod_nick_self", name=name)
            return await ctx.send(message)
        except IndexError:
            return await ctx.send(f"Nickname design {design} is not available.")
        except discord.Forbidden:
            return await ctx.send(language.string("mod_nick_forbidden"))
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")

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
        return await ctx.send(output)


async def setup(bot: bot_data.Bot):
    if bot.name == "kyomi":
        await bot.add_cog(ModerationKyomi(bot))
    else:
        await bot.add_cog(Moderation(bot))
