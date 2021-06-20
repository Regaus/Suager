from io import BytesIO
from typing import List

import discord
from discord.ext import commands

from core.utils import general, logger, time
from languages import langs


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db
        self.config = self.bot.config
        self.local_config = self.bot.local_config
        self.blocked = [667187968145883146]
        self.bad = ["re", "rag", "<@302851022790066185>", "<@!302851022790066185>"]
        self.updates = [572857995852251169, 740665941712568340, 786008719657664532, 796755072427360256, 843876833221148713]
        self.blocked_logs = self.bot.get_channel(739183533792297164)
        self.message_ignore = [671520521174777869, 672535025698209821, 681647810357362786, 705947617779253328, 721705731937665104, 725835449502924901,
                               571025667265658881, 571025667265658881, 571278954523000842, 573636220622471168, 571030189451247618, 582598504233304075,
                               571031080908357633, 674342275421175818, 764528556507922442, 742885168997466196, 798513492697153536, 799714065256808469]
        self.dm_logger = 806884278037643264

    @commands.Cog.listener()
    async def on_message(self, ctx: discord.Message):
        if ctx.guild is None:  # it's a DM
            if ctx.author.id != self.bot.user.id:  # isn't Suager himself
                await general.send(f"{ctx.author} ({ctx.author.id}) | {time.time()}\n{ctx.content}", self.bot.get_channel(self.dm_logger))
        if self.blocked_logs is not None:
            if ctx.author.id in self.blocked:
                for word in self.bad:
                    if word in ctx.content.lower():
                        gid = ctx.guild.id if ctx.guild is not None else "not a guild"
                        await general.send(f"{ctx.author} ({ctx.author.id}) | {ctx.guild} ({gid}) | {ctx.channel.mention} ({ctx.channel.name} - "
                                           f"{ctx.channel.id}) | {time.time()}\n{ctx.content}", self.blocked_logs)
                        break
        if self.bot.name == "suager":
            if ctx.channel.id == 742886280911913010:
                for channel_id in self.updates:
                    channel = self.bot.get_channel(channel_id)
                    try:
                        if channel is not None:
                            await general.send(f"{ctx.author} | Suager updates | {time.time()}\n{ctx.content}", channel)
                        else:
                            general.print_error(f"on_message > Update announcement > Channel {channel_id} was not found...")
                    except Exception as e:
                        general.print_error(f"on_message > Update announcement > {channel_id} > {type(e).__name__}: {e}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, err):
        locale = langs.gl(ctx)
        if isinstance(err, commands.errors.MissingRequiredArgument) or isinstance(err, commands.errors.BadArgument):
            helper = str(ctx.invoked_subcommand) if ctx.invoked_subcommand else str(ctx.command)
            await ctx.send_help(helper)
        elif isinstance(err, commands.errors.CommandInvokeError):
            error = general.traceback_maker(err.original, ctx.message.content[:1000], ctx.guild, ctx.author)
            if "2000 or fewer" in str(err) and len(ctx.message.clean_content) > 1900:
                return await general.send(langs.gls("events_err_message_too_long", locale), ctx.channel)
                # return general.send("You inputted a very long piece of text.. Well, congrats. The command broke.", ctx.channel)
            await general.send(langs.gls("events_err_error", locale, type(err.original).__name__, str(err.original)), ctx.channel)
            # await general.send(f"{emotes.Deny} An error has occurred:\n`{type(err.original).__name__}: {err.original}`", ctx.channel)
            ec = self.bot.get_channel(self.bot.local_config["error_channel"])
            if ec is not None:
                await ec.send(error)
        elif isinstance(err, commands.errors.CheckFailure):
            pass
        elif isinstance(err, commands.errors.CommandOnCooldown):
            await general.send(langs.gls("events_err_cooldown", locale, langs.gfs(err.retry_after, locale)), ctx.channel)
            # await general.send(f"This command is currently on cooldown... Try again in {err.retry_after:.2f} seconds.", ctx.channel)
        elif isinstance(err, commands.errors.CommandNotFound):
            pass
        elif isinstance(err, commands.errors.MaxConcurrencyReached):
            await general.send(langs.gls("events_err_concurrency", locale), ctx.channel)
            # await general.send("Maximum concurrency has been reached - try again later.", ctx.channel)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        send = f"{time.time()} > {self.bot.internal_name} > Joined {guild.name} ({guild.id})"
        if self.local_config["logs"]:
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
        send = f"{time.time()} > {self.bot.internal_name} > Left {guild.name} ({guild.id})"
        if self.local_config["logs"]:
            logger.log(self.bot.name, "guilds", send)
        print(send)
        if self.bot.name == "suager":
            self.db.execute("DELETE FROM leveling WHERE gid=?", (guild.id,))
            self.db.execute("DELETE FROM locales WHERE gid=?", (guild.id,))
            self.db.execute("DELETE FROM settings WHERE gid=?", (guild.id,))
            self.db.execute("DELETE FROM starboard WHERE gid=?", (guild.id,))
            self.db.execute("DELETE FROM tags WHERE gid=?", (guild.id,))
            self.db.execute("DELETE FROM tbl_guild WHERE gid=?", (guild.id,))

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        try:
            g = ctx.guild.name
        except AttributeError:
            g = "Private Message"
        content = ctx.message.clean_content
        send = f"{time.time()} > {self.bot.internal_name} > {g} > {ctx.author} ({ctx.author.id}) > {content}"
        if self.local_config["logs"]:
            logger.log(self.bot.name, "commands", send)
        print(send)
        try:
            self.bot.usages[str(ctx.command)] += 1
        except KeyError:
            self.bot.usages[str(ctx.command)] = 1

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        logger.log(self.bot.name, "members", f"{time.time()} > {self.bot.internal_name} > {member} ({member.id}) just joined {member.guild.name}")
        if self.bot.name == "suager":
            if member.guild.id == 568148147457490954:
                members = len(member.guild.members)
                await general.send(f"Welcome **{member.name}** to Senko Lair!\nThere are now **{members}** members.", self.bot.get_channel(610836120321785869))
                if time.now() < time.dt(2022):
                    role = member.guild.get_role(794699877325471776)
                    await member.add_roles(role, reason="Joining Senko Lair during 2021.")
                else:
                    await general.send("<@302851022790066185> Update the code for 2022 role", self.bot.get_channel(610482988123422750))
            if member.guild.id == 738425418637639775:
                join = langs.gts(member.joined_at, "en", seconds=True)
                age = langs.td_dt(member.created_at, "en")
                await general.send(f"Welcome {member.name} to Regaus' Playground!\nJoin time: {join}\nAccount age: {age}", self.bot.get_channel(754425619336396851))
            if member.guild.id == 806811462345031690:
                role = member.guild.get_role(841403040534888458)
                await member.add_roles(role, reason="Welcome to /bin/games!")
                await general.send(f"Welcome to {member.guild.name}, {member.name}!", self.bot.get_channel(841405544686551044))
        if member.guild.id in [568148147457490954, 738425418637639775] and member.id not in [302851022790066185]:
            if member.name[0] < "A":
                await member.edit(reason="De-hoist", nick=f"\u17b5{member.name[:31]}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        logger.log(self.bot.name, "members", f"{time.time()} > {self.bot.internal_name} > {member} ({member.id}) just left {member.guild.name}")
        if self.bot.name == "suager":
            if member.guild.id == 568148147457490954:
                survival = langs.td_dt(member.joined_at, "en")
                remaining = len(member.guild.members)
                await general.send(f"**{member.name}** just **abandoned** Senko Lair...\nThey had survived for {survival}...\n"
                                   f"**{remaining}** Senkoists remaining.", self.bot.get_channel(610836120321785869))
            if member.guild.id == 738425418637639775:
                survival = langs.td_dt(member.joined_at, "en")
                await general.send(f"{member.name} just abandoned Regaus' Playground after surviving for {survival}...", self.bot.get_channel(754425619336396851))
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

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User or discord.Member):
        logger.log(self.bot.name, "members", f"{time.time()} > {self.bot.internal_name} > {user} ({user.id}) just got banned from {guild.name}")
        message = f"{user} ({user.id}) has been **banned** from {guild.name}"
        if self.bot.name == "suager":
            if guild.id == 568148147457490954:
                await general.send(message, self.bot.get_channel(626028890451869707))
            if guild.id == 738425418637639775:
                await general.send(message, self.bot.get_channel(764469594303234078))

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        logger.log(self.bot.name, "members", f"{time.time()} > {self.bot.internal_name} > {user} ({user.id}) just got unbanned from {guild.name}")
        message = f"{user} ({user.id}) has been **unbanned** from {guild.name}"
        if self.bot.name == "suager":
            if guild.id == 568148147457490954:
                await general.send(message, self.bot.get_channel(626028890451869707))
            if guild.id == 738425418637639775:
                await general.send(message, self.bot.get_channel(764469594303234078))

    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self.bot, 'uptime'):
            self.bot.uptime = time.now(None)
        self.blocked_logs = self.bot.get_channel(739183533792297164)
        print(f"{time.time()} > {self.bot.internal_name} > Ready: {self.bot.user} - {len(self.bot.guilds)} servers, {len(self.bot.users)} users")
        playing = f"Loading... | v{general.get_version()[self.bot.name]['short_version']}"
        await self.bot.change_presence(activity=discord.Game(name=playing), status=discord.Status.dnd)
        if self.local_config["logs"]:
            logger.log(self.bot.name, "uptime", f"{time.time()} > {self.bot.internal_name} > Bot is online")

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        async def process_msg(cid: int):
            output = f"A message was deleted in {message.channel.mention} ({message.channel.id})\nAuthor: {message.author}\n" \
                     f"Message sent: {message.created_at}\nMessage content: {message.content[:1850]}"
            files = []
            for attachment in message.attachments:
                file = BytesIO()
                try:
                    await attachment.save(file)
                except (discord.NotFound, discord.HTTPException):
                    pass
                files.append(discord.File(file, filename=attachment.filename))
            embed = message.embeds[0] if message.embeds else None
            await general.send(output, self.bot.get_channel(cid), embed=embed, files=files)

        if self.bot.name == "suager":
            if message.guild.id in [568148147457490954, 738425418637639775]:
                if message.channel.id not in self.message_ignore:
                    if not message.author.bot:
                        await process_msg(764473671090831430 if message.guild.id == 568148147457490954 else 764494075663351858)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: List[discord.Message]):
        async def process_msg(cid: int):
            output = f"A message was deleted in {message.channel.mention} ({message.channel.id})\nAuthor: {message.author}\n" \
                     f"Message sent: {message.created_at}\nMessage content: {message.content[:1850]}"
            files = []
            for attachment in message.attachments:
                file = BytesIO()
                try:
                    await attachment.save(file)
                except (discord.NotFound, discord.HTTPException):
                    pass
                files.append(discord.File(file, filename=attachment.filename))
            embed = message.embeds[0] if message.embeds else None
            await general.send(output, self.bot.get_channel(cid), embed=embed, files=files)
        if self.bot.name == "suager":
            for message in messages:
                if message.guild.id in [568148147457490954, 738425418637639775]:
                    if message.channel.id not in self.message_ignore:
                        if not message.author.bot:
                            await process_msg(764473671090831430 if message.guild.id == 568148147457490954 else 764494075663351858)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        async def process_msg(cid: int):
            embed = discord.Embed(description=f"Message was edited in {after.channel.mention} ({after.channel.id})\n"
                                              f"Author: {after.author}\nMessage sent: {after.created_at}\nMessage edited: {after.edited_at}")
            embed.add_field(name="Content Before", value=before.content[:1024], inline=False)
            embed.add_field(name="Content After", value=after.content[:1024], inline=False)
            await general.send(None, self.bot.get_channel(cid), embed=embed)

        if self.bot.name == "suager":
            if after.guild is not None and after.guild.id in [568148147457490954, 738425418637639775]:
                if after.channel.id not in self.message_ignore:
                    if not after.author.bot:
                        if after.content != before.content:
                            await process_msg(764473671090831430 if after.guild.id == 568148147457490954 else 764494075663351858)


def setup(bot):
    bot.add_cog(Events(bot))
