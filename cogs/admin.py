from discord.ext import commands

from utils import generic


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = generic.get_config()

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, name: str):
        """ Reloads an extension. """
        try:
            self.bot.unload_extension(f"cogs.{name}")
            self.bot.load_extension(f"cogs.{name}")
        except Exception as e:
            return await ctx.send(f"```\n{e}```")
        await ctx.send(f"Reloaded extension **{name}.py**")

    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx):
        """ Reboot the bot """
        await ctx.send('Shutting down...')
        await self.bot.logout()

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, name: str):
        """ Reloads an extension. """
        try:
            self.bot.load_extension(f"cogs.{name}")
        except Exception as e:
            return await ctx.send(f"```diff\n- {e}```")
        await ctx.send(f"Loaded extension **{name}.py**")

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, name: str):
        """ Reloads an extension. """
        try:
            self.bot.unload_extension(f"cogs.{name}")
        except Exception as e:
            return await ctx.send(f"```diff\n- {e}```")
        await ctx.send(f"Unloaded extension **{name}.py**")


def setup(bot):
    bot.add_cog(Admin(bot))
