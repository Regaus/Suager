import discord
from discord.ext import commands
from discord.ext.tasks import loop

from core.utils import events, time, database, general

playing_rate = 60


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.changes = f"data/{self.bot.name}/changes.json"
        self.config = self.bot.config
        self.db = database.Database(self.bot.name)
        self.exists = False
        self.local_config = self.bot.local_config
        global playing_rate
        playing_rate = self.local_config["playing_rate"]
        self.playing.start()
        if self.bot.name == "suager":
            self.avatar.start()

    def con_unload(self):
        self.playing.cancel()
        if self.bot.name == "suager":
            self.avatar.cancel()

    @commands.Cog.listener()
    async def on_message(self, ctx: discord.Message):
        if ctx.author.id == 667187968145883146:
            bad = ["reg", "rag", "reh", "<@302851022790066185>", "<@!302851022790066185>"]
            for word in bad:
                if word in ctx.content.lower():
                    await general.send(f"{ctx.author} | {ctx.channel.mention} | {time.time()}\n{ctx.content}", self.bot.get_channel(739183533792297164))
                    break

    @commands.Cog.listener()
    async def on_command_error(self, ctx, err):
        return await events.on_command_error(self, ctx, err)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        return await events.on_guild_join(self, guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        return await events.on_guild_remove(self, guild)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        return await events.on_command(self, ctx)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        return await events.on_member_join(self, member)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        return await events.on_member_remove(self, member)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User or discord.Member):
        return await events.on_member_ban(self, guild, user)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        return await events.on_member_unban(self, guild, user)

    @commands.Cog.listener()
    async def on_disconnect(self):
        self.exists = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self.bot, 'uptime'):
            self.bot.uptime = time.now(None)
        self.exists = True
        return await events.on_ready(self)

    @loop(seconds=playing_rate)
    async def playing(self):
        self.config = general.get_config()
        self.local_config = self.config["bots"][self.bot.index]
        global playing_rate
        playing_rate = self.local_config["playing_rate"]
        await events.playing_changer(self)

    @playing.before_loop
    async def playing_before(self):
        await self.bot.wait_until_ready()

    @loop(hours=1)
    async def avatar(self):
        await events.avatar_changer(self)

    @avatar.before_loop
    async def avatar_before(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Events(bot))
