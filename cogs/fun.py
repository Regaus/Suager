import asyncio
import random

import discord
from discord.ext import commands

from utils import lists, time


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="vote", aliases=["petition"])
    async def vote(self, ctx, *, question: commands.clean_content):
        """ Start a vote """
        message = await ctx.send(f"A {ctx.invoked_with.lower()} has been started by {ctx.author} ```fix\n{question}```")
        await message.add_reaction("<:allow:610828713424191498>")
        await message.add_reaction("<:meh:610828713315139623>")
        await message.add_reaction("<:deny:610828713533112350>")

    @commands.command(name="shrug")
    async def shrug(self, ctx):
        """ ¯\u005C_(ツ)_/¯ """
        await ctx.send("¯\u005C\u005C_(ツ)\u005C_/¯")

    @commands.command(name="epic")
    async def epic(self, ctx):
        """ Very epic """
        await ctx.send("<a:epic:603691073822261248>")

    @commands.command(name="vibecheck")
    async def vibe_check(self, ctx, *, who: discord.Member = None):
        """ Check your vibe """
        user = who or ctx.author
        message = await ctx.send(f"<a:loading:651883385878478858> Checking {user.name}'s vibe...")
        await asyncio.sleep(3)
        return await message.edit(content=f"**{user.name}** {random.choice(['failed', 'passed'])} the vibe check")

    @commands.command(name="flip", aliases=["coin"])
    async def flip_a_coin(self, ctx):
        """ Flip a coin """
        message = await ctx.send("<a:loading:651883385878478858> Flipping a coin...")
        await asyncio.sleep(3)
        return await message.edit(content=f"The coin landed on {random.choice(['Heads', 'Tails'])}")

    @commands.command(name="bean")
    async def bean(self, ctx, *, user: discord.Member = None):
        """ Beans a user from the current server """
        user = user or "the user"
        return await ctx.send(f"<:newjesus:579796865038548993> Successfully beaned {user} <a:licc:579413180200124436>")

    @commands.command()
    async def beer(self, ctx, user: discord.Member = None, *, reason: commands.clean_content = ""):
        """ Give someone a beer! 🍻 """
        if not user or user.id == ctx.author.id:
            with ctx.typing():
                # bio = io.StringIO("Image is currently broken, try again later...")
                return await ctx.send(f"**{ctx.author.name}**: paaaarty!🎉🍺",
                                      file=discord.File("assets/drunk.gif", filename="party.gif"))
            # await ctx.send(f"**{ctx.author.name}: Party!**", file=discord.File(bio, filename="partay.gif"))
        if user.id == self.bot.user.id:
            return await ctx.send("*drinks beer with you* 🍻")
        if user.bot:
            return await ctx.send(f"I would love to give beer to the bot **{ctx.author.name}**, but I don't think it "
                                  f"will respond to you :/")

        beer_offer = f"**{user.name}**, you got a 🍺 offer from **{ctx.author.name}**"
        beer_offer = beer_offer + f"\n\n**Reason:** {reason}" if reason else beer_offer
        msg = await ctx.send(beer_offer)

        def reaction_check(m):
            if m.message_id == msg.id and m.user_id == user.id and str(m.emoji) == "🍻":
                return True
            return False

        try:
            await msg.add_reaction("🍻")
            await self.bot.wait_for('raw_reaction_add', timeout=30.0, check=reaction_check)
            await msg.edit(content=f"**{user.name}** and **{ctx.author.name}** are enjoying a lovely beer together 🍻")
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.send(f"well, doesn't seem like **{user.name}** would like to have "
                           f"a beer with you **{ctx.author.name}** ;-;")
        except discord.Forbidden:
            # Yeah so, bot doesn't have reaction permission, drop the "offer" word
            beer_offer = f"**{user.name}**, you got a 🍺 from **{ctx.author.name}**"
            beer_offer = beer_offer + f"\n\n**Reason:** {reason}" if reason else beer_offer
            await msg.edit(content=beer_offer)

    @commands.command(name="8ball", aliases=["eightball"])
    async def eight_ball(self, ctx, *, question: commands.clean_content):
        """ Consult the 8-Ball """
        return await ctx.send(f"**Question:** {question}\n**Answer:** {random.choice(lists.ball_response)}")

    @commands.command(name="satan", aliases=["demons"])
    async def demons(self, ctx, *, question: commands.clean_content):
        """ Consult Satan """
        return await ctx.send(f"**Question:** {question}\n**Answer:** {random.choice(lists.demons_response)}")

    @commands.command(name="stackoverflow")
    async def stack_overflow(self, ctx, *, question: commands.clean_content):
        """ Consult Stack Overflow"""
        return await ctx.send(f"**Question:** {question}\n**Answer:** This is a stupid question.")

    @commands.command(name="roll")
    async def roll(self, ctx, num1: int = 6, num2: int = 1, repeat: int = 1):
        """ Rolls a number between given range """
        if repeat <= 0:
            return await ctx.send("How are I supposed to do that?")
        if repeat > 50:
            return await ctx.send("But why?")
        n1, n2 = [-(10**12), 10**12]
        if num1 > n2 or num2 > n2 or num1 < n1 or num2 < n1:
            return await ctx.send("Why do you need such large values?")
        res = []
        if num1 > num2:
            v1, v2 = [num2, num1]
        else:
            v1, v2 = [num1, num2]
        for i in range(repeat):
            r = random.randint(v1, v2)
            s = f"{r:,}"
            res.append(s)
        multiple = len(res) != 1
        output = res if not multiple else ', '.join(res)
        p = 's' if multiple else ''
        out = output if not multiple else f"```fix\n{output}```"
        return await ctx.send(f"**{ctx.author.name}** rolled **{v1:,}-{v2:,}** ({repeat} time{p} and got this: {out}")

    @commands.command(name="f")
    async def pay_respects(self, ctx, *, text: commands.clean_content = None):
        """ Press F to pay respects """
        heart = random.choice(lists.hearts)
        if text is None:
            return await ctx.send(f"**{ctx.author.name}** has paid their respects {heart}")
        return await ctx.send(f"**{ctx.author.name}** has paid their respects for **{text}** {heart}")

    @commands.command(name="toast")
    async def toast(self, ctx, *, user: discord.Member = None):
        """ Toast someone """
        if user is None:
            user = ctx.author
        return await ctx.send(f"*{user} is now a toast.*")

    @commands.command(name="quote")
    @commands.guild_only()
    async def quote(self, ctx, user: discord.Member, *, text: str):
        """ Make a very true quote """
        embed = discord.Embed(colour=random.randint(0, 0xffffff))
        embed.set_thumbnail(url=user.avatar_url)
        embed.title = f"**{user}** once said..."
        embed.description = text
        embed.set_footer(text=f"Quote author: {ctx.author}")
        embed.timestamp = time.now(True)
        return await ctx.send(embed=embed)

    @commands.command(name="reverse")
    async def reverse_text(self, ctx, *, text: commands.clean_content):
        """ Reverses text """
        reverse = text[::-1].replace("@", "@\u200B").replace("&", "&\u200B")
        return await ctx.send(reverse)

    @commands.command(name="yeet")
    @commands.is_owner()
    async def yeet(self, ctx, user: discord.Member, *, reason: str):
        """ Yeet someone """
        return await ctx.send(f"{user.name} has been yeeted off the bridge for {reason}")


def setup(bot):
    bot.add_cog(Fun(bot))
