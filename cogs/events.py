import asyncio
import json
import os
import random
from datetime import datetime

import discord
import psutil
from aiohttp import ClientConnectorError
from discord.ext import commands

from cogs.genders import genders
from utils import generic, time, logs, lists, http, emotes
from utils.emotes import AlexHeartBroken

ct = time.now()  # Current time
changes = {"playing": 3601, "avatar": [25, -1], "senko": [25, -1], "ad": False, "tired": {
    "dates": [], "time": [], "lr": [ct.year, ct.month, ct.day]
}}


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = generic.get_config()
        self.process = psutil.Process(os.getpid())
        self.exists = False
        try:
            times = json.loads(open('changes.json', 'r').read())
        except Exception as e:
            print(e)
            times = changes.copy()
        self.today = times['tired']['lr']
        # self.ad = False

    @commands.Cog.listener()
    async def on_command_error(self, ctx, err):
        if isinstance(err, commands.errors.MissingRequiredArgument) or isinstance(err, commands.errors.BadArgument):
            # await send_cmd_help(ctx)
            helper = str(ctx.invoked_subcommand) if ctx.invoked_subcommand else str(ctx.command)
            await ctx.send_help(helper)

        elif isinstance(err, commands.errors.CommandInvokeError):
            error = generic.traceback_maker(err.original, text=ctx.message.content)
            if "2000 or fewer" in str(err) and len(ctx.message.clean_content) > 1900:
                return await ctx.send(
                    f"You attempted to make the command display more than 2,000 characters...\n"
                    f"Congratulations, you broke it. Now go find something more interesting to do."
                )
            # await self.bot.get_user(302851022790066185).send(error)
            _error = generic.traceback_maker(err.original, advance=False)
            await ctx.send(f"There has been an error, try again later...\n`{_error}`")
            if self.config.logs:
                await logs.log_channel(self.bot, "errors").send(error)

        elif isinstance(err, commands.errors.CheckFailure):
            pass

        elif isinstance(err, commands.errors.CommandOnCooldown):
            await ctx.send(f"This command is on cooldown... try again in {generic.round_value(err.retry_after)} "
                           f"seconds.")

        elif isinstance(err, commands.errors.CommandNotFound):
            pass

        elif isinstance(err, commands.errors.MaxConcurrencyReached):
            await ctx.send("This command cannot be used right now - max concurrency reached. Try again later.")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        send = f"{time.time()} > Joined {guild.name}"
        if self.config.logs:
            await logs.log_channel(self.bot, "servers").send(send)
        print(send)
        if not self.config.join_message:
            return

        try:
            to_send = sorted([chan for chan in guild.channels if chan.permissions_for(guild.me).send_messages and
                              isinstance(chan, discord.TextChannel)], key=lambda x: x.position)[0]
        except IndexError:
            pass
        else:
            await to_send.send(self.config.join_message)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        send = f"{time.time()} > Left {guild.name}"
        if self.config.logs:
            await logs.log_channel(self.bot, "servers").send(send)
        print(send)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        # Some shitfuckery below
        try:
            g = ctx.guild.name
        except AttributeError:
            g = "Private Message"
        if ctx.guild.id == 568148147457490954:
            cool_days = [[1, 1], [1, 7], [1, 27], [2, 14], [2, 23], [3, 17], [4, 1], [5, 9], [6, 12],
                         [9, 3], [10, 31], [12, 25], [12, 31]]
            now = time.now()
            year, month, day, hour = now.year, now.month, now.day, now.hour
            try:
                # times = json.loads('changes.json')
                times = json.loads(open('changes.json', 'r').read())
            except Exception as e:
                print(e)
                times = changes.copy()
            changed = False
            for date in cool_days:
                if month == date[0] and day == date[1]:
                    d = [ctx.author.id, year, month, day]
                    if d not in times['tired']['dates']:
                        times['tired']['dates'].append(d)
                        today = now.strftime("%d %b %Y")
                        await ctx.channel.send(f"{emotes.BlobSleepy} {ctx.author.mention} "
                                               f"What if I sometimes want a day off too?")
                        print(f"{time.time()} > Reminded {ctx.author} that it's {today} today and I want a day off")
                        changed = True
            # if ctx.author.id == 302851022790066185:  # Me
            if hour >= 23 or hour < 7:
                t = [ctx.author.id, year, month, day, hour]
                if t not in times['tired']['time']:
                    times['tired']['time'].append(t)
                    rn = now.strftime("%H:%M")
                    await ctx.channel.send(f"{emotes.BlobSleepy} {ctx.author.mention} It's already "
                                           f"{time.time(day=False, seconds=False)}! I wanna rest, and so should you...")
                    print(f"{time.time()} > Reminder {ctx.author} that it's already {rn} and I'm tired.")
                    changed = True
            if changed:
                open('changes.json', 'w+').write(json.dumps(times))
        send = f"{time.time()} > {g} > {ctx.author} > {ctx.message.content}"\
            .replace("<@302851022790066185>", "<Regaus mention>").replace("<@!302851022790066185>", "<Regaus mention>")
        if self.config.logs:
            await logs.log_channel(self.bot).send(send)
        print(send)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if self.config.spyware:
            await logs.log_channel(self.bot, "spyware").send(
                f"{time.time()} > {member} just joined {member.guild.name}")
        if member.guild.id == 568148147457490954:
            td = time.now_ts() - datetime.timestamp(member.created_at)
            if td < 86400:
                await member.kick(reason="Account created less than a day ago")
            try:
                gender = json.loads(open(f"data/gender/{member.id}.json", "r").read())
            except FileNotFoundError:
                gender = genders.copy()
            roles = [651339885013106688, 651339932681371659, 651339982652571648]
            snowflakes = [discord.Object(id=i) for i in roles]
            reason = "Gender assignments - Joined Senko Lair"
            if gender['male']:
                await member.add_roles(snowflakes[0], reason=reason)
            if gender['female']:
                await member.add_roles(snowflakes[1], reason=reason)
            if gender['invalid']:
                await member.add_roles(snowflakes[2], reason=reason)
            embed = discord.Embed(colour=generic.random_colour())
            embed.set_thumbnail(url=member.avatar_url)
            embed.add_field(name="User ID", value=member.id)
            embed.add_field(name="Created at", value=time.time_output(member.created_at))
            embed.add_field(name="Joined at", value=time.time_output(member.joined_at))
            await self.bot.get_channel(568148147457490958).send(f"Welcome {member.mention} to Senko Lair!")
            await self.bot.get_channel(650774303192776744).send(f"{member.name} just joined Senko Lair.", embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if self.config.spyware:
            await logs.log_channel(self.bot, "spyware").send(f"{time.time()} > {member} just left {member.guild.name}")
        if member.guild.id == 568148147457490954:
            await self.bot.get_channel(610836120321785869).send(
                f"{member.name} has abandoned Senko Lair :( {AlexHeartBroken}")

    async def readiness(self):
        while not self.exists:
            await asyncio.sleep(1)

        if not hasattr(self.bot, 'uptime'):
            self.bot.uptime = time.now(True)

        # config = default.get("config.json")
        playing = f"{self.config.playing} | v{self.config.version}"
        # print(f'Ready: {self.bot.user} | Servers: {len(self.bot.guilds)} - Members: {len(self.bot.users)}')
        print(f"{time.time()} > Ready: {self.bot.user} - {len(self.bot.guilds)} servers, {len(self.bot.users)} users")
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing,
                                                                 name=playing), status=discord.Status.dnd)
        # general_commands = self.bot.get_channel(577599230567383058)
        # await general_commands.send(f"{statuses.time_output()} - Bot is now online")
        # logs = statuses.logs
        # log_channel = statuses.tb_log_channel(self.bot)
        hour = time.now().hour
        when = int(hour / 6)
        send = f"{time.time()} > Server is online\n{lists.hello[when]}, motherfuckers, " \
               f"I'm ready to torture your minds >:3"
        if self.config.logs:
            await logs.log_channel(self.bot, "uptime").send(send)
            # await log_channel.send(f"{statuses.time_output()} - Server is online")
        await self.bot.get_channel(577599230567383058).send(send)
        try:
            # times = json.loads('changes.json')
            times = json.loads(open('changes.json', 'r').read())
        except Exception as e:
            print(e)
            times = changes.copy()
        ad = times['ad']
        if ad:
            print(f"{time.time()} > Detected that I'm already doing the loop...")
            return
        else:
            times['ad'] = True
            open('changes.json', 'w+').write(json.dumps(times))
            cp = self.config.changeplaying
            ca = self.config.changeavatars
            cs = self.config.changesenkolair
            sl = self.bot.get_guild(568148147457490954)
            while cp or ca or cs:
                try:
                    self.config = generic.get_config()
                    cp = self.config.changeplaying
                    ca = self.config.changeavatars
                    cs = self.config.changesenkolair
                    log = self.config.logs
                    now = time.now()
                    try:
                        # times = json.loads('changes.json')
                        times = json.loads(open('changes.json', 'r').read())
                    except Exception as e:
                        print(e)
                        times = changes.copy()
                    today = [now.year, now.month, now.day]
                    if today != self.today:
                        print(f"{time.time()} > Nice, a new day began!")
                        self.today = today
                        times['tired']['dates'] = []
                        times['tired']['time'] = []
                        times['tired']['lr'] = today
                    if cp:
                        this = now.minute * 60 + now.second
                        that = times['playing']
                        speed = self.config.playing_rate
                        plays = lists.playing
                        a, b = [int(this / speed) % len(plays), int(that / speed) % len(plays)]
                        if a != b:
                            await generic.you_little_shit(sl)
                            play = plays[a]
                            playing = f"{play} | v{self.config.version}"
                            await self.bot.change_presence(activity=discord.Activity(type=0, name=playing),
                                                           status=discord.Status.dnd)
                            times["playing"] = this
                            if log:
                                ch = logs.log_channel(self.bot, "playing")
                                try:
                                    await ch.send(f"{time.time()} > Updated playing to `{playing}` - "
                                                  f"{a+1}/{len(plays)}")
                                except discord.errors.HTTPException or ClientConnectorError:
                                    print(f"{time.time()} > Updated playing to `{playing}`, "
                                          f"but failed to send message.")
                    hour = now.hour
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
                                await logs.log_channel(self.bot, "senko").send(send)
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
                                await logs.log_channel(self.bot, "senko").send(send)
                            times['senko'] = [hour, sn]
                    open('changes.json', 'w+').write(json.dumps(times))
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

        # print(f"{time.time()} > I am ready to abuse your mind")


def setup(bot):
    bot.add_cog(Events(bot))
