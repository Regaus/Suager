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

from utils import bot_data, commands, data_io, database, general, http, logger, time


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
        # noinspection PyUnresolvedReferences
        body = parsed.body[0].body
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
        return await ctx.send("\n".join(tb))


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
                            await ctx.send(f"`{filename}`: Encoding broke - `{e}`")
                    else:
                        try:
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


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Admin(bot))
