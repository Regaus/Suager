from __future__ import annotations

import json
from io import BytesIO
from typing import List

import discord
from aiohttp import ClientPayloadError

from utils import bot_data, commands, general, help_utils, http, languages, logger, time
from regaus import time as time2


class Events(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        self.db = self.bot.db
        self.local_config = self.bot.local_config
        self.blocked = [667187968145883146, 852695205073125376]
        self.bad = ["reg", "reag", "302851022790066185"]
        self.updates = [572857995852251169, 740665941712568340, 786008719657664532, 796755072427360256, 843876833221148713]
        self.blocked_logs = 739183533792297164
        # Ignored channels for Senko Lair and RK message logs
        # self.message_ignore = [671520521174777869, 672535025698209821, 681647810357362786, 705947617779253328, 721705731937665104, 725835449502924901,
        #                        571025667265658881, 571025667265658881, 571278954523000842, 573636220622471168, 571030189451247618, 582598504233304075,
        #                        571031080908357633, 674342275421175818, 764528556507922442, 742885168997466196, 798513492697153536, 799714065256808469]
        self.dm_logger = 806884278037643264  # DM logs channel
        # Suager, Suager Dev, Suager Original
        self.self = [609423646347231282, 568149836927467542, 520042197391769610]

    @commands.Cog.listener()
    async def on_message(self, ctx: discord.Message):
        if ctx.guild is None:  # it's a DM
            if ctx.author.id != self.bot.user.id:  # isn't Suager himself
                await general.send(f"{ctx.author} ({ctx.author.id}) | {time.time()}\n{ctx.content}", self.bot.get_channel(self.dm_logger))
        if ctx.author.id in self.blocked:
            for word in self.bad:
                if word in ctx.content.lower():
                    channel = self.bot.get_channel(self.blocked_logs)
                    gid = ctx.guild.id if ctx.guild is not None else "not a guild"
                    await general.send(f"{ctx.author} ({ctx.author.id}) | {ctx.guild} ({gid}) | {ctx.channel.mention} ({ctx.channel.name} - "
                                       f"{ctx.channel.id}) | {time.time()}\n{ctx.content}", channel)
                    break
        if self.bot.name == "suager":
            if ctx.channel.id == 742886280911913010:
                for channel_id in self.updates:
                    channel = self.bot.get_channel(channel_id)
                    # These don't need to be logged because nobody cares
                    try:
                        if channel is not None:
                            await general.send(f"{ctx.author} | Suager updates | {time.time()}\n{ctx.content}", channel)
                        else:
                            general.print_error(f"on_message > Update announcement > Channel {channel_id} was not found...")
                    except Exception as e:
                        general.print_error(f"on_message > Update announcement > {channel_id} > {type(e).__name__}: {e}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, err: commands.CommandError):
        """ Triggered when a command fails for any reason """
        guild = getattr(ctx.guild, "name", "Private Message")
        error_message = f"{time.time()} > {self.bot.full_name} > {guild} > {ctx.author} ({ctx.author.id}) > {ctx.message.clean_content} > {type(err).__name__}: {str(err)}"
        language = ctx.language()
        if isinstance(err, commands.MissingRequiredArgument):
            # A required argument is missing
            helper = str(ctx.invoked_subcommand) if ctx.invoked_subcommand else str(ctx.command)
            # await general.send(language.string("events_error_missing", param=err.param.name), ctx.channel)
            await help_utils.send_help(ctx, helper, language.string("events_error_missing", param=err.param.name))

        elif isinstance(err, commands.TooManyArguments):
            # Too many arguments were specified
            helper = str(ctx.invoked_subcommand) if ctx.invoked_subcommand else str(ctx.command)
            # await general.send(language.string("events_error_extra_argument"), ctx.channel)
            await ctx.send_help(ctx, helper, language.string("events_error_extra_argument"))

        elif isinstance(err, commands.MemberNotFound):
            # The specified Member was not found
            await general.send(language.string("events_error_not_found_member", value=err.argument), ctx.channel)
        elif isinstance(err, commands.UserNotFound):
            # The specified User was not found
            await general.send(language.string("events_error_not_found_user", value=err.argument), ctx.channel)
        elif isinstance(err, commands.GuildNotFound):
            # The specified Guild was not found
            await general.send(language.string("events_error_not_found_guild", value=err.argument), ctx.channel)
        elif isinstance(err, commands.ChannelNotFound):
            # The specified Channel was not found
            await general.send(language.string("events_error_not_found_channel", value=err.argument), ctx.channel)
        elif isinstance(err, commands.ThreadNotFound):
            # The specified Thread was not found
            await general.send(language.string("events_error_not_found_thread", value=err.argument), ctx.channel)
        elif isinstance(err, commands.MessageNotFound):
            # The specified Message was not found
            await general.send(language.string("events_error_not_found_message", value=err.argument), ctx.channel)
        elif isinstance(err, commands.RoleNotFound):
            # The specified Role was not found
            await general.send(language.string("events_error_not_found_role", value=err.argument), ctx.channel)
        elif isinstance(err, commands.ChannelNotReadable):
            # The specified Channel or Thread cannot be read by the bot
            await general.send(language.string("events_error_channel_access", value=err.argument), ctx.channel)
        elif isinstance(err, (commands.ConversionError, commands.UserInputError)):
            # This is a generic condition for other bad argument and parsing/conversion errors
            # We will handle all these errors the same, and just tell the user that an argument is invalid
            helper = str(ctx.invoked_subcommand) if ctx.invoked_subcommand else str(ctx.command)
            await general.send(language.string("events_error_bad_argument"), ctx.channel)
            await ctx.send_help(helper)

        elif isinstance(err, commands.NoPrivateMessage):
            # The command cannot be used in DMs
            await general.send(language.string("events_error_guild_only"), ctx.channel)
        elif isinstance(err, commands.NotOwner):
            # The command can only be used by the bot owner
            await general.send(language.string("events_error_owner"), ctx.channel)
        elif isinstance(err, commands.MissingPermissions):
            # The author does not have sufficient permissions to run the command
            await general.send(language.string("events_error_permissions", perms=language.join([f"`{perm}`" for perm in err.missing_permissions])), ctx.channel)
        elif isinstance(err, commands.BotMissingPermissions):
            # The bot does not have sufficient permissions to run the command
            await general.send(language.string("events_error_permissions_bot", perms=language.join([f"`{perm}`" for perm in err.missing_permissions])), ctx.channel)
        elif isinstance(err, commands.NSFWChannelRequired):
            # The command can only be used in NSFW channel
            await general.send(language.string("events_error_nsfw"), ctx.channel)
        elif isinstance(err, commands.CheckFailure):
            # This handles any other remaining check failure errors, if there are any...
            await general.send(language.string("events_error_check"), ctx.channel)

        elif isinstance(err, commands.CommandOnCooldown):
            # The command is currently on cooldown and cannot be used
            await general.send(language.string("events_error_cooldown", time=language.number(err.retry_after, precision=2),
                                               rate=language.number(err.cooldown.rate), per=language.number(err.cooldown.per, precision=1)),
                               ctx.channel, delete_after=err.retry_after + 5)
        elif isinstance(err, commands.MaxConcurrencyReached):
            # I think this might show `per` as some funny value instead of the name, but this isn't going to matter for Suager so...
            await general.send(language.string("events_error_concurrency", rate=language.number(err.number), per=err.per), ctx.channel, delete_after=15)

        elif isinstance(err, (commands.CommandNotFound, commands.DisabledCommand)):
            pass  # We will not respond at all if no such command exists, or it is disabled...

        elif isinstance(err, commands.CommandInvokeError):
            # An error occurred while invoking the command
            error = general.traceback_maker(err.original, ctx.message.content[:750], ctx.guild, ctx.author)
            if "2000 or fewer" in str(err) and len(ctx.message.content) > 1900:
                await general.send(language.string("events_error_message_length"), ctx.channel)
                error_message = f"{time.time()} > {self.bot.full_name} > {guild} > {ctx.author} ({ctx.author.id}) > Cheeky little bastard entered an unnecessarily long string"
            else:
                await general.send(language.string("events_error_error", type(err.original).__name__, str(err.original)), ctx.channel)
                ec = self.bot.get_channel(self.bot.local_config["error_channel"])
                if ec is not None:
                    await ec.send(error)
                error_message = f"{time.time()} > {self.bot.full_name} > {guild} > {ctx.author} ({ctx.author.id}) > {ctx.message.clean_content} > " \
                                f"{type(err.original).__name__}: {str(err.original)}"

        else:
            # Catch-all error statement. This shouldn't ever get called, but who knows...
            await general.send(language.string("events_error_error", type(err).__name__), ctx.channel)
            ec = self.bot.get_channel(self.bot.local_config["error_channel"])
            if ec is not None:
                error = general.traceback_maker(err, ctx.message.content[:750], ctx.guild, ctx.author)
                await ec.send(error)

        logger.log(self.bot.name, "commands", error_message)
        logger.log(self.bot.name, "errors", error_message)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        """ Triggered when a command successfully completes """
        guild = getattr(ctx.guild, "name", "Private Message")
        content = ctx.message.clean_content
        send = f"{time.time()} > {self.bot.full_name} > {guild} > {ctx.author} ({ctx.author.id}) > {content}"
        logger.log(self.bot.name, "commands", send)
        print(send)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        send = f"{time.time()} > {self.bot.full_name} > Joined {guild.name} ({guild.id})"
        logger.log(self.bot.name, "guilds", send)
        print(send)
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
    async def on_guild_remove(self, guild):
        send = f"{time.time()} > {self.bot.full_name} > Left {guild.name} ({guild.id})"
        logger.log(self.bot.name, "guilds", send)
        print(send)
        # At this point I think it's easier to just let it all stay, since Suager barely ever leaves servers, and they probably don't have that much data anyways
        # if self.bot.name == "suager":
        #     self.db.execute("DELETE FROM leveling WHERE gid=?", (guild.id,))
        #     self.db.execute("DELETE FROM locales WHERE gid=?", (guild.id,))
        #     self.db.execute("DELETE FROM settings WHERE gid=? AND bot=?", (guild.id, self.bot.name))
        #     self.db.execute("DELETE FROM starboard WHERE gid=?", (guild.id,))
        #     self.db.execute("DELETE FROM tags WHERE gid=?", (guild.id,))
        #     # self.db.execute("DELETE FROM tbl_guild WHERE gid=?", (guild.id,))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        logger.log(self.bot.name, "members", f"{time.time()} > {self.bot.full_name} > {member} ({member.id}) just joined {member.guild.name}")
        # Load settings
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (member.guild.id, self.bot.name))
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

        if self.bot.name == "suager":
            if member.guild.id == 568148147457490954:  # Senko Lair
                role_ids = {
                    2021: 794699877325471776,
                    2022: 922602168010309732
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
                trials = self.bot.db.fetch("SELECT * FROM trials WHERE guild_id=? and user_id=?", (member.guild.id, member.id,))
                if trials:
                    for trial in trials:
                        if trial["type"] in ["mute", "kick", "ban"]:
                            voters_yes: list = json.loads(trial["voters_yes"])
                            voters_neutral: list = json.loads(trial["voters_neutral"])
                            voters_no: list = json.loads(trial["voters_no"])
                            yes, neutral, no = len(voters_yes), len(voters_neutral), len(voters_no)
                            try:
                                upvotes = yes / (yes + no)
                            except ZeroDivisionError:
                                upvotes = 0
                            if yes + neutral + no >= trial["required_score"] and upvotes >= 0.6:
                                await member.add_roles(member.guild.get_role(870338399922446336), reason="Trial in progress")  # Give the On Trial role
                                await member.remove_roles(member.guild.get_role(869975498799845406), reason="Trial in progress")  # Revoke the Anarchists role
                                break

        if member.guild.id in [568148147457490954, 738425418637639775] and member.id not in [302851022790066185]:
            if member.name[0] < "A":
                await member.edit(reason="De-hoist", nick=f"\u17b5{member.name[:31]}")

        if data:
            settings = json.loads(data["data"])
            if "join_roles" in settings:
                try:
                    _roles = settings["join_roles"]["bots"] if member.bot else settings["join_roles"]["members"]
                    if _roles:
                        for _role in _roles:
                            role: discord.Role = member.guild.get_role(_role)
                            if role:
                                try:
                                    await member.add_roles(role, reason=f"[Auto-Roles] Joining the server")
                                except discord.Forbidden:
                                    out = f"{time.time()} > {self.bot.full_name} > {member.guild} > Failed to give {member} join role (Forbidden)"
                                    general.print_error(out)
                                    logger.log(self.bot.name, "errors", out)
                except KeyError:
                    pass
            if "welcome" in settings:
                welcome = settings["welcome"]
                if welcome["channel"]:
                    channel = self.bot.get_channel(welcome["channel"])
                    if channel:
                        language = self.bot.language(languages.FakeContext(member.guild, self.bot))
                        message = welcome["message"] \
                            .replace("[MENTION]", member.mention)\
                            .replace("[USER]", member.name)\
                            .replace("[SERVER]", member.guild.name)\
                            .replace("[CREATED_AT]", language.time(member.created_at, short=1, dow=False, seconds=False, tz=False))\
                            .replace("[JOINED_AT]", language.time(member.joined_at, short=1, dow=False, seconds=False, tz=False))\
                            .replace("[ACCOUNT_AGE]", language.delta_dt(member.created_at, accuracy=3, brief=False, affix=False))\
                            .replace("[MEMBERS]", language.number(member.guild.member_count))
                        try:
                            await general.send(message, channel, u=[member])
                        except discord.Forbidden:
                            out = f"{time.time()} > {self.bot.full_name} > Member Joined > {member.guild.name} > Failed to send message for {member} - Forbidden"
                            general.print_error(out)
                            logger.log(self.bot.name, "errors", out)

        if self.bot.name == "kyomi":
            if member.guild.id == 693948857939132478:  # Midnight Dessert
                await member.edit(nick=f"✧₊˚🍰⌇{member.name[:23]}🌙⋆｡˚", reason="Joining the server")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        logger.log(self.bot.name, "members", f"{time.time()} > {self.bot.full_name} > {member} ({member.id}) just left {member.guild.name}")
        # Push all unhandled punishments to "User left" status
        self.bot.db.execute("UPDATE punishments SET handled=3 WHERE uid=? and gid=? AND handled=0 AND bot=?", (member.id, member.guild.id, self.bot.name))
        if self.bot.name == "suager":
            # language = self.bot.language2("english")
            # if member.guild.id == 568148147457490954:
            #     survival = language.delta_dt(member.joined_at, accuracy=3, brief=False, affix=False)
            #     remaining = len(member.guild.members)
            #     await general.send(f"**{member.name}** just abandoned Senko Lair after surviving for {survival}...\n"
            #                        f"{remaining} Senkoists remaining.", self.bot.get_channel(610836120321785869))
            # if member.guild.id == 738425418637639775:
            #     survival = language.delta_dt(member.joined_at, accuracy=3, brief=False, affix=False)
            #     await general.send(f"{member.name} just abandoned Regaus' Playground after surviving for {survival}...", self.bot.get_channel(754425619336396851))
            uid, gid = member.id, member.guild.id
            # self.db.execute("DELETE FROM economy WHERE uid=? AND gid=?", (uid, gid))
            sel = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=?", (uid, gid))
            if sel:
                if sel["xp"] < 0:
                    return
                elif sel["level"] < 0:
                    self.db.execute("UPDATE leveling SET xp=0 WHERE uid=? AND gid=?", (uid, gid))
                else:
                    self.db.execute("DELETE FROM leveling WHERE uid=? AND gid=?", (uid, gid))

        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (member.guild.id, self.bot.name))
        if data:
            settings = json.loads(data["data"])
            if "goodbye" in settings:
                goodbye = settings["goodbye"]
                if goodbye["channel"]:
                    channel = self.bot.get_channel(goodbye["channel"])
                    if channel:
                        language = self.bot.language(languages.FakeContext(member.guild, self.bot))
                        message = goodbye["message"] \
                            .replace("[MENTION]", member.mention)\
                            .replace("[USER]", member.name)\
                            .replace("[SERVER]", member.guild.name)\
                            .replace("[CREATED_AT]", language.time(member.created_at, short=1, dow=False, seconds=False, tz=False))\
                            .replace("[JOINED_AT]", language.time(member.joined_at, short=1, dow=False, seconds=False, tz=False))\
                            .replace("[ACCOUNT_AGE]", language.delta_dt(member.created_at, accuracy=3, brief=False, affix=False))\
                            .replace("[LENGTH_OF_STAY]", language.delta_dt(member.joined_at, accuracy=3, brief=False, affix=False))\
                            .replace("[MEMBERS]", language.number(member.guild.member_count))
                        try:
                            await general.send(message, channel, u=[member])
                        except discord.Forbidden:
                            out = f"{time.time()} > {self.bot.full_name} > Member Left > {member.guild.name} > Failed to send message for {member} - Forbidden"
                            general.print_error(out)
                            logger.log(self.bot.name, "errors", out)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User | discord.Member):
        logger.log(self.bot.name, "members", f"{time.time()} > {self.bot.full_name} > {user} ({user.id}) just got banned from {guild.name}")
        # message = f"{user} ({user.id}) has been **banned** from {guild.name}"
        # if self.bot.name == "suager":
        #     if guild.id == 568148147457490954:
        #         await general.send(message, self.bot.get_channel(626028890451869707))
        #     if guild.id == 738425418637639775:
        #         await general.send(message, self.bot.get_channel(764469594303234078))

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        logger.log(self.bot.name, "members", f"{time.time()} > {self.bot.full_name} > {user} ({user.id}) just got unbanned from {guild.name}")
        # message = f"{user} ({user.id}) has been **unbanned** from {guild.name}"
        # if self.bot.name == "suager":
        #     if guild.id == 568148147457490954:
        #         await general.send(message, self.bot.get_channel(626028890451869707))
        #     if guild.id == 738425418637639775:
        #         await general.send(message, self.bot.get_channel(764469594303234078))

    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self.bot, 'uptime') or self.bot.uptime is None:
            self.bot.uptime = time.now(None)

        # await self.bot.http.bulk_upsert_global_commands(self.bot.application_id, [])
        # await self.bot.http.bulk_upsert_guild_commands(self.bot.application_id, 738425418637639775, [])
        print(f"{time.time()} > {self.bot.full_name} > Ready: {self.bot.user} - {len(self.bot.guilds)} servers, {len(self.bot.users)} users")
        playing = f"Loading... | v{general.get_version()[self.bot.name]['short_version']}"
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
            await general.send(None, self.bot.get_channel(cid), embed=embed, files=files)

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
            # if message.guild is not None and message.guild.id in [568148147457490954, 738425418637639775]:
            #     if message.channel.id not in self.message_ignore:
            #         if not message.author.bot:
            #             await process_msg(764473671090831430 if message.guild.id == 568148147457490954 else 764494075663351858)

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
            await general.send(None, self.bot.get_channel(cid), embed=embed, files=files)
        # if self.bot.name == "suager":
        #     for message in messages:
        #         if message.guild.id in [568148147457490954, 738425418637639775]:
        #             if message.channel.id not in self.message_ignore:
        #                 if not message.author.bot:
        #                     await process_msg(764473671090831430 if message.guild.id == 568148147457490954 else 764494075663351858)
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
                        # delete_channel: discord.TextChannel = message.guild.get_channel(delete_id)
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
                                              f"Message edited: {after.edited_at:%Y-%m-%d %H:%M:%S}")
            embed.add_field(name="Content Before", value=before.content[:1024], inline=False)
            embed.add_field(name="Content After", value=after.content[:1024], inline=False)
            await general.send(None, self.bot.get_channel(cid), embed=embed)

        # if self.bot.name == "suager":
        #     if after.guild is not None and after.guild.id in [568148147457490954, 738425418637639775]:
        #         if after.channel.id not in self.message_ignore:
        #             if not after.author.bot:
        #                 if after.content != before.content:
        #                     await process_msg(764473671090831430 if after.guild.id == 568148147457490954 else 764494075663351858)
        if self.bot.name in ["suager", "kyomi"]:
            if after.guild is not None and after.content != before.content:
                data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (after.guild.id, self.bot.name))
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
                    if ignore_bots and after.author.bot:
                        return
                    ignored_channels: list = logs_settings.get("ignore_channels", [])
                    if after.channel.id in ignored_channels:
                        return
                    return await process_msg(delete_id)

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        to = time.time()
        log = "names"
        uid = after.id
        n1, n2 = [before.name, after.name]
        if n1 != n2:
            send = f"{to} > {n1} ({uid}) is now known as {n2}"
            logger.log(self.bot.name, log, send)
        d1, d2 = [before.discriminator, after.discriminator]
        if d1 != d2:
            send = f"{to} > {n2}'s ({uid}) discriminator is now {d2} (from {d1})"
            logger.log(self.bot.name, log, send)
        if self.bot.name in ["suager", "kyomi"]:
            a1, a2 = [before.avatar, after.avatar]  # type: discord.Asset, discord.Asset
            al = self.bot.get_channel(745760639955370083)
            if a1 != a2:
                send = f"{to} > {n2} ({uid}) changed their avatar"
                logger.log(self.bot.name, "user_avatars", send)
                if uid not in self.self:
                    try:
                        avatar = BytesIO(await http.get(str(after.avatar.replace(static_format="png", size=4096)), res_method="read"))
                        ext = "gif" if after.avatar.is_animated() else "png"
                        if al is None:
                            out = f"{time.time()} > {self.bot.name} > User Update > No avatar log channel found."
                            general.print_error(out)
                            logger.log(self.bot.name, "errors", out)
                        else:
                            await al.send(f"{time.time()} > {n2} ({uid}) changed their avatar", file=discord.File(avatar, filename=f"{a2.key}.{ext}"))
                    except (discord.HTTPException, ClientPayloadError) as e:
                        out = f"{time.time()} > {self.bot.name} > User Update > Failed to send updated avatar: {e}"
                        general.print_error(out)
                        logger.log(self.bot.name, "errors", out)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        to = time.time()
        log = "member_roles"
        guild = after.guild.name
        n = after.name
        uid = after.id
        if after.guild.id in [568148147457490954, 738425418637639775] and uid not in [302851022790066185]:
            if after.display_name[0] < "A":
                await after.edit(reason="De-hoist", nick=f"\u17b5{after.display_name[:31]}")
            if "spoingus" in after.display_name.lower():
                await after.edit(nick=None)
        # if after.guild.id in [430945139142426634] and uid == self.bot.user.id:
        #     await after.guild.me.edit(nick=None)
        # if after.guild.id == 784357864482537473 and uid == 517012611573743621:
        #     if after.nick is not None:
        #        await after.edit(nick=None, reason="Don't you dare")
        n1, n2 = before.nick, after.nick
        if n1 != n2:
            logger.log(self.bot.name, "names", f"{to} > {guild} > {n}'s ({uid}) nickname is now {n2} (from {n1})")
        r1, r2 = before.roles, after.roles
        if r1 != r2:
            roles_lost = []
            for role in r1:
                if role not in r2:
                    roles_lost.append(role.name)
            roles_gained = []
            for role in r2:
                if role not in r1:
                    roles_gained.append(role.name)
            for role in roles_lost:
                logger.log(self.bot.name, log, f"{to} > {guild} > {n} ({uid}) lost role {role}")
            for role in roles_gained:
                logger.log(self.bot.name, log, f"{to} > {guild} > {n} ({uid}) got role {role}")
            if self.bot.name == "kyomi" and after.guild.id == 693948857939132478:  # Midnight Dessert
                booster_role = after.guild.get_role(716324385119535168)
                if booster_role in roles_gained:  # User started boosting MD
                    await after.edit(nick=f"⁀➷Booster!🧁 ☆ {after.name[:14]} 🍩 ✦", reason="Applying booster nick design")
                if booster_role in roles_lost:  # User no longer boosts MD
                    if "⁀➷Booster!🧁 ☆" in after.nick:  # If they still have "Booster" in their nickname
                        await after.edit(nick=f"✧₊˚🍰⌇{after.name[:23]}🌙⋆｡˚", reason="Removing booster nick design")  # Default nickname design


def setup(bot: bot_data.Bot):
    bot.add_cog(Events(bot))
