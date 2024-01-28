from __future__ import annotations

from collections import namedtuple
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any, Optional

import pandas
import pytz
from regaus import time

from utils import database
from utils.errors import GTFSAPIError


real_time_filename = "data/gtfs/real_time.json"
vehicles_filename = "data/gtfs/vehicles.json"
# static_filename = "data/gtfs/static.pickle"
# db = get_database()
# db = database.Database("gtfs/static.db")
TIMEZONE = pytz.timezone("Europe/Dublin")
CHUNK_SIZE = 256


def get_database() -> database.Database:
    return database.Database("gtfs/static.db")


# These classes handle the GTFS-R Real time information
def load_gtfs_r_data(data: dict | None, vehicle_data: dict | None) -> tuple[GTFSRData | None, VehicleData | None]:
    try:
        return GTFSRData.load(data), VehicleData.load(vehicle_data)
    except Exception as e:
        from utils import general
        general.print_error(general.traceback_maker(e, code_block=False))
        raise e from None  # Propagate the error instead of just printing and ignoring it


@dataclass()
class GTFSRData:
    header: Header
    entities: list[Entity]

    @classmethod
    def load(cls, data: dict | None):
        # If no data is available, keep self.data null until we do get some data
        if data is None:
            return None
        # See if the API returned any errors
        if "status_code" in data and "message" in data:
            raise GTFSAPIError(f"{data['status_code']}: {data['message']}", "real-time")
        if "entity" not in data:
            return None
        return cls(Header.load(data["header"]), [Entity.load(e) for e in data["entity"]])


@dataclass()
class VehicleData:
    header: Header
    entities: dict[str, Vehicle]

    @classmethod
    def load(cls, data: dict | None):
        if data is None:
            return None
        # See if the API returned any errors
        if "status_code" in data and "message" in data:
            raise GTFSAPIError(f"{data['status_code']}: {data['message']}", "vehicles")
        if "entity" not in data:
            return None
        vehicles = {}
        for entity in data["entity"]:
            vehicle = Vehicle.load(entity)
            vehicles[vehicle.vehicle_id] = vehicle
        return cls(Header.load(data["header"]), vehicles)


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
    vehicle_id: str | None

    @classmethod
    def load(cls, data: dict):
        stop_times = [StopTimeUpdate.load(i) for i in data["stop_time_update"]] if "stop_time_update" in data else None
        if "vehicle" in data:
            vehicle_id = data["vehicle"]["id"]
        else:
            vehicle_id = None
        return cls(RealTimeTrip.load(data["trip"]), stop_times, vehicle_id)


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
        start_time = time.datetime(int(y), int(mo), int(d), int(h) % 24, int(m), int(s), tz=TIMEZONE)
        if int(h) >= 24:
            start_time += time.timedelta(days=1)
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


@dataclass()
class Vehicle:
    entity_id: str
    trip: RealTimeTrip
    latitude: float
    longitude: float
    vehicle_id: str

    @classmethod
    def load(cls, data: dict):
        entity_id = data["id"]
        vehicle_data = data["vehicle"]
        trip = RealTimeTrip.load(vehicle_data["trip"])
        position = vehicle_data["position"]
        vehicle_id = vehicle_data["vehicle"]["id"]
        return cls(entity_id, trip, position["latitude"], position["longitude"], vehicle_id)


# These classes handle the GTFS static information
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


class SpecificStopTime:
    """ A StopTime initialised to a specific date """
    def __init__(self, stop_time: StopTime, date: time.date):
        self.raw_stop_time = stop_time
        self.trip_id = stop_time.trip_id
        # self.trip = stop_time.trip
        # self.route = stop_time.trip.route
        self.stop_id = stop_time.stop_id
        # self.stop = stop_time.stop
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

    def trip(self, data: GTFSData) -> Trip:
        return load_value_from_id(data, "trips.txt", self.trip_id, None)

    def route(self, data: GTFSData) -> Route:
        return self.trip(data).route(data)

    def __repr__(self):
        # "SpecificStopTime - 2023-10-14 02:00:00 - Stop #1 for trip 3626_214"
        return f"SpecificStopTime - {self.departure_time} - Stop #{self.sequence} for Trip {self.trip_id}"
        # "SpecificStopTime - 2023-10-14 02:00:00 to Charlesland, stop 7462 (Stop D'Olier Street - #1, Trip 3626_214)"
        # return f"SpecificStopTime - {self.departure_time} to {self.trip.headsign} (Stop {self.stop.name} - #{self.sequence}, Trip {self.trip.trip_id})"


class AddedStopTime:
    """ A stop from an ADDED trip """
    def __init__(self, stop_time_update: StopTimeUpdate, trip_id: str | None, route: Route | None, stop: Stop, destination: str = None, vehicle: Vehicle = None):  # stops: dict[str, Stop]
        self.stop_time = stop_time_update
        self.trip_id = trip_id
        self.route = route
        self.stop_id = stop.id
        self.stop = stop  # Has to be provided manually
        # self.stop = stops.get(stop_time_update.stop_id)
        self.sequence = stop_time_update.stop_sequence
        self.arrival_time = stop_time_update.arrival_time
        self.departure_time = stop_time_update.departure_time or self.arrival_time  # If the departure time is unknown, show the arrival time
        self.destination = destination
        if vehicle:
            self.vehicle = vehicle
            self.vehicle_id = vehicle.vehicle_id
        else:
            self.vehicle = self.vehicle_id = None

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
    destination: str | None
    vehicle: Vehicle | None
    vehicle_id: str | None

    def __init__(self, stop_time: SpecificStopTime | AddedStopTime, real_trips: dict[str, TripUpdate] | None, vehicles: VehicleData | None):
        if isinstance(stop_time, SpecificStopTime):
            self.stop_time = stop_time
            # self.trip = stop_time.trip
            self.trip_id = stop_time.trip_id
            self._route = None
            # self.route = stop_time.route
            # self.stop = stop_time.stop
            self.stop_id = stop_time.stop_id
            self.sequence = stop_time.sequence
            self.stop_headsign = stop_time.stop_headsign
            self.pickup_type = stop_time.pickup_type
            self.drop_off_type = stop_time.drop_off_type
            self.timepoint = stop_time.timepoint
            self.scheduled_arrival_time = stop_time.arrival_time
            self.scheduled_departure_time = stop_time.departure_time
            # self.destination = stop_time.trip.headsign
            self._destination = None

            self.real_time = False
            self.real_trip = None
            self.schedule_relationship = None
            self.arrival_time = None
            self.departure_time = None

            # Check if the real_trips actually contains this Trip ID
            if real_trips is None:
                raise TypeError("real_trips cannot be None for a SpecificStopTime")
            if self.trip_id in real_trips:
                self.real_time = True
                self.real_trip = real_trips[self.trip_id]
                self.schedule_relationship = self.real_trip.trip.schedule_relationship
                # Calculate arrival and departure times
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
                # Find the vehicle
                vehicle_id = self.real_trip.vehicle_id
                if vehicle_id is not None and vehicles is not None:
                    self.vehicle_id = vehicle_id
                    self.vehicle = vehicles.entities.get(vehicle_id)  # In case there somehow doesn't exist a value
                else:
                    self.vehicle = self.vehicle_id = None
            else:
                self.vehicle = self.vehicle_id = None
        elif isinstance(stop_time, AddedStopTime):
            self.stop_time = stop_time
            # self.trip = None
            self.trip_id = stop_time.trip_id
            self._route = stop_time.route
            self.stop_id = stop_time.stop_id
            # self.stop = stop_time.stop
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
            self._destination = stop_time.destination
            self.vehicle = stop_time.vehicle
            self.vehicle_id = stop_time.vehicle_id
        else:
            raise TypeError(f"Unexpected StopTime type {type(stop_time).__name__} received")

    def trip(self, data: GTFSData) -> Optional[Trip]:
        try:
            return load_value_from_id(data, "trips.txt", self.trip_id, None)
        except KeyError:
            return None

    def route(self, data: GTFSData) -> Optional[Route]:
        if self._route:
            return self._route
        try:
            trip = self.trip(data)
            if trip is None:
                return None
            route = trip.route(data)
            self._route = route
            return route
        except KeyError:
            return None

    def stop(self, data: GTFSData) -> Optional[Stop]:
        try:
            return load_value_from_id(data, "stops.txt", self.stop_id, None)
        except KeyError:
            return None

    def destination(self, data: GTFSData) -> str:
        if self._destination:
            return self._destination
        destination = self.trip(data).headsign
        self._destination = destination
        return destination

    @property
    def available_departure_time(self):
        return self.departure_time or self.scheduled_departure_time

    def __repr__(self):
        # "RealStopTime - [SCHEDULED] 2023-10-14 02:00:00 - Stop #1 for Trip 3626_214"
        return f"RealStopTime - [{self.schedule_relationship}] {self.available_departure_time} - Stop #{self.sequence} for Trip {self.trip_id}"
        # "RealStopTime - [SCHEDULED] 2023-10-14 02:00:00 to Charlesland, stop 7462 (Stop D'Olier Street - #1, Trip 3626_214)"
        # if self.trip is not None:
        #     departure_time = self.departure_time or self.scheduled_departure_time
        #     return f"RealStopTime - [{self.schedule_relationship}] {departure_time} to {self.trip.headsign} (Stop {self.stop.name} - #{self.sequence}, Trip {self.trip_id})"
        # return f"RealStopTime - [{self.schedule_relationship}] {self.departure_time} to <Unknown> (Stop {self.stop.name} - #{self.sequence}, Trip {self.trip_id})"

# @dataclass()
# class TripSchedule:
#     trip: Trip
#     stops: list[StopTime]


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


def iterate_over_csv_partial(filename: str, skip_lines: set[int]) -> Generator[namedtuple, Any, None]:
    """ Iterates over a CSV file while skipping certain lines """
    with open("assets/gtfs/" + filename, "r", encoding="utf-8") as file:
        for chunk in pandas.read_csv(file, chunksize=CHUNK_SIZE, na_filter=False, skiprows=list(skip_lines)):
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


def read_and_store_gtfs_data(self=None):
    """ Read static GTFS data and store it into the database

     This uses its own SQL database instance because it's intended to be run in a different thread """
    if hasattr(self, "updating"):
        self.updating = True
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

    if hasattr(self, "updating"):
        self.updating = False


def init_gtfs_data(*, ignore_expiry: bool = False, db: database.Database = None) -> GTFSData:
    """ Initialise GTFS Data and check for expiry """
    if not ignore_expiry:
        if db is None:
            db = get_database()
        check_gtfs_data_expiry(db)
    return GTFSData({}, {}, {}, {}, {}, {}, {})


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


# This here is for dealing with (static) schedules, getting closer to user-readable output
class StopSchedule:
    """ Get the stop's schedule """
    def __init__(self, data: GTFSData, stop_id: str):
        self.db = get_database()
        self.data = data
        self.stop = load_value_from_id(data, "stops.txt", stop_id, self.db)
        self.stop_id = self.stop.id
        # self.stop = self.data.stops[stop_id]
        # self.all_stop_times = []
        self.all_trips = []
        # self.stop_times[trip_id] = StopTime(stop_id=self.stop_id)
        self.stop_times: dict[str, StopTime] = {}

        # Load all schedules (trips) that will pass through this stop
        # sql_data = db.fetchrow("SELECT * FROM schedules WHERE stop_id=?", (self.stop_id,))
        # trip_ids_full = set(sql_data["trip_ids"].split(" "))
        sql_data = self.db.fetch("SELECT * FROM data WHERE filename=? AND id=?", ("stop_times.txt", stop_id))
        trip_ids_full = set(entry["search_key"] for entry in sql_data)
        trip_ids_inter = trip_ids_full.intersection(self.data.trips.keys())
        for key in trip_ids_inter:
            self.all_trips.append(self.data.trips[key])

        # Add trips that are not yet loaded into memory
        trip_ids = trip_ids_full.difference(trip_ids_inter)
        if trip_ids:
            for row in iterate_over_csv_full("trips.txt"):
                if row.trip_id in trip_ids:
                    trip = Trip.parse([row[1:]])
                    self.all_trips.append(trip)
                    self.data.trips[row.trip_id] = trip

        # Load stop times from trips that were already loaded into memory
        schedule_ids_inter = trip_ids_full.intersection(self.data.stop_times.keys())
        schedule_ids_copy = schedule_ids_inter.copy()
        for key in schedule_ids_inter:  # key1 = trip_id, key2 = stop_id
            if stop_id in self.data.stop_times[key]:
                self.stop_times[key] = self.data.stop_times[key][stop_id]
            else:
                schedule_ids_copy.remove(key)  # False positive: Trip ID exists in memory but this stop's StopTime is not loaded
        # schedule_ids_inter = trip_ids_full.intersection(self.data.schedules.keys())
        # for key in schedule_ids_inter:
        #     schedule = self.data.schedules[key]
        #     if schedule[0].trip_id in trip_ids_full:
        #         for stop_time in schedule:
        #             if self.stop_id == stop_time.stop_id:
        #                 self.stop_times[stop_time.trip_id] = stop_time

        # Add stop times from trips that are not yet loaded in memory
        schedule_ids = trip_ids_full.difference(schedule_ids_copy)
        if schedule_ids:
            lines = set(entry["start"] + 1 for entry in sql_data if entry["search_key"] in schedule_ids)  # search_key is trip_id
            skipped = set(range(1, max(lines))).difference(lines)
            # rows = set()
            for row in iterate_over_csv_partial("stop_times.txt", skipped):
                if row.stop_id == stop_id and row.trip_id in schedule_ids:
                    stop_time = StopTime.parse([row[1:]])[0]
                    self.stop_times[row.trip_id] = stop_time
                    if row.trip_id in self.data.stop_times:
                        self.data.stop_times[row.trip_id][row.stop_id] = stop_time
                    else:
                        self.data.stop_times[row.trip_id] = {row.stop_id: stop_time}
                    schedule_ids.remove(row.trip_id)
                # Once all the trips we need have been loaded, exit the loop
                if not schedule_ids:
                    break
                # else:
                #     if row.trip_id not in schedule_ids:
                #         print(row.Index, "Wrong trip")
                #     else:
                #         print(row.Index, "Wrong stop")
                # print(row.Index, row.stop_id)
                # rows.add(row.Index)
            # if schedule_ids:
            #     print("Missed IDs: ", schedule_ids)
            # Maybe we can just skip the "ask the database" part, since we have to loop through the entire file anyways?
            # stop_time_data = db.fetch(f"SELECT * FROM data WHERE filename=? AND id IN ({"?, " * (len(trip_ids) - 1)}?)", ("stop_times.txt", *schedule_ids))
            # stop_time_data.sort(key=lambda x: x["start"])
            # lines: set[int] = set()  # type: ignore
            # for schedule in stop_time_data:
            #     lines.update(range(schedule["start"], schedule["start"] + schedule["length"]))

            # Maybe try to load the amount of lines and then just make a huge set/list with all the lines we need to skip?
            # Or just skip all the lines until the last line in the set, at which point just break out of the loop?
            # schedules = {}
            # for row in iterate_over_csv_full("stop_times.txt"):
            #     # if row.Index in lines:
            #     if row.trip_id in schedule_ids:
            #         stop_time = StopTime.parse([row[1:]])[0]
            #         trip_id = stop_time.trip_id
            #         if trip_id in schedules:
            #             schedules[trip_id].append(stop_time)
            #         else:
            #             schedules[trip_id] = [stop_time]
            #         if stop_time.stop_id == self.stop_id:
            #             self.stop_times[trip_id] = stop_time

            # self.data.schedules.update(schedules)

        # self.all_stop_times = load_values_from_key(self.data, "stop_times.txt", self.stop.id)
        # for schedule in self.data.schedules.values():
        #     for stop_time in schedule:
        #         # In case the stop objects happen to be different, ID should still be same
        #         if self.stop.id == stop_time.stop_id:
        #             self.all_stop_times.append(stop_time)

    def relevant_stop_times_one_day(self, date: time.date) -> list[SpecificStopTime]:
        """ Get the stop times for one day """
        db = get_database()  # This may get called in a separate thread than the one where the schedule was created
        output = []
        weekday = date.weekday
        # for stop_time in self.all_stop_times:
        for trip in self.all_trips:
            calendar = trip.calendar(self.data)
            # calendar = stop_time.trip(self.data).calendar(self.data)
            valid = None  # Whether the trip is valid for the given day

            # Check if the calendar has exceptions for today
            try:
                calendar_exceptions = load_value_from_id(self.data, "calendar_dates.txt", calendar.service_id, db)
                exception = calendar_exceptions.get(date)
                if exception is not None:
                    valid = exception.exception
            except KeyError:
                self.data.calendar_exceptions[calendar.service_id] = {}

            # Check that the current date is within the dates range
            if valid is None:
                if date > calendar.end_date or date < calendar.start_date:
                    valid = False

            # if service_id in self.data.calendar_exceptions:
            #     calendar_exception = self.data.calendar_exceptions[service_id].get(date)
            #     if calendar_exception is not None:
            #         valid = calendar_exception.exception

            # If there is no exceptional values today, load the default validity from calendar
            if valid is None:
                valid = calendar.data[weekday]

            # If the service is, indeed, valid today, then add it to the output
            if valid:
                output.append(SpecificStopTime(self.stop_times[trip.trip_id], date))

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
    if real_time_data is None:
        return {}, {}
    output = {}
    added = {}
    for entity in real_time_data.entities:
        trip = entity.trip_update
        if trip.trip.trip_id in trip_ids:
            output[trip.trip.trip_id] = trip

        # Check ADDED trips, as they may include our stop
        if trip.trip.schedule_relationship == "ADDED" and trip.stop_times is not None:
            for stop_time_update in trip.stop_times:
                if stop_time_update.stop_id == stop_id:
                    added[entity.id] = trip
    return output, added


# Stuff for real-time schedules
class RealTimeStopSchedule:
    def __init__(self, data: GTFSData | None, stop_id: str | None, real_time_data: GTFSRData, vehicle_data: VehicleData,
                 existing_schedule: StopSchedule | None = None, stop_times: list[SpecificStopTime] | None = None):
        self.db = get_database()
        if existing_schedule is not None:
            self.stop_schedule = existing_schedule
            self.data = existing_schedule.data
        else:
            if data is None:
                raise ValueError("data cannot be None if existing_schedule is not provided")
            if stop_id is None:
                raise ValueError("stop_id cannot be None if existing_schedule is not provided")
            self.data = data
            self.stop_schedule = StopSchedule(data, stop_id)
        self.stop = self.stop_schedule.stop
        self.stop_id = self.stop_schedule.stop_id
        if stop_times is not None:
            self.stop_times = stop_times
        else:
            self.stop_times = self.stop_schedule.relevant_stop_times(time.date.today())
        self.trip_ids = {stop_time.trip_id for stop_time in self.stop_times}  # Exclude duplicates

        self.real_trips, self.added_trips = real_trip_updates(real_time_data, self.trip_ids, self.stop_id)

        self.vehicle_data = vehicle_data

    @classmethod
    def from_existing_schedule(cls, existing_schedule: StopSchedule, real_time_data: GTFSRData, vehicle_data: VehicleData, stop_times: list[SpecificStopTime] | None = None):
        """ Load a RealTimeStopSchedule from an existing StopSchedule, so that the operation need not be repeated """
        return cls(None, None, real_time_data, vehicle_data, existing_schedule, stop_times)

    def real_stop_times(self):
        output = []
        for stop_time in self.stop_times:
            output.append(RealStopTime(stop_time, self.real_trips, self.vehicle_data))

        for trip_id, added_trip in self.added_trips.items():
            for stop_time in added_trip.stop_times:
                if stop_time.stop_id == self.stop_id:
                    try:
                        last_stop = load_value_from_id(self.data, "stops.txt", added_trip.stop_times[-1].stop_id, self.db)
                        destination = last_stop.name
                    except KeyError:
                        # last_stop = None
                        destination = "Unknown"
                    # last_stop = self.stop_schedule.data.stops.get(added_trip.stop_times[-1].stop_id)
                    # if last_stop is not None:
                    #     destination = last_stop.name
                    # else:
                    #     destination = "Unknown"
                    try:
                        route = load_value_from_id(self.data, "routes.txt", added_trip.trip.route_id, self.db)
                    except KeyError:
                        route = None
                    # route = self.stop_schedule.data.routes.get(added_trip.trip.route_id)
                    if added_trip.vehicle_id:
                        vehicle_id = added_trip.vehicle_id
                        vehicle = self.vehicle_data.entities[vehicle_id]
                    else:
                        vehicle = None
                    added_stop_time = AddedStopTime(stop_time, trip_id, route, self.stop_schedule.stop, destination, vehicle)
                    output.append(RealStopTime(added_stop_time, None, None))

        output.sort(key=lambda st: st.available_departure_time)
        return output

    def __repr__(self):
        return f"Real-Time Stop Schedule for {self.stop}"
