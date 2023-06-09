import re
from datetime import datetime

import discord

from utils import bot_data, commands
from utils.general import username


class Birthdays(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        self.timestamp_regex = re.compile(r"^([0-2]?\d|3[0-1])/((1[0-2])|(0?[1-9]))$")
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
            language = ctx.language()
            user = user or ctx.author
            if user.id == self.bot.user.id:
                return await ctx.send(language.string(self.birthday_self))
            birthday_date = self.check_birthday(user.id)
            if not birthday_date:
                return await ctx.send(language.string("birthdays_birthday_not_saved", user=user.name))
            birthday = language.date(birthday_date, short=0, dow=False, year=False)
            tz = language.get_timezone(user.id, "Earth")
            now = datetime.now(tz=tz)
            if now.day == birthday_date.day and now.month == birthday_date.month:
                today = "_today"
                delta = False
            else:
                today = ""
                year = now.year + 1 if (now.day > birthday_date.day and now.month == birthday_date.month) or now.month > birthday_date.month else now.year
                delta = language.delta_dt(birthday_date.replace(year=year, tzinfo=tz), accuracy=2, brief=False, affix=True)
            if user == ctx.author:
                return await ctx.send(language.string(f"birthdays_birthday_your{today}", date=birthday, delta=delta))
            return await ctx.send(language.string(f"birthdays_birthday_general{today}", user=username(user), date=birthday, delta=delta))

    @birthday.command(name="set")
    async def set(self, ctx: commands.Context, date: str):
        """ Set your birthday

        Format: `DD/MM`
        Example: 27 January -> `//birthdays set 27/01`"""
        language = ctx.language()
        if self.timestamp_regex.search(date):
            try:
                d, m = date.split("/", 1)
                timestamp = datetime(2020, int(m), int(d))
                # timestamp = datetime.strptime(date + "/2020", "%d/%m/%Y")
            except ValueError:
                return await ctx.send(language.string("birthdays_set_invalid", p=ctx.clean_prefix))
        else:
            return await ctx.send(language.string("birthdays_set_invalid", p=ctx.clean_prefix))
        date = language.date(timestamp, short=0, dow=False, year=False)
        has_birthday = self.check_birthday(ctx.author.id)
        if has_birthday is not None:
            self.bot.db.execute(f"UPDATE birthdays SET birthday=? WHERE uid=? AND bot=?", (timestamp, ctx.author.id, self.bot.name))
            old_date = language.date(has_birthday, short=0, dow=False, year=False)
            return await ctx.send(language.string("birthdays_set_already", user=username(ctx.author), new=date, old=old_date))
        else:
            self.bot.db.execute(f"INSERT INTO birthdays VALUES (?, ?, ?, ?)", (ctx.author.id, timestamp, False, self.bot.name))
            return await ctx.send(language.string("birthdays_set_set", user=username(ctx.author), date=date))

    @birthday.command(name="clear", aliases=["reset", "delete"])
    async def delete(self, ctx: commands.Context):
        """ Delete your birthday """
        language = ctx.language()
        self.bot.db.execute(f"DELETE FROM birthdays WHERE uid=? AND bot=?", (ctx.author.id, self.bot.name))
        return await ctx.send(language.string("birthdays_clear", user=ctx.author.name))

    @birthday.command(name="forceset", aliases=["force"])
    @commands.is_owner()
    async def force_set(self, ctx: commands.Context, user: discord.User, *, new_time: str):
        """ Force-set someone's birthday """
        timestamp = datetime.strptime(new_time + "/2020", "%d/%m/%Y")
        data = self.bot.db.execute(f"UPDATE birthdays SET birthday=? WHERE uid=? AND bot=?", (timestamp, user.id, self.bot.name))
        return await ctx.send(data)

    @birthday.command(name="insert")
    @commands.is_owner()
    async def insert(self, ctx: commands.Context, user: discord.User, *, new_time: str):
        """ Force-insert someone's birthday """
        timestamp = datetime.strptime(new_time + "/2020", "%d/%m/%Y")
        data = self.bot.db.execute(f"INSERT INTO birthdays VALUES (?, ?, ?, ?)", (user.id, timestamp, False, self.bot.name))
        return await ctx.send(data)

    @birthday.command(name="forcedelete")
    @commands.is_owner()
    async def force_delete(self, ctx: commands.Context, user: discord.User):
        """ Force-delete someone's birthday """
        data = self.bot.db.execute(f"DELETE FROM birthdays WHERE uid=? AND bot=?", (user.id, self.bot.name))
        return await ctx.send(data)


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Birthdays(bot))
