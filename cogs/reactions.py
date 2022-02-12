import re

import discord

from utils import bot_data, commands, permissions

#                  Senko Lair,         RK,                 Imperium
reaction_guilds = [568148147457490954, 738425418637639775, 853385632813678643]


class ReactionRoles(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    async def reaction_handle(self, payload: discord.RawReactionActionEvent, reacted: bool):
        """ Handle reactions """
        if payload.guild_id is None:
            return
        group = self.bot.db.fetchrow("SELECT * FROM reaction_groups WHERE gid=? AND message=?", (payload.guild_id, payload.message_id))
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
        member: discord.Member = guild.get_member(payload.user_id)
        if reacted:
            if group_type in [2, 4]:
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
            if group_type in [3, 4]:  # For Types 3 and 4, you can't leave the role once you're in the group
                return
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

    @commands.group(name="reactiongroup", aliases=["rrg", "rg"])
    @commands.guild_only()
    @permissions.has_permissions(manage_guild=True)
    @commands.check(lambda ctx: ctx.bot.name == "kyomi" or (ctx.guild is not None and ctx.guild.id in reaction_guilds))
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def reaction_group(self, ctx: commands.Context):
        """ Control reaction groups """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @reaction_group.command(name="add")
    async def rg_add(self, ctx: commands.Context, message_id: int, reaction_type: int = 1):
        """ Add a new reaction group """
        group_exists = self.bot.db.fetchrow("SELECT * FROM reaction_groups WHERE gid=? AND message=?", (ctx.guild.id, message_id))
        if group_exists:
            return await ctx.send("A reaction group with this Message ID already exists.")
        if not (1 <= reaction_type <= 4):
            return await ctx.send("Type must be between 1 and 4.")
        self.bot.db.execute("INSERT INTO reaction_groups VALUES (?, ?, ?)", (ctx.guild.id, message_id, reaction_type))
        return await ctx.send(f"Reaction group with ID {message_id} and type {reaction_type} has been added.")

    @reaction_group.command(name="edit")
    async def rg_edit(self, ctx: commands.Context, message_id: int, reaction_type: int):
        """ Change the reaction type of an existing reaction group """
        group_exists = self.bot.db.fetchrow("SELECT * FROM reaction_groups WHERE gid=? AND message=?", (ctx.guild.id, message_id))
        if not group_exists:
            return await ctx.send("A reaction group with this Message ID does not exist.")
        if not (1 <= reaction_type <= 4):
            return await ctx.send("Type must be between 1 and 4.")
        self.bot.db.execute("UPDATE reaction_groups SET type=? WHERE gid=? AND message=?", (reaction_type, ctx.guild.id, message_id))
        return await ctx.send(f"The reaction group with ID {message_id} is now type {reaction_type}.")

    @reaction_group.command(name="remove")
    async def rg_remove(self, ctx: commands.Context, message_id: int):
        """ Remove a reaction group """
        group_exists = self.bot.db.fetchrow("SELECT * FROM reaction_groups WHERE gid=? AND message=?", (ctx.guild.id, message_id))
        if not group_exists:
            return await ctx.send("A reaction group with this Message ID does not exist.")
        self.bot.db.execute("DELETE from reaction_groups WHERE gid=? AND message=?", (ctx.guild.id, message_id))
        return await ctx.send(f"Reaction group with ID {message_id} has been deleted.")

    @reaction_group.command(name="types")
    async def rg_types(self, ctx: commands.Context):
        """ Explains reaction group types """
        return await ctx.send("1 - You can join and leave the roles. You can join multiple within the group (Default)\n"
                              "2 - You can join and leave the roles. You can only have one role within the group\n"
                              "3 - You can join roles but can't leave. You can join multiple within the group\n"
                              "4 - You can join roles but can't leave. You can only have one role within the group")

    @commands.group(name="reactionroles", aliases=["reactionrole", "rr"])
    @commands.guild_only()
    @permissions.has_permissions(manage_guild=True)
    @commands.check(lambda ctx: ctx.bot.name == "kyomi" or (ctx.guild is not None and ctx.guild.id in reaction_guilds))
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def reaction_roles(self, ctx: commands.Context):
        """ Control reaction roles """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @reaction_roles.command(name="add")
    async def rr_add(self, ctx: commands.Context, message_id: int, reaction: str, role: discord.Role):
        """ Add a new reaction role

        Note: Due to the way this command was designed, the bot won't react to the message."""
        group_exists = self.bot.db.fetchrow("SELECT * FROM reaction_groups WHERE gid=? AND message=?", (ctx.guild.id, message_id))
        if not group_exists:
            return await ctx.send("A reaction group with this Message ID does not exist.")
        if re.compile(r"<(a?):(.+):(\d{17,18})>").search(reaction):  # If the reaction is a custom emote
            emoji = reaction.split(":")[2][:-1]
        elif len(reaction) <= 2:  # 2 chars or less, a unicode emoji
            emoji = reaction
        else:
            return await ctx.send("This does not seem to be a valid emoji...")
        reaction1 = self.bot.db.fetchrow("SELECT * FROM reaction_roles WHERE message=? AND reaction=?", (message_id, emoji))
        if reaction1:
            return await ctx.send("This reaction already has a role assigned in this reaction group.")
        reaction2 = self.bot.db.fetchrow("SELECT * FROM reaction_roles WHERE message=? AND role=?", (message_id, role.id))
        if reaction2:
            return await ctx.send("This role already has a reaction assigned in this reaction group.")
        self.bot.db.execute("INSERT INTO reaction_roles VALUES (?, ?, ?)", (message_id, emoji, role.id))
        return await ctx.send(f"Added reaction {reaction} to give role {role} in reaction group {message_id}.")

    @reaction_roles.group(name="edit")
    async def rr_edit(self, ctx: commands.Context):
        """ Change a reaction role within its reaction group """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @rr_edit.command(name="reaction", aliases=["emoji"])
    async def rr_edit_reaction(self, ctx: commands.Context, message_id: int, role: discord.Role, new_reaction: str):
        """ Change a role's reaction in the group """
        group_exists = self.bot.db.fetchrow("SELECT * FROM reaction_groups WHERE gid=? AND message=?", (ctx.guild.id, message_id))
        if not group_exists:
            return await ctx.send("A reaction group with this Message ID does not exist.")
        if re.compile(r"<(a?):(.+):(\d{17,18})>").search(new_reaction):  # If the reaction is a custom emote
            emoji = new_reaction.split(":")[2][:-1]
        elif len(new_reaction) <= 2:  # 2 chars or less, a unicode emoji
            emoji = new_reaction
        else:
            return await ctx.send("This does not seem to be a valid emoji...")
        reaction1 = self.bot.db.fetchrow("SELECT * FROM reaction_roles WHERE message=? AND reaction=?", (message_id, emoji))
        if reaction1:
            return await ctx.send("The new reaction already has a role assigned in this reaction group.")
        reaction2 = self.bot.db.fetchrow("SELECT * FROM reaction_roles WHERE message=? AND role=?", (message_id, role.id))
        if not reaction2:
            return await ctx.send("This role is not available in this reaction group.")
        self.bot.db.execute("UPDATE reaction_roles SET reaction=? WHERE message=? AND role=?", (emoji, message_id, role.id))
        return await ctx.send(f"The role {role} is now assigned to the reaction {new_reaction} in the group {message_id}.")

    @rr_edit.command(name="role")
    async def rr_edit_role(self, ctx: commands.Context, message_id: int, reaction: str, new_role: discord.Role):
        """ Change a reaction's role in the group """
        group_exists = self.bot.db.fetchrow("SELECT * FROM reaction_groups WHERE gid=? AND message=?", (ctx.guild.id, message_id))
        if not group_exists:
            return await ctx.send("A reaction group with this Message ID does not exist.")
        if re.compile(r"<(a?):(.+):(\d{17,18})>").search(reaction):  # If the reaction is a custom emote
            emoji = reaction.split(":")[2][:-1]
        elif len(reaction) <= 2:  # 2 chars or less, a unicode emoji
            emoji = reaction
        else:
            return await ctx.send("This does not seem to be a valid emoji...")
        reaction1 = self.bot.db.fetchrow("SELECT * FROM reaction_roles WHERE message=? AND reaction=?", (message_id, emoji))
        if not reaction1:
            return await ctx.send("This reaction does not have any role assigned in this reaction group.")
        reaction2 = self.bot.db.fetchrow("SELECT * FROM reaction_roles WHERE message=? AND role=?", (message_id, new_role.id))
        if reaction2:
            return await ctx.send("The new role is already available in this reaction group.")
        self.bot.db.execute("UPDATE reaction_roles SET role=? WHERE message=? AND reaction=?", (new_role.id, message_id, emoji))
        return await ctx.send(f"The reaction {reaction} now assigns the role {new_role} in the group {message_id}.")

    @reaction_roles.group(name="remove")
    async def rr_remove(self, ctx: commands.Context):
        """ Remove a reaction role (by reaction or role) from the reaction group """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @rr_remove.command(name="reaction", aliases=["emoji"])
    async def rr_remove_reaction(self, ctx: commands.Context, message_id: int, reaction: str):
        """ Remove the reaction from the reaction group """
        group_exists = self.bot.db.fetchrow("SELECT * FROM reaction_groups WHERE gid=? AND message=?", (ctx.guild.id, message_id))
        if not group_exists:
            return await ctx.send("A reaction group with this Message ID does not exist.")
        if re.compile(r"<(a?):(.+):(\d{17,18})>").search(reaction):  # If the reaction is a custom emote
            emoji = reaction.split(":")[2][:-1]
        elif len(reaction) <= 2:  # 2 chars or less, a unicode emoji
            emoji = reaction
        else:
            return await ctx.send("This does not seem to be a valid emoji...")
        self.bot.db.execute("DELETE FROM reaction_roles WHERE message=? AND reaction=?", (message_id, emoji))
        return await ctx.send(f"The reaction {reaction} has been removed from the group {message_id}.")

    @rr_remove.command(name="role")
    async def rr_remove_role(self, ctx: commands.Context, message_id: int, role: discord.Role):
        """ Remove the role from the reaction group """
        group_exists = self.bot.db.fetchrow("SELECT * FROM reaction_groups WHERE gid=? AND message=?", (ctx.guild.id, message_id))
        if not group_exists:
            return await ctx.send("A reaction group with this Message ID does not exist.")
        self.bot.db.execute("DELETE FROM reaction_roles WHERE message=? AND role=?", (message_id, role))
        return await ctx.send(f"The role {role} has been removed from the group {message_id}.")


def setup(bot: bot_data.Bot):
    bot.add_cog(ReactionRoles(bot))
