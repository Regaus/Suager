import asyncio

import discord

from core.utils import bot_data, general, logger, time
from languages import langs


async def temporaries(bot: bot_data.Bot):
    await bot.wait_until_ready()
    print(f"{time.time()} > Initialised Temporaries handler")
    while True:
        expired = bot.db.fetch("SELECT * FROM temporary WHERE DATETIME(expiry) < DATETIME('now') AND handled=0", ())
        bot.db.execute("DELETE FROM temporary WHERE handled=1", ())
        if expired:
            # print(expired)
            for entry in expired:
                entry_id = entry["entry_id"]
                if entry["type"] == "reminder":
                    user: discord.User = bot.get_user(entry["uid"])
                    expiry = langs.gts(entry["expiry"], "en_gb", True, True, False, True, False)
                    try:
                        if user is not None:
                            await user.send(f"⏰ **Reminder** (for {expiry}):\n\n{entry['message']}")
                            logger.log(bot.name, "temporaries", f"{time.time()} > Successfully sent the user {user} ({user.id}) the "
                                                                f"reminder for {expiry} ({entry_id})")
                            bot.db.execute("UPDATE temporary SET handled=1 WHERE entry_id=?", (entry_id,))
                        else:
                            general.print_error(f"{time.time()} > User ID {user} not found! Putting reminder {entry_id} to error list...")
                            logger.log(bot.name, "temporaries", f"{time.time()} > Could not find user for reminder for {expiry} with Entry ID {entry_id}!")
                            bot.db.execute("UPDATE temporary SET handled=2 WHERE entry_id=?", (entry_id,))
                    except Exception as e:
                        general.print_error(f"{time.time()} > Reminder {entry_id} error: {e}")
                        logger.log(bot.name, "temporaries", f"{time.time()} > Reminder {entry_id} error: {e}")
                        bot.db.execute("UPDATE temporary SET handled=2 WHERE entry_id=?", (entry_id,))
                if entry["type"] == "mute":
                    pass
        await asyncio.sleep(1)


async def try_error_temps(bot: bot_data.Bot):
    errors = bot.db.fetch("SELECT * FROM temporary WHERE handled=2", ())
    if errors:
        for entry in errors:
            entry_id = entry["entry_id"]
            if entry["type"] == "reminder":
                user: discord.User = bot.get_user(entry["uid"])
                expiry = langs.gts(entry["expiry"], "en_gb", True, True, False, True, False)
                try:
                    if user is not None:
                        await user.send(f"There was an error sending this reminder earlier.\n⏰ **Reminder** (for {expiry}):\n\n{entry['message']}")
                        logger.log(bot.name, "temporaries", f"{time.time()} > Successfully sent the user {user} ({user.id}) the "
                                                            f"reminder for {expiry} ({entry_id}) (previously was an error)")
                    else:
                        general.print_error(f"{time.time()} > User ID {user} not found! Skipping...")
                        logger.log(bot.name, "temporaries", f"{time.time()} > Could not find user for reminder for {expiry} with Entry ID {entry_id}! "
                                                            f"Skipping reminder...")
                except Exception as e:
                    general.print_error(f"{time.time()} > Reminder {entry_id} error: {e} | Skipping...")
                    logger.log(bot.name, "temporaries", f"{time.time()} > Reminder {entry_id} error: {e} | Skipping...")
            bot.db.execute("UPDATE temporary SET handled=1 WHERE entry_id=?", (entry_id,))
            if entry["type"] == "mute":
                pass
