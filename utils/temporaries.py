import asyncio
import json
import random
from datetime import date, timedelta

import aiohttp
import discord
from regaus import conworlds

from cogs.mod import send_mod_dm, send_mod_log
from utils import bot_data, general, http, languages, lists, logger, time


async def handle_reminder(bot: bot_data.Bot, entry: dict, retry: bool = False):
    entry_id = entry["id"]
    handled = 2 if not retry else 1
    user: discord.User = bot.get_user(entry["uid"])
    if user is None:
        message = f"{time.time()} > {bot.full_name} > Reminders > Reminder ID {entry_id} - User ID {user} not found!"
        general.print_error(message)
        logger.log(bot.name, "reminders", message)
        logger.log(bot.name, "errors", message)
    else:
        try:
            await user.send(f"⏰ **Reminder**:\n\n{entry['message']}")
            expiry = bot.language2("english").time(entry["expiry"], short=1, dow=False, seconds=True, tz=False)
            logger.log(bot.name, "reminders", f"{time.time()} > {bot.full_name} > Reminders > Successfully sent {user} ({user.id}) the reminder for {expiry} ({entry_id})")
            handled = 1
        except Exception as e:
            message = f"{time.time()} > {bot.full_name} > Reminders > Reminder ID {entry_id} - Error: {type(e).__name__}: {e}"
            general.print_error(message)
            logger.log(bot.name, "reminders", message)
            logger.log(bot.name, "errors", message)
    bot.db.execute("UPDATE reminders SET handled=? WHERE id=?", (handled, entry_id))


async def reminders(bot: bot_data.Bot):
    """ Handle reminders """
    await bot.wait_until_ready()
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised Reminders Handler")
    while True:
        expired = bot.db.fetch("SELECT * FROM reminders WHERE DATETIME(expiry) < DATETIME('now') AND handled=0 AND bot=?", (bot.name,))
        bot.db.execute("DELETE FROM reminders WHERE handled=1", ())  # We don't need to keep reminders after they expire and are dealt with
        if expired:
            for entry in expired:
                await handle_reminder(bot, entry, False)
        await asyncio.sleep(1)


async def reminders_errors(bot: bot_data.Bot):
    """ Try to send the reminder again... if it doesn't work, ignore it anyways """
    await bot.wait_until_ready()
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised Reminders Errors Handler")

    while True:
        # If it's errored out, it must've expired already...
        expired = bot.db.fetch("SELECT * FROM reminders WHERE handled=2 AND bot=?", (bot.name,))
        if expired:
            for entry in expired:
                await handle_reminder(bot, entry, True)
        await asyncio.sleep(3600)


async def handle_punishment(bot: bot_data.Bot, entry: dict, retry: bool = False):
    def save_handle(_handled: int, _entry_id: int):
        bot.db.execute("UPDATE punishments SET handled=? WHERE id=?", (_handled, _entry_id))

    def send_error(message: str, _entry_id: int):
        general.print_error(message)
        logger.log(bot.name, "moderation", message)
        logger.log(bot.name, "errors", message)
        save_handle(2 if not retry else 1, _entry_id)  # If it errors out the second time, just ignore it as "handled" anyways...

    entry_id = entry["id"]
    # handled = 2
    if entry["action"] == "warn":
        save_handle(1, entry_id)
        return
    elif entry["action"] != "mute":
        # Only warns and mutes can possibly be temporary... If it's something else, something went wrong
        _message = f"{time.time()} > {bot.full_name} > Punishments > Weird action type {entry['action']} expired..."
        general.print_error(_message)
        logger.log(bot.name, "moderation", _message)
        logger.log(bot.name, "errors", _message)
        save_handle(1, entry_id)
        return
    guild: discord.Guild = bot.get_guild(entry["gid"])
    if guild is None:
        send_error(f"{time.time()} > {bot.full_name} > Punishments > Mute entry ID {entry_id} - Guild not found!", entry_id)
        return
    _data = bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (guild.id, bot.name))
    if not _data:
        send_error(f"{time.time()} > {bot.full_name} > Punishments > Mute entry ID {entry_id} - Settings not found!", entry_id)
        return
    data = json.loads(_data["data"])
    try:
        mute_role_id = data["mute_role"]
    except KeyError:
        send_error(f"{time.time()} > {bot.full_name} > Punishments > Mute entry ID {entry_id} - No mute role set!", entry_id)
        return
    mute_role = guild.get_role(mute_role_id)
    if not mute_role:
        send_error(f"{time.time()} > {bot.full_name} > Punishments > Mute entry ID {entry_id} - Mute role not found!", entry_id)
        return
    member: discord.Member = guild.get_member(entry["uid"])
    if not member:
        send_error(f"{time.time()} > {bot.full_name} > Punishments > Mute entry ID {entry_id} - Member not found! Have they left?", entry_id)
        return
    try:
        await member.remove_roles(mute_role, reason="[Auto-Unmute] Punishment expired")
        if guild.id == 869975256566210641:  # Nuriki's anarchy server
            try:
                role = guild.get_role(869975498799845406)
                if role is not None:
                    await member.add_roles(role, reason="Punishment expired")  # Give back the Anarchists role
            except (discord.Forbidden, discord.NotFound):
                pass
    except Exception as e:
        send_error(f"{time.time()} > {bot.full_name} > Punishments > Mute entry ID {entry_id} - Error: {type(e).__name__}: {e}", entry_id)
        return
    logger.log(bot.name, "moderation", f"{time.time()} > {bot.full_name} > Punishments > Successfully unmuted the user {member} ({member.id}) from guild {guild} ({entry_id})")
    save_handle(1, entry_id)
    await send_mod_dm(bot, languages.FakeContext(guild, bot), member, "unmute", "[Auto-Unmute] Punishment expired", None, True)
    await send_mod_log(bot, languages.FakeContext(guild, bot), member, bot.user, entry_id, "unmute", "[Auto-Unmute] Punishment expired", None)
    # bot.db.execute("UPDATE punishments SET handled=? WHERE id=?", (handled, entry_id))


async def punishments(bot: bot_data.Bot):
    """ Handle temporary mutes and stuff """
    await bot.wait_until_ready()
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised Punishments Handler")

    while True:
        expired = bot.db.fetch("SELECT * FROM punishments WHERE temp=1 AND DATETIME(expiry) < DATETIME('now') AND handled=0 AND bot=?", (bot.name,))
        if expired:
            for entry in expired:
                await handle_punishment(bot, entry, False)
        await asyncio.sleep(1)


async def punishments_errors(bot: bot_data.Bot):
    await bot.wait_until_ready()
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised Punishments Errors Handler")

    while True:
        # If it's errored out, it must've expired already...
        expired = bot.db.fetch("SELECT * FROM punishments WHERE temp=1 AND handled=2 AND bot=?", (bot.name,))
        if expired:
            for entry in expired:
                await handle_punishment(bot, entry, True)
        await asyncio.sleep(3600)


async def birthdays(bot: bot_data.Bot):
    """ Handle birthdays """
    await bot.wait_until_ready()

    now = time.now(None)
    then = (now + timedelta(hours=1)).replace(minute=0, second=1, microsecond=0)  # Start at xx:00:01 to avoid starting at 59:59 and breaking everything
    await asyncio.sleep((then - now).total_seconds())
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised Birthdays")

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
                                    out = f"{time.time()} > {bot.full_name} > Birthdays Handler > Failed sending birthday message (Guild {gid}, User {user.id}): {e}"
                                    general.print_error(out)
                                    logger.log(bot.name, "errors", out)
                            if data[0]:
                                role: discord.Role = guild.get_role(data[0])
                                try:
                                    await user.add_roles(role, reason=f"[Birthdays] It is {user}'s birthday")
                                    print(f"{time.time()} > {bot.full_name} > {guild.name} > Gave {user} the birthday role")
                                except Exception as e:
                                    out = f"{time.time()} > {bot.full_name} > Birthdays Handler > Failed giving birthday role (Guild {gid}, User {user.id}): {e}"
                                    general.print_error(out)
                                    logger.log(bot.name, "errors", out)
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
                                out = f"{time.time()} > {bot.full_name} > Birthdays Handler > Failed taking away birthday role (Guild {gid}, User {user.id}): {e}"
                                general.print_error(out)
                                logger.log(bot.name, "errors", out)
                # except Exception as e:
                #     general.print_error(f"{time.time()} > {bot.full_name} > Birthdays Handler > {e}")

        await asyncio.sleep(3600)


ka_places = {
    "Regaazdall": {
        "Regavall": {"en": None, "weight": 5},
        "Reggar":   {"en": None, "weight": 5},
        "Suvagar":  {"en": None, "weight": 3},
    },
    "Nehtivia": {
        "Ekspigar":    {"en": None, "weight": 3},
        "Leitagar":    {"en": None, "weight": 3},
        "Orlagar":     {"en": None, "weight": 3},
        "Pakigar":     {"en": None, "weight": 3},
        "Runnegar":    {"en": None, "weight": 2},
        "Shonangar":   {"en": None, "weight": 3},
        "Steirigar":   {"en": None, "weight": 3},
        "Sunmagar":    {"en": None, "weight": 2},
        "Tenmagar":    {"en": None, "weight": 2},
        "Peaskar":     {"en": None, "weight": 2},
        "Sulingar":    {"en": None, "weight": 3},
        "Alyksandris": {"en": None, "weight": 3},
        "Läkingar":    {"en": None, "weight": 2},
        "Leogar":      {"en": None, "weight": 3},
        "Menenvallus": {"en": None, "weight": 2},
        "Tevivall":    {"en": None, "weight": 2},
        "Kamikava":    {"en": None, "weight": 3},
        "Kiomigar":    {"en": None, "weight": 3},
        "Lailagar":    {"en": None, "weight": 3},
    },
    "Nittavia": {
        "Erdagar":  {"en": None, "weight": 2},
        "Nuktagar": {"en": None, "weight": 2},
    },
    "Tebaria": {
        "Sentatebaria": {"en": None, "weight": 3},
        "Kaivalgard":   {"en": None, "weight": 3},
        "Harvugar":     {"en": None, "weight": 2},
        "Vallangar":    {"en": None, "weight": 2},
        "Bylkangar":    {"en": None, "weight": 3},
        "Sadegar":      {"en": None, "weight": 2},
        "Vadertebaria": {"en": None, "weight": 2},
        "Istagar":      {"en": None, "weight": 2},
        "Lervagar":     {"en": None, "weight": 2},
    },
    "Kaltar Azdall": {
        "Kaltar Kainead": {"en": None, "weight": 1},
        "Kaltarena":      {"en": None, "weight": 2},
        "Küangar":        {"en": None, "weight": 2},
    },
    "Arnattia": {
        "Vainararna": {"en": None, "weight": 2},
        "Avikarna":   {"en": None, "weight": 2},
        "Kanerarna":  {"en": None, "weight": 2},
        "Terra Arna": {"en": None, "weight": 2},
    },
    "Erellia": {
        "Raagar": {"en": None, "weight": 2},
    },
    "Centeria": {
        "Kalagar": {"en": None, "weight": 2},
        "Virsetgar": {"en": None, "weight": 2},
    },
    "Verlennia": {
    },
    "Inhattia": {
    },
    "Other Areas": {
        "Vintelingar":    {"en": None, "weight": 3},
        "Kanerakainedus": {"en": None, "weight": 1},
    }
}
_places = {}  # Since the playing status won't be able to read through a 2-layer dict...
# ka-time will read the data from ka_places, to show the data with layers
# Playing will read the data from _places, to show as a simple dict
# _places will also store the Place instances, so that it wouldn't be necessary to keep calling new ones...

# The ka_time uses Reggar for now, I will either keep it so or change it once Virsetgar is actually added to the places list
ka_time: ...  # Current time in Virsetgar, used to determine time until next holiday
update_speed_play = 120  # 150
update_speed_data = 60
update_speed_time = 300
update_speed_avatar = 3600
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


async def wait_until_next_iter(update_speed: int = 120, adjustment: int = 0):
    now = time.now(None)
    then = time.from_ts(((time.get_ts(now) // update_speed) + 1) * update_speed + adjustment, None)
    await asyncio.sleep((then - now).total_seconds())


async def ka_data_updater(bot: bot_data.Bot):
    """ Update time and weather data for Kargadian cities """
    await bot.wait_until_ready()
    # Start this script ahead of the updates to make sure the city time updater and the playing status get accurate data
    await wait_until_next_iter(update_speed_data, -1)
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised City Data Updater")

    while True:
        for area_name, area in ka_places.items():
            for city, _data in area.items():
                try:
                    if city not in _places.keys():
                        place: conworlds.Place = conworlds.Place(city)
                        _places[city] = {"place": place, "text": None, "weight": _data["weight"]}
                    else:
                        # It seems this actually does what I want it to, and simply keeps updating the instance, not needing to do any rewriting into the dict
                        place: conworlds.Place = _places[city]["place"]
                        place.update_time()
                    tebarian = place.time.strftime("%d %b %Y, %H:%M", "ka_tb")
                    english = place.time.strftime("%d %B %Y, %H:%M", "en")  # Note to future self: Consider shortening to %b (eg 14 Kar 2151) to save space
                    if place.weather is not None:
                        temp = f"{place.weather['temperature']:.0f}°C"
                        rain = place.weather['rain']
                        if rain == "sunny":
                            rain += "2" if place.sun is not None and place.sun.elevation < 0 else "1"
                        weather_en = languages.Language("en").data("weather78")[rain]
                        weather_tb = languages.Language("ka_tb").data("weather78")[rain]
                        english += f" | {temp} | {weather_en}"
                        tebarian += f" | {temp} | {weather_tb}"
                    # ka_cities[city] = {"english": english, "tebarian": tebarian, "weight": ka_cities[city]["weight"]}
                    ka_places[area_name][city]["en"] = english
                    _places[city]["text"] = tebarian
                    if city == "Reggar":
                        global ka_time
                        ka_time = place.time
                    # logger.log(bot.name, "kargadia", f"{time.time()} > {bot.full_name} > Updated data for {city}")
                except Exception as e:
                    general.print_error(f"{time.time()} > {bot.full_name} > City Data Updater > {type(e).__name__}: {e}")
                    log_out = f"{time.time()} > {bot.full_name} > Error updating data for {city} - {type(e).__name__}: {e}"
                    logger.log(bot.name, "kargadia", log_out)
                    logger.log(bot.name, "errors", log_out)
        logger.log(bot.name, "kargadia", f"{time.time()} > {bot.full_name} > Updated Kargadian cities data")

        # This should make it adjust itself for lag caused
        await asyncio.sleep(2)  # Hopefully prevents it from lagging ahead of itself and hanging
        await wait_until_next_iter(update_speed_data, -1)
        # await asyncio.sleep(update_speed)


async def ka_time_updater(bot: bot_data.Bot):
    """ Update the time and weather info for Kargadian cities in Regaus'tar Koankadu """
    await bot.wait_until_ready()
    await wait_until_next_iter(update_speed_time, 0)
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised RK City Time Updater")
    channel = bot.get_channel(935982691801780224)  # ka-time | Old channel: 887087307918802964

    async def update_message(name: str, content: str):
        try:
            # message: discord.Message = (await channel.history(limit=1, oldest_first=True).flatten())[0]
            message = None
            async for msg in channel.history(limit=None, oldest_first=True):
                if msg.author.id == bot.user.id and msg.content.startswith(name):
                    message = msg
                    break
            if message is None:
                raise general.RegausError("City time message not found")
            await message.edit(content=content)
        except (IndexError, discord.NotFound, general.RegausError):
            await channel.send(content)
            logger.log(bot.name, "kargadia", f"{time.time()} > {bot.full_name} > Reset Kargadian cities times message for {name}")
        except Exception as e:
            out = f"{time.time()} > {bot.full_name} > City Time Updater > {type(e).__name__}: {e}"
            general.print_error(out)
            logger.log(bot.name, "kargadia", out)
            logger.log(bot.name, "errors", out)

    while True:
        for area_name, area in ka_places.items():
            data = [f"{area_name}:"]
            for city, _data in area.items():
                data.append(f"`{city:<14} - {_data['en']}`")
            await update_message(area_name, "\n".join(data))
        logger.log(bot.name, "kargadia", f"{time.time()} > {bot.full_name} > Updated Kargadian cities times messages")
        # out = "\n\n".join(data)

        # This should make it adjust itself for lag caused
        await asyncio.sleep(1)  # Hopefully prevents it from lagging ahead of itself
        await wait_until_next_iter(update_speed_time, 0)
        # await asyncio.sleep(update_speed)


async def playing(bot: bot_data.Bot):
    await bot.wait_until_ready()
    await wait_until_next_iter(update_speed_play, 0)
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised Playing updater")

    def error(text: str):
        general.print_error(text)
        logger.log(bot.name, "errors", text)

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
                    status_cobble = f"🎉 Esea jat mun reidesea!" if is_cobble else f"{until(cobble, True)} mun reideseat an Zymlä'n"
                    status_regaus = f"🎉 Esea jat Regaus'ta reidesea!" if is_regaus else f"{until(regaus, True)} Regaus'tat reideseat an Zymlä'n"
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
                        # {"type": 0, "name": "na Temval na Bylkain'den Liidenvirkalten"},
                        # {"type": 0, "name": "na TBL'n"},
                        # {"type": 0, "name": "Akos'an"},
                        # {"type": 0, "name": "na Tadevan Kunneanpaitenan"},
                        # {"type": 0, "name": "na TKP'n"},
                        {"type": 0, "name": "vaihaga kiinanshavarkan"},
                        # {"type": 0, "name": "Vainar veikidat pahtemar, discord.py"},
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
                        status = f"Kovanan {holiday[0]}!"
                    elif days_left == 1:
                        status = f"1 sea astallat {holiday[1]} an Kargadian"
                    else:
                        status = f"{days_left} seain astallan {holiday[1]} an Kargadian"
                    activity = discord.Game(name=status)
                    logger.log(bot.name, "playing", f"{time.time()} > {bot.full_name} > Updated activity to {status} (Status Type 3)")
                else:  # status_type == 4
                    # Original weights list: [2, 2, 2, 3, 3, 2, 2, 2, 2, 2, 2, 2, 5, 5, 2, 3, 2, 2, 3, 2, 2]
                    data, weights = [], []
                    for city in _places.items():
                        data.append(city)
                        weights.append(city[1]["weight"])
                    # city, city_data = random.choices(list(ka_cities.items()), [v["weight"] for v in ka_cities.values()])[0]
                    city, city_data = random.choices(data, weights)[0]
                    status = f"{city}: {city_data['text']}"
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
                        # {"type": 1, "name": "Русские Вперёд!", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
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
                        # {"type": 0, "name": "sentience"},
                        # {"type": 0, "name": "RIP discord.py"},
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
            _status = discord.Status.online if bot.name == "kyomi" else discord.Status.dnd
            await bot.change_presence(activity=activity, status=_status)
        except PermissionError:
            error(f"{time.time()} > {bot.full_name} > Playing Changer > Failed to save changes.")
        except aiohttp.ClientConnectorError:
            error(f"{time.time()} > {bot.full_name} > Playing Changer > The bot tried to do something while disconnected.")
        except Exception as e:
            error(f"{time.time()} > {bot.full_name} > Playing Changer > {type(e).__name__}: {e}")

        # This should make it adjust itself for lag caused
        await asyncio.sleep(1)  # Hopefully prevents it from lagging ahead of itself
        await wait_until_next_iter(update_speed_play, 0)


async def avatars(bot: bot_data.Bot):
    await bot.wait_until_ready()

    # now = time.now(None)
    # then = (now + timedelta(hours=1)).replace(minute=0, second=1, microsecond=0)
    # await asyncio.sleep((then - now).total_seconds())
    await wait_until_next_iter(update_speed_avatar, 1)
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised Avatar updater")

    def error(text: str):
        general.print_error(text)
        logger.log(bot.name, "errors", text)

    while True:
        try:
            # bot.config = general.get_config()
            # bot.local_config = bot.config["bots"][bot.index]
            # log = bot.local_config["logs"]
            # avatars = lists.avatars
            avatar = random.choice(lists.avatars)
            e = False
            s1, s2 = [f"{time.time()} > {bot.full_name} > Avatar updated", f"{time.time()} > {bot.name} > Failed to change avatar due to an error"]
            try:
                bio = await http.get(avatar, res_method="read")
                await bot.user.edit(avatar=bio)
            except discord.errors.HTTPException:
                e = True
            send = s2 if e else s1
            logger.log(bot.name, "avatar", send)
        except PermissionError:
            error(f"{time.time()} > {bot.full_name} > Avatar Changer > Failed to save changes.")
        except aiohttp.ClientConnectorError:
            error(f"{time.time()} > {bot.full_name} > Avatar Changer > The bot tried to do something while disconnected.")
        except Exception as e:
            error(f"{time.time()} > {bot.full_name} > Avatar Changer > {type(e).__name__}: {e}")

        await asyncio.sleep(1)
        await wait_until_next_iter(update_speed_avatar, 1)


async def polls(bot: bot_data.Bot):
    await bot.wait_until_ready()

    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised Polls")
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
                out = f"{time.time()} > {bot.full_name} > Polls > Poll {poll['poll_id']} error: {type(e).__name__}: {e}"
                general.print_error(out)
                logger.log(bot.name, "errors", out)
            bot.db.execute("DELETE FROM polls WHERE poll_id=?", (poll["poll_id"],))

        await asyncio.sleep(1)


async def trials(bot: bot_data.Bot):
    await bot.wait_until_ready()

    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised Trials")
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
                    if upvotes >= 0.6 and total >= required:
                        colour = general.green
                    elif score >= 0:
                        colour = general.red2
                    else:
                        colour = general.red
                    success = total >= required and upvotes >= 0.6  # The trial has reached a high enough vote count and at least 60% upvoted
                    action: str = trial["type"]
                    user: discord.User = await bot.fetch_user(trial["user_id"])  # Load the overall user
                    member: discord.Member = guild.get_member(trial["user_id"])  # Load the Member for the functions that need it
                    channel: discord.TextChannel = guild.get_channel(trial["channel_id"])
                    output = "Error: Trial result next not defined"
                    if success:
                        # reason_dm = f"Reason: {action.capitalize()} trial ({trial_id}) has succeeded - Score: {score:+}, {upvotes:.2%} voted yes"
                        trial_success_text = general.reason(guild.me, f"{action.capitalize()} trial {trial_id} has succeeded (Score: {score:+} - {upvotes:.2%} voted yes)")
                        duration_text = None
                        if action in ["mute", "unmute"]:
                            if member:
                                _data = bot.db.fetchrow("SELECT * FROM settings WHERE gid=?", (guild.id,))
                                if not _data:
                                    out = f"{time.time()} > Trials > Trial {trial_id} > Guild settings not found"
                                    general.print_error(out)
                                    logger.log(bot.name, "errors", out)
                                else:
                                    data = json.loads(_data["data"])
                                    try:
                                        mute_role_id = data["mute_role"]
                                    except KeyError:
                                        out = f"{time.time()} > Trials > Trial {trial_id} > Guild has no mute role set"
                                        general.print_error(out)
                                        logger.log(bot.name, "errors", out)
                                    else:
                                        mute_role = guild.get_role(mute_role_id)
                                        if not mute_role:
                                            out = f"{time.time()} > Trials > Trial {trial_id} > Mute role not found"
                                            general.print_error(out)
                                            logger.log(bot.name, "errors", out)
                                        else:
                                            if action == "mute":
                                                await member.add_roles(mute_role, reason=trial_success_text)
                                                duration = trial["mute_length"]
                                                # temp_mute_entry = bot.db.fetchrow("SELECT * FROM temporary WHERE uid=? AND gid=? AND bot=? AND type='mute'",
                                                #                                   (member.id, guild.id, bot.name))
                                                bot.db.execute("UPDATE punishments SET handled=5 WHERE uid=? AND gid=? AND action='mute' AND handled=0 AND bot=?",
                                                               (member.id, guild.id, bot.name))
                                                if duration:
                                                    new_mute_end = time.now2() + timedelta(seconds=duration)
                                                    # if temp_mute_entry:
                                                    #     bot.db.execute("UPDATE temporary SET expiry=? WHERE entry_id=?", (new_mute_end, temp_mute_entry["entry_id"]))
                                                    # else:
                                                    #     random_id = general.random_id()
                                                    #     while bot.db.fetchrow("SELECT entry_id FROM temporary WHERE entry_id=?", (random_id,)):
                                                    #         random_id = general.random_id()
                                                    #     bot.db.execute("INSERT INTO temporary VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                                    #                    (member.id, "mute", new_mute_end, guild.id, None, random_id, 0, bot.name))
                                                    if channel:
                                                        _duration = language.delta_int(duration, accuracy=3, brief=False, affix=False)
                                                        output = language.string("trials_success_mute_timed", trial_id, user, _duration)
                                                        await general.send(output, channel)

                                                    bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                                                   (member.id, guild.id, "mute", trial["author_id"], trial_success_text, True, new_mute_end, 0, bot.name))
                                                else:
                                                    # if temp_mute_entry:
                                                    #     bot.db.execute("DELETE FROM temporary WHERE entry_id=?", (temp_mute_entry["entry_id"],))
                                                    if channel:
                                                        output = language.string("trials_success_mute", trial_id, user)
                                                        await general.send(output, channel)

                                                    bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                                                   (member.id, guild.id, "mute", trial["author_id"], trial_success_text, False, time.now2(), 0, bot.name))
                                                if guild.id == 869975256566210641:  # Nuriki's anarchy server
                                                    try:
                                                        await member.remove_roles(guild.get_role(869975498799845406), reason=trial_success_text)  # Remove the Anarchists role
                                                    except AttributeError:
                                                        out = f"{time.time()} > {bot.full_name} > Trials > Trial {trial_id} > Trial or Anarchist role not found..."
                                                        general.print_error(out)
                                                        logger.log(bot.name, "errors", out)
                                                if duration:
                                                    duration_text = bot.language2("english").delta_int(duration, accuracy=3, brief=False, affix=False)
                                                    # try:
                                                    #     if duration:
                                                    #         _duration2 = bot.language2("english").delta_int(duration, accuracy=3, brief=False, affix=False)
                                                    #         _output = f"You've been muted in {guild.name} for {_duration2}.\n{reason_dm}"
                                                    #     else:
                                                    #         _output = f"You've been muted in {guild.name}.\n{reason_dm}"
                                                    #     await user.send(_output)
                                                    # except discord.Forbidden:
                                                    #     pass
                                            else:
                                                await member.remove_roles(mute_role, reason=trial_success_text)
                                                # temp_mute_entry = bot.db.fetchrow("SELECT * FROM temporary WHERE uid=? AND gid=? AND bot=? AND type='mute'",
                                                #                                   (member.id, guild.id, bot.name))
                                                # if temp_mute_entry:
                                                #     bot.db.execute("DELETE FROM temporary WHERE entry_id=?", (temp_mute_entry["entry_id"],))
                                                bot.db.execute("UPDATE punishments SET handled=5 WHERE uid=? AND gid=? AND action='mute' AND handled=0 AND bot=?",
                                                               (member.id, guild.id, bot.name))
                                                bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                                               (member.id, guild.id, "unmute", trial["author_id"], trial_success_text, False, time.now2(), 1, bot.name))
                                                if guild.id == 869975256566210641:  # Nuriki's anarchy server
                                                    try:
                                                        await member.add_roles(guild.get_role(869975498799845406), reason=trial_success_text)  # Give back the Anarchists role
                                                    except AttributeError:
                                                        out = f"{time.time()} > {bot.full_name} > Trials > Trial {trial_id} > Trial or Anarchist role not found..."
                                                        general.print_error(out)
                                                        logger.log(bot.name, "errors", out)
                                                    # try:
                                                    #     await user.send(f"You've been unmuted in {guild.name}.\n{reason_dm}")
                                                    # except discord.Forbidden:
                                                    #     pass
                                                if channel:
                                                    output = language.string("trials_success_unmute", trial_id, user)
                                                    await general.send(output, channel)
                            else:
                                out = f"{time.time()} > {bot.full_name} > Trials > Trial {trial_id} > Member not found - can't mute"
                                general.print_error(out)
                                logger.log(bot.name, "errors", out)
                                if channel:
                                    string = "trials_error_member_none_mute" if action == "mute" else "trials_error_member_none_unmute"
                                    await general.send(language.string(string, trial_id), channel)
                        elif action == "kick":
                            if member:
                                # try:
                                #     await user.send(f"You have been kicked from {guild.name}.\n{reason_dm}")
                                # except (discord.HTTPException, discord.Forbidden):
                                #     pass
                                await member.kick(reason=trial_success_text)
                                if channel:
                                    output = language.string("trials_success_kick", trial_id, user)
                                    await general.send(output, channel)
                            else:
                                out = f"{time.time()} > {bot.full_name} > Trials > Trial {trial_id} > Member not found - can't kick"
                                general.print_error(out)
                                logger.log(bot.name, "errors", out)
                                if channel:
                                    await general.send(language.string("trials_error_member_none_kick", trial_id), channel)
                        elif action == "ban":
                            # I don't have to check if the user exists here, because otherwise it would raise a discord.NotFound while fetching
                            # try:
                            #     await user.send(f"You have been banned from {guild.name}.\n{reason_dm}")
                            # except (discord.HTTPException, discord.Forbidden):
                            #     pass
                            await guild.ban(user, reason=trial_success_text, delete_message_days=0)
                            if channel:
                                output = language.string("trials_success_ban", trial_id, user)
                                await general.send(output, channel)
                        elif action == "unban":
                            # try:
                            #     await user.send(f"You have been unbanned from {guild.name}.\n{reason_dm}")
                            # except (discord.HTTPException, discord.Forbidden):
                            #     pass
                            await guild.unban(user, reason=trial_success_text)
                            if channel:
                                output = language.string("trials_success_unban", trial_id, user)
                                await general.send(output, channel)
                        else:
                            out = f"{time.time()} > {bot.full_name} > Trials > Trial {trial_id} > Action type detection went wrong."
                            general.print_error(out)
                            logger.log(bot.name, "errors", out)
                        await send_mod_dm(bot, languages.FakeContext(guild, bot), member, action, f"Trial results (Score: {score:+}, {upvotes:.2%} voted yes)", duration_text)
                    else:  # The trial has failed, so restore the member's anarchist roles
                        if guild.id == 869975256566210641 and member:  # Nuriki's anarchy server
                            try:
                                await member.remove_roles(guild.get_role(870338399922446336), reason="Trial has ended")  # Remove the On Trial role
                                await member.add_roles(guild.get_role(869975498799845406), reason="Trial has ended")  # Give the Anarchists role
                            except AttributeError:
                                out = f"{time.time()} > {bot.full_name} > Trials > Trial {trial_id} > Trial or Anarchist role not found..."
                                general.print_error(out)
                                logger.log(bot.name, "errors", out)
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
                    out = f"{time.time()} > {bot.full_name} > Trials > Trial {trial_id} > Guild not found"
                    general.print_error(out)
                    logger.log(bot.name, "errors", out)
            except Exception as e:
                out = f"{time.time()} > {bot.full_name} > Trials > Trial {trial_id} error: {type(e).__name__}: {e}"
                general.print_error(out)
                logger.log(bot.name, "errors", out)
            bot.db.execute("DELETE FROM trials WHERE trial_id=?", (trial_id,))

        await asyncio.sleep(1)


async def new_year(bot: bot_data.Bot):
    await bot.wait_until_ready()

    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised 2022 New Year Script")
    ny = time.dt(2022)
    now = time.now()
    if now > ny:
        logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > New Year script > It is already 2022...")
        return

    channel = bot.get_channel(572857995852251169)  # 742885168997466196 Secretive-commands | Announcements channel: 572857995852251169
    delay = ny - now
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > New Year script > Waiting {delay} until midnight...")
    await asyncio.sleep(delay.total_seconds())
    await general.send("It is now 2022. Congrats, you have all survived yet another year. Now it's time to see what kind of shitshow this year will bring...", channel)
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > New Year script > Sent the New Year message. Exiting.")
    return
