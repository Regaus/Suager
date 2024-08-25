import discord
from discord import app_commands

from utils import bot_data, commands, permissions, reactions


class ReactionRoles(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    async def reaction_handle(self, payload: discord.RawReactionActionEvent, reacted: bool):
        """ Handle reactions """
        if payload.guild_id is None:
            return
        if payload.user_id == self.bot.user.id:
            return
        group = self.bot.db.fetchrow("SELECT * FROM reaction_groups WHERE gid=? AND message=? AND bot=?", (payload.guild_id, payload.message_id, self.bot.name))
        if not group:
            return
        group_type = group["type"]
        # reacted = payload.event_type == "REACTION_ADD"  # Check whether the user reacted or unreacted to the message
        emoji = payload.emoji.name if payload.emoji.id is None else str(payload.emoji.id)
        roles = self.bot.db.fetchrow("SELECT * FROM reaction_roles WHERE message=? AND reaction=?", (payload.message_id, emoji))
        if not roles:
            return
        guild: discord.Guild = self.bot.get_guild(payload.guild_id)
        role: discord.Role = guild.get_role(roles["role"])
        if not role:
            return await guild.get_channel(payload.channel_id).send(f"The role {roles['role']} was not found...")
        member: discord.Member = guild.get_member(payload.user_id)
        if reacted:
            if group_type in (2, 4):
                has_role = self.bot.db.fetchrow("SELECT * FROM reaction_tracking WHERE message=? AND uid=?", (payload.message_id, payload.user_id))
                if has_role:  # For Types 2 and 4, you can't have more than one role per group
                    return
                else:
                    self.bot.db.execute("INSERT INTO reaction_tracking VALUES (?, ?)", (payload.message_id, payload.user_id))
            try:
                await member.add_roles(role, reason="Reaction Roles")
            except discord.Forbidden:
                try:
                    await guild.get_channel(payload.channel_id).send(f"I can't give the role {role}, because I don't have enough permissions.")
                except discord.Forbidden:
                    pass
        else:
            if group_type in (3, 4):  # For Types 3 and 4, you can't leave the role once you're in the group
                return
            if role in member.roles:  # Only try to take away the role if the member actually has it
                if group_type == 2:
                    self.bot.db.execute("DELETE FROM reaction_tracking WHERE message=? AND uid=?", (payload.message_id, payload.user_id))
                try:
                    await member.remove_roles(role, reason="Reaction Roles")
                except discord.Forbidden:
                    try:
                        await guild.get_channel(payload.channel_id).send(f"I can't take away the role {role}, because I don't have enough permissions.")
                    except discord.Forbidden:
                        pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """ Reaction was added to a message """
        return await self.reaction_handle(payload, True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """ Reaction was removed from a message """
        return await self.reaction_handle(payload, False)

    @commands.hybrid_group(name="reactionroles", aliases=["rr"], case_insensitive=True)
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    @app_commands.default_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True, read_message_history=True, add_reactions=True)
    @app_commands.guild_install()
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def reaction_roles(self, ctx: commands.Context):
        """ Control reaction roles """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @reaction_roles.command(name="create", aliases=["add", "c", "a"])
    @app_commands.describe(
        channel="The channel where the new reaction role group will be created",
        existing_message_id="(Optional) The ID of an existing message, for which the new group will be created",
    )
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)  # For some reason using this on the base command doesn't work???
    async def add_reaction_group(self, ctx: commands.Context, channel: discord.TextChannel, existing_message_id: int = None):
        """ Create a new reaction role group """
        language = ctx.language()
        bot_permissions = channel.permissions_for(ctx.guild.me)
        if not all((bot_permissions.read_messages, bot_permissions.send_messages, bot_permissions.read_message_history, bot_permissions.add_reactions)):
            return await ctx.send(language.string("reaction_roles_bad_channel"))
        reaction_message: discord.Message | None = None
        if existing_message_id is not None:
            # This doesn't care which bot the message belongs to - as long as it exists, it's a problem
            reaction_group = self.bot.db.fetchrow("SELECT * FROM reaction_groups WHERE gid=? AND message=?", (ctx.guild.id, existing_message_id))
            if reaction_group and reaction_group["bot"] != self.bot.name:
                bot_name = language.data2("generic_bot_names", reaction_group["bot"])
                return await ctx.send(language.string("reaction_roles_group_bot2", bot=language.case(bot_name, case="with")))
            if reaction_group:
                return await ctx.send(language.string("reaction_roles_group_exists", p=ctx.prefix))
            try:
                reaction_message = await channel.fetch_message(existing_message_id)
            except discord.NotFound:
                return await ctx.send(language.string("reaction_roles_group_not_found"))
        # message = await ctx.send(language.string("reaction_roles_group_setup", channel=channel.mention, reaction_type="1", message_preview=language.string("reaction_roles_message_empty")))
        message = await ctx.send(language.string("reaction_roles_message_loading"), allowed_mentions=reactions.NO_ALLOWED_MENTIONS)
        view = reactions.ReactionGroupSetupView(ctx.author, message, ctx, language, channel, reaction_message, self.bot)
        return await message.edit(content=view.full_message_content, view=view)

    @reaction_roles.command(name="edit", aliases=["update", "e", "u"])
    @app_commands.describe(message_id="The ID of the message whose reaction role group will be edited")
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def edit_reaction_group(self, ctx: commands.Context, message_id: int):
        """ Edit an existing reaction role group """
        language = ctx.language()
        reaction_group = self.bot.db.fetchrow("SELECT * FROM reaction_groups WHERE gid=? AND message=?", (ctx.guild.id, message_id))
        if not reaction_group:
            return await ctx.send(language.string("reaction_roles_group_not_found3e", p=ctx.prefix))
        if reaction_group["bot"] != self.bot.name:
            bot_name = language.data2("generic_bot_names", reaction_group["bot"])
            return await ctx.send(language.string("reaction_roles_group_bot", bot=language.case(bot_name, case="with")))
        try:
            channel = ctx.guild.get_channel(reaction_group["channel"])
            reaction_message = await channel.fetch_message(message_id)
        except discord.NotFound:
            return await ctx.send(language.string("reaction_roles_group_not_found2e"))
        message = await ctx.send(language.string("reaction_roles_message_loading"), allowed_mentions=reactions.NO_ALLOWED_MENTIONS)
        view = reactions.ReactionGroupEditView(ctx.author, message, ctx, language, channel, reaction_message, self.bot)
        return await message.edit(content=view.full_message_content, view=view)

    @reaction_roles.command(name="remove", aliases=["delete", "r", "d"])
    @app_commands.describe(message_id="The ID of the message whose reaction role group will be removed")
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def remove_reaction_group(self, ctx: commands.Context, message_id: int):
        """ Remove a reaction role group """
        language = ctx.language()
        reaction_group = self.bot.db.fetchrow("SELECT * FROM reaction_groups WHERE gid=? AND message=?", (ctx.guild.id, message_id))
        if not reaction_group:
            return await ctx.send(language.string("reaction_roles_group_not_found3d"))
        if reaction_group["bot"] != self.bot.name:
            bot_name = language.data2("generic_bot_names", reaction_group["bot"])
            return await ctx.send(language.string("reaction_roles_group_bot", bot=language.case(bot_name, case="with")))
        try:
            channel = ctx.guild.get_channel(reaction_group["channel"])
            reaction_message = await channel.fetch_message(message_id)
        except discord.NotFound:
            return await ctx.send(language.string("reaction_roles_group_not_found2d"))
        message = await ctx.send(language.string("reaction_roles_message_loading"), allowed_mentions=reactions.NO_ALLOWED_MENTIONS)
        view = reactions.ReactionGroupRemoveView(ctx.author, message, ctx, language, reaction_message, self.bot)
        return await message.edit(content=view.full_message_content, view=view)


async def setup(bot: bot_data.Bot):
    await bot.add_cog(ReactionRoles(bot))
