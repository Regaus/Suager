import asyncio
import json
import os
import sys

import discord

from cogs.events import changes
from utils import generic, time, botdata, database, logs

config = generic.get_config()
desc = """Suager - A bot by Regaus"""
print(f"{time.time()} > Initialisation Started")
loop = asyncio.get_event_loop()
tasks = []

# Test DB before launching
tables = database.creation()
if not tables:
    sys.exit(1)
db = database.Database()
logs.create()


async def get_prefix(_bot, ctx):
    uid = _bot.user.id
    default = [f"<@!{uid}> ", f"<@{uid}> "]
    _data = db.fetchrow("SELECT * FROM data_stable WHERE type=? AND id=?", ("settings", ctx.guild.id))
    if not _data:
        dp = config["bots"]["stable"]["prefixes"]
        cp = []
    else:
        data = json.loads(_data['data'])
        dp = config["bots"]["stable"]["prefixes"] if data['use_default'] else []
        cp = data['prefixes']
    sp = config['common_prefix'] if ctx.author.id in config["owners"] else []
    return default + dp + cp + sp


async def get_prefix2(_bot, ctx):
    uid = _bot.user.id
    default = [f"<@!{uid}> ", f"<@{uid}> "]
    _data = db.fetchrow("SELECT * FROM data_beta WHERE type=? AND id=?", ("settings", ctx.guild.id))
    if not _data:
        dp = config["bots"]["beta"]["prefixes"]
        cp = []
    else:
        data = json.loads(_data['data'])
        dp = config["bots"]["beta"]["prefixes"] if data['use_default'] else []
        cp = data['prefixes']
    sp = config['common_prefix'] if ctx.author.id in config["owners"] else []
    return default + dp + cp + sp


async def get_prefix3(_bot, ctx):
    uid = _bot.user.id
    default = [f"<@!{uid}> ", f"<@{uid}> "]
    _data = db.fetchrow("SELECT * FROM data_alpha WHERE type=? AND id=?", ("settings", ctx.guild.id))
    if not _data:
        dp = config["bots"]["alpha"]["prefixes"]
        cp = []
    else:
        data = json.loads(_data['data'])
        dp = config["bots"]["alpha"]["prefixes"] if data['use_default'] else []
        cp = data['prefixes']
    sp = config['common_prefix'] if ctx.author.id in config["owners"] else []
    return default + dp + cp + sp

try:
    # times = json.loads('changes.json')
    times = json.loads(open('changes.json', 'r').read())
except Exception as e:
    print(e)
    times = changes.copy()
times['ad'] = False
open('changes.json', 'w+').write(json.dumps(times))


types = ["stable", "beta", "alpha"]
dirs = ["cogs", "beta", "alpha"]

for i in range(len(types)):
    fn = f"data/{types[i]}/changes.json"
    try:
        times = json.loads(open(fn, 'r').read())
    except Exception as e:
        print(e)
        times = changes.copy()
    times['ad'] = False
    open(fn, 'w+').write(json.dumps(times))
    if config["bots"][types[i]]["boot"]:
        a = config["bots"][types[i]].copy()
        func = get_prefix if i == 0 else get_prefix2 if i == 1 else get_prefix3
        bot = botdata.Bot(command_prefix=func, prefix=a["prefixes"], command_attrs=dict(hidden=True),
                          case_insensitive=True, help_command=botdata.HelpFormat(), description=desc,
                          owner_ids=generic.owners,
                          activity=discord.Activity(type=discord.ActivityType.playing, name=config["playing"]),
                          status=discord.Status.dnd)
        # bot.prefixes = get_prefixes()
        for file in os.listdir(dirs[i]):
            if file.endswith(".py"):
                name = file[:-3]
                bot.load_extension(f"{dirs[i]}.{name}")
        tasks.append(loop.create_task(bot.start(config["tokens"][i])))

try:
    loop.run_until_complete(asyncio.gather(*tasks))
except KeyboardInterrupt:
    print("CTRL + C was pressed, closing asyncio...")
    loop.close()
except asyncio.CancelledError:
    print("Process killed, closing asyncio...")
    loop.close()
