import re
import sqlite3
from datetime import datetime, date
from typing import Any

from utils import general, logger, time


def adapt_date_iso(val: date) -> str:
    """ Convert date object into ISO timestamp """
    return val.isoformat()


def adapt_datetime_iso(val: datetime) -> str:
    """ Convert datetime object into ISO timestamp """
    return val.isoformat(sep=" ")


def convert_date(val: bytes) -> date:
    """ Convert ISO date back into date object """
    return date.fromisoformat(val.decode("latin1"))


def convert_datetime(val: bytes) -> datetime:
    """ Convert ISO timestamp back into datetime object """
    return datetime.fromisoformat(val.decode("latin1"))


sqlite3.register_adapter(date, adapt_date_iso)
sqlite3.register_adapter(datetime, adapt_datetime_iso)
sqlite3.register_converter("date", convert_date)
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
    def __init__(self, filename: str = "database.db"):
        self.conn = sqlite3.connect(f"data/{filename}", isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.row_factory = dict_factory
        self.conn.create_function("REGEXP", 2, regex_function)
        self.conn.create_function("APRILMULT", 0, april_fools_multiplier)
        self.db = self.conn.cursor()

    def execute(self, sql: str, parameters: tuple[Any, ...] = (), /) -> str:
        """ Execute SQL command """
        try:
            data = self.db.execute(sql, parameters)
        except Exception as e:
            now = f"{datetime.now():%d %b %Y, %H:%M:%S}"
            msg = f"{now} > Database > {type(e).__name__}: {e}\n" \
                  f"{now} > Database > SQL statement: {sql}\n" \
                  f"{now} > Database > Values given: {parameters}"
            general.print_error(msg)
            logger.log("suager", "database", msg)
            return f"{type(e).__name__}: {e}"
        status_word = sql.split(' ')[0].upper()
        status_code = data.rowcount if data.rowcount > 0 else 0
        if status_word == "SELECT":
            status_code = len(data.fetchall())
        return f"{status_word} {status_code}"

    def executemany(self, sql: str, parameters_iter: list[tuple[Any, ...]], /) -> str:
        """ Execute the same SQL command over multiple different values """
        try:
            data = self.db.executemany(sql, parameters_iter)
        except Exception as e:
            now = f"{datetime.now():%d %b %Y, %H:%M:%S}"
            msg = f"{now} > Database > {type(e).__name__}: {e}\n" \
                  f"{now} > Database > SQL statement (many): {sql}\n" \
                  f"{now} > Database > Values given: {parameters_iter}"
            general.print_error(msg)
            logger.log("suager", "database", msg)
            return f"{type(e).__name__}: {e}"
        status_word = sql.split(' ')[0].upper()
        status_code = data.rowcount if data.rowcount > 0 else 0
        if status_word == "SELECT":
            status_code = len(data.fetchall())
        return f"{status_word} {status_code}"

    def executescript(self, sql: str, /) -> str:
        """ Execute an entire SQL script """
        try:
            self.db.executescript(sql)
        except Exception as e:
            now = f"{datetime.now():%d %b %Y, %H:%M:%S}"
            msg = f"{now} > Database > {type(e).__name__}: {e}\n" \
                  f"{now} > Database > SQL Script: {sql}\n"
            general.print_error(msg)
            logger.log("suager", "database", msg)
            return f"{type(e).__name__}: {e}"
        return "SUCCESS"

    def fetch(self, sql: str, parameters: tuple[Any, ...] = (), /) -> list[dict[str, Any]]:
        """ Fetch data from DB """
        data = self.db.execute(sql, parameters).fetchall()
        return data

    def fetchrow(self, sql: str, parameters: tuple[Any, ...] = (), /) -> dict[str, Any]:
        """ Fetch one row of data from DB """
        data = self.db.execute(sql, parameters).fetchone()
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
    def __init__(self, name: str, filename: str, columns: list, extra_sql: str = ""):
        self.name = name
        self.filename = filename  # Filename for the database
        self.columns = columns
        self.extra_sql = extra_sql

    def create(self):
        start = f"CREATE TABLE IF NOT EXISTS {self.name} (\n"
        strings = [str(column) for column in self.columns]
        if self.extra_sql:
            strings.append(self.extra_sql)
        middle = ",\n".join(strings)
        end = "\n);"
        command = f"{start}{middle}{end}"
        db = Database(self.filename)
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
    Table("birthdays", "database.db", [
        Column("uid", "INTEGER", True),
        Column("birthday", "DATE", True),
        Column("has_role", "BOOLEAN", True),
        Column("bot", "TEXT", True),
    ]),
    Table("counters", "database.db", [
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
        Column("tuck", "INTEGER", True),       # 24
        Column("wave", "INTEGER", True),       # 25
    ]),
    Table("custom_rank", "database.db", [
        Column("uid", "INTEGER", True),
        Column("font", "INTEGER", False),        # Text colour
        Column("progress", "INTEGER", False),    # Progress bar colour
        Column("background", "INTEGER", False),  # Background colour
        Column("custom_font", "TEXT", False),    # Font to use
    ]),
    Table("custom_role", "database.db", [
        Column("uid", "INTEGER", True),
        Column("rid", "INTEGER", True),
        Column("gid", "INTEGER", True)
    ]),
    Table("kargadia", "database.db", [
        Column("id", "INTEGER", True, True),   # Citizen ID
        Column("uid", "INTEGER", True),        # Discord User ID
        Column("protected", "INTEGER", True),  # Privacy enum: 0 = Show all, 1 = "Protected" (only viewable by me and that user), 2 = Hide age, 3 = Protected + Age hidden
        Column("name", "TEXT", True),          # First Name
        Column("name2", "TEXT", False),        # Parent Name
        Column("name3", "TEXT", False),        # Surname
        Column("gender", "TEXT", True),        # Gender - m/f/n/u
        Column("birthday", "TEXT", False),     # Kargadian birthday - iso date string
        Column("has_role", "BOOLEAN", True),   # Is it currently the person's Kargadian birthday?
        Column("location", "TEXT", False),     # Kargadian location - can also be used to determine timezone
        Column("joined", "TEXT", False),       # When the user joined as an Earth date
    ]),
    Table("leveling", "database.db", [
        Column("uid", "INTEGER", True),
        Column("gid", "INTEGER", True),
        Column("level", "INTEGER", True),
        Column("xp", "INTEGER", True),
        Column("last", "REAL", True),
        Column("last_sent", "REAL", False),
        Column("name", "TEXT", True),
        Column("disc", "INTEGER", True),
        Column("bot", "TEXT", True),
        Column("remove", "DATE", False),  # The date on which to delete the database entry
    ]),
    Table("locales", "database.db", [    # Language settings for servers
        Column("id", "INTEGER", True),   # ID of the guild, channel, or user
        Column("locale", "TEXT", True),  # Language chosen
        Column("bot", "TEXT", True),     # Name of the bot
        Column("type", "TEXT", True),    # Type: "guild", "channel", or "user"
    ]),
    Table("polls", "database.db", [
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
    Table("punishments", "database.db", [
        Column("id", "INTEGER", True, True),   # Case ID
        Column("uid", "INTEGER", True),        # User ID, the punished
        Column("gid", "INTEGER", True),        # Guild ID
        Column("action", "TEXT", True),        # Action taken (warn, pardon, mute, unmute, kick, ban, unban)
        Column("author", "INTEGER", True),     # User ID who applied the punishment
        Column("reason", "TEXT", False),       # Why the punishment was applied
        Column("temp", "BOOLEAN", True),       # Whether the action is temporary (warns and mutes)
        Column("expiry", "TIMESTAMP", False),  # When the punishment expires
        Column("handled", "INTEGER", True),    # Handled value (0 = Unhandled, 1 = Expired, 2 = Error, 3 = User left, 4 = Pardoned/Manually unmuted)
        Column("bot", "TEXT", True),           # Bot used for punishment
        Column("remove", "DATE", False),       # The date on which to delete the database entry
    ]),
    Table("reaction_groups", "database.db", [
        Column("gid", "INTEGER", True),      # Guild ID
        Column("channel", "INTEGER", True),  # Channel ID
        Column("message", "INTEGER", True),  # Message ID - Must be unique
        Column("type", "INTEGER", True),     # Reaction Type (1-4)
        Column("start", "TEXT", False),      # Reaction message start (Optional)
        Column("end", "TEXT", False),        # Reaction message end (Optional)
        Column("style", "TEXT", True),       # Reaction list style (Required)
        Column("bot", "TEXT", True),         # The bot responsible for interactions with this group
    ], "UNIQUE(message)"),
    Table("reaction_roles", "database.db", [
        Column("message", "INTEGER", True),   # Message ID (Group)
        Column("ord", "INTEGER", True),       # Order of the reaction within the group
        Column("reaction", "TEXT", True),     # Reaction Emoji
        Column("role", "INTEGER", True)       # Role ID
    ], "UNIQUE(message, ord)"),
    Table("reaction_tracking", "database.db", [  # Track if someone already has a role (Type 2 and 4 reaction groups)
        Column("message", "INTEGER", True),   # Message ID (Group)
        Column("uid", "INTEGER", True),       # User ID
    ], "UNIQUE(message, uid)"),
    Table("reminders", "database.db", [
        Column("id", "INTEGER", True, True),  # Reminder ID
        Column("uid", "INTEGER", True),       # User ID
        Column("expiry", "TIMESTAMP", True),  # Expiry (as datetime string)
        Column("message", "TEXT", True),      # Reminder message
        Column("handled", "INTEGER", True),   # Handled value (0 = Unhandled, 1 = Expired, 2 = Error)
        Column("bot", "TEXT", True)           # Bot used for reminder
    ]),
    Table("settings", "database.db", [
        Column("gid", "INTEGER", True),
        Column("bot", "TEXT", True),      # The name of the bot to which the settings belong
        Column("data", "TEXT", True),
        Column("remove", "DATE", False),  # The date on which to delete the database entry
    ]),
    Table("starboard", "database.db", [
        Column("message", "INTEGER", True),        # Original message ID
        Column("channel", "INTEGER", True),        # Original message's channel ID
        Column("author", "INTEGER", True),         # Original message's author's user ID
        Column("guild", "INTEGER", True),          # Original message's guild ID
        Column("stars", "INTEGER", True),          # Star count
        Column("star_message", "INTEGER", False),  # Starboard message ID
        Column("bot", "TEXT", True),               # The bot tracking the message
        Column("remove", "DATE", False),           # The date on which to delete the database entry
    ]),
    Table("tags", "database.db", [
        Column("gid", "INTEGER", True),
        Column("creator", "INTEGER", True),
        Column("owner", "INTEGER", True),
        Column("name", "TEXT", True),
        Column("content", "TEXT", True),
        Column("created", "INTEGER", True),
        Column("edited", "INTEGER", True),
        Column("usage", "INTEGER", True),
        Column("bot", "TEXT", True),      # The bot for which the tag was created
        Column("remove", "DATE", False),  # The date on which to delete the database entry
    ]),
    Table("timezones", "database.db", [
        Column("uid", "INTEGER", True),
        Column("tz", "TEXT", True)
    ]),
    Table("user_roles", "database.db", [  # We should only need to log people who left with roles, so we only need this much data
        Column("gid", "INTEGER", True),   # Guild ID
        Column("uid", "INTEGER", True),   # User ID
        Column("roles", "TEXT", True)     # JSON list of role IDs the user had
    ]),
    Table("route_filters", "database.db", [  # Route filters for Timetables bot
        Column("user_id", "INTEGER", True),  # The user for whom to filter departures
        Column("stop_id", "TEXT", True),     # Stop ID at which to apply the filter
        Column("routes", "TEXT", True),      # JSON list of routes to filter
    ], "UNIQUE(user_id, stop_id)"),

    # Pretender database
    Table("pretender_blacklist", "pretender.db", [  # Users ignored for message logging
        Column("uid", "INTEGER", True),  # Blacklisted User's ID
    ]),
    Table("pretender_messages", "pretender.db", [  # All the messages
        Column("id", "INTEGER", True, True),  # Message ID
        Column("author", "INTEGER", True),    # Message author ID
        Column("channel", "INTEGER", False),  # Message channel ID
        Column("content", "TEXT", True)       # Message content
    ]),
    Table("pretender_webhooks", "pretender.db", [  # Stores webhooks for channels
        Column("id", "INTEGER", True),      # Webhook ID
        Column("token", "TEXT", True),      # Webhook's token
        Column("channel", "INTEGER", True)  # Webhook's channel ID
    ]),

    # GTFS database
    Table("agencies", "gtfs/static.db", [
        Column("id", "TEXT", True, True),  # Primary key: Agency ID
        Column("name", "TEXT", True),
        Column("url", "TEXT", True),
        Column("timezone", "TEXT", True),
    ]),
    Table("calendars", "gtfs/static.db", [
        Column("service_id", "TEXT", True, True),  # Primary key: Service ID
        Column("data", "INTEGER", True),     # An integer storing 7 booleans corresponding to whether the service runs on each weekday
        Column("start_date", "DATE", True),  # Note: this will store as datetime.date
        Column("end_date", "DATE", True),    # Note: this will store as datetime.date
    ]),
    Table("calendar_exceptions", "gtfs/static.db", [
        Column("service_id", "TEXT", True),     # Should match Calendar.service_id
        Column("date", "DATE", True),           # Note: this will store as datetime.date
        Column("exception", "BOOLEAN", True),   # True -> Added, False -> Removed
    ], "UNIQUE(service_id, date)"),             # Constraint: Service ID + date
    Table("routes", "gtfs/static.db", [
        Column("id", "TEXT", True, True),        # Primary key: Route ID
        Column("agency_id", "INTEGER", True),    # Route operator
        Column("short_name", "TEXT", True),      # Route name for people
        Column("long_name", "TEXT", True),       # Route description for people
        Column("route_desc", "TEXT", True),      # Route Description - usually empty
        Column("route_type", "INTEGER", True),   # Tram/Subway/Rail/Bus
        Column("route_url", "TEXT", True),       # Route URL - Not provided by Irish public transport
        Column("route_colour", "TEXT", True),
        Column("route_text_colour", "TEXT", True),
    ]),
    Table("stops", "gtfs/static.db", [
        Column("id", "TEXT", True, True),        # Primary key: Full Stop ID
        Column("code", "TEXT", True),            # Short code (Dublin Bus / Bus Éireann)
        Column("name", "TEXT", True),            # Stop name
        Column("description", "TEXT", True),     # Stop description - usually empty
        Column("latitude", "REAL", True),
        Column("longitude", "REAL", True),
        Column("zone_id", "TEXT", True),         # Fare zone
        Column("stop_url", "TEXT", True),        # URL to a webpage about the location
        Column("location_type", "TEXT", True),   # Stop, Station or whatever else - empty
        Column("parent_station", "TEXT", True),  # Empty in our case
    ]),
    Table("trips", "gtfs/static.db", [
        Column("route_id", "TEXT", True),         # Route served by the Trip
        Column("calendar_id", "TEXT", True),      # Schedule followed by the Trip
        Column("trip_id", "TEXT", True, True),    # Primary key: Trip ID
        Column("headsign", "TEXT", True),         # Destination shown
        Column("short_name", "TEXT", True),
        Column("direction_id", "INTEGER", True),  # 0 -> outbound, 1 -> inbound
        Column("block_id", "TEXT", True),
        Column("shape_id", "TEXT", True),         # ID of geospatial shape of the trip
        Column("total_stops", "INTEGER", True),   # Total number of stop times associated with the trip
    ]),
    Table("stop_times", "gtfs/static.db", [
        Column("trip_id", "TEXT", True),            # Trip ID this stop time belongs to
        Column("arrival_time", "INTEGER", True),    # Arrival time as number of seconds since midnight
        Column("departure_time", "INTEGER", True),  # Departure time as number of seconds since midnight
        Column("stop_id", "TEXT", True),            # Stop ID served by this stop time
        Column("sequence", "INTEGER", True),        # Order of the stop along the route
        Column("stop_headsign", "TEXT", True),      # In case the headsign changes at a certain stop
        Column("pickup_type", "INTEGER", True),     # 0 or empty -> Pickup, 1 -> No pickup
        Column("drop_off_type", "INTEGER", True),   # 0 or empty -> Drop off, 1 -> No drop off
        Column("timepoint", "INTEGER", True),       # 0 -> Times are approximate, 1 -> Times are exact
    ], "UNIQUE(trip_id, sequence)"),                 # Constraint: Trip ID + Sequence
    Table("shapes", "gtfs/static.db", [
        Column("shape_id", "TEXT", True),            # ID of the shape
        Column("sequence", "INTEGER", True),         # Order of the shape point
        Column("latitude", "REAL", True),            # Coordinates of the shape point
        Column("longitude", "REAL", True),
        Column("distance_travelled", "REAL", True),  # Total distance travelled along the line up until this point
    ], "UNIQUE(shape_id, sequence)"),                # Constraint: Shape ID + Sequence
    Table("expiry", "gtfs/static.db", [
        Column("type", "INTEGER", True, True),  # 0 -> soft limit, 1 -> hard limit | 2 -> vehicle data
        Column("date", "DATE", True)            # Date when expiry limit is reached
    ]),
    Table("vehicles", "gtfs/static.db", [
        Column("vehicle_id", "TEXT", True, True),     # Vehicle ID used by the GTFS-R API
        Column("fleet_number", "TEXT", True),         # Fleet number (e.g. "AH1")
        Column("reg_plates", "TEXT", True),           # Reg plates (e.g. "191-D-44403")
        Column("model", "TEXT", True),                # Model name (e.g. "ADL Enviro400H MMC")
        Column("trivia", "TEXT", False),              # Trivia (e.g. presence of USB sockets)
    ])
]
