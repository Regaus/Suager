import asyncio
import random

import discord
from discord.ext import commands

from utils import lists, time, emotes, generic


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # self.banned = [690254056354087047, 694684764074016799]

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
        # message = await ctx.send(f"A {ctx.invoked_with.lower()} has been started by {ctx.author} ```fix\n{question}```")
        await message.add_reaction(emotes.Allow)
        await message.add_reaction(emotes.Meh)
        await message.add_reaction(emotes.Deny)

    @commands.command(name="epic")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def epic(self, ctx: commands.Context):
        """ Very epic """
        return await generic.send(emotes.Epic, ctx.channel)
        # await ctx.send("<a:epic:603691073822261248>")

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
        # message = await ctx.send(f"<a:loading:651883385878478858> Checking {user.name}'s vibe...")
        await asyncio.sleep(3)
        if user.id == 302851022790066185:
            r = 2
        else:
            r = random.randint(1, 2)
        return await message.edit(content=generic.gls(locale, "vibe_check2", [generic.gls(locale, f"vibe_check{r + 2}")]))
        # return await message.edit(content=f"**{user.name}** {random.choice(['failed', 'passed'])} the vibe check")

    @commands.command(name="flip", aliases=["coin"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def flip_a_coin(self, ctx: commands.Context):
        """ Flip a coin """
        locale = generic.get_lang(ctx.guild)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        return await generic.send(generic.gls(locale, "coin_flip", [random.choice([generic.gls(locale, f"coin_flip{i}") for i in [1, 2]])]), ctx.channel)
        # message = await ctx.send("<a:loading:651883385878478858> Flipping a coin...")
        # await asyncio.sleep(3)
        # return await message.edit(content=f"The coin landed on {random.choice(['Heads', 'Tails'])}")

    @commands.command()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def beer(self, ctx: commands.Context, user: discord.Member = None, *, reason: str = ""):
        """ Give someone a beer! 🍻 """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "beer"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        # if ctx.channel.id in generic.channel_locks:
        #     return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        if not user or user.id == ctx.author.id:
            return await generic.send(generic.gls(locale, "beer_self", [ctx.author.name]), ctx.channel)
            # with ctx.typing():
            # bio = io.StringIO("Image is currently broken, try again later...")
            # return await ctx.send(f"**{ctx.author.name}**: paaaarty!🎉🍺")
            #                     file=discord.File("assets/drunk.gif", filename="party.gif"))
            # await ctx.send(f"**{ctx.author.name}: Party!**", file=discord.File(bio, filename="partay.gif"))
        if user.id == self.bot.user.id:
            return await generic.send(generic.gls(locale, "beer_me"), ctx.channel)
            # return await ctx.send("*drinks beer with you* 🍻")
        if user.bot:
            return await generic.send(generic.gls(locale, "beer_bot", [user.name]), ctx.channel)
            # return await ctx.send(f"I would love to give beer to the bot **{ctx.author.name}**, but I don't think it "
            #                       f"will respond to you :/")
        beer_offer = generic.gls(locale, "beer_offer1", [user.name, ctx.author.name])
        if reason:
            beer_offer += generic.gls(locale, "beer_offer2", [reason])
        # beer_offer = f"**{user.name}**, you got a 🍺 offer from **{ctx.author.name}**"
        # beer_offer = beer_offer + f"\n\n**Reason:** {reason}" if reason else beer_offer
        # msg = await ctx.send(beer_offer)
        msg = await generic.send(beer_offer, ctx.channel)

        def reaction_check(m):
            if m.message_id == msg.id and m.user_id == user.id and str(m.emoji) == "🍻":
                return True
            return False

        try:
            await msg.add_reaction("🍻")
            await self.bot.wait_for('raw_reaction_add', timeout=30.0, check=reaction_check)
            return await msg.edit(content=generic.gls(locale, "beer_success", [user.name, ctx.author.name]))
            # await msg.edit(content=f"**{user.name}** and **{ctx.author.name}** are enjoying a lovely beer together 🍻")
        except asyncio.TimeoutError:
            await msg.delete()
            return await generic.send(generic.gls(locale, "beer_timeout", [user.name, ctx.author]), ctx.channel)
            # await ctx.send(f"well, doesn't seem like **{user.name}** would like to have "
            #                f"a beer with you **{ctx.author.name}** ;-;")
        except discord.Forbidden:
            # Yeah so, bot doesn't have reaction permission, drop the "offer" word
            # beer_offer = f"**{user.name}**, you got a 🍺 from **{ctx.author.name}**"
            # beer_offer = beer_offer + f"\n\n**Reason:** {reason}" if reason else beer_offer
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
        # return await ctx.send(f"**Question:** {question}\n**Answer:** {random.choice(lists.ball_response)}")

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
        # if len(output) > 1900:
        #     data = BytesIO(str(output).encode('utf-8'))
        #     return await ctx.send(f"**{ctx.author.name}** rolled **{v1:,}-{v2:,}** ({repeat} time{p}) and got this:",
        #                           file=discord.File(data, filename=f"{time.file_ts('Roll')}"))
        # return await ctx.send(f"**{ctx.author.name}** rolled **{v1:,}-{v2:,}** ({repeat} time{p}) and got this: {out}")

    @commands.command(name="f")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def pay_respects(self, ctx: commands.Context, *, text: str = None):
        """ Press F to pay respects """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "f"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        # if ctx.channel.id in generic.channel_locks:
        #     return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        heart = random.choice(lists.hearts)
        if text is None:
            return await generic.send(generic.gls(locale, "respects1", [ctx.author.name, heart]), ctx.channel)
            # return await ctx.send(f"**{ctx.author.name}** has paid their respects {heart}")
        return await generic.send(generic.gls(locale, "respects2", [ctx.author.name, text, heart]), ctx.channel)
        # return await ctx.send(f"**{ctx.author.name}** has paid their respects for **{text}** {heart}")

    @commands.command(name="quote")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def quote(self, ctx: commands.Context, user: discord.Member, *, text: str):
        """ Make a very true quote """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "quote"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        embed = discord.Embed(colour=random.randint(0, 0xffffff))
        embed.set_thumbnail(url=user.avatar_url)
        # embed.title = f"**{user}** once said..."
        embed.title = generic.gls(locale, "quote_begin", [str(user)])
        embed.description = text
        embed.set_footer(text=generic.gls(locale, "quote_author", [ctx.author]))
        # embed.set_footer(text=f"Quote author: {ctx.author}")
        embed.timestamp = time.now(False)
        return await generic.send(None, ctx.channel, embed=embed)
        # return await ctx.send(embed=embed)

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
        # return await ctx.send(f"🔁 {ctx.author.name}:\n{reverse}")

    @commands.command(name="notwork")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def notwork(self, ctx: commands.Context):
        """ That's not how it works you little shit """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "notwork"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        # if ctx.channel.id in generic.channel_locks:
        #     return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        embed = discord.Embed(colour=random.randint(0, 0xffffff))
        embed.set_image(url="https://cdn.discordapp.com/attachments/577599230567383058/695424749097975808/notwork.png")
        return await generic.send(None, ctx.channel, embed=embed)
        # return await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Fun(bot))
