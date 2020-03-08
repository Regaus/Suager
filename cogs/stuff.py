import asyncio
import json
import random
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from utils import sqlite, time, permissions, tbl
from utils.generic import value_string, round_value, random_colour

soon = "Coming Soon\u005c\u2122"
# aqos_guilds = []


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite.Database()

    @commands.group(name="aqos")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    # @commands.max_concurrency(1, per=commands.BucketType.guild, wait=False)
    async def aqos(self, ctx):
        """ The Aqos Game """
        # return await ctx.send(soon)
        if ctx.invoked_subcommand is None:
            # if ctx.guild.id in self.aqos_guilds:
            #     return await ctx.send("Someone in this server is currently using Aqos, please wait...")
            # self.aqos_guilds.append(ctx.guild.id)
            return await aqos_game(self.db, ctx)

    @aqos.command(name="stats", aliases=["rank"])
    async def aqos_stats(self, ctx, *, who: discord.Member = None):
        """ Aqos Stats """
        user = who or ctx.author
        _data = self.db.fetchrow(find, (user.id, "aqos"))
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
        # biased = bias.get_bias(self.db, ctx.author)
        try:
            xp = levels('aqos')[level - 1]
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

    @commands.group(name="tbl")
    @commands.guild_only()
    # @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    # @commands.max_concurrency(1, per=commands.BucketType.guild, wait=False)
    async def tbl(self, ctx):
        """ The TBL Game """
        # return await ctx.send(soon)
        if ctx.invoked_subcommand is None:
            return await ctx.invoke(self.tbl_run)

    @tbl.command(name="run", hidden=True)
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=False)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def tbl_run(self, ctx):
        """ The TBL Game """
        return await tbl_game(self.db, ctx)

    @tbl.command(name="stats")
    async def tbl_stats(self, ctx, *, who: discord.Member = None):
        """ TBL Stats """
        user = who or ctx.author
        data = self.db.fetchrow(find, (user.id, "tbl_player"))
        if not data:
            player = tbl_player.copy()
        else:
            if data['usage']:
                return await ctx.send(f"{user.name} is currently playing TBL - "
                                      f"Please wait for any currently running TBL command to finish...")
            player = json.loads(data['data'])
        embed = discord.Embed(colour=random_colour())
        embed.set_thumbnail(url=user.avatar_url)
        ze = player['potion_energy'] > time.now_ts()
        mp = player['potion_mana'] > time.now_ts()
        player['energy'], player['time'], player['mana'] = regenerate_energy(
            player['energy'], player['mana'], time.now_ts(), ze, player['time'],
            player['level'], player['potion_energy'], player['potion_mana'])
        embed.add_field(name="Araksan", value=value_string(player['araksan']), inline=True)
        embed.add_field(name="Coins", value=value_string(player['coins']), inline=True)
        embed.add_field(name="Mana", value=value_string(player['mana']), inline=True)
        nl = value_string(tbl.xp_levels[player['level']]['experience'])
        embed.add_field(name="Experience", inline=True,
                        value=f"Level {player['level']:,}\n{value_string(player['xp'])}/{nl} XP")
        embed.add_field(name="Title", value=tbl.xp_levels[player['level'] - 1]['title'], inline=True)
        snl = value_string(tbl.sh_levels[player['sh_level'] - 1])
        embed.add_field(name="Shaman Stats", inline=True,
                        value=f"Level {player['sh_level']}\n{value_string(player['sh_xp'])}/{snl} XP")
        el = 420 if ze else 119 + player['level']
        embed.add_field(name="Energy", value=f"{player['energy']:,.0f}/{el}", inline=True)
        epe = f"Active until {time.time_output(time.from_ts(player['potion_energy']))}" if ze else "Inactive"
        mpe = f"Active until {time.time_output(time.from_ts(player['potion_mana']))}" if mp else "Inactive"
        embed.add_field(name="Energy Potion", value=epe, inline=True)
        embed.add_field(name="Mana Potion", value=mpe, inline=True)
        league = "None"
        for lg in tbl.tbl_leagues:
            if lg['min_scores'] <= player['league']:
                league = lg['en']
        embed.add_field(name="League", value=f"{league} - {value_string(player['league'])} points", inline=True)
        embed.add_field(name="Current Clan", value=ctx.guild.name, inline=True)
        embed.add_field(name="Rounds Played", value=value_string(player['used']), inline=True)
        return await ctx.send(f"TBL Stats for {user.name}", embed=embed)

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


def levels(which: str):
    if which == "aqos":  # Aqos Leveling System
        r = 0
        xp = []
        for x in range(aqos_ml):
            if x < 499:
                power = 3
            else:
                power = 3 + (x - 500) / 1000
            base = 2.7 * x ** power + 30 * x ** 2 + 750 * x + 2000  # 1 KI = 0.7 XP
            # too_bad = 1 / multipliers  # Imagine needing more XP just cuz the bot doesn't like you as much
            # val = base * too_bad
            r += base  # Removed bias
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


find = 'SELECT * FROM data WHERE id=? and type=?'  # Type is 'aqos'
insert = 'INSERT INTO data VALUES (?, ?, ?, ?, ?, ?, ?)'
# user.id, "aqos", data, False, user.name, user.discriminator, data['score']
update = 'UPDATE data SET data=?, usage=?, name=?, disc=?, extra=? WHERE id=? AND type=?'
# data, False, user.name, user.discriminator, user.id, "aqos", data['score']


async def aqos_game(db, ctx):
    _data = db.fetchrow(find, (ctx.author.id, "aqos"))
    if not _data:
        data = aqos_data.copy()
        d = json.dumps(data)
        db.execute(insert, (ctx.author.id, "aqos", d, True, ctx.author.name, ctx.author.discriminator, 0))
    else:
        if _data['usage']:
            return await ctx.send("It seems that Aqos is already being used, please wait...")
        data = json.loads(_data['data'])
        db.execute("UPDATE data SET usage=? WHERE id=? AND type=?", (True, ctx.author.id, "aqos"))
    try:
        # if ctx.guild.id in aqos_guilds:
        #     # await ctx.send("It seems that someone is using Aqos in this server, please wait...")
        #     raise errors.AqosError("It seems that someone is using Aqos in this server, please wait...")
        # aqos_guilds.append(ctx.guild.id)
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
        # bv = bias.get_bias(db, ctx.author)  # Bias Value
        if etu < 1:
            db.execute(update, (json.dumps(data), False, ctx.author.name, ctx.author.discriminator, data['score'],
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
                    data['score'] += (ki / 10) * val
                data['xp'] += kp * aqos_kpr
                if new > le + 2:
                    le = new
                    elapsed = time.human_timedelta(now_dt, accuracy=2, suffix=False)
                    md = f"{time.time()} > {ctx.author.name} > Aqos Normal Mode\nEnergy used: {used:,}/{etu:,}\n" \
                         f"Current Level: {data['level']:,}\nScore: {data['score']:,.2f}\nXP: {data['xp']:,.2f} " \
                         f"(XP Level {data['xp_level']:,})\nElapsed: {elapsed}"
                    await message.edit(content=md)
                await asyncio.sleep(wait)
            xpr = levels('aqos')
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
            db.execute(update, (json.dumps(data), False, ctx.author.name, ctx.author.discriminator, data['score'],
                                ctx.author.id, "aqos"))
            md = f"{time.time()} > {ctx.author.name} > Aqos Normal Mode\nEnergy used: {used:,}\n" \
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
                wait = 0.001 if etu < 10000 else 0.0002 if 10000 <= etu < 125000 else 0
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
                    ls = int(round(random.randint(s1, s2), -2))
                    bs = (ls ** 0.7) * (61 + int(data['level'] / 100))
                    data['score'] += ls + bs
                    # if data['level'] % 10 == 0:
                    #     b1, b2 = int(s1 ** 0.7), int(s2 ** 0.7)
                    #     bl = 61 + int(data['level'] / 100)
                    #     for j in range(bl):
                    #         data['score'] += int(round(random.randint(b1, b2), -2))
                    #         await asyncio.sleep(wait)
                    lr = 1440 * 6 + data['level']
                    data['lr'] = random.randint(lr - 100, lr + 100)
                ki = int(data['level'] / 1.5)
                kp = int(ki / 1.25)
                ki = int(random.randint(ki - 50, ki + 50) * tm)
                kp = int(random.randint(kp - 50, kp + 50) * tm)
                sp = int(data['level'] / 2.5)
                rs = [random.randint(sp - 100, sp + 100) for _ in range(10)]
                for val in rs:
                    data['score'] += (ki / 10) * val
                data['xp'] += kp * aqos_kpr
                if new > le + 2:
                    le = new
                    elapsed = time.human_timedelta(now_dt, accuracy=2, suffix=False)
                    md = f"{time.time()} > {ctx.author.name} > Aqos Infinite Mode\nEnergy used: {used:,}/{etu:,}\n" \
                         f"Current Level: {data['level']:,}\nScore: {data['score']:,.2f}\nXP: {data['xp']:,.2f} " \
                         f"(XP Level {data['xp_level']:,})\nElapsed: {elapsed}"
                    await message.edit(content=md)
                await asyncio.sleep(wait)
            xpr = levels('aqos')
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
            db.execute(update,
                       (json.dumps(data), False, ctx.author.name, ctx.author.discriminator, data['score'],
                        ctx.author.id, "aqos"))
            md = f"{time.time()} > {ctx.author.name} > Aqos Infinite Mode\nEnergy used: {used:,}\nTime taken: " \
                 f"{elapsed}\nLevel: **{data['level']:,}/{aqos_iml:,}**\nProgress: Current Level - **{clp}%** | " \
                 f"Overall - **{oap}%**\nScore: **{value_string(data['score'], big=True)}**\nXP: **" \
                 f"{value_string(data['xp'], big=True)}/{xpn}** - XP Level **{data['xp_level']:,}**\n" \
                 f"Energy Left: **{data['energy']:,.1f}/{el:,.1f}**\nEnergy regeneration: {round(er, 2)} " \
                 f"seconds - {((1 / er) * 60):,.2f} per minute\nFull in: {fi}"
            # try:
            #     aqos_guilds.pop(ctx.guild.id)
            # except IndexError:
            #     pass
            return await message.edit(content=md)
    # except errors.RegausError as e:
    #     save_shit(db, ctx, data)
    #     return await ctx.send(f"{e}")
    except Exception as e:
        save_shit(db, ctx, data),
        return await ctx.send(f"Congratulations, everything broke.\n`{type(e).__name__}: {e}`")


def save_shit(db, ctx, data):
    db.execute(update, (json.dumps(data), False, ctx.author.name, ctx.author.discriminator, data['score'],
                        ctx.author.id, "aqos"))
    # try:
    #     aqos_guilds.pop(ctx.guild.id)
    # except IndexError:
    #     pass


def aqos_xpl(xp, xpr):
    level = 0
    for lr in xpr:
        if xp >= lr:
            level += 1
        else:
            break
    return level


tbl_player = {
    "level": 1,
    "xp": 0,
    "araksan": 150,
    "coins": 5,
    "sh_level": 1,
    "sh_xp": 0,
    "mana": 0,
    "dr_day": 0,  # Daily Reward Day
    "dr_ll": 0,   # Daily Reward Last Login
    "energy": 0,
    "time": 0,
    "potion_energy": 0,
    "potion_mana": 0,
    "secret_mode": 0,
    "league": 0,
    "used": 0,
    "sh": 0,
    "location": 0,  # Your current location
    "2001": 0,  # How many times you went to visit Senko (2001)
    "2002": 0,  # How many times you went to the Warm Lands (2002)
    "timed": 0,  # How many times you went to timed locations (1001+)
    # "revival": 0,  # Time since last free reincarnation used (from clan)  - Not in use
}
tbl_clan = {
    "level": 1,
    "xp": 0,
    "temples": [0, 0, 0],
    "expiry": [0, 0, 0],
    "skill_points": 0,
    "araksan": 0,
    "coins": 0,
    "temple_levels": [1] * len(tbl.tbl_totems),
}

# tbl_find = 'SELECT * FROM data WHERE id=? and type=?'  # Type is 'aqos'
# tbl_insert = 'INSERT INTO data VALUES (?, ?, ?, ?, ?, ?, ?)'
# user.id, "aqos", data, False, user.name, user.discriminator, data['score']
# tbl_update = 'UPDATE data SET data=?, usage=?, name=?, disc=?, extra=? WHERE id=? AND type=?'
# data, False, user.name, user.discriminator, user.id, "aqos", data['score']
tp, tc = "tbl_player", "tbl_clan"


async def tbl_game(db, ctx):
    d1 = db.fetchrow(find, (ctx.author.id, "tbl_player"))
    d2 = db.fetchrow(find, (ctx.guild.id, "tbl_clan"))
    if not d1:
        player = tbl_player.copy()
        d = json.dumps(player)
        db.execute(insert, (ctx.author.id, "tbl_player", d, True, ctx.author.name, ctx.author.discriminator, 0))
    else:
        if d1['usage']:
            return await ctx.send("Seems like you're already playing TBL, please wait...")
        player = json.loads(d1['data'])
        db.execute("UPDATE data SET usage=? WHERE id=? AND type=?", (True, ctx.author.id, "tbl_player"))
    if not d2:
        clan = tbl_clan.copy()
        d = json.dumps(clan)
        db.execute(insert, (ctx.guild.id, "tbl_clan", d, True, ctx.guild.name, None, 0))
    else:
        if d2['usage']:
            return await ctx.send("Seems like someone here is already playing TBL, please wait...")
        clan = json.loads(d2['data'])
        db.execute("UPDATE data SET usage=? WHERE id=? AND type=?", (True, ctx.guild.id, "tbl_clan"))
    try:
        now = time.now_ts()
        now_dt = time.now()
        # elapsed = "None"
        lid = player['location']
        sm = player['secret_mode']
        if lid == 0 or (sm < now and lid == -1):
            lid = get_location_id(player['level'], sm, now)
        if 1000 <= lid < 2000:
            a = get_location(lid)
            o = a['open']
            h = now.hour
            if h < o[0] or h >= o[1]:
                lid = get_location_id(player['level'], sm, now)
        loc = get_location(lid)
        send = f"{time.time()} > {ctx.author.name} > TBL Initiated.\nWelcome to TBL, you motherfucker. " \
               f"Enjoy your stay while it still lasts."
        ep = player['potion_energy'] > now
        player['energy'], player['time'], player['mana'] = regenerate_energy(
            player['energy'], player['mana'], now, ep, player['time'], player['level'],
            player['potion_energy'], player['potion_mana'])
        # try:
        #     rounds = int(player['energy'] / loc['energy'])
        # except ZeroDivisionError:
        #     rounds = 10
        # re = loc['energy'] * rounds
        # enough = player['energy'] - re >= 0 and rounds > 0
        if player['energy'] < loc['energy']:
            db.execute(update, (json.dumps(player), False, ctx.author.name, ctx.author.discriminator, player['league'],
                                ctx.author.id, "tbl_player"))
            db.execute(update, (json.dumps(clan), False, ctx.guild.name, None, 0, ctx.guild.id, "tbl_clan"))
            return await ctx.send(f"You don't have enough energy right now. {player['energy']:.0f}/{loc['energy']}")
        # fl = False - Force life - deprecated
        message = await ctx.send(send)
        # le = now
        used = 0
        while player['energy'] >= loc['energy'] and used < 100:
            cool = player['sh'] > 0
            # new = time.now_ts()
            used += 1
            if 1000 <= loc['id'] < 2000:
                player['timed'] += 1
            if loc['id'] == 2001:
                player['2001'] += 1
            if loc['id'] == 2002:
                player['2002'] += 1
            player['energy'] -= loc['energy']
            player['used'] += 1
            life = random.random()
            live = life > loc['dr']
            rewards = [0, 0, 0, 0, 0]  # Araksan, XP, Mana, SH and SH XP
            activity = get_activity(loc['activity'])
            people = activity if activity < 15 else 15
            if 50 <= activity < 100:
                people = 20
            elif 100 <= activity < 150:
                people = 30
            elif activity >= 150:
                people = int(activity / 4)
            place = 0
            if live:
                clan['xp'] += loc['sh']
                a1, a2 = loc['araksan']
                rewards[0] += random.randint(a1, a2)
                x1, x2 = loc['xp']
                rewards[1] += random.randint(x1, x2)
                l1, l2 = loc['points']
                player['league'] += random.randint(l1, l2)
                if not cool and people > 1:
                    place = random.randint(1, people - 1)
                    rewards[2] += people - place
                    sh = 3 - place
                    rewards[3] = sh if sh > 0 else 0
                else:
                    saves = random.randint(0, people)
                    rewards[4] += loc['sh'] * saves
                    rewards[0] += saves
                    rewards[3] -= 1
            else:
                if cool or people == 1:
                    saves = random.randint(0, people)
                    rewards[4] += loc['sh'] * saves
                    rewards[0] += saves
                    rewards[3] -= 1
            # totems = tbl.tbl_totems
            for k in range(len(clan['temples'])):
                if clan['expiry'][k] > now or k == 0:
                    if clan['temples'][k] == 1:
                        rewards[0] *= (1.08 + 0.02 * clan['temple_levels'][0])
                    if clan['temples'][k] == 2:
                        rewards[1] *= (1.06 + 0.04 * clan['temple_levels'][1])
                    if clan['temples'][k] == 3:
                        rewards[4] *= (1.05 + 0.025 * clan['temple_levels'][2])
            t1, t2 = loc['act']
            rct = random.randint(t1, t2)
            td = timedelta(seconds=rct).__str__()
            if ep:
                rewards[1] *= 2
                rewards[2] *= 1.5
                rewards[4] *= 2
            player['araksan'] += rewards[0]
            player['xp'] += rewards[1]
            player['mana'] += rewards[2]
            player['sh'] += rewards[3]
            player['sh'] = 0 if player['sh'] < 0 else player['sh']
            player['sh_xp'] += rewards[4]
            er = 2 if ep else 1
            el = 420 if ep else 119 + player['level']
            if player['energy'] < el:
                player['energy'] += rct / 60 * er
                if player['energy'] > el:
                    player['energy'] = el
            await asyncio.sleep(loc['ll'] / 60)
            elapsed = time.human_timedelta(now_dt, suffix=False)
            pl = f" - You were #{place}/{int(people - 1)}" if not cool else ""
            sd = f"\nShaman XP: {rewards[4]}" if cool or people == 1 else ""
            md = f"{time.time()} > {ctx.author.name} > TBL\nRound: {used}\nLocation: {loc['name']}\n" \
                 f"Elapsed: {elapsed}\nEnergy: {player['energy']:,.0f}/{el}\n\nRound results:\n" \
                 f"Time taken: {td}{pl}\nAraksan: {rewards[0]:,.0f} - You now have {player['araksan']:,.0f}\n" \
                 f"XP: {rewards[1]:,.0f} - You now have {player['xp']:,.0f}\n" \
                 f"Mana: {rewards[2]:,.0f} - You now have {player['mana']:,.0f}{sd}"
            await message.edit(content=md)
        player['level'], ld, title = get_level(player['level'], player['xp'])
        oa = ""
        if ld > 0:
            el = 420 if ep else 119 + player['level']
            if player['energy'] < el:
                player['energy'] = el
            oa += f"You've reached XP Level **{player['level']}**! - New title: {title}\n"
        player['sh_level'], sld = sh_level(player['sh_level'], player['sh_xp'])
        if sld > 0:
            oa += f"You've reached Shaman Level **{player['sh_level']}**!\n"
        clan['level'], cld = sh_level(clan['level'], clan['xp'])
        clan['skill_points'] += cld
        if cld > 0:
            oa += f"This clan is now Level **{clan['level']}**! - Earned {cld} Skill Points\n"
        player['time'] = now
        db.execute(update, (json.dumps(player), False, ctx.author.name, ctx.author.discriminator, player['league'],
                            ctx.author.id, "tbl_player"))
        db.execute(update, (json.dumps(clan), False, ctx.guild.name, None, 0, ctx.guild.id, "tbl_clan"))
        tt = time.human_timedelta(now_dt, suffix=False)
        md = f"{time.time()} > {ctx.author.name} > Thank you for playing TBL\nTime taken: {tt}\nNew totals:\n" \
             f"Energy left: {player['energy']:,.0f}\n" \
             f"Araksan: {value_string(player['araksan'])}\nXP: {value_string(player['xp'])}\n" \
             f"Mana: {value_string(player['mana'])}\nShaman XP: {value_string(player['sh_xp'])}\n{oa}\n" \
             f"Check \"{ctx.prefix}help tbl\" for possible commands"
        return await message.edit(content=md)
    except Exception as e:
        db.execute(update, (json.dumps(player), False, ctx.author.name, ctx.author.discriminator, player['league'],
                            ctx.author.id, "tbl_player"))
        db.execute(update, (json.dumps(clan), False, ctx.guild.name, None, 0, ctx.guild.id, "tbl_clan"))
        return await ctx.send(f"Congratulations, everything broke.\n`{type(e).__name__}: {e}`")


def get_location_id(level, sm, now):
    if sm > now:
        return -1
    loc = tbl.tbl_locations
    for i in range(len(loc)):
        if loc[i]['id'] < 1000:  # If it ain't some kinda special one
            if level < loc[i]['level']:
                try:
                    return loc[i - 1]['id']
                except IndexError:
                    return 1


def get_location(lid):
    loc = tbl.tbl_locations
    for i in range(len(loc)):
        if loc[i]['id'] == lid:
            return loc[i]


def regenerate_energy(energy, bm, now, ze, er, xp, epe, mpe):
    td = now - er
    rs = 30 if ze else 60
    el = 420 if ze else 119 + xp
    zt = 0
    if epe > er:
        if epe > now:
            zt = now - er
        else:
            zt = epe - er
    if zt > 0:
        bm += int(round(100 * zt / 3600))
    zm = 0
    if mpe > er:
        if mpe > er:
            zm = now - er
        else:
            zm = mpe - er
    if zm > 0:
        bm += int(round(1000 * zm / 3600))
    if energy < el:
        re = int(td / rs)
        ne = energy + re
        if ne > el:
            energy = el
            er = now
        else:
            er += re * rs
    else:
        er = now
    return energy, er, bm


def get_activity(activity: list):
    """ Get location's current activity """
    now = time.now()
    hour = now.hour
    al = len(activity)
    four = int(hour / 4)
    rest = hour % 4
    return (activity[four] * rest + activity[(four + 1) % al] * (4 - rest)) / 4


def get_level(xpl, xp):
    old_level = xpl
    xp_level = 0
    title = "Unknown"
    for level in tbl.xp_levels:
        if level["experience"] <= xp:
            xp_level += 1
            title = level["title"]
        else:
            break
    return xp_level, xp_level - old_level, title


def sh_level(sl, sxp):
    old_level = sl
    shl = 1
    for level in tbl.sh_levels:
        if level <= sxp:
            shl += 1
        else:
            break
    return shl, shl - old_level


def clan_level(cl, cxp):
    old_level = cl
    ncl = 1
    for level in tbl.clan_levels:
        if level <= cxp:
            ncl += 1
        else:
            break
    return ncl, ncl - old_level
