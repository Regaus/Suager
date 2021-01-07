import asyncio

import discord

from core.utils import bot_data, general, logger, time
from languages import langs


async def temporaries(bot: bot_data.Bot):
    await bot.wait_until_ready()
    print(f"{time.time()} > Initialised Temporaries handler")
    while True:
        expired = bot.db.fetch("SELECT * FROM temporary WHERE DATETIME(expiry) < DATETIME('now') AND handled=0", ())
        bot.db.execute("DELETE FROM temporary WHERE DATETIME(expiry) < DATETIME('now') AND handled=1", ())
        if expired:
            # print(expired)
            for entry in expired:
                entry_id = entry["entry_id"]
                if entry["type"] == "reminder":
                    user: discord.User = bot.get_user(entry["uid"])
                    expiry = langs.gts(entry["expiry"], "en_gb", True, True, False, True, False)
                    if user is not None:
                        await user.send(f"⏰ **Reminder** (for {expiry}):\n\n{entry['message']}")
                        logger.log(bot.name, "temporaries", f"Successfully sent reminder for {expiry} to user {user} ({user.id})")
                    else:
                        general.print_error(f"User ID {user} not found! Skipping reminder {entry_id}...")
                        logger.log(bot.name, "temporaries", f"Could not find user for reminder for {expiry} with Entry ID {entry_id}. Skipping...")
                    bot.db.execute("UPDATE temporary SET handled=1 WHERE entry_id=?", (entry_id,))
                if entry["type"] == "mute":
                    pass
        await asyncio.sleep(1)
