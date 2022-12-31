from __future__ import annotations

import asyncio
import json
import random
import re
from typing import Type

import aiohttp
import discord
import pytz
from regaus import conworlds, RegausError, time as time2

from cogs.mod import send_mod_dm, send_mod_log
from utils import birthday, bot_data, commands, general, http, lists, logger, time


async def wait_until_next_iter(update_speed: int = 120, adjustment: int = 0, time_class: Type[time2.Earth] = time2.Earth):
    now = time2.datetime.now(time_class=time_class)
    then = time2.datetime.from_timestamp(((now.timestamp // update_speed) + 1) * update_speed + adjustment, time2.timezone.utc, time_class)
    await asyncio.sleep((then.to_earth_time() - now.to_earth_time()).total_seconds())


def can_send(channel: discord.TextChannel | discord.DMChannel | discord.Thread):
    return isinstance(channel, discord.DMChannel) or channel.permissions_for(channel.guild.me).send_messages


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
            expiry = bot.language2("english").time(entry["expiry"], short=1, dow=False, seconds=True, tz=True, uid=user.id)
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
        try:
            expired = bot.db.fetch("SELECT * FROM reminders WHERE DATETIME(expiry) < DATETIME('now') AND handled=0 AND bot=?", (bot.name,))
            bot.db.execute("DELETE FROM reminders WHERE handled=1", ())  # We don't need to keep reminders after they expire and are dealt with
            if expired:
                for entry in expired:
                    await handle_reminder(bot, entry, False)
            await asyncio.sleep(1)
        except (aiohttp.ClientConnectorError, ConnectionError):
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Reminders > Error with connection.")
        except Exception as e:
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Reminders > {type(e).__name__}: {e}")
            general.log_error(bot, general.traceback_maker(e).strip("```")[3:-1])  # Remove the codeblock markdown and extra newlines


async def reminders_errors(bot: bot_data.Bot):
    """ Try to send the reminder again... if it doesn't work, ignore it anyways """
    update_speed = 3600
    await wait_until_next_iter(update_speed, 0)  # This only needs to run once an hour
    await bot.wait_until_ready()
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised Reminders Errors Handler")

    while True:
        try:
            # If it's errored out, it must've expired already...
            expired = bot.db.fetch("SELECT * FROM reminders WHERE handled=2 AND bot=?", (bot.name,))
            if expired:
                for entry in expired:
                    await handle_reminder(bot, entry, True)
            await asyncio.sleep(1)
            await wait_until_next_iter(update_speed, 0)
        except (aiohttp.ClientConnectorError, ConnectionError):
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Reminders Errors > Error with connection.")
        except Exception as e:
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Reminders Errors > {type(e).__name__}: {e}")
            general.log_error(bot, general.traceback_maker(e).strip("```")[3:-1])  # Remove the codeblock markdown and extra newlines


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
    fake_ctx = commands.FakeContext(guild, bot)
    language = bot.language(fake_ctx)
    reason = language.string("mod_unmute_auto_reason")
    await send_mod_dm(bot, fake_ctx, member, "unmute", reason, None, True)
    await send_mod_log(bot, fake_ctx, member, bot.user, entry_id, "unmute", reason, None)
    # bot.db.execute("UPDATE punishments SET handled=? WHERE id=?", (handled, entry_id))


async def punishments(bot: bot_data.Bot):
    """ Handle temporary mutes and stuff """
    await bot.wait_until_ready()
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised Punishments Handler")

    while True:
        try:
            expired = bot.db.fetch("SELECT * FROM punishments WHERE temp=1 AND DATETIME(expiry) < DATETIME('now') AND handled=0 AND bot=?", (bot.name,))
            if expired:
                for entry in expired:
                    await handle_punishment(bot, entry, False)
            await asyncio.sleep(1)
        except (aiohttp.ClientConnectorError, ConnectionError):
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Punishments > Error with connection.")
        except Exception as e:
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Punishments > {type(e).__name__}: {e}")
            general.log_error(bot, general.traceback_maker(e).strip("```")[3:-1])  # Remove the codeblock markdown and extra newlines


async def punishments_errors(bot: bot_data.Bot):
    update_speed = 3600
    await wait_until_next_iter(update_speed, 0)  # This only needs to run once an hour
    await bot.wait_until_ready()
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised Punishments Errors Handler")

    while True:
        try:
            # If it's errored out, it must've expired already...
            expired = bot.db.fetch("SELECT * FROM punishments WHERE temp=1 AND handled=2 AND bot=?", (bot.name,))
            if expired:
                for entry in expired:
                    await handle_punishment(bot, entry, True)
            await asyncio.sleep(1)
            await wait_until_next_iter(update_speed, 0)
        except (aiohttp.ClientConnectorError, ConnectionError):
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Punishments Errors > Error with connection.")
        except Exception as e:
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Punishments Errors > {type(e).__name__}: {e}")
            general.log_error(bot, general.traceback_maker(e).strip("```")[3:-1])  # Remove the codeblock markdown and extra newlines


def process_birthday(bot: bot_data.Bot, entry: dict) -> birthday.Birthday:
    uid = entry["uid"]
    if bot.name == "cobble":
        date = time2.date.from_iso(entry["birthday"], time2.Kargadia)
        try:
            tz = conworlds.Place(entry["location"]).tz
        except (ValueError, AttributeError, KeyError):  # Place does not exist or is not specified (null -> AttError)
            tz = time2.KargadianTimezone(time2.timedelta(), "Virsetgar", "VSG")  # Since they have Virsetgar instead of UTC
    else:
        date = time2.date.from_datetime(entry["birthday"])  # although the birthday is stored as a datetime, the converter only takes in the date part
        tz_entry = bot.db.fetchrow("SELECT * FROM timezones WHERE uid=?", (uid,))
        if tz_entry:
            tz = pytz.timezone(tz_entry["tz"])
        else:
            tz = time2.timezone.utc
    return birthday.Birthday(uid, date, tz, bot.name, entry["has_role"])


def prep_birthdays(bot: bot_data.Bot):
    # Load all birthdays
    if bot.name == "cobble":
        all_birthdays = bot.db.fetch("SELECT uid, birthday, has_role, location FROM kargadia WHERE birthday IS NOT NULL")
    else:
        all_birthdays = bot.db.fetch("SELECT * FROM birthdays WHERE bot=?", (bot.name,))

    # Check if the bot has not yet saved its birthdays into the class system
    if bot.name not in birthday.birthdays:
        data = {}
        for entry in all_birthdays:
            uid = entry["uid"]
            data[uid] = process_birthday(bot, entry)
        birthday.birthdays[bot.name] = data
    # If the birthdays are present, check the validity of the data
    else:
        data = birthday.birthdays[bot.name]
        mentioned = []  # If someone's entry is removed from the databases, we should remove it from the class system too
        # Go through all birthdays to see if there are any new ones
        for entry in all_birthdays:
            uid = entry["uid"]
            mentioned.append(uid)
            if uid not in data:  # This would happen if there's a new entry to the database that we haven't yet treated
                data[uid] = process_birthday(bot, entry)
            else:
                if bot.name == "cobble":
                    if data[uid].birthday_date.iso() != entry["birthday"]:
                        data[uid].birthday_date = time2.date.from_iso(entry["birthday"], time2.Kargadia)

                    if entry["location"] and str(data[uid].tz) != entry["location"]:
                        try:
                            data[uid].tz = conworlds.Place(entry["location"]).tz
                        except (ValueError, AttributeError, KeyError):  # Place does not exist or is not specified (null -> AttError)
                            data[uid].tz = time2.KargadianTimezone(time2.timedelta(), "Virsetgar", "VSG")
                    elif not entry["location"]:
                        data[uid].tz = time2.KargadianTimezone(time2.timedelta(), "Virsetgar", "VSG")
                else:
                    if data[uid].birthday_date.iso() != entry["birthday"].strftime("%Y-%m-%d"):
                        data[uid].birthday_date = time2.date.from_datetime(entry["birthday"])
                    tz_entry = bot.db.fetchrow("SELECT * FROM timezones WHERE uid=?", (uid,))
                    if tz_entry and tz_entry["tz"] != str(data[uid].tz):
                        data[uid].tz = pytz.timezone(tz_entry["tz"])
                    elif tz_entry is None:
                        data[uid].tz = time2.timezone.utc
                data[uid].push_birthday()  # Force the birthday to go ahead of itself if it gets stuck
                # if data[uid].breaking < 2:  # Regenerate the data if a breaking change is hit and the old pickle won't work anymore
                #     current = data[uid]
                #     data[uid] = birthday.Birthday(current.uid, current.birthday_date, current.tz, current.bot)
        # Go through the data entries to see if there are any old entries that don't exist in the db anymore
        for uid in list(data):  # Should prevent "RuntimeError: dictionary changed size during iteration"
            if uid not in mentioned:  # not an entry in the db
                data.pop(uid)  # removes the entry
        birthday.birthdays[bot.name] = data


async def birthdays(bot: bot_data.Bot):
    """ Handle birthdays """
    update_speed = 1800  # 3600
    time_class = time2.Kargadia if bot.name == "cobble" else time2.Earth
    prep_birthdays(bot)
    # birthday.save()
    await wait_until_next_iter(update_speed, 1, time_class)  # Start at xx:00:01 to avoid starting at 59:59 and breaking everything
    await bot.wait_until_ready()
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised Birthdays")

    while True:
        try:
            guilds = {}
            settings = bot.db.fetch("SELECT * FROM settings WHERE bot=?", (bot.name,))
            for entry in settings:
                data = json.loads(entry["data"])
                if "birthdays" in data:
                    if data["birthdays"]["enabled"]:
                        out = [data["birthdays"]["role"], data["birthdays"]["channel"], data["birthdays"]["message"]]
                        guilds[entry["gid"]] = out

            prep_birthdays(bot)
            # birthday_today = bot.db.fetch("SELECT * FROM birthdays WHERE has_role=0 AND strftime('%m-%d', birthday) = strftime('%m-%d', 'now') AND bot=?", (bot.name,))
            birthday_today = birthday.birthdays_today(bot.name)
            if birthday_today:
                for person in birthday_today:
                    # dm = True
                    for gid, data in guilds.items():
                        # guild = guilds[i]
                        guild: discord.Guild = bot.get_guild(gid)
                        if guild is not None:
                            user: discord.Member = guild.get_member(person.uid)
                            if user is not None:
                                # dm = False
                                if data[1] and data[2]:
                                    channel: discord.TextChannel = guild.get_channel(data[1])
                                    message = data[2].replace("[MENTION]", user.mention).replace("[USER]", user.name)
                                    try:
                                        await channel.send(message)
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
                    person.has_role = True
                    if bot.name == "cobble":
                        bot.db.execute("UPDATE kargadia SET has_role=1 WHERE uid=?", (person.uid,))
                    else:
                        bot.db.execute(f"UPDATE birthdays SET has_role=1 WHERE uid=? AND bot=?", (person.uid, bot.name))

            # birthday_over = bot.db.fetch("SELECT * FROM birthdays WHERE has_role=1 AND strftime('%m-%d', birthday) != strftime('%m-%d', 'now') AND bot=?", (bot.name,))
            birthday_over = birthday.birthdays_ended(bot.name)
            for person in birthday_over:
                if bot.name == "cobble":
                    bot.db.execute("UPDATE kargadia SET has_role=0 WHERE uid=?", (person.uid,))
                else:
                    bot.db.execute(f"UPDATE birthdays SET has_role=0 WHERE uid=? AND bot=?", (person.uid, bot.name))
                person.has_role = False
                person.push_birthday()
                for gid, data in guilds.items():
                    # guild = guilds[i]
                    guild: discord.Guild = bot.get_guild(gid)
                    if guild is not None:
                        user: discord.Member = guild.get_member(person.uid)
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
        except (aiohttp.ClientConnectorError, ConnectionError):
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Birthdays Handler > Error with connection.")
        except Exception as e:
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Birthdays Handler > {type(e).__name__}: {e}")
            general.log_error(bot, general.traceback_maker(e).strip("```")[3:-1])  # Remove the codeblock markdown and extra newlines

        # birthday.save()
        await asyncio.sleep(1)
        await wait_until_next_iter(update_speed, 1, time_class)


ka_places = {
    "Regaazdall": {
        "Munearan Köreldaivus": {"data": "", "weight": 30},
        "Regavall":             {"data": "", "weight": 40},
        "Reggar":               {"data": "", "weight": 50},
        "Suvagar":              {"data": "", "weight": 40},
        "Vaidangar":            {"data": "", "weight": 25},
        "Vakungar":             {"data": "", "weight": 25},
    },
    "Nehtivia": {
        "Ekspigar":           {"data": "", "weight": 35},
        "Kollugar":           {"data": "", "weight": 35},
        "Leitagar":           {"data": "", "weight": 35},
        "Pakigar":            {"data": "", "weight": 35},
        "Steirigar":          {"data": "", "weight": 35},
        "Sunmagar":           {"data": "", "weight": 25},
        "Tenmagar":           {"data": "", "weight": 30},
        "Runnegar":           {"data": "", "weight": 25},
        "Lurvugar":           {"data": "", "weight": 25},
        "Peaskar":            {"data": "", "weight": 25},
        "Sulingar":           {"data": "", "weight": 30},
        "Alexandris":         {"data": "", "weight": 35},
        "Drippangar":         {"data": "", "weight": 35},
        "Joptanagar":         {"data": "", "weight": 35},
        "Läkingar":           {"data": "", "weight": 25},
        "Leogar":             {"data": "", "weight": 35},
        "Menenvallus":        {"data": "", "weight": 30},
        "Melligar":           {"data": "", "weight": 35},
        "Tevivall":           {"data": "", "weight": 30},
        # "Watsangar":          {"data": "", "weight": 35},
        "Chakkangar":         {"data": "", "weight": 35},
        "Kamikawa":           {"data": "", "weight": 35},
        "Kiomigar":           {"data": "", "weight": 35},
        "Lailagar":           {"data": "", "weight": 35},
        "Koutun Köreldaivus": {"data": "", "weight": 30},
    },
    "Nittavia": {
        "Erdagar":     {"data": "", "weight": 25},
        "Ammugar":     {"data": "", "weight": 25},
        "Körevallus":  {"data": "", "weight": 30},
        "Saikovallus": {"data": "", "weight": 30},
    },
    "Tebaria": {
        "Kianta":       {"data": "", "weight": 25},
        "Kuntuma":      {"data": "", "weight": 25},
        "Sentatebaria": {"data": "", "weight": 30},
        "Nilli":        {"data": "", "weight": 25},
        "Nilligar":     {"data": "", "weight": 25},
        "Hantia":       {"data": "", "weight": 25},
        "Hantisgar":    {"data": "", "weight": 25},
        "Tahda":        {"data": "", "weight": 25},
        "Kaivalgard":   {"data": "", "weight": 35},
        "Kuvul-Ghuzu":  {"data": "", "weight": 25},
        "Harvugar":     {"data": "", "weight": 30},
        "Urum":         {"data": "", "weight": 30},
        "Kullivi":      {"data": "", "weight": 25},
        "Nurvut":       {"data": "", "weight": 25},
        "Vallangar":    {"data": "", "weight": 25},
        "Kaltagar":     {"data": "", "weight": 25},
        "Noqqo":        {"data": "", "weight": 25},
        "Qeshte":       {"data": "", "weight": 25},
        "Kainedungar":  {"data": "", "weight": 25},
        "Suttulu":      {"data": "", "weight": 25},
        "Usmutgar":     {"data": "", "weight": 25},
        "Bylkangar":    {"data": "", "weight": 30},
        "Kaltatebaria": {"data": "", "weight": 25},
        "Sittegar":     {"data": "", "weight": 25},
        "Keltagar":     {"data": "", "weight": 25},
        "Sadegar":      {"data": "", "weight": 25},
        "Tenkigar":     {"data": "", "weight": 25},
        "Vadertebaria": {"data": "", "weight": 25},
        "Istagar":      {"data": "", "weight": 25},
        "Lervagar":     {"data": "", "weight": 25},
        "Simmagar":     {"data": "", "weight": 25},
        "Hinnegar":     {"data": "", "weight": 25},
    },
    "Kaltar Azdall": {
        "Kalta Centeria": {"data": "", "weight": 25},
        "Kalta Mainta":   {"data": "", "weight": 25},
        "Kaltar Kainead": {"data": "", "weight": 20},
        "Kaltarena":      {"data": "", "weight": 25},
        "Küangar":        {"data": "", "weight": 25},
    },
    "Arnattia": {
        "Mahatarna":   {"data": "", "weight": 25},
        "Vainararna":  {"data": "", "weight": 25},
        "Ezmetarna":   {"data": "", "weight": 25},
        "Tuhtun Arna": {"data": "", "weight": 25},
        "Avikarna":    {"data": "", "weight": 25},
        "Kanerarna":   {"data": "", "weight": 25},
        "Terra Arna":  {"data": "", "weight": 25},
    },
    "Erellia": {
        "Itta":      {"data": "", "weight": 25},
        "Rankadus":  {"data": "", "weight": 20},
        "Raagar":    {"data": "", "weight": 25},
        "Orlagar":   {"data": "", "weight": 35},
        "Shonangar": {"data": "", "weight": 35},
    },
    "Centeria": {
        "Kalagar":   {"data": "", "weight": 25},
        "Sukugar":   {"data": "", "weight": 30},
        "Virsetgar": {"data": "", "weight": 30},
    },
    "Verlennia": {
    },
    "Inhattia": {
    },
    "Other Areas": {
        "Rakka's Volcano":     {"data": "", "weight": 35},
        "Vintelingar":         {"data": "", "weight": 35},
        "North Pole Kargadia": {"data": "", "weight": 20},
    }
}
_places = {}  # Since the playing status won't be able to read through a 2-layer dict...
# ka-time will read the data from ka_places, to show the data with layers
# Playing will read the data from _places, to show as a simple dict
# _places will also store the Place instances, so that it wouldn't be necessary to keep calling new ones...

ka_time: ...  # Current time in Virsetgar, used to determine time until next holiday

# The key is the timestamp as mm-dd, the value is the date instance
# Lists are used to store the holidays in a shorter way, then the dicts store the times
ka_holidays_list = ["01-01", "01-06", "01-07", "02-06", "02-14", "03-07", "03-12", "03-13", "04-08", "05-07", "05-13", "06-02",
                    "07-01", "07-09", "08-01", "08-02", "08-11", "08-16", "09-09", "10-09", "11-02", "11-03", "11-04", "12-05",
                    "12-11", "13-01", "13-03", "14-01", "14-02", "14-03", "14-04", "15-16", "16-05", "16-07", "16-08"]
ka_holidays: dict[str, time2.date] = {}
sl_holidays_list = ["01-01", "01-27", "02-14", "03-03", "03-17", "04-17", "05-13", "06-03", "06-20", "06-25", "08-08",
                    "09-01", "10-03", "10-22", "10-31", "11-19", "12-05"]
sl_holidays: dict[str, time2.date] = {}


def get_time_ka():
    now = time2.date.today(time2.Kargadia)
    year = now.year
    for key in ka_holidays_list:
        month, day = key.split("-", 1)
        holiday_time = time2.date(year, int(month), int(day), time2.Kargadia)
        if now > holiday_time:  # if the holiday already passed this year, skip to next year
            holiday_time = holiday_time.replace(year=holiday_time.year + 1)
            # holiday_time = (holiday_time + time2.relativedelta(years=1, time_class=time2.Kargadia)).date()
        ka_holidays[key] = holiday_time


def get_time_sl():
    now = time2.date.today(time2.Earth)
    year = now.year
    for key in sl_holidays_list:
        month, day = key.split("-", 1)
        holiday_time = time2.date(year, int(month), int(day), time2.Earth)
        if now > holiday_time:  # if the holiday already passed this year, skip to next year
            holiday_time = holiday_time.replace(year=holiday_time.year + 1)
            # holiday_time = (holiday_time + time2.relativedelta(years=1)).date()
        sl_holidays[key] = holiday_time


get_time_ka()
get_time_sl()


# Instead of running itself all the time, this function will now simply run itself when showing Kargadian times or loading holidays
def ka_data_updater(bot: bot_data.Bot):
    """ Update time and weather data for Kargadian cities """
    # logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised City Data Updater")
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
                en = bot.language2("en")
                ka = bot.language2("ne_rc")
                kargadian = f"{place.name_translation(ka)}: "
                kargadian += place.time.strftime("%d %b %Y, %H:%M", "ne_rc")
                english = f"{place.name_translation(en):<20} - "
                english += place.time.strftime("%d %b %Y, %H:%M", "en")
                if place.weather is not None:
                    temp = f"{place.weather['temperature']:.0f}°C"
                    rain = place.weather['rain']
                    if rain == "sunny":
                        rain += "2" if place.sun is not None and place.sun.elevation < 0 else "1"
                    weather_en = en.data("weather78")[rain]
                    weather_ka = ka.data("weather78")[rain]
                    english += f" | {temp} | {weather_en}"
                    kargadian += f" | {temp} | {weather_ka}"
                # ka_cities[city] = {"english": english, "tebarian": tebarian, "weight": ka_cities[city]["weight"]}
                ka_places[area_name][city]["data"] = english
                _places[city]["text"] = kargadian
                if city == "Virsetgar":  # Since, after all, Virsetgar is currently the UTC base, so the dates and times are based off of that...
                    global ka_time
                    ka_time = place.time
                # logger.log(bot.name, "kargadia", f"{time.time()} > {bot.full_name} > Updated data for {city}")
            except Exception as e:
                general.print_error(f"{time.time()} > {bot.full_name} > City Data Updater > {type(e).__name__}: {e}")
                log_out = f"{time.time()} > {bot.full_name} > Error updating data for {city} - {type(e).__name__}: {e}"
                logger.log(bot.name, "kargadia", log_out)
                logger.log(bot.name, "errors", log_out)
    logger.log(bot.name, "kargadia", f"{time.time()} > {bot.full_name} > City Data Updater > Updated Kargadian cities data")


async def ka_time_updater(bot: bot_data.Bot):
    """ Update the time and weather info for Kargadian cities in Kargadia and Regaus'tar Koankadu """
    update_speed = 300
    await wait_until_next_iter(update_speed, 1, time2.Kargadia)
    await bot.wait_until_ready()
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised RK City Time Updater")

    channel_ka = bot.get_channel(942476819892961290)  # Kargadia server
    channel_rk = bot.get_channel(935982691801780224)  # Old RK channel: 887087307918802964

    # This is so that I wouldn't have to continuously ask the discord API for the message. Their instances can be stored here, and if they magically disappear, they will be recreated.
    async def get_data(channel: discord.abc.Messageable) -> dict[str, discord.Message | None]:
        messages = {}
        # Load all areas currently available, initialise them with a None
        for key in ka_places.keys():
            messages[key] = None
        # Store the messages for the appropriate channel
        # Now, if the message exists, it will be stored in its appropriate area, and if not, it will remain null
        async for msg in channel.history(limit=None, oldest_first=True):
            if msg.author.id == bot.user.id:  # Make sure the message is sent by us
                line = msg.content.splitlines()[0]  # Get the message's header (eg "Regaazdall:")
                messages[line[:-1]] = msg  # The message's instance is then stored into its appropriate dict
        return messages

    try:
        messages_ka = await get_data(channel_ka)
        messages_rk = await get_data(channel_rk)
    except (aiohttp.ClientConnectorError, ConnectionError):
        general.log_error(bot, f"{time.time()} > {bot.full_name} > City Time Updater (Message Loader) > Error with connection.")
        await bot.wait_until_ready()
        await asyncio.sleep(10)

        # Try again, whatever...
        try:
            messages_ka = await get_data(channel_ka)
            messages_rk = await get_data(channel_rk)
        except (aiohttp.ClientConnectorError, ConnectionError):
            general.log_error(bot, f"{time.time()} > {bot.full_name} > City Time Updater (Message Loader) > Discord.py is weird.")
            logger.log(bot.name, "kargadia", f"{time.time()} > {bot.full_name} > City Time Updater > Messages broken, relaunching function in 5 minutes...")
            await asyncio.sleep(300)
            return await ka_time_updater(bot)
    except Exception as e:
        general.log_error(bot, f"{time.time()} > {bot.full_name} > City Time Updater (Message Loader) > {type(e).__name__}: {e}")
        general.log_error(bot, general.traceback_maker(e).strip("```")[3:-1])  # Remove the codeblock markdown and extra newlines
        logger.log(bot.name, "kargadia", f"{time.time()} > {bot.full_name} > City Time Updater > Messages broken, relaunching function in 1 minute...")
        await asyncio.sleep(60)
        return await ka_time_updater(bot)

    async def update_message(name: str, content: str):
        async def edit_message(messages_dict: dict, channel: discord.abc.Messageable):
            try:
                message = messages_dict[name]
                if message is None:  # Only edit the message if it actually exists
                    raise RegausError(f"Message for {name} does not exist")
                await message.edit(content=content)
            except (KeyError, discord.NotFound, RegausError):  # Message not found
                message = await channel.send(content)  # Send a new message
                messages_dict[name] = message  # Store the new message
                logger.log(bot.name, "kargadia", f"{time.time()} > {bot.full_name} > City Time Updater > {channel} > {name} > Message not found, sending new one")
            except Exception as _e:  # Any other error
                out = f"{time.time()} > {bot.full_name} > City Time Updater > {channel} > {name} > {type(_e).__name__}: {_e}"
                general.print_error(out)
                logger.log(bot.name, "kargadia", out)
                logger.log(bot.name, "errors", out)

        await edit_message(messages_ka, channel_ka)
        await edit_message(messages_rk, channel_rk)

    while True:
        try:
            ka_data_updater(bot)

            for area_name, area in ka_places.items():
                data = [f"{area_name}:"]
                for _data in area.values():
                    data.append(f"`{_data['data']}`")
                await update_message(area_name, "\n".join(data))
            logger.log(bot.name, "kargadia", f"{time.time()} > {bot.full_name} > City Time Updater > Updated Kargadian cities times messages")

            # This should make it adjust itself for lag caused
            await asyncio.sleep(1)  # Hopefully prevents it from lagging ahead of itself
            await wait_until_next_iter(update_speed, 1, time2.Kargadia)
            # await asyncio.sleep(update_speed)
        except (aiohttp.ClientConnectorError, ConnectionError):
            general.log_error(bot, f"{time.time()} > {bot.full_name} > City Time Updater > Error with connection.")
        except Exception as e:
            general.log_error(bot, f"{time.time()} > {bot.full_name} > City Time Updater > {type(e).__name__}: {e}")
            general.log_error(bot, general.traceback_maker(e).strip("```")[3:-1])  # Remove the codeblock markdown and extra newlines


async def playing(bot: bot_data.Bot):
    update_speed = 120
    await wait_until_next_iter(update_speed, 0)
    await bot.wait_until_ready()
    await asyncio.sleep(1)  # So that the new status isn't immediately overwritten with the "Loading..." status if the status change time is hit during loading
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised Playing updater")

    # It would be funnier to set it to Cobbletopia Tebarian, but that language will not be made anytime soon,
    # and it would also be even less likely to be understood by anyone, so it's better off to leave the language as Regaazdall Nehtivian
    language = bot.language2("ne_rc")
    holiday_names_ka = language.data("data_holidays_ka")
    holiday_names_sl = language.data("data_holidays_sl")

    def get_date(month, day):
        _date = time2.date(year, month, day)
        if today > _date:
            return time2.date(year + 1, month, day)
        return _date

    def until(when: time2.date, rsl: bool = False):
        days = (when - time2.date.today(when.time_class)).days
        if rsl:
            s = "in" if days != 1 else ""
            v = "at" if days == 1 else "an"
            return f"{days} sea{s} astall{v}"
        else:
            s = "s" if days != 1 else ""
            return f"{days} day{s}"

    while True:
        try:
            version = general.get_version().get(bot.name, {"version": "Unknown version", "short_version": "Unknown"})
            fv, sv = f"v{version['version']}", f"v{version['short_version']}"
            today = time2.date.today()
            year = today.year

            regaus = get_date(1, 27)
            is_regaus = today == regaus
            status_regaus = f"🎉 Today is Regaus's birthday!" if is_regaus else f"{until(regaus, False)} until Regaus's birthday"
            if bot.name == "cobble":
                status_type = random.choices([1, 2, 3, 4, 5], [15, 40, 10, 10, 25])[0]
                # 1 = birthdays, 2 = playing, 3 = WK holidays, 4 = SL holidays, 5 = time and weather
                if status_type == 1:
                    cobble = get_date(12, 5)
                    is_cobble = today == cobble
                    status_cobble = f"🎉 Esea jat mun reidesea!" if is_cobble else f"{until(cobble, True)} mun reideseat"
                    status_regaus = f"🎉 Esea jat Regaus'ta reidesea!" if is_regaus else f"{until(regaus, True)} Regaus'tat reideseat"
                    random.seed()
                    status = random.choice([status_cobble, status_regaus])
                    activity = discord.Game(name=status)
                    logger.log(bot.name, "playing", f"{time.time()} > {bot.full_name} > Updated activity to {status} (Status Type 1)")
                elif status_type == 2:
                    activities = [
                        {"type": 0, "name": fv},
                        {"type": 0, "name": f"{bot.local_config['prefixes'][0]}help | {sv}"},
                        {"type": 0, "name": "ka Regausan"},
                        {"type": 0, "name": "ka dekedan"},
                        {"type": 0, "name": "ka ten rajain"},
                        {"type": 5, "name": "i noartan"},
                        {"type": 0, "name": "denedan"},
                        {"type": 3, "name": "ten"},
                        {"type": 3, "name": "ten sevartan"},
                        {"type": 2, "name": "ut penat"},
                        {"type": 3, "name": "na meitan"},
                        {"type": 2, "name": "na deinettat"},
                        {"type": 0, "name": "inkorra kiinan seldevanvarkan an ten eivarkaivanan"},
                    ]
                    random.seed()
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
                        3: "Veitea",
                        5: "Ahmura sen"
                    }.get(_activity["type"], "Undefined")
                    logger.log(bot.name, "playing", f"{time.time()} > {bot.full_name} > Updated activity to {status} {name} (Status Type 2)")
                elif status_type == 3:  # Kargadian holidays
                    ka_data_updater(bot)
                    ka_day: time2.date = ka_time.date()
                    status = None
                    for key, holiday in ka_holidays.items():
                        if holiday == ka_day:
                            # name = language.case(holiday_names_ka.get(key), "genitive", "singular")
                            _name = holiday_names_ka.get(key, key)
                            if _name == "Nuar Kad":
                                name = "Nuan Kadan"
                            else:
                                name = re.sub(r"^Sea", "Sean", _name)
                                name = re.sub(r"sea$", "sean", name)
                            status = f"Kovanan {name}!"
                            break
                    if status is None:  # if no holidays are on, so the status hasn't yet been determined
                        random.seed()
                        key, holiday = random.choice(list(ka_holidays.items()))
                        # name = language.case(holiday_names_ka.get(key), "dative", "singular")
                        _name = holiday_names_ka.get(key, key)
                        if _name == "Nuar Kad":
                            name = "Nuart Kadut"
                        else:
                            name = re.sub(r"^Sea", "Seat", _name)
                            name = re.sub(r"sea$", "seat", name)
                        status = f"ZK: {until(holiday, True)} {name}"
                    activity = discord.Game(name=status)
                    logger.log(bot.name, "playing", f"{time.time()} > {bot.full_name} > Updated activity to {status} (Status Type 3)")
                elif status_type == 4:  # SL holidays
                    status = None
                    for key, holiday in sl_holidays.items():
                        if holiday == today:
                            # name = language.case(holiday_names_sl.get(key), "genitive", "singular")
                            _name = holiday_names_sl.get(key, key)
                            if _name == "Nuar Kad":
                                name = "Nuan Kadan"
                            elif _name == "Hallauvin":
                                name = "Hallauvinan"
                            else:
                                name = re.sub(r"^Sea", "Sean", _name)
                                name = re.sub(r"sea$", "sean", name)
                            status = f"Kovanan {name}!"
                            break
                    if status is None:  # if the status still hasn't been decided, meaning no holidays are on
                        random.seed()
                        key, holiday = random.choice(list(sl_holidays.items()))
                        # name = language.case(holiday_names_sl.get(key), "dative", "singular")
                        _name = holiday_names_sl.get(key, key)
                        if _name == "Nuar Kad":
                            name = "Nuart Kadut"
                        elif _name == "Hallauvin":
                            name = "Hallauvinut"
                        else:
                            name = re.sub(r"^Sea", "Seat", _name)
                            name = re.sub(r"sea$", "seat", name)
                        status = f"SL: {until(holiday, True)} {name}"
                    activity = discord.Game(name=status)
                    logger.log(bot.name, "playing", f"{time.time()} > {bot.full_name} > Updated activity to {status} (Status Type 4)")
                else:  # status_type == 5
                    ka_data_updater(bot)
                    data, weights = [], []
                    for city in _places.items():
                        data.append(city)
                        weights.append(city[1]["weight"])
                    random.seed()
                    city_data = random.choices(data, weights)[0][1]
                    status = f"{city_data['text']}"
                    activity = discord.Game(name=status)
                    logger.log(bot.name, "playing", f"{time.time()} > {bot.full_name} > Updated activity to {status} (Status Type 5)")

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
                    random.seed()
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
                        {"type": 0, "name": "Snuggling with Matsu"},
                        {"type": 0, "name": "Feeding Matsu"},
                        {"type": 0, "name": "Petting Matsu"},
                        {"type": 0, "name": "Eating pineapples"},
                        {"type": 0, "name": "Eating pineapple pizza"},
                        {"type": 0, "name": "Stealing pineapples"},
                        {"type": 0, "name": "Stealing star cookies"},
                        {"type": 0, "name": "Praying to the Pineapple God"},
                        {"type": 3, "name": "you"},
                    ]
                    random.seed()
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

            elif bot.name == "kyomi2":  # Mochi
                activities = [
                    {"type": 0, "name": "Looking for cookies"},
                    {"type": 0, "name": "Snuggling with Mizuki"},
                    {"type": 0, "name": "Stealing cookies from Mizuki"},
                    {"type": 0, "name": "Eating cookies"},
                ]
                random.seed()
                _activity = random.choice(activities)
                activity = discord.Activity(type=_activity["type"], name=_activity["name"])
                name = _activity["name"]
                status = {
                    0: "Playing",
                }.get(_activity["type"], "Undefined")
                logger.log(bot.name, "playing", f"{time.time()} > {bot.full_name} > Updated activity to {status} {name}")

            elif bot.name == "kyomi3":  # Matsu
                activities = [
                    {"type": 0, "name": "Looking for cheese"},
                    {"type": 0, "name": "Snuggling with Mizuki"},
                    {"type": 0, "name": "Stealing cheese from Mizuki"},
                    {"type": 0, "name": "Eating cheese"},
                ]
                random.seed()
                _activity = random.choice(activities)
                activity = discord.Activity(type=_activity["type"], name=_activity["name"])
                name = _activity["name"]
                status = {
                    0: "Playing",
                }.get(_activity["type"], "Undefined")
                logger.log(bot.name, "playing", f"{time.time()} > {bot.full_name} > Updated activity to {status} {name}")

            elif bot.name == "pretender":
                activities = [
                    {"type": 0, "name": "Amogus"},
                    {"type": 0, "name": "Among us"},
                    {"type": 3, "name": "your every move"},
                    {"type": 3, "name": "after you"}
                ]
                random.seed()
                _activity = random.choice(activities)
                activity = discord.Activity(type=_activity["type"], name=_activity["name"])
                name = _activity["name"]
                status = {
                    0: "Playing",
                    3: "Watching"
                }.get(_activity["type"], "Undefined")
                logger.log(bot.name, "playing", f"{time.time()} > {bot.full_name} > Updated activity to {status} {name}")

            else:  # Suager
                status_type = random.random()
                if status_type <= 0.2:  # 20% chance of being a birthday status
                    suager = get_date(5, 13)
                    is_suager = today == suager
                    status_suager = f"🎉 Today is my birthday!" if is_suager else f"{until(suager, False)} until my birthday"
                    random.seed()
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
                    random.seed()
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
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Playing Changer > Failed to save changes.")
        except (aiohttp.ClientConnectorError, ConnectionError):
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Playing Changer > Error with connection.")
        except Exception as e:
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Playing Changer > {type(e).__name__}: {e}")
            general.log_error(bot, general.traceback_maker(e).strip("```")[3:-1])  # Remove the codeblock markdown and extra newlines

        # This should make it adjust itself for lag caused
        await asyncio.sleep(1)  # Hopefully prevents it from lagging ahead of itself
        await wait_until_next_iter(update_speed, 0)


async def avatars(bot: bot_data.Bot):
    await wait_until_next_iter(3600, 1)
    await bot.wait_until_ready()
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised Avatar updater")

    while True:
        try:
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
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Avatar Changer > Failed to save changes.")
        except (aiohttp.ClientConnectorError, ConnectionError):
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Avatar Changer > Error with connection.")
        except Exception as e:
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Avatar Changer > {type(e).__name__}: {e}")
            general.log_error(bot, general.traceback_maker(e).strip("```")[3:-1])  # Remove the codeblock markdown and extra newlines

        await asyncio.sleep(1)
        await wait_until_next_iter(3600, 1)


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
                    language = bot.language(commands.FakeContext(guild, bot))
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
                        ended = language.time(poll["expiry"], short=1, dow=False, seconds=False, tz=True)
                        embed.description = language.string("polls_end_description", question=poll["question"], time=ended, result=result)
                        embed.add_field(name=language.string("polls_votes_result"), inline=False,
                                        value=language.string("polls_votes_current2", yes=language.number(yes), neutral=language.number(neutral), no=language.number(no),
                                                              total=language.number(total), score=language.number(score, positives=True),
                                                              percentage=language.number(upvotes, precision=2, percentage=True)))
                        if not poll["anonymous"]:
                            _yes = "\n".join([f"<@{voter}>" for voter in voters_yes[:45]])
                            if yes >= 45:
                                _yes += language.string("polls_votes_many", val=language.number(yes - 45))
                            if not _yes:
                                _yes = language.string("polls_votes_none2")
                            embed.add_field(name=language.string("polls_votes_yes"), value=_yes, inline=True)
                            _neutral = "\n".join([f"<@{voter}>" for voter in voters_neutral[:45]])
                            if neutral >= 45:
                                _neutral += language.string("polls_votes_many", val=language.number(neutral - 45))
                            if not _neutral:
                                _neutral = language.string("polls_votes_none2")
                            embed.add_field(name=language.string("polls_votes_neutral"), value=_neutral, inline=True)
                            _no = "\n".join([f"<@{voter}>" for voter in voters_no[:45]])
                            if no >= 45:
                                _no += language.string("polls_votes_many", val=language.number(no - 45))
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
                            await channel.send(embed=embed)
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
                    language = bot.language(commands.FakeContext(guild, bot))
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
                                _data = bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (guild.id, bot.name))
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
                                                    new_mute_end = time.now2() + time.td(seconds=duration)
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
                                                        output = language.string("trials_success_mute_timed", id=trial_id, user=user, duration=_duration)
                                                        await channel.send(output)

                                                    bot.db.execute("INSERT INTO punishments(uid, gid, action, author, reason, temp, expiry, handled, bot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                                                   (member.id, guild.id, "mute", trial["author_id"], trial_success_text, True, new_mute_end, 0, bot.name))
                                                else:
                                                    # if temp_mute_entry:
                                                    #     bot.db.execute("DELETE FROM temporary WHERE entry_id=?", (temp_mute_entry["entry_id"],))
                                                    if channel:
                                                        output = language.string("trials_success_mute", id=trial_id, user=user)
                                                        await channel.send(output)

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
                                                    output = language.string("trials_success_unmute", id=trial_id, user=user)
                                                    await channel.send(output)
                            else:
                                out = f"{time.time()} > {bot.full_name} > Trials > Trial {trial_id} > Member not found - can't mute"
                                general.print_error(out)
                                logger.log(bot.name, "errors", out)
                                if channel:
                                    string = "trials_error_member_none_mute" if action == "mute" else "trials_error_member_none_unmute"
                                    await channel.send(language.string(string, id=trial_id))
                        elif action == "kick":
                            if member:
                                # try:
                                #     await user.send(f"You have been kicked from {guild.name}.\n{reason_dm}")
                                # except (discord.HTTPException, discord.Forbidden):
                                #     pass
                                await member.kick(reason=trial_success_text)
                                if channel:
                                    output = language.string("trials_success_kick", id=trial_id, user=user)
                                    await channel.send(output)
                            else:
                                out = f"{time.time()} > {bot.full_name} > Trials > Trial {trial_id} > Member not found - can't kick"
                                general.print_error(out)
                                logger.log(bot.name, "errors", out)
                                if channel:
                                    await channel.send(language.string("trials_error_member_none_kick", id=trial_id))
                        elif action == "ban":
                            # I don't have to check if the user exists here, because otherwise it would raise a discord.NotFound while fetching
                            # try:
                            #     await user.send(f"You have been banned from {guild.name}.\n{reason_dm}")
                            # except (discord.HTTPException, discord.Forbidden):
                            #     pass
                            await guild.ban(user, reason=trial_success_text, delete_message_days=0)
                            if channel:
                                output = language.string("trials_success_ban", id=trial_id, user=user)
                                await channel.send(output)
                        elif action == "unban":
                            # try:
                            #     await user.send(f"You have been unbanned from {guild.name}.\n{reason_dm}")
                            # except (discord.HTTPException, discord.Forbidden):
                            #     pass
                            await guild.unban(user, reason=trial_success_text)
                            if channel:
                                output = language.string("trials_success_unban", id=trial_id, user=user)
                                await channel.send(output)
                        else:
                            out = f"{time.time()} > {bot.full_name} > Trials > Trial {trial_id} > Action type detection went wrong."
                            general.print_error(out)
                            logger.log(bot.name, "errors", out)
                        await send_mod_dm(bot, commands.FakeContext(guild, bot), member, action, f"Trial results (Score: {score:+}, {upvotes:.2%} voted yes)", duration_text)
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
                            output = language.string(fail_text, id=trial_id, user=user)
                            await channel.send(output)
                    if channel:
                        embed = discord.Embed(colour=colour)
                        embed.title = language.string("trials_end_title")
                        _expiry = language.time(trial["expiry"], short=1, dow=False, seconds=False, tz=True)
                        embed.description = language.string("trials_end_description", result=output, reason=trial["reason"], time=_expiry)
                        embed.add_field(name=language.string("trials_votes_result"), inline=False,
                                        value=language.string("trials_votes_current2", yes=language.number(yes), neutral=language.number(neutral), no=language.number(no),
                                                              total=language.number(total), score=language.number(score, positives=True),
                                                              percentage=language.number(upvotes, precision=2, percentage=True), required=language.number(required)))
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
                            await channel.send(embed=embed)
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
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised 2023 New Year Script")
    # ny = time.dt(2022, 12, 31, 17, 22)
    ny = time.dt(2023)
    now = time.now()
    if now > ny:
        logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > New Year script > It is already 2023...")
        return

    # Testing channels: 742885168997466196 Secretive-commands, 753000962297299005 SC2 | Announcements channels: 572857995852251169 SL, 970756319164399656 Ka
    # channels = [bot.get_channel(742885168997466196)]
    channels = [bot.get_channel(572857995852251169), bot.get_channel(970756319164399656)]
    delay = ny - now
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > New Year script > Waiting for {delay} until midnight...")
    await asyncio.sleep(delay.total_seconds())
    for channel in channels:
        await channel.send("The year 2022 has finally come to an end.\n"
                           "Another year has passed, and another has begun.\n"
                           "This was overall quite a challenging year. Many bad things happened, albeit with some occasional good news inbetween.\n"
                           "Now we can look back at this year and hope the next one will be better.\n"
                           "Happy New Year, fellow members of Senko Lair and the Kargadia cult! "
                           "Welcome to 2023, and let's see what this year will bring us...")
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > New Year script > Sent the New Year message. Exiting.")
    return


async def sl_holidays_updater(bot: bot_data.Bot):
    update_speed = 86400
    await wait_until_next_iter(update_speed, 1)  # Wait until midnight of the next day, to prevent sending holidays twice when restarting
    await bot.wait_until_ready()
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised Senko Lair Holidays")
    # Servers:  Senko Lair general, Kargadia Eve Earth, RK general
    channels = [568148147457490958, 974071578918785024, 738425419325243424]
    # Kargadia server temporarily excluded to not look weird while I test this stuff
    for ch in channels:
        channel = bot.get_channel(ch)
        if channel is None or not can_send(channel):
            general.print_error(f"{time.time()} > {bot.full_name} > SL Holidays > Channel {ch} can't be accessed")
            channels.remove(ch)  # Remove channels we can't access from the list

    language = bot.language2("en")
    holiday_names = language.data("data_holidays_sl")

    while True:
        try:
            today = time2.date.today()
            for key, holiday in sl_holidays.items():
                if holiday == today:
                    for ch in channels:
                        channel = bot.get_channel(ch)
                        await channel.send(f"Happy {holiday_names.get(key, key)}!")
                    logger.log(bot.name, "holidays", f"{time.time()} > {bot.full_name} > Kargadia Holidays > It is now {holiday_names.get(key)}")
                    # sl_holidays[key] = (sl_holidays[key] + time2.relativedelta(years=1, time_class=time2.Earth)).date()
                    sl_holidays[key] = holiday.replace(year=holiday.year + 1)
                    break
        except Exception as e:
            general.print_error(f"{time.time()} > {bot.full_name} > SL Holidays > {type(e).__name__}: {e}")
            logger.log(bot.name, "errors", f"{time.time()} > {bot.full_name} > SL Holidays > {type(e).__name__}: {e}")

        await asyncio.sleep(1)
        await wait_until_next_iter(update_speed, 1)


async def ka_holidays_updater(bot: bot_data.Bot):
    update_speed = 86400
    await wait_until_next_iter(update_speed, 1, time2.Kargadia)  # Update this every Kargadian midnight
    await bot.wait_until_ready()
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised Kargadian Holidays")
    # I don't think Kargadian holidays need to be sent into SL
    # Servers:  Kargadia Eve Karg,   RK general
    channels = [1051868654037389342, 738425419325243424]
    for ch in channels:
        channel = bot.get_channel(ch)
        if channel is None or not can_send(channel):
            general.print_error(f"{time.time()} > {bot.full_name} > Kargadia Holidays > Channel {ch} can't be accessed")
            channels.remove(ch)  # Remove channels we can't access from the list

    language = bot.language2("en")
    holiday_names = language.data("data_holidays_ka")

    while True:
        ka_data_updater(bot)
        try:
            ka_day: time2.date = ka_time.date()
            for key, holiday in ka_holidays.items():
                if holiday == ka_day:
                    for ch in channels:
                        channel = bot.get_channel(ch)
                        await channel.send(f"Happy {holiday_names.get(key, key)}!")
                    logger.log(bot.name, "holidays", f"{time.time()} > {bot.full_name} > Kargadia Holidays > It is now {holiday_names.get(key)}")
                    ka_holidays[key] = holiday.replace(year=holiday.year + 1)
                    # ka_holidays[key] = (ka_holidays[key] + time2.relativedelta(years=1, time_class=time2.Kargadia)).date()
                    break
        except Exception as e:
            general.print_error(f"{time.time()} > {bot.full_name} > Kargadia Holidays > {type(e).__name__}: {e}")
            logger.log(bot.name, "errors", f"{time.time()} > {bot.full_name} > Kargadia Holidays > {type(e).__name__}: {e}")

        await asyncio.sleep(1)
        await wait_until_next_iter(update_speed, 1, time2.Kargadia)
