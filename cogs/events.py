from __future__ import annotations

import json
from datetime import date, timedelta
from io import BytesIO
from typing import List

import discord
from discord import app_commands
from regaus import time as time2

from utils import bot_data, commands, general, logger, time, cpu_burner


class Events(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        self.db = self.bot.db
        self.local_config = self.bot.local_config
        # Watched blocked users
        self.blocked = [667187968145883146, 852695205073125376]
        # Watched ignored chans: none
        self.watch_channels = []
        self.bad = ["reg", "reag", "302851022790066185"]
        self.bad2 = ["rega", "reag", "regg", "302851022790066185"]
        self.blocked_logs = 739183533792297164
        # Suager updates:      SL announcements,   3tk4 updates,       mimohome suwu,      Chill Crew updates, 1337xp updates,     # Kargadia updates
        self.updates_suager = [572857995852251169, 740665941712568340, 786008719657664532, 796755072427360256, 843876833221148713, 1051869244771549314]
        # Cobble updates:      Kargadia updates
        self.updates_cobble = [1051869244771549314]
        self.dm_logger = 806884278037643264  # DM logs channel

    @commands.Cog.listener()
    async def on_message(self, ctx: discord.Message):
        if ctx.guild is None:  # it's a DM
            if ctx.author.id != self.bot.user.id:  # isn't Suager himself
                channel = self.bot.get_channel(self.dm_logger)
                language = self.bot.language2("en")
                now = language.time(ctx.created_at, short=1, dow=False, seconds=True, tz=True, at=True)
                limit = 1900
                extra = []

                embeds = [embed for embed in ctx.embeds if embed.type == "rich"]
                files = [await att.to_file() for att in ctx.attachments if att.size <= 8388608]  # has to be under 8 MB because discord is too afraid of big files by bots
                file_links = [att.url for att in ctx.attachments if att.size > 8388608]

                if ctx.embeds:
                    extra.append(f"{len(ctx.embeds)} embeds ({len(embeds)} rich)")

                if ctx.attachments:
                    size = sum(att.size for att in ctx.attachments)
                    file_size = language.bytes(size, precision=2)
                    extra.append(f"{len(ctx.attachments)} files ({len(files)} uploadable) - Total file size {file_size}")
                    if file_links:
                        limit -= len(file_links) * 100  # Discord links are extremely fat, so they would use up the space for other message content.
                        extra.append("\nOther attachment links:")
                        extra.extend(file_links)
                extra_str = "\n\n" + "\n".join(extra) if extra else ""

                await channel.send(f"{general.username(ctx.author)} ({ctx.author.name} - {ctx.author.id}) | {now}\n{ctx.content[:limit]}{extra_str}", embeds=embeds, files=files)

        if ctx.author.id in self.blocked:
            for word in self.bad:
                if word in ctx.content.lower():
                    await self.handle_logged_message(ctx, 1)
                    break
        if ctx.channel.id in self.watch_channels:
            for word in self.bad2:
                if word in ctx.content.lower():
                    await self.handle_logged_message(ctx, 2)
                    break

        await self.update_message(ctx, "suager",  742886280911913010, self.updates_suager)  # Update channel: RK suager-updates
        await self.update_message(ctx, "cobble", 1051871739879116821, self.updates_cobble)  # Update channel: RK cobble-updates

    async def handle_logged_message(self, ctx: discord.Message, msg_type: int):
        channel = self.bot.get_channel(self.blocked_logs)
        gid = ctx.guild.id if ctx.guild is not None else "not a guild"
        types = {1: "User", 2: "Channel"}
        _author = f"{general.username(ctx.author)} ({ctx.author.name} - {ctx.author.id})"
        _server = f"{ctx.guild} ({gid})"
        _channel = f"{ctx.channel.mention} ({ctx.channel.name} - {ctx.channel.id})"
        return await channel.send(f"{_author} | {_server} | {_channel} | {time.time()} | Type: {types[msg_type]}\n{ctx.content}")

    async def update_message(self, ctx: discord.Message, bot_name: str, update_channel: int, channel_ids: list[int]):
        if self.bot.name == bot_name:
            if ctx.channel.id == update_channel:
                for channel_id in channel_ids:
                    channel = self.bot.get_channel(channel_id)
                    # These don't need to be logged because nobody cares
                    try:
                        if channel is not None:
                            await channel.send(f"{general.username(ctx.author)} | {self.bot.full_name} updates | {time.time()}\n{ctx.content}")
                        else:
                            general.print_error(f"{time.time()} > {self.bot.full_name} > Update announcement > Channel {channel_id} was not found...")
                    except Exception as e:
                        general.print_error(f"{time.time()} > {self.bot.full_name} > Update announcement > Channel {channel_id} > {type(e).__name__}: {e}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, err: commands.CommandError):
        """ Triggered when a command fails for any reason """
        if ctx.interaction is None:
            content = ctx.message.clean_content
        else:
            content = general.build_interaction_content(ctx.interaction)
        guild = getattr(ctx.guild, "name", "Private Message")
        error_msg = f"{type(err).__name__}: {str(err)}"
        error_message = f"{time.time()} > {self.bot.full_name} > {guild} > {ctx.author} ({ctx.author.id}) > {content} > {error_msg}"
        language = ctx.language()
        if isinstance(err, commands.MissingRequiredArgument):
            # A required argument is missing
            helper = str(ctx.invoked_subcommand) if ctx.invoked_subcommand else str(ctx.command)
            await ctx.send_help(helper, language.string("events_error_missing", param=err.param.name))

        elif isinstance(err, commands.TooManyArguments):
            # Too many arguments were specified
            helper = str(ctx.invoked_subcommand) if ctx.invoked_subcommand else str(ctx.command)
            await ctx.send_help(helper, language.string("events_error_extra_argument"))

        elif isinstance(err, commands.MemberNotFound):
            # The specified Member was not found
            await ctx.send(language.string("events_error_not_found_member", value=err.argument))
        elif isinstance(err, commands.UserNotFound):
            # The specified User was not found
            await ctx.send(language.string("events_error_not_found_user", value=err.argument))
        elif isinstance(err, commands.GuildNotFound):
            # The specified Guild was not found
            await ctx.send(language.string("events_error_not_found_guild", value=err.argument))
        elif isinstance(err, commands.ChannelNotFound):
            # The specified Channel was not found
            await ctx.send(language.string("events_error_not_found_channel", value=err.argument))
        elif isinstance(err, commands.ThreadNotFound):
            # The specified Thread was not found
            await ctx.send(language.string("events_error_not_found_thread", value=err.argument))
        elif isinstance(err, commands.MessageNotFound):
            # The specified Message was not found
            await ctx.send(language.string("events_error_not_found_message", value=err.argument))
        elif isinstance(err, commands.RoleNotFound):
            # The specified Role was not found
            await ctx.send(language.string("events_error_not_found_role", value=err.argument))
        elif isinstance(err, commands.ChannelNotReadable):
            # The specified Channel or Thread cannot be read by the bot
            await ctx.send(language.string("events_error_channel_access", value=err.argument))
        elif isinstance(err, (commands.ConversionError, commands.UserInputError)):
            # This is a generic condition for other bad argument and parsing/conversion errors
            # We will handle all these errors the same, and just tell the user that an argument is invalid
            helper = str(ctx.invoked_subcommand) if ctx.invoked_subcommand else str(ctx.command)
            await ctx.send_help(helper, language.string("events_error_bad_argument"))

        elif isinstance(err, commands.NoPrivateMessage):
            # The command cannot be used in DMs
            await ctx.send(language.string("events_error_guild_only"))
        elif isinstance(err, commands.NotOwner):
            # The command can only be used by the bot owner
            await ctx.send(language.string("events_error_owner"))
        elif isinstance(err, commands.MissingPermissions):
            # The author does not have sufficient permissions to run the command
            await ctx.send(language.string("events_error_permissions", perms=language.join([f"`{perm}`" for perm in err.missing_permissions])))
        elif isinstance(err, commands.BotMissingPermissions):
            # The bot does not have sufficient permissions to run the command
            await ctx.send(language.string("events_error_permissions_bot", perms=language.join([f"`{perm}`" for perm in err.missing_permissions])))
        elif isinstance(err, commands.NSFWChannelRequired):
            # The command can only be used in NSFW channel
            await ctx.send(language.string("events_error_nsfw"))
        elif isinstance(err, commands.CheckFailure):
            # This handles any other remaining check failure errors, if there are any...
            await ctx.send(language.string("events_error_check"))

        elif isinstance(err, commands.CommandOnCooldown):
            # The command is currently on cooldown and cannot be used
            await ctx.send(language.string("events_error_cooldown", time=language.number(err.retry_after, precision=2), rate=language.number(err.cooldown.rate),
                                           per=language.number(err.cooldown.per, precision=1)), delete_after=5 if err.retry_after < 5 else err.retry_after)
        elif isinstance(err, commands.MaxConcurrencyReached):
            # I think this might show `per` as some funny value instead of the name, but this isn't going to matter for Suager so...
            await ctx.send(language.string("events_error_concurrency", rate=language.number(err.number), per=err.per), delete_after=15)

        elif isinstance(err, (commands.CommandNotFound, commands.DisabledCommand)):
            # We will not respond at all if no such command exists, or it is disabled...
            # Use `return` instead of `pass` here because this isn't worthy of getting logged at all
            return

        elif isinstance(err, commands.CommandInvokeError):
            # An error occurred while invoking the command
            if ("2000 or fewer" in str(err.original) or "4000 or fewer" in str(err.original)) and len(ctx.message.content) > 1900:
                await ctx.send(language.string("events_error_message_length"))
                error_message = f"{time.time()} > {self.bot.full_name} > {guild} > {ctx.author} ({ctx.author.id}) > Cheeky little bastard entered an unnecessarily long string"
            else:
                await ctx.send(language.string("events_error_error", err=f"{type(err.original).__name__}: {str(err.original)}"))
                ec = self.bot.get_channel(self.bot.local_config["error_channel"])
                if ec is not None:
                    full_content = ctx.message.content if ctx.interaction is None else general.build_interaction_content(ctx.interaction)
                    error = general.traceback_maker(err.original, full_content[:750], ctx.guild, ctx.author, limit_text=True)
                    await ec.send(error)
                error_message = f"{time.time()} > {self.bot.full_name} > {guild} > {ctx.author} ({ctx.author.id}) > {content} > " \
                                f"{type(err.original).__name__}: {str(err.original)}"
                general.print_error(error_message)

        elif isinstance(err, (app_commands.AppCommandError, commands.HybridCommandError)):
            # An error occurred with a slash command
            if isinstance(err, commands.HybridCommandError):
                err = err.original  # Access the actual app command error
                # print(type(err).__module__, type(err).__name__)

            if isinstance(err, app_commands.CommandInvokeError):  # This includes InteractionResponded errors
                # print("hi3", err)
                err = err.original
                error_msg = f"{type(err).__name__}: {str(err)}"
                # await ctx.send(language.string("events_error_error", err=f"{type(err).__name__}: {str(err)}"))
                # await ctx.interaction.followup.send(language.string("events_error_error", err=error_msg))
                # If the interaction had not yet been responded, respond. If it has, send to followup. If the interaction expired, send regular message.
                await ctx.send(language.string("events_error_error", err=error_msg))
                ec = self.bot.get_channel(self.bot.local_config["error_channel"])
                if ec is not None:
                    full_content = general.build_interaction_content(ctx.interaction)
                    error = general.traceback_maker(err, full_content[:750], ctx.guild, ctx.author, limit_text=True)
                    await ec.send(error)
                error_message = f"{time.time()} > {self.bot.full_name} > {guild} > {ctx.author} ({ctx.author.id}) > {content} > {error_msg}"
                general.print_error(error_message)

            else:
                # Catch-all error statement for other slash-command related errors
                error_msg = f"{type(err).__name__}: {str(err)}"
                error_message = f"{time.time()} > {self.bot.full_name} > {guild} > {ctx.author} ({ctx.author.id}) > {content} > {error_msg}"
                general.print_error(error_message)
                await ctx.send(language.string("events_error_error", err=f"{type(err).__name__}: {str(err)}"))
                ec = self.bot.get_channel(self.bot.local_config["error_channel"])
                if ec is not None:
                    full_content = general.build_interaction_content(ctx.interaction)
                    error = general.traceback_maker(err, full_content[:750], ctx.guild, ctx.author, limit_text=True)
                    await ec.send(error)

        else:
            # Catch-all error statement. This shouldn't ever get called, but who knows...
            general.print_error(error_message)
            await ctx.send(language.string("events_error_error", err=f"{type(err).__name__}: {str(err)}"))
            ec = self.bot.get_channel(self.bot.local_config["error_channel"])
            if ec is not None:
                full_content = ctx.message.content if ctx.interaction is None else general.build_interaction_content(ctx.interaction)
                error = general.traceback_maker(err, full_content[:750], ctx.guild, ctx.author, limit_text=True)
                await ec.send(error)

        logger.log(self.bot.name, "commands", error_message)
        logger.log(self.bot.name, "errors", error_message)

    @commands.Cog.listener()
    async def on_command(self, _ctx: commands.Context):
        """ Triggered when a command is run """
        cpu_burner.run = False
        cpu_burner.last_command = time.now_ts()

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        """ Triggered when a command successfully completes """
        guild = getattr(ctx.guild, "name", "Private Message")
        content = ctx.message.clean_content if ctx.interaction is None else general.build_interaction_content(ctx.interaction)
        send = f"{time.time()} > {self.bot.full_name} > {guild} > {ctx.author} ({ctx.author.id}) > {content}"
        logger.log(self.bot.name, "commands", send)
        print(send)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        send = f"{time.time()} > {self.bot.full_name} > Joined {guild.name} ({guild.id})"
        logger.log(self.bot.name, "guilds", send)
        print(send)
        # Cancel the deletion of the server's data
        self.bot.db.execute("UPDATE leveling    SET remove=NULL WHERE gid=?   AND bot=?", (guild.id, self.bot.name))
        self.bot.db.execute("UPDATE punishments SET remove=NULL WHERE gid=?   AND bot=?", (guild.id, self.bot.name))
        self.bot.db.execute("UPDATE settings    SET remove=NULL WHERE gid=?   AND bot=?", (guild.id, self.bot.name))
        self.bot.db.execute("UPDATE starboard   SET remove=NULL WHERE guild=? AND bot=?", (guild.id, self.bot.name))
        self.bot.db.execute("UPDATE tags        SET remove=NULL WHERE gid=?   AND bot=?", (guild.id, self.bot.name))

        if not self.local_config["join_message"]:
            return
        try:
            to_send = sorted([c for c in guild.channels if c.permissions_for(guild.me).send_messages and isinstance(c, discord.TextChannel)],
                             key=lambda x: x.position)[0]
        except IndexError:
            pass
        else:
            await to_send.send(self.local_config["join_message"])

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        send = f"{time.time()} > {self.bot.full_name} > Left {guild.name} ({guild.id})"
        logger.log(self.bot.name, "guilds", send)
        print(send)
        # Delete most of the data about the server in 90 days' time
        removal_timestamp = date.today() + timedelta(days=90)  # 90 days from now
        self.bot.db.execute("UPDATE leveling    SET remove=? WHERE gid=?   AND bot=?", (removal_timestamp, guild.id, self.bot.name))
        self.bot.db.execute("UPDATE punishments SET remove=? WHERE gid=?   AND bot=?", (removal_timestamp, guild.id, self.bot.name))
        self.bot.db.execute("UPDATE settings    SET remove=? WHERE gid=?   AND bot=?", (removal_timestamp, guild.id, self.bot.name))
        self.bot.db.execute("UPDATE starboard   SET remove=? WHERE guild=? AND bot=?", (removal_timestamp, guild.id, self.bot.name))
        self.bot.db.execute("UPDATE tags        SET remove=? WHERE gid=?   AND bot=?", (removal_timestamp, guild.id, self.bot.name))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Load settings
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (member.guild.id, self.bot.name))
        # Cancel the deletion of the user's leveling data
        self.bot.db.execute("UPDATE leveling SET remove=NULL WHERE uid=? AND gid=? AND bot=?", (member.id, member.guild.id, self.bot.name))
        # Push all "User left" status punishments back into normal mode
        self.bot.db.execute("UPDATE punishments SET handled=0 WHERE uid=? and gid=? AND handled=3 AND bot=?", (member.id, member.guild.id, self.bot.name))
        active_mutes = self.bot.db.fetch("SELECT * FROM punishments WHERE uid=? AND gid=? AND action='mute' AND handled=0 AND bot=?", (member.id, member.guild.id, self.bot.name))
        if active_mutes and data:
            # Check for validity of the mutes: if they are still applicable
            valid = False
            for mute in active_mutes:
                if mute["temp"] and mute["expiry"] > time.now2():
                    valid = True
                    break
                elif not mute["temp"]:
                    valid = True
                    break

            if valid:
                settings = json.loads(data["data"])
                if "mute_role" in settings:
                    mute_role: discord.Role = member.guild.get_role(settings["mute_role"])
                    if mute_role is not None:
                        try:
                            await member.add_roles(mute_role, reason="Rejoining while muted")
                            logger.log(self.bot.name, "moderation", f"{time.time()} > {self.bot.name} > Member Join > {member.guild} > Re-muted {member} upon rejoining")
                        except Exception as e:
                            out = f"{time.time()} > {self.bot.name} > Member Join > {member.guild} > Failed to re-mute {member}: {type(e).__name__}: {e}"
                            general.print_error(out)
                            logger.log(self.bot.name, "moderation", out)
                            logger.log(self.bot.name, "errors", out)
                    else:
                        out = f"{time.time()} > {self.bot.name} > Member Join > {member.guild} > Failed to re-mute {member}: Mute role not found"
                        general.print_error(out)
                        logger.log(self.bot.name, "moderation", out)
                        logger.log(self.bot.name, "errors", out)

        if member.guild.id in [568148147457490954, 738425418637639775] and member.id not in [302851022790066185]:
            if member.display_name[0] < "A":
                await member.edit(reason="De-hoist", nick=f"\u17b5{member.display_name[:31]}")

        if data:
            settings = json.loads(data["data"])
            if "join_roles" in settings:
                try:
                    _roles = settings["join_roles"]["bots"] if member.bot else settings["join_roles"]["members"]
                    if _roles:
                        # for _role in _roles:
                        #     role: discord.Role = member.guild.get_role(_role)
                        #     if role:
                        roles = [member.guild.get_role(role) for role in _roles]
                        roles = [role for role in roles if role is not None]  # Remove any roles that don't exist anymore
                        try:
                            await member.add_roles(*roles, reason=f"[Auto-Roles] Joining the server")
                        except discord.Forbidden:
                            out = f"{time.time()} > {self.bot.full_name} > Member Joined > {member.guild} > Failed to give {member} join role"
                            general.print_error(out)
                            logger.log(self.bot.name, "errors", out)
                except KeyError:
                    pass

            if "welcome" in settings:
                welcome = settings["welcome"]
                if welcome["channel"]:
                    channel = self.bot.get_channel(welcome["channel"])
                    if channel:
                        language = self.bot.language(commands.FakeContext(member.guild, self.bot))
                        message = welcome["message"] \
                            .replace("[MENTION]", member.mention)\
                            .replace("[USER]", general.username(member))\
                            .replace("[SERVER]", member.guild.name)\
                            .replace("[CREATED_AT]", language.time(member.created_at, short=1, dow=False, seconds=False, tz=True))\
                            .replace("[JOINED_AT]", language.time(member.joined_at, short=1, dow=False, seconds=False, tz=True))\
                            .replace("[ACCOUNT_AGE]", language.delta_dt(member.created_at, accuracy=3, brief=False, affix=False))\
                            .replace("[MEMBERS]", language.number(member.guild.member_count))
                        try:
                            await channel.send(message, allowed_mentions=discord.AllowedMentions(users=[member]))
                        except (discord.Forbidden, discord.NotFound):
                            out = f"{time.time()} > {self.bot.full_name} > Member Joined > {member.guild.name} > Failed to send message for {member} - Forbidden"
                            general.print_error(out)
                            logger.log(self.bot.name, "errors", out)

            if "user_logs" in settings:
                user_logs = settings["user_logs"]
                if user_logs["join"]:
                    channel = self.bot.get_channel(user_logs["join"])
                    if channel:
                        language = self.bot.language(commands.FakeContext(member.guild, self.bot))
                        embed = discord.Embed(title=language.string("events_user_joined"), colour=general.green2)
                        embed.add_field(name=language.string("discord_user_username"), value=f"{member} ({member.mention})", inline=False)
                        embed.add_field(name=language.string("discord_user_id"), value=str(member.id), inline=False)
                        embed.add_field(name=language.string("discord_created_at"), value=language.time(member.created_at, short=0, dow=False, seconds=True, tz=True), inline=False)
                        embed.set_thumbnail(url=str(member.display_avatar.replace(size=1024, static_format="png")))
                        embed.timestamp = member.joined_at
                        try:
                            await channel.send(embed=embed)
                        except discord.Forbidden:
                            out = f"{time.time()} > {self.bot.full_name} > Member Joined > {member.guild.name} > Failed to send user log message for {member} - Forbidden"
                            general.print_error(out)
                            logger.log(self.bot.name, "errors", out)

                if user_logs["preserve_roles"]:
                    data = self.bot.db.fetchrow("SELECT * FROM user_roles WHERE gid=? AND uid=?", (member.guild.id, member.id))
                    if data:
                        role_ids = json.loads(data["roles"])
                        roles = [member.guild.get_role(role) for role in role_ids]
                        roles = [role for role in roles if role is not None]  # Remove any roles that don't exist anymore
                        try:
                            await member.add_roles(*roles, reason=f"[Saved Roles] Coming back to the server")
                        except (discord.Forbidden, discord.NotFound):
                            out = f"{time.time()} > {self.bot.full_name} > Member Joined > {member.guild} > Failed to give {member} preserved roles"
                            general.print_error(out)
                            logger.log(self.bot.name, "errors", out)
                        # Remove the entry as their roles have now been handled
                        self.bot.db.execute("DELETE FROM user_roles WHERE gid=? AND uid=?", (member.guild.id, member.id))

        if self.bot.name == "suager":
            if member.guild.id == 568148147457490954:  # Senko Lair
                role_ids = {
                    2021:  794699877325471776,
                    2022:  922602168010309732,
                    2023: 1091828639940747274,
                    2024: 1221468869282107612,
                }
                role_id = role_ids[time.now().year]
                await member.add_roles(member.guild.get_role(role_id))

            if member.guild.id == 869975256566210641:  # Nuriki's anarchy server
                if time2.datetime.now() - time2.datetime.from_datetime(member.created_at) < time.td(days=30):
                    try:
                        await member.send(f"Your account must be **at least 30 days old** to join **{member.guild}**.")
                    except (discord.HTTPException, discord.Forbidden):
                        pass
                    await member.kick(reason="Users must be at least 30 days old to join the server.")
                    await member.guild.get_channel(870015339142996079).send(f"{member} has been kicked - account less than 30 days old...")
                # trials = self.bot.db.fetch("SELECT * FROM trials WHERE guild_id=? and user_id=?", (member.guild.id, member.id,))
                # if trials:
                #     for trial in trials:
                #         if trial["type"] in ["mute", "kick", "ban"]:
                #             voters_yes: list = json.loads(trial["voters_yes"])
                #             voters_neutral: list = json.loads(trial["voters_neutral"])
                #             voters_no: list = json.loads(trial["voters_no"])
                #             yes, neutral, no = len(voters_yes), len(voters_neutral), len(voters_no)
                #             try:
                #                 upvotes = yes / (yes + no)
                #             except ZeroDivisionError:
                #                 upvotes = 0
                #             if yes + neutral + no >= trial["required_score"] and upvotes >= 0.6:
                #                 await member.add_roles(member.guild.get_role(870338399922446336), reason="Trial in progress")  # Give the On Trial role
                #                 await member.remove_roles(member.guild.get_role(869975498799845406), reason="Trial in progress")  # Revoke the Anarchists role
                #                 break

        if self.bot.name == "kyomi":
            if member.guild.id == 693948857939132478:  # Midnight Dessert
                await member.edit(nick=f"✧₊˚🍰⌇{general.username(member)[:23]}🌙⋆｡˚", reason="Joining the server")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        # Push all unhandled punishments to "User left" status
        self.bot.db.execute("UPDATE punishments SET handled=3 WHERE uid=? and gid=? AND handled=0 AND bot=?", (member.id, member.guild.id, self.bot.name))

        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (member.guild.id, self.bot.name))
        if data:
            settings = json.loads(data["data"])
            if self.bot.name == "suager":
                # Reset the user's XP upon leaving, unless the server enabled data retention
                if "leveling" in settings and not settings["leveling"].get("retain_data", False):
                    removal_timestamp = date.today() + timedelta(days=30)  # 30 days from now
                    self.bot.db.execute("UPDATE leveling SET remove=? WHERE uid=? AND gid=? AND bot=?", (removal_timestamp, member.id, member.guild.id, self.bot.name))
                    # This code below is for the old behaviour, where members with negative levels or xp were not removed from the database
                    # uid, gid = member.id, member.guild.id
                    # sel = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=? AND bot=?", (uid, gid, self.bot.name))
                    # if sel:
                    #     if sel["xp"] < 0:
                    #         return
                    #     elif sel["level"] < 0:
                    #         self.db.execute("UPDATE leveling SET xp=0 WHERE uid=? AND gid=? AND bot=?", (uid, gid, self.bot.name))
                    #     else:
                    #         self.db.execute("DELETE FROM leveling WHERE uid=? AND gid=? AND bot=?", (uid, gid, self.bot.name))

            if "goodbye" in settings:
                goodbye = settings["goodbye"]
                if goodbye["channel"]:
                    channel = self.bot.get_channel(goodbye["channel"])
                    if channel:
                        language = self.bot.language(commands.FakeContext(member.guild, self.bot))
                        message = goodbye["message"] \
                            .replace("[MENTION]", member.mention)\
                            .replace("[USER]", general.username(member))\
                            .replace("[SERVER]", member.guild.name)\
                            .replace("[CREATED_AT]", language.time(member.created_at, short=1, dow=False, seconds=False, tz=True))\
                            .replace("[JOINED_AT]", language.time(member.joined_at, short=1, dow=False, seconds=False, tz=True))\
                            .replace("[ACCOUNT_AGE]", language.delta_dt(member.created_at, accuracy=3, brief=False, affix=False))\
                            .replace("[LENGTH_OF_STAY]", language.delta_dt(member.joined_at, accuracy=3, brief=False, affix=False))\
                            .replace("[MEMBERS]", language.number(member.guild.member_count))
                        try:
                            await channel.send(message, allowed_mentions=discord.AllowedMentions(users=[member]))
                        except discord.Forbidden:
                            out = f"{time.time()} > {self.bot.full_name} > Member Left > {member.guild.name} > Failed to send message for {member} - Forbidden"
                            general.print_error(out)
                            logger.log(self.bot.name, "errors", out)

            if "user_logs" in settings:
                user_logs = settings["user_logs"]
                if user_logs["leave"]:
                    channel = self.bot.get_channel(user_logs["leave"])
                    if channel:
                        language = self.bot.language(commands.FakeContext(member.guild, self.bot))
                        embed = discord.Embed(title=language.string("events_user_left"), colour=general.red3)
                        embed.add_field(name=language.string("discord_user_username"), value=f"{member} ({member.mention})", inline=False)
                        embed.add_field(name=language.string("discord_user_id"), value=str(member.id), inline=False)
                        embed.add_field(name=language.string("discord_created_at"), value=language.time(member.created_at, short=0, dow=False, seconds=True, tz=True), inline=False)
                        joined = language.time(member.joined_at, short=0, dow=False, seconds=True, tz=True)
                        stayed = language.delta_dt(member.joined_at, accuracy=3, brief=False, affix=False)
                        embed.add_field(name=language.string("discord_length_of_stay"), value=f"{joined}\n{stayed}", inline=False)
                        embed.add_field(name=language.string("discord_user_roles"), value=", ".join([r.mention for r in member.roles if not r.is_default()]))
                        embed.set_thumbnail(url=str(member.display_avatar.replace(size=1024, static_format="png")))
                        embed.timestamp = time.now(None)
                        try:
                            await channel.send(embed=embed)
                        except discord.Forbidden:
                            out = f"{time.time()} > {self.bot.full_name} > Member Left > {member.guild.name} > Failed to send user log message for {member} - Forbidden"
                            general.print_error(out)
                            logger.log(self.bot.name, "errors", out)

                if user_logs["preserve_roles"]:
                    self.bot.db.execute("INSERT INTO user_roles VALUES (?, ?, ?)", (member.guild.id, member.id, json.dumps([r.id for r in member.roles if not r.is_default()])))

    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self.bot, 'uptime') or self.bot.uptime is None:
            self.bot.uptime = time.now(None)

        print(f"{time.time()} > {self.bot.full_name} > Ready: {self.bot.user} - {len(self.bot.guilds)} servers, {len(self.bot.users)} users")
        try:
            playing = f"Good morning | v{general.get_version()[self.bot.name]['short_version']}"
        except KeyError:
            playing = "Good morning | Version unknown"
        await self.bot.change_presence(activity=discord.Game(name=playing), status=discord.Status.dnd)
        logger.log(self.bot.name, "uptime", f"{time.time()} > {self.bot.full_name} > Bot is online")

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        async def process_msg(cid: int):
            output = f"Channel: {message.channel.mention} ({message.channel.id})\nAuthor: {message.author}\n" \
                     f"Message sent: {message.created_at:%Y-%m-%d %H:%M:%S}\nMessage content: {message.content}"  # [:1850]
            # It should be fine now, since Discord says the description can be up to 4096 characters long
            embed = discord.Embed(title="Message Deleted", description=output)
            files = []
            for attachment in message.attachments:
                file = BytesIO()
                try:
                    await attachment.save(file)
                except (discord.NotFound, discord.HTTPException):
                    pass
                files.append(discord.File(file, filename=attachment.filename))
            # embed = message.embeds[0] if message.embeds else None
            await self.bot.get_channel(cid).send(embed=embed, files=files)

        if self.bot.name in ["suager", "kyomi"]:
            if message.guild is not None:
                data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (message.guild.id, self.bot.name))
                if not data:
                    return
                settings: dict = json.loads(data["data"])
                if "message_logs" in settings:
                    logs_settings: dict = settings["message_logs"]
                    enabled: bool = logs_settings.get("enabled", False)
                    if not enabled:
                        return
                    delete_id: int = logs_settings.get("delete", 0)
                    if delete_id == 0:
                        return
                    # delete_channel: discord.TextChannel = message.guild.get_channel(delete_id)
                    ignore_bots: bool = logs_settings.get("ignore_bots", True)  # Default value
                    if ignore_bots and message.author.bot:
                        return
                    ignored_channels: list = logs_settings.get("ignore_channels", [])
                    if message.channel.id in ignored_channels:
                        return
                    return await process_msg(delete_id)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: List[discord.Message]):
        async def process_msg(cid: int):
            output = f"Channel: {message.channel.mention} ({message.channel.id})\nAuthor: {message.author}\n" \
                     f"Message sent: {message.created_at:%Y-%m-%d %H:%M:%S}\nMessage content: {message.content}"  # [:1850]
            # It should be fine now, since Discord says the description can be up to 4096 characters long
            embed = discord.Embed(title="Message Deleted", description=output)
            files = []
            for attachment in message.attachments:
                file = BytesIO()
                try:
                    await attachment.save(file)
                except (discord.NotFound, discord.HTTPException):
                    pass
                files.append(discord.File(file, filename=attachment.filename))
            # embed = message.embeds[0] if message.embeds else None
            await self.bot.get_channel(cid).send(embed=embed, files=files)

        if self.bot.name in ["suager", "kyomi"]:
            for message in messages:
                if message.guild is not None:
                    data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (message.guild.id, self.bot.name))
                    if not data:
                        return
                    settings: dict = json.loads(data["data"])
                    if "message_logs" in settings:
                        logs_settings: dict = settings["message_logs"]
                        enabled: bool = logs_settings.get("enabled", False)
                        if not enabled:
                            return
                        delete_id: int = logs_settings.get("delete", 0)
                        if delete_id == 0:
                            return
                        ignore_bots: bool = logs_settings.get("ignore_bots", True)  # Default value
                        if ignore_bots and message.author.bot:
                            return
                        ignored_channels: list = logs_settings.get("ignore_channels", [])
                        if message.channel.id in ignored_channels:
                            return
                        return await process_msg(delete_id)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        async def process_msg(cid: int):
            embed = discord.Embed(title="Message Edited",
                                  description=f"Channel: {after.channel.mention} ({after.channel.id})\n"
                                              f"Author: {after.author}\n"
                                              f"Message sent: {after.created_at:%Y-%m-%d %H:%M:%S}\n"
                                              f"Message edited: {after.edited_at:%Y-%m-%d %H:%M:%S}\n")
            embed.add_field(name="Content Before", value=before.content[:1024] or "None", inline=False)
            embed.add_field(name="Content After", value=after.content[:1024] or "None", inline=False)
            files = []
            att_removed = 0
            att_added = 0

            async def add_file(att: discord.Attachment):
                file = BytesIO()
                try:
                    await att.save(file)
                except (discord.NotFound, discord.HTTPException):
                    pass
                files.append(discord.File(file, filename=att.filename))

            # This checks if any new attachments have been added
            for attachment in after.attachments:
                if attachment not in before.attachments:
                    await add_file(attachment)
                    att_added += 1

            # This checks if any old attachments have been removed
            for attachment in before.attachments:
                if attachment not in after.attachments:
                    await add_file(attachment)
                    att_removed += 1

            if att_added:
                embed.description += f"\nAttachments added: {att_added}"
            if att_removed:
                embed.description += f"\nAttachments removed: {att_removed}"
            await self.bot.get_channel(cid).send(embed=embed, files=files)

        if self.bot.name in ["suager", "kyomi"]:
            # We only do anything if either the content or attachments of the message were changed
            if after.guild is not None and (after.content != before.content or after.attachments != before.attachments):
                data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (after.guild.id, self.bot.name))
                if not data:
                    return
                settings: dict = json.loads(data["data"])
                if "message_logs" in settings:
                    logs_settings: dict = settings["message_logs"]
                    enabled: bool = logs_settings.get("enabled", False)
                    if not enabled:
                        return
                    delete_id: int = logs_settings.get("edit", 0)
                    if delete_id == 0:
                        return
                    ignore_bots: bool = logs_settings.get("ignore_bots", True)  # Default value
                    if ignore_bots and after.author.bot:
                        return
                    ignored_channels: list = logs_settings.get("ignore_channels", [])
                    if after.channel.id in ignored_channels:
                        return
                    return await process_msg(delete_id)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Nickname - Dehoist in SL and RK
        if after.guild.id in [568148147457490954, 738425418637639775] and after.id != 302851022790066185:
            if after.display_name[0] < "A":
                await after.edit(reason="De-hoist", nick=f"\u17b5{after.display_name[:31]}")
            if "spoingus" in after.display_name.lower():
                await after.edit(nick=None)

        # Some people don't learn
        # if after.guild.id == 378586302703992835 and after.id == 302851022790066185 and after.nick is not None:
        #     try:
        #         await after.edit(nick=None, reason="De skullar mun tekinaan jollaan")
        #     except discord.Forbidden:
        #         message = f"{time.time()} > {self.bot.full_name} > Nickname Change > Can't revert nickname change for {after.name} in {after.guild.name} - Forbidden"
        #         general.print_error(message)
        #         logger.log(self.bot.name, "errors", message)

        # Roles - boosters in Kyomi's server
        if self.bot.name == "kyomi" and after.guild.id == 693948857939132478:  # Midnight Dessert
            r1, r2 = before.roles, after.roles
            if r1 != r2:
                roles_lost = []
                for role in r1:
                    if role not in r2:
                        roles_lost.append(role)
                roles_gained = []
                for role in r2:
                    if role not in r1:
                        roles_gained.append(role)

                booster_role = after.guild.get_role(716324385119535168)
                if booster_role in roles_gained:  # User started boosting MD
                    await after.edit(nick=f"⁀➷Booster!🧁 ☆ {general.username(after)[:14]} 🍩 ✦", reason="Applying booster nick design")
                if booster_role in roles_lost:  # User no longer boosts MD
                    if "⁀➷Booster!🧁 ☆" in after.nick:  # If they still have "Booster" in their nickname
                        await after.edit(nick=f"✧₊˚🍰⌇{general.username(after)[:23]}🌙⋆｡˚", reason="Removing booster nick design")  # Default nickname design


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Events(bot))
