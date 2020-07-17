import asyncio
import json

import discord
from discord.ext import commands

from core.utils import general, database, time, permissions
from languages import langs
from suager.utils import tbl, tbl_data


class TBL(commands.Cog):
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
        limit = 119 + level if level != 200 else 320
        next_in = f" - Next in: **{time.timedelta(60 - (now - regen_t))}**" if energy < limit else ""
        embed.add_field(name="Energy", inline=False, value=f"**{energy:,.0f}/{limit}**{next_in}")
        return await general.send(None, ctx.channel, embed=embed)

    @tbl.command(name="clan")
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
        embed.add_field(name="Totem 1", value=f"**{tbl_data.totems[t1['id'] - 1]['name']}**" if t1['id'] != 0 else "**Inactive totem**", inline=True)
        if t2["id"] != 0:
            e2 = t2["expiry"]
            r2 = f"**{tbl_data.totems[t2['id'] - 1]['name']}**\nExpires **{langs.td_ts(e2, suffix=True)}**" if e2 > now else "**Totem expired**"
        else:
            r2 = "**Inactive totem**"
        embed.add_field(name="Totem 2", value=r2, inline=True)
        if t3["id"] != 0:
            e3 = t3["expiry"]
            r3 = f"**{tbl_data.totems[t3['id'] - 1]['name']}**\nExpires **{langs.td_ts(e3, suffix=True)}**" if e3 > now else "**Totem expired**"
        else:
            r3 = "**Inactive totem**"
        embed.add_field(name="Totem 3", value=r3, inline=True)
        return await general.send(None, ctx.channel, embed=embed)

    @tbl.command(name="donate")
    async def tbl_donate(self, ctx: commands.Context, what: str, value: int):
        """ Donate to your TBL clan """
        now = int(time.now_ts())
        player, exists = tbl.get_player(ctx.author, self.db, now)
        if not exists:
            return await general.send(f"You have not played TBL yet. Run `{ctx.prefix}tbl play` at least once before using this.", ctx.channel)
        clan, exists = tbl.get_clan(ctx.guild, self.db)
        if not exists:
            return await general.send(f"This clan has not been fully created yet. Run `{ctx.prefix}tbl play` at least once before using this.", ctx.channel)
        if clan["usage"]:
            return await general.send("TBL is running in this clan at the moment, so this function is currently unavailable. Try again later.", ctx.channel)
        choice = what.lower()
        if choice == "nuts":
            nuts = player["nuts"]
            if nuts < value:
                return await general.send("You don't have enough Nuts to do that.", ctx.channel)
            self.db.execute("UPDATE tbl_player SET nuts=nuts-? WHERE uid=?", (value, ctx.author.id))
            self.db.execute("UPDATE tbl_clan SET nuts=nuts+? WHERE gid=?", (value, ctx.guild.id))
            word = langs.plural(value, "Nut")
        elif choice == "coins":
            coins = player["coins"]
            if coins < value:
                return await general.send("You don't have enough Coins to do that.", ctx.channel)
            self.db.execute("UPDATE tbl_player SET coins=coins-? WHERE uid=?", (value, ctx.author.id))
            self.db.execute("UPDATE tbl_clan SET coins=coins+? WHERE gid=?", (value, ctx.guild.id))
            word = langs.plural(value, "Coins")
        else:
            return await general.send("You need to specify either `nuts` or `coins`.", ctx.channel)
        return await general.send(f"Donated **{word}** to current clan.", ctx.channel)

    @tbl.group(name="totems")
    @permissions.has_permissions(kick_members=True)
    async def tbl_totems(self, ctx: commands.Context):
        """ Set TBL totems for your clan """
        if ctx.invoked_subcommand is None:
            return await general.send(f"`{ctx.prefix}tbl details totems` for information on totems\n`{ctx.prefix}tbl totems set` to set a totem\n"
                                      f"`{ctx.prefix}tbl totems upgrade` to upgrade a totem", ctx.channel)

    @tbl_totems.command(name="upgrade")
    async def tbl_totem_upgrade(self, ctx: commands.Context, totem_id: int = 0, upgrades: int = 1):
        """ Upgrade a TBL totem """
        clan, exists = tbl.get_clan(ctx.guild, self.db)
        if not exists:
            return await general.send(f"This clan has not been fully created yet. Run `{ctx.prefix}tbl play` at least once before using this.", ctx.channel)
        if clan["usage"]:
            return await general.send("TBL is running in this clan at the moment, so this function is currently unavailable. Try again later.", ctx.channel)
        levels = json.loads(clan["temple_levels"])
        if totem_id <= 0:
            return await general.send(f"Please enter a totem ID. These can be found with `{ctx.prefix}tbl details totems`.", ctx.channel)
        if totem_id >= 4:
            return await general.send("Totems of Senko and Cthulhu cannot be upgraded.", ctx.channel)
        if clan["upgrade_points"] < upgrades:
            return await general.send("This clan does not have enough Upgrade Points available. "
                                      "You will get more from leveling the clan up by playing TBL.", ctx.channel)
        levels[totem_id - 1] += upgrades
        self.db.execute("UPDATE tbl_clan SET upgrade_points=upgrade_points-?, temple_levels=? WHERE gid=?", (upgrades, json.dumps(levels), ctx.guild.id))
        new_level = langs.gns(levels[totem_id - 1])
        times = langs.plural(upgrades, "time")
        return await general.send(f"The **{tbl_data.totems[totem_id - 1]['name']}** has been successfully upgraded **{times}**. It is now "
                                  f"level **{new_level}.** You can see its new power multiplier with `{ctx.prefix}tbl details totems`", ctx.channel)

    @tbl_totems.command(name="set")
    async def tbl_totem_set(self, ctx: commands.Context, slot: int = 0, totem_id: int = -1):
        """ Set a TBL totem """
        clan, exists = tbl.get_clan(ctx.guild, self.db)
        if not exists:
            return await general.send(f"This clan has not been fully created yet. Run `{ctx.prefix}tbl play` at least once before using this.", ctx.channel)
        if clan["usage"]:
            return await general.send("TBL is running in this clan at the moment, so this function is currently unavailable. Try again later.", ctx.channel)
        totems = json.loads(clan["temples"])
        nuts = clan["nuts"]
        totem_amount = len(tbl_data.totems)
        if slot <= 0:
            return await general.send("Please specify which totem you want to set. (1-3)", ctx.channel)
        if slot > 3:
            return await general.send("There can be only 3 totems", ctx.channel)
        if totem_id < 0:
            return await general.send(f"Please enter a totem ID. These can be found with `{ctx.prefix}tbl details totems`.", ctx.channel)
        if totem_id > totem_amount:
            return await general.send(f"There is no totem with ID {totem_id}", ctx.channel)
        active_totems = [totem['id'] for totem in totems]
        if totem_id in active_totems and totem_id != 0:
            return await general.send("This totem is already active", ctx.channel)
        c = langs.plural(0, "Nut")
        if slot == 1:
            totems[0]["id"] = totem_id
        if slot in [2, 3]:
            totems[slot - 1]["id"] = totem_id
            expiry = totems[slot - 1]["expiry"]
            now = time.now_ts()
            if expiry > now:
                await general.send("As there is already an active totem in this slot, the totem ID will be updated, however the expiry time will remain "
                                   "the same, and no Nuts will be charged.", ctx.channel)
            else:
                if totem_id == 0:
                    return await general.send("This totem has already expired, you can't reset it.", ctx.channel)
                cost = (13 if slot == 2 else 37) * ctx.guild.member_count
                if nuts < cost:
                    n = langs.gns(nuts)
                    c = langs.plural(cost, "Nut")
                    return await general.send(f"This clan does not have sufficient balance to activate this totem right now. ({n}/{c})", ctx.channel)
                totems[slot - 1]["expiry"] = now + 72 * 3600
                nuts -= cost
                c = langs.plural(cost, "Nut")
        self.db.execute("UPDATE tbl_clan SET nuts=?, temples=? WHERE gid=?", (nuts, json.dumps(totems), ctx.guild.id))
        name = f"Set **{tbl_data.totems[totem_id - 1]['name']}** to" if totem_id > 0 else "**Reset**"
        return await general.send(f"{name} to Slot **{slot}** for **{c}**.", ctx.channel)

    @tbl.command(name="location")
    async def tbl_set_location(self, ctx: commands.Context, location_id: int = -1):
        """ Set your location """
        player, exists = tbl.get_player(ctx.author, self.db, 0)
        if not exists:
            return await general.send(f"You have not played TBL yet. Run `{ctx.prefix}tbl play` at least once before using this.", ctx.channel)
        locations = tbl_data.locations
        if location_id < 0:
            return await general.send("You need to specify which location you want to be in. Entering `0` will reset it, entering `1`-`17` will set you to the "
                                      "specified one", ctx.channel)
        if location_id > len(locations):
            return await general.send(f"Location with ID {location_id} does not exist.", ctx.channel)
        location = tbl.get_location(location_id, 201)
        output = f"Set your location to **{location['name']} ({location['en']})**" if location_id > 0 else "**Reset** you location"
        self.db.execute("UPDATE tbl_player SET location=? WHERE uid=?", (location_id, ctx.author.id))
        return await general.send(f"{output}. Note that if your level is not high enough to be there, it will be set to the nearest available.", ctx.channel)

    @tbl.group(name="details", aliases=["documentation", "docs", "explain"])
    async def tbl_docs(self, ctx: commands.Context):
        """ Information about TBL """
        if ctx.invoked_subcommand is None:
            sub_commands = {
                "levels": "Explains how leveling works",
                "game": "Explains how the main game works",
                "locations": "Shows details on in-game locations and how they work",
                "totems": "Explains the clan totems and what they do",
                "leagues": "Shows details on leagues",
                "clans": "What clans do",
                "seasons": "Shows details on league seasons"
            }
            data = [[key, value] for key, value in sub_commands.items()]
            data.sort(key=lambda x: x[0])
            _data = [f"`{key}` - {value}" for key, value in data]
            return await general.send("Here are subcommands which can help you:\n" + "\n".join(_data), ctx.channel)

    @tbl_docs.command(name="game")
    async def tbl_docs_game(self, ctx: commands.Context):
        """ Information on how TBL works """
        return await general.send(
            "Each round costs **10 Energy**, and the game keeps going until you no longer have enough energy to continue.\nEnergy regenerates at the rate of "
            "**1 per minute**.\n\nWhether you win the level or not is chosen at random. The chance of winning can be seen in the locations details.\nYou can "
            "also be shaman (chance: **16%**) and get extra rewards from the round.\nThe amount of people in the round depends on the current time. You can "
            "see the time in TBL (which is used to calculate the activity level) using `{ctx.prefix}timetb`. Activity is higher during hours **8 to 24**.\n"
            "The more people are active - the higher rewards you can potentially get from each round.\nAt the end of a round, a portion of energy will "
            "regenerate, based on the level length, and then the game will continue until you don't have enough energy to do so.\n\nFor each round you can get "
            "the following rewards:\nNuts, XP, and Clan XP - each winning round,\nExtra nuts and XP, and also Shaman XP - for each save if you are shaman "
            "during the round.\nIf you win, you also get League Points, which are used for leaderboards. League Seasons last around a month and will reward "
            "you with extra Nuts, and the top 5 will also get extra Coins.", ctx.channel)

    @tbl_docs.command(name="levels")
    async def tbl_docs_levels(self, ctx: commands.Context):
        """ Information on levels """
        return await general.send(
            "You get normal XP for each successful round, and also for saves when you get to be shaman. Normal levels will give you higher energy caps, "
            "decrease your chance of losing rounds and can give you a new title.\nYou get shaman XP for saves when you play as shaman. Reaching new shaman "
            "levels doesn't do anything so far.\nYou get clan XP for each successful round. Reaching higher clan levels will give Upgrade Points, which can "
            "be used to level up your totems. These can help your server's members reach higher levels faster.", ctx.channel)

    @tbl_docs.command(name="totems")
    async def tbl_docs_totems(self, ctx: commands.Context):
        """ Information on totems """
        clan, _ = tbl.get_clan(ctx.guild, self.db)
        del _
        levels = json.loads(clan["temple_levels"])
        totems = tbl_data.totems
        outputs = []
        for i in range(len(levels)):
            totem = totems[i]
            level = levels[i]
            effect = 0.06 + 0.04 * level if i == 0 else 0.07 + 0.03 * level if i == 1 else 0.075 + 0.025 * level if i == 2 else -1
            effect_str = langs.gfs(effect, "en_gb", 1, True)
            if effect != -1:
                totem_desc = totem['desc'] % effect_str
            else:
                totem_desc = totem['desc']
            outputs.append(f"{langs.gns(i + 1)}) **{totem['name']}** - Level **{langs.gns(level)}**:\n{totem_desc}")
        cost_2 = langs.gns(13 * ctx.guild.member_count)
        cost_3 = langs.gns(37 * ctx.guild.member_count)
        return await general.send("This is information on your clan's totems.\n\n" + "\n".join(outputs) +
                                  f"\n\nYou can check current totem stats using `{ctx.prefix}tbl clan`.\nYou can assign totems using `{ctx.prefix}tbl totems`."
                                  f"\nThe first totem is **free**, the 2nd costs **{cost_2} Nuts** and the 3rd costs **{cost_3} Nuts**. Paid totems will "
                                  f"expire after **72 hours**.\nYou can also buy extra Upgrade Points for **3 coins each**.", ctx.channel)

    @tbl_docs.command(name="leagues")
    async def tbl_docs_leagues(self, ctx: commands.Context):
        """ Information on TBL Leagues """
        leagues = tbl_data.leagues
        names = []
        points = []
        outputs = []
        for league in leagues:
            names.append(league['name'])
            points.append(langs.gns(league['score']))
        for i in range(1, len(leagues)):
            outputs.append(f"`{names[i]:<{len(max(names))}} - {points[i]:>{len(points[-1])}} Points`")
        season_end = tbl_data.seasons[self.season][1]
        await general.send("You get league points by winning rounds in TBL.\nThose who have the highest points at the end of a season will receive coins. "
                           "Everyone gets 1/5 of their points converted into extra Nuts, 1/10 of their league points get carried over into the next season. "
                           "There is an extra reward for being in the top 5 at the end of the season\nThe current season is "
                           f"**Season {langs.gns(self.season)}** - Ends in **{langs.td_dt(season_end, brief=True)}**", ctx.channel)
        await general.send("These are the leagues in TBL:\n" + "\n".join(outputs), ctx.channel)
        # await general.send("\nAnd these are the prizes for being in the top 5 globally:\n" +
        #                    "\n".join([f"#{i}: **{p}**" for i, p in enumerate(prizes, start=1)]), ctx.channel)

    @tbl_docs.command(name="seasons")
    async def tbl_docs_seasons(self, ctx: commands.Context):
        """ Information on TBL Seasons """
        seasons = list(tbl_data.seasons.items())
        season_b = self.season - 2 if self.season - 2 > 0 else 0
        season_l = self.season + 8
        season_data = ""
        for season, data in seasons[season_b:season_l]:
            season_data += f"\nSeason {langs.gns(season)}: from **{langs.gts_date(data[0])}** to **{langs.gts_date(data[1])}**"
            if season == self.season:
                season_data += " __(current season)__"
        await general.send("TBL has League Seasons, which means that about every month 1/5 of your League Points is converted into Nuts, and 1/10 of the "
                           "points carry over into the next Season. People who are in the Top 5 also get extra coins. Here are a few past seasons and "
                           f"the upcoming ones:{season_data}", ctx.channel)

    @tbl_docs.command(name="locations")
    async def tbl_docs_loc(self, ctx: commands.Context, location_id: int = 0):
        """ Information on TBL locations """
        if location_id == 0:
            locations = tbl_data.locations
            data = []
            for loc in locations:
                data.append(f"Loc. ID **{loc['id']}** - **{loc['name']}**")
            return await general.send("These are the TBL locations:\n" + "\n".join(data) +
                                      f"\nYou can use `{ctx.prefix}tbl details locations <id>` for more data on a specific location", ctx.channel)
        else:
            location = tbl.get_location(location_id, 201)
            embed = discord.Embed(colour=general.random_colour())
            embed.title = f"Information on Loc. ID **{location_id}**"
            embed.description = location["desc_en"]
            embed.add_field(name="Location Name (RSL-1)", value=location["name"], inline=False)
            embed.add_field(name="Location Name (English)", value=location["en"], inline=False)
            embed.add_field(name="Minimum XP Level", value=f"**{langs.gns(location['level'])}**", inline=True)
            a1, a2 = location["araksan"]
            embed.add_field(name="Nuts per round", value=f"**{langs.gns(a1)}-{langs.gns(a2)}**", inline=True)
            x1, x2 = location["xp"]
            embed.add_field(name="XP per round", value=f"**{langs.gns(x1)}-{langs.gns(x2)}**", inline=True)
            embed.add_field(name="Shaman XP per save", value=f"**{langs.gns(location['sh'])}**", inline=True)
            p1, p2 = location["points"]
            embed.add_field(name="League Points per round", value=f"**{langs.gns(p1)}-{langs.gns(p2)}**", inline=True)
            embed.add_field(name="Average level length", value=f"**{langs.td_int(location['ll'])}**", inline=True)
            player, _ = tbl.get_player(ctx.author, self.db, time.now_ts())
            level = player['level']
            death_rate = location['dr'] / (1 + (level - 1) / 64)
            embed.add_field(name="Death Rate", value=f"**{langs.gfs(death_rate, 'en_gb', 0, True)}** at level **{langs.gns(level)}**", inline=False)
            embed.add_field(name="Current activity", value=f"**{langs.gns(tbl.get_activity(location['activity']))} people**", inline=False)
            embed.set_footer(text="Note that location rewards do not take totem bonuses into account.")
            return await general.send(None, ctx.channel, embed=embed)

    @tbl_docs.command(name="clans")
    async def tbl_clans(self, ctx: commands.Context):
        """ Tells more about clans """
        return await general.send("Clans represent of your server within TBL. It provides benefits for the whole clan. Clan XP can be gained from just "
                                  "playing TBL, and will provide your clan with Upgrade Points, which can be used to upgrade your clan's totems. Those will "
                                  "give you more rewards in TBL. The first totem is free, while the second and third will cost Nuts and will expire after "
                                  "72 hours. You can donate Nuts and Coins to your clan, and then the server moderators can use them for totems.\n"
                                  f"Here are some useful commands:\n`{ctx.prefix}tbl donate` - to donate Nuts and/or Coins to your clan\n"
                                  f"`{ctx.prefix}tbl details totems` - for information on totems\n`{ctx.prefix}tbl totems set` - to set a totem\n"
                                  f"`{ctx.prefix}tbl totems upgrade` - to upgrade a totem", ctx.channel)

    @tbl.command(name="leaderboard", aliases=["top", "lb"])
    async def tbl_leaderboard(self, ctx: commands.Context, page: int = 0):
        """ TBL Leaderboard """
        data = self.db.fetch("SELECT * FROM tbl_player ORDER BY points DESC")
        if not data:
            return await general.send("I have no data saved for this server so far.", ctx.channel)
        block = "```fix\n"
        un = []   # User names
        xp = []   # XP
        xpl = []  # XP string lengths
        for user in data:
            name = f"{user['name']}#{user['disc']:04d}"
            un.append(name)
            val = f"{user['points']:,.0f}"
            xp.append(val)
            xpl.append(len(val))
        total = len(xp)
        place = "unknown"
        n = 0
        for x in range(len(data)):
            if data[x]['uid'] == ctx.author.id:
                place = f"#{x + 1}"
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
            for i, val in enumerate(_data, start=start):
                k = i - 1
                who = un[k]
                if val['uid'] == ctx.author.id:
                    who = f"-> {who}"
                s = ' '
                sp = xpl[k]
                block += f"{i:2d}){s*4}{xp[k]}{s*(spaces-sp)}{who}\n"
        except ValueError:
            block += "No data available"
        return await general.send(f"Top users in TBL - Sorted by League Points\nYour place: {place}\nShowing places {start:,} to {start + 9:,} of {total}"
                                  f"\n{block}```", ctx.channel)


def setup(bot):
    bot.add_cog(TBL(bot))
