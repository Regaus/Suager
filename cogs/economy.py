import asyncio
import json

import discord
from discord.ext import commands

from utils import database, generic
from utils.generic import random_colour, get_config

default_currency = "€"


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database()

    def get_currency(self, gid):
        settings = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (gid,))
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
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def balance(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Check someone's balance"""
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "balance"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        user = who or ctx.author
        if user.bot:
            return await generic.send(generic.gls(locale, "bots_money"), ctx.channel)
        data = self.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data:
            return await generic.send(generic.gls(locale, "no_money", [user.name]), ctx.channel)
        currency = self.get_currency(ctx.guild.id)
        return await generic.send(generic.gls(locale, "balance", [user.name, f"{data['money']:,}", currency, ctx.guild.name]), ctx.channel)

    @commands.command(name="donate", aliases=["give"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def donate(self, ctx: commands.Context, user: discord.Member, amount: int):
        """ Give someone your money """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "donate"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        if amount < 0:
            return await generic.send(generic.gls(locale, "donate_negative", [ctx.author.name]), ctx.channel)
        if user == ctx.author:
            return await generic.send(generic.gls(locale, "donate_self", [user.name]), ctx.channel)
        if user.bot:
            return await generic.send(generic.gls(locale, "bots_money"), ctx.channel)
        data1 = self.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        data2 = self.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data1:
            return await generic.send(generic.gls(locale, "no_money2"), ctx.channel)
        if data1['money'] - amount < 0:
            return await generic.send(generic.gls(locale, "no_money3", [ctx.author.name]), ctx.channel)
        money1, money2, donated1 = [data1['money'], data2['money'], data1['donated']]
        money1 -= amount
        donated1 += amount
        money2 += amount
        self.db.execute("UPDATE economy SET money=?, donated=? WHERE uid=? AND gid=?", (money1, donated1, ctx.author.id, ctx.guild.id))
        if data2:
            self.db.execute("UPDATE economy SET money=? WHERE uid=? AND gid=?", (money2, user.id, ctx.guild.id))
        else:
            self.db.execute("INSERT INTO economy VALUES (?, ?, ?, ?, ?, ?, ?)", (user.id, ctx.guild.id, money2, 0, 0, user.name, user.discriminator))
        currency = self.get_currency(ctx.guild.id)
        return await generic.send(generic.gls(locale, "donate_yes", [ctx.author.name, f"{amount:,}", currency, user.name]), ctx.channel)

    @commands.command(name="profile")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def profile(self, ctx: commands.Context, who: discord.Member = None):
        """ Check someone's profile """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "profile"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        user = who or ctx.author
        is_self = user.id == self.bot.user.id
        if user.bot and not is_self:
            return await generic.send(generic.gls(locale, "bots_money"), ctx.channel)
        embed = discord.Embed(colour=random_colour())
        embed.set_thumbnail(url=user.avatar_url)
        if is_self:
            if ctx.author.id in get_config()["owners"]:
                embed.add_field(name=generic.gls(locale, "money"), value=generic.gls(locale, "money_self"), inline=False)
                embed.add_field(name=generic.gls(locale, "donated"), value=generic.gls(locale, "donated_self"), inline=False)
            else:
                embed.add_field(name=generic.gls(locale, "money"), value=generic.gls(locale, "more_than_you"), inline=False)
                embed.add_field(name=generic.gls(locale, "donated"), value=generic.gls(locale, "more_than_you2"), inline=False)
        else:
            data = self.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
            if not data:
                return await generic.send(generic.gls(locale, "no_money", [user.name]), ctx.channel)
            r1 = f"{data['money']:,}"
            r2 = f"{data['donated']:,}"
            currency = self.get_currency(ctx.guild.id)
            embed.add_field(name=generic.gls(locale, "money"), value=f"{r1}{currency}", inline=False)
            embed.add_field(name=generic.gls(locale, "donated"), value=f"{r2}{currency}", inline=False)
        return await generic.send(generic.gls(locale, "profile", [user.name, ctx.guild.name]), ctx.channel, embed=embed)

    @commands.command(name="buy")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def buy_something(self, ctx: commands.Context, *, role: discord.Role):
        """ Buy a role from the shop """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "buy"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        settings = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not settings:
            return await generic.send(generic.gls(locale, "shop_empty"), ctx.channel)
        data = json.loads(settings["data"])
        user = self.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not user:
            return await generic.send(generic.gls(locale, "buy_role_no5", [ctx.author.name]), ctx.channel)
        try:
            try:
                currency = data["currency"]
            except KeyError:
                currency = default_currency
            rewards = data['shop_items']
            roles = [r["role"] for r in rewards]
            if role.id not in roles:
                return await generic.send(generic.gls(locale, "buy_role_no", [ctx.author.name, role.name]), ctx.channel)
            _role = [r for r in rewards if r["role"] == role.id][0]
            if role in ctx.author.roles:
                return await generic.send(generic.gls(locale, "buy_role_no3", [ctx.author.name, role.name]), ctx.channel)
            if user["money"] < _role["cost"]:
                return await generic.send(generic.gls(locale, "buy_role_no4", [ctx.author.name, role.name, f'{user["money"]:,}',
                                                                               f'{_role["cost"]:,}', currency]), ctx.channel)

            def check_confirm(m):
                if m.author == ctx.author and m.channel == ctx.channel:
                    if m.content.startswith("yes"):
                        return True
                    if m.content.startswith("да"):
                        return True
                return False
            confirm_msg = await generic.send(generic.gls(locale, "buy_role_confirm", [ctx.author.name, role.name, f'{_role["cost"]:,}', currency]), ctx.channel)
            try:
                await self.bot.wait_for('message', timeout=30.0, check=check_confirm)
            except asyncio.TimeoutError:
                content = generic.gls(locale, "buy_role_no2", [confirm_msg.clean_content])
                return await confirm_msg.edit(content=content)
            await ctx.author.add_roles(role, reason="Bought role")
            user["money"] -= _role["cost"]
            self.db.execute("UPDATE economy SET money=? WHERE uid=? AND gid=?", (user["money"], ctx.author.id, ctx.guild.id))
            return await generic.send(generic.gls(locale, "buy_role_success", [ctx.author.name, role.name, f'{_role["cost"]:,}', currency]), ctx.channel)
        except KeyError:
            return await generic.send(generic.gls(locale, "shop_empty"), ctx.channel)
        except discord.Forbidden:
            return await generic.send(generic.gls(locale, "buy_role_forbidden"), ctx.channel)

    @commands.command(name="shop")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def item_shop(self, ctx: commands.Context):
        """ Item shop """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "shop"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        settings = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not settings:
            return await generic.send(generic.gls(locale, "shop_empty"), ctx.channel)
        data = json.loads(settings["data"])
        try:
            try:
                currency = data["currency"]
            except KeyError:
                currency = default_currency
            rewards = data['shop_items']
            rewards.sort(key=lambda x: x['cost'])
            embed = discord.Embed(colour=random_colour())
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.title = generic.gls(locale, "shop", [ctx.guild.name])
            d = ''
            for role in rewards:
                d += generic.gls(locale, "shop_item", [f'{role["cost"]}', role["role"], currency])
            embed.description = d
            return await generic.send(None, ctx.channel, embed=embed)
        except KeyError:
            return await generic.send(generic.gls(locale, "shop_empty"), ctx.channel)

    @commands.command(name="bank")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def money_lb(self, ctx: commands.Context, top: str = ""):
        """ Server's money Leaderboard """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "levels"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        data = self.db.fetch("SELECT * FROM economy WHERE gid=? AND money!=0 AND disc!=0 ORDER BY money DESC", (ctx.guild.id,))
        if not data:
            return await generic.send(generic.gls(locale, "levels_no_data"), ctx.channel)
        block = "```fix\n"
        un = []   # User names
        xp = []   # XP
        xpl = []  # XP string lengths
        for user in data:
            name = f"{user['name']}#{user['disc']:04d}"
            un.append(name)
            val = f"{user['money']:,}"
            xp.append(val)
            xpl.append(len(val))
        total = len(xp)
        place = "unknown"
        n = 0
        for x in range(len(data)):
            if data[x]['uid'] == ctx.author.id:
                place = f"#{x + 1}"
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
            for i, val in enumerate(_data, start=start):
                k = i - 1
                who = un[k]
                if val['uid'] == ctx.author.id:
                    who = f"-> {who}"
                s = ' '
                sp = xpl[k]
                block += f"{i:2d}){s*4}{xp[k]}{s*(spaces-sp)}{who}\n"
        except ValueError:
            block += "No data available"
        return await generic.send(generic.gls(locale, "economy_lb", [ctx.guild.name, place, block, start, start + 9, total]), ctx.channel)


def setup(bot):
    bot.add_cog(Economy(bot))
