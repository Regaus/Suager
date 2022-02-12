import asyncio
import random

import discord

from utils import bot_data, commands, lists


class Entertainment(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.command(name="hotchocolate", aliases=["hc"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def hot_chocolate(self, ctx: commands.Context, user: discord.Member = None, *, reason: str = ""):
        """ Give someone a hot chocolate! ☕🍫 """
        language = self.bot.language(ctx)
        if not user or user.id == ctx.author.id:
            async with ctx.typing():
                return await ctx.send(language.string("fun_hc_self", ctx.author.name), file=discord.File("assets/hc.gif", "chocolate.gif"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("fun_hc_me"))
        if user.bot:
            return await ctx.send(language.string("fun_hc_bot"))
        beer_offer = language.string("fun_beer_offer", user.name, ctx.author.name, "☕🍫")
        if reason:
            beer_offer += language.string("fun_beer_reason", reason)
        msg = await ctx.send(beer_offer)
        try:
            def reaction_check(m):
                if m.message_id == msg.id and m.user_id == user.id and str(m.emoji) == "☕":
                    return True
                return False
            await msg.add_reaction("☕")
            await self.bot.wait_for('raw_reaction_add', timeout=30.0, check=reaction_check)
            await msg.delete()
            return await ctx.send(language.string("fun_hc_success", user.name, ctx.author.name, "☕🍫"))
        except asyncio.TimeoutError:
            await msg.delete()
            return await ctx.send(language.string("fun_hc_timeout", user.name, ctx.author.name))
        except discord.Forbidden:
            beer = language.string("fun_beer_no_react", user.name, ctx.author.name, "☕🍫")
            if reason:
                beer += reason
            return await msg.edit(content=beer)

    @commands.command(name="8ball", aliases=["eightball"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def eight_ball(self, ctx: commands.Context, *, question: str):
        """ Consult the 8-Ball """
        language = self.bot.language(ctx)
        return await ctx.send(language.string("fun_8ball", ctx.author.name, question, random.choice(language.data("fun_8ball_responses"))))

    @commands.command(name="f")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def pay_respects(self, ctx: commands.Context, *, text: str = None):
        """ Press F to pay respects """
        language = self.bot.language(ctx)
        heart = random.choice(lists.hearts)
        return await ctx.send(language.string("fun_f_none" if text is None else "fun_f_text", ctx.author.name, heart, text))

    @commands.command(name="coin", aliases=["flip", "coinflip"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def flip_a_coin(self, ctx: commands.Context):
        """ Flip a coin """
        language = self.bot.language(ctx)
        return await ctx.send(language.string("fun_coin_main", language.string(f"fun_coin_{random.choice(['heads', 'tails'])}")))


class EntertainmentSuager(Entertainment, name="Entertainment"):
    @commands.command(name="beer")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def beer(self, ctx: commands.Context, user: discord.Member = None, *, reason: str = ""):
        """ Give someone a beer! 🍻 """
        language = self.bot.language(ctx)
        if not user or user.id == ctx.author.id:
            async with ctx.typing():
                return await ctx.send(language.string("fun_beer_self", ctx.author.name), file=discord.File("assets/party.gif", "party.gif"))
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("fun_beer_me"))
        if user.bot:
            return await ctx.send(language.string("fun_beer_bot"))
        beer_offer = language.string("fun_beer_offer", user.name, ctx.author.name, "🍺")
        if reason:
            beer_offer += language.string("fun_beer_reason", reason)
        msg = await ctx.send(beer_offer)
        try:
            def reaction_check(m):
                if m.message_id == msg.id and m.user_id == user.id and str(m.emoji) == "🍻":
                    return True
                return False
            await msg.add_reaction("🍻")
            await self.bot.wait_for('raw_reaction_add', timeout=30.0, check=reaction_check)
            await msg.delete()
            return await ctx.send(language.string("fun_beer_success", user.name, ctx.author.name, "🍻"))
        except asyncio.TimeoutError:
            await msg.delete()
            return await ctx.send(language.string("fun_beer_timeout", user.name, ctx.author.name))
        except discord.Forbidden:
            beer = language.string("fun_beer_no_react", user.name, ctx.author.name, "🍺")
            if reason:
                beer += reason
            return await msg.edit(content=beer)


def setup(bot: bot_data.Bot):
    if bot.name == "suager":
        bot.add_cog(EntertainmentSuager(bot))
    else:
        bot.add_cog(Entertainment(bot))
