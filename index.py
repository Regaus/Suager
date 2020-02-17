import json
import os
import sys

import discord

from utils import generic, time, botdata, create_tables, sqlite

config = generic.get_config()
desc = """Suager v4 - A bot by Regaus
Originates from AlexFlipnote's code"""
print(time.time(False, True, True) + " > Initialisation Started")

# Test DB before launching
tables = create_tables.creation(debug=True)
if not tables:
    sys.exit(1)
db = sqlite.Database()


# async def get_prefix(_bot, message):
#     uid = _bot.user.id
#     default = [f"<@!{uid}> ", f"<@{uid}> "]
#     if not message.guild:
#         prefixes = default + config.prefix
#     else:
#         try:
#             data = json.loads(open(f"{generic.prefixes}/{message.guild.id}.json", 'r').read())
#             pre = data['prefixes']
#             ud = data['default']
#             pre += config.prefix if ud else []
#             prefixes = default + pre
#         except FileNotFoundError:
#             prefixes = default + config.prefix
#    return prefixes
#     # if not message.guild:
#     #     return config.prefix
#     # prefix = bot.prefixes.get(str(message.guild.id), config.prefix)
#     # return when_mentioned_or(prefix)

async def get_prefix(_bot, ctx):
    uid = _bot.user.id
    default = [f"<@!{uid}> ", f"<@{uid}> "]
    _data = db.fetchrow("SELECT * FROM data WHERE type=? AND id=?", ("settings", ctx.guild.id))
    if not _data:
        dp = config.prefix
        cp = []
    else:
        data = json.loads(_data['data'])
        dp = config.prefix if data['use_default'] else []
        cp = data['prefixes']
    return default + dp + cp


try:
    files = os.listdir(generic.prefixes)
except FileNotFoundError:
    os.mkdir('data')
    os.mkdir(generic.prefixes)


bot = botdata.Bot(command_prefix=get_prefix, prefix=config.prefix, command_attrs=dict(hidden=True),
                  case_insensitive=True, help_command=botdata.HelpFormat(), description=desc, owner_ids=config.owners,
                  activity=discord.Activity(type=discord.ActivityType.playing, name=config.playing),
                  status=discord.Status.dnd)
# bot.prefixes = get_prefixes()
for file in os.listdir("cogs"):
    if file.endswith(".py"):
        name = file[:-3]
        bot.load_extension(f"cogs.{name}")
bot.run(config.token)
