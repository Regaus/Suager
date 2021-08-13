import asyncio
import json
from sqlite3 import OperationalError

import discord

from utils import bot_data, database, general, temporaries, time

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
    # fn = f"data/{_name}/changes.json"
    # try:
    #      times = json.loads(open(fn, 'r').read())
    # except Exception as e:
    #     print(e)
    #     times = changes.copy()
    # times['ad'] = False
    # open(fn, 'w+').write(json.dumps(times))
    try:
        blacklist = json.loads(open("blacklist.json", "r").read())
    except FileNotFoundError:
        blacklist = []
    name = local_config["internal_name"]
    db = database.Database()
    bot = bot_data.Bot(blacklist, i, local_config, config, name, db, {},
                       command_prefix=get_prefix, prefix=get_prefix, command_attrs=dict(hidden=True), help_command=bot_data.HelpFormat(),
                       case_insensitive=True, owner_ids=config["owners"], activity=discord.Game(name="Loading..."), status=discord.Status.dnd,
                       # connector=aiohttp.TCPConnector(ssl=False),
                       intents=discord.Intents(members=True, messages=True, guilds=True, bans=True, emojis=True, reactions=True))
    # if bot.name == "suager":
    #     bot.db.execute("UPDATE tbl_clan SET usage=0")
    load = bot_data.load[name]
    for name in load:
        bot.load_extension(f"cogs.{name}")
    bot.load_extension("jishaku")
    for command in bot.commands:
        bot.usages[str(command)] = 0
    if "token" in local_config and local_config["token"]:
        tasks.append(loop.create_task(bot.start(local_config["token"])))
        tasks.append(loop.create_task(temporaries.playing(bot)))
        if bot.name == "suager":
            tasks.append(loop.create_task(temporaries.avatars(bot)))
            tasks.append(loop.create_task(temporaries.birthdays(bot)))
            tasks.append(loop.create_task(temporaries.temporaries(bot)))
            tasks.append(loop.create_task(temporaries.vote_bans(bot)))
            tasks.append(loop.create_task(temporaries.polls(bot)))
        if bot.name == "kyomi":
            tasks.append(loop.create_task(temporaries.birthdays(bot)))
            tasks.append(loop.create_task(temporaries.temporaries(bot)))

try:
    loop.run_until_complete(asyncio.gather(*tasks))
except KeyboardInterrupt or asyncio.CancelledError:
    loop.close()
