import json
from typing import Optional

import asyncio
import nest_asyncio
from regaus import time

from utils import database
from utils.timetables.shared import TIMEZONE, get_database, get_data_database
from utils.timetables.realtime import *
from utils.timetables.trains import *
from utils.timetables.static import *

__all__ = (
    "trip_validity", "SpecificStopTime", "AddedStopTime", "RealStopTime", "ScheduledTrip",
    "StopSchedule", "RealTimeStopSchedule", "real_trip_updates", "RouteSchedule"
)


def trip_validity(static_data: GTFSData, trip: Trip, date: time.date, db):
    """ Returns whether a trip is valid on a given date """
    weekday = date.weekday
    calendars = static_data.calendars
    calendar_exceptions = static_data.calendar_exceptions
    if not calendars:  # calendars empty = no calendars have been loaded yet
        load_calendars(static_data)

    if trip.calendar_id in calendars:
        calendar = calendars[trip.calendar_id]
    else:  # Weird but just in case
        calendar = trip.calendar(static_data)
    # calendar = stop_time.trip(self.data).calendar(self.data)
    valid = None  # Whether the trip is valid for the given day

    # Check if the calendar has exceptions for today
    if trip.calendar_id in calendar_exceptions:
        exception = calendar_exceptions[trip.calendar_id].get(date)
        if exception:
            valid = exception.exception
    else:  # Weird but just in case
        try:
            exceptions: dict[time.date, CalendarException] = load_value(static_data, CalendarException, calendar.service_id, db)
            exception = exceptions.get(date)
            if exception is not None:
                valid = exception.exception
        except KeyError:
            static_data.calendar_exceptions[calendar.service_id] = {}

    # Check that the current date is within the dates range
    if valid is None:
        if date > calendar.end_date or date < calendar.start_date:
            valid = False

    # If there is no exceptional value today, load the default validity from calendar
    if valid is None:
        valid = calendar.data[weekday]

    return valid


def _create_trip_update_from_train(station_departure: StationDeparture) -> TripUpdate:
    """ Create a real-time TripUpdate from an added station departure """
    # The TripDiagramViewer will still report it as "Unknown route", but whatever
    try:
        static_trip: Trip = Trip.from_short_name(station_departure.trip_code, None)
        route_id = static_trip.route_id
    except KeyError:
        route_id = "Unknown"
    real_time_trip = RealTimeTrip(station_departure.trip_code, route_id, station_departure.date, station_departure.origin_time, "ADDED", -1)
    # train_movements: list[TrainMovement] = await fetch_train_movements(station_departure.trip_code, station_departure.date, debug, write, _bypass_invalid_check=True)
    stop_time_updates: list[StopTimeUpdate] = [StopTimeUpdate(-1, TRAIN_STATION_CODE_TO_ID[station_departure.station_code], "ADDED", None, None,
                                                              station_departure.expected_arrival, station_departure.expected_departure)]
    # for movement in train_movements:
    #     if movement.location_type == "T":
    #         continue
    #     stop_id = TRAIN_STATION_CODE_TO_ID[movement.location_code]
    #     schedule_relationship = "SKIPPED" if movement.location_type == "C" else "ADDED"
    #     arrival_time = movement.actual_arrival or movement.expected_arrival
    #     departure_time = movement.actual_departure or movement.expected_departure
    #     stop_time_updates.append(StopTimeUpdate(len(stop_time_updates) + 1, stop_id, schedule_relationship, None, None, arrival_time, departure_time))
    return TripUpdate(station_departure.trip_code, real_time_trip, stop_time_updates, station_departure.trip_code, station_departure.query_time)


class SpecificStopTime:
    """ A StopTime initialised to a specific date """

    def __init__(self, stop_time: StopTime, date: time.date, *, day_modifier: int = 0):
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
        self._destination: str | None = None
        self.day_modifier = day_modifier  # To track trips starting on a different day
        # These will never be used here, but are there for parity with the RealStopTime
        self.actual_destination = None
        self.actual_start = None
        self.is_added = False
        self.real_time = False

        self.date = date
        _date = time.datetime.combine(date, time.time(tz=TIMEZONE))
        self.arrival_time = _date + time.timedelta(seconds=self.raw_arrival_time)
        self.departure_time = _date + time.timedelta(seconds=self.raw_departure_time)

    def trip(self, data: GTFSData = None) -> Trip:
        return load_value(data, Trip, self.trip_id, None)

    def route(self, data: GTFSData = None) -> Route:
        return self.trip(data).route(data)

    def stop(self, data: GTFSData = None) -> Stop:
        return load_value(data, Stop, self.stop_id, None)

    def destination(self, data: GTFSData = None) -> str:
        """ Get the destination of the StopTime """
        if self._destination:
            return self._destination
        destination = self.trip(data).headsign
        self._destination = destination
        return destination

    @property
    def available_departure_time(self):
        return self.departure_time

    def __repr__(self):
        # "SpecificStopTime - 2023-10-14 02:00:00 - Stop #1 for trip 3626_214"
        return f"SpecificStopTime - {self.departure_time} - Stop #{self.sequence} for Trip {self.trip_id}"

        # "SpecificStopTime - 2023-10-14 02:00:00 to Charlesland, stop 7462 (Stop D'Olier Street - #1, Trip 3626_214)"
        # trip = self.trip()
        # stop = self.stop()
        # return f"SpecificStopTime - {self.departure_time} to {trip.headsign} (Stop {stop.name} - #{self.sequence}, Trip {trip.trip_id})"


class AddedStopTime:
    """ A stop from an ADDED trip """

    def __init__(self, stop_time_update: StopTimeUpdate, trip_update: TripUpdate, route: Route | None, stop: Stop, destination: str = None, vehicle: Vehicle = None):  # stops: dict[str, Stop]
        self.stop_time = stop_time_update
        self.trip_update = trip_update
        self.trip_id = trip_update.entity_id
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
    is_added: bool
    stop_time: SpecificStopTime | AddedStopTime | StationDeparture
    trip: Trip | None
    trip_id: str
    route: Route
    stop: Stop
    sequence: int | None
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
    _destination: str | None
    vehicle: Vehicle | None
    vehicle_id: str | None
    day_modifier: int

    def __init__(self, stop_time: SpecificStopTime | AddedStopTime | StationDeparture, real_trips: dict[str, TripUpdate] | None, vehicles: VehicleData | None,
                 station_data: dict[str, StationDeparture] | None, day_modifier: int = 0, station_trip_update: TripUpdate = None):
        self.actual_destination = None
        self.actual_start = None
        self.station_departure: StationDeparture | None = None
        if isinstance(stop_time, SpecificStopTime):
            self.is_added = False
            self.stop_time = stop_time
            self._trip = None
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
            self.day_modifier = stop_time.day_modifier

            self.real_time = False
            self.real_trip = None
            self.schedule_relationship = None
            self.arrival_time = None
            self.departure_time = None
            self.trip_code = self.trip().short_name
            self.is_train_departure: bool = False  # default value

            # Check if the real_trips actually contains this Trip ID
            if real_trips is None:
                raise TypeError("real_trips cannot be None for a SpecificStopTime")
            if station_data and self.trip_code in station_data:
                if self.trip_code in invalid_trips:
                    self.remove = True
                else:
                    self.station_departure = station_data.pop(self.trip_code)
                    # If the trip is invalid (the scheduled arrival/departure time doesn't match our expected value), mark the trip as invalid and add it to the schedule
                    if self.scheduled_arrival_time != self.station_departure.scheduled_arrival or self.scheduled_departure_time != self.station_departure.scheduled_departure:
                        invalid_trips.add(self.trip_code)
                        station_data[self.trip_code] = self.station_departure
                        # self.remove = True
                    elif self.station_departure.status != "No Information":
                        self.real_time = True
                        if self.trip_id in real_trips:
                            self.real_trip = real_trips[self.trip_id]
                        self.schedule_relationship = "SCHEDULED"
                        self.arrival_time = self.station_departure.expected_arrival
                        self.departure_time = self.station_departure.expected_departure
                    else:
                        self.real_time = False
                        self.real_trip = None
                    self.vehicle = self.vehicle_id = None
                self.is_train_departure = True
            elif self.trip_id in real_trips:
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
                            if _departure_delay is not None:
                                departure_delay = _departure_delay
                            # The schedule relationship should only matter for this stop
                            if stop_time_update.stop_sequence == self.sequence:
                                self.schedule_relationship = stop_time_update.schedule_relationship
                        else:
                            break  # We reached the desired point

                    # all_stops = []
                    #
                    # def load_stops():
                    #     return sorted(StopTime.from_sql(self.trip_id), key=lambda st: st.sequence)
                    total_stops = self.trip().total_stops

                    # Handle the case where the bus terminates early
                    if self.real_trip.stop_times[-1].schedule_relationship == "SKIPPED":
                        skipped_sequence = self.real_trip.stop_times[-1].stop_sequence
                        # all_stops = load_stops()
                        # last_stop = all_stops[-1].sequence
                        # If the last skipped stop is not the last stop on the route, do nothing.
                        if skipped_sequence == total_stops:
                            i = len(self.real_trip.stop_times) - 1
                            stop_time_update = self.real_trip.stop_times[i]
                            try:
                                # Find the last stop sequence not skipped
                                while stop_time_update.schedule_relationship == "SKIPPED" and i > 0:
                                    i -= 1
                                    stop_time_update = self.real_trip.stop_times[i]

                                if stop_time_update.schedule_relationship == "SKIPPED":
                                    sequence = stop_time_update.stop_sequence - 1
                                else:
                                    sequence = self.real_trip.stop_times[i + 1].stop_sequence - 1
                                # sequence - 1 because the sequences start from 1.
                                if sequence < 1:
                                    sequence = 1
                                if sequence > total_stops:
                                    sequence = total_stops
                                stop_id = StopTime.from_sql_sequence(self.trip_id, sequence).stop_id
                                # stop_id = all_stops[sequence - 1].stop_id
                                # stop_id = self.real_trip.stop_times[i + 1].stop_id
                            except IndexError:
                                # It has happened before, but I don't fully understand why it does.
                                pass
                            else:
                                if 1 < sequence < total_stops:  # If it terminates at the first stop, something is probably wrong
                                    try:
                                        destination_stop: Stop = load_value(None, Stop, stop_id)
                                        self.actual_destination = f"Terminates at {destination_stop.name}, stop {destination_stop.code_or_id}"
                                    except KeyError:
                                        self.actual_destination = f"Terminates at unknown stop {stop_id}"

                    # Handle the case where the bus departs later than scheduled
                    if self.real_trip.stop_times[0].schedule_relationship == "SKIPPED":
                        # skipped_sequence = self.real_trip.stop_times[0].stop_sequence
                        length = len(self.real_trip.stop_times)
                        # Apparently this doesn't necessarily have to be indicated from the first stop...
                        # if skipped_sequence == 1:
                        i = 0
                        stop_time_update = self.real_trip.stop_times[i]
                        try:
                            # Find the first stop sequence not skipped
                            while stop_time_update.schedule_relationship == "SKIPPED" and i < length - 1:
                                i += 1
                                stop_time_update = self.real_trip.stop_times[i]

                            if stop_time_update.schedule_relationship == "SKIPPED":
                                sequence = stop_time_update.stop_sequence + 1
                            else:
                                sequence = self.real_trip.stop_times[i - 1].stop_sequence + 1
                            if sequence < 1:
                                sequence = 1
                            if sequence > total_stops:
                                sequence = total_stops
                            # if not all_stops:
                            #     all_stops = load_stops()
                            # stop_id = all_stops[sequence].stop_id
                            stop_id = StopTime.from_sql_sequence(self.trip_id, sequence).stop_id
                        except IndexError:
                            # This shouldn't happen, but if it does, just ignore the departure text
                            pass
                        else:
                            if 1 < sequence < total_stops:  # If it thinks it's departing from the last stop, something is probably wrong
                                try:
                                    departure_stop: Stop = load_value(None, Stop, stop_id)
                                    self.actual_start = f"Departs from {departure_stop.name}, stop {departure_stop.code_or_id}"
                                except KeyError:
                                    self.actual_start = f"Departs from unknown stop {stop_id}"

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
                    self.vehicle = vehicles.vehicles.get(vehicle_id)  # In case there somehow doesn't exist a value
                else:
                    self.vehicle = self.vehicle_id = None
            else:
                self.vehicle = self.vehicle_id = None
            self.is_train_departure: bool = getattr(self.route(), "route_type", None) == 2  # Trains use a different API for vehicle locations
        elif isinstance(stop_time, AddedStopTime):
            self.is_added = True
            self.stop_time = stop_time
            self.day_modifier = 0
            self._trip = None
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
            self.real_trip = stop_time.trip_update
            self.schedule_relationship = "ADDED"
            self._destination = stop_time.destination
            self.vehicle = stop_time.vehicle
            self.vehicle_id = stop_time.vehicle_id
            self.is_train_departure: bool = getattr(self.route(), "route_type", None) == 2  # Trains use a different API for vehicle locations
        elif isinstance(stop_time, StationDeparture):
            self.is_added = True
            self.station_departure = stop_time
            self.stop_time = stop_time
            self.day_modifier = day_modifier
            self._trip = None
            self.trip_id = stop_time.trip_code
            if station_trip_update and station_trip_update.trip.route_id != "Unknown":
                try:
                    self._route = Route.from_sql(station_trip_update.trip.route_id)
                except KeyError:
                    self._route = None
            else:
                self._route = None
            self.stop_id = TRAIN_STATION_CODE_TO_ID[stop_time.station_code]
            self.sequence = None
            self.stop_headsign = self._destination = stop_time.destination
            self.pickup_type = stop_time.destination == stop_time.station_name
            self.drop_off_type = stop_time.origin == stop_time.station_name
            if stop_time.status == "No Information":
                self.arrival_time = self.departure_time = None
            else:
                self.arrival_time = stop_time.expected_arrival
                self.departure_time = stop_time.expected_departure
            self.scheduled_arrival_time = stop_time.scheduled_arrival
            self.scheduled_departure_time = stop_time.scheduled_departure
            self.real_time = True
            self.real_trip = station_trip_update
            # nest_asyncio.apply()
            # loop = asyncio.new_event_loop()  # asyncio is stupid
            # # self.real_trip = asyncio.run(_create_trip_update_from_train(stop_time, debug, write))
            # # self.real_trip = loop.run_until_complete(loop.create_task(_create_trip_update_from_train(stop_time, debug, write)))
            # asyncio_is_stupid = asyncio.run_coroutine_threadsafe(_create_trip_update_from_train(stop_time, debug, write), loop)
            # self.real_trip = asyncio_is_stupid.result(timeout=20)
            self.schedule_relationship = "ADDED"
            self.vehicle = self.vehicle_id = None
            self.is_train_departure = True
        else:
            raise TypeError(f"Unexpected StopTime type {type(stop_time).__name__} received")

    def trip(self, data: GTFSData = None) -> Optional[Trip]:
        if self._trip:
            return self._trip
        try:
            trip = load_value(data, Trip, self.trip_id, None)
            # return load_value_from_id(data, "trips.txt", self.trip_id, None)
            self._trip = trip
            return trip
        except KeyError:
            return None

    def route(self, data: GTFSData = None) -> Optional[Route]:
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

    def stop(self, data: GTFSData = None) -> Optional[Stop]:
        try:
            return load_value(data, Stop, self.stop_id, None)
            # return load_value_from_id(data, "stops.txt", self.stop_id, None)
        except KeyError:
            return None

    def destination(self, data: GTFSData = None) -> str:
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
        # trip = self.trip()
        # stop = self.stop()
        # if trip is not None:
        #     return f"RealStopTime - [{self.schedule_relationship}] {self.available_departure_time} to {trip.headsign} (Stop {stop.name} - #{self.sequence}, Trip {self.trip_id})"
        # return f"RealStopTime - [{self.schedule_relationship}] {self.available_departure_time} to <Unknown> (Stop {stop.name} - #{self.sequence}, Trip {self.trip_id})"


class ScheduledTrip:
    """ A Trip that carries information about its scheduling """
    def __init__(self, trip: Trip, stop_times: list[StopTime], date: time.date, *, day_modifier: int = 0):
        self.raw_trip: Trip = trip
        self.raw_stop_times: list[StopTime] = stop_times
        self.trip_id: str = self.raw_trip.trip_id
        self.route_id: str = self.raw_trip.route_id
        self.calendar_id: str = self.raw_trip.calendar_id
        self.headsign: str = self.raw_trip.headsign
        self.short_name: str = self.raw_trip.short_name
        self.direction_id: int = self.raw_trip.direction_id
        self.block_id: str = self.raw_trip.block_id
        self.shape_id: str = self.raw_trip.shape_id
        self.total_stops: int = self.raw_trip.total_stops
        self.start_date: time.date = date
        self.day_modifier: int = day_modifier
        self.trip_identifier: str = f"{self.trip_id}||{self.day_modifier}"
        self.stop_times: list[SpecificStopTime] = []
        for stop_time in self.raw_stop_times:
            self.stop_times.append(SpecificStopTime(stop_time, self.start_date, day_modifier=self.day_modifier))
        self.departure_time = self.stop_times[0].departure_time

    def route(self, data: GTFSData = None, db: database.Database = None) -> Route:
        return self.raw_trip.route(data, db)

    def calendar(self, data: GTFSData = None, db: database.Database = None) -> Calendar:
        return self.raw_trip.calendar(data, db)

    def shape(self, data: GTFSData = None, db: database.Database = None) -> Shape:
        return self.raw_trip.shape(data, db)

    def __repr__(self):
        # ScheduledTrip 3626_209 - 2023-10-14 02:00:00 to Charlesland, stop 7462 (93 stops) - Route 3626_39040
        return f"{self.__class__.__name__} {self.trip_id} - {self.departure_time} to {self.headsign} ({self.total_stops} stops) - Route {self.route_id}"

# @dataclass()
# class TripSchedule:
#     trip: Trip
#     stops: list[StopTime]


# This here is for dealing with (static) schedules, getting closer to user-readable output
class StopSchedule:
    """ Get the stop's schedule """

    def __init__(self, data: GTFSData, stop_id: str, hide_terminating: bool = True, route_filter_userid: int = None):
        self.db = get_database()
        self.data_db = get_data_database()
        self.data = data
        self.stop = load_value(data, Stop, stop_id, self.db)
        # self.stop = load_value_from_id(data, "stops.txt", stop_id, self.db)
        self.stop_id = self.stop.id

        # self._route_id_cache[route_id] = Route.filter_name()
        self.route_filter_userid = route_filter_userid
        self._route_id_cache: dict[str, str] = {}
        self.route_filter: set[str] = set()
        self.route_filter_exists: bool = False
        if route_filter_userid is not None:
            # noinspection SqlResolve
            route_filter_data = self.data_db.fetchrow("SELECT routes FROM route_filters WHERE user_id=? AND stop_id=?", (route_filter_userid, self.stop_id))
            if route_filter_data:
                self.route_filter = set(json.loads(route_filter_data["routes"]))
                self.route_filter_exists = True

        self._all_routes: dict[str, Route] = {}  # All routes passing through the stop (Does not account for routes that only terminate at this stop)
        self.all_trips: dict[str, Trip] = {}
        self.hide_terminating = hide_terminating
        self.has_trains: bool = False  # Whether this schedule contains train routes

        # self.total_stops[trip_id] = Trip.total_stops
        self.total_stops: dict[str, int] = {}

        # self.stop_times[trip_id] = StopTime(stop_id=self.stop_id)
        self.stop_times: dict[str, StopTime] = {}

        def handle_trip(_trip: Trip) -> None:
            self.all_trips[_trip.trip_id] = _trip
            self.total_stops[_trip.trip_id] = _trip.total_stops
            if _trip.route_id not in self._all_routes:
                route = _trip.route(self.data, self.db)
                self._all_routes[_trip.route_id] = route
                self._route_id_cache[_trip.route_id] = route.filter_name()
                if route.route_type == 2:
                    self.has_trains |= True

            route_name = self._route_id_cache.get(_trip.route_id, None)
            if route_name is None:
                route_name = _trip.route(self.data, self.db).filter_name()
            # If route filter exists and the route name is not in the filter, delete it
            if self.route_filter and route_name not in self.route_filter:
                del self.all_trips[_trip.trip_id]
                trip_ids_full.remove(_trip.trip_id)

        # Load all schedules (trips) that will pass through this stop
        sql_data = self.db.fetch("SELECT * FROM stop_times WHERE stop_id=?", (stop_id,))
        trip_ids_full = set(entry["trip_id"] for entry in sql_data)
        trip_ids_inter = trip_ids_full.intersection(self.data.trips.keys())
        for trip_id in trip_ids_inter:
            trip = self.data.trips[trip_id]
            handle_trip(trip)

        # Add trips that are not yet loaded into memory
        trip_ids = trip_ids_full.difference(trip_ids_inter)
        if trip_ids:
            for trip_id in trip_ids:
                trip = Trip.from_sql(trip_id, self.db)
                self.data.trips[trip_id] = trip
                handle_trip(trip)

        # Load stop times from trips that were already loaded into memory
        schedule_ids_inter = trip_ids_full.intersection(self.data.stop_times.keys())
        schedule_ids_copy = schedule_ids_inter.copy()
        for trip_id in schedule_ids_inter:  # key1 = trip_id, key2 = stop_id
            if stop_id in self.data.stop_times[trip_id]:
                stop_time = self.data.stop_times[trip_id][stop_id]
                if not hide_terminating or (hide_terminating and stop_time.sequence < self.total_stops[trip_id]):  # Ignore if it's the last stop of the trip
                    self.stop_times[trip_id] = stop_time
                else:
                    del self.all_trips[trip_id]
            else:
                schedule_ids_copy.remove(trip_id)  # False positive: Trip ID exists in memory but this stop's StopTime is not loaded

        # Add stop times from trips that are not yet loaded in memory
        schedule_ids = trip_ids_full.difference(schedule_ids_copy)
        schedule_ids_copy = schedule_ids.copy()
        if schedule_ids:
            for trip_id in schedule_ids:
                stop_time = StopTime.from_sql_specific(trip_id, stop_id, self.db)
                if not hide_terminating or (hide_terminating and stop_time.sequence < self.total_stops[trip_id]):  # Ignore if it's the last stop of the trip
                    self.stop_times[trip_id] = stop_time
                else:
                    del self.all_trips[trip_id]
                if trip_id in self.data.stop_times:
                    self.data.stop_times[trip_id][stop_id] = stop_time
                else:
                    self.data.stop_times[trip_id] = {stop_id: stop_time}
                schedule_ids_copy.remove(trip_id)
        if schedule_ids_copy:
            print("Missed Trip IDs: ", schedule_ids_copy)

        self.all_routes = list(self._all_routes.values())
        del self._all_routes

    def relevant_stop_times_one_day(self, date: time.date, *, day_modifier: int = 0) -> list[SpecificStopTime]:
        """ Get the stop times for one day """
        db = get_database()  # This may get called in a separate thread than the one where the schedule was created
        output = []
        for trip in self.all_trips.values():
            valid = trip_validity(self.data, trip, date, db)
            # If the service is, indeed, valid today, then add it to the output
            if valid:
                output.append(SpecificStopTime(self.stop_times[trip.trip_id], date, day_modifier=day_modifier))

        # Sort the stop times by departure time and return
        output.sort(key=lambda st: st.departure_time)
        return output

    def relevant_stop_times(self, date: time.date) -> list[SpecificStopTime]:
        """ Get the stop times for yesterday, today, and tomorrow """
        yesterday = self.relevant_stop_times_one_day(date - time.timedelta(days=1), day_modifier=-1)
        today = self.relevant_stop_times_one_day(date, day_modifier=0)
        tomorrow = self.relevant_stop_times_one_day(date + time.timedelta(days=1), day_modifier=1)
        return yesterday + today + tomorrow

    def __repr__(self):
        return f"Stop Schedule for {self.stop}"


def real_trip_updates(real_time_data: GTFSRData, trip_ids: set[str], stop_id: str) -> tuple[dict[str, TripUpdate], dict[str, TripUpdate]]:
    if not real_time_data:
        return {}, {}
    output = {}
    added = {}
    for trip_id in trip_ids:
        if trip_id in real_time_data.scheduled:
            output[trip_id] = real_time_data.scheduled[trip_id]
    for trip_update in real_time_data.added.values():
        if trip_update.stop_times is not None:
            for stop_time_update in trip_update.stop_times:
                if stop_time_update.stop_id == stop_id:
                    added[trip_update.entity_id] = trip_update
                    break
    return output, added


# Stuff for real-time schedules
class RealTimeStopSchedule:
    def __init__(self, data: GTFSData | None, stop_id: str | None, real_time_data: GTFSRData, vehicle_data: VehicleData,
                 static_schedule: StopSchedule | None = None, stop_times: list[SpecificStopTime] | None = None, hide_terminating: bool = True, debug: bool = False, write: bool = True):
        self.db = get_database()
        if static_schedule is not None:
            self.stop_schedule = static_schedule
            self.data = static_schedule.data
        else:
            if data is None:
                raise ValueError("data cannot be None if existing_schedule is not provided")
            if stop_id is None:
                raise ValueError("stop_id cannot be None if existing_schedule is not provided")
            self.data = data
            self.stop_schedule = StopSchedule(data, stop_id, hide_terminating=hide_terminating)
        self.stop = self.stop_schedule.stop
        self.stop_id = self.stop_schedule.stop_id
        self.hide_terminating = self.stop_schedule.hide_terminating
        if stop_times is not None:
            self.stop_times = stop_times
        else:
            self.stop_times = self.stop_schedule.relevant_stop_times(time.date.today())
        self.trip_ids = {stop_time.trip_id for stop_time in self.stop_times}  # Exclude duplicates

        self.real_trips, self.added_trips = real_trip_updates(real_time_data, self.trip_ids, self.stop_id)

        self.real_time_data = real_time_data
        self.vehicle_data = vehicle_data
        self.debug: bool = debug
        self.write: bool = write
        self.has_trains = self.stop_schedule.has_trains

        self.station_data: dict[str, StationDeparture] | None = None
        if self.has_trains:
            nest_asyncio.apply()
            loop = asyncio.get_event_loop()  # asyncio is stupid
            self.station_data: dict[str, StationDeparture] = loop.run_until_complete(loop.create_task(fetch_station_departures(self.stop_id, self.debug, self.write)))

    @classmethod
    def from_existing_schedule(cls, existing_schedule: StopSchedule, real_time_data: GTFSRData, vehicle_data: VehicleData,
                               stop_times: list[SpecificStopTime] | None = None, debug: bool = False, write: bool = True):
        """ Load a RealTimeStopSchedule from an existing StopSchedule, so that the operation need not be repeated """
        return cls(None, None, real_time_data, vehicle_data, existing_schedule, stop_times, debug=debug, write=write)

    def real_stop_times(self):
        """ Get the real-time stop times for this schedule """
        output = []
        for stop_time in self.stop_times:
            real_stop_time = RealStopTime(stop_time, self.real_trips, self.vehicle_data, self.station_data)
            if not getattr(real_stop_time, "remove", False):
                output.append(real_stop_time)

        # nest_asyncio.apply()
        # loop = asyncio.new_event_loop()
        if self.station_data:
            for departure in self.station_data.values():  # Any trips that exist on the real-time but couldn't be matched to an existing trip (or had invalid static information)
                if self.hide_terminating and departure.destination == departure.station_name:  # Skip trips that terminate here if that option is set
                    continue
                day_modifier = (departure.date - time.date.today()).days
                # real_trip = loop.run_until_complete(loop.create_task(_create_trip_update_from_train(departure)))
                real_trip = _create_trip_update_from_train(departure)
                output.append(RealStopTime(departure, None, None, None, day_modifier, real_trip))

        for trip_id, added_trip in self.added_trips.items():
            for stop_time in added_trip.stop_times:
                if stop_time.stop_id == self.stop_id:
                    try:
                        last_stop = load_value(self.data, Stop, added_trip.stop_times[-1].stop_id, self.db)
                        # last_stop = load_value_from_id(self.data, "stops.txt", added_trip.stop_times[-1].stop_id, self.db)
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
                        route = load_value(self.data, Route, added_trip.trip.route_id, self.db)
                        # route = load_value_from_id(self.data, "routes.txt", added_trip.trip.route_id, self.db)
                    except KeyError:
                        route = None
                    # route = self.stop_schedule.data.routes.get(added_trip.trip.route_id)
                    if added_trip.vehicle_id:
                        vehicle_id = added_trip.vehicle_id
                        vehicle = self.vehicle_data.vehicles[vehicle_id]
                    else:
                        vehicle = None
                    trip_update = self.real_time_data.added[trip_id]
                    added_stop_time = AddedStopTime(stop_time, trip_update, route, self.stop_schedule.stop, destination, vehicle)
                    output.append(RealStopTime(added_stop_time, None, None, None))

        output.sort(key=lambda st: st.available_departure_time)
        return output

    def __repr__(self):
        return f"Real-Time Stop Schedule for {self.stop}"


class RouteSchedule:
    def __init__(self, data: GTFSData, route: Route):  # route_id: str
        self.data = data
        self.db = get_database()
        self.route: Route = route
        self.route_id: str = self.route.id
        # self.route: Route = load_value(self.data, Route, route_id, self.db)
        # self.route_id = self.route.id

        self.all_trips: dict[str, Trip] = {}
        self.stop_times: dict[str, list[StopTime]] = {}

        # The data is loaded into GTFSData so that it can be fetched by the StopSchedule or similar
        trips = Trip.from_route(self.route.id, self.db)
        for trip in trips:
            self.all_trips[trip.trip_id] = trip
            self.data.trips[trip.trip_id] = trip
            self.stop_times[trip.trip_id] = StopTime.from_sql(trip.trip_id, self.db)
            for stop_time in self.stop_times[trip.trip_id]:
                if trip.trip_id not in self.data.stop_times:
                    self.data.stop_times[trip.trip_id] = {}
                self.data.stop_times[trip.trip_id][stop_time.stop_id] = stop_time

    def relevant_trips_one_day(self, date: time.date, *, day_modifier: int = 0) -> list[ScheduledTrip]:
        """ Get relevant trips and stop times for one day (all trips valid for date on GTFS data) """
        db = get_database()
        valid_trips: list[ScheduledTrip] = []
        for trip_id, trip in self.all_trips.items():
            if trip_validity(self.data, trip, date, db):
                valid_trips.append(ScheduledTrip(trip, self.stop_times[trip_id], date, day_modifier=day_modifier))

        valid_trips.sort(key=lambda t: t.departure_time)
        return valid_trips

    def relevant_trips(self, date: time.date) -> list[ScheduledTrip]:
        """ Get relevant trips and stop times from 00:00 until end of the day """
        yesterday = self.relevant_trips_one_day(date - time.timedelta(days=1), day_modifier=-1)
        today = self.relevant_trips_one_day(date, day_modifier=0)
        valid_trips: list[ScheduledTrip] = []
        today_datetime = time.datetime.combine(date, time.time(), tz=TIMEZONE)
        for trip in yesterday:  # Only add trips from yesterday that start at/after midnight today
            if trip.departure_time >= today_datetime:
                valid_trips.append(trip)
        return valid_trips + today

    def __repr__(self):
        return f"Route Schedule for {self.route}"
