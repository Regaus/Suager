import discord
from discord import app_commands

from utils import time, logger, general, languages


def get_command_str(interaction: discord.Interaction) -> str:
    if isinstance(interaction.command, app_commands.Command):
        command = f"Slash command: {interaction.command.name}"
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
    message = f"{time.time()} > {bot.full_name} > {interaction.guild or "Private Message"} > {interaction.user} ({interaction.user.id}) > {command}"
    logger.log(bot.name, "commands", message)
    print(message)


async def on_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """ Error handler for interactions """
    language = languages.Language.get(interaction, personal=True)

    ignore = False
    error_msg = f"{type(error).__name__}: {str(error)}"
    content = f"{get_command_str(interaction)[:750]}"
    bot = interaction.client  # bot_data.Bot

    if isinstance(error, app_commands.CheckFailure):
        ignore = True  # Don't send this to error logs
        message = language.string("events_error_check2")
    elif isinstance(error, app_commands.CommandInvokeError):
        error_msg = f"{type(error.original).__name__}: {str(error.original)}"
        message = language.string("events_error_error", err=error_msg)
    elif isinstance(error, app_commands.TransformerError):
        error_msg = (f"{type(error).__name__}: {type(error.transformer).__name__} converting {error.value} to type {error.type.name} - "  # type: ignore
                     f"{type(error.__cause__).__name__}: {str(error.__cause__)}")
        message = language.string("events_error_error", err=error_msg)
    elif isinstance(error, app_commands.TranslationError):
        error_msg = (f"{type(error).__name__}: Translating {error.string} to {error.locale.name} ({error.context.location.name}) - "  # type: ignore
                     f"{type(error.__cause__).__name__}: {str(error.__cause__)}")
        message = language.string("events_error_error", err=error_msg)
    elif isinstance(error, app_commands.NoPrivateMessage):
        ignore = True
        message = language.string("events_error_guild_only")
    elif isinstance(error, app_commands.MissingPermissions):
        ignore = True
        message = language.string("events_error_permissions", perms=language.join([f"`{perm}`" for perm in error.missing_permissions]))
    elif isinstance(error, app_commands.BotMissingPermissions):
        ignore = True
        message = language.string("events_error_permissions_bot", perms=language.join([f"`{perm}`" for perm in error.missing_permissions]))
    elif isinstance(error, app_commands.CommandOnCooldown):
        ignore = True
        message = language.string("events_error_cooldown", time=language.number(error.retry_after, precision=2), rate=language.number(error.cooldown.rate),
                                  per=language.number(error.cooldown.per, precision=1))
    else:
        message = language.string("events_error_error", err=error_msg)

    if interaction.is_expired():
        if interaction.channel.guild is None or interaction.channel.permissions_for(interaction.channel.guild.me).send_messages:
            await interaction.channel.send(message)
    elif interaction.response.is_done():  # type: ignore
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)  # type: ignore

    error_message = f"{time.time()} > {bot.full_name} > {interaction.guild or "Private Message"} > {interaction.user} ({interaction.user.id}) > {content} > {error_msg}"

    if not ignore:
        logger.log(bot.name, "errors", error_message)
        general.print_error(error_message)
        ec = bot.get_channel(bot.local_config["error_channel"])
        if ec is not None:
            error = general.traceback_maker(error, content, interaction.guild, interaction.user, limit_text=True)
            await ec.send(error)
    logger.log(bot.name, "commands", error_message)
