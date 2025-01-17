import discord
from discord import app_commands

from utils import commands, general, interactions, logger, time, languages


def _get_role_name(ctx: commands.Context, role_arg: str | int) -> str:
    if isinstance(role_arg, int):
        _role: discord.Role | None = ctx.guild.get_role(role_arg)
        role = _role.name if _role else f"Unknown role {role_arg}"
    else:
        role = role_arg
    return role


def _get_permissions(language: languages.Language, permissions: list[str]) -> str:
    permission_names = language.data("generic_permissions")
    return language.join([permission_names.get(permission, permission) for permission in permissions])


async def on_command_error(ctx: commands.Context | discord.Interaction, error: commands.CommandError | app_commands.AppCommandError):
    """ Wrapper for handling errors on both normal and slash commands """
    if isinstance(ctx, discord.Interaction):
        ctx: commands.Context = await commands.Context.from_interaction(ctx)
    if ctx.interaction is None:
        content = ctx.message.clean_content
    else:
        content = interactions.get_command_str(ctx.interaction)
    guild = getattr(ctx.guild, "name", "Private Message")
    error_msg = f"{type(error).__name__}: {str(error)}"
    language = ctx.language()
    ignore = True  # Ignore by default, aside from a few rare cases where it does actually matter

    # If an error occurred with a hybrid slash command, extract the actual exception and handle it accordingly
    if isinstance(error, commands.HybridCommandError):
        error: app_commands.AppCommandError = error.original

    # Command parsing errors
    if isinstance(error, commands.MissingRequiredArgument):  # A required argument is missing
        helper = str(ctx.invoked_subcommand) if ctx.invoked_subcommand else str(ctx.command)
        await ctx.send_help(helper, language.string("events_error_missing", param=error.param.name))
        message = None  # A message has already been sent
    elif isinstance(error, commands.MissingRequiredAttachment):  # A required argument is missing
        helper = str(ctx.invoked_subcommand) if ctx.invoked_subcommand else str(ctx.command)
        await ctx.send_help(helper, language.string("events_error_missing_attachment", param=error.param.name))
        message = None
    elif isinstance(error, commands.TooManyArguments):  # Too many arguments were specified
        helper = str(ctx.invoked_subcommand) if ctx.invoked_subcommand else str(ctx.command)
        await ctx.send_help(helper, language.string("events_error_extra_argument"))
        message = None
    # Argument parsing errors
    elif isinstance(error, commands.ChannelNotFound):  # The specified Channel was not found
        message = language.string("events_error_not_found_channel", value=error.argument)
    elif isinstance(error, (commands.EmojiNotFound, commands.PartialEmojiConversionFailure)):  # The specified Emoji was not found
        message = language.string("events_error_not_found_emoji", value=error.argument)
    elif isinstance(error, commands.GuildNotFound):  # The specified Guild was not found
        message = language.string("events_error_not_found_guild", value=error.argument)
    elif isinstance(error, commands.MemberNotFound):  # The specified Member was not found
        message = language.string("events_error_not_found_member", value=error.argument)
    elif isinstance(error, commands.MessageNotFound):  # The specified Message was not found
        message = language.string("events_error_not_found_message", value=error.argument)
    elif isinstance(error, commands.RoleNotFound):  # The specified Role was not found
        message = language.string("events_error_not_found_role", value=error.argument)
    elif isinstance(error, commands.GuildStickerNotFound):  # The specified Sticker was not found
        message = language.string("events_error_not_found_sticker", value=error.argument)
    elif isinstance(error, commands.ThreadNotFound):  # The specified Thread was not found
        message = language.string("events_error_not_found_thread", value=error.argument)
    elif isinstance(error, commands.UserNotFound):  # The specified User was not found
        message = language.string("events_error_not_found_user", value=error.argument)
    elif isinstance(error, commands.ChannelNotReadable):  # The specified Channel or Thread cannot be read by the bot
        message = language.string("events_error_channel_access", value=error.argument)
    elif isinstance(error, (commands.ConversionError, commands.UserInputError)):
        # This is a generic condition for other bad argument and parsing/conversion errors
        # We will handle all these errors the same, and just tell the user that an argument is invalid
        helper = str(ctx.invoked_subcommand) if ctx.invoked_subcommand else str(ctx.command)
        await ctx.send_help(helper, language.string("events_error_bad_argument"))
        message = None
    elif isinstance(error, app_commands.TransformerError):  # Slash command conversion error
        possible_types: dict[str, str] = language.data("generic_slash_argument_type")
        error_type: str = error.type.name  # type: ignore
        transformer = type(error.transformer).__name__
        if error_type == "user" and transformer == "MemberTransformer":
            error_type = "member"
        message = language.string("events_error_bad_argument2", value=error.value, type=possible_types.get(error_type, error_type))
    # Errors with permissions and cooldowns
    elif isinstance(error, (commands.NoPrivateMessage, app_commands.NoPrivateMessage)):  # The command cannot be used in DMs
        message = language.string("events_error_guild_only")
    elif isinstance(error, commands.NotOwner):  # The command can only be used by the bot owner
        message = language.string("events_error_owner")
    elif isinstance(error, (commands.MissingRole, app_commands.MissingRole)):  # You need to have a certain role to access this command
        role: str = _get_role_name(ctx, error.missing_role)
        message = language.string("events_error_role", role=role)
    elif isinstance(error, (commands.MissingAnyRole, app_commands.MissingAnyRole)):  # You need to have at least one of some roles to access this command
        roles: list[str] = [_get_role_name(ctx, role) for role in error.missing_roles]
        message = language.string("events_error_role_many", roles=language.join(roles, final="generic_or"))
    elif isinstance(error, commands.BotMissingRole):  # The bot needs to have a certain role to access this command
        role: str = _get_role_name(ctx, error.missing_role)
        message = language.string("events_error_role_bot", role=role)
    elif isinstance(error, commands.BotMissingAnyRole):  # The bot needs to have at least one of some roles to access this command
        roles: list[str] = [_get_role_name(ctx, role) for role in error.missing_roles]
        message = language.string("events_error_role_bot_many", roles=language.join(roles, final="generic_or"))
    elif isinstance(error, (commands.MissingPermissions, app_commands.MissingPermissions)):  # You do not have sufficient permissions to run this command
        permissions: str = _get_permissions(language, error.missing_permissions)
        message = language.string("events_error_permissions", perms=permissions)
    elif isinstance(error, (commands.BotMissingPermissions, app_commands.BotMissingPermissions)):
        permissions: str = _get_permissions(language, error.missing_permissions)
        message = language.string("events_error_permissions_bot", perms=permissions)
    elif isinstance(error, commands.NSFWChannelRequired):
        message = language.string("events_error_nsfw")
    elif isinstance(error, (commands.CommandOnCooldown, app_commands.CommandOnCooldown)):
        message = language.string("events_error_cooldown", time=language.number(error.retry_after, precision=2), rate=language.number(error.cooldown.rate),
                                  per=language.number(error.cooldown.per, precision=1))
    elif isinstance(error, commands.MaxConcurrencyReached):
        message = language.string("events_error_concurrency", rate=language.number(error.number), per=error.per)
    elif isinstance(error, (commands.CheckFailure, app_commands.CheckFailure)):
        message = language.string("events_error_check")
    elif isinstance(error, (commands.CommandNotFound, commands.DisabledCommand)):
        message = None  # Log the attempt to commands log but don't say anything
    # An actual error occurred while running the command
    elif isinstance(error, (commands.CommandInvokeError, app_commands.CommandInvokeError)):
        ignore = False
        error: Exception = error.original
        if "000 or fewer" in str(error) and len(ctx.message.content) > 1900:
            error_msg = "User entered very long input and broke the command"
            message = language.string("events_error_message_length")
        else:
            error_msg = f"{type(error).__name__}: {str(error)}"
            message = language.string("events_error_error", err=error_msg)
    else:  # Catch-all for any exceptions not mentioned here
        ignore = False
        message = language.string("events_error_error", err=error_msg)

    if message:
        await ctx.send(message, ephemeral=True)
    error_message = f"{time.time()} > {ctx.bot.full_name} > {guild} > {ctx.author} ({ctx.author.id}) > {content} > {error_msg}"
    if not ignore:
        logger.log(ctx.bot.name, "errors", error_message)
        general.print_error(error_message)
        ec = ctx.bot.get_channel(ctx.bot.local_config["error_channel"])
        if ec is not None:
            error_tb = general.traceback_maker(error, content, ctx.guild, ctx.author, limit_text=True)
            await ec.send(error_tb)
    logger.log(ctx.bot.name, "commands", error_message)
