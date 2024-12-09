import re
from datetime import datetime, date as _date, time as _time
from typing import Union

import discord
from discord import app_commands

from utils import bot_data, commands, interactions
from utils.general import username


class Birthdays(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        self.timestamp_regex = re.compile(r"^([0-2]?\d|3[0-1])/((1[0-2])|(0?[1-9]))$")
        self.birthday_self = "birthdays_birthday_mizuki" if bot.name == "kyomi" else "birthdays_birthday_suager"

    def check_birthday(self, user_id) -> Union[_date, None]:
        data = self.bot.db.fetchrow(f"SELECT * FROM birthdays WHERE uid=? AND bot=?", (user_id, self.bot.name))
        return data["birthday"] if data else None

    async def cmd_check_birthday(self, ctx: commands.Context | discord.Interaction, user: discord.User):
        if isinstance(ctx, discord.Interaction):
            await ctx.response.defer(ephemeral=True)  # type: ignore
            ctx: commands.Context = await commands.Context.from_interaction(ctx)
        language = ctx.language()
        user = user or ctx.author
        if user.id == self.bot.user.id:
            return await ctx.send(language.string(self.birthday_self), ephemeral=True)
        _birthday_date = self.check_birthday(user.id)
        if not _birthday_date:
            return await ctx.send(language.string("birthdays_birthday_not_saved", user=username(user)), ephemeral=True)
        birthday_date = datetime.combine(_birthday_date, _time(0, 0, 0))
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
            return await ctx.send(language.string(f"birthdays_birthday_your{today}", date=birthday, delta=delta), ephemeral=True)
        return await ctx.send(language.string(f"birthdays_birthday_general{today}", user=username(user), date=birthday, delta=delta), ephemeral=True)

    @commands.hybrid_group(name="birthday", aliases=['b', 'bd', 'birth', 'day'], invoke_without_command=True, fallback="check")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.user)
    @app_commands.describe(user="The user whose birthday you want to check")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def birthday(self, ctx: commands.Context, *, user: discord.User = None):
        """ Check your or someone else's birthday """
        if ctx.invoked_subcommand is None:
            return await self.cmd_check_birthday(ctx, user)

    @birthday.command(name="set")
    @app_commands.describe(date="Your birthday in DD/MM format (e.g. 27/01 for 27th January)")
    async def set(self, ctx: commands.Context, date: str):
        """ Set your birthday

        Format: `DD/MM`
        Example: 27 January -> `//birthdays set 27/01`"""
        await ctx.defer(ephemeral=True)
        language = ctx.language()
        if self.timestamp_regex.search(date):
            try:
                d, m = date.split("/", 1)
                timestamp = _date(2020, int(m), int(d))
                # timestamp = datetime.strptime(date + "/2020", "%d/%m/%Y")
            except ValueError:
                return await ctx.send(language.string("birthdays_set_invalid", p=ctx.clean_prefix), ephemeral=True)
        else:
            return await ctx.send(language.string("birthdays_set_invalid", p=ctx.clean_prefix), ephemeral=True)
        date = language.date(timestamp, short=0, dow=False, year=False)
        has_birthday = self.check_birthday(ctx.author.id)
        if has_birthday is not None:
            self.bot.db.execute(f"UPDATE birthdays SET birthday=? WHERE uid=? AND bot=?", (timestamp, ctx.author.id, self.bot.name))
            old_date = language.date(has_birthday, short=0, dow=False, year=False)
            return await ctx.send(language.string("birthdays_set_already", user=username(ctx.author), new=date, old=old_date), ephemeral=True)
        else:
            self.bot.db.execute(f"INSERT INTO birthdays VALUES (?, ?, ?, ?)", (ctx.author.id, timestamp, False, self.bot.name))
            return await ctx.send(language.string("birthdays_set_set", user=username(ctx.author), date=date), ephemeral=True)

    @birthday.command(name="clear", aliases=["reset", "delete"])
    async def delete(self, ctx: commands.Context):
        """ Un-set your birthday """
        await ctx.defer(ephemeral=True)
        language = ctx.language()
        self.bot.db.execute(f"DELETE FROM birthdays WHERE uid=? AND bot=?", (ctx.author.id, self.bot.name))
        return await ctx.send(language.string("birthdays_clear", user=username(ctx.author)), ephemeral=True)

    @birthday.command(name="forceset", aliases=["force"], with_app_command=False)
    @commands.is_owner()
    async def force_set(self, ctx: commands.Context, user: discord.User, *, new_time: str):
        """ Force-set someone's birthday """
        timestamp = datetime.strptime(new_time + "/2020", "%d/%m/%Y")
        data = self.bot.db.execute(f"UPDATE birthdays SET birthday=? WHERE uid=? AND bot=?", (timestamp, user.id, self.bot.name))
        return await ctx.send(data)

    @birthday.command(name="insert", with_app_command=False)
    @commands.is_owner()
    async def insert(self, ctx: commands.Context, user: discord.User, *, new_time: str):
        """ Force-insert someone's birthday """
        timestamp = datetime.strptime(new_time + "/2020", "%d/%m/%Y")
        data = self.bot.db.execute(f"INSERT INTO birthdays VALUES (?, ?, ?, ?)", (user.id, timestamp, False, self.bot.name))
        return await ctx.send(data)

    @birthday.command(name="forcedelete", with_app_command=False)
    @commands.is_owner()
    async def force_delete(self, ctx: commands.Context, user: discord.User):
        """ Force-delete someone's birthday """
        data = self.bot.db.execute(f"DELETE FROM birthdays WHERE uid=? AND bot=?", (user.id, self.bot.name))
        return await ctx.send(data)


async def setup(bot: bot_data.Bot):
    cog = Birthdays(bot)
    await bot.add_cog(cog)

    @bot.tree.context_menu(name="Check Birthday")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def ctx_check_birthday(interaction: discord.Interaction, user: discord.Member | discord.User):
        """ Context menu to check a user's birthday """
        interactions.log_interaction(interaction)
        return await cog.cmd_check_birthday(interaction, user)

    @ctx_check_birthday.error
    async def ctx_check_birthday_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        return await interactions.on_error(interaction, error)
