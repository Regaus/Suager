from __future__ import annotations

import warnings
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Type, TypeVar

from discord import Interaction
from discord.context_managers import Typing
from discord.ext.commands import *
from discord.utils import MISSING

from utils import help_utils, languages

T = TypeVar("T")
CogT = TypeVar("CogT", bound="Cog")
CommandT = TypeVar("CommandT", bound="Command")
ContextT = TypeVar("ContextT", bound="Context")
GroupT = TypeVar("GroupT", bound="Group")
HookT = TypeVar("HookT", bound="Hook")
ErrorT = TypeVar("ErrorT", bound="Error")


def command(name: str = MISSING, cls: Type[CommandT] = MISSING, nsfw: bool = False, **attrs: Any):
    if cls is MISSING:
        cls = Command  # type: ignore

    def decorator(func) -> CommandT:
        if isinstance(func, Command):
            raise TypeError("Callback is already a command.")
        return cls(func, nsfw=nsfw, name=name, **attrs)

    return decorator


class Command(Command):
    def __init__(self, func, nsfw: bool = False, *args, **kwargs):
        self.nsfw: bool = nsfw
        super().__init__(func, **kwargs)


def group(name: str = MISSING, cls: Type[GroupT] = MISSING, **attrs: Any):
    if cls is MISSING:
        cls = Group  # type: ignore
    return command(name=name, cls=cls, **attrs)  # type: ignore


class Group(Group):
    pass
    # def to_application_command(self, nested: int = 0):
    #     if self.slash_command is False:
    #         return
    #     elif nested == 2:
    #         raise ApplicationCommandRegistrationError(self, f"{self.qualified_name} is too deeply nested!")
    #
    #     options = [cmd.to_application_command(nested=nested + 1) for cmd in sorted(self.commands, key=lambda x: x.name)]
    #
    #     return {  # type: ignore
    #         "name": self.name,
    #         "type": int(not (nested - 1)) + 1,
    #         "description": self.short_doc or "no description",
    #         "options": [option for option in options if option is not None],
    #     }


class Context(Context):
    # If a command needs AllowedMentions overrides, then we'll have to summon an instance of that. The other commands don't need protection.
    async def send_help(self, cmd: str | None, extra_text: str = None):
        return await help_utils.send_help(self, cmd, extra_text)

    def language(self):
        return languages.Language.get(self)

    @staticmethod
    def language2(name: str):
        return languages.Language(name)

    @classmethod
    async def from_interaction(cls, interaction: Interaction, /) -> Context:
        return await super().from_interaction(interaction)

    # Prevent an error being raised if the interaction gets deferred twice
    async def defer(self, *, ephemeral: bool = False) -> None:
        if self.interaction:
            # If the interaction has already been responded to, don't try to defer again but show a warning
            if self.interaction.response.is_done():  # type: ignore
                warnings.warn("Interaction already responded to", RuntimeWarning, stacklevel=2)
            else:
                await self.interaction.response.defer(ephemeral=ephemeral)  # type: ignore

    def typing(self, *, ephemeral: bool = False) -> Typing | DeferTyping:
        if self.interaction is None:
            return Typing(self)
        return DeferTyping(self, ephemeral=ephemeral)


# The solution to the type warnings is just using "type: ignore"
class MemberID(Converter):
    """ Tries to find a Member by name, mention, nickname, or ID. Their ID is returned. If the Member isn't found, tries to just convert the input to int. """
    async def convert(self, ctx, argument):
        try:
            m = await MemberConverter().convert(ctx, argument)
            return m.id
        except BadArgument:
            try:
                return int(argument, base=10)
            except ValueError:
                raise MemberNotFound(argument) from None


class UserID(MemberID):
    """ Tries to find a User by username, mention, or ID. Their ID is returned. If the User isn't found, tries to just convert the input to int. """
    async def convert(self, ctx, argument):
        try:
            m = await UserConverter().convert(ctx, argument)
            return m.id
        except BadArgument:
            try:
                return int(argument, base=10)  # For Kargadia citizen profiles, this should therefore accept citizen IDs
            except ValueError:
                raise UserNotFound(argument) from None


@dataclass
class FakeContext:
    """ Build a fake Context instead of commands.Context to pass on to Language.get() or other things """
    guild: Any
    bot: Bot
    author: Any = None


class DeferTyping:
    """ Typing context manager for interaction-based contexts which defers the interaction.
     Copies the original discord.py implementation but does nothing if the interaction has already been responded. """
    def __init__(self, ctx: Context, *, ephemeral: bool):
        self.ctx: Context = ctx
        self.ephemeral: bool = ephemeral

    def __await__(self):
        if not self.ctx.interaction.response.is_done():  # type: ignore
            return self.ctx.defer(ephemeral=self.ephemeral).__await__()

    async def __aenter__(self) -> None:
        if not self.ctx.interaction.response.is_done():  # type: ignore
            await self.ctx.defer(ephemeral=self.ephemeral)

    async def __aexit__(self, exc_type: Type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        pass
