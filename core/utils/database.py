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
    Table("economy", [  # New Economy
        Column("uid", 0, True),
        # Column("gid", 0, True),
        Column("money", 0, True),
        Column("daily", 0, True),
        Column("streak", 0, True),
        Column("rsbk", 2, True),
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
    ])
]
