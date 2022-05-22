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
    def __init__(self, name: str, column_type: int, not_null: bool, pk: bool = False):
        self.name = name
        self.type = column_type
        self.not_null = not_null
        self.nn = " NOT NULL" if self.not_null else ""
        self.pk = " PRIMARY KEY" if pk else ""
        self.ct = types[self.type]

    def __str__(self):
        return f'\t"{self.name}" {self.ct}{self.nn}{self.pk}'


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
        Column("has_role", 3, True),
        Column("bot", 2, True),
    ]),
    Table("counters", [
        Column("uid1", 0, True),       # 00 - Author
        Column("uid2", 0, True),       # 01 - Target
        Column("bot", 2, True),        # 02 - Bot Name
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
        Column("tickle", 0, True),     # 14
        Column("punch", 0, True),      # 15
        Column("bang", 0, True),       # 16
        Column("suck", 0, True),       # 17
        Column("kill", 0, True),       # 18
        Column("ff", 0, True),         # 19
        Column("r", 0, True),          # 20
        Column("nibble", 0, True),     # 21
        Column("feed", 0, True),       # 22
    ]),
    Table("custom_rank", [
        Column("uid", 0, True),
        Column("font", 0, True),
        Column("progress", 0, True),
        Column("background", 0, True)
    ]),
    Table("custom_role", [
        Column("uid", 0, True),
        Column("rid", 0, True),
        Column("gid", 0, True)
    ]),
    Table("kargadia", [
        Column("id", 0, True, True),   # Citizen ID
        Column("uid", 0, True),        # Discord User ID
        Column("name", 2, True),       # First name
        Column("name2", 2, False),     # Vaaraninema
        Column("gender", 2, True),     # m/f
        Column("birthday", 2, False),  # Kargadian birthday - iso date string
        Column("has_role", 3, True),   # Is it currently the person's Kargadian birthday?
        Column("location", 2, False),  # Kargadian location - can also be used to determine timezone
        Column("joined", 2, True),     # When the user joined as an Earth date
    ]),
    Table("leveling", [
        Column("uid", 0, True),
        Column("gid", 0, True),
        Column("level", 0, True),
        Column("xp", 0, True),
        Column("last", 1, True),
        Column("last_sent", 1, False),
        Column("name", 2, True),
        Column("disc", 0, True),
        Column("bot", 2, True),
    ]),
    Table("locales", [
        Column("gid", 0, True),
        Column("locale", 2, True),
        Column("bot", 2, True)
    ]),
    Table("polls", [
        Column("guild_id", 0, True),        # The Guild ID where the poll was started
        Column("channel_id", 0, True),      # The Channel ID of the poll status message
        Column("message_id", 0, True),      # The Message ID of the poll status message
        Column("poll_id", 0, True),         # The Poll ID
        Column("question", 2, True),        # The question of the poll ([Author#1234] Question)
        Column("voters_yes", 2, True),      # List of users who voted Yes
        Column("voters_neutral", 2, True),  # List of users who voted Neutral
        Column("voters_no", 2, True),       # List of users who voted No
        Column("expiry", 4, True),          # When the poll ends
        Column("anonymous", 3, True),       # Whether the poll is anonymous or not
    ]),
    Table("punishments", [
        Column("id", 0, True, True),  # Case ID
        Column("uid", 0, True),       # User ID, the punished
        Column("gid", 0, True),       # Guild ID
        Column("action", 2, True),    # Action taken (warn, pardon, mute, unmute, kick, ban, unban)
        Column("author", 0, True),    # User ID who applied the punishment
        Column("reason", 2, False),   # Why the punishment was applied
        Column("temp", 3, True),      # Whether the action is temporary (warns and mutes)
        Column("expiry", 4, False),   # When the punishment expires
        Column("handled", 0, True),   # Handled value (0 = Unhandled, 1 = Expired, 2 = Error, 3 = User left, 4 = Pardoned/Manually unmuted)
        Column("bot", 2, True)        # Bot used for punishment
    ]),
    Table("reaction_groups", [
        Column("gid", 0, True),      # Guild ID
        Column("message", 0, True),  # Message ID
        Column("type", 0, True)      # Reaction Type (1-4)
    ]),
    Table("reaction_roles", [
        Column("message", 0, True),   # Message ID (Group)
        Column("reaction", 2, True),  # Reaction Emoji
        Column("role", 0, True)       # Role ID
    ]),
    Table("reaction_tracking", [      # Track if someone already has a role (dType 2 and 4 reaction groups)
        Column("message", 0, True),   # Message ID (Group)
        Column("uid", 0, True),       # User ID
    ]),
    Table("reminders", [
        Column("id", 0, True, True),  # Reminder ID
        Column("uid", 0, True),       # User ID
        Column("expiry", 4, True),    # Expiry (as datetime string)
        Column("message", 2, True),   # Reminder message
        Column("handled", 0, True),   # Handled value (0 = Unhandled, 1 = Expired, 2 = Error)
        Column("bot", 2, True)        # Bot used for reminder
    ]),
    Table("settings", [
        Column("gid", 0, True),
        Column("bot", 2, True),  # The name of the bot to which the settings belong
        Column("data", 2, True)
    ]),
    Table("starboard", [
        Column("message", 0, True),       # Original message ID
        Column("channel", 0, True),       # Original message's channel ID
        Column("author", 0, True),        # Original message's author's user ID
        Column("guild", 0, True),         # Original message's guild ID
        Column("stars", 0, True),         # Star count
        Column("star_message", 0, False)  # Starboard message ID
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
    Table("timezones", [
        Column("uid", 0, True),
        Column("tz", 2, True)
    ]),
    Table("trials", [
        Column("guild_id", 0, True),        # The Guild ID where the trial was started
        Column("channel_id", 0, True),      # The Channel ID of the trial status message
        Column("message_id", 0, True),      # The Message ID of the trial status message
        Column("trial_id", 0, True),        # The Trial ID
        Column("author_id", 0, True),       # The User ID of who started the trial
        Column("user_id", 0, True),         # The User ID, to which the action will be done if the trial succeeds
        Column("type", 2, True),            # The type of trial (ban, unban, kick, mute, unmute)
        Column("mute_length", 0, True),     # The mute length in seconds (if the trial type is mute)
        Column("reason", 2, True),          # The reason for starting the trial ([Author#1234] Reason)
        Column("voters_yes", 2, True),      # List of users who voted Yes
        Column("voters_neutral", 2, True),  # List of users who voted Neutral
        Column("voters_no", 2, True),       # List of users who voted No
        Column("start_time", 1, True),      # Timestamp when the trial was started
        Column("expiry", 4, True),          # When the poll ends
        Column("anonymous", 3, True),       # Whether the poll is anonymous or not
        Column("required_score", 0, True),  # Score required for the trial to pass
    ]),
    Table("user_roles", [         # We should only need to log people who left with roles, so we only need this much data
        Column("gid", 0, True),   # Guild ID
        Column("uid", 0, True),   # User ID
        Column("roles", 2, True)  # JSON list of role IDs the user had
    ]),
    # Table("user_logs", [
    #     Column("gid", 0, True),        # Guild ID
    #     Column("uid", 0, True),        # User ID
    #     Column("action", 2, True),     # "join" or "leave"
    #     Column("timestamp", 4, True),  # When the user left
    #     Column("roles", 2, False),     # JSON [] of role IDs the user had when leaving (ignored if joining, or if role retention is disabled)
    # ])
]
