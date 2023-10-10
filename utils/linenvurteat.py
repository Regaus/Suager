from __future__ import annotations

import csv
from dataclasses import dataclass

from regaus import time


# These classes handle the GTFS-R Real time information
@dataclass()
class GTFSData:
    header: Header
    entities: list[...]

    @classmethod
    def load(cls, data: dict):
        # If no data is available, keep self.data null until we do get some data
        if data is None:
            return None
        return cls(Header.load(data["Header"]), [Entity.load(e) for e in data["Entity"]])


@dataclass()
class Header:
    gtfsr_version: str
    incrementality: str
    timestamp: time.datetime

    @classmethod
    def load(cls, data: dict):
        return cls(data["GtfsRealtimeVersion"], data["Incrementality"], time.datetime.from_timestamp(data["Timestamp"]))


@dataclass()
class Entity:
    id: str
    is_deleted: bool
    trip_update: TripUpdate

    # def __post_init__(self):
    #     print(f"Entity {self.id} initialised")

    @classmethod
    def load(cls, data: dict):
        return cls(data["Id"], data["IsDeleted"], TripUpdate.load(data["TripUpdate"]))


@dataclass()
class TripUpdate:
    trip: RealTimeTrip
    stop_times: list[StopTimeUpdate] | None

    @classmethod
    def load(cls, data: dict):
        stop_times = [StopTimeUpdate.load(i) for i in data["StopTimeUpdate"]] if "StopTimeUpdate" in data else None
        return cls(data["Trip"], stop_times)


@dataclass()
class RealTimeTrip:
    trip_id: str
    route_id: str
    start_time: time.datetime
    schedule: str

    @classmethod
    def load(cls, data: dict):
        _time: str = data["StartTime"]
        _date: str = data["StartDate"]
        h, m, s = _time.split(":")
        y, mo, d = _date[0:4], _date[4:6], _date[6:8]
        # This might have to be in Europe/Dublin timezone, but we'll ignore that for now
        # TODO: See what happens in March when daylight savings kick back in
        start_time = time.datetime(int(y), int(mo), int(d), int(h), int(m), int(s))
        return cls(data["TripId"], data["RouteId"], start_time, data["ScheduleRelationship"])


@dataclass()
class StopTimeUpdate:
    stop_sequence: int
    stop_id: str
    schedule: str
    arrival_delay: time.timedelta = None
    departure_delay: time.timedelta = None

    @classmethod
    def load(cls, data: dict):
        try:
            arrival = time.timedelta(seconds=data["Arrival"]["Delay"]) if "Arrival" in data else None
        except KeyError:
            arrival = None
        try:
            departure = time.timedelta(seconds=data["Departure"]["Delay"]) if "Departure" in data else None
        except KeyError:
            departure = None
        return cls(data["StopSequence"], data["StopId"], data["ScheduleRelationship"], arrival, departure)


# These classes handle the GTFS static information
agencies: dict[int, Agency] = {}
calendars: dict[int, Calendar] = {}
calendar_exceptions: dict[int, dict[time.date, CalendarException]] = {}  # calendar_exceptions[service_id][date] = CalendarException
routes: dict[str, Route] = {}
stops: dict[str, Stop] = {}
# stop_times = {}
schedules: dict[str, list[StopTime]] = {}  # schedules[trip_id][i]
trips: dict[str, Trip] = {}


@dataclass()
class Agency:
    id: int
    name: str
    url: str
    timezone: str


@dataclass()
class Calendar:
    service_id: int
    # List of 7 booleans corresponding to whether the service runs on each day of the week
    # This would be more convenient than trying to find the appropriate weekday's attribute
    data: list[bool]
    # monday: bool
    # tuesday: bool
    # wednesday: bool
    # thursday: bool
    # friday: bool
    # saturday: bool
    # sunday: bool
    start_date: time.date
    end_date: time.date


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


@dataclass()
class Route:
    id: str
    agency: Agency
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


@dataclass()
class Trip:
    route: Route
    service_id: Calendar
    trip_id: str
    headsign: str      # What is shown as the destination, can be overridden by StopTime.stop_headsign
    short_name: str    # Supposed to be text identifying the trip to riders - in reality, useless gibberish
    direction_id: int  # 0 -> outbound, 1 -> inbound
    block_id: str      # "A block consists of a single trip or many sequential trips made using the same vehicle"
    shape_id: str      # ID of geospatial shape (not really useful for my case)


@dataclass()
class StopTime:
    trip: Trip
    arrival_time: int   # Return the number of seconds since midnight, to avoid breaking with their silly "28:30:00"
    departure_time: int
    stop: Stop
    sequence: int       # Order of the stop along the route
    stop_headsign: str  # I guess this is in case the "headsign" changes after a certain stop?
    pickup_type: int    # Pick up or not, I guess?
    drop_off_type: int  # Drop off or not, I guess?
    timepoint: int      # No idea


@dataclass()
class TripSchedule:
    trip: Trip
    stops: list[StopTime]


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


def load_gtfs_data():
    """ Load available GTFS data """
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
            else:
                if headers != row:
                    raise ValueError(f"agency.txt: unexpected headers expected: {row}")

    with open("assets/gtfs/calendar.txt", "r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=",", quotechar="\"")
        headers = ["service_id", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "start_date", "end_date"]
        for i, row in enumerate(reader):
            if i > 0:
                service_id = int(row[0])
                mon = bool(row[1])
                tue = bool(row[2])
                wed = bool(row[3])
                thu = bool(row[4])
                fri = bool(row[5])
                sat = bool(row[6])
                sun = bool(row[7])
                start_date = str_to_date(row[8])
                end_date = str_to_date(row[9])
                calendar = Calendar(service_id, [mon, tue, wed, thu, fri, sat, sun], start_date, end_date)
                calendars[service_id] = calendar
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
                calendar_date = CalendarException(service_id, date, exc_type != 2)
                if service_id in calendar_exceptions:
                    calendar_exceptions[service_id][date] = calendar_date
                else:
                    calendar_exceptions[service_id] = {}
                    calendar_exceptions[service_id][date] = calendar_date
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
                route = Route(route_id, agencies[agency_id], row[2], row[3], row[4], int(row[5]), row[6], row[7], row[8])
                routes[route_id] = route
            else:
                if headers != row:
                    raise ValueError(f"routes.txt: unexpected headers expected: {row}")

    with open("assets/gtfs/stops.txt", "r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=",", quotechar="\"")
        headers = ["stop_id", "stop_code", "stop_name", "stop_desc", "stop_lat", "stop_lon", "zone_id", "stop_url", "location_type", "parent_station"]
        for i, row in enumerate(reader):
            if i > 0:
                stop_id = row[0]
                stop = Stop(stop_id, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9])
                stops[stop_id] = stop
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
                trip = Trip(routes[route_id], calendars[service_id], trip_id, row[3], row[4], int(row[5]), row[6], row[7])
                trips[trip_id] = trip
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
                stop = stops[row[3]]
                stop_seq = int(row[4])
                stop_time = StopTime(trips[trip_id], arrival, departure, stop, stop_seq, row[5], int(row[6]), int(row[7]), int(row[8]))
                if trip_id in schedules:
                    schedules[trip_id].append(stop_time)
                else:
                    schedules[trip_id] = [stop_time]
            else:
                if headers != row:
                    raise ValueError(f"stop_times.txt: unexpected headers expected: {row}")
