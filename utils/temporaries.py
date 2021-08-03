import asyncio
import json
import random
from datetime import date, timedelta

import aiohttp
import discord

from utils import bot_data, general, http, lists, logger, time


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


async def playing(bot: bot_data.Bot):
    await bot.wait_until_ready()
    update_speed = 150

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

            def until(when: date, lang: str = "en"):
                days = (when - today).days
                if lang == "rsl-1":
                    s = "in" if days != 1 else ""
                    v = "t" if days == 1 else "n"
                    return f"{days} sea{s} astalla{v}"
                else:
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
            status_regaus2 = f"🎉 Esea jat Regaus'ta reidesea!" if is_regaus else f"{until(regaus, 'rsl-1')} Regaus'tat reideseat"
            status_suager = f"🎉 Today is my birthday!" if is_suager else f"{until(suager)} until my birthday"
            status_cobble = f"🎉 Esea jat reideseani!" if is_cobble else f"{until(cobble, 'rsl-1')} mun reideseat"
            status_kyomi = f"🎉 Today is Kyomi's birthday!" if is_kyomi else f"{until(kyomi)} until Kyomi's birthday"
            status_blucy = f"🎉 Today is Blucy's birthday!" if is_blucy else f"{until(blucy)} until Blucy's birthday"
            status_mizuki = f"🎉 Today is my birthday!" if is_mizuki else f"{until(mizuki)} until my birthday"
            plays = {
                "cobble": [
                    {"type": 0, "name": fv},
                    {"type": 0, "name": f"{bot.local_config['prefixes'][0]}help | {sv}"},
                    # {"type": 1, "name": "denedaa", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
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
                    {"type": 0, "name": status_regaus2},
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
                    {"type": 0, "name": "Petting Mochi"},
                    {"type": 0, "name": "Eating pineapples"},
                    {"type": 0, "name": "Eating pineapple pizza"},
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
            name = _activity["name"]
            status = {
                0: "Playing",
                1: "Streaming",
                2: "Listening to",
                3: "Watching",
                5: "Competing in"
            }.get(_activity["type"], "Undefined")
            logger.log(bot.name, "playing", f"{time.time()} > {bot.full_name} > Updated activity to {status} {name}")
        except PermissionError:
            general.print_error(f"{time.time()} > {bot.full_name} > Playing Changer > Failed to save changes.")
        except aiohttp.ClientConnectorError:
            general.print_error(f"{time.time()} > {bot.full_name} > Playing Changer > The bot tried to do something while disconnected.")
        except Exception as e:
            general.print_error(f"{time.time()} > {bot.full_name} > Playing Changer > {type(e).__name__}: {e}")
        await asyncio.sleep(update_speed)


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


async def vote_bans(bot: bot_data.Bot):
    await bot.wait_until_ready()

    print(f"{time.time()} > {bot.full_name} > Initialised Vote Bans")
    guild: discord.Guild = bot.get_guild(869975256566210641)  # Nuriki's Anarchy Server
    channel: discord.TextChannel = guild.get_channel(871811287166898187)  # Trials channel
    while True:
        expired = bot.db.fetch("SELECT * FROM vote_bans WHERE DATETIME(expiry) < DATETIME('now')", ())
        for entry in expired:
            upvotes, downvotes = len(json.loads(entry["upvotes"])), len(json.loads(entry["downvotes"]))
            user: discord.User = await bot.fetch_user(entry["uid"])
            votes = upvotes - downvotes
            acceptance = upvotes / (upvotes + downvotes)
            if votes >= 3 and acceptance >= 0.6:
                try:
                    await guild.ban(user, reason=general.reason(guild.me, f"Vote-banned ({votes} votes, {acceptance:.0%} upvoted)"), delete_message_days=0)
                except discord.Forbidden:
                    general.print_error(f"Failed to ban {user} - Missing permissions")
                    if channel is not None:
                        await general.send(f"Failed to ban {user} - Missing permissions", channel)
                if channel is not None:
                    await general.send(f"The vote has ended: {user} has been banned. ({votes} votes, {acceptance:.0%} upvoted)", channel)
            else:
                member = guild.get_member(entry["uid"])
                if member is not None:
                    await member.remove_roles(guild.get_role(870338399922446336), reason="Trial has ended")  # Remove the On Trial role
                    await member.add_roles(guild.get_role(869975498799845406), reason="Trial has ended")  # Give the Anarchists role
                if channel is not None:
                    await general.send(f"The vote has ended: {user} has __not__ been banned. ({votes} votes, {acceptance:.0%} upvoted)\n"
                                       f"Must be at least 3 votes and 60% upvotes to ban.", channel)
            bot.db.execute("DELETE FROM vote_bans WHERE uid=?", (entry["uid"],))
        await asyncio.sleep(1)
