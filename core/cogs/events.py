from io import BytesIO
from typing import List

import discord
from discord.ext import commands
from discord.ext.tasks import loop

from core.utils import events, general, time


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db
        self.changes = f"data/{self.bot.name}/changes.json"
        self.config = self.bot.config
        self.exists = False
        self.local_config = self.bot.local_config
        self.playing.start()
        if self.bot.name == "suager":
            self.avatar.start()
        self.blocked = [667187968145883146]
        self.bad = ["re", "rag", "<@302851022790066185>", "<@!302851022790066185>"]
        self.updates = [self.bot.get_channel(x) for x in [572857995852251169, 740665941712568340]]
        self.blocked_logs = self.bot.get_channel(739183533792297164)
        self.message_ignore = [671520521174777869, 672535025698209821, 681647810357362786, 705947617779253328, 721705731937665104, 725835449502924901,
                               571025667265658881, 571025667265658881, 571278954523000842, 573636220622471168, 571030189451247618, 582598504233304075,
                               571031080908357633, 674342275421175818, 764528556507922442, 742885168997466196]

    def con_unload(self):
        self.playing.cancel()
        if self.bot.name == "suager":
            self.avatar.cancel()

    @commands.Cog.listener()
    async def on_message(self, ctx: discord.Message):
        if ctx.guild is not None:
            if (ctx.guild.id == 568148147457490954 and ctx.channel.id == 568148147457490958) and "<a:SM_rape:568254043030421536>" in ctx.content:
                try:
                    await ctx.delete()
                except discord.NotFound:
                    pass
        if self.blocked_logs is not None:
            if ctx.author.id in self.blocked:
                for word in self.bad:
                    if word in ctx.content.lower():
                        await general.send(f"{ctx.author} | {ctx.channel.mention} | {time.time()}\n{ctx.content}", self.blocked_logs)
                        break
        if ctx.channel.id == 742886280911913010:
            for channel in self.updates:
                try:
                    if channel is not None:
                        await general.send(f"{ctx.author} | #{ctx.channel.name} ({ctx.guild.name}) | {time.time()}\n{ctx.content}", channel)
                except Exception as e:
                    await general.send(f"on_message > Update announcement > {channel} > {type(e).__name__}: {e}", ctx.channel)

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
        self.updates = [self.bot.get_channel(x) for x in [572857995852251169, 740665941712568340]]
        self.blocked_logs = self.bot.get_channel(739183533792297164)
        return await events.on_ready(self)

    @loop(minutes=1)
    async def playing(self):
        self.config = general.get_config()
        self.local_config = self.config["bots"][self.bot.index]
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

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        async def process_msg(cid: int):
            output = f"A message was deleted in {message.channel.mention} ({message.channel.id})\nAuthor: {message.author}\n" \
                     f"Message sent: {message.created_at}\nMessage content: {message.content[:1850]}"
            files = []
            for attachment in message.attachments:
                file = BytesIO()
                try:
                    await attachment.save(file)
                except (discord.NotFound, discord.HTTPException):
                    pass
                files.append(discord.File(file, filename=attachment.filename))
            embed = message.embeds[0] if message.embeds else None
            await general.send(output, self.bot.get_channel(cid), embed=embed, files=files)

        if message.guild.id in [568148147457490954, 738425418637639775]:
            if message.channel.id not in self.message_ignore:
                if not message.author.bot:
                    await process_msg(764473671090831430 if message.guild.id == 568148147457490954 else 764494075663351858)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: List[discord.Message]):
        async def process_msg(cid: int):
            output = f"A message was deleted in {message.channel.mention} ({message.channel.id})\nAuthor: {message.author}\n" \
                     f"Message sent: {message.created_at}\nMessage content: {message.content[:1850]}"
            files = []
            for attachment in message.attachments:
                file = BytesIO()
                try:
                    await attachment.save(file)
                except (discord.NotFound, discord.HTTPException):
                    pass
                files.append(discord.File(file, filename=attachment.filename))
            embed = message.embeds[0] if message.embeds else None
            await general.send(output, self.bot.get_channel(cid), embed=embed, files=files)
        for message in messages:
            if message.guild.id in [568148147457490954, 738425418637639775]:
                if message.channel.id not in self.message_ignore:
                    if not message.author.bot:
                        await process_msg(764473671090831430 if message.guild.id == 568148147457490954 else 764494075663351858)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        async def process_msg(cid: int):
            embed = discord.Embed(description=f"Message was edited in {after.channel.mention} ({after.channel.id})\n"
                                              f"Author: {after.author}\nMessage sent: {after.created_at}")
            embed.add_field(name="Content Before", value=before.content, inline=False)
            embed.add_field(name="Content After", value=after.content, inline=False)
            await general.send(None, self.bot.get_channel(cid), embed=embed)

        if after.guild.id in [568148147457490954, 738425418637639775]:
            if after.channel.id not in self.message_ignore:
                if not after.author.bot:
                    await process_msg(764473671090831430 if after.guild.id == 568148147457490954 else 764494075663351858)


def setup(bot):
    bot.add_cog(Events(bot))
