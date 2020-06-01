import json
import os
import sys

import discord

from cogs.events import changes
from utils import generic, time, botdata, database, logs

config = generic.get_config()
desc = "Suager - A bot by Regaus"
print(f"{time.time()} > Initialisation Started")
# loop = asyncio.get_event_loop()
# tasks = []

# Test DB before launching
tables = database.creation()
if not tables:
    sys.exit(1)
db = database.Database()
logs.create_logs()
# logs.create()


async def get_prefix(_bot, ctx):
    uid = _bot.user.id
    default = [f"<@!{uid}> ", f"<@{uid}> "]
    if ctx.guild is not None:
        _data = db.fetchrow("SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not _data:
            dp = config["prefixes"]
            cp = []
        else:
            data = json.loads(_data['data'])
            dp = config["prefixes"] if data['use_default'] else []
            cp = data['prefixes']
        sp = config['common_prefix'] if ctx.author.id in config["owners"] else []
    else:
        dp = config["prefixes"]
        sp = config['common_prefix'] if ctx.author.id in config["owners"] else []
        cp = []
    return default + dp + cp + sp

fn = f"data/changes.json"
try:
    times = json.loads(open(fn, 'r').read())
except Exception as e:
    print(e)
    times = changes.copy()
times['ad'] = False
open(fn, 'w+').write(json.dumps(times))
bot = botdata.Bot(command_prefix=get_prefix, prefix=config["prefixes"], command_attrs=dict(hidden=True),
                  case_insensitive=True, help_command=botdata.HelpFormat(), description=desc,
                  owner_ids=generic.owners,
                  activity=discord.Game(name=config["playing"]),
                  # activity=discord.Activity(type=discord.ActivityType.playing, name=config["playing"]),
                  status=discord.Status.dnd)
# bot.prefixes = get_prefixes()
for file in os.listdir("cogs"):
    if file.endswith(".py"):
        name = file[:-3]
        bot.load_extension(f"cogs.{name}")
# tasks.append(loop.create_task(bot.start(config["token"])))
bot.run(config["token"])
