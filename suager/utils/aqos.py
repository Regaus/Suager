import random

from core.utils import general, time
from languages import langs


data = [
    [  # Temple 1
        [  # Part 1 (1 - 288)
            # Order: Level Length, Energy Limit, BR Length
            [[2, 4], 150, 2],
            [[4, 6], 170, 3],
            [[6, 10], 190, 4],
            [[12, 18], 220, 5],
            5750, 180.0  # Level End Score, Energy Regen Speed
        ],
        [  # Part 2 (289 - 576)
            [[15, 25], 250, 6],
            [[20, 40], 280, 7],
            [[33, 57], 320, 8],
            [[45, 75], 360, 9],
            6250, 150.0
        ],
        [  # Part 3 (577 - 864)
            [[70, 110], 400, 10],
            [[90, 150], 440, 11],
            [[140, 220], 480, 12],
            [[220, 320], 520, 13],
            7000, 120.0
        ],
        [  # Part 4 (865 - 1152)
            [[300, 420], 560, 14],
            [[405, 555], 640, 15],
            [[630, 810], 720, 17],
            [[855, 1065], 780, 19],
            7500, 90.0
        ],
        [  # Part 5 (1153 - 1440)
            [[1320, 1560], 900, 21],
            [[1680, 1920], 1150, 23],
            [[2040, 2280], 1400, 25],
            [[2760, 3000], 1600, 30],
            8000, 60.0
        ],
        # Final digits: Score Per Piece, KIsp, KPad, Energy Regen
        [8, 12], [195, 245], [150, 190]
    ],
    [  # Temple 2 (1441 - 2880)
        [
            [[3500, 4000], 1800, 32],
            [[4000, 4500], 2000, 34],
            [[4500, 5000], 2250, 36],
            [[5000, 5500], 2500, 38],
            8500, 45.0
        ],
        [
            [[5500, 6000], 2750, 40],
            [[6000, 6500], 3000, 42],
            [[6500, 7000], 3250, 44],
            [[7000, 7500], 3500, 46],
            9250, 30.0
        ],
        [
            [[7500, 8000], 3750, 48],
            [[8000, 8500], 4000, 50],
            [[8500, 9000], 4250, 52],
            [[9000, 9500], 4500, 54],
            10000, 20.0
        ],
        [
            [[9500, 10000], 4750, 56],
            [[10000, 10500], 5000, 58],
            [[10500, 11000], 5250, 60],
            [[11000, 11500], 5500, 62],
            10750, 15.0
        ],
        [
            [[11500, 12000], 5750, 64],
            [[12000, 12500], 6000, 66],
            [[12500, 13000], 6250, 68],
            [[13000, 13500], 6500, 70],
            11500, 12.5
        ],
        [20, 30], [285, 335], [205, 245]
    ],
    [  # Temple 3 (2881 - 4320)
        [
            [[13500, 14000], 6750, 72],
            [[14000, 14500], 7000, 74],
            [[14500, 15000], 7250, 76],
            [[15000, 15500], 7500, 78],
            12500, 10.0
        ],
        [
            [[15500, 16000], 7750, 80],
            [[16000, 16500], 8000, 82],
            [[16500, 17000], 8250, 84],
            [[17000, 17500], 8500, 86],
            13750, 7.5
        ],
        [
            [[17500, 18000], 8750, 88],
            [[18000, 18500], 9000, 90],
            [[18500, 19000], 9250, 92],
            [[19000, 19500], 9500, 94],
            15000, 5.0
        ],
        [
            [[19500, 20000], 9750, 96],
            [[20000, 20500], 10000, 98],
            [[20500, 21000], 10250, 100],
            [[21000, 21500], 10500, 102],
            15625, 3.5
        ],
        [
            [[21500, 22000], 10750, 104],
            [[22000, 22500], 11000, 106],
            [[22500, 23000], 11250, 108],
            [[23000, 23500], 11500, 110],
            16250, 2.5
        ],
        [47, 77], [400, 450], [290, 330]
    ],
    [  # Temple 4 (4321 - 5760
        [
            [[23500, 24000], 11750, 112],
            [[24000, 24500], 12000, 114],
            [[24500, 25000], 12250, 116],
            [[25000, 25500], 12500, 118],
            17500, 2
        ],
        [
            [[25500, 26000], 12750, 120],
            [[26000, 26500], 13000, 122],
            [[26500, 27000], 13250, 124],
            [[27000, 27500], 13500, 126],
            18750, 1.75
        ],
        [
            [[27500, 28000], 13750, 128],
            [[28000, 28500], 14000, 130],
            [[28500, 29000], 14250, 132],
            [[29000, 29500], 14500, 134],
            20000, 1.5
        ],
        [
            [[29500, 30000], 14750, 136],
            [[30000, 30500], 15000, 138],
            [[30500, 31000], 15250, 140],
            [[31000, 31500], 15500, 142],
            22500, 1.4
        ],
        [
            [[31500, 32000], 15750, 144],
            [[32000, 32500], 16000, 146],
            [[32500, 33000], 16250, 148],
            [[33000, 33500], 16500, 150],
            25000, 1.3
        ],
        [126, 186], [575, 625], [455, 495]
    ],
    [  # Temple 5 (5761 - 7200)
        [
            [[33500, 34000], 16750, 152],
            [[34000, 34500], 17000, 154],
            [[34500, 35000], 17250, 156],
            [[35000, 35500], 17500, 158],
            27500, 1.2
        ],
        [
            [[35500, 36000], 17750, 160],
            [[36000, 36500], 18000, 162],
            [[36500, 37000], 18250, 164],
            [[37000, 37500], 18500, 166],
            30000, 1.1
        ],
        [
            [[37500, 38000], 18750, 168],
            [[38000, 38500], 19000, 170],
            [[38500, 39000], 19250, 172],
            [[39000, 39500], 19500, 174],
            37500, 1
        ],
        [
            [[39500, 40000], 19750, 177],
            [[40000, 40500], 20000, 180],
            [[40500, 41000], 20250, 183],
            [[41000, 41500], 20500, 185],
            45000, 0.9
        ],
        [
            [[41500, 42000], 21000, 188],
            [[42000, 43000], 22000, 191],
            [[43000, 44000], 23000, 194],
            [[44000, 45000], 24000, 197],
            50000, 0.7
        ],
        [200, 325], [750, 800], [580, 620]
    ],
    [  # Temple 6 (7201 - 1048576)
        [
            [[45000, 50000], 25000, 200],
            75000, 0.5
        ],
        [300, 480], [900, 1000], [700, 800]
    ]
]
max_xp_level = 1000
levels = [int(2.7 * (x ** 3) + 30 * (x ** 2) + 750 * x + 2000) for x in range(max_xp_level)]
max_level = 1048576
k_pad_xp = 0.75
sel_player = f"SELECT * FROM aqos WHERE uid=?"


# def time_per_energy(level: int) -> float:  # Aqos Level
#     return (60 + (level - 1) * 0.01 if level < 7201 else 132.0) / 60


# def score_multiplier(level: int) -> float:  # Aqos Level
#     return 1 + (level - 1) / 1000 if level < 6001 else 7.0


class Temple:
    def __init__(self, level: int, xp_level: int, score: int, locale: str = "en_gb"):
        self.temple = (level - 1) // 1440 if level < 7201 else 5
        self.part = ((level - 1) % 1440) // 288 if self.temple < 5 else 0
        self.sub_part = ((level - 1) % 288) // 72 if self.temple < 5 else 0
        self.next_temple = [1440, 2880, 4320, 5760, 7200, 1048576][self.temple]
        names = langs.get_data("aqos_temple_names", locale)
        parts = langs.get_data("aqos_temple_parts", locale)
        self.name = langs.gls("aqos_temple_name", locale, names[self.temple], parts[self.part])
        if self.temple >= 5:
            self.name = langs.gls("aqos_temple_name_final", locale, names[self.temple])
        self.score_mult = 1 + (level - 1) / 1000 if level < 6001 else 7.0
        self.energy_time = (60 + (level - 1) * 0.01 if level < 7201 else 132.0) / 60  # "Minutes" per energy point
        energy_regen_mult = 1 + (xp_level - 1) / 111 if xp_level < 1001 else 10
        temple_data = data[self.temple]
        part_data = temple_data[self.part]
        sub_part_data = part_data[self.sub_part]
        self.level_length, energy, self.br_length = sub_part_data
        self.ki_score, self.ki_rate, self.kp_rate = temple_data[-3:]
        self.level_score, energy_regen_speed = part_data[-2:]
        extra_energy = score / 500000 if score < 50000000000 else 100000.0
        self.energy_regen = energy_regen_speed / energy_regen_mult
        self.energy_limit = energy + extra_energy


def get_player(user, db, now_ts: float):
    player = db.fetchrow(sel_player, (user.id,))
    if not player:
        return {
            "xp_level": 0,
            "xp": 0,
            "level": 1,
            "level_length": 3,
            "level_progress": 0,
            "energy": 225,
            "energy_used": 0,
            "time": now_ts,
            "score": 0
        }, False
    return player, True


async def aqos_game(ctx):
    locale = langs.gl(ctx)
    db = ctx.bot.db
    now_ts = time.now_ts()
    user, wp = get_player(ctx.author, db, now_ts)
    try:
        message = await general.send(f"{ctx.author.name} > Aqos Initiated", ctx.channel)
        _ki, _kp, _runs = 0, 0, 0  # KISp, KPad
        knowledge = Temple(user["level"], user["xp_level"], user["score"], locale)
        user["energy"], user["time"] = regen_energy(user["energy"], user["time"], now_ts, knowledge)
        if user["level"] > 1048576:
            return await message.edit(content=langs.gls("aqos_game_max_level", locale, ctx.author.name))
        if user["energy"] < 1:
            _next = langs.td_ts(int(now_ts + knowledge.energy_regen), locale, 3, False, True)
            return await message.edit(content=langs.gls("aqos_game_energy_none", locale, ctx.author.name, _next))
        while user["energy"] >= 1:
            _runs += 1
            user["energy"] -= 1
            user["level_progress"] += knowledge.energy_time
            if user["level_progress"] >= user["level_length"]:
                user["level"] += 1
                if user["level"] > 1048576:
                    save(user, wp, ctx, db)
                    return await message.edit(content=langs.gls("aqos_game_max_level", locale, ctx.author.name))
                user["score"] += knowledge.level_score
                if user["level"] % 6 in [0, 4]:
                    user["score"] += int(round(knowledge.level_score ** 0.7 * knowledge.br_length, -2))
                    # user["energy"] -= knowledge.br_length
                    _runs += knowledge.br_length
                user["level_progress"] -= user["level_length"]
                knowledge = Temple(user["level"], user["xp_level"], user["score"], locale)
                l1, l2 = knowledge.level_length
                user["level_length"] = random.randint(l1, l2)
            ki1, ki2 = knowledge.ki_rate
            ks1, ks2 = knowledge.ki_score
            kp1, kp2 = knowledge.kp_rate
            ki = int(random.uniform(ki1, ki2) * knowledge.energy_time)
            kp = int(random.uniform(kp1, kp2) * knowledge.energy_time)
            _ki += ki
            _kp += kp
            ki_score = random.randint(ks1, ks2)
            user["score"] += ki * ki_score
            user["xp"] += kp * k_pad_xp
        user["xp_level"], ld = xp_to_level(user["xp_level"], user["xp"])
        user["energy_used"] += _runs
        save(user, wp, ctx, db)
        r6 = langs.gns(levels[user["xp_level"]], locale) if user["xp_level"] < max_xp_level else langs.gls("generic_max", locale)
        knowledge = Temple(user["level"], user["xp_level"], user["score"], locale)
        td = langs.td_ts(int(now_ts), locale, 3, True, False)
        el, er = knowledge.energy_limit, knowledge.energy_regen
        r1, r2, r3, r4, r5, r7, r8, r9, r10, r11 = (
            langs.gns(user["level"], locale), langs.gns(knowledge.next_temple, locale), langs.gns(user["score"], locale), langs.gns(user["xp_level"], locale),
            langs.gfs(user["xp"], locale), langs.gfs(user["energy"], locale), langs.gns(el, locale), langs.gfs(er, locale),
            langs.td_ts(now_ts + el * er, locale, 3, False, True), knowledge.name)
        message_data = langs.gls("aqos_game_output", locale, ctx.author.name, _runs, td, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11)
        return await message.edit(content=message_data)
    except Exception as e:
        if ctx.channel.id == 742885168997466196:
            await general.send(general.traceback_maker(e), ctx.channel)
        return await general.send(langs.gls("tbl_game_error", locale, type(e).__name__, str(e)), ctx.channel)


def regen_energy(current: int, regen_time: int, now: float, knowledge: Temple):
    td = now - regen_time
    limit = knowledge.energy_limit
    regen_speed = knowledge.energy_regen
    # limit = energy_limit(level)
    # limit = 119 + level if level <= 200 else 320 if level == 200 else 420
    if current >= limit:
        return current, now
    else:
        regen = td / regen_speed
        new = current + regen
        if new > limit:
            energy = limit
            regen_t = now
        else:
            energy = new
            regen_t = regen_time + regen * regen_speed
        return energy, regen_t


def save(user: dict, wp: bool, ctx, db):
    if wp:
        db.execute("UPDATE aqos SET level=?, level_length=?, level_progress=?, energy=?, energy_used=?, time=?, score=?, xp=?, xp_level=?, name=?, "
                   "disc=? WHERE uid=?", (user["level"], user["level_length"], user["level_progress"], user["energy"], user["energy_used"], user["time"],
                                          user["score"], user["xp"], user["xp_level"], ctx.author.name, ctx.author.discriminator, ctx.author.id))
    else:
        db.execute("INSERT INTO aqos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (ctx.author.id, user["level"], user["level_length"], user["level_progress"], user["energy"], user["energy_used"], user["time"],
                    user["score"], user["xp"], user["xp_level"], ctx.author.name, ctx.author.discriminator))


def xp_to_level(old_lvl: int, xp: int):
    new_lvl = 0
    for level in levels:
        if level <= xp:
            new_lvl += 1
        else:
            break
    return new_lvl, new_lvl - old_lvl
