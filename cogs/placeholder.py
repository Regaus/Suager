from discord import app_commands

from utils import bot_data, commands


class Placeholder(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.hybrid_command(name="placeholder")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.user)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def placeholder(self, ctx: commands.Context):
        """ Placeholder """
        language = ctx.language()
        return await ctx.send(language.string("placeholder"))


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Placeholder(bot))
