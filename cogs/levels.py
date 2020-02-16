import json
import random

import discord
from discord.ext import commands
from utils import sqlite, time, bias
from utils.generic import random_colour, value_string, round_value

max_level = 2500
level_xp = [12, 17]
level_mr = [{'min': -1, 'max': 15, 'val': 0.03},  # Multiplier Rise for level between 0 and 15
            {'min': 15, 'max': 30, 'val': 0.06}, {'min': 30, 'max': 50, 'val': 0.09},
            {'min': 50, 'max': 100, 'val': 0.12}, {'min': 100, 'max': max_level, 'val': 0.15}]
settings_template = {
    'prefixes': [],
    'use_default': True,
    'leveling': {
        'enabled': True,
        'xp_multiplier': 1.0,
        'level_up_message': "[MENTION] is now level **[LEVEL]**! <a:forsendiscosnake:613403121686937601>",
        'ignored_channels': [],
        'announce_channel': 0,
        'rewards': [
            {'level': 2501, 'role': 12345},
            {'level': 2502, 'role': 67890}
        ]
    }
}


def levels(bias_value):
    req = 0
    xp = []
    for x in range(max_level):
        if x < 499:
            power = 3
        else:
            power = 3 + (x - 500) / 1000
        base = x ** power + 4 * x ** 2 + 250 * x + 500
        if bias_value < 1:
            oh = 1 / bias_value
        else:
            bv = 1 + (bias_value - 1) / 2
            oh = 1 / bv
        total = base * oh
        req += total
        xp.append(req)
    return xp


def level_mult(level):
    mult = 1
    for lvl in range(level):
        for data in level_mr:
            if data['min'] < lvl <= data['max']:
                mult += data['val']
    return mult


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite.Database()

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.bot or ctx.guild is None:
            return
        _settings = self.db.fetchrow("SELECT * FROM data WHERE type=? AND id=?", ("settings", ctx.guild.id))
        if not _settings:
            settings = settings_template.copy()
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
        data = self.db.fetchrow("SELECT * FROM leveling WHERE user_id=? AND guild_id=?", (ctx.author.id, ctx.guild.id))
        if data:
            level, xp, last = [data['level'], data['xp'], data['last_time']]
        else:
            level, xp, last = [0, 0, 0]
        now = time.now_ts()
        if last > now - 60:
            return
        x1, x2 = level_xp
        base_mult = level_mult(level)
        biased = bias.get_bias(self.bot, ctx.author)
        try:
            sm = float(settings['leveling']['xp_multiplier'])
            sm = 0 if sm < 0 else sm if sm < 10 else 10
        except KeyError:
            sm = 1
        new = random.randint(x1, x2) * base_mult * biased * sm
        xp += new
        requirements = levels(biased)
        lu = False
        while level < max_level and xp >= requirements[level]:
            level += 1
            lu = True
        if lu:
            try:
                send = str(settings['leveling']['level_up_message']).replace('[MENTION]', ctx.author.mention).replace(
                    '[USER]', ctx.author.name).replace('[LEVEL]', f"{level:,}")
            except KeyError:
                send = f"{ctx.author.mention} has reached **level {level:,}**! <a:forsendiscosnake:613403121686937601>"
            try:
                ac = settings['leveling']['announce_channel']
                if ac != 0:
                    ch = self.bot.get_channel(ac)
                    ch = ch if ch is not None else ctx.channel
                else:
                    ch = ctx.channel
            except KeyError:
                ch = ctx.channel
            try:
                await ch.send(send)
            except discord.Forbidden:
                pass  # Well, if it can't send it there, too bad.
            try:
                rewards = settings['leveling']['rewards']
                l1, l2 = [], []
                rewards.sort(key=lambda x: x['level'])
                for i in range(len(rewards)):
                    l1.append(rewards[i]['level'])
                    l2.append(rewards[i]['role'])
                roles = [r.id for r in ctx.author.roles]
                for i in range(len(rewards)):
                    role = discord.Object(id=l2[i])
                    has_role = l2[i] in roles
                    if level > l1[i]:
                        if i < len(rewards) - 1:
                            if level < l1[i + 1]:
                                if not has_role:
                                    await ctx.author.add_roles(role, reason="Level Rewards")
                            else:
                                if has_role:
                                    await ctx.author.remove_roles(role, reason="Level Rewards")
                        else:
                            if not has_role:
                                await ctx.author.add_roles(role, reason="Level Rewards")
                    else:
                        if has_role:
                            await ctx.author.remove_roles(role, reason="Level Rewards")
            except KeyError:
                pass  # If no level rewards, don't even bother
            except discord.Forbidden:
                pass  # If I can't add/remove the roles, don't even bother
            except Exception as e:
                print(f"{type(e).__name__}: {e}")
        if data:
            self.db.execute("UPDATE leveling SET level=?, xp=?, last_time=?, name=?, disc=? "
                            "WHERE user_id=? AND guild_id=?",
                            (level, xp, now, ctx.author.name, ctx.author.discriminator, ctx.author.id, ctx.guild.id))
        else:
            self.db.execute("INSERT INTO leveling VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (ctx.author.id, ctx.guild.id, level, xp, now, ctx.author.name, ctx.author.discriminator))

    @commands.command(name="rewards")
    @commands.guild_only()
    async def rewards(self, ctx):
        """ Rewards """
        settings = self.db.fetchrow("SELECT * FROM data WHERE type=? AND id=?", ("settings", ctx.guild.id))
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
        user = who or ctx.author
        is_self = user.id == self.bot.user.id
        if user.bot and not is_self:
            return await ctx.send("Bots are cheating, so I don't even bother storing their XP.")
        data = self.db.fetchrow("SELECT * FROM leveling WHERE user_id=? AND guild_id=?", (user.id, ctx.guild.id))
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
            biased = bias.get_bias(self.bot, user)
            r1 = f"{xp:,.0f}"
            if level < max_level:
                yes = levels(biased)   # All levels
                req = int(yes[level])  # Requirement to next level
                re = req - xp
                r2 = f"{req:,.0f}"
                r3 = value_string(re)
                prev = int(yes[level-1]) if level != 0 else 0
                progress = (xp - prev) / (req - prev)
                r4 = round_value(progress * 100)
                embed.add_field(name="Experience", value=f"**{r1}**/{r2}", inline=False)
                embed.add_field(name="Level", value=f"{level:,}", inline=False)
                embed.add_field(name="Progress to next level", value=f"{r4}% - {r3} XP to level up", inline=False)
            else:
                embed.add_field(name="Experience", value=f"**{r1}**", inline=False)
                embed.add_field(name="Level", value=f"{level:,}", inline=False)
            base = level_mult(level)
            x1, x2 = [val * base * biased for val in level_xp]
            embed.add_field(name="Multipliers", inline=False,
                            value=f"XP multiplier: {base * biased:.2f}\nXP per message: {x1:.2f}-{x2:.2f}")
        return await ctx.send(f"**{user}**'s rank in **{ctx.guild.name}:**", embed=embed)

    @commands.command(name="xplevel")
    async def xp_level(self, ctx, level: int):
        """ XP required to achieve a level """
        if level > max_level or level < max_level * -1 + 1:
            return await ctx.send(f"The max level is {max_level}.")
        normal = level_mult(level)
        biased = bias.get_bias(self.bot, ctx.author)
        try:
            xp = levels(biased)[level - 1]
        except IndexError:
            return await ctx.send(f"Level specified - {level:,} gave an IndexError. Max level is {max_level}, btw.")
        x1, x2 = [val * normal * biased for val in level_xp]
        needed = value_string(xp, big=True)
        return await ctx.send(f"Well, {ctx.author.name}...\nTo reach level **{level:,}** you will need "
                              f"**{needed} XP**\nBy then, you'll be getting **{x1:,.2f}-{x2:,.2f} XP** per message")

    @commands.command(name="nextlevel")
    @commands.guild_only()
    async def next_level(self, ctx):
        """ XP required for next level """
        data = self.db.fetchrow("SELECT * FROM leveling WHERE user_id=? AND guild_id=?", (ctx.author.id, ctx.guild.id))
        if not data:
            return await ctx.send("It doesn't seem like I have any data saved for you right now...")
        level, xp = [data['level'], data['xp']]
        r1 = f"{xp:,.0f}"
        biased = bias.get_bias(self.bot, ctx.author)
        yes = levels(biased)
        r, p = [int(yes[level]), int(yes[level-1])]
        re = r - xp
        r2 = f"{r:,.0f}"
        r3 = f"{re:,.2f}"
        pr = (xp - p) / (r - p)
        r4 = round_value(pr * 100)
        r5 = f"{level + 1:,}"
        normal = level_mult(level)
        x1, x2 = [val * normal * biased for val in level_xp]
        a1, a2 = [(r - xp) / x2, (r - xp) / x1]
        m1, m2 = [f"{a1:,.0f}", f"{a2:,.0f}"]
        return await ctx.send(f"Alright, **{ctx.author.name}**:\nYou currently have **{r1}/{r2}** XP. You need "
                              f"**{r3}** more to reach level **{r5}** (Progress: **{r4}%**).\nMessages left: around "
                              f"**{m1}-{m2}**")

    @commands.command(name="levels")
    @commands.guild_only()
    async def levels_lb(self, ctx):
        """ Server's XP Leaderboard """
        async with ctx.typing():
            data = self.db.fetch("SELECT * FROM leveling WHERE guild_id=? ORDER BY xp DESC LIMIT 250", (ctx.guild.id,))
            if not data:
                return await ctx.send("I have no data at all for this server... Weird")
            block = "```fix\n"
            un = []   # User names
            xp = []   # XP
            # unl = []  # User name lengths
            xpl = []  # XP string lengths
            for user in data:
                name = f"{user['name']}#{str(user['disc']).zfill(4)}"
                un.append(name)
                # unl.append(len(name))
                val = f"{value_string(user['xp'])}"
                xp.append(val)
                xpl.append(len(val))
            spaces = max(xpl) + 5
            place = "unknown, or over 250"
            for x in range(len(data)):
                if data[x]['user_id'] == ctx.author.id:
                    place = f"#{x + 1}"
                    break
            for i, val in enumerate(data[:10], start=1):
                k = i - 1
                who = un[k]
                if val['user_id'] == ctx.author.id:
                    who = f"-> {who}"
                s = ' '
                sp = xpl[k]
                block += f"{str(i).zfill(2)}){s*4}{xp[k]}{s*(spaces-sp)}{who}\n"
            return await ctx.send(f"Top users in {ctx.guild.name} - Sorted by XP\nYour place: {place}\n{block}```")

    @commands.command(name="addxp")
    @commands.guild_only()
    async def add_xp(self, ctx, user: discord.Member, amount: float):
        """ Add XP to a user """
        data = self.db.fetchrow("SELECT * FROM leveling WHERE user_id=? AND guild_id=?", (user.id, ctx.guild.id))
        xp = data['xp'] if data else 0
        xp += amount
        if data:
            yes = self.db.execute("UPDATE leveling SET xp=? WHERE user_id=? AND guild_id=?",
                                  (xp, user.id, ctx.guild.id))
        else:
            yes = self.db.execute("INSERT INTO leveling VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (user.id, ctx.guild.id, 0, xp, 0, user.name, user.discriminator))
        return await ctx.send(f"Added {amount:,.0f} XP to {user.name} in {ctx.guild.name}.\n{yes}")


def setup(bot):
    bot.add_cog(Leveling(bot))
