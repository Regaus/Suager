import asyncio
import json
import random
from datetime import datetime

import discord
from discord.ext import commands

from utils import sqlite, time, bias, permissions
from utils.generic import value_string, round_value, random_colour

soon = "Coming Soon\u005c\u2122"


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite.Database()

    @commands.group(name="aqos")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=False)
    async def aqos(self, ctx):
        """ The Aqos Game """
        # return await ctx.send(soon)
        if ctx.invoked_subcommand is None:
            return await aqos_game(self.db, ctx)

    @aqos.command(name="stats", aliases=["rank"])
    async def aqos_stats(self, ctx, *, who: discord.Member = None):
        """ Aqos Stats """
        user = who or ctx.author
        _data = self.db.fetchrow(aqos_find, (user.id, "aqos"))
        if not _data:
            data = aqos_data.copy()
        else:
            if _data['usage']:
                return await ctx.send(f"{user.name} is currently using Aqos - "
                                      f"Please wait for any currently running Aqos command to finish...")
            data = json.loads(_data['data'])
        embed = discord.Embed(colour=random_colour())
        embed.set_thumbnail(url=user.avatar_url)
        normal = data['level'] < 1441
        if normal:
            p, s = get_part(data['level'])
            lr = (p * 4 + s + 1) * 72
        else:
            lr = aqos_iml
        embed.add_field(name="Level", value=f"{data['level']:,}/{lr:,}", inline=True)
        if normal:
            embed.add_field(name="Normal Mode Progress", inline=True,
                            value=f"{round_value((data['level'] - 1) / 1440 * 100)}%")
        else:
            embed.add_field(name="Overall Progress", inline=True,
                            value=f"{round_value((data['level'] - 1) / aqos_iml * 100)}%")
        embed.add_field(name="Score", value=value_string(data['score'], big=True), inline=True)
        embed.add_field(name="XP", value=value_string(data['xp'], big=True), inline=True)
        embed.add_field(name="XP Level", value=f"{data['xp_level']:,}", inline=True)
        now = time.now_ts()
        el = max_energy(data['level'], data['score'])
        er = energy_regen(data['level'], data['xp_level'], el)
        if data['energy'] < el:
            regen = (now - data['time']) / er
            data['energy'] += regen
            data['energy'] = el if data['energy'] > el else data['energy']
        ert = (el - data['energy']) * er
        tr = now + ert
        try:
            fi = time.human_timedelta(datetime.fromtimestamp(tr), accuracy=3, suffix=True)
        except OSError:
            fi = "An error ago"
        embed.add_field(name="Energy", value=f"{data['energy']:,.1f}/{el:,.1f}", inline=True)
        embed.add_field(name="Energy full in", value=fi, inline=True)
        embed.set_footer(text=f"{user.name} has used {data['used']:,} energy")
        return await ctx.send(f"**{user}**'s current Aqos stats", embed=embed)

    @aqos.command(name="resetusage")
    @permissions.has_permissions(administator=True)
    async def aqos_ru(self, ctx, user: discord.Member):
        """ Reset usage """
        data = self.db.execute("UPDATE data SET usage=? WHERE id=? AND type=?", (False, user.id, "aqos"))
        return await ctx.send(f"Updated usage status for {user.name} -> {data}")

    @aqos.command(name="xplevel")
    async def aqos_xp_level(self, ctx, level: int):
        """ XP required to reach a level """
        if level > aqos_ml or level < aqos_ml * -1 + 1:
            return await ctx.send(f"The max level is {aqos_ml}.")
        biased = bias.get_bias(self.db, ctx.author)
        try:
            xp = levels('aqos', biased)[level - 1]
        except IndexError:
            return await ctx.send(f"Level specified - {level:,} gave an IndexError. Max level is {aqos_ml}, btw.")
        needed = value_string(xp, big=True)
        return await ctx.send(f"Well, {ctx.author.name}...\nTo reach level **{level:,}** you will need **{needed} XP**")

    @aqos.command(name="leaderboard", aliases=["lb", "halloffame"])
    async def aqos_hof(self, ctx):
        """ Aqos Hall of Fame """
        data = self.db.fetch("SELECT * FROM data WHERE type=? ORDER BY extra DESC LIMIT 250", ("aqos",))
        if not data:
            return await ctx.send("Doesn't seem like I have any data saved, weird.")
        block = "```fix\n"
        un, sc, scl = [], [], []
        for user in data:
            name = f"{user['name']}#{str(user['disc']).zfill(4)}"
            un.append(name)
            val = value_string(user['extra'])
            sc.append(val)
            scl.append(len(val))
        spaces = max(scl) + 5
        place = "unknown, or over 250"
        for x in range(len(data)):
            if data[x]['id'] == ctx.author.id:
                place = f"#{x + 1}"
                break
        for i, val in enumerate(data[:10], start=1):
            k = i - 1
            who = un[k]
            if val['id'] == ctx.author.id:
                who = f"-> {who}"
            s = ' '
            sp = scl[k]
            block += f"{str(i).zfill(2)}){s * 4}{sc[k]}{s * (spaces - sp)}{who}\n"
        return await ctx.send(f"Top users: Aqos - Sorted by score\nYour place: {place}\n{block}```")

    @commands.command(name="tbl")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def tbl(self, ctx):
        """ The TBL Game """
        return await ctx.send(soon)

    @commands.command(name="cobblecobble", aliases=["cc"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def cobble_cobble(self, ctx):
        """ CobbleCobble """
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
aqos_ils = [75000, 100000]
aqos_ml = 5000  # Max XP Level
aqos_iml = 2147483647  # Infinity Mode Max Level
aqos_kpr = 0.7  # KP to XP rate
# SPP, LES, LL, BRL, KI and KP in Infinity Mode will depend on your level.


def levels(which: str, multipliers: int or float = 1):
    if which == "aqos":  # Aqos Leveling System
        r = 0
        xp = []
        for x in range(aqos_ml):
            if x < 499:
                power = 3
            else:
                power = 3 + (x - 500) / 1000
            base = 2.7 * x ** power + 30 * x ** 2 + 750 * x + 2000  # 1 KI = 0.7 XP
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
    return aqos_tpe + (level - 1) / 1.75


def energy_regen(level, xp, me):
    if level <= 1440:
        p = get_part(level)[0]
        base = aqos_er[p]
    else:
        base = aqos_ier
    more = xp * 0.4
    cool = base - more
    # limit = [{'min': -1, 'max': 750, 'er': 15}, {'min': 750, 'max': 1000, 'er': 10},
    #          {'min': 1000, 'max': 1250, 'er': 7.5}, {'min': 1250, 'max': 1440, 'er': 5}]
    # mr = 20
    if level <= 1400:
        mr = 86400 / me * 2
    else:
        mr = 86400 / me
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
    no = 50000 if nm else 100000 + (level - 1440) * 20
    return no if el > no else el


aqos_find = 'SELECT * FROM data WHERE id=? and type=?'  # Type is 'aqos'
aqos_insert = 'INSERT INTO data VALUES (?, ?, ?, ?, ?, ?, ?)'
# user.id, "aqos", data, False, user.name, user.discriminator, data['score']
aqos_update = 'UPDATE data SET data=?, usage=?, name=?, disc=?, extra=? WHERE id=? AND type=?'
# data, False, user.name, user.discriminator, user.id, "aqos", data['score']


async def aqos_game(db, ctx):
    _data = db.fetchrow(aqos_find, (ctx.author.id, "aqos"))
    if not _data:
        data = aqos_data.copy()
        d = json.dumps(data)
        db.execute(aqos_insert, (ctx.author.id, "aqos", d, True, ctx.author.name, ctx.author.discriminator, 0))
    else:
        if _data['usage']:
            return await ctx.send("It seems that Aqos is already being used, please wait...")
        data = json.loads(_data['data'])
        db.execute("UPDATE data SET usage=? WHERE id=? AND type=?", (True, ctx.author.id, "aqos"))
    try:
        now = time.now_ts()
        now_dt = time.now()
        elapsed = "None"
        send = f"{time.time()} > {ctx.author.name} > Aqos Initiated."
        message = await ctx.send(send)
        el = max_energy(data['level'], data['score'])
        er = energy_regen(data['level'], data['xp_level'], el)
        if data['energy'] < el:
            regen = (now - data['time']) / er
            data['energy'] += regen
            data['energy'] = el if data['energy'] > el else data['energy']
        data['time'] = now
        normal = data['level'] <= 1440
        etu = int(data['energy'])  # Energy to use
        bv = bias.get_bias(db, ctx.author)  # Bias Value
        if etu < 1:
            db.execute(aqos_update, (json.dumps(data), False, ctx.author.name, ctx.author.discriminator, data['score'],
                                     ctx.author.id, "aqos"))
            left = time.human_timedelta(datetime.fromtimestamp(now + er * (1 - data['energy'])), accuracy=3)
            return await message.edit(content=f"{ctx.author.name}, you don't have any energy to use."
                                              f"\nNext energy point in: {left}")
        if etu > 10000000:  # 10 million
            etu = 10000000
        if normal:
            await message.edit(content=f"{time.time()} > {ctx.author.name} > Aqos Normal Mode\n"
                                       f"Level: {data['level']:,} | Energy: {int(data['energy']):,}")
            le = now
            used = 0
            for i in range(etu):
                wait = 0.02 if etu < 500 else 0.015 if 500 <= etu < 1000 else 0.007 if 1000 <= etu < 10000 else 0.001 \
                    if etu < 500000 else 0
                new = time.now_ts()
                used += 1
                data['used'] += 1
                data['energy'] -= 1
                tm = time_per_energy(data['level']) / 60
                data['lp'] += tm
                lu = False
                if data['lp'] > data['lr']:
                    data['level'] += 1
                    if data['level'] > 1440:
                        await message.edit(content=f"{time.time()} > {ctx.author.name} > Aqos Normal Mode complete.\n"
                                                   f"Run `{ctx.prefix}aqos` again to enter Infinite Mode")
                        s1, s2 = aqos_les[-1][-1]
                        data['lp'] -= data['lr']
                        data['score'] += int(round(random.randint(s1, s2), -2))
                        lr = 1440 * 7 + 1
                        data['lr'] = random.randint(lr - 100, lr + 100)
                        await asyncio.sleep(7)
                        break
                    lu = True
                p, s = get_part(data['level'])
                if lu:
                    s1, s2 = aqos_les[p][s]
                    data['score'] += int(round(random.randint(s1, s2), -2))
                    b = data['level'] % 6
                    if b == 4 or b == 0:
                        b1, b2 = [int(s1 ** 0.7), int(s2 ** 0.7)]
                        for j in range(aqos_brl[p][s]):
                            data['score'] += int(round(random.randint(b1, b2), -2))
                            await asyncio.sleep(wait)
                    data['lp'] -= data['lr']
                    l1, l2 = aqos_ll[p][s]
                    data['lr'] = random.randint(l1, l2)
                ki1, ki2 = aqos_ki[p]
                kp1, kp2 = aqos_kp[p]
                ki = int(random.randint(ki1, ki2) * tm)
                kp = int(random.randint(kp1, kp2) * tm)
                spp1, spp2 = aqos_spp[p]
                rs = [random.randint(spp1, spp2) for _ in range(10)]
                for val in rs:
                    data['score'] += (ki / 10) * val * bv
                data['xp'] += kp * aqos_kpr * bv
                if new > le + 2:
                    le = new
                    elapsed = time.human_timedelta(now_dt, accuracy=2, suffix=False)
                    md = f"{time.time()} > {ctx.author.name} > Aqos Normal Mode\nEnergy used: {used:,}/{etu:,}\n" \
                         f"Current Level: {data['level']:,}\nScore: {data['score']:,.2f}\nXP: {data['xp']:,.2f} " \
                         f"(XP Level {data['xp_level']:,})\nElapsed: {elapsed}"
                    await message.edit(content=md)
                await asyncio.sleep(wait)
            xpr = levels('aqos', bv)
            data['xp_level'] = aqos_xpl(data['xp'], xpr)
            p, s = get_part(data['level'])
            lr = (p * 4 + s + 1) * 72
            el = max_energy(data['level'], data['score'])
            er = energy_regen(data['level'], data['xp_level'], el)
            ert = (el - data['energy']) * er
            tr = now + ert
            try:
                fi = time.human_timedelta(datetime.fromtimestamp(tr), accuracy=3, suffix=False)
            except OSError:
                fi = "An error ago"
            xpn = value_string(xpr[data['xp_level']], big=True) if data['xp_level'] < aqos_ml else "MAX"
            clp = round_value(data['lp']/data['lr']*100)
            oap = round_value((data['level']-1)/1440*100)
            db.execute(aqos_update, (json.dumps(data), False, ctx.author.name, ctx.author.discriminator, data['score'],
                                     ctx.author.id, "aqos"))
            md = f"{time.time()} > {ctx.author.name} > Aqos Normality Mode\nEnergy used: {used}\n" \
                 f"Time taken: {elapsed}\nLevel: **{data['level']:,}/{lr:,}**\nProgress: Current Level - **{clp}%** | "\
                 f"Normal Mode - **{oap}%**\nScore: **{value_string(data['score'], big=True)}**\nXP: **" \
                 f"{value_string(data['xp'], big=True)}/{xpn}** - XP Level **{data['xp_level']:,}**\n" \
                 f"Energy Left: **{data['energy']:,.1f}/{el:,.1f}**\nEnergy regeneration: {round(er, 2)} " \
                 f"seconds - {((1/er) * 60):,.2f} per minute\nFull in: {fi}"
            return await message.edit(content=md)
        # db.execute(aqos_update, (json.dumps(data), False, ctx.author.name, ctx.author.discriminator, data['score'],
        #                          ctx.author.id, "aqos"))
        # return await message.edit(content=f"{ctx.author.name}, Aqos is not yet available above level 1440 - {soon}")
        else:
            await message.edit(content=f"{time.time()} > {ctx.author.name} > Aqos Infinite Mode\n"
                                       f"Level: {data['level']:,} | Energy: {int(data['energy']):,}")
            le = now
            used = 0
            for i in range(etu):
                wait = 0.001 if etu < 10000 else 0.0002 if 10000 <= etu < 500000 else 0
                new = time.now_ts()
                used += 1
                data['used'] += 1
                data['energy'] -= 1
                tm = time_per_energy(data['level']) / 60
                data['lp'] += tm
                if data['lp'] > data['lr']:
                    data['level'] += 1
                    data['lp'] -= data['lr']
                    s1, s2 = aqos_ils
                    s1 += data['level']
                    s2 += data['level']
                    data['score'] += int(round(random.randint(s1, s2), -2))
                    if data['level'] % 10 == 0:
                        b1, b2 = int(s1 ** 0.7), int(s2 ** 0.7)
                        bl = 61 + int(data['level'] / 100)
                        for j in range(bl):
                            data['score'] += int(round(random.randint(b1, b2), -2))
                            await asyncio.sleep(wait)
                    lr = 1440 * 6 + data['level']
                    data['lr'] = random.randint(lr - 100, lr + 100)
                ki = int(data['level'] / 1.5)
                kp = int(ki / 1.25)
                ki = int(random.randint(ki - 50, ki + 50) * tm)
                kp = int(random.randint(kp - 50, kp + 50) * tm)
                sp = int(data['level'] / 2.5)
                rs = [random.randint(sp - 100, sp + 100) for _ in range(10)]
                for val in rs:
                    data['score'] += (ki / 10) * val * bv
                data['xp'] += kp * aqos_kpr * bv
                if new > le + 2:
                    le = new
                    elapsed = time.human_timedelta(now_dt, accuracy=2, suffix=False)
                    md = f"{time.time()} > {ctx.author.name} > Aqos Infinite Mode\nEnergy used: {used:,}/{etu:,}\n" \
                         f"Current Level: {data['level']:,}\nScore: {data['score']:,.2f}\nXP: {data['xp']:,.2f} " \
                         f"(XP Level {data['xp_level']:,})\nElapsed: {elapsed}"
                    await message.edit(content=md)
                await asyncio.sleep(wait)
            xpr = levels('aqos', bv)
            data['xp_level'] = aqos_xpl(data['xp'], xpr)
            el = max_energy(data['level'], data['score'])
            er = energy_regen(data['level'], data['xp_level'], el)
            ert = (el - data['energy']) * er
            tr = now + ert
            try:
                fi = time.human_timedelta(datetime.fromtimestamp(tr), accuracy=3, suffix=False)
            except OSError:
                fi = "An error ago"
            xpn = value_string(xpr[data['xp_level']], big=True) if data['xp_level'] < aqos_ml else "MAX"
            clp = round_value(data['lp'] / data['lr'] * 100)
            oap = round_value((data['level'] - 1) / aqos_iml * 100)
            db.execute(aqos_update,
                       (json.dumps(data), False, ctx.author.name, ctx.author.discriminator, data['score'],
                        ctx.author.id, "aqos"))
            md = f"{time.time()} > {ctx.author.name} > Aqos Infinite Mode\nEnergy used: {used}\nTime taken: " \
                 f"{elapsed}\nLevel: **{data['level']:,}/{aqos_iml:,}**\nProgress: Current Level - **{clp}%** | " \
                 f"Overall - **{oap}%**\nScore: **{value_string(data['score'], big=True)}**\nXP: **" \
                 f"{value_string(data['xp'], big=True)}/{xpn}** - XP Level **{data['xp_level']:,}**\n" \
                 f"Energy Left: **{data['energy']:,.1f}/{el:,.1f}**\nEnergy regeneration: {round(er, 2)} " \
                 f"seconds - {((1 / er) * 60):,.2f} per minute\nFull in: {fi}"
            return await message.edit(content=md)
    except Exception as e:
        db.execute(aqos_update, (json.dumps(data), False, ctx.author.name, ctx.author.discriminator, data['score'],
                                 ctx.author.id, "aqos"))
        return await ctx.send(f"Congratulations, everything broke.\n`{type(e).__name__}: {e}`")


def aqos_xpl(xp, xpr):
    level = 0
    for lr in xpr:
        if xp >= lr:
            level += 1
        else:
            break
    return level
