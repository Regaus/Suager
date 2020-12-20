import asyncio
import random

import discord
from discord.ext import commands

from core.utils import general, lists
from languages import langs


class Entertainment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
        beer_offer = langs.gls("fun_beer_offer", locale, user.name, ctx.author.name)
        if reason:
            beer_offer += langs.gls("fun_beer_reason", locale, reason)
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

    @commands.command(name="f")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def pay_respects(self, ctx: commands.Context, *, text: str = None):
        """ Press F to pay respects """
        locale = langs.gl(ctx)
        heart = random.choice(lists.hearts)
        return await general.send(langs.gls("fun_f_none" if text is None else "fun_f_text", locale, ctx.author.name, heart, text), ctx.channel)


def setup(bot):
    bot.add_cog(Entertainment(bot))
