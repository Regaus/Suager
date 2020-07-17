import discord
from discord.ext import commands

from core.utils import general, database, time
from languages import langs
from suager.utils import dlram


class DownloadRAM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database(self.bot.name)

    @commands.group(name="dlram")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def dlram(self, ctx: commands.Context):
        """ Download more RAM """
        if ctx.invoked_subcommand is None:
            return await general.send(f"Use `{ctx.prefix}dlram run` to download more RAM", ctx.channel)

    @dlram.command(name="run")
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=False)
    async def dlram_run(self, ctx: commands.Context):
        """ Download more RAM """
        return await dlram.download_ram(ctx, self.db)

    @dlram.command(name="stats")
    async def dlram_stats(self, ctx: commands.Context):
        """ See your server's stats in DLRAM """
        now_ts = int(time.now_ts())
        data, exists = dlram.get_data(ctx.guild, self.db, now_ts)
        if not exists:
            return await general.send("This server has no stats available yet.", ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        embed.title = f"Stats for **{ctx.guild.name}** in DLRAM"
        embed.set_thumbnail(url=ctx.guild.icon_url)
        ram_now = langs.gbs(data["ram"])
        level = data["level"]
        ram_req = langs.gbs(dlram.levels()[level - 1])
        embed.add_field(name="RAM", value=f"Level **{langs.gns(level)}**\n**{ram_now}/{ram_req}** RAM", inline=False)
        charge, regen_t, regen_speed = dlram.regen_energy(data["energy"], data["time"], level, now_ts)
        limit = 200 + level * 25
        charge_str = f"**{langs.gns(charge)}/{langs.gns(limit)}**"
        if charge < limit:
            next_in = time.timedelta(regen_speed - (now_ts - regen_t))
            fill = limit - charge
            full_in = time.timedelta((regen_t + regen_speed * fill) - now_ts)
            charge_str += f"\n+1 in: **{next_in}**\nFull in: **{full_in}**"
        embed.add_field(name="Charge", value=charge_str, inline=False)
        embed.add_field(name="Downloads", value=langs.gns(data["downloads"]), inline=False)
        return await general.send(None, ctx.channel, embed=embed)

    @dlram.command(name="recharge")
    async def dlram_regen_info(self, ctx: commands.Context):
        """ Recharge speeds information """
        return await general.send("Recharge speed starts at **1 per 3 minutes**, and decreases by 1 seconds every level. Caps at 1 charge per 1 second at "
                                  "level 179.", ctx.channel)
        # levels = {"1-99": 60, "100-249": 30, "250-999": 15, "1000-2999": 5, "3000+": 1}
        # output = []
        # indent = max([len(key) for key in levels.keys()])
        # for level, speed in levels.items():
        #     output.append(f"`Levels {level:<{indent}} = {speed} second{'s' if speed > 1 else ''}`")
        # return await general.send(f"\n".join(output), ctx.channel)


def setup(bot):
    bot.add_cog(DownloadRAM(bot))
