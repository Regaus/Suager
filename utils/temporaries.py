import asyncio
import json
import random
from datetime import date, timedelta

import aiohttp
import discord

from utils import bot_data, general, http, languages, lists, logger, places, time, times


async def temporaries(bot: bot_data.Bot):
    """ Handle reminders and mutes """
    await bot.wait_until_ready()
    print(f"{time.time()} > {bot.full_name} > Initialised Temporaries")
    while True:
        expired = bot.db.fetch("SELECT * FROM temporary WHERE DATETIME(expiry) < DATETIME('now') AND handled=0 AND bot=?", (bot.name,))
        bot.db.execute("DELETE FROM temporary WHERE handled=1", ())
        if expired:
            # print(expired)
            for entry in expired:
                entry_id = entry["entry_id"]
                handled = 2
                if entry["type"] == "reminder":
                    user: discord.User = bot.get_user(entry["uid"])
                    expiry = bot.language2("english").time(entry["expiry"], short=1, dow=False, seconds=True, tz=False)
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
                                            if guild.id == 869975256566210641:  # Nuriki's anarchy server
                                                await member.add_roles(guild.get_role(869975498799845406), reason="Punishment expired")  # Give back the Anarchists role
                                                try:
                                                    await member.send(f"You have been unmuted in {guild.name}: Your mute has expired.")
                                                except discord.Forbidden:
                                                    pass
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
    errors = bot.db.fetch("SELECT * FROM temporary WHERE handled=2 AND bot=?", (bot.name,))
    if errors:
        for entry in errors:
            entry_id = entry["entry_id"]
            if entry["type"] == "reminder":
                user: discord.User = bot.get_user(entry["uid"])
                expiry = bot.language2("english").time(entry["expiry"], short=1, dow=False, seconds=True, tz=False)
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


# bd_config = {  # Birthday data: {Guild: [BirthdayChannel, BirthdayRole]}
#     568148147457490954: [568148147457490958, 663661621448802304],  # Senko Lair
#     706574018928443442: [715620849167761458, 720780796293677109],  # oda-shi
#     738425418637639775: [738425419325243424, 748647340423905420],  # Regaus'tar Koankadu
#     693948857939132478: [716144209567940660, 857074383985311755],  # Midnight Dessert
# }


async def birthdays(bot: bot_data.Bot):
    """ Handle birthdays """
    await bot.wait_until_ready()

    now = time.now(None)
    then = (now + timedelta(hours=1)).replace(minute=0, second=1, microsecond=0)  # Start at xx:00:01 to avoid starting at 59:59 and breaking everything
    await asyncio.sleep((then - now).total_seconds())
    print(f"{time.time()} > {bot.full_name} > Initialised Birthdays")

    # birthday_message = "birthdays_message2" if bot.name == "kyomi" else "birthdays_message"
    # _guilds, _channels, _roles = [], [], []
    # for guild, data in bd_config.items():
    #     _guilds.append(guild)
    #     _channels.append(data[0])
    #     _roles.append(data[1])
    # guilds = [bot.get_guild(guild) for guild in _guilds]
    # channels = [bot.get_channel(cid) for cid in _channels]
    # roles = [discord.Object(id=rid) for rid in _roles]
    while True:
        guilds = {}
        settings = bot.db.fetch("SELECT * FROM settings WHERE bot=?", (bot.name,))
        for entry in settings:
            data = json.loads(entry["data"])
            if "birthdays" in data:
                if data["birthdays"]["enabled"]:
                    out = [data["birthdays"]["role"], data["birthdays"]["channel"], data["birthdays"]["message"]]
                    guilds[entry["gid"]] = out
        birthday_today = bot.db.fetch("SELECT * FROM birthdays WHERE has_role=0 AND strftime('%m-%d', birthday) = strftime('%m-%d', 'now') AND bot=?", (bot.name,))
        if birthday_today:
            for person in birthday_today:
                # dm = True
                for gid, data in guilds.items():
                    # guild = guilds[i]
                    guild: discord.Guild = bot.get_guild(gid)
                    if guild is not None:
                        user: discord.Member = guild.get_member(person["uid"])
                        if user is not None:
                            # dm = False
                            if data[1] and data[2]:
                                channel: discord.TextChannel = guild.get_channel(data[1])
                                message = data[2].replace("[MENTION]", user.mention).replace("[USER]", user.name)
                                try:
                                    await general.send(message, channel, u=True)
                                    print(f"{time.time()} > {bot.full_name} > {guild.name} > Told {user} happy birthday")
                                except Exception as e:
                                    general.print_error(f"{time.time()} > {bot.full_name} > Birthdays Handler > Birthday Message (Guild {gid}, User {user.id}) > {e}")
                            if data[0]:
                                role: discord.Role = guild.get_role(data[0])
                                try:
                                    await user.add_roles(role, reason=f"[Birthdays] It is {user}'s birthday")
                                    print(f"{time.time()} > {bot.full_name} > {guild.name} > Gave {user} the birthday role")
                                except Exception as e:
                                    general.print_error(f"{time.time()} > {bot.full_name} > Birthdays Handler > Birthday Role (Guild {gid}, User {user.id}) > {e}")
                # if dm:
                #     try:
                #         user = bot.get_user(person["uid"])
                #         if user is not None:
                #             await user.send(bot.language2("english").string("birthdays_message", user.name))
                #             print(f"{time.time()} > {bot.full_name} > Told {user.name} happy birthday in DMs")
                #         else:
                #             general.print_error(f"{time.time()} > {bot.full_name} > User {person['uid']} was not found")
                #     except Exception as e:
                #         general.print_error(f"{time.time()} > {bot.full_name} > Birthdays Handler > {e}")
                bot.db.execute("UPDATE birthdays SET has_role=1 WHERE uid=?", (person["uid"],))
        birthday_over = bot.db.fetch("SELECT * FROM birthdays WHERE has_role=1 AND strftime('%m-%d', birthday) != strftime('%m-%d', 'now') AND bot=?", (bot.name,))
        for person in birthday_over:
            bot.db.execute("UPDATE birthdays SET has_role=0 WHERE uid=? AND bot=?", (person["uid"], bot.name))
            for gid, data in guilds.items():
                # guild = guilds[i]
                guild: discord.Guild = bot.get_guild(gid)
                if guild is not None:
                    user: discord.Member = guild.get_member(person["uid"])
                    if user is not None:
                        if data[0]:
                            role: discord.Role = guild.get_role(data[0])
                            try:
                                await user.remove_roles(role, reason=f"[Birthdays] It is no longer {user}'s birthday")
                                print(f"{time.time()} > {bot.full_name} > {guild.name} > Removed birthday role from {user}")
                            except Exception as e:
                                general.print_error(f"{time.time()} > {bot.full_name} > Birthdays Handler > Birthday Role End (Guild {gid}, User {user.id}) > {e}")
                # except Exception as e:
                #     general.print_error(f"{time.time()} > {bot.full_name} > Birthdays Handler > {e}")

        await asyncio.sleep(3600)


ka_cities = {  # List of Kargadian cities to be shown in the ka-time clock, and in playing statuses
    "Akkigar":       {"english": None, "tebarian": None},  # Weight: 2
    "Bylkangar":     {"english": None, "tebarian": None},  # Weight: 2
    "Ekspigar":      {"english": None, "tebarian": None},  # Weight: 2
    "Huntavall":     {"english": None, "tebarian": None},  # Weight: 3
    "Kaivalgar":     {"english": None, "tebarian": None},  # Weight: 3
    "Kanerakainead": {"english": None, "tebarian": None},  # Weight: 2
    "Kiomigar":      {"english": None, "tebarian": None},  # Weight: 2
    "Lailagar":      {"english": None, "tebarian": None},  # Weight: 2
    "Leitagar":      {"english": None, "tebarian": None},  # Weight: 2
    "Nurvutgar":     {"english": None, "tebarian": None},  # Weight: 2
    "Pakigar":       {"english": None, "tebarian": None},  # Weight: 2
    "Peaskar":       {"english": None, "tebarian": None},  # Weight: 2
    "Regavall":      {"english": None, "tebarian": None},  # Weight: 5
    "Reggar":        {"english": None, "tebarian": None},  # Weight: 5
    "Sentagar":      {"english": None, "tebarian": None},  # Weight: 2
    "Sentatebaria":  {"english": None, "tebarian": None},  # Weight: 3
    "Shonangar":     {"english": None, "tebarian": None},  # Weight: 2
    "Steirigar":     {"english": None, "tebarian": None},  # Weight: 2
    "Suvagar":       {"english": None, "tebarian": None},  # Weight: 3
    "Vintelingar":   {"english": None, "tebarian": None},  # Weight: 2
    "Virsetgar":     {"english": None, "tebarian": None},  # Weight: 2
}
ka_time: times.TimeSolarNormal = times.time_kargadia(tz=0)  # Current time in Virsetgar, used to determine time until next holiday
update_speed = 120  # 150
ka_holidays = {  # List of Kargadian holidays, sorted by day of year when they occur
    1:   ("Nuan Kadan",              "Nuat Kadut"),
    21:  ("Kattansean",              "Kattanseat"),
    55:  ("Sean Tebarian",           "Seat Tebarian"),
    60:  ("Sean na Liidenvirkalten", "Seat na Liidenvirkalten"),
    97:  ("Semiansean",              "Semianseat"),
    105: ("Sean Kaivallun",          "Seat Kaivallun"),
    119: ("Sean Suvakyn",            "Seat Suvakyn"),
    162: ("Sean Regaus'an",          "Seat Regaus'an"),
    193: ("Tentasean",               "Tentaseat"),
    209: ("Sean na Sevarddain",      "Seat na Sevarddain"),
    220: ("Sean Leitakin",           "Seat Leitakin")
}


async def city_data_updater(bot: bot_data.Bot):
    """ Update time and weather data for Kargadian cities """
    await bot.wait_until_ready()

    now = time.now(None)
    # Start this script ahead of the updates to make sure the city time updater and the playing status get accurate data
    then = time.from_ts(((time.get_ts(now) // update_speed) + 1) * update_speed - 1, None)
    await asyncio.sleep((then - now).total_seconds())
    print(f"{time.time()} > {bot.full_name} > Initialised City Data Updater")

    while True:
        try:
            for city in ka_cities.keys():
                place = places.Place(city)
                tebarian = place.time.str(dow=False, era=None, month=False, short=True, seconds=False)
                # Tricks into changing the month from Genitive to Nominative
                english = place.time.str(dow=False, era=None, month=False, short=False, seconds=False).replace("n ", "r ")
                temperature, _, _, rain_out = place.weather()
                if temperature is not None and rain_out is not None:
                    temp = f"{temperature:.0f}°C"
                    weather_en = languages.Language("english").weather_data("weather78")[rain_out]
                    weather_tb = languages.Language("tebarian").weather_data("weather78")[rain_out]
                    english += f" | {temp} | {weather_en}"
                    tebarian += f" | {temp} | {weather_tb}"
                ka_cities[city] = {"english": english, "tebarian": tebarian}
                if city == "Virsetgar":
                    global ka_time
                    ka_time = place.time
            logger.log(bot.name, "kargadia", f"{time.time()} > {bot.full_name} > Updated city data")
        except Exception as e:
            general.print_error(f"{time.time()} > {bot.full_name} > City Data Updater > {type(e).__name__}: {e}")

        # This should make it adjust itself for lag caused
        await asyncio.sleep(2)  # Hopefully prevents it from lagging ahead of itself and hanging
        now = time.now(None)
        then = time.from_ts(((time.get_ts(now) // update_speed) + 1) * update_speed - 1, None)
        await asyncio.sleep((then - now).total_seconds())
        # await asyncio.sleep(update_speed)


async def city_time_updater(bot: bot_data.Bot):
    """ Update the time and weather info for Kargadian cities in Regaus'tar Koankadu """
    await bot.wait_until_ready()

    now = time.now(None)
    then = time.from_ts(((time.get_ts(now) // update_speed) + 1) * update_speed, None)
    await asyncio.sleep((then - now).total_seconds())
    print(f"{time.time()} > {bot.full_name} > Initialised RK City Time Updater")

    while True:
        data = []
        for city, _data in ka_cities.items():
            data.append(f"`{city:<13} - {_data['english']}`")
        out = "\n".join(data)
        channel: discord.TextChannel = bot.get_channel(887087307918802964)  # ka-time
        try:
            # message: discord.Message = (await channel.history(limit=1, oldest_first=True).flatten())[0]
            message = None
            async for msg in channel.history(limit=None, oldest_first=True):
                if msg.author.id == bot.user.id:
                    message = msg
                    break
            if message is None:
                raise general.RegausError("City time message not found")
            await message.edit(content=out)
            logger.log(bot.name, "kargadia", f"{time.time()} > {bot.full_name} > Updated city time message")
        except (IndexError, discord.NotFound, general.RegausError):
            await channel.send(out)
            logger.log(bot.name, "kargadia", f"{time.time()} > {bot.full_name} > Reset city time message")
        except Exception as e:
            general.print_error(f"{time.time()} > {bot.full_name} > City Time Updater > {type(e).__name__}: {e}")

        # This should make it adjust itself for lag caused
        await asyncio.sleep(1)  # Hopefully prevents it from lagging ahead of itself
        now = time.now(None)
        then = time.from_ts(((time.get_ts(now) // update_speed) + 1) * update_speed, None)
        await asyncio.sleep((then - now).total_seconds())
        # await asyncio.sleep(update_speed)


async def playing(bot: bot_data.Bot):
    await bot.wait_until_ready()

    now = time.now(None)
    then = time.from_ts(((time.get_ts(now) // update_speed) + 1) * update_speed, None)
    await asyncio.sleep((then - now).total_seconds())
    print(f"{time.time()} > {bot.full_name} > Initialised Playing updater")

    while True:
        try:
            # log = bot.local_config["logs"]
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

            def until(when: date, rsl: bool = False):
                days = (when - today).days
                if rsl:
                    s = "in" if days != 1 else ""
                    v = "t" if days == 1 else "n"
                    return f"{days} sea{s} astalla{v}"
                else:
                    s = "s" if days != 1 else ""
                    return f"{days} day{s}"

            regaus = get_date(1, 27)
            is_regaus = today == regaus
            status_regaus = f"🎉 Today is Regaus's birthday!" if is_regaus else f"{until(regaus, False)} until Regaus's birthday"
            if bot.name == "cobble":
                status_type = random.choices([1, 2, 3, 4], [15, 40, 15, 30])[0]
                # 1 = birthdays, 2 = playing, 3 = holidays, 4 = time and weather
                if status_type == 1:
                    cobble = get_date(12, 5)
                    is_cobble = today == cobble
                    status_cobble = f"🎉 Esea jat mun reidesea!" if is_cobble else f"{until(cobble, True)} mun reideseat"
                    status_regaus = f"🎉 Esea jat Regaus'ta reidesea!" if is_regaus else f"{until(regaus, True)} Regaus'tat reideseat"
                    status = random.choice([status_cobble, status_regaus])
                    activity = discord.Game(name=status)
                    logger.log(bot.name, "playing", f"{time.time()} > {bot.full_name} > Updated activity to {status} (Status Type 1)")
                elif status_type == 2:
                    activities = [
                        {"type": 0, "name": fv},
                        {"type": 0, "name": f"{bot.local_config['prefixes'][0]}help | {sv}"},
                        {"type": 0, "name": "Regaus'ar"},
                        {"type": 0, "name": "dekedar"},
                        {"type": 0, "name": "tarair sevirtair"},
                        {"type": 5, "name": "noartai"},
                        {"type": 0, "name": "denedaa"},
                        {"type": 3, "name": "ten"},
                        {"type": 3, "name": "ten sevartan"},
                        {"type": 2, "name": "ut penat"},
                        {"type": 3, "name": "na meitan"},
                        {"type": 2, "name": "na deinettat"},
                        {"type": 0, "name": "na Temval na Bylkain'den Liidenvirkalten"},
                        {"type": 0, "name": "na TBL'n"},
                        {"type": 0, "name": "Akos'an"},
                        {"type": 0, "name": "na Tadevan Kunneanpaitenan"},
                        {"type": 0, "name": "na TKP'n"},
                        {"type": 0, "name": "vaihaga kiinanshavarkan"},
                        {"type": 0, "name": "Vainar veikidat pahtemar, discord.py"},
                    ]
                    _activity = random.choice(activities)
                    if _activity["type"] == 0:  # Game
                        activity = discord.Game(name=_activity["name"])
                    elif _activity["type"] == 1:  # Streaming
                        name = _activity["name"]
                        activity = discord.Streaming(name=name, details=name, url=_activity["url"])
                    else:
                        activity = discord.Activity(type=_activity["type"], name=_activity["name"])
                    name = _activity["name"]
                    status = {
                        0: "Koa",
                        1: "Eimia",
                        2: "Sanna",
                        3: "Veita",
                        5: "Aara sen"
                    }.get(_activity["type"], "Undefined")
                    logger.log(bot.name, "playing", f"{time.time()} > {bot.full_name} > Updated activity to {status} {name} (Status Type 2)")
                elif status_type == 3:
                    year_day, holiday = random.choice(list(ka_holidays.items()))
                    now_day = ka_time.year_day
                    if ka_time.year % 16 == 0:
                        now_day -= 1
                    if now_day > year_day:
                        year_day += 256
                        if (ka_time.year + 1) % 16 == 0:
                            year_day += 1
                    days_left = year_day - now_day
                    if days_left == 0:
                        status = f"Kovanan {holiday[0]}"
                    elif days_left == 1:
                        status = f"1 sea astallat {holiday[1]}"
                    else:
                        status = f"{days_left} seain astallan {holiday[1]}"
                    activity = discord.Game(name=status)
                    logger.log(bot.name, "playing", f"{time.time()} > {bot.full_name} > Updated activity to {status} (Status Type 3)")
                else:  # status_type == 4
                    city, city_data = random.choices(list(ka_cities.items()), [2, 2, 2, 3, 3, 2, 2, 2, 2, 2, 2, 2, 5, 5, 2, 3, 2, 2, 3, 2, 2])[0]
                    status = f"{city}: {city_data['tebarian']}"
                    activity = discord.Game(name=status)
                    logger.log(bot.name, "playing", f"{time.time()} > {bot.full_name} > Updated activity to {status} (Status Type 4)")
            elif bot.name == "kyomi":
                status_type = random.random()
                if status_type <= 0.2:  # 20% chance of being a birthday status
                    kyomi = get_date(5, 19)
                    blucy = get_date(7, 13)
                    mizuki = get_date(6, 17)
                    is_kyomi, is_blucy, is_mizuki = today == kyomi, today == blucy, today == mizuki
                    status_kyomi = f"🎉 Today is Kyomi's birthday!" if is_kyomi else f"{until(kyomi, False)} until Kyomi's birthday"
                    status_blucy = f"🎉 Today is Blucy's birthday!" if is_blucy else f"{until(blucy, False)} until Blucy's birthday"
                    status_mizuki = f"🎉 Today is my birthday!" if is_mizuki else f"{until(mizuki, False)} until my birthday"
                    status = random.choice([status_mizuki, status_regaus, status_kyomi, status_blucy])
                    activity = discord.Game(name=status)
                    logger.log(bot.name, "playing", f"{time.time()} > {bot.full_name} > Updated activity to {status} (Status Type 1)")
                else:
                    activities = [
                        {"type": 0, "name": fv},
                        {"type": 0, "name": f"{bot.local_config['prefixes'][0]}help | {sv}"},
                        {"type": 0, "name": "Snuggling with Mochi"},
                        {"type": 0, "name": "Feeding Mochi"},
                        {"type": 0, "name": "Petting Mochi"},
                        {"type": 0, "name": "Eating pineapples"},
                        {"type": 0, "name": "Eating pineapple pizza"},
                        {"type": 0, "name": "Stealing pineapples"},
                        {"type": 0, "name": "Stealing star cookies"},
                        {"type": 0, "name": "Praying to the Pineapple God"},
                        {"type": 3, "name": "you"},
                    ]
                    _activity = random.choice(activities)
                    if _activity["type"] == 0:  # Game
                        activity = discord.Game(name=_activity["name"])
                    elif _activity["type"] == 1:  # Streaming
                        name = _activity["name"]
                        activity = discord.Streaming(name=name, details=name, url=_activity["url"])
                    else:
                        activity = discord.Activity(type=_activity["type"], name=_activity["name"])
                    name = _activity["name"]
                    status = {
                        0: "Playing",
                        1: "Streaming",
                        2: "Listening to",
                        3: "Watching",
                        5: "Competing in"
                    }.get(_activity["type"], "Undefined")
                    logger.log(bot.name, "playing", f"{time.time()} > {bot.full_name} > Updated activity to {status} {name} (Status Type 2)")
            else:  # Suager
                status_type = random.random()
                if status_type <= 0.2:  # 20% chance of being a birthday status
                    suager = get_date(5, 13)
                    is_suager = today == suager
                    status_suager = f"🎉 Today is my birthday!" if is_suager else f"{until(suager, False)} until my birthday"
                    status = random.choice([status_suager, status_regaus])
                    activity = discord.Game(name=status)
                    logger.log(bot.name, "playing", f"{time.time()} > {bot.full_name} > Updated activity to {status} (Status Type 1)")
                else:
                    activities = [
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
                        {"type": 0, "name": "RIP discord.py"},
                    ]
                    _activity = random.choice(activities)
                    if _activity["type"] == 0:  # Game
                        activity = discord.Game(name=_activity["name"])
                    elif _activity["type"] == 1:  # Streaming
                        name = _activity["name"]
                        activity = discord.Streaming(name=name, details=name, url=_activity["url"])
                    else:
                        activity = discord.Activity(type=_activity["type"], name=_activity["name"])
                    name = _activity["name"]
                    status = {
                        0: "Playing",
                        1: "Streaming",
                        2: "Listening to",
                        3: "Watching",
                        5: "Competing in"
                    }.get(_activity["type"], "Undefined")
                    logger.log(bot.name, "playing", f"{time.time()} > {bot.full_name} > Updated activity to {status} {name} (Status Type 2)")
            # plays = {
            #     "cobble": [
            #         {"type": 0, "name": fv},
            #         {"type": 0, "name": f"{bot.local_config['prefixes'][0]}help | {sv}"},
            #         # {"type": 1, "name": "denedaa", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            #         {"type": 0, "name": "Regaus'ar"},
            #         {"type": 0, "name": "dekedar"},
            #         {"type": 0, "name": "tarair sevirtair"},
            #         {"type": 5, "name": "noartai"},
            #         {"type": 0, "name": "denedaa"},
            #         {"type": 3, "name": "ten"},
            #         {"type": 3, "name": "ten sevartan"},
            #         {"type": 2, "name": "ut penat"},
            #         {"type": 3, "name": "na meitan"},
            #         {"type": 2, "name": "na deinettat"},
            #         {"type": 0, "name": status_regaus2},
            #         {"type": 0, "name": status_cobble},
            #         {"type": 0, "name": "na Temval na Bylkain'den Liidenvirkalten"},
            #         {"type": 0, "name": "na TBL'n"},
            #         {"type": 0, "name": "Akos'an"},
            #         {"type": 0, "name": "na Tadevan Kunneanpaitenan"},
            #         {"type": 0, "name": "na TKP'n"},
            #         {"type": 0, "name": "vaihaga kiinanshavarkan"},
            #         {"type": 0, "name": "RIP discord.py"},
            #     ],
            #     "kyomi": [
            #         {"type": 0, "name": fv},
            #         {"type": 0, "name": f"{bot.local_config['prefixes'][0]}help | {sv}"},
            #         {"type": 0, "name": status_regaus},
            #         {"type": 0, "name": status_kyomi},
            #         {"type": 0, "name": status_blucy},
            #         {"type": 0, "name": status_mizuki},
            #         {"type": 0, "name": "Snuggling with Mochi"},
            #         {"type": 0, "name": "Feeding Mochi"},
            #         {"type": 0, "name": "Petting Mochi"},
            #         {"type": 0, "name": "Eating pineapples"},
            #         {"type": 0, "name": "Eating pineapple pizza"},
            #         {"type": 0, "name": "Stealing pineapples"},
            #         {"type": 0, "name": "Stealing star cookies"},
            #         {"type": 0, "name": "Praying to the Pineapple God"},
            #         {"type": 3, "name": "you"},
            #     ],
            #     "suager": [
            #         {"type": 0, "name": fv},
            #         {"type": 0, "name": f"{bot.local_config['prefixes'][0]}help | {sv}"},
            #         {"type": 1, "name": "Русские Вперёд!", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            #         {"type": 1, "name": "nothing", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            #         {"type": 2, "name": "music"},
            #         {"type": 5, "name": "a competition"},
            #         {"type": 0, "name": "with Regaus"},
            #         {"type": 0, "name": "with nobody"},
            #         {"type": 0, "name": "with your feelings"},
            #         # {"type": 0, "name": "Custom Status"},
            #         {"type": 0, "name": "Discord"},
            #         {"type": 3, "name": "Senko"},
            #         {"type": 5, "name": "uselessness"},
            #         # {"type": 0, "name": "nothing"},
            #         {"type": 1, "name": "nothing", "url": "https://www.youtube.com/watch?v=qD_CtEX5OuA"},
            #         {"type": 3, "name": "you"},
            #         # {"type": 0, "name": "None"},
            #         # {"type": 0, "name": "KeyError: 'name'"},
            #         # {"type": 0, "name": "IndexError: list index out of range"},
            #         # {"type": 0, "name": "suager.utils.exceptions.BoredomError: Imagine reading this"},
            #         # {"type": 0, "name": "TypeError: unsupported operand type(s) for +: 'Activity' and 'Activity'"},
            #         {"type": 3, "name": "the Void"},
            #         # {"type": 0, "name": "PyCharm"},
            #         {"type": 0, "name": "a game"},
            #         {"type": 1, "name": "a stream", "url": "https://www.youtube.com/watch?v=d1YBv2mWll0"},
            #         {"type": 2, "name": "a song"},
            #         {"type": 2, "name": "the void"},
            #         {"type": 2, "name": "Terraria's soundtrack"},
            #         {"type": 2, "name": "your conversations"},
            #         {"type": 3, "name": "murder"},
            #         {"type": 3, "name": "arson"},
            #         {"type": 2, "name": "your screams for help"},
            #         # {"type": 3, "name": "something"},
            #         # {"type": 3, "name": "nothing"},
            #         # {"type": 0, "name": "something"},
            #         {"type": 0, "name": "sentience"},
            #         {"type": 0, "name": status_regaus},
            #         {"type": 0, "name": status_suager},
            #         {"type": 0, "name": "RIP discord.py"},
            #     ]
            # }
            # _activity = random.choice(plays.get(bot.name))
            # playing = f"{play} | v{self.local_config['short_version']}"
            # if _activity["type"] == 0:  # Game
            #     activity = discord.Game(name=_activity["name"])
            # elif _activity["type"] == 1:  # Streaming
            #     name = _activity["name"]
            #     activity = discord.Streaming(name=name, details=name, url=_activity["url"])
            # else:
            #     activity = discord.Activity(type=_activity["type"], name=_activity["name"])
            #     # activity = discord.Activity(type=activity, name=playing)
            await bot.change_presence(activity=activity, status=discord.Status.dnd)
            # name = _activity["name"]
            # status = {
            #     0: "Playing",
            #     1: "Streaming",
            #     2: "Listening to",
            #     3: "Watching",
            #     5: "Competing in"
            # }.get(_activity["type"], "Undefined")
            # logger.log(bot.name, "playing", f"{time.time()} > {bot.full_name} > Updated activity to {status} {name}")
        except PermissionError:
            general.print_error(f"{time.time()} > {bot.full_name} > Playing Changer > Failed to save changes.")
        except aiohttp.ClientConnectorError:
            general.print_error(f"{time.time()} > {bot.full_name} > Playing Changer > The bot tried to do something while disconnected.")
        except Exception as e:
            general.print_error(f"{time.time()} > {bot.full_name} > Playing Changer > {type(e).__name__}: {e}")

        # This should make it adjust itself for lag caused
        await asyncio.sleep(1)  # Hopefully prevents it from lagging ahead of itself
        now = time.now(None)
        then = time.from_ts(((time.get_ts(now) // update_speed) + 1) * update_speed, None)
        await asyncio.sleep((then - now).total_seconds())
        # await asyncio.sleep(update_speed)


async def avatars(bot: bot_data.Bot):
    await bot.wait_until_ready()

    now = time.now(None)
    then = (now + timedelta(hours=1)).replace(minute=0, second=1, microsecond=0)
    await asyncio.sleep((then - now).total_seconds())
    print(f"{time.time()} > {bot.full_name} > Initialised Avatar updater")

    while True:
        try:
            # bot.config = general.get_config()
            # bot.local_config = bot.config["bots"][bot.index]
            # log = bot.local_config["logs"]
            # avatars = lists.avatars
            avatar = random.choice(lists.avatars)
            e = False
            s1, s2 = [f"{time.time()} > {bot.full_name} > Avatar updated", f"{time.time()} > {bot.name} > Didn't change avatar due to an error"]
            try:
                bio = await http.get(avatar, res_method="read")
                await bot.user.edit(avatar=bio)
            except discord.errors.HTTPException:
                e = True
            send = s2 if e else s1
            logger.log(bot.name, "avatar", send)
        except PermissionError:
            general.print_error(f"{time.time()} > {bot.full_name} > Avatar Changer > Failed to save changes.")
        except aiohttp.ClientConnectorError:
            general.print_error(f"{time.time()} > {bot.full_name} > Avatar Changer > The bot tried to do something while disconnected.")
        except Exception as e:
            general.print_error(f"{time.time()} > {bot.full_name} > Avatar Changer > {type(e).__name__}: {e}")

        await asyncio.sleep(3600)


async def polls(bot: bot_data.Bot):
    await bot.wait_until_ready()

    print(f"{time.time()} > {bot.full_name} > Initialised Polls")
    while True:
        expired = bot.db.fetch("SELECT * FROM polls WHERE DATETIME(expiry) < DATETIME('now')", ())
        for poll in expired:
            voters_yes: list = json.loads(poll["voters_yes"])
            voters_neutral: list = json.loads(poll["voters_neutral"])
            voters_no: list = json.loads(poll["voters_no"])
            guild_id = poll["guild_id"]
            settings = bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (guild_id, bot.name))
            resend = True
            if settings:
                setting = json.loads(settings["data"])
                if "polls" in setting:
                    resend = setting["polls"]["channel"] == 0
            try:
                guild: discord.Guild = bot.get_guild(guild_id)
                if guild:
                    language = bot.language(languages.FakeContext(guild, bot))
                    channel: discord.TextChannel = guild.get_channel(poll["channel_id"])
                    if channel:
                        embed = discord.Embed()
                        yes, neutral, no = len(voters_yes), len(voters_neutral), len(voters_no)
                        total = yes + neutral + no
                        score = yes - no
                        try:
                            upvotes = yes / (yes + no)
                        except ZeroDivisionError:
                            upvotes = 0
                        if 3 >= score > 0:
                            embed.colour = general.green2
                            result = language.string("generic_yes")
                        elif score > 3:
                            embed.colour = general.green
                            result = language.string("generic_yes")
                        elif -3 <= score < 0:
                            embed.colour = general.red2
                            result = language.string("generic_no")
                        elif score < -3:
                            embed.colour = general.red
                            result = language.string("generic_no")
                        else:
                            embed.colour = general.yellow
                            result = language.string("polls_end_neutral")
                        embed.title = language.string("polls_end_title")
                        ended = language.time(poll["expiry"], short=1, dow=False, seconds=False, tz=False)
                        embed.description = language.string("polls_end_description", poll["question"], ended, result)
                        embed.add_field(name=language.string("polls_votes_result"), inline=False,
                                        value=language.string("polls_votes_current2", language.number(yes), language.number(neutral), language.number(no),
                                                              language.number(total), language.number(score, positives=True),
                                                              language.number(upvotes, precision=2, percentage=True)))
                        if not poll["anonymous"]:
                            _yes = "\n".join([f"<@{voter}>" for voter in voters_yes[:45]])
                            if yes >= 45:
                                _yes += language.string("polls_votes_many", language.number(yes - 45))
                            if not _yes:
                                _yes = language.string("polls_votes_none2")
                            embed.add_field(name=language.string("polls_votes_yes"), value=_yes, inline=True)
                            _neutral = "\n".join([f"<@{voter}>" for voter in voters_neutral[:45]])
                            if neutral >= 45:
                                _neutral += language.string("polls_votes_many", language.number(neutral - 45))
                            if not _neutral:
                                _neutral = language.string("polls_votes_none2")
                            embed.add_field(name=language.string("polls_votes_neutral"), value=_neutral, inline=True)
                            _no = "\n".join([f"<@{voter}>" for voter in voters_no[:45]])
                            if no >= 45:
                                _no += language.string("polls_votes_many", language.number(no - 45))
                            if not _no:
                                _no = language.string("polls_votes_none2")
                            embed.add_field(name=language.string("polls_votes_no"), value=_no, inline=True)
                        if not resend:
                            try:
                                message: discord.Message = await channel.fetch_message(poll["message_id"])
                                if message.embeds:
                                    # embed = message.embeds[0]
                                    await message.edit(embed=embed)
                                    resend = False
                            except discord.NotFound:
                                resend = True
                        if resend:
                            await general.send(None, channel, embed=embed)
            except Exception as e:
                general.print_error(f"{time.time()} > {bot.full_name} > Polls > Poll {poll['poll_id']} error: {type(e).__name__}: {e}")
            bot.db.execute("DELETE FROM polls WHERE poll_id=?", (poll["poll_id"],))

        await asyncio.sleep(1)


async def trials(bot: bot_data.Bot):
    await bot.wait_until_ready()

    print(f"{time.time()} > {bot.full_name} > Initialised Trials")
    while True:
        expired = bot.db.fetch("SELECT * FROM trials WHERE DATETIME(expiry) < DATETIME('now')", ())
        for trial in expired:
            voters_yes: list = json.loads(trial["voters_yes"])
            voters_neutral: list = json.loads(trial["voters_neutral"])
            voters_no: list = json.loads(trial["voters_no"])
            trial_id: int = trial["trial_id"]
            try:
                guild: discord.Guild = bot.get_guild(trial["guild_id"])
                if guild:
                    language = bot.language(languages.FakeContext(guild, bot))
                    yes, neutral, no = len(voters_yes), len(voters_neutral), len(voters_no)
                    total = yes + neutral + no
                    score = yes - no
                    try:
                        upvotes = yes / (yes + no)
                    except ZeroDivisionError:
                        upvotes = 0
                    required = trial["required_score"]
                    if score >= required:
                        colour = general.green
                    elif score >= 0:
                        colour = general.red2
                    else:
                        colour = general.red
                    success = score >= required and upvotes >= 0.6  # The trial has reached a high enough score, therefore it succeeded
                    action: str = trial["type"]
                    user: discord.User = await bot.fetch_user(trial["user_id"])  # Load the overall user
                    member: discord.Member = guild.get_member(trial["user_id"])  # Load the Member for the functions that need it
                    channel: discord.TextChannel = guild.get_channel(trial["channel_id"])
                    output = "Error: Trial result next not defined"
                    if success:
                        reason_dm = f"Reason: {action.capitalize()} trial ({trial_id}) has succeeded - Score: {score:+}, {upvotes:.2%} voted yes"
                        trial_success_text = general.reason(guild.me, f"{action.capitalize()} trial {trial_id} has succeeded (Score: {score:+} - {upvotes:.2%} voted yes)")
                        if action in ["mute", "unmute"]:
                            if member:
                                _data = bot.db.fetchrow("SELECT * FROM settings WHERE gid=?", (guild.id,))
                                if not _data:
                                    general.print_error(f"{time.time()} > Trials > Trial {trial_id} > Guild settings not found")
                                else:
                                    data = json.loads(_data["data"])
                                    try:
                                        mute_role_id = data["mute_role"]
                                    except KeyError:
                                        general.print_error(f"{time.time()} > Trials > Trial {trial_id} > Guild has no mute role set")
                                    else:
                                        mute_role = guild.get_role(mute_role_id)
                                        if not mute_role:
                                            general.print_error(f"{time.time()} > Trials > Trial {trial_id} > Mute role not found")
                                        else:
                                            if action == "mute":
                                                await member.add_roles(mute_role, reason=trial_success_text)
                                                duration = trial["mute_length"]
                                                temp_mute_entry = bot.db.fetchrow("SELECT * FROM temporary WHERE uid=? AND gid=? AND bot=? AND type='mute'",
                                                                                  (member.id, guild.id, bot.name))
                                                if duration:
                                                    new_mute_end = time.now2() + timedelta(seconds=duration)
                                                    if temp_mute_entry:
                                                        bot.db.execute("UPDATE temporary SET expiry=? WHERE entry_id=?", (new_mute_end, temp_mute_entry["entry_id"]))
                                                    else:
                                                        random_id = general.random_id()
                                                        while bot.db.fetchrow("SELECT entry_id FROM temporary WHERE entry_id=?", (random_id,)):
                                                            random_id = general.random_id()
                                                        bot.db.execute("INSERT INTO temporary VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                                                       (member.id, "mute", new_mute_end, guild.id, None, random_id, 0, bot.name))
                                                    if channel:
                                                        _duration = language.delta_int(duration, accuracy=3, brief=False, affix=False)
                                                        output = language.string("trials_success_mute_timed", trial_id, user, _duration)
                                                        await general.send(output, channel)
                                                else:
                                                    if temp_mute_entry:
                                                        bot.db.execute("DELETE FROM temporary WHERE entry_id=?", (temp_mute_entry["entry_id"],))
                                                    if channel:
                                                        output = language.string("trials_success_mute", trial_id, user)
                                                        await general.send(output, channel)
                                                if guild.id == 869975256566210641:  # Nuriki's anarchy server
                                                    await member.remove_roles(guild.get_role(869975498799845406), reason=trial_success_text)  # Remove the Anarchists role
                                                    try:
                                                        if duration:
                                                            _duration2 = bot.language2("english").delta_int(duration, accuracy=3, brief=False, affix=False)
                                                            _output = f"You've been muted in {guild.name} for {_duration2}.\n{reason_dm}"
                                                        else:
                                                            _output = f"You've been muted in {guild.name}.\n{reason_dm}"
                                                        await user.send(_output)
                                                    except discord.Forbidden:
                                                        pass
                                            else:
                                                await member.remove_roles(mute_role, reason=trial_success_text)
                                                temp_mute_entry = bot.db.fetchrow("SELECT * FROM temporary WHERE uid=? AND gid=? AND bot=? AND type='mute'",
                                                                                  (member.id, guild.id, bot.name))
                                                if temp_mute_entry:
                                                    bot.db.execute("DELETE FROM temporary WHERE entry_id=?", (temp_mute_entry["entry_id"],))
                                                if guild.id == 869975256566210641:  # Nuriki's anarchy server
                                                    await member.add_roles(guild.get_role(869975498799845406), reason=trial_success_text)  # Give back the Anarchists role
                                                    try:
                                                        await user.send(f"You've been unmuted in {guild.name}.\n{reason_dm}")
                                                    except discord.Forbidden:
                                                        pass
                                                if channel:
                                                    output = language.string("trials_success_unmute", trial_id, user)
                                                    await general.send(output, channel)
                            else:
                                general.print_error(f"{time.time()} > {bot.full_name} > Trials > Trial {trial_id} > Member not found - can't mute")
                                if channel:
                                    string = "trials_error_member_none_mute" if action == "mute" else "trials_error_member_none_unmute"
                                    await general.send(language.string(string, trial_id), channel)
                        elif action == "kick":
                            if member:
                                try:
                                    await user.send(f"You have been kicked from {guild.name}.\n{reason_dm}")
                                except (discord.HTTPException, discord.Forbidden):
                                    pass
                                await member.kick(reason=trial_success_text)
                                if channel:
                                    output = language.string("trials_success_kick", trial_id, user)
                                    await general.send(output, channel)
                            else:
                                general.print_error(f"{time.time()} > {bot.full_name} > Trials > Trial {trial_id} > Member not found - can't kick")
                                if channel:
                                    await general.send(language.string("trials_error_member_none_kick", trial_id), channel)
                        elif action == "ban":
                            # I don't have to check if the user exists here, because otherwise it would raise a discord.NotFound while fetching
                            try:
                                await user.send(f"You have been banned from {guild.name}.\n{reason_dm}")
                            except (discord.HTTPException, discord.Forbidden):
                                pass
                            await guild.ban(user, reason=trial_success_text, delete_message_days=0)
                            if channel:
                                output = language.string("trials_success_ban", trial_id, user)
                                await general.send(output, channel)
                        elif action == "unban":
                            try:
                                await user.send(f"You have been unbanned from {guild.name}.\n{reason_dm}")
                            except (discord.HTTPException, discord.Forbidden):
                                pass
                            await guild.unban(user, reason=trial_success_text)
                            if channel:
                                output = language.string("trials_success_unban", trial_id, user)
                                await general.send(output, channel)
                        else:
                            general.print_error(f"{time.time()} > {bot.full_name} > Trials > Trial {trial_id} > Action type detection went wrong.")
                    else:  # The trial has failed, so restore the member's anarchist roles
                        if guild.id == 869975256566210641 and member:  # Nuriki's anarchy server
                            await member.remove_roles(guild.get_role(870338399922446336), reason="Trial has ended")  # Remove the On Trial role
                            await member.add_roles(guild.get_role(869975498799845406), reason="Trial has ended")  # Give the Anarchists role
                        if channel:
                            fail_text = {
                                "ban": "trials_failure_ban",
                                "kick": "trials_failure_kick",
                                "mute": "trials_failure_mute",
                                "unban": "trials_failure_unban",
                                "unmute": "trials_failure_unmute",
                            }.get(action)
                            output = language.string(fail_text, trial_id, user)
                            await general.send(output, channel)
                    if channel:
                        embed = discord.Embed(colour=colour)
                        embed.title = language.string("trials_end_title")
                        _expiry = language.time(trial["expiry"], short=1, dow=False, seconds=False, tz=False)
                        embed.description = language.string("trials_end_description", output, trial["reason"], _expiry)
                        embed.add_field(name=language.string("trials_votes_result"), inline=False,
                                        value=language.string("trials_votes_current2", language.number(yes), language.number(neutral), language.number(no),
                                                              language.number(total), language.number(score, positives=True),
                                                              language.number(upvotes, precision=2, percentage=True), language.number(required, positives=True)))
                        if not trial["anonymous"]:
                            _yes = "\n".join([f"<@{voter}>" for voter in voters_yes[:45]])
                            if yes >= 45:
                                _yes += language.string("polls_votes_many", language.number(yes - 45))
                            if not _yes:
                                _yes = language.string("polls_votes_none2")
                            embed.add_field(name=language.string("polls_votes_yes"), value=_yes, inline=True)
                            _neutral = "\n".join([f"<@{voter}>" for voter in voters_neutral[:45]])
                            if neutral >= 45:
                                _neutral += language.string("polls_votes_many", language.number(neutral - 45))
                            if not _neutral:
                                _neutral = language.string("polls_votes_none2")
                            embed.add_field(name=language.string("polls_votes_neutral"), value=_neutral, inline=True)
                            _no = "\n".join([f"<@{voter}>" for voter in voters_no[:45]])
                            if no >= 45:
                                _no += language.string("polls_votes_many", language.number(no - 45))
                            if not _no:
                                _no = language.string("polls_votes_none2")
                            embed.add_field(name=language.string("polls_votes_no"), value=_no, inline=True)
                        resend = True
                        try:
                            message: discord.Message = await channel.fetch_message(trial["message_id"])
                            if message.embeds:
                                # embed = message.embeds[0]
                                await message.edit(embed=embed)
                                resend = False
                        except discord.NotFound:
                            resend = True
                        if resend:
                            await general.send(None, channel, embed=embed)
                else:
                    general.print_error(f"{time.time()} > {bot.full_name} > Trials > Trial {trial_id} > Guild not found")
            except Exception as e:
                general.print_error(f"{time.time()} > {bot.full_name} > Trials > Trial {trial_id} error: {type(e).__name__}: {e}")
            bot.db.execute("DELETE FROM trials WHERE trial_id=?", (trial_id,))

        await asyncio.sleep(1)
