import discord
from discord.ext import commands

from utils import permissions


class Speech(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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


def setup(bot):
    bot.add_cog(Speech(bot))
