from __future__ import annotations

import csv
import pickle
from dataclasses import dataclass

import pytz
from regaus import time


real_time_filename = "data/gtfs/real_time.json"
static_filename = "data/gtfs/static.pickle"
TIMEZONE = pytz.timezone("Europe/Dublin")


# These classes handle the GTFS-R Real time information
def load_gtfs_r_data(data: dict) -> GTFSRData:
    try:
        return GTFSRData.load(data)
    except Exception as e:
        from utils import general
        general.print_error(general.traceback_maker(e))


@dataclass()
class GTFSRData:
    header: Header
    entities: list[...]

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
    schedule: str
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
    schedule: str
    arrival_delay: time.timedelta = None
    departure_delay: time.timedelta = None

    @classmethod
    def load(cls, data: dict):
        try:
            arrival = time.timedelta(seconds=data["arrival"]["delay"]) if "arrival" in data else None
        except KeyError:
            arrival = None
        try:
            departure = time.timedelta(seconds=data["departure"]["delay"]) if "departure" in data else None
        except KeyError:
            departure = None
        return cls(data["stop_sequence"], data.get("stop_id", "Unknown"), data.get("schedule_relationship", "Unknown"), arrival, departure)


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


@dataclass()
class Agency:
    id: int
    name: str
    url: str
    timezone: str

    def __repr__(self):
        # "Agency 7778019 - Bus Átha Cliath / Dublin Bus"
        return f"Agency {self.id} - {self.name}"


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

    def __repr__(self):
        # "Route 3643_54890 (DART) - Bray - Howth - Operated by Agency 7778017 - Iardród Éireann / Irish Rail"
        return f"Route {self.id} ({self.short_name}) - {self.route_desc} - Operated by {self.agency}"


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


@dataclass()
class Trip:
    route: Route
    calendar: Calendar
    trip_id: str
    headsign: str      # What is shown as the destination, can be overridden by StopTime.stop_headsign
    short_name: str    # Supposed to be text identifying the trip to riders - in reality, useless gibberish
    direction_id: int  # 0 -> outbound, 1 -> inbound
    block_id: str      # "A block consists of a single trip or many sequential trips made using the same vehicle"
    shape_id: str      # ID of geospatial shape (not really useful for my case)

    def __repr__(self):
        # "Trip 3626_209 to Charlesland, stop 7462 - Route 3626_39040 (84n)"
        return f"Trip {self.trip_id} to {self.headsign} - Route {self.route.id} ({self.route.short_name})"


@dataclass()
class StopTime:
    trip: Trip
    arrival_time: int   # Return the number of seconds since midnight, to avoid breaking with their silly "28:30:00"
    departure_time: int
    stop: Stop
    sequence: int       # Order of the stop along the route
    stop_headsign: str  # I guess this is in case the "headsign" changes after a certain stop?
    pickup_type: int    # 0 or empty -> Pickup, 1 -> No pickup
    drop_off_type: int  # 0 or empty -> Drop off, 1 -> No drop off
    timepoint: int      # 0 -> Times are approximate, 1 or empty -> Time are exact (this is factually incorrect)

    def __repr__(self):
        # This basically returns the time of departure modulo 24 hours
        departure_time = time.time.from_microsecond(self.departure_time * 1000000)
        # "02:00:00 to Charlesland, stop 7462 (Stop D'Olier Street - #1, Trip 3626_214)"
        return f"{departure_time} to {self.trip.headsign} (Stop {self.stop.name} - #{self.sequence}, Trip {self.trip.trip_id})"


class SpecificStopTime:
    """ A StopTime initialised to a specific date """
    def __init__(self, stop_time: StopTime, date: time.date):
        self.raw_stop_time = stop_time
        self.trip = stop_time.trip
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
        # "2023-10-14 02:00:00 to Charlesland, stop 7462 (Stop D'Olier Street - #1, Trip 3626_214)"
        return f"{self.departure_time} to {self.trip.headsign} (Stop {self.stop.name} - #{self.sequence}, Trip {self.trip.trip_id})"


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


def load_gtfs_data_from_pickle(*, write: bool = True) -> GTFSData:
    try:
        data = pickle.load(open(static_filename, "rb"))
    except FileNotFoundError:
        data = load_gtfs_data(write=write)
    return data


def save_gtfs_data_to_pickle(data: GTFSData):
    return pickle.dump(data, open(static_filename, "wb+"))


def load_gtfs_data(*, write: bool = True) -> GTFSData:
    """ Load available GTFS data """
    agencies: dict[int, Agency] = {}
    calendars: dict[int, Calendar] = {}
    calendar_exceptions: dict[int, dict[time.date, CalendarException]] = {}
    routes: dict[str, Route] = {}
    stops: dict[str, Stop] = {}
    schedules: dict[str, list[StopTime]] = {}
    trips: dict[str, Trip] = {}

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

    gtfs_data = GTFSData(agencies, calendars, calendar_exceptions, routes, stops, schedules, trips)
    if write:
        save_gtfs_data_to_pickle(gtfs_data)
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
