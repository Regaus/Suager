import asyncio
import json
import random

from core.utils import time, general
from languages import langs
from suager.utils import tbl_data, ss23

sel_player = f"SELECT * FROM tbl_player WHERE uid=?"
sel_clan = f"SELECT * FROM tbl_clan WHERE gid=?"


def get_player(user, db, now_ts: float):
    player = db.fetchrow(sel_player, (user.id,))
    if not player:
        return {
            "level": 1,
            "xp": 0,
            "nuts": 150,
            "coins": 5,
            "sh_xp": 0,
            "energy": 300,
            "time": now_ts,
            "points": 0,
            "runs": 0,
            "location": 0
        }, False
    return player, True


def get_clan(guild, db):
    clan = db.fetchrow(sel_clan, (guild.id,))
    if not clan:
        return {
            "level": 1,
            "xp": 0,
            "temples": json.dumps([{"id": 0, "expiry": 0}] * 3),
            "temple_levels": json.dumps([1] * len(tbl_data.totems)),
            "nuts": 0,
            "coins": 0,
            "upgrade_points": 0,
            "usage": False
        }, False
    return clan, True


async def tbl_game(ctx, db):
    locale = langs.gl(ctx.guild, db)
    now_ts = time.now_ts()
    player, wp = get_player(ctx.author, db, now_ts)
    clan, wc = get_clan(ctx.guild, db)
    if wc:
        if clan["usage"]:
            return await general.send(langs.gls("tbl_game_usage", locale, ctx.guild.name), ctx.channel)
            # return await general.send("It seems that TBL is currently running in this server, please try again later.", ctx.channel)
        db.execute("UPDATE tbl_clan SET usage=1 WHERE gid=?", (ctx.guild.id,))
    try:
        lid = player["location"]
        level = player['level']
        loc = get_location(lid, level)
        stuff = f"{ctx.author.name} > TBL Initiated"
        energy, regen_time = player["energy"], player["time"]
        energy, regen_time = regen_energy(energy, regen_time, level, int(now_ts))
        if energy < loc["energy"]:
            return await general.send(langs.gls("tbl_game_energy", locale, langs.gns(energy, locale), langs.gns(loc["energy"], locale)), ctx.channel)
            # return await general.send(f"You don't have enough energy right now (**{energy}/{loc['energy']}**)", ctx.channel)
        message = await general.send(stuff, ctx.channel)
        await asyncio.sleep(1)
        runs = player["runs"]
        new_level = player["level"]
        _runs = 0
        _act = get_activity(loc['activity'])
        people = random.randint(int(_act * 0.9), int(_act * 1.1))
        # if act < 100:
        #     people = 15
        # elif 100 <= act < 1000:
        #     people = int(act / random.uniform(3, 5))
        # else:
        #     people = int(act / random.uniform(7, 20))
        # people = 1500 if people > 1500 else people
        nuts_mult, nuts_end = get_events("nuts")
        xp_mult, xp_end = get_events("xp")
        a = ['🕛', '🕒', '🕕', '🕘']
        while energy >= loc["energy"] and _runs < 500:
            runs += 1
            _runs += 1
            cool = random.random() > 0.84
            energy -= loc['energy']
            life = random.random()
            life_req = loc['dr'] / (1 + (new_level - 1) / 64)
            live = life > life_req
            people = int(people * random.uniform(0.9, 1.1))
            place = 0
            saves = 0
            nuts, xp, points, sh_xp = 0, 0, 0, 0
            if live:
                clan['xp'] += loc['sh']
                a1, a2 = loc["araksan"]
                nuts += random.randint(a1, a2)
                x1, x2 = loc["xp"]
                xp += random.randint(x1, x2)
                l1, l2 = loc["points"]
                points += random.randint(l1, l2)
                if not cool and people > 1:
                    place = random.randint(1, people - 1)
                    xp *= (people - place - 1) / people * 2
                    # xp += int((people - place - 1) / people * 3000)
                else:
                    saves = random.randint(0, people - 1)
                    # _saves = saves if saves < 2000 else 2000
                    xp += int(loc["sh"] * saves / 5)
                    sh_xp += loc["sh"] * saves
                    nuts += saves
            else:
                if cool:
                    saves = random.randint(0, people - 1)
                    # _saves = saves if saves < 2000 else 2000
                    xp += int(loc["sh"] * saves / 5)
                    sh_xp += loc["sh"] * saves
                    nuts += saves
            temples = json.loads(clan["temples"])
            temple_levels = json.loads(clan["temple_levels"])
            for i in range(3):
                temple = temples[i]
                if temple["expiry"] > now_ts or i == 0:
                    if temple["id"] == 1:
                        nuts *= 1.06 + 0.04 * temple_levels[0]
                    elif temple["id"] == 2:
                        xp *= 1.07 + 0.03 * temple_levels[1]
                    elif temple["id"] == 3:
                        sh_xp *= 1.075 + 0.025 * temple_levels[2]
            _lvl_len_int = loc['ll']
            lvl_len_int = random.randint(int(_lvl_len_int * 0.9), int(_lvl_len_int * 1.1))
            pass_time_int = random.randint(loc["act"], lvl_len_int)
            # m, s = divmod(pass_time_int, 60)
            # pass_time = f"{m}m {s:02d}s"
            # m, s = divmod(lvl_len_int, 60)
            # lvl_len = f"{m}m {s:02d}s"
            pass_time = langs.td_int(pass_time_int, locale, brief=True, suffix=False)
            lvl_len = langs.td_int(lvl_len_int, locale, brief=True, suffix=False)
            player["nuts"] += int(nuts * nuts_mult)
            player["xp"] += int(xp * xp_mult)
            player["sh_xp"] += int(sh_xp)
            player["points"] += int(points)
            new_level, ld, _title = xp_level(new_level, player["xp"])
            player["coins"] += ld
            limit = 119 + new_level if new_level <= 200 else 320 if level == 200 else 420
            if energy < limit:
                if ld > 0:
                    energy = limit
                else:
                    energy += lvl_len_int / 60
                    if energy > limit:
                        energy = limit
            place_str = langs.gls("tbl_game_mid3a", locale, langs.gns(place, locale), langs.gns(people - 1, locale))
            saves_str = langs.gls("tbl_game_mid3b", locale, langs.gns(saves, locale))
            sh_xp_str = langs.gls("tbl_game_mid4b", locale, langs.gns(int(sh_xp), locale)) if cool else ""
            # place_str = f"You came **#{langs.gns(place, locale)}/{langs.gns(people - 1, locale)}**"
            # saves_str = f"Saves: **{langs.gns(saves, locale)}**"
            # sh_xp_str = f"\nShaman XP: **{langs.gns(int(sh_xp), locale)}**" if cool else ""
            message_data = f"**{ctx.author.name}**:\n"
            if nuts_mult != 1:
                _m, _e = langs.gfs(nuts_mult, locale), langs.td_dt(nuts_end, brief=True, suffix=False)
                message_data += langs.gls("tbl_game_events_nuts", locale, _m, _e, a[_runs % 4])
                # message_data += f"Current Nuts Multiplier: **x{nuts_mult}** - \\{a[_runs % 4]} Ends in **{langs.td_dt(nuts_end, brief=True)}**\n"
            if xp_mult != 1:
                _m, _e = langs.gfs(xp_mult, locale), langs.td_dt(xp_end, brief=True, suffix=False)
                message_data += langs.gls("tbl_game_events_xp", locale, _m, _e, a[_runs % 4])
                # message_data += f"Current XP Multiplier: **x{xp_mult}** - \\{a[_runs % 4]} Ends in **{langs.td_dt(xp_end, brief=True)}**\n"
            # message_data += f"Round: **{_runs}**\nLocation: **{loc['name']}**\n" \
            #                 f"Energy remaining: **{energy:,.0f}**\n\nThis round's results:\nLevel length: **{lvl_len}**\n"
            message_data += langs.gls("tbl_game_mid1", locale, langs.gns(_runs, locale), loc["name"], langs.gns(int(energy), locale), lvl_len)
            if live:
                if not cool:
                    message_data += langs.gls("tbl_game_mid2a", locale, pass_time, place_str)
                    # message_data += f"Time taken: **{pass_time}**\n{place_str}"
                else:
                    message_data += saves_str
            else:
                message_data += langs.gls("tbl_game_mid2b", locale)
                # message_data += "You did not win this round."
                if cool:
                    message_data += f"\n{saves_str}"
            message_data += langs.gls("tbl_game_mid4a", locale, langs.gns(int(nuts), locale), langs.gns(player["nuts"], locale), langs.gns(int(xp), locale),
                                      langs.gns(player["xp"], locale), langs.gns(new_level, locale), sh_xp_str)
            # message_data += f"\nRewards:\nNuts: **{nuts:,.0f}** - New total: **{player['nuts']:,}**\nXP: **{xp:,.0f}** - New total: **{player['xp']:,}** - " \
            #                 f"Level **{new_level}**{sh_xp_str}"
            await message.edit(content=message_data)
            await asyncio.sleep(1.5)
        new_level, ld, title = xp_level(level, player['xp'])
        level_up = langs.gls("tbl_game_level_xp", locale, langs.gns(new_level, locale), langs.gls(title, locale)) if ld > 0 else ""
        # level_up = f"__You are now Level **{new_level}**! New title: **{title}**__\n" if ld > 0 else ""
        new_sh_level = sh_level(player['sh_xp'])
        cl_level, cld = clan_level(clan["level"], clan["xp"])
        clan["upgrade_points"] += cld
        if cld > 0:
            level_up += langs.gls("tbl_game_level_clan", locale, langs.gns(cl_level, locale), langs.plural(cld, "tbl_game_upgrade_points", locale))
            # level_up += f"__This clan is now Level **{cl_level}**! Earned **{cld}** Upgrade Points__\n"
        new_time = time.now_ts()
        if wp:
            db.execute("UPDATE tbl_player SET level=?, xp=?, nuts=?, coins=?, sh_xp=?, energy=?, time=?, points=?, runs=?, name=?, disc=? WHERE uid=?",
                       (new_level, player["xp"], player["nuts"], player["coins"], player["sh_xp"], int(energy), new_time, player["points"], runs,
                        ctx.author.name, ctx.author.discriminator, ctx.author.id))
        else:
            db.execute("INSERT INTO tbl_player VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (ctx.author.id, new_level, player["xp"], player["nuts"], player["coins"], player["sh_xp"], int(energy), new_time, player["points"],
                        runs, 0, ctx.author.name, ctx.author.discriminator))
        if wc:
            db.execute("UPDATE tbl_clan SET level=?, xp=?, upgrade_points=?, name=? WHERE gid=?",
                       (cl_level, clan["xp"], clan["upgrade_points"], ctx.guild.name, ctx.guild.id))
        else:
            db.execute("INSERT INTO tbl_clan VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (ctx.guild.id, cl_level, clan["xp"], clan["temples"], clan["temple_levels"], clan["nuts"], clan["coins"],
                        clan["upgrade_points"], ctx.guild.name, False))
        message_data = langs.gls("tbl_game_end", locale, ctx.author.name, langs.gns(int(energy), locale), langs.gns(player["nuts"], locale),
                                 langs.gns(player["xp"], locale), langs.gns(new_level, locale), langs.gns(player["sh_xp"], locale),
                                 langs.gns(new_sh_level, locale), langs.gns(clan["xp"], locale), langs.gns(cl_level, locale), level_up, ctx.prefix)
        # message_data = f"{time.time()} > {ctx.author.name} > TBL over\nTime taken: **{total_time}**\nNew stats:\nEnergy left: **{energy:,.0f}**\n" \
        #                f"Nuts: **{player['nuts']:,}**\nXP: **{player['xp']:,}** | Level **{new_level}**\nShaman XP: **{player['sh_xp']:,}** | " \
        #                f"Level **{new_sh_level}**\nClan XP: **{clan['xp']:,}** | Level **{cl_level}**\n{level_up}\nCheck `{ctx.prefix}tbl stats` to see your "
        #                f"stats or `{ctx.prefix}tbl clan` for the clan stats. Use `{ctx.prefix}tbl details` for details on things"
        return await message.edit(content=message_data)
    except Exception as e:
        if ctx.channel.id == 610482988123422750:
            await general.send(general.traceback_maker(e), ctx.channel)
        return await general.send(langs.gls("tbl_game_error", locale, type(e).__name__, str(e)), ctx.channel)
        # return await general.send(f"An error has occurred.\n`{type(e).__name__}: {e}`\nData was reverted.", ctx.channel)
    finally:
        db.execute("UPDATE tbl_clan SET usage=0 WHERE gid=?", (ctx.guild.id,))


def get_location(lid: int, level: int):
    locations = tbl_data.locations
    for i in range(len(locations)):
        location = locations[i]
        if location['id'] == lid:
            return location
        if level < location['level']:
            return locations[i - 1]
    return locations[-1]


def get_activity(loc_act: list):
    """ Get location's activity """
    now = ss23.time_kargadia(tz=2.5)
    month = now.month
    month_var = [1.51, 1.37, 1.22, 1.09, 1.00, 0.93, 0.87, 0.91, 0.96, 1.01, 1.17, 1.27, 1.59, 2.01, 2.31, 1.97]
    hour = now.hour + (now.minute / 32)
    al = len(loc_act)
    part, mod = divmod(hour, 4)
    return int(((loc_act[int(part)] * mod + loc_act[int(part + 1) % al] * (4 - mod)) / 4) * month_var[month - 1])


def regen_energy(current: int, regen_time: int, level: int, now: int):
    td = now - regen_time
    limit = 119 + level if level <= 200 else 320 if level == 200 else 420
    if current >= limit:
        return current, now
    else:
        regen = td // 60
        new = current + regen
        if new > limit:
            energy = limit
            regen_t = now
        else:
            energy = new
            regen_t = regen_time + regen * 60
        return energy, regen_t


def xp_level(old_lvl: int, xp: int):
    new_lvl = 0
    title = "Undefined"
    for level in tbl_data.xp_levels:
        if level["experience"] <= xp:
            new_lvl += 1
            title = level["title"]
        else:
            break
    return new_lvl, new_lvl - old_lvl, title


def sh_level(xp: int):
    new_lvl = 1
    for level in tbl_data.sh_levels:
        if level <= xp:
            new_lvl += 1
        else:
            break
    return new_lvl


def clan_level(old_lvl: int, xp: int):
    new_lvl = 1
    for level in tbl_data.clan_levels:
        if level <= xp:
            new_lvl += 1
        else:
            break
    return new_lvl, new_lvl - old_lvl


def get_season():
    now = time.now()
    for season, data in tbl_data.seasons.items():
        start, end = data
        if end < now:
            continue
        elif start > now:
            continue
        return season


def get_events(what: str):
    now = time.now()
    events = tbl_data.events.get(what)
    for start, end, mult in events:
        if end < now:
            continue
        elif start > now:
            continue
        return mult, end
    return 1.0, now
