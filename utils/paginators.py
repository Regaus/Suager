import asyncio
import collections
import dataclasses
from typing import override

import discord
from discord.ext import commands
from jishaku import paginators

# emoji settings, this sets what emoji are used for PaginatorInterface
EmojiSettings = collections.namedtuple('EmojiSettings', 'start back forward end close')

EMOJI_DEFAULT = EmojiSettings(
    start="\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}",
    back="\N{BLACK LEFT-POINTING TRIANGLE}",
    forward="\N{BLACK RIGHT-POINTING TRIANGLE}",
    end="\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}",
    close="\N{BLACK SQUARE FOR STOP}"
)


class LinePaginator(commands.Paginator):
    """ Paginator that separates based on the line count rather than on the character length

     max_lines is the maximum amount of lines per page (default 10)
     max_size is the maximum amount of characters per page (default 2000) """
    def __init__(self, prefix: str | None = None, suffix: str | None = None, max_lines: int = 10, max_size: int = 2000, linesep: str = "\n"):
        super().__init__(prefix, suffix, max_size, linesep)
        self.prefix = prefix
        self.suffix = suffix
        self.max_lines = max_lines
        self.max_size = max_size
        self.linesep = linesep
        self.clear()
        # self._current_page is [self.prefix] and contains nothing else
        # self._count is len(prefix) + len(linesep) or zero if no prefix
        # self._pages is []

    @override
    def add_line(self, line: str = '', *, empty: bool = False) -> None:
        """ Adds a line to the current page """
        max_page_size = self.max_size - self._prefix_len - self._suffix_len - 2 * self._linesep_len
        if len(line) > max_page_size:
            raise RuntimeError(f'Line exceeds maximum page size {max_page_size}')

        # If the length of the page exceeds self.max_size, end the current page early
        if self._count + len(line) + self._linesep_len > self.max_size - self._suffix_len:
            self.close_page()

        self._count += len(line) + self._linesep_len
        self._current_page.append(line)

        if empty:
            self._current_page.append('')
            self._count += self._linesep_len

        # If the line count reaches self.max_lines, finish the page after we're done
        if self._line_count() + empty >= self.max_lines:
            self.close_page()

    def _line_count(self):
        """ Amount of lines in the current page """
        # Don't subtract anything if prefix is None or empty, else subtract 1
        return len(self._current_page) - bool(self.prefix)

    def __repr__(self) -> str:
        fmt = '<LinePaginator prefix: {0.prefix!r} suffix: {0.suffix!r} linesep: {0.linesep!r} max_size: {0.max_size} count: {0._count}>'
        return fmt.format(self)


@dataclasses.dataclass
class EmbedField:
    """ Represents a field for an Embed, used by the EmbedFieldPaginator """
    name: str
    value: str
    inline: bool = False

    def __len__(self) -> int:
        return len(self.name) + len(self.value)


# This does not inherit from commands.Paginator
# Code loosely based on the main Paginator code (from discord/ext/commands/help.py)
class EmbedFieldPaginator:
    """ Paginator that separates based on field count rather than max page length

    max_fields is the maximum amount of fields per page (default 10)
    max_size is the maximum amount of characters in the total embed (default 6000)
      Note that this does not take into account the length of the rest of the contents (e.g. title or description)"""
    def __init__(self, max_fields: int = 10, max_size: int = 3000) -> None:
        # super().__init__(prefix, suffix, max_size, linesep)
        if max_fields > 25:
            raise ValueError("There can only be up to 25 fields in an Embed.")
        if max_size > 6000:
            raise ValueError("There can only be up to 6000 characters in an Embed.")
        self.max_fields = max_fields
        self.max_size = max_size
        self._current_page: list[EmbedField] = []
        self._count: int = 0
        self._pages: list[list[EmbedField]] = []
        # self._current_page is [self.prefix] and contains nothing else
        # self._count is len(prefix) + len(linesep) or zero if no prefix
        # self._pages is []

    def clear(self) -> None:
        """Clears the paginator to have no pages."""
        self._current_page: discord.Embed = discord.Embed()
        self._count: int = 0
        self._pages: list[discord.Embed] = []

    def add_field(self, *, name: str, value: str, inline: bool = False) -> None:
        """ Adds a field to the current page. Follows the parameters of Embed.add_field() """
        if len(name) > 256:
            raise ValueError("The name cannot be longer than 256 characters.")
        elif len(value) > 1024:
            raise ValueError("The value cannot be longer than 1024 characters.")
        field = EmbedField(name=name, value=value, inline=inline)

        # If the length of the page exceeds self.max_size, end the current page early
        if self._count + len(field) > self.max_size:
            self.close_page()

        self._count += len(field)
        self._current_page.append(field)

        # If the field count reaches self.max_lines, finish the page after we're done
        if self._field_count() >= self.max_fields:
            self.close_page()

    def _field_count(self) -> int:
        """ Return the amount of fields on the current page """
        return len(self._current_page)

    def close_page(self) -> None:
        """ Prematurely terminate a page. """
        self._pages.append(self._current_page)
        self._current_page = []
        self._count = 0

    def __len__(self) -> int:
        total = sum(sum(len(field) for field in page) for page in self._pages)
        return total + self._count

    @property
    def pages(self) -> list[list[EmbedField]]:
        """ Returns the rendered list of pages. """
        # If the current page is not empty, include it without closing
        # Else, return the current list of pages
        if self._current_page:
            return [*self._pages, self._current_page]
        return self._pages

    def __repr__(self) -> str:
        fmt = '<EmbedFieldPaginator prefix: {0.prefix!r} suffix: {0.suffix!r} linesep: {0.linesep!r} max_size: {0.max_size} count: {0._count}>'
        return fmt.format(self)


# Code copied from jishaku.shim.paginator_170.py
# (c) 2021 Devon (Gorialis) R
# This code is for the reaction-based paginator, used in the help command and stuff like that
class ReactionPaginatorInterface:  # pylint: disable=too-many-instance-attributes
    """
    A message and reaction based interface for paginators.

    This allows users to interactively navigate the pages of a Paginator, and supports live output.

    An example of how to use this with a standard Paginator:

    .. code:: python3

        from discord.ext import commands

        from jishaku.paginators import PaginatorInterface

        # In a command somewhere...
            # Paginators need to have a reduced max_size to accommodate the extra text added by the interface.
            paginator = commands.Paginator(max_size=1900)

            # Populate the paginator with some information
            for line in range(100):
                paginator.add_line(f"Line {line + 1}")

            # Create and send the interface.
            # The 'owner' field determines who can interact with this interface. If it's None, anyone can use it.
            interface = PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
            await interface.send_to(ctx)

            # send_to creates a task and returns control flow.
            # It will raise if the interface can't be created, e.g., if there's no reaction permission in the channel.
            # Once the interface has been sent, line additions have to be done asynchronously, so the interface can be updated.
            await interface.add_line("My, the Earth sure is full of things!")

            # You can also check if it's closed using the 'closed' property.
            if not interface.closed:
                await interface.add_line("I'm still here!")
    """

    def __init__(self, bot: commands.Bot, paginator: commands.Paginator, **kwargs):
        if not isinstance(paginator, commands.Paginator):
            raise TypeError('paginator must be a commands.Paginator instance')

        self._display_page = 0

        self.bot = bot

        self.message = None
        self.paginator = paginator

        self.owner = kwargs.pop('owner', None)
        self.emojis = kwargs.pop('emoji', EMOJI_DEFAULT)
        self.timeout = kwargs.pop('timeout', 7200)
        self.delete_message = kwargs.pop('delete_message', False)

        self.sent_page_reactions = False

        self.task: asyncio.Task = None  # type: ignore
        self.send_lock: asyncio.Event = asyncio.Event()

        self.close_exception: Exception = None  # type: ignore

        if self.page_size > self.max_page_size:
            raise ValueError(
                f'Paginator passed has too large of a page size for this interface. '
                f'({self.page_size} > {self.max_page_size})'
            )

    @property
    def pages(self) -> list[str]:
        return self.paginator.pages

    # @property
    # def pages(self):
    #     """
    #     Returns the paginator's pages without prematurely closing the active page.
    #     """
    #     # protected access has to be permitted here to not close the paginator's pages
    #
    #     # pylint: disable=protected-access
    #     paginator_pages = list(self.paginator._pages)
    #     if len(self.paginator._current_page) > 1:
    #         paginator_pages.append('\n'.join(self.paginator._current_page) + '\n' + (self.paginator.suffix or ''))
    #     # pylint: enable=protected-access
    #
    #     return paginator_pages

    @property
    def page_count(self):
        """
        Returns the page count of the internal paginator.
        """

        return len(self.pages)

    @property
    def display_page(self):
        """
        Returns the current page the paginator interface is on.
        """

        self._display_page = max(0, min(self.page_count - 1, self._display_page))
        return self._display_page

    @display_page.setter
    def display_page(self, value):
        """
        Sets the current page the paginator is on. Automatically pushes values inbounds.
        """

        self._display_page = max(0, min(self.page_count - 1, value))

    max_page_size = 2000

    @property
    def page_size(self) -> int:
        """
        A property that returns how large a page is, calculated from the paginator properties.

        If this exceeds `max_page_size`, an exception is raised upon instantiation.
        """
        page_count = self.page_count
        return self.paginator.max_size + len(f'\nPage {page_count}/{page_count}')

    @property
    def send_kwargs(self) -> dict:
        """
        A property that returns the kwargs forwarded to send/edit when updating the page.

        As this must be compatible with both `discord.TextChannel.send` and `discord.Message.edit`,
        it should be a dict containing 'content', 'embed' or both.
        """

        display_page = self.display_page
        page_num = f'\nPage {display_page + 1}/{self.page_count}'
        content = self.pages[display_page] + page_num
        return {'content': content}

    async def add_line(self, *args, **kwargs):
        """
        A proxy function that allows this PaginatorInterface to remain locked to the last page
        if it is already on it.
        """

        display_page = self.display_page
        page_count = self.page_count

        self.paginator.add_line(*args, **kwargs)

        new_page_count = self.page_count

        if display_page + 1 == page_count:
            # To keep position fixed on the end, update position to new last page and update message.
            self._display_page = new_page_count

        # Unconditionally set send lock to try and guarantee page updates on unfocused pages
        self.send_lock.set()

    async def send_to(self, destination: discord.abc.Messageable):
        """
        Sends a message to the given destination with this interface.

        This automatically creates the response task for you.
        """

        self.message = await destination.send(
            **self.send_kwargs, allowed_mentions=discord.AllowedMentions.none()
        )

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

    async def send_all_reactions(self):
        """
        Sends all reactions for this paginator, if any are missing.

        This method is generally for internal use only.
        """

        for emoji in filter(None, self.emojis):
            try:
                await self.message.add_reaction(emoji)
            except discord.NotFound:
                # the paginator has probably already been closed
                break
        self.sent_page_reactions = True

    @property
    def closed(self):
        """
        Is this interface closed?
        """

        if not self.task:
            return False
        return self.task.done()

    async def send_lock_delayed(self):
        """
        A coroutine that returns 1 second after the send lock has been released
        This helps reduce release spam that hits rate limits quickly
        """

        gathered = await self.send_lock.wait()
        self.send_lock.clear()
        await asyncio.sleep(1)
        return gathered

    async def wait_loop(self):
        """
        Waits on a loop for reactions to the message. This should not be called manually - it is handled by `send_to`.
        """

        start, back, forward, end, close = self.emojis

        def check(_payload: discord.RawReactionActionEvent):
            """
            Checks if this reaction is related to the paginator interface.
            """

            owner_check = not self.owner or _payload.user_id == self.owner.id

            _emoji = _payload.emoji
            if isinstance(_emoji, discord.PartialEmoji) and _emoji.is_unicode_emoji():
                _emoji = _emoji.name

            tests = (
                owner_check,
                _payload.message_id == self.message.id,
                _emoji,
                _emoji in self.emojis,
                _payload.user_id != self.bot.user.id
            )

            return all(tests)

        task_list = [
            self.bot.loop.create_task(coro) for coro in {
                self.bot.wait_for('raw_reaction_add', check=check),
                self.bot.wait_for('raw_reaction_remove', check=check),
                self.send_lock_delayed()
            }
        ]

        try:  # pylint: disable=too-many-nested-blocks
            last_kwargs = None

            while not self.bot.is_closed():
                done, _ = await asyncio.wait(task_list, timeout=self.timeout, return_when=asyncio.FIRST_COMPLETED)

                if not done:
                    raise asyncio.TimeoutError

                for task in done:
                    task_list.remove(task)
                    payload = task.result()

                    if isinstance(payload, discord.RawReactionActionEvent):
                        emoji = payload.emoji
                        if isinstance(emoji, discord.PartialEmoji) and emoji.is_unicode_emoji():
                            emoji = emoji.name

                        if emoji == close:
                            await self.message.delete()
                            return

                        if emoji == start:
                            self._display_page = 0
                        elif emoji == end:
                            self._display_page = self.page_count - 1
                        elif emoji == back:
                            self._display_page -= 1
                        elif emoji == forward:
                            self._display_page += 1

                        if payload.event_type == 'REACTION_ADD':
                            task_list.append(self.bot.loop.create_task(
                                self.bot.wait_for('raw_reaction_add', check=check)
                            ))
                        elif payload.event_type == 'REACTION_REMOVE':
                            task_list.append(self.bot.loop.create_task(
                                self.bot.wait_for('raw_reaction_remove', check=check)
                            ))
                    else:
                        # Send lock was released
                        task_list.append(self.bot.loop.create_task(self.send_lock_delayed()))  # type: ignore

                if not self.sent_page_reactions and self.page_count > 1:
                    self.bot.loop.create_task(self.send_all_reactions())
                    self.sent_page_reactions = True  # don't spawn any more tasks

                if self.send_kwargs != last_kwargs:
                    try:
                        await self.message.edit(**self.send_kwargs)
                    except discord.NotFound:
                        # something terrible has happened
                        return

                    last_kwargs = self.send_kwargs

        except (asyncio.CancelledError, asyncio.TimeoutError) as exception:
            self.close_exception = exception

            if self.bot.is_closed():
                # Can't do anything about the messages, so just close out to avoid noisy error
                return

            if self.delete_message:
                return await self.message.delete()

            for emoji in filter(None, self.emojis):
                try:
                    await self.message.remove_reaction(emoji, self.bot.user)
                except (discord.Forbidden, discord.NotFound):
                    pass

        finally:
            for task in task_list:
                task.cancel()


class ReactionPaginatorEmbedInterface(ReactionPaginatorInterface):
    """
    A subclass of :class:`PaginatorInterface` that encloses content in an Embed.
    """

    def __init__(self, *args, **kwargs):
        self._embed = kwargs.pop('embed', None) or discord.Embed()
        super().__init__(*args, **kwargs)

    @property
    @override
    def send_kwargs(self) -> dict:
        display_page = self.display_page
        self._embed.description = self.pages[display_page]
        self._embed.set_footer(text=f'Page {display_page + 1}/{self.page_count}')
        return {'embed': self._embed}

    max_page_size = 2048

    @property
    @override
    def page_size(self) -> int:
        return self.paginator.max_size


class PaginatorInterface(paginators.PaginatorInterface):
    def __init__(self, bot: commands.Bot, paginator: commands.Paginator, **kwargs):
        timeout = kwargs.pop("timeout", 600)  # Set default timeout to 10 minutes rather than 2 hours
        super().__init__(bot, paginator, timeout=timeout, **kwargs)

    # @property
    # def display_page(self):
    #     """ Returns the current page the paginator interface is on. """
    #     self._display_page = max(0, min(self.page_count - 1, self._display_page))
    #     return self._display_page

    # @display_page.setter
    # def display_page(self, value: int):
    #     """ Set the current display page to the supplied value (1 = first page) """
    #     self._display_page = max(0, min(self.page_count - 1, value - 1))

    @property
    @override
    def pages(self) -> list[str]:
        return self.paginator.pages  # We don't need to have custom behaviour for the last page ???

    @property
    @override
    def page_size(self) -> int:
        return self.paginator.max_size  # We don't need to add "Page 1/x", as it's not actually appended anywhere

    def remove_buttons(self):
        """ Remove all buttons except "Close Paginator" if there is only one page """
        if len(self.pages) <= 1:
            self.remove_item(self.button_start)     # type: ignore
            self.remove_item(self.button_previous)  # type: ignore
            self.remove_item(self.button_current)   # type: ignore
            self.remove_item(self.button_next)      # type: ignore
            self.remove_item(self.button_last)      # type: ignore
            self.remove_item(self.button_goto)      # type: ignore

    @property
    @override
    def send_kwargs(self) -> dict:
        """ Returns the kwards forwarded to send/edit when updating the page """
        # Don't crash if we have an empty paginator
        if self.pages:
            content = self.pages[self.display_page]
        else:
            content = "No data available"
        self.remove_buttons()
        return {"content": content, "view": self}

    async def set_message(self, message: discord.Message):
        """ Make the paginator interface use an existing message """
        self.message = await message.edit(**self.send_kwargs, allowed_mentions=discord.AllowedMentions.none())
        self.send_lock.set()
        if self.task:
            self.task.cancel()
        self.task = self.bot.loop.create_task(self.wait_loop())
        return self


# Code adapted from jishaku.shim.paginator_200.py
# (c) 2021 Devon (Gorialis) R
class PaginatorEmbedInterface(PaginatorInterface):
    """ A subclass of PaginatorInterface that encloses content in an Embed """
    def __init__(self, *args, **kwargs):
        self._embed = kwargs.pop('embed', discord.Embed())
        super().__init__(*args, **kwargs)

    @property
    @override
    def send_kwargs(self) -> dict:
        # Don't crash if we have an empty paginator
        if self.pages:
            self._embed.description = self.pages[self.display_page]
        else:
            self._embed.description = "No data available"
        self.remove_buttons()
        return {'embed': self._embed, 'view': self}

    max_page_size = 2048

    @override
    async def set_message(self, message: discord.Message, *, clear_content: bool = False):
        if clear_content:
            self.message = await message.edit(content=None, **self.send_kwargs, allowed_mentions=discord.AllowedMentions.none())
        else:
            self.message = await message.edit(**self.send_kwargs, allowed_mentions=discord.AllowedMentions.none())
        self.send_lock.set()
        if self.task:
            self.task.cancel()
        self.task = self.bot.loop.create_task(self.wait_loop())
        return self


class EmbedFieldPaginatorInterface(PaginatorEmbedInterface):
    """ A version of PaginatorInterface that supports EmbedFieldPaginator instead of the regular Paginator """
    def __init__(self, *args, paginator: EmbedFieldPaginator, **kwargs):
        # This is done to pass the isinstance() check inside jishaku.paginators.PaginatorInterface
        self.max_page_size = 6000
        super().__init__(paginator=commands.Paginator(), *args, **kwargs)

        self._embed = kwargs.pop('embed', discord.Embed())
        self._embed.clear_fields()
        self.max_page_size -= len(self._embed)  # This won't account for the embed being updated afterwards, but that shouldn't happen
        self.paginator = paginator

        if self.page_size > self.max_page_size:
            raise ValueError(f"Paginator passed has too large of a page size for this embed. "
                             f"(Max page size: {self.page_size} > {self.max_page_size}; Embed length: {len(self._embed)})")

    @property
    @override
    def pages(self) -> list[list[EmbedField]]:
        return self.paginator.pages  # This is purely here for type hinting purposes

    @property
    @override
    def send_kwargs(self) -> dict:
        # Don't crash if we have an empty paginator
        if self.pages:
            page: list[EmbedField] = self.pages[self.display_page]
            self._embed.clear_fields()
            for field in page:
                self._embed.add_field(name=field.name, value=field.value, inline=field.inline)
        self.remove_buttons()
        return {'embed': self._embed, 'view': self}

    @override
    async def add_line(self, *, name: str, value: str, inline: bool = False):
        """ A function that allows the PaginatorInterface to remain locked to the last page if already on it.

        This class overrides it to follow the signature of EmbedFieldPaginator. """
        display_page = self.display_page
        page_count = self.page_count

        self.paginator.add_field(name=name, value=value, inline=inline)

        new_page_count = self.page_count
        if display_page + 1 == page_count:
            self._display_page = new_page_count

        # "Unconditionally set send lock to try to guarantee page updates on unfocused pages"
        self.send_lock.set()

    add_field = add_line
