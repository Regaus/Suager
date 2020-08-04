import asyncio
import json

import discord
from discord.ext import commands

from core.utils import general, database, time, permissions
from languages import langs
from suager.utils import dlram, tbl, tbl_data


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database(self.bot.name)
        self.season = tbl.get_season()

    @commands.Cog.listener()
    async def on_ready(self):
        while True:
            season = tbl.get_season()
            if season != self.season:
                channel = self.bot.get_channel(733751281184931850)
                all_players = self.db.fetch("SELECT * FROM tbl_player")
                old_points = []
                for player in all_players:
                    old_points.append({"name": f"{player['name']}#{player['disc']:04d}", "points": player["points"], 'id': player['uid']})
                old_points.sort(key=lambda x: x["points"], reverse=True)
                top_5 = ""
                emotes = ["🥇", "🥈", "🥉", "🏆", "🏆"]
                prize = [50, 30, 20, 10, 5]
                prizes = [langs.plural(i, "coin") for i in prize]
                for place, user in enumerate(old_points[:5], start=1):
                    emote = emotes[place - 1]
                    top_5 += f"\n{emote} **#{place}: {user['name']}** at **{user['points']:,} Points** - Prize: **{prizes[place - 1]}**"
                    self.db.execute("UPDATE tbl_player SET coins=coins+? WHERE uid=?", (prize[place - 1], user["id"]))
                self.db.execute("UPDATE tbl_player SET points=points/10, nuts=nuts+(points/5)")
                await general.send(f"Season {self.season} has now ended! Here are the Top 5 people of the past season:{top_5}\n"
                                   f"1/10 of everyone's League Points will carry over to the next season, and some will be converted to extra Nuts.\n"
                                   f"The top 5 will also receive some extra coins.", channel)
                self.season = season
            await asyncio.sleep(60)

    @commands.group(name="dlram")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def dlram(self, ctx: commands.Context):
        """ Download more RAM """
        if ctx.invoked_subcommand is None:
            return await general.send(langs.gls("dlram_no_subcommand", langs.gl(ctx.guild, self.db), ctx.prefix), ctx.channel)
            # return await general.send(f"Use `{ctx.prefix}dlram run` to download more RAM", ctx.channel)

    @dlram.command(name="run")
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=False)
    async def dlram_run(self, ctx: commands.Context):
        """ Download more RAM """
        return await dlram.download_ram(ctx, self.db)

    @dlram.command(name="stats")
    async def dlram_stats(self, ctx: commands.Context):
        """ See your server's stats in DLRAM """
        locale = langs.gl(ctx.guild, self.db)
        now_ts = int(time.now_ts())
        data, exists = dlram.get_data(ctx.guild, self.db, now_ts)
        if not exists:
            return await general.send(langs.gls("dlram_stats_none", locale), ctx.channel)
            # return await general.send("This server has no stats available yet.", ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        # embed.title = f"Stats for **{ctx.guild.name}** in DLRAM"
        embed.title = langs.gls("dlram_stats", locale, ctx.guild.name)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        ram_now = langs.gbs(data["ram"], locale)
        level = data["level"]
        ram_req = langs.gbs(dlram.levels()[level - 1], locale)
        _level = langs.gns(level, locale)
        embed.add_field(name=langs.gls("dlram_stats_ram", locale), value=langs.gls("dlram_stats_ram_data", locale, _level, ram_now, ram_req), inline=False)
        # embed.add_field(name="RAM", value=f"Level **{langs.gns(level)}**\n**{ram_now}/{ram_req}** RAM", inline=False)
        charge, regen_t, regen_speed = dlram.regen_energy(data["energy"], data["time"], level, now_ts)
        limit, _ = dlram.speed_limit(level)
        charge_str = f"**{langs.gns(charge, locale)}/{langs.gns(limit, locale)}**\n"
        if charge < limit:
            # next_in = time.timedelta(regen_speed - (now_ts - regen_t))
            fill = limit - charge
            # full_in = time.timedelta((regen_t + regen_speed * fill) - now_ts)
            # charge_str += f"\n+1 in: **{next_in}**\nFull in: **{full_in}**"
            next_in = langs.td_int(regen_speed - (now_ts - regen_t), locale, is_future=True, suffix=True)
            full_in = langs.td_int((regen_t + regen_speed * fill) - now_ts, locale, is_future=True, suffix=True)
            charge_str += langs.gls("dlram_stats_charge_data", locale, next_in, full_in)
        embed.add_field(name=langs.gls("dlram_stats_charge", locale), value=charge_str, inline=False)
        embed.add_field(name=langs.gls("dlram_stats_downloads", locale), value=langs.gns(data["downloads"], locale), inline=False)
        return await general.send(None, ctx.channel, embed=embed)

    @dlram.command(name="data")
    async def dlram_regen(self, ctx: commands.Context):
        """ DLRAM data on charge speeds for levels """
        levels = [1, 2, 3, 4, 5, 10, 15, 20, 40, 60, 80, 100, 150, 200, 350, 500, 750, 1000, 1750, 2500, 5000, 7500, 10000, 12500, 15000, 17500, 20000, 25000]
        _levels = dlram.levels()
        outputs = []
        for level in levels:
            limit, regen_speed = dlram.speed_limit(level)
            fill = regen_speed * limit
            h, m = divmod(int(fill), 3600)
            m, s = divmod(m, 60)
            _time = f"{h:02d}h {m:02d}m {s:02d}s"
            ram = langs.gbs(_levels[level - 1], "en_gb", 1)
            outputs.append(f"Level {level:>5} | Charge {limit:>7} | Recharge {regen_speed:>8.4f}s | Fill {_time:>11} | RAM {ram:>11}")
        for i in range(int(len(outputs) / 20) + 1):
            r, e = i * 20, (i + 1) * 20
            output = "\n".join(outputs[r:e])
            await general.send(f"```fix\n{output}```", ctx.channel)
        # _outputs = "\n".join(outputs)
        # output = "\n".join(outputs)
        # print(len(output))

    @commands.group(name="tbl")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def tbl(self, ctx: commands.Context):
        """ TBL """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))
            # return await general.send(f"Use `{ctx.prefix}tbl play` to play\nUse `{ctx.prefix}tbl stats` to see stats\n"
            #                           f"Use `{ctx.prefix}help tbl` for the list of commands available", ctx.channel)

    @tbl.command(name="play")
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=True)
    async def tbl_play(self, ctx: commands.Context):
        """ Play TBL """
        return await tbl.tbl_game(ctx, self.db)

    @tbl.command(name="stats")
    async def tbl_stats(self, ctx: commands.Context, who: discord.User = None):
        """ See your own or someone else's stats """
        locale = langs.gl(ctx.guild, self.db)
        user = who or ctx.author
        now = int(time.now_ts())
        player, _no = tbl.get_player(user, self.db, now)
        if not _no:
            return await general.send(langs.gls("tbl_stats_no_data", locale, user.name), ctx.channel)
            # return await general.send(f"{user.name} has not played TBL yet, so no data is available", ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        embed.title = langs.gls("tbl_stats", locale, user)
        # embed.title = f"Stats for **{user}** in TBL"
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name=langs.gls("tbl_stats_nuts", locale), value=f"**{langs.gns(player['nuts'], locale)}**", inline=True)
        embed.add_field(name=langs.gls("tbl_stats_coins", locale), value=f"**{langs.gns(player['coins'], locale)}**", inline=True)
        embed.add_field(name=langs.gls("tbl_stats_rounds", locale), value=f"**{langs.gns(player['runs'], locale)}**", inline=True)
        level = player["level"]
        if level < len(tbl_data.xp_levels):
            next_level = f"{langs.gns(tbl_data.xp_levels[level]['experience'], locale)}"
        else:
            next_level = langs.gls("generic_max", locale)
        sh_xp = player["sh_xp"]
        sh_level = tbl.sh_level(sh_xp)
        if sh_level < len(tbl_data.sh_levels):
            next_sh = f"{langs.gns(tbl_data.sh_levels[sh_level], locale)}"
        else:
            next_sh = langs.gls("generic_max", locale)
        title = langs.gls(tbl_data.xp_levels[level - 1]['title'], locale)
        _level, _xp, _sh_l, _sh_xp = langs.gns(level, locale), langs.gns(player["xp"], locale), langs.gns(sh_level, locale), langs.gns(sh_xp, locale)
        embed.add_field(name=langs.gls("tbl_stats_xp", locale), inline=False, value=langs.gls("tbl_stats_xp_data", locale, _level, _xp, next_level, title))
        embed.add_field(name=langs.gls("tbl_stats_xp_sh", locale), inline=False, value=langs.gls("tbl_stats_xp_sh_data", locale, _sh_l, _sh_xp, next_sh))
        league = "None"
        points = player['points']
        next_league = "Undefined"
        leagues = tbl_data.leagues
        league_len = len(leagues)
        for i in range(league_len):
            _league = leagues[i]
            if _league['score'] <= player["points"]:
                league = langs.gls(_league["name"], locale)
                if i < league_len - 1:
                    next_league = f"{langs.gns(leagues[i + 1]['score'], locale)}"
                else:
                    next_league = langs.gls("generic_max", locale)
            else:
                break
        p = langs.gns(points, locale)
        embed.add_field(name=langs.gls("tbl_stats_league", locale), inline=False, value=langs.gls("tbl_stats_league_data", locale, league, p, next_league))
        energy, regen_t = tbl.regen_energy(player["energy"], player["time"], player["level"], now)
        limit = 119 + level if level <= 200 else 320 if level == 200 else 420
        # next_in = f" - Next in: **{time.timedelta(60 - (now - regen_t))}**" if energy < limit else ""
        next_in = langs.gls("tbl_stats_energy_next", locale, langs.td_int(60 - (now - regen_t), locale, is_future=True)) if energy < limit else ""
        _e, _l = langs.gns(int(energy), locale), langs.gns(limit, locale)
        embed.add_field(name=langs.gls("tbl_stats_energy", locale), inline=False, value=f"**{_e}/{_l}**{next_in}")
        return await general.send(None, ctx.channel, embed=embed)

    @tbl.command(name="clan")
    async def tbl_clan(self, ctx: commands.Context):
        """ Stats about your clan (server) """
        locale = langs.gl(ctx.guild, self.db)
        clan, _no = tbl.get_clan(ctx.guild, self.db)
        if not _no:
            return await general.send(langs.gls("tbl_stats_no_data", locale, ctx.guild.name), ctx.channel)
            # return await general.send("There is no data available about this clan so far.", ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        embed.title = langs.gls("tbl_stats", locale, ctx.guild.name)
        # embed.title = f"Stats for **{ctx.guild.name}** in TBL"
        embed.set_thumbnail(url=ctx.guild.icon_url)
        if clan['level'] < len(tbl_data.clan_levels):
            next_level = f"{langs.gns(tbl_data.clan_levels[clan['level'] + 1], locale)}"
        else:
            next_level = langs.gls("generic_max", locale)
        _l, _xp = langs.gns(clan["level"], locale), langs.gns(clan["xp"], locale)
        embed.add_field(name=langs.gls("tbl_stats_xp", locale), value=langs.gls("tbl_clan_xp", locale, _l, _xp, next_level), inline=True)
        embed.add_field(name=langs.gls("tbl_clan_points", locale), value=f"**{langs.gns(clan['upgrade_points'], locale)}**", inline=True)
        embed.add_field(name=langs.gls("tbl_clan_finance", locale), value=f"**{clan['nuts']:,}** nuts\n**{clan['coins']}** coins", inline=True)
        t1, t2, t3 = json.loads(clan["temples"])
        now = time.now_ts()
        inactive = langs.gls("tbl_totems_inactive", locale)
        expired = langs.gls("tbl_totems_expired", locale)
        embed.add_field(name=langs.gls("tbl_clan_totems", locale, 1),
                        value=f"**{langs.gls(tbl_data.totems[t1['id'] - 1]['name'], locale)}**" if t1['id'] != 0 else inactive, inline=True)
        if t2["id"] != 0:
            e2 = t2["expiry"]
            expiry = langs.gls("tbl_clan_totem_expiry", locale, langs.td_ts(e2, locale, suffix=True))
            r2 = f"**{langs.gls(tbl_data.totems[t2['id'] - 1]['name'], locale)}**\n{expiry}" if e2 > now else expired
        else:
            r2 = inactive
        embed.add_field(name=langs.gls("tbl_clan_totems", locale, 2), value=r2, inline=True)
        if t3["id"] != 0:
            e3 = t3["expiry"]
            expiry = langs.gls("tbl_clan_totem_expiry", locale, langs.td_ts(e3, locale, suffix=True))
            r3 = f"**{langs.gls(tbl_data.totems[t3['id'] - 1]['name'], locale)}**\n{expiry}" if e3 > now else expired
        else:
            r3 = inactive
        embed.add_field(name=langs.gls("tbl_clan_totems", locale, 3), value=r3, inline=True)
        return await general.send(None, ctx.channel, embed=embed)

    @tbl.command(name="donate")
    async def tbl_donate(self, ctx: commands.Context, what: str, value: int):
        """ Donate to your TBL clan """
        locale = langs.gl(ctx.guild, self.db)
        now = int(time.now_ts())
        player, exists = tbl.get_player(ctx.author, self.db, now)
        if not exists:
            return await general.send(langs.gls("tbl_stats_no_data", locale, ctx.author.name), ctx.channel)
            # return await general.send(f"You have not played TBL yet. Run `{ctx.prefix}tbl play` at least once before using this.", ctx.channel)
        clan, exists = tbl.get_clan(ctx.guild, self.db)
        if not exists:
            return await general.send(langs.gls("tbl_stats_no_data", locale, ctx.guild.name), ctx.channel)
            # return await general.send(f"This clan has not been fully created yet. Run `{ctx.prefix}tbl play` at least once before using this.", ctx.channel)
        if clan["usage"]:
            return await general.send(langs.gls("tbl_clan_usage", locale), ctx.channel)
            # return await general.send("TBL is running in this clan at the moment, so this function is currently unavailable. Try again later.", ctx.channel)
        choice = what.lower()
        if choice == "nuts":
            nuts = player["nuts"]
            if nuts < value:
                return await general.send(langs.gls("tbl_donate_nuts", locale), ctx.channel)
                # return await general.send("You don't have enough Nuts to do that.", ctx.channel)
            self.db.execute("UPDATE tbl_player SET nuts=nuts-? WHERE uid=?", (value, ctx.author.id))
            self.db.execute("UPDATE tbl_clan SET nuts=nuts+? WHERE gid=?", (value, ctx.guild.id))
            word = langs.plural(value, "tbl_nuts", locale)
        elif choice == "coins":
            coins = player["coins"]
            if coins < value:
                return await general.send(langs.gls("tbl_donate_nuts", locale), ctx.channel)
                # return await general.send("You don't have enough Coins to do that.", ctx.channel)
            self.db.execute("UPDATE tbl_player SET coins=coins-? WHERE uid=?", (value, ctx.author.id))
            self.db.execute("UPDATE tbl_clan SET coins=coins+? WHERE gid=?", (value, ctx.guild.id))
            word = langs.plural(value, "tbl_coins", locale)
        else:
            return await general.send(langs.gls("tbl_donate_invalid", locale), ctx.channel)
            # return await general.send("You need to specify either `nuts` or `coins`.", ctx.channel)
        return await general.send(langs.gls("tbl_donate", locale, word), ctx.channel)
        # return await general.send(f"Donated **{word}** to current clan.", ctx.channel)

    @tbl.group(name="totems")
    @permissions.has_permissions(kick_members=True)
    async def tbl_totems(self, ctx: commands.Context):
        """ Set TBL totems for your clan """
        if ctx.invoked_subcommand is None:
            locale = langs.gl(ctx.guild, self.db)
            return await general.send(langs.gls("tbl_totems_help", locale, ctx.prefix), ctx.channel)
            # return await general.send(f"`{ctx.prefix}tbl details totems` for information on totems\n`{ctx.prefix}tbl totems set` to set a totem\n"
            #                           f"`{ctx.prefix}tbl totems upgrade` to upgrade a totem", ctx.channel)

    @tbl_totems.command(name="upgrade")
    async def tbl_totem_upgrade(self, ctx: commands.Context, totem_id: int = 0, upgrades: int = 1):
        """ Upgrade a TBL totem """
        locale = langs.gl(ctx.guild, self.db)
        clan, exists = tbl.get_clan(ctx.guild, self.db)
        if upgrades < 1:
            return await general.send(langs.gls("tbl_totem_upgrade_negative2", locale), ctx.channel)
        if not exists:
            return await general.send(langs.gls("tbl_stats_no_data", locale, ctx.guild.name), ctx.channel)
            # return await general.send(f"This clan has not been fully created yet. Run `{ctx.prefix}tbl play` at least once before using this.", ctx.channel)
        if clan["usage"]:
            return await general.send(langs.gls("tbl_clan_usage", locale), ctx.channel)
            # return await general.send("TBL is running in this clan at the moment, so this function is currently unavailable. Try again later.", ctx.channel)
        if totem_id <= 0:
            return await general.send(langs.gls("tbl_totem_upgrade_negative", locale, ctx.prefix), ctx.channel)
            # return await general.send(f"Please enter a totem ID. These can be found with `{ctx.prefix}tbl details totems`.", ctx.channel)
        if totem_id >= 4:
            return await general.send(langs.gls("tbl_totem_upgrade_4", locale, ctx.prefix), ctx.channel)
            # return await general.send("Totems of Senko and Cthulhu cannot be upgraded.", ctx.channel)
        if clan["upgrade_points"] < upgrades:
            return await general.send(langs.gls("tbl_totem_upgrade_not_enough", locale), ctx.channel)
            # return await general.send("This clan does not have enough Upgrade Points available. "
            #                           "You will get more from leveling the clan up by playing TBL.", ctx.channel)
        levels = json.loads(clan["temple_levels"])
        levels[totem_id - 1] += upgrades
        self.db.execute("UPDATE tbl_clan SET upgrade_points=upgrade_points-?, temple_levels=? WHERE gid=?", (upgrades, json.dumps(levels), ctx.guild.id))
        new_level = langs.gns(levels[totem_id - 1], locale)
        times = langs.plural(upgrades, "generic_times", locale)
        name = langs.gls(tbl_data.totems[totem_id - 1]['name'], locale)
        return await general.send(langs.gls("tbl_totem_upgrade", locale, name, times, new_level, ctx.prefix), ctx.channel)
        # return await general.send(f"The **{tbl_data.totems[totem_id - 1]['name']}** has been successfully upgraded **{times}**. It is now "
        #                           f"level **{new_level}.** You can see its new power multiplier with `{ctx.prefix}tbl details totems`", ctx.channel)

    @tbl_totems.command(name="set")
    async def tbl_totem_set(self, ctx: commands.Context, slot: int = 0, totem_id: int = -1):
        """ Set a TBL totem """
        locale = langs.gl(ctx.guild, self.db)
        clan, exists = tbl.get_clan(ctx.guild, self.db)
        if not exists:
            return await general.send(langs.gls("tbl_stats_no_data", locale, ctx.guild.name), ctx.channel)
            # return await general.send(f"This clan has not been fully created yet. Run `{ctx.prefix}tbl play` at least once before using this.", ctx.channel)
        if clan["usage"]:
            return await general.send(langs.gls("tbl_clan_usage", locale), ctx.channel)
            # return await general.send("TBL is running in this clan at the moment, so this function is currently unavailable. Try again later.", ctx.channel)
        totems = json.loads(clan["temples"])
        nuts = clan["nuts"]
        totem_amount = len(tbl_data.totems)
        if slot <= 0:
            return await general.send(langs.gls("tbl_totem_set_negative", locale, ctx.prefix), ctx.channel)
            # return await general.send("Please specify which totem you want to set. (1-3)", ctx.channel)
        if slot > 3:
            return await general.send(langs.gls("tbl_totem_set_3", locale), ctx.channel)
            # return await general.send("There can be only 3 totems", ctx.channel)
        if totem_id < 0:
            return await general.send(langs.gls("tbl_totem_upgrade_negative", locale), ctx.channel)
            # return await general.send(f"Please enter a totem ID. These can be found with `{ctx.prefix}tbl details totems`.", ctx.channel)
        if totem_id > totem_amount:
            return await general.send(langs.gls("tbl_totem_set_invalid", locale, totem_id), ctx.channel)
            # return await general.send(f"There is no totem with ID {totem_id}", ctx.channel)
        active_totems = [totem['id'] for totem in totems]
        if totem_id in active_totems and totem_id != 0:
            return await general.send(langs.gls("tbl_totem_set_active", locale), ctx.channel)
            # return await general.send("This totem is already active", ctx.channel)
        c = langs.plural(0, "tbl_nuts", locale)
        if slot == 1:
            totems[0]["id"] = totem_id
        if slot in [2, 3]:
            totems[slot - 1]["id"] = totem_id
            expiry = totems[slot - 1]["expiry"]
            now = time.now_ts()
            if expiry > now:
                await general.send(langs.gls("tbl_totem_set_active2", locale), ctx.channel)
                # await general.send("As there is already an active totem in this slot, the totem ID will be updated, however the expiry time will remain "
                #                    "the same, and no Nuts will be charged.", ctx.channel)
            else:
                if totem_id == 0:
                    return await general.send(langs.gls("tbl_totem_set_expired", locale), ctx.channel)
                    # return await general.send("This totem has already expired, you can't reset it.", ctx.channel)
                cost = (13 if slot == 2 else 37) * ctx.guild.member_count
                if nuts < cost:
                    n = langs.gns(nuts, locale)
                    c = langs.plural(cost, "tbl_nuts", locale)
                    return await general.send(langs.gls("tbl_totem_set_money", locale, n, c), ctx.channel)
                    # return await general.send(f"This clan does not have sufficient balance to activate this totem right now. ({n}/{c})", ctx.channel)
                totems[slot - 1]["expiry"] = now + 72 * 3600
                nuts -= cost
                c = langs.plural(cost, "tbl_nuts", locale)
        self.db.execute("UPDATE tbl_clan SET nuts=?, temples=? WHERE gid=?", (nuts, json.dumps(totems), ctx.guild.id))
        name = langs.gls("tbl_totem_set_set", locale, langs.gls(tbl_data.totems[totem_id - 1]['name'], locale)) if totem_id > 0 else \
            langs.gls("tbl_totem_set_reset", locale)
        return await general.send(langs.gls("tbl_totem_set", locale, name, slot, c), ctx.channel)
        # name = f"Set **{tbl_data.totems[totem_id - 1]['name']}** to" if totem_id > 0 else "**Reset**"
        # return await general.send(f"{name} to Slot **{slot}** for **{c}**.", ctx.channel)

    @tbl.command(name="location")
    async def tbl_set_location(self, ctx: commands.Context, location_id: int = -1):
        """ Set your location """
        locale = langs.gl(ctx.guild, self.db)
        player, exists = tbl.get_player(ctx.author, self.db, 0)
        if not exists:
            return await general.send(langs.gls("tbl_stats_no_data", locale, ctx.author.name), ctx.channel)
            # return await general.send(f"You have not played TBL yet. Run `{ctx.prefix}tbl play` at least once before using this.", ctx.channel)
        locations = tbl_data.locations
        if location_id < 0:
            return await general.send(langs.gls("tbl_location_negative", locale), ctx.channel)
        # return await general.send("You need to specify which location you want to be in. Entering `0` will reset it, entering `1`-`17` will set you to
        # the                            "specified one", ctx.channel)
        if location_id > len(locations):
            return await general.send(langs.gls("tbl_location_nonexistent", locale, location_id), ctx.channel)
            # return await general.send(f"Location with ID {location_id} does not exist.", ctx.channel)
        location = tbl.get_location(location_id, 999)
        output = langs.gls("tbl_location_set", locale, location['name'], langs.gls(location['en'], locale)) if location_id > 0 else \
            langs.gls("tbl_location_reset", locale)
        # output = f"Set your location to **{location['name']} ({location['en']})**" if location_id > 0 else "**Reset** you location"
        self.db.execute("UPDATE tbl_player SET location=? WHERE uid=?", (location_id, ctx.author.id))
        return await general.send(langs.gls("tbl_location_success", locale, output), ctx.channel)
        # return await general.send(f"{output}. Note that if your level is not high enough to be there, it will be set to the nearest available.", ctx.channel)

    @tbl.group(name="details", aliases=["documentation", "docs", "explain"])
    async def tbl_docs(self, ctx: commands.Context):
        """ Information about TBL """
        if ctx.invoked_subcommand is None:
            locale = langs.gl(ctx.guild, self.db)
            sub_commands = ["clans", "game", "leagues", "levels", "locations", "seasons", "totems"]
            sub_commands.sort()
            _data = [f"`{key}` - {langs.gls(f'tbl_details_subcommands_{key}', locale)}" for key in sub_commands]
            return await general.send(langs.gls("tbl_details_subcommands", locale, "\n".join(_data)), ctx.channel)
            # return await general.send("Here are subcommands which can help you:\n" + "\n".join(_data), ctx.channel)

    @tbl_docs.command(name="game")
    async def tbl_docs_game(self, ctx: commands.Context):
        """ Information on how TBL works """
        return await general.send(langs.gls("tbl_details_game", langs.gl(ctx.guild, self.db)), ctx.channel)

    @tbl_docs.command(name="levels")
    async def tbl_docs_levels(self, ctx: commands.Context):
        """ Information on levels """
        return await general.send(langs.gls("tbl_details_levels", langs.gl(ctx.guild, self.db)), ctx.channel)

    @tbl_docs.command(name="totems")
    async def tbl_docs_totems(self, ctx: commands.Context):
        """ Information on totems """
        locale = langs.gl(ctx.guild, self.db)
        clan, _ = tbl.get_clan(ctx.guild, self.db)
        del _
        levels = json.loads(clan["temple_levels"])
        totems = tbl_data.totems
        outputs = []
        for i in range(len(levels)):
            totem = totems[i]
            level = levels[i]
            effect = 0.06 + 0.04 * level if i == 0 else 0.07 + 0.03 * level if i == 1 else 0.075 + 0.025 * level if i == 2 else -1
            effect_str = langs.gfs(effect, locale, 1, True)
            totem_desc = langs.gls(totem['desc'], locale, effect_str)
            outputs.append(f"{i + 1}) **{langs.gls(totem['name'], locale)}** - Level **{langs.gns(level, locale)}**:\n{totem_desc}")
        cost_2 = langs.plural(13 * ctx.guild.member_count, "tbl_nuts", locale)
        cost_3 = langs.plural(37 * ctx.guild.member_count, "tbl_nuts", locale)
        return await general.send(langs.gls("tbl_details_totems", locale, "\n".join(outputs), ctx.prefix, cost_2, cost_3), ctx.channel)
        # return await general.send("This is information on your clan's totems.\n\n" + "\n".join(outputs) +
        #                          f"\n\nYou can check current totem stats using `{ctx.prefix}tbl clan`.\nYou can assign totems using `{ctx.prefix}tbl totems`."
        #                           f"\nThe first totem is **free**, the 2nd costs **{cost_2} Nuts** and the 3rd costs **{cost_3} Nuts**. Paid totems will "
        #                           f"expire after **72 hours**.\nYou can also buy extra Upgrade Points for **3 coins each**.", ctx.channel)

    @tbl_docs.command(name="leagues")
    async def tbl_docs_leagues(self, ctx: commands.Context):
        """ Information on TBL Leagues """
        locale = langs.gl(ctx.guild, self.db)
        leagues = tbl_data.leagues
        names = []
        points = []
        outputs = []
        for league in leagues:
            names.append(langs.gls(league['name'], locale))
            points.append(langs.gns(league['score'], locale))
        for i in range(1, len(leagues)):
            a, b = f"{names[i]:<{len(max(names))}}", f"{points[i]:>{len(points[-1])}}"
            outputs.append(langs.gls("tbl_details_leagues_data", locale, a, b))
            # outputs.append(f"`{names[i]:<{len(max(names))}} - {points[i]:>{len(points[-1])}} Points`")
        season = langs.gns(self.season, locale)
        season_end = langs.td_dt(tbl_data.seasons[self.season][1], locale, brief=True, suffix=False)
        await general.send(langs.gls("tbl_details_leagues", locale, season, season_end), ctx.channel)
        return await general.send(langs.gls("tbl_details_leagues2", locale, "\n".join(outputs)), ctx.channel)
        # await general.send("You get league points by winning rounds in TBL.\nThose who have the highest points at the end of a season will receive coins. "
        #                    "Everyone gets 1/5 of their points converted into extra Nuts, 1/10 of their league points get carried over into the next season. "
        #                    "There is an extra reward for being in the top 5 at the end of the season\nThe current season is "
        #                    f"**Season {langs.gns(self.season)}** - Ends in **{langs.td_dt(season_end, brief=True)}**", ctx.channel)
        # await general.send("These are the leagues in TBL:\n" + "\n".join(outputs), ctx.channel)
        # await general.send("\nAnd these are the prizes for being in the top 5 globally:\n" +
        #                    "\n".join([f"#{i}: **{p}**" for i, p in enumerate(prizes, start=1)]), ctx.channel)

    @tbl_docs.command(name="seasons")
    async def tbl_docs_seasons(self, ctx: commands.Context):
        """ Information on TBL Seasons """
        locale = langs.gl(ctx.guild, self.db)
        seasons = list(tbl_data.seasons.items())
        season_b = self.season - 2 if self.season - 2 > 0 else 0
        season_l = self.season + 8
        season_data = ""
        for season, data in seasons[season_b:season_l]:
            # season_data += f"\nSeason {langs.gns(season)}: from **{langs.gts_date(data[0])}** to **{langs.gts_date(data[1])}**"
            season_data += langs.gls("tbl_details_seasons_data", locale, langs.gns(season, locale), langs.gts_date(data[0], locale),
                                     langs.gts_date(data[1], locale))
            if season == self.season:
                season_data += langs.gls("tbl_details_seasons_current", locale)
        return await general.send(langs.gls("tbl_details_seasons", locale, season_data), ctx.channel)
        # await general.send("TBL has League Seasons, which means that about every month 1/5 of your League Points is converted into Nuts, and 1/10 of the "
        #                    "points carry over into the next Season. People who are in the Top 5 also get extra coins. Here are a few past seasons and "
        #                    f"the upcoming ones:{season_data}", ctx.channel)

    @tbl_docs.command(name="locations")
    async def tbl_docs_loc(self, ctx: commands.Context, location_id: int = 0):
        """ Information on TBL locations """
        locale = langs.gl(ctx.guild, self.db)
        if location_id == 0:
            locations = tbl_data.locations
            data = []
            for loc in locations:
                data.append(langs.gls("tbl_details_locations_data", locale, loc["id"], loc["name"], langs.gns(loc["level"], locale)))
                # data.append(f"Loc. ID **{loc['id']}** - **{loc['name']}** - Unlocks at level **{langs.gns(loc['level'])}**")
            return await general.send(langs.gls("tbl_details_locations", locale, "\n".join(data)), ctx.channel)
            # return await general.send("These are the TBL locations:\n" + "\n".join(data) +
            #                           f"\nYou can use the location ID with this command for more data on a specific location", ctx.channel)
        else:
            location = tbl.get_location(location_id, 999)
            embed = discord.Embed(colour=general.random_colour())
            # embed.title = f"Information on Loc. ID **{location_id}**"
            embed.title = langs.gls("tbl_details_locations_title", locale, location_id)
            embed.description = langs.gls(location["desc_en"], locale)
            embed.add_field(name=langs.gls("tbl_details_locations_name", locale), value=location["name"], inline=False)
            embed.add_field(name=langs.gls("tbl_details_locations_name2", locale), value=langs.gls(location["en"], locale), inline=False)
            embed.add_field(name=langs.gls("tbl_details_locations_req", locale), value=f"**{langs.gns(location['level'], locale)}**", inline=True)
            a1, a2 = location["araksan"]
            embed.add_field(name=langs.gls("tbl_details_locations_nuts", locale), value=f"**{langs.gns(a1, locale)}-{langs.gns(a2, locale)}**", inline=True)
            x1, x2 = location["xp"]
            embed.add_field(name=langs.gls("tbl_details_locations_xp", locale), value=f"**{langs.gns(x1, locale)}-{langs.gns(x2, locale)}**", inline=True)
            embed.add_field(name=langs.gls("tbl_details_locations_sh", locale), value=f"**{langs.gns(location['sh'], locale)}**", inline=True)
            p1, p2 = location["points"]
            embed.add_field(name=langs.gls("tbl_details_locations_league", locale), value=f"**{langs.gns(p1, locale)}-{langs.gns(p2, locale)}**", inline=True)
            embed.add_field(name=langs.gls("tbl_details_locations_length", locale), inline=True,
                            value=f"**{langs.td_int(location['ll'], locale, brief=True, suffix=False)}**")
            player, _ = tbl.get_player(ctx.author, self.db, time.now_ts())
            level = player['level']
            death_rate = location['dr'] / (1 + (level - 1) / 64)
            dr, lvl = langs.gfs(death_rate, locale, 0, True), langs.gns(level, locale)
            embed.add_field(name=langs.gls("tbl_details_locations_dr", locale), value=langs.gls("tbl_details_locations_dr_data", locale, dr, lvl), inline=True)
            act = langs.plural(tbl.get_activity(location['activity']), "tbl_details_locations_players", locale)
            embed.add_field(name=langs.gls("tbl_details_locations_activity", locale), value=act, inline=True)
            embed.set_footer(text=langs.gls("tbl_details_locations_note", locale))
            return await general.send(None, ctx.channel, embed=embed)

    @tbl_docs.command(name="clans")
    async def tbl_clans(self, ctx: commands.Context):
        """ Tells more about clans """
        return await general.send(langs.gls("tbl_details_clans", langs.gl(ctx.guild, self.db), ctx.prefix), ctx.channel)

    @tbl.command(name="leaderboard", aliases=["top", "lb"])
    async def tbl_leaderboard(self, ctx: commands.Context, page: int = 0):
        """ TBL Leaderboard """
        locale = langs.gl(ctx.guild, self.db)
        data = self.db.fetch("SELECT * FROM tbl_player ORDER BY points DESC")
        if not data:
            return await general.send(langs.gls("leaderboards_no_data", locale), ctx.channel)
            # return await general.send("I have no data saved for this server so far.", ctx.channel)
        block = "```fix\n"
        un = []   # User names
        xp = []   # XP
        xpl = []  # XP string lengths
        for user in data:
            name = f"{user['name']}#{user['disc']:04d}"
            un.append(name)
            val = langs.gns(user['points'], locale)
            xp.append(val)
            xpl.append(len(val))
        total = len(xp)
        place = langs.gls("generic_unknown", locale)
        n = 0
        for x in range(len(data)):
            if data[x]['uid'] == ctx.author.id:
                place = langs.gls("leaderboards_place", locale, langs.gns(x + 1, locale, 0, False))
                n = x + 1
                break
        start = 0
        try:
            if (n <= 10) and page == 0:
                _data = data[:10]
                start = 1
                spaces = max(xpl[:10]) + 5
            elif page > 0:
                _data = data[(page - 1)*10:page*10]
                start = page * 10 - 9
                spaces = max(xpl[(page - 1)*10:page*10]) + 5
            else:
                _data = data[n-5:n+5]
                start = n - 4
                spaces = max(xpl[n-5:n+5]) + 5
            s = ' '
            for i, val in enumerate(_data, start=start):
                k = i - 1
                who = un[k]
                if val['uid'] == ctx.author.id:
                    who = f"-> {who}"
                sp = xpl[k]
                block += f"{langs.gns(i, locale, 2, False)}){s*4}{xp[k]}{s*(spaces-sp)}{who}\n"
        except (ValueError, IndexError):
            block += "No data available"
        s, e, t = langs.gns(start, locale), langs.gns(start + 9, locale), langs.gns(total, locale)
        return await general.send(langs.gls("leaderboards_tbl_league", locale, place, s, e, t, block), ctx.channel)
        # return await general.send(f"Top users in TBL - Sorted by League Points\nYour place: {place}\nShowing places {start:,} to {start + 9:,} of {total}"
        #                           f"\n{block}```", ctx.channel)


def setup(bot):
    bot.add_cog(Games(bot))
