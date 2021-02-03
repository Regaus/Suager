import ast
import asyncio
import importlib
import json
import os
import re
from asyncio.subprocess import PIPE
from io import BytesIO

import aiohttp
import discord
from discord.ext import commands

from core.utils import database, general, time, logger, permissions, data_io, http
from languages import langs


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
        cmd = "\n".join(f"    {i}" for i in cmd.splitlines())
        body = f"async def {fn_name}():\n{cmd}"
        parsed = ast.parse(body)
        body = parsed.body[0].body
        insert_returns(body)
        env = {'bot': ctx.bot, 'discord': discord, 'commands': commands, 'ctx': ctx, 'db': ctx.bot.db, '__import__': __import__}
        exec(compile(parsed, filename="<ast>", mode="exec"), env)
        result = (await eval(f"{fn_name}()", env))
        if ctx.guild is None:
            limit = 8000000
        else:
            limit = int(ctx.guild.filesize_limit / 1.05)
        if len(str(result)) == 0 or result is None:
            return await general.send("Code has completed. No result was returned.", ctx.channel)
        elif len(str(result)) in range(2001, limit + 1):
            async with ctx.typing():
                data = BytesIO(str(result).encode('utf-8'))
                return await general.send(f"Result was a bit too long... ({len(str(result)):,} chars)", ctx.channel,
                                          file=discord.File(data, filename=f"{time.file_ts('Eval')}"))
        elif len(str(result)) > limit:
            async with ctx.typing():
                data = BytesIO(str(result)[-limit:].encode('utf-8'))
                return await general.send(f"Result was a bit too long... ({len(str(result)):,} chars)\nSending last {limit:,} chars", ctx.channel,
                                          file=discord.File(data, filename=f"{time.file_ts('Eval')}"))
        else:
            return await general.send(str(result), ctx.channel)
    except Exception as e:
        return await general.send(f"{type(e).__name__}: {e}", ctx.channel)


def reload_util(base: str, name: str, bot):
    return reload_module_base(base, "utils", name, bot)


def reload_langs(bot):
    name_maker = f"**languages/langs.py**"
    module_name = "languages.langs"
    return reload_module(name_maker, module_name, bot)


def reload_module_base(base: str, folder: str, name: str, bot):
    name_maker = f"**{base}/{folder}/{name}.py**"
    module_name = f"{base}.{folder}.{name}"
    return reload_module(name_maker, module_name, bot)


def reload_module(human_name: str, module_name: str, bot):
    try:
        module = importlib.import_module(module_name)
        importlib.reload(module)
    except ModuleNotFoundError:
        return f"Could not find module named {human_name}"
    except Exception as e:
        error = general.traceback_maker(e)
        return f"Module {human_name} returned an error and was not reloaded...\n{error}"
    reloaded = f"Reloaded module {human_name}"
    if bot.local_config["logs"]:
        logger.log(bot.name, "changes", f"{time.time()} > {bot.local_config['name']} > {reloaded}")
    return reloaded


def reload_extension(bot, base: str, name: str):
    try:
        bot.reload_extension(f"{base}.cogs.{name}")
    except Exception as e:
        return f"{type(e).__name__}: {e}"
    reloaded = f"Reloaded extension **{base}/cogs/{name}.py**"
    lc = general.get_config()["bots"][bot.index]
    if lc["logs"]:
        logger.log(bot.name, "changes", f"{time.time()} > {lc['name']} > {reloaded}")
    return reloaded


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = general.get_config()

    @commands.command(name="db")
    @commands.check(permissions.is_owner)
    async def db_command(self, ctx: commands.Context, *, query: str):
        """ Database query """
        try:
            data = self.bot.db.execute(query)
            return await general.send(data, ctx.channel)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name="fetch", aliases=["select"])
    @commands.check(permissions.is_owner)
    async def db_fetch(self, ctx: commands.Context, *, query: str):
        """ Fetch data from db """
        try:
            data = self.bot.db.fetch("SELECT " + query)
            result = f"{data}"
            if ctx.guild is None:
                limit = 8000000
            else:
                limit = int(ctx.guild.filesize_limit / 1.05)
            # return await ctx.send(result)
            rl = len(str(result))
            if rl == 0 or result is None:
                return await general.send("No result was returned.", ctx.channel)
            elif rl in range(2001, limit + 1):
                async with ctx.typing():
                    data = BytesIO(str(result).encode('utf-8'))
                    return await general.send(f"Result was a bit too long... ({rl:,} chars)", ctx.channel,
                                              file=discord.File(data, filename=f"{time.file_ts('Fetch')}"))
            elif rl > limit:
                async with ctx.typing():
                    data = BytesIO(str(result)[-limit:].encode('utf-8'))
                    return await general.send(f"Result was a bit too long... ({rl:,} chars)\nSending last {limit:,} chars", ctx.channel,
                                              file=discord.File(data, filename=f"{time.file_ts('Fetch')}"))
            else:
                return await general.send(str(result), ctx.channel)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.group(name="log", aliases=["logs"], invoke_without_command=True)
    @commands.check(permissions.is_owner)
    async def log(self, ctx: commands.Context, log: str, *, search: str = None):
        """ Get logs """
        try:
            data = ""
            for path, _, __ in os.walk(f"data/logs/{self.bot.name}"):
                if re.compile(r"(\d{4})-(\d{2})-(\d{2})").search(path):
                    filename = os.path.join(path, f"{log}.rsf")
                    # _path = path.replace("\\", "/")
                    # filename = f"{_path}/{log}.rsf"
                    try:
                        file = open(filename, "r", encoding="utf-8")
                    except FileNotFoundError:
                        # await general.send(f"File `{filename}` not found.", ctx.channel)
                        continue
                    if search is None:
                        try:
                            result = file.read()
                            data += f"{result}"  # Put a newline in the end, just in case
                        except UnicodeDecodeError as e:
                            await general.send(f"`{filename}`: Encoding broke - `{e}`", ctx.channel)
                    else:
                        try:
                            stuff = file.readlines()
                            result = ""
                            for line in stuff:
                                if search in line:
                                    result += line
                            data += f"{result}"
                        except UnicodeDecodeError as e:
                            await general.send(f"`{filename}`: Encoding broke - `{e}`", ctx.channel)
            if ctx.guild is None:
                limit = 8000000
            else:
                limit = int(ctx.guild.filesize_limit / 1.05)
            rl = len(str(data))
            if rl == 0 or data is None:
                return await general.send("Nothing was found...", ctx.channel)
            elif 0 < rl <= limit:
                async with ctx.typing():
                    _data = BytesIO(str(data).encode('utf-8'))
                    lines = len(str(data).splitlines())
                    return await general.send(f"Results for {log}.rsf - search term `{search}` - {lines:,} lines, {rl:,} chars", ctx.channel,
                                              file=discord.File(_data, filename=f"{time.file_ts('Logs')}"))
            elif rl > limit:
                async with ctx.typing():
                    _data = BytesIO(str(data)[-limit:].encode('utf-8'))
                    return await general.send(f"Result was a bit too long... ({rl:,} chars) - search term `{search}`\nSending latest", ctx.channel,
                                              file=discord.File(_data, filename=f"{time.file_ts('Logs')}"))
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @log.command(name="date")
    @commands.check(permissions.is_owner)
    async def log_date(self, ctx: commands.Context, date: str, log_file: str, *, search: str = None):
        """ Get logs """
        try:
            filename = f"data/logs/{self.bot.name}/{date}/{log_file}.rsf"
            file = open(filename, "r", encoding="utf-8")
            if search is None:
                result = file.read()
                data = f"{result}"  # Put a newline in the end, just in case
            else:
                stuff = file.readlines()
                result = ""
                for line in stuff:
                    if search in line:
                        result += line
                data = f"{result}"
            if ctx.guild is None:
                limit = 8000000
            else:
                limit = int(ctx.guild.filesize_limit / 1.05)
            rl = len(str(data))
            if rl == 0 or data is None:
                return await general.send("Nothing was found...", ctx.channel)
            elif 0 < rl <= limit:
                async with ctx.typing():
                    _data = BytesIO(str(data).encode('utf-8'))
                    lines = len(str(data).splitlines())
                    return await general.send(f"Results for {log_file}.rsf - search term `{search}` - {lines:,} lines, {rl:,} chars", ctx.channel,
                                              file=discord.File(_data, filename=f"{time.file_ts('Logs')}"))
            elif rl > limit:
                async with ctx.typing():
                    _data = BytesIO(str(data)[-limit:].encode('utf-8'))
                    return await general.send(f"Result was a bit too long... ({rl:,} chars) - search term `{search}`\nSending latest", ctx.channel,
                                              file=discord.File(_data, filename=f"{time.file_ts('Logs')}"))
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)

    @commands.command(name='eval')
    @commands.check(permissions.is_owner)
    async def eval_cmd(self, ctx: commands.Context, *, cmd):
        """ Evaluates input. """
        return await eval_(ctx, cmd)

    @commands.command(name="reload", aliases=["re", "r"])
    @commands.check(permissions.is_owner)
    async def reload(self, ctx: commands.Context, name: str):
        """ Reloads an extension. """
        out = reload_extension(self.bot, self.bot.name, name)
        return await general.send(out, ctx.channel)

    @commands.command(name="reloadcore", aliases=["rc"])
    @commands.check(permissions.is_owner)
    async def reload_core(self, ctx: commands.Context, name: str):
        """ Reloads a core extension. """
        out = reload_extension(self.bot, "core", name)
        return await general.send(out, ctx.channel)

    @commands.command(name="reloadshared", aliases=["rs"])
    @commands.check(permissions.is_owner)
    async def reload_shared(self, ctx: commands.Context, name: str = None):
        """ Reload shared cogs """
        shared = []
        for _name, _cogs in self.bot.local_config["shared"].items():
            for _cog in _cogs:
                shared.append([_name, _cog])
        if name is not None:
            for base, cog in shared:
                if name in cog:
                    out = reload_extension(self.bot, base, cog)
                    return await general.send(out, ctx.channel)
            return await general.send(f"Looks like nothing was found for {name}...", ctx.channel)
        else:
            error_collection = []
            for base, cog in shared:
                try:
                    self.bot.reload_extension(f"{base}.cogs.{cog}")
                except Exception as e:
                    error_collection.append([f"{base}/cogs/{cog}", f"{type(e).__name__}: {e}"])
            if error_collection:
                output = "\n".join([f"**{error[0]}** - `{error[1]}`" for error in error_collection])
                logger.log(self.bot.name, "changes", f"{time.time()} > {self.bot.local_config['name']} > Unsuccessfully reloaded all shared extensions")
                return await general.send(f"Attempted to reload all shared extensions.\nThe following failed:\n\n{output}", ctx.channel)
            return await general.send("Successfully reloaded all shared extensions", ctx.channel)

    @commands.command(name="reloadall", aliases=["rall", "ra"])
    @commands.check(permissions.is_owner)
    async def reload_all(self, ctx: commands.Context):
        """ Reloads all extensions. """
        error_collection = []
        try:
            for file in os.listdir(os.path.join(self.bot.name, "cogs")):
                if file.endswith(".py"):
                    name = file[:-3]
                    try:
                        self.bot.reload_extension(f"{self.bot.name}.cogs.{name}")
                    except Exception as e:
                        error_collection.append([file, f"{type(e).__name__}: {e}"])
        except FileNotFoundError:
            pass
        for file in os.listdir(os.path.join("core", "cogs")):
            if file.endswith(".py"):
                name = file[:-3]
                if name not in self.bot.local_config["exclude_core_cogs"]:
                    try:
                        self.bot.reload_extension(f"core.cogs.{name}")
                    except Exception as e:
                        error_collection.append([file, f"{type(e).__name__}: {e}"])
        if error_collection:
            output = "\n".join([f"**{error[0]}** - `{error[1]}`" for error in error_collection])
            logger.log(self.bot.name, "changes", f"{time.time()} > {self.bot.local_config['name']} > Unsuccessfully reloaded all extensions")
            return await general.send(f"Attempted to reload all extensions.\nThe following failed:\n\n{output}", ctx.channel)
        logger.log(self.bot.name, "changes", f"{time.time()} > {self.bot.local_config['name']} > Successfully reloaded all extensions")
        return await general.send("Successfully reloaded all extensions", ctx.channel)

    @commands.command(name="reloadutil", aliases=["ru"])
    @commands.check(permissions.is_owner)
    async def reload_utils(self, ctx: commands.Context, name: str):
        """ Reloads a utility module. """
        out = reload_util(self.bot.name, name, self.bot)
        return await general.send(out, ctx.channel)

    @commands.command(name="reloadcoreutil", aliases=["rcu"])
    @commands.check(permissions.is_owner)
    async def reload_core_util(self, ctx: commands.Context, name: str):
        """ Reloads a core utility module. """
        out = reload_util("core", name, self.bot)
        return await general.send(out, ctx.channel)

    @commands.command(name="reloadlangs", aliases=["rl"])
    @commands.check(permissions.is_owner)
    async def reload_lang(self, ctx: commands.Context):
        """ Reloads langs.py """
        out = reload_langs(self.bot)
        return await general.send(out, ctx.channel)

    async def load_ext(self, ctx, name1: str, name2: str):
        try:
            self.bot.load_extension(f"{name1}.cogs.{name2}")
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)
        reloaded = f"Loaded extension **{name1}/cogs/{name2}.py**"
        await general.send(reloaded, ctx.channel)
        if self.bot.local_config["logs"]:
            logger.log(self.bot.name, "changes", f"{time.time()} > {self.bot.local_config['name']} > {reloaded}")

    async def unload_ext(self, ctx, name1: str, name2: str):
        try:
            self.bot.unload_extension(f"{name1}.cogs.{name2}")
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)
        reloaded = f"Unloaded extension **{name1}/cogs/{name2}.py**"
        await general.send(reloaded, ctx.channel)
        if self.bot.local_config["logs"]:
            logger.log(self.bot.name, "changes", f"{time.time()} > {self.bot.local_config['name']} > {reloaded}")

    @commands.command(name="load", aliases=["l"])
    @commands.check(permissions.is_owner)
    async def load(self, ctx: commands.Context, name: str):
        """ Loads an extension. """
        return await self.load_ext(ctx, self.bot.name, name)

    @commands.command(name="loadcore", aliases=["lc"])
    @commands.check(permissions.is_owner)
    async def load_core(self, ctx: commands.Context, name: str):
        """ Loads a core extension. """
        return await self.load_ext(ctx, "core", name)

    @commands.command(name="unload", aliases=["ul"])
    @commands.check(permissions.is_owner)
    async def unload(self, ctx: commands.Context, name: str):
        """ Unloads an extension. """
        return await self.unload_ext(ctx, self.bot.name, name)

    @commands.command(name="unloadcore", aliases=["ulc"])
    @commands.check(permissions.is_owner)
    async def unload_core(self, ctx: commands.Context, name: str):
        """ Unloads a core extension. """
        return await self.unload_ext(ctx, "core", name)

    def reload_config(self):
        config = general.get_config()
        self.bot.config = config
        self.bot.local_config = config["bots"][self.bot.index]
        reloaded = "Reloaded config.json"
        if self.bot.local_config["logs"]:
            logger.log(self.bot.name, "changes", f"{time.time()} > {self.bot.local_config['name']} > {reloaded}")
        return reloaded

    @commands.command(name="updateconfig", aliases=["uc"])
    @commands.check(permissions.is_owner)
    async def update_config(self, ctx: commands.Context):
        """ Reload config """
        reloaded = self.reload_config()
        return await general.send(reloaded, ctx.channel)

    @commands.command(name="shutdown")
    @commands.check(permissions.is_owner)
    async def shutdown(self, ctx: commands.Context):
        """ Shut down the bot """
        import time as _time
        import sys
        await general.send("Shutting down...", ctx.channel)
        if self.bot.local_config["logs"]:
            logger.log(self.bot.name, "uptime", f"{time.time()} > {self.bot.local_config['name']} > Shutting down from command...")
        _time.sleep(1)
        sys.stderr.close()
        sys.exit(0)

    @commands.command(name="execute", aliases=["exec"])
    @commands.check(permissions.is_owner)
    async def execute(self, ctx: commands.Context, *, text: str):
        """ Do a shell command. """
        message = await general.send("Loading...", ctx.channel)
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
                await general.send("The result was a bit too long.. so here is a text file instead 👍", ctx.channel,
                                   file=discord.File(data, filename=time.file_ts('Execute')))
            except asyncio.TimeoutError as e:
                await message.delete()
                return await general.send(str(e), ctx.channel)
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

    @commands.command(name="restart", aliases=["res"])
    @commands.check(permissions.is_owner)
    async def restart(self, ctx: commands.Context):
        """ Restart incoming """
        return await status(ctx, 2)

    @commands.command(name="tables")
    @commands.is_owner()
    async def recreate_tables(self, ctx: commands.Context):
        """ Recreate all tables """
        module_name = importlib.import_module(f"core.utils.database")
        importlib.reload(module_name)
        database.creation()
        return await general.send("Tables recreated...", ctx.channel)

    @commands.command(name="version", aliases=["fversion", "fullversion", "fv", "v"])
    @commands.check(permissions.is_owner)
    async def change_full_version(self, ctx: commands.Context, new_version: str):
        """ Change version (full) """
        try:
            # old_version = self.bot.local_config["version"]
            old_version = general.get_version()[self.bot.name]["version"]
            data_io.change_version("version", new_version, self.bot.name)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)
        self.reload_config()
        to_send = f"Changed full version from **{old_version}** to **{new_version}**"
        if self.bot.local_config["logs"]:
            logger.log(self.bot.name, "version_changes", f"{time.time()} > {self.bot.local_config['name']} > {to_send}")
        return await general.send(to_send, ctx.channel)

    @commands.command(name="sversion", aliases=["shortversion", "sv"])
    @commands.check(permissions.is_owner)
    async def change_short_version(self, ctx: commands.Context, new_version: str):
        """ Change version (short) """
        try:
            # old_version = self.bot.local_config["short_version"]
            old_version = general.get_version()[self.bot.name]["short_version"]
            data_io.change_version("short_version", new_version, self.bot.name)
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)
        self.reload_config()
        to_send = f"Changed short version from **{old_version}** to **{new_version}**"
        if self.bot.local_config["logs"]:
            logger.log(self.bot.name, "version_changes", f"{time.time()} > {self.bot.local_config['name']} > {to_send}")
        return await general.send(to_send, ctx.channel)

    @commands.group()
    @commands.check(permissions.is_owner)
    async def change(self, ctx: commands.Context):
        """ Change bot's data """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @change.command(name="username")
    @commands.check(permissions.is_owner)
    async def change_username(self, ctx: commands.Context, *, name: str):
        """ Change username. """
        try:
            await self.bot.user.edit(username=name)
            return await general.send(f"Successfully changed username to **{name}**", ctx.channel)
        except discord.HTTPException as err:
            return await general.send(str(err), ctx.channel)

    @change.command(name="nickname")
    @commands.check(permissions.is_owner)
    async def change_nickname(self, ctx: commands.Context, *, name: str = None):
        """ Change nickname. """
        try:
            await ctx.guild.me.edit(nick=name)
            if name:
                return await general.send(f"Successfully changed nickname to **{name}**", ctx.channel)
            else:
                return await general.send("Successfully removed nickname", ctx.channel)
        except Exception as err:
            return await general.send(str(err), ctx.channel)

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
            return await general.send(f"Successfully changed the avatar. Currently using:\n{url}", ctx.channel)
        except aiohttp.InvalidURL:
            return await general.send("The URL is invalid...", ctx.channel)
        except discord.InvalidArgument:
            return await general.send("This URL does not contain a usable image", ctx.channel)
        except discord.HTTPException as err:
            return await general.send(str(err), ctx.channel)
        except TypeError:
            return await general.send("You need to either provide an image URL or upload one with the command", ctx.channel)

    @commands.command(name="gls")
    @commands.check(permissions.is_owner)
    async def get_lang_string(self, ctx: commands.Context, string: str, locale: str = "en_gb"):
        """ Test a string """
        return await general.send(langs.languages.get(locale, langs.languages["en_gb"]).get(string, f"String not found: {string}"), ctx.channel)

    @commands.command(name="blacklist")
    @commands.check(permissions.is_owner)
    async def blacklist_add(self, ctx: commands.Context, user: discord.User):
        """ Blacklist a user from using the bot """
        blacklist = json.loads(open("blacklist.json", "r").read())
        blacklist.append(user.id)
        self.bot.blacklist = blacklist
        open("blacklist.json", "w+").write(json.dumps(blacklist))
        return await general.send(f"Added {user.id} ({user}) to the Blacklist", ctx.channel)

    @commands.command(name="whitelist")
    @commands.check(permissions.is_owner)
    async def blacklist_remove(self, ctx: commands.Context, user: discord.User):
        """ Remove a user from the blacklist """
        blacklist = json.loads(open("blacklist.json", "r").read())
        try:
            blacklist.remove(user.id)
            self.bot.blacklist = blacklist
            open("blacklist.json", "w+").write(json.dumps(blacklist))
            return await general.send(f"Removed {user.id} ({user}) from the Blacklist", ctx.channel)
        except ValueError:
            return await general.send(f"User {user.id} was not found in the Blacklist", ctx.channel)

    @commands.command(name="usage", aliases=["usages"])
    @commands.check(permissions.is_owner)
    async def usages(self, ctx: commands.Context):
        """ See command usage counters """
        data = sorted([f"`{name}`: {usage}" for name, usage in self.bot.usages.items()])
        send = [data[i:i + 80] for i in range(0, len(data), 80)]
        for result in send:
            await general.send(" | ".join(result), ctx.channel)

    @commands.command(name="seedm")
    @commands.check(permissions.is_owner)
    async def see_dm(self, ctx: commands.Context, user: discord.User):
        """ Check someone's DMs with Suager """
        try:
            data = "\n\n".join([f"{message.author} - {langs.gts(message.created_at, 'en_gb', seconds=True)}\n{message.content}" for message in await
                                (await user.create_dm()).history(limit=None, oldest_first=True).flatten()])
            if ctx.guild is None:
                limit = 8000000
            else:
                limit = int(ctx.guild.filesize_limit / 1.05)
            rl = len(str(data))
            if rl == 0 or not data:
                return await general.send("Nothing was found...", ctx.channel)
            elif 2000 < rl <= limit:
                async with ctx.typing():
                    _data = BytesIO(str(data).encode('utf-8'))
                    lines = len(str(data).splitlines())
                    return await general.send(f"Results for {user} DMs - {lines:,} lines, {rl:,} chars", ctx.channel,
                                              file=discord.File(_data, filename=f"{time.file_ts('Logs')}"))
            elif rl > limit:
                async with ctx.typing():
                    _data = BytesIO(str(data)[-limit:].encode('utf-8'))
                    return await general.send(f"Result was a bit too long... ({rl:,} chars)\nSending latest", ctx.channel,
                                              file=discord.File(_data, filename=f"{time.file_ts('Logs')}"))
        except Exception as e:
            return await general.send(f"{type(e).__name__}: {e}", ctx.channel)


async def status(ctx: commands.Context, _type: int):
    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass
    updates = ["Server is offline", "Server is online", "Restart incoming"]
    update = updates[_type]
    now = time.time()
    return await general.send(f"{now} > **{update}**", ctx.channel)


def setup(bot):
    bot.add_cog(Admin(bot))
