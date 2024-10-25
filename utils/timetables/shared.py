import json

import pytz

from utils import database

__all__ = (
    "__version__",
    "real_time_filename", "vehicles_filename", "trains_filename",
    "TIMEZONE", "CHUNK_SIZE", "WEEKDAYS", "NUMBERS", "WARNING", "CANCELLED",
    "get_database", "get_data_database",
    "GTFSAPIError",
)


# Constants
__version__ = json.load(open("version.json", "r"))["timetables"]["version"]

real_time_filename = "data/gtfs/real_time.json"
vehicles_filename = "data/gtfs/vehicles.json"
trains_filename = "data/gtfs/trains.xml"
TIMEZONE = pytz.timezone("Europe/Dublin")
CHUNK_SIZE = 256

WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
NUMBERS = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
WARNING = "⚠️ "
CANCELLED = "⛔\u2060 "  # Insert a zero-width non-breaking space to even out the string length


def get_database() -> database.Database:
    """ Returns the database for static GTFS data """
    return database.Database("gtfs/static.db")


def get_data_database() -> database.Database:
    """ Returns the database for general bot data (including Timetables bot's route filter) """
    return database.Database("database.db")


class GTFSAPIError(RuntimeError):
    """ An error occurred when requesting data from the GTFS API """
    def __init__(self, text=None, error_place: str = None):
        # error_place = whether the error occurred at real-time data or vehicle data
        super().__init__(text)
        self.error_place = error_place
