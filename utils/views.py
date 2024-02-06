import asyncio
import discord

from utils import conworlds, emotes


class View(discord.ui.View):
    def __init__(self, timeout: int = 300):
        super().__init__(timeout=timeout)

    async def disable_button(self, message: discord.Message, button: discord.Button, cooldown: int = 2):
        original_label = button.label
        button.label = "Button on cooldown..."
        button.style = discord.ButtonStyle.danger
        button.disabled = True
        await message.edit(view=self)

        await asyncio.sleep(cooldown)
        button.label = original_label
        button.style = discord.ButtonStyle.primary
        button.disabled = False
        await message.edit(view=self)

    async def on_timeout(self):
        # Disable the View after it has timed out
        if hasattr(self, "message"):
            await self.message.edit(view=None)
        self.stop()


class InteractiveView(View):
    def __init__(self, sender: discord.Member, message: discord.Message, timeout: int = 300):
        super().__init__(timeout=timeout)
        self.sender = sender
        self.message = message

    async def validate_sender(self, interaction: discord.Interaction):
        """ Make sure that the person clicking on the button is also the author of the message """
        if interaction.user.id != self.sender.id:
            return await interaction.response.send(f"{emotes.Deny} This interaction is not from you.", ephemeral=True)


class GenerateNamesView(InteractiveView):
    def __init__(self, sender: discord.Member, message: discord.Message, language: str):
        super().__init__(sender=sender, message=message, timeout=900)
        self.language = language  # Language used for the citizen generation

    @discord.ui.button(label='Generate more names', style=discord.ButtonStyle.primary)
    async def generate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.sender.id:
            await interaction.response.defer()
            await self.message.edit(content=conworlds.generate_citizen_names(self.language))
            await self.disable_button(self.message, button, cooldown=6)
        else:
            await interaction.response.send_message(f"{emotes.Deny} This interaction is not from you.", ephemeral=True)


class GenerateCitizenView(InteractiveView):
    def __init__(self, sender: discord.Member, message: discord.Message, language: str):
        super().__init__(sender=sender, message=message, timeout=900)
        self.language = language  # Language used for the citizen generation

    @discord.ui.button(label='Generate another citizen', style=discord.ButtonStyle.primary)
    async def generate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.sender.id:
            await interaction.response.defer()
            new_embed = await conworlds.generate_citizen_embed(interaction.response, self.language)
            await self.message.edit(embed=new_embed)
            await self.disable_button(self.message, button, cooldown=3)
        else:
            await interaction.response.send_message(f"{emotes.Deny} This interaction is not from you.", ephemeral=True)
