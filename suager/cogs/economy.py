import json
from textwrap import wrap

import discord
from discord.ext import commands

from core.utils import general
from languages import langs

currency = "€"


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="create")
    @commands.cooldown(rate=1, per=3600, type=commands.BucketType.user)
    async def create_bank(self, ctx: commands.Context):
        """ Create an account in your server """
        locale = langs.gl(ctx)
        data = self.bot.db.fetchrow("SELECT * FROM economy WHERE uid=?", (ctx.author.id,))
        if data:
            return await general.send(langs.gls("economy_create_already", locale), ctx.channel)
        val = f"{ctx.author.id % 10000000000000000:016d}"
        m1 = str(round(int((float(f"27281120{val[0]}") % 97) / 97 * 1000) * 0.097))
        l1 = len(m1) == 1
        m2 = str(round(int((float(f"{m1}{val[1:(i1 := 8 + l1)]}") % 97) / 97 * 1000) * 0.097))
        l2 = len(m2) == 1
        m3 = str(round(int((float(f"{m2}{val[i1:(i2 := 15 + l1 + l2)]}") % 97) / 97 * 1000) * 0.097))
        l3 = len(m3) == 1
        m4 = 98 - round(int((float(f"{m3}{val[i2:(22 + l1 + l2 + l3)]}") % 97) / 97 * 1000) * 0.097)
        rsbk = f"KA{m4:02d} RSVK {' '.join(wrap(val, 4))}"
        self.bot.db.execute("INSERT INTO economy VALUES (?, ?, ?, ?, ?, ?, ?)", (ctx.author.id, 500, 1, 0, rsbk, ctx.author.name, ctx.author.discriminator))
        return await general.send(langs.gls("economy_create", locale, ctx.author.name, rsbk, ctx.prefix), ctx.channel)

    @commands.command(name="code")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def code(self, ctx: commands.Context, who: discord.User = None):
        """ RSVK """
        user = who or ctx.author
        data = self.bot.db.fetchrow("SELECT * FROM economy WHERE uid=?", (user.id,))
        if not data:
            return await general.send("Unknown", ctx.channel)
        return await general.send(data["rsbk"], ctx.channel)

    @commands.command(name="work")
    @commands.command(rate=1, per=300, type=commands.BucketType.user)
    async def work(self, ctx: commands.Context):
        """ Earn some money for yourself """
        return await general.send("Soon™", ctx.channel)

    @commands.command(name="daily")
    @commands.command(rate=1, per=300, type=commands.BucketType.user)
    async def daily(self, ctx: commands.Context):
        """ Earn a daily bonus """
        return await general.send("Soon™", ctx.channel)

    # @commands.command(name="donate", aliases=["give"])
    # @commands.guild_only()
    # @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    # async def donate(self, ctx: commands.Context, user: discord.Member, amount: int):
    #     """ Give someone your money """
    #     locale = langs.gl(ctx)
    #     if amount < 0:
    #         return await general.send(langs.gls("economy_donate_negative", locale, ctx.author.name), ctx.channel)
    #     if user == ctx.author:
    #         return await general.send(langs.gls("economy_donate_self", locale, ctx.author.name), ctx.channel)
    #    if user.bot:
    #          return await general.send(langs.gls("economy_balance_bots", locale), ctx.channel)
    #     data1 = self.bot.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
    #     data2 = self.bot.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
    #     if not data1 or data1["money"] - amount < 0:
    #         return await general.send(langs.gls("economy_donate_not_enough", locale, ctx.author.name), ctx.channel)
    #     money1, money2, donated1 = [data1['money'], data2['money'], data1['donated']]
    #     money1 -= amount
    #     donated1 += amount
    #     money2 += amount
    #     self.bot.db.execute("UPDATE economy SET money=?, donated=? WHERE uid=? AND gid=?", (money1, donated1, ctx.author.id, ctx.guild.id))
    #     if data2:
    #         self.bot.db.execute("UPDATE economy SET money=? WHERE uid=? AND gid=?", (money2, user.id, ctx.guild.id))
    #     else:
    #         self.bot.db.execute("INSERT INTO economy VALUES (?, ?, ?, ?, ?, ?, ?)", (user.id, ctx.guild.id, money2, 0, 0, user.name, user.discriminator))
    #     currency = get_currency()
    #     pre, suf = get_ps(currency)
    #     greed = langs.gls("economy_donate_zero", locale) if amount == 0 else ""
    #     return await general.send(langs.gls("economy_donate", locale, ctx.author, pre, langs.gns(amount, locale), suf, user.name, greed), ctx.channel)

    @commands.command(name="balance", aliases=["bal"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def balance(self, ctx: commands.Context, who: discord.User = None):
        """ See how much money you have """
        locale = langs.gl(ctx)
        user = who or ctx.author
        is_self = user.id == self.bot.user.id
        if user.bot and not is_self:
            return await general.send(langs.gls("economy_balance_bots", locale), ctx.channel)
        if is_self:
            return await general.send(langs.gls("economy_balance_self", locale), ctx.channel)
        else:
            data = self.bot.db.fetchrow("SELECT * FROM economy WHERE uid=?", (user.id,))
            if not data:
                return await general.send(langs.gls("economy_balance_none", locale, user.name), ctx.channel)
            return await general.send(langs.gls("economy_balance_data", locale, user.name, ctx.guild.name, langs.gns(data["money"], locale), currency),
                                      ctx.channel)

    # @commands.command(name="buy")
    # @commands.guild_only()
    # @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    # @commands.max_concurrency(1, per=commands.BucketType.user)
    # async def buy_something(self, ctx: commands.Context, *, role: discord.Role):
    #     """ Buy a role from the shop """
    #     locale = langs.gl(ctx)
    #     settings = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
    #     if not settings:
    #         return await general.send(langs.gls("economy_shop_empty", locale), ctx.channel)
    #     data = json.loads(settings["data"])
    #     user = self.bot.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
    #     if not user:
    #        return await general.send(langs.gls("economy_buy_no_money", locale), ctx.channel)
    #     try:
    #         rewards = data['shop_items']
    #         roles = [r["role"] for r in rewards]
    #         if role.id not in roles:
    #             return await general.send(langs.gls("economy_buy_unavailable", locale, role.name), ctx.channel)
    #         _role = [r for r in rewards if r["role"] == role.id][0]
    #         if role in ctx.author.roles:
    #             return await general.send(langs.gls("economy_buy_already", locale, role.name), ctx.channel)
    #         cost = langs.gns(_role["cost"], locale)
    #         if user["money"] < _role["cost"]:
    #           return await general.send(langs.gls("economy_buy_not_enough", locale, role.name, langs.gns(user["money"], locale), cost, currency), ctx.channel)

    #         def check_confirm(m):
    #             if m.author == ctx.author and m.channel == ctx.channel:
    #                 if m.content.startswith("yes"):
    #                     return True
    #             return False
    #         confirm_msg = await general.send(langs.gls("economy_buy_confirm", locale, ctx.author.name, role.name, cost, currency), ctx.channel)
    #         try:
    #             await self.bot.wait_for('message', timeout=30.0, check=check_confirm)
    #         except asyncio.TimeoutError:
    #             return await confirm_msg.edit(content=langs.gls("generic_timeout", locale, confirm_msg.clean_content))
    #         await ctx.author.add_roles(role, reason="Bought role")
    #         user["money"] -= _role["cost"]
    #         self.bot.db.execute("UPDATE economy SET money=? WHERE uid=? AND gid=?", (user["money"], ctx.author.id, ctx.guild.id))
    #         return await general.send(langs.gls("economy_buy", locale, ctx.author.name, role.name, cost, currency), ctx.channel)
    #     except KeyError:
    #         return await general.send(langs.gls("economy_shop_empty", locale), ctx.channel)
    #     except discord.Forbidden:
    #         return await general.send(langs.gls("economy_buy_forbidden", locale), ctx.channel)

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
            rewards = data['shop_items']
            rewards.sort(key=lambda x: x['cost'])
            embed = discord.Embed(colour=general.random_colour())
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.title = langs.gls("economy_shop_server", locale, ctx.guild.name)
            d = ''
            for role in rewards:
                d += f"<@&{role['role']}>: {langs.gns(role['cost'])}{currency}\n"
            embed.description = d
            if not embed.description:
                embed.description = langs.gls("economy_shop_empty", locale)
            return await general.send(None, ctx.channel, embed=embed)
        except KeyError:
            return await general.send(langs.gls("economy_shop_empty", locale), ctx.channel)


def setup(bot):
    bot.add_cog(Economy(bot))
