# This holds the views for Reaction Roles.

from __future__ import annotations

from contextlib import suppress
from typing import Type

import discord
from typing_extensions import override

from utils import views, languages, commands, database, bot_data


NO_ALLOWED_MENTIONS = discord.AllowedMentions(everyone=False, users=False, roles=False, replied_user=False)
DELETION_DELAY = 30
KEEP_EMOJI = "⬅️"
CANCEL_EMOJI = "✖️"
DELETE_EMOJI = "🗑️"
REACTION_STYLES = [
    "{emoji} {role}",
    "{emoji} -> {role}",
    "{emoji} - {role}",
    "{emoji} > {role}",
    "{emoji} = {role}",
    "- {emoji} {role}",
    "- {emoji} -> {role}",
    "- {emoji} - {role}",
    "- {emoji} > {role}",
    "- {emoji} = {role}",
    "- {emoji} {role}",
    "> {emoji} -> {role}",
    "> {emoji} - {role}",
    "> {emoji} > {role}",
    "> {emoji} = {role}",
    "> {emoji} {role}",
]


class ReactionGroupView(views.TranslatedView):
    def __init__(self, sender: discord.Member, message: discord.Message, ctx: commands.Context, language: languages.Language,
                 channel: discord.TextChannel, existing_message: discord.Message | None, bot: bot_data.Bot):
        super().__init__(sender=sender, message=message, ctx=ctx, language=language)
        self.ctx: commands.Context = ctx
        self.channel: discord.TextChannel = channel
        # self.message_id: int | None = existing_message_id
        self.reaction_message: discord.Message | None = existing_message
        self.reaction_type: int = 1
        self.message_start: str = ""
        self.message_end: str = ""
        self.preview_title: str = "reaction_roles_group_setup"
        self.success_string: str = "reaction_roles_group_setup_complete"
        self.reaction_style = "{emoji} -> {role}"
        self.bot: bot_data.Bot = bot
        self.db: database.Database = self.bot.db
        self.empty_string = self.language.string("reaction_roles_message_empty")
        self.reaction_roles: list[ReactionRole] = []
        self.save_button.print_override = True
        self.references: list[EphemeralView] = []  # A list of views that reference this one, so that they can be destroyed when cancelling the changes
        self._saving: bool = False  # Prevent the user from being able to press "Done" multiple times

    @override
    async def on_timeout(self):
        try:
            await self.message.edit(content=self.language.string("reaction_roles_timeout"), view=None)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass
        self.stop()

    def is_emoji_already_used(self, emoji: discord.PartialEmoji, ignore_idx: int = None) -> bool:
        """ Returns whether an emoji is already used in this reaction group """
        return any(reaction_role.emoji == emoji for i, reaction_role in enumerate(self.reaction_roles) if i != ignore_idx)

    def is_role_already_used(self, role: discord.Role, ignore_idx: int = None) -> bool:
        """ Returns whether a role is already used in this reaction group """
        return any(reaction_role.role == role for i, reaction_role in enumerate(self.reaction_roles) if i != ignore_idx)

    def add_reaction_role(self, emoji: discord.PartialEmoji, role: discord.Role) -> None:
        """ Append a new reaction role to the list """
        self.reaction_roles.append(ReactionRole(emoji=emoji, role=role))

    @discord.ui.button(label="reaction_roles_button_add_reaction", emoji="➕", style=discord.ButtonStyle.primary, row=0)  # Blue, first row
    async def add_reaction_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Add a new reaction role """
        if len(self.reaction_roles) >= 20:
            return await interaction.response.send_message(self.language.string("reaction_roles_add_reaction_limit"), ephemeral=True)  # type: ignore
        try:
            return await AddReactionView.send(self, interaction)
        except RuntimeError:
            return await interaction.followup.send(self.language.string("reaction_roles_add_reaction_limit", ephemeral=True))  # The message is responded to in EphemeralView.send_view()

    @discord.ui.button(label="reaction_roles_button_edit_reaction", emoji="➰", style=discord.ButtonStyle.primary, row=0, disabled=True)  # Blue, first row
    async def edit_reaction_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Edit a reaction role """
        if not self.reaction_roles:
            return await interaction.response.send_message(self.language.string("reaction_roles_edit_reaction_none"), ephemeral=True)  # type: ignore
        return await EditReactionRoleView.send(self, interaction)

    @discord.ui.button(label="reaction_roles_button_remove_reaction", emoji="➖", style=discord.ButtonStyle.primary, row=0, disabled=True)  # Blue, first row
    async def remove_reaction_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Remove a reaction role """
        if not self.reaction_roles:
            return await interaction.response.send_message(self.language.string("reaction_roles_edit_reaction_none"), ephemeral=True)  # type: ignore
        return await RemoveReactionRoleView.send(self, interaction)

    @discord.ui.button(label="reaction_roles_button_group_type", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def change_group_type(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Change the reaction group type """
        return await ReactionTypeView.send(self, interaction)

    @discord.ui.button(label="reaction_roles_button_group_style", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def change_reaction_style(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Change the reaction role list style """
        return await ReactionStyleView.send(self, interaction)

    @discord.ui.button(label="reaction_roles_button_group_message", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def change_message_start_and_end(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Change the start and end of the output message """
        return await interaction.response.send_modal(MessagePartsModal(self))  # type: ignore

    @property
    def message_content(self):
        """ Returns the dynamic part of the message content (start, end, and roles list) """
        output = []
        if self.message_start:  # Only append the title if it is non-empty
            output.append(self.message_start)
        for reaction_role in self.reaction_roles:
            output.append(self.reaction_style.format(emoji=str(reaction_role.emoji), role=reaction_role.role.mention))
        if self.message_end:
            output.append(self.message_end)
        if not output:
            return self.empty_string
        return "\n".join(output)

    @property
    def full_message_content(self):
        """ Returns the full message contents, including the setup-related text """
        return self.language.string(self.preview_title, channel=self.channel.mention, reaction_type=str(self.reaction_type), message_preview=self.message_content)

    def update_buttons(self):
        """ Update the buttons to reflect the current state of the editor """
        # Cannot add reaction if there are already 20, cannot edit/remove reactions if there are none
        _reaction_role_count = len(self.reaction_roles)
        self.add_reaction_button.disabled = _reaction_role_count >= 20
        self.edit_reaction_button.disabled = self.remove_reaction_button.disabled = _reaction_role_count < 1
        self.save_button.disabled = _reaction_role_count < 1 or _reaction_role_count > 20  # Must be 1-20 reaction roles to be able to save

    async def update_setup_message(self):
        """ Update the message we're using """
        if self.is_finished():  # Don't update the message if the view is no longer interacting
            return await self.message.edit(view=None)
        self.update_buttons()
        output = self.full_message_content
        if len(output) > 2000:
            return await self.message.edit(view=self, content=self.language.string("reaction_roles_message_long"))
        return await self.message.edit(view=self, content=output, allowed_mentions=NO_ALLOWED_MENTIONS)

    @discord.ui.button(label="generic_button_cancel", emoji=CANCEL_EMOJI, style=discord.ButtonStyle.danger, row=4)
    async def cancel_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Cancel all changes and exit """
        if self._saving:
            return await interaction.response.send_message(self.language.string("reaction_roles_group_cancel_save"), ephemeral=True)  # type: ignore
        return await ConfirmCancellationView.send(self, interaction)

    async def save_action(self, interaction: discord.Interaction):
        """ The actions to do to save the changes made """
        raise NotImplementedError("This method must be overridden by subclasses")

    @discord.ui.button(label="generic_button_done", emoji="☑️", style=discord.ButtonStyle.success, row=4, disabled=True)
    async def save_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Save changes and exit """
        await interaction.response.defer()  # type: ignore
        if self._saving:
            return await interaction.followup.send(self.language.string("reaction_roles_group_save_already"), ephemeral=True)
        # Ensure we have a valid amount of reaction roles - Should not happen but just in case.
        if len(self.reaction_roles) > 20:
            return await interaction.followup.send(self.language.string("reaction_roles_group_save_invalid_reaction_limit"), ephemeral=True)
        if not self.reaction_roles:
            return await interaction.followup.send(self.language.string("reaction_roles_group_save_invalid_reaction_none"), ephemeral=True)
        if len(self.message_content) > 2000:
            return await self.message.edit(view=self, content=self.language.string("reaction_roles_message_long2"))
        if self.references:  # Let's hope this never gets erroneously filled in prod
            # print("\n".join(ref.command for ref in self.references))
            return await interaction.followup.send(self.language.string("reaction_roles_group_save_other_open"), ephemeral=True)
        self._saving = True
        try:
            for item in self.children:
                if item != self.save_button and item != self.cancel_button:
                    self.remove_item(item)
            await self.message.edit(view=self)
            # return await interaction.followup.send("DEBUG: Save button disabled.")
            # # noinspection PyUnreachableCode
            # Save the message and send it to the channel
            _ret = await self.save_action(interaction)
            if _ret is None:  # if the value returns something, something is wrong - don't proceed.
                await self.message.edit(content=self.language.string(self.success_string), view=None)
                # await self.message.edit(view=None)
                # await interaction.followup.send(self.language.string(self.success_string))
                with suppress(discord.NotFound, discord.Forbidden):
                    await self.message.clear_reactions()
                self.stop()
        finally:
            self._saving = False  # Disable saving state at the end even if something goes wrong


class ReactionGroupSetupView(ReactionGroupView):
    @override
    async def save_action(self, interaction: discord.Interaction):
        if self.reaction_message is None:
            self.reaction_message = await self.channel.send(self.message_content, allowed_mentions=NO_ALLOWED_MENTIONS)
        else:
            if self.reaction_message.author.id == self.bot.user.id:
                self.reaction_message = await self.reaction_message.edit(content=self.message_content, allowed_mentions=NO_ALLOWED_MENTIONS)
            else:
                await interaction.followup.send(self.language.string("reaction_roles_message_author"), allowed_mentions=NO_ALLOWED_MENTIONS)
                await interaction.followup.send(self.message_content, allowed_mentions=NO_ALLOWED_MENTIONS)
        self.db.execute("INSERT INTO reaction_groups(gid, channel, message, type, start, end, style, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (self.channel.guild.id, self.channel.id, self.reaction_message.id, self.reaction_type, self.message_start, self.message_end, self.reaction_style, self.bot.name))
        for i, reaction_role in enumerate(self.reaction_roles):
            await self.reaction_message.add_reaction(reaction_role.emoji)
            self.db.execute("INSERT INTO reaction_roles(message, ord, reaction, role) VALUES (?, ?, ?, ?)",
                            (self.reaction_message.id, i, reaction_role.emoji_id, reaction_role.role.id))


class ReactionGroupEditView(ReactionGroupView):
    def __init__(self, sender: discord.Member, message: discord.Message, ctx: commands.Context, language: languages.Language,
                 channel: discord.TextChannel, existing_message: discord.Message, bot: bot_data.Bot):
        if existing_message is None:
            raise ValueError(f"existing_message cannot be None for {self.__class__.__name__}")
        super().__init__(sender=sender, message=message, ctx=ctx, language=language, channel=channel, existing_message=existing_message, bot=bot)
        data = self.db.fetchrow("SELECT * FROM reaction_groups WHERE message=?", (self.reaction_message.id,))
        self.reaction_type: int = data["type"]
        self.message_start: str = data["start"]
        self.message_end: str = data["end"]
        self.reaction_style: str = data["style"]
        self.guild: discord.Guild = self.reaction_message.guild
        reaction_roles_data = self.db.fetch("SELECT * FROM reaction_roles WHERE message=?", (self.reaction_message.id,))
        reaction_roles_data.sort(key=lambda rr: rr["ord"])
        for reaction_role in reaction_roles_data:
            if reaction_role["reaction"].isdigit():
                _emoji_id = int(reaction_role["reaction"])
                _emoji = self.bot.get_emoji(_emoji_id)
                if _emoji:
                    emoji = discord.PartialEmoji(name=_emoji.name, id=_emoji.id, animated=_emoji.animated)
                else:
                    emoji = discord.PartialEmoji(name="UnknownEmoji", id=_emoji_id, animated=False)
            else:
                emoji = discord.PartialEmoji.from_str(reaction_role["reaction"])
            role = self.guild.get_role(reaction_role["role"])
            self.reaction_roles.append(ReactionRole(emoji, role))
        self._original_reactions: list[ReactionRole] = [ReactionRole(rr.emoji, rr.role) for rr in self.reaction_roles]
        self._original_reactions_len: int = len(self._original_reactions)
        self.preview_title: str = "reaction_roles_group_edit"
        self.success_string: str = "reaction_roles_group_edit_complete"
        self._data_saved: bool = False
        self.update_buttons()

    @override
    async def save_action(self, interaction: discord.Interaction):
        if not self._data_saved:
            if self.reaction_message.author.id == self.bot.user.id:
                self.reaction_message = await self.reaction_message.edit(content=self.message_content, allowed_mentions=NO_ALLOWED_MENTIONS)
            else:
                await interaction.followup.send(self.language.string("reaction_roles_message_author"))
                await interaction.followup.send(self.message_content)
            self.db.execute("UPDATE reaction_groups SET type=?, start=?, end=?, style=? WHERE message=?",
                            (self.reaction_type, self.message_start, self.message_end, self.reaction_style, self.reaction_message.id))
            if len(self.reaction_roles) < self._original_reactions_len:
                self.db.execute("DELETE FROM reaction_roles WHERE message=? AND ord>=?", (self.reaction_message.id, len(self.reaction_roles)))
            for i, reaction_role in enumerate(self.reaction_roles):
                params = (self.reaction_message.id, i, reaction_role.emoji_id, reaction_role.role.id)
                if i < self._original_reactions_len:
                    self.db.execute("UPDATE reaction_roles SET reaction=?3, role=?4 WHERE message=?1 AND ord=?2", params)
                else:
                    self.db.execute("INSERT INTO reaction_roles(message, ord, reaction, role) VALUES (?, ?, ?, ?)", params)
            self._data_saved = True
        # _emojis_changed: bool = False
        # for original_reaction, new_reaction in zip(self.reaction_roles, self._original_reactions):
        #     if original_reaction.emoji != new_reaction.emoji:
        #         _emojis_changed = True
        #         break
        if self._data_saved:  # Re-fetch the message to check if reactions have been cleared
            self.reaction_message = await self.reaction_message.fetch()
            # _emojis_changed = bool(self.reaction_message.reactions)
        if self.reaction_message.reactions and self.reaction_roles != self._original_reactions:  # Only update reactions if there is a difference in the list of reaction roles
            try:
                await self.reaction_message.clear_reactions()
            except discord.Forbidden:
                for item in self.children:
                    item.disabled = True
                self.save_button.disabled = False
                await self.message.edit(view=self)
                return await interaction.followup.send(self.language.string("reaction_roles_message_reactions", channel=self.reaction_message.channel.mention))
        for i, reaction_role in enumerate(self.reaction_roles):
            await self.reaction_message.add_reaction(reaction_role.emoji)


class ReactionGroupRemoveView(views.TranslatedView):
    """ Represents the view for removing a reaction role """
    def __init__(self, sender: discord.Member, message: discord.Message, ctx: commands.Context, language: languages.Language, reaction_message: discord.Message, bot: bot_data.Bot):
        super().__init__(sender=sender, message=message, ctx=ctx, language=language)
        self.ctx: commands.Context = ctx
        self.reaction_message: discord.Message = reaction_message
        self.channel: discord.TextChannel = self.reaction_message.channel
        self.guild: discord.Guild = self.reaction_message.guild
        self.bot: bot_data.Bot = bot
        self.db: database.Database = self.bot.db
        # self._reaction_group = reaction_group
        roles = self.db.fetch("SELECT * FROM reaction_roles WHERE message=?", (self.reaction_message.id,))
        self._roles: list[discord.Role] = [self.guild.get_role(role["role"]) for role in roles]
        self.delete_group.print_override = True

    @property
    def full_message_content(self) -> str:
        """ The message content shown when the view is initialised """
        return self.language.string("reaction_roles_group_delete", roles=", ".join(role.mention for role in self._roles))

    @discord.ui.button(label="reaction_roles_group_delete_keep", emoji=KEEP_EMOJI, style=discord.ButtonStyle.primary, row=0)
    async def keep_group(self, _interaction: discord.Interaction, _: discord.ui.Button):
        await self.message.delete()
        self.stop()

    @discord.ui.button(label="reaction_roles_group_delete_confirm", emoji=DELETE_EMOJI, style=discord.ButtonStyle.danger, row=0)
    async def delete_group(self, _interaction: discord.Interaction, _: discord.ui.Button):
        self.db.execute("DELETE FROM reaction_groups WHERE message=?", (self.reaction_message.id,))
        self.db.execute("DELETE FROM reaction_roles WHERE message=?", (self.reaction_message.id,))
        new_view = DeleteMessageView(self.sender, self.message, self.ctx, self.language, self.reaction_message)
        return await self.message.edit(content=self.language.string("reaction_roles_group_delete_success"), view=new_view)


class DeleteMessageView(views.TranslatedView):
    def __init__(self, sender: discord.Member, message: discord.Message, ctx: commands.Context, language: languages.Language, reaction_message: discord.Message):
        super().__init__(sender=sender, message=message, ctx=ctx, language=language)
        self.reaction_message: discord.Message = reaction_message

    @discord.ui.button(label="reaction_roles_group_delete_message", emoji=DELETE_EMOJI, style=discord.ButtonStyle.danger, row=0)
    async def delete_message(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Deletes the reaction message """
        await interaction.response.defer()  # type: ignore
        try:
            await self.reaction_message.delete()
        except discord.NotFound:
            await self.message.edit(content=self.language.string("reaction_roles_group_delete_success2"), view=None)
            return await interaction.followup.send(self.language.string("reaction_roles_group_delete_message_not_found"), ephemeral=True)
        except discord.Forbidden:
            return await interaction.followup.send(self.language.string("reaction_roles_group_delete_message_permissions"), ephemeral=True)
        return await self.message.edit(content=self.language.string("reaction_roles_group_delete_message_success"), view=None)


class ReactionRole:
    """ A class representing a reaction role """
    def __init__(self, emoji: discord.PartialEmoji, role: discord.Role):
        self._emoji = emoji
        self._role = role

    @property
    def emoji(self) -> discord.PartialEmoji:
        """ The custom or Unicode emoji used for the reaction """
        return self._emoji

    @emoji.setter
    def emoji(self, new_emoji: discord.PartialEmoji, /):
        self._emoji = new_emoji

    @property
    def emoji_id(self) -> str:
        """ The ID/name of the emoji stored in the database """
        return self._emoji.id if self._emoji.is_custom_emoji() else self._emoji.name

    @property
    def role(self) -> discord.Role:
        """ The role associated with the reaction emoji """
        return self._role

    @role.setter
    def role(self, new_role: discord.Role, /):
        self._role = new_role

    def to_select_option(self, idx: int) -> discord.SelectOption:
        return discord.SelectOption(label=self.role.name, emoji=self.emoji, value=str(idx))

    def __eq__(self, other: ReactionRole):
        return self.emoji == other.emoji and self.role == other.role


class EphemeralView(views.TranslatedView):
    def __init__(self, original_view: ReactionGroupView):
        super().__init__(original_view.sender, original_view.message, None, original_view.language)
        self.original_view = original_view
        self.original_view.references.append(self)
        self.language = self.original_view.language
        self.command = f"{self.original_view.command} > {self.__class__.__name__}"

    @override
    def stop(self):
        self.original_view.references.remove(self)
        super().stop()

    @classmethod
    async def send_view(cls, original_view: ReactionGroupView, interaction: discord.Interaction, translation_string: str | None, *translation_args, **translation_kwargs):
        await interaction.response.defer()  # type: ignore
        if len(original_view.references) >= 5 and not issubclass(cls, ConfirmCancellationView):
            return await interaction.followup.send(original_view.language.string("reaction_roles_view_limit"), ephemeral=True)
        new_view = cls(original_view)
        content = new_view.language.string(translation_string, *translation_args, **translation_kwargs) if translation_string else None
        new_view.message = await interaction.followup.send(content=content, ephemeral=True, allowed_mentions=NO_ALLOWED_MENTIONS, view=new_view)
        return new_view

    @classmethod
    async def send(cls, original_view: views.TranslatedView, interaction: discord.Interaction):
        raise NotImplementedError("This method must be overridden by subclasses")


class ConfirmCancellationView(EphemeralView):
    def __init__(self, original_view: ReactionGroupView):
        super().__init__(original_view)
        self.confirm_cancellation.print_override = True

    @classmethod
    @override
    async def send(cls, original_view: ReactionGroupView, interaction: discord.Interaction):
        if isinstance(original_view, ReactionGroupSetupView):
            translation_string = "reaction_roles_group_setup_cancel"
        elif isinstance(original_view, ReactionGroupEditView):
            translation_string = "reaction_roles_group_edit_cancel"
        else:
            raise TypeError(f"Unexpected interface {original_view.__class__.__name__} received")
        return await super().send_view(original_view, interaction, translation_string)

    @discord.ui.button(label="generic_button_keep_changes", emoji=KEEP_EMOJI, style=discord.ButtonStyle.primary, row=0)
    async def go_back(self, _interaction: discord.Interaction, _: discord.ui.Button):
        await self.message.delete()
        self.stop()

    @discord.ui.button(label="generic_button_cancel_confirm", emoji=CANCEL_EMOJI, style=discord.ButtonStyle.danger, row=0)
    async def confirm_cancellation(self, _interaction: discord.Interaction, _: discord.ui.Button):
        cancelled_string = None
        if isinstance(self.original_view, ReactionGroupSetupView):
            cancelled_string = "reaction_roles_group_setup_cancelled"
        elif isinstance(self.original_view, ReactionGroupEditView):
            cancelled_string = "reaction_roles_group_edit_cancelled"
        try:  # Try to remove all reactions from the message
            await self.original_view.message.clear_reactions()
        except discord.Forbidden:
            pass
        await self.message.delete()
        self.stop()
        await self.original_view.message.edit(content=self.language.string(cancelled_string), view=None)
        self.original_view.stop()
        for view in self.original_view.references:
            try:
                await view.message.edit(content=self.language.string(cancelled_string), view=None)
                await view.message.delete(delay=DELETION_DELAY)
            except (discord.NotFound, discord.Forbidden):
                pass


class ReactionRoleEditView(EphemeralView):
    title_text: str = "placeholder"
    cancel_text: str = "placeholder"
    success_text: str = "placeholder"

    def __init__(self, original_view: ReactionGroupView):
        super().__init__(original_view)
        self.unset = self.language.string("reaction_roles_unset")
        self.emoji: discord.PartialEmoji | None = None
        self.role: discord.Role | None = None
        self.bot: bot_data.Bot = original_view.bot
        self.idx: int | None = None
        self._emoji_invalid: bool = False
        self._role_invalid: bool = False

        self.add_item(RoleSelect(self, "reaction_roles_role"))

    @property
    def emoji_string(self) -> str:
        return str(self.emoji) if self.emoji else self.unset

    @property
    def role_string(self) -> str:
        return self.role.mention if self.role else self.unset

    @classmethod
    @override
    async def send(cls, original_view: ReactionGroupView, interaction: discord.Interaction):
        unset = original_view.language.string("reaction_roles_unset")
        return await super().send_view(original_view, interaction, cls.title_text, emoji=unset, role=unset)

    async def update_message(self):
        self.save_button.disabled = not self.emoji or not self.role
        return await self.message.edit(content=self.language.string(self.title_text, emoji=self.emoji_string, role=self.role_string), view=self)

    @discord.ui.button(label="reaction_roles_button_set_emoji", style=discord.ButtonStyle.primary, row=1)
    async def set_emoji(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Set the emoji used for the reaction """
        return await interaction.response.send_modal(ReactionEmojiModal(self))  # type: ignore

    @discord.ui.button(label="generic_button_cancel", emoji="❌", style=discord.ButtonStyle.danger, row=1)
    async def cancel_button(self, _interaction: discord.Interaction, _: discord.ui.Button):
        """ Cancel the creation of a new reaction """
        await self.message.edit(content=self.language.string(self.cancel_text), view=None)
        await self.message.delete(delay=DELETION_DELAY)
        self.stop()

    async def save_action(self):
        """ The action to do when saving the results to the main view """
        raise NotImplementedError("This method must be overridden by subclasses")

    @discord.ui.button(label="generic_button_done", emoji="☑️", style=discord.ButtonStyle.success, row=1, disabled=True)  # Disabled until both emoji and role are set
    async def save_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Save changes and exit """
        await interaction.response.defer()  # type: ignore
        # Make sure the emoji and role are actually set - Should not happen at this stage, but just in case
        if self.emoji is None:
            return await interaction.followup.send(self.language.string("reaction_roles_emoji_none"), ephemeral=True)
        if self.role is None:
            return await interaction.followup.send(self.language.string("reaction_roles_role_none"), ephemeral=True)
        # Make sure the emoji and role are not already used
        if self.original_view.is_emoji_already_used(self.emoji, ignore_idx=self.idx):
            return await interaction.followup.send(self.language.string("reaction_roles_emoji_used"), ephemeral=True)
        if self.original_view.is_role_already_used(self.role, ignore_idx=self.idx):
            return await interaction.followup.send(self.language.string("reaction_roles_role_used"), ephemeral=True)
        # Make sure the emoji is valid
        if self._emoji_invalid:
            return await interaction.followup.send(self.language.string("reaction_roles_add_reaction_invalid_emoji"), ephemeral=True)
        if (original_emoji := getattr(self, "_original_emoji", None)) is not None and original_emoji != self.emoji:  # The emoji was changed (EditReactionView)
            try:
                await self.original_view.message.remove_reaction(original_emoji, self.bot.user)
            except (discord.NotFound, discord.Forbidden):  # Shouldn't happen but whatever
                pass
        try:
            await self.original_view.message.add_reaction(self.emoji)
        except (discord.NotFound, TypeError):
            self._emoji_invalid = True
            return await interaction.followup.send(self.language.string("reaction_roles_add_reaction_not_found"), ephemeral=True)
        except discord.Forbidden:
            self._emoji_invalid = True
            return await interaction.followup.send(self.language.string("reaction_roles_add_reaction_forbidden"), ephemeral=True)
        # Make sure the role is valid
        if self._role_invalid:  # The role was marked as invalid and it did not change
            return await interaction.followup.send(self.language.string("reaction_roles_add_reaction_invalid_role"), ephemeral=True)
        if getattr(self, "_original_role", None) != self.role:  # The role was changed (EditReactionView) | Always triggered for AddReactionView
            try:
                reason = self.language.string("reaction_roles_audit_reason2")
                await self.original_view.sender.add_roles(self.role, reason=reason)
                await self.original_view.sender.remove_roles(self.role, reason=reason)
            except discord.Forbidden:
                self._role_invalid = True
                return await interaction.followup.send(self.language.string("reaction_roles_add_reaction_forbidden2"), ephemeral=True)
        # Success: Add/Update the reaction role and exit
        await self.save_action()
        await self.message.edit(content=self.language.string(self.success_text), view=None)
        await self.message.delete(delay=DELETION_DELAY)
        await self.original_view.update_setup_message()
        self.stop()


class FromReactionRole(EphemeralView):
    idx: int

    @classmethod
    @override
    async def send_view(cls, original_view: ReactionGroupView, interaction: discord.Interaction, translation_string: str, *translation_args, **translation_kwargs):
        raise NotImplementedError(f"This method is not supported by this class. Use {cls.__name__}.from_reaction_role(original_view, interaction, reaction_role_idx) instead.")

    @classmethod
    @override
    async def send(cls, original_view: ReactionGroupView, interaction: discord.Interaction):
        raise NotImplementedError(f"This method is not supported by this class. Use {cls.__name__}.from_reaction_role(original_view, interaction, reaction_role_idx) instead.")

    @classmethod
    async def from_reaction_role(cls, interface: EditReactionRoleView | RemoveReactionRoleView, interaction: discord.Interaction, reaction_role_idx: int):
        """ Create an editing view from a reaction role """
        raise NotImplementedError("This method must be implemented by subclasses")

    @staticmethod
    def validity_check(original_view: ReactionGroupView, reaction_role_idx: int):
        """ Make sure we are not trying to modify a role that is already being modified """
        for view in original_view.references:
            if isinstance(view, FromReactionRole) and view.idx == reaction_role_idx:
                return False
        return True


class AddReactionView(ReactionRoleEditView):
    original_view: ReactionGroupView
    title_text: str = "reaction_roles_add_reaction"
    cancel_text: str = "reaction_roles_add_reaction_cancelled"
    success_text: str = "reaction_roles_add_reaction_done"

    def __init__(self, original_view: ReactionGroupView):
        roles = len(original_view.reaction_roles)
        for ref in original_view.references:
            if isinstance(ref, self.__class__):
                roles += 1
        if roles >= 20:  # There are already 20 reactions, or there will be 20 reactions if all existing AddReactionViews finish successfully
            raise RuntimeError(f"Spawning a new {self.__class__} might lead to having more than 20 reactions in the group.")
        super().__init__(original_view)

    @override
    async def save_action(self):
        self.original_view.add_reaction_role(self.emoji, self.role)


class EditReactionView(ReactionRoleEditView, FromReactionRole):
    original_view: ReactionGroupView
    title_text: str = "reaction_roles_edit_reaction"
    cancel_text: str = "reaction_roles_edit_reaction_cancelled"
    success_text: str = "reaction_roles_edit_reaction_done"

    def __init__(self, original_view: ReactionGroupView, reaction_role_idx: int):
        super().__init__(original_view)
        self.idx = reaction_role_idx
        reaction_role = self.original_view.reaction_roles[self.idx]
        self.emoji = self._original_emoji = reaction_role.emoji
        self.role = self._original_role = reaction_role.role
        self.save_button.disabled = False  # Enabled by default

    @classmethod
    @override
    async def send_view(cls, original_view: ReactionGroupView, interaction: discord.Interaction, translation_string: str, *translation_args, **translation_kwargs):
        raise NotImplementedError(f"This method is not supported by this class. Use {cls.__name__}.from_reaction_role(original_view, interaction, reaction_role_idx) instead.")

    @classmethod
    @override
    async def send(cls, original_view: ReactionGroupView, interaction: discord.Interaction):
        raise NotImplementedError(f"This method is not supported by this class. Use {cls.__name__}.from_reaction_role(original_view, interaction, reaction_role_idx) instead.")

    @classmethod
    @override
    async def from_reaction_role(cls, interface: EditReactionRoleView, interaction: discord.Interaction, reaction_role_idx: int):
        """ Create an editing view from a reaction role """
        if not cls.validity_check(interface.original_view, reaction_role_idx):
            return await interaction.followup.send(interface.language.string("reaction_roles_edit_reaction_already"), ephemeral=True)
        new_view = cls(interface.original_view, reaction_role_idx)
        new_view.message = await interface.message.edit(content=new_view.language.string(new_view.title_text, emoji=new_view.emoji_string, role=new_view.role_string),
                                                        allowed_mentions=NO_ALLOWED_MENTIONS, view=new_view)
        return new_view

    @override
    async def save_action(self):
        self.original_view.reaction_roles[self.idx].emoji = self.emoji
        self.original_view.reaction_roles[self.idx].role = self.role


class RemoveReactionView(FromReactionRole):
    original_view: ReactionGroupView

    def __init__(self, original_view: ReactionGroupView, reaction_role_idx: int):
        super().__init__(original_view)
        self.idx = reaction_role_idx
        self.reaction_role: ReactionRole = self.original_view.reaction_roles[self.idx]

    @classmethod
    @override
    async def from_reaction_role(cls, interface: RemoveReactionRoleView, interaction: discord.Interaction, reaction_role_idx: int):
        """ Create an editing view from a reaction role """
        if not cls.validity_check(interface.original_view, reaction_role_idx):
            return await interaction.followup.send(interface.language.string("reaction_roles_edit_reaction_already"), ephemeral=True)
        new_view = cls(interface.original_view, reaction_role_idx)
        reaction_role = interface.original_view.reaction_roles[reaction_role_idx]
        emoji: str = str(reaction_role.emoji)
        role: str = reaction_role.role.mention
        new_view.message = await interface.message.edit(content=new_view.language.string("reaction_roles_remove_reaction", emoji=emoji, role=role),
                                                        allowed_mentions=NO_ALLOWED_MENTIONS, view=new_view)
        return new_view

    @discord.ui.button(label="reaction_roles_button_remove_keep", emoji=KEEP_EMOJI, style=discord.ButtonStyle.primary, row=0)
    async def go_back(self, _interaction: discord.Interaction, _: discord.ui.Button):
        await self.message.delete()
        self.stop()

    @discord.ui.button(label="reaction_roles_button_remove_reaction", emoji=DELETE_EMOJI, style=discord.ButtonStyle.danger, row=0)
    async def confirm_deletion(self, interaction: discord.Interaction, _: discord.ui.Button):
        if self.reaction_role not in self.original_view.reaction_roles:
            await interaction.response.defer()  # type: ignore
            await self.message.edit(content=self.language.string("reaction_roles_remove_reaction_not_found"), view=None)
            await self.message.delete(delay=DELETION_DELAY)
            self.stop()
            return
        await self.message.edit(content=self.language.string("reaction_roles_remove_reaction_done"), view=None)
        await self.message.delete(delay=DELETION_DELAY)
        removed_role = self.original_view.reaction_roles.pop(self.idx)
        await self.original_view.update_setup_message()
        try:
            await self.original_view.message.remove_reaction(removed_role.emoji, self.original_view.bot.user)
        except (discord.NotFound, discord.Forbidden):  # Shouldn't happen but whatever
            pass
        self.stop()


class ReactionEmojiModal(views.Modal):
    """ A modal sent when adding a new reaction role """
    interface: ReactionRoleEditView
    text_input: discord.ui.TextInput[ReactionEmojiModal]

    def __init__(self, interface: ReactionRoleEditView):
        self.language = interface.language
        super().__init__(interface=interface, title=self.language.string("reaction_roles_modal_emoji_label"))
        self.bot = interface.bot
        self._emoji_output: str | None = None
        self.text_input = discord.ui.TextInput(
            label=self.language.string("reaction_roles_modal_emoji_label"),
            placeholder=self.language.string("reaction_roles_modal_emoji_placeholder"),
            style=discord.TextStyle.short, required=True, min_length=1, max_length=50, row=0
        )
        self.add_item(self.text_input)

    @override
    def _interaction_description(self) -> str:
        return self._emoji_output

    async def submit_handler(self, interaction: discord.Interaction, emoji: discord.PartialEmoji):
        await interaction.response.defer()  # type: ignore
        if self.interface.original_view.is_emoji_already_used(emoji):
            return await interaction.followup.send(self.language.string("reaction_roles_emoji_used"), ephemeral=True)
        self.interface.emoji = emoji
        self.interface._emoji_invalid = False
        await self.interface.update_message()
        # return await interaction.followup.send(self.language.string("reaction_roles_modal_emoji_success", emoji=str(emoji)), ephemeral=True)

    @override
    async def on_submit(self, interaction: discord.Interaction):
        value: str = self.text_input.value
        emoji_str: str | None = None
        if len(value) <= 4 and not value.isascii():  # 1-4 chars = Unicode emojis
            emoji_str = value
        elif len(value) >= 2:  # 2-32 chars = custom emojis
            if value.isdigit():  # Emoji ID
                emoji = self.bot.get_emoji(int(value))
                if emoji:
                    emoji_str = str(emoji)
            elif value.isascii():  # Emoji Name
                for emoji in self.bot.emojis:
                    if emoji.name == value:
                        emoji_str = str(emoji)
        if not emoji_str:
            return await interaction.response.send_message(self.language.string("reaction_roles_modal_emoji_invalid"), ephemeral=True)  # type: ignore
        emoji = discord.PartialEmoji.from_str(emoji_str)
        self._emoji_output = str(emoji)
        self._log_interaction(interaction)
        return await self.submit_handler(interaction, emoji)


class RoleSelect(discord.ui.RoleSelect):
    """ Select the role to use for the reaction """
    def __init__(self, interface: ReactionRoleEditView, title_string: str, row: int = 0):
        self.interface = interface
        self.language = self.interface.language
        self.print_override = False
        super().__init__(placeholder=self.language.string(title_string), min_values=1, max_values=1, row=row)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()  # type: ignore
        role = self.values[0]
        if self.interface.original_view.is_role_already_used(role):
            return await interaction.followup.send(self.language.string("reaction_roles_role_used"), ephemeral=True)
        self.interface.role = role
        self.interface._role_invalid = False
        await self.interface.update_message()
        # return await interaction.followup.send(self.language.string("reaction_roles_modal_role_success", role=str(role)), ephemeral=True, allowed_mentions=no_allowed_mentions)


class GenericReactionRoleSelect(views.SelectMenu):
    """ Common class for Edit and Remove reaction role select menu """
    interface: SimpleSelectMenuView

    def __init__(self, interface: SimpleSelectMenuView, placeholder_string: str, row: int):
        placeholder = interface.language.string(placeholder_string)
        super().__init__(interface, placeholder=placeholder, min_values=1, max_values=1, row=row)
        self.print_override = False
        self.set_options()

    def set_options(self):
        """ Generate options """
        for i, reaction_role in enumerate(self.interface.original_view.reaction_roles):
            self.add_option(value=str(i), label=reaction_role.role.name, emoji=reaction_role.emoji)

    def update_options(self):
        """ Update the list of options """
        self.reset_options()
        self.set_options()

    @override
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()  # type: ignore
        if isinstance(self.interface, EditReactionRoleView):
            new_view_cls = EditReactionView
        elif isinstance(self.interface, RemoveReactionRoleView):
            new_view_cls = RemoveReactionView
        else:
            raise TypeError(f"{self.__class__.__name__}.callback() received unexpected interface class {self.interface.__class__.__name__}")
        self.interface.stop()
        return await new_view_cls.from_reaction_role(self.interface, interaction, int(self.values[0]))


class SimpleSelectMenuView(EphemeralView):
    """ Represents a view that contains a select menu and nothing else """
    # This could be generalised to views.TranslatedView, but this is only used by the ReactionGroupView.
    def __init__(self, original_view: ReactionGroupView, select_menu_cls: Type[views.SelectMenu]):
        super().__init__(original_view)
        self.language = self.original_view.language
        self.add_item(select_menu_cls(self))

    @classmethod
    @override
    async def send(cls, original_view: ReactionGroupView, interaction: discord.Interaction):
        return await super().send_view(original_view, interaction, None)


class EditReactionRoleView(SimpleSelectMenuView):
    def __init__(self, original_view: ReactionGroupView):
        super().__init__(original_view, EditReactionRoleSelect)


class EditReactionRoleSelect(GenericReactionRoleSelect):
    interface: EditReactionRoleView

    def __init__(self, interface: EditReactionRoleView):
        super().__init__(interface, "reaction_roles_edit_reaction_menu", 0)


class RemoveReactionRoleView(SimpleSelectMenuView):
    def __init__(self, original_view: ReactionGroupView):
        super().__init__(original_view, RemoveReactionRoleSelect)


class RemoveReactionRoleSelect(GenericReactionRoleSelect):
    interface: RemoveReactionRoleView

    def __init__(self, interface: RemoveReactionRoleView):
        super().__init__(interface, "reaction_roles_remove_reaction_menu", 0)


class ReactionTypeView(SimpleSelectMenuView):
    def __init__(self, original_view: ReactionGroupView):
        super().__init__(original_view, ReactionTypeSelect)


class ReactionTypeSelect(views.SelectMenu):
    """ Set the message reaction type """
    interface: ReactionTypeView

    def __init__(self, interface: ReactionTypeView):
        placeholder = interface.language.string("reaction_roles_type_select_placeholder")
        descriptions = interface.language.data("reaction_roles_type_select_descriptions")
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        options = []
        for i in range(4):
            options.append(discord.SelectOption(
                label=interface.language.string("reaction_roles_type_select_title", n=i+1),
                description=descriptions[i],
                emoji=emojis[i],
                value=str(i+1)
            ))
        super().__init__(interface, placeholder=placeholder, min_values=1, max_values=1, options=options, row=0)
        self.language = interface.language
        self.print_override = False

    @override
    async def callback(self, interaction: discord.Interaction):
        self.interface.original_view.reaction_type = int(self.values[0])
        await self.interface.message.edit(content=self.language.string("reaction_roles_type_set", n=self.interface.original_view.reaction_type), view=None)
        await self.interface.message.delete(delay=DELETION_DELAY)
        await self.interface.original_view.update_setup_message()
        self.interface.stop()


class ReactionStyleView(SimpleSelectMenuView):
    def __init__(self, original_view: ReactionGroupView):
        super().__init__(original_view, ReactionStyleSelect)

    @discord.ui.button(label="reaction_roles_style_custom", style=discord.ButtonStyle.secondary, row=1)
    async def set_custom_style(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Allows the user to set a custom style """
        return await interaction.response.send_modal(CustomReactionStyleModal(self))  # type: ignore


class ReactionStyleSelect(views.SelectMenu):
    """ Set the reaction role list style """
    interface: ReactionStyleView

    def __init__(self, interface: ReactionStyleView):
        placeholder = interface.language.string("reaction_roles_style_placeholder")
        options = []
        for i, style in enumerate(REACTION_STYLES):
            options.append(discord.SelectOption(label=style, value=str(i)))
        # options.append(discord.SelectOption(label=interface.language.string("reaction_roles_style_custom"), value="custom"))
        super().__init__(interface, placeholder=placeholder, min_values=1, max_values=1, options=options, row=0)
        self.language = interface.language
        self.print_override = False

    @override
    async def callback(self, interaction: discord.Interaction):
        # if self.values[0] == "custom":
        #     return await interaction.response.send_modal(CustomReactionStyleModal(self.interface))
        await interaction.response.defer()  # type: ignore
        self.interface.original_view.reaction_style = REACTION_STYLES[int(self.values[0])]
        await self.interface.message.edit(content=self.language.string("reaction_roles_style_set", style=self.interface.original_view.reaction_style), view=None)
        await self.interface.message.delete(delay=DELETION_DELAY)
        await self.interface.original_view.update_setup_message()
        self.interface.stop()


class CustomReactionStyleModal(views.Modal):
    """ A modal for custom reaction styles """
    interface: ReactionStyleView
    text_input: discord.ui.TextInput[CustomReactionStyleModal]

    def __init__(self, interface: ReactionStyleView):
        self.language = interface.language
        super().__init__(interface, title=self.language.string("reaction_roles_style_custom_modal_title"))
        self.text_input = discord.ui.TextInput(
            label=self.language.string("reaction_roles_style_custom_modal_label"),
            placeholder=self.language.string("reaction_roles_style_custom_modal_placeholder"),
            style=discord.TextStyle.short, required=True, min_length=1, max_length=50, row=0
        )
        self.add_item(self.text_input)

    @override
    def _interaction_description(self) -> str:
        return self.text_input.value

    @override
    async def on_submit(self, interaction: discord.Interaction):
        value: str = self.text_input.value
        if "{emoji}" not in value or "{role}" not in value:
            return await interaction.response.send_message(self.language.string("reaction_roles_style_custom_modal_invalid"), ephemeral=True)  # type: ignore
        self._log_interaction(interaction)
        await interaction.response.defer()  # type: ignore
        self.interface.original_view.reaction_style = value
        await self.interface.message.edit(content=self.language.string("reaction_roles_style_set", style=self.interface.original_view.reaction_style), view=None)
        await self.interface.message.delete(delay=DELETION_DELAY)
        await self.interface.original_view.update_setup_message()
        self.interface.stop()


class MessagePartsModal(views.Modal):
    """ A modal for the start/end of the message """
    interface: ReactionGroupView
    message_start: discord.ui.TextInput[MessagePartsModal]
    message_end: discord.ui.TextInput[MessagePartsModal]

    def __init__(self, interface: ReactionGroupView):
        self.language = interface.language
        super().__init__(interface, title=self.language.string("reaction_roles_message_modal_title"))
        self.message_start = discord.ui.TextInput(
            label=self.language.string("reaction_roles_message_modal_start_label"),
            placeholder=self.language.string("reaction_roles_message_modal_start_placeholder"),
            style=discord.TextStyle.long, required=False, min_length=0, max_length=500, row=0
        )
        self.message_end = discord.ui.TextInput(
            label=self.language.string("reaction_roles_message_modal_end_label"),
            placeholder=self.language.string("reaction_roles_message_modal_end_placeholder"),
            style=discord.TextStyle.long, required=False, min_length=0, max_length=500, row=1
        )
        if self.interface.message_start:
            self.message_start.default = self.interface.message_start
        if self.interface.message_end:
            self.message_end.default = self.interface.message_end
        self.add_item(self.message_start)
        self.add_item(self.message_end)

    @override
    def _interaction_description(self) -> str:
        return f"Message Start: {self.message_start.value!r} | Message End: {self.message_end.value!r}"

    @override
    async def on_submit(self, interaction: discord.Interaction):
        self._log_interaction(interaction)
        await interaction.response.defer()  # type: ignore
        # if self.message_start.value:
        self.interface.message_start = self.message_start.value.replace("\\n", "\n")
        # if self.message_end.value:
        self.interface.message_end = self.message_end.value.replace("\\n", "\n")
        message: discord.WebhookMessage = await interaction.followup.send(self.language.string("reaction_roles_message_modal_success"), ephemeral=True)
        await message.delete(delay=DELETION_DELAY)
        await self.interface.update_setup_message()
