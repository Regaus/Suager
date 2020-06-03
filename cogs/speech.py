import random
from io import BytesIO

import discord
from discord.ext import commands

from utils import permissions, http, generic


class Speech(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="dm")
    @commands.is_owner()
    async def dm(self, ctx: commands.Context, user_id: int, *, message: str):
        """ DM a user """
        locale = generic.get_lang(ctx.guild)
        try:
            await ctx.message.delete()
        except Exception as e:
            await generic.send(generic.gls(locale, "message_del_error", [e]), ctx.channel, delete_after=5)
        user = self.bot.get_user(user_id)
        if not user:
            return await generic.send(generic.gls(locale, "dm_not_found", [user_id]), ctx.channel)
        try:
            await user.send(message)
            return await generic.send(generic.gls(locale, "dm_successful", [user]), ctx.channel, delete_after=5)
        except discord.Forbidden:
            return await generic.send(generic.gls(locale, "dm_failed"), ctx.channel)

    @commands.command(name="tell")
    @commands.guild_only()
    @permissions.has_permissions(manage_messages=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def tell(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str):
        """ Say something to a channel """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "tell"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        try:
            await ctx.message.delete()
        except Exception as e:
            await generic.send(generic.gls(locale, "message_del_error", [e]), ctx.channel, delete_after=5)
        if channel.guild != ctx.guild:
            return await generic.send(generic.gls(locale, "tell_guild_diff", [ctx.guild.name, channel.guild.name]), ctx.channel)
        try:
            await generic.send(message, channel, u=True, r=True)
        except Exception as e:
            return await generic.send(generic.gls(locale, "message_send_error", [e]), ctx.channel)
        return await generic.send(generic.gls(locale, "tell_successful", [channel.mention]), ctx.channel, delete_after=5)

    @commands.command(name="atell")
    @commands.is_owner()
    async def admin_tell(self, ctx: commands.Context, channel_id: int, *, message: str):
        """ Say something to a channel """
        locale = generic.get_lang(ctx.guild)
        channel = self.bot.get_channel(channel_id)
        try:
            await ctx.message.delete()
        except Exception as e:
            await generic.send(generic.gls(locale, "message_del_error", [e]), ctx.channel, delete_after=5)
        try:
            await generic.send(message, channel, u=True, r=True)
        except Exception as e:
            return await generic.send(generic.gls(locale, "message_send_error", [e]), ctx.channel)
        return await generic.send(generic.gls(locale, "tell_successful", [channel.mention]), ctx.channel, delete_after=5)

    @commands.command(name="say")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def say(self, ctx: commands.Context, *, message: str):
        """ Make me speak! """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "say"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        try:
            await ctx.message.delete()
        except Exception as e:
            await generic.send(generic.gls(locale, "message_del_error", [e]), ctx.channel, delete_after=5)
        await generic.send(f"**{ctx.author}:**\n{message}", ctx.channel)
        return await generic.send(generic.gls(locale, "say_successful"), ctx.channel, delete_after=5)

    @commands.command(name="tellimg")
    @commands.guild_only()
    @permissions.has_permissions(manage_messages=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def tell_image(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str = ""):
        """ Send an image to a channel """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "tellimg"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        if len(ctx.message.attachments) == 1:
            url = ctx.message.attachments[0].url
            fn = ctx.message.attachments[0].filename
            spoiler = ctx.message.attachments[0].is_spoiler()
        else:
            return await generic.send(generic.gls(locale, "tell_image_none", [ctx.prefix]), ctx.channel)
        bio = BytesIO(await http.get(url, res_method="read"))
        try:
            await ctx.message.delete()
        except Exception as e:
            await generic.send(generic.gls(locale, "message_del_error", [e]), ctx.channel, delete_after=5)
        if channel.guild != ctx.guild:
            return await generic.send(generic.gls(locale, "tell_guild_diff", [ctx.guild.name, channel.guild.name]), ctx.channel)
        try:
            await generic.send(message, ctx.channel, file=discord.File(bio, filename=fn, spoiler=spoiler), u=True, r=True)
        except Exception as e:
            return await generic.send(generic.gls(locale, "message_send_error", [e]), ctx.channel)
        return await generic.send(generic.gls(locale, "tell_successful", [channel.mention]), ctx.channel, delete_after=5)

    @commands.command(name="tellembed")
    @commands.guild_only()
    @permissions.has_permissions(manage_messages=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def tell_embed(self, ctx: commands.Context, channel: discord.TextChannel, embed_colour: str, thumbnail_url: str,
                         *, message: str):
        """ Say something with an embed

         Put "none" as thumbnail_url to not use one """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "tellembed"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        if embed_colour == "random":
            colour = random.randint(0, 0xffffff)
            a = 6
        else:
            try:
                colour = int(embed_colour, base=16)
                a = len(embed_colour)
                if a != 3 and a != 6:
                    return await generic.send(generic.gls(locale, "colour_value_len"), ctx.channel)
            except Exception as e:
                return await generic.send(generic.gls(locale, "colour_invalid", [e]), ctx.channel)
        if a == 3:
            d, e, f = embed_colour
            colour = int(f"{d}{d}{e}{e}{f}{f}", base=16)
        embed = discord.Embed(colour=colour, description=message)
        if thumbnail_url.lower() != "none":
            embed.set_thumbnail(url=thumbnail_url.lower())
        try:
            await ctx.message.delete()
        except Exception as e:
            await generic.send(generic.gls(locale, "message_del_error", [e]), ctx.channel, delete_after=5)
        if channel.guild != ctx.guild:
            return await generic.send(generic.gls(locale, "tell_guild_diff", [ctx.guild.name, channel.guild.name]), ctx.channel)
        try:
            await generic.send(None, channel, embed=embed, u=True, r=True)
        except Exception as e:
            return await generic.send(generic.gls(locale, "message_send_error", [e]), ctx.channel)
        return await generic.send(generic.gls(locale, "tell_successful", [channel.mention]), ctx.channel, delete_after=5)


def setup(bot):
    bot.add_cog(Speech(bot))
