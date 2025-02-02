from __future__ import annotations

import json
import re
from typing import Literal, Union

import discord
from discord import app_commands

from utils import bot_data, commands, general, interactions, languages, logger, paginators, permissions, settings, time


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


async def duration_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """ Autocomplete for punishment durations """
    return await interactions.duration_autocomplete(interaction, current, moderation_limit=True)


class Moderation(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        # self.admins = self.bot.config["owners"]

        # Regex for a discord invite link
        # Detected links: https://discord.gg/, https://discord.com/invite/, https://discord.com/servers/ (Public servers list),
        # Listing sites: https://disboard.org/server/(join/), https://top.gg/servers/, https://discadia.com/, https://discadia.com/servers/,
        # Listing sites: https://discordservers.com/server/, https://discordbotlist.com/servers/, https://disforge.com/server/, https://discord.me/, https://discords.com/servers/
        self.discord_link = re.compile(r"(?:https://)?(discord\.gg/|discord(?:app)?\.com/(?:invite/|servers/)|disboard.org/server/(?:join/)?|"
                                       r"top.gg/servers/|discadia.com/(?!add|emojis|\?)|discordservers.com/server/|discordbotlist.com/servers/|"
                                       r"disforge.com/server/|discord.me/(?!bots)|discords.com/servers/)\S+")

        # Formats for images and videos, that are allowed to be used in image-only channels
        # I might adjust this as time goes on, if we find file formats that might not be as popular but still images/videos
        self.image_formats = ["jpg", "jpeg", "jfif", "png", "gif", "webp", "tiff", "psd", "pdn",
                              "mp4", "mov", "wmv", "avi", "flv", "mkv", "webm"]
        self.image_link = re.compile(r"https?://\S+")
        # self.exceptions = ["https://tenor.com/", "https://imgur.com/", "https://youtu.be/", "https://www.youtube.com/watch?"]

    @commands.Cog.listener(name="on_message")
    async def on_message(self, ctx: discord.Message):
        """ A message is sent """
        return await self.moderate_message(ctx)

    @commands.Cog.listener(name="on_message_edit")
    async def on_message_edit(self, _: discord.Message, after: discord.Message):
        """ A message is edited - We still run all the checks """
        return await self.moderate_message(after)

    async def moderate_message(self, ctx: discord.Message):
        """ This function will call all the moderation checks for every message """
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
                    # if links := re.findall(self.image_link, ctx.content):  # If there are any links present
                    #     valid |= any((any(link.endswith(ext) for ext in self.image_formats) or any(link.startswith(exc) for exc in self.exceptions)) for link in links)
                    if re.findall(self.image_link, ctx.content):  # Ignore what the link points to, always count links as valid: it would be easier to moderate manually
                        valid = True

                    if not valid:
                        try:
                            await ctx.delete()
                            if permissions.can_send(ctx):
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
                    message = None  # If the message can't be sent
                    try:
                        await ctx.delete()
                        if permissions.can_send(ctx):
                            message = await ctx.channel.send(f"{ctx.author.mention} It would be preferable if you don't advertise here...", delete_after=20)
                    except (discord.Forbidden, discord.HTTPException):
                        if permissions.can_send(ctx):
                            message = await ctx.reply("This message contains an advertisement, but I seem to be unable to delete it...")

                    # Now we will try to warn the person
                    # Generate a context from our response message, just so that the author is set to us
                    if message is not None:
                        response_ctx: commands.Context = await self.bot.get_context(message, cls=commands.Context)  # type: ignore
                    else:
                        response_ctx: commands.FakeContext = commands.FakeContext(ctx.guild, self.bot, ctx.guild.me)
                    language = self.bot.language(response_ctx)
                    warn_settings, missing = self.get_warn_settings(response_ctx, language)
                    if missing:
                        await response_ctx.send(missing)

                    _, delta, expiry, error = await self.get_duration(anti_ads.get("warning", ""), language, "mod_warn_limit")
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

            # Warn Aya if he mentions China or uses any Chinese characters
            # if ctx.guild.id == 738425418637639775 and ctx.author.id == 577642516438843412:  # testing
            if ctx.guild.id == 568148147457490954 and ctx.author.id == 527729196688998415:
                async def warn_aya():
                    response_ctx: commands.Context = await self.bot.get_context(ctx, cls=commands.Context)  # type: ignore
                    language = response_ctx.language()
                    warn_settings, _ = self.get_warn_settings(response_ctx, language)
                    expiry = time.datetime.now() + time.relativedelta(months=1)
                    duration = "1 month"
                    reason = "[Automatic] Government's decisions"
                    await self.warn_user(response_ctx, ctx.author, warn_settings, reason, language, expiry, duration)
                    await ctx.reply(content="<:smack:765312065551728640>", mention_author=True)
                    nonlocal warned
                    warned = True

                warned = False
                if not warned:
                    for word in ctx.content.lower().split():
                        if word.startswith("chin") and word != "chin":
                            await warn_aya()
                            break
                if not warned:
                    for char in ctx.content:
                        if 0x4e00 <= ord(char) <= 0x9fff:  # There are more Chinese characters in Unicode, but 4E00-9FFF maps the most common ones
                            await warn_aya()
                            break

    def kick_check(self, ctx: commands.Context, member: discord.Member, language: languages.Language):
        if member == ctx.author:
            return language.string("mod_kick_self")
        elif member.id == ctx.guild.owner.id:
            return language.string("mod_kick_owner")
        elif member.id == self.bot.user.id:
            return language.string("mod_ban_suager", author=general.username(ctx.author))
        elif (member.top_role.position >= ctx.author.top_role.position) and ctx.author != ctx.guild.owner:
            return language.string("mod_kick_forbidden", member=member)
        elif member.top_role.position >= ctx.guild.me.top_role.position:  # The bot can't bypass this unless it's the guild owner, which is unlikely
            return language.string("mod_kick_forbidden2", member=member)
        return True

    async def kick_user(self, ctx: commands.Context, member: discord.Member, reason: str):
        await send_mod_dm(self.bot, ctx, member, "kick", reason, None)
        await member.kick(reason=general.reason(ctx.author, reason))
        self.bot.db.execute("UPDATE punishments SET handled=3 WHERE uid=? AND gid=? AND action='mute' AND handled=0 AND bot=?", (member.id, ctx.guild.id, self.bot.name))
        # noinspection SqlInsertValues
        self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (member.id, ctx.guild.id, "kick", ctx.author.id, reason, False, time.now2(), 1, self.bot.name))
        entry_id = self.bot.db.db.lastrowid
        await send_mod_log(self.bot, ctx, member, ctx.author, entry_id, "kick", reason, None)

    @commands.hybrid_command(name="kick")
    @permissions.has_permissions(kick_members=True, owner_bypass=False)
    @app_commands.default_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @app_commands.describe(member="The member you wish to kick from the server", reason="(Optional) The reason for kicking the member")
    @commands.guild_only()
    @app_commands.guild_install()
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        """ Kick a member from the server """
        await ctx.defer(ephemeral=False)
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

    @commands.hybrid_command(name="masskick")
    @permissions.has_permissions(ban_members=True, owner_bypass=False)
    @app_commands.default_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(members="List the usernames or user IDs of the members you wish to kick from the server", reason="(Optional) The reason for kicking the members")
    @commands.guild_only()
    @app_commands.guild_install()
    async def mass_kick(self, ctx: commands.Context, members: commands.Greedy[commands.MemberID], *, reason: str = None):
        """ Mass-kick members from the server """
        language = self.bot.language(ctx)
        reason = reason[:400] if reason else language.string("mod_reason_none")
        async with ctx.typing(ephemeral=False):
            successes = 0
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
                        await ctx.send(kick_check)
                        continue
                    await self.kick_user(ctx, member, reason)
                    successes += 1
                    success = True
                except Exception as e:
                    await ctx.send(f"`{member_id}` - {type(e).__name__}: {e}")
                finally:
                    if not success:
                        failed += 1
            total = successes + failed
            if failed:
                output = language.string("mod_kick_mass2", reason=reason, total=language.number(total),
                                         stats=language.string("mod_mass_stats", success=language.number(successes), failed=language.number(failed)))
            else:
                output = language.string("mod_kick_mass", reason=reason, total=language.number(total))
            return await ctx.send(output)

    def ban_check(self, ctx: commands.Context, user: commands.MemberID, language: languages.Language):
        member = ctx.guild.get_member(user)  # type: ignore
        if user == ctx.author.id:
            return language.string("mod_ban_self")
        elif user == ctx.guild.owner.id:
            return language.string("mod_ban_owner")
        elif user == self.bot.user.id:
            return language.string("mod_ban_suager", author=general.username(ctx.author))
        elif member is not None and (member.top_role.position >= ctx.author.top_role.position) and ctx.author != ctx.guild.owner:
            return language.string("mod_ban_forbidden", member=member)
        elif member is not None and (member.top_role.position >= ctx.guild.me.top_role.position):  # The bot can't bypass this unless it's the guild owner, which is unlikely
            return language.string("mod_ban_forbidden2", member=member)
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
        # noinspection SqlInsertValues
        self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (user.id, ctx.guild.id, "ban", ctx.author.id, reason, False, time.now2(), 1, self.bot.name))
        entry_id = self.bot.db.db.lastrowid
        await send_mod_log(self.bot, ctx, user, ctx.author, entry_id, "ban", reason, None)

    async def _ban_command(self, ctx: commands.Context, member: commands.MemberID, reason: str):
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

    # The slash command version maps MemberID to a string, so a separate version is needed to use a member selector
    @commands.command(name="ban")
    @permissions.has_permissions(ban_members=True, owner_bypass=False)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban_cmd(self, ctx: commands.Context, member: commands.MemberID, *, reason: str = None):
        """ Ban a member from the server """
        return await self._ban_command(ctx, member, reason)

    @app_commands.command(name="ban")
    @permissions.has_permissions(ban_members=True, owner_bypass=False)
    @app_commands.default_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(member="The member you wish to ban from the server", reason="(Optional) The reason for banning the member")
    @commands.guild_only()
    @app_commands.guild_install()
    async def ban_slash(self, interaction: discord.Interaction, member: discord.User, reason: str = None):
        """ Ban a member from the server """
        interactions.log_interaction(interaction)
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.defer(ephemeral=False)
        return await self._ban_command(ctx, member.id, reason)  # type: ignore

    @commands.hybrid_command(name="massban")
    @permissions.has_permissions(ban_members=True, owner_bypass=False)
    @app_commands.default_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(members="List the usernames or user IDs of the members you wish to ban from the server", reason="(Optional) The reason for banning the members")
    @commands.guild_only()
    @app_commands.guild_install()
    async def mass_ban(self, ctx: commands.Context, members: commands.Greedy[commands.MemberID], *, reason: str = None):
        """ Mass-ban members from the server """
        language = self.bot.language(ctx)
        reason = reason[:400] if reason else language.string("mod_reason_none")
        if ctx.author.id in members:
            return await ctx.send(language.string("mod_ban_self"))
        async with ctx.typing(ephemeral=False):
            successes = 0
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
                    successes += 1
                    success = True
                except Exception as e:
                    await ctx.send(f"`{member}` - {type(e).__name__}: {e}")
                finally:
                    if not success:
                        failed += 1
            total = successes + failed
            if failed:
                output = language.string("mod_ban_mass2", reason=reason, total=language.number(total),
                                         stats=language.string("mod_mass_stats", success=language.number(successes), failed=language.number(failed)))
            else:
                output = language.string("mod_ban_mass", reason=reason, total=language.number(total))
            return await ctx.send(output)

    async def unban_user(self, ctx: commands.Context, user: discord.User, reason: str):
        await ctx.guild.unban(user, reason=general.reason(ctx.author, reason))
        await send_mod_dm(self.bot, ctx, user, "unban", reason, None)
        # noinspection SqlInsertValues
        self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (user.id, ctx.guild.id, "unban", ctx.author.id, reason, False, time.now2(), 1, self.bot.name))
        entry_id = self.bot.db.db.lastrowid
        await send_mod_log(self.bot, ctx, user, ctx.author, entry_id, "unban", reason, None)

    async def _unban_command(self, ctx: commands.Context, member: commands.MemberID, reason: str):
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

    @commands.command(name="unban")
    @permissions.has_permissions(ban_members=True, owner_bypass=False)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def unban_cmd(self, ctx: commands.Context, member: commands.MemberID, *, reason: str = None):
        """ Unban a member from the server """
        return await self._unban_command(ctx, member, reason)

    @app_commands.command(name="unban")
    @permissions.has_permissions(ban_members=True, owner_bypass=False)
    @app_commands.default_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(member="The member you wish to unban from the server", reason="(Optional) The reason for unbanning the member")
    @commands.guild_only()
    @app_commands.guild_install()
    async def unban_slash(self, interaction: discord.Interaction, member: discord.User, reason: str = None):
        """ Unban a member from the server """
        interactions.log_interaction(interaction)
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.defer(ephemeral=False)
        return await self._unban_command(ctx, member.id, reason)  # type: ignore

    @commands.hybrid_command(name="massunban")
    @permissions.has_permissions(ban_members=True, owner_bypass=False)
    @app_commands.default_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(members="List the usernames or user IDs of the members you wish to unban from the server", reason="(Optional) The reason for unbanning the members")
    @commands.guild_only()
    @app_commands.guild_install()
    async def mass_unban(self, ctx: commands.Context, members: commands.Greedy[commands.MemberID], *, reason: str = None):
        """ Mass unban-members from the server """
        language = self.bot.language(ctx)
        reason = reason[:400] if reason else language.string("mod_reason_none")
        async with ctx.typing(ephemeral=False):
            successes = 0
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
                    successes += 1
                    success = True
                except Exception as e:
                    await ctx.send(f"`{member}` - {type(e).__name__}: {e}")
                finally:
                    if not success:
                        failed += 1
            total = successes + failed
            if failed:
                output = language.string("mod_unban_mass2", reason=reason, total=language.number(total),
                                         stats=language.string("mod_mass_stats", success=language.number(successes), failed=language.number(failed)))
            else:
                output = language.string("mod_unban_mass", reason=reason, total=language.number(total))
            return await ctx.send(output)

    def mute_role(self, ctx: commands.Context, language: languages.Language) -> discord.Role | str:
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

    def mute_check(self, ctx: commands.Context, member: discord.Member, language: languages.Language):
        if member.id == ctx.author.id:
            return language.string("mod_mute_self")
        elif member.id == self.bot.user.id:
            return language.string("mod_mute_suager")
        return True

    @staticmethod
    async def get_duration(reason: str, language: languages.Language, overflow_response: str = "mod_duration_limit_5y"):
        reason = reason[:400] if reason else language.string("mod_reason_none")
        _duration = reason.split(" ")[0]
        delta = time.interpret_time(_duration)
        expiry, _ = time.add_time(delta)
        error = False  # ignore other parsing errors
        if time.rd_is_above_5y(delta):
            # await ctx.send(language.string(overflow_response), delete_after=15)
            expiry = language.string(overflow_response)
            error = True
        return reason, delta, expiry, error

    async def mute_user_generic(self, ctx: commands.Context, member: discord.Member, mute_role: discord.Role, reason: str):
        if not isinstance(mute_role, discord.Role):  # Ignore any errors from a non-existent mute role
            return
        try:
            await member.add_roles(mute_role, reason=reason)
        except Exception as e:
            await ctx.send(ctx.language().string("mod_mute_error", error=f"{type(e).__name__}: {e}"))
            raise
        # Overwrite all older still active mutes as 5 ("Handled Otherwise")
        self.bot.db.execute("UPDATE punishments SET handled=5 WHERE uid=? AND gid=? AND action='mute' AND handled=0 AND bot=?", (member.id, ctx.guild.id, self.bot.name))

    async def mute_user_temporary(self, ctx: commands.Context, member: discord.Member, mute_role: discord.Role, reason: str, expiry: time.datetime, duration: str):
        await self.mute_user_generic(ctx, member, mute_role, general.reason(ctx.author, reason))
        # noinspection SqlInsertValues
        self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (member.id, ctx.guild.id, "mute", ctx.author.id, reason, True, expiry, 0, self.bot.name))
        entry_id = self.bot.db.db.lastrowid
        await send_mod_dm(self.bot, ctx, member, "mute", reason, duration)
        await send_mod_log(self.bot, ctx, member, ctx.author, entry_id, "mute", reason, duration)

    async def mute_user_permanent(self, ctx: commands.Context, member: discord.Member, mute_role: discord.Role, reason: str):
        await self.mute_user_generic(ctx, member, mute_role, general.reason(ctx.author, reason))
        # noinspection SqlInsertValues
        self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (member.id, ctx.guild.id, "mute", ctx.author.id, reason, False, time.now2(), 0, self.bot.name))
        entry_id = self.bot.db.db.lastrowid
        await send_mod_dm(self.bot, ctx, member, "mute", reason, None)
        await send_mod_log(self.bot, ctx, member, ctx.author, entry_id, "mute", reason, None)

    async def _mute_command(self, ctx: commands.Context, member: discord.Member, duration_str: str | None, reason: str | None):
        """ Wrapper for the mute command """
        language = self.bot.language(ctx)
        mute_role = self.mute_role(ctx, language)
        if not isinstance(mute_role, discord.Role):
            return await ctx.send(mute_role)
        mute_check = self.mute_check(ctx, member, language)
        if mute_check is not True:
            return await ctx.send(mute_check)
        if duration_str:
            _, delta, expiry, error = await self.get_duration(duration_str, language)
            if isinstance(expiry, str):  # If the duration is specified but is invalid, then ignore
                return await ctx.send(language.string("mod_duration_error"))
            reason = reason[:400] if reason else language.string("mod_reason_none")
        else:
            reason, delta, expiry, error = await self.get_duration(reason, language)
            if not isinstance(expiry, str):  # If the duration was specified within the reason and it is valid, remove it from the reason
                reason = " ".join(reason.split(" ")[1:]) or language.string("mod_reason_none")
        if error:
            return await ctx.send(expiry)  # Expiry holds the error message.
        if isinstance(expiry, str):  # There was a parsing error, therefore the mute should be permanent
            await self.mute_user_permanent(ctx, member, mute_role, reason)
            return await ctx.send(language.string("mod_mute", user=member, reason=reason))
        # If we got here, the mute is temporary.
        duration = language.delta_rd(delta, accuracy=7, brief=False, affix=False, case="for")
        await self.mute_user_temporary(ctx, member, mute_role, reason, expiry, duration)
        return await ctx.send(language.string("mod_mute_timed", user=member, duration=duration, reason=reason))

    @commands.command(name="mute")
    @permissions.has_permissions(kick_members=True, owner_bypass=False)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    async def mute_cmd(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        """ Mute a member (using a Muted role)

        You can specify the duration of the mute before the reason:
        `//mute @someone 7d This will be a temporary mute`
        `//mute @someone This will be a permanent mute`"""
        return await self._mute_command(ctx, member, None, reason)

    @app_commands.command(name="mute")
    @permissions.has_permissions(kick_members=True, owner_bypass=False)
    @app_commands.default_permissions(kick_members=True)
    @commands.bot_has_permissions(manage_roles=True)
    @app_commands.autocomplete(duration=duration_autocomplete)
    @app_commands.describe(
        member="The member you wish to mute",
        duration="The duration of the mute (Format: 1y1mo1d1h1m1s). Cannot be above 5 years.",
        reason="(Optional) The reason for muting the member")
    @commands.guild_only()
    @app_commands.guild_install()
    async def mute_slash(self, interaction: discord.Interaction, member: discord.Member, duration: str = None, reason: str = None):
        """ Mute a member (using a Muted role) """
        interactions.log_interaction(interaction)
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.defer(ephemeral=False)
        return await self._mute_command(ctx, member, duration, reason)

    async def _mass_mute_command(self, ctx: commands.Context, members: commands.Greedy[commands.MemberID], duration_str: str | None, reason: str | None):
        """ Wrapper for the mass-mute command """
        language = self.bot.language(ctx)
        mute_role = self.mute_role(ctx, language)
        if not isinstance(mute_role, discord.Role):
            return await ctx.send(mute_role)
        if duration_str:
            _, delta, expiry, error = await self.get_duration(duration_str, language)
            if isinstance(expiry, str):  # If the duration is specified but is invalid, then ignore
                return await ctx.send(language.string("mod_duration_error"))
            reason = reason[:400] if reason else language.string("mod_reason_none")
        else:
            reason, delta, expiry, error = await self.get_duration(reason, language)
            if not isinstance(expiry, str):  # If the duration was specified within the reason and it is valid, remove it from the reason
                reason = " ".join(reason.split(" ")[1:]) or language.string("mod_reason_none")
        if error:
            return await ctx.send(expiry)  # Expiry holds the error message.
        if isinstance(expiry, str):
            permanent = True
            duration = None
        else:
            permanent = False
            duration = language.delta_rd(delta, accuracy=7, brief=False, affix=False, case="for")
        async with ctx.typing(ephemeral=False):
            successes = failed = 0
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
                    if permanent:
                        await self.mute_user_permanent(ctx, member, mute_role, reason)
                    else:
                        await self.mute_user_temporary(ctx, member, mute_role, reason, expiry, duration)
                    successes += 1
                    success = True
                except Exception as e:
                    await ctx.send(f"`{member_id}` - {type(e).__name__}: {e}")
                finally:
                    if not success:
                        failed += 1
            total = successes + failed
            timed = "_timed" if not permanent else ""
            if failed:
                output = language.string("mod_mute_mass2" + timed, reason=reason, total=language.number(total),
                                         stats=language.string("mod_mass_stats", success=language.number(successes), failed=language.number(failed)), duration=duration)
            else:
                output = language.string("mod_mute_mass" + timed, reason=reason, total=language.number(total), duration=duration)
            return await ctx.send(output)

    @commands.command(name="massmute")
    @permissions.has_permissions(moderate_members=True, owner_bypass=False)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    async def mass_mute(self, ctx: commands.Context, members: commands.Greedy[commands.MemberID], *, reason: str = None):
        """ Mass-mute multiple members """
        return await self._mass_mute_command(ctx, members, None, reason)

    @app_commands.command(name="massmute")
    @permissions.has_permissions(moderate_members=True, owner_bypass=False)
    @app_commands.default_permissions(moderate_members=True)
    @commands.bot_has_permissions(manage_roles=True)
    @app_commands.autocomplete(duration=duration_autocomplete)
    @app_commands.describe(
        members="List the usernames or user IDs of the members you wish to mute",
        duration="The duration of the mutes (Format: 1y1mo1d1h1m1s). Cannot be above 5 years.",
        reason="(Optional) The reason for muting the members")
    @commands.guild_only()
    @app_commands.guild_install()
    async def mass_mute_slash(self, interaction: discord.Interaction, members: str, duration: str | None, reason: str = None):
        """ Mass-mute multiple members """
        interactions.log_interaction(interaction)
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.defer(ephemeral=False)  # Not the best solution, but defer the interaction straight away, so that it doesn't break if parsing takes too long
        # Why couldn't they just bring Greedy into slash commands?
        converter = commands.MemberID()
        members = [await converter.convert(ctx, member) for member in members.split()]
        return await self._mass_mute_command(ctx, members, duration, reason)  # type: ignore

    @staticmethod
    def unmute_check(ctx: commands.Context, member: discord.Member, mute_role: discord.Role, language: languages.Language):
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
        # noinspection SqlInsertValues
        self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (member.id, ctx.guild.id, "unmute", ctx.author.id, reason, False, time.now2(), 1, self.bot.name))
        entry_id = self.bot.db.db.lastrowid
        await send_mod_dm(self.bot, ctx, member, "unmute", reason, None)
        await send_mod_log(self.bot, ctx, member, ctx.author, entry_id, "unmute", reason, None)

    @commands.hybrid_command(name="unmute")
    @permissions.has_permissions(moderate_members=True, owner_bypass=False)
    @app_commands.default_permissions(moderate_members=True)
    @commands.bot_has_permissions(manage_roles=True)
    @app_commands.describe(member="The member you wish to unmute", reason="(Optional) The reason for unmuting the member")
    @commands.guild_only()
    @app_commands.guild_install()
    async def unmute(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        """ Unmute someone """
        await ctx.defer(ephemeral=False)
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

    @commands.hybrid_command(name="massunmute")
    @permissions.has_permissions(moderate_members=True, owner_bypass=False)
    @app_commands.default_permissions(moderate_members=True)
    @commands.bot_has_permissions(manage_roles=True)
    @app_commands.describe(members="List the usernames or user IDs of the members you wish to unmute", reason="(Optional) The reason for unmuting the members")
    @commands.guild_only()
    @app_commands.guild_install()
    async def mass_unmute(self, ctx: commands.Context, members: commands.Greedy[commands.MemberID], *, reason: str = None):
        """ Mass-unmute multiple members """
        language = self.bot.language(ctx)
        reason = reason[:400] if reason else language.string("mod_reason_none")
        mute_role = self.mute_role(ctx, language)
        if not isinstance(mute_role, discord.Role):
            return await ctx.send(mute_role)
        async with ctx.typing(ephemeral=False):
            successes, failed = 0, 0
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
                    successes += 1
                    success = True
                except Exception as e:
                    await ctx.send(f"`{member_id}` - {type(e).__name__}: {e}")
                finally:
                    if not success:
                        failed += 1
            total = successes + failed
            if failed:
                output = language.string("mod_unmute_mass2", reason=reason, total=language.number(total),
                                         stats=language.string("mod_mass_stats", success=language.number(successes), failed=language.number(failed)))
            else:
                output = language.string("mod_unmute_mass", reason=reason, total=language.number(total))
            return await ctx.send(output)

    @commands.hybrid_command(name="mutelist", aliases=["mutes"])
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @permissions.has_permissions(moderate_members=True, owner_bypass=False)
    @app_commands.default_permissions(moderate_members=True)
    @commands.guild_only()
    @app_commands.guild_install()
    async def mute_list(self, ctx: commands.Context):
        """ List all people who are currently muted in this server """
        await ctx.defer(ephemeral=False)
        language = self.bot.language(ctx)
        # This also has the side effect of showing active permanent mutes first, as their "expiry" value is set to the time the mute was issued, which is in the past.
        mutes = self.bot.db.fetch("SELECT * FROM punishments WHERE gid=? AND action='mute' AND handled=0 ORDER BY expiry", (ctx.guild.id,))
        if not mutes:
            return await ctx.send(language.string("mod_mute_list_none", server=ctx.guild.name))
        header = language.string("mod_mute_list", server=ctx.guild.name)
        paginator = paginators.LinePaginator(prefix=header, suffix=None, max_lines=5, max_size=2000, linesep="\n\n")
        for number, mute in enumerate(mutes, start=1):
            member = general.username(ctx.guild.get_member(mute["uid"]))
            expiry = mute["expiry"]
            i = language.number(number, commas=False)
            case_id = language.number(mute["id"], commas=False)
            if mute["temp"]:
                expires_on = language.time(expiry, short=1, dow=False, seconds=True, tz=True, at=True, uid=ctx.author.id)
                expires_in = language.delta_dt(expiry, accuracy=3, brief=False, affix=True)
                paginator.add_line(language.string("mod_mute_list_item", i=i, id=case_id, who=member, time=expires_on, delta=expires_in))
            else:
                delta = language.delta_dt(expiry, accuracy=3, brief=False, affix=False, case="for")
                paginator.add_line(language.string("mod_mute_list_item2", i=i, id=case_id, who=member, delta=delta))
        interface = paginators.PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
        return await interface.send_to(ctx)

    @property
    def settings_template(self) -> dict:
        return {
            "suager": settings.template_suager,
            "cobble": settings.template_cobble,
            "kyomi":  settings.template_mizuki,
        }.get(self.bot.name)

    def get_warn_settings(self, ctx: commands.Context, language: languages.Language) -> tuple[dict, str | None]:
        _data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if not _data:
            return self.settings_template["warnings"], language.string("mod_warn_settings", ctx.prefix)
        data = json.loads(_data["data"])
        try:
            return data["warnings"], None
        except KeyError:
            return self.settings_template["warnings"], language.string("mod_warn_settings", ctx.prefix)

    @staticmethod
    def warn_check(ctx: commands.Context, member: discord.Member, language: languages.Language):
        if member.id == ctx.author.id:
            return language.string("mod_warn_self")
        # I think they should be allowed to warn the bot if they so wish, it wouldn't really affect much...
        return True

    def get_warn_count(self, uid: int, gid: int):
        """ Return the total amount of non-expire warnings against this user """
        return len(self.bot.db.fetch("SELECT * FROM punishments WHERE uid=? AND gid=? AND bot=? AND action='warn' AND handled=0", (uid, gid, self.bot.name)))

    async def warn_user(self, ctx: commands.Context, member: discord.Member, warn_settings: dict, reason: str, language: languages.Language, expiry: time.datetime = None, duration: str = None):
        if expiry and duration:
            # noinspection SqlInsertValues
            self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (member.id, ctx.guild.id, "warn", ctx.author.id, reason, True, expiry, 0, self.bot.name))
        else:
            # noinspection SqlInsertValues
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
                # noinspection SqlInsertValues
                self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                    (member.id, ctx.guild.id, "mute", self.bot.user.id, mute_reason, True, expiry, 0, self.bot.name))
            else:
                mute_duration = None
                # noinspection SqlInsertValues
                self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                    (member.id, ctx.guild.id, "mute", self.bot.user.id, mute_reason, False, time.now2(), 0, self.bot.name))
            entry_id = self.bot.db.db.lastrowid
            await send_mod_dm(self.bot, ctx, member, "mute", warnings, mute_duration, True)
            await send_mod_log(self.bot, ctx, member, ctx.author, entry_id, "mute", mute_reason, mute_duration)

    async def _warn_command(self, ctx: commands.Context, member: discord.Member, duration_str: str | None, reason: str | None):
        """ Wrapper for the warn command """
        language = ctx.language()
        warn_settings, missing = self.get_warn_settings(ctx, language)
        if missing:
            await ctx.send(missing)
        warn_check = self.warn_check(ctx, member, language)
        if warn_check is not True:
            return await ctx.send(warn_check)
        if duration_str:
            _, delta, expiry, error = await self.get_duration(duration_str, language)
            if isinstance(expiry, str):  # If the duration is specified but is invalid, then ignore
                return await ctx.send(language.string("mod_duration_error"))
            reason = reason[:400] if reason else language.string("mod_reason_none")
        else:
            reason, delta, expiry, error = await self.get_duration(reason, language)
            if not isinstance(expiry, str):  # If the duration was specified within the reason and it is valid, remove it from the reason
                reason = " ".join(reason.split(" ")[1:]) or language.string("mod_reason_none")
        if error:
            return await ctx.send(expiry)  # Expiry holds the error message.
        if isinstance(expiry, str):  # There was a parsing error, therefore the warn should be permanent
            await self.warn_user(ctx, member, warn_settings, reason, language, None, None)
            return await ctx.send(language.string("mod_warn", user=member, reason=reason))
        duration = language.delta_rd(delta, accuracy=7, brief=False, affix=False, case="for")
        await self.warn_user(ctx, member, warn_settings, reason, language, expiry, duration)
        return await ctx.send(language.string("mod_warn_timed", user=member, duration=duration, reason=reason))

    @commands.command(name="warn", aliases=["warning"])
    @permissions.has_permissions(moderate_members=True, owner_bypass=False)
    @commands.guild_only()
    async def warn_cmd(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        """ Warn a member

        You can specify the duration of the warning before the reason:
        `//warn @someone 7d This will be a temporary warning`
        `//warn @someone This will be a permanent warning`"""
        return await self._warn_command(ctx, member, None, reason)

    @app_commands.command(name="warn")
    @permissions.has_permissions(moderate_members=True, owner_bypass=False)
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.autocomplete(duration=duration_autocomplete)
    @app_commands.describe(
        member="The member you wish to warn",
        duration="The duration of the warning (Format: 1y1mo1d1h1m1s). Cannot be above 5 years.",
        reason="(Optional) The reason for warning the member")
    @commands.guild_only()
    @app_commands.guild_install()
    async def warn_slash(self, interaction: discord.Interaction, member: discord.Member, duration: str = None, reason: str = None):
        """ Warn a member """
        interactions.log_interaction(interaction)
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.defer(ephemeral=False)
        return await self._warn_command(ctx, member, duration, reason)

    async def _mass_warn_command(self, ctx: commands.Context, members: commands.Greedy[commands.MemberID], duration_str: str | None, reason: str | None):
        """ Wrapper for the mass-warn command """
        language = self.bot.language(ctx)
        warn_settings, missing = self.get_warn_settings(ctx, language)
        if missing:
            await ctx.send(missing)
        if duration_str:
            _, delta, expiry, error = await self.get_duration(duration_str, language)
            if isinstance(expiry, str):  # If the duration is specified but is invalid, then ignore
                return await ctx.send(language.string("mod_duration_error"))
            reason = reason[:400] if reason else language.string("mod_reason_none")
        else:
            reason, delta, expiry, error = await self.get_duration(reason, language)
            if not isinstance(expiry, str):  # If the duration was specified within the reason and it is valid, remove it from the reason
                reason = " ".join(reason.split(" ")[1:]) or language.string("mod_reason_none")
        if error:
            return await ctx.send(expiry)  # Expiry holds the error message.
        if isinstance(expiry, str):
            expiry = duration = None
        else:
            duration = language.delta_rd(delta, accuracy=7, brief=False, affix=False, case="for")
        async with ctx.typing(ephemeral=False):
            successes = failed = 0
            for member_id in members:
                success = False
                try:
                    member: discord.Member = ctx.guild.get_member(member_id)  # type: ignore
                    if member is None:
                        await ctx.send(language.string("mod_kick_none", id=member_id))
                        continue
                    warn_check = self.warn_check(ctx, member, language)
                    if warn_check is not True:
                        await ctx.send(warn_check)
                        continue
                    await self.warn_user(ctx, member, warn_settings, reason, language, expiry, duration)
                    successes += 1
                    success = True
                except Exception as e:
                    await ctx.send(f"`{member_id}` - {type(e).__name__}: {e}")
                finally:
                    if not success:
                        failed += 1
            total = successes + failed
            timed = "_timed" if not error else ""
            if failed:
                output = language.string("mod_warn_mass2" + timed, reason=reason, total=language.number(total),
                                         stats=language.string("mod_mass_stats", success=language.number(successes), failed=language.number(failed)), duration=duration)
            else:
                output = language.string("mod_warn_mass" + timed, reason=reason, total=language.number(total), duration=duration)
            return await ctx.send(output)

    @commands.command(name="masswarn")
    @permissions.has_permissions(moderate_members=True, owner_bypass=False)
    @commands.guild_only()
    async def mass_warn(self, ctx: commands.Context, members: commands.Greedy[commands.MemberID], *, reason: str = None):
        """ Mass-warn multiple users """
        return await self._mass_warn_command(ctx, members, None, reason)

    @app_commands.command(name="masswarn")
    @permissions.has_permissions(moderate_members=True, owner_bypass=False)
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.autocomplete(duration=duration_autocomplete)
    @app_commands.describe(
        members="List the usernames or user IDs of the members you wish to warn",
        duration="The duration of the warnings (Format: 1y1mo1d1h1m1s). Cannot be above 5 years.",
        reason="(Optional) The reason for warning the members")
    @commands.guild_only()
    @app_commands.guild_install()
    async def mass_warn_slash(self, interaction: discord.Interaction, members: str, duration: str | None, reason: str = None):
        """ Mass-warn multiple members """
        interactions.log_interaction(interaction)
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.defer(ephemeral=False)  # Not the best solution, but defer the interaction straight away, so that it doesn't break if parsing takes too long
        converter = commands.MemberID()
        members = [await converter.convert(ctx, member) for member in members.split()]
        return await self._mass_warn_command(ctx, members, duration, reason)  # type: ignore

    @staticmethod
    def pardon_check(ctx: commands.Context, member: discord.Member, language: languages.Language):
        if member.id == ctx.author.id:
            return language.string("mod_pardon_self")
        return True

    async def pardon_user(self, ctx: commands.Context, member: discord.Member, warning_id: Union[int, Literal["all"]], reason: str, language: languages.Language):
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
        # noinspection SqlInsertValues
        self.bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (member.id, ctx.guild.id, "pardon", ctx.author.id, reason_log, False, time.now2(), 1, self.bot.name))
        entry_id = self.bot.db.db.lastrowid
        await send_mod_dm(self.bot, ctx, member, "pardon", reason, original_warning=original_warning)
        await send_mod_log(self.bot, ctx, member, ctx.author, entry_id, "pardon", reason, original_warning=original_warning)

    @commands.hybrid_command(name="pardon", aliases=["forgive", "unwarn"])
    @permissions.has_permissions(moderate_members=True, owner_bypass=False)
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(
        member="The member whose warning you wish to pardon",
        warning_id="The ID of the warning, or \"all\" to pardon all warnings",
        reason="(Optional) The reason for pardoning the warning")
    @commands.guild_only()
    @app_commands.guild_install()
    async def pardon(self, ctx: commands.Context, member: discord.Member, warning_id: str, *, reason: str = None):
        """ Remove someone's warning

        Specific warning: `//pardon @someone 7 Reason here`
        Remove all warnings: `//pardon @someone all Reason here`"""
        await ctx.defer(ephemeral=False)
        language = ctx.language()
        reason = reason or language.string("mod_reason_none")
        pardon_check = self.pardon_check(ctx, member, language)
        if pardon_check is not True:
            return await ctx.send(pardon_check)
        if warning_id != "all":
            try:
                warning_id = int(warning_id)
            except ValueError:
                return await ctx.send(language.string("mod_pardon_invalid"))
        ret = await self.pardon_user(ctx, member, warning_id, reason, language)
        if ret is None:  # Since the function "returns" the await ctx.send() of the error message, we can test if that did not happen
            if warning_id == "all":
                return await ctx.send(language.string("mod_pardon_all", user=member, reason=reason))
            return await ctx.send(language.string("mod_pardon", user=member, warning=warning_id, reason=reason))

    @commands.hybrid_command(name="warnings", aliases=["warns"])
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @app_commands.describe(member="The member whose warnings to check. If unspecified, shows your own.")
    @commands.guild_only()
    @app_commands.guild_install()
    async def warns_list(self, ctx: commands.Context, *, member: discord.Member = None):
        """ See your or someone else's list of currently active warnings """
        await ctx.defer(ephemeral=False)
        member = member or ctx.author
        language = self.bot.language(ctx)
        if member != ctx.author and not ctx.author.guild_permissions.moderate_members:
            return await ctx.send(language.string("mod_warn_list_permissions"))
        # This also has the side effect of showing active permanent warnings first, as their "expiry" value is set to the time the mute was issued, which is in the past.
        warns = self.bot.db.fetch("SELECT * FROM punishments WHERE uid=? AND gid=? AND action='warn' AND handled=0 ORDER BY expiry", (member.id, ctx.guild.id))
        if not warns:
            return await ctx.send(language.string("mod_warn_list_none", user=general.username(member)))
        header = language.string("mod_warn_list", user=general.username(member), server=ctx.guild.name)
        paginator = paginators.LinePaginator(prefix=header, suffix=None, max_lines=5, max_size=2000, linesep="\n\n")
        for item, warning in enumerate(warns, start=1):
            text = general.reason(ctx.guild.get_member(warning["author"]), warning["reason"])
            expiry = warning["expiry"]
            i = language.number(item, commas=False)
            case_id = language.number(warning["id"], commas=False)
            if warning["temp"]:
                expires_on = language.time(expiry, short=1, dow=False, seconds=True, tz=True, at=False, uid=ctx.author.id)
                expires_in = language.delta_dt(expiry, accuracy=3, brief=False, affix=True)
                paginator.add_line(language.string("mod_warn_list_item", i=i, id=case_id, text=text, time=expires_on, delta=expires_in))
            else:
                delta = language.delta_dt(expiry, accuracy=3, brief=False, affix=True)
                paginator.add_line(language.string("mod_warn_list_item2", i=i, id=case_id, text=text, delta=delta))
        interface = paginators.PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
        interface.display_page = len(interface.pages)  # Set to last page (i.e. show latest punishments first)
        return await interface.send_to(ctx)

    @commands.hybrid_command(name="modlog", aliases=["punishments", "infractions"])
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @permissions.has_permissions(moderate_members=True, owner_bypass=False)
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(member="The member whose punishment history to check. If unspecified, shows your own.")
    @commands.guild_only()
    @app_commands.guild_install()
    async def mod_log(self, ctx: commands.Context, *, member: discord.Member = None):
        """ See the log of all punishments ever applied against the user in this server """
        await ctx.defer(ephemeral=False)
        member = member or ctx.author
        language = self.bot.language(ctx)
        # Show all actions taken against the user, in chronological order (i.e. sorted by punishment ID)
        punishments = self.bot.db.fetch("SELECT * FROM punishments WHERE uid=? AND gid=? ORDER BY id", (member.id, ctx.guild.id))
        if not punishments:
            return await ctx.send(language.string("mod_log_none", user=general.username(member)))
        header = language.string("mod_log", user=general.username(member), server=ctx.guild.name)
        paginator = paginators.LinePaginator(prefix=header, suffix=None, max_lines=5, max_size=2000, linesep="\n\n")
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
            paginator.add_line(base + extra + times)
        interface = paginators.PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
        interface.display_page = len(interface.pages)  # Set to last page (i.e. show latest punishments first)
        return await interface.send_to(ctx)

    @commands.hybrid_command(name="nickname", aliases=["nick"])
    @permissions.has_permissions(manage_nicknames=True, owner_bypass=False)
    @app_commands.default_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    @app_commands.describe(member="The member whose nickname to change", name="The new nickname. Leave empty to remove the nickname.")
    @commands.guild_only()
    @app_commands.guild_install()
    async def nickname_user(self, ctx: commands.Context, member: discord.Member, *, name: str = None):
        """ Change a member's nickname """
        await ctx.defer(ephemeral=False)
        language = self.bot.language(ctx)
        try:
            if member.id == ctx.guild.owner.id:
                return await ctx.send(language.string("mod_nick_owner"))
            if (member.top_role.position >= ctx.author.top_role.position and member != ctx.author) and ctx.author != ctx.guild.owner:
                return await ctx.send(language.string("mod_nick_forbidden2"))
            await member.edit(nick=name, reason=general.reason(ctx.author, "Changed using command"))
            if name is None:
                message = language.string("mod_nick_reset", user=member)
            else:
                message = language.string("mod_nick", user=member, name=name)
            return await ctx.send(message)
        except discord.Forbidden:
            return await ctx.send(language.string("mod_nick_forbidden"))
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")

    @commands.hybrid_command(name="nickname-me", aliases=["nicknameme", "nickme", "nameme"])
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @permissions.has_permissions(change_nickname=True, owner_bypass=False)
    @app_commands.default_permissions(change_nickname=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    @app_commands.describe(name="The new nickname. Leave empty to remove the nickname.")
    @commands.guild_only()
    @app_commands.guild_install()
    async def nickname_self(self, ctx: commands.Context, *, name: str = None):
        """ Change your own nickname """
        await ctx.defer(ephemeral=True)  # It's your nickname, so doesn't make sense to show this to everyone
        language = self.bot.language(ctx)
        try:
            if ctx.author.id == ctx.guild.owner.id:
                return await ctx.send(language.string("mod_nick_owner"))
            await ctx.author.edit(nick=name, reason=general.reason(ctx.author, "Changed using command"))
            if name is None:
                message = language.string("mod_nick_self_reset")
            else:
                message = language.string("mod_nick_self", name=name)
            return await ctx.send(message)
        except discord.Forbidden:
            return await ctx.send(language.string("mod_nick_forbidden"))
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")

    @commands.hybrid_group(name="find")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @permissions.has_permissions(moderate_members=True, owner_bypass=False)
    @app_commands.default_permissions(moderate_members=True)
    @commands.guild_only()
    @app_commands.guild_install()
    async def find(self, ctx: commands.Context):
        """ Find members in your server """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @find.command(name="username", aliases=["name"])
    @app_commands.describe(search="The username to search for")
    async def find_name(self, ctx: commands.Context, *, search: str):
        """ Find members whose username fits the search string """
        language = self.bot.language(ctx)
        loop = [f"{member} ({member.id})" for member in ctx.guild.members if search.lower() in member.name.lower() or search.lower() in member.global_name.lower()]  # and not i.bot
        await general.pretty_results(ctx, "name", language.string("mod_find", results=language.number(len(loop)), search=search), loop)

    @find.command(name="nickname", aliases=["nick"])
    @app_commands.describe(search="The nickname to search for")
    async def find_nickname(self, ctx: commands.Context, *, search: str):
        """ Find members whose nickname fits the search string """
        language = self.bot.language(ctx)
        loop = [f"{member.nick} | {member} ({member.id})" for member in ctx.guild.members if member.nick if (search.lower() in member.nick.lower())]  # and not i.bot
        await general.pretty_results(ctx, "name", language.string("mod_find", results=language.number(len(loop)), search=search), loop)

    @find.command(name="discriminator", aliases=["disc"])
    @app_commands.describe(search="The discriminator to search for")
    async def find_discriminator(self, ctx: commands.Context, *, search: str):
        """ Find members whose discriminator is the same as the search """
        language = self.bot.language(ctx)
        if len(search) != 4 or not re.compile(r"^\d*$").search(search):
            return await ctx.send(language.string("mod_find_disc"))
        loop = [f"{i} ({i.id})" for i in ctx.guild.members if search == i.discriminator]
        await general.pretty_results(ctx, "discriminator", language.string("mod_find", results=language.number(len(loop)), search=search), loop)

    @commands.hybrid_group(name="purge", aliases=["prune", "delete"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @permissions.has_permissions(manage_messages=True, owner_bypass=False)
    @app_commands.default_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    @commands.guild_only()
    @app_commands.guild_install()
    async def prune(self, ctx: commands.Context):
        """ Removes messages from the current server """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @prune.command(name="embeds")
    @app_commands.describe(limit="The amount of messages to search through")
    async def prune_embeds(self, ctx: commands.Context, limit: int = 100):
        """ Remove messages that have embeds in them """
        await do_removal(ctx, limit, lambda e: len(e.embeds))

    @prune.command(name="files", aliases=["attachments"])
    @app_commands.describe(limit="The amount of messages to search through")
    async def prune_files(self, ctx: commands.Context, limit: int = 100):
        """ Remove messages that have attachments in them """
        await do_removal(ctx, limit, lambda e: len(e.attachments))

    @prune.command(name="mentions")
    @app_commands.describe(limit="The amount of messages to search through")
    async def prune_mentions(self, ctx: commands.Context, limit: int = 100):
        """ Remove messages that have mentions in them """
        await do_removal(ctx, limit, lambda e: len(e.mentions) or len(e.role_mentions))

    @prune.command(name="images")
    @app_commands.describe(limit="The amount of messages to search through")
    async def prune_images(self, ctx: commands.Context, limit: int = 100):
        """ Remove messages that have embeds or attachments """
        await do_removal(ctx, limit, lambda e: len(e.embeds) or len(e.attachments))

    @prune.command(name="all")
    @app_commands.describe(limit="The amount of messages to delete")
    async def prune_all(self, ctx: commands.Context, limit: int = 100):
        """ Remove all messages """
        await do_removal(ctx, limit, lambda e: True)

    @prune.command(name="user")
    @app_commands.describe(limit="The amount of messages to search through", user="The user whose messages to delete")
    async def prune_user(self, ctx: commands.Context, user: discord.User = None, limit: int = 100):
        """ Remove all messages by the specified user """
        if user is None:
            return await ctx.send(self.bot.language(ctx).string("mod_purge_user"))
        await do_removal(ctx, limit, lambda e: e.author == user)

    @prune.command(name="contains")
    @app_commands.describe(limit="The amount of messages to search through", substring="The substring to search for in message contents")
    async def prune_contains(self, ctx: commands.Context, substring: str = None, limit: int = 100):
        """ Remove all messages containing a substring

        The substring must be at least 3 characters long"""
        if substring is None or len(substring) < 3:
            return await ctx.send(self.bot.language(ctx).string("mod_purge_substring"))
            # await ctx.send('The substring length must be at least 3 characters.')
        else:
            await do_removal(ctx, limit, lambda e: substring in e.content)

    @prune.command(name="bots")
    @app_commands.describe(limit="The amount of messages to search through", prefix="The bot prefix to look for")
    async def prune_bots(self, ctx: commands.Context, limit: int = 100, prefix: str = None):
        """Remove a bots' messages and others' messages with a given bot prefix """
        get_prefix = prefix if prefix else self.bot.local_config["prefixes"]

        def predicate(m):
            return (m.webhook_id is None and m.author.bot) or m.content.startswith(tuple(get_prefix))
        await do_removal(ctx, limit, predicate)

    @prune.command(name="users")
    @app_commands.describe(limit="The amount of messages to search through")
    async def prune_users(self, ctx: commands.Context, limit: int = 100):
        """ Remove only user messages """
        def predicate(m):
            return m.author.bot is False
        await do_removal(ctx, limit, predicate)

    @prune.command(name="after")
    @app_commands.describe(message_id="The message ID after which messages should be deleted")
    async def prune_after(self, ctx: commands.Context, message_id: int):
        """ Remove all messages sent after a message ID (up to 2,000 messages in the past) """
        await do_removal(ctx, 2000, lambda e: True, after=message_id)

    @prune.command(name="emojis", aliases=["emotes"])
    @app_commands.describe(limit="The amount of messages to search through")
    async def prune_emoji(self, ctx: commands.Context, limit: int = 100):
        """ Remove all messages containing custom emojis """
        # custom_emoji = re.compile(r'<(?:a)?:(\w+):(\d+)>')
        custom_emoji = re.compile(r'<a?:(\w+):(\d{17,19})>')

        def predicate(m):
            return custom_emoji.search(m.content)
        await do_removal(ctx, limit, predicate)

    @prune.command(name="reactions")
    @app_commands.describe(limit="The amount of messages to search through")
    async def prune_reactions(self, ctx: commands.Context, limit: int = 100):
        """ Remove all reactions from messages that have them """
        language = self.bot.language(ctx)
        if limit > 2000:
            return await ctx.send(language.string("mod_purge_max", given=language.number(limit)))
            # return await ctx.send(f'Too many messages to search for ({search:,}/2000)')
        total_reactions = 0
        async for message in ctx.history(limit=limit, before=ctx.message):
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
    design_choices = [app_commands.Choice(name=design.split(" // ")[0], value=idx) for idx, design in enumerate(designs, start=1)]

    @commands.hybrid_command(name="nickname", aliases=["nick"])
    @permissions.has_permissions(manage_nicknames=True, owner_bypass=False)
    @app_commands.default_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    @app_commands.choices(design=design_choices)
    @app_commands.describe(
        member="The member whose nickname to change",
        design="The nickname design to use",
        name="The new nickname. Leave empty to remove the nickname."
    )
    @commands.guild_only()
    @app_commands.guild_install()
    async def nickname_user(self, ctx: commands.Context, member: discord.Member, design: int, *, name: str = None):
        """ Change a member's nickname """
        await ctx.defer(ephemeral=False)
        language = self.bot.language(ctx)
        try:
            if member.id == ctx.guild.owner.id:
                return await ctx.send(language.string("mod_nick_owner"))
            if (member.top_role.position >= ctx.author.top_role.position and member != ctx.author) and ctx.author != ctx.guild.owner:
                return await ctx.send(language.string("mod_nick_forbidden2"))
            name = name or general.username(member)
            _design, length = self.designs[design - 1].split(" // ")
            name = _design.replace('<nick>', name[:int(length)])
            await member.edit(nick=name, reason=general.reason(ctx.author, "Changed using command"))
            message = language.string("mod_nick", user=member, name=name)
            return await ctx.send(message)
        except discord.Forbidden:
            return await ctx.send(language.string("mod_nick_forbidden"))
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")

    @commands.hybrid_command(name="nickname-me", aliases=["nicknameme", "nickme", "nameme"])
    @permissions.has_permissions(change_nickname=True, owner_bypass=False)
    @app_commands.default_permissions(change_nickname=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    @app_commands.choices(design=design_choices)
    @app_commands.describe(design="The nickname design to use", name="The new nickname. Leave empty to remove the nickname.")
    @commands.guild_only()
    @app_commands.guild_install()
    async def nickname_self(self, ctx: commands.Context, design: int, *, name: str = None):
        """ Change your own nickname """
        await ctx.defer(ephemeral=False)
        language = self.bot.language(ctx)
        try:
            if ctx.author.id == ctx.guild.owner.id:
                return await ctx.send(language.string("mod_nick_owner"))
            name = name or general.username(ctx.author)
            _design, length = self.designs[design - 1].split(" // ")
            name = _design.replace('<nick>', name[:int(length)])
            await ctx.author.edit(nick=name, reason=general.reason(ctx.author, "Changed using command"))
            message = language.string("mod_nick_self", name=name)
            return await ctx.send(message)
        except IndexError:
            return await ctx.send(f"Nickname design {design} is not available.")
        except discord.Forbidden:
            return await ctx.send(language.string("mod_nick_forbidden"))
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")

    @commands.hybrid_command(name="nickname-design", aliases=["nicknamedesign", "nickdesign", "design"])
    @commands.bot_has_permissions(manage_nicknames=True)
    @app_commands.choices(design=design_choices)
    @app_commands.describe(design="The nickname design to use")
    @commands.guild_only()
    @app_commands.guild_install()
    async def nickname_design(self, ctx: commands.Context, design: int):
        """ Change your nickname design
        Example: `m!nickdesign 7`"""
        await ctx.defer(ephemeral=False)
        language = self.bot.language(ctx)
        try:
            if ctx.author.id == ctx.guild.owner.id:
                return await ctx.send(language.string("mod_nick_owner"))
            _design, length = self.designs[design - 1].split(" // ")
            name = _design.replace('<nick>', general.username(ctx.author)[:int(length)])
            await ctx.author.edit(nick=name, reason=general.reason(ctx.author, "Changed by command"))
            message = language.string("mod_nick_self", name=name)
            return await ctx.send(message)
        except IndexError:
            return await ctx.send(f"Nickname design {design} is not available.")
        except discord.Forbidden:
            return await ctx.send(language.string("mod_nick_forbidden"))
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")

    @commands.hybrid_command(name="nickname-designs", aliases=["nicknamedesigns", "nickdesigns", "designs"])
    async def nickname_designs(self, ctx: commands.Context):
        """ See all nickname designs available in the server """
        # await ctx.send(str([32 - (len(x) - 6) for x in self.designs]))
        await ctx.defer(ephemeral=False)
        output = "Here are the designs available in Midnight Dessert:\n\n"
        for i, _design in enumerate(self.designs, start=1):
            design, length = _design.split(" // ")
            output += f"{i}) {design.replace('<nick>', general.username(ctx.author)[:int(length)])}\n"
        prefix = ctx.prefix
        output += f"\nUse `{prefix}nickdesigns` to see the nicknames applied to your username\n" \
                  f"\nUse `{prefix}nickdesign <design_number>` to apply a design to your name\n" \
                  f"  \\- Note: This command will use your username (and therefore reset any nickname you have)\n" \
                  f"  \\- If you want to have a nickname, use `{prefix}nickme`\n" \
                  f"  \\- Example: `{prefix}nickdesign 7`\n" \
                  f"\nUse `{prefix}nickme <design_number> <nickname>` to apply a design to a nickname of your choice\n" \
                  f"  \\- Note: Requires permission to change your nickname\n" \
                  f"  \\- Example: `{prefix}nickme 7 {general.username(ctx.author)}`\n" \
                  f"\nNote: If you boost this server, you will get a special nickname design. It is not included here, " \
                  f"so if you change it, only the admins will be able to change it back.\n" \
                  f"\nWarning: these designs are NF2U, you may not copy these for your own servers."
        return await ctx.send(output)


async def setup(bot: bot_data.Bot):
    if bot.name == "kyomi":
        await bot.add_cog(ModerationKyomi(bot))
    else:
        await bot.add_cog(Moderation(bot))
