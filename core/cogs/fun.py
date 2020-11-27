import asyncio
import random

import discord
from discord.ext import commands

from core.utils import emotes, general, lists, permissions, time
from languages import langs


class Entertainment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="vote", aliases=["petition"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def vote(self, ctx: commands.Context, *, question: str):
        """ Start a vote """
        locale = langs.gl(ctx)
        message = await general.send(langs.gls("fun_vote", locale, ctx.author.name, langs.gls(f"fun_vote_{str(ctx.invoked_with).lower()}", locale), question),
                                     ctx.channel)
        await message.add_reaction(emotes.Allow)
        await message.add_reaction(emotes.Meh)
        await message.add_reaction(emotes.Deny)

    @commands.command(name="vibecheck")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def vibe_check(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Check your vibe """
        locale = langs.gl(ctx)
        user = who or ctx.author
        message = await general.send(langs.gls("fun_vibe_begin", locale, user.name), ctx.channel)
        await asyncio.sleep(3)
        responses = [langs.gls("fun_vibe_fail", locale, user.name), langs.gls("fun_vibe_pass", locale, user.name)]
        return await message.edit(content=responses[1] if user.id == 302851022790066185 else random.choice(responses))

    @commands.command(name="flip", aliases=["coin"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def flip_a_coin(self, ctx: commands.Context):
        """ Flip a coin """
        locale = langs.gl(ctx)
        return await general.send(langs.gls("fun_coin_main", locale, langs.gls(f"fun_coin_{random.choice(['heads', 'tails'])}", locale)), ctx.channel)

    @commands.command(name="beer")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def beer(self, ctx: commands.Context, user: discord.Member = None, *, reason: str = ""):
        """ Give someone a beer! 🍻 """
        locale = langs.gl(ctx)
        if not user or user.id == ctx.author.id:
            async with ctx.typing():
                return await general.send(langs.gls("fun_beer_self", locale, ctx.author.name), ctx.channel, file=discord.File("assets/party.gif", "party.gif"))
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("fun_beer_me", locale), ctx.channel)
        if user.bot:
            return await general.send(langs.gls("fun_beer_bot", locale), ctx.channel)
        reason = langs.gls("fun_beer_reason", locale, reason)
        beer_offer = langs.gls("fun_beer_offer", locale, user.name, ctx.author.name)
        if reason:
            beer_offer += reason
        msg = await general.send(beer_offer, ctx.channel)
        try:
            def reaction_check(m):
                if m.message_id == msg.id and m.user_id == user.id and str(m.emoji) == "🍻":
                    return True
                return False
            await msg.add_reaction("🍻")
            await self.bot.wait_for('raw_reaction_add', timeout=30.0, check=reaction_check)
            return await general.send(langs.gls("fun_beer_success", locale, user.name, ctx.author.name), ctx.channel)
        except asyncio.TimeoutError:
            await msg.delete()
            return await general.send(langs.gls("fun_beer_timeout", locale, user.name, ctx.author.name), ctx.channel)
        except discord.Forbidden:
            beer = langs.gls("fun_beer_no_react", locale, user.name, ctx.author.name)
            if reason:
                beer += reason
            return await msg.edit(content=beer)

    @commands.command(name="8ball", aliases=["eightball"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def eight_ball(self, ctx: commands.Context, *, question: str):
        """ Consult the 8-Ball """
        locale = langs.gl(ctx)
        return await general.send(langs.gls("fun_8ball", locale, ctx.author.name, question, random.choice(langs.get_data("fun_8ball_responses", locale))),
                                  ctx.channel)

    @commands.command(name="roll")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def roll(self, ctx: commands.Context, num1: int = 6, num2: int = 1):
        """ Rolls a number between given range """
        locale = langs.gl(ctx)
        if num1 > num2:
            v1, v2 = [num2, num1]
        else:
            v1, v2 = [num1, num2]
        r = random.randint(v1, v2)
        n1, n2, no = langs.gns(v1, locale), langs.gns(v2, locale), langs.gns(r, locale)
        return await general.send(langs.gls("fun_roll", locale, ctx.author.name, n1, n2, no), ctx.channel)

    @commands.command(name="f")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def pay_respects(self, ctx: commands.Context, *, text: str = None):
        """ Press F to pay respects """
        locale = langs.gl(ctx)
        heart = random.choice(lists.hearts)
        return await general.send(langs.gls("fun_f_none" if text is None else "fun_f_text", locale, ctx.author.name, heart, text), ctx.channel)

    @commands.command(name="quote")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def quote(self, ctx: commands.Context, user: discord.User, *, text: str):
        """ Make a very true quote """
        locale = langs.gl(ctx)
        embed = discord.Embed(colour=random.randint(0, 0xffffff))
        embed.set_thumbnail(url=user.avatar_url)
        embed.title = langs.gls("fun_quote_begin", locale, user)
        embed.description = text
        embed.set_footer(text=langs.gls("fun_quote_author", locale, ctx.author))
        embed.timestamp = time.now(None)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="reverse")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def reverse_text(self, ctx: commands.Context, *, text: str):
        """ Reverses text """
        reverse = text[::-1].replace("@", "@\u200B").replace("&", "&\u200B")
        return await general.send(f"🔁 {ctx.author.name}:\n{reverse}", ctx.channel)

    @commands.command(name="dm")
    @commands.check(permissions.is_owner)
    async def dm(self, ctx: commands.Context, user_id: int, *, message: str):
        """ DM a user """
        try:
            await ctx.message.delete()
        except Exception as e:
            await general.send(f"Message deletion failed: `{type(e).__name__}: {e}`", ctx.channel, delete_after=5)
        user = self.bot.get_user(user_id)
        if not user:
            return await general.send(f"Could not find a user with ID {user_id}", ctx.channel)
        try:
            await user.send(message)
            return await general.send(f"✉ Sent DM to {user}", ctx.channel, delete_after=5)
        except discord.Forbidden:
            return await general.send(f"Failed to send DM - the user might have blocked DMs, or be a bot.", ctx.channel)

    @commands.command(name="tell")
    @commands.guild_only()
    @permissions.has_permissions(manage_messages=True)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def tell(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str):
        """ Say something to a channel """
        locale = langs.gl(ctx)
        try:
            await ctx.message.delete()
        except Exception as e:
            await general.send(langs.gls("fun_say_delete_fail", locale, type(e).__name__, str(e)), ctx.channel, delete_after=5)
        if channel.guild != ctx.guild:
            return await general.send(langs.gls("fun_tell_guilds", locale), ctx.channel)
        try:
            await general.send(message, channel, u=True, r=True)
        except Exception as e:
            return await general.send(langs.gls("fun_tell_fail", locale, type(e).__name__, str(e)), ctx.channel)
        return await general.send(langs.gls("fun_tell_success", locale, channel.mention), ctx.channel, delete_after=5)

    @commands.command(name="atell")
    @commands.check(permissions.is_owner)
    async def admin_tell(self, ctx: commands.Context, channel_id: int, *, message: str):
        """ Say something to a channel """
        channel = self.bot.get_channel(channel_id)
        try:
            await ctx.message.delete()
        except Exception as e:
            await general.send(f"Message deletion failed: `{type(e).__name__}: {e}`", ctx.channel, delete_after=5)
        try:
            await general.send(message, channel, u=True, r=True)
        except Exception as e:
            return await general.send(f"{emotes.Deny} Failed to send the message: `{type(e).__name__}: {e}`", ctx.channel)
        return await general.send(f"{emotes.Allow} Successfully sent the message to {channel.mention}", ctx.channel, delete_after=5)

    @commands.command(name="say")
    @commands.check(lambda ctx: not (ctx.author.id == 667187968145883146 and ctx.guild.id == 568148147457490954))
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def say(self, ctx: commands.Context, *, message: str):
        """ Make me speak! """
        locale = langs.gl(ctx)
        try:
            await ctx.message.delete()
        except Exception as e:
            await general.send(langs.gls("fun_say_delete_fail", locale, type(e).__name__, str(e)), ctx.channel, delete_after=5)
        await general.send(f"**{ctx.author}:**\n{message}", ctx.channel)
        return await general.send(langs.gls("fun_say_success", locale), ctx.channel, delete_after=5)


def setup(bot):
    bot.add_cog(Entertainment(bot))
