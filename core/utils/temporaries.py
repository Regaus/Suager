import asyncio
import json

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
                    guild: discord.Guild = bot.get_guild(entry["gid"])
                    if guild is None:
                        general.print_error(f"{time.time()} > Mute entry ID {entry_id} - Guild not found! Putting mute to error list...")
                        logger.log(bot.name, "temporaries", f"{time.time()} > Mute entry ID {entry_id} - Guild not found! Putting mute to error list...")
                        handled = 2
                    else:
                        _data = bot.db.fetchrow("SELECT * FROM settings WHERE gid=?", (guild.id,))
                        if not _data:
                            general.print_error(f"{time.time()} > Mute entry ID {entry_id} - Guild settings not found! Putting mute to error list...")
                            logger.log(bot.name, "temporaries", f"{time.time()} > Mute entry ID {entry_id} - Guild settings not found! "
                                                                f"Putting mute to error list...")
                            handled = 2
                        else:
                            data = json.loads(_data["data"])
                            try:
                                mute_role_id = data["mute_role"]
                            except KeyError:
                                general.print_error(f"{time.time()} > Mute entry ID {entry_id} - Guild has no mute role set! Putting mute to error list...")
                                logger.log(bot.name, "temporaries", f"{time.time()} > Mute entry ID {entry_id} - Guild has no mute role set! "
                                                                    f"Putting mute to error list...")
                                handled = 2
                                # return await general.send("This server has no mute role set, or it no longer exists.", ctx.channel)
                            else:
                                mute_role = guild.get_role(mute_role_id)
                                if not mute_role:
                                    general.print_error(f"{time.time()} > Mute entry ID {entry_id} - Mute role not found! Putting mute to error list...")
                                    logger.log(bot.name, "temporaries", f"{time.time()} > Mute entry ID {entry_id} - Mute role not found! "
                                                                        f"Putting mute to error list...")
                                    handled = 2
                                    # return await general.send("This server has no mute role set, or it no longer exists.", ctx.channel)
                                else:
                                    member: discord.Member = guild.get_member(entry["uid"])
                                    if not member:
                                        general.print_error(f"{time.time()} > Mute entry ID {entry_id} - Member not found! Putting mute to error list...")
                                        logger.log(bot.name, "temporaries", f"{time.time()} > Mute entry ID {entry_id} - Member not found! "
                                                                            f"Putting mute to error list...")
                                        handled = 2
                                    else:
                                        try:
                                            await member.remove_roles(mute_role, reason=f"[Suager Temporaries Handler] Punishment expired")
                                            logger.log(bot.name, "temporaries", f"{time.time()} > Successfully unmuted the user {member} ({member.id}) from "
                                                                                f"guild {guild} ({entry_id})")
                                            handled = 1
                                        except Exception as e:
                                            general.print_error(f"{time.time()} > Mute {entry_id} error: {e}")
                                            logger.log(bot.name, "temporaries", f"{time.time()} > Mute {entry_id} error: {e}")
                                            handled = 2
                                            # return await general.send(f"{type(e).__name__}: {e}", ctx.channel)
                    bot.db.execute("UPDATE temporary SET handled=? WHERE entry_id=?", (handled, entry_id,))
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
