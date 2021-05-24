import asyncio
import json
import random
from datetime import datetime, timezone
from typing import Optional, Union

import discord
from discord.ext.commands import Context

from cobble.utils import ga78
from core.utils import database, general, time
from languages import langs


def level_gen(max_level: int, addition) -> list[int]:  # addition = function
    req = 0
    xp = []
    for x in range(max_level):
        # base = 1.25 * x ** 2 + x * 80 + 250
        # base = x ** 2 + 99 * x + 175
        base = addition(x)
        req += int(base)
        if x not in bad:
            xp.append(int(req))
        else:
            xp.append(xp[-1])
    return xp


def dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


db = database.Database()
bad = [69, 420, 666, 1337]
player_max = 250
shaman_max = 175
guild_max = 200
clan_max = 250
player_levels = level_gen(player_max, lambda x: 4.4 * x ** 2.2 + 195.6 * x)
for _ in range(25000 - player_max):
    player_levels.append(player_levels[-1] + 2500000)
shaman_levels = level_gen(shaman_max, lambda x: 0.27 * x ** 3 + 7.5 * x ** 2 + 92.23 * x)
guild_levels = level_gen(guild_max, lambda x: 10 * x ** 1.8 + 490 * x)
clan_levels = level_gen(clan_max, lambda x: 7.5 * x ** 2 + 242.5 * x)
# Activity based on TBL time: midnight, 3am, 6am, 9am, noon, 3pm, 6pm, 9pm
activity_hour = [0.91, 0.37, 0.74, 1.00, 1.27, 1.21, 1.37, 1.13]
# Monthly variation of activity
activity_month = [1.12, 0.91, 0.83, 1.00, 1.07, 1.15, 1.21, 1.11, 1.09, 1.12, 1.08, 1.14, 1.31, 1.40, 1.56, 1.35]
players_base = 50  # Base amount of players per location
energy_consumption = 10
energy_regen = 120
start_araksat = 500
start_coins = 10
start_energy = 300
start_shaman_probability = 0.08
start_tax_gain = 0.025
clock = ['🕛', '🕒', '🕕', '🕘']


# No League, Wood, Stone, Copper, Tin, Bronze, Iron, Silver, Gold, Platinum, Ruby, Emerald, Sapphire, Diamond
leagues = [0, 500, 2000, 5000, 10000, 20000, 50000, 100000, 250000, 500000, 1000000, 5000000, 20000000, 100000000]


events = {  # Events before January 2021 removed because those already passed anyways
    "araksat": [
        [dt(2021,  1, 16), dt(2021,  1, 18), 1.50],
        [dt(2021,  1, 27), dt(2021,  1, 28), 2.50],
        [dt(2021,  1, 30), dt(2021,  2,  1), 1.50],
        [dt(2021,  2, 27), dt(2021,  3,  2), 1.50],
        [dt(2021,  3, 17), dt(2021,  3, 18), 2.75],
        [dt(2021,  3, 30), dt(2021,  4,  2), 1.50],
        [dt(2021,  4, 17), dt(2021,  4, 18), 2.75],
        [dt(2021,  4, 29), dt(2021,  5,  2), 1.50],
        [dt(2021,  5, 16), dt(2021,  5, 19), 1.50],
        [dt(2021,  6, 14), dt(2021,  6, 17), 1.50],
        [dt(2021,  6, 25), dt(2021,  6, 26), 2.25],
    ],
    "xp": [
        [dt(2021,  1, 23), dt(2021,  1, 25), 1.50],
        [dt(2021,  1, 27), dt(2021,  1, 28), 2.50],
        [dt(2021,  3, 15), dt(2021,  3, 20), 1.50],
        [dt(2021,  4, 15), dt(2021,  4, 18), 1.50],
        [dt(2021,  5, 13), dt(2021,  5, 14), 2.75],
        [dt(2021,  5, 30), dt(2021,  6,  2), 1.50],
        [dt(2021,  6, 25), dt(2021,  6, 26), 2.75],
        [dt(2021,  6, 29), dt(2021,  7,  2), 1.50],
    ]
}
seasons = [
    [dt(2020,  7, 17), dt(2020,  9,  1)],  # 01
    [dt(2020,  9,  1), dt(2020, 10,  1)],  # 02
    [dt(2020, 10,  1), dt(2020, 10, 30)],  # 03
    [dt(2020, 10, 30), dt(2020, 11, 30)],  # 04
    [dt(2020, 11, 30), dt(2020, 12, 25)],  # 05
    [dt(2020, 12, 25), dt(2021,  1, 27)],  # 06
    [dt(2021,  1, 27), dt(2021,  2, 23)],  # 07
    [dt(2021,  2, 23), dt(2021,  3, 17)],  # 08
    [dt(2021,  3, 17), dt(2021,  4, 18)],  # 09
    [dt(2021,  4, 18), dt(2021,  5, 19)],  # 10
    [dt(2021,  5, 19), dt(2021,  6, 16)],  # 11
    [dt(2021,  6, 16), dt(2021,  7, 13)],  # 12
    [dt(2021,  7, 13), dt(2021,  8, 21)],  # 13
    [dt(2021,  8, 21), dt(2021, 10,  1)],  # 14
    [dt(2021, 10,  1), dt(2021, 10, 30)],  # 15
    [dt(2021, 10, 30), dt(2021, 11, 30)],  # 16
    [dt(2021, 11, 30), dt(2021, 12, 25)],  # 17
    [dt(2021, 12, 25), dt(2022,  1, 27)],  # 18
    [dt(2022,  1, 27), dt(2022,  3,  1)],  # 19
    [dt(2022,  3,  1), dt(2022,  4,  2)],  # 20
    [dt(2022,  4,  2), dt(2022,  5,  1)],  # 21
    [dt(2022,  5,  1), dt(2022,  6,  1)],  # 22
    [dt(2022,  6,  1), dt(2022,  7,  1)],  # 23
    [dt(2022,  7,  1), dt(2022,  8,  1)],  # 24
    [dt(2022,  8,  1), dt(2022,  9,  1)],  # 25
    [dt(2022,  9,  1), dt(2022, 10,  1)],  # 26
    [dt(2022, 10,  1), dt(2022, 11,  1)],  # 27
    [dt(2022, 11,  1), dt(2022, 12,  1)],  # 28
    [dt(2022, 12,  1), dt(2023,  1,  1)],  # 29
    [dt(2023,  1,  1), dt(2023,  1, 27)],  # 30
    [dt(2023,  1, 27), dt(2023,  3,  1)],  # 31
    [dt(2023,  3,  1), dt(2023,  4,  2)],  # 32
]


def player_level(old_lvl: int, xp: float):
    new_lvl = 0
    for level in player_levels:
        if level <= xp:
            new_lvl += 1
        else:
            break
    return new_lvl, new_lvl - old_lvl


def shaman_level(old_lvl: int, xp: float):
    new_lvl = 0
    for level in shaman_levels:
        if level <= xp:
            new_lvl += 1
        else:
            break
    return new_lvl, new_lvl - old_lvl


def guild_level(old_lvl: int, xp: float):
    new_lvl = 0
    for level in guild_levels:
        if level <= xp:
            new_lvl += 1
        else:
            break
    return new_lvl, new_lvl - old_lvl


def clan_level(old_lvl: int, xp: float):
    new_lvl = 0
    for level in clan_levels:
        if level <= xp:
            new_lvl += 1
        else:
            break
    return new_lvl, new_lvl - old_lvl


def get_league(points: int, locale: str) -> tuple[str, str]:
    league, next_league = 0, "0"
    for i, j in enumerate(leagues):
        if j <= points:
            league = i
            next_league = langs.gls("generic_max", locale) if i == len(leagues) - 1 else langs.plural(leagues[i + 1], "kuastall_tbl_pl_league_points2", locale)
            # langs.gns(leagues[i + 1], locale)
    return langs.get_data("kuastall_tbl_leagues", locale)[league], next_league


def get_season():
    now = time.now()
    for season, data in enumerate(seasons):
        start, end = data
        if end < now:
            continue
        elif start > now:
            continue
        return season + 1


def get_events(what: str):
    now = time.now()
    for start, end, mult in events[what]:
        if end < now:
            continue
        elif start > now:
            continue
        return mult, end
    return 1.0, now


def get_next(name: str, level: int, locale: str) -> str:
    system = []
    max_level = -1
    if name == "player":
        system = player_levels
        max_level = player_max
    elif name == "shaman":
        system = shaman_levels
        max_level = shaman_max
    elif name == "clan":
        system = clan_levels
        max_level = clan_max
    elif name == "guild":
        system = guild_levels
        max_level = guild_max
    if level >= max_level:
        return langs.gls("generic_max", locale)
    else:
        return langs.gns(system[level], locale)


class Clan:
    def __init__(self, data: dict, new: bool):
        self.id: int = data["clan_id"]
        self.name: str = data["name"]
        self.description: Optional[str] = data["description"]
        self.type: int = data["type"]
        self.level: int = data["level"]
        self.xp: float = data["xp"]
        self.points: float = data["points"]
        self.owner: int = data["owner"]
        self.locations: list = json.loads(data["locations"])
        self.araksat: float = data["araksat"]
        self.tax_gain_level: int = data["tax_gain"]
        self.tax_gain: float = start_tax_gain + 0.001 * self.tax_gain_level
        self.reward_boost_level: int = data["reward_boost"]
        self.reward_boost: float = 0.005 * self.reward_boost_level
        self.energy_limit_boost_level: int = data["energy_limit_boost"]
        self.energy_limit_boost: float = 1.0 * self.energy_limit_boost_level
        self.energy_regen_boost_level: int = data["energy_regen_boost"]
        self.energy_regen_boost: float = 0.7 * self.energy_regen_boost_level
        self.is_new: bool = new
        self.member_count: int = len(db.fetch("SELECT * FROM tbl_player WHERE clan=?", (self.id,))) if not self.is_new else 1

    @classmethod
    def new(cls, name: str, invite_type: int, owner: int):
        """ Create a new clan """
        clan_id = random.randint(1000000, 9999999)
        check_exists = db.fetchrow("SELECT * FROM tbl_clan WHERE clan_id=?", (clan_id,))
        while check_exists is not None:
            clan_id = random.randint(1000000, 9999999)
            check_exists = db.fetchrow("SELECT * FROM tbl_clan WHERE clan_id=?", (clan_id,))
        return cls({"clan_id": clan_id, "name": name, "description": None, "type": invite_type, "level": 1, "xp": 0.0, "points": 0.0, "owner": owner,
                    "locations": "[]", "araksat": 0.0, "tax_gain": 0, "reward_boost": 0, "energy_limit_boost": 0, "energy_regen_boost": 0}, True)

    @classmethod
    def from_db(cls, clan: int):
        """ Load clan from database """
        data = db.fetchrow("SELECT * FROM tbl_clan WHERE clan_id=?", (clan,))
        if not data:
            return None
        else:
            return cls(data, False)

    def save(self):
        """ Save the clan data to database """
        location_data = json.dumps(self.locations)
        if self.is_new:
            db.execute("INSERT INTO tbl_clan VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                self.id, self.name, self.type, self.level, self.xp, self.points, self.owner, location_data, self.araksat, self.tax_gain_level, self.reward_boost_level,
                self.energy_limit_boost_level, self.energy_regen_boost_level))
        else:
            db.execute("UPDATE tbl_clan SET name=?, description=?, type=?, level=?, xp=?, points=?, owner=?, locations=?, araksat=?, tax_gain=?, "
                       "reward_boost=?, energy_limit_boost=?, energy_regen_boost=? WHERE clan_id=?", (
                           self.name, self.description, self.type, self.level, self.xp, self.points, self.owner, location_data, self.araksat, self.tax_gain_level,
                           self.reward_boost_level, self.energy_limit_boost_level, self.energy_regen_boost_level, self.id))

    def status(self, ctx: Context, locale: str) -> discord.Embed:
        """ Returns an embed of the clan's status """
        embed = discord.Embed(colour=general.random_colour())
        embed.title = langs.gls("kuastall_tbl_clan_stats", locale, self.name)
        embed.description = self.description
        embed.set_footer(text=f"Clan ID: {self.id}")
        embed.timestamp = time.now(None)
        r1, r2, r3 = langs.gns(self.level, locale), langs.gfs(self.xp, locale, 1), get_next("clan", self.level, locale)
        types = langs.get_data("kuastall_tbl_clan_types", locale)
        owner = ctx.bot.get_user(self.owner)
        embed.add_field(name=langs.gls("kuastall_tbl_clan_owner", locale), value=general.bold(str(owner)), inline=False)
        embed.add_field(name=langs.gls("kuastall_tbl_clan_members", locale), value=general.bold(langs.gns(self.member_count, locale)), inline=False)
        embed.add_field(name=langs.gls("kuastall_tbl_clan_type", locale), value=types[self.type], inline=False)
        embed.add_field(name=langs.gls("kuastall_tbl_clan_level", locale), value=langs.gls("kuastall_tbl_clan_xp", locale, r1, r2, r3), inline=False)
        embed.add_field(name=langs.gls("kuastall_tbl_clan_araksat", locale), value=general.bold(langs.gfs(self.araksat, locale, 1)), inline=True)
        embed.add_field(name=langs.gls("kuastall_tbl_clan_points", locale), value=general.bold(langs.gfs(self.points, locale, 1)), inline=True)
        embed.add_field(name=langs.gls("kuastall_tbl_clan_tax_gain", locale), value=general.bold(langs.gfs(self.tax_gain, locale, 1, True)), inline=True)
        embed.add_field(name=langs.gls("kuastall_tbl_clan_rewards", locale), value=general.bold(langs.gfs(self.reward_boost, locale, 1, True)), inline=True)
        embed.add_field(name=langs.gls("kuastall_tbl_clan_elb", locale), value=general.bold(langs.gfs(self.energy_limit_boost, locale, 1)), inline=True)
        erb = general.bold(langs.gfs(self.energy_regen_boost, locale, 1)) + langs.gls("time_s", locale)
        embed.add_field(name=langs.gls("kuastall_tbl_clan_erb", locale), value=erb, inline=True)
        clan_locations = []
        names = langs.get_data("kuastall_tbl_locations", locale)
        for location in sorted(self.locations, key=lambda x: x["id"]):
            loc = locations[location["id"] - 1]
            name = names[loc.id - 1]
            expiry = langs.td_ts(location["expiry"], locale, 3, True, True)
            clan_locations.append(langs.gls("kuastall_tbl_clan_location", locale, name, loc.id, expiry))
        clan_loc_out = "\n".join(clan_locations) if clan_locations else langs.gls("generic_none", locale)
        embed.add_field(name=langs.gls("kuastall_tbl_clan_locations", locale), value=clan_loc_out, inline=False)
        return embed


class Guild:
    def __init__(self, data: dict, new: bool):
        self.id: int = data["gid"]
        self.name: str = data["name"]
        self.level: int = data["level"]
        self.xp: float = data["xp"]
        self.coins: float = data["coins"]
        self.araksat_boost_level: int = data["araksat_boost"]
        self.araksat_boost: float = 0.01 * self.araksat_boost_level
        self.xp_boost_level: int = data["xp_boost"]
        self.xp_boost: float = 0.01 * self.xp_boost_level
        self.energy_reduction_level: int = data["energy_reduction"]
        self.energy_reduction: float = 0.1 * self.energy_reduction_level
        self.is_new: bool = new

    @classmethod
    def new(cls, gid: int, name: str):
        """ Add a new guild """
        return cls({"gid": gid, "level": 1, "xp": 0.0, "coins": 0.0, "araksat_boost": 0, "xp_boost": 0, "energy_reduction": 0, "name": name}, True)

    @classmethod
    def from_db(cls, guild: discord.Guild):
        """ Load guild from database """
        data = db.fetchrow("SELECT * FROM tbl_guild WHERE gid=?", (guild.id,))
        if not data:
            return cls.new(guild.id, guild.name)
        else:
            data["name"] = guild.name
            return cls(data, False)

    def save(self):
        """ Save the guild data to database """
        if self.is_new:
            db.execute("INSERT INTO tbl_guild VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (
                self.id, self.name, self.level, self.xp, self.coins, self.araksat_boost_level, self.xp_boost_level, self.energy_reduction_level))
        else:
            db.execute("UPDATE tbl_guild SET name=?, level=?, xp=?, coins=?, araksat_boost=?, xp_boost=?, energy_reduction=? WHERE gid=?", (
                self.name, self.level, self.xp, self.coins, self.araksat_boost_level, self.xp_boost_level, self.energy_reduction_level, self.id))

    def status(self, locale: str, icon_url: str) -> discord.Embed:
        """ Returns an embed of the guild's status """
        embed = discord.Embed(colour=general.random_colour())
        embed.title = langs.gls("kuastall_tbl_guild_stats", locale, self.name)
        embed.set_thumbnail(url=icon_url)
        embed.set_footer(text=f"Guild ID: {self.id}")
        embed.timestamp = time.now(None)
        r1, r2, r3 = langs.gns(self.level, locale), langs.gfs(self.xp, locale, pre=0), get_next("guild", self.level, locale)
        embed.add_field(name=langs.gls("kuastall_tbl_guild_level", locale), value=langs.gls("kuastall_tbl_guild_xp", locale, r1, r2, r3), inline=False)
        embed.add_field(name=langs.gls("kuastall_tbl_guild_coins", locale), value=general.bold(langs.gfs(self.coins, locale, pre=1)), inline=False)
        r4, r5 = langs.gfs(self.araksat_boost, locale, 0, True), langs.gfs(self.xp_boost, locale, 0, True)
        embed.add_field(name=langs.gls("kuastall_tbl_guild_rewards", locale), value=langs.gls("kuastall_tbl_guild_boost", locale, r4, r5), inline=False)
        embed.add_field(name=langs.gls("kuastall_tbl_guild_energy", locale), value=general.bold(langs.gfs(self.energy_reduction, locale, 1)), inline=False)
        return embed


class Location:
    def __init__(self, loc_id: int, araksat: list[int], xp: list[int], sh: int, points: list[int], level: int, popularity: float, min_ll: int,
                 death: float, max_ll: int):
        self.id = loc_id              # Location ID
        self.araksat = araksat
        self.xp = xp
        self.shaman_xp = sh
        self.points = points          # League Points
        self.level_req = level
        self.popularity = popularity  # Total player multiplier, ~50 squirrels
        self.min = min_ll             # Minimal completion time
        self.death = death            # Death rate
        self.max = max_ll             # Level Length
        self.base_activity = self.get_activity()

    def get_activity(self):
        """ Get the location's activity multiplier """
        now = ga78.time_kargadia(tz=2)
        hour = now.hour + (now.minute / 60)
        al = len(activity_hour)
        part, mod = divmod(hour, 3)  # It's now 3 hours because 24 hours instead of 32
        # I have no idea how this works, but that's what I had from Suager v6 TBL
        month_mult = ((activity_month[now.month - 1] * (16 - now.day) + activity_month[now.month] * now.day) if now.day < 16 else activity_month[now.month] * 16
                      if now.day == 16 else (activity_month[now.month] * (32 - now.day) + activity_month[(now.month + 1) % 16] * (now.day - 16))) / 16
        return self.popularity * (((activity_hour[int(part)] * mod + activity_hour[int(part + 1) % al] * (3 - mod)) / 3) * month_mult)

    def clan(self, clan: Clan) -> int:
        """ Get the locations activity if it's in a clan """
        activity = clan.member_count * 0.3
        if activity <= 3:
            activity = 3
        if clan.member_count == 2:
            activity = 2
        self.base_activity = self.get_activity()  # Update the activity level up to current time
        activity *= self.base_activity
        if activity < 2:
            activity = 2
        if activity > clan.member_count:
            activity = clan.member_count
        return int(activity)

    def normal(self) -> int:
        """ Get the location's normal activity """
        self.base_activity = self.get_activity()  # Update the activity level up to current time
        return int(players_base * self.base_activity)

    def death_rate_level(self, xp_level: int):
        if xp_level > 250:
            xp_level = 250
        return self.death / (1 if xp_level <= 50 else 1 + (xp_level - 50) / 100)  # At level 250: x3.00

    def status(self, locale: str, level: int) -> discord.Embed:
        """ Returns an embed of the location's status """
        embed = discord.Embed(colour=general.random_colour())
        location_names = langs.get_data("kuastall_tbl_locations", locale)
        location_name = location_names[self.id - 1]
        location_desc = langs.get_data("kuastall_tbl_descriptions", locale)
        embed.title = langs.gls("kuastall_tbl_location_stats", locale, location_name)
        embed.description = location_desc[self.id - 1]
        embed.set_footer(text=f"Location ID: {self.id}")
        embed.timestamp = time.now(None)
        a1, a2 = self.araksat
        x1, x2 = self.xp
        l1, l2 = self.points
        r1, r2, r3, r4, r5, r6, r7 = langs.gns(a1, locale), langs.gns(a2, locale), langs.gns(x1, locale), langs.gns(x2, locale), langs.gns(l1, locale), \
            langs.gns(l2, locale), langs.gns(self.shaman_xp, locale)
        r8 = langs.gns(self.level_req, locale)
        r9 = langs.gns(self.normal(), locale)
        r10, r11 = langs.td_int(self.min, locale, brief=True, suffix=False), langs.td_int(self.max, locale, brief=True, suffix=False)
        if level > 250:
            level = 250
        r12 = langs.gls("kuastall_tbl_locations_death2", locale, langs.gfs(self.death_rate_level(level), locale, 1, True), langs.gns(level, locale))
        embed.add_field(name=langs.gls("kuastall_tbl_location_level", locale), value=general.bold(r8), inline=True)
        embed.add_field(name=langs.gls("kuastall_tbl_location_players", locale), value=general.bold(r9), inline=True)
        embed.add_field(name=langs.gls("kuastall_tbl_location_points", locale), value=general.bold(f"{r5}-{r6}"), inline=True)
        embed.add_field(name=langs.gls("kuastall_tbl_location_araksat", locale), value=general.bold(f"{r1}-{r2}"), inline=True)
        embed.add_field(name=langs.gls("kuastall_tbl_location_xp", locale), value=general.bold(f"{r3}-{r4}"), inline=True)
        embed.add_field(name=langs.gls("kuastall_tbl_location_sh", locale), value=general.bold(r7), inline=True)
        embed.add_field(name=langs.gls("kuastall_tbl_location_death", locale), value=r12, inline=True)
        embed.add_field(name=langs.gls("kuastall_tbl_location_time_min", locale), value=general.bold(r10), inline=True)
        embed.add_field(name=langs.gls("kuastall_tbl_location_time_max", locale), value=general.bold(r11), inline=True)
        return embed


locations = [
    Location(1, [4, 7], [15, 25], 4, [25, 60], 1, 1.00, 30, 0.07, 90),                    # 01 - Floating Islands / Leitannan Azdallat / Летающие Острова
    Location(2, [5, 8], [27, 50], 6, [35, 70], 7, 0.94, 45, 0.15, 105),                   # 02 - The Mountains of Snow / Na Kirtinat Kalvadan / Хребты Снега
    Location(3, [7, 9], [40, 60], 7, [50, 100], 12, 1.07, 50, 0.17, 120),                 # 03 - The Swamp / Taivead / Топи
    Location(4, [9, 11], [50, 75], 9, [75, 125], 20, 1.32, 60, 0.14, 130),                # 04 - Squirrels City / Bylkangar / Белкоград
    Location(5, [11, 14], [60, 85], 11, [100, 150], 30, 1.12, 65, 0.16, 140),             # 05 - Valleys of the Sun / Valliat na Sennon / Долины Солнца
    Location(6, [14, 17], [70, 100], 13, [125, 185], 40, 0.52, 75, 0.22, 150),            # 06 - Blue Sea / Veksan Vaidaat / Синее Море
    Location(7, [17, 20], [85, 125], 17, [150, 225], 50, 1.21, 90, 0.27, 160),            # 07 - Veilaran Bylkaddan Peaskat / Великая Беличья Пустыня
    Location(8, [20, 25], [100, 150], 20, [175, 250], 70, 0.37, 100, 0.28, 170),          # 08 - Wild Lands / Degazeilat / Дикие Земли
    Location(9, [25, 30], [125, 175], 24, [200, 300], 80, 0.44, 110, 0.30, 180),          # 09 - Stormy Plains / Pulkannat Dittagan / Равнины Штормов
    Location(10, [27, 35], [150, 210], 27, [250, 375], 90, 0.87, 140, 0.32, 190),         # 10 - Hills of Challenges / Kahtat Kidevalladan / Вершины Испытаний
    Location(11, [32, 40], [180, 250], 32, [300, 450], 100, 0.94, 100, 0.25, 200),        # 11 - The Forest / Na Lias / Сосновый Бор
    Location(12, [40, 50], [225, 300], 40, [400, 600], 110, 1.11, 130, 0.36, 210),        # 12 - The Anomalous Zone / Na Kadu Denarvaltan / Аномальная Зона
    Location(13, [50, 70], [250, 375], 50, [500, 700], 125, 0.63, 115, 0.38, 220),        # 13 - The Dark Cave / Temannar Hintakadu / Тёмная Пещера
    Location(14, [60, 80], [300, 500], 60, [600, 800], 150, 0.87, 120, 0.40, 230),        # 14 - Shadow Volcano / Teinaangartina / Вулкан Теней
    Location(15, [70, 90], [500, 750], 70, [750, 1000], 175, 0.58, 125, 0.41, 240),       # 15 - The Sunken Ship / Kineiridada Vallaita / Потонувший Корабль
    Location(16, [80, 105], [600, 900], 85, [875, 1250], 200, 0.27, 130, 0.43, 250),      # 16 - Southern Ice / Seinankaran Teivadat / Южные Льды
    Location(17, [90, 125], [675, 950], 92, [950, 1375], 225, 1.08, 150, 0.50, 260),      # 17 - The Land of the Dead / Na Zeila na Sevarddann
    Location(18, [100, 150], [750, 1000], 100, [1000, 1500], 250, 1.47, 180, 0.27, 270),  # 18 - The Ship of Salvation / Na Vallaita Ivankan / Корабль Спасения
]


class Player:
    def __init__(self, data: dict, clan: Optional[Clan], guild: Guild, new: bool):
        self.id: int = data["uid"]
        self.name: str = data["name"]
        self.disc: int = int(data["disc"])
        self.full_name: str = f"{self.name}#{self.disc:04d}"
        self.araksat: float = data["araksat"]
        self.coins: int = data["coins"]
        self.level: int = data["level"]
        self.xp: float = data["xp"]
        self.shaman_level: int = data["shaman_level"]
        self.shaman_xp: float = data["shaman_xp"]
        self.shaman_feathers: int = data["shaman_feathers"]
        self.shaman_probability_level: int = data["shaman_probability"]
        self.shaman_probability: float = start_shaman_probability + 0.005 * self.shaman_probability_level
        self.shaman_xp_boost_level: int = data["shaman_xp_boost"]
        self.shaman_xp_boost: float = 0.02 * self.shaman_xp_boost_level
        self.shaman_save_boost_level: int = data["shaman_save_boost"]
        self.shaman_save_boost: float = 0.01 * self.shaman_save_boost_level
        self.league_points: int = data["league_points"]
        self.max_points: int = data["max_points"]
        self.energy: float = data["energy"]
        self.energy_time: float = data["energy_time"]
        # self.renewal: int = data["cr"]
        self.clan: Optional[Clan] = clan  # Fetch clan data on loading
        self.guild: Guild = guild
        self.is_new: bool = new
        self.energy_limit: float = self.energy_limit_calc()
        self.energy_regen: float = self.energy_regen_speed()
        self.araksat_multiplier: float = self.araksat_mult()
        self.xp_multiplier: float = self.xp_mult()
        self.round_cost: float = self.energy_cost()

    @classmethod
    def new(cls, uid: int, name: str, disc: int, guild: Guild):
        """ Add a new player """
        return cls({"uid": uid, "name": name, "disc": int(disc), "araksat": start_araksat, "coins": start_coins, "level": 1, "xp": 0.0, "shaman_level": 1,
                    "shaman_xp": 0.0, "shaman_feathers": 0, "shaman_probability": start_shaman_probability, "shaman_xp_boost": 0.0, "shaman_save_boost": 0.0,
                    "league_points": 0, "energy": start_energy, "energy_time": time.now_ts(), "max_points": 0},
                   None, guild, True)

    @classmethod
    def from_db(cls, user: Union[discord.User, discord.Member], guild: discord.Guild):
        """ Get the player data from database """
        data = db.fetchrow("SELECT * FROM tbl_player WHERE uid=?", (user.id,))
        guild_data = Guild.from_db(guild)
        if not data:
            return cls.new(user.id, user.name, user.discriminator, guild_data)
        else:
            data["name"] = user.name
            data["disc"] = int(user.discriminator)
            if "clan" not in data or data["clan"] is None:
                clan = None
            else:
                clan = Clan.from_db(data["clan"])
            return cls(data, clan, guild_data, False)

    def save(self):
        """ Save the player's data into database """
        if self.clan:
            self.clan.save()
            clan_id = self.clan.id
        else:
            clan_id = None
        self.guild.save()
        if self.league_points > self.max_points:
            self.max_points = self.league_points
        if self.is_new:
            db.execute("INSERT INTO tbl_player VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                self.id, self.name, self.disc, self.araksat, self.coins, self.level, self.xp, self.shaman_level, self.shaman_xp, self.shaman_feathers,
                self.shaman_probability_level, self.shaman_xp_boost_level, self.shaman_save_boost_level, self.league_points, self.energy, self.energy_time, clan_id,
                self.max_points))
        else:
            db.execute("UPDATE tbl_player SET name=?, disc=?, araksat=?, coins=?, level=?, xp=?, shaman_level=?, shaman_xp=?, shaman_feathers=?, "
                       "shaman_probability=?, shaman_xp_boost=?, shaman_save_boost=?, league_points=?, energy=?, energy_time=?, clan=?, max_points=? WHERE uid=?", (
                        self.name, self.disc, self.araksat, self.coins, self.level, self.xp, self.shaman_level, self.shaman_xp, self.shaman_feathers,
                        self.shaman_probability_level, self.shaman_xp_boost_level, self.shaman_save_boost_level, self.league_points, self.energy, self.energy_time,
                        clan_id, self.max_points, self.id))

    def energy_limit_calc(self) -> float:
        """ Determine the player's Energy limit """
        level = self.level if self.level <= 250 else 250
        if 2 <= level < 200:
            base = 120 + level
        elif level == 200:
            base = 420
        elif level > 200:
            base = 420 + (level - 200) * 1.6
        else:
            base = 120
        limit = base
        if self.clan is not None:
            limit += self.clan.energy_limit_boost
        return limit

    def energy_regen_speed(self) -> float:
        """ Calculate the player's Energy regeneration speed """
        if self.clan is None:
            return energy_regen
        else:
            return energy_regen - self.clan.energy_regen_boost

    def araksat_mult(self) -> float:
        """ Player's Araksat reward multiplier """
        base = 1.00
        base += self.guild.araksat_boost
        if self.clan is not None:
            base += self.clan.reward_boost
            base *= 0.975  # Take off the 2.5% tax
        return base

    def xp_mult(self) -> float:
        """ Player's XP reward multiplier """
        base = 1.00
        base += self.guild.xp_boost
        if self.clan is not None:
            base += self.clan.reward_boost
            base *= 0.975  # Take off the 2.5% tax
        return base

    def energy_cost(self) -> float:
        """ How much a round costs """
        return energy_consumption - self.guild.energy_reduction

    def regenerate_energy(self):
        """ Regenerate the player's energy """
        now = time.now_ts()
        if self.energy > self.energy_limit:
            self.energy_time = now
            return
        time_passed = now - self.energy_time
        regen = time_passed / self.energy_regen
        new_energy = self.energy + regen
        if new_energy > self.energy_limit:
            new_energy = self.energy_limit
        self.energy = new_energy
        self.energy_time = now

    def get_location(self):
        for i, location in enumerate(locations):
            if self.level < location.level_req:
                return locations[i - 1]
        return locations[-1]

    def status(self, locale: str, avatar_url: str) -> discord.Embed:
        """ Returns an embed of the player's stats """
        self.regenerate_energy()
        embed = discord.Embed(colour=general.random_colour())
        embed.title = langs.gls("kuastall_tbl_stats", locale, self.full_name)
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(name=langs.gls("kuastall_tbl_stats_araksat", locale), value=general.bold(langs.gns(self.araksat, locale)), inline=False)
        embed.add_field(name=langs.gls("kuastall_tbl_stats_coins", locale), value=general.bold(langs.gns(self.coins, locale)), inline=False)
        # xp_req = player_levels[self.level]
        level = self.level if self.level <= 250 else 250
        r1, r2, r3 = langs.gns(level, locale), langs.gfs(self.xp, locale, pre=0), get_next("player", self.level, locale)
        # langs.gns(xp_req, locale)
        embed.add_field(name=langs.gls("kuastall_tbl_stats_level", locale), value=langs.gls("kuastall_tbl_stats_xp", locale, r1, r2, r3), inline=False)
        r4, r5, r6 = langs.gns(self.shaman_level, locale), langs.gfs(self.shaman_xp, locale, pre=0), get_next("shaman", self.shaman_level, locale)
        r7 = langs.gns(self.shaman_feathers, locale)
        r8 = langs.gfs(self.shaman_probability, locale, 1, True)
        r9 = langs.gfs(self.shaman_xp_boost, locale, 0, True)
        r0 = langs.gfs(self.shaman_save_boost, locale, 0, True)
        embed.add_field(name=langs.gls("kuastall_tbl_stats_shaman", locale), inline=False,
                        value=langs.gls("kuastall_tbl_stats_sh", locale, r4, r5, r6, r7))
        embed.add_field(name=langs.gls("kuastall_tbl_stats_shaman2", locale), inline=False,
                        value=langs.gls("kuastall_tbl_stats_sh2", locale, r8, r9, r0))
        embed.timestamp = time.now(None)
        l1, l3 = get_league(self.league_points, locale)
        l2 = langs.gns(self.league_points, locale)
        l4 = langs.plural(self.max_points, "kuastall_tbl_pl_league_points2", locale)
        embed.add_field(name=langs.gls("kuastall_tbl_stats_leagues", locale), value=langs.gls("kuastall_tbl_stats_league", locale, l1, l2, l3, l4), inline=False)
        e1, e2 = langs.gfs(self.energy, locale, 1), langs.gfs(self.energy_limit, locale, 1)
        e3 = langs.plural(self.energy_regen, "time_second", locale, 1)  # langs.gfs(self.energy_regen, locale, 1)
        if self.energy >= self.energy_limit:
            e4 = langs.gls("kuastall_tbl_stats_energy_full", locale)
        else:
            full = self.energy_time + ((self.energy_limit - self.energy) * self.energy_regen)
            e4 = langs.td_ts(int(full), locale, 3, False, True)
        embed.add_field(name=langs.gls("kuastall_tbl_stats_energy", locale), inline=False,
                        value=langs.gls("kuastall_tbl_stats_energy2", locale, e1, e2, e3, e4))
        footer = f"Player/User ID: {self.id}"
        if self.clan is None:
            clan = langs.gls("generic_none", locale)
        else:
            clan = f"**{self.clan.name}** ({langs.gls('leveling_rank_level', locale, self.clan.level)})"
            footer += f" | Clan ID: {self.clan.id}"
        embed.add_field(name=langs.gls("kuastall_tbl_clan", locale), value=clan, inline=False)
        embed.set_footer(text=footer)
        embed.add_field(name=langs.gls("kuastall_tbl_guild", locale), inline=False,
                        value=f"**{self.guild.name}** ({langs.gls('leveling_rank_level', locale, self.guild.level)})")
        return embed

    async def play(self, ctx: Context, locale: str, custom_location: Optional[Location]):
        """ Do the calculations called playing TBL """
        location_names = langs.get_data("kuastall_tbl_locations", locale)
        try:
            # The Game
            self.regenerate_energy()
            location = custom_location or self.get_location()
            is_clan = custom_location is not None
            if is_clan:
                players = location.clan(self.clan)
            else:
                players = location.normal()
            if self.energy < self.round_cost:
                e1, e2 = langs.gfs(self.energy, locale, 1), langs.gfs(self.round_cost, locale, 1)
                return await general.send(langs.gls("kuastall_tbl_game_energy", locale, e1, e2), ctx.channel)
            location_name = location_names[location.id - 1]
            message = await general.send(f"{langs.gts(time.now(), locale, True, False, False, True, False)} > {ctx.author} > "  # time.time()
                                         f"Hiarikiiteak na TBL't! Kaltera...", ctx.channel)
            await asyncio.sleep(2)
            runs = 0
            ar_mult, ar_end = get_events("araksat")
            xp_mult, xp_end = get_events("xp")
            while self.energy >= self.round_cost and runs < 1000000:
                if runs < 5000:
                    rao = int(runs / 50) + 1  # Runs at once
                elif 5000 <= runs < 10000:
                    rao = 100
                elif 10000 <= runs < 20000:
                    rao = 250
                else:
                    rao = 1000
                runs += 1
                shaman = random.random() < self.shaman_probability
                self.energy -= self.round_cost
                results = []
                death = location.death_rate_level(self.level)
                death2 = location.death_rate_level(location.level_req)  # Just assume that everyone else is only at the lowest level required to be in the loc
                reward_ar, reward_xp, reward_lp, reward_sh = 0, 0, 0, 0  # Araksat, XP, League Points, Shaman XP
                ll = random.randint(int(location.max * 0.9), int(location.max * 1.1))  # Level length
                for player in range(players - 1):
                    completion, survival = random.randint(location.min, ll), random.random() > death2
                    results.append({"time": completion, "life": survival, "self": False})
                you = {"time": random.randint(location.min, location.max), "life": random.random() > death, "self": True}  # Your result
                results.append(you)
                results.sort(key=lambda x: x["time"])  # Sort by time
                saves = 0
                if shaman:
                    for player in results:
                        if player["life"] and not player["self"]:
                            saves += 1
                    # All players that lived are counted as "saves", and then multiplied by the save boost
                    saves *= 1 + self.shaman_save_boost
                    if saves >= players:
                        saves = players - 1  # You can't save more people than there are to begin with
                    saves = int(saves)
                    reward_xp += int(location.shaman_xp * saves / 5)
                    reward_sh += location.shaman_xp * saves
                    reward_ar += saves
                place = 0
                if you["life"]:
                    if not shaman:
                        for player in results:
                            if player["life"]:  # Only if the player survived
                                place += 1
                                if player["self"]:
                                    break
                    self.guild.xp += 10 if self.level < 10 else self.level if self.level <= 250 else 250
                    a1, a2 = location.araksat
                    reward_ar += random.randint(a1, a2)
                    x1, x2 = location.xp
                    reward_xp += random.randint(x1, x2)
                    l1, l2 = location.points
                    reward_lp += random.randint(l1, l2)
                if is_clan:
                    reward_ar *= 1.25
                    reward_xp *= 1.25
                    reward_lp *= 0
                reward_ar *= ar_mult * self.araksat_multiplier
                reward_xp *= xp_mult * self.xp_multiplier
                reward_sh *= 1 + self.shaman_xp_boost
                # Add the rewards to the player, clan and guild
                self.araksat += reward_ar
                self.xp += reward_xp
                if self.clan:
                    self.clan.araksat += reward_ar * self.clan.tax_gain
                    self.clan.xp += reward_xp * self.clan.tax_gain
                self.league_points += reward_lp
                self.shaman_xp += reward_sh
                self.level, xld = player_level(self.level, self.xp)
                self.coins += xld
                self.shaman_level, sld = shaman_level(self.shaman_level, self.shaman_xp)
                self.shaman_feathers += sld
                if xld > 0:
                    self.energy_limit = self.energy_limit_calc()
                    if not is_clan:
                        location = self.get_location()
                        location_name = location_names[location.id - 1]
                        players = location.normal()
                if self.energy < self.energy_limit:
                    if xld > 0 and self.level <= 250:
                        self.energy = self.energy_limit
                    else:
                        if you["life"] and not shaman:
                            rate = self.energy_regen if self.energy_regen > 60 else 60  # Min energy regen speed 60
                            self.energy += (ll - you["time"]) / rate
                        if shaman:
                            bonus = saves / 10
                            if bonus > (self.round_cost - 2):
                                bonus = self.round_cost - 2
                            self.energy += bonus
                        if self.energy > self.energy_limit:
                            self.energy = self.energy_limit
                if runs % rao == 0:  # If this specific round is worthy of giving output
                    level_length = langs.td_int(ll, locale, brief=True, suffix=False)
                    your_time = langs.td_int(you["time"], locale, brief=True, suffix=False)
                    r1 = langs.gts(time.now(), locale, True, False, False, True, False)
                    r2 = ga78.time_kargadia(tz=2).str(dow=False, era=None, month=False)
                    # r2 = ss23.time_kargadia(tz=2).str(dow=False, era=None, tz=False)
                    r3 = langs.gns(runs, locale)
                    r4, r5 = langs.gfs(self.energy, locale, 1), langs.gfs(self.energy_limit, locale, 1)
                    out_1 = langs.gls("kuastall_tbl_game_1", locale, r1, r2, location_name, r3, r4, r5, level_length)
                    out_2 = ""
                    if ar_mult != 1:
                        r1, r2 = langs.gfs(ar_mult, locale, 2), langs.td_dt(ar_end, locale, brief=True, suffix=True)
                        out_2 += langs.gls("kuastall_tbl_game_2a", locale, clock[runs % 4], r1, r2)
                    if xp_mult != 1:
                        r1, r2 = langs.gfs(xp_mult, locale, 2), langs.td_dt(xp_end, locale, brief=True, suffix=True)
                        out_2 += langs.gls("kuastall_tbl_game_2b", locale, clock[runs % 4], r1, r2)
                    if you["life"]:
                        out_3 = langs.gls("kuastall_tbl_game_3a", locale)
                        if not shaman:
                            out_3 += langs.gls("kuastall_tbl_game_3b", locale, your_time, place, players)
                    else:
                        out_3 = langs.gls("kuastall_tbl_game_3c", locale)
                    out_4 = ""
                    if shaman:
                        out_4 += langs.gls("kuastall_tbl_game_4", locale, saves)
                    r1, r2 = langs.gns(reward_ar, locale), langs.gns(self.araksat, locale)
                    r3, r4, r6 = langs.gns(reward_xp, locale), langs.gns(self.xp, locale), langs.gns(self.level if self.level <= 250 else 250, locale)
                    r5 = get_next("player", self.level, locale)
                    r7, r8 = langs.gns(reward_lp, locale), langs.gns(self.league_points, locale)
                    r9, r10 = get_league(self.league_points, locale)  # League name, next league requirement
                    r11, r12, r14 = langs.gns(reward_sh, locale), langs.gns(self.shaman_xp, locale), langs.gns(self.shaman_level, locale)
                    r13 = get_next("shaman", self.shaman_level, locale)
                    out_5 = langs.gls("kuastall_tbl_game_5", locale, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14)
                    await message.edit(content=out_1 + out_2 + out_3 + out_4 + out_5)
                    await asyncio.sleep(1)
            if self.clan:
                self.clan.level, cld = clan_level(self.clan.level, self.clan.xp)
                self.clan.points += cld
            self.guild.level, gld = guild_level(self.guild.level, self.guild.xp)
            self.guild.coins += gld
            self.energy_time = time.now_ts()
            self.save()  # Save all data for player, clan and guild, and only then calculate all the outputs
            r1 = langs.gts(time.now(), locale, True, False, False, True, False)
            r2 = ga78.time_kargadia(tz=2).str(dow=False, era=None, month=False)
            # r2 = ss23.time_kargadia(tz=2).str(dow=False, era=None, tz=False)
            r3 = langs.gns(runs, locale)
            r4, r5 = langs.gfs(self.energy, locale, 1), langs.gfs(self.energy_limit, locale, 1)
            # When the energy will be full again
            if self.energy >= self.energy_limit:  # somehow...
                r6 = langs.gls("kuastall_tbl_stats_energy_full", locale)
            else:
                full = self.energy_time + ((self.energy_limit - self.energy) * self.energy_regen)
                r6 = langs.td_ts(int(full), locale, 3, False, True)
            r7 = langs.gns(self.araksat, locale)
            r8, r9, r10 = langs.gns(self.xp, locale), get_next("player", self.level, locale), langs.gns(self.level if self.level <= 250 else 250, locale)
            r11, r12, r13 = langs.gns(self.shaman_xp, locale), get_next("shaman", self.shaman_level, locale), langs.gns(self.shaman_level, locale)
            r14 = langs.gns(self.league_points, locale)
            r16, r15 = get_league(self.league_points, locale)  # League req before league name
            r17 = ctx.prefix
            output = langs.gls("kuastall_tbl_game_end", locale, ctx.author.name, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14, r15, r16, r17)
            await message.edit(content=output)
        except Exception as e:
            if ctx.channel.id in [742885168997466196, 610482988123422750]:  # Hidden Commands channels
                await general.send(general.traceback_maker(e), ctx.channel)
            return await general.send(langs.gls("kuastall_tbl_game_error", locale, type(e).__name__, e), ctx.channel)


class Invite:
    def __init__(self, data: dict, is_new: bool):
        self.user_id: int = data["user"]
        self.clan_id: int = data["clan"]
        self.type: int = data["type"]
        self.id: int = data["id"]
        self.is_new: bool = is_new

    @classmethod
    def new(cls, user_id: int, clan_id: int, invite_type: int):
        """ Create a new invite """
        return cls({"user": user_id, "clan": clan_id, "type": invite_type, "id": random.randint(10000, 99999)}, True)

    @classmethod
    def from_db_id(cls, invite_id: int):
        """ Load an invite by invite ID """
        data = db.fetchrow("SELECT * FROM tbl_invite WHERE id=?", (invite_id,))
        if not data:
            return None
        return cls(data, False)

    @classmethod
    def from_db_clan(cls, clan_id: int):
        """ Load all invites belonging to a clan """
        data = db.fetch("SELECT * FROM tbl_invite WHERE clan=?", (clan_id,))
        out = []
        for clan in data:
            out.append(cls(clan, False))
        return out

    @classmethod
    def from_db_user(cls, user_id: int):
        """ Load all invites belonging to a user/player """
        data = db.fetch("SELECT * FROM tbl_invite WHERE user=?", (user_id,))
        out = []
        for user in data:
            out.append(cls(user, False))
        return out

    @classmethod
    def from_db(cls, user_id: int, clan_id: int):
        """ Load an invite by user ID and clan ID """
        data = db.fetchrow("SELECT * FROM tbl_invite WHERE user=? AND clan=?", (user_id, clan_id))
        if not data:
            return None
        return cls(data, False)

    def save(self):
        """ Save the Invite to the database """
        if self.is_new:
            db.execute("INSERT INTO tbl_invite VALUES (?, ?, ?, ?)", (self.user_id, self.clan_id, self.type, self.id))
        else:  # I mean, overall that would be useless because there isn't really much to change, but whatever
            db.execute("UPDATE tbl_values SET user=?, clan=?, type=? WHERE id=?", (self.user_id, self.clan_id, self.type, self.id))

    def delete(self):
        """ Delete/Reject the invite """
        if not self.is_new:
            db.execute("DELETE FROM tbl_invite WHERE id=?", (self.id,))

    def accept(self):
        """ Accept the invite """
        player = db.fetchrow("SELECT * FROM tbl_player WHERE uid=?", (self.user_id,))
        clan = db.fetchrow("SELECT * FROM tbl_clan WHERE clan_id=?", (self.clan_id,))
        if not (player and clan):
            return False  # Indicate failure to accept invite
        db.execute("UPDATE tbl_player SET clan=? WHERE uid=?", (self.clan_id, self.user_id))
        self.delete()
        return True
