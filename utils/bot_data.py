import discord
from discord.ext.commands import AutoShardedBot, MinimalHelpCommand
from jishaku.paginators import PaginatorEmbedInterface

from utils import languages, permissions
from utils.database import Database

# List of all cogs each bot needs to load
load = {
    "cobble": [
        "achievements",
        "admin",
        "conlangs",
        "conworlds",
        "events",
        "info",
        "kuastall",
        "leveling",
        "placeholder",
        "settings",
        "util"
    ],
    "kyomi": [
        "admin",
        "birthdays",
        "events",
        "fun",
        "images",
        "info",
        "mod",
        "ratings",
        "reactions",
        "settings",
        "social",
        "starboard",
        "util"
    ],
    "suager": [
        "achievements",
        "admin",
        "birthdays",
        "events",
        "fun",
        "images",
        "info",
        "leveling",
        "mod",
        "polls",
        "ratings",
        "reactions",
        "settings",
        "social",
        "starboard",
        "tags",
        "util",
    ]
}


class Bot(AutoShardedBot):
    def __init__(self, blacklist: list, index: int, lc: dict, config: dict, name: str, db: Database, usages: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blacklist = blacklist
        self.index = index
        self.local_config = lc
        self.config = config
        self.name = name
        self.full_name = self.local_config["name"]
        self.db = db
        self.usages = usages
        self.uptime = None

    async def on_message(self, msg):
        if not self.is_ready() or msg.author.bot or not permissions.can_send(msg) or msg.author.id in self.blacklist:
            return
        await self.process_commands(msg)

    @staticmethod
    def language(ctx):
        return languages.Language.get(ctx)

    @staticmethod
    def language2(name: str):
        return languages.Language(name)


class HelpFormat(MinimalHelpCommand):
    def __init__(self):
        super().__init__(dm_help=None, dm_help_threshold=750, command_attrs={
            "name": "help",
            "aliases": ["commands"]
        })

    async def send_pages(self):
        try:
            destination = self.get_destination()
            interface = PaginatorEmbedInterface(self.context.bot, self.paginator, owner=self.context.author)
            await interface.send_to(destination)
            # for page in self.paginator.pages:
            #     await destination.send(page)
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
            await destination.send("Couldn't send help to you due to blocked DMs or insufficient permissions...")
