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
    if ctx.guild is not None:
        _data = db.fetchrow("SELECT * FROM data_stable WHERE type=? AND id=?", ("settings", ctx.guild.id))
        if not _data:
            dp = config["bots"]["stable"]["prefixes"]
            cp = []
        else:
            data = json.loads(_data['data'])
            dp = config["bots"]["stable"]["prefixes"] if data['use_default'] else []
            cp = data['prefixes']
        sp = config['common_prefix'] if ctx.author.id in config["owners"] else []
    else:
        dp = config["bots"]["stable"]["prefixes"]
        sp = config['common_prefix'] if ctx.author.id in config["owners"] else []
        cp = []
    return default + dp + cp + sp

try:
    # times = json.loads('changes.json')
    times = json.loads(open('changes.json', 'r').read())
except Exception as e:
    print(e)
    times = changes.copy()
times['ad'] = False
open('changes.json', 'w+').write(json.dumps(times))


types = ["stable"]
dirs = ["cogs"]

fn = f"data/stable/changes.json"
try:
    times = json.loads(open(fn, 'r').read())
except Exception as e:
    print(e)
    times = changes.copy()
times['ad'] = False
open(fn, 'w+').write(json.dumps(times))
a = config["bots"]["stable"].copy()
func = get_prefix
bot = botdata.Bot(command_prefix=func, prefix=a["prefixes"], command_attrs=dict(hidden=True),
                  case_insensitive=True, help_command=botdata.HelpFormat(), description=desc,
                  owner_ids=generic.owners,
                  activity=discord.Activity(type=discord.ActivityType.playing, name=config["playing"]),
                  status=discord.Status.dnd)
# bot.prefixes = get_prefixes()
for file in os.listdir("cogs"):
    if file.endswith(".py"):
        name = file[:-3]
        bot.load_extension(f"cogs.{name}")
tasks.append(loop.create_task(bot.start(config["token"])))

try:
    loop.run_until_complete(asyncio.gather(*tasks))
except KeyboardInterrupt:
    print("CTRL + C was pressed, closing asyncio...")
    loop.close()
except asyncio.CancelledError:
    print("Process killed, closing asyncio...")
    loop.close()
