import asyncio
import json
import random

import aiohttp
import discord
from discord.ext import commands

from core.utils import general, emotes, time, logger, http
from suager.utils import lists

changes = {"playing": 3601, "avatar": [25, -1], "ad": False}


async def on_command_error(self, ctx, err):
    if isinstance(err, commands.errors.MissingRequiredArgument) or isinstance(err, commands.errors.BadArgument):
        helper = str(ctx.invoked_subcommand) if ctx.invoked_subcommand else str(ctx.command)
        await ctx.send_help(helper)
    elif isinstance(err, commands.errors.CommandInvokeError):
        error = general.traceback_maker(err.original, ctx.message.content, ctx.guild, ctx.author)
        if "2000 or fewer" in str(err) and len(ctx.message.clean_content) > 1900:
            return general.send("You inputted a very long piece of text.. Well, congrats. The command broke.", ctx.channel)
        await general.send(f"{emotes.Deny} An error has occurred:\n`{type(err.original).__name__}: {err.original}`", ctx.channel)
        ec = self.bot.get_channel(self.bot.local_config["error_channel"])
        if ec is not None:
            await ec.send(error)
    elif isinstance(err, commands.errors.CheckFailure):
        pass
    elif isinstance(err, commands.errors.CommandOnCooldown):
        await general.send(f"This command is currently on cooldown... Try again in {err.retry_after:.2f} seconds.", ctx.channel)
    elif isinstance(err, commands.errors.CommandNotFound):
        pass
    elif isinstance(err, commands.errors.MaxConcurrencyReached):
        await general.send("Maximum concurrency has been reached - try again later.", ctx.channel)


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


async def on_member_remove(self, member: discord.Member):
    logger.log(self.bot.name, "members", f"{time.time()} > {self.bot.local_config['name']} > {member} ({member.id}) just left {member.guild.name}")


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
    while len(self.local_config["playing"]) > 1:
        if self.exists:
            try:
                self.config = general.get_config()
                self.local_config = self.config["bots"][self.bot.index]
                log = self.local_config["logs"]
                now = time.now()
                try:
                    times = json.loads(open(self.changes, 'r').read())
                except Exception as e:
                    general.print_error(f"{time.time()} > on_ready() > {e}")
                    times = changes.copy()
                if len(self.local_config["playing"]) > 1:
                    this = now.minute * 60 + now.second
                    that = times['playing']
                    speed = self.local_config["playing_rate"]
                    plays = self.local_config["playing"]
                    a, b = [int(this / speed) % len(plays), int(that / speed) % len(plays)]
                    if a != b:
                        play = random.choice(plays)
                        playing = f"{play} | v{self.local_config['short_version']}"
                        await self.bot.change_presence(activity=discord.Game(name=playing), status=discord.Status.dnd)
                        times["playing"] = this
                        if log:
                            logger.log(self.bot.name, "playing", f"{time.time()} > {self.bot.local_config['name']} > Updated playing to {playing}")
                open(self.changes, 'w+').write(json.dumps(times))
            except PermissionError:
                general.print_error(f"{time.time()} > {self.bot.local_config['name']} > on_ready > Failed to save changes.")
            except aiohttp.ClientConnectorError:
                general.print_error(f"{time.time()} > {self.bot.local_config['name']} > on_ready > The bot tried to do something while disconnected.")
            except Exception as e:
                general.print_error(f"{time.time()} > {self.bot.local_config['name']} > on_ready > {type(e).__name__}: {e}")
        await asyncio.sleep(5)


async def avatar_changer(self):
    if self.exists:
        try:
            self.config = general.get_config()
            self.local_config = self.config["bots"][self.bot.index]
            log = self.local_config["logs"]
            now = time.now()
            try:
                times = json.loads(open(self.changes, 'r').read())
            except Exception as e:
                general.print_error(f"{time.time()} > on_ready() > {e}")
                times = changes.copy()
            that, last = times['avatar']
            hour = now.hour
            if hour != that:
                avatars = lists.avatars
                al = len(avatars)
                an = last + 1 if last < al - 1 else 0
                avatar = avatars[an]
                e = False
                s1, s2 = [f"{time.time()} > {self.bot.name} > Avatar changed - {an + 1}/{al}",
                          f"{time.time()} > {self.bot.name} > Didn't change avatar due to an error"]
                try:
                    bio = await http.get(avatar, res_method="read")
                    await self.bot.user.edit(avatar=bio)
                except discord.errors.HTTPException:
                    e = True
                send = s2 if e else s1
                if log:
                    logger.log(self.bot.name, "avatar", send)
                times['avatar'] = [hour, an]
            open(self.changes, 'w+').write(json.dumps(times))
        except PermissionError:
            general.print_error(f"{time.time()} > {self.bot.local_config['name']} > on_ready > Failed to save changes.")
        except aiohttp.ClientConnectorError:
            general.print_error(f"{time.time()} > {self.bot.local_config['name']} > on_ready > The bot tried to do something while disconnected.")
        except Exception as e:
            general.print_error(f"{time.time()} > {self.bot.local_config['name']} > on_ready > {type(e).__name__}: {e}")
    await asyncio.sleep(5)
