import asyncio
import random
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
        # self.already = False

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     if not self.already:
    #         self.already = True
    # moved to temporaries.py

    def check_birthday_noted(self, user_id):
        """ Convert timestamp string to datetime """
        data = self.bot.db.fetchrow("SELECT * FROM birthdays WHERE uid=?", (user_id,))
        return data["birthday"] if data else None

    @commands.group(name="birthday", aliases=['b', 'bd', 'birth', 'day'], invoke_without_command=True)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.user)
    async def birthday(self, ctx: commands.Context, *, user: discord.User = None):
        """ Check your birthday or other people """
        if ctx.invoked_subcommand is None:
            locale = langs.gl(ctx)
            user = user or ctx.author
            if user.id == self.bot.user.id:
                return await general.send(langs.gls("birthdays_birthday_suager", locale), ctx.channel)
            has_birthday = self.check_birthday_noted(user.id)
            if not has_birthday:
                return await general.send(langs.gls("birthdays_birthday_not_saved", locale, user.name), ctx.channel)
            birthday = langs.gts_date(has_birthday, locale, False, False)
            if user == ctx.author:
                return await general.send(langs.gls("birthdays_birthday_your", locale, birthday), ctx.channel)
            return await general.send(langs.gls("birthdays_birthday_general", locale, str(user), birthday), ctx.channel)

    @birthday.command(name="set")
    async def set(self, ctx: commands.Context, date: str):
        """ Set your birthday :) [DD/MM] """
        locale = langs.gl(ctx)
        has_birthday = self.check_birthday_noted(ctx.author.id)
        if has_birthday:
            return await general.send(langs.gls("birthdays_set_already", locale, ctx.author.name, langs.gts_date(has_birthday, locale, False, False)),
                                      ctx.channel)
        confirm_code = random.randint(10000, 99999)

        def check_confirm(m):
            if m.author == ctx.author and m.channel == ctx.channel:
                if m.content.startswith(str(confirm_code)):
                    return True
            return False
        if re.compile(self.re_timestamp).search(date):
            try:
                timestamp = datetime.strptime(date + "/2020", "%d/%m/%Y")
            except ValueError:
                return await general.send(langs.gls("birthdays_set_invalid", locale), ctx.channel)
        else:
            return await general.send(langs.gls("birthdays_set_invalid", locale), ctx.channel)
        date = langs.gts_date(timestamp, locale, False, False)
        confirm_msg = await general.send(langs.gls("birthdays_set_confirmation", locale, ctx.author.name, date, confirm_code), ctx.channel)
        try:
            await self.bot.wait_for('message', timeout=30.0, check=check_confirm)
        except asyncio.TimeoutError:
            return await confirm_msg.edit(content=langs.gls("generic_timed_out", locale, confirm_msg.clean_content))
        self.bot.db.execute("INSERT INTO birthdays VALUES (?, ?, ?)", (ctx.author.id, timestamp, False))
        await confirm_msg.delete()
        return await general.send(langs.gls("birthdays_set_set", locale, ctx.author.name, date), ctx.channel)

    @birthday.command(name="forceset", aliases=["force"])
    @commands.check(permissions.is_owner)
    async def force_set(self, ctx: commands.Context, user: discord.User, *, new_time: str):
        """ Force-set someone's birthday """
        timestamp = datetime.strptime(new_time + "/2020", "%d/%m/%Y")
        data = self.bot.db.execute("UPDATE birthdays SET birthday=? WHERE uid=?", (timestamp, user.id))
        return await general.send(data, ctx.channel)

    @birthday.command(name="insert")
    @commands.check(permissions.is_owner)
    async def insert(self, ctx: commands.Context, user: discord.User, *, new_time: str):
        """ Insert someone's birthday """
        timestamp = datetime.strptime(new_time + "/2020", "%d/%m/%Y")
        data = self.bot.db.execute("INSERT INTO birthdays VALUES (?, ?, ?)", (user.id, timestamp, False))
        return await general.send(data, ctx.channel)


def setup(bot):
    bot.add_cog(Birthdays(bot))
