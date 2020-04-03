import json
import random

import discord
from discord.ext import commands

from beta import main
from utils import time, database
from utils.generic import random_colour, value_string, round_value

max_level = 5000
level_xp = [21, 30]


def levels():
    req = 0
    xp = []
    for x in range(max_level):
        base = 1.5 * x ** 2 + 125 * x + 200
        req += base
        xp.append(req)
    return xp


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database()
        self.type = main.version
        self.banned = [690254056354087047, 694684764074016799]

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.bot or ctx.guild is None:
            return
        if self.type == "stable":
            _settings = self.db.fetchrow(f"SELECT * FROM data_{self.type} WHERE type=? AND id=?",
                                         ("settings", ctx.guild.id))
            if not _settings:
                settings = main.settings_template.copy()
            else:
                settings = json.loads(_settings['data'])
            try:
                if not settings['leveling']['enabled']:
                    return
                ic = settings['leveling']['ignored_channels']
                if ctx.channel.id in ic:
                    return
            except KeyError:
                pass
            data = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
            if data:
                level, xp, last = [data['level'], data['xp'], data['last']]
            else:
                level, xp, last = [0, 0, 0]
            now = time.now_ts()
            if last > now - 60:
                return
            x1, x2 = level_xp
            try:
                sm = float(settings['leveling']['xp_multiplier'])
                sm = 0 if sm < 0 else sm if sm < 10 else 10
            except KeyError:
                sm = 1
            new = int(random.randint(x1, x2) * sm)
            new = 0 if ctx.author.id == 592345932062916619 else new
            xp += new
            requirements = levels()
            lu = False
            while level < max_level and xp >= requirements[level]:
                level += 1
                lu = True
            if lu:
                try:
                    send = str(settings['leveling']['level_up_message']).replace('[MENTION]', ctx.author.mention)\
                        .replace('[USER]', ctx.author.name).replace('[LEVEL]', f"{level:,}")
                except KeyError:
                    send = f"{ctx.author.mention} has reached **level {level:,}**! " \
                           f"<a:forsendiscosnake:613403121686937601>"
                try:
                    ac = settings['leveling']['announce_channel']
                    if ac != 0:
                        ch = self.bot.get_channel(ac)
                        if ch is None or ch.guild.id != ctx.guild.id:
                            ch = ctx.channel
                    else:
                        ch = ctx.channel
                except KeyError:
                    ch = ctx.channel
                try:
                    await ch.send(send)
                except discord.Forbidden:
                    pass  # Well, if it can't send it there, too bad.
            reason = f"Level Rewards - Level {level}"
            try:
                rewards = settings['leveling']['rewards']
                if rewards:  # Don't bother if they're empty
                    l1, l2 = [], []
                    rewards.sort(key=lambda x: x['level'])
                    for i in range(len(rewards)):
                        l1.append(rewards[i]['level'])
                        l2.append(rewards[i]['role'])
                    roles = [r.id for r in ctx.author.roles]
                    for i in range(len(rewards)):
                        role = discord.Object(id=l2[i])
                        has_role = l2[i] in roles
                        if level >= l1[i]:
                            if i < len(rewards) - 1:
                                if level < l1[i + 1]:
                                    if not has_role:
                                        await ctx.author.add_roles(role, reason=reason)
                                else:
                                    if has_role:
                                        await ctx.author.remove_roles(role, reason=reason)
                            else:
                                if not has_role:
                                    await ctx.author.add_roles(role, reason=reason)
                        else:
                            if has_role:
                                await ctx.author.remove_roles(role, reason=reason)
            except KeyError:
                pass  # If no level rewards, don't even bother
            except discord.Forbidden:
                await ctx.send(f"{ctx.author.name} should have got a level reward, "
                               f"but I do not have sufficient permissions to do so.")
            except Exception as e:
                print(f"{time.time()} > Levels on_message > {type(e).__name__}: {e}")
            if data:
                self.db.execute(
                    "UPDATE leveling SET level=?, xp=?, last=?, name=?, disc=? WHERE uid=? AND gid=?",
                    (level, xp, now, ctx.author.name, ctx.author.discriminator, ctx.author.id, ctx.guild.id))
            else:
                self.db.execute(
                    "INSERT INTO leveling VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (ctx.author.id, ctx.guild.id, level, xp, now, ctx.author.name, ctx.author.discriminator))

    @commands.command(name="rewards")
    @commands.guild_only()
    async def rewards(self, ctx):
        """ Rewards """
        if ctx.channel.id in self.banned:
            return await ctx.send(f"Stop using this command in {ctx.channel.mention} ffs...")
        settings = self.db.fetchrow(f"SELECT * FROM data_{self.type} WHERE type=? AND id=?", ("settings", ctx.guild.id))
        if not settings:
            return await ctx.send("Doesn't seem like this server has leveling rewards")
        else:
            data = json.loads(settings['data'])
        try:
            rewards = data['leveling']['rewards']
            rewards.sort(key=lambda x: x['level'])
            embed = discord.Embed(colour=random_colour())
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.title = f"Rewards for having no life in {ctx.guild.name}"
            d = ''
            for role in rewards:
                d += f"Level {role['level']}: <@&{role['role']}>\n"
            embed.description = d
            return await ctx.send(embed=embed)
        except KeyError:
            return await ctx.send("Doesn't seem like this server has leveling rewards...")

    @commands.command(name="rank")
    @commands.guild_only()
    async def rank(self, ctx, *, who: discord.Member = None):
        """ Check your or someone's rank """
        if ctx.channel.id in self.banned:
            return await ctx.send(f"Stop using this command in {ctx.channel.mention} ffs...")
        user = who or ctx.author
        is_self = user.id == self.bot.user.id
        if user.bot and not is_self:
            return await ctx.send("Bots are cheating, so I don't even bother storing their XP.")
        _settings = self.db.fetchrow(f"SELECT * FROM data_{self.type} WHERE type=? AND id=?",
                                     ("settings", ctx.guild.id))
        if not _settings:
            dm = 1
        else:
            settings = json.loads(_settings['data'])
            try:
                dm = settings['leveling']['xp_multiplier']
                dm = 0 if dm < 0 else dm if dm < 10 else 10
            except KeyError:
                dm = 1
        data = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if data:
            level, xp = [data['level'], data['xp']]
        else:
            level, xp = [0, 0]
        embed = discord.Embed(colour=random_colour())
        embed.set_thumbnail(url=user.avatar_url)
        if is_self:
            embed.description = "Imagine playing fair in your own XP system. That'd be boring."
            embed.add_field(name="Experience", value="**More than you**", inline=False)
            embed.add_field(name="Level", value="Higher than yours", inline=False)
        else:
            # biased = bias.get_bias(self.db, user)
            r1 = f"{xp:,.0f}"
            if level < max_level:
                yes = levels()   # All levels
                req = int(yes[level])  # Requirement to next level
                re = req - xp
                r2 = f"{req:,.0f}"
                r3 = value_string(re)
                prev = int(yes[level-1]) if level != 0 else 0
                progress = (xp - prev) / (req - prev)
                r4 = round_value(progress * 100)
                r4 = 100 if r4 > 100 else r4
                embed.add_field(name="Experience", value=f"**{r1}**/{r2}", inline=False)
                embed.add_field(name="Level", value=f"{level:,}", inline=False)
                embed.add_field(name="Progress to next level", value=f"{r4}% - {r3} XP to level up", inline=False)
            else:
                embed.add_field(name="Experience", value=f"**{r1}**", inline=False)
                embed.add_field(name="Level", value=f"{level:,}", inline=False)
            x1, x2 = [val * dm for val in level_xp]
            o1, o2 = int(x1), int(x2)
            embed.add_field(name="XP per message", inline=False, value=f"{o1}-{o2}")
        return await ctx.send(f"**{user}**'s rank in **{ctx.guild.name}:**", embed=embed)

    @commands.command(name="xplevel")
    async def xp_level(self, ctx, level: int):
        """ XP required to achieve a level """
        if ctx.channel.id in self.banned:
            return await ctx.send(f"Stop using this command in {ctx.channel.mention} ffs...")
        if level > max_level or level < max_level * -1 + 1:
            return await ctx.send(f"The max level is {max_level}.")
        try:
            r = levels()[level - 1]
        except IndexError:
            return await ctx.send(f"Level specified - {level:,} gave an IndexError. Max level is {max_level}, btw.")
        data = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not data:
            return await ctx.send("It doesn't seem like I have any data saved for you right now...")
        _settings = self.db.fetchrow(f"SELECT * FROM data_{self.type} WHERE type=? AND id=?",
                                     ("settings", ctx.guild.id))
        if not _settings:
            dm = 1
        else:
            settings = json.loads(_settings['data'])
            try:
                dm = settings['leveling']['xp_multiplier']
            except KeyError:
                dm = 1
        xp = data['xp']
        x1, x2 = [val * dm for val in level_xp]
        a1, a2 = [(r - xp) / x2, (r - xp) / x1]
        m1, m2 = int(a1) + 1, int(a2) + 1
        t1, t2 = [time.timedelta(x * 60, show_seconds=False) for x in [m1, m2]]
        # x1, x2 = [val * normal * dm for val in level_xp]
        needed = value_string(r, big=True)
        tl = ""
        if xp < r:
            tl = f"\nXP left to reach level: **{value_string(r - xp, big=True)}**\n" \
                 f"That is **{m1:,} to {m2:,}** more messages.\nTalking time: **{t1} to {t2}**"
        return await ctx.send(f"Well, {ctx.author.name}...\nTo reach level **{level:,}** you will need "
                              f"**{needed} XP**{tl}")

    @commands.command(name="nextlevel")
    @commands.guild_only()
    async def next_level(self, ctx):
        """ XP required for next level """
        if ctx.channel.id in self.banned:
            return await ctx.send(f"Stop using this command in {ctx.channel.mention} ffs...")
        data = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not data:
            return await ctx.send("It doesn't seem like I have any data saved for you right now...")
        _settings = self.db.fetchrow(f"SELECT * FROM data_{self.type} WHERE type=? AND id=?",
                                     ("settings", ctx.guild.id))
        if not _settings:
            dm = 1
        else:
            settings = json.loads(_settings['data'])
            try:
                dm = settings['leveling']['xp_multiplier']
            except KeyError:
                dm = 1
        level, xp = [data['level'], data['xp']]
        r1 = f"{int(xp):,}"
        # biased = bias.get_bias(self.db, ctx.author)
        yes = levels()
        r, p = [int(yes[level]), int(yes[level-1]) if level != 0 else 0]
        re = r - xp
        r2 = f"{int(r):,}"
        r3 = f"{int(re):,}"
        pr = (xp - p) / (r - p)
        r4 = round_value(pr * 100)
        r4 = 100 if r4 > 100 else r4
        r5 = f"{level + 1:,}"
        normal = 1
        x1, x2 = [val * normal * dm for val in level_xp]
        a1, a2 = [(r - xp) / x2, (r - xp) / x1]
        m1, m2 = int(a1) + 1, int(a2) + 1
        t1, t2 = [time.timedelta(x * 60, show_seconds=False) for x in [m1, m2]]
        return await ctx.send(f"Alright, **{ctx.author.name}**:\nYou currently have **{r1}/{r2}** XP.\nYou need "
                              f"**{r3}** more to reach level **{r5}** (Progress: **{r4}%**).\nMessages left: "
                              f"**{m1} to {m2}**\nEstimated talking time: **{t1} to {t2}**")

    @commands.command(name="levels")
    @commands.guild_only()
    async def levels_lb(self, ctx):
        """ Server's XP Leaderboard """
        if ctx.channel.id in self.banned:
            return await ctx.send(f"Stop using this command in {ctx.channel.mention} ffs...")
        async with ctx.typing():
            data = self.db.fetch("SELECT * FROM leveling WHERE gid=? ORDER BY xp DESC LIMIT 250", (ctx.guild.id,))
            if not data:
                return await ctx.send("I have no data at all for this server... Weird")
            block = "```fix\n"
            un = []   # User names
            xp = []   # XP
            # unl = []  # User name lengths
            xpl = []  # XP string lengths
            for user in data:
                name = f"{user['name']}#{user['disc']:04d}"
                un.append(name)
                # unl.append(len(name))
                val = f"{value_string(user['xp'])}"
                xp.append(val)
                xpl.append(len(val))
            spaces = max(xpl) + 5
            place = "unknown, or over 250"
            for x in range(len(data)):
                if data[x]['uid'] == ctx.author.id:
                    place = f"#{x + 1}"
                    break
            for i, val in enumerate(data[:10], start=1):
                k = i - 1
                who = un[k]
                if val['uid'] == ctx.author.id:
                    who = f"-> {who}"
                s = ' '
                sp = xpl[k]
                block += f"{str(i).zfill(2)}){s*4}{xp[k]}{s*(spaces-sp)}{who}\n"
            return await ctx.send(f"Top users in {ctx.guild.name} - Sorted by XP\nYour place: {place}\n{block}```")

    @commands.command(name="glevels")
    async def global_levels(self, ctx):
        """ Global XP Leaderboard """
        if ctx.channel.id in self.banned:
            return await ctx.send(f"Stop using this command in {ctx.channel.mention} ffs...")
        async with ctx.typing():
            data = self.db.fetch("SELECT * FROM leveling", ())
            coll = {}
            for i in data:
                if i['uid'] not in coll:
                    coll[i['uid']] = [0, f"{i['name']}#{i['disc']:04d}"]
                coll[i['uid']][0] += i['xp']
            sl = sorted(coll.items(), key=lambda a: a[1][0], reverse=True)
            r = len(sl) if len(sl) < 10 else 10
            block = "```fix\n"
            un, xp, xpl = [], [], []
            for thing in range(r):
                v = sl[thing][1]
                un.append(v[1])
                x = value_string(v[0])
                xp.append(x)
                xpl.append(len(x))
            spaces = max(xpl) + 5
            place = "unknown, or over 250"
            for someone in range(len(sl)):
                if sl[someone][0] == ctx.author.id:
                    place = f"#{someone + 1}"
            s = ' '
            for i, d in enumerate(sl[:10], start=1):
                k = i - 1
                who = un[k]
                if d[0] == ctx.author.id:
                    who = f"-> {who}"
                sp = xpl[k]
                block += f"{str(i).zfill(2)}){s*4}{xp[k]}{s*(spaces-sp)}{who}\n"
            return await ctx.send(f"Top users globally - Sorted by XP\nYour place: {place}\n{block}```")


def setup(bot):
    bot.add_cog(Leveling(bot))
