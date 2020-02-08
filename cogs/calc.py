import asyncio
import random

from discord.ext import commands

from utils import time, emotes
import time as _time


class Calculations(commands.Cog):
    @commands.command(name="add")
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def addition(self, ctx, num1: int, num2: int):
        """ Add 2 integers """
        if num1 > 200 or num2 > 200:
            return await ctx.send(f"I'm afraid of such huge numbers... {emotes.NotLikeThis}")
        if num1 < 0 or num2 < 0:
            return await ctx.send("Wait. That's illegal")
        ot = time.now()
        text = f"{emotes.Loading} Sorry, Python takes a while to compute..."
        message = await ctx.send(text)
        s = _time.time()
        c = num1 + num2
        for i in range(int(c / 2.5)):
            await asyncio.sleep(2.5)
            p = (i + 1) * 2.5 / c * 100
            await message.edit(content=f"{text} ({p:.1f}%)")
        f = _time.time()
        d = int(round(f - s))
        b = random.choice([True, False])
        if b:
            d += int(random.random() * num1**0.5 * num2 ** 0.7)
        od = time.human_timedelta(ot, suffix=False)
        return await message.edit(content=f"{num1} + {num2} = {d:,}\nThis took {od} to calculate")

    @commands.command(name="multiply")
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def multiplication(self, ctx, num1: int, num2: int):
        """ Add 2 integers """
        if num1 > 1000 or num2 > 1000:
            return await ctx.send(f"I'm afraid of such huge numbers... {emotes.NotLikeThis}")
        if num1 < 0 or num2 < 0:
            return await ctx.send("Negative numbers don't exist.")
        ot = time.now()
        text = f"{emotes.Loading} BRB, using a 1729-dimensional Fourier transform..."
        message = await ctx.send(text)
        s = _time.time()
        t1, t2 = [num1 if num1 < 100 else 100, num2 if num2 < 100 else 100]
        c = t1 + t2
        for i in range(int(c / 2.5)):
            await asyncio.sleep(2.5)
            p = (i + 1) * 2.5 / c * 100
            await message.edit(content=f"{text} ({p:.1f}%)")
        f = _time.time()
        d = int(round(f - s))
        b = random.choice([True, False])
        if b:
            d += int(random.random() * num1**0.25 * num2 ** 0.7)
        od = time.human_timedelta(ot, suffix=False)
        result = int(d + t1 + t2 + num1 * num2)
        return await message.edit(content=f"{num1} x {num2} = {result:,}\nThis took {od} to calculate")

    @commands.command(name="divide")
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def division(self, ctx, num1: int, num2: int):
        """ Add 2 integers """
        if num2 == 0:
            z = f"**Oh no! {ctx.author.name}, what have you done?!**"
            return await ctx.send(z.upper())
        if num1 > 1000 or num2 > 1000:
            return await ctx.send(f"I'm afraid of such huge numbers... {emotes.NotLikeThis}")
        if num1 < 0 or num2 < 0:
            return await ctx.send(f"I can't do that, because Bowser65 is extremely "
                                  f"disappointed in me :( {emotes.AlexHeartBroken}")
        ot = time.now()
        text = f"{emotes.Loading} Getting Bowser65 extremely disappointed in me..."
        message = await ctx.send(text)
        s = _time.time()
        t1, t2 = [num1 if num1 < 100 else 100, num2 if num2 < 100 else 100]
        c = t1 + t2
        for i in range(int(c / 2.5)):
            await asyncio.sleep(2.5)
            p = (i + 1) * 2.5 / c * 100
            await message.edit(content=f"{text} ({p:.1f}%)")
        f = _time.time()
        d = int(round(f - s))
        b = random.choice([True, False])
        if b:
            d += int(random.random() * num1**0.25 * num2 ** 0.7)
        od = time.human_timedelta(ot, suffix=False)
        why = d / (t1 * t2) ** 0.7
        result = round(why + num1 / num2, 2)
        return await message.edit(content=f"{num1} / {num2} = {result:,}\nThis took {od} to calculate")

    @commands.command(name="subtract")
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def subtraction(self, ctx, num1: int, num2: int):
        """ Add 2 integers """
        if num1 > 200 or num2 > 200:
            return await ctx.send(f"I'm afraid of such huge numbers... {emotes.NotLikeThis}")
        if num1 < 0 or num2 < 0:
            return await ctx.send("Nice try, but I am no deviant.")
        ot = time.now()
        text = f"{emotes.Loading} Contemplating life..."
        message = await ctx.send(text)
        s = _time.time()
        c = num1 + num2
        for i in range(int(c / 2.5)):
            await asyncio.sleep(2.5)
            p = (i + 1) * 2.5 / c * 100
            await message.edit(content=f"{text} ({p:.1f}%)")
        f = _time.time()
        d = int(round(f - s))
        b = random.choice([True, False])
        if b:
            d += int(random.random() * num1**0.25 * num2 ** 0.7)
        od = time.human_timedelta(ot, suffix=False)
        result = num1 - num2 + int(d ** 0.25 - 3)
        illegal = result < 0
        val = "illegal" if illegal else f"{result:,}"
        extra = "\nRegaus taught me that negative numbers don't exist. Therefore, they don't. " \
                "Your attempts at convincing me otherwise are very, very bad and inefficient." if illegal else ''
        return await message.edit(content=f"{num1} - {num2} = {val}\nThis took {od} to calculate{extra}")


def setup(bot):
    bot.add_cog(Calculations(bot))
