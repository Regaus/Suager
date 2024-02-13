from __future__ import annotations

from collections import namedtuple
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any, Optional

import pandas
from regaus import time

from utils import database
from utils.timetables.shared import CHUNK_SIZE, get_database


__all__ = [
    "str_to_date", "time_to_int",
    "GTFSData", "Agency", "Calendar", "CalendarException", "Route", "Stop", "Trip", "StopTime",
    "class_mapping", "key_mapping",
    "load_csv_lines", "check_gtfs_data_expiry", "iterate_over_csv_partial", "iterate_over_csv_full", "iterate_over_csv_multiline", "load_calendars",
    "read_and_store_gtfs_data", "init_gtfs_data",
    "load_value_from_id", "load_values_from_key"
]


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
    def parse(cls, data: list[tuple[Any, ...]]) -> Agency:
        """ Parse text GTFS data into an Agency object """
        values = data[0]
        # Types have to be forced, else the CSV reader may confuse them
        return cls(str(values[0]), str(values[1]), str(values[2]), str(values[3]))


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
    def parse(cls, data: list[tuple[Any, ...]]) -> Calendar:
        """ Parse text GTFS data into a Calendar object """
        values = data[0]
        service_id = str(values[0])  # int
        mon = bool(int(values[1]))
        tue = bool(int(values[2]))
        wed = bool(int(values[3]))
        thu = bool(int(values[4]))
        fri = bool(int(values[5]))
        sat = bool(int(values[6]))
        sun = bool(int(values[7]))
        start_date = str_to_date(values[8])
        end_date = str_to_date(values[9])
        return cls(service_id, (mon, tue, wed, thu, fri, sat, sun), start_date, end_date)


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
    def parse(cls, data: list[tuple[Any, ...]]) -> dict[time.date, CalendarException]:
        """ Parse text GTFS data into CalendarException objects """
        output = {}
        for row in data:
            service_id = str(row[0])  # int
            date = str_to_date(row[1])
            # 1 -> Service is added (-> True)
            # 2 -> Service is removed (-> False)
            exception = int(row[2]) == 1
            output[date] = cls(service_id, date, exception)
        return output


@dataclass()
class Route:
    id: str
    agency_id: str  # int
    # agency: Agency
    short_name: str  # Usually something like "145", "39A", "DART"
    long_name: str   # Usually something like "Ballywaltrim - Heuston Station"
    route_desc: str  # Description - Doesn't seem to be provided by Irish public transport
    # Route types:
    # 0 -> Tram / Light rail
    # 1 -> Subway
    # 2 -> Rail
    # 3 -> Bus
    route_type: int
    route_url: str   # URL to route info - Doesn't seem to be provided by Irish public transport
    route_colour: str
    route_text_colour: str

    def agency(self, data: GTFSData) -> Agency:
        return load_value_from_id(data, "agency.txt", str(self.agency_id), None)

    # @property
    # def agency(self) -> Agency:
    #     return load_value_from_id(None, "agency.txt", str(self.agency_id))

    def __repr__(self):
        # "Route 3643_54890 (DART) - Bray - Howth - Operated by Agency 7778017"
        return f"Route {self.id} ({self.short_name}) - {self.long_name} - Operated by Agency {self.agency_id}"

    @classmethod
    def parse(cls, data: list[tuple[Any, ...]]) -> Route:
        """ Parse text GTFS data into a Route object """
        values = data[0]
        # Types have to be forced, else the CSV reader may confuse them
        return cls(str(values[0]), str(values[1]), str(values[2]), str(values[3]), str(values[4]), int(values[5]), str(values[6]), str(values[7]), str(values[8]))


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
    def parse(cls, data: list[tuple[Any, ...]]) -> Stop:
        """ Parse text GTFS data into a Stop object """
        values = data[0]
        # Types have to be forced, else the CSV reader may confuse them
        return cls(str(values[0]), str(values[1]), str(values[2]), str(values[3]), float(values[4]), float(values[5]), str(values[6]), str(values[7]), str(values[8]), str(values[9]))


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

    def route(self, data: GTFSData) -> Route:
        return load_value_from_id(data, "routes.txt", self.route_id, None)

    # @property
    # def route(self) -> Route:
    #     return load_value_from_id(None, "routes.txt", self.route_id)

    def calendar(self, data: GTFSData) -> Calendar:
        return load_value_from_id(data, "calendar.txt", str(self.calendar_id), None)

    # @property
    # def calendar(self) -> Calendar:
    #     return load_value_from_id(None, "calendar.txt", str(self.calendar_id))

    def __repr__(self):
        # "Trip 3626_209 to Charlesland, stop 7462 - Route 3626_39040
        return f"Trip {self.trip_id} to {self.headsign} - Route {self.route_id}"

    @classmethod
    def parse(cls, data: list[tuple[Any, ...]]) -> Trip:
        """ Parse text GTFS data into a Trip object """
        values = data[0]
        # Types have to be forced, else the CSV reader may confuse them
        return cls(str(values[0]), str(values[1]), str(values[2]), str(values[3]), str(values[4]), int(values[5]), str(values[6]), str(values[7]))


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

    def trip(self, data: GTFSData) -> Trip:
        return load_value_from_id(data, "trips.txt", self.trip_id, None)

    def route(self, data: GTFSData) -> Route:
        return self.trip(data).route(data)

    # @property
    # def trip(self) -> Trip:
    #     return load_value_from_id(None, "trips.txt", self.trip_id)

    def stop(self, data: GTFSData) -> Stop:
        return load_value_from_id(data, "stops.txt", self.stop_id, None)

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
    def parse(cls, data: list[tuple[Any, ...]]) -> list[StopTime]:
        # Types have to be forced, else the CSV reader may confuse them
        return [cls(str(row[0]), time_to_int(row[1]), time_to_int(row[2]), str(row[3]), int(row[4]), str(row[5]), int(row[6]), int(row[7]), int(row[8])) for row in data]

    # @classmethod
    # def parse(cls, data: tuple[Any, ...]) -> StopTime:
    #     """ Parse text GTFS data into a StopTime object """
    #     return cls(cls(str(row[0]), time_to_int(row[1]), time_to_int(row[2]), str(row[3]), int(row[4]), str(row[5]), int(row[6]), int(row[7]), int(row[8])))


# Mapping of files to corresponding dataclasses
class_mapping = {
    "agency.txt": Agency,
    "calendar.txt": Calendar,
    "calendar_dates.txt": CalendarException,
    "routes.txt": Route,
    "stops.txt": Stop,
    "stop_times.txt": StopTime,
    "trips.txt": Trip
}
key_mapping = {
    "agency.txt": "agencies",
    "calendar.txt": "calendars",
    "calendar_dates.txt": "calendar_exceptions",
    "routes.txt": "routes",
    "stops.txt": "stops",
    "stop_times.txt": "schedules",
    "trips.txt": "trips"
}


def load_csv_lines(filename: str, start_line: int, length: int) -> list[tuple[Any, ...]]:
    """ Load a list of CSV lines from the required file """
    return list(pandas.read_csv("assets/gtfs/" + filename, skiprows=start_line + 1, nrows=length, header=None, na_filter=False).itertuples(index=False, name=None))


def check_gtfs_data_expiry(db: database.Database):
    """ Check for GTFS data expiry """
    expiry = db.fetchrow("SELECT * FROM expiry")
    if expiry is None:
        raise RuntimeError("Expiry data not found.")
    if time.datetime.now() > time.datetime.from_datetime(expiry["expiry"]):
        raise RuntimeError(f"GTFS Data expired on {expiry['expiry']:%Y-%m-%d at %H:%M:%S}")


def iterate_over_csv_partial(filename: str, skip_lines: list[int]) -> Generator[namedtuple, Any, None]:
    """ Iterates over a CSV file while skipping certain lines """
    with open("assets/gtfs/" + filename, "r", encoding="utf-8") as file:
        for chunk in pandas.read_csv(file, chunksize=CHUNK_SIZE, na_filter=False, skiprows=skip_lines):
            for row in chunk.itertuples():
                yield row


def iterate_over_csv_full(filename: str) -> Generator[namedtuple, Any, None]:
    """ Iterates over the full CSV file """
    with open("assets/gtfs/" + filename, "r", encoding="utf-8") as file:
        for chunk in pandas.read_csv(file, chunksize=CHUNK_SIZE, na_filter=False):  # type: pandas.DataFrame
            for row in chunk.itertuples():  # type: namedtuple
                yield row


def iterate_over_csv_multiline(filename: str, key: str) -> Generator[tuple[str, str, int, int, str | None], Any, None]:
    """ Iterates over a CSV file where values can span multiple lines """
    # stop_times = filename == "stop_times.txt"
    _id = None
    data = [filename, "", 0, 0, None]
    # stops = []
    for row in iterate_over_csv_full(filename):
        # If the ID is the same, add to length
        if _id == getattr(row, key):
            data[3] += 1
            # if stop_times:
            #     stops.append(str(row.stop_id))
        # If a new ID is reached, save the existing data and begin counting again
        else:
            # Save previous data
            if _id is not None:
                # if stop_times:
                #     data[4] = " ".join(stops)
                yield tuple(data)  # type: ignore
            # Prepare new data
            _id = getattr(row, key)
            data = [filename, getattr(row, key), row.Index, 1, None]
            # if stop_times:
            #     stops = [str(row.stop_id)]
    yield tuple(data)  # type: ignore  # Save the last piece of information


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
    db.execute("DELETE FROM data")
    # noinspection SqlWithoutWhere
    db.execute("DELETE FROM schedules")

    def save_to_sql():
        nonlocal store
        statements = []
        for values in store:
            search_key = repr(values[4]) if values[4] is not None else "NULL"
            statements.append(f"INSERT INTO data VALUES ({values[0]!r}, {values[1]!r}, {values[2]}, {values[3]}, {search_key});")
        # noinspection SqlCommit
        db.executescript(f"BEGIN; {" ".join(statements)} COMMIT;")
        # db.executemany(statement, store)
        store = []

    def now():
        return time.datetime.now().strftime("%d %b %Y, %H:%M:%S")

    print(f"{now()} > Static GTFS Loader > Started reading new GTFS data")

    # Structure: (filename, id, start, length, search_key)
    store: list[tuple[str, str, int, int, str | None]] = []

    for row in iterate_over_csv_full("agency.txt"):
        store.append(("agency.txt", row.agency_id, row.Index, 1, f"{row.agency_id} {row.agency_name}"))
    save_to_sql()
    print(f"{now()} > Static GTFS Loader > Saved agencies")

    for row in iterate_over_csv_full("calendar.txt"):
        store.append(("calendar.txt", row.service_id, row.Index, 1, None))  # No special search identifier
    save_to_sql()
    print(f"{now()} > Static GTFS Loader > Saved calendars")

    for data in iterate_over_csv_multiline("calendar_dates.txt", "service_id"):
        store.append(data)
    save_to_sql()
    print(f"{now()} > Static GTFS Loader > Saved calendar exceptions")

    for row in iterate_over_csv_full("routes.txt"):
        # All routes have a "short name", so this shouldn't need to be updated unless they add a route without a name
        store.append(("routes.txt", row.route_id, row.Index, 1, f"{row.route_short_name} {row.route_long_name}"))  # f"{row.route_id} {row.route_short_name} {row.route_long_name}"
    save_to_sql()
    print(f"{now()} > Static GTFS Loader > Saved routes")

    for row in iterate_over_csv_full("stops.txt"):
        if row.stop_code:
            key = f"{row.stop_code} {row.stop_name}"
        else:
            key = f"{row.stop_id} {row.stop_name}"
        store.append(("stops.txt", row.stop_id, row.Index, 1, key))
    save_to_sql()
    print(f"{now()} > Static GTFS Loader > Saved stops")

    for row in iterate_over_csv_full("stop_times.txt"):
        store.append(("stop_times.txt", row.stop_id, row.Index, 1, row.trip_id))
    save_to_sql()
    print(f"{now()} > Static GTFS Loader > Saved stop times")

    # for data in iterate_over_csv_multiline("stop_times.txt", "trip_id"):
    #     store.append(data)
    # save_to_sql()
    # print(f"{now()} > Static GTFS Loader > Saved stop times")

    # for row in iterate_over_csv_full("stop_times.txt"):
    #     store.append(("stop_times.txt", row.stop_id, row.Index, 1, row.trip_id))

    for row in iterate_over_csv_full("trips.txt"):
        store.append(("trips.txt", row.trip_id, row.Index, 1, row.route_id))
    save_to_sql()
    print(f"{now()} > Static GTFS Loader > Saved trips")

    # store_trips_per_stop(db)
    # print(f"{now()} > Static GTFS Loader > Saved stop-to-trip correlations")

    # Delete old expiry and set the new one
    # noinspection SqlWithoutWhere
    db.execute("DELETE FROM expiry")
    db.execute("INSERT INTO expiry VALUES (?)", ((time.date.today().replace(day=1) + time.relativedelta(months=1)).to_datetime(),))
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
    for row in iterate_over_csv_full("calendar.txt"):
        calendar = Calendar.parse([row[1:]])
        data.calendars[calendar.service_id] = calendar
    _id = None
    exception_data = []
    for row in iterate_over_csv_full("calendar_dates.txt"):
        if _id == row.service_id:
            exception_data.append(row[1:])
        else:
            if _id is not None:
                exceptions = CalendarException.parse(exception_data)
                data.calendar_exceptions[_id] = exceptions
            _id = row.service_id
            exception_data = []
    exceptions = CalendarException.parse(exception_data)
    data.calendar_exceptions[_id] = exceptions


def load_value_from_id(data: GTFSData | None, filename: str, _id: str, db: database.Database | None) -> Optional[Any]:
    """ Load a value from the static GTFS data by ID """
    # Return None if no ID is provided
    if not _id:
        return None
    # Attempt 1: Load from GTFSData
    if data:
        values: dict = getattr(data, key_mapping[filename])
        loaded = values.get(_id)
        if loaded is not None:
            return loaded
        # print(filename, "Value", _id, "not loaded")
    # Attempt 2: Load from files
    try:
        if db is None:
            db = get_database()
        sql_data = db.fetchrow("SELECT * FROM data WHERE filename=? AND id=?", (filename, _id))
        if not sql_data:
            raise KeyError
        gtfs_values = load_csv_lines(filename, sql_data["start"], sql_data["length"])
        cls = class_mapping[filename]
        new = cls.parse(gtfs_values)
        if data:
            # noinspection PyUnboundLocalVariable
            values[_id] = new
            # getattr(data, key_mapping[filename])[_id] = new
            # print(filename, "Value", _id, "saved")
        return new
    except (KeyError, ValueError):
        raise KeyError(f"Could not find any data from {filename} with ID {_id}") from None


def load_values_from_key(data: GTFSData | None, filename: str, search_key: str, db: database.Database | None) -> list[Any]:
    """ Load values from the static GTFS data by search key """
    if db is None:
        db = get_database()
    # Convert into SQL's search pattern
    _search = "%" + search_key.replace("!", "!!").replace("%", "!%").replace("_", "!_").replace("[", "![") + "%"
    # Search the database for any data that is similar to the query
    sql_data = db.fetch("SELECT * FROM data WHERE filename=? AND search_key LIKE ? ESCAPE '!'", (filename, _search))
    if data:
        values = getattr(data, key_mapping[filename])
    cls = class_mapping[filename]
    output = []
    for value in sql_data:
        # Attempt 1: Load from GTFSData
        if data:
            # noinspection PyUnboundLocalVariable
            loaded = values.get(value["id"])
            if loaded:
                output.append(loaded)
                continue
        # Attempt 2: Load from files
        gtfs_values = load_csv_lines(filename, value["start"], value["length"])
        new = cls.parse(gtfs_values)
        if data:
            # noinspection PyUnboundLocalVariable
            values[value["id"]] = new
        output.append(new)
    return output
