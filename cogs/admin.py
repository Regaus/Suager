import ast
import asyncio
import importlib
import os
import re
from asyncio.subprocess import PIPE
from io import BytesIO

import aiohttp
import discord
from discord.ext import commands

from utils import generic, permissions, time, database, logs, data_io, http, emotes


def insert_returns(body):
    # insert return statement if the last expression is a expression statement
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    # for if statements, we insert returns into the body and the or-else
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    # for with blocks, again we insert returns into the body
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)


async def eval_(ctx: commands.Context, cmd):
    try:
        fn_name = "_eval_expr"

        cmd = cmd.strip("` ")

        # add a layer of indentation
        cmd = "\n".join(f"    {i}" for i in cmd.splitlines())

        # wrap in async def body
        body = f"async def {fn_name}():\n{cmd}"

        parsed = ast.parse(body)
        body = parsed.body[0].body

        insert_returns(body)

        env = {
            'bot': ctx.bot,
            'discord': discord,
            'commands': commands,
            'ctx': ctx,
            'db': database.Database(),
            '__import__': __import__,
        }
        exec(compile(parsed, filename="<ast>", mode="exec"), env)

        result = (await eval(f"{fn_name}()", env))
        if ctx.guild is None:
            limit = 8000000
        else:
            limit = int(ctx.guild.filesize_limit / 1.05)
        if len(str(result)) == 0 or result is None:
            return await generic.send("Code has been run, however returned no result.", ctx.channel)
        elif len(str(result)) in range(2001, limit + 1):
            async with ctx.typing():
                data = BytesIO(str(result).encode('utf-8'))
                return await generic.send(f"Result was a bit too long... ({len(str(result)):,} chars)", ctx.channel,
                                          file=discord.File(data, filename=f"{time.file_ts('Eval')}"))
        elif len(str(result)) > limit:
            async with ctx.typing():
                data = BytesIO(str(result)[-limit:].encode('utf-8'))
                return await generic.send(f"Result was a bit too long... ({len(str(result)):,} chars)\nSending last {limit:,} chars", ctx.channel,
                                          file=discord.File(data, filename=f"{time.file_ts('Eval')}"))
        else:
            return await generic.send(str(result), ctx.channel)
    except Exception as e:
        return await generic.send(f"{type(e).__name__}: {e}", ctx.channel)


def reload_util(name: str):
    return reload_module("utils", name)


def reload_locale(name: str):
    return reload_module("langs", name)


def reload_module(folder: str, name: str):
    name_maker = f"**{folder}/{name}.py**"
    try:
        module_name = importlib.import_module(f"{folder}.{name}")
        importlib.reload(module_name)
    except ModuleNotFoundError:
        return f"Couldn't find module named {name_maker}"
    except Exception as e:
        error = generic.traceback_maker(e)
        return f"Module {name_maker} returned an error and was not reloaded...\n{error}"
    reloaded = f"Reloaded module {name_maker}"
    if generic.get_config()["logs"]:
        logs.log("changes", f"{time.time()} > {reloaded}")
    return reloaded


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = generic.get_config()
        self.db = database.Database()
        self.admin_mod = ["cogs.admin", "cogs.birthdays"]

    @commands.command(name="amiowner")
    @commands.cooldown(2, 5, commands.BucketType.guild)
    async def are_you_admin(self, ctx: commands.Context):
        """ Are you admin? """
        if generic.is_locked(ctx.guild, "amiowner"):
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "channel_locked"), ctx.channel)
        if ctx.author.id == 86477779717066752:
            out = "admin_source"
        elif ctx.author.id in self.config["owners"]:
            out = "admin_yes"
        else:
            out = "admin_no"
        return await generic.send(generic.gls(generic.get_lang(ctx.guild), out, [ctx.author.name]), ctx.channel)

    @commands.command(name="db")
    @commands.check(permissions.is_owner)
    async def db_command(self, ctx: commands.Context, *, query: str):
        """ Database query """
        try:
            data = self.db.execute(query)
            return await generic.send(data, ctx.channel)
        except Exception as e:
            return await generic.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="fetch", aliases=["select"])
    @commands.check(permissions.is_owner)
    async def db_fetch(self, ctx: commands.Context, *, query: str):
        """ Fetch data from db """
        try:
            data = self.db.fetch("SELECT " + query)
            result = f"{data}"
            if ctx.guild is None:
                limit = 8000000
            else:
                limit = int(ctx.guild.filesize_limit / 1.05)
            # return await ctx.send(result)
            rl = len(str(result))
            if rl == 0 or result is None:
                return await generic.send("Code has been run, however returned no result.", ctx.channel)
            elif rl in range(2001, limit + 1):
                async with ctx.typing():
                    data = BytesIO(str(result).encode('utf-8'))
                    return await generic.send(f"Result was a bit too long... ({rl:,} chars)", ctx.channel,
                                              file=discord.File(data, filename=f"{time.file_ts('Fetch')}"))
            elif rl > limit:
                async with ctx.typing():
                    data = BytesIO(str(result)[-limit:].encode('utf-8'))
                    return await generic.send(f"Result was a bit too long... ({rl:,} chars)\nSending last {limit:,} chars", ctx.channel,
                                              file=discord.File(data, filename=f"{time.file_ts('Fetch')}"))
            else:
                return await generic.send(str(result), ctx.channel)
        except Exception as e:
            return await generic.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="log", aliases=["logs"])
    @commands.check(permissions.is_owner)
    async def log(self, ctx: commands.Context, log: str, *, search: str = None):
        """ Get logs """
        try:
            data = ""
            for path, _, __ in os.walk("data"):
                if re.compile(r"data\\(\d{4})-(\d{2})-(\d{2})").search(path):
                    _path = path.replace("\\", "/")
                    filename = f"{_path}/{log}.rsf"
                    file = open(filename, "r")
                    if search is None:
                        result = file.read()
                        data += f"{result}"  # Put a newline in the end, just in case
                    else:
                        stuff = file.readlines()
                        result = ""
                        for line in stuff:
                            if search in line:
                                result += line
                        data += f"{result}"
            if ctx.guild is None:
                limit = 8000000
            else:
                limit = int(ctx.guild.filesize_limit / 1.05)
            rl = len(str(data))
            if rl == 0 or data is None:
                return await generic.send("Nothing was found...", ctx.channel)
            elif 0 < rl <= limit:
                async with ctx.typing():
                    _data = BytesIO(str(data).encode('utf-8'))
                    return await generic.send(f"Results for {log}.rsf - search term `{search}` - {rl:,} chars", ctx.channel,
                                              file=discord.File(_data, filename=f"{time.file_ts('Logs')}"))
            elif rl > limit:
                async with ctx.typing():
                    _data = BytesIO(str(data)[-limit:].encode('utf-8'))
                    return await generic.send(f"Result was a bit too long... ({rl:,} chars) - search term `{search}`\nSending latest", ctx.channel,
                                              file=discord.File(_data, filename=f"{time.file_ts('Logs')}"))
        except Exception as e:
            return await generic.send(f"{type(e).__name__}: {e}", ctx.channel)
        """try:
            if search is None:
                data = open(f"data/{log}.rsf").read()
                result = f"{data}"
            else:
                data = open(f"data/{log}.rsf").readlines()
                result = ""
                for line in data:
                    if search in line:
                        result += line
            if ctx.guild is None:
                limit = 8000000
            else:
                limit = int(ctx.guild.filesize_limit / 1.05)
            rl = len(str(result))
            if rl == 0 or result is None:
                return await generic.send("Nothing was found...", ctx.channel)
            elif 0 < rl <= limit:
                async with ctx.typing():
                    data = BytesIO(str(result).encode('utf-8'))
                    return await generic.send(f"Results for {log}.rsf - search term `{search}` - {rl:,} chars", ctx.channel,
                                              file=discord.File(data, filename=f"{time.file_ts('Logs')}"))
            elif rl > limit:
                async with ctx.typing():
                    data = BytesIO(str(result)[-limit:].encode('utf-8'))
                    return await generic.send(f"Result was a bit too long... ({rl:,} chars)\nSending latest", ctx.channel,
                                              file=discord.File(data, filename=f"{time.file_ts('Logs')}"))
        except Exception as e:
            return await generic.send(f"{type(e).__name__}: {e}", ctx.channel)
    """

    @commands.command(name='eval')
    @commands.check(permissions.is_owner)
    async def eval_cmd(self, ctx: commands.Context, *, cmd):
        """ Evaluates input.
        Input is interpreted as newline separated statements.
        If the last statement is an expression, that is the return value.
        Such that `//eval 1 + 1` gives `2` as the result.
        """
        return await eval_(ctx, cmd)

    @commands.command(name="reload", aliases=["r"])
    @commands.check(permissions.is_owner)
    async def reload(self, ctx: commands.Context, name: str):
        """ Reloads an extension. """
        try:
            self.bot.reload_extension(f"cogs.{name}")
        except Exception as e:
            return await generic.send(f"{type(e).__name__}: {e}", ctx.channel)
        reloaded = f"Reloaded extension **cogs/{name}.py**"
        await generic.send(reloaded, ctx.channel)
        if generic.get_config()["logs"]:
            logs.log("changes", f"{time.time()} > {reloaded}")

    @commands.command(name="reloadall", aliases=["rall", "ra"])
    @commands.check(permissions.is_owner)
    async def reload_all(self, ctx: commands.Context):
        """ Reloads all extensions. """
        error_collection = []
        for file in os.listdir("cogs"):
            if file.endswith(".py"):
                name = file[:-3]
                try:
                    self.bot.reload_extension(f"cogs.{name}")
                except Exception as e:
                    error_collection.append([file, generic.traceback_maker(e, advance=False)])
        if error_collection:
            output = "\n".join([f"**{g[0]}** ```fix\n{g[1]}```" for g in error_collection])
            return await generic.send(f"Attempted to reload all extensions.\nThe following failed:\n\n{output}",
                                      ctx.channel)
        await generic.send("Successfully reloaded all extensions", ctx.channel)
        logs.log("changes", f"{time.time()} > Successfully reloaded all extensions")

    @commands.command(name="reloadutil", aliases=["ru"])
    @commands.check(permissions.is_owner)
    async def reload_utils(self, ctx: commands.Context, name: str):
        """ Reloads a utility module. """
        out = reload_util(name)
        return await generic.send(out, ctx.channel)

    @commands.command(name="reloadlang", aliases=["rl"])
    @commands.check(permissions.is_owner)
    async def reload_locale(self, ctx: commands.Context, name: str):
        """ Reloads a locale file. """
        out = reload_locale(name)
        return await generic.send(out, ctx.channel)

    @commands.command(name="load", aliases=["l"])
    @commands.check(permissions.is_owner)
    async def load(self, ctx: commands.Context, name: str):
        """ Loads an extension. """
        try:
            self.bot.load_extension(f"cogs.{name}")
        except Exception as e:
            return await generic.send(f"{type(e).__name__}: {e}", ctx.channel)
        reloaded = f"Loaded extension **{name}.py**"
        await generic.send(reloaded, ctx.channel)
        if generic.get_config()["logs"]:
            logs.log("changes", f"{time.time()} > {reloaded}")

    @commands.command(name="unload", aliases=["ul"])
    @commands.check(permissions.is_owner)
    async def unload(self, ctx: commands.Context, name: str):
        """ Unloads an extension. """
        try:
            self.bot.unload_extension(f"cogs.{name}")
        except Exception as e:
            return await generic.send(f"{type(e).__name__}: {e}", ctx.channel)
        reloaded = f"Unloaded extension **{name}.py**"
        await generic.send(reloaded, ctx.channel)
        if generic.get_config()["logs"]:
            logs.log("changes", f"{time.time()} > {reloaded}")

    @commands.command(name="shutdown")
    @commands.check(permissions.is_owner)
    async def shutdown(self, ctx: commands.Context):
        """ Shut down the bot """
        import time as _time
        import sys
        await generic.send("Shutting down...", ctx.channel)
        if generic.get_config()["logs"]:
            logs.log("uptime", f"{time.time()} > Shutting down from command...")
        _time.sleep(1)
        sys.stderr.close()
        sys.exit(0)

    @commands.command(name="execute", aliases=["exec"])
    @commands.check(permissions.is_owner)
    async def execute(self, ctx: commands.Context, *, text: str):
        """ Do a shell command. """
        message = await generic.send("Loading...", ctx.channel)
        proc = await asyncio.create_subprocess_shell(text, stdin=None, stderr=PIPE, stdout=PIPE)
        out = (await proc.stdout.read()).decode('utf-8').strip()
        err = (await proc.stderr.read()).decode('utf-8').strip()

        if not out and not err:
            await message.delete()
            return await ctx.message.add_reaction('👌')

        content = ""

        if err:
            content += f"Error:\r\n{err}\r\n{'-' * 30}\r\n"
        if out:
            content += out

        if len(content) > 1500:
            try:
                data = BytesIO(content.encode('utf-8'))
                await message.delete()
                await generic.send("The result was a bit too long.. so here is a text file instead 👍", ctx.channel,
                                   file=discord.File(data, filename=time.file_ts('Execute')))
            except asyncio.TimeoutError as e:
                await message.delete()
                return await generic.send(str(e), ctx.channel)
        else:
            await message.edit(content=f"```fix\n{content}\n```")

    @commands.command(name="online", aliases=["on"])
    @commands.check(permissions.is_owner)
    async def online(self, ctx: commands.Context):
        """ Server is online """
        return await status(ctx, 1)

    @commands.command(name="offline", aliases=["off"])
    @commands.check(permissions.is_owner)
    async def offline(self, ctx: commands.Context):
        """ Server is offline """
        return await status(ctx, 0)

    @commands.command(name="restart", aliases=["re"])
    @commands.check(permissions.is_owner)
    async def restart(self, ctx: commands.Context):
        """ Restart incoming """
        return await status(ctx, 2)

    @commands.command(name="tables", aliases=["create", "recreate"])
    @commands.is_owner()
    async def recreate_tables(self, ctx: commands.Context):
        """ Recreate all tables """
        module_name = importlib.import_module(f"utils.database")
        importlib.reload(module_name)
        val = database.creation()
        send = "Task succeeded successfully - Tables created." if val else "Task failed successfully - Great, more time to waste on trying to fix that!"
        return await generic.send(send, ctx.channel)

    def get_user(self, uid: int) -> str:
        try:
            return str([user for user in self.bot.users if user.id == uid][0])
        except IndexError:
            return "None"

    def get_val(self, what: list) -> str:
        val = "\n".join([" - ".join([f"<@{u}>", self.get_user(u)]) for u in what])
        return val if val else "No data available... yet"

    @commands.group(name="infidels", aliases=["il", "heretics"])
    @commands.check(permissions.is_owner)
    async def infidel_list(self, ctx: commands.Context):
        """ The infidel list """
        if ctx.invoked_subcommand is None:
            if ctx.channel.id in generic.channel_locks:
                return await generic.send(generic.gls("en", "channel_locked"), ctx.channel)
            embed = discord.Embed(colour=generic.random_colour())
            embed.title = "The Infidel List for Suager"
            embed.timestamp = time.now()
            sn = ("Stage 1", "Stage 2", "Stage 3", "Stage 4 - Bad Lock", "Stage 5 - Love Lock I", "Stage 6 - Love Lock II", "Stage 7 - Senko Lair Ban")
            stages = (generic.stage_1, generic.stage_2, generic.stage_3, generic.stage_4, generic.stage_5, generic.stage_6, generic.stage_7)
            for i in range(len(stages)):
                embed.add_field(name=sn[i], value=self.get_val(stages[i]), inline=False)
            lev = ""
            le = generic.love_exceptions
            for lock in le:
                for exc in le[str(lock)]:
                    lev += f"<@{exc}> - {self.get_user(exc)} for {self.get_user(int(lock))}\n"
            if lev == "":
                lev = "No data available... yet"
            embed.add_field(name="Love Exceptions", value=lev, inline=True)
            return await generic.send(None, ctx.channel, embed=embed)

    @infidel_list.command(name="up")
    @commands.check(permissions.is_owner)
    async def infidel_up(self, ctx: commands.Context, user: discord.User):
        """ Move someone up the Infidel List """
        output = generic.infidel_up(user.id)
        if output == -1:
            return await generic.send("Something went wrong...", ctx.channel)
        elif output == -2:
            return await generic.send(f"{user} is already not on the List", ctx.channel)
        elif output == 0:
            return await generic.send(f"{user} is already no longer on the List", ctx.channel)
        else:
            reload = reload_util("generic")
            return await generic.send(f"{user} is now a Stage {output} Infidel\n{reload}", ctx.channel)

    @infidel_list.command(name="down")
    @commands.check(permissions.is_owner)
    async def infidel_down(self, ctx: commands.Context, user: discord.User):
        """ Move someone down the Infidel List """
        output = generic.infidel_down(user.id)
        if output == -1:
            return await generic.send("Something went wrong...", ctx.channel)
        elif output == 8:
            return await generic.send(f"{user} is already at Stage 7", ctx.channel)
        else:
            reload = reload_util("generic")
            return await generic.send(f"{user} is now a Stage {output} Infidel\n{reload}", ctx.channel)

    @infidel_list.command(name="set", aliases=["specific"])
    @commands.check(permissions.is_owner)
    async def infidel_set(self, ctx: commands.Context, action: str, stage: int, user: discord.User):
        """ Set someone to a specific Stage """
        try:
            data_io.change_infidels(stage, action, user.id)
        except Exception as e:
            return await generic.send(f"{type(e).__name__}: {str(e)}", ctx.channel)
        reload = reload_util("generic")
        w1 = "Added" if action == "add" else "Removed"
        w2 = "to" if action == "add" else "from"
        return await generic.send(f"{w1} {user} {w2} Stage {stage} Infidel List\nReload status: {reload}", ctx.channel)

    @commands.command(name="lv2l", aliases=["infidels2", "il2"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def lv2_list(self, ctx: commands.Context):
        """ Imagine being level -2 """
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls("en", "channel_locked"), ctx.channel)
        res = self.db.fetch("SELECT * FROM leveling WHERE level=-2")
        embed = discord.Embed(colour=generic.random_colour())
        embed.title = "People who managed to get level -2"
        desc = ""
        for user in res:
            desc += f"<@{user['uid']}> - {user['name']}#{user['disc']:04d} - in {self.bot.get_guild(user['gid'])}\n"
        embed.description = desc
        return await generic.send(None, ctx.channel, embed=embed)

    @commands.group(name="config")
    @commands.check(permissions.is_owner)
    async def config(self, ctx: commands.Context):
        """ Change bot's configs """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @config.command(name="fullversion", aliases=["fversion", "version", "fv", "v"])
    @commands.check(permissions.is_owner)
    async def change_full_version(self, ctx: commands.Context, new_version: str):
        """ Change version (full) """
        try:
            old_version = self.config["full_version"]
            data_io.change_version("full_version", new_version)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)
        try:
            for cog in self.admin_mod:
                self.bot.reload_extension(cog)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)
        to_send = f"Changed full version from **{old_version}** to **{new_version}**"
        if generic.get_config()["logs"]:
            logs.log("version_changes", f"{time.time()} > {to_send}")
        return await generic.send(to_send, ctx.channel)

    @config.command(name="shortversion", aliases=["sversion", "sv"])
    @commands.check(permissions.is_owner)
    async def change_short_version(self, ctx: commands.Context, new_version: str):
        """ Change version (short) """
        try:
            old_version = self.config["version"]
            data_io.change_version("version", new_version)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)
        try:
            for cog in self.admin_mod:
                self.bot.reload_extension(cog)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)
        to_send = f"Changed short version from **{old_version}** to **{new_version}**"
        if generic.get_config()["logs"]:
            logs.log("version_changes", f"{time.time()} > {to_send}")
        return await generic.send(to_send, ctx.channel)

    @config.command(name="loveexceptions", aliases=["le"])
    @commands.check(permissions.is_owner)
    async def config_love_exceptions(self, ctx: commands.Context, action: str, uid: int, lid: int):
        """ Update the love exceptions list
        uid = exception, lid = locked user """
        try:
            data_io.change_locks("love_exceptions", str(lid), action, uid)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)
        reload = reload_util("generic")
        w1 = "added" if action == "add" else "removed"
        w2 = "to" if action == "add" else "from"
        return await generic.send(f"{emotes.Allow} Successfully {w1} <@{uid}> ({self.bot.get_user(uid)}) {w2} the Love Exceptions List of <@{lid}>\n"
                                  f"Reload status: {reload}", ctx.channel)

    @config.command(name="channellocks", aliases=["cl"])
    @commands.check(permissions.is_owner)
    async def config_channel_locks(self, ctx: commands.Context, action: str, cid: int):
        """ Update the channel locks list (tell to use bot commands) """
        try:
            data_io.change_locks("channel_locks", None, action, cid)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)
        reload = reload_util("generic")
        w1 = "added" if action == "add" else "removed"
        w2 = "to" if action == "add" else "from"
        return await generic.send(f"{emotes.Allow} Successfully {w1} <#{cid}> ({self.bot.get_channel(cid)}) {w2} the Channel Locks List\n"
                                  f"Reload status: {reload}", ctx.channel)

    @config.command(name="serverlocks", aliases=["sl"])
    @commands.check(permissions.is_owner)
    async def config_server_locks(self, ctx: commands.Context, action: str, gid: int, command: str):
        """ Update the server command locks list (disable commands) """
        try:
            data_io.change_locks("server_locks", str(gid), action, command)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)
        reload = reload_util("generic")
        w1 = "added" if action == "add" else "removed"
        w2 = "to" if action == "add" else "from"
        return await generic.send(f"{emotes.Allow} Successfully {w1} `{command}` {w2} the Server Locks List for {self.bot.get_guild(gid)}\n"
                                  f"Reload status: {reload}", ctx.channel)

    @config.command(name="counterlocks", aliases=["cl2", "nl"])
    @commands.check(permissions.is_owner)
    async def config_counter_locks(self, ctx: commands.Context, action: str, gid: int):
        """ Update the counter locks list """
        try:
            data_io.change_locks("counter_locks", None, action, gid)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)
        reload = reload_util("generic")
        w1 = "added" if action == "add" else "removed"
        w2 = "to" if action == "add" else "from"
        return await generic.send(f"{emotes.Allow} Successfully {w1} {self.bot.get_guild(gid)} {w2} the Counter Locks List\n"
                                  f"Reload status: {reload}", ctx.channel)

    @commands.command(name="lv2", aliases=["lv-2"])
    @commands.check(permissions.is_owner)
    async def lv2(self, ctx: commands.Context, user: discord.User, guild: discord.Guild = None):
        """ Set someone to level -2 """
        guild = guild or ctx.guild
        ret = self.db.execute("UPDATE leveling SET level=-2 WHERE uid=? AND gid=?", (user.id, guild.id))
        return await generic.send(ret, ctx.channel)

    @commands.command(name="lv0")
    @commands.check(permissions.is_owner)
    async def lv0(self, ctx: commands.Context, user: discord.User, guild: discord.Guild = None):
        """ Restore someone's levels """
        guild = guild or ctx.guild
        ret = self.db.execute("UPDATE leveling SET level=0 WHERE uid=? AND gid=?", (user.id, guild.id))
        return await generic.send(ret, ctx.channel)

    @commands.group()
    @commands.check(permissions.is_owner)
    async def change(self, ctx: commands.Context):
        """ Change bot's data """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @change.command(name="playing")
    @commands.check(permissions.is_owner)
    async def change_playing(self, ctx: commands.Context, *, playing: str):
        """ Change playing status. """
        try:
            await self.bot.change_presence(activity=discord.Game(name=playing), status=discord.Status.dnd)
            data_io.change_value("config.json", "playing", playing)
            return await generic.send(f"Successfully changed playing status to **{playing}**", ctx.channel)
        except discord.InvalidArgument as err:
            return await generic.send(str(err), ctx.channel)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)

    @change.command(name="username")
    @commands.check(permissions.is_owner)
    async def change_username(self, ctx: commands.Context, *, name: str):
        """ Change username. """
        try:
            await self.bot.user.edit(username=name)
            return await generic.send(f"Successfully changed username to **{name}**", ctx.channel)
        except discord.HTTPException as err:
            return await generic.send(str(err), ctx.channel)

    @change.command(name="nickname")
    @commands.check(permissions.is_owner)
    async def change_nickname(self, ctx: commands.Context, *, name: str = None):
        """ Change nickname. """
        try:
            await ctx.guild.me.edit(nick=name)
            if name:
                return await generic.send(f"Successfully changed nickname to **{name}**", ctx.channel)
            else:
                return await generic.send("Successfully removed nickname", ctx.channel)
        except Exception as err:
            return await generic.send(str(err), ctx.channel)

    @change.command(name="avatar")
    @commands.check(permissions.is_owner)
    async def change_avatar(self, ctx: commands.Context, url: str = None):
        """ Change avatar. """
        if url is None and len(ctx.message.attachments) == 1:
            url = ctx.message.attachments[0].url
        else:
            url = url.strip('<>') if url else None
        try:
            bio = await http.get(url, res_method="read")
            await self.bot.user.edit(avatar=bio)
            return await generic.send(f"Successfully changed the avatar. Currently using:\n{url}", ctx.channel)
        except aiohttp.InvalidURL:
            return await generic.send("The URL is invalid...", ctx.channel)
        except discord.InvalidArgument:
            return await generic.send("This URL does not contain a useable image", ctx.channel)
        except discord.HTTPException as err:
            return await generic.send(str(err), ctx.channel)
        except TypeError:
            return await generic.send("You need to either provide an image URL or upload one with the command", ctx.channel)


async def status(ctx: commands.Context, _type: int):
    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass
    updates = ["Server is offline", "Server is online", "Restart incoming"]
    update = updates[_type]
    now = time.time()
    return await generic.send(f"{now} > **{update}**", ctx.channel)


def setup(bot):
    bot.add_cog(Admin(bot))
