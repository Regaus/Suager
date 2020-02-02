import json
import os

import discord
from discord.ext.commands import when_mentioned_or

from utils import generic, time, botdata

config = generic.get_config()
desc = """Suager v4 - A bot by Regaus
Originates from AlexFlipnote's code"""
print(time.time(False, True, True) + " > Initialisation Started")


async def get_prefix(bot, message):
    uid = bot.user.id
    default = [f"<@!{uid}> ", f"<@{uid}> "]
    if not message.guild:
        prefixes = default + config.prefix
    else:
        try:
            use_default = json.loads(open(os.path.join(generic.prefixes, f'{message.guild.id}.json')).read())['default']
        except FileNotFoundError:
            use_default = True
        prefixes = default + bot.prefixes.get(str(message.guild.id), [])
        if use_default:
            prefixes += config.prefix
    return prefixes
    # if not message.guild:
    #     return config.prefix
    # prefix = bot.prefixes.get(str(message.guild.id), config.prefix)
    # return when_mentioned_or(prefix)


def get_prefixes():
    try:
        res = {}
        dir = generic.prefixes
        files = os.listdir(dir)
        for f in files:
            data = json.loads(open(os.path.join(dir, f)).read())
            res[f"{f[:-5]}"] = data['prefixes']
        return res
    except FileNotFoundError:
        os.mkdir('data')
        os.mkdir(generic.prefixes)
        return {}


bot = botdata.Bot(command_prefix=get_prefix, prefix=config.prefix, command_attrs=dict(hidden=True),
                  case_insensitive=True, help_command=botdata.HelpFormat(), description=desc, owner_ids=config.owners,
                  activity=discord.Activity(type=discord.ActivityType.playing, name=config.playing),
                  status=discord.Status.dnd)
bot.prefixes = get_prefixes()
for file in os.listdir("cogs"):
    if file.endswith(".py"):
        name = file[:-3]
        bot.load_extension(f"cogs.{name}")
bot.run(config.token)
