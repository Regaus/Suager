import os

import discord

from utils import generic, time, botdata

config = generic.get_config()
desc = """Suager v4 - A bot by Regaus
Originates from AlexFlipnote's code"""
print(time.time(False, True, True) + " > Initialisation Started")
bot = botdata.Bot(command_prefix=config.prefix, prefix=config.prefix, command_attrs=dict(hidden=True),
                  case_insensitive=True, help_command=botdata.HelpFormat(), description=desc, owner_ids=config.owners,
                  activity=discord.Activity(type=discord.ActivityType.playing, name=config.playing),
                  status=discord.Status.dnd)
for file in os.listdir("cogs"):
    if file.endswith(".py"):
        name = file[:-3]
        bot.load_extension(f"cogs.{name}")
bot.run(config.token)
