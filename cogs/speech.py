import random
from io import BytesIO

import discord
from discord.ext import commands

from utils import permissions, emotes, http


class Speech(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, msg):
        mention = [f"<@!{self.bot.user.id}>", f"<@{self.bot.user.id}>"]
        gb = [f"{m} good bot" for m in mention]
        bb = [f"{m} bad bot" for m in mention]
        if msg.content.lower() in gb:
            await msg.channel.send(f"Thanks :3 {emotes.AlexPat}")
        if msg.content.lower() in bb:
            await msg.channel.send(f"Aww... :( {emotes.AlexHeartBroken}")

    @commands.command(name="dm")
    @commands.is_owner()
    async def dm(self, ctx, user_id: int, message: str):
        """ DM a user """
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        user = self.bot.get_user(user_id)
        if not user:
            return await ctx.send(f"Could not find user with ID {user_id}")
        try:
            await user.send(message)
            return await ctx.send(f"✉️ Sent DM to **{user}**", delete_after=10)
        except discord.Forbidden:
            return await ctx.send("User might have blocked DMs, or be a bot account.")

    @commands.command(name="tell")
    @commands.guild_only()
    @permissions.has_permissions(manage_messages=True)
    async def tell(self, ctx, channel: discord.TextChannel, *, message: str):
        """ Say something to a channel """
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        if channel.guild != ctx.guild:
            return await ctx.send(f"Hmm, it doesn't seem like this channel is in {ctx.guild.name}, "
                                  f"but rather {channel.guild.name}...")
        try:
            await channel.send(message)
        except Exception as e:
            return await ctx.send(f"Could not send message: {e}")
        return await ctx.send(f"✉️ Successfully sent message to {channel.mention}", delete_after=10)

    @commands.command(name="atell")
    @commands.is_owner()
    async def admin_tell(self, ctx, channel_id: int, *, message: str):
        """ Say something to a channel """
        channel = self.bot.get_channel(channel_id)
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        try:
            await channel.send(message)
        except Exception as e:
            return await ctx.send(f"Could not send message: {e}")
        return await ctx.send(f"✉️ Successfully sent message to {channel.mention}", delete_after=10)

    @commands.command(name="say")
    @commands.guild_only()
    async def say(self, ctx, *, message: str):
        """ Make me speak! """
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        await ctx.send(f"**{ctx.author}:**\n{message}")
        return await ctx.send(f"✉️ Successfully sent message", delete_after=10)

    @commands.command(name="tellimg")
    @commands.guild_only()
    @permissions.has_permissions(manage_messages=True)
    async def tell_image(self, ctx, channel: discord.TextChannel, *, message: str = ""):
        """ Send an image to a channel """
        if len(ctx.message.attachments) == 1:
            url = ctx.message.attachments[0].url
            fn = ctx.message.attachments[0].filename
            spoiler = ctx.message.attachments[0].is_spoiler()
        else:
            return await ctx.send(f"I need you to upload a file with the command, otherwise use {ctx.prefix}tell.")
        bio = BytesIO(await http.get(url, res_method="read"))
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        if channel.guild != ctx.guild:
            return await ctx.send(f"Hmm, it doesn't seem like this channel is in {ctx.guild.name}, "
                                  f"but rather {channel.guild.name}...")
        try:
            await channel.send(message, file=discord.File(bio, filename=fn, spoiler=spoiler))
        except Exception as e:
            return await ctx.send(f"Could not send message: {e}")
        return await ctx.send(f"✉️ Successfully sent message to {channel.mention}", delete_after=10)

    @commands.command(name="tellembed")
    @commands.guild_only()
    @permissions.has_permissions(manage_messages=True)
    async def tell_embed(self, ctx, channel: discord.TextChannel, embed_colour: str, thumbnail_url: str,
                         *, message: str):
        """ Say something with an embed

         Put "none" as thumbnail_url to not use one """
        if embed_colour == "random":
            colour = random.randint(0, 0xffffff)
            # _colour = hex(__colour)[2:]
            a = 6
        else:
            try:
                colour = int(embed_colour, base=16)
                # _colour = hex(__colour)[2:]
                a = len(embed_colour)
                if a != 3 and a != 6:
                    return await ctx.send(f"Value must be either 3 or 6 digits long")
            except Exception as e:
                return await ctx.send(f"Invalid colour: {e}\nValue must be either `random` or a HEX value")
        if a == 3:
            d, e, f = embed_colour
            colour = int(f"{d}{d}{e}{e}{f}{f}", base=16)
        embed = discord.Embed(colour=colour, description=message)
        if thumbnail_url.lower() != "none":
            embed.set_thumbnail(url=thumbnail_url.lower())
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        if channel.guild != ctx.guild:
            return await ctx.send(f"Hmm, it doesn't seem like this channel is in {ctx.guild.name}, "
                                  f"but rather {channel.guild.name}...")
        try:
            await channel.send(embed=embed)
        except Exception as e:
            return await ctx.send(f"Could not send message: {e}")
        return await ctx.send(f"✉️ Successfully sent message to {channel.mention}", delete_after=10)


def setup(bot):
    bot.add_cog(Speech(bot))
