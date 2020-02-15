from discord.ext import commands

from utils import sqlite

soon = "Coming Soon\u005c\u2122"


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite.Database()

    @commands.command(name="aqos")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def aqos_command(self, ctx):
        """ The Aqos Game """
        return await ctx.send(soon)

    @commands.command(name="tbl")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def tbl_command(self, ctx):
        """ The TBL Game """
        return await ctx.send(soon)


def setup(bot):
    bot.add_cog(Games(bot))


aqos_ll = [[[2, 4], [4, 6], [6, 10], [12, 18]], [[15, 25], [20, 40], [33, 57], [45, 75]],
           [[70, 110], [90, 150], [140, 220], [220, 320]],
           [[300, 420], [405, 555], [630, 810], [855, 1065]],
           [[1320, 1560], [1680, 1920], [2040, 2280], [2760, 3000]]]  # Level Length
aqos_spp = [[8, 12], [20, 30], [47, 77], [126, 186], [300, 480]]  # Score per piece
aqos_ki = [[195, 245], [285, 335], [400, 450], [575, 625], [750, 800]]  # K.Isp. per minute
aqos_kp = [[150, 190], [205, 245], [290, 330], [455, 495], [580, 620]]  # K.Pad. per minute
aqos_er = [180, 150, 120, 90, 60]  # Energy regen
aqos_ier = 45  # Energy regen in infinity mode
aqos_tpe = 60  # 60 in-game seconds per 1 energy
aqos_el = [[150, 170, 190, 220], [250, 280, 320, 360], [400, 440, 480, 520],
           [560, 640, 720, 780], [1000, 1200, 1400, 1600]]  # Energy limit
aqos_iel = 2000  # Infinity Mode Max Energy
aqos_brl = [[2, 3, 4, 5], [6, 7, 8, 9], [10, 11, 12, 13], [14, 15, 17, 19], [21, 23, 25, 30]]  # BR Length
aqos_les = [[[4750, 6500], [5250, 7000], [6000, 8000], [6500, 9000]],
            [[7000, 10000], [7500, 11250], [8000, 12500], [9000, 13750]],
            [[10000, 15000], [11250, 16250], [12500, 17500], [13750, 18750]],
            [[15000, 20000], [16250, 22500], [17500, 25000], [18750, 27500]],
            [[20000, 30000], [22500, 35000], [25000, 40000], [30000, 50000]]]  # Level end scores
aqos_ml = 5000  # Max XP Level
aqos_iml = 2147483647  # Infinity Mode Max Level
aqos_kir = 0.7  # KI to XP rate


def levels(which: str, multipliers: float):
    if which == "aqos":  # Aqos Leveling System
        r = 0
        xp = []
        for x in range(aqos_ml):
            base = 2.7 * x ** 3 + 30 * x ** 2 + 750 * x + 2000  # 1 KI = 0.7 XP
            too_bad = 1 / multipliers  # Imagine needing more XP just cuz the bot doesn't like you as much
            val = base * too_bad
            r += val
            xp.append(r)
        return xp


def get_part(level):
    val = level - 1
    part = int(val / 288)
    spl = val - part * 288
    sp = int(spl / 72)
    return part, sp


aqos_data = {
    'xp': 0,
    'xp_level': 0,
    'level': 0,
    'lr': 0,  # Level Requirement
    'lp': 0,  # Level Progress
    'score': 0,
    'energy': aqos_el[0][0] * 1.5,
    'time': 0,  # Energy Time
    'used': 0,
}


def time_per_energy(level):
    return aqos_tpe + (level - 1) * 1


def energy_regen(level, xp):
    if level <= 1440:
        p = get_part(level)[0]
        base = aqos_er[p]
    else:
        base = aqos_ier
    more = xp * 0.4
    cool = base - more
    limit = [{'min': -1, 'max': 750, 'er': 20}, {'min': 750, 'max': 1000, 'er': 15},
             {'min': 1000, 'max': 1250, 'er': 10}, {'min': 1250, 'max': 1440, 'er': 7.5},
             {'min': 1440, 'max': 3000, 'er': 5}, {'min': 3000, 'max': aqos_iml, 'er': 2.5}]
    mr = 20
    for val in limit:
        if val['min'] < level <= val['max']:
            mr = val['er']
    return mr if cool < mr else cool


def max_energy(level, score):
    nm = level <= 1440
    if nm:
        p, s = get_part(level)
        me = aqos_el[p][s]
    else:
        me = aqos_iel
    se = int(score / 50000)
    el = me + se
    no = 30000 if nm else 50000 + (level - 1440) * 10
    return no if el > no else el


aqos_find = 'SELECT * FROM data WHERE id=? and type=?'  # Type is 'aqos'
aqos_insert = 'INSERT INTO data VALUES (?, ?, ?, ?, ?, ?)'
# user.id, "aqos", data, False, user.name, user.discriminator
aqos_update = 'UPDATE leveling SET data=?, usage=?, name=?, disc=? WHERE id=? AND type=?'
# data, False, user.name, user.discriminator, user.id, "aqos"


# async def aqos_game(db, ctx):
#     data = db.fetchrow(aqos_find, (ctx.author.id, "aqos"))
#     try:
#         pass
#     except Exception as e:
#         return await ctx.send(f"Congratulations, you broke everything.\n`{e}`")
