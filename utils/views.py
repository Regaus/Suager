import asyncio

import discord
from discord import app_commands, Interaction

from utils import conworlds, emotes, languages, general, time, logger


class NotMessageAuthor(app_commands.CheckFailure):
    """ Raised when the interaction user is not the message author """
    def __init__(self, language: languages.Language = None):
        if language:
            message = language.string("events_error_author")
        else:
            message = f"{emotes.Deny} Only the author of the command can use this interaction."
        super().__init__(message)


class View(discord.ui.View):
    def __init__(self, timeout: int | float = 300):  # , bot: bot_data.Bot
        super().__init__(timeout=timeout)
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

    async def interaction_check(self, interaction: Interaction, /) -> bool:
        if hasattr(self, "sender"):
            if interaction.user.id != self.sender.id:
                raise NotMessageAuthor(languages.Language.get(interaction, personal=True))
        return True

    async def on_timeout(self):
        """ Called when the view times out """
        # Disable the View after it has timed out
        if hasattr(self, "message"):
            await self.message.edit(view=None)
        self.stop()

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item):
        """ Called when an error occurs during an interaction with an item """
        language = languages.Language.get(interaction, personal=True)
        component_type = language.data("generic_component_type")
        if hasattr(item, "label"):
            if hasattr(item.type, "name"):
                origin = f"{component_type.get(item.type.name, item.type.name)}: {item.label!r}"
            else:
                origin = item.label  # I don't see how that would happen, but leave it just in case
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
        content = f"{general.build_interaction_content(interaction)} > {origin}"
        bot = interaction.client  # bot_data.Bot
        error_message = f"{time.time()} > {bot.full_name} > {interaction.guild or "Private Message"} > {interaction.user} ({interaction.user.id}) > {content} > {error_msg}"
        if not ignore:
            logger.log(bot.name, "errors", error_message)
            general.print_error(error_message)
            ec = bot.get_channel(bot.local_config["error_channel"])
            if ec is not None:
                error = general.traceback_maker(error, content[:750], interaction.guild, interaction.user)
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

    @discord.ui.button(label="Restore view", emoji="🔄", style=discord.ButtonStyle.primary)
    async def restore_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        # noinspection PyUnresolvedReferences
        await interaction.response.defer()
        await self.message.edit(view=self.original_view)
        # return await interaction.followup.send("The original view has now been restored.", ephemeral=True)


class InteractiveView(View):
    def __init__(self, sender: discord.Member, message: discord.Message, timeout: int = 300):
        super().__init__(timeout=timeout)
        self.sender = sender
        self.message = message

    # async def validate_sender(self, interaction: discord.Interaction):
    #     """ Make sure that the person clicking on the button is also the author of the message """
    #     if interaction.user.id != self.sender.id:
    #         return await interaction.response.send(f"{emotes.Deny} This interaction is not from you.", ephemeral=True)


class GenerateNamesView(InteractiveView):
    def __init__(self, sender: discord.Member, message: discord.Message, language: str):
        super().__init__(sender=sender, message=message, timeout=900)
        self.language = language  # Language used for the citizen generation

    @discord.ui.button(label='Generate more names', style=discord.ButtonStyle.primary)
    async def generate(self, interaction: discord.Interaction, button: discord.ui.Button):
        # noinspection PyUnresolvedReferences
        await interaction.response.defer()
        await self.message.edit(content=conworlds.generate_citizen_names(self.language))
        await self.disable_button(self.message, button, cooldown=6)


class GenerateCitizenView(InteractiveView):
    def __init__(self, sender: discord.Member, message: discord.Message, language: str):
        super().__init__(sender=sender, message=message, timeout=900)
        self.language = language  # Language used for the citizen generation

    @discord.ui.button(label='Generate another citizen', style=discord.ButtonStyle.primary)
    async def generate(self, interaction: discord.Interaction, button: discord.ui.Button):
        # noinspection PyUnresolvedReferences
        await interaction.response.defer()
        new_embed = await conworlds.generate_citizen_embed(interaction.response, self.language)
        await self.message.edit(embed=new_embed)
        await self.disable_button(self.message, button, cooldown=3)
