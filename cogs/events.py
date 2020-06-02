import asyncio
import json
import random

import aiohttp
import discord
from discord.ext import commands

from utils import generic, database, logs, time, emotes, lists, http

changes = {"playing": 3601, "avatar": [25, -1], "senko": [25, -1], "ad": False}


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.changes = f"data/changes.json"
        self.config = generic.get_config()
        self.db = database.Database()
        self.roles = self.config["gender_roles"]
        self.exists = False

    @commands.Cog.listener()
    async def on_command_error(self, ctx, err):
        if isinstance(err, commands.errors.MissingRequiredArgument) or isinstance(err, commands.errors.BadArgument):
            helper = str(ctx.invoked_subcommand) if ctx.invoked_subcommand else str(ctx.command)
            await ctx.send_help(helper)

        elif isinstance(err, commands.errors.CommandInvokeError):
            error = generic.traceback_maker(err.original, text=ctx.message.content, guild=ctx.guild, author=ctx.author)
            if "2000 or fewer" in str(err) and len(ctx.message.clean_content) > 1900:
                return generic.send(generic.gls(generic.get_lang(ctx.guild), "input_too_long"), ctx.channel)
            _error = generic.traceback_maker(err.original, advance=False)
            await generic.send(generic.gls(generic.get_lang(ctx.guild), "error_occurred", [_error]), ctx.channel)
            ec = self.bot.get_channel(logs.error_channel)
            if ec is not None:
                await ec.send(error)
            else:
                await ctx.send(f"No error channel found, full error:\n{error}")

        elif isinstance(err, commands.errors.CheckFailure):
            pass

        elif isinstance(err, commands.errors.CommandOnCooldown):
            rm, rs = divmod(err.retry_after, 60)
            # z = "0" if rs < 10 else ""
            ra = f"{int(rm)}m {round(rs, 2)}s"
            await generic.send(generic.gls(generic.get_lang(ctx.guild), "command_cooldown", [ra]), ctx.channel)

        elif isinstance(err, commands.errors.CommandNotFound):
            pass

        elif isinstance(err, commands.errors.MaxConcurrencyReached):
            await generic.send(generic.gls(generic.get_lang(ctx.guild), "max_concurrency"), ctx.channel)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        send = f"{time.time()} > Joined {guild.name} ({guild.id})"
        if self.config["logs"]:
            logs.log("guilds", send)
        print(send)
        if not self.config["join_message"]:
            return
        try:
            to_send = sorted([chan for chan in guild.channels if chan.permissions_for(guild.me).send_messages and
                              isinstance(chan, discord.TextChannel)], key=lambda x: x.position)[0]
        except IndexError:
            pass
        else:
            await to_send.send(self.config["join_message"])

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        send = f"{time.time()} > Left {guild.name} ({guild.id})"
        if self.config["logs"]:
            logs.log("guilds", send)
        print(send)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        try:
            g = ctx.guild.name
        except AttributeError:
            g = "Private Message"
        content = ctx.message.clean_content
        send = f"{time.time()} > {g} > {ctx.author} ({ctx.author.id}) > {content}"
        if self.config["logs"]:
            logs.log("commands", send)
        print(send)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if self.config["spyware"]:
            logs.log("members", f"{time.time()} > {member} ({member.id}) just joined {member.guild.name}")
        data = self.db.fetchrow("SELECT * FROM genders WHERE uid=?", (member.id,))
        if data:  # if gender is available
            snowflakes = [discord.Object(id=i) for i in self.roles.get(str(member.guild.id), [0, 0, 0])]
            reason = "Gender assignments on server join"
            gender = data["gender"]
            if gender == "male":
                await member.add_roles(snowflakes[0], reason=reason)
            if gender == "female":
                await member.add_roles(snowflakes[1], reason=reason)
            if gender == "invalid" or gender == "other":
                await member.add_roles(snowflakes[2], reason=reason)
        if member.guild.id == 568148147457490954:
            embed = discord.Embed(colour=generic.random_colour())
            embed.set_thumbnail(url=member.avatar_url)
            embed.add_field(name="User ID", value=member.id)
            embed.add_field(name="Created at", value=time.time_output(member.created_at))
            embed.add_field(name="Joined at", value=time.time_output(member.joined_at))
            await generic.send(f"{member.name} just joined Senko Lair", self.bot.get_channel(650774303192776744), embed=embed)
            if not self.config["disable_welcome"]:
                await generic.send(f"Welcome {member.mention} to Senko Lair!", self.bot.get_channel(568148147457490958), u=[member])

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if self.config["spyware"]:
            logs.log("members", f"{time.time()} > {member} ({member.id}) just left {member.guild.name}")
        if member.guild.id == 568148147457490954:
            await self.bot.get_channel(610836120321785869).send(
                f"{member.name} has abandoned Senko Lair :( {emotes.AlexHeartBroken}")
        uid = member.id
        gid = member.guild.id
        self.db.execute("DELETE FROM economy WHERE uid=? AND gid=?", (uid, gid))
        self.db.execute("DELETE FROM counters WHERE uid=? AND gid=?", (uid, gid))
        sel = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=?", (uid, gid))
        if sel:
            if sel["xp"] < 0:
                return
            elif sel["level"] < 0:
                self.db.execute("UPDATE leveling SET xp=0 WHERE uid=? AND gid=?", (uid, gid))
            else:
                self.db.execute("DELETE FROM leveling WHERE uid=? AND gid=?", (uid, gid))

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User or discord.Member):
        logs.log("members", f"{time.time()} > {user} ({user.id}) just got banned from {guild.name}")

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        logs.log("members", f"{time.time()} > {user} ({user.id}) just got unbanned from {guild.name}")

    @commands.Cog.listener()
    async def on_disconnect(self):
        self.exists = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self.bot, 'uptime'):
            self.bot.uptime = time.now(False)
        self.exists = True
        print(f"{time.time()} > Ready: {self.bot.user} - {len(self.bot.guilds)} servers, {len(self.bot.users)} users")
        try:
            times = json.loads(open(self.changes, 'r').read())
        except Exception as e:
            print(e)
            times = changes.copy()
        playing = f"{self.config['playing']} | v{self.config['version']}"
        await self.bot.change_presence(activity=discord.Game(name=playing), status=discord.Status.dnd)
        hour = time.now().hour
        when = int(hour / 6)
        send = f"{time.time()} > Successfully connected. {lists.hello[when]}."
        if self.config["logs"]:
            logs.log("uptime", f"{time.time()} > Server is online")
        slc = self.bot.get_channel(577599230567383058)
        if slc is not None:
            await slc.send(send)
        ad = times['ad']
        if ad:
            return
        else:
            times['ad'] = True
            open(self.changes, 'w+').write(json.dumps(times))
            # cp = self.config["change_playing"]
            # ca = self.config["change_avatars"]
            # cs = self.config["change_senko"]
            while True:
                if self.exists:
                    try:
                        self.config = generic.get_config()
                        cp = self.config["change_playing"]
                        ca = self.config["change_avatars"]
                        cs = self.config["change_senko"]
                        log = self.config["logs"]
                        now = time.now()
                        try:
                            times = json.loads(open(self.changes, 'r').read())
                        except Exception as e:
                            generic.print_error(f"{time.time()} > on_ready() > {e}")
                            times = changes.copy()
                        hour = now.hour
                        if cp:
                            this = now.minute * 60 + now.second
                            that = times['playing']
                            speed = self.config["playing_rate"]
                            plays = lists.playing
                            a, b = [int(this / speed) % len(plays), int(that / speed) % len(plays)]
                            if a != b:
                                play = random.choice(plays)
                                playing = f"{play} | v{self.config['version']}"
                                await self.bot.change_presence(activity=discord.Game(name=playing), status=discord.Status.dnd)
                                times["playing"] = this
                                if log:
                                    logs.log("playing", f"{time.time()} > Updated playing to {playing}")
                        if ca:
                            that, last = times['avatar']
                            if hour != that:
                                avatars = lists.avatars
                                al = len(avatars)
                                an = last + 1 if last < al - 1 else 0
                                avatar = avatars[an]
                                e = False
                                s1, s2 = [f"{time.time()} > Avatar changed - {an+1}/{al}", f"{time.time()} > Didn't change avatar cuz error"]
                                try:
                                    bio = await http.get(avatar, res_method="read")
                                    await self.bot.user.edit(avatar=bio)
                                    print(s1)
                                except discord.errors.HTTPException:
                                    print(s2)
                                    e = True
                                send = s2 if e else s1
                                if log:
                                    logs.log("avatar", send)
                                times['avatar'] = [hour, an]
                        if cs:
                            that, last = times['senko']
                            if hour != that:
                                senko_list = lists.server_icons
                                ss = len(senko_list)
                                sn = last + 1 if last < ss - 1 else 0
                                senko = senko_list[sn]
                                e = False
                                s1, s2 = [f"{time.time()} > Rainbow Senko - {sn+1}/{ss}", f"{time.time()} > Didn't change Senko Lair icon cuz error"]
                                try:
                                    bio = await http.get(senko, res_method="read")
                                    senko_lair = await self.bot.fetch_guild(568148147457490954)
                                    await senko_lair.edit(icon=bio, reason="Rainbow Senko")
                                    print(s1)
                                except discord.errors.HTTPException:
                                    print(s2)
                                    e = True
                                send = s2 if e else s1
                                if log:
                                    logs.log("senko", send)
                                times['senko'] = [hour, sn]
                        open(self.changes, 'w+').write(json.dumps(times))
                    except PermissionError:
                        generic.print_error(f"{time.time()} > on_ready > Failed to save changes.")
                    except aiohttp.ClientConnectorError:
                        generic.print_error(f"{time.time()} > on_ready > Looks like the bot tried to do something before it was even connected.")
                    except Exception as e:
                        generic.print_error(f"{time.time()} > on_ready > {type(e).__name__}: {e}")
                await asyncio.sleep(5)


def setup(bot):
    bot.add_cog(Events(bot))
