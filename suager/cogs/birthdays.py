import asyncio
import random
import re
from datetime import datetime

import discord
from discord.ext import commands

from core.utils import permissions, general, time, database, emotes


class Birthdays(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.re_timestamp = r"^([0-2][0-9]|3[0-1])\/(0[1-9]|1[0-2])"
        self.db = database.Database(self.bot.name)
        self.bd_config = {568148147457490954: [568148147457490958, 663661621448802304]}

    @commands.Cog.listener()
    async def on_ready(self):
        while True:
            await asyncio.sleep(10)
            _guilds, _channels, _roles = [], [], []
            for guild, data in self.bd_config.items():
                _guilds.append(guild)
                _channels.append(data[0])
                _roles.append(data[1])
            guilds = [self.bot.get_guild(guild) for guild in _guilds]
            channels = [self.bot.get_channel(cid) for cid in _channels]
            roles = [discord.Object(id=rid) for rid in _roles]
            birthday_today = self.db.fetch("SELECT * FROM birthdays WHERE has_role=0 AND strftime('%m-%d', birthday) = strftime('%m-%d', 'now')")
            if birthday_today:
                for g in birthday_today:
                    self.db.execute("UPDATE birthdays SET has_role=1 WHERE uid=?", (g["uid"],))
                    for i in range(len(guilds)):
                        try:
                            guild = guilds[i]
                            if guild is not None:
                                user = guild.get_member(g["uid"])
                                if user is not None:
                                    await general.send(f"Happy birthday {user.mention}, have a nice birthday and enjoy your role today 🎂🎉",
                                                       channels[i], u=True)
                                    # await channels[i].send(f"Happy birthday {user.mention}, have a nice birthday and enjoy your role today 🎂🎉")
                                    await user.add_roles(roles[i], reason=f"{user} has birthday 🎂🎉")
                                    print(f"{time.time()} > {guild.name} > Gave birthday role to {user.name}")
                        except Exception as e:
                            print(e)
            birthday_over = self.db.fetch("SELECT * FROM birthdays WHERE has_role=1 AND strftime('%m-%d', birthday) != strftime('%m-%d', 'now')")
            for g in birthday_over:
                self.db.execute("UPDATE birthdays SET has_role=0 WHERE uid=?", (g["uid"],))
                for i in range(len(guilds)):
                    try:
                        guild = guilds[i]
                        user = guild.get_member(g["uid"])
                        if user is not None:
                            await user.remove_roles(roles[i], reason=f"It is no longer {user}'s birthday...")
                            print(f"{time.time()} > {guild.name} > Removed birthday role from {user.name}")
                    except Exception as e:
                        print(e)

    def check_birthday_noted(self, user_id):
        """ Convert timestamp string to datetime """
        data = self.db.fetchrow("SELECT * FROM birthdays WHERE uid=?", (user_id,))
        return data["birthday"] if data else None

    @commands.group(name="birthday", aliases=['b', 'bd', 'birth', 'day'], invoke_without_command=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.user)
    async def birthday(self, ctx: commands.Context, *, user: discord.User = None):
        """ Check your birthday or other people """
        if ctx.invoked_subcommand is None:
            user = user or ctx.author
            if user.id == self.bot.user.id:
                return await general.send(f"My birthday is on **13th May**, thanks for asking {emotes.AlexHeart}", ctx.channel)
            has_birthday = self.check_birthday_noted(user.id)
            if not has_birthday:
                return await general.send(f"{user.name} doesn't have their birthday saved.", ctx.channel)
            birthday = has_birthday.strftime("%d %B")
            if user == ctx.author:
                return await general.send(f"**Your** birthday is on **{birthday}**", ctx.channel)
            return await general.send(f"**{user.name}**'s birthday is on **{birthday}**", ctx.channel)

    @birthday.command(name="set")
    async def set(self, ctx: commands.Context, date: str):
        """ Set your birthday :) [DD/MM] """
        has_birthday = self.check_birthday_noted(ctx.author.id)
        if has_birthday:
            return await general.send(f"{ctx.author.name}, your birthday is already set to {has_birthday.strftime('%d %B')}. "
                                      f"Contact a bot admin to change this.", ctx.channel)
        confirm_code = random.randint(10000, 99999)

        def check_confirm(m):
            if m.author == ctx.author and m.channel == ctx.channel:
                if m.content.startswith(str(confirm_code)):
                    return True
            return False
        if re.compile(self.re_timestamp).search(date):
            timestamp = datetime.strptime(date + "/2020", "%d/%m/%Y")
        else:
            return await general.send("You need to enter a valid date with the command. Please note that the format is `DD/MM`.", ctx.channel)
        date = timestamp.strftime("%d %B")
        confirm_msg = await general.send(f"{ctx.author.name}, do you confirm that your birthday is on **{date}**? Type `{confirm_code}` to confirm this. "
                                         f"(You'll need to send the valid date to a bot admin to change this later)", ctx.channel)
        try:
            await self.bot.wait_for('message', timeout=30.0, check=check_confirm)
        except asyncio.TimeoutError:
            return await confirm_msg.edit(content=f"~~{confirm_msg.clean_content}~~\nWell, I'm taking that as a no...")
        self.db.execute("INSERT INTO birthdays VALUES (?, ?, ?)", (ctx.author.id, timestamp, False))
        return await general.send(f"Okay, your birthday is now saved as **{date}**", ctx.channel)

    @birthday.command(name="forceset", aliases=["force"])
    @commands.check(permissions.is_owner)
    async def force_set(self, ctx: commands.Context, user: discord.User, *, new_time: str):
        """ Force-set someone's birthday """
        timestamp = datetime.strptime(new_time + "/2020", "%d/%m/%Y")
        data = self.db.execute("UPDATE birthdays SET birthday=? WHERE uid=?", (timestamp, user.id))
        return await general.send(data, ctx.channel)

    @birthday.command(name="insert")
    @commands.check(permissions.is_owner)
    async def insert(self, ctx: commands.Context, user: discord.User, *, new_time: str):
        """ Insert someone's birthday """
        timestamp = datetime.strptime(new_time + "/2020", "%d/%m/%Y")
        data = self.db.execute("INSERT INTO birthdays VALUES (?, ?, ?)", (user.id, timestamp, False))
        return await general.send(data, ctx.channel)


def setup(bot):
    bot.add_cog(Birthdays(bot))
