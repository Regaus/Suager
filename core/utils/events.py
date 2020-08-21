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
    locale = langs.gl(ctx.guild, self.db)
    if isinstance(err, commands.errors.MissingRequiredArgument) or isinstance(err, commands.errors.BadArgument):
        helper = str(ctx.invoked_subcommand) if ctx.invoked_subcommand else str(ctx.command)
        await ctx.send_help(helper)
    elif isinstance(err, commands.errors.CommandInvokeError):
        error = general.traceback_maker(err.original, ctx.message.content, ctx.guild, ctx.author)
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


async def on_member_remove(self, member: discord.Member):
    logger.log(self.bot.name, "members", f"{time.time()} > {self.bot.local_config['name']} > {member} ({member.id}) just left {member.guild.name}")
    if self.bot.name == "suager":
        if member.guild.id == 568148147457490954:
            await general.send(f"{member.name} just abandoned Senko Lair...", self.bot.get_channel(610836120321785869))
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


async def on_member_unban(self, guild: discord.Guild, user: discord.User):
    logger.log(self.bot.name, "members", f"{time.time()} > {self.bot.local_config['name']} > {user} ({user.id}) just got unbanned from {guild.name}")


async def on_ready(self):
    print(f"{time.time()} > {self.bot.local_config['name']} > Ready: {self.bot.user} - {len(self.bot.guilds)} servers, {len(self.bot.users)} users")
    try:
        times = json.loads(open(self.changes, 'r').read())
    except Exception as e:
        print(e)
        times = changes.copy()
    playing = f"{self.local_config['playing'][0]} | v{self.local_config['short_version']}"
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
                "suager": [
                    [0, fv],
                    [0, "with Regaus"],
                    [0, "without you"],
                    [0, "with nobody"],
                    [0, "with your feelings"],
                    [0, "Custom Status"],
                    [0, "with the Nuriki Cult"],
                    [0, "PyCharm"],
                    [1, "Русские Вперёд!"],
                    [0, f"{self.local_config['prefixes'][0]}help | {sv}"],
                    [2, "music"],
                    [0, "<CustomActivity name='Something interesting' emoji=<PartialEmoji animated=False name='SenkoDX' id=709828828184445009>>"],
                    [0, "<Game object at 0x000001C86D4D1520>"],
                    [3, "anime"],
                    [0, "nothing"],
                    [1, "nothing"],
                    [2, "nothing"],
                    [3, "you"],
                    [3, f"{len(self.bot.guilds):,} guilds"],
                    [0, f"with {len(self.bot.users):,} users"]
                ]
            }
            activity, playing = random.choice(plays.get(self.bot.name))
            # playing = f"{play} | v{self.local_config['short_version']}"
            await self.bot.change_presence(activity=discord.Activity(type=activity, name=playing), status=discord.Status.dnd)
            if log:
                logger.log(self.bot.name, "playing", f"{time.time()} > {self.bot.local_config['name']} > Updated playing to {playing}")
        except PermissionError:
            general.print_error(f"{time.time()} > {self.bot.local_config['name']} > on_ready > Failed to save changes.")
        except aiohttp.ClientConnectorError:
            general.print_error(f"{time.time()} > {self.bot.local_config['name']} > on_ready > The bot tried to do something while disconnected.")
        except Exception as e:
            general.print_error(f"{time.time()} > {self.bot.local_config['name']} > on_ready > {type(e).__name__}: {e}")


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
            general.print_error(f"{time.time()} > {self.bot.local_config['name']} > on_ready > Failed to save changes.")
        except aiohttp.ClientConnectorError:
            general.print_error(f"{time.time()} > {self.bot.local_config['name']} > on_ready > The bot tried to do something while disconnected.")
        except Exception as e:
            general.print_error(f"{time.time()} > {self.bot.local_config['name']} > on_ready > {type(e).__name__}: {e}")
    await asyncio.sleep(5)
