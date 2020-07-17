import random

from core.utils import time, general
from languages import langs

max_level = 5000
sel_data = f"SELECT * FROM dlram WHERE gid=?"


def levels():
    req = 0
    xp = []
    for x in range(max_level):
        base = 0.12 * x ** 5 + 0.7 * x ** 4 + 10 * x ** 3 + 40 * x ** 2 + 750 * x + 2048
        req += int(base)
        if x not in [69, 420, 666, 1337]:
            xp.append(int(req))
        else:
            xp.append(xp[-1])
    return xp


def ram_mult(level: int):
    return 1 + (level - 1) * 0.25


def get_data(guild, db, now_ts: float):
    data = db.fetchrow(sel_data, (guild.id,))
    if not data:
        return {
            "level": 1,
            "ram": 0,
            "energy": 300,
            "time": now_ts,
            "downloads": 0
        }, False
    return data, True


async def download_ram(ctx, db):
    now_ts = int(time.now_ts())
    data, wd = get_data(ctx.guild, db, now_ts)
    energy, regen_t, regen_speed = regen_energy(data["energy"], data["time"], data["level"], now_ts)
    if energy < 1:
        return await general.send(f"{ctx.author.name}: You don't have enough energy. Try again in {time.timedelta(regen_speed - (now_ts - regen_t))}",
                                  ctx.channel)
    async with ctx.typing():
        ram_range = 256, 10240
        r1, r2 = ram_range
        downloaded = 0
        runs = 0
        multiplier = ram_mult(data["level"])
        while energy >= 1 and runs <= 1000000:
            runs += 1
            new_ram = int(random.randint(r1, r2) * multiplier)
            energy -= 1
            downloaded += new_ram
        data["ram"] += downloaded
        new_level, ld = xp_level(data["level"], data["ram"])
        al = levels()
        if new_level < max_level:
            next_level = langs.gbs(al[new_level - 1])
        else:
            next_level = "MAX"
        ram = langs.gbs(data["ram"])
        data["level"] = new_level
        data["energy"] = energy
        data["time"] = regen_t
        data["downloads"] += runs
        limit = 200 + new_level * 25
        if wd:
            db.execute("UPDATE dlram SET level=?, ram=?, energy=?, time=?, downloads=?, name=? WHERE gid=?",
                       (data["level"], data["ram"], data["energy"], data["time"], data["downloads"], ctx.guild.name, ctx.guild.id))
        else:
            db.execute("INSERT INTO dlram VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (ctx.guild.id, data["level"], data["ram"], data["energy"], data["time"], data["downloads"], ctx.guild.name))
        message = f"{ctx.author.name}: Downloads: **{langs.gns(runs)}**\nYou have downloaded **{langs.gbs(downloaded)} RAM**\nThis server now has " \
                  f"**{ram}/{next_level} RAM**\nThis server is level **{langs.gns(new_level)}**.\nCharge left: **{langs.gns(energy)}/{langs.gns(limit)}**"
        if energy < limit:
            fill = limit - energy
            regen_speed = 180 - new_level if new_level < 179 else 1
            # regen_speed = 60 - int(new_level / 500 * 59)
            # regen_speed = 60 if new_level < 100 else 30 if 100 <= new_level < 250 else 15 if 250 <= new_level < 1000 else 5 if 1000 <= new_level < 3000 else 1
            time_req = regen_t + fill * regen_speed
            message += f"\nCharge will be full in **{time.timedelta(int(time_req - time.now_ts()))}**"
        return await general.send(message, ctx.channel)


def regen_energy(current: int, regen_time: int, level: int, now: int):
    td = now - regen_time
    limit = 200 + level * 25
    regen_speed = 180 - level if level < 179 else 1
    # regen_speed = 60 if level < 100 else 30 if 100 <= level < 250 else 15 if 250 <= level < 1000 else 5 if 1000 <= level < 3000 else 1
    if current >= limit:
        return current, now, regen_speed
    else:
        regen = td // regen_speed
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
    al = levels()
    for level in al:
        if level <= xp:
            new_lvl += 1
        else:
            break
    return new_lvl, new_lvl - old_lvl
