import ast
import asyncio
import importlib
import json
import os
import re
from asyncio.subprocess import PIPE
from contextlib import suppress
from io import BytesIO

import aiohttp
import discord

from utils import bot_data, commands, data_io, database, general, http, logger, time, cpu_burner


def insert_returns(body):
    # insert return statement if the last expression is an expression statement
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


async def eval_fn(ctx: commands.Context, cmd):
    try:
        fn_name = "eval_expr"
        cmd = cmd.strip("` ")
        cmd = "\n".join(f"    {i}" for i in cmd.splitlines())
        body = f"async def {fn_name}():\n{cmd}"
        parsed = ast.parse(body)
        body = parsed.body[0].body  # type: ignore
        insert_returns(body)
        env = {'bot': ctx.bot, 'discord': discord, 'commands': commands, 'ctx': ctx, 'db': ctx.bot.db, 'time': time, '__import__': __import__}
        exec(compile(parsed, filename="<ast>", mode="exec"), env)
        result = (await eval(f"{fn_name}()", env))
        if ctx.guild is None:
            limit = 8000000
        else:
            limit = int(ctx.guild.filesize_limit / 1.05)
        if len(str(result)) == 0 or result is None:
            return await ctx.send("Code has completed. No result was returned.")
        elif 2000 < len(str(result)) <= limit:
            async with ctx.typing():
                data = BytesIO(str(result).encode('utf-8'))
                return await ctx.send(f"Result was a bit too long... ({len(str(result)):,} chars)", file=discord.File(data, filename=f"{time.file_ts('Eval')}"))
        elif len(str(result)) > limit:
            async with ctx.typing():
                data = BytesIO(str(result)[-limit:].encode('utf-8'))
                return await ctx.send(f"Result was a bit too long... ({len(str(result)):,} chars)\nSending last {limit:,} chars",
                                      file=discord.File(data, filename=f"{time.file_ts('Eval')}"))
        else:
            return await ctx.send(str(result))
    except Exception as e:
        tb = general.traceback_maker(e).splitlines()
        # At this point: -3 is the "File <ast>" line, -2 is the exception raised, -1 is the closing ```
        # "  File "<ast>", line x, in eval_expr"
        i, data = 0, None
        for i, line in enumerate(tb):
            if re.match(r'(\s*)File "<ast>", line (\d+), in eval_expr', line):
                data = line.split(", ", 2)  # We split this into three parts: file name, line number, and function name
                break
        if data is not None:
            value = int(data[1][5:])  # Extracts the line number from the line number string
            code_line = cmd.splitlines()[value - 2]  # The `cmd` variable is the code input, while the function itself inserts `async def` first
            if code_line[0] == " ":  # if the block of code starts with a whitespace
                code_start = len(re.match(r"\s*", code_line).group(0))  # Find the first index that is not a whitespace
            else:
                code_start = 0
            code = code_line[code_start:]  # Extract the code without the indentation
            tb.insert(i + 1, "    " + code)  # We insert a line before the exception, which shows the code actually run, indented properly
        else:
            await ctx.send("Error line number not found...")

        traceback = "\n".join(tb)

        if len(traceback) == 0 or traceback is None:
            return await ctx.send("An error has occurred. No traceback is available.")
        elif 2000 < len(traceback) <= 8000000:
            async with ctx.typing():
                data = BytesIO(traceback.encode('utf-8'))
                return await ctx.send(f"An error has occurred. The traceback is a bit too long... ({len(traceback):,} chars)", file=discord.File(data, filename=f"{time.file_ts('Traceback')}"))
        elif len(traceback) > 8000000:
            async with ctx.typing():
                data = BytesIO(traceback[-8000000:].encode('utf-8'))
                return await ctx.send(f"An error has occurred. The traceback is a bit too long... ({len(traceback):,} chars)\nSending last {8000000:,} chars",
                                      file=discord.File(data, filename=f"{time.file_ts('Traceback')}"))
        return await ctx.send(traceback)
        # return await ctx.send("\n".join(tb))


def reload_util(name: str, bot: bot_data.Bot):
    name_maker = f"**utils/{name}.py**"
    module_name = f"utils.{name}"
    return reload_module(name_maker, module_name, bot)


def reload_module(human_name: str, module_name: str, bot: bot_data.Bot):
    try:
        module = importlib.import_module(module_name)
        importlib.reload(module)
    except ModuleNotFoundError:
        return f"Could not find module named {human_name}"
    except Exception as e:
        error = general.traceback_maker(e)
        return f"Module {human_name} returned an error and was not reloaded...\n{error}"
    reloaded = f"Reloaded module {human_name}"
    logger.log(bot.name, "changes", f"{time.time()} > {bot.full_name} > {reloaded}")
    return reloaded


async def reload_extension(bot: bot_data.Bot, name: str):
    try:
        await bot.reload_extension(f"cogs.{name}")
    except Exception as e:
        return f"{type(e).__name__}: {e}"
    reloaded = f"Reloaded extension **cogs/{name}.py**"
    logger.log(bot.name, "changes", f"{time.time()} > {bot.full_name} > {reloaded}")
    return reloaded


def make_valid_sql(data: str) -> str:
    # Replace ' with '' to make valid SQL
    return "'" + data.replace("'", "''") + "'"


class Admin(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        self.config = general.get_config()

    @commands.command(name="db")
    @commands.is_owner()
    async def db_command(self, ctx: commands.Context, *, query: str):
        """ Database query """
        try:
            data = self.bot.db.execute(query)
            return await ctx.send(data)
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")

    @commands.command(name="fetch", aliases=["select"])
    @commands.is_owner()
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
                return await ctx.send("No result was returned.")
            elif rl in range(2001, limit + 1):
                async with ctx.typing():
                    data = BytesIO(str(result).encode('utf-8'))
                    return await ctx.send(f"Result was a bit too long... ({rl:,} chars)", file=discord.File(data, filename=f"{time.file_ts('Fetch')}"))
            elif rl > limit:
                async with ctx.typing():
                    data = BytesIO(str(result)[-limit:].encode('utf-8'))
                    return await ctx.send(f"Result was a bit too long... ({rl:,} chars)\nSending last {limit:,} chars",
                                          file=discord.File(data, filename=f"{time.file_ts('Fetch')}"))
            else:
                return await ctx.send(str(result))
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")

    @commands.group(name="log", aliases=["logs"], invoke_without_command=True)
    @commands.is_owner()
    async def log(self, ctx: commands.Context, log: str, *, search: str = None):
        """ Get logs """
        try:
            data = ""
            for path, dirs, __ in os.walk(f"data/logs/{self.bot.name}"):
                dirs.sort()  # Sort the folder names, this should make them appear alphabetically
                if re.compile(r"(\d{4})-(\d{2})-(\d{2})").search(path):
                    filename = os.path.join(path, f"{log}.rsf")
                    # _path = path.replace("\\", "/")
                    # filename = f"{_path}/{log}.rsf"
                    try:
                        file = open(filename, "r", encoding="utf-8", errors="replace")
                    except FileNotFoundError:
                        # await general.send(f"File `{filename}` not found.", ctx.channel)
                        continue
                    try:
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
                    except UnicodeDecodeError as e:
                        await ctx.send(f"`{filename}`: Encoding broke - `{e}`")
            if ctx.guild is None:
                limit = 8000000
            else:
                limit = int(ctx.guild.filesize_limit / 1.05)
            rl = len(str(data))
            if rl == 0 or data is None:
                return await ctx.send("Nothing was found...")
            elif 0 < rl <= limit:
                async with ctx.typing():
                    _data = BytesIO(str(data).encode('utf-8'))
                    lines = len(str(data).splitlines())
                    return await ctx.send(f"Results for {log}.rsf - search term `{search}` - {lines:,} lines, {rl:,} chars",
                                          file=discord.File(_data, filename=f"{time.file_ts('Logs')}"))
            elif rl > limit:
                async with ctx.typing():
                    _data = BytesIO(str(data)[-limit:].encode('utf-8'))
                    return await ctx.send(f"Result was a bit too long... ({rl:,} chars) - search term `{search}`\nSending latest",
                                          file=discord.File(_data, filename=f"{time.file_ts('Logs')}"))
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")

    @log.command(name="date")
    @commands.is_owner()
    async def log_date(self, ctx: commands.Context, date: str, log_file: str, *, search: str = None):
        """ Get logs """
        try:
            filename = f"data/logs/{self.bot.name}/{date}/{log_file}.rsf"
            file = open(filename, "r", encoding="utf-8", errors="replace")
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
                return await ctx.send("Nothing was found...")
            elif 0 < rl <= limit:
                async with ctx.typing():
                    _data = BytesIO(str(data).encode('utf-8'))
                    lines = len(str(data).splitlines())
                    return await ctx.send(f"Results for {log_file}.rsf - search term `{search}` - {lines:,} lines, {rl:,} chars",
                                          file=discord.File(_data, filename=f"{time.file_ts('Logs')}"))
            elif rl > limit:
                async with ctx.typing():
                    _data = BytesIO(str(data)[-limit:].encode('utf-8'))
                    return await ctx.send(f"Result was a bit too long... ({rl:,} chars) - search term `{search}`\nSending latest",
                                          file=discord.File(_data, filename=f"{time.file_ts('Logs')}"))
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")

    @commands.command(name='eval')
    @commands.is_owner()
    async def eval_cmd(self, ctx: commands.Context, *, cmd):
        """ Evaluates input. """
        return await eval_fn(ctx, cmd)

    @commands.command(name="error")
    @commands.is_owner()
    async def simulate_error(self, ctx: commands.Context):
        """ Simulate an unhandled error """
        raise RuntimeError("This is an example error")

    @commands.command(name="reload", aliases=["re", "r"])
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, name: str):
        """ Reloads an extension. """
        return await ctx.send(await reload_extension(self.bot, name))

    @commands.command(name="reloadall", aliases=["rall", "ra"])
    @commands.is_owner()
    async def reload_all(self, ctx: commands.Context):
        """ Reloads all extensions. """
        error_collection = []
        load = bot_data.load[self.bot.name]
        for name in load:
            try:
                await self.bot.reload_extension(f"cogs.{name}")
            except Exception as e:
                error_collection.append([name, f"{type(e).__name__}: {e}"])
        if error_collection:
            output = "\n".join([f"**{error[0]}** - `{error[1]}`" for error in error_collection])
            logger.log(self.bot.name, "changes", f"{time.time()} > {self.bot.full_name} > Unsuccessfully reloaded all extensions")
            return await ctx.send(f"Attempted to reload all extensions.\nThe following failed:\n\n{output}")
        else:
            logger.log(self.bot.name, "changes", f"{time.time()} > {self.bot.full_name} > Successfully reloaded all extensions")
            return await ctx.send("Successfully reloaded all extensions")

    @commands.command(name="reloadutil", aliases=["ru"])
    @commands.is_owner()
    async def reload_utils(self, ctx: commands.Context, name: str):
        """ Reloads a utility module. """
        return await ctx.send(reload_util(name, self.bot))

    @commands.command(name="reloadregaus", aliases=["rt"])  # `rr` is already taken by reaction roles...
    @commands.is_owner()
    async def reload_time(self, ctx: commands.Context):
        """ Reloads regaus.py """
        return await ctx.send(reload_module(f"**regaus.py**", "regaus", self.bot))

    # @commands.command(name="reloadlangs", aliases=["rl"])
    # @commands.is_owner()
    # async def reload_lang(self, ctx: commands.Context):
    #     """ Reloads languages.py """
    #     out = reload_langs(self.bot)
    #     return await general.send(out, ctx.channel)

    async def load_ext(self, ctx: commands.Context, name2: str):
        try:
            await self.bot.load_extension(f"cogs.{name2}")
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")
        reloaded = f"Loaded extension **cogs/{name2}.py**"
        await ctx.send(reloaded)
        logger.log(self.bot.name, "changes", f"{time.time()} > {self.bot.full_name} > {reloaded}")

    async def unload_ext(self, ctx: commands.Context, name2: str):
        try:
            await self.bot.unload_extension(f"cogs.{name2}")
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")
        reloaded = f"Unloaded extension **cogs/{name2}.py**"
        await ctx.send(reloaded)
        logger.log(self.bot.name, "changes", f"{time.time()} > {self.bot.full_name} > {reloaded}")

    @commands.command(name="load", aliases=["l"])
    @commands.is_owner()
    async def load(self, ctx: commands.Context, name: str):
        """ Loads an extension. """
        return await self.load_ext(ctx, name)

    @commands.command(name="unload", aliases=["ul"])
    @commands.is_owner()
    async def unload(self, ctx: commands.Context, name: str):
        """ Unloads an extension. """
        return await self.unload_ext(ctx, name)

    def reload_config(self):
        config = general.get_config()
        self.bot.config = config
        self.bot.local_config = config["bots"][self.bot.index]
        reloaded = "Reloaded config.json"
        logger.log(self.bot.name, "changes", f"{time.time()} > {self.bot.full_name} > {reloaded}")
        return reloaded

    @commands.command(name="updateconfig", aliases=["reloadconfig", "uc", "rc"])
    @commands.is_owner()
    async def update_config(self, ctx: commands.Context):
        """ Reload config """
        return await ctx.send(self.reload_config())

    @commands.command(name="shutdown")
    @commands.is_owner()
    async def shutdown(self, ctx: commands.Context):
        """ Shut down the bot """
        import time as _time
        import sys
        await ctx.send("Shutting down...")
        logger.log(self.bot.name, "uptime", f"{time.time()} > {self.bot.full_name} > Shutting down...")
        cpu_burner.arr[1] = True
        _time.sleep(1)
        sys.stderr.close()
        sys.exit(0)

    @commands.command(name="execute", aliases=["exec"])
    @commands.is_owner()
    async def execute(self, ctx: commands.Context, *, text: str):
        """ Do a shell command. """
        message = await ctx.send("Loading...")
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
        if len(content) > 1900:
            try:
                data = BytesIO(content.encode('utf-8'))
                await message.edit(content="The result was a bit too long, so here is a text file instead", attachments=[discord.File(data, filename=time.file_ts('Execute'))])
            except asyncio.TimeoutError as e:
                # I have no idea when or why this could occur, but whatever...
                await message.delete()
                return await ctx.send(str(e))
        else:
            await message.edit(content=f"```fix\n{content}\n```")

    @commands.command(name="tables")
    @commands.is_owner()
    async def recreate_tables(self, ctx: commands.Context):
        """ Recreate all tables """
        module_name = importlib.import_module("utils.database")
        importlib.reload(module_name)
        database.creation()
        return await ctx.send("Tables recreated")

    @commands.command(name="version", aliases=["fversion", "fullversion", "fv", "v"])
    @commands.is_owner()
    async def change_full_version(self, ctx: commands.Context, new_version: str):
        """ Change version (full) """
        try:
            # old_version = self.bot.local_config["version"]
            old_version = general.get_version()[self.bot.name]["version"]
            data_io.change_version("version", new_version, self.bot.name)
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")
        self.reload_config()
        to_send = f"Changed full version from **{old_version}** to **{new_version}**"
        logger.log(self.bot.name, "version_changes", f"{time.time()} > {self.bot.full_name} > {to_send}")
        return await ctx.send(to_send)

    @commands.command(name="sversion", aliases=["shortversion", "sv"])
    @commands.is_owner()
    async def change_short_version(self, ctx: commands.Context, new_version: str):
        """ Change version (short) """
        try:
            # old_version = self.bot.local_config["short_version"]
            old_version = general.get_version()[self.bot.name]["short_version"]
            data_io.change_version("short_version", new_version, self.bot.name)
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")
        self.reload_config()
        to_send = f"Changed short version from **{old_version}** to **{new_version}**"
        logger.log(self.bot.name, "version_changes", f"{time.time()} > {self.bot.full_name} > {to_send}")
        return await ctx.send(to_send)

    @commands.group()
    @commands.is_owner()
    async def change(self, ctx: commands.Context):
        """ Change bot's data """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @change.command(name="username")
    @commands.is_owner()
    async def change_username(self, ctx: commands.Context, *, name: str):
        """ Change username. """
        try:
            await self.bot.user.edit(username=name)
            return await ctx.send(f"Successfully changed username to **{name}**")
        except discord.HTTPException as err:
            return await ctx.send(str(err))

    @change.command(name="nickname")
    @commands.is_owner()
    async def change_nickname(self, ctx: commands.Context, *, name: str = None):
        """ Change nickname. """
        try:
            await ctx.guild.me.edit(nick=name)
            if name:
                return await ctx.send(f"Successfully changed nickname to **{name}**")
            else:
                return await ctx.send("Successfully removed nickname")
        except Exception as err:
            return await ctx.send(str(err))

    @change.command(name="avatar")
    @commands.is_owner()
    async def change_avatar(self, ctx: commands.Context, url: str = None):
        """ Change avatar. """
        if url is None and len(ctx.message.attachments) == 1:
            url = ctx.message.attachments[0].url
        else:
            url = url.strip('<>') if url else None
        try:
            bio = await http.get(url, res_method="read")
            await self.bot.user.edit(avatar=bio)
            return await ctx.send(f"Successfully changed the avatar. Currently using:\n{url}")
        except aiohttp.InvalidURL:
            return await ctx.send("The URL is invalid...")
        except ValueError:
            return await ctx.send("This URL does not contain a usable image")
        except discord.HTTPException as err:
            return await ctx.send(str(err))
        except TypeError:
            return await ctx.send("You need to either provide an image URL or upload one with the command")

    @commands.command(name="gls")
    @commands.is_owner()
    async def get_lang_string(self, ctx: commands.Context, string: str, locale: str = "en"):
        """ Test a string """
        return await ctx.send(ctx.language2(locale).string(string))

    @commands.command(name="data")
    @commands.is_owner()
    async def get_lang_data(self, ctx: commands.Context, key: str, locale: str = "en"):
        """ Test a set of data of a language """
        return await ctx.send(str(ctx.language2(locale).data(key)))

    @commands.command(name="blacklist")
    @commands.is_owner()
    async def blacklist_add(self, ctx: commands.Context, user: discord.User):
        """ Blacklist a user from using the bot """
        try:
            blacklist = json.loads(open("blacklist.json", "r").read())
        except FileNotFoundError:
            blacklist = []
        blacklist.append(user.id)
        self.bot.blacklist = blacklist
        open("blacklist.json", "w+").write(json.dumps(blacklist))
        return await ctx.send(f"Added {user.id} ({user}) to the Blacklist")

    @commands.command(name="whitelist")
    @commands.is_owner()
    async def blacklist_remove(self, ctx: commands.Context, user: discord.User):
        """ Remove a user from the blacklist """
        try:
            blacklist = json.loads(open("blacklist.json", "r").read())
        except FileNotFoundError:
            blacklist = []
        try:
            blacklist.remove(user.id)
            self.bot.blacklist = blacklist
            open("blacklist.json", "w+").write(json.dumps(blacklist))
            return await ctx.send(f"Removed {user.id} ({user}) from the Blacklist")
        except ValueError:
            return await ctx.send(f"User {user.id} was not found in the Blacklist")

    @commands.command(name="seedm")
    @commands.is_owner()
    async def see_dm(self, ctx: commands.Context, user: discord.User, limit: int = None):
        """ Check someone's DMs with Suager """
        try:
            language = self.bot.language2('en')

            def convert(msg: discord.Message):
                base = f"{msg.author} - {language.time(msg.created_at, short=1, seconds=True)}\n"
                lmt = 1900
                extra = ""
                if msg.embeds:
                    extra += f"\nEmbeds: {len(msg.embeds)}"
                if msg.attachments:
                    file_links = [att.url + f" ({language.bytes(att.size)})" for att in msg.attachments]
                    lmt -= len(file_links) * 100
                    extra += f"\nAttachments: {len(file_links)}\n" + "\n".join(file_links)
                return base + msg.content[:lmt] + extra

            # We fetch the latest n messages, and then invert the order to be "oldest first" out of the n most recent messages (instead of the first n messages ever sent)
            _data = [convert(message) for message in [_ async for _ in (await user.create_dm()).history(limit=limit, oldest_first=False)][::-1]]
            messages = len(_data)
            data = "\n\n".join(_data)
            if ctx.guild is None:
                _limit = 8000000
            else:
                _limit = int(ctx.guild.filesize_limit / 1.05)
            rl = len(str(data))
            if rl == 0 or not data:
                return await ctx.send("Nothing was found...")
            elif 0 < rl <= 1900:
                return await ctx.send(f"DMs with {user} - {rl:,} chars (Last {messages} messages)\n\n{data}")
            elif 1900 < rl <= _limit:
                async with ctx.typing():
                    _data = BytesIO(str(data).encode('utf-8'))
                    lines = len(str(data).splitlines())
                    return await ctx.send(f"Results for {user} DMs - {lines:,} lines, {rl:,} chars (last {messages} messages)",
                                          file=discord.File(_data, filename=f"{time.file_ts('Logs')}"))
            elif rl > _limit:
                async with ctx.typing():
                    _data = BytesIO(str(data)[-_limit:].encode('utf-8'))
                    return await ctx.send(f"Result was a bit too long... ({rl:,} chars)\nSending latest", file=discord.File(_data, filename=f"{time.file_ts('DMs')}"))
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")

    @commands.group(name="config")
    @commands.is_owner()
    @commands.check(lambda ctx: ctx.channel.id == 753000962297299005)  # only secretive-commands-2
    async def config(self, ctx: commands.Context):
        """ See or update config
        Note to self: This command only works in <#753000962297299005>!"""
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @config.command(name="current")
    async def config_current(self, ctx: commands.Context):
        """ Current config (in JSON) """
        return await ctx.send("Current config:", file=discord.File("config.json"))

    @config.command(name="upload", aliases=["update"])
    async def config_upload(self, ctx: commands.Context):
        """ Upload settings using a JSON file """
        ma = ctx.message.attachments
        if len(ma) == 1:
            name = ma[0].filename
            if not name.endswith('.json'):
                return await ctx.send("This must be a JSON file.")
            try:
                stuff: bytes = await ma[0].read()
            except (discord.HTTPException, discord.NotFound):
                return await ctx.send("There was an error getting the file.")
        else:
            return await ctx.send("There must be exactly one JSON file.")
        try:
            stuff_str = json.dumps(json.loads(stuff), indent=2)
        except Exception as e:
            return await ctx.send(f"Error loading file:\n{type(e).__name__}: {e}")
        # stuff = json.dumps(json.loads(stuff), indent=0)
        open("config.json", "w").write(stuff_str)
        return await ctx.send("Config file updated.")

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync_slash_commands(self, ctx: commands.Context, action: str = ""):
        """ Synchronise slash commands

         (Empty) -> sync global slash commands
         local -> sync local slash commands for the current server
         global -> copy global slash commands to this server
         clear -> clear guild-specific slash commands from this server """
        async with ctx.typing():
            if not action:
                result = await self.bot.tree.sync()
                return await ctx.send(f"Synchronised {len(result)} slash commands")
            if action == "local":
                result = await self.bot.tree.sync(guild=ctx.guild)
                return await ctx.send(f"Synchronised {len(result)} local slash commands in this server")
            if action == "global":
                self.bot.tree.copy_global_to(guild=ctx.guild)
                result = await self.bot.tree.sync(guild=ctx.guild)
                return await ctx.send(f"Copied {len(result)} global slash commands to this server")
            if action == "clear":
                self.bot.tree.clear_commands(guild=ctx.guild)
                result = await self.bot.tree.sync(guild=ctx.guild)
                return await ctx.send(f"Cleared {len(result)} guild-specific slash commands from this server")

    # noinspection SqlResolve
    @commands.command(name="backup", hidden=True)
    @commands.is_owner()
    async def backup_image_server(self, ctx: commands.Command, guild_id: int, *, attachments_dir: str):
        """ Back up everything from the Regaus Image Server """
        server = self.bot.get_guild(guild_id)
        db = database.Database("backup.db")
        if server is None:
            return await ctx.send("Server not found...")
        await ctx.send(f"Starting backup for {server.name} ({server.id})")
        statements = ["BEGIN"]
        server_exists = db.fetchrow("SELECT * FROM servers WHERE id=?", (guild_id,))
        server_name = make_valid_sql(server.name)
        server_locale = server.preferred_locale.value  # type: ignore
        if server_exists:
            statements.append(f"UPDATE servers SET name={server_name}, owner_id={server.owner_id}, preferred_locale={server_locale!r} WHERE id={server.id}")
        else:
            statements.append(f"INSERT INTO servers(id, name, owner_id, preferred_locale) VALUES ({server.id!r}, {server_name}, {server.owner_id}, {server_locale!r})")

        # Emojis and stickers: emojis[id] = (name, filename)
        existing_emojis: dict[int, tuple[str, str]] = {e["id"]: (e["name"], e["filename"]) for e in db.fetch("SELECT id, name, filename FROM emojis WHERE guild_id=?", (guild_id,))}
        for emoji in server.emojis:
            emoji_name = make_valid_sql(emoji.name)
            emoji_roles = make_valid_sql(json.dumps([r.id for r in emoji.roles]))
            emoji_filename = emoji.url.split("/")[-1]
            physical_path = os.path.join(attachments_dir, emoji_filename)
            if not os.path.isfile(physical_path):
                try:
                    await emoji.save(physical_path)  # type: ignore
                except (discord.HTTPException, discord.NotFound):
                    await ctx.send(f"Emoji {emoji.id} ({emoji.name}) failed to download.")
            check: tuple[str, str] = existing_emojis.get(emoji.id)
            if check is not None:
                statements.append(f"UPDATE emojis SET name={emoji_name}, roles={emoji_roles}, filename={emoji_filename!r} WHERE id={emoji.id} AND guild_id={emoji.guild_id}")
                existing_emojis.pop(emoji.id)
            else:
                statements.append(f"INSERT INTO emojis(id, guild_id, name, roles, filename) VALUES ({emoji.id}, {emoji.guild_id}, {emoji_name}, {emoji_roles}, {emoji_filename!r})")
        for deleted_emoji, (deleted_name, deleted_filename) in existing_emojis.items():
            statements.append(f"DELETE FROM emojis WHERE id={deleted_emoji}")
            with suppress(FileNotFoundError):
                os.remove(os.path.join(attachments_dir, deleted_filename))
            # print(f"Debug: Emoji {deleted_emoji} - {deleted_name} no longer exists")
        await ctx.send("Backed up emojis")

        existing_stickers: dict[int, tuple[str, str]] = {s["id"]: (s["name"], s["filename"]) for s in db.fetch("SELECT id, name, filename FROM stickers WHERE guild_id=?", (guild_id,))}
        for sticker in server.stickers:
            sticker_name = make_valid_sql(sticker.name)
            sticker_description = make_valid_sql(sticker.description)
            sticker_emoji = make_valid_sql(sticker.emoji)  # Name of the Unicode emoji
            sticker_filename = sticker.url.split("/")[-1]
            physical_path = os.path.join(attachments_dir, sticker_filename)
            if not os.path.isfile(physical_path):
                try:
                    await sticker.save(physical_path)  # type: ignore
                except (discord.HTTPException, discord.NotFound):
                    await ctx.send(f"Sticker {sticker.id} ({sticker.name}) failed to download.")
            check: tuple[str, str] = existing_stickers.get(sticker.id)
            if check is not None:
                statements.append(f"UPDATE stickers SET name={sticker_name}, description={sticker_description}, unicode_emoji={sticker_emoji}, filename={sticker_filename!r} "
                                  f"WHERE id={sticker.id} AND guild_id={sticker.guild_id}")
                existing_stickers.pop(sticker.id)
            else:
                statements.append(f"INSERT INTO stickers(id, guild_id, name, description, unicode_emoji, filename) VALUES "
                                  f"({sticker.id}, {sticker.guild_id}, {sticker_name}, {sticker_description}, {sticker_emoji}, {sticker_filename!r})")
        for deleted_sticker, (deleted_name, deleted_filename) in existing_stickers.items():
            statements.append(f"DELETE FROM stickers WHERE id={deleted_sticker}")
            with suppress(FileNotFoundError):
                os.remove(os.path.join(attachments_dir, deleted_filename))
            # print(f"Debug: Sticker {deleted_sticker} - {deleted_name} no longer exists")
        await ctx.send("Backed up stickers")

        existing_roles: dict[int, str] = {r["id"]: r["name"] for r in db.fetch("SELECT id, name FROM roles WHERE guild_id=?", (guild_id,))}
        for role in server.roles:
            # We don't need to save information about the default role or bot roles.
            if not role.is_default() and not role.managed:
                # It seems like role position is not worth saving. I will just manually sort the positions afterwards.
                role_members = str([m.id for m in role.members])
                role_name = make_valid_sql(role.name)
                # payload = (role.id, role.guild.id, role.name, role.hoist, role.permissions.value, role.colour.value, role_members)
                # check = db.fetchrow("SELECT * FROM roles WHERE id=?", (role.id,))
                check: str = existing_roles.get(role.id)
                if check is not None:
                    # The server ID should never change, so we don't need to care about it.
                    # db.execute("UPDATE roles SET name=?, hoist=?, permissions=?, colour=?, members=? WHERE id=?", payload[2:] + payload[:1])  # id last
                    statements.append(f"UPDATE roles SET name={role_name}, hoist={role.hoist!r}, permissions={role.permissions.value!r}, "
                                      f"colour={role.colour.value!r}, members={role_members!r} WHERE id={role.id!r} AND guild_id={role.guild.id!r}")
                    existing_roles.pop(role.id)  # Remove from list so that we can delete roles we didn't find
                    # print(f"Debug: Updated role {role.id} - {role.name}")
                else:
                    # db.execute("INSERT INTO roles(id, guild_id, name, hoist, permissions, colour, members) VALUES (?, ?, ?, ?, ?, ?, ?)", payload)
                    statements.append(f"INSERT INTO roles(id, guild_id, name, hoist, permissions, colour, members) VALUES "
                                      f"({role.id!r}, {role.guild.id!r}, {role_name}, {role.hoist!r}, {role.permissions.value!r}, {role.colour.value!r}, {role_members!r})")
                    # print(f"Debug: Found new role {role.id} - {role.name}")
        for deleted_role, deleted_name in existing_roles.items():
            statements.append(f"DELETE FROM roles WHERE id={deleted_role!r}")
            # print(f"Debug: Role {deleted_role} - {deleted_name} no longer exists")
        statements.append("COMMIT")
        db.executescript("; ".join(statements))
        await ctx.send("Backed up roles")

        existing_channels: dict[int, str] = {c["id"]: c["name"] for c in db.fetch("SELECT id, name FROM channels WHERE guild_id=?", (guild_id,))}
        for channel in server.channels:
            statements = ["BEGIN"]
            if channel.category:
                category_id = repr(channel.category_id)
                category_name = make_valid_sql(channel.category.name)
            else:
                category_id = "NULL"
                category_name = "NULL"  # None

            # payload = (channel.id, channel.guild.id, channel.name, channel.type.value, channel.category_id, category_name, channel.nsfw, channel.position)
            # check = db.fetchrow("SELECT * FROM channels WHERE id=?", (channel.id,))
            check: str = existing_channels.get(channel.id)
            if check is not None:
                # db.execute("UPDATE channels SET name=?, type=?, category_id=?, category_name=?, nsfw=?, position=? WHERE id=?", payload[2:] + payload[:1])
                statements.append(f"UPDATE channels SET name={channel.name!r}, type={channel.type.value!r}, category_id={category_id}, category_name={category_name}, "  # cat name is repr'd
                                  f"nsfw={channel.nsfw!r}, position={channel.position!r} WHERE id={channel.id!r} AND guild_id={channel.guild.id!r}")
                existing_channels.pop(channel.id)
                # print(f"Debug: Updated channel {channel.id} - #{channel.name}")
            else:
                # db.execute("INSERT INTO channels(id, guild_id, name, type, category_id, category_name, nsfw, position) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", payload)
                statements.append(f"INSERT INTO channels(id, guild_id, name, type, category_id, category_name, nsfw, position) VALUES "
                                  f"({channel.id!r}, {channel.guild.id!r}, {channel.name!r}, {channel.type.value!r}, {category_id}, {category_name}, {channel.nsfw!r}, {channel.position!r})")
                # print(f"Debug: Found new channel {channel.id} - #{channel.name}")

            if channel.type == discord.ChannelType.text:
                # existing_messages[message_id] = [attachment_filename, attachment_filename, ...]
                existing_messages: dict[int, list[str]] = {m["message_id"]: json.loads(m["attachments_physical"]) for m in db.fetch("SELECT * FROM messages WHERE channel_id=?", (channel.id,))}
                # Go over all messages, as some might have been edited or deleted.
                async for message in channel.history(limit=None, oldest_first=True):
                    attachments_physical = []
                    attachments_filenames = []
                    for attachment in message.attachments:
                        # extension = attachment.filename.split('.')[-1]
                        extension = os.path.splitext(attachment.filename)[1]  # Get the extension, if any
                        physical_filename = f"{attachment.id}{extension}"  # The extension variable includes the dot
                        physical_path = os.path.join(attachments_dir, physical_filename)
                        # This could've been physical_path for ease of access (albeit wasting storage space on the repetition), but it's too late now.
                        # Just need to manually append attachment dir to path when creating the restoration messages.
                        # I guess it also means that the files can end up in a different directory and still be accessible.
                        attachments_physical.append(physical_filename)
                        attachments_filenames.append(attachment.filename)
                        if not os.path.isfile(physical_path):  # Only bother saving the attachment again if it does not already exist
                            try:
                                await attachment.save(physical_path)  # type: ignore
                            except (discord.HTTPException, discord.NotFound):
                                await ctx.send(f"{channel.name} -> Message {message.id} -> Attachment {attachment.filename} failed to download.")
                    # payload = (message.id, message.guild.id, message.author.id, general.username(message.author), str(message.author.display_avatar),
                    #            message.channel.id, message.channel.name, message.system_content, message.type.value, message.pinned,  # type: ignore
                    #            json.dumps(attachments_physical), json.dumps(attachments_filenames), json.dumps([e.to_dict() for e in message.embeds]))

                    author_name = make_valid_sql(general.username(message.author))
                    author_avatar_url = str(message.author.display_avatar)
                    message_content = make_valid_sql(message.system_content)  # type: ignore
                    attachments_physical_str = json.dumps(attachments_physical)
                    attachments_filenames_str = json.dumps(attachments_filenames)
                    embeds_str = make_valid_sql(json.dumps([e.to_dict() for e in message.embeds]))
                    # check = db.fetchrow("SELECT * FROM messages WHERE message_id=?", (message.id,))
                    check: list[str] = existing_messages.get(message.id)
                    if check is not None:  # Don't fail if the list of attachments is empty but the message does exist
                        for filename in check:
                            if filename not in attachments_physical:  # File no longer exists
                                with suppress(FileNotFoundError):
                                    os.remove(os.path.join(attachments_dir, filename))
                                    # print(f"Debug: Deleted attachment {filename} for existing message {message.id} in #{channel.name}")
                        # db.execute("UPDATE messages SET author_id=?, author_name=?, author_avatar_url=?, channel_id=?, channel_name=?, contents=?,"
                        #            "type=?, pinned=?, attachments_physical=?, attachments_filenames=?, embeds=? WHERE message_id=?", payload[2:] + payload[:1])
                        statements.append(f"UPDATE messages SET author_id={message.author.id!r}, author_name={author_name}, author_avatar_url={author_avatar_url!r}, "
                                          f"channel_id={message.channel.id!r}, channel_name={message.channel.name!r}, contents={message_content}, "
                                          f"type={message.type.value!r}, pinned={message.pinned!r}, attachments_physical={attachments_physical_str!r}, "  # type: ignore
                                          f"attachments_filenames={attachments_filenames_str!r}, embeds={embeds_str} WHERE message_id={message.id!r} AND guild_id={message.guild.id!r}")
                        existing_messages.pop(message.id)
                        # print(f"Debug: Updated message {message.id} in #{channel.name}")
                    else:
                        # db.execute("INSERT INTO messages(message_id, guild_id, author_id, author_name, author_avatar_url, channel_id, channel_name, contents, "
                        #            "type, pinned, attachments_physical, attachments_filenames, embeds) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", payload)
                        statements.append(f"INSERT INTO messages(message_id, guild_id, author_id, author_name, author_avatar_url, channel_id, channel_name, contents, "
                                          f"type, pinned, attachments_physical, attachments_filenames, embeds) VALUES ({message.id!r}, {message.guild.id!r}, {message.author.id!r}, {author_name},"
                                          f"{author_avatar_url!r}, {message.channel.id!r}, {message.channel.name!r}, {message_content}, {message.type.value!r},"  # type: ignore
                                          f"{message.pinned!r}, {attachments_physical_str!r}, {attachments_filenames_str!r}, {embeds_str})")
                        # print(f"Debug: Found new message {message.id} in #{channel.name}")
                for deleted_message, deleted_attachments in existing_messages.items():
                    statements.append(f"DELETE FROM messages WHERE message_id={deleted_message!r}")
                    # print(f"Debug: Message {deleted_message} no longer exists in #{channel.name}")
                    for filename in deleted_attachments:
                        with suppress(FileNotFoundError):
                            os.remove(os.path.join(attachments_dir, filename))
                            # print(f"Debug: Deleted attachment {filename} for deleted message {deleted_message}")
            statements.append("COMMIT")
            db.executescript("; ".join(statements))
            await ctx.send(f"Backed up channel {channel.mention}")
        statements = ["BEGIN"]
        for deleted_channel, deleted_name in existing_channels.items():
            statements.append(f"DELETE FROM channels WHERE id={deleted_channel!r}")
            # print(f"Debug: Channel {deleted_channel} - {deleted_name} no longer exists")
            deleted_messages = db.fetch("SELECT * FROM messages WHERE channel_id=?", (deleted_channel,))
            for message in deleted_messages:
                deleted_attachments = json.loads(message["attachments_physical"])
                for filename in deleted_attachments:
                    os.remove(os.path.join(attachments_dir, filename))
                    # print(f"Debug: Deleted attachment {filename} for message {message['message_id']} in deleted channel #{deleted_name}")
            statements.append(f"DELETE FROM messages WHERE channel_id={deleted_channel!r}")
        statements.append("COMMIT")
        db.executescript("; ".join(statements))
        return await ctx.send("Backup successful")


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Admin(bot))
