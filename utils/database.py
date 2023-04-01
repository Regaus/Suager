import re
import sqlite3
from datetime import datetime

from utils import general, logger, time


def adapt_datetime_iso(val: datetime) -> str:
    """ Convert datetime object into ISO timestamp """
    return val.isoformat(sep=" ")


def convert_datetime(val: bytes) -> datetime:
    """ Convert ISO timestamp back into datetime object """
    return datetime.fromisoformat(val.decode("latin1"))


sqlite3.register_adapter(datetime, adapt_datetime_iso)
sqlite3.register_converter("timestamp", convert_datetime)


def dict_factory(cursor, row):
    d = {}
    for index, col in enumerate(cursor.description):
        d[col[0]] = row[index]
    return d


# Built to support the regex required on the Pretender bot, but I suppose if I ever need to use this on other bots I could still use the same thing or just call it something else
def regex_function(expr, item):
    if item is None:
        return False
    reg = re.compile(re.escape(expr), re.IGNORECASE)
    return reg.search(item) is not None


def april_fools_multiplier():
    return -1 if time.april_fools() else 1


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(f"data/database.db", isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.row_factory = dict_factory
        self.conn.create_function("REGEXP", 2, regex_function)
        self.conn.create_function("APRILMULT", 0, april_fools_multiplier)
        self.db = self.conn.cursor()

    def execute(self, sql: str, prepared: tuple = ()):
        """ Execute SQL command """
        try:
            data = self.db.execute(sql, prepared)
        except Exception as e:
            msg = f"{datetime.now():%d %b %Y, %H:%M:%S} > Database > {type(e).__name__}: {e}"
            general.print_error(msg)
            logger.log("suager", "database", msg)
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
    def __init__(self, name: str, column_type: str, not_null: bool, pk: bool = False):
        self.name = name
        self.type = column_type
        self.not_null = not_null
        self.nn = " NOT NULL" if self.not_null else ""
        self.pk = " PRIMARY KEY" if pk else ""
        # self.ct = types[self.type]

    def __str__(self):
        return f'\t"{self.name}" {self.type}{self.nn}{self.pk}'


class Table:
    def __init__(self, name: str, columns: list):
        self.name = name
        self.columns = columns

    def create(self):
        start = f"CREATE TABLE IF NOT EXISTS {self.name} (\n"
        strings = [str(column) for column in self.columns]
        middle = ",\n".join(strings)
        end = "\n);"
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


# Column types: Real = float, Text = str, Timestamp = datetime
tables = [
    Table("birthdays", [
        Column("uid", "INTEGER", True),
        Column("birthday", "TIMESTAMP", True),
        Column("has_role", "BOOLEAN", True),
        Column("bot", "TEXT", True),
    ]),
    Table("counters", [
        Column("uid1", "INTEGER", True),       # 00 - Author
        Column("uid2", "INTEGER", True),       # 01 - Target
        Column("bot", "TEXT", True),           # 02 - Bot Name
        Column("bite", "INTEGER", True),       # 03
        Column("cuddle", "INTEGER", True),     # 04
        Column("high_five", "INTEGER", True),  # 05
        Column("hug", "INTEGER", True),        # 06
        Column("kiss", "INTEGER", True),       # 07
        Column("lick", "INTEGER", True),       # 08
        Column("pat", "INTEGER", True),        # 09
        Column("slap", "INTEGER", True),       # 10
        Column("sniff", "INTEGER", True),      # 11
        Column("poke", "INTEGER", True),       # 12
        Column("boop", "INTEGER", True),       # 13
        Column("tickle", "INTEGER", True),     # 14
        Column("punch", "INTEGER", True),      # 15
        Column("bang", "INTEGER", True),       # 16
        Column("suck", "INTEGER", True),       # 17
        Column("kill", "INTEGER", True),       # 18
        Column("ff", "INTEGER", True),         # 19
        Column("r", "INTEGER", True),          # 20
        Column("nibble", "INTEGER", True),     # 21
        Column("feed", "INTEGER", True),       # 22
        Column("handhold", "INTEGER", True),   # 23
    ]),
    Table("custom_rank", [
        Column("uid", "INTEGER", True),
        Column("font", "INTEGER", False),        # Text colour
        Column("progress", "INTEGER", False),    # Progress bar colour
        Column("background", "INTEGER", False),  # Background colour
        Column("custom_font", "TEXT", False),    # Font to use
    ]),
    Table("custom_role", [
        Column("uid", "INTEGER", True),
        Column("rid", "INTEGER", True),
        Column("gid", "INTEGER", True)
    ]),
    Table("kargadia", [
        Column("id", "INTEGER", True, True),   # Citizen ID
        Column("uid", "INTEGER", True),        # Discord User ID
        Column("protected", "BOOLEAN", True),  # Whether a profile is "Protected" (only viewable by me and that user)
        Column("name", "TEXT", True),          # First Name
        Column("name2", "TEXT", False),        # Parent Name
        Column("name3", "TEXT", False),        # Surname
        Column("gender", "TEXT", True),        # Gender - m/f/n/u
        Column("birthday", "TEXT", False),     # Kargadian birthday - iso date string
        Column("has_role", "BOOLEAN", True),   # Is it currently the person's Kargadian birthday?
        Column("location", "TEXT", False),     # Kargadian location - can also be used to determine timezone
        Column("joined", "TEXT", False),       # When the user joined as an Earth date
    ]),
    Table("leveling", [
        Column("uid", "INTEGER", True),
        Column("gid", "INTEGER", True),
        Column("level", "INTEGER", True),
        Column("xp", "INTEGER", True),
        Column("last", "REAL", True),
        Column("last_sent", "REAL", False),
        Column("name", "TEXT", True),
        Column("disc", "INTEGER", True),
        Column("bot", "TEXT", True),
    ]),
    Table("locales", [
        Column("gid", "INTEGER", True),
        Column("locale", "TEXT", True),
        Column("bot", "TEXT", True)
    ]),
    Table("polls", [
        Column("guild_id", "INTEGER", True),     # The Guild ID where the poll was started
        Column("channel_id", "INTEGER", True),   # The Channel ID of the poll status message
        Column("message_id", "INTEGER", True),   # The Message ID of the poll status message
        Column("poll_id", "INTEGER", True),      # The Poll ID
        Column("question", "TEXT", True),        # The question of the poll ([Author#1234] Question)
        Column("voters_yes", "TEXT", True),      # List of users who voted Yes
        Column("voters_neutral", "TEXT", True),  # List of users who voted Neutral
        Column("voters_no", "TEXT", True),       # List of users who voted No
        Column("expiry", "TIMESTAMP", True),     # When the poll ends
        Column("anonymous", "BOOLEAN", True),    # Whether the poll is anonymous or not
    ]),
    Table("pretender_blacklist", [       # Users ignored for message logging
        Column("uid", "INTEGER", True),  # Blacklisted User's ID
    ]),
    Table("pretender_messages", [             # All the messages
        Column("id", "INTEGER", True, True),  # Message ID
        Column("author", "INTEGER", True),    # Message author ID
        Column("channel", "INTEGER", False),  # Message channel ID
        Column("content", "TEXT", True)       # Message content
    ]),
    Table("pretender_webhooks", [           # Stores webhooks for channels
        Column("id", "INTEGER", True),      # Webhook ID
        Column("token", "TEXT", True),      # Webhook's token
        Column("channel", "INTEGER", True)  # Webhook's channel ID
    ]),
    Table("punishments", [
        Column("id", "INTEGER", True, True),   # Case ID
        Column("uid", "INTEGER", True),        # User ID, the punished
        Column("gid", "INTEGER", True),        # Guild ID
        Column("action", "TEXT", True),        # Action taken (warn, pardon, mute, unmute, kick, ban, unban)
        Column("author", "INTEGER", True),     # User ID who applied the punishment
        Column("reason", "TEXT", False),       # Why the punishment was applied
        Column("temp", "BOOLEAN", True),       # Whether the action is temporary (warns and mutes)
        Column("expiry", "TIMESTAMP", False),  # When the punishment expires
        Column("handled", "INTEGER", True),    # Handled value (0 = Unhandled, 1 = Expired, 2 = Error, 3 = User left, 4 = Pardoned/Manually unmuted)
        Column("bot", "TEXT", True)            # Bot used for punishment
    ]),
    Table("reaction_groups", [
        Column("gid", "INTEGER", True),      # Guild ID
        Column("message", "INTEGER", True),  # Message ID
        Column("type", "INTEGER", True)      # Reaction Type (1-4)
    ]),
    Table("reaction_roles", [
        Column("message", "INTEGER", True),   # Message ID (Group)
        Column("reaction", "TEXT", True),     # Reaction Emoji
        Column("role", "INTEGER", True)       # Role ID
    ]),
    Table("reaction_tracking", [              # Track if someone already has a role (dType 2 and 4 reaction groups)
        Column("message", "INTEGER", True),   # Message ID (Group)
        Column("uid", "INTEGER", True),       # User ID
    ]),
    Table("reminders", [
        Column("id", "INTEGER", True, True),  # Reminder ID
        Column("uid", "INTEGER", True),       # User ID
        Column("expiry", "TIMESTAMP", True),  # Expiry (as datetime string)
        Column("message", "TEXT", True),      # Reminder message
        Column("handled", "INTEGER", True),   # Handled value (0 = Unhandled, 1 = Expired, 2 = Error)
        Column("bot", "TEXT", True)           # Bot used for reminder
    ]),
    Table("settings", [
        Column("gid", "INTEGER", True),
        Column("bot", "TEXT", True),  # The name of the bot to which the settings belong
        Column("data", "TEXT", True)
    ]),
    Table("starboard", [
        Column("message", "INTEGER", True),       # Original message ID
        Column("channel", "INTEGER", True),       # Original message's channel ID
        Column("author", "INTEGER", True),        # Original message's author's user ID
        Column("guild", "INTEGER", True),         # Original message's guild ID
        Column("stars", "INTEGER", True),         # Star count
        Column("star_message", "INTEGER", False)  # Starboard message ID
    ]),
    Table("tags", [
        Column("gid", "INTEGER", True),
        Column("creator", "INTEGER", True),
        Column("owner", "INTEGER", True),
        Column("name", "TEXT", True),
        Column("content", "TEXT", True),
        Column("created", "INTEGER", True),
        Column("edited", "INTEGER", True),
        Column("usage", "INTEGER", True)
    ]),
    Table("timezones", [
        Column("uid", "INTEGER", True),
        Column("tz", "TEXT", True)
    ]),
    Table("trials", [
        Column("guild_id", "INTEGER", True),        # The Guild ID where the trial was started
        Column("channel_id", "INTEGER", True),      # The Channel ID of the trial status message
        Column("message_id", "INTEGER", True),      # The Message ID of the trial status message
        Column("trial_id", "INTEGER", True),        # The Trial ID
        Column("author_id", "INTEGER", True),       # The User ID of who started the trial
        Column("user_id", "INTEGER", True),         # The User ID, to which the action will be done if the trial succeeds
        Column("type", "TEXT", True),               # The type of trial (ban, unban, kick, mute, unmute)
        Column("mute_length", "INTEGER", True),     # The mute length in seconds (if the trial type is mute)
        Column("reason", "TEXT", True),             # The reason for starting the trial ([Author#1234] Reason)
        Column("voters_yes", "TEXT", True),         # List of users who voted Yes
        Column("voters_neutral", "TEXT", True),     # List of users who voted Neutral
        Column("voters_no", "TEXT", True),          # List of users who voted No
        Column("start_time", "REAL", True),         # Timestamp when the trial was started
        Column("expiry", "TIMESTAMP", True),        # When the poll ends
        Column("anonymous", "BOOLEAN", True),       # Whether the poll is anonymous or not
        Column("required_score", "INTEGER", True),  # Score required for the trial to pass
    ]),
    Table("user_roles", [                 # We should only need to log people who left with roles, so we only need this much data
        Column("gid", "INTEGER", True),   # Guild ID
        Column("uid", "INTEGER", True),   # User ID
        Column("roles", "TEXT", True)     # JSON list of role IDs the user had
    ]),
]
