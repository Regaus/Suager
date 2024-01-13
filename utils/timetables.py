from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import Any, Type

import pytz
from regaus import time

from utils import database

real_time_filename = "data/gtfs/real_time.json"
# static_filename = "data/gtfs/static.pickle"
db = database.Database("gtfs/static.db")
TIMEZONE = pytz.timezone("Europe/Dublin")


def _weekdays_to_int(weekdays: list[bool]) -> int:
    """ For Calendars - converts the weekdays list to a single integer """
    return sum(map(lambda x: x[1] << x[0], enumerate(weekdays)))


def _int_to_weekdays(weekdays: int) -> list[bool]:
    """ For Calendars - converts the single integer into a weekdays list """
    return list(bool(weekdays & (1 << n)) for n in range(7))


# These classes handle the GTFS-R Real time information
def load_gtfs_r_data(data: dict) -> GTFSRData:
    try:
        return GTFSRData.load(data)
    except Exception as e:
        from utils import general
        general.print_error(general.traceback_maker(e, code_block=False))


@dataclass()
class GTFSRData:
    header: Header
    entities: list[Entity]

    @classmethod
    def load(cls, data: dict):
        # If no data is available, keep self.data null until we do get some data
        if data is None:
            return None
        return cls(Header.load(data["header"]), [Entity.load(e) for e in data["entity"]])


@dataclass()
class Header:
    gtfsr_version: str
    incrementality: str
    timestamp: time.datetime

    @classmethod
    def load(cls, data: dict):
        return cls(data["gtfs_realtime_version"], data["incrementality"], time.datetime.from_timestamp(int(data["timestamp"])))


@dataclass()
class Entity:
    id: str
    # is_deleted: bool
    trip_update: TripUpdate

    # def __post_init__(self):
    #     print(f"Entity {self.id} initialised")

    @classmethod
    def load(cls, data: dict):
        # is_deleted was data["IsDeleted"]
        return cls(data["id"], TripUpdate.load(data["trip_update"]))


@dataclass()
class TripUpdate:
    trip: RealTimeTrip
    stop_times: list[StopTimeUpdate] | None

    @classmethod
    def load(cls, data: dict):
        stop_times = [StopTimeUpdate.load(i) for i in data["stop_time_update"]] if "stop_time_update" in data else None
        return cls(RealTimeTrip.load(data["trip"]), stop_times)


@dataclass()
class RealTimeTrip:
    trip_id: str
    route_id: str
    start_time: time.datetime
    schedule_relationship: str  # SCHEDULED, ADDED, UNSCHEDULED, CANCELED, DUPLICATED, DELETED
    direction_id: int

    @classmethod
    def load(cls, data: dict):
        _time: str = data["start_time"]
        _date: str = data["start_date"]
        h, m, s = _time.split(":")
        y, mo, d = _date[0:4], _date[4:6], _date[6:8]
        # This might have to be in Europe/Dublin timezone, but we'll ignore that for now
        # TODO: See what happens in March when daylight savings kick back in
        start_time = time.datetime(int(y), int(mo), int(d), int(h), int(m), int(s), tz=TIMEZONE)
        return cls(data.get("trip_id", "Unknown"), data["route_id"], start_time, data.get("schedule_relationship", "Unknown"), data["direction_id"])


@dataclass()
class StopTimeUpdate:
    stop_sequence: int
    stop_id: str
    schedule_relationship: str  # SCHEDULED, SKIPPED, NO_DATA, or UNSCHEDULED
    arrival_delay: time.timedelta = None
    departure_delay: time.timedelta = None
    arrival_time: time.datetime = None
    departure_time: time.datetime = None

    @classmethod
    def load(cls, data: dict):
        arrival_delay = arrival_time = departure_delay = departure_time = None
        if "arrival" in data:
            _arrival_delay = data["arrival"].get("delay")
            if _arrival_delay is not None:
                arrival_delay = time.timedelta(seconds=_arrival_delay)
            _arrival_time = data["arrival"].get("time")
            if _arrival_time is not None:
                arrival_time = time.datetime.from_timestamp(int(_arrival_time), tz=TIMEZONE)
        if "departure" in data:
            _departure_delay = data["departure"].get("delay")
            if _departure_delay is not None:
                departure_delay = time.timedelta(seconds=_departure_delay)
            _departure_time = data["departure"].get("time")
            if _departure_time is not None:
                departure_time = time.datetime.from_timestamp(int(_departure_time), tz=TIMEZONE)
        return cls(data["stop_sequence"], data.get("stop_id", "Unknown"), data.get("schedule_relationship", "Unknown"), arrival_delay, departure_delay, arrival_time, departure_time)


# These classes handle the GTFS static information
@dataclass()
class GTFSData:
    # agencies[agency_id] = Agency
    agencies: dict[int, Agency]
    # calendars[service_id] = Calendar
    calendars: dict[int, Calendar]
    # calendar_exceptions[service_id][date] = CalendarException
    calendar_exceptions: dict[int, dict[time.date, CalendarException]]
    # routes[route_id] = Route
    routes: dict[str, Route]
    # stops[stop_id] = Stop
    stops: dict[str, Stop]
    # schedules[trip_id] = [StopTime, StopTime, StopTime, ...]
    schedules: dict[str, list[StopTime]]
    # trips[trip_id] = Trip
    trips: dict[str, Trip]

    def __repr__(self):
        return "This string is too large to be feasible to render."


def load_something(data: GTFSData, cls: Type[Any], key: str, _id: str | int) -> Any:
    """ Load an instance of a provided class from the given values """
    # Attempt 1: Return an existing instance from GTFSData
    values: dict = getattr(data, key)
    loaded = values.get(_id)
    if loaded:
        return loaded
    # Attempt 2: Return an instance from SQL
    try:
        new = cls.from_sql(_id)  # type: ignore
        if new:
            values[_id] = new
            return new
        else:
            raise ValueError
    except (KeyError, ValueError):
        raise KeyError(f"Could not find an instance for key {key} and ID {_id}") from None


@dataclass()
class Agency:
    id: int
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
    def from_sql(cls, agency_id: int) -> Agency:
        """ Load an Agency from the SQL database """
        return cls.from_dict(db.fetchrow("SELECT * FROM agencies WHERE id=?", (agency_id,)))

    def save_to_sql(self):
        """ Save the Agency to the SQL database"""
        return db.execute("INSERT OR IGNORE INTO agencies VALUES (?, ?, ?, ?)", (self.id, self.name, self.url, self.timezone))


@dataclass()
class Calendar:
    service_id: int
    # List of 7 booleans corresponding to whether the service runs on each day of the week
    # This would be more convenient than trying to find the appropriate weekday's attribute
    data: list[bool]
    start_date: time.date
    end_date: time.date

    def __repr__(self):
        # "Calendar 3 - [True, True, True, True, True, False, False]"
        return f"Calendar {self.service_id} - {self.data}"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Calendar:
        """ Construct a new Calendar object from a dictionary """
        return cls(data["service_id"], _int_to_weekdays(data["data"]),
                   time.date.from_datetime(data["start_date"]), time.date.from_datetime(data["end_date"]))

    @classmethod
    def from_sql(cls, service_id: int) -> Calendar:
        """ Load a Calendar object from the SQL database """
        return cls.from_dict(db.fetchrow("SELECT * FROM calendars WHERE service_id=?", (service_id,)))

    def save_to_sql(self):
        """ Save the Calendar to the SQL database """
        return db.execute("INSERT OR IGNORE INTO calendars VALUES (?, ?, ?, ?)",
                          (self.service_id, _weekdays_to_int(self.data), self.start_date.to_datetime(), self.end_date.to_datetime()))


@dataclass()
class CalendarException:
    """ Exceptions to the regular calendar """
    service_id: int  # Should match Calendar.service_id
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
    def from_sql(cls, service_id: int) -> list[CalendarException]:
        """ Load all CalendarExceptions from the SQL database for a given service ID """
        return list(map(cls.from_dict, db.fetch("SELECT * FROM calendar_exceptions WHERE service_id=?", (service_id,))))

    def save_to_sql(self):
        """ Save the CalendarException to the SQL database """
        return db.execute("INSERT OR IGNORE INTO calendar_exceptions VALUES (?, ?, ?)", (self.service_id, self.date.to_datetime(), self.exception))


@dataclass()
class Route:
    id: str
    agency_id: int
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

    @property
    def agency(self):
        return Agency.from_sql(self.agency_id)

    def __repr__(self):
        # "Route 3643_54890 (DART) - Bray - Howth - Operated by Agency 7778017 - Iardród Éireann / Irish Rail"
        return f"Route {self.id} ({self.short_name}) - {self.route_desc} - Operated by {self.agency}"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Route:
        """ Construct a new Route object from a dictionary """
        return cls(data["id"], data["agency_id"], data["short_name"], data["long_name"], data["route_desc"],
                   data["route_type"], data["route_url"], data["route_colour"], data["route_text_colour"])

    @classmethod
    def from_sql(cls, route_id: str) -> Route:
        """ Load a Route from the SQL database """
        return cls.from_dict(db.fetchrow("SELECT * FROM routes WHERE id=?", (route_id,)))

    def save_to_sql(self):
        """ Save the Route to the SQL database """
        return db.execute("INSERT OR IGNORE INTO routes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                          (self.id, self.agency_id, self.short_name, self.long_name, self.route_desc,
                           self.route_type, self.route_url, self.route_colour, self.route_text_colour))


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

    def __repr__(self):
        # "Stop 8220DB000334 (334) - D'Olier Street"
        return f"Stop {self.id} ({self.code}) - {self.name}"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Stop:
        """ Construct a new Stop object from a dictionary """
        return cls(data["id"], data["code"], data["name"], data["description"], data["latitude"], data["longitude"],
                   data["zone_id"], data["stop_url"], data["location_type"], data["parent_station"])

    @classmethod
    def from_sql(cls, stop_id: str) -> Stop:
        """ Load a Stop from the SQL database """
        return cls.from_dict(db.fetchrow("SELECT * FROM stops WHERE id=?", (stop_id,)))

    def save_to_sql(self):
        """ Save the Stop to the SQL database """
        return db.execute("INSERT OR IGNORE INTO stops VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                          (self.id, self.code, self.name, self.description, self.latitude, self.longitude,
                           self.zone_id, self.stop_url, self.location_type, self.parent_station))


@dataclass()
class Trip:
    route_id: str
    # route: Route
    calendar_id: int
    # calendar: Calendar
    trip_id: str
    headsign: str      # What is shown as the destination, can be overridden by StopTime.stop_headsign
    short_name: str    # Supposed to be text identifying the trip to riders - in reality, useless gibberish
    direction_id: int  # 0 -> outbound, 1 -> inbound
    block_id: str      # "A block consists of a single trip or many sequential trips made using the same vehicle"
    shape_id: str      # ID of geospatial shape (not really useful for my case)

    @property
    def route(self) -> Route:
        return Route.from_sql(self.route_id)

    @property
    def calendar(self) -> Calendar:
        return Calendar.from_sql(self.calendar_id)

    def __repr__(self):
        # "Trip 3626_209 to Charlesland, stop 7462 - Route 3626_39040 (84n)"
        return f"Trip {self.trip_id} to {self.headsign} - Route {self.route.id} ({self.route.short_name})"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Trip:
        """ Construct a new Trip object from a dictionary """
        return cls(data["route_id"], data["calendar_id"], data["trip_id"], data["headsign"],
                   data["short_name"], data["direction_id"], data["block_id"], data["shape_id"])

    @classmethod
    def from_sql(cls, trip_id: str) -> Trip:
        """ Load a Trip from the SQL database """
        return cls.from_dict(db.fetchrow("SELECT * FROM trips WHERE trip_id=?", (trip_id,)))

    def save_to_sql(self):
        """ Save the Trip to the SQL database """
        return db.execute("INSERT OR IGNORE INTO TRIPS VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                          (self.route_id, self.calendar_id, self.trip_id, self.headsign, self.short_name, self.direction_id, self.block_id, self.shape_id))


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

    @property
    def trip(self) -> Trip:
        return Trip.from_sql(self.trip_id)

    @property
    def stop(self) -> Stop:
        return Stop.from_sql(self.stop_id)

    def __repr__(self):
        # This basically returns the time of departure modulo 24 hours
        departure_time = time.time.from_microsecond(self.departure_time * 1000000)
        # "StopTime - 02:00:00 to Charlesland, stop 7462 (Stop D'Olier Street - #1, Trip 3626_214)"
        return f"StopTime - {departure_time} to {self.trip.headsign} (Stop {self.stop.name} - #{self.sequence}, Trip {self.trip.trip_id})"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StopTime:
        """ Construct a new StopTime object from a dictionary """
        return cls(data["trip_id"], data["arrival_time"], data["departure_time"], data["stop_id"],
                   data["sequence"], data["stop_headsign"], data["pickup_type"], data["drop_off_type"], data["timepoint"])

    @classmethod
    def from_sql(cls, trip_id: str) -> list[StopTime]:
        """ Load all StopTimes associated with a given Trip ID, sorted by sequence """
        return sorted(list(map(cls.from_dict, db.fetch("SELECT * FROM stop_times WHERE trip_id=?", (trip_id,)))), key=lambda s: s.sequence)

    def save_to_sql(self):
        """ Save the StopTime into the SQL database """
        return db.execute("INSERT OR IGNORE INTO stop_times VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                          (self.trip_id, self.arrival_time, self.departure_time, self.stop_id, self.sequence,
                           self.stop_headsign, self.pickup_type, self.drop_off_type, self.timepoint))


class SpecificStopTime:
    """ A StopTime initialised to a specific date """
    def __init__(self, stop_time: StopTime, date: time.date):
        self.raw_stop_time = stop_time
        self.trip = stop_time.trip
        self.route = stop_time.trip.route
        self.stop = stop_time.stop
        self.sequence = stop_time.sequence
        self.stop_headsign = stop_time.stop_headsign
        self.pickup_type = stop_time.pickup_type
        self.drop_off_type = stop_time.drop_off_type
        self.timepoint = stop_time.timepoint
        self.raw_arrival_time = stop_time.arrival_time
        self.raw_departure_time = stop_time.departure_time

        self.date = date
        _date = time.datetime.combine(date, time.time(tz=TIMEZONE))
        self.arrival_time = _date + time.timedelta(seconds=self.raw_arrival_time)
        self.departure_time = _date + time.timedelta(seconds=self.raw_departure_time)

    def __repr__(self):
        # "SpecificStopTime - 2023-10-14 02:00:00 to Charlesland, stop 7462 (Stop D'Olier Street - #1, Trip 3626_214)"
        return f"SpecificStopTime - {self.departure_time} to {self.trip.headsign} (Stop {self.stop.name} - #{self.sequence}, Trip {self.trip.trip_id})"


class AddedStopTime:
    """ A stop from an ADDED trip """
    def __init__(self, stop_time_update: StopTimeUpdate, trip_id: str | None, route: Route | None, stop: Stop, destination: str = None):  # stops: dict[str, Stop]
        self.stop_time = stop_time_update
        self.trip_id = trip_id
        self.route = route
        self.stop = stop  # Has to be provided manually
        # self.stop = stops.get(stop_time_update.stop_id)
        self.sequence = stop_time_update.stop_sequence
        self.arrival_time = stop_time_update.arrival_time
        self.departure_time = stop_time_update.departure_time
        self.destination = destination

    def __repr__(self):
        # "AddedStopTime - 2023-10-14 02:00:00 (Stop D'Olier Street - #1, Trip ID T130)"
        return f"AddedStopTime - {self.departure_time} (Stop {self.stop.name} - #{self.sequence}, Trip ID {self.trip_id})"


class RealStopTime:
    """ A SpecificStopTime with real-time information applied """
    stop_time: SpecificStopTime | AddedStopTime
    trip: Trip | None
    trip_id: str
    route: Route
    stop: Stop
    sequence: int
    stop_headsign: str | None
    pickup_type: int | None
    drop_off_type: int | None
    timepoint: int | None
    scheduled_arrival_time: time.datetime | None
    scheduled_departure_time: time.datetime | None
    real_time: bool
    real_trip: TripUpdate | None
    schedule_relationship: str | None
    arrival_time: time.datetime | None
    departure_time: time.datetime | None
    destination: str

    def __init__(self, stop_time: SpecificStopTime | AddedStopTime, real_trips: dict[str, TripUpdate] | None):
        if isinstance(stop_time, SpecificStopTime):
            self.stop_time = stop_time
            self.trip = stop_time.trip
            self.trip_id = stop_time.trip.trip_id
            self.route = stop_time.route
            self.stop = stop_time.stop
            self.sequence = stop_time.sequence
            self.stop_headsign = stop_time.stop_headsign
            self.pickup_type = stop_time.pickup_type
            self.drop_off_type = stop_time.drop_off_type
            self.timepoint = stop_time.timepoint
            self.scheduled_arrival_time = stop_time.arrival_time
            self.scheduled_departure_time = stop_time.departure_time
            self.destination = stop_time.trip.headsign

            self.real_time = False
            self.real_trip = None
            self.schedule_relationship = None
            self.arrival_time = None
            self.departure_time = None

            # Check if the real_trips actually contains this Trip ID
            if real_trips is None:
                raise TypeError("real_trips cannot be None for a SpecificStopTime")
            if self.trip.trip_id in real_trips:
                self.real_time = True
                self.real_trip = real_trips[self.trip.trip_id]
                self.schedule_relationship = self.real_trip.trip.schedule_relationship
                arrival_delay = None
                departure_delay = None
                if self.real_trip.stop_times is not None:
                    for stop_time_update in self.real_trip.stop_times:
                        # if stop_time_update.stop_id == self.stop.id:
                        #     arrival_delay = stop_time_update.arrival_delay
                        #     departure_delay = stop_time_update.departure_delay
                        #     break
                        if stop_time_update.stop_sequence <= self.sequence:
                            _arrival_delay = stop_time_update.arrival_delay
                            _departure_delay = stop_time_update.departure_delay
                            if _arrival_delay is not None:
                                arrival_delay = _arrival_delay
                                departure_delay = _departure_delay
                            # The schedule relationship should only matter for this stop
                            if stop_time_update.stop_sequence == self.sequence:
                                self.schedule_relationship = stop_time_update.schedule_relationship
                        else:
                            break  # We reached the desired point
                else:
                    pass
                if arrival_delay is not None:
                    self.arrival_time = self.scheduled_arrival_time + arrival_delay
                else:
                    self.arrival_time = self.scheduled_arrival_time
                if departure_delay is not None:
                    self.departure_time = self.scheduled_departure_time + departure_delay
                else:
                    self.departure_time = self.scheduled_departure_time
        elif isinstance(stop_time, AddedStopTime):
            self.stop_time = stop_time
            self.trip = None
            self.trip_id = stop_time.trip_id
            self.route = stop_time.route
            self.stop = stop_time.stop
            self.sequence = stop_time.sequence
            self.stop_headsign = None
            self.pickup_type = None
            self.drop_off_type = None
            self.timepoint = None
            self.scheduled_arrival_time = None
            self.scheduled_departure_time = None
            self.arrival_time = stop_time.arrival_time
            self.departure_time = stop_time.departure_time
            self.real_time = True
            self.real_trip = None
            self.schedule_relationship = "ADDED"
            self.destination = stop_time.destination
        else:
            raise TypeError(f"Unexpected StopTime type {type(stop_time).__name__} received")

    def __repr__(self):
        # "RealStopTime - [SCHEDULED] 2023-10-14 02:00:00 to Charlesland, stop 7462 (Stop D'Olier Street - #1, Trip 3626_214)"
        if self.trip is not None:
            departure_time = self.departure_time or self.scheduled_departure_time
            return f"RealStopTime - [{self.schedule_relationship}] {departure_time} to {self.trip.headsign} (Stop {self.stop.name} - #{self.sequence}, Trip {self.trip_id})"
        return f"RealStopTime - [{self.schedule_relationship}] {self.departure_time} to <Unknown> (Stop {self.stop.name} - #{self.sequence}, Trip {self.trip_id})"

# @dataclass()
# class TripSchedule:
#     trip: Trip
#     stops: list[StopTime]


def str_to_date(value: str) -> time.date:
    """ Convert YYYYMMDD string to date """
    year = value[:4]
    month = value[4:6]
    day = value[6:]
    return time.date(int(year), int(month), int(day))


def time_to_int(value: str) -> int:
    """ Convert HH:MM:SS string to integer (seconds since midnight) """
    h, m, s = value.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


def check_gtfs_data_expiry():
    # Read the expiry file. If it does not exist, FileNotFoundError will be thrown and caught by self.load_data()
    with open("assets/gtfs/expiry.txt", "r", encoding="utf-8") as file:
        try:
            expiry_ts = int(file.read())
            expiry = time.datetime.from_timestamp(expiry_ts)
            if time.datetime.now() > expiry:  # The data has expired
                raise RuntimeError(f"GTFS Data expired on {expiry:%Y-%m-%d at %H:%M:%S}")
        except ValueError as e:
            raise RuntimeError(f"Encountered an error while trying to read expiry data: {type(e).__name__}: {e}") from None


# def load_gtfs_data_from_pickle(*, write: bool = True, ignore_expiry: bool = False) -> GTFSData:
#     try:
#         if not ignore_expiry:
#             check_gtfs_data_expiry()
#         data = pickle.load(open(static_filename, "rb"))
#     except FileNotFoundError:
#         data = load_gtfs_data(write=write)
#     return data


# def save_gtfs_data_to_pickle(data: GTFSData):
#     return pickle.dump(data, open(static_filename, "wb+"))


def load_gtfs_data(*, ignore_expiry: bool = False, read_from_files: bool = False) -> GTFSData:
    """ Read the GTFS data from the files and save into the database if required, else just return an empty GTFSData object """
    if not ignore_expiry:
        check_gtfs_data_expiry()

    agencies: dict[int, Agency] = {}
    calendars: dict[int, Calendar] = {}
    calendar_exceptions: dict[int, dict[time.date, CalendarException]] = {}
    routes: dict[str, Route] = {}
    stops: dict[str, Stop] = {}
    schedules: dict[str, list[StopTime]] = {}
    trips: dict[str, Trip] = {}

    if read_from_files:
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

        with open("assets/gtfs/agency.txt", "r", encoding="utf-8") as file:
            reader = csv.reader(file, delimiter=",", quotechar="\"")
            headers = ["agency_id", "agency_name", "agency_url", "agency_timezone"]
            # Sample row: ['7778000', 'Citylink', 'https://www.citylink.ie/', 'Europe/London']
            for i, row in enumerate(reader):
                if i > 0:  # Skip the first line, since it contains headers
                    agency_id = int(row[0])
                    # int(ID) -> Name -> URL -> Timezone
                    agency = Agency(agency_id, row[1], row[2], row[3])
                    agencies[agency_id] = agency
                    # TODO: Turn this into an .executemany() so that we don't have to waste as much time
                    agency.save_to_sql()
                else:
                    if headers != row:
                        raise ValueError(f"agency.txt: unexpected headers expected: {row}")

        with open("assets/gtfs/calendar.txt", "r", encoding="utf-8") as file:
            reader = csv.reader(file, delimiter=",", quotechar="\"")
            headers = ["service_id", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "start_date", "end_date"]
            for i, row in enumerate(reader):
                if i > 0:
                    service_id = int(row[0])
                    mon = bool(int(row[1]))
                    tue = bool(int(row[2]))
                    wed = bool(int(row[3]))
                    thu = bool(int(row[4]))
                    fri = bool(int(row[5]))
                    sat = bool(int(row[6]))
                    sun = bool(int(row[7]))
                    start_date = str_to_date(row[8])
                    end_date = str_to_date(row[9])
                    calendar = Calendar(service_id, [mon, tue, wed, thu, fri, sat, sun], start_date, end_date)
                    calendars[service_id] = calendar
                    calendar.save_to_sql()
                else:
                    if headers != row:
                        raise ValueError(f"calendar.txt: unexpected headers expected: {row}")

        with open("assets/gtfs/calendar_dates.txt", "r", encoding="utf-8") as file:
            reader = csv.reader(file, delimiter=",", quotechar="\"")
            headers = ["service_id", "date", "exception_type"]
            for i, row in enumerate(reader):
                if i > 0:
                    service_id = int(row[0])
                    date = str_to_date(row[1])
                    exc_type = int(row[2])
                    # 1 -> Service is added (-> return True when checking if trip is applicable today)
                    # 2 -> Service is removed (-> return False when checking if trip is applicable today)
                    calendar_date = CalendarException(service_id, date, exc_type == 1)
                    if service_id in calendar_exceptions:
                        calendar_exceptions[service_id][date] = calendar_date
                    else:
                        calendar_exceptions[service_id] = {}
                        calendar_exceptions[service_id][date] = calendar_date
                    calendar_date.save_to_sql()
                else:
                    if headers != row:
                        raise ValueError(f"calendar_dates.txt: unexpected headers expected: {row}")

        with open("assets/gtfs/routes.txt", "r", encoding="utf-8") as file:
            reader = csv.reader(file, delimiter=",", quotechar="\"")
            headers = ["route_id", "agency_id", "route_short_name", "route_long_name", "route_desc", "route_type", "route_url", "route_color", "route_text_color"]
            for i, row in enumerate(reader):
                if i > 0:
                    route_id = row[0]
                    agency_id = int(row[1])
                    route = Route(route_id, agency_id, row[2], row[3], row[4], int(row[5]), row[6], row[7], row[8])
                    # route = Route(route_id, agencies[agency_id], row[2], row[3], row[4], int(row[5]), row[6], row[7], row[8])
                    # routes[route_id] = route
                    route.save_to_sql()
                else:
                    if headers != row:
                        raise ValueError(f"routes.txt: unexpected headers expected: {row}")

        with open("assets/gtfs/stops.txt", "r", encoding="utf-8") as file:
            reader = csv.reader(file, delimiter=",", quotechar="\"")
            headers = ["stop_id", "stop_code", "stop_name", "stop_desc", "stop_lat", "stop_lon", "zone_id", "stop_url", "location_type", "parent_station"]
            for i, row in enumerate(reader):
                if i > 0:
                    stop_id = row[0]
                    stop = Stop(stop_id, row[1], row[2], row[3], float(row[4]), float(row[5]), row[6], row[7], row[8], row[9])
                    # stops[stop_id] = stop
                    stop.save_to_sql()
                else:
                    if headers != row:
                        raise ValueError(f"stops.txt: unexpected headers expected: {row}")

        with open("assets/gtfs/trips.txt", "r", encoding="utf-8") as file:
            reader = csv.reader(file, delimiter=",", quotechar="\"")
            headers = ["route_id", "service_id", "trip_id", "trip_headsign", "trip_short_name", "direction_id", "block_id", "shape_id"]
            for i, row in enumerate(reader):
                if i > 0:
                    route_id = row[0]
                    service_id = int(row[1])
                    trip_id = row[2]
                    trip = Trip(route_id, service_id, trip_id, row[3], row[4], int(row[5]), row[6], row[7])
                    # trip = Trip(routes[route_id], calendars[service_id], trip_id, row[3], row[4], int(row[5]), row[6], row[7])
                    # trips[trip_id] = trip
                    trip.save_to_sql()
                else:
                    if headers != row:
                        raise ValueError(f"trips.txt: unexpected headers expected: {row}")

        with open("assets/gtfs/stop_times.txt", "r", encoding="utf-8") as file:
            reader = csv.reader(file, delimiter=",", quotechar="\"")
            headers = ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence", "stop_headsign", "pickup_type", "drop_off_type", "timepoint"]
            for i, row in enumerate(reader):
                if i > 0:
                    trip_id = row[0]
                    arrival = time_to_int(row[1])
                    departure = time_to_int(row[2])
                    # stop = stops[row[3]]
                    stop_seq = int(row[4])
                    stop_time = StopTime(trip_id, arrival, departure, row[3], stop_seq, row[5], int(row[6]), int(row[7]), int(row[8]))
                    # stop_time = StopTime(trips[trip_id], arrival, departure, stop, stop_seq, row[5], int(row[6]), int(row[7]), int(row[8]))
                    # if trip_id in schedules:
                    #     schedules[trip_id].append(stop_time)
                    # else:
                    #     schedules[trip_id] = [stop_time]
                    stop_time.save_to_sql()
                else:
                    if headers != row:
                        raise ValueError(f"stop_times.txt: unexpected headers expected: {row}")

    gtfs_data = GTFSData(agencies, calendars, calendar_exceptions, routes, stops, schedules, trips)
    # if write:
    #     save_gtfs_data_to_pickle(gtfs_data)
    return gtfs_data


# This here is for dealing with (static) schedules, getting closer to user-readable output
class StopSchedule:
    """ Get the stop's schedule """
    def __init__(self, data: GTFSData, stop_id: str):
        self.data = data
        self.stop = self.data.stops[stop_id]
        self.all_stop_times = []

        # Load all schedules (trips) that will pass through this stop
        for schedule in self.data.schedules.values():
            for stop_time in schedule:
                # In case the stop objects happen to be different, ID should still be same
                if self.stop.id == stop_time.stop.id:
                    self.all_stop_times.append(stop_time)

    def relevant_stop_times_one_day(self, date: time.date) -> list[SpecificStopTime]:
        """ Get the stop times for one day """
        output = []
        weekday = date.weekday
        for stop_time in self.all_stop_times:
            calendar = stop_time.trip.calendar
            valid = None  # Whether the trip is valid for the given day

            # Check if the calendar has exceptions for today
            service_id = calendar.service_id
            if service_id in self.data.calendar_exceptions:
                calendar_exception = self.data.calendar_exceptions[service_id].get(date)
                if calendar_exception is not None:
                    valid = calendar_exception.exception

            # If there is no exceptional values today, load the default validity from calendar
            if valid is None:
                valid = calendar.data[weekday]

            # If the service is, indeed, valid today, then add it to the output
            if valid:
                output.append(SpecificStopTime(stop_time, date))

        # Sort the stop times by departure time and return
        output.sort(key=lambda st: st.departure_time)
        return output

    def relevant_stop_times(self, date: time.date) -> list[SpecificStopTime]:
        """ Get the stop times for yesterday, today, and tomorrow """
        yesterday = self.relevant_stop_times_one_day(date - time.timedelta(days=1))
        today = self.relevant_stop_times_one_day(date)
        tomorrow = self.relevant_stop_times_one_day(date + time.timedelta(days=1))
        return yesterday + today + tomorrow

    def __repr__(self):
        return f"Stop Schedule for {self.stop}"


def real_trip_updates(real_time_data: GTFSRData, trip_ids: set[str], stop_id: str) -> tuple[dict[str, TripUpdate], dict[str, TripUpdate]]:
    output = {}
    added = {}
    for entity in real_time_data.entities:
        trip = entity.trip_update
        if trip.trip.trip_id in trip_ids:
            output[trip.trip.trip_id] = trip

        # Check ADDED trips, as they may include our stop
        if trip.trip.schedule_relationship == "ADDED":
            for stop_time_update in trip.stop_times:
                if stop_time_update.stop_id == stop_id:
                    added[entity.id] = trip
    return output, added


# Stuff for real-time schedules
class RealTimeStopSchedule:
    def __init__(self, data: GTFSData, stop_id: str, real_time_data: GTFSRData):
        self.stop_schedule = StopSchedule(data, stop_id)
        self.stop = self.stop_schedule.stop
        self.stop_id = self.stop_schedule.stop.id
        self.stop_times = self.stop_schedule.relevant_stop_times(time.date.today())
        self.trip_ids = {stop_time.trip.trip_id for stop_time in self.stop_times}  # Exclude duplicates

        self.real_trips, self.added_trips = real_trip_updates(real_time_data, self.trip_ids, self.stop_id)

    def real_stop_times(self):
        output = []
        for stop_time in self.stop_times:
            output.append(RealStopTime(stop_time, self.real_trips))

        for trip_id, added_trip in self.added_trips.items():
            for stop_time in added_trip.stop_times:
                if stop_time.stop_id == self.stop_id:
                    last_stop = self.stop_schedule.data.stops.get(added_trip.stop_times[-1].stop_id)
                    if last_stop is not None:
                        destination = last_stop.name
                    else:
                        destination = "Unknown"
                    route = self.stop_schedule.data.routes.get(added_trip.trip.route_id)
                    added_stop_time = AddedStopTime(stop_time, trip_id, route, self.stop_schedule.stop, destination)
                    output.append(RealStopTime(added_stop_time, None))

        output.sort(key=lambda st: st.departure_time or st.scheduled_departure_time)
        return output

    def __repr__(self):
        return f"Real-Time Stop Schedule for {self.stop}"
