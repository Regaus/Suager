from __future__ import annotations

from itertools import groupby
from typing import Any, Iterable

import discord
from discord.ext.commands import NSFWChannelRequired
from discord.ext.commands.core import Group, wrap_callback

from utils.paginators import PaginatorEmbedInterface  # Forces to use the v1.7 paginator (without buttons)
from utils.commands import Command, CommandError, Context, MinimalHelpCommand, NoPrivateMessage, NotOwner


class PaginatorInterface(PaginatorEmbedInterface):
    @property
    def send_kwargs(self) -> dict:
        display_page = self.display_page
        self._embed.description = self.pages[display_page]
        self._embed.set_footer(text=f'Page {display_page + 1}/{self.page_count}')
        return {'embed': self._embed}

    async def send_to(self, destination: discord.abc.Messageable, extra_text: str = None):
        """
        Sends a message to the given destination with this interface.

        This automatically creates the response task for you.
        """

        self.message = await destination.send(content=extra_text, **self.send_kwargs)

        # add the close reaction
        await self.message.add_reaction(self.emojis.close)

        self.send_lock.set()

        if self.task:
            self.task.cancel()

        self.task = self.bot.loop.create_task(self.wait_loop())

        # if there is more than one page, and the reactions haven't been sent yet, send navigation emotes
        if not self.sent_page_reactions and self.page_count > 1:
            await self.send_all_reactions()

        return self


# Also find, a way to append a message to the output (ie send something as content and then the help embed)
class HelpFormat(MinimalHelpCommand):
    def __init__(self):
        super().__init__(command_attrs={
            "name": "help",
            "aliases": ["commands"],
            "help": "I wonder what this command does..."
        }, sort_commands=True, dm_help=False)

        self.commands_heading = "Commands"
        self.aliases_heading = "Aliases:"
        self.no_category = "No Category"
        self.extra_text: str | None = None
        self.nsfw = 0

    @property
    def prefix(self):
        return self.context.clean_prefix if self.context else None

    async def predicate(self, command: Command):
        try:
            return await command.can_run(self.context)
        except NoPrivateMessage:  # still show if guild-only
            return True
        except NotOwner:  # completely hide if owner-only
            return False
        except NSFWChannelRequired:  # hide if NSFW command in a SFW channel
            self.nsfw += 1  # Add to counter, at the end show as "x nsfw commands hidden"
            return False
        except CommandError:  # any other error, eg permissions -> cross out
            return None

    async def send_pages(self):
        destination: discord.User | discord.TextChannel = self.get_destination()  # type: ignore
        if self.nsfw:
            self.paginator.add_line()
            self.paginator.add_line(f"⚠ {self.nsfw:,} NSFW commands hidden")
        interface = PaginatorInterface(self.context.bot, self.paginator, owner=self.context.author)
        try:
            await interface.send_to(destination, extra_text=self.extra_text)
        except discord.Forbidden:
            pass
        finally:
            # Reset self.extra_text so that the next time the command is called, it wouldn't suddenly appear
            self.extra_text = None
            self.nsfw = 0

    def get_opening_note(self):
        command_name = self.invoked_with
        return "Use `{0}{1} [command]` for more info on a command.\n" \
               "Use `{0}{1} [category]` for more info on a category.".format(self.prefix, command_name)

    def get_ending_note(self):
        return "Crossed out commands cannot be used by you in the current channel."

    def add_subcommand_formatting(self, command):
        fmt = '`{0}{1}` \N{EN DASH} {2}' if command.short_doc else '{0}{1}'
        self.paginator.add_line(fmt.format(self.prefix, command.qualified_name, command.short_doc))

    async def filter_commands(self, command: Iterable[Command], *, sort=False, key: Any = lambda c: c.name):
        # This function is where commands are filtered on whether they can be used or not...
        # Maybe attach an attribute to them on whether they're usable
        iterator = command if self.show_hidden else filter(lambda c: not c.hidden, command)

        # if we're here then we need to check every command if it can run

        ret = []
        for cmd in iterator:
            valid = await self.predicate(cmd)
            if valid is True or valid is None:
                ret.append(cmd)

        if sort:
            ret.sort(key=key)
        return ret

    def add_aliases_formatting(self, aliases):
        self.paginator.add_line(f'**{self.aliases_heading}** `{"`, `".join(aliases)}`', empty=True)

    async def add_command_formatting(self, command: Command):
        if command.description:
            self.paginator.add_line(command.description, empty=True)

        signature = self.get_command_signature(command)
        if command.aliases:
            self.paginator.add_line(signature)
            self.add_aliases_formatting(command.aliases)
        else:
            self.paginator.add_line(signature, empty=True)

        if command.help:
            try:
                self.paginator.add_line(command.help, empty=True)
            except RuntimeError:
                for line in command.help.splitlines():
                    self.paginator.add_line(line)
                self.paginator.add_line()

        if not (await self.predicate(command)):  # This also includes cases where the user is not the owner and stuff
            self.paginator.add_line()
            self.paginator.add_line("You cannot use this command in this channel.")

    async def add_bot_commands_formatting(self, command, heading):
        if command:
            # U+2002 Middle Dot
            joined = "\u2002".join([(f"~~{c.name}~~" if (await self.predicate(c) is None) else c.name) for c in command])
            self.paginator.add_line(f"__**{heading}**__")
            self.paginator.add_line(joined)

    async def prepare_help_command(self, ctx: Context, command: Any):
        # In reality, command should be a str, but I need this to get the type checker to shut up
        self.paginator.clear()
        await super().prepare_help_command(ctx, command)

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        if bot.description:
            self.paginator.add_line(bot.description, empty=True)

        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)

        no_category = f"\u200b{self.no_category}"

        def get_category(command, *, no_category_name=no_category):
            cog = command.cog
            return cog.qualified_name if cog is not None else no_category_name

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        to_iterate = groupby(filtered, key=get_category)  # type: ignore

        for category, cmds in to_iterate:
            cmds = sorted(cmds, key=lambda c: c.name) if self.sort_commands else list(cmds)
            await self.add_bot_commands_formatting(cmds, category)

        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

        await self.send_pages()

    async def send_cog_help(self, cog):
        bot = self.context.bot
        if bot.description:
            self.paginator.add_line(bot.description, empty=True)

        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)

        if cog.description:
            self.paginator.add_line(cog.description, empty=True)

        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)
        if filtered:
            self.paginator.add_line(f"**{cog.qualified_name} {self.commands_heading}**")
            for command in filtered:  # type: ignore
                self.add_subcommand_formatting(command)

        await self.send_pages()

    async def send_group_help(self, group):
        await self.add_command_formatting(group)

        filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
        if filtered:
            note = self.get_opening_note()
            if note:
                self.paginator.add_line(note, empty=True)

            self.paginator.add_line(f"**{self.commands_heading}**")
            for command in filtered:  # type: ignore
                self.add_subcommand_formatting(command)

        await self.send_pages()

    async def send_command_help(self, command):
        await self.add_command_formatting(command)
        self.paginator.close_page()
        await self.send_pages()


async def send_help(ctx: Context, command: str | None, extra_text: str = None) -> Any:
    bot = ctx.bot  # bot_data.Bot
    cmd: HelpFormat | None = bot.help_command

    if cmd is None:
        return None

    cmd = cmd.copy()
    cmd.context = ctx
    cmd.extra_text = extra_text
    if command is None:
        await cmd.prepare_help_command(ctx, None)
        mapping = cmd.get_bot_mapping()
        injected = wrap_callback(cmd.send_bot_help)
        try:
            return await injected(mapping)
        except CommandError as e:
            await cmd.on_help_command_error(ctx, e)
            return None

    if isinstance(command, str):
        entity = bot.get_cog(command) or bot.get_command(command)
    else:
        entity = command

    if entity is None:
        return None

    if not hasattr(entity, "qualified_name"):
        # if we're here then it's not a cog, group, or command.
        return None

    await cmd.prepare_help_command(ctx, entity.qualified_name)

    try:
        if hasattr(entity, "__cog_commands__"):
            injected = wrap_callback(cmd.send_cog_help)
            return await injected(entity)
        elif isinstance(entity, Group):
            injected = wrap_callback(cmd.send_group_help)
            return await injected(entity)
        elif isinstance(entity, Command):
            injected = wrap_callback(cmd.send_command_help)
            return await injected(entity)
        else:
            return None
    except CommandError as e:
        await cmd.on_help_command_error(ctx, e)
