import re

import discord
from discord.ext import commands

from utils import generic as default, permissions, generic


async def do_removal(ctx, limit, predicate, *, before=None, after=None, message=True):
    locale = generic.get_lang(ctx.guild)
    if limit > 2000:
        return await generic.send(generic.gls(locale, "removal_message_limit", [f"{limit:,}"]), ctx.channel)
    if before is None:
        before = ctx.message
    else:
        before = discord.Object(id=before)
    if after is not None:
        after = discord.Object(id=after)
    try:
        deleted = await ctx.channel.purge(limit=limit, before=before, after=after, check=predicate)
    except discord.Forbidden:
        return await generic.send(generic.gls(locale, "removal_forbidden"), ctx.channel)
    except discord.HTTPException as e:
        return await generic.send(generic.gls(locale, "removal_error", [e]), ctx.channel)
    _deleted = len(deleted)
    if message is True:
        await generic.send(generic.gls(locale, "removal_success", [_deleted]), ctx.channel, delete_after=10)


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
        self.config = default.get_config

    @commands.command(name="kick")
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick_user(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        """ Kick a user from the server """
        locale = generic.get_lang(ctx.guild)
        invalid = self.config()["owners"]
        invalid.append(self.bot.user.id)
        invalid.append(ctx.guild.owner.id)
        if member == ctx.author:
            return await generic.send(generic.gls(locale, "self_harm_bad"), ctx.channel)
        elif member.top_role.position <= ctx.author.top_role.position:
            return await generic.send(generic.gls(locale, "kick_forbidden"), ctx.channel)
        elif member.id in invalid:
            return await generic.send(generic.gls(locale, "kick_invalid"), ctx.channel)
        try:
            user = self.bot.get_user(member)
            await member.kick(reason=default.reason(ctx.author, reason))
            return await generic.send(generic.gls(locale, "kicked", [member, user, reason]), ctx.channel)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)

    @commands.command(name="ban")
    @commands.guild_only()
    @permissions.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_user(self, ctx: commands.Context, member: MemberID, *, reason: str = None):
        """ Ban a user from the server """
        locale = generic.get_lang(ctx.guild)
        invalid = [o for o in self.config()["owners"]]
        invalid.append(self.bot.user.id)
        if member == ctx.author.id:
            return await generic.send(generic.gls(locale, "self_harm_bad"), ctx.channel)
        elif (them := ctx.guild.get_member(member)) is not None and (them.top_role.position <= ctx.author.top_role.position):
            return await generic.send(generic.gls(locale, "ban_forbidden"), ctx.channel)
        elif member in invalid:
            return await generic.send(generic.gls(locale, "ban_invalid"), ctx.channel)
        try:
            user = self.bot.get_user(member)
            await ctx.guild.ban(discord.Object(id=member), reason=default.reason(ctx.author, reason))
            return await generic.send(generic.gls(locale, "banned", [member, user, reason]), ctx.channel)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)

    @commands.command(name="massban")
    @commands.guild_only()
    @permissions.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def mass_ban(self, ctx: commands.Context, reason: str, *who: MemberID):
        """ Mass ban users from the server """
        locale = generic.get_lang(ctx.guild)
        invalid = [o for o in self.config()["owners"]]
        invalid.append(self.bot.user.id)
        if ctx.author.id in who:
            return await generic.send(generic.gls(locale, "self_harm_bad"), ctx.channel)
        else:
            for member in who:
                if member in invalid:
                    return await generic.send(generic.gls(locale, "ban_invalid"), ctx.channel)
                elif (them := ctx.guild.get_member(member)) is not None and (them.top_role.position <= ctx.author.top_role.position):
                    return await generic.send(generic.gls(locale, "ban_forbidden"), ctx.channel)
        banned = 0
        failed = 0
        for member in who:
            try:
                await ctx.guild.ban(discord.Object(id=member), reason=default.reason(ctx.author, reason))
                banned += 1
            except Exception as e:
                failed += 1
                await generic.send(str(e), ctx.channel)
        return await generic.send(generic.gls(locale, "mass_banned", [banned, failed, reason]), ctx.channel)

    @commands.command(name="unban")
    @commands.guild_only()
    @permissions.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban_user(self, ctx: commands.Context, member: MemberID, *, reason: str = None):
        """ Unban a user """
        try:
            await ctx.guild.unban(discord.Object(id=member), reason=default.reason(ctx.author, reason))
            user = self.bot.get_user(member)
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "unbanned", [member, user, reason]), ctx.channel)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)

    @commands.command(name="nickname", aliases=["nick"])
    @commands.guild_only()
    @permissions.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nickname_user(self, ctx: commands.Context, member: discord.Member, *, name: str = None):
        """ Sets a user's nickname """
        locale = generic.get_lang(ctx.guild)
        try:
            if member.top_role.position <= ctx.author.top_role.position and member != ctx.author:
                return await generic.send(generic.gls(locale, "nick_forbidden"), ctx.channel)
            await member.edit(nick=name, reason=default.reason(ctx.author, "Changed by command"))
            if name is None:
                message = generic.gls(locale, "nickname_reset", [member.name])
            else:
                message = generic.gls(locale, "nickname_changed", [member.name, name])
            return await generic.send(message, ctx.channel)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)

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
        await default.pretty_results(ctx, "playing", f"Found **{len(loop)}** on your search for **{search}**", loop)

    @find.command(name="username", aliases=["name"])
    async def find_name(self, ctx: commands.Context, *, search: str):
        loop = [f"{i} ({i.id})" for i in ctx.guild.members if search.lower() in i.name.lower() and not i.bot]
        await default.pretty_results(ctx, "name", f"Found **{len(loop)}** on your search for **{search}**", loop)

    @find.command(name="nickname", aliases=["nick"])
    async def find_nickname(self, ctx: commands.Context, *, search: str):
        loop = [f"{i.nick} | {i} ({i.id})" for i in ctx.guild.members if i.nick if (search.lower() in i.nick.lower()) and not i.bot]
        await default.pretty_results(ctx, "name", f"Found **{len(loop)}** on your search for **{search}**", loop)

    @find.command(name="discriminator", aliases=["discrim"])
    async def find_discriminator(self, ctx: commands.Context, *, search: str):
        if not len(search) != 4 or not re.compile("^[0-9]*$").search(search):
            return await ctx.send("You must provide exactly 4 digits")
        loop = [f"{i} ({i.id})" for i in ctx.guild.members if search == i.discriminator]
        await default.pretty_results(ctx, "discriminator", f"Found **{len(loop)}** on your search for **{search}**", loop)

    @commands.group(aliases=["purge"])
    @commands.guild_only()
    @permissions.has_permissions(manage_messages=True)
    async def prune(self, ctx: commands.Context):
        """ Removes messages from the current server. """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @prune.command()
    async def embeds(self, ctx: commands.Context, search=100):
        """Removes messages that have embeds in them."""
        await do_removal(ctx, search, lambda e: len(e.embeds))

    @prune.command()
    async def files(self, ctx: commands.Context, search=100):
        """Removes messages that have attachments in them."""
        await do_removal(ctx, search, lambda e: len(e.attachments))

    @prune.command()
    async def mentions(self, ctx: commands.Context, search=100):
        """Removes messages that have mentions in them."""
        await do_removal(ctx, search, lambda e: len(e.mentions) or len(e.role_mentions))

    @prune.command()
    async def images(self, ctx: commands.Context, search=100):
        """Removes messages that have embeds or attachments."""
        await do_removal(ctx, search, lambda e: len(e.embeds) or len(e.attachments))

    @prune.command(name='all')
    async def _remove_all(self, ctx: commands.Context, search=100):
        """Removes all messages."""
        await do_removal(ctx, search, lambda e: True)

    @prune.command()
    async def user(self, ctx: commands.Context, member: discord.Member, search=100):
        """Removes all messages by the member."""
        await do_removal(ctx, search, lambda e: e.author == member)

    @prune.command()
    async def contains(self, ctx: commands.Context, *, substr: str):
        """Removes all messages containing a substring.
        The substring must be at least 3 characters long.
        """
        if len(substr) < 3:
            await ctx.send('The substring length must be at least 3 characters.')
        else:
            await do_removal(ctx, 100, lambda e: substr in e.content)

    @prune.command(name='bots')
    async def _bots(self, ctx: commands.Context, search=100, prefix=None):
        """Removes a bot user's messages and messages with their optional prefix."""
        getprefix = prefix if prefix else self.config()["prefixes"]

        def predicate(m):
            return (m.webhook_id is None and m.author.bot) or m.content.startswith(tuple(getprefix))
        await do_removal(ctx, search, predicate)

    @prune.command(name='users')
    async def _users(self, ctx: commands.Context, search=100):
        """Removes only user messages. """
        def predicate(m):
            return m.author.bot is False
        await do_removal(ctx, search, predicate)

    @prune.command(name='emojis')
    async def _emojis(self, ctx: commands.Context, search=100):
        """Removes all messages containing custom emoji."""
        # custom_emoji = re.compile(r'<(?:a)?:(\w+):(\d+)>')
        custom_emoji = re.compile(r'<(?:a)?:(\w+):(\d{17,18})>')

        def predicate(m):
            return custom_emoji.search(m.content)
        await do_removal(ctx, search, predicate)

    @prune.command(name='reactions')
    async def _reactions(self, ctx: commands.Context, search=100):
        """Removes all reactions from messages that have them."""
        locale = default.get_lang(ctx.guild)
        if search > 2000:
            return await ctx.send(f'Too many messages to search for ({search}/2000)')
        total_reactions = 0
        async for message in ctx.history(limit=search, before=ctx.message):
            if len(message.reactions):
                total_reactions += sum(r.count for r in message.reactions)
                await message.clear_reactions()
        await generic.send(generic.gls(locale, "removal_reactions", [total_reactions]), ctx.channel)


def setup(bot):
    bot.add_cog(Moderation(bot))
