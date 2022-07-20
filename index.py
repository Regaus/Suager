import asyncio
import json
from sqlite3 import OperationalError

import discord

from utils import bot_data, database, general, temporaries, time
from utils.help_utils import HelpFormat

# import logging
# log = logging.getLogger("discord")
# log.setLevel(logging.DEBUG)
# handler = logging.FileHandler(filename="data/log.log", encoding="utf-8", mode="w")
# log.addHandler(handler)

boot_time = time.now(None)
print(f"{time.time()} > Initialisation Started")
config = general.get_config()
general.create_dirs()
tables = database.creation()
loop = asyncio.get_event_loop_policy().get_event_loop()
tasks = []
db = database.Database()  # The database is the same for all bots anyways, so no point in initialising it thrice...


async def get_prefix(_bot, ctx):
    uid = _bot.user.id
    default = [f"<@!{uid}> ", f"<@{uid}> "]
    try:
        settings = _bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, _bot.name))
        if settings:
            data = json.loads(settings['data'])
            if data["use_default"]:
                default += _bot.local_config["prefixes"]
            if data["prefixes"]:
                default += data["prefixes"]
        else:
            default += _bot.local_config["prefixes"]
    except OperationalError:
        default += _bot.local_config["prefixes"]
    except AttributeError:
        default += _bot.local_config["prefixes"]
    owner = config["owner_prefixes"] if ctx.author.id in config["owners"] else []
    return default + owner

for i in range(len(config["bots"])):
    local_config = config["bots"][i]
    try:
        blacklist = json.loads(open("blacklist.json", "r").read())
    except FileNotFoundError:
        blacklist = []
    name = local_config["internal_name"]
    if name == "kyomi":
        intents = discord.Intents(members=True, messages=True, guilds=True, bans=True, emojis=True, reactions=True, voice_states=True, message_content=True)
    else:
        intents = discord.Intents(members=True, messages=True, guilds=True, bans=True, emojis=True, reactions=True, message_content=True)
    bot = bot_data.Bot(blacklist, i, local_config, config, name, db,
                       command_prefix=get_prefix, prefix=get_prefix, command_attrs=dict(hidden=True), help_command=HelpFormat(),
                       case_insensitive=True, owner_ids=config["owners"], activity=discord.Game(name="Starting up..."), status=discord.Status.dnd, intents=intents,
                       allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=True), message_commands=True, slash_commands=False)
    load = bot_data.load[name]
    for name in load:
        tasks.append(loop.create_task(bot.load_extension(f"cogs.{name}")))
    tasks.append(loop.create_task(bot.load_extension("jishaku")))
    if "token" in local_config and local_config["token"]:
        tasks.append(loop.create_task(bot.start(local_config["token"])))
        tasks.append(loop.create_task(temporaries.playing(bot)))
        if bot.name == "suager":
            tasks.append(loop.create_task(temporaries.avatars(bot)))
            tasks.append(loop.create_task(temporaries.birthdays(bot)))
            tasks.append(loop.create_task(temporaries.reminders(bot)))
            tasks.append(loop.create_task(temporaries.reminders_errors(bot)))
            tasks.append(loop.create_task(temporaries.punishments(bot)))
            tasks.append(loop.create_task(temporaries.punishments_errors(bot)))
            tasks.append(loop.create_task(temporaries.polls(bot)))
            tasks.append(loop.create_task(temporaries.trials(bot)))
        elif bot.name == "cobble":
            tasks.append(loop.create_task(temporaries.birthdays(bot)))
            tasks.append(loop.create_task(temporaries.ka_time_updater(bot)))
            tasks.append(loop.create_task(temporaries.sl_holidays_updater(bot)))
            tasks.append(loop.create_task(temporaries.ka_holidays_updater(bot)))
        elif bot.name == "kyomi":
            tasks.append(loop.create_task(temporaries.birthdays(bot)))
            tasks.append(loop.create_task(temporaries.reminders(bot)))
            tasks.append(loop.create_task(temporaries.reminders_errors(bot)))
            tasks.append(loop.create_task(temporaries.punishments(bot)))
            tasks.append(loop.create_task(temporaries.punishments_errors(bot)))

try:
    loop.run_until_complete(asyncio.gather(*tasks))
except (KeyboardInterrupt, asyncio.CancelledError):
    loop.close()
