import asyncio
import random

import discord
from discord.ext import commands

from utils import lists, time, emotes, generic


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="vote", aliases=["petition"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def vote(self, ctx: commands.Context, *, question: str):
        """ Start a vote """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "vote"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        a = 1 if ctx.invoked_with.lower() == "vote" else 2
        message = await generic.send(generic.gls(locale, "vote", [generic.gls(locale, f"vote{a}"), ctx.author, question]), ctx.channel)
        await message.add_reaction(emotes.Allow)
        await message.add_reaction(emotes.Meh)
        await message.add_reaction(emotes.Deny)

    @commands.command(name="epic")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def epic(self, ctx: commands.Context):
        """ Very epic """
        return await generic.send(emotes.Epic, ctx.channel)

    @commands.command(name="vibecheck")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def vibe_check(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Check your vibe """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "vibecheck"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        user = who or ctx.author
        message = await generic.send(generic.gls(locale, "vibe_check1", [user.name]), ctx.channel)
        await asyncio.sleep(3)
        if user.id == 302851022790066185:
            r = 2
        else:
            r = random.randint(1, 2)
        return await message.edit(content=generic.gls(locale, "vibe_check2", [generic.gls(locale, f"vibe_check{r + 2}")]))

    @commands.command(name="flip", aliases=["coin"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def flip_a_coin(self, ctx: commands.Context):
        """ Flip a coin """
        locale = generic.get_lang(ctx.guild)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        return await generic.send(generic.gls(locale, "coin_flip", [random.choice([generic.gls(locale, f"coin_flip{i}") for i in [1, 2]])]), ctx.channel)

    @commands.command()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def beer(self, ctx: commands.Context, user: discord.Member = None, *, reason: str = ""):
        """ Give someone a beer! 🍻 """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "beer"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if not user or user.id == ctx.author.id:
            async with ctx.typing():
                return await generic.send(generic.gls(locale, "beer_self", [ctx.author.name]), ctx.channel, file=discord.File("assets/party.gif", "party.gif"))
        if user.id == self.bot.user.id:
            return await generic.send(generic.gls(locale, "beer_me"), ctx.channel)
        if user.bot:
            return await generic.send(generic.gls(locale, "beer_bot", [user.name]), ctx.channel)
        beer_offer = generic.gls(locale, "beer_offer1", [user.name, ctx.author.name])
        if reason:
            beer_offer += generic.gls(locale, "beer_offer2", [reason])
        msg = await generic.send(beer_offer, ctx.channel)

        def reaction_check(m):
            if m.message_id == msg.id and m.user_id == user.id and str(m.emoji) == "🍻":
                return True
            return False
        try:
            await msg.add_reaction("🍻")
            await self.bot.wait_for('raw_reaction_add', timeout=30.0, check=reaction_check)
            return await msg.edit(content=generic.gls(locale, "beer_success", [user.name, ctx.author.name]))
        except asyncio.TimeoutError:
            await msg.delete()
            return await generic.send(generic.gls(locale, "beer_timeout", [user.name, ctx.author]), ctx.channel)
        except discord.Forbidden:
            beer = generic.gls(locale, "beer_offer3", [user.name, ctx.author.name])
            if reason:
                beer += generic.gls(locale, "beer_offer2", [reason])
            return await msg.edit(content=beer)

    @commands.command(name="8ball", aliases=["eightball"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def eight_ball(self, ctx: commands.Context, *, question: commands.clean_content):
        """ Consult the 8-Ball """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "8ball"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        return await generic.send(generic.gls(locale, "8ball", [question, random.choice(lists.ball_response)]), ctx.channel)

    @commands.command(name="roll")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def roll(self, ctx: commands.Context, num1: int = 6, num2: int = 1):
        """ Rolls a number between given range """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "roll"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        if num1 > num2:
            v1, v2 = [num2, num1]
        else:
            v1, v2 = [num1, num2]
        r = random.randint(v1, v2)
        s = f"{r:,}"
        return await generic.send(generic.gls(locale, "roll", [ctx.author.name, f"{v1:,}", f"{v2:,}", s]), ctx.channel)

    @commands.command(name="f")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def pay_respects(self, ctx: commands.Context, *, text: str = None):
        """ Press F to pay respects """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "f"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        heart = random.choice(lists.hearts)
        if text is None:
            return await generic.send(generic.gls(locale, "respects1", [ctx.author.name, heart]), ctx.channel)
        return await generic.send(generic.gls(locale, "respects2", [ctx.author.name, text, heart]), ctx.channel)

    @commands.command(name="quote")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def quote(self, ctx: commands.Context, user: discord.Member, *, text: str):
        """ Make a very true quote """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "quote"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        embed = discord.Embed(colour=random.randint(0, 0xffffff))
        embed.set_thumbnail(url=user.avatar_url)
        embed.title = generic.gls(locale, "quote_begin", [str(user)])
        embed.description = text
        embed.set_footer(text=generic.gls(locale, "quote_author", [ctx.author]))
        embed.timestamp = time.now(False)
        return await generic.send(None, ctx.channel, embed=embed)

    @commands.command(name="reverse")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def reverse_text(self, ctx: commands.Context, *, text: str):
        """ Reverses text """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "reverse"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        reverse = text[::-1].replace("@", "@\u200B").replace("&", "&\u200B")
        return await generic.send(f"🔁 {ctx.author.name}:\n{reverse}", ctx.channel)

    @commands.command(name="notwork")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def notwork(self, ctx: commands.Context):
        """ That's not how it works you little shit """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "notwork"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        embed = discord.Embed(colour=random.randint(0, 0xffffff))
        embed.set_image(url="https://cdn.discordapp.com/attachments/577599230567383058/695424749097975808/notwork.png")
        return await generic.send(None, ctx.channel, embed=embed)


def setup(bot):
    bot.add_cog(Fun(bot))
