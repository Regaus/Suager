import sqlite3

types = ["INTEGER", "REAL", "TEXT", "BOOLEAN", "TIMESTAMP"]  # Real = float, Text = str, Timestamp = datetime
beginning = "CREATE TABLE IF NOT EXISTS <name> (\n"
ending = "\n);"
joiner = ",\n"


def dict_factory(cursor, row):
    d = {}
    for index, col in enumerate(cursor.description):
        d[col[0]] = row[index]
    return d


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(f"data/database.db", isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.row_factory = dict_factory
        self.db = self.conn.cursor()

    def execute(self, sql: str, prepared: tuple = ()):
        """ Execute SQL command """
        try:
            data = self.db.execute(sql, prepared)
        except Exception as e:
            return f"{type(e).__name__}: {e}"
        status_word = sql.split(' ')[0].upper()
        status_code = data.rowcount if data.rowcount > 0 else 0
        if status_word == "SELECT":
            status_code = len(data.fetchall())
        return f"{status_word} {status_code}"

    def fetch(self, sql: str, prepared: tuple = ()):
        """ Fetch data from DB """
        data = self.db.execute(sql, prepared).fetchall()
        return data

    def fetchrow(self, sql: str, prepared: tuple = ()):
        """ Fetch one row of data from DB """
        data = self.db.execute(sql, prepared).fetchone()
        return data


class Column:
    def __init__(self, name: str, column_type: int, not_null: bool):
        self.name = name
        self.type = column_type
        self.not_null = not_null
        self.nn = " NOT NULL" if self.not_null else ""
        self.ct = types[self.type]

    def __str__(self):
        return f'\t"{self.name}" {self.ct} {self.nn}'


class Table:
    def __init__(self, name: str, columns: list):
        self.name = name
        self.columns = columns

    def create(self):
        start = beginning.replace("<name>", self.name)
        strings = [str(column) for column in self.columns]
        middle = joiner.join(strings)
        end = ending
        command = f"{start}{middle}{end}"
        db = Database()
        result = db.execute(command)
        if result != "CREATE 0":
            print(f"{self.name} > {result}")


def creation():
    for table in tables:
        try:
            table.create()
        except Exception as e:
            print(f"{type(e).__name__}: {e}")


tables = [
    Table("birthdays", [
        Column("uid", 0, True),
        Column("birthday", 4, True),
        Column("has_role", 3, True)
    ]),
    Table("custom_role", [
        Column("uid", 0, True),
        Column("rid", 0, True),
        Column("gid", 0, True)
    ]),
    Table("settings", [
        Column("gid", 0, True),
        Column("data", 2, True)
    ]),
    Table("leveling", [
        Column("uid", 0, True),
        Column("gid", 0, True),
        Column("level", 0, True),
        Column("xp", 0, True),
        Column("last", 1, True),
        Column("last_sent", 1, False),
        Column("name", 2, True),
        Column("disc", 0, True)
    ]),
    Table("leveling2", [
        Column("uid", 0, True),
        Column("gid", 0, True),
        Column("level", 0, True),
        Column("xp", 0, True),
        Column("last", 1, True),
        Column("last_sent", 1, False),
        Column("name", 2, True),
        Column("disc", 0, True)
    ]),
    Table("custom_rank", [
        Column("uid", 0, True),
        Column("font", 0, True),
        Column("progress", 0, True),
        Column("background", 0, True)
    ]),
    Table("timezones", [
        Column("uid", 0, True),
        Column("tz", 2, True)
    ]),
    Table("counters", [
        Column("uid1", 0, True),       # 00
        Column("uid2", 0, True),       # 01
        Column("bang", 0, True),       # 02
        Column("bite", 0, True),       # 03
        Column("cuddle", 0, True),     # 04
        Column("high_five", 0, True),  # 05
        Column("hug", 0, True),        # 06
        Column("kiss", 0, True),       # 07
        Column("lick", 0, True),       # 08
        Column("pat", 0, True),        # 09
        Column("slap", 0, True),       # 10
        Column("sniff", 0, True),      # 11
        Column("poke", 0, True),       # 12
        Column("boop", 0, True),       # 13
        Column("suck", 0, True),       # 14
        Column("tickle", 0, True),     # 15
        Column("punch", 0, True),      # 16
        Column("kill", 0, True),       # 17
        Column("ff", 0, True),         # 18
        Column("r", 0, True),          # 19
    ]),
    Table("tags", [
        Column("gid", 0, True),
        Column("creator", 0, True),
        Column("owner", 0, True),
        Column("name", 2, True),
        Column("content", 2, True),
        Column("created", 0, True),
        Column("edited", 0, True),
        Column("usage", 0, True)
    ]),
    Table("locales", [
        Column("gid", 0, True),
        Column("locale", 2, True)
    ]),
    Table("starboard", [
        Column("message", 0, True),       # Original message ID
        Column("channel", 0, True),
        Column("guild", 0, True),
        Column("stars", 0, True),
        Column("star_message", 0, False)  # Starboard message ID
    ]),
    Table("temporary", [
        Column("uid", 0, True),       # User ID
        Column("type", 2, True),      # "mute" or "reminder"
        Column("expiry", 4, True),    # When the action is due
        Column("gid", 0, False),      # Guild ID if it's a mute
        Column("message", 2, False),  # Message if it's a reminder
        Column("entry_id", 0, True),  # Random ID to later find this entry in the database
        Column("handled", 0, True),   # Whether the entry has been handled upon expiry
    ]),
    Table("tbl_player", [
        Column("uid", 0, True),                 # 01 - User ID
        Column("name", 2, True),                # 02 - Username
        Column("disc", 0, True),                # 03 - Discriminator
        Column("araksat", 1, True),             # 04 - Player's Araksat balance
        Column("coins", 0, True),               # 05 - Player's Coins
        Column("level", 0, True),               # 06 - Normal Level
        Column("xp", 1, True),                  # 07
        Column("shaman_level", 0, True),        # 08
        Column("shaman_xp", 1, True),           # 09
        Column("shaman_feathers", 0, True),     # 10 - Shaman Feathers for upgrading capabilities
        Column("shaman_probability", 0, True),  # 11 - Probability of being Shaman (default: 0.08 (8%), 0.5% per boost, max 40%) //  64 SF
        Column("shaman_xp_boost", 0, True),     # 12 - Shaman XP gain boost (2% per boost, max 150%)                             //  75 SF
        Column("shaman_save_boost", 0, True),   # 13 - Shaman Saves boost (1% per boost, max 100%)                               // 100 SF
        Column("league_points", 0, True),       # 14
        Column("energy", 1, True),              # 15 - Current energy
        Column("energy_time", 1, True),         # 16 - When to start energy regen
        Column("clan", 0, False),               # 17 - Clan ID player's a part of
        Column("cr", 0, True),                  # 18 - Challenge Renewal Level
    ]),
    Table("tbl_clan", [
        Column("clan_id", 0, True),
        Column("name", 2, True),
        Column("description", 2, False),        # Description of clan
        Column("type", 0, True),                # 0 = open, 1 = invite-only, 2 = closed
        Column("level", 0, True),
        Column("xp", 1, True),
        Column("points", 1, True),              # Upgrade Points
        Column("owner", 0, True),               # Owner's user ID
        Column("locations", 2, True),           # JSON of Clan Locations and how long they'll last
        Column("araksat", 1, True),             # Clan Araksat
        Column("tax_gain", 0, True),            # How much the clan gains from tax (Default: 0.025 (2.5%), 0.1% per boost, max 25%)      // 225 UP
        Column("reward_boost", 0, True),        # How much more Araksat and XP all clan members gain (0.5% each per boost, max 200%)     // 400 UP
        Column("energy_limit_boost", 0, True),  # How much bigger members' energy limit will be (1 per boost, max 250)                   // 250 UP
        Column("energy_regen_boost", 0, True),  # Amount of seconds members' energy takes less time to regen (-0.4s per boost, max -60s) // 150 UP
    ]),
    Table("tbl_guild", [
        Column("gid", 0, True),               # Guild ID
        Column("name", 2, True),
        Column("level", 0, True),
        Column("xp", 1, True),
        Column("coins", 1, True),             # Guild Coins
        Column("araksat_boost", 0, True),     # How much members' Araksat gain is increased (1% per boost, max 300%) // 300 GC
        Column("xp_boost", 0, True),          # How much members' XP gain is increased (1% per boost, max 300%)      // 300 GC
        Column("energy_reduction", 0, True),  # How much less energy members need per round (-0.1 per boost, max -5) // 500 GC
    ]),
    Table("tbl_invite", [
        Column("user", 0, True),
        Column("clan", 0, True),
        Column("type", 0, True),
        Column("id", 0, True)     # Invite ID
    ])
]
