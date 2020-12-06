import asyncio
import json
import random

import aiohttp
import discord
from discord.ext import commands

from core.utils import general, time, logger, http
from languages import langs
from suager.utils import lists

changes = {"playing": 3601, "avatar": [25, -1], "ad": False}


async def on_command_error(self, ctx, err):
    locale = langs.gl(ctx)
    if isinstance(err, commands.errors.MissingRequiredArgument) or isinstance(err, commands.errors.BadArgument):
        helper = str(ctx.invoked_subcommand) if ctx.invoked_subcommand else str(ctx.command)
        await ctx.send_help(helper)
    elif isinstance(err, commands.errors.CommandInvokeError):
        error = general.traceback_maker(err.original, ctx.message.content[:1000], ctx.guild, ctx.author)
        if "2000 or fewer" in str(err) and len(ctx.message.clean_content) > 1900:
            return await general.send(langs.gls("events_err_message_too_long", locale), ctx.channel)
            # return general.send("You inputted a very long piece of text.. Well, congrats. The command broke.", ctx.channel)
        await general.send(langs.gls("events_err_error", locale, type(err.original).__name__, str(err.original)), ctx.channel)
        # await general.send(f"{emotes.Deny} An error has occurred:\n`{type(err.original).__name__}: {err.original}`", ctx.channel)
        ec = self.bot.get_channel(self.bot.local_config["error_channel"])
        if ec is not None:
            await ec.send(error)
    elif isinstance(err, commands.errors.CheckFailure):
        pass
    elif isinstance(err, commands.errors.CommandOnCooldown):
        await general.send(langs.gls("events_err_cooldown", locale, langs.gfs(err.retry_after, locale)), ctx.channel)
        # await general.send(f"This command is currently on cooldown... Try again in {err.retry_after:.2f} seconds.", ctx.channel)
    elif isinstance(err, commands.errors.CommandNotFound):
        pass
    elif isinstance(err, commands.errors.MaxConcurrencyReached):
        await general.send(langs.gls("events_err_concurrency", locale), ctx.channel)
        # await general.send("Maximum concurrency has been reached - try again later.", ctx.channel)


async def on_guild_join(self, guild):
    send = f"{time.time()} > {self.bot.local_config['name']} > Joined {guild.name} ({guild.id})"
    if self.local_config["logs"]:
        logger.log(self.bot.name, "guilds", send)
    print(send)
    if not self.local_config["join_message"]:
        return
    try:
        to_send = sorted([c for c in guild.channels if c.permissions_for(guild.me).send_messages and isinstance(c, discord.TextChannel)],
                         key=lambda x: x.position)[0]
    except IndexError:
        pass
    else:
        await to_send.send(self.local_config["join_message"])


async def on_guild_remove(self, guild):
    send = f"{time.time()} > {self.bot.local_config['name']} > Left {guild.name} ({guild.id})"
    if self.local_config["logs"]:
        logger.log(self.bot.name, "guilds", send)
    print(send)
    if self.bot.name == "suager":
        self.db.execute("DELETE FROM leveling WHERE gid=?", (guild.id,))
        self.db.execute("DELETE FROM economy WHERE gid=?", (guild.id,))
        self.db.execute("DELETE FROM tags WHERE gid=?", (guild.id,))
        self.db.execute("DELETE FROM tbl_clan WHERE gid=?", (guild.id,))
        self.db.execute("DELETE FROM dlram WHERE gid=?", (guild.id,))


async def on_command(self, ctx):
    try:
        g = ctx.guild.name
    except AttributeError:
        g = "Private Message"
    content = ctx.message.clean_content
    send = f"{time.time()} > {self.bot.local_config['name']} > {g} > {ctx.author} ({ctx.author.id}) > {content}"
    if self.local_config["logs"]:
        logger.log(self.bot.name, "commands", send)
    print(send)


async def on_member_join(self, member: discord.Member):
    logger.log(self.bot.name, "members", f"{time.time()} > {self.bot.local_config['name']} > {member} ({member.id}) just joined {member.guild.name}")
    if self.bot.name == "suager":
        if member.guild.id == 568148147457490954:
            await general.send(f"Welcome {member.name} to Senko Lair!", self.bot.get_channel(610836120321785869))
        if member.guild.id == 738425418637639775:
            join = langs.gts(member.joined_at, "en_gb", seconds=True)
            age = langs.td_dt(member.created_at, "en_gb")
            await general.send(f"Welcome {member.name} to Regaus' Playground!\nJoin time: {join}\nAccount age: {age}", self.bot.get_channel(754425619336396851))
    if member.guild.id in [568148147457490954, 738425418637639775] and member.id not in [302851022790066185]:
        if member.name[0] < "A":
            await member.edit(reason="De-hoist", nick=f"z{member.name}")


async def on_member_remove(self, member: discord.Member):
    logger.log(self.bot.name, "members", f"{time.time()} > {self.bot.local_config['name']} > {member} ({member.id}) just left {member.guild.name}")
    if self.bot.name == "suager":
        if member.guild.id == 568148147457490954:
            survival = langs.td_dt(member.joined_at, "en_gb")
            await general.send(f"{member.name} just abandoned Senko Lair after surviving for {survival}...", self.bot.get_channel(610836120321785869))
        if member.guild.id == 738425418637639775:
            survival = langs.td_dt(member.joined_at, "en_gb")
            await general.send(f"{member.name} just abandoned Regaus' Playground after surviving for {survival}...", self.bot.get_channel(754425619336396851))
        uid, gid = member.id, member.guild.id
        self.db.execute("DELETE FROM economy WHERE uid=? AND gid=?", (uid, gid))
        sel = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=?", (uid, gid))
        if sel:
            if sel["xp"] < 0:
                return
            elif sel["level"] < 0:
                self.db.execute("UPDATE leveling SET xp=0 WHERE uid=? AND gid=?", (uid, gid))
            else:
                self.db.execute("DELETE FROM leveling WHERE uid=? AND gid=?", (uid, gid))


async def on_member_ban(self, guild: discord.Guild, user: discord.User or discord.Member):
    logger.log(self.bot.name, "members", f"{time.time()} > {self.bot.local_config['name']} > {user} ({user.id}) just got banned from {guild.name}")
    message = f"{user} ({user.id}) has been **banned** from {guild.name}"
    if guild.id == 568148147457490954:
        await general.send(message, self.bot.get_channel(626028890451869707))
    if guild.id == 738425418637639775:
        await general.send(message, self.bot.get_channel(764469594303234078))


async def on_member_unban(self, guild: discord.Guild, user: discord.User):
    logger.log(self.bot.name, "members", f"{time.time()} > {self.bot.local_config['name']} > {user} ({user.id}) just got unbanned from {guild.name}")
    message = f"{user} ({user.id}) has been **unbanned** from {guild.name}"
    if guild.id == 568148147457490954:
        await general.send(message, self.bot.get_channel(626028890451869707))
    if guild.id == 738425418637639775:
        await general.send(message, self.bot.get_channel(764469594303234078))


async def on_ready(self):
    print(f"{time.time()} > {self.bot.local_config['name']} > Ready: {self.bot.user} - {len(self.bot.guilds)} servers, {len(self.bot.users)} users")
    try:
        times = json.loads(open(self.changes, 'r').read())
    except Exception as e:
        print(e)
        times = changes.copy()
    # playing = f"{self.local_config['playing'][0]} | v{self.local_config['short_version']}"
    playing = f"Loading... | v{self.local_config['short_version']}"
    await self.bot.change_presence(activity=discord.Game(name=playing), status=discord.Status.dnd)
    if self.local_config["logs"]:
        logger.log(self.bot.name, "uptime", f"{time.time()} > {self.bot.local_config['name']} > Bot is online")
    ad = times['ad']
    if ad:
        return
    else:
        times['ad'] = True
        open(self.changes, 'w+').write(json.dumps(times))


async def playing_changer(self):
    if self.exists:
        try:
            log = self.local_config["logs"]
            # plays = self.local_config["playing"]
            fv, sv = f"v{self.local_config['version']}", f"v{self.local_config['short_version']}"
            plays = {
                "cobble": [
                    {"type": 0, "name": fv},
                    {"type": 1, "name": "Nothing", "url": "https://www.twitch.tv/nosmdjf"},
                    {"type": 0, "name": "with Regaus"},
                    {"type": 0, "name": "without you"},
                    {"type": 0, "name": "with nobody"},
                    {"type": 0, "name": "with your feelings"},
                    {"type": 0, "name": f"{self.local_config['prefixes'][0]}help | {sv}"},
                    {"type": 5, "name": "uselessness"},
                    {"type": 0, "name": "Nothing"},
                    {"type": 3, "name": "you"},
                    {"type": 2, "name": "a song"},
                    {"type": 3, "name": "the Void"},
                ],
                "suager": [
                    {"type": 0, "name": fv},
                    {"type": 1, "name": "Русские Вперёд!", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
                    {"type": 1, "name": "Nothing", "url": "https://www.twitch.tv/nosmdjf"},
                    {"type": 2, "name": "Music"},
                    {"type": 5, "name": "a competition"},
                    {"type": 0, "name": "with Regaus"},
                    {"type": 0, "name": "without you"},
                    {"type": 0, "name": "with nobody"},
                    {"type": 0, "name": "with your feelings"},
                    {"type": 0, "name": "Custom Status"},
                    {"type": 5, "name": "Discord"},
                    {"type": 3, "name": "Senko"},
                    {"type": 0, "name": f"{self.local_config['prefixes'][0]}help | {sv}"},
                    {"type": 5, "name": "uselessness"},
                    {"type": 0, "name": "Nothing"},
                    {"type": 1, "name": "Nothing", "url": "https://www.youtube.com/watch?v=qD_CtEX5OuA"},
                    {"type": 3, "name": "you"},
                    {"type": 0, "name": "None"},
                    {"type": 0, "name": "KeyError: 'name'"},
                    {"type": 0, "name": "IndexError: list index out of range"},
                    {"type": 0, "name": "suager.utils.exceptions.BoredomError: Imagine reading this"},
                    {"type": 0, "name": "TypeError: unsupported operand type(s) for +: 'Activity' and 'Activity'"},
                    {"type": 2, "name": "a song"},
                    {"type": 2, "name": "10 Hours of Nothing ft. Nobody (Non-Existent Remix by Negative Zero)"},
                    {"type": 3, "name": "the Void"},
                    {"type": 5, "name": "Minecraft"},
                    {"type": 0, "name": "Minecraft"},
                    {"type": 1, "name": "Minecraft", "url": "https://www.youtube.com/watch?v=d1YBv2mWll0"},
                ]
            }
            _activity = random.choice(plays.get(self.bot.name))
            # playing = f"{play} | v{self.local_config['short_version']}"
            if _activity["type"] == 0:  # Game
                activity = discord.Game(name=_activity["name"])
            elif _activity["type"] == 1:  # Streaming
                name = _activity["name"]
                activity = discord.Streaming(name=name, details=name, url=_activity["url"])
            else:
                activity = discord.Activity(type=_activity["type"], name=_activity["name"])
                # activity = discord.Activity(type=activity, name=playing)
            await self.bot.change_presence(activity=activity, status=discord.Status.dnd)
            if log:
                name = _activity["name"]
                status = {
                    0: "Playing",
                    1: "Streaming",
                    2: "Listening to",
                    3: "Watching",
                    5: "Competing in"
                }.get(_activity["type"], "Undefined")
                logger.log(self.bot.name, "playing", f"{time.time()} > {self.bot.local_config['name']} > Updated activity to {status} {name}")
        except PermissionError:
            general.print_error(f"{time.time()} > {self.bot.local_config['name']} > Playing Changer > Failed to save changes.")
        except aiohttp.ClientConnectorError:
            general.print_error(f"{time.time()} > {self.bot.local_config['name']} > Playing Changer > The bot tried to do something while disconnected.")
        except Exception as e:
            general.print_error(f"{time.time()} > {self.bot.local_config['name']} > Playing Changer > {type(e).__name__}: {e}")


async def avatar_changer(self):
    if self.exists:
        try:
            self.config = general.get_config()
            self.local_config = self.config["bots"][self.bot.index]
            log = self.local_config["logs"]
            avatars = lists.avatars
            avatar = random.choice(avatars)
            e = False
            s1, s2 = [f"{time.time()} > {self.bot.name} > Avatar updated", f"{time.time()} > {self.bot.name} > Didn't change avatar due to an error"]
            try:
                bio = await http.get(avatar, res_method="read")
                await self.bot.user.edit(avatar=bio)
            except discord.errors.HTTPException:
                e = True
            send = s2 if e else s1
            if log:
                logger.log(self.bot.name, "avatar", send)
        except PermissionError:
            general.print_error(f"{time.time()} > {self.bot.local_config['name']} > Avatar Changer > Failed to save changes.")
        except aiohttp.ClientConnectorError:
            general.print_error(f"{time.time()} > {self.bot.local_config['name']} > Avatar Changer > The bot tried to do something while disconnected.")
        except Exception as e:
            general.print_error(f"{time.time()} > {self.bot.local_config['name']} > Avatar Changer > {type(e).__name__}: {e}")
    await asyncio.sleep(5)
