import asyncio
import random
import re
from datetime import datetime

import discord
from discord.ext import commands

from utils import permissions, sqlite, generic, emotes


def if_else(statement, if_statement: str, else_statement: str = None):
    """ Make it easier with if/else cases of what grammar to use
    - if_statement is returned when statement is True
    - else_statement is returned when statement is False/None
    """
    else_statement = else_statement if else_statement else ""
    return if_statement if statement else else_statement


def calculate_age(born):
    """ Calculate age (datetime) """
    today = datetime.now()
    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    return age


class Birthdays(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.re_timestamp = r"^(0[0-9]|1[0-9]|2[0-9]|3[0-1])\/(0[1-9]|1[0-2])\/([1-2]{1}[0-9]{3})"
        self.db = sqlite.Database()
        self.config = generic.get_config()

    @commands.Cog.listener()
    async def on_ready(self):
        # print(f'Ready: {self.bot.user} | Servers: {len(self.bot.guilds)}')
        # await self.bot.change_presence(
        #     activity=discord.Activity(type=3, name="when your birthday is due 🎉🎂"),
        #     status=discord.Status.idle
        # )

        while True:
            await asyncio.sleep(10)
            guild = self.bot.get_guild(self.config.guild_id)
            birthday_role = discord.Object(id=self.config.birthday_role_id)

            # Check if someone has birthday today
            birthday_today = self.db.fetch(
                "SELECT * FROM birthdays WHERE has_role=0 AND strftime('%m-%d', birthday) = strftime('%m-%d', 'now')"
            )
            if birthday_today:
                for g in birthday_today:
                    self.db.execute("UPDATE birthdays SET has_role=1 WHERE user_id=?", (g["user_id"],))
                    try:
                        user = guild.get_member(g["user_id"])
                        await self.bot.get_channel(self.config.announce_channel_id).send(
                            f"Happy birthday {user.mention}, have a nice birthday and enjoy your role "
                            f"today 🎂🎉"
                        )
                        await user.add_roles(birthday_role, reason=f"{user} has birthday! 🎂🎉")
                        print(f"Gave role to {user.name}")
                    except Exception as e:
                        print(e)

            birthday_over = self.db.fetch(
                "SELECT * FROM birthdays WHERE has_role=1 AND strftime('%m-%d', birthday) != strftime('%m-%d', 'now')"
            )
            for g in birthday_over:
                self.db.execute("UPDATE birthdays SET has_role=0 WHERE user_id=?", (g["user_id"],))
                try:
                    user = guild.get_member(g["user_id"])
                    await user.remove_roles(birthday_role, reason=f"{user} does not have birthday now...")
                    print(f"Removed role from {user.name}")
                except Exception as e:
                    print(e)

    def check_birthday_noted(self, user_id):
        """ Convert timestamp string to datetime """
        data = self.db.fetchrow("SELECT * FROM birthdays WHERE user_id=?", (user_id,))
        if data:
            return data["birthday"]
        else:
            return None

    @commands.command(aliases=['b', 'bd', 'birth', 'day'])
    async def birthday(self, ctx, *, user: discord.Member = None):
        """ Check your birthday or other people """
        user = user or ctx.author

        if user.id == self.bot.user.id:
            return await ctx.send(f"I have birthday on **6th December**, thank you for asking {emotes.AlexHeart}")

        has_birthday = self.check_birthday_noted(user.id)
        if not has_birthday:
            return await ctx.send(f"**{user.name}** has not saved his/her birthday :(")

        birthday = has_birthday.strftime('%d %B')
        age = calculate_age(has_birthday)

        is_author = user == ctx.author
        target = if_else(is_author, "**You** have", f"**{user.name}** has")
        grammar = if_else(is_author, "are", "is")
        when = if_else(is_author, " ", " on ")

        await ctx.send(
            f"{target} birthday{when}**{birthday}** and {grammar} currently **{age}** years old."
        )

    @commands.command()
    async def set(self, ctx):
        """ Set your birthday :) """
        has_birthday = self.check_birthday_noted(ctx.author.id)
        if has_birthday:
            return await ctx.send(
                f"You've already set your birth date to **{has_birthday.strftime('%d %B %Y')}**\n"
                f"To change this, please contact the owner of the bot."
            )

        start_msg = await ctx.send(f"Hello there **{ctx.author.name}**, please enter when you were born. "
                                   f"`[ DD/MM/YYYY ]`")
        confirmcode = random.randint(10000, 99999)

        def check_timestamp(m):
            if m.author == ctx.author and m.channel == ctx.channel:
                if re.compile(self.re_timestamp).search(m.content):
                    return True
            return False

        def check_confirm(m):
            if m.author == ctx.author and m.channel == ctx.channel:
                if m.content.startswith(str(confirmcode)):
                    return True
            return False

        try:
            user = await self.bot.wait_for('message', timeout=30.0, check=check_timestamp)
        except asyncio.TimeoutError:
            return await start_msg.edit(
                content=f"~~{start_msg.clean_content}~~\n\nfine then, I won't save your birthday :("
            )

        timestamp = datetime.strptime(user.content.split(" ")[0], "%d/%m/%Y")
        timestamp_clean = timestamp.strftime("%d %B %Y")
        today = datetime.now()
        age = calculate_age(timestamp)

        if timestamp > today:
            return await ctx.send(f"Nope.. you can't exist in the future **{ctx.author.name}**")
        if age > 300:
            return await ctx.send(f"**{ctx.author.name}**... Are you sure you're over 300 years old?")
        if age <= 13:
            return await ctx.send(f"You have to be **13** to use Discord **{ctx.author.name}**. "
                                  f"Are you saying you're underage (only {age})? 🤔")

        confirm_msg = await ctx.send(
            f"Alright **{ctx.author.name}**, do you confirm that your birth date is **{timestamp_clean}** "
            f"and you're currently **{age}** years old?\nType `{confirmcode}` to confirm this choice\n"
            f"(NOTE: To change birthday later, you must send valid birthday to the owner)"
        )

        try:
            await self.bot.wait_for('message', timeout=30.0, check=check_confirm)
        except asyncio.TimeoutError:
            return await confirm_msg.edit(
                content=f"~~{confirm_msg.clean_content}~~\n\nStopped process..."
            )

        self.db.execute("INSERT INTO birthdays VALUES (?, ?, ?)", (ctx.author.id, timestamp, False))
        await ctx.send(f"Done, your birth date is now saved in my database at **{timestamp_clean}** 🎂")

    @commands.command(name="forceset", aliases=["force"])
    @commands.check(permissions.is_owner)
    async def force_set(self, ctx, user: discord.Member, *, time: str):
        """ Force-set someone's birthday """
        timestamp = datetime.strptime(time, "%d/%m/%Y")
        data = self.db.execute("UPDATE birthdays SET birthday=? WHERE user_id=?", (timestamp, user.id))
        await ctx.send(data)

    @commands.command(name="insert")
    @commands.check(permissions.is_owner)
    async def insert(self, ctx, user: discord.Member, *, time: str):
        """ Insert someone's birthday """
        timestamp = datetime.strptime(time, "%d/%m/%Y")
        data = self.db.execute("INSERT INTO birthdays VALUES (?, ?, ?)", (user.id, timestamp, False))
        await ctx.send(data)

    @commands.command()
    @commands.check(permissions.is_owner)
    async def db(self, ctx, *, query: str):
        """ Database query """
        data = self.db.execute(query)
        await ctx.send(f"{data}")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def dropall(self, ctx):
        """ Delete everything """
        data = self.db.execute("DELETE FROM birthdays")
        await ctx.send(f"DEBUG: {data}")


def setup(bot):
    bot.add_cog(Birthdays(bot))
