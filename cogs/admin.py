import ast
import asyncio
import importlib
import os
from asyncio.subprocess import PIPE
from io import BytesIO

import aiohttp
import discord
from discord.ext import commands

from utils import generic, permissions, time, database, logs, data_io, http, emotes


def insert_returns(body):
    # insert return stmt if the last expression is a expression statement
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    # for if statements, we insert returns into the body and the orelse
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
        # return await ctx.send(result)
        if ctx.guild is None:
            limit = 8000000
        else:
            limit = int(ctx.guild.filesize_limit / 1.05)
        if len(str(result)) == 0 or result is None:
            return await generic.send("Code has been run, however returned no result.", ctx.channel)
            # return await ctx.send("Code has been run, however returned no result.")
        elif len(str(result)) in range(2001, limit + 1):
            async with ctx.typing():
                data = BytesIO(str(result).encode('utf-8'))
                return await generic.send(f"Result was a bit too long... ({len(str(result)):,} chars)", ctx.channel,
                                          file=discord.File(data, filename=f"{time.file_ts('Eval')}"))
                # return await ctx.send(f"Result was a bit too long... ({len(str(result)):,} chars)",
                #                       file=discord.File(data, filename=f"{time.file_ts('Eval')}"))
        elif len(str(result)) > limit:
            async with ctx.typing():
                data = BytesIO(str(result)[-limit:].encode('utf-8'))
                return await generic.send(f"Result was a bit too long... ({len(str(result)):,} chars)\nSending last {limit:,} chars", ctx.channel,
                                          file=discord.File(data, filename=f"{time.file_ts('Eval')}"))
            # return await generic.send(f"Result was way too long... ({len(str(result)):,} chars)", ctx.channel)
            # return await ctx.send(f"Result was way too long... ({len(str(result)):,} chars)")
        else:
            return await generic.send(str(result), ctx.channel)
            # return await ctx.send(str(result))
    except Exception as e:
        return await generic.send(f"{type(e).__name__}: {e}", ctx.channel)
        # return await ctx.send(f"{type(e).__name__}: {e}")


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
        # return await ctx.send(f"Couldn't find module named {name_maker}")
    except Exception as e:
        error = generic.traceback_maker(e)
        return f"Module {name_maker} returned an error and was not reloaded...\n{error}"
        # return await ctx.send(f"Module {name_maker} returned an error and was not reloaded...\n{error}")
    reloaded = f"Reloaded module {name_maker}"
    # await generic.send(reloaded, ctx.channel)
    # await ctx.send(reloaded)
    if generic.get_config()["logs"]:
        logs.log("changes", f"{time.time()} > {reloaded}")
        # await logs.log_channel(self.bot, 'changes').send(f"{time.time()} > {reloaded}")
        # logs.save(logs.get_place(version, "changes"), f"{time.time()} > {reloaded}")'
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
            # return await ctx.send(f"**{ctx.author.name}**... No, but you are the author of the original source code")
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
            # return await ctx.send(f"{data}")
        except Exception as e:
            return await generic.send(f"{type(e).__name__}: {e}", ctx.channel)
            # return await ctx.send(f"{type(e).__name__}: {e}")

    @commands.command(name="fetch")
    @commands.check(permissions.is_owner)
    async def db_fetch(self, ctx: commands.Context, *, query: str):
        """ Fetch data from db """
        try:
            data = self.db.fetch(query)
            result = f"{data}"
            if ctx.guild is None:
                limit = 8000000
            else:
                limit = int(ctx.guild.filesize_limit / 1.05)
            # return await ctx.send(result)
            if len(str(result)) == 0 or result is None:
                return await generic.send("Code has been run, however returned no result.", ctx.channel)
                # return await ctx.send("Code has been run, however returned no result.")
            elif len(str(result)) in range(2001, limit + 1):
                async with ctx.typing():
                    data = BytesIO(str(result).encode('utf-8'))
                    return await generic.send(f"Result was a bit too long... ({len(str(result)):,} chars)", ctx.channel,
                                              file=discord.File(data, filename=f"{time.file_ts('Fetch')}"))
                    # return await ctx.send(f"Result was a bit too long... ({len(str(result)):,} chars)",
                    #                       file=discord.File(data, filename=f"{time.file_ts('Eval')}"))
            elif len(str(result)) > limit:
                async with ctx.typing():
                    data = BytesIO(str(result)[-limit:].encode('utf-8'))
                    return await generic.send(f"Result was a bit too long... ({len(str(result)):,} chars)\nSending last {limit:,} chars", ctx.channel,
                                              file=discord.File(data, filename=f"{time.file_ts('Fetch')}"))
                # return await ctx.send(f"Result was way too long... ({len(str(result)):,} chars)")
            else:
                return await generic.send(str(result), ctx.channel)
                # return await ctx.send(str(result))
        except Exception as e:
            return await generic.send(f"{type(e).__name__}: {e}", ctx.channel)
            # return await ctx.send(f"{type(e).__name__}: {e}")

    @commands.command(name='eval')
    @commands.check(permissions.is_owner)
    async def eval_cmd(self, ctx: commands.Context, *, cmd):
        """ Evaluates input.
        Input is interpreted as newline separated statements.
        If the last statement is an expression, that is the return value.
        Such that `>eval 1 + 1` gives `2` as the result.
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
            # return await ctx.send(f"{type(e).__name__}: {e}")
        reloaded = f"Reloaded extension **cogs/{name}.py**"
        await generic.send(reloaded, ctx.channel)
        # await ctx.send(reloaded)
        if generic.get_config()["logs"]:
            logs.log("changes", f"{time.time()} > {reloaded}")
            # await logs.log_channel(self.bot, 'changes').send(f"{time.time()} > {reloaded}")
            # logs.save(logs.get_place(version, "changes"), f"{time.time()} > {reloaded}")

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
            # return await ctx.send(f"Attempted to reload all extensions, was able to reload, "
            #                       f"however the following failed...\n\n{output}")
        await generic.send("Successfully reloaded all extensions", ctx.channel)
        logs.log("changes", f"{time.time()} > Successfully reloaded all extensions")
        # await ctx.send("Successfully reloaded all extensions")

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

    @commands.command(name="load")
    @commands.check(permissions.is_owner)
    async def load(self, ctx: commands.Context, name: str):
        """ Loads an extension. """
        try:
            self.bot.load_extension(f"cogs.{name}")
        except Exception as e:
            return await generic.send(f"{type(e).__name__}: {e}", ctx.channel)
            # return await ctx.send(f"```diff\n- {e}```")
        reloaded = f"Loaded extension **{name}.py**"
        # await ctx.send(reloaded)
        await generic.send(reloaded, ctx.channel)
        if generic.get_config()["logs"]:
            logs.log("changes", f"{time.time()} > {reloaded}")
            # await logs.log_channel(self.bot, 'changes').send(f"{time.time()} > {reloaded}")
            # logs.save(logs.get_place(version, "changes"), f"{time.time()} > {reloaded}")

    @commands.command(name="unload")
    @commands.check(permissions.is_owner)
    async def unload(self, ctx: commands.Context, name: str):
        """ Unloads an extension. """
        try:
            self.bot.unload_extension(f"cogs.{name}")
        except Exception as e:
            return await generic.send(f"{type(e).__name__}: {e}", ctx.channel)
            # return await ctx.send(f"```diff\n- {e}```")
        reloaded = f"Unloaded extension **{name}.py**"
        await generic.send(reloaded, ctx.channel)
        # await ctx.send(reloaded)
        if generic.get_config()["logs"]:
            logs.log("changes", f"{time.time()} > {reloaded}")
            # await logs.log_channel(self.bot, 'changes').send(f"{time.time()} > {reloaded}")
            # logs.save(logs.get_place(version, "changes"), f"{time.time()} > {reloaded}")

    @commands.command(name="shutdown")
    @commands.check(permissions.is_owner)
    async def shutdown(self, ctx: commands.Context):
        """ Shut down the bot """
        import time as _time
        import sys
        await generic.send("Shutting down...", ctx.channel)
        # await ctx.send('Shutting down...')
        if generic.get_config()["logs"]:
            logs.log("uptime", f"{time.time()} > Shutting down from command...")
            # await logs.log_channel(self.bot, 'uptime').send(f"{time.time()} > Shutting down from command...")
            # logs.save(logs.get_place(version, "uptime"), f"{time.time()} > Shutting down from command...")
        _time.sleep(1)
        sys.stderr.close()
        sys.exit(0)

    @commands.command(name="execute", aliases=["exec"])
    @commands.check(permissions.is_owner)
    async def execute(self, ctx: commands.Context, *, text: str):
        """ Do a shell command. """
        message = await generic.send("Loading...", ctx.channel)
        # message = await ctx.send(f"Loading...")
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
                # await ctx.send(content=f"The result was a bit too long.. so here is a text file instead 👍",
                #                file=discord.File(data, filename=time.file_ts(f'Result')))
            except asyncio.TimeoutError as e:
                await message.delete()
                return await generic.send(str(e), ctx.channel)
                # return await ctx.send(e)
        else:
            await message.edit(content=f"```fix\n{content}\n```")

    @commands.command(name="online")
    @commands.check(permissions.is_owner)
    async def online(self, ctx: commands.Context):
        """ Server is online """
        return await status(ctx, 1)

    @commands.command(name="offline")
    @commands.check(permissions.is_owner)
    async def offline(self, ctx: commands.Context):
        """ Server is offline """
        return await status(ctx, 0)

    @commands.command(name="restart")
    @commands.check(permissions.is_owner)
    async def restart(self, ctx: commands.Context):
        """ Restart incoming """
        return await status(ctx, 2)

    @commands.command(name="tables")
    @commands.is_owner()
    async def recreate_tables(self, ctx: commands.Context):
        """ Recreate all tables """
        module_name = importlib.import_module(f"utils.database")
        importlib.reload(module_name)
        val = database.creation()
        send = "Task succeeded successfully - Tables created." if val else "Task failed successfully - Great, more time to was on trying to fix that!"
        return await generic.send(send, ctx.channel)

    @commands.group()
    @commands.check(permissions.is_owner)
    async def config(self, ctx: commands.Context):
        """ Change bot's configs """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @config.command(name="fullversion", aliases=["fversion", "version"])
    @commands.check(permissions.is_owner)
    async def change_full_version(self, ctx: commands.Context, new_version: str):
        """ Change version (full) """
        try:
            old_version = self.config["full_version"]
            data_io.change_version("full_version", new_version)
            # data_io.change_value("config.json", "full_version", new_version)
            # data_io.change_value("config_example.json", "full_version", new_version)
            # data_io.change_versions(self.type, "full_version", new_version)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)
            # return await ctx.send(e)
        try:
            for cog in self.admin_mod:
                self.bot.reload_extension(cog)
                # await ctx.send(f"_Reloaded **{cog[5:]}.py** for config update_")
        except Exception as e:
            return await generic.send(str(e), ctx.channel)
            # return await ctx.send(e)
        to_send = f"Changed full version from **{old_version}** to **{new_version}**"
        if generic.get_config()["logs"]:
            logs.log("version_changes", f"{time.time()} > {to_send}")
            # await logs.log_channel(self.bot, 'changes').send(to_send)
            # file = logs.get_place(self.type, "version_changes")
            # logs.save(file, f"{time.time()} > {to_send}")
        return await generic.send(to_send, ctx.channel)
        # return await ctx.send(to_send)

    @config.command(name="shortversion", aliases=["sversion"])
    @commands.check(permissions.is_owner)
    async def change_short_version(self, ctx: commands.Context, new_version: str):
        """ Change version (short) """
        try:
            old_version = self.config["version"]
            data_io.change_version("version", new_version)
            # data_io.change_value("config.json", "version", new_version)
            # data_io.change_value("config_example.json", "version", new_version)
            # data_io.change_versions(self.type, "version", new_version)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)
            # return await ctx.send(e)
        try:
            for cog in self.admin_mod:
                self.bot.reload_extension(cog)
                # await ctx.send(f"_Reloaded **{cog[5:]}.py** for config update_")
        except Exception as e:
            return await generic.send(str(e), ctx.channel)
            # return await ctx.send(e)
        to_send = f"Changed short version from **{old_version}** to **{new_version}**"
        if generic.get_config()["logs"]:
            logs.log("version_changes", f"{time.time()} > {to_send}")
            # await logs.log_channel(self.bot, 'changes').send(to_send)
            # file = logs.get_place(self.type, "version_changes")
            # logs.save(file, f"{time.time()} > {to_send}")
        return await generic.send(to_send, ctx.channel)
        # return await ctx.send(to_send)

    @config.command(name="heretics", aliases=["hl"])
    @commands.check(permissions.is_owner)
    async def config_heretics(self, ctx: commands.Context, action: str, tier: int, uid: int):
        """ Update the heretic list """
        try:
            data_io.change_values("heretics", str(tier), action, uid)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)
        reload = reload_util("generic")
        w1 = "added" if action == "add" else "removed"
        w2 = "to" if action == "add" else "from"
        return await generic.send(f"{emotes.Allow} Successfully {w1} <@{uid}> ({self.bot.get_user(uid)}) {w2} Tier {tier} Heretic List\n"
                                  f"Reload status: {reload}", ctx.channel)

    @config.command(name="heretics2", aliases=["hl2", "1up"])
    @commands.check(permissions.is_owner)
    async def config_heretics2(self, ctx: commands.Context, uid: int):
        """ Move someone higher up in the Heretic List """
        try:
            ret = generic.heresy(uid)
            # data_io.change_values("heretics", str(tier), action, uid)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)
        reload = reload_util("generic")
        if ret == 0:
            out = f"{emotes.Deny} Nothing happened."
        elif ret == 4:
            out = f"{emotes.Deny} <@{uid}> ({self.bot.get_user(uid)}) is already Tier 3."
        else:
            out = f"{emotes.Allow} <@{uid}> ({self.bot.get_user(uid)}) is now a Tier {ret} Heretic."
        return await generic.send(f"{out}\n{reload}", ctx.channel)
        # w1 = "added" if action == "add" else "removed"
        # w2 = "to" if action == "add" else "from"
        # return await generic.send(f"{emotes.Allow} Successfully {w1} <@{uid}> ({self.bot.get_user(uid)}) {w2} Tier {tier} Heretic List\n"
        #                           f"Reload status: {reload}", ctx.channel)

    @config.command(name="lovelocks", aliases=["love", "ll"])
    @commands.check(permissions.is_owner)
    async def config_love_locks(self, ctx: commands.Context, action: str, uid: int):
        """ Update the love locks list """
        try:
            data_io.change_values("love_locks", None, action, uid)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)
        reload = reload_util("generic")
        w1 = "added" if action == "add" else "removed"
        w2 = "to" if action == "add" else "from"
        return await generic.send(f"{emotes.Allow} Successfully {w1} <@{uid}> ({self.bot.get_user(uid)}) {w2} the Love Locks List\n"
                                  f"Reload status: {reload}", ctx.channel)

    @config.command(name="loveexceptions", aliases=["le"])
    @commands.check(permissions.is_owner)
    async def config_love_exceptions(self, ctx: commands.Context, action: str, uid: int, lid: int):  # UID = Who to except, LID = Locked user
        """ Update the love exceptions list """
        try:
            data_io.change_values("love_exceptions", str(lid), action, uid)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)
        reload = reload_util("generic")
        w1 = "added" if action == "add" else "removed"
        w2 = "to" if action == "add" else "from"
        return await generic.send(f"{emotes.Allow} Successfully {w1} <@{uid}> ({self.bot.get_user(uid)}) {w2} the Love Exceptions List of <@{lid}>\n"
                                  f"Reload status: {reload}", ctx.channel)

    @config.command(name="badlocks", aliases=["bl"])
    @commands.check(permissions.is_owner)
    async def config_bad_locks(self, ctx: commands.Context, action: str, uid: int):
        """ Update the bad/trash/bean locks list """
        try:
            data_io.change_values("bad_locks", None, action, uid)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)
        reload = reload_util("generic")
        w1 = "added" if action == "add" else "removed"
        w2 = "to" if action == "add" else "from"
        return await generic.send(f"{emotes.Allow} Successfully {w1} <@{uid}> ({self.bot.get_user(uid)}) {w2} the Bad Locks List\n"
                                  f"Reload status: {reload}", ctx.channel)

    @config.command(name="channellocks", aliases=["cl"])
    @commands.check(permissions.is_owner)
    async def config_channel_locks(self, ctx: commands.Context, action: str, cid: int):
        """ Update the channel locks list (tell to use bot commands) """
        try:
            data_io.change_values("channel_locks", None, action, cid)
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
            data_io.change_values("server_locks", str(gid), action, command)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)
        reload = reload_util("generic")
        w1 = "added" if action == "add" else "removed"
        w2 = "to" if action == "add" else "from"
        return await generic.send(f"{emotes.Allow} Successfully {w1} `{command}` {w2} the Server Locks List for {self.bot.get_guild(gid)}\n"
                                  f"Reload status: {reload}", ctx.channel)

    def get_user(self, uid: int) -> str:
        try:
            return str([user for user in self.bot.users if user.id == uid][0])
        except IndexError:
            return "None"

    @commands.command(name="heretics")
    @commands.check(permissions.is_owner)
    async def heretic_list(self, ctx: commands.Context):
        """ Heretic List """
        embed = discord.Embed(colour=generic.random_colour())
        embed.add_field(name="Tier 1", value="\n".join([" - ".join([f"<@{u}>", self.get_user(u)]) for u in generic.tier_1]), inline=False)
        embed.add_field(name="Tier 2", value="\n".join([" - ".join([f"<@{u}>", self.get_user(u)]) for u in generic.tier_2]), inline=False)
        embed.add_field(name="Tier 3", value="\n".join([" - ".join([f"<@{u}>", self.get_user(u)]) for u in generic.tier_3]), inline=False)
        return await generic.send("Here is a list of heretics", ctx.channel, embed=embed)

    @commands.command(name="locks", aliases=["heretics2"])
    @commands.check(permissions.is_owner)
    async def heretic_list2(self, ctx: commands.Context):
        """ Locks list """
        embed = discord.Embed(colour=generic.random_colour())
        embed.add_field(name="LL", value="\n".join([" - ".join([f"<@{u}>", self.get_user(u)]) for u in generic.love_locks]), inline=False)
        lev = ""
        le = generic.love_exceptions
        for lock in le:
            for exc in le[str(lock)]:
                lev += f"<@{exc}> - {self.get_user(exc)} for {self.get_user(int(lock))}\n"
        embed.add_field(name="LE", value=lev, inline=True)
        # embed.add_field(name="LE", value="\n".join([" - ".join([f"<@{u}>", self.get_user(u)]) for u in generic.love_exceptions]), inline=False)
        embed.add_field(name="BL", value="\n".join([" - ".join([f"<@{u}>", self.get_user(u)]) for u in generic.bad_locks]), inline=False)
        return await generic.send("Here is the locks list", ctx.channel, embed=embed)

    @commands.command(name="lv2l", aliases=["heretics3", "regausmad"])
    async def heretic_list3(self, ctx: commands.Context):
        """ The list of people who annoyed Regaus and got level -2 """
        res = self.db.fetch("SELECT * FROM leveling WHERE level=-2")
        embed = discord.Embed(colour=generic.random_colour())
        au = []
        desc = ""
        for user in res:
            if user["uid"] not in au:
                desc += f"<@{user['uid']}> - {user['name']}#{user['disc']:04d}\n"
                au.append(user["uid"])
        embed.description = desc
        # embed.description = "\n".join([" - ".join([f"<@{u['uid']}>", f"{u['name']}#{u['disc']:04d}"]) for u in res])
        return await generic.send("The list of people who managed to get level -2", ctx.channel, embed=embed)

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
            # await ctx.send(f"Successfully changed playing status to **{playing}**")
        except discord.InvalidArgument as err:
            return await generic.send(str(err), ctx.channel)
            # await ctx.send(err)
        except Exception as e:
            return await generic.send(str(e), ctx.channel)
            # await ctx.send(e)

    @change.command(name="username")
    @commands.check(permissions.is_owner)
    async def change_username(self, ctx: commands.Context, *, name: str):
        """ Change username. """
        try:
            await self.bot.user.edit(username=name)
            return await generic.send(f"Successfully changed username to **{name}**", ctx.channel)
            # await ctx.send(f"Successfully changed username to **{name}**")
        except discord.HTTPException as err:
            return await generic.send(str(err), ctx.channel)
            # await ctx.send(err)

    @change.command(name="nickname")
    @commands.check(permissions.is_owner)
    async def change_nickname(self, ctx: commands.Context, *, name: str = None):
        """ Change nickname. """
        try:
            await ctx.guild.me.edit(nick=name)
            if name:
                return await generic.send(f"Successfully changed nickname to **{name}**", ctx.channel)
                # await ctx.send(f"Successfully changed nickname to **{name}**")
            else:
                return await generic.send("Successfully removed nickname", ctx.channel)
                # await ctx.send("Successfully removed nickname")
        except Exception as err:
            return await generic.send(str(err), ctx.channel)
            # await ctx.send(err)

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
            # await ctx.send(f"Successfully changed the avatar. Currently using:\n{url}")
        except aiohttp.InvalidURL:
            return await generic.send("The URL is invalid...", ctx.channel)
            # await ctx.send("The URL is invalid...")
        except discord.InvalidArgument:
            return await generic.send("This URL does not contain a useable image", ctx.channel)
            # await ctx.send("This URL does not contain a useable image")
        except discord.HTTPException as err:
            return await generic.send(str(err), ctx.channel)
            # await ctx.send(err)
        except TypeError:
            return await generic.send("You need to either provide an image URL or upload one with the command", ctx.channel)
            # await ctx.send("You need to either provide an image URL or upload one with the command")

    @commands.command(name="log")
    @commands.check(permissions.is_owner)
    async def log(self, ctx: commands.Context, log: str):
        """ Get logs """
        try:
            data = open(f"data/{log}.rsf")
            result = f"{data}"
            if ctx.guild is None:
                limit = 8000000
            else:
                limit = int(ctx.guild.filesize_limit / 1.05)
            # return await ctx.send(result)
            if len(str(result)) == 0 or result is None:
                return await generic.send("Nothing was available...", ctx.channel)
                # return await ctx.send("Code has been run, however returned no result.")
            elif len(str(result)) in range(2001, limit + 1):
                async with ctx.typing():
                    data = BytesIO(str(result).encode('utf-8'))
                    return await generic.send(f"Result was a bit too long... ({len(str(result)):,} chars)", ctx.channel,
                                              file=discord.File(data, filename=f"{time.file_ts('Logs')}"))
                    # return await ctx.send(f"Result was a bit too long... ({len(str(result)):,} chars)",
                    #                       file=discord.File(data, filename=f"{time.file_ts('Eval')}"))
            elif len(str(result)) > limit:
                async with ctx.typing():
                    data = BytesIO(str(result)[-limit:].encode('utf-8'))
                    return await generic.send(f"Result was a bit too long... ({len(str(result)):,} chars)\nSending latest", ctx.channel,
                                              file=discord.File(data, filename=f"{time.file_ts('Logs')}"))
                # return await ctx.send(f"Result was way too long... ({len(str(result)):,} chars)")
            else:
                return await generic.send(str(result), ctx.channel)
                # return await ctx.send(str(result))
        except Exception as e:
            return await generic.send(f"{type(e).__name__}: {e}", ctx.channel)
            # return await ctx.send(f"{type(e).__name__}: {e}")


async def status(ctx: commands.Context, _type: int):
    """ Offline / Online / Restart """
    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass
    updates = ["Server is offline", "Server is online", "Restart incoming"]
    update = updates[_type]
    now = time.time()
    return await generic.send(f"{now} > **{update}**", ctx.channel)
    # return await ctx.send(f"{now} > **{update}**")


def setup(bot):
    bot.add_cog(Admin(bot))
