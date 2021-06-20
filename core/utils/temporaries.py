import asyncio
import json
import random
from datetime import date, timedelta

import aiohttp
import discord

from core.utils import bot_data, general, http, logger, time
from languages import langs
from suager.cogs.birthdays import Ctx
from suager.utils import lists


async def temporaries(bot: bot_data.Bot):
    """ Handle reminders and mutes """
    await bot.wait_until_ready()
    print(f"{time.time()} > Initialised Temporaries")
    while True:
        expired = bot.db.fetch("SELECT * FROM temporary WHERE DATETIME(expiry) < DATETIME('now') AND handled=0", ())
        bot.db.execute("DELETE FROM temporary WHERE handled=1", ())
        if expired:
            # print(expired)
            for entry in expired:
                entry_id = entry["entry_id"]
                handled = 2
                if entry["type"] == "reminder":
                    user: discord.User = bot.get_user(entry["uid"])
                    expiry = langs.gts(entry["expiry"], "en", True, True, False, True, False)
                    try:
                        if user is not None:
                            await user.send(f"⏰ **Reminder**:\n\n{entry['message']}")  # (for {expiry})
                            logger.log(bot.name, "temporaries", f"{time.time()} > Successfully sent the user {user} ({user.id}) the reminder for {expiry} ({entry_id})")
                            handled = 1
                        else:
                            general.print_error(f"{time.time()} > Reminder ID {entry_id} - User ID {user} not found!")
                            logger.log(bot.name, "temporaries", f"{time.time()} > Reminder ID {entry_id} - User not found!")
                    except Exception as e:
                        general.print_error(f"{time.time()} > Reminder ID {entry_id} - Error: {e}")
                        logger.log(bot.name, "temporaries", f"{time.time()} > Reminder ID {entry_id} - Error: {e}")
                elif entry["type"] == "mute":
                    guild: discord.Guild = bot.get_guild(entry["gid"])
                    if guild is None:
                        general.print_error(f"{time.time()} > Mute entry ID {entry_id} - Guild not found!")
                        logger.log(bot.name, "temporaries", f"{time.time()} > Mute entry ID {entry_id} - Guild not found!")
                    else:
                        _data = bot.db.fetchrow("SELECT * FROM settings WHERE gid=?", (guild.id,))
                        if not _data:
                            general.print_error(f"{time.time()} > Mute entry ID {entry_id} - Guild settings not found!")
                            logger.log(bot.name, "temporaries", f"{time.time()} > Mute entry ID {entry_id} - Guild settings not found!")
                        else:
                            data = json.loads(_data["data"])
                            try:
                                mute_role_id = data["mute_role"]
                            except KeyError:
                                general.print_error(f"{time.time()} > Mute entry ID {entry_id} - Guild has no mute role set!")
                                logger.log(bot.name, "temporaries", f"{time.time()} > Mute entry ID {entry_id} - Guild has no mute role set!")
                                # return await general.send("This server has no mute role set, or it no longer exists.", ctx.channel)
                            else:
                                mute_role = guild.get_role(mute_role_id)
                                if not mute_role:
                                    general.print_error(f"{time.time()} > Mute entry ID {entry_id} - Mute role not found!")
                                    logger.log(bot.name, "temporaries", f"{time.time()} > Mute entry ID {entry_id} - Mute role not found!")
                                    # return await general.send("This server has no mute role set, or it no longer exists.", ctx.channel)
                                else:
                                    member: discord.Member = guild.get_member(entry["uid"])
                                    if not member:
                                        general.print_error(f"{time.time()} > Mute entry ID {entry_id} - Member not found!")
                                        logger.log(bot.name, "temporaries", f"{time.time()} > Mute entry ID {entry_id} - Member not found!")
                                    else:
                                        try:
                                            await member.remove_roles(mute_role, reason=f"[Auto-Unmute] Punishment expired")
                                            logger.log(bot.name, "temporaries", f"{time.time()} > Successfully unmuted the user {member} ({member.id}) from "
                                                                                f"guild {guild} ({entry_id})")
                                            handled = 1
                                        except Exception as e:
                                            general.print_error(f"{time.time()} > Mute ID {entry_id} - Error: {e}")
                                            logger.log(bot.name, "temporaries", f"{time.time()} > Mute ID {entry_id} - Error: {e}")
                                            # return await general.send(f"{type(e).__name__}: {e}", ctx.channel)
                bot.db.execute("UPDATE temporary SET handled=? WHERE entry_id=?", (handled, entry_id,))
        await asyncio.sleep(1)


async def try_error_temps(bot: bot_data.Bot):
    """ Try to handle temporaries that had an error, else delete them """
    errors = bot.db.fetch("SELECT * FROM temporary WHERE handled=2", ())
    if errors:
        for entry in errors:
            entry_id = entry["entry_id"]
            if entry["type"] == "reminder":
                user: discord.User = bot.get_user(entry["uid"])
                expiry = langs.gts(entry["expiry"], "en", True, True, False, True, False)
                try:
                    if user is not None:
                        await user.send(f"There was an error sending this reminder earlier.\n⏰ **Reminder** (for {expiry}):\n\n{entry['message']}")
                        logger.log(bot.name, "temporaries", f"{time.time()} > Successfully sent the user {user} ({user.id}) the "
                                                            f"reminder for {expiry} ({entry_id}) (previously was an error)")
                    else:
                        general.print_error(f"{time.time()} > Reminder ID {entry_id} - User ID {user} not found! Deleting...")
                        logger.log(bot.name, "temporaries", f"{time.time()} > Still could not find user for reminder for {expiry} with Entry ID {entry_id}! "
                                                            f"Deleting reminder...")
                except Exception as e:
                    general.print_error(f"{time.time()} > Reminder ID {entry_id} - Error: {e} | Deleting...")
                    logger.log(bot.name, "temporaries", f"{time.time()} > Reminder ID {entry_id} - Error: {e} | Deleting reminder...")
            if entry["type"] == "mute":
                guild: discord.Guild = bot.get_guild(entry["gid"])
                if guild is None:
                    general.print_error(f"{time.time()} > Mute entry ID {entry_id} - Guild not found! Deleting...")
                    logger.log(bot.name, "temporaries", f"{time.time()} > Mute entry ID {entry_id} - Guild not found! Deleting...")
                else:
                    _data = bot.db.fetchrow("SELECT * FROM settings WHERE gid=?", (guild.id,))
                    if not _data:
                        general.print_error(f"{time.time()} > Mute entry ID {entry_id} - Guild settings not found! Deleting...")
                        logger.log(bot.name, "temporaries", f"{time.time()} > Mute entry ID {entry_id} - Guild settings not found! Deleting...")
                    else:
                        data = json.loads(_data["data"])
                        try:
                            mute_role_id = data["mute_role"]
                        except KeyError:
                            general.print_error(f"{time.time()} > Mute entry ID {entry_id} - Guild has no mute role set! Deleting...")
                            logger.log(bot.name, "temporaries", f"{time.time()} > Mute entry ID {entry_id} - Guild has no mute role set! Deleting...")
                        else:
                            mute_role = guild.get_role(mute_role_id)
                            if not mute_role:
                                general.print_error(f"{time.time()} > Mute entry ID {entry_id} - Mute role not found! Deleting...")
                                logger.log(bot.name, "temporaries", f"{time.time()} > Mute entry ID {entry_id} - Mute role not found! Deleting...")
                            else:
                                member: discord.Member = guild.get_member(entry["uid"])
                                if not member:
                                    general.print_error(f"{time.time()} > Mute entry ID {entry_id} - Member not found! Deleting...")
                                    logger.log(bot.name, "temporaries", f"{time.time()} > Mute entry ID {entry_id} - Member not found! Deleting...")
                                else:
                                    try:
                                        await member.remove_roles(mute_role, reason=f"[Auto-Unmute] Punishment expired")
                                        logger.log(bot.name, "temporaries", f"{time.time()} > Successfully unmuted the user {member} ({member.id}) from "
                                                                            f"guild {guild} ({entry_id}) (previously was an error)")
                                    except Exception as e:
                                        general.print_error(f"{time.time()} > Mute ID {entry_id} - Error: {e}")
                                        logger.log(bot.name, "temporaries", f"{time.time()} > Mute ID {entry_id} - Error: {e}")
            bot.db.execute("UPDATE temporary SET handled=1 WHERE entry_id=?", (entry_id,))


bd_config = {  # Birthday data: {Guild: [BirthdayChannel, BirthdayRole]}
    568148147457490954: [568148147457490958, 663661621448802304],
    706574018928443442: [715620849167761458, 720780796293677109],
    738425418637639775: [738425419325243424, 748647340423905420]
}


async def birthdays(bot: bot_data.Bot):
    """ Handle birthdays """
    await bot.wait_until_ready()

    now = time.now(None)
    then = (now + timedelta(hours=1)).replace(minute=0, second=1, microsecond=0)  # Start at xx:00:01 to avoid starting at 59:59 and breaking everything
    await asyncio.sleep((then - now).total_seconds())
    print(f"{time.time()} > Initialised Birthdays for {bot.local_config['name']}")

    birthday_table = "birthdays_kyomi" if bot.name == "kyomi" else "birthdays"
    _guilds, _channels, _roles = [], [], []
    for guild, data in bd_config.items():
        _guilds.append(guild)
        _channels.append(data[0])
        _roles.append(data[1])
    guilds = [bot.get_guild(guild) for guild in _guilds]
    channels = [bot.get_channel(cid) for cid in _channels]
    roles = [discord.Object(id=rid) for rid in _roles]
    while True:
        birthday_today = bot.db.fetch(f"SELECT * FROM {birthday_table} WHERE has_role=0 AND strftime('%m-%d', birthday) = strftime('%m-%d', 'now')")
        if birthday_today:
            for person in birthday_today:
                dm = True
                for i in range(len(guilds)):
                    try:
                        guild = guilds[i]
                        if guild is not None:
                            user = guild.get_member(person["uid"])
                            if user is not None:
                                dm = False
                                await general.send(langs.gls("birthdays_message", langs.gl(Ctx(guild, bot)), user.mention), channels[i], u=True)
                                await user.add_roles(roles[i], reason=f"{user} has birthday 🎂🎉")
                                print(f"{time.time()} > {bot.name} > {guild.name} > Gave birthday role to {user.name}")
                    except Exception as e:
                        print(f"{time.time()} > {bot.name} > Birthdays Handler > {e}")
                if dm:
                    try:
                        user = bot.get_user(person["uid"])
                        if user is not None:
                            await user.send(langs.gls("birthdays_message", "en", user.mention))
                            print(f"{time.time()} > {bot.name} > Told {user.name} happy birthday in DMs")
                        else:
                            print(f"{time.time()} > {bot.name} > User {person['uid']} was not found")
                    except Exception as e:
                        print(f"{time.time()} > {bot.name} > Birthdays Handler > {e}")
                bot.db.execute(f"UPDATE {birthday_table} SET has_role=1 WHERE uid=?", (person["uid"],))
        birthday_over = bot.db.fetch(f"SELECT * FROM {birthday_table} WHERE has_role=1 AND strftime('%m-%d', birthday) != strftime('%m-%d', 'now')")
        for person in birthday_over:
            bot.db.execute(f"UPDATE {birthday_table} SET has_role=0 WHERE uid=?", (person["uid"],))
            for i in range(len(guilds)):
                try:
                    guild = guilds[i]
                    if guild is not None:
                        user = guild.get_member(person["uid"])
                        if user is not None:
                            await user.remove_roles(roles[i], reason=f"It is no longer {user}'s birthday...")
                            print(f"{time.time()} > {bot.name} > {guild.name} > Removed birthday role from {user.name}")
                except Exception as e:
                    print(f"{time.time()} > {bot.name} > Birthdays Handler > {e}")
        await asyncio.sleep(3600)


async def playing(bot: bot_data.Bot):
    await bot.wait_until_ready()
    update_speed = 150

    now = time.now(None)
    then = time.from_ts(((time.get_ts(now) // update_speed) + 1) * update_speed, None)
    await asyncio.sleep((then - now).total_seconds())
    print(f"{time.time()} > Initialised Playing updater for {bot.local_config['name']}")

    while True:
        try:
            log = bot.local_config["logs"]
            # plays = self.local_config["playing"]
            version = general.get_version()[bot.name]
            fv, sv = f"v{version['version']}", f"v{version['short_version']}"
            today = date.today()
            year = today.year

            def get_date(month, day):
                _date = date(year, month, day)
                if today > _date:
                    return date(year + 1, month, day)
                return _date

            def until(when: date):
                days = (when - today).days
                s = "s" if days != 1 else ""
                return f"{days} day{s}"

            regaus = get_date(1, 27)
            suager = get_date(5, 13)
            cobble = get_date(12, 5)
            kyomi = get_date(5, 19)
            blucy = get_date(7, 13)
            mizuki = get_date(6, 17)
            is_regaus, is_suager, is_cobble, is_kyomi, is_blucy, is_mizuki = today == regaus, today == suager, today == cobble, today == kyomi, today == blucy, today == mizuki

            status_regaus = f"🎉 Today is Regaus's birthday!" if is_regaus else f"{until(regaus)} until Regaus's birthday"
            status_suager = f"🎉 Today is my birthday!" if is_suager else f"{until(suager)} until my birthday"
            status_cobble = f"🎉 Today is my birthday!" if is_cobble else f"{until(cobble)} until my birthday"
            status_kyomi = f"🎉 Today is Kyomi's birthday!" if is_kyomi else f"{until(kyomi)} until Kyomi's birthday"
            status_blucy = f"🎉 Today is Blucy's birthday!" if is_blucy else f"{until(blucy)} until Blucy's birthday"
            status_mizuki = f"🎉 Today is my birthday!" if is_mizuki else f"{until(mizuki)} until my birthday"
            plays = {
                "cobble": [
                    {"type": 0, "name": fv},
                    {"type": 0, "name": f"{bot.local_config['prefixes'][0]}help | {sv}"},
                    {"type": 1, "name": "nothing", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
                    {"type": 0, "name": "with Regaus"},
                    {"type": 0, "name": "without you"},
                    {"type": 0, "name": "with nobody"},
                    {"type": 0, "name": "with your feelings"},
                    {"type": 5, "name": "uselessness"},
                    {"type": 0, "name": "nothing"},
                    {"type": 3, "name": "you"},
                    {"type": 2, "name": "a song"},
                    {"type": 3, "name": "the void"},
                    {"type": 0, "name": status_regaus},
                    {"type": 0, "name": status_cobble},
                ],
                "kyomi": [
                    {"type": 0, "name": fv},
                    {"type": 0, "name": f"{bot.local_config['prefixes'][0]}help | {sv}"},
                    {"type": 0, "name": status_regaus},
                    {"type": 0, "name": status_kyomi},
                    {"type": 0, "name": status_blucy},
                    {"type": 0, "name": status_mizuki},
                    {"type": 0, "name": "Snuggling with Mochi"},
                    {"type": 0, "name": "Feeding Mochi"},
                    {"type": 0, "name": "Stealing pineapples"},
                    {"type": 0, "name": "Stealing star cookies"},
                    {"type": 0, "name": "Praying to the Pineapple God"},
                    {"type": 3, "name": "you"},
                ],
                "suager": [
                    {"type": 0, "name": fv},
                    {"type": 0, "name": f"{bot.local_config['prefixes'][0]}help | {sv}"},
                    {"type": 1, "name": "Русские Вперёд!", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
                    {"type": 1, "name": "nothing", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
                    {"type": 2, "name": "music"},
                    {"type": 5, "name": "a competition"},
                    {"type": 0, "name": "with Regaus"},
                    {"type": 0, "name": "without you"},
                    {"type": 0, "name": "with nobody"},
                    {"type": 0, "name": "with your feelings"},
                    # {"type": 0, "name": "Custom Status"},
                    {"type": 0, "name": "Discord"},
                    {"type": 3, "name": "Senko"},
                    {"type": 5, "name": "uselessness"},
                    # {"type": 0, "name": "nothing"},
                    {"type": 1, "name": "nothing", "url": "https://www.youtube.com/watch?v=qD_CtEX5OuA"},
                    {"type": 3, "name": "you"},
                    # {"type": 0, "name": "None"},
                    # {"type": 0, "name": "KeyError: 'name'"},
                    # {"type": 0, "name": "IndexError: list index out of range"},
                    # {"type": 0, "name": "suager.utils.exceptions.BoredomError: Imagine reading this"},
                    # {"type": 0, "name": "TypeError: unsupported operand type(s) for +: 'Activity' and 'Activity'"},
                    {"type": 3, "name": "the Void"},
                    # {"type": 0, "name": "PyCharm"},
                    {"type": 0, "name": "a game"},
                    {"type": 1, "name": "a stream", "url": "https://www.youtube.com/watch?v=d1YBv2mWll0"},
                    {"type": 2, "name": "a song"},
                    {"type": 2, "name": "the void"},
                    {"type": 2, "name": "Terraria's soundtrack"},
                    {"type": 2, "name": "your conversations"},
                    {"type": 3, "name": "murder"},
                    {"type": 3, "name": "arson"},
                    {"type": 2, "name": "your screams for help"},
                    # {"type": 3, "name": "something"},
                    # {"type": 3, "name": "nothing"},
                    # {"type": 0, "name": "something"},
                    {"type": 0, "name": "sentience"},
                    {"type": 0, "name": status_regaus},
                    {"type": 0, "name": status_suager},
                ]
            }
            _activity = random.choice(plays.get(bot.name))
            # playing = f"{play} | v{self.local_config['short_version']}"
            if _activity["type"] == 0:  # Game
                activity = discord.Game(name=_activity["name"])
            elif _activity["type"] == 1:  # Streaming
                name = _activity["name"]
                activity = discord.Streaming(name=name, details=name, url=_activity["url"])
            else:
                activity = discord.Activity(type=_activity["type"], name=_activity["name"])
                # activity = discord.Activity(type=activity, name=playing)
            await bot.change_presence(activity=activity, status=discord.Status.dnd)
            if log:
                name = _activity["name"]
                status = {
                    0: "Playing",
                    1: "Streaming",
                    2: "Listening to",
                    3: "Watching",
                    5: "Competing in"
                }.get(_activity["type"], "Undefined")
                logger.log(bot.name, "playing", f"{time.time()} > {bot.local_config['name']} > Updated activity to {status} {name}")
        except PermissionError:
            general.print_error(f"{time.time()} > {bot.local_config['name']} > Playing Changer > Failed to save changes.")
        except aiohttp.ClientConnectorError:
            general.print_error(f"{time.time()} > {bot.local_config['name']} > Playing Changer > The bot tried to do something while disconnected.")
        except Exception as e:
            general.print_error(f"{time.time()} > {bot.local_config['name']} > Playing Changer > {type(e).__name__}: {e}")
        await asyncio.sleep(update_speed)


async def avatars(bot: bot_data.Bot):
    await bot.wait_until_ready()

    now = time.now(None)
    then = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)  # Start at xx:00:01 to avoid starting at 59:59 and breaking everything
    await asyncio.sleep((then - now).total_seconds())
    print(f"{time.time()} > Initialised Avatar updater")

    while True:
        try:
            bot.config = general.get_config()
            bot.local_config = bot.config["bots"][bot.index]
            log = bot.local_config["logs"]
            # avatars = lists.avatars
            avatar = random.choice(lists.avatars)
            e = False
            s1, s2 = [f"{time.time()} > {bot.local_config['name']} > Avatar updated", f"{time.time()} > {bot.name} > Didn't change avatar due to an error"]
            try:
                bio = await http.get(avatar, res_method="read")
                await bot.user.edit(avatar=bio)
            except discord.errors.HTTPException:
                e = True
            send = s2 if e else s1
            if log:
                logger.log(bot.name, "avatar", send)
        except PermissionError:
            general.print_error(f"{time.time()} > {bot.local_config['name']} > Avatar Changer > Failed to save changes.")
        except aiohttp.ClientConnectorError:
            general.print_error(f"{time.time()} > {bot.local_config['name']} > Avatar Changer > The bot tried to do something while disconnected.")
        except Exception as e:
            general.print_error(f"{time.time()} > {bot.local_config['name']} > Avatar Changer > {type(e).__name__}: {e}")
        await asyncio.sleep(3600)
