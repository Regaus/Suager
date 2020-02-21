import asyncio
import json
import os

import discord
import psutil
from aiohttp import ClientConnectorError
from discord.ext import commands

from cogs.genders import genders
from utils import generic, time, logs, lists, http
from utils.emotes import AlexHeartBroken

changes = {"playing": 3601, "avatar": [25, -1], "senko": [25, -1]}


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = generic.get_config()
        self.process = psutil.Process(os.getpid())

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
        try:
            g = ctx.guild.name
        except AttributeError:
            g = "Private Message"
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
            embed.add_field(name="Joined at", value=time.time_output(member.joined_at))
            embed.add_field(name="Created at", value=time.time_output(member.created_at))
            await self.bot.get_channel(568148147457490958).send(f"Welcome {member.mention} to Senko Lair!")
            await self.bot.get_channel(650774303192776744).send(f"{member.name} just joined Senko Lair.", embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if self.config.spyware:
            await logs.log_channel(self.bot, "spyware").send(f"{time.time()} > {member} just left {member.guild.name}")
        if member.guild.id == 568148147457490954:
            await self.bot.get_channel(610836120321785869).send(
                f"{member.name} has abandoned Senko Lair :( {AlexHeartBroken}")

    @commands.Cog.listener()
    async def on_ready(self):
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
        send = f"{time.time()} > Server is online"
        if self.config.logs:
            await logs.log_channel(self.bot, "uptime").send(send)
            # await log_channel.send(f"{statuses.time_output()} - Server is online")
        await self.bot.get_channel(577599230567383058).send(send)
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
                                await ch.send(f"{time.time()} > Updated playing to `{playing}` - {a+1}/{len(plays)}")
                            except discord.errors.HTTPException or ClientConnectorError:
                                print(f"{time.time()} > Updated playing to `{playing}`, but failed to send message.")
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


def setup(bot):
    bot.add_cog(Events(bot))
