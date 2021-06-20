import re
from datetime import datetime

import discord
from discord.ext import commands

from core.utils import general, permissions
from languages import langs


class Ctx:
    def __init__(self, guild, bot):
        self.guild = guild
        self.bot = bot


class Birthdays(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.re_timestamp = r"^([0-2][0-9]|3[0-1])\/(0[1-9]|1[0-2])"
        self.birthdays, self.birthday_self = ("birthdays_kyomi", "birthdays_birthday_mizuki") if bot.name == "kyomi" else ("birthdays", "birthdays_birthday_suager")

    def check_birthday(self, user_id):
        data = self.bot.db.fetchrow(f"SELECT * FROM {self.birthdays} WHERE uid=?", (user_id,))
        return data["birthday"] if data else None

    @commands.group(name="birthday", aliases=['b', 'bd', 'birth', 'day'], invoke_without_command=True)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.user)
    async def birthday(self, ctx: commands.Context, *, user: discord.User = None):
        """ Check someone's birthday"""
        if ctx.invoked_subcommand is None:
            locale = langs.gl(ctx)
            user = user or ctx.author
            if user.id == self.bot.user.id:
                return await general.send(langs.gls(self.birthday_self, locale), ctx.channel)
            has_birthday = self.check_birthday(user.id)
            if not has_birthday:
                return await general.send(langs.gls("birthdays_birthday_not_saved", locale, user.name), ctx.channel)
            birthday = langs.gts_date(has_birthday, locale, False, False)
            if user == ctx.author:
                return await general.send(langs.gls("birthdays_birthday_your", locale, birthday), ctx.channel)
            return await general.send(langs.gls("birthdays_birthday_general", locale, str(user), birthday), ctx.channel)

    @birthday.command(name="set")
    async def set(self, ctx: commands.Context, date: str):
        """ Set your birthday :)

        Format: `DD/MM`
        Example: //birthdays set 27/01"""
        locale = langs.gl(ctx)
        if re.compile(self.re_timestamp).search(date):
            try:
                timestamp = datetime.strptime(date + "/2020", "%d/%m/%Y")
            except ValueError:
                return await general.send(langs.gls("birthdays_set_invalid", locale), ctx.channel)
        else:
            return await general.send(langs.gls("birthdays_set_invalid", locale), ctx.channel)
        date = langs.gts_date(timestamp, locale, False, False)
        has_birthday = self.check_birthday(ctx.author.id)
        if has_birthday:
            self.bot.db.execute(f"UPDATE {self.birthdays} SET birthday=? WHERE uid=?", (timestamp, ctx.author.id))
            old_date = langs.gts_date(has_birthday, locale, False, False)
            return await general.send(langs.gls("birthdays_set_already", locale, ctx.author.name, date, old_date), ctx.channel)
        else:
            self.bot.db.execute(f"INSERT INTO {self.birthdays} VALUES (?, ?, ?)", (ctx.author.id, timestamp, False))
            return await general.send(langs.gls("birthdays_set_set", locale, ctx.author.name, date), ctx.channel)

    @birthday.command(name="clear", aliases=["reset", "delete"])
    async def delete(self, ctx: commands.Context):
        """ Delete your birthday """
        locale = langs.gl(ctx)
        self.bot.db.execute(f"DELETE FROM {self.birthdays} WHERE uid=?", (ctx.author.id,))
        return await general.send(langs.gls("birthdays_clear", locale, ctx.author.name), ctx.channel)

    @birthday.command(name="forceset", aliases=["force"])
    @commands.check(permissions.is_owner)
    async def force_set(self, ctx: commands.Context, user: discord.User, *, new_time: str):
        """ Force-set someone's birthday """
        timestamp = datetime.strptime(new_time + "/2020", "%d/%m/%Y")
        data = self.bot.db.execute(f"UPDATE {self.birthdays} SET birthday=? WHERE uid=?", (timestamp, user.id))
        return await general.send(data, ctx.channel)

    @birthday.command(name="insert")
    @commands.check(permissions.is_owner)
    async def insert(self, ctx: commands.Context, user: discord.User, *, new_time: str):
        """ Force-insert someone's birthday """
        timestamp = datetime.strptime(new_time + "/2020", "%d/%m/%Y")
        data = self.bot.db.execute(f"INSERT INTO {self.birthdays} VALUES (?, ?, ?)", (user.id, timestamp, False))
        return await general.send(data, ctx.channel)

    @birthday.command(name="forcedelete")
    @commands.check(permissions.is_owner)
    async def force_delete(self, ctx: commands.Context, user: discord.User):
        """ Force-delete someone's birthday """
        data = self.bot.db.execute(f"DELETE FROM {self.birthdays} WHERE uid=?", (user.id,))
        return await general.send(data, ctx.channel)


def setup(bot):
    bot.add_cog(Birthdays(bot))
