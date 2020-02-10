import asyncio
import random

import discord
from discord.ext import commands

from utils import generic, emotes, bias


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="rate")
    async def rate(self, ctx, *, what: commands.clean_content):
        """ Rate something """
        r = random.randint(0, 1000) / 10
        bad = ["xela", "lidl xela"]
        if str(what).lower() in bad:  # xelA is a meanie, and meanies don't deserve love mmlol
            r = 0.0                   # I don't like LIDL xelA, so it ain't getting any love either
        return await ctx.send(f"I'd rate {what} a {r}/100")

    @commands.command(name="rateuser")
    @commands.guild_only()
    async def rate_user(self, ctx, who: discord.Member):
        """ Rate someone """
        random.seed(who.id)
        r1, r2 = [800, 1000]
        if who.id == ctx.author.id:
            return await ctx.send(f"{ctx.author.mention} I like you the way you are! {emotes.AlexPat}")
        r = random.randint(r1, r2) / 10
        if ctx.guild.id == 568148147457490954:
            if ctx.guild.get_role(660880373894610945) in who.roles:
                r /= 2
        return await ctx.send(f"I'd rate {who} a {r}/100")

    @commands.command(name="pingspam", hidden=True)
    @commands.guild_only()
    @commands.is_owner()
    async def ping_spam(self, ctx, who: discord.Member, times: int, *, message: str = None):
        """ Ping Spam """
        if who.id == 302851022790066185:
            return await ctx.send("Nah, not Regaus. :^)")
        if ctx.channel.id != 674338147689168897:
            return await ctx.send("Nah, <#674338147689168897> only.")
        if times > 15000:
            return await ctx.send("Nah, only up to 15k.")
        add = f"\nMessage from {ctx.author.name}: {message}" if message is not None else ''
        try:
            for i in range(1, times+1):
                await ctx.send(f"{who.mention} - Get pinged! ({i}/{times}){add}")
        except Exception as e:
            return await ctx.send(f"An error has occurred... {e}")
        return await ctx.send(f"{ctx.author.mention} - I'm done torturing {who.name}, you motherfucker")

    @commands.command(name="babyrate")
    @commands.guild_only()
    async def baby_rate(self, ctx, user1: discord.Member, user2: discord.Member):
        """ Chance of 2 users having a baby """
        seed = user1.id + user2.id
        random.seed(seed)
        rate = random.randint(0, 100)
        embed = discord.Embed(colour=generic.random_colour(),
                              description=f"The chance of {user1.mention} and {user2.mention} "
                                          f"having a baby is **{rate}**%")
        return await ctx.send(embed=embed)

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
    async def vibe_check(self, ctx):
        """ Check your vibe """
        message = await ctx.send(f"<a:loading:651883385878478858> Checking {ctx.author.name}'s vibe...")
        await asyncio.sleep(3)
        return await message.edit(content=f"**{ctx.author.name}** {random.choice(['failed', 'passed'])} the vibe check")

    @commands.command(name="flip", aliases=["coin"])
    async def flip_a_coin(self, ctx):
        """ Flip a coin """
        message = await ctx.send("<a:loading:651883385878478858> Flipping a coin...")
        await asyncio.sleep(3)
        return await message.edit(content=f"The coin landed on {random.choice(['Heads', 'Tails'])}")

    @commands.command(name="bean")
    async def bean(self, ctx, user: discord.Member = None):
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

    @commands.command(name="hotcalc", aliases=["hotness"])
    async def hotness(self, ctx, user: discord.Member = None):
        """ Check how hot someone is """
        user = user or ctx.author
        is_me = user.id in generic.get_config().owners
        random.seed(user.id)
        step1 = int(round(random.random() * 100))
        step2 = int(round(random.random() * 20))
        step3 = step1 / (107 + step2) * 100
        step4 = bias.friend_bias(self.bot, user)
        step5 = step3 * step4
        step6 = 100 if step5 > 100 else step5
        if 0 < step6 < 33:
            emote = "<:sadcat:620306629124161536>"
        elif 33 <= step6 < 67:
            emote = "<:lul:568168505543753759>"
        else:
            emote = "<:pog:610583684663345192>"
        message = await ctx.send(f"{emotes.Loading} Checking how hot {user.name} is...")
        await asyncio.sleep(3)
        return await message.edit(content=f"**{user.name}** is **{step6:.2f}%** hot {emote}")


def setup(bot):
    bot.add_cog(Fun(bot))
