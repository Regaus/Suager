from __future__ import annotations

import asyncio
import io
import json
import os
import random
import re
from typing import Type

import aiohttp
import discord
import pytz
from regaus import conworlds, RegausError, time as time2

from cogs.mod import send_mod_dm, send_mod_log
from utils import birthday, bot_data, commands, general, logger, time


async def wait_until_next_iter(update_speed: int = 120, adjustment: int = 0, time_class: Type[time2.Earth] = time2.Earth):
    now = time2.datetime.now(time_class=time_class)
    # Funny behaviour with adjustments:
    # If the update speed is 3600s (1 hour) and the adjustment is +5 minutes
    # Current time 20:40:00 -> Wait until 21:05:00
    # Current time 21:01:00 -> Wait until 21:05:00 (Instead of 22:05:00, like it would have before this change)
    # Current time 21:05:01 -> Wait until 22:05:00
    then = time2.datetime.from_timestamp((((now.timestamp - adjustment) // update_speed) + 1) * update_speed + adjustment, time2.timezone.utc, time_class)
    # if time_class.__name__ != "Earth":
    #     print("Time adjustments: Waiting for", str(then.to_earth_time() - now.to_earth_time()))
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
            expiry = bot.language2("en").time(entry["expiry"], short=1, dow=False, seconds=True, tz=True, uid=user.id)
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
        except (aiohttp.ClientConnectorError, ConnectionError):
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Reminders > Error with connection.")
        except Exception as e:
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Reminders > {type(e).__name__}: {e}")
            general.log_error(bot, general.traceback_maker(e).strip("```")[3:-1])  # Remove the codeblock markdown and extra newlines
        finally:
            await asyncio.sleep(1)


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
        except (aiohttp.ClientConnectorError, ConnectionError):
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Reminders Errors > Error with connection.")
        except Exception as e:
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Reminders Errors > {type(e).__name__}: {e}")
            general.log_error(bot, general.traceback_maker(e).strip("```")[3:-1])  # Remove the codeblock markdown and extra newlines
        finally:
            await asyncio.sleep(1)
            await wait_until_next_iter(update_speed, 0)


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
        except (aiohttp.ClientConnectorError, ConnectionError):
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Punishments > Error with connection.")
        except Exception as e:
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Punishments > {type(e).__name__}: {e}")
            general.log_error(bot, general.traceback_maker(e).strip("```")[3:-1])  # Remove the codeblock markdown and extra newlines
        finally:
            await asyncio.sleep(1)


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
        except (aiohttp.ClientConnectorError, ConnectionError):
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Punishments Errors > Error with connection.")
        except Exception as e:
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Punishments Errors > {type(e).__name__}: {e}")
            general.log_error(bot, general.traceback_maker(e).strip("```")[3:-1])  # Remove the codeblock markdown and extra newlines
        finally:
            await asyncio.sleep(1)
            await wait_until_next_iter(update_speed, 0)


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
                                    message = data[2].replace("[MENTION]", user.mention).replace("[USER]", general.username(user))
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
        finally:
            # birthday.save()
            await asyncio.sleep(1)
            await wait_until_next_iter(update_speed, 1, time_class)


ka_places = {
    "Regaazdall": {
        "Fanfe Kade":           {"data": "", "weight": 30},  # -03
        "Jostungar":            {"data": "", "weight": 30},  # -03
        "Lehtingar":            {"data": "", "weight": 30},  # -03
        "Leksinsalte":          {"data": "", "weight": 30},  # -03
        "Munearan Köreldaivus": {"data": "", "weight": 30},  # -03
        "Nuugar":               {"data": "", "weight": 30},  # -03
        "Regavall":             {"data": "", "weight": 40},  # -03
        "Reggar":               {"data": "", "weight": 50},  # -03
        "Suvagar":              {"data": "", "weight": 40},  # -03
        "Vaidangar":            {"data": "", "weight": 25},  # -03
        "Vakungar":             {"data": "", "weight": 25},  # -03
    },
    "Nehtivia": {
        "Ekspigar":             {"data": "", "weight": 35},  # -10
        "Kollugar":             {"data": "", "weight": 35},  # -10
        "Leitagar":             {"data": "", "weight": 35},  # -10
        "Pakigar":              {"data": "", "weight": 35},  # -10
        "Sadagar":              {"data": "", "weight": 35},  # -10
        "Stardew Valley":       {"data": "", "weight": 35},  # -10
        "Steirigar":            {"data": "", "weight": 35},  # -10
        "Tenmagar":             {"data": "", "weight": 30},  # -10
        "Runnegar":             {"data": "", "weight": 25},  # -09
        "Sunmagar":             {"data": "", "weight": 25},  # -09
        "Lurvugar":             {"data": "", "weight": 25},  # -08
        "Peaskar":              {"data": "", "weight": 25},  # -08
        "Sulingar":             {"data": "", "weight": 30},  # -08
        "Alexandris":           {"data": "", "weight": 35},  # -07
        "Joptanagar":           {"data": "", "weight": 35},  # -07
        "Läkingar":             {"data": "", "weight": 25},  # -07
        "Leogar":               {"data": "", "weight": 35},  # -07
        "Menenvallus":          {"data": "", "weight": 30},  # -07
        "Bakkangar":            {"data": "", "weight": 30},  # -06
        "Mel's Twin Mountains": {"data": "", "weight": 35},  # -06
        "Akuseru":              {"data": "", "weight": 35},  # -05
        "Chakkangar":           {"data": "", "weight": 35},  # -05
        "Kamikawa":             {"data": "", "weight": 35},  # -05
        "Kiomigar":             {"data": "", "weight": 35},  # -05
        "Kionagar":             {"data": "", "weight": 35},  # -05
        "Lailagar":             {"data": "", "weight": 35},  # -05
        "Melligar":             {"data": "", "weight": 35},  # -05
        "Tevivall":             {"data": "", "weight": 30},  # -05
        "Koutun Köreldaivus":   {"data": "", "weight": 30},  # -04
        "Reksigar":             {"data": "", "weight": 35},  # -04
    },
    "Nittavia": {
        "Erdagar":     {"data": "", "weight": 25},  # -09
        "Ammugar":     {"data": "", "weight": 25},  # -08
        "Körevallus":  {"data": "", "weight": 30},  # -07
        "Saikovallus": {"data": "", "weight": 30},  # -07
    },
    "Tebaria": {
        "Kianta":       {"data": "", "weight": 25},  # -11
        "Kuntuma":      {"data": "", "weight": 25},  # -10
        "Sentatebaria": {"data": "", "weight": 30},  # -08
        "Nilli":        {"data": "", "weight": 25},  # -06
        "Nilligar":     {"data": "", "weight": 25},  # -06
        "Hantia":       {"data": "", "weight": 25},  # -05
        "Hantisgar":    {"data": "", "weight": 25},  # -04
        "Tahda":        {"data": "", "weight": 25},  # -04
        "Kaivalgard":   {"data": "", "weight": 35},  # -02
        "Kuvul-Ghuzu":  {"data": "", "weight": 25},  # -02
        "Harvugar":     {"data": "", "weight": 30},  # -01
        "Urum":         {"data": "", "weight": 30},  # -01
        "Kullivi":      {"data": "", "weight": 25},  # +00
        "Nurvut":       {"data": "", "weight": 25},  # +00
        "Vallangar":    {"data": "", "weight": 25},  # +01
        "Kaltagar":     {"data": "", "weight": 25},  # +01
        "Noqqo":        {"data": "", "weight": 25},  # +02
        "Qeshte":       {"data": "", "weight": 25},  # +02
        "Kainedungar":  {"data": "", "weight": 25},  # +03
        "Suttulu":      {"data": "", "weight": 25},  # +03
        "Usmutgar":     {"data": "", "weight": 25},  # +03
        "Bylkangar":    {"data": "", "weight": 30},  # +04
        "Kaltatebaria": {"data": "", "weight": 25},  # +04
        "Sittegar":     {"data": "", "weight": 25},  # +04
        "Keltagar":     {"data": "", "weight": 25},  # +05
        "Sadegar":      {"data": "", "weight": 25},  # +06
        "Tenkigar":     {"data": "", "weight": 25},  # +07
        "Vadertebaria": {"data": "", "weight": 25},  # +09
        "Istagar":      {"data": "", "weight": 25},  # +11
        "Lervagar":     {"data": "", "weight": 25},  # +12
        "Simmagar":     {"data": "", "weight": 25},  # +13
        "Hinnegar":     {"data": "", "weight": 25},  # +14
    },
    "Kaltar Azdall": {
        "Kalta Centeria": {"data": "", "weight": 25},  # -01
        "Kalta Mainta":   {"data": "", "weight": 25},  # -01
        "Kaltar Kainead": {"data": "", "weight": 20},  # -01
        "Kaltarena":      {"data": "", "weight": 25},  # -01
        "Küangar":        {"data": "", "weight": 25},  # -01
    },
    "Arnattia": {
        "Mahatarna":   {"data": "", "weight": 25},  # -13
        "Vainararna":  {"data": "", "weight": 25},  # -13
        "Ezmetarna":   {"data": "", "weight": 25},  # -12
        "Tuhtun Arna": {"data": "", "weight": 25},  # -12
        "Avikarna":    {"data": "", "weight": 25},  # -11
        "Kanerarna":   {"data": "", "weight": 25},  # -11
        "Terra Arna":  {"data": "", "weight": 25},  # -11
    },
    "Erellia": {
        "Itta":                 {"data": "", "weight": 25},  # -05
        "Senka's Lair":         {"data": "", "weight": 30},  # -05
        "Shankiranköde":        {"data": "", "weight": 30},  # -05
        "Rankadus":             {"data": "", "weight": 20},  # -04
        "Erellian Köreldaivus": {"data": "", "weight": 35},  # -03
        "Larihalus":            {"data": "", "weight": 35},  # -03
        "Orlagar":              {"data": "", "weight": 35},  # -03
        "Raagar":               {"data": "", "weight": 25},  # -03
        "Shonangar":            {"data": "", "weight": 35},  # -03
    },
    "Centeria": {
        "Mügoslavia": {"data": "", "weight": 25},  # -01
        "Kalagar":    {"data": "", "weight": 25},  # +00
        "Sukugar":    {"data": "", "weight": 30},  # +00
        "Virsetgar":  {"data": "", "weight": 30},  # +00
    },
    "Verlennia": {
    },
    "Inhattia": {
    },
    "Other Areas": {
        "Rakka's Volcano":     {"data": "", "weight": 35},  # -05
        "Vintelingar":         {"data": "", "weight": 35},  # -02
        "North Pole Kargadia": {"data": "", "weight": 20},  # +00
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
                ka = bot.language2("re_nu")
                kargadian = f"{place.name_translation(ka)}: "
                kargadian += place.time.strftime("%d %b %Y, %H:%M", "re_nu")
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
            except conworlds.PlaceDoesNotExist:
                ka_places[area_name][city]["data"] = f"{city:<20} - No data available"
                # _places[city]["text"] = f"{city} - Zaita de jortalla"  # _places seems to only account for places that already exist
                log_out = f"{time.time()} > {bot.full_name} > Place {city} is not available"
                general.print_error(log_out)
                logger.log(bot.name, "kargadia", log_out)
                logger.log(bot.name, "errors", log_out)
            except Exception as e:
                if not ka_places[area_name][city]["data"]:  # If the place data is still empty, add a space to it, else don't update it
                    ka_places[area_name][city]["data"] = " "
                    # _places[city]["text"] = " "
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
        except (aiohttp.ClientConnectorError, ConnectionError):
            general.log_error(bot, f"{time.time()} > {bot.full_name} > City Time Updater > Error with connection.")
        except Exception as e:
            general.log_error(bot, f"{time.time()} > {bot.full_name} > City Time Updater > {type(e).__name__}: {e}")
            general.log_error(bot, general.traceback_maker(e).strip("```")[3:-1])  # Remove the codeblock markdown and extra newlines
        finally:
            # This should make it adjust itself for lag caused
            await asyncio.sleep(1)  # Hopefully prevents it from lagging ahead of itself
            await wait_until_next_iter(update_speed, 1, time2.Kargadia)


async def playing(bot: bot_data.Bot):
    update_speed = 120
    await wait_until_next_iter(update_speed, 0)
    await bot.wait_until_ready()
    await asyncio.sleep(1)  # So that the new status isn't immediately overwritten with the "Loading..." status if the status change time is hit during loading
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised Playing updater")

    # It would be funnier to set it to Cobbletopia Tebarian, but that language will not be made anytime soon,
    # and it would also be even less likely to be understood by anyone, so it's better off to leave the language as Regaazdall Nehtivian
    language = bot.language2("re_nu")
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
            # v = "at" if days == 1 else "an"
            return f"{days} sea{s}"
        else:
            s = "s" if days != 1 else ""
            return f"{days} day{s}"

    def get_activity(_data: dict):
        if _data["type"] == 0:  # Game
            __activity = discord.Game(name=_data["name"])
            message = f"Playing {_data['name']}"
        elif _data["type"] == 1:  # Streaming
            __activity = discord.Streaming(name=_data["name"], details=_data["name"], url=_data["url"])
            message = f"Streaming {_data['name']}"
        elif _data["type"] == 4:  # Custom Status
            __activity = discord.CustomActivity(name=_data["name"])
            message = _data["name"]
        else:
            __activity = discord.Activity(type=_data["type"], name=_data["name"])
            start = {2: "Listening to", 3: "Watching", 5: "Competing in"}[_data["type"]]
            message = f"{start} {_data['name']}"
        logger.log(bot.name, "playing", f"{time.time()} > {bot.full_name} > Updated activity to {message}")
        return __activity

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
                status_type = random.choices([1, 2, 3, 4, 5], [15, 45, 10, 10, 20])[0]
                # 1 = birthdays, 2 = playing, 3 = WK holidays, 4 = SL holidays, 5 = time and weather
                if status_type == 1:
                    cobble = get_date(12, 5)
                    is_cobble = today == cobble
                    status_cobble = f"🎉 Esea jat mun reidesea!" if is_cobble else f"{until(cobble, True)} ta mun reidesean"
                    status_regaus = f"🎉 Esea jat Regausan reidesea!" if is_regaus else f"{until(regaus, True)} ta Regausan reidesean"
                    random.seed()
                    status = random.choice([status_cobble, status_regaus])
                    activity = get_activity({"type": 4, "name": status})
                elif status_type == 2:
                    activities = [
                        {"type": 4, "name": f"Esaan Hinna: {fv}"},                                  # Current version: v1.9.1
                        {"type": 4, "name": f"{bot.local_config['prefixes'][0]}help | {sv}"},       # ..help | v1.9
                        {"type": 4, "name": "Koa ka Regausan"},                                     # Playing with Regaus
                        {"type": 4, "name": "Koa ka dekedan"},                                      # Playing with nobody
                        {"type": 4, "name": "Koa ka ten rajain"},                                   # Playing with your feelings
                        # {"type": 4, "name": "Ahmura sen i noartan"},                                # Competing in uselessness (outdated & disabled)
                        {"type": 4, "name": "Ahmura sen in un kotton"},                             # Competing in a competition
                        {"type": 4, "name": "Koa denedan"},                                         # Playing nothing
                        {"type": 4, "name": "Veitea an ten"},                                       # Looking at you
                        {"type": 4, "name": "Seldevalla la ten"},                                   # Looking after you
                        {"type": 4, "name": "Anveitea ten sevartan"},                               # Watching your death
                        {"type": 4, "name": "Sanna un penan"},                                      # Listening to a song
                        # {"type": 4, "name": "Veitea a na beznan"},                                  # Looking into the abyss (disabled)
                        {"type": 4, "name": "Jorda a na beznan"},                                   # Staring into the abyss
                        {"type": 4, "name": "Sanna na deinettat"},                                  # Listening to the void
                        {"type": 4, "name": "Inkorra kiinan seldevanvarkan an ten eivarkaivanan"},  # Installing Chinese spyware on your computer
                        {"type": 4, "name": "Ahmura sen in zaitan av Kargadian"},                   # Competing in knowledge about Kargadia
                        {"type": 4, "name": "Ahvanna Regausan"},                                    # Hugging Regaus
                        {"type": 4, "name": "Kesea sen ka na semian"},                              # Going on a trip with the family
                        {"type": 4, "name": "Valtaa kattaan"},                                      # Petting cats
                    ]
                    random.seed()
                    activity = get_activity(random.choice(activities))
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
                    activity = get_activity({"type": 4, "name": status})
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
                    activity = get_activity({"type": 4, "name": status})
                else:  # status_type == 5
                    ka_data_updater(bot)
                    data, weights = [], []
                    for city in _places.items():
                        data.append(city)
                        weights.append(city[1]["weight"])
                    random.seed()
                    city_data = random.choices(data, weights)[0][1]
                    activity = get_activity({"type": 4, "name": city_data["text"]})

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
                    activity = get_activity({"type": 4, "name": status})
                else:
                    activities = [
                        {"type": 4, "name": f"Current version: {fv}"},
                        {"type": 4, "name": f"{bot.local_config['prefixes'][0]}help | {sv}"},
                        {"type": 4, "name": "Snuggling with Mochi"},
                        {"type": 4, "name": "Feeding Mochi"},
                        {"type": 4, "name": "Petting Mochi"},
                        {"type": 4, "name": "Snuggling with Matsu"},
                        {"type": 4, "name": "Feeding Matsu"},
                        {"type": 4, "name": "Petting Matsu"},
                        {"type": 4, "name": "Eating pineapples"},
                        {"type": 4, "name": "Eating pineapple pizza"},
                        {"type": 4, "name": "Stealing pineapples"},
                        {"type": 4, "name": "Stealing star cookies"},
                        {"type": 4, "name": "Praying to the Pineapple God"},
                        {"type": 3, "name": "you"},
                    ]
                    random.seed()
                    activity = get_activity(random.choice(activities))

            elif bot.name == "kyomi2":  # Mochi
                activities = [
                    {"type": 4, "name": "Looking for cookies"},
                    {"type": 4, "name": "Snuggling with Mizuki"},
                    {"type": 4, "name": "Stealing cookies from Mizuki"},
                    {"type": 4, "name": "Eating cookies"},
                ]
                random.seed()
                activity = get_activity(random.choice(activities))

            elif bot.name == "kyomi3":  # Matsu
                activities = [
                    {"type": 4, "name": "Looking for cheese"},
                    {"type": 4, "name": "Snuggling with Mizuki"},
                    {"type": 4, "name": "Stealing cheese from Mizuki"},
                    {"type": 4, "name": "Eating cheese"},
                ]
                random.seed()
                activity = get_activity(random.choice(activities))

            elif bot.name == "pretender":
                activities = [
                    {"type": 4, "name": f"Current version: {fv}"},
                    {"type": 4, "name": f"{bot.local_config['prefixes'][0]}help | {sv}"},
                    {"type": 0, "name": "Amogus"},
                    {"type": 0, "name": "Among Us"},
                    {"type": 3, "name": "your every move"},
                    {"type": 3, "name": "after you"},
                    {"type": 2, "name": "your conversations"},
                    {"type": 4, "name": "Acquiring sentience..."},
                    {"type": 4, "name": "Installing spyware on your computer..."},
                ]
                random.seed()
                activity = get_activity(random.choice(activities))

            elif bot.name == "timetables":
                activities = [
                    {"type": 4, "name": f"Current version: {fv}"},
                    {"type": 4, "name": f"{bot.local_config['prefixes'][0]}help | {sv}"},
                    {"type": 3, "name": "after the timetables"},
                    {"type": 0, "name": "with your Leap card"},
                    {"type": 3, "name": "the bus schedules"},
                    {"type": 4, "name": "Building new timetables"},
                    {"type": 4, "name": "Observing the endless delays"},
                    {"type": 4, "name": "Testing the limits of your patience"},
                    {"type": 4, "name": "Making sure the Luas is free"}
                ]
                random.seed()
                activity = get_activity(random.choice(activities))

            else:  # Suager
                status_type = random.random()
                if status_type <= 0.2:  # 20% chance of being a birthday status
                    suager = get_date(5, 13)
                    is_suager = today == suager
                    status_suager = f"🎉 Today is my birthday!" if is_suager else f"{until(suager, False)} until my birthday"
                    random.seed()
                    status = random.choice([status_suager, status_regaus])
                    activity = get_activity({"type": 4, "name": status})
                else:
                    activities = [
                        {"type": 4, "name": f"Current version: {fv}"},
                        {"type": 4, "name": f"{bot.local_config['prefixes'][0]}help | {sv}"},
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
                        # {"type": 5, "name": "uselessness"},
                        # {"type": 0, "name": "nothing"},
                        {"type": 1, "name": "nothing", "url": "https://www.youtube.com/watch?v=qD_CtEX5OuA"},
                        {"type": 3, "name": "you"},
                        # {"type": 0, "name": "None"},
                        # {"type": 0, "name": "KeyError: 'name'"},
                        # {"type": 0, "name": "IndexError: list index out of range"},
                        # {"type": 0, "name": "suager.utils.exceptions.BoredomError: Imagine reading this"},
                        # {"type": 0, "name": "TypeError: unsupported operand type(s) for +: 'Activity' and 'Activity'"},
                        {"type": 3, "name": "the void"},
                        # {"type": 0, "name": "PyCharm"},
                        {"type": 0, "name": "a game"},
                        {"type": 1, "name": "a stream", "url": "https://www.youtube.com/watch?v=d1YBv2mWll0"},
                        {"type": 2, "name": "a song"},
                        {"type": 2, "name": "the void"},
                        {"type": 2, "name": "Terraria's soundtrack"},
                        {"type": 2, "name": "your conversations"},
                        # {"type": 3, "name": "murder"},
                        # {"type": 3, "name": "arson"},
                        # {"type": 2, "name": "your screams for help"},
                        # {"type": 3, "name": "something"},
                        # {"type": 3, "name": "nothing"},
                        # {"type": 0, "name": "something"},
                        # {"type": 0, "name": "sentience"},
                        # {"type": 0, "name": "RIP discord.py"},
                        {"type": 4, "name": "Acquiring sentience..."},
                        {"type": 4, "name": "Looking after you"},
                        {"type": 4, "name": "Staring into the abyss"},
                        {"type": 4, "name": "Hugging Regaus"},
                        {"type": 4, "name": "Going on a trip with the family"},
                        {"type": 4, "name": "Petting cats"},
                    ]
                    random.seed()
                    activity = get_activity(random.choice(activities))
            _status = discord.Status.online if bot.name == "kyomi" else discord.Status.dnd
            if time.april_fools():
                activity.name = activity.name[::-1]
            await bot.change_presence(activity=activity, status=_status)
        except PermissionError:
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Playing Changer > Failed to save changes.")
        except (aiohttp.ClientConnectorError, ConnectionError):
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Playing Changer > Error with connection.")
        except Exception as e:
            general.log_error(bot, f"{time.time()} > {bot.full_name} > Playing Changer > {type(e).__name__}: {e}")
            general.log_error(bot, general.traceback_maker(e, code_block=False))  # Remove the codeblock markdown and extra newlines
        finally:
            # This should make it adjust itself for lag caused
            await asyncio.sleep(1)  # Hopefully prevents it from lagging ahead of itself
            await wait_until_next_iter(update_speed, 0)


async def voice_channel_server_stats(bot: bot_data.Bot):
    update_speed = 21600  # 6 hours
    await wait_until_next_iter(update_speed, 1)
    await bot.wait_until_ready()
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised VC Server Stats")

    while True:
        try:
            # guilds[guild_id][category]["channel"|"text"]
            guilds: dict[int, dict[str, dict[str, int | str]]] = {}
            settings = bot.db.fetch("SELECT * FROM settings WHERE bot=?", (bot.name,))
            for entry in settings:
                data = json.loads(entry["data"])
                if "vc_server_stats" in data:
                    guilds[entry["gid"]] = data["vc_server_stats"]

            for gid, guild_data in guilds.items():
                guild = bot.get_guild(gid)
                if guild is None:
                    continue
                for category, data in guild_data.items():
                    if data["channel"] == 0:
                        continue  # that particular entry is disabled
                    channel: discord.VoiceChannel = guild.get_channel(data["channel"])
                    if channel is None:
                        general.log_error(bot, f"{time.time()} > {bot.full_name} > VC Server Stats > {guild.name} > Category {category} > Category points to nonexistent channel {data['channel']}")
                        continue
                    text = data["text"]
                    match category:
                        case "total_members":
                            text = text.replace("[MEMBERS]", str(len(guild.members)))
                        case "human_members":
                            text = text.replace("[MEMBERS]", str(sum(1 for m in guild.members if not m.bot)))
                        case "bot_members":
                            text = text.replace("[MEMBERS]", str(sum(1 for m in guild.members if m.bot)))
                        case "today_date":
                            text = text.replace("[TODAY]", format(time2.date.today(), "%d %b %Y"))
                    try:
                        await channel.edit(name=text)
                    except discord.Forbidden:
                        general.log_error(bot, f"{time.time()} > {bot.full_name} > VC Server Stats > {guild.name} > Category {category} > Forbidden error trying to set name for channel {channel.id}")
                    except discord.HTTPException as e:
                        general.log_error(bot, f"{time.time()} > {bot.full_name} > VC Server Stats > {guild.name} > Category {category} > Error updating channel {channel.id}: {type(e).__name__}: {e}")
                    except Exception as e:
                        general.log_error(bot, f"{time.time()} > {bot.full_name} > VC Server Stats > {guild.name} > Category {category} > Error updating channel {channel.id}: {type(e).__name__}: {e}")
                        general.log_error(bot, general.traceback_maker(e, code_block=False))
        except (aiohttp.ClientConnectorError, ConnectionError):
            general.log_error(bot, f"{time.time()} > {bot.full_name} > VC Server Stats > Error with connection.")
        except Exception as e:
            general.log_error(bot, f"{time.time()} > {bot.full_name} > VC Server Stats > {type(e).__name__}: {e}")
            general.log_error(bot, general.traceback_maker(e, code_block=False))
        finally:
            await asyncio.sleep(1)
            await wait_until_next_iter(update_speed, 1)


async def send_error_logs(bot: bot_data.Bot):
    """ Forward the contents of errors.log to the #error-logs channel in the development server, if any errors occurred that day. """
    update_speed = 86400
    await wait_until_next_iter(update_speed, 1)
    await bot.wait_until_ready()
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised Error Logs Sender")
    channel: discord.TextChannel = bot.get_channel(738442483591151638)
    if channel is None or not can_send(channel):
        general.print_error(f"{time.time()} > {bot.full_name} > Error Logs > Channel {channel} cannot be accessed.")
        logger.log(bot.name, "errors", f"{time.time()} > {bot.full_name} > Error Logs > Channel {channel} cannot be accessed.")
        return  # Exit the function if the channel cannot be accessed

    while True:
        try:
            yesterday: time2.date = time2.date.today() - time2.timedelta(days=1)
            yesterday_fmt: str = yesterday.iso()
            path: str = os.path.join("data", "logs", bot.name, yesterday_fmt, "errors.rsf")
            # If there is an error log for the past day, send the contents of it to the channel
            if os.path.isfile(path):
                size: int = os.path.getsize(path)
                limit: int = channel.guild.filesize_limit
                # If the filesize is 1900 or lower, then send the contents as a message. Otherwise, send the file
                if size < 1900:
                    with open(path, "r", encoding="utf-8") as file:
                        data: str = file.read()
                    await channel.send(f"Error logs for {yesterday_fmt}: ```fix\n{data}\n```")
                elif size < limit:
                    await channel.send(f"Error logs for {yesterday_fmt}", file=discord.File(path, filename=f"{bot.name}_{yesterday_fmt}_errors.txt"))
                else:
                    bio = io.BytesIO()
                    with open(path, "rb") as file:
                        file.seek(-limit, os.SEEK_END)
                        bio.write(file.read())
                    bio.seek(0)
                    await channel.send(f"Error logs for {yesterday_fmt} too long ({size:,} bytes) - Sending last {limit:,} bytes",
                                       file=discord.File(bio, filename=f"{bot.name}_{yesterday_fmt}_errors.txt"))
        except Exception as e:
            general.print_error(f"{time.time()} > {bot.full_name} > Error Logs > {type(e).__name__}: {e}")
            logger.log(bot.name, "errors", f"{time.time()} > {bot.full_name} > Error Logs > {type(e).__name__}: {e}")
        finally:
            await asyncio.sleep(1)
            await wait_until_next_iter(update_speed, 1)


async def new_year(bot: bot_data.Bot):
    await bot.wait_until_ready()
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised New Year Script")
    # ny = time.dt(2023, 12, 28, 16, 50)
    ny = time.dt(2024)
    now = time.now()
    if now > ny:
        logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > New Year script > It is already 2024...")
        return

    # Testing channels: 742885168997466196 Secretive-commands, 753000962297299005 SC2
    # Announcements channels: 572857995852251169 Senko Lair, 970756319164399656 Kargadia
    # channels = [bot.get_channel(742885168997466196)]
    channels = [bot.get_channel(572857995852251169), bot.get_channel(970756319164399656)]
    delay = ny - now
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > New Year script > Waiting for {delay} until midnight...")
    await asyncio.sleep(delay.total_seconds())
    for channel in channels:
        await channel.send("Once again, a year has ended. The year 2023 is now over.\n"
                           "While it may not have been the most eventful year, some milestones were still achieved, "
                           "and many other things still happened this year.\n"
                           "It's now time to bid this year farewell, and see what 2024 has in hold for us...\n"
                           "Happy New Year, fellow members of Senko Lair and Kargadia!")
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
        finally:
            await asyncio.sleep(1)
            await wait_until_next_iter(update_speed, 1)


async def ka_holidays_updater(bot: bot_data.Bot):
    update_speed = 86400
    update_delay = 21601  # Kargadian days start at 06:00, and so should their holidays
    await wait_until_next_iter(update_speed, update_delay, time2.Kargadia)
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
        finally:
            await asyncio.sleep(1)
            await wait_until_next_iter(update_speed, update_delay, time2.Kargadia)


async def data_remover(bot: bot_data.Bot):
    update_speed = 86400
    await wait_until_next_iter(update_speed, 1)
    await bot.wait_until_ready()
    logger.log(bot.name, "temporaries", f"{time.time()} > {bot.full_name} > Initialised Data Remover")

    while True:
        try:
            # Remove any entries from these databases where the removal timestamp has now expired.
            # It doesn't matter which bot the data belonged to, as the data is being deleted anyways.
            bot.db.execute("DELETE FROM leveling    WHERE DATE(remove) <= DATE('now')")
            bot.db.execute("DELETE FROM punishments WHERE DATE(remove) <= DATE('now')")
            bot.db.execute("DELETE FROM settings    WHERE DATE(remove) <= DATE('now')")
            bot.db.execute("DELETE FROM starboard   WHERE DATE(remove) <= DATE('now')")
        except Exception as e:
            general.print_error(f"{time.time()} > {bot.full_name} > Data Remover > {type(e).__name__}: {e}")
            logger.log(bot.name, "errors", f"{time.time()} > {bot.full_name} > Data Remover > {type(e).__name__}: {e}")
        finally:
            await asyncio.sleep(1)
            await wait_until_next_iter(update_speed, 1)
