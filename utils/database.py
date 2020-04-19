import sqlite3

from utils import time
types = [
    "INTEGER",   # int
    "REAL",      # float
    "TEXT",      # str
    "BOOLEAN",   # bool
    "TIMESTAMP"  # datetime
]
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
        self.conn = sqlite3.connect(
            "database.db", isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES
        )
        self.conn.row_factory = dict_factory
        self.db = self.conn.cursor()

    def execute(self, sql: str, prepared: tuple = ()):
        """ Execute SQL command with args for 'Prepared Statements' """
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
        """ Fetch DB data with args for 'Prepared Statements' """
        data = self.db.execute(sql, prepared).fetchall()
        return data

    def fetchrow(self, sql: str, prepared: tuple = ()):
        """ Fetch DB row (one row only) with args for 'Prepared Statements' """
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
            print(f"{time.time()} > {self.name} > {result}")


def creation():
    try:
        for table in tables:
            table.create()
        return True
    except Exception as e:
        print(f"{type(e).__name__}: {e}")
        return False


tables = [
    Table("birthdays", [
        Column("uid", 0, True),
        Column("birthday", 4, True),
        Column("has_role", 3, True)
    ]),
    Table("custom_role", [
        Column("uid", 0, True),
        Column("rid", 0, True)
    ]),
    Table("data_stable", [
        Column("id", 0, True),
        Column("type", 2, True),
        Column("data", 2, True),
        Column("usage", 3, True),
        Column("name", 2, False),
        Column("disc", 0, False),
        Column("extra", 0, False)
    ]),
    Table("data_beta", [
        Column("id", 0, True),
        Column("type", 2, True),
        Column("data", 2, True),
        Column("usage", 3, True),
        Column("name", 2, False),
        Column("disc", 0, False),
        Column("extra", 0, False)
    ]),
    Table("data_alpha", [
        Column("id", 0, True),
        Column("type", 2, True),
        Column("data", 2, True),
        Column("usage", 3, True),
        Column("name", 2, False),
        Column("disc", 0, False),
        Column("extra", 0, False)
    ]),
    Table("economy", [
        Column("uid", 0, True),
        Column("gid", 0, True),
        Column("money", 0, True),
        Column("last", 1, True),
        Column("donated", 0, True),
        Column("name", 2, True),
        Column("disc", 0, True)
    ]),
    Table("leveling", [
        Column("uid", 0, True),
        Column("gid", 0, True),
        Column("level", 0, True),
        Column("xp", 0, True),  # int from 4.1
        Column("last", 1, True),
        Column("last_sent", 1, False),
        Column("last_messages", 2, False),
        Column("name", 2, True),
        Column("disc", 0, True)
    ]),
    Table("genders", [
        Column("uid", 0, True),
        Column("gender", 2, True)
    ]),
    Table("custom_rank", [
        Column("uid", 0, True),
        Column("font", 0, True),
        Column("progress", 0, True),
        Column("background", 0, True)
    ]),
    Table("counters", [
        Column("uid", 0, True),
        Column("gid", 0, True),
        Column("bangs_given", 0, True),
        Column("bangs_received", 0, True),
        Column("bites_given", 0, True),
        Column("bites_received", 0, True),
        Column("cuddles_given", 0, True),
        Column("cuddles_received", 0, True),
        Column("high_fives_given", 0, True),
        Column("high_fives_received", 0, True),
        Column("hugs_given", 0, True),
        Column("hugs_received", 0, True),
        Column("kisses_given", 0, True),
        Column("kisses_received", 0, True),
        Column("licks_given", 0, True),
        Column("licks_received", 0, True),
        Column("pats_given", 0, True),
        Column("pats_received", 0, True),
        Column("slaps_given", 0, True),
        Column("slaps_received", 0, True),
        Column("sniffs_given", 0, True),
        Column("sniffs_received", 0, True),
        Column("bad_given", 0, True),
        Column("bad_received", 0, True),
        Column("beaned", 0, True),
        Column("beans_given", 0, True),
        Column("shipped", 0, True),
        Column("ships_built", 0, True),
        Column("trashed", 0, True),
        Column("trash_given", 0, True),
        Column("blushed", 0, True),
        Column("cried", 0, True),
        Column("sleepy", 0, True),
        Column("smiled", 0, True),
        Column("carrots_received", 0, True),
        Column("carrots_eaten", 0, True),
        Column("cookies_received", 0, True),
        Column("cookies_eaten", 0, True),
        Column("fruits_received", 0, True),
        Column("fruits_eaten", 0, True),
        Column("lemons_received", 0, True),
        Column("lemons_eaten", 0, True)
    ])
]
