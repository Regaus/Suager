import pytz

from utils import database

__all__ = [
    "real_time_filename", "vehicles_filename", "TIMEZONE", "CHUNK_SIZE", "get_database", "get_data_database", "GTFSAPIError"
]


# Constants
real_time_filename = "data/gtfs/real_time.json"
vehicles_filename = "data/gtfs/vehicles.json"
TIMEZONE = pytz.timezone("Europe/Dublin")
CHUNK_SIZE = 256


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
