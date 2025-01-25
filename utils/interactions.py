from typing import Any, Awaitable, Callable

import discord
from discord import app_commands

from utils import time, logger, commands


def get_command_str(interaction: discord.Interaction) -> str:
    if isinstance(interaction.command, app_commands.Command):
        command = f"Slash command: /{interaction.command.qualified_name}"
        arguments: list[str] = []
        for key, value in interaction.namespace:  # type: ignore
            if value is not None:
                arguments.append(f"{key}={value}")
    else:
        command = f"Context Menu: {interaction.command.qualified_name}"
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


async def slash_command[**P](command_callback: Callable[[commands.Context, P], Awaitable[Any]] | Callable[[commands.Context], Awaitable[Any]],
                             interaction: discord.Interaction, *args: P, ephemeral: bool = False):
    """ Wrapper for a slash command invocation that executes the same code as the text command equivalent """
    ctx = await commands.Context.from_interaction(interaction)
    await ctx.defer(ephemeral=ephemeral)
    log_interaction(interaction)
    return await command_callback(ctx, *args)
