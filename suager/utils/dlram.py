import random

from core.utils import time, general
from languages import langs

max_level = 1024
sel_data = f"SELECT * FROM dlram WHERE gid=?"


def levels():
    req = 0
    xp = []
    for x in range(max_level):
        # base = 16 * x ** (3 + x / 200 if x <= 500 else 5.5) + 256 * x ** 3 + 8192 * x ** 2 + 1048576 * x + 4194304
        base = 16 * x ** (3 + x / 1024 if x <= 921 else 3.9) + 256 * x ** 3 + 8192 * x ** 2 + 1048576 * x + 4194304
        req += int(base)
        if x not in [68, 419, 665, 1336]:
            xp.append(int(req))
        else:
            xp.append(xp[-1])
    return xp


_levels = levels()


def get_data(guild, db, now_ts: float):
    data = db.fetchrow(sel_data, (guild.id,))
    if not data:
        return {
            "level": 1,
            "ram": 0,
            "energy": 1024,
            "time": now_ts,
            "downloads": 0
        }, False
    return data, True


async def download_ram(ctx, db):
    locale = langs.gl(ctx.guild, db)
    now_ts = int(time.now_ts())
    data, wd = get_data(ctx.guild, db, now_ts)
    energy, regen_t, regen_speed = regen_energy(data["energy"], data["time"], data["level"], now_ts)
    if energy < 1:
        return await general.send(langs.gls("dlram_charge_none", locale, ctx.author.name, langs.td_int(
            regen_speed - (now_ts - regen_t), locale, is_future=True, brief=False, suffix=True)), ctx.channel)
        # return await general.send(f"{ctx.author.name}: You don't have enough energy. Try again in {time.timedelta(regen_speed - (now_ts - regen_t))}",
        #                           ctx.channel)
    async with ctx.typing():
        try:
            ram_range = 131072, 2097152
            r1, r2 = ram_range
            downloaded = 0
            runs = 0
            _xp = data["ram"]
            _new_level = data["level"]
            while energy >= 1 and runs <= 1000000:
                # multiplier = ram_mult(_new_level)
                multiplier = 1
                runs += 1
                new_ram = int(random.randint(r1, r2) * multiplier)
                energy -= 1
                downloaded += new_ram
                _xp += new_ram
                _new_level, _ld = xp_level(_new_level, _xp)
                if _ld != 0:
                    limit, _ = speed_limit(_new_level)
                    # limit = 256 if _new_level < 8 else _new_level * 32
                    energy += int((limit / ((10 + _new_level / 40) if _new_level < 200 else 15)) * _ld)
            data["ram"] += downloaded
            new_level, ld = xp_level(data["level"], data["ram"])
            al = levels()
            if new_level < max_level:
                next_level = langs.gbs(al[new_level - 1], locale)
            else:
                next_level = langs.gls("generic_max", locale)
            ram = langs.gbs(data["ram"], locale)
            data["level"] = new_level
            data["energy"] = int(energy)
            data["time"] = regen_t
            data["downloads"] += runs
            limit, regen_speed = speed_limit(new_level)
            if wd:
                db.execute("UPDATE dlram SET level=?, ram=?, energy=?, time=?, downloads=?, name=? WHERE gid=?",
                           (data["level"], data["ram"], data["energy"], data["time"], data["downloads"], ctx.guild.name, ctx.guild.id))
            else:
                db.execute("INSERT INTO dlram VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (ctx.guild.id, data["level"], data["ram"], data["energy"], data["time"], data["downloads"], ctx.guild.name))
            regen_pm = langs.gfs((1 / regen_speed) * 60, locale, 2)
            message = langs.gls("dlram_message", locale, ctx.author.name, langs.gns(runs, locale), langs.gbs(downloaded, locale), ram, next_level,
                                langs.gns(new_level, locale), langs.gns(energy, locale), langs.gns(limit, locale), regen_pm)
            # message = f"{ctx.author.name}: Downloads: **{langs.gns(runs)}**\nYou have downloaded **{langs.gbs(downloaded)} RAM**\nThis server now has " \
            #           f"**{ram}/{next_level} RAM**\nThis server is level **{langs.gns(new_level)}**.\nCharge left: **{langs.gns(energy)}/{langs.gns(limit)}**"
            if energy < limit:
                fill = limit - energy
                # regen_speed = 60 - int(new_level / 500 * 59)
                # n_speed = 60 if new_level < 100 else 30 if 100 <= new_level < 250 else 15 if 250 <= new_level < 1000 else 5 if 1000 <= new_level < 3000 else 1
                time_req = regen_t + fill * regen_speed
                ts = int(time_req - time.now_ts())
                message += langs.gls("dlram_message_charge", locale, langs.td_int(ts, locale, is_future=True, brief=False, suffix=True))
                # message += f"\nCharge will be full in **{time.timedelta(int(time_req - time.now_ts()))}**"
            return await general.send(message, ctx.channel)
        except Exception as e:
            if ctx.channel.id == 610482988123422750:
                await general.send(general.traceback_maker(e), ctx.channel)
            return await general.send(langs.gls("tbl_game_error", locale, type(e).__name__, str(e)), ctx.channel)


def speed_limit(level: int):
    if level == max_level:
        limit = 12582912
    else:
        limit = 256
        for i in range(1, level + 1):
            if i < 5:
                continue
            elif 5 <= i < 32:
                limit += 64
            elif 32 <= i < 64:
                limit += 128
            elif 64 <= i < 128:
                limit += 256
            elif 128 <= i < 192:
                limit += 1024
            elif 192 <= i < 384:
                limit += 4096
            elif 384 <= i < 512:
                limit += 8192
            else:
                limit += 16384
    # regen_speed = (192 / (level * (0.7 - (level / 5000 * 0.6 if level < 2500 else 0.3)))) if level != 1 else 192
    # regen_speed = 192 if level == 1 else 192 / ((level - 1) * (0.5 + level / 25))
    start = (400 if level < 192 else 400 - (level - 128) / 2 if 128 <= level < 512 else 208)
    regen_speed = start / (level * (0.5 + level / ((36 - level / 64) if level < 256 else (32 - (level - 256) / 16) if 256 <= level < 640 else 8)))
    limit //= 16
    regen_speed *= 16
    return limit, regen_speed if regen_speed < 900 else 900


def regen_energy(current: int, regen_time: int, level: int, now: int):
    td = now - regen_time
    limit, regen_speed = speed_limit(level)
    # regen_speed = 60 if level < 100 else 30 if 100 <= level < 250 else 15 if 250 <= level < 1000 else 5 if 1000 <= level < 3000 else 1
    if current >= limit:
        return current, now, regen_speed
    else:
        regen = int(td / regen_speed)
        new = current + regen
        if new > limit:
            energy = limit
            regen_t = now
        else:
            energy = new
            regen_t = regen_time + regen * regen_speed
        return energy, regen_t, regen_speed


def xp_level(old_lvl: int, xp: int):
    new_lvl = 1
    al = _levels
    for level in al:
        if level <= xp:
            new_lvl += 1
        else:
            break
    return new_lvl, new_lvl - old_lvl
