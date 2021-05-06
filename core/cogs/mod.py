import json
import re
from io import BytesIO

import discord
from discord.ext import commands

from core.utils import general, permissions, emotes, time
from languages import langs


async def do_removal(ctx, limit, predicate, *, before=None, after=None, message=True):
    if limit > 2000:
        return await general.send(f"Too many messages to search given ({limit:,}/2,000)", ctx.channel)
    if before is None:
        before = ctx.message
    else:
        before = discord.Object(id=before)
    if after is not None:
        after = discord.Object(id=after)
    try:
        deleted = await ctx.channel.purge(limit=limit, before=before, after=after, check=predicate)
    except discord.Forbidden:
        return await general.send("I don't have the permissions to delete messages", ctx.channel)
    except discord.HTTPException as e:
        return await general.send(f"An error has occurred: `{type(e).__name__}: {e}`\nTry a smaller search?", ctx.channel)
    _deleted = len(deleted)
    if message is True:
        await general.send(f"🚮 Successfully removed {_deleted:,} messages", ctx.channel, delete_after=10)


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
        if member == ctx.author:
            return await general.send(f"Self harm bad {emotes.BlobCatPolice}", ctx.channel)
        elif member.id == ctx.guild.owner.id:
            return await general.send("Imagine trying to kick the server's owner, lol", ctx.channel)
        elif (member.top_role.position >= ctx.author.top_role.position) and ctx.author != ctx.guild.owner:
            return await general.send("You can't kick a member whose top role is equal to or is above yours.", ctx.channel)
        # elif member.id in self.admins:
        #     return await general.send("I can't kick my owners or admins...", ctx.channel)
        elif member.id == self.bot.user.id:
            return await general.send(f"We are not friends anymore, {ctx.author.name}.", ctx.channel)
        try:
            user = str(member)
            await member.kick(reason=general.reason(ctx.author, reason))
            return await general.send(f"{emotes.Allow} Successfully kicked **{user}** for {reason}", ctx.channel)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="ban")
    @commands.guild_only()
    @permissions.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_user(self, ctx: commands.Context, member: MemberID, *, reason: str = None):
        """ Ban a user from the server """
        if member == ctx.author.id:
            return await general.send(f"Self harm bad {emotes.BlobCatPolice}", ctx.channel)
        elif member == ctx.guild.owner.id:
            return await general.send("Imagine trying to ban the server's owner, lol", ctx.channel)
        elif (them := ctx.guild.get_member(member)) is not None and (them.top_role.position >= ctx.author.top_role.position) and ctx.author != ctx.guild.owner:
            return await general.send("You can't ban a member whose top role is equal to or is above yours.", ctx.channel)
        # elif member in self.admins:
        #     return await general.send("I can't ban my owners or admins...", ctx.channel)
        elif member == self.bot.user.id:
            return await general.send(f"We are not friends anymore, {ctx.author.name}.", ctx.channel)
        try:
            user = await self.bot.fetch_user(member)
            await ctx.guild.ban(discord.Object(id=member), reason=general.reason(ctx.author, reason))
            return await general.send(f"{emotes.Allow} Successfully banned **{member} ({user})** for **{reason}**", ctx.channel)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="massban")
    @commands.guild_only()
    @permissions.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def mass_ban(self, ctx: commands.Context, reason: str, *who: MemberID):
        """ Mass ban users from the server """
        if ctx.author.id in who:
            return await general.send(f"Self harm bad {emotes.BlobCatPolice}", ctx.channel)
        else:
            for member in who:
                # if member in self.admins:
                #     return await general.send("I can't ban my owners or admins...", ctx.channel)
                if member == self.bot.user.id:
                    return await general.send(f"We are not friends anymore, {ctx.author.name}.", ctx.channel)
                if member == ctx.guild.owner.id:
                    return await general.send("Imagine trying to ban the server's owner, lol", ctx.channel)
                elif (them := ctx.guild.get_member(member)) is not None and (them.top_role.position >= ctx.author.top_role.position) \
                        and ctx.author != ctx.guild.owner:
                    return await general.send("You can't ban a member whose top role is equal to or is above yours.", ctx.channel)
        banned = 0
        failed = 0
        for member in who:
            try:
                await ctx.guild.ban(discord.Object(id=member), reason=general.reason(ctx.author, reason))
                banned += 1
            except Exception as e:
                failed += 1
                await general.send(f"{type(e).__name__}: {e}", ctx.channel)
        total = banned + failed
        return await general.send(f"Mass-banned **{total} users** for {reason}:\n{emotes.Allow} Successful: **{banned}**\n"
                                  f"{emotes.Deny} Failed: **{failed}**", ctx.channel)

    @commands.command(name="unban")
    @commands.guild_only()
    @permissions.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban_user(self, ctx: commands.Context, member: MemberID, *, reason: str = None):
        """ Unban a user """
        try:
            await ctx.guild.unban(discord.Object(id=member), reason=general.reason(ctx.author, reason))
            user = await self.bot.fetch_user(member)
            return await general.send(f"{emotes.Allow} Successfully unbanned **{member} ({user})** for {reason}", ctx.channel)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="nickname", aliases=["nick"])
    @commands.guild_only()
    @permissions.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nickname_user(self, ctx: commands.Context, member: discord.Member, *, name: str = None):
        """ Sets a user's nickname """
        try:
            if member.id == ctx.guild.owner.id:
                return await general.send("The server owner's nickname can't be edited.", ctx.channel)
            if (member.top_role.position >= ctx.author.top_role.position and member != ctx.author) and ctx.author != ctx.guild.owner:
                return await general.send("You can't change the nickname of a member whose top role is equal to or is above yours.", ctx.channel)
            await member.edit(nick=name, reason=general.reason(ctx.author, "Changed by command"))
            if name is None:
                message = f"Reset **{member}**'s nickname"
            else:
                message = f"Changed **{member}**'s nickname to **{name}**"
            return await general.send(message, ctx.channel)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="nicknameme", aliases=["nickme", "nameme"])
    @commands.guild_only()
    @permissions.has_permissions(change_nickname=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nickname_self(self, ctx: commands.Context, *, name: str = None):
        """ Change your own nickname """
        try:
            if ctx.author.id == ctx.guild.owner.id:
                return await general.send("I can't change the server owner's nickname.", ctx.channel)
            await ctx.author.edit(nick=name, reason=general.reason(ctx.author, "Changed by command"))
            if name is None:
                message = f"Reset your nickname"
            else:
                message = f"Changed your nickname to **{name}**"
            return await general.send(message, ctx.channel)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="mute")
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.check(lambda ctx: ctx.bot.name == "suager")
    async def mute_user(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        """ Mute a user """
        if member.id == self.bot.user.id:
            return await general.send("Why did you bring me to this server... just to mute me?", ctx.channel)
        if member == ctx.author:
            return await general.send(f"Self harm bad {emotes.BlobCatPolice}", ctx.channel)
        # if (member.top_role.position >= ctx.author.top_role.position) and ctx.author != ctx.guild.owner:  # and ctx.guild.id not in [784357864482537473]:
        #     return await general.send("You aren't supposed to mute people above you.", ctx.channel)
        _reason = general.reason(ctx.author, reason)
        _data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not _data:
            return await general.send(f"This server does not seem to have a mute role set. Use `{ctx.prefix}settings` to set one.", ctx.channel)
        data = json.loads(_data["data"])
        try:
            mute_role_id = data["mute_role"]
        except KeyError:
            return await general.send("This server has no mute role set, or it no longer exists.", ctx.channel)
        mute_role = ctx.guild.get_role(mute_role_id)
        if not mute_role:
            return await general.send("This server has no mute role set, or it no longer exists.", ctx.channel)
        try:
            await member.add_roles(mute_role, reason=_reason)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)
        out = f"{emotes.Allow} Successfully muted **{member}** for **{reason}**"
        if reason is not None:
            _duration = reason.split(" ")[0]
            delta = time.interpret_time(_duration)
            expiry, error = time.add_time(delta)
            if time.rd_is_above_5y(delta):
                await general.send("You can't specify a time range above 5 years. Making mute permanent...", ctx.channel)
                error = True
            if error:
                pass  # Quietly ignore any errors, since it's probably someone fucking around, or it's not a duration to begin with
                # await general.send(f"Failed to convert duration: {expiry} | Making mute permanent...", ctx.channel)
            else:
                random_id = general.random_id(ctx)
                self.bot.db.execute("INSERT INTO temporary VALUES (?, ?, ?, ?, ?, ?, ?)", (member.id, "mute", expiry, ctx.guild.id, None, random_id, 0))
                duration = langs.td_rd(delta, "en", accuracy=7, brief=False, suffix=False)
                reason = " ".join(reason.split(" ")[1:])
                out = f"{emotes.Allow} Successfully muted **{member}** for **{duration}** for **{reason}**"
        return await general.send(out, ctx.channel)

    @commands.command(name="mutes", aliases=["punishments"])
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    @commands.check(lambda ctx: ctx.bot.name == "suager")
    async def temp_mutes(self, ctx: commands.Context):
        """ See a list of your currently active temporary mutes """
        reminders = self.bot.db.fetch("SELECT * FROM temporary WHERE gid=? AND type='mute' ORDER BY expiry", (ctx.guild.id,))
        if not reminders:
            return await general.send(f"No one is temporarily muted at the moment in {ctx.guild.name}.", ctx.channel)
        output = f"List of currently active temporary mutes in **{ctx.guild.name}**"
        outputs = []
        _reminder = 0
        for reminder in reminders:
            _reminder += 1
            expiry = reminder["expiry"]
            expires_on = langs.gts(expiry, "en", True, True, False, True, False)
            expires_in = langs.td_dt(expiry, "en", accuracy=3, brief=False, suffix=True)
            who = self.bot.get_user(reminder["uid"])
            outputs.append(f"**{_reminder})** {who}\nMuted until {expires_on}\nExpires {expires_in}")
        output2 = "\n\n".join(outputs)
        if len(output2) > 1900:
            _data = BytesIO(str(output2).encode('utf-8'))
            return await general.send(output, ctx.channel, file=discord.File(_data, filename=f"{time.file_ts('Reminders')}"))
        else:
            return await general.send(f"{output}\n{output2}", ctx.channel)

    @commands.command(name="unmute")
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.check(lambda ctx: ctx.bot.name == "suager")
    async def unmute_user(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        """ Unmute a user """
        if member == ctx.author:
            return await general.send(f"Imagine trying to unmute yourself {emotes.BlobCatPolice}", ctx.channel)
        _reason = general.reason(ctx.author, reason)
        _data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not _data:
            return await general.send(f"This server does not seem to have a mute role set. Use `{ctx.prefix}settings` to set one.", ctx.channel)
        data = json.loads(_data["data"])
        try:
            mute_role_id = data["mute_role"]
        except KeyError:
            return await general.send("This server has no mute role set, or it no longer exists.", ctx.channel)
        mute_role = ctx.guild.get_role(mute_role_id)
        if not mute_role:
            return await general.send("This server has no mute role set, or it no longer exists.", ctx.channel)
        try:
            await member.remove_roles(mute_role, reason=_reason)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)
        self.bot.db.execute("DELETE FROM temporary WHERE uid=? AND type='mute' AND gid=?", (member.id, ctx.guild.id))
        return await general.send(f"{emotes.Allow} Successfully unmuted **{member}** for **{reason}**", ctx.channel)

    @commands.group()
    @commands.guild_only()
    @permissions.has_permissions(ban_members=True)
    async def find(self, ctx: commands.Context):
        """ Finds a user within your search term """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @find.command(name="playing")
    async def find_playing(self, ctx: commands.Context, *, search: str):
        loop = [f"{i} | {i.activity.name} ({i.id})" for i in ctx.guild.members if i.activity if (search.lower() in i.activity.name.lower()) and (not i.bot)]
        await general.pretty_results(ctx, "playing", f"Found **{len(loop)}** on your search for **{search}**", loop)

    @find.command(name="username", aliases=["name"])
    async def find_name(self, ctx: commands.Context, *, search: str):
        loop = [f"{i} ({i.id})" for i in ctx.guild.members if search.lower() in i.name.lower() and not i.bot]
        await general.pretty_results(ctx, "name", f"Found **{len(loop)}** on your search for **{search}**", loop)

    @find.command(name="nickname", aliases=["nick"])
    async def find_nickname(self, ctx: commands.Context, *, search: str):
        loop = [f"{i.nick} | {i} ({i.id})" for i in ctx.guild.members if i.nick if (search.lower() in i.nick.lower()) and not i.bot]
        await general.pretty_results(ctx, "name", f"Found **{len(loop)}** on your search for **{search}**", loop)

    @find.command(name="discriminator", aliases=["discrim"])
    async def find_discriminator(self, ctx: commands.Context, *, search: str):
        if not len(search) != 4 or not re.compile("^[0-9]*$").search(search):
            return await ctx.send("You must provide exactly 4 digits")
        loop = [f"{i} ({i.id})" for i in ctx.guild.members if search == i.discriminator]
        await general.pretty_results(ctx, "discriminator", f"Found **{len(loop)}** on your search for **{search}**", loop)

    @commands.group(aliases=["purge"])
    @commands.guild_only()
    @permissions.has_permissions(manage_messages=True)
    async def prune(self, ctx: commands.Context):
        """ Removes messages from the current server. """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @prune.command(name="embeds")
    async def embeds(self, ctx: commands.Context, search=100):
        """Removes messages that have embeds in them."""
        await do_removal(ctx, search, lambda e: len(e.embeds))

    @prune.command(name="files")
    async def files(self, ctx: commands.Context, search=100):
        """Removes messages that have attachments in them."""
        await do_removal(ctx, search, lambda e: len(e.attachments))

    @prune.command(name="mentions")
    async def mentions(self, ctx: commands.Context, search=100):
        """Removes messages that have mentions in them."""
        await do_removal(ctx, search, lambda e: len(e.mentions) or len(e.role_mentions))

    @prune.command(name="images")
    async def images(self, ctx: commands.Context, search=100):
        """Removes messages that have embeds or attachments."""
        await do_removal(ctx, search, lambda e: len(e.embeds) or len(e.attachments))

    @prune.command(name="all")
    async def _remove_all(self, ctx: commands.Context, search=100):
        """Removes all messages."""
        await do_removal(ctx, search, lambda e: True)

    @prune.command(name="user")
    async def user(self, ctx: commands.Context, user: discord.User, search=100):
        """Removes all messages by the member."""
        await do_removal(ctx, search, lambda e: e.author == user)

    @prune.command(name="contains")
    async def contains(self, ctx: commands.Context, *, substr: str):
        """Removes all messages containing a substring.
        The substring must be at least 3 characters long.
        """
        if len(substr) < 3:
            await ctx.send('The substring length must be at least 3 characters.')
        else:
            await do_removal(ctx, 100, lambda e: substr in e.content)

    @prune.command(name="bots")
    async def _bots(self, ctx: commands.Context, search=100, prefix=None):
        """Removes a bot user's messages and messages with their optional prefix."""
        get_prefix = prefix if prefix else self.bot.local_config["prefixes"]

        def predicate(m):
            return (m.webhook_id is None and m.author.bot) or m.content.startswith(tuple(get_prefix))
        await do_removal(ctx, search, predicate)

    @prune.command(name="users")
    async def _users(self, ctx: commands.Context, search=100):
        """Removes only user messages. """
        def predicate(m):
            return m.author.bot is False
        await do_removal(ctx, search, predicate)

    @prune.command(name="emojis", aliases=["emotes"])
    async def _emoji(self, ctx: commands.Context, search=100):
        """Removes all messages containing custom emoji."""
        # custom_emoji = re.compile(r'<(?:a)?:(\w+):(\d+)>')
        custom_emoji = re.compile(r'<(?:a)?:(\w+):(\d{17,18})>')

        def predicate(m):
            return custom_emoji.search(m.content)
        await do_removal(ctx, search, predicate)

    @prune.command(name="reactions")
    async def _reactions(self, ctx: commands.Context, search=100):
        """Removes all reactions from messages that have them."""
        if search > 2000:
            return await ctx.send(f'Too many messages to search for ({search:,}/2000)')
        total_reactions = 0
        async for message in ctx.history(limit=search, before=ctx.message):
            if len(message.reactions):
                total_reactions += sum(r.count for r in message.reactions)
                await message.clear_reactions()
        await general.send(f"🚮 Successfully removed {total_reactions:,} reactions.", ctx.channel)


def setup(bot):
    bot.add_cog(Moderation(bot))
