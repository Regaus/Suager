import random

import discord
from discord.ext import commands

from beta import main
from beta.stuff import soon
from utils import time, emotes, database
from utils.generic import value_string, random_colour, get_config

money_amounts = [50, 100]
currency = "€"


class Economy(commands.Cog):
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
            data = self.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
            if data:
                xp, last = [data['money'], data['last']]
            else:
                xp, last = [0, 0]
            now = time.now_ts()
            if last > now - 60:
                return
            x1, x2 = money_amounts
            # biased = bias.get_bias(self.db, ctx.author)
            new = random.randint(x1, x2)
            xp += new
            if data:
                self.db.execute("UPDATE economy SET money=?, last=?, name=?, disc=? "
                                "WHERE uid=? AND gid=?",
                                (xp, now, ctx.author.name, ctx.author.discriminator, ctx.author.id, ctx.guild.id))
            else:
                self.db.execute("INSERT INTO economy VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (ctx.author.id, ctx.guild.id, xp, now, 0, ctx.author.name, ctx.author.discriminator))

    @commands.command(name="balance", aliases=["bal"])
    @commands.guild_only()
    async def balance(self, ctx, *, who: discord.Member = None):
        """ Check someone's balance"""
        if ctx.channel.id in self.banned:
            return
        user = who or ctx.author
        if user.bot:
            return await ctx.send("Bots can't have any money, cuz they're cheaters. I get my money from Regaus, dw.")
        data = self.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data:
            return await ctx.send(f"Doesn't appear like {user.name} has anything at all...")
        return await ctx.send(f"**{user.name}** has **{value_string(data['money'], big=True)}{currency}** "
                              f"in **{ctx.guild.name}**")

    @commands.command(name="donate", aliases=["give"])
    @commands.guild_only()
    async def donate(self, ctx, user: discord.Member, amount: int):
        """ Give someone your money """
        if ctx.channel.id in self.banned:
            return
        if amount < 0:
            return await ctx.send(f"Nice try, {ctx.author.name}")
        if user == ctx.author:
            return await ctx.send(f"{user.name}, giving money to yourself? Greedy.")
        if user.bot:
            return await ctx.send("Bots can't have any money, cuz they're cheaters. I get my money from Regaus, dw.")
        data1 = self.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        data2 = self.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not data1:
            return await ctx.send("I don't have any data saved for you, and you already trying to give money?")
        if data1['money'] - amount < 0:
            return await ctx.send(f"{ctx.author.name}, it doesn't seem like you have enough money to do that rn.")
        money1, money2, donated1 = [data1['money'], data2['money'], data1['donated']]
        money1 -= amount
        donated1 += amount
        money2 += amount
        self.db.execute("UPDATE economy SET money=?, donated=? WHERE uid=? AND gid=?",
                        (money1, donated1, ctx.author.id, ctx.guild.id))
        if data2:
            self.db.execute("UPDATE economy SET money=? WHERE uid=? AND gid=?",
                            (money2, user.id, ctx.guild.id))
        else:
            self.db.execute("INSERT INTO economy VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (user.id, ctx.guild.id, money2, 0, 0, user.name, user.discriminator))
        return await ctx.send(f"{ctx.author.name} just gave {amount}{currency} to {user.name}. {emotes.AlexHeart}")

    @commands.command(name="profile")
    @commands.guild_only()
    async def profile(self, ctx, who: discord.Member = None):
        """ Check someone's profile """
        if ctx.channel.id in self.banned:
            return
        user = who or ctx.author
        is_self = user.id == self.bot.user.id
        if user.bot and not is_self:
            return await ctx.send("Bots can't have any money, cuz they're cheaters. I get my money from Regaus, dw.")
        embed = discord.Embed(colour=random_colour())
        embed.set_thumbnail(url=user.avatar_url)
        if is_self:
            if ctx.author.id in get_config().owners:
                embed.add_field(name="Money", value="I have enough, thanks for asking.", inline=False)
                embed.add_field(name="Donated", value="Never counted tbh", inline=False)
            else:
                embed.add_field(name="Money", value="More than you", inline=False)
                embed.add_field(name="Donated", value="More than you", inline=False)
        else:
            data = self.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
            if not data:
                return await ctx.send(f"I ain't sure if {user.name} has anything at all...")
            r1 = value_string(data['money'], big=True)
            r2 = value_string(data['donated'], big=True)
            embed.add_field(name="Money", value=f"{r1}{currency}", inline=False)
            embed.add_field(name="Donated", value=f"{r2}{currency}", inline=False)
        return await ctx.send(f"**{user.name}'s** profile in **{ctx.guild.name}**", embed=embed)

    @commands.command(name="buy")
    @commands.guild_only()
    async def buy_something(self, ctx):
        """ Buy an item from the shop """
        if ctx.channel.id in self.banned:
            return
        return await ctx.send(soon)

    @commands.command(name="shop")
    @commands.guild_only()
    async def item_shop(self, ctx):
        """ Item shop """
        if ctx.channel.id in self.banned:
            return
        return await ctx.send(soon)


def setup(bot):
    bot.add_cog(Economy(bot))
