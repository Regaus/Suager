import json

import discord
from discord.ext import commands

from core.utils import general, database, time
from suager.utils import tbl, tbl_data


class TBL(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database(self.bot.name)

    @commands.group(name="tbl")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def tbl_command(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            return await general.send(f"Use `{ctx.prefix}tbl play` to play\nUse `{ctx.prefix}tbl stats` to see stats\n"
                                      f"Use `{ctx.prefix}help tbl` for the list of commands available", ctx.channel)

    @tbl_command.command(name="play")
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=False)
    async def tbl_play(self, ctx: commands.Context):
        """ Play TBL """
        return await tbl.tbl_game(ctx, self.db)

    @tbl_command.command(name="stats")
    async def tbl_stats(self, ctx: commands.Context, who: discord.User = None):
        """ See your own or someone else's stats """
        user = who or ctx.author
        now = int(time.now_ts())
        player, _no = tbl.get_player(user, self.db, now)
        if not _no:
            return await general.send(f"{user.name} has not played TBL yet, so no data is available", ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        embed.title = f"Stats for **{user}** in TBL"
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name="Nuts", value=f"**{player['nuts']:,}**", inline=True)
        embed.add_field(name="Coins", value=f"**{player['coins']:,}**", inline=True)
        embed.add_field(name="Rounds played", value=f"**{player['runs']:,}**", inline=True)
        level = player["level"]
        if level < len(tbl_data.xp_levels):
            next_level = f"{tbl_data.xp_levels[level]['experience']:,}"
        else:
            next_level = "MAX"
        sh_xp = player["sh_xp"]
        sh_level = tbl.sh_level(sh_xp)
        if sh_level < len(tbl_data.sh_levels):
            next_sh = f"{tbl_data.sh_levels[sh_level]:,}"
        else:
            next_sh = "MAX"
        title = tbl_data.xp_levels[level - 1]['title']
        embed.add_field(name="Experience", inline=False, value=f"Level **{level}** - **{player['xp']:,}/{next_level}** XP\nTitle: **{title}**")
        embed.add_field(name="Shaman XP", inline=False, value=f"Level **{sh_level}** - **{sh_xp:,}/{next_sh}** XP")
        league = "None"
        points = player['points']
        next_league = "Undefined"
        leagues = tbl_data.leagues
        league_len = len(leagues)
        for i in range(league_len):
            _league = leagues[i]
            if _league['score'] <= player["points"]:
                league = _league["name"]
                if i < league_len - 1:
                    next_league = f"{leagues[i + 1]['score']:,}"
                else:
                    next_league = "MAX"
            else:
                break
        embed.add_field(name="League", inline=False, value=f"**{league}** - **{points:,}/{next_league}** points")
        energy, regen_t = tbl.regen_energy(player["energy"], player["time"], player["level"], now)
        limit = 119 + level
        next_in = f" - Next in: **{time.timedelta(now - regen_t)}**" if energy < limit else ""
        embed.add_field(name="Energy", inline=False, value=f"**{energy:,.0f}/{limit}**{next_in}")
        return await general.send(None, ctx.channel, embed=embed)

    @tbl_command.command(name="clan")
    @commands.guild_only()
    async def tbl_clan(self, ctx: commands.Context):
        """ Stats about your clan (server) """
        clan, _no = tbl.get_clan(ctx.guild, self.db)
        if not _no:
            return await general.send("There is no data available about this clan so far.", ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        embed.title = f"Stats for **{ctx.guild.name}** in TBL"
        embed.set_thumbnail(url=ctx.guild.icon_url)
        if clan['level'] < len(tbl_data.clan_levels):
            next_level = f"{tbl_data.clan_levels[clan['level'] + 1]:,}"
        else:
            next_level = "MAX"
        embed.add_field(name="Level and XP", value=f"Level **{clan['level']}**\n**{clan['xp']:,}/{next_level}** XP", inline=True)
        embed.add_field(name="Upgrade points", value=f"**{clan['upgrade_points']:,}**", inline=True)
        embed.add_field(name="Finances", value=f"**{clan['nuts']:,}** nuts\n**{clan['coins']}** coins", inline=True)
        t1, t2, t3 = json.loads(clan["temples"])
        now = time.now_ts()
        embed.add_field(name="Temple 1", value=f"**{tbl_data.totems[t1['id'] - 1]['name']}**" if t1['id'] != 0 else "**Inactive totem**", inline=True)
        if t2["id"] != 0:
            e2 = t2["expiry"]
            r2 = f"**{tbl_data.totems[t2['id'] - 1]['name']}**\nExpires {time.human_timedelta(time.from_ts(e2), brief=True)}" if e2 > now else "Totem expired"
        else:
            r2 = "**Inactive totem**"
        embed.add_field(name="Temple 2", value=r2, inline=True)
        if t3["id"] != 0:
            e3 = t3["expiry"]
            r3 = f"**{tbl_data.totems[t3['id'] - 1]['name']}**\nExpires {time.human_timedelta(time.from_ts(e3), brief=True)}" if e3 > now else "Totem expired"
        else:
            r3 = "**Inactive totem**"
        embed.add_field(name="Temple 3", value=r3, inline=True)
        max_members = ctx.guild.max_members or 250000
        embed.add_field(name="Members", value=f"**{ctx.guild.member_count:,}/{max_members:,}**")
        return await general.send(None, ctx.channel, embed=embed)


def setup(bot):
    bot.add_cog(TBL(bot))
