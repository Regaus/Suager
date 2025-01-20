import discord
from discord import app_commands

from utils import time, logger


def get_command_str(interaction: discord.Interaction) -> str:
    if isinstance(interaction.command, app_commands.Command):
        command = f"Slash command: /{interaction.command.name}"
        arguments: list[str] = []
        for key, value in interaction.namespace:  # type: ignore
            if value is not None:
                arguments.append(f"{key}={value}")
    else:
        command = f"Context Menu: {interaction.command.name}"
        if interaction.command.type == discord.AppCommandType.user:  # User context menu
            arguments = [f"user={interaction.data["target_id"]}"]
        else:  # Message context menu
            arguments = [f"message={interaction.data["target_id"]}"]

    return f"{command} {" ".join(arguments)}"


def log_interaction(interaction: discord.Interaction):
    """ Log the interaction from context menus """
    command = get_command_str(interaction)
    bot = interaction.client  # bot_data.Bot
    guild = getattr(interaction.guild, "name", "Private Message") or "Private Server"  # Guilds where the bot isn't installed have an empty name
    message = f"{time.time()} > {bot.full_name} > {guild} > {interaction.user} ({interaction.user.id}) > {command}"
    logger.log(bot.name, "commands", message)
    print(message)
