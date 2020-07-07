import discord
from discord.ext.commands import AutoShardedBot, DefaultHelpCommand

from core.utils import permissions


class Bot(AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_message(self, msg):
        if not self.is_ready() or msg.author.bot or not permissions.can_send(msg):
            return
        await self.process_commands(msg)


class HelpFormat(DefaultHelpCommand):
    def __init__(self):
        super().__init__(dm_help=None, dm_help_threshold=750)

    async def send_pages(self):
        try:
            destination = self.get_destination()
            for page in self.paginator.pages:
                await destination.send(page)
            try:
                if permissions.can_react(self.context):
                    await self.context.message.add_reaction(chr(0x2709))
            except discord.Forbidden:
                pass
        except discord.Forbidden:
            destination = self.context.channel
            try:
                if permissions.can_react(self.context):
                    await self.context.message.add_reaction(chr(0x274C))
            except discord.Forbidden:
                pass
            await destination.send("Couldn't send help to you due to blocked DMs...")
