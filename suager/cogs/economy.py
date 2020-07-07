import asyncio
import json

import discord
from discord.ext import commands

from core.utils import database, general, emotes

default_currency = "€"


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database(self.bot.name)

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
        user = who or ctx.author
        if user.bot:
            return await general.send("Bots are cheating, so I don't count their money.", ctx.channel)
        data = self.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data:
            return await general.send(f"{user.name} doesn't seem to have any money.", ctx.channel)
        currency = self.get_currency(ctx.guild.id)
        return await general.send(f"{user.name} has {data['money']:,}{currency} in {ctx.guild.name}", ctx.channel)

    @commands.command(name="donate", aliases=["give"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def donate(self, ctx: commands.Context, user: discord.Member, amount: int):
        """ Give someone your money """
        if amount < 0:
            return await general.send(f"Nice try, {ctx.author.name}", ctx.channel)
        if user == ctx.author:
            return await general.send("What's the point of donating money to yourself?", ctx.channel)
        if user.bot:
            return await general.send("I don't count bots' money, so you can't give them any.", ctx.channel)
        data1 = self.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        data2 = self.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data1:
            return await general.send("It appears that you don't have any money to begin with...", ctx.channel)
        if data1['money'] - amount < 0:
            return await general.send(f"{ctx.author.name}, you don't have enough money to do that", ctx.channel)
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
        greed = ". How generous" if amount == 0 else ""
        return await general.send(f"{ctx.author.name} just gave {amount:,}{currency} to {user.name}{greed} {emotes.AlexHeart}", ctx.channel)

    @commands.command(name="profile")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def profile(self, ctx: commands.Context, who: discord.Member = None):
        """ Check someone's profile """
        user = who or ctx.author
        is_self = user.id == self.bot.user.id
        if user.bot and not is_self:
            return await general.send("Bots are cheating, so I don't count their money.", ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        embed.set_thumbnail(url=user.avatar_url)
        embed.title = f"**{user.name}**'s profile in **{ctx.guild.name}**"
        if is_self:
            if ctx.author.id in self.bot.config["owners"]:
                embed.add_field(name="Balance", value="Higher than others'", inline=False)
                embed.add_field(name="Donated", value="Never bothered counting", inline=False)
            else:
                embed.add_field(name="Balance", value="Higher than yours", inline=False)
                embed.add_field(name="Donated", value="More than you ever will", inline=False)
        else:
            data = self.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
            if not data:
                return await general.send(f"{user.name} has no money...", ctx.channel)
            r1 = f"{data['money']:,}"
            r2 = f"{data['donated']:,}"
            currency = self.get_currency(ctx.guild.id)
            embed.add_field(name="Balance", value=f"{r1}{currency}", inline=False)
            embed.add_field(name="Donated", value=f"{r2}{currency}", inline=False)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="buy")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.user)
    async def buy_something(self, ctx: commands.Context, *, role: discord.Role):
        """ Buy a role from the shop """
        settings = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not settings:
            return await general.send("This server doesn't sell anything", ctx.channel)
        data = json.loads(settings["data"])
        user = self.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not user:
            return await general.send("You don't seem to have any money to begin with.", ctx.channel)
        try:
            try:
                currency = data["currency"]
            except KeyError:
                currency = default_currency
            rewards = data['shop_items']
            roles = [r["role"] for r in rewards]
            if role.id not in roles:
                return await general.send(f"The role {role.name} is not available for purchase.", ctx.channel)
            _role = [r for r in rewards if r["role"] == role.id][0]
            if role in ctx.author.roles:
                return await general.send(f"You already have the role {role.name}", ctx.channel)
            if user["money"] < _role["cost"]:
                return await general.send(f"You don't have enough money to buy {role.name} ({user['money']:,}/{_role['cost']:,}{currency})", ctx.channel)

            def check_confirm(m):
                if m.author == ctx.author and m.channel == ctx.channel:
                    if m.content.startswith("yes"):
                        return True
                return False
            confirm_msg = await general.send(f"{ctx.author.name}, are you sure you want to buy the role {role.name} for {_role['cost']:,}{currency}? "
                                             f"Type `yes` to confirm.", ctx.channel)
            try:
                await self.bot.wait_for('message', timeout=30.0, check=check_confirm)
            except asyncio.TimeoutError:
                content = f"~~{confirm_msg.clean_content}~~\nNo response. Guess not."
                return await confirm_msg.edit(content=content)
            await ctx.author.add_roles(role, reason="Bought role")
            user["money"] -= _role["cost"]
            self.db.execute("UPDATE economy SET money=? WHERE uid=? AND gid=?", (user["money"], ctx.author.id, ctx.guild.id))
            return await general.send(f"{ctx.author.name} just bought the role {role.name} for {_role['cost']}{currency}", ctx.channel)
        except KeyError:
            return await general.send("This server doesn't seem to sell anything", ctx.channel)
        except discord.Forbidden:
            return await general.send("I don't seem to have the permissions to give you the role. Contact the server's admins.", ctx.channel)

    @commands.command(name="shop")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def item_shop(self, ctx: commands.Context):
        """ Item shop """
        settings = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not settings:
            return await general.send("This server doesn't sell anything", ctx.channel)
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
            embed.title = f"The {ctx.guild.name} Shop"
            d = ''
            for role in rewards:
                d += f"<@&{role['role']}>: {role['cost']:,}{currency}"
            embed.description = d
            return await general.send(None, ctx.channel, embed=embed)
        except KeyError:
            return await general.send("This server doesn't sell anything", ctx.channel)

    @commands.command(name="bank")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def money_lb(self, ctx: commands.Context, top: str = ""):
        """ Server's money Leaderboard """
        data = self.db.fetch("SELECT * FROM economy WHERE gid=? AND money!=0 AND disc!=0 ORDER BY money DESC", (ctx.guild.id,))
        if not data:
            return await general.send("I have no data saved for this server so far.", ctx.channel)
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
        return await general.send(f"Top users in {ctx.guild.name} - Sorted by balance\nYour place: {place}\nShowing places {start:,} to {start + 9:,} of "
                                  f"{total}\n{block}```", ctx.channel)


def setup(bot):
    bot.add_cog(Economy(bot))
