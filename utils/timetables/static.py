from __future__ import annotations

from collections import namedtuple
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any, Type

import pandas
from regaus import time

from utils import database
from utils.timetables.shared import CHUNK_SIZE, get_database

__all__ = [
    "str_to_date", "time_to_int",
    "GTFSData", "Agency", "Calendar", "CalendarException", "Route", "Stop", "Trip", "StopTime",
    "load_csv_lines", "check_gtfs_data_expiry", "iterate_over_csv_full",
    "read_and_store_gtfs_data", "init_gtfs_data",
    "load_calendars", "load_value"
]


def _weekdays_to_int(weekdays: tuple[bool, bool, bool, bool, bool, bool, bool]) -> int:
    """ For Calendars - converts the weekdays list to a single integer """
    return sum(map(lambda x: x[1] << x[0], enumerate(weekdays)))


def _int_to_weekdays(weekdays: int) -> tuple[bool, bool, bool, bool, bool, bool, bool]:
    """ For Calendars - converts the single integer into a weekdays list """
    return tuple(bool(weekdays & (1 << n)) for n in range(7))  # type: ignore


def str_to_date(value: str) -> time.date:
    """ Convert YYYYMMDD string to date """
    value = str(value)  # Force string conversion, in case the value is accidentally interpreted as int
    year = value[:4]
    month = value[4:6]
    day = value[6:]
    return time.date(int(year), int(month), int(day))


def time_to_int(value: str) -> int:
    """ Convert HH:MM:SS string to integer (seconds since midnight) """
    h, m, s = value.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


@dataclass()
class GTFSData:
    # agencies[agency_id] = Agency
    agencies: dict[str, Agency]  # int
    # calendars[service_id] = Calendar
    calendars: dict[str, Calendar]  # int
    # calendar_exceptions[service_id][date] = CalendarException
    calendar_exceptions: dict[str, dict[time.date, CalendarException]]  # int
    # routes[route_id] = Route
    routes: dict[str, Route]
    # stops[stop_id] = Stop
    stops: dict[str, Stop]
    # schedules[trip_id] = [StopTime, StopTime, StopTime, ...]
    # schedules: dict[str, list[StopTime]]
    # stop_times[trip_id][stop_id] = StopTime - Stores specific stop times for a given route
    stop_times: dict[str, dict[str, StopTime]]
    # trips[trip_id] = Trip
    trips: dict[str, Trip]

    def __repr__(self):
        return "This string is too large to be feasible to render."


@dataclass()
class Agency:
    id: str  # int
    name: str
    url: str
    timezone: str

    def __repr__(self):
        # "Agency 7778019 - Bus Átha Cliath / Dublin Bus"
        return f"Agency {self.id} - {self.name}"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Agency:
        """ Construct a new Agency object from a dictionary """
        return cls(data["id"], data["name"], data["url"], data["timezone"])

    @classmethod
    def from_sql(cls, agency_id: str, db: database.Database = None) -> Agency:
        """ Load an Agency from the SQL database """
        if not db:
            db = get_database()
        return cls.from_dict(db.fetchrow("SELECT * FROM agencies WHERE id=?", (agency_id,)))

    def save_to_sql(self) -> str:
        """ Save the Agency to the SQL database"""
        return f"INSERT INTO agencies(id, name, url, timezone) VALUES ({self.id!r}, {self.name!r}, {self.url!r}, {self.timezone!r})"


@dataclass()
class Calendar:
    service_id: str  # int
    # Tuple of 7 booleans corresponding to whether the service runs on each day of the week
    # This would be more convenient than trying to find the appropriate weekday's attribute
    data: tuple[bool, bool, bool, bool, bool, bool, bool]
    start_date: time.date
    end_date: time.date

    def __repr__(self):
        # "Calendar 3 - (True, True, True, True, True, False, False)"
        return f"Calendar {self.service_id} - {self.data}"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Calendar:
        """ Construct a new Calendar object from a dictionary """
        return cls(data["service_id"], _int_to_weekdays(data["data"]),
                   time.date.from_datetime(data["start_date"]), time.date.from_datetime(data["end_date"]))

    @classmethod
    def from_sql(cls, service_id: str, db: database.Database = None) -> Calendar:
        """ Load a Calendar object from the SQL database """
        if not db:
            db = get_database()
        return cls.from_dict(db.fetchrow("SELECT * FROM calendars WHERE service_id=?", (service_id,)))

    def save_to_sql(self) -> str:
        """ Save the Calendar to the SQL database """
        return ("INSERT INTO calendars(service_id, data, start_date, end_date) VALUES "
                f"({self.service_id!r}, {_weekdays_to_int(self.data)!r}, {database.adapt_date_iso(self.start_date.to_datetime())!r}, {database.adapt_date_iso(self.end_date.to_datetime())!r})")


@dataclass()
class CalendarException:
    """ Exceptions to the regular calendar """
    service_id: str  # int  # Should match Calendar.service_id
    date: time.date
    # Exception types:
    # 1 -> Service has been added for the specified date
    # 2 -> Service has been removed for the specified date
    # My implementation returns a bool of (exception_type != 2)
    exception: bool

    def __repr__(self):
        # "Exception for Calendar 343 - 2023-10-13 -> False"
        return f"Exception for Calendar {self.service_id} - {self.date} -> {self.exception}"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CalendarException:
        """ Construct a new CalendarException object from a dictionary """
        return cls(data["service_id"], time.date.from_datetime(data["date"]), data["exception"])

    @classmethod
    def from_sql(cls, service_id: str, db: database.Database = None) -> list[CalendarException]:
        """ Load all CalendarExceptions from the SQL database for a given service ID """
        if not db:
            db = get_database()
        return list(map(cls.from_dict, db.fetch("SELECT * FROM calendar_exceptions WHERE service_id=?", (service_id,))))

    def save_to_sql(self) -> str:
        """ Save the CalendarException to the SQL database """
        return ("INSERT INTO calendar_exceptions(service_id, date, exception) VALUES "
                f"({self.service_id!r}, {database.adapt_date_iso(self.date.to_datetime())!r}, {self.exception!r})")


@dataclass()
class Route:
    id: str
    agency_id: str  # int
    # agency: Agency
    short_name: str  # Usually something like "145", "39A", "DART"
    long_name: str   # Usually something like "Ballywaltrim - Heuston Station"
    route_desc: str  # Description - Doesn't seem to be provided by Irish public transport
    # Route types: 0 -> Tram | 1 -> Subway | 2 -> Rail | 3 -> Bus
    route_type: int
    route_url: str   # URL to route info - Doesn't seem to be provided by Irish public transport
    route_colour: str
    route_text_colour: str

    # @property
    def agency(self) -> Agency:
        return Agency.from_sql(self.agency_id)

    # def agency(self, data: GTFSData) -> Agency:
    #     return load_value_from_id(data, "agency.txt", str(self.agency_id), None)

    # @property
    # def agency(self) -> Agency:
    #     return load_value_from_id(None, "agency.txt", str(self.agency_id))

    def __repr__(self):
        # # "Route 3643_54890 (DART) - Bray - Howth - Operated by Agency 7778017"
        # return f"Route {self.id} ({self.short_name}) - {self.long_name} - Operated by Agency {self.agency_id}"

        # "Route 3643_54890 (DART) - Bray - Howth - Operated by Agency 7778017 - Iardród Éireann / Irish Rail"
        return f"Route {self.id} ({self.short_name}) - {self.route_desc} - Operated by {self.agency()!r}"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Route:
        """ Construct a new Route object from a dictionary """
        return cls(data["id"], data["agency_id"], data["short_name"], data["long_name"], data["route_desc"],
                   data["route_type"], data["route_url"], data["route_colour"], data["route_text_colour"])

    @classmethod
    def from_sql(cls, route_id: str, db: database.Database = None) -> Route:
        """ Load a Route from the SQL database """
        if not db:
            db = get_database()
        return cls.from_dict(db.fetchrow("SELECT * FROM routes WHERE id=?", (route_id,)))

    def save_to_sql(self) -> str:
        """ Save the Route to the SQL database """
        return ("INSERT INTO routes(id, agency_id, short_name, long_name, route_desc, route_type, route_url, route_colour, route_text_colour) VALUES "
                f"({self.id!r}, {self.agency_id!r}, {self.short_name!r}, {self.long_name!r}, {self.route_desc!r}, "
                f"{self.route_type!r}, {self.route_url!r}, {self.route_colour!r}, {self.route_text_colour!r})")


@dataclass()
class Stop:
    id: str              # Full ID of the stop
    code: str            # Short code for the stop (Dublin Bus / Bus Éireann)
    name: str            # Stop name
    description: str     # Description - Seems to be empty
    latitude: float      # Latitude
    longitude: float     # Longitude
    zone_id: str         # Used for fare zones - Doesn't seem to be used by Irish public transport
    stop_url: str        # URL to a web page about the location (?)
    location_type: str   # Type: stop, station, or something else - Empty in our case
    parent_station: str  # Empty in our case

    @property
    def code_or_id(self):
        """ Returns the stop code if available, else stop ID """
        return self.code or self.id

    def __repr__(self):
        # "Stop 8220DB000334 (334) - D'Olier Street"
        return f"Stop {self.id} ({self.code}) - {self.name}"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Stop:
        """ Construct a new Stop object from a dictionary """
        return cls(data["id"], data["code"], data["name"], data["description"], data["latitude"], data["longitude"],
                   data["zone_id"], data["stop_url"], data["location_type"], data["parent_station"])

    @classmethod
    def from_sql(cls, stop_id: str, db: database.Database = None) -> Stop:
        """ Load a Stop from the SQL database """
        if not db:
            db = get_database()
        return cls.from_dict(db.fetchrow("SELECT * FROM stops WHERE id=?", (stop_id,)))

    def save_to_sql(self) -> str:
        """ Save the Stop to the SQL database """
        return ("INSERT INTO stops(id, code, name, description, latitude, longitude, zone_id, stop_url, location_type, parent_station) VALUES "
                f"({self.id!r}, {self.code!r}, {self.name!r}, {self.description!r}, {self.latitude!r}, {self.longitude!r}, "
                f"{self.zone_id!r}, {self.stop_url!r}, {self.location_type!r}, {self.parent_station!r})")


@dataclass()
class Trip:
    route_id: str
    # route: Route
    calendar_id: str  # int
    # calendar: Calendar
    trip_id: str
    headsign: str      # What is shown as the destination, can be overridden by StopTime.stop_headsign
    short_name: str    # Supposed to be text identifying the trip to riders - in reality, useless gibberish
    direction_id: int  # 0 -> outbound, 1 -> inbound
    block_id: str      # "A block consists of a single trip or many sequential trips made using the same vehicle"
    shape_id: str      # ID of geospatial shape (not really useful for my case)

    # @property
    def route(self) -> Route:
        return Route.from_sql(self.route_id)

    # def route(self, data: GTFSData) -> Route:
    #     return load_value_from_id(data, "routes.txt", self.route_id, None)

    # @property
    # def route(self) -> Route:
    #     return load_value_from_id(None, "routes.txt", self.route_id)

    # @property
    def calendar(self) -> Calendar:
        return Calendar.from_sql(self.calendar_id)

    # def calendar(self, data: GTFSData) -> Calendar:
    #     return load_value_from_id(data, "calendar.txt", str(self.calendar_id), None)

    # @property
    # def calendar(self) -> Calendar:
    #     return load_value_from_id(None, "calendar.txt", str(self.calendar_id))

    def __repr__(self):
        # "Trip 3626_209 to Charlesland, stop 7462 - Route 3626_39040
        return f"Trip {self.trip_id} to {self.headsign} - Route {self.route_id}"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Trip:
        """ Construct a new Trip object from a dictionary """
        return cls(data["route_id"], data["calendar_id"], data["trip_id"], data["headsign"],
                   data["short_name"], data["direction_id"], data["block_id"], data["shape_id"])

    @classmethod
    def from_sql(cls, trip_id: str, db: database.Database = None) -> Trip:
        """ Load a Trip from the SQL database """
        if not db:
            db = get_database()
        return cls.from_dict(db.fetchrow("SELECT * FROM trips WHERE trip_id=?", (trip_id,)))

    def save_to_sql(self) -> str:
        """ Save the Trip to the SQL database """
        return ("INSERT INTO trips(route_id, calendar_id, trip_id, headsign, short_name, direction_id, block_id, shape_id) VALUES "
                f"({self.route_id!r}, {self.calendar_id!r}, {self.trip_id!r}, {self.headsign!r}, {self.short_name!r}, {self.direction_id!r}, {self.block_id!r}, {self.shape_id!r})")


@dataclass()
class StopTime:
    trip_id: str
    # trip: Trip
    arrival_time: int   # Return the number of seconds since midnight, to avoid breaking with their silly "28:30:00"
    departure_time: int
    stop_id: str
    # stop: Stop
    sequence: int       # Order of the stop along the route
    stop_headsign: str  # I guess this is in case the "headsign" changes after a certain stop?
    pickup_type: int    # 0 or empty -> Pickup, 1 -> No pickup
    drop_off_type: int  # 0 or empty -> Drop off, 1 -> No drop off
    timepoint: int      # 0 -> Times are approximate, 1 or empty -> Time are exact (this is factually incorrect)

    # @property
    def trip(self) -> Trip:
        return Trip.from_sql(self.trip_id)

    # def trip(self, data: GTFSData) -> Trip:
    #     return load_value_from_id(data, "trips.txt", self.trip_id, None)

    def route(self) -> Route:
        return self.trip().route()

    # def route(self, data: GTFSData) -> Route:
    #     return self.trip(data).route(data)

    # @property
    # def trip(self) -> Trip:
    #     return load_value_from_id(None, "trips.txt", self.trip_id)

    # @property
    def stop(self) -> Stop:
        return Stop.from_sql(self.stop_id)

    # def stop(self, data: GTFSData) -> Stop:
    #     return load_value_from_id(data, "stops.txt", self.stop_id, None)

    # @property
    # def stop(self) -> Stop:
    #     return load_value_from_id(None, "stops.txt", self.stop_id)

    def __repr__(self):
        # This basically returns the time of departure modulo 24 hours
        departure_time = time.time.from_microsecond(self.departure_time * 1000000)
        # "StopTime - 02:00:00 - Stop #1 for Trip 3626_214"
        return f"StopTime - {departure_time} - Stop #{self.sequence} for Trip {self.trip_id}"
        # "StopTime - 02:00:00 to Charlesland, stop 7462 (Stop D'Olier Street - #1, Trip 3626_214)"
        # return f"StopTime - {departure_time} to {self.trip.headsign} (Stop {self.stop.name} - #{self.sequence}, Trip {self.trip.trip_id})"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StopTime:
        """ Construct a new StopTime object from a dictionary """
        return cls(data["trip_id"], data["arrival_time"], data["departure_time"], data["stop_id"],
                   data["sequence"], data["stop_headsign"], data["pickup_type"], data["drop_off_type"], data["timepoint"])

    @classmethod
    def from_sql(cls, trip_id: str, db: database.Database = None) -> list[StopTime]:
        """ Load all StopTimes associated with a given Trip ID, sorted by sequence """
        if not db:
            db = get_database()
        return sorted(list(map(cls.from_dict, db.fetch("SELECT * FROM stop_times WHERE trip_id=?", (trip_id,)))), key=lambda s: s.sequence)

    @classmethod
    def from_sql_specific(cls, trip_id: str, stop_id: str, db: database.Database = None) -> StopTime:
        """ Load a specific StopTime for a given Stop ID on a given Trip ID """
        if not db:
            db = get_database()
        return cls.from_dict(db.fetchrow("SELECT * FROM stop_times WHERE trip_id=? AND stop_id=?", (trip_id, stop_id)))

    def save_to_sql(self) -> str:
        """ Save the StopTime into the SQL database """
        return ("INSERT INTO stop_times(trip_id, arrival_time, departure_time, stop_id, sequence, stop_headsign, pickup_type, drop_off_type, timepoint) VALUES "
                f"({self.trip_id!r}, {self.arrival_time!r}, {self.departure_time!r}, {self.stop_id!r}, {self.sequence!r}, "
                f"{self.stop_headsign!r}, {self.pickup_type!r}, {self.drop_off_type!r}, {self.timepoint!r})")


# # Mapping of files to corresponding dataclasses
# class_mapping = {
#     "agency.txt": Agency,
#     "calendar.txt": Calendar,
#     "calendar_dates.txt": CalendarException,
#     "routes.txt": Route,
#     "stops.txt": Stop,
#     "stop_times.txt": StopTime,
#     "trips.txt": Trip
# }
# key_mapping = {
#     "agency.txt": "agencies",
#     "calendar.txt": "calendars",
#     "calendar_dates.txt": "calendar_exceptions",
#     "routes.txt": "routes",
#     "stops.txt": "stops",
#     "stop_times.txt": "schedules",
#     "trips.txt": "trips"
# }


def load_csv_lines(filename: str, start_line: int, length: int) -> list[tuple[Any, ...]]:
    """ Load a list of CSV lines from the required file """
    return list(pandas.read_csv("assets/gtfs/" + filename, skiprows=start_line + 1, nrows=length, header=None, na_filter=False).itertuples(index=False, name=None))


def check_gtfs_data_expiry(db: database.Database) -> bool:
    """ Check for GTFS data expiry

     If hard limit has been reached, raises an error.
     Otherwise, returns True if the soft limit has not yet been reached (and False if it has). """
    hard_expiry = db.fetchrow("SELECT * FROM expiry WHERE type=1")
    if not hard_expiry:
        raise RuntimeError("Expiry data not found.")
    if time.date.today() > time.date.from_datetime(hard_expiry["date"]):
        raise RuntimeError(f"GTFS Data expired on {hard_expiry['date']:%Y-%m-%d}")
    soft_expiry = db.fetchrow("SELECT * FROM expiry WHERE type=0")
    if not soft_expiry:
        return False
    return time.date.today() < time.date.from_datetime(soft_expiry["date"])


# def iterate_over_csv_partial(filename: str, skip_lines: list[int]) -> Generator[namedtuple, Any, None]:
#     """ Iterates over a CSV file while skipping certain lines """
#     with open("assets/gtfs/" + filename, "r", encoding="utf-8") as file:
#         for chunk in pandas.read_csv(file, chunksize=CHUNK_SIZE, na_filter=False, skiprows=skip_lines):
#             for row in chunk.itertuples():
#                 yield row


def iterate_over_csv_full(filename: str) -> Generator[namedtuple, Any, None]:
    """ Iterates over the full CSV file """
    with open("assets/gtfs/" + filename, "r", encoding="utf-8") as file:
        for chunk in pandas.read_csv(file, chunksize=CHUNK_SIZE, na_filter=False):  # type: pandas.DataFrame
            for row in chunk.itertuples():  # type: namedtuple
                yield row


# def iterate_over_csv_multiline(filename: str, key: str) -> Generator[tuple[str, str, int, int, str | None], Any, None]:
#     """ Iterates over a CSV file where values can span multiple lines """
#     # stop_times = filename == "stop_times.txt"
#     _id = None
#     data = [filename, "", 0, 0, None]
#     # stops = []
#     for row in iterate_over_csv_full(filename):
#         # If the ID is the same, add to length
#         if _id == getattr(row, key):
#             data[3] += 1
#             # if stop_times:
#             #     stops.append(str(row.stop_id))
#         # If a new ID is reached, save the existing data and begin counting again
#         else:
#             # Save previous data
#             if _id is not None:
#                 # if stop_times:
#                 #     data[4] = " ".join(stops)
#                 yield tuple(data)  # type: ignore
#             # Prepare new data
#             _id = getattr(row, key)
#             data = [filename, getattr(row, key), row.Index, 1, None]
#             # if stop_times:
#             #     stops = [str(row.stop_id)]
#     yield tuple(data)  # type: ignore  # Save the last piece of information


#  def store_trips_per_stop(db: database.Database):
#     """ Store what trips are hit at a particular stop ID """
#     schedules: dict[str, list[str]] = {}
#     for row in iterate_over_csv_full("stop_times.txt"):
#         stop_id = row.stop_id
#         trip_id = row.trip_id
#         if stop_id not in schedules:
#             schedules[stop_id] = [trip_id]
#         else:
#             schedules[stop_id].append(trip_id)
#
#     statements = []
#     for stop_id, trips in schedules.items():
#         statements.append(f"INSERT INTO schedules VALUES ({stop_id!r}, \"{" ".join(trips)}\");")
#     db.executescript(f"BEGIN; {" ".join(statements)} COMMIT;")


def read_and_store_gtfs_data():  # self=None
    """ Read static GTFS data and store it into the database

     This uses its own SQL database instance because it's intended to be run in a different thread """
    # if hasattr(self, "updating"):
    #     self.updating = True
    db = get_database()
    # Start by deleting previous data
    # noinspection SqlWithoutWhere
    # db.execute("DELETE FROM data")
    # noinspection SqlWithoutWhere
    # db.execute("DELETE FROM schedules")

    # Delete the currently-existing records
    # noinspection SqlWithoutWhere
    db.executescript("BEGIN;"
                     "DELETE FROM agencies;"
                     "DELETE FROM calendars;"
                     "DELETE FROM calendar_exceptions;"
                     "DELETE FROM routes;"
                     "DELETE FROM stops;"
                     "DELETE FROM trips;"
                     "DELETE FROM stop_times;"
                     "COMMIT;")

    # def save_to_sql():
    #     nonlocal store
    #     statements = []
    #     for values in store:
    #         search_key = repr(values[4]) if values[4] is not None else "NULL"
    #         statements.append(f"INSERT INTO data VALUES ({values[0]!r}, {values[1]!r}, {values[2]}, {values[3]}, {search_key});")
    #     # noinspection SqlCommit
    #     db.executescript(f"BEGIN; {" ".join(statements)} COMMIT;")
    #     # db.executemany(statement, store)
    #     store = []

    def save_to_sql():
        nonlocal statements
        db.executescript(f"BEGIN; {"; ".join(statements)}; COMMIT;")
        statements = []

    def now():
        return time.datetime.now().strftime("%d %b %Y, %H:%M:%S")

    print(f"{now()} > Static GTFS Loader > Started reading new GTFS data")

    # Structure: (filename, id, start, length, search_key)
    # store: list[tuple[str, str, int, int, str | None]] = []
    statements: list[str] = []

    for row in iterate_over_csv_full("agency.txt"):
        statements.append(Agency(row.agency_id, row.agency_name, row.agency_url, row.agency_timezone).save_to_sql())
        # store.append(("agency.txt", row.agency_id, row.Index, 1, f"{row.agency_id} {row.agency_name}"))
    save_to_sql()
    print(f"{now()} > Static GTFS Loader > Saved agencies")

    for row in iterate_over_csv_full("calendar.txt"):
        statements.append(Calendar(row.service_id, (row.monday, row.tuesday, row.wednesday, row.thursday, row.friday, row.saturday, row.sunday),
                                   str_to_date(row.start_date), str_to_date(row.end_date)).save_to_sql())
        # store.append(("calendar.txt", row.service_id, row.Index, 1, None))  # No special search identifier
    save_to_sql()
    print(f"{now()} > Static GTFS Loader > Saved calendars")

    # for data in iterate_over_csv_multiline("calendar_dates.txt", "service_id"):
    #     store.append(data)
    for row in iterate_over_csv_full("calendar_dates.txt"):
        statements.append(CalendarException(row.service_id, str_to_date(row.date), int(row.exception_type) == 1).save_to_sql())
    save_to_sql()
    print(f"{now()} > Static GTFS Loader > Saved calendar exceptions")

    for row in iterate_over_csv_full("routes.txt"):
        statements.append(Route(row.route_id, row.agency_id, row.route_short_name, row.route_long_name, row.route_desc,
                                row.route_type, row.route_url, row.route_color, row.route_text_color).save_to_sql())
        # All routes have a "short name", so this shouldn't need to be updated unless they add a route without a name
        # store.append(("routes.txt", row.route_id, row.Index, 1, f"{row.route_short_name} {row.route_long_name}"))  # f"{row.route_id} {row.route_short_name} {row.route_long_name}"
    save_to_sql()
    print(f"{now()} > Static GTFS Loader > Saved routes")

    for row in iterate_over_csv_full("stops.txt"):
        statements.append(Stop(row.stop_id, row.stop_code, row.stop_name, row.stop_desc, row.stop_lat, row.stop_lon,
                               row.zone_id, row.stop_url, row.location_type, row.parent_station).save_to_sql())
        # if row.stop_code:
        #     key = f"{row.stop_code} {row.stop_name}"
        # else:
        #     key = f"{row.stop_id} {row.stop_name}"
        # store.append(("stops.txt", row.stop_id, row.Index, 1, key))
    save_to_sql()
    print(f"{now()} > Static GTFS Loader > Saved stops")

    for row in iterate_over_csv_full("trips.txt"):
        statements.append(Trip(row.route_id, row.service_id, row.trip_id, row.trip_headsign, row.trip_short_name,
                               row.direction_id, row.block_id, row.shape_id).save_to_sql())
        # store.append(("trips.txt", row.trip_id, row.Index, 1, row.route_id))
    save_to_sql()
    print(f"{now()} > Static GTFS Loader > Saved trips")

    for row in iterate_over_csv_full("stop_times.txt"):
        statements.append(StopTime(row.trip_id, time_to_int(row.arrival_time), time_to_int(row.departure_time), row.stop_id, row.stop_sequence,
                                   row.stop_headsign, row.pickup_type, row.drop_off_type, row.timepoint).save_to_sql())
        if len(statements) >= 100000:
            save_to_sql()  # Don't overwhelm the memory with millions of these entries
        # store.append(("stop_times.txt", row.stop_id, row.Index, 1, row.trip_id))
    save_to_sql()
    print(f"{now()} > Static GTFS Loader > Saved stop times")

    # for data in iterate_over_csv_multiline("stop_times.txt", "trip_id"):
    #     store.append(data)
    # save_to_sql()
    # print(f"{now()} > Static GTFS Loader > Saved stop times")

    # for row in iterate_over_csv_full("stop_times.txt"):
    #     store.append(("stop_times.txt", row.stop_id, row.Index, 1, row.trip_id))

    # store_trips_per_stop(db)
    # print(f"{now()} > Static GTFS Loader > Saved stop-to-trip correlations")

    # Delete old expiry and set the new one
    # noinspection SqlWithoutWhere
    db.execute("DELETE FROM expiry")
    # Soft limit: 30 days (1 month) from today
    db.execute("INSERT INTO expiry(type, date) VALUES (?, ?)", (0, (time.date.today() + time.timedelta(days=30)).to_datetime(),))
    # Hard limit: 90 days (3 months) from today
    db.execute("INSERT INTO expiry(type, date) VALUES (?, ?)", (1, (time.date.today() + time.timedelta(days=90)).to_datetime(),))
    print(f"{now()} > Static GTFS Loader > Saved expiry data")

    # if hasattr(self, "updating"):
    #     self.updating = False


def init_gtfs_data(*, ignore_expiry: bool = False, db: database.Database = None) -> GTFSData:
    """ Initialise GTFS Data and check for expiry """
    if not ignore_expiry:
        if db is None:
            db = get_database()
        check_gtfs_data_expiry(db)
    return GTFSData({}, {}, {}, {}, {}, {}, {})


def load_calendars(data: GTFSData):
    db = get_database()
    calendars = db.fetch("SELECT * FROM calendars")
    for calendar_dict in calendars:
        calendar = Calendar.from_dict(calendar_dict)
        data.calendars[calendar.service_id] = calendar
        exceptions = CalendarException.from_sql(calendar.service_id, db)
        exceptions_dict = {}
        for exception in exceptions:
            exceptions_dict[exception.date] = exception
        data.calendar_exceptions[calendar.service_id] = exceptions_dict
    # for row in iterate_over_csv_full("calendar.txt"):
    #     calendar = Calendar.parse([row[1:]])
    #     data.calendars[calendar.service_id] = calendar
    # _id = None
    # exception_data = []
    # for row in iterate_over_csv_full("calendar_dates.txt"):
    #     if _id == row.service_id:
    #         exception_data.append(row[1:])
    #     else:
    #         if _id is not None:
    #             exceptions = CalendarException.parse(exception_data)
    #             data.calendar_exceptions[_id] = exceptions
    #         _id = row.service_id
    #         exception_data = []
    # exceptions = CalendarException.parse(exception_data)
    # data.calendar_exceptions[_id] = exceptions


# def load_value_from_id(data: GTFSData | None, filename: str, _id: str, db: database.Database | None) -> Optional[Any]:
#     """ Load a value from the static GTFS data by ID """
#     # Return None if no ID is provided
#     if not _id:
#         return None
#     # Attempt 1: Load from GTFSData
#     if data:
#         values: dict = getattr(data, key_mapping[filename])
#         loaded = values.get(_id)
#         if loaded is not None:
#             return loaded
#         # print(filename, "Value", _id, "not loaded")
#     # Attempt 2: Load from files
#     try:
#         if db is None:
#             db = get_database()
#         sql_data = db.fetchrow("SELECT * FROM data WHERE filename=? AND id=?", (filename, _id))
#         if not sql_data:
#             raise KeyError
#         gtfs_values = load_csv_lines(filename, sql_data["start"], sql_data["length"])
#         cls = class_mapping[filename]
#         new = cls.parse(gtfs_values)
#         if data:
#             # noinspection PyUnboundLocalVariable
#             values[_id] = new
#             # getattr(data, key_mapping[filename])[_id] = new
#             # print(filename, "Value", _id, "saved")
#         return new
#     except (KeyError, ValueError):
#         raise KeyError(f"Could not find any data from {filename} with ID {_id}") from None
#
#
# def load_values_from_key(data: GTFSData | None, filename: str, search_key: str, db: database.Database | None) -> list[Any]:
#     """ Load values from the static GTFS data by search key """
#     if db is None:
#         db = get_database()
#     # Convert into SQL's search pattern
#     _search = "%" + search_key.replace("!", "!!").replace("%", "!%").replace("_", "!_").replace("[", "![") + "%"
#     # Search the database for any data that is similar to the query
#     sql_data = db.fetch("SELECT * FROM data WHERE filename=? AND search_key LIKE ? ESCAPE '!'", (filename, _search))
#     if data:
#         values = getattr(data, key_mapping[filename])
#     cls = class_mapping[filename]
#     output = []
#     for value in sql_data:
#         # Attempt 1: Load from GTFSData
#         if data:
#             # noinspection PyUnboundLocalVariable
#             loaded = values.get(value["id"])
#             if loaded:
#                 output.append(loaded)
#                 continue
#         # Attempt 2: Load from files
#         gtfs_values = load_csv_lines(filename, value["start"], value["length"])
#         new = cls.parse(gtfs_values)
#         if data:
#             # noinspection PyUnboundLocalVariable
#             values[value["id"]] = new
#         output.append(new)
#     return output


# A map from class type to its key in GTFSData
key_mapping = {
    Agency:            "agencies",
    Calendar:          "calendars",
    CalendarException: "calendar_exceptions",
    Route:             "routes",
    Stop:              "stops",
    StopTime:          "stop_times",
    Trip:              "trips"
}


def load_value(data: GTFSData | None, cls: Type[Any], _id: str, db: database.Database | None = None) -> Any | None:
    """ Load an instance of a given class from the given values"""
    # Attempt 1: Return an existing instance from GTFSData
    if data:
        values: dict = getattr(data, key_mapping[cls])  # type: ignore
        loaded = values.get(_id)
        if loaded:
            return loaded
    # Attempt 2: Return an instance from SQL
    try:
        new = cls.from_sql(_id, db)  # type: ignore
        if data and new:
            # noinspection PyUnboundLocalVariable
            values[_id] = new
            return new
        else:
            raise ValueError
    except (KeyError, ValueError):
        raise KeyError(f"Could not find an instance for key {key_mapping[cls]} and ID {_id}") from None  # type: ignore
