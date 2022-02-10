import re
from datetime import datetime

import discord
from discord.ext import commands

from utils import bot_data, general, permissions


class Birthdays(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        self.timestamp_regex = r"^([0-2][0-9]|3[0-1])\/(0[1-9]|1[0-2])"
        self.birthday_self = "birthdays_birthday_mizuki" if bot.name == "kyomi" else "birthdays_birthday_suager"

    def check_birthday(self, user_id):
        data = self.bot.db.fetchrow(f"SELECT * FROM birthdays WHERE uid=? AND bot=?", (user_id, self.bot.name))
        return data["birthday"] if data else None

    @commands.group(name="birthday", aliases=['b', 'bd', 'birth', 'day'], invoke_without_command=True)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.user)
    async def birthday(self, ctx: commands.Context, *, user: discord.User = None):
        """ Check someone's birthday"""
        if ctx.invoked_subcommand is None:
            language = self.bot.language(ctx)
            user = user or ctx.author
            if user.id == self.bot.user.id:
                return await general.send(language.string(self.birthday_self), ctx.channel)
            has_birthday = self.check_birthday(user.id)
            if not has_birthday:
                return await general.send(language.string("birthdays_birthday_not_saved", user.name), ctx.channel)
            birthday = language.date(has_birthday, short=0, dow=False, year=False)
            if user == ctx.author:
                return await general.send(language.string("birthdays_birthday_your", birthday), ctx.channel)
            return await general.send(language.string("birthdays_birthday_general", str(user), birthday), ctx.channel)

    @birthday.command(name="set")
    async def set(self, ctx: commands.Context, date: str):
        """ Set your birthday

        Format: `DD/MM`
        Example: //birthdays set 27/01"""
        language = self.bot.language(ctx)
        if re.compile(self.timestamp_regex).search(date):
            try:
                timestamp = datetime.strptime(date + "/2020", "%d/%m/%Y")
            except ValueError:
                return await general.send(language.string("birthdays_set_invalid"), ctx.channel)
        else:
            return await general.send(language.string("birthdays_set_invalid"), ctx.channel)
        date = language.date(timestamp, short=0, dow=False, year=False)
        has_birthday = self.check_birthday(ctx.author.id)
        if has_birthday is not None:
            self.bot.db.execute(f"UPDATE birthdays SET birthday=? WHERE uid=? AND bot=?", (timestamp, ctx.author.id, self.bot.name))
            old_date = language.date(has_birthday, short=0, dow=False, year=False)
            return await general.send(language.string("birthdays_set_already", ctx.author.name, date, old_date), ctx.channel)
        else:
            self.bot.db.execute(f"INSERT INTO birthdays VALUES (?, ?, ?, ?)", (ctx.author.id, timestamp, False, self.bot.name))
            return await general.send(language.string("birthdays_set_set", ctx.author.name, date), ctx.channel)

    @birthday.command(name="clear", aliases=["reset", "delete"])
    async def delete(self, ctx: commands.Context):
        """ Delete your birthday """
        language = self.bot.language(ctx)
        self.bot.db.execute(f"DELETE FROM birthdays WHERE uid=? AND bot=?", (ctx.author.id, self.bot.name))
        return await general.send(language.string("birthdays_clear", ctx.author.name), ctx.channel)

    @birthday.command(name="forceset", aliases=["force"])
    @commands.is_owner()
    async def force_set(self, ctx: commands.Context, user: discord.User, *, new_time: str):
        """ Force-set someone's birthday """
        timestamp = datetime.strptime(new_time + "/2020", "%d/%m/%Y")
        data = self.bot.db.execute(f"UPDATE birthdays SET birthday=? WHERE uid=? AND bot=?", (timestamp, user.id, self.bot.name))
        return await general.send(data, ctx.channel)

    @birthday.command(name="insert")
    @commands.is_owner()
    async def insert(self, ctx: commands.Context, user: discord.User, *, new_time: str):
        """ Force-insert someone's birthday """
        timestamp = datetime.strptime(new_time + "/2020", "%d/%m/%Y")
        data = self.bot.db.execute(f"INSERT INTO birthdays VALUES (?, ?, ?, ?)", (user.id, timestamp, False, self.bot.name))
        return await general.send(data, ctx.channel)

    @birthday.command(name="forcedelete")
    @commands.is_owner()
    async def force_delete(self, ctx: commands.Context, user: discord.User):
        """ Force-delete someone's birthday """
        data = self.bot.db.execute(f"DELETE FROM birthdays WHERE uid=? AND bot=?", (user.id, self.bot.name))
        return await general.send(data, ctx.channel)


def setup(bot: bot_data.Bot):
    bot.add_cog(Birthdays(bot))
