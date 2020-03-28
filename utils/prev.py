# Commands from previous bot, which were in shared/shared.py
import ast
import asyncio
import importlib
import os
import time as _time
from asyncio.subprocess import PIPE
from io import BytesIO

import discord
from discord.ext import commands

from utils import time, generic, logs, emotes, database


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


async def eval_(ctx, cmd):
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
            '__import__': __import__
        }
        exec(compile(parsed, filename="<ast>", mode="exec"), env)

        result = (await eval(f"{fn_name}()", env))
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


async def eval_cmd(ctx, cmd):
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
    return await eval_(ctx, cmd)


async def are_you_admin(ctx):
    """ Are you admin? """
    if ctx.author.id == 86477779717066752:
        return await ctx.send(f"**{ctx.author.name}**... No, but you are the author of the original source code")
    elif ctx.author.id in generic.get_config().owners:
        return await ctx.send(f"{emotes.Allow} Yes **{ctx.author.name}** you are admin")

    return await ctx.send(f"{emotes.Deny} **no**, go away **{ctx.author.name}** "
                          f"{emotes.BlobCatPolice}")


async def reload(self, ctx, version: str, name: str, where: str):
    """ Reloads an extension. """
    try:
        self.bot.reload_extension(f"{where}.{name}")
    except Exception as e:
        return await ctx.send(f"```diff\n- {e}```")
    reloaded = f"Reloaded extension **{name}.py**"
    await ctx.send(reloaded)
    if generic.get_config()["logs"]:
        # await logs.log_channel(self.bot, 'changes').send(f"{time.time()} > {reloaded}")
        logs.save(logs.get_place(version, "changes"), f"{time.time()} > {reloaded}")


async def reload_all(self, ctx, where: str):
    """ Reloads all extensions. """
    error_collection = []
    for file in os.listdir("cogs"):
        if file.endswith(".py"):
            name = file[:-3]
            try:
                self.bot.reload_extension(f"{where}.{name}")
            except Exception as e:
                error_collection.append([file, generic.traceback_maker(e, advance=False)])
    if error_collection:
        output = "\n".join([f"**{g[0]}** ```diff\n- {g[1]}```" for g in error_collection])
        return await ctx.send(f"Attempted to reload all extensions, was able to reload, "
                              f"however the following failed...\n\n{output}")
    await ctx.send("Successfully reloaded all extensions")


async def shutdown(ctx, version: str):
    """ Shut down the bot """
    import sys
    await ctx.send('Shutting down...')
    if generic.get_config()["logs"]:
        # await logs.log_channel(self.bot, 'uptime').send(f"{time.time()} > Shutting down from command...")
        logs.save(logs.get_place(version, "uptime"), f"{time.time()} > Shutting down from command...")
    _time.sleep(1)
    sys.exit(0)


async def load(self, ctx, version: str, name: str, where: str):
    """ Loads an extension. """
    try:
        self.bot.load_extension(f"{where}.{name}")
    except Exception as e:
        return await ctx.send(f"```diff\n- {e}```")
    reloaded = f"Loaded extension **{name}.py**"
    await ctx.send(reloaded)
    if generic.get_config()["logs"]:
        # await logs.log_channel(self.bot, 'changes').send(f"{time.time()} > {reloaded}")
        logs.save(logs.get_place(version, "changes"), f"{time.time()} > {reloaded}")


async def unload(self, ctx, version: str, name: str, where: str):
    """ Unloads an extension. """
    try:
        self.bot.unload_extension(f"{where}.{name}")
    except Exception as e:
        return await ctx.send(f"```diff\n- {e}```")
    reloaded = f"Unloaded extension **{name}.py**"
    await ctx.send(reloaded)
    if generic.get_config()["logs"]:
        # await logs.log_channel(self.bot, 'changes').send(f"{time.time()} > {reloaded}")
        logs.save(logs.get_place(version, "changes"), f"{time.time()} > {reloaded}")


async def reload_utils(ctx, version: str, name: str):
    """ Reloads a utility module. """
    name_maker = f"**utils/{name}.py**"
    try:
        module_name = importlib.import_module(f"utils.{name}")
        importlib.reload(module_name)
    except ModuleNotFoundError:
        return await ctx.send(f"Couldn't find module named {name_maker}")
    except Exception as e:
        error = generic.traceback_maker(e)
        return await ctx.send(f"Module {name_maker} returned an error and was not reloaded...\n{error}")
    reloaded = f"Reloaded module {name_maker}"
    await ctx.send(reloaded)
    if generic.get_config()["logs"]:
        # await logs.log_channel(self.bot, 'changes').send(f"{time.time()} > {reloaded}")
        logs.save(logs.get_place(version, "changes"), f"{time.time()} > {reloaded}")


async def execute(ctx, text: str):
    """ Do a shell command. """
    message = await ctx.send(f"Loading...")
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
            await ctx.send(content=f"The result was a bit too long.. so here is a text file instead 👍",
                           file=discord.File(data, filename=time.file_ts(f'Result')))
        except asyncio.TimeoutError as e:
            await message.delete()
            return await ctx.send(e)
    else:
        await message.edit(content=f"```fix\n{content}\n```")


async def status(ctx, _type: int):
    """ Offline / Online / Restart """
    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass
    updates = ["Server is offline", "Server is online", "Restart incoming"]
    update = updates[_type]
    now = time.time()
    return await ctx.send(f"{now} > **{update}**")
