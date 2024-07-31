from __future__ import annotations

import asyncio

import discord
import nest_asyncio
from discord import app_commands

from utils import conworlds, emotes, languages, general, time, logger, commands


class NotMessageAuthor(app_commands.CheckFailure):
    """ Raised when the interaction user is not the message author """
    def __init__(self, language: languages.Language = None):
        if language:
            message = language.string("events_error_author")
        else:
            message = f"{emotes.Deny} Only the author of the command can use this interaction."
        super().__init__(message)


class View(discord.ui.View):
    def __init__(self, timeout: int | float = 300, ctx: commands.Context | discord.Interaction = None):  # , bot: bot_data.Bot
        super().__init__(timeout=timeout)
        # self.context = ctx
        if ctx is None:
            self.command: str = "Unknown command"
        elif isinstance(ctx, discord.Interaction):
            self.command: str = general.build_interaction_content(ctx)
        elif ctx.interaction is not None:
            self.command: str = general.build_interaction_content(ctx.interaction)
        else:
            self.command: str = ctx.message.content
        # self.bot = bot

    async def disable_button(self, message: discord.Message, button: discord.Button, cooldown: int = 2):
        """ Disable the button for the specified amount of seconds, replace the label to state that the button is on cooldown """
        original_label = button.label
        original_style = button.style
        button.label = f"Cooldown ({cooldown}s)"  # "Button on cooldown..."
        button.style = discord.ButtonStyle.grey  # used to be danger
        button.disabled = True
        await message.edit(view=self)

        await asyncio.sleep(cooldown)
        button.label = original_label
        button.style = original_style
        button.disabled = False
        await message.edit(view=self)

    async def disable_button_light(self, message: discord.Message, button: discord.Button, cooldown: int = 2):
        """ Disable the button for the specified amount of seconds, but don't do anything with the label """
        original_style = button.style
        button.style = discord.ButtonStyle.grey
        button.disabled = True
        await message.edit(view=self)

        await asyncio.sleep(cooldown)
        button.style = original_style
        button.disabled = False
        await message.edit(view=self)

    async def disable_buttons_light(self, message: discord.Message, *buttons: discord.Button, cooldown: int = 2):
        """ Disable multiple buttons at once (without changing their names) """
        original_styles = []
        for button in buttons:
            original_styles.append(button.style)
            button.disabled = True
        await message.edit(view=self)

        await asyncio.sleep(cooldown)
        for i, button in enumerate(buttons):
            button.style = original_styles[i]
            button.disabled = False
        await message.edit(view=self)

    def _child_from_custom_id(self, custom_id: str) -> discord.ui.Item:
        for item in self.children:
            if hasattr(item, "custom_id") and item.custom_id == custom_id:  # type: ignore
                return item
        raise KeyError(custom_id)  # No such item exists

    @staticmethod
    def _select_menu_name(item: discord.ui.Select | discord.ui.ChannelSelect | discord.ui.RoleSelect | discord.ui.UserSelect | discord.ui.MentionableSelect) -> str:
        """ Get the item_name variable for a select menu from self._log_interaction() """
        match item.type:
            case discord.ComponentType.select:
                base_name = "Select Menu"
            case discord.ComponentType.channel_select:
                base_name = "Channel Select"
            case discord.ComponentType.role_select:
                base_name = "Role Select"
            case discord.ComponentType.user_select:
                base_name = "User Select"
            case discord.ComponentType.mentionable_select:
                base_name = "Mentionable Select"
            case _:
                base_name = "Unknown Select Menu Type"
        item_name = item.placeholder
        if item.max_values > 1:
            value = ", ".join([str(v) for v in item.values])
        else:
            value = str(item.values[0])
        return f"{base_name}: {item_name} > {value}"

    def _log_interaction(self, interaction: discord.Interaction):
        """ Log the interaction - e.g. button presses """
        item: discord.ui.Item = self._child_from_custom_id(interaction.data["custom_id"])  # type: ignore
        match item.type:
            case discord.ComponentType.button:
                item: discord.ui.Button
                do_print = False
                if hasattr(item, "log_label"):
                    item_name = f"Button press: {item.log_label}"
                else:
                    item_name = f"Button press: {item.label}"
            case discord.ComponentType.text_input:
                item: discord.ui.TextInput
                do_print = True
                item_name = f"Text input: {item.label} > {item.value}"
            case discord.ComponentType.select | discord.ComponentType.channel_select | discord.ComponentType.role_select | discord.ComponentType.user_select | discord.ComponentType.mentionable_select:
                do_print = True
                item_name = self._select_menu_name(item)  # type: ignore
            case _:
                do_print = True
                item_name = f"Unknown item {item}"
        bot = interaction.client  # bot_data.Bot
        message = f"{time.time()} > {bot.full_name} > {interaction.guild or "Private Message"} > {interaction.user} ({interaction.user.id}) > {self.command} > {item_name}"
        logger.log(bot.name, "commands", message)
        if do_print:
            print(message)

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        """ Ensure the validity of the interaction """
        if hasattr(self, "sender"):
            if interaction.user.id != self.sender.id:
                raise NotMessageAuthor(languages.Language.get(interaction, personal=True))
        self._log_interaction(interaction)
        return True

    async def on_timeout(self):
        """ Called when the view times out """
        # Disable the View after it has timed out, if possible
        if hasattr(self, "message"):
            try:
                await self.message.edit(view=None)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass
        self.stop()

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item):
        """ Called when an error occurs during an interaction with an item """
        language = languages.Language.get(interaction, personal=True)
        component_type = language.data("generic_component_type")
        temporary_view = getattr(self, "temporary", False) and "Invalid Webhook Token" in str(error)  # Our temporary view has expired
        if hasattr(item, "label") or hasattr(item, "log_label"):
            if hasattr(item, "log_label"):
                label = item.log_label
            else:
                label = item.label
            if hasattr(item.type, "name"):
                origin = f"{component_type.get(item.type.name, item.type.name)}: {label}"  # e.g. Button: Move Offset
            else:
                origin = label  # I don't see how that would happen, but leave it just in case
        elif getattr(item.type, "name", None) == "select":
            if hasattr(item, "placeholder"):
                origin = f"{component_type.get('select', 'select')}: {item.placeholder}"  # e.g. Select: Route Filter
            else:
                origin = component_type.get("select", "select")
        else:
            if hasattr(item.type, "name"):
                origin = component_type.get(item.type.name, item.type.name)
            else:
                origin = language.string("generic_component_unknown")

        error_msg = f"{type(error).__name__}: {str(error)}"
        ephemeral = False
        ignore = False
        if isinstance(error, app_commands.CheckFailure):
            ignore = True  # Don't send this to error logs
            if isinstance(error, NotMessageAuthor):
                message = f"{str(error)}"
                ephemeral = True
            else:
                message = language.string("events_error_check2")
        elif temporary_view:
            message = language.string("events_error_temporary_view")
            ephemeral = True
        else:
            message = f"{origin} > {language.string("events_error_error", err=error_msg)}"
        # noinspection PyUnresolvedReferences
        if interaction.is_expired():
            await interaction.channel.send(message)
        elif interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=ephemeral)
        else:
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(message, ephemeral=ephemeral)

        # content = f"{general.build_interaction_content(interaction)} > {origin}"
        content = f"{self.command[:750]} > {origin}"
        bot = interaction.client  # bot_data.Bot
        error_message = f"{time.time()} > {bot.full_name} > {interaction.guild or "Private Message"} > {interaction.user} ({interaction.user.id}) > {content} > {error_msg}"

        if temporary_view:
            logger.log(bot.name, "commands", error_message)
            general.print_error(error_message)
            self.stop()
            return

        if not ignore:
            logger.log(bot.name, "errors", error_message)
            general.print_error(error_message)
            ec = bot.get_channel(bot.local_config["error_channel"])
            if ec is not None:
                error = general.traceback_maker(error, content, interaction.guild, interaction.user, limit_text=True)
                await ec.send(error)
        logger.log(bot.name, "commands", error_message)


class HiddenView(View):
    """ A View that replaces the original one with a simple Restore button. """

    def __init__(self, original_view: View):
        super().__init__(timeout=original_view.timeout)
        self.original_view = original_view

        if hasattr(self.original_view, "message"):
            self.message: discord.Message = self.original_view.message
        else:
            raise AttributeError("View passed as original_view must have a message attribute.")

        if hasattr(self.original_view, "sender"):  # So that only the author can restore the original view
            self.sender: discord.Member = self.original_view.sender

        self.command = getattr(self.original_view, "command", None)

    @discord.ui.button(label="Restore view", emoji="🔄", style=discord.ButtonStyle.primary)
    async def restore_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        # noinspection PyUnresolvedReferences
        await interaction.response.defer()
        await self.message.edit(view=self.original_view)
        # return await interaction.followup.send("The original view has now been restored.", ephemeral=True)

    @discord.ui.button(label="Close view", emoji="⏹️", style=discord.ButtonStyle.danger)
    async def close_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Close the view """
        # noinspection PyUnresolvedReferences
        await interaction.response.defer()
        await self.message.edit(view=None)


class InteractiveView(View):
    message: discord.Message | discord.InteractionMessage

    def __init__(self, sender: discord.Member, message: discord.Message | discord.InteractionMessage, timeout: int = 300, ctx: commands.Context | discord.Interaction = None):
        super().__init__(timeout=timeout, ctx=ctx)
        self.sender = sender
        self.temporary = False

        if isinstance(message, (discord.InteractionMessage, discord.WebhookMessage)):  # Fetch the full Message from the partial InteractionMessage
            if message.interaction_metadata.is_guild_integration():  # This should be fine. I don't think we'll ever need to load partial messages from a non-interaction webhook?
                try:
                    nest_asyncio.apply()  # https://stackoverflow.com/a/56434301 - Patches asyncio to let the code below run properly
                    self.message = asyncio.get_event_loop().run_until_complete(asyncio.create_task(message.fetch()))
                except (discord.NotFound, discord.Forbidden):
                    self.message = message
                    self.temporary = True
            else:
                self.message = message
                self.temporary = True
        else:
            self.message: discord.Message = message

        if self.temporary:
            self.timeout = min(self.timeout, 900)

    # async def validate_sender(self, interaction: discord.Interaction):
    #     """ Make sure that the person clicking on the button is also the author of the message """
    #     if interaction.user.id != self.sender.id:
    #         return await interaction.response.send(f"{emotes.Deny} This interaction is not from you.", ephemeral=True)


class GenerateNamesView(InteractiveView):
    def __init__(self, sender: discord.Member, message: discord.Message, language: str, ctx: commands.Context | discord.Interaction = None):
        super().__init__(sender=sender, message=message, timeout=900, ctx=ctx)
        self.language = language  # Language used for the citizen generation

    @discord.ui.button(label='Generate more names', style=discord.ButtonStyle.primary)
    async def generate(self, interaction: discord.Interaction, button: discord.ui.Button):
        # noinspection PyUnresolvedReferences
        await interaction.response.defer()
        await self.message.edit(content=conworlds.generate_citizen_names(self.language))
        await self.disable_button(self.message, button, cooldown=6)


class GenerateCitizenView(InteractiveView):
    def __init__(self, sender: discord.Member, message: discord.Message, language: str, ctx: commands.Context | discord.Interaction = None):
        super().__init__(sender=sender, message=message, timeout=900, ctx=ctx)
        self.language = language  # Language used for the citizen generation

    @discord.ui.button(label='Generate another citizen', style=discord.ButtonStyle.primary)
    async def generate(self, interaction: discord.Interaction, button: discord.ui.Button):
        # noinspection PyUnresolvedReferences
        await interaction.response.defer()
        new_embed = await conworlds.generate_citizen_embed(interaction.response, self.language)
        await self.message.edit(embed=new_embed)
        await self.disable_button(self.message, button, cooldown=3)


class NumericInputModal(discord.ui.Modal):
    """ A modal that asks the user to enter a number (e.g. for changing pages) """
    text_input: discord.ui.TextInput[NumericInputModal] = discord.ui.TextInput(label="Enter value", style=discord.TextStyle.short, placeholder="0")

    def __init__(self, interface: InteractiveView, title: str = "Modal"):
        super().__init__(title=title, timeout=interface.timeout)
        self.interface = interface
        self.minimum = 0  # Override this in subclasses
        self.maximum = 0  # Override this in subclasses

    def _log_interaction(self, interaction: discord.Interaction):
        """ Log the interaction - e.g. button presses """
        bot = interaction.client  # bot_data.Bot
        item_name = self.__class__.__name__
        # item_name = f"{self.__class__.__name__}: {self.text_input.label}"
        message = (f"{time.time()} > {bot.full_name} > {interaction.guild or "Private Message"} > {interaction.user} ({interaction.user.id}) > "
                   f"{self.interface.command} > {item_name} > {self.text_input.value}")
        logger.log(bot.name, "commands", message)
        # print(message)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        language = languages.Language.get(interaction, personal=True)
        origin = self.__class__.__name__
        # origin = f"{self.__class__.__name__}: {self.text_input.label}"
        error_msg = f"{type(error).__name__}: {str(error)}"
        ephemeral = False
        ignore = False
        if isinstance(error, app_commands.CheckFailure):
            ignore = True  # Don't send this to error logs
            if isinstance(error, NotMessageAuthor):
                message = f"{str(error)}"
                ephemeral = True
            else:
                message = f"{language.string("events_error_check2")}"
        else:
            message = f"{origin} > {language.string("events_error_error", err=error_msg)}"
        # noinspection PyUnresolvedReferences
        if interaction.is_expired():
            await interaction.channel.send(message)
        elif interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=ephemeral)
        else:
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(message, ephemeral=ephemeral)
        # content = f"{general.build_interaction_content(interaction)} > {origin}"
        content = f"{self.interface.command[:750]} > {origin}"
        bot = interaction.client  # bot_data.Bot
        error_message = f"{time.time()} > {bot.full_name} > {interaction.guild or "Private Message"} > {interaction.user} ({interaction.user.id}) > {content} > {error_msg}"
        if not ignore:
            logger.log(bot.name, "errors", error_message)
            general.print_error(error_message)
            ec = bot.get_channel(bot.local_config["error_channel"])
            if ec is not None:
                error = general.traceback_maker(error, content, interaction.guild, interaction.user, limit_text=True)
                await ec.send(error)
        logger.log(bot.name, "commands", error_message)

    async def submit_handler(self, interaction: discord.Interaction, value: int):
        """ Handle the user input """
        raise NotImplementedError("This method must be implemented by subclasses")

    # noinspection PyUnresolvedReferences
    async def on_submit(self, interaction: discord.Interaction):
        """ This is called when a value is submitted to this modal """
        try:
            if not self.text_input.value:
                raise ValueError("Value was not filled")
            value = int(self.text_input.value)
            if value < self.minimum:
                return await interaction.response.send_message(f"Value must be greater than {self.minimum}.", ephemeral=True)
            if value > self.maximum:
                return await interaction.response.send_message(f"Value must be less than {self.maximum}.", ephemeral=True)
            self._log_interaction(interaction)  # Only log the interaction if it is valid
            return await self.submit_handler(interaction, value)
        except ValueError:
            if self.text_input.value:
                content = f"`{self.text_input.value}` could not be converted to a valid number."
            else:
                content = f"You need to enter a value."
            await interaction.response.send_message(content=content, ephemeral=True)


class SelectMenu(discord.ui.Select):
    """ Subclass of Discord's default Select menu that incorporates an interface """

    def __init__(self, interface: InteractiveView, *, placeholder: str = None, min_values: int = 1, max_values: int = 1, options: list[discord.SelectOption] = None, row: int = None):
        if options is None:
            options = []
        super().__init__(placeholder=placeholder, min_values=min_values, max_values=max_values, options=options, row=row)
        self.interface = interface

    def reset_options(self):
        """ Reset the list of options to nothing """
        self.options = []
