import asyncio
import json

import discord
from discord.ext import commands

from core.utils import general
from languages import langs

default_currency = "€"


def get_ps(currency):
    return (currency, "") if len(currency) == 1 else ("", currency)


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_currency(self, gid):
        settings = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (gid,))
        if not settings:
            currency = default_currency
        else:
            try:
                setting = json.loads(settings["data"])
                currency = setting["currency"]
            except KeyError:
                currency = default_currency
        return currency

    @commands.command(name="balance", aliases=["bal"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def balance(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Check someone's balance"""
        locale = langs.gl(ctx)
        user = who or ctx.author
        if user.bot:
            return await general.send(langs.gls("economy_balance_bots", locale), ctx.channel)
        data = self.bot.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data:
            return await general.send(langs.gls("economy_balance_none", locale, user.name), ctx.channel)
        currency = self.get_currency(ctx.guild.id)
        pre, suf = get_ps(currency)
        return await general.send(langs.gls("economy_balance", locale, user.name, ctx.guild.name, langs.gns(data["money"], locale), pre, suf), ctx.channel)

    @commands.command(name="donate", aliases=["give"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def donate(self, ctx: commands.Context, user: discord.Member, amount: int):
        """ Give someone your money """
        locale = langs.gl(ctx)
        if amount < 0:
            return await general.send(langs.gls("economy_donate_negative", locale, ctx.author.name), ctx.channel)
        if user == ctx.author:
            return await general.send(langs.gls("economy_donate_self", locale, ctx.author.name), ctx.channel)
        if user.bot:
            return await general.send(langs.gls("economy_balance_bots", locale), ctx.channel)
        data1 = self.bot.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        data2 = self.bot.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data1 or data1["money"] - amount < 0:
            return await general.send(langs.gls("economy_donate_not_enough", locale, ctx.author.name), ctx.channel)
        money1, money2, donated1 = [data1['money'], data2['money'], data1['donated']]
        money1 -= amount
        donated1 += amount
        money2 += amount
        self.bot.db.execute("UPDATE economy SET money=?, donated=? WHERE uid=? AND gid=?", (money1, donated1, ctx.author.id, ctx.guild.id))
        if data2:
            self.bot.db.execute("UPDATE economy SET money=? WHERE uid=? AND gid=?", (money2, user.id, ctx.guild.id))
        else:
            self.bot.db.execute("INSERT INTO economy VALUES (?, ?, ?, ?, ?, ?, ?)", (user.id, ctx.guild.id, money2, 0, 0, user.name, user.discriminator))
        currency = self.get_currency(ctx.guild.id)
        pre, suf = get_ps(currency)
        greed = langs.gls("economy_donate_zero", locale) if amount == 0 else ""
        return await general.send(langs.gls("economy_donate", locale, ctx.author, pre, langs.gns(amount, locale), suf, user.name, greed), ctx.channel)

    @commands.command(name="profile")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def profile(self, ctx: commands.Context, who: discord.Member = None):
        """ Check someone's profile """
        locale = langs.gl(ctx)
        user = who or ctx.author
        is_self = user.id == self.bot.user.id
        if user.bot and not is_self:
            return await general.send("Bots are cheating, so I don't count their money.", ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        embed.set_thumbnail(url=user.avatar_url)
        embed.title = langs.gls("economy_profile", locale, user.name, ctx.guild.name)
        if is_self:
            embed.add_field(name=langs.gls("economy_profile_balance", locale), value=langs.gls("economy_profile_balance_self", locale), inline=False)
            embed.add_field(name=langs.gls("economy_profile_donated", locale), value=langs.gls("economy_profile_donated_self", locale), inline=False)
        else:
            data = self.bot.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
            if not data:
                return await general.send(langs.gls("economy_balance_none", locale, user.name), ctx.channel)
            currency = self.get_currency(ctx.guild.id)
            pre, suf = get_ps(currency)
            r1 = f"{pre}{langs.gns(data['money'], locale)}{suf}"
            r2 = f"{pre}{langs.gns(data['donated'], locale)}{suf}"
            embed.add_field(name=langs.gls("economy_profile_balance", locale), value=r1, inline=False)
            embed.add_field(name=langs.gls("economy_profile_donated", locale), value=r2, inline=False)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="buy")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.user)
    async def buy_something(self, ctx: commands.Context, *, role: discord.Role):
        """ Buy a role from the shop """
        locale = langs.gl(ctx)
        settings = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not settings:
            return await general.send(langs.gls("economy_shop_empty", locale), ctx.channel)
        data = json.loads(settings["data"])
        user = self.bot.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not user:
            return await general.send(langs.gls("economy_buy_no_money", locale), ctx.channel)
        try:
            try:
                currency = data["currency"]
            except KeyError:
                currency = default_currency
            pre, suf = get_ps(currency)
            rewards = data['shop_items']
            roles = [r["role"] for r in rewards]
            if role.id not in roles:
                return await general.send(langs.gls("economy_buy_unavailable", locale, role.name), ctx.channel)
            _role = [r for r in rewards if r["role"] == role.id][0]
            if role in ctx.author.roles:
                return await general.send(langs.gls("economy_buy_already", locale, role.name), ctx.channel)
            cost = langs.gns(_role["cost"], locale)
            if user["money"] < _role["cost"]:
                return await general.send(langs.gls("economy_buy_not_enough", locale, role.name, langs.gns(user["money"], locale), cost, pre, suf), ctx.channel)

            def check_confirm(m):
                if m.author == ctx.author and m.channel == ctx.channel:
                    if m.content.startswith("yes"):
                        return True
                return False
            confirm_msg = await general.send(langs.gls("economy_buy_confirm", locale, ctx.author.name, role.name, pre, cost, suf), ctx.channel)
            try:
                await self.bot.wait_for('message', timeout=30.0, check=check_confirm)
            except asyncio.TimeoutError:
                return await confirm_msg.edit(content=langs.gls("generic_timeout", locale, confirm_msg.clean_content))
            await ctx.author.add_roles(role, reason="Bought role")
            user["money"] -= _role["cost"]
            self.bot.db.execute("UPDATE economy SET money=? WHERE uid=? AND gid=?", (user["money"], ctx.author.id, ctx.guild.id))
            return await general.send(langs.gls("economy_buy", locale, ctx.author.name, role.name, pre, cost, suf), ctx.channel)
        except KeyError:
            return await general.send(langs.gls("economy_shop_empty", locale), ctx.channel)
        except discord.Forbidden:
            return await general.send(langs.gls("economy_buy_forbidden", locale), ctx.channel)

    @commands.command(name="shop")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def item_shop(self, ctx: commands.Context):
        """ Item shop """
        locale = langs.gl(ctx)
        settings = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not settings:
            return await general.send(langs.gls("economy_shop_empty", locale), ctx.channel)
        data = json.loads(settings["data"])
        try:
            try:
                currency = data["currency"]
            except KeyError:
                currency = default_currency
            rewards = data['shop_items']
            rewards.sort(key=lambda x: x['cost'])
            embed = discord.Embed(colour=general.random_colour())
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.title = langs.gls("economy_shop_server", locale, ctx.guild.name)
            pre, suf = get_ps(currency)
            d = ''
            for role in rewards:
                d += f"<@&{role['role']}>: {pre}{langs.gns(role['cost'])}{suf}\n"
            embed.description = d
            return await general.send(None, ctx.channel, embed=embed)
        except KeyError:
            return await general.send(langs.gls("economy_shop_empty", locale), ctx.channel)

    @commands.command(name="bank")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def money_lb(self, ctx: commands.Context, top: str = ""):
        """ Server's money Leaderboard """
        locale = langs.gl(ctx)
        data = self.bot.db.fetch("SELECT * FROM economy WHERE gid=? AND money!=0 AND disc!=0 ORDER BY money DESC", (ctx.guild.id,))
        if not data:
            return await general.send(langs.gls("leaderboards_no_data", locale), ctx.channel)
        block = "```fix\n"
        un = []   # User names
        xp = []   # XP
        xpl = []  # XP string lengths
        for user in data:
            name = f"{user['name']}#{user['disc']:04d}"
            un.append(name)
            val = langs.gns(user["money"], locale)
            xp.append(val)
            xpl.append(len(val))
        total = len(xp)
        place = langs.gls("generic_unknown", locale)
        n = 0
        for x in range(len(data)):
            if data[x]['uid'] == ctx.author.id:
                place = langs.gls("leaderboards_place", locale, langs.gns(x + 1, locale, 0, False))
                n = x + 1
                break
        try:
            page = int(top)
            if page < 1:
                page = None
        except ValueError:
            page = None
        start = 0
        try:
            if (n <= 10 or top.lower() == "top") and page is None:
                _data = data[:10]
                start = 1
                spaces = max(xpl[:10]) + 5
            elif page is not None:
                _data = data[(page - 1)*10:page*10]
                start = page * 10 - 9
                spaces = max(xpl[(page - 1)*10:page*10]) + 5
            else:
                _data = data[n-5:n+5]
                start = n - 4
                spaces = max(xpl[n-5:n+5]) + 5
            s = ' '
            for i, val in enumerate(_data, start=start):
                k = i - 1
                who = un[k]
                if val['uid'] == ctx.author.id:
                    who = f"-> {who}"
                sp = xpl[k]
                # block += f"{i:2d}){s*4}{xp[k]}{s*(spaces-sp)}{who}\n"
                block += f"{langs.gns(i, locale, 2, False)}){s*4}{xp[k]}{s*(spaces-sp)}{who}\n"
        except (ValueError, IndexError):
            block += "No data available"
        s, e, t = langs.gns(start, locale), langs.gns(start + 9, locale), langs.gns(total, locale)
        return await general.send(langs.gls("leaderboards_bank", locale, ctx.guild.name, place, s, e, t, block), ctx.channel)


def setup(bot):
    bot.add_cog(Economy(bot))
