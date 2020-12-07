import asyncio
import json
import os
from sqlite3 import OperationalError

import aiohttp
import discord

from core.utils import bot_data, database, general, time
from core.utils.events import changes

boot_time = time.now(None)
print(f"{time.time()} > Initialisation Started")
config = general.get_config()
general.create_dirs()
tables = database.creation()
loop = asyncio.get_event_loop()
tasks = []


async def get_prefix(_bot, ctx):
    uid = _bot.user.id
    default = [f"<@!{uid}> ", f"<@{uid}> "]
    try:
        settings = _bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
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
    _name = local_config["internal_name"]
    fn = f"data/{_name}/changes.json"
    try:
        times = json.loads(open(fn, 'r').read())
    except Exception as e:
        print(e)
        times = changes.copy()
    times['ad'] = False
    open(fn, 'w+').write(json.dumps(times))
    blacklist = json.loads(open("blacklist.json", "r").read())
    bot = bot_data.Bot(blacklist, command_prefix=get_prefix, prefix=get_prefix, command_attrs=dict(hidden=True), help_command=bot_data.HelpFormat(),
                       case_insensitive=True, owner_ids=config["owners"], activity=discord.Game(name="Loading..."), status=discord.Status.dnd,
                       connector=aiohttp.TCPConnector(ssl=False),
                       intents=discord.Intents(members=True, messages=True, guilds=True, bans=True, emojis=True, reactions=True))
    bot.index = i
    bot.local_config = local_config
    bot.config = config
    bot.name = local_config["internal_name"]
    bot.db = database.Database(bot.name)
    if bot.name == "suager":
        bot.db.execute("UPDATE tbl_clan SET usage=0")
    try:
        for file in os.listdir(os.path.join(_name, "cogs")):
            if file.endswith(".py"):
                name = file[:-3]
                bot.load_extension(f"{_name}.cogs.{name}")
    except FileNotFoundError:
        pass
    for file in os.listdir(os.path.join("core", "cogs")):
        if file.endswith(".py"):
            name = file[:-3]
            if name not in local_config["exclude_core_cogs"]:
                bot.load_extension(f"core.cogs.{name}")
    bot.load_extension("jishaku")
    bot.usages = {}
    for command in bot.commands:
        bot.usages[str(command)] = 0
    if "token" in local_config and local_config["token"]:
        tasks.append(loop.create_task(bot.start(local_config["token"])))

try:
    loop.run_until_complete(asyncio.gather(*tasks))
except KeyboardInterrupt or asyncio.CancelledError:
    loop.close()
