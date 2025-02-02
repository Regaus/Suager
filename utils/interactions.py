from typing import Any, Awaitable, Callable, Concatenate

import discord
from discord import app_commands

from utils import time, logger, commands, languages


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


async def init_slash_command(interaction: discord.Interaction, ephemeral: bool = False) -> commands.Context:
    """ Wrapper for the initialisation of the slash command - log and defer the interaction, then return the context """
    log_interaction(interaction)
    ctx = await commands.Context.from_interaction(interaction)
    await ctx.defer(ephemeral=ephemeral)
    return ctx


async def slash_command[**P](command_callback: Callable[[Concatenate[commands.Context, P]], Awaitable[Any]],
                             interaction: discord.Interaction, *args: P, ephemeral: bool = False):
    """ Wrapper for a slash command invocation that executes the same code as the text command equivalent """
    ctx = await init_slash_command(interaction, ephemeral=ephemeral)
    return await command_callback(ctx, *args)


async def duration_autocomplete(interaction: discord.Interaction, current: str, moderation_limit: bool = False) -> list[app_commands.Choice[str]]:
    """ Autocomplete for durations """
    language = languages.Language.get(interaction, personal=True)
    if not current:
        suggestions = ["15m", "30m", "1h", "4h", "8h", "12h", "1d", "3d", "7d", "28d", "1y"]
        return [app_commands.Choice(name=language.delta_rd(time.interpret_time(suggestion), accuracy=7, brief=False, affix=False), value=suggestion) for suggestion in suggestions]
    delta = time.interpret_time(current)
    if moderation_limit and time.rd_is_above_5y(delta):
        return [app_commands.Choice(name=language.string("mod_duration_limit_5y"), value=current)]
    if time.rd_is_zero(delta):
        return [app_commands.Choice(name=language.string("generic_zero"), value=current)]
    return [app_commands.Choice(name=language.delta_rd(delta, accuracy=7, brief=False, affix=False), value=current)]
