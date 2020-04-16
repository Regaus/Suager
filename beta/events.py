import asyncio
import json
import os
import random
from datetime import datetime

import discord
import psutil
from aiohttp import ClientConnectorError
from discord.ext import commands

from beta import main
from beta.genders import select, roles
from utils import generic, time, logs, lists, http, database
from utils.emotes import AlexHeartBroken

# ct = time.now()  # Current time
changes = {"playing": 3601, "avatar": [25, -1], "senko": [25, -1], "ad": False}


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.process = psutil.Process(os.getpid())
        self.exists = False
        self.config = generic.get_config()
        self.type = main.version
        self.dir = main.folder
        # self.stop, self.done = False, False
        # self.ad = False
        self.changes = f"data/{self.type}/changes.json"
        self.db = database.Database()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, err):
        if isinstance(err, commands.errors.MissingRequiredArgument) or isinstance(err, commands.errors.BadArgument):
            # await send_cmd_help(ctx)
            helper = str(ctx.invoked_subcommand) if ctx.invoked_subcommand else str(ctx.command)
            await ctx.send_help(helper)

        elif isinstance(err, commands.errors.CommandInvokeError):
            error = generic.traceback_maker(err.original, text=ctx.message.content, guild=ctx.guild, author=ctx.author)
            if "2000 or fewer" in str(err) and len(ctx.message.clean_content) > 1900:
                return await ctx.send(
                    f"You attempted to make the command display more than 2,000 characters, didn't you?\n"
                    f"Congratulations, you broke it. Now go find something more interesting to do."
                )
            # await self.bot.get_user(302851022790066185).send(error)
            _error = generic.traceback_maker(err.original, advance=False)
            await ctx.send(f"There has been an error, try again later...\n`{_error}`")
            ec = self.bot.get_channel(logs.error_channel)
            if ec is not None:
                await ec.send(error)
            else:
                await ctx.send(f"No error channel found, full error:\n{error}")
            # if self.config.logs:
            #     await logs.log_channel(self.bot, "errors").send(error)

        elif isinstance(err, commands.errors.CheckFailure):
            pass

        elif isinstance(err, commands.errors.CommandOnCooldown):
            # ra = timedelta(seconds=err.retry_after).__str__()
            rm, rs = divmod(err.retry_after, 60)
            ra = f"{rm}:{rs:02d.2f}"
            # rm = err.retry_after // 60
            # _rs = err.retry_after - 60 * rm
            # rs = str(_rs).zfill(2)
            # ra = f"{rm}:{rs}"
            await ctx.send(f"This command is on cooldown... try again in {ra}")

        elif isinstance(err, commands.errors.CommandNotFound):
            pass

        elif isinstance(err, commands.errors.MaxConcurrencyReached):
            await ctx.send("This command cannot be used right now - max concurrency reached. Try again later.")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        send = f"{time.time()} > Joined {guild.name} ({guild.id})"
        # if self.config.logs:
        #     await logs.log_channel(self.bot, "servers").send(send)
        if self.config["logs"]:
            logs.save(logs.get_place(self.type, "guilds"), send)
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
        # if self.config.logs:
        #     await logs.log_channel(self.bot, "servers").send(send)
        if self.config["logs"]:
            logs.save(logs.get_place(self.type, "guilds"), send)
        print(send)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        # Some shitfuckery below
        try:
            g = ctx.guild.name
        except AttributeError:
            g = "Private Message"
        content = ctx.message.clean_content
        send = f"{time.time()} > {g} > {ctx.author} ({ctx.author.id}) > {content}"
        # if self.config.logs:
        #     await logs.log_channel(self.bot).send(send)
        if self.config["logs"]:
            logs.save(logs.get_place(self.type, "commands"), send)
        print(send)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if self.config["spyware"]:
            # await logs.log_channel(self.bot, "spyware").send(
            #     f"{time.time()} > {member} just joined {member.guild.name}")
            logs.save(logs.get_place(self.type, "members"),
                      f"{time.time()} > {member} ({member.id}) just joined {member.guild.name}")
        data = self.db.fetchrow(select, (member.id,))
        if data:  # if gender is available
            snowflakes = [discord.Object(id=i) for i in roles.get(member.guild.id, [0, 0, 0])]
            reason = "Gender assignments on server join"
            gender = data["gender"]
            if gender == "male":
                await member.add_roles(snowflakes[0], reason=reason)
            if gender == "female":
                await member.add_roles(snowflakes[1], reason=reason)
            if gender == "invalid" or gender == "other":
                await member.add_roles(snowflakes[2], reason=reason)
        if self.type == "stable":
            if member.guild.id == 568148147457490954:
                td = time.now_ts() - datetime.timestamp(member.created_at)
                if td < 86400:
                    await member.kick(reason="Account created less than a day ago")
                embed = discord.Embed(colour=generic.random_colour())
                embed.set_thumbnail(url=member.avatar_url)
                embed.add_field(name="User ID", value=member.id)
                embed.add_field(name="Created at", value=time.time_output(member.created_at))
                embed.add_field(name="Joined at", value=time.time_output(member.joined_at))
                await self.bot.get_channel(568148147457490958).send(f"Welcome {member.mention} to Senko Lair!")
                await self.bot.get_channel(650774303192776744).send(
                    f"{member.name} just joined Senko Lair.", embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if self.config["spyware"]:
            # await logs.log_channel(self.bot, "spyware").send(
            # f"{time.time()} > {member} just left {member.guild.name}")
            logs.save(logs.get_place(self.type, "members"),
                      f"{time.time()} > {member} ({member.id}) just left {member.guild.name}")
        if self.type == "stable":
            if member.guild.id == 568148147457490954:
                await self.bot.get_channel(610836120321785869).send(
                    f"{member.name} has abandoned Senko Lair :( {AlexHeartBroken}")

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User or discord.Member):
        uid = user.id
        gid = guild.id
        del1 = self.db.execute("DELETE FROM leveling WHERE uid=? AND gid=?", (uid, gid))
        del2 = self.db.execute("DELETE FROM economy WHERE uid=? AND gid=?", (uid, gid))
        logs.save(logs.get_place(self.type, "members"),
                  f"{time.time()} > {user} ({user.id}) just got banned from {guild.name} - Database statuses: "
                  f"leveling {del1}, economy {del2}")
        print(f"{time.time()} > Banned {user.name} from {guild.name} > DB statuses: lvl {del1}, economy {del2}")

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        logs.save(logs.get_place(self.type, "members"),
                  f"{time.time()} > {user} ({user.id}) just got unbanned from {guild.name}")

    async def readiness(self):
        while not self.exists:
            await asyncio.sleep(1)

        if not hasattr(self.bot, 'uptime'):
            self.bot.uptime = time.now(True)

        print(f"{time.time()} > Ready: {self.bot.user} - {len(self.bot.guilds)} servers, {len(self.bot.users)} users")
        try:
            # times = json.loads('changes.json')
            times = json.loads(open(self.changes, 'r').read())
        except Exception as e:
            print(e)
            times = changes.copy()
        stuff = self.config["bots"][self.type]
        playing = f"{self.config['playing']} | v{stuff['version']}"
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing,
                                                                 name=playing), status=discord.Status.dnd)
        hour = time.now().hour
        when = int(hour / 6)
        send = f"{time.time()} > Server is online - {lists.hello[when]}"
        # if self.config.logs:
        #     await logs.log_channel(self.bot, "uptime").send(send)
        if self.config["logs"]:
            logs.save(logs.get_place(self.type, "uptime"), f"{time.time()} > Server is online")
        slc = self.bot.get_channel(577599230567383058)
        if slc is not None:
            await slc.send(send)
        ad = times['ad']
        if ad:
            print(f"{time.time()} > Detected that I'm already doing the loop...")
            return
        else:
            times['ad'] = True
            open(self.changes, 'w+').write(json.dumps(times))
            cp = self.config["bots"][self.type]["change_playing"]
            ca = self.config["bots"][self.type]["change_avatars"]
            cs = self.config["bots"][self.type]["change_senko"]
            # sl = self.bot.get_guild(568148147457490954)
            while cp or ca or cs:
                if self.exists:
                    try:
                        self.config = generic.get_config()
                        cp = self.config["bots"][self.type]["change_playing"]
                        ca = self.config["bots"][self.type]["change_avatars"]
                        cs = self.config["bots"][self.type]["change_senko"]
                        log = self.config["logs"]
                        now = time.now()
                        try:
                            # times = json.loads('changes.json')
                            times = json.loads(open(self.changes, 'r').read())
                        except Exception as e:
                            print(e)
                            times = changes.copy()
                        hour = now.hour
                        pf = logs.get_place(self.type, "playing")
                        af = logs.get_place(self.type, "avatar")
                        sf = logs.get_place(self.type, "senko")
                        if cp:
                            this = now.minute * 60 + now.second
                            that = times['playing']
                            speed = self.config["playing_rate"]
                            plays = lists.playing
                            a, b = [int(this / speed) % len(plays), int(that / speed) % len(plays)]
                            if a != b:
                                play = plays[a]
                                playing = f"{play} | v{self.config['bots'][self.type]['version']}"
                                await self.bot.change_presence(activity=discord.Activity(type=0, name=playing),
                                                               status=discord.Status.dnd)
                                times["playing"] = this
                                if log:
                                    logs.save(pf, f"{time.time()} > Updated playing to `{playing}` - "
                                                  f"{a+1}/{len(plays)}")
                        if ca:
                            that, last = times['avatar']
                            if hour != that:
                                avatars = lists.avatars
                                al = len(avatars)
                                an = last + 1 if last < al - 1 else 0
                                avatar = avatars[an]
                                e = False
                                s1, s2 = [f"{time.time()} > Avatar changed - {an+1}/{al}",
                                          f"{time.time()} > Didn't change avatar cuz error"]
                                try:
                                    bio = await http.get(avatar, res_method="read")
                                    await self.bot.user.edit(avatar=bio)
                                    print(s1)
                                except discord.errors.HTTPException:
                                    print(s2)
                                    e = True
                                send = s2 if e else s1
                                if log:
                                    logs.save(af, send)
                                    # await logs.log_channel(self.bot, "senko").send(send)
                                times['avatar'] = [hour, an]
                        if cs:
                            that, last = times['senko']
                            if hour != that:
                                senko_list = lists.server_icons
                                ss = len(senko_list)
                                sn = last + 1 if last < ss - 1 else 0
                                senko = senko_list[sn]
                                e = False
                                s1, s2 = [f"{time.time()} > Rainbow Senko - {sn+1}/{ss}",
                                          f"{time.time()} > Didn't change Senko Lair icon cuz error"]
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
                                    # await logs.log_channel(self.bot, "senko").send(send)
                                    logs.save(sf, send)
                                times['senko'] = [hour, sn]
                        open(self.changes, 'w+').write(json.dumps(times))
                    except PermissionError:
                        print(f"{time.time()} > Looks like I failed to save changes.. Weird")
                    except ClientConnectorError:
                        print(f"{time.time()} > Looks like the bot tried to do something before it was even connected.")
                    except Exception as e:
                        print(f"{time.time()} > {type(e).__name__}: {e}")
                await asyncio.sleep(5)

    @commands.Cog.listener()
    async def on_connect(self):
        if not hasattr(self.bot, 'uptime'):
            self.bot.uptime = time.now(True)

        print(f"{time.time()} > Connection established.")

        # await self.readiness()

    @commands.Cog.listener()
    async def on_disconnect(self):
        self.exists = False
        phrases = ["My life is over", "UwU, not again!"]
        print(f"{time.time()} > {random.choice(phrases)}")

    @commands.Cog.listener()
    async def on_ready(self):
        self.exists = True
        await self.readiness()


def setup(bot):
    bot.add_cog(Events(bot))
