import asyncio
import json
import random

import aiohttp
import discord

from cobble.utils import tbl
from core.utils import bot_data, general, http, logger, time
from languages import langs
from suager.cogs.birthdays import Ctx
from suager.utils import lists


async def temporaries(bot: bot_data.Bot):
    """ Handle reminders and mutes """
    await bot.wait_until_ready()
    # print(f"{time.time()} > Initialised Temporaries handler")
    while True:
        expired = bot.db.fetch("SELECT * FROM temporary WHERE DATETIME(expiry) < DATETIME('now') AND handled=0", ())
        bot.db.execute("DELETE FROM temporary WHERE handled=1", ())
        if expired:
            # print(expired)
            for entry in expired:
                entry_id = entry["entry_id"]
                if entry["type"] == "reminder":
                    user: discord.User = bot.get_user(entry["uid"])
                    expiry = langs.gts(entry["expiry"], "en", True, True, False, True, False)
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
                                            await member.remove_roles(mute_role, reason=f"[Suager Auto-Unmute] Punishment expired")
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
                        general.print_error(f"{time.time()} > User ID {user} not found! Skipping...")
                        logger.log(bot.name, "temporaries", f"{time.time()} > Still could not find user for reminder for {expiry} with Entry ID {entry_id}! "
                                                            f"Deleting reminder...")
                except Exception as e:
                    general.print_error(f"{time.time()} > Reminder {entry_id} error: {e} | Deleting...")
                    logger.log(bot.name, "temporaries", f"{time.time()} > Reminder {entry_id} error: {e} | Deleting...")
            if entry["type"] == "mute":
                guild: discord.Guild = bot.get_guild(entry["gid"])
                if guild is None:
                    general.print_error(f"{time.time()} > Mute entry ID {entry_id} - Guild not found! Putting mute to error list...")
                    logger.log(bot.name, "temporaries", f"{time.time()} > Mute entry ID {entry_id} - Guild not found! Putting mute to error list...")
                else:
                    _data = bot.db.fetchrow("SELECT * FROM settings WHERE gid=?", (guild.id,))
                    if not _data:
                        general.print_error(f"{time.time()} > Mute entry ID {entry_id} - Guild settings not found! Putting mute to error list...")
                        logger.log(bot.name, "temporaries", f"{time.time()} > Mute entry ID {entry_id} - Guild settings not found! "
                                                            f"Putting mute to error list...")
                    else:
                        data = json.loads(_data["data"])
                        try:
                            mute_role_id = data["mute_role"]
                        except KeyError:
                            general.print_error(f"{time.time()} > Mute entry ID {entry_id} - Guild has no mute role set! Putting mute to error list...")
                            logger.log(bot.name, "temporaries", f"{time.time()} > Mute entry ID {entry_id} - Guild has no mute role set! "
                                                                f"Putting mute to error list...")
                        else:
                            mute_role = guild.get_role(mute_role_id)
                            if not mute_role:
                                general.print_error(f"{time.time()} > Mute entry ID {entry_id} - Mute role not found! Putting mute to error list...")
                                logger.log(bot.name, "temporaries", f"{time.time()} > Mute entry ID {entry_id} - Mute role not found! "
                                                                    f"Putting mute to error list...")
                            else:
                                member: discord.Member = guild.get_member(entry["uid"])
                                if not member:
                                    general.print_error(f"{time.time()} > Mute entry ID {entry_id} - Member not found! Putting mute to error list...")
                                    logger.log(bot.name, "temporaries", f"{time.time()} > Mute entry ID {entry_id} - Member not found! "
                                                                        f"Putting mute to error list...")
                                else:
                                    try:
                                        await member.remove_roles(mute_role, reason=f"[Suager Temporary Mutes] Punishment expired")
                                        logger.log(bot.name, "temporaries", f"{time.time()} > Successfully unmuted the user {member} ({member.id}) from "
                                                                            f"guild {guild} ({entry_id})")
                                    except Exception as e:
                                        general.print_error(f"{time.time()} > Mute {entry_id} error: {e}")
                                        logger.log(bot.name, "temporaries", f"{time.time()} > Mute {entry_id} error: {e}")
            bot.db.execute("UPDATE temporary SET handled=1 WHERE entry_id=?", (entry_id,))


bd_config = {  # Birthday data: {Guild: [BirthdayChannel, BirthdayRole]}
    568148147457490954: [568148147457490958, 663661621448802304],
    706574018928443442: [715620849167761458, 720780796293677109],
    738425418637639775: [738425419325243424, 748647340423905420]
}


async def birthdays(bot: bot_data.Bot):
    """ Handle birthdays """
    await bot.wait_until_ready()
    # print(f"{time.time()} > Initialised Birthdays handler")
    _guilds, _channels, _roles = [], [], []
    for guild, data in bd_config.items():
        _guilds.append(guild)
        _channels.append(data[0])
        _roles.append(data[1])
    guilds = [bot.get_guild(guild) for guild in _guilds]
    channels = [bot.get_channel(cid) for cid in _channels]
    roles = [discord.Object(id=rid) for rid in _roles]
    while True:
        birthday_today = bot.db.fetch("SELECT * FROM birthdays WHERE has_role=0 AND strftime('%m-%d', birthday) = strftime('%m-%d', 'now')")
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
                                print(f"{time.time()} > {guild.name} > Gave birthday role to {user.name}")
                    except Exception as e:
                        print(f"{time.time()} > Birthdays Handler > {e}")
                if dm:
                    try:
                        user = bot.get_user(person["uid"])
                        if user is not None:
                            await user.send(langs.gls("birthdays_message", "en", user.mention))
                    except Exception as e:
                        print(f"{time.time()} > Birthdays Handler > {e}")
                bot.db.execute("UPDATE birthdays SET has_role=1 WHERE uid=?", (person["uid"],))
        birthday_over = bot.db.fetch("SELECT * FROM birthdays WHERE has_role=1 AND strftime('%m-%d', birthday) != strftime('%m-%d', 'now')")
        for person in birthday_over:
            bot.db.execute("UPDATE birthdays SET has_role=0 WHERE uid=?", (person["uid"],))
            for i in range(len(guilds)):
                try:
                    guild = guilds[i]
                    if guild is not None:
                        user = guild.get_member(person["uid"])
                        if user is not None:
                            await user.remove_roles(roles[i], reason=f"It is no longer {user}'s birthday...")
                            print(f"{time.time()} > {guild.name} > Removed birthday role from {user.name}")
                except Exception as e:
                    print(f"{time.time()} > Birthdays Handler > {e}")
        await asyncio.sleep(5)


async def playing(bot: bot_data.Bot):
    await bot.wait_until_ready()
    # print(f"{time.time()} > Initialised Playing changer ({bot.local_config['name']})")
    while True:
        try:
            log = bot.local_config["logs"]
            # plays = self.local_config["playing"]
            version = general.get_version()[bot.name]
            fv, sv = f"v{version['version']}", f"v{version['short_version']}"
            plays = {
                "cobble": [
                    {"type": 0, "name": fv},
                    {"type": 1, "name": "nothing", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
                    {"type": 0, "name": "with Regaus"},
                    {"type": 0, "name": "without you"},
                    {"type": 0, "name": "with nobody"},
                    {"type": 0, "name": "with your feelings"},
                    {"type": 0, "name": f"{bot.local_config['prefixes'][0]}help | {sv}"},
                    {"type": 5, "name": "uselessness"},
                    {"type": 0, "name": "nothing"},
                    {"type": 3, "name": "you"},
                    {"type": 2, "name": "a song"},
                    {"type": 3, "name": "the void"},
                ],
                "suager": [
                    {"type": 0, "name": fv},
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
                    {"type": 0, "name": f"{bot.local_config['prefixes'][0]}help | {sv}"},
                    {"type": 5, "name": "uselessness"},
                    {"type": 0, "name": "nothing"},
                    {"type": 1, "name": "nothing", "url": "https://www.youtube.com/watch?v=qD_CtEX5OuA"},
                    {"type": 3, "name": "you"},
                    # {"type": 0, "name": "None"},
                    # {"type": 0, "name": "KeyError: 'name'"},
                    # {"type": 0, "name": "IndexError: list index out of range"},
                    # {"type": 0, "name": "suager.utils.exceptions.BoredomError: Imagine reading this"},
                    # {"type": 0, "name": "TypeError: unsupported operand type(s) for +: 'Activity' and 'Activity'"},
                    {"type": 2, "name": "a song"},
                    # {"type": 2, "name": "10 Hours of Nothing ft. Nobody (Non-Existent Remix by Negative Zero)"},
                    {"type": 3, "name": "the Void"},
                    # {"type": 5, "name": "Minecraft"},
                    # {"type": 0, "name": "Minecraft"},
                    # {"type": 0, "name": "Minceraft"},
                    # {"type": 1, "name": "Minecraft", "url": "https://www.youtube.com/watch?v=d1YBv2mWll0"},
                    # {"type": 0, "name": "Terraria"},
                    # {"type": 1, "name": "Terraria", "url": "https://www.youtube.com/watch?v=d1YBv2mWll0"},
                    # {"type": 0, "name": "Grand Theft Auto V"},
                    {"type": 0, "name": "PyCharm"},
                    {"type": 0, "name": "a game"},
                    {"type": 1, "name": "a stream", "url": "https://www.youtube.com/watch?v=d1YBv2mWll0"},
                    {"type": 2, "name": "the void"},
                    {"type": 2, "name": "Terraria's soundtrack"},
                    {"type": 2, "name": "your conversations"},
                    {"type": 3, "name": "murder"},
                    {"type": 3, "name": "arson"},
                    {"type": 2, "name": "your screams for help"},
                    {"type": 3, "name": "something"},
                    {"type": 3, "name": "nothing"},
                    {"type": 0, "name": "something"},
                    {"type": 0, "name": "sentience"}
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
        await asyncio.sleep(300)


async def avatars(bot: bot_data.Bot):
    await bot.wait_until_ready()
    # print(f"{time.time()} > Initialised Avatar changer")
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


async def tbl_seasons(bot: bot_data.Bot):
    _season = tbl.get_season()
    await bot.wait_until_ready()
    # print(f"{time.time()} > Initialised TBL Seasons Updater")
    while True:
        season = tbl.get_season()
        if season != _season:
            channel = bot.get_channel(819223338844946522)
            all_players = bot.db.fetch("SELECT * FROM tbl_player")
            old_points = []
            for player in all_players:
                old_points.append({"name": f"{player['name']}#{player['disc']:04d}", "points": player["league_points"], 'id': player['uid']})
            old_points.sort(key=lambda x: x["points"], reverse=True)
            top_5 = ""
            emotes = ["🥇", "🥈", "🥉", "🏆", "🏆", "🏆", "🏆", "🏆", "🏆", "🏆"]
            prize = [250, 225, 200, 175, 150, 125, 100, 75, 50, 25]
            prizes = [f"{i} Coins" for i in prize]
            # prizes = [langs.plural(i, "tbl_coins") for i in prize]
            for place, user in enumerate(old_points[:10], start=1):
                emote = emotes[place - 1]
                top_5 += f"\n{emote} **#{place}: {user['name']}** at **{user['points']:,} League Points** - Prize: **{prizes[place - 1]}**"
                bot.db.execute("UPDATE tbl_player SET coins=coins+? WHERE uid=?", (prize[place - 1], user["id"]))
            bot.db.execute("UPDATE tbl_player SET araksat=araksat+(league_points/5), league_points=league_points/10, coins=coins+50")
            await general.send(f"Season {_season} has now ended! Here are the Top 5 people of the past season:{top_5}", channel)
            # 1/10 of everyone's League Points will carry over to the next season, and some will be converted to extra Araksat.
            # Everyone gets 50 coins. The top 10 will also receive some extra coins.
            _season = season
        await asyncio.sleep(1800)
