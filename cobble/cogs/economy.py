import random
from textwrap import wrap

import discord
from discord.ext import commands

from core.utils import general, time
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
    @commands.cooldown(rate=1, per=300, type=commands.BucketType.user)
    async def work(self, ctx: commands.Context):
        """ Earn some money for yourself """
        locale = langs.gl(ctx)
        returns = langs.get_data("economy_work", locale)
        data = self.bot.db.fetchrow("SELECT * FROM economy WHERE uid=?", (ctx.author.id,))
        if not data:
            return await general.send(langs.gls("economy_work_none", locale), ctx.channel)
        earn = random.randint(100, 270)
        self.bot.db.execute("UPDATE economy SET money=money+? WHERE uid=?", (earn, ctx.author.id))
        return await general.send((random.choice(returns)).format(ctx.author.name, f"{langs.gns(earn, locale)}{currency}"), ctx.channel)
        # return await general.send("Soon™", ctx.channel)

    @commands.command(name="daily")
    @commands.cooldown(rate=1, per=300, type=commands.BucketType.user)
    async def daily(self, ctx: commands.Context):
        """ Earn a daily bonus """
        locale = langs.gl(ctx)
        data = self.bot.db.fetchrow("SELECT * FROM economy WHERE uid=?", (ctx.author.id,))
        if not data:
            return await general.send(langs.gls("economy_work_none", locale), ctx.channel)
        base = 500
        when = data["daily"] // 86400
        now = int(time.now_ts()) // 86400
        if when == now:
            return await general.send(langs.gls("economy_daily_already", locale, ctx.author, langs.gts_date(time.now(None), locale, False, True)), ctx.channel)
        diff = now - when
        streak = 1 if diff > 1 else data["streak"] + 1
        bonus = 0 if streak < 7 else 15 * streak
        total = base + bonus
        self.bot.db.execute("UPDATE economy SET money=money+?, daily=?, streak=? WHERE uid=?", (total, int(time.now_ts()), streak, ctx.author.id))
        return await general.send(langs.gls("economy_daily", locale, ctx.author.name, f"{langs.gns(total, locale)}{currency}"), ctx.channel)
        # return await general.send("Soon™", ctx.channel)

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
        data1 = self.bot.db.fetchrow("SELECT * FROM economy WHERE uid=?", (ctx.author.id,))
        data2 = self.bot.db.fetchrow("SELECT * FROM economy WHERE uid=?", (user.id,))
        if not data2:
            return await general.send("Target user does not have an account, cannot transfer money.", ctx.channel)
        if not data1 or data1["money"] - amount < 0:
            return await general.send(langs.gls("economy_donate_not_enough", locale, ctx.author.name), ctx.channel)
        money1, money2 = [data1['money'], data2['money']]
        money1 -= amount
        money2 += amount
        self.bot.db.execute("UPDATE economy SET money=? WHERE uid=?", (money1, ctx.author.id))
        self.bot.db.execute("UPDATE economy SET money=? WHERE uid=?", (money2, user.id))
        # self.bot.db.execute("INSERT INTO economy VALUES (?, ?, ?, ?, ?, ?, ?)", (user.id, ctx.guild.id, money2, 0, 0, user.name, user.discriminator))
        greed = langs.gls("economy_donate_zero", locale) if amount == 0 else ""
        return await general.send(langs.gls("economy_donate", locale, ctx.author, langs.gns(amount, locale), currency, user.name, greed), ctx.channel)

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
            return await general.send(langs.gls("economy_balance_data", locale, user.name, langs.gns(data["money"], locale), currency), ctx.channel)


def setup(bot):
    bot.add_cog(Economy(bot))
