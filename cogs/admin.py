import importlib
from datetime import datetime
from io import BytesIO

import aiohttp
import discord
from discord.ext import commands

from cogs import main
from utils import generic, time, logs, permissions, data_io, http, prev, database


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = generic.get_config()
        self.db = database.Database()
        self.type = main.version
        self.dir = main.folder
        self.admin_mod = [f"{self.dir}.admin", f"{self.dir}.birthdays"]

    @commands.command(name="db")
    @commands.check(permissions.is_owner)
    async def db_command(self, ctx, *, query: str):
        """ Database query """
        try:
            data = self.db.execute(query)
            return await ctx.send(f"{data}")
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")

    @commands.command(name="fetch")
    @commands.check(permissions.is_owner)
    async def db_fetch(self, ctx, *, query: str):
        """ Fetch data from db """
        try:
            data = self.db.fetch(query)
            result = f"{data}"
            # return await ctx.send(result)
            if len(str(result)) == 0 or result is None:
                return await ctx.send("Code has been run, however returned no result.")
            elif len(str(result)) in range(2001, 8000001):
                async with ctx.typing():
                    data = BytesIO(str(result).encode('utf-8'))
                    return await ctx.send(f"Result was a bit too long... ({len(str(result)):,} chars)",
                                          file=discord.File(data, filename=f"{time.file_ts('Eval')}"))
            elif len(str(result)) > 8000000:
                return await ctx.send(f"Result was way too long... ({len(str(result)):,} chars)")
            else:
                return await ctx.send(str(result))
        except Exception as e:
            return await ctx.send(f"{type(e).__name__}: {e}")

    @commands.command(name='eval')
    @commands.check(permissions.is_owner)
    async def eval_cmd(self, ctx, *, cmd):
        """Evaluates input.
        Input is interpreted as newline separated statements.
        If the last statement is an expression, that is the return value.
        Usable globals:
          - `bot`: the bot instance
          - `discord`: the discord module
          - `commands`: the discord.ext.commands module
          - `ctx`: the invocation context
          - `__import__`: the builtin `__import__` function
        Such that `>eval 1 + 1` gives `2` as the result.
        """
        return await prev.eval_cmd(ctx, cmd)

    @commands.command(name="amiadmin")
    async def are_you_admin(self, ctx):
        """ Are you admin? """
        return await prev.are_you_admin(ctx)

    @commands.command()
    @commands.check(permissions.is_owner)
    async def reload(self, ctx, name: str):
        """ Reloads an extension. """
        return await prev.reload(self, ctx, self.type, name, self.dir)

    @commands.command(name="reloadall")
    @commands.check(permissions.is_owner)
    async def reload_all(self, ctx):
        """ Reloads all extensions. """
        return await prev.reload_all(self, ctx, self.dir)

    @commands.command()
    @commands.check(permissions.is_owner)
    async def shutdown(self, ctx):
        """ Shut the bot down """
        return await prev.shutdown(ctx, self.type)

    @commands.command()
    @commands.check(permissions.is_owner)
    async def load(self, ctx, name: str):
        """ Loads an extension. """
        return await prev.load(self, ctx, self.type, name, self.dir)

    @commands.command()
    @commands.check(permissions.is_owner)
    async def unload(self, ctx, name: str):
        """ Unloads an extension. """
        return await prev.unload(self, ctx, self.type, name, self.dir)

    @commands.command(name="reloadutil", aliases=["reloadutils"])
    @commands.check(permissions.is_owner)
    async def reload_utils(self, ctx, name: str):
        """ Reloads a utility module. """
        return await prev.reload_utils(ctx, self.type, name)

    @commands.command(name="exec", aliases=["execute"])
    @commands.check(permissions.is_owner)
    async def execute(self, ctx, *, text: str):
        """ Do a shell command. """
        return await prev.execute(ctx, text)

    @commands.group()
    @commands.check(permissions.is_owner)
    async def change(self, ctx):
        """ Change bot's data """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @change.command(name="playing")
    @commands.check(permissions.is_owner)
    async def change_playing(self, ctx, *, playing: str):
        """ Change playing status. """
        try:
            await self.bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.watching, name=playing),
                status=discord.Status.dnd
            )
            data_io.change_value("config.json", "playing", playing)
            await ctx.send(f"Successfully changed playing status to **{playing}**")
        except discord.InvalidArgument as err:
            await ctx.send(err)
        except Exception as e:
            await ctx.send(e)

    @change.command(name="username")
    @commands.check(permissions.is_owner)
    async def change_username(self, ctx, *, name: str):
        """ Change username. """
        try:
            await self.bot.user.edit(username=name)
            await ctx.send(f"Successfully changed username to **{name}**")
        except discord.HTTPException as err:
            await ctx.send(err)

    @change.command(name="nickname")
    @commands.check(permissions.is_owner)
    async def change_nickname(self, ctx, *, name: str = None):
        """ Change nickname. """
        try:
            await ctx.guild.me.edit(nick=name)
            if name:
                await ctx.send(f"Successfully changed nickname to **{name}**")
            else:
                await ctx.send("Successfully removed nickname")
        except Exception as err:
            await ctx.send(err)

    @change.command(name="avatar")
    @commands.check(permissions.is_owner)
    async def change_avatar(self, ctx, url: str = None):
        """ Change avatar. """
        if url is None and len(ctx.message.attachments) == 1:
            url = ctx.message.attachments[0].url
        else:
            url = url.strip('<>') if url else None

        try:
            bio = await http.get(url, res_method="read")
            await self.bot.user.edit(avatar=bio)
            await ctx.send(f"Successfully changed the avatar. Currently using:\n{url}")
        except aiohttp.InvalidURL:
            await ctx.send("The URL is invalid...")
        except discord.InvalidArgument:
            await ctx.send("This URL does not contain a useable image")
        except discord.HTTPException as err:
            await ctx.send(err)
        except TypeError:
            await ctx.send("You need to either provide an image URL or upload one with the command")

    @change.command(name="fullversion", aliases=["fversion", "version"])
    @commands.check(permissions.is_owner)
    async def change_full_version(self, ctx, new_version: str):
        """ Change version (full) """
        try:
            old_version = self.config["bots"][self.type]["full_version"]
            # data_io.change_value("config.json", "full_version", new_version)
            # data_io.change_value("config_example.json", "full_version", new_version)
            data_io.change_versions(self.type, "full_version", new_version)
        except Exception as e:
            return await ctx.send(e)
        try:
            for cog in self.admin_mod:
                self.bot.reload_extension(cog)
                # await ctx.send(f"_Reloaded **{cog[5:]}.py** for config update_")
        except Exception as e:
            return await ctx.send(e)
        to_send = f"Changed full version from **{old_version}** to **{new_version}**"
        if generic.get_config()["logs"]:
            # await logs.log_channel(self.bot, 'changes').send(to_send)
            file = logs.get_place(self.type, "version_changes")
            logs.save(file, f"{time.time()} > {to_send}")
        return await ctx.send(to_send)

    @change.command(name="shortversion", aliases=["sversion"])
    @commands.check(permissions.is_owner)
    async def change_short_version(self, ctx, new_version: str):
        """ Change version (short) """
        try:
            old_version = self.config["bots"][self.type]["version"]
            # data_io.change_value("config.json", "version", new_version)
            # data_io.change_value("config_example.json", "version", new_version)
            data_io.change_versions(self.type, "version", new_version)
        except Exception as e:
            return await ctx.send(e)
        try:
            for cog in self.admin_mod:
                self.bot.reload_extension(cog)
                # await ctx.send(f"_Reloaded **{cog[5:]}.py** for config update_")
        except Exception as e:
            return await ctx.send(e)
        to_send = f"Changed short version from **{old_version}** to **{new_version}**"
        if generic.get_config()["logs"]:
            # await logs.log_channel(self.bot, 'changes').send(to_send)
            file = logs.get_place(self.type, "version_changes")
            logs.save(file, f"{time.time()} > {to_send}")
        return await ctx.send(to_send)

    @change.command(name="lastupdate")
    @commands.check(permissions.is_owner)
    async def change_last_update_value(self, ctx):
        """ Change last update time """
        now = time.now(False)
        try:
            last_update = self.config["bots"][self.type]["last_update"]
            # data_io.change_value("config.json", "last_update", int(datetime.timestamp(now)))
            # data_io.change_value("config_example.json", "last_update", int(datetime.timestamp(now)))
            data_io.change_versions(self.type, "last_update", int(datetime.timestamp(now)))
            # self.config.last_update = int(datetime.timestamp(now))
        except Exception as e:
            return await ctx.send(e)
        try:
            for cog in self.admin_mod:
                self.bot.reload_extension(cog)
                # await ctx.send(f"_Reloaded **{cog[5:]}.py** for config update_")
        except Exception as e:
            return await ctx.send(e)
        _lu = time.time_output(time.from_ts(last_update))
        _nu = time.time_output(now)
        to_send = f"Changed last update from **{_lu}** to **{_nu}**"
        if generic.get_config()["logs"]:
            # await logs.log_channel(self.bot, 'changes').send(to_send)
            file = logs.get_place(self.type, "version_changes")
            logs.save(file, f"{time.time()} > {to_send}")
        return await ctx.send(to_send)

    @commands.command(name="tables")
    @commands.is_owner()
    async def recreate_tables(self, ctx):
        """ Recreate all tables """
        module_name = importlib.import_module(f"utils.database")
        importlib.reload(module_name)
        val = database.creation()
        return await ctx.send("Task succeeded successfully - Tables created." if val else
                              "Task failed successfully - Great, more time to was on trying to fix that!")

    @commands.command(name="timeout")
    @commands.is_owner()
    async def fuck_off(self, ctx):
        """ Cause the bot to disconnect """
        import time as tl
        await ctx.send(f"{ctx.author.mention} Disconnecting...")
        tl.sleep(100)
        return await ctx.send(f"{ctx.author.mention} Finished. Why even make me do this?")


def setup(bot):
    bot.add_cog(AdminCommands(bot))
