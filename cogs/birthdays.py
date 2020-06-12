import asyncio
import random
import re
from datetime import datetime

import discord
from discord.ext import commands

from utils import permissions, generic, time, database


class Birthdays(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.re_timestamp = r"^(0[0-9]|1[0-9]|2[0-9]|3[0-1])\/(0[1-9]|1[0-2])"
        self.db = database.Database()
        self.config = generic.get_config()
        self.bd_config = self.config["birthdays"]

    @commands.Cog.listener()
    async def on_ready(self):
        while True:
            await asyncio.sleep(10)
            ag = [a for a in self.bd_config]
            guilds = [self.bot.get_guild(int(guild)) for guild in ag]
            channel_ids, role_ids = [], []
            for guild in guilds:
                if guild is not None:
                    data = self.bd_config[str(guild.id)]
                    channel_ids.append(data["channel"])
                    role_ids.append(data["role_id"])
            channels = [self.bot.get_channel(cid) for cid in channel_ids]
            roles = [discord.Object(id=rid) for rid in role_ids]
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
                                    await generic.send(generic.gls(generic.get_lang(guild), "birthday_today", [user.mention]), channels[i], u=True)
                                    # await channels[i].send(f"Happy birthday {user.mention}, have a nice birthday and enjoy your role today 🎂🎉")
                                    await user.add_roles(roles[i], reason=f"{user} has birthday! 🎂🎉")
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
                            await user.remove_roles(roles[i], reason=f"{user} does not have birthday anymore...")
                            print(f"{time.time()} > {guild.name} > Removed birthday role from {user.name}")
                    except Exception as e:
                        print(e)

    def check_birthday_noted(self, user_id):
        """ Convert timestamp string to datetime """
        data = self.db.fetchrow("SELECT * FROM birthdays WHERE uid=?", (user_id,))
        if data:
            return data["birthday"]
        else:
            return None

    @commands.group(name="birthday", aliases=['b', 'bd', 'birth', 'day'], invoke_without_command=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def birthday(self, ctx: commands.Context, *, user: discord.User = None):
        """ Check your birthday or other people """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "birthday"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        if ctx.invoked_subcommand is None:
            user = user or ctx.author
            if user.id == self.bot.user.id:
                return await generic.send(generic.gls(locale, "birthday_self"), ctx.channel)
            has_birthday = self.check_birthday_noted(user.id)
            if not has_birthday:
                return await generic.send(generic.gls(locale, "birthday_none", [user.name]), ctx.channel)
            birthday = generic.time_ls(locale, has_birthday, show_year=False, show_time=False)
            if user == ctx.author:
                return await generic.send(generic.gls(locale, "birthday_you", [birthday]), ctx.channel)
            return await generic.send(generic.gls(locale, "birthday_other", [user.name, birthday]), ctx.channel)

    @birthday.command(name="set")
    async def set(self, ctx: commands.Context, date: str):
        """ Set your birthday :) [DD/MM] """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "birthday"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        has_birthday = self.check_birthday_noted(ctx.author.id)
        if has_birthday:
            return await generic.send(generic.gls(locale, "birthday_already_set", [has_birthday.strftime('%d %B')]), ctx.channel)
        confirm_code = random.randint(10000, 99999)

        def check_confirm(m):
            if m.author == ctx.author and m.channel == ctx.channel:
                if m.content.startswith(str(confirm_code)):
                    return True
            return False
        if re.compile(self.re_timestamp).search(date):
            timestamp = datetime.strptime(date + "/2020", "%d/%m/%Y")
        else:
            return await generic.send(generic.gls(locale, "birthday_no"), ctx.channel)
        timestamp_clean = generic.time_ls(locale, timestamp, show_year=False, show_time=False)
        confirm_msg = await generic.send(generic.gls(locale, "birthday_confirm", [ctx.author.name, timestamp_clean, confirm_code]), ctx.channel)
        try:
            await self.bot.wait_for('message', timeout=30.0, check=check_confirm)
        except asyncio.TimeoutError:
            content = generic.gls(locale, "birthday_no2", [confirm_msg.clean_content])
            return await confirm_msg.edit(content=content)
        self.db.execute("INSERT INTO birthdays VALUES (?, ?, ?)", (ctx.author.id, timestamp, False))
        return await generic.send(generic.gls(locale, "birthday_set", [timestamp_clean]),
                                  ctx.channel)

    @birthday.command(name="forceset", aliases=["force"])
    @commands.check(permissions.is_owner)
    async def force_set(self, ctx: commands.Context, user: discord.User, *, new_time: str):
        """ Force-set someone's birthday """
        timestamp = datetime.strptime(new_time + "/2020", "%d/%m/%Y")
        data = self.db.execute("UPDATE birthdays SET birthday=? WHERE uid=?", (timestamp, user.id))
        return await generic.send(data, ctx.channel)

    @birthday.command(name="insert")
    @commands.check(permissions.is_owner)
    async def insert(self, ctx: commands.Context, user: discord.User, *, new_time: str):
        """ Insert someone's birthday """
        timestamp = datetime.strptime(new_time + "/2020", "%d/%m/%Y")
        data = self.db.execute("INSERT INTO birthdays VALUES (?, ?, ?)", (user.id, timestamp, False))
        return await generic.send(data, ctx.channel)


def setup(bot):
    bot.add_cog(Birthdays(bot))
