from __future__ import annotations

from utils import commands, languages, permissions
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
    "kyomi2": [],
    "kyomi3": [],
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


class Bot(commands.AutoShardedBot):
    def __init__(self, blacklist: list, index: int, lc: dict, config: dict, name: str, db: Database, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blacklist = blacklist
        self.index = index
        self.local_config = lc
        self.config = config
        self.name = name
        self.full_name = self.local_config["name"]
        self.db = db
        # self.usages = usages
        self.uptime = None

    async def on_message(self, msg):
        if not self.is_ready() or msg.author.bot or not permissions.can_send(msg) or msg.author.id in self.blacklist:
            return
        await self.process_commands(msg)

    async def get_context(self, message, *, cls=commands.Context):
        return await super().get_context(message, cls=cls)

    @staticmethod
    def language(ctx: commands.Context | languages.FakeContext):
        return languages.Language.get(ctx)

    @staticmethod
    def language2(name: str):
        return languages.Language(name)

    @staticmethod
    def timezone(uid: int, time_class: str = "Earth"):
        return languages.Language.get_timezone(uid, time_class)
