import random

import discord
from discord import app_commands

from utils import bot_data, commands, lists, views
from utils.general import username


class Entertainment(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.hybrid_command(name="hotchocolate", aliases=["hc"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.rename(user="member")
    @app_commands.describe(user="The member with whom you want to share a hot chocolate", reason="(Optional) The reason why you want to share a hot chocolate")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def hot_chocolate(self, ctx: commands.Context, user: discord.Member = None, *, reason: str = ""):
        """ Give someone a hot chocolate! ☕🍫 """
        language = self.bot.language(ctx)
        if not user or user.id == ctx.author.id:
            async with ctx.typing(ephemeral=True):
                return await ctx.send(language.string("fun_hc_self", author=username(ctx.author)), file=discord.File("assets/hc.gif", "chocolate.gif"), ephemeral=True)
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("fun_hc_me"), ephemeral=True)
        if user.bot:
            return await ctx.send(language.string("fun_hc_bot"), ephemeral=True)
        offer = language.string("fun_beer_offer", target=language.case(username(user), "nominative"), author=language.case(username(ctx.author), "with"), emote="☕🍫")
        if reason:
            offer += language.string("fun_beer_reason", reason=reason)
        message = await ctx.send(offer, ephemeral=False)
        return await message.edit(view=views.DrinkView(ctx.author, user, message, ctx, language,
                                                       button_emoji="☕", output_emoji="☕🍫", success_text="fun_hc_success", decline_text="fun_hc_declined", timeout_text="fun_hc_timeout"))

    @commands.hybrid_command(name="8ball", aliases=["eightball"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @app_commands.describe(question="The question to ask the 8-ball")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def eight_ball(self, ctx: commands.Context, *, question: str):
        """ Consult the 8-Ball """
        language = self.bot.language(ctx)
        return await ctx.send(language.string("fun_8ball", name=username(ctx.author), question=question, answer=random.choice(language.data("fun_8ball_responses"))), ephemeral=True)

    @commands.hybrid_command(name="f")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @app_commands.describe(text="(Optional) Specify what you are paying respects for")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def pay_respects(self, ctx: commands.Context, *, text: str = None):
        """ Press F to pay respects """
        language = self.bot.language(ctx)
        heart = random.choice(lists.hearts)
        return await ctx.send(language.string("fun_f_none" if text is None else "fun_f_text", name=username(ctx.author), heart=heart, text=text), ephemeral=True)

    @commands.hybrid_command(name="coin", aliases=["flip", "coinflip"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def flip_a_coin(self, ctx: commands.Context):
        """ Flip a coin """
        language = self.bot.language(ctx)
        return await ctx.send(language.string("fun_coin_main", result=language.string(f"fun_coin_{random.choice(['heads', 'tails'])}")), ephemeral=True)


class EntertainmentSuager(Entertainment, name="Entertainment"):
    @commands.hybrid_command(name="beer")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.rename(user="member")
    @app_commands.describe(user="The member with whom you want to share a beer", reason="(Optional) The reason why you want to share a beer")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def beer(self, ctx: commands.Context, user: discord.Member = None, *, reason: str = ""):
        """ Give someone a beer! 🍻 """
        language = self.bot.language(ctx)
        if not user or user.id == ctx.author.id:
            async with ctx.typing(ephemeral=True):
                return await ctx.send(language.string("fun_beer_self", author=username(ctx.author)), file=discord.File("assets/party.gif", "party.gif"), ephemeral=True)
        if user.id == self.bot.user.id:
            return await ctx.send(language.string("fun_beer_me"), ephemeral=True)
        if user.bot:
            return await ctx.send(language.string("fun_beer_bot"), ephemeral=True)
        offer = language.string("fun_beer_offer", target=language.case(username(user), "nominative"), author=language.case(username(ctx.author), "with"), emote="🍺")
        if reason:
            offer += language.string("fun_beer_reason", reason=reason)
        message = await ctx.send(offer, ephemeral=False)
        return await message.edit(view=views.DrinkView(ctx.author, user, message, ctx, language,
                                                       button_emoji="🍻", output_emoji="🍺", success_text="fun_beer_success", decline_text="fun_beer_declined", timeout_text="fun_beer_timeout"))


async def setup(bot: bot_data.Bot):
    if bot.name == "suager":
        await bot.add_cog(EntertainmentSuager(bot))
    else:
        await bot.add_cog(Entertainment(bot))
