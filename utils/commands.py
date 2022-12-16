from __future__ import annotations

from typing import Any, Type, TypeVar

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


def command(name: str = MISSING, cls: Type[CommandT] = MISSING, **attrs: Any):
    if cls is MISSING:
        cls = Command  # type: ignore

    def decorator(func) -> CommandT:
        if isinstance(func, Command):
            raise TypeError("Callback is already a command.")
        return cls(func, name=name, **attrs)

    return decorator


class Command(Command):
    pass


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


class FakeContext:
    """ Build a fake Context instead of commands.Context to pass on to Language.get() """
    def __init__(self, guild, bot):
        self.guild = guild
        self.bot = bot
