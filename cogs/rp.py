from dateutil.relativedelta import relativedelta
from discord.ext import commands

from utils import time


class RPStuff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="loungeactivity")
    @commands.guild_only()
    @commands.is_owner()
    async def lounge_activity(self, ctx):
        """ Lounge Activity """
        if ctx.guild.id != 568148147457490954:
            return await ctx.send("This command is only available in Senko Lair")
        async with ctx.typing():
            lounge_activity = ""
            channels = [[577991306723196928, "Sinners' Ranch"], [579029449211904002, "Purgatory"],
                        [655945599157403676, "Bourgeoisie Lounge"], [658112317384556544, "Kool Kids Klub"],
                        [658112535656005663, "Elite Lounge"], [660580413370269716, "Dark Street"],
                        [673190670952955905, "Nuriki Cult"], [655945823074648085, "Male Lounge"],
                        [655945962480599051, "Female Lounge"], [655946029556039690, "Invalid Lounge"],
                        [658690448478568468, "Super Secret Lounge"], [662107594151952384, "Bot Lounge"],
                        [671520521174777869, "Secret Room 1"], [672535025698209821, "Secret Room 2"]]
            for ch in channels:
                channel = self.bot.get_channel(ch[0])
                lm = await channel.history(limit=None).flatten()
                la = len(lm)
                ca = channel.created_at
                # since = time.date_time_str(ca, False, False, False)
                now = time.now(True)
                td = now - ca
                msg_per_day = round(la / (td.days * 86400 + td.seconds) * 86400, 2)
                lounge_activity += f"{ch[1]}: **{la:,} messages** (avg {msg_per_day} per day)\n"
            # ch = await self.bot.get_channel(577991306723196928)
            # lounge_activity = f"Sinners' Ranch: {len(await ch.history.flatten())}\n"
            return await ctx.send(f"Here is the lounge activity in Senko Lair:\n{lounge_activity}")

    @commands.command(name="requirement", aliases=["requiredactivity", "rla"], hidden=True)
    @commands.guild_only()
    @commands.is_owner()
    async def required_lounge_activity(self, ctx, target: int):
        """ Required Super Secret Lounge Activity """
        if ctx.guild.id != 568148147457490954:
            return await ctx.send("This command is only available in Senko Lair")
        async with ctx.typing():
            channel = self.bot.get_channel(658690448478568468)
            lm = await channel.history(limit=None).flatten()
            la = len(lm)
            ca = channel.created_at
            now = time.now(True)
            td = now - ca
            days = (td.days * 86400 + td.seconds) / 86400
            required = target * (days + 1) - la
            return await ctx.send(f"You need to send **{required:,.2f} messages** within the next 24 hours to "
                                  f"have an average of **{target:,} messages per day**")

    @commands.command(name="busstop", hidden=True)
    @commands.is_owner()
    async def bus_stop_display(self, ctx, routes: str, destinations: str, times: str, place: str):
        """ Bus stop display maker """
        rd = relativedelta(years=-276, days=5, hours=1, minutes=30)
        now = time.now(True)
        rp_time = now + rd
        cur_time = rp_time.strftime("%H:%M")
        r = routes.split(', ')
        if len(r) == 1:
            r *= 3
        if len(r) != 3:
            return await ctx.send("There must be 1 or 3 route values specified - split like `1, 2, 3`")
        d = destinations.split(', ')
        if len(d) == 1:
            d *= 3
        if len(d) != 3:
            return await ctx.send("There must be 1 or 3 destination values specified - split like `1, 2, 3`")
        t = times.split(', ')
        if len(t) != 3:
            return await ctx.send("There must be 3 time values specified - split like `1, 2, 3`")
        rl = [len(r[i]) for i in range(len(r))]
        dl = [len(d[i]) for i in range(len(d))]
        tl = [len(t[i]) for i in range(len(t))]
        rd_spaces = max(rl) + 1
        dt_spaces = max(dl) + 6
        block = "```fix\n"
        for i in range(3):
            if t[i] == '0':
                ts = 4
                to = "Due"
            elif t[i] == " ":
                ts = 7
                to = ''
            else:
                ts = 3 - tl[i]
                to = f"{t[i]} min"
            block += f"{r[i]}{' '*(rd_spaces-rl[i])}{d[i]}{' '*(dt_spaces-dl[i])}{' '*ts}{to}\n"
        block += f"{place}{' '*(rd_spaces + dt_spaces + 7 - len(place) - 5)}{cur_time}```"
        return await ctx.send(block)


def setup(bot):
    bot.add_cog(RPStuff(bot))
