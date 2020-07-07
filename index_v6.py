import asyncio
import json
import os
from sqlite3 import OperationalError

import discord

from core.utils import general, database, time, bot_data
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
    db = database.Database(_bot.name)
    try:
        settings = db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
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
    bot = bot_data.Bot(command_prefix=get_prefix, prefix=get_prefix, command_attrs=dict(hidden=True), case_insensitive=True,
                       help_command=bot_data.HelpFormat(), owner_ids=config["owners"], activity=discord.Game(name="Loading..."), status=discord.Status.dnd)
    bot.start_time = boot_time
    bot.index = i
    bot.local_config = local_config
    bot.config = config
    bot.admin_ids = local_config["admins"]
    bot.name = local_config["internal_name"]
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
    if local_config["token"]:
        tasks.append(loop.create_task(bot.start(local_config["token"])))

try:
    loop.run_until_complete(asyncio.gather(*tasks))
except KeyboardInterrupt or asyncio.CancelledError:
    loop.close()
