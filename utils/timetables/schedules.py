from typing import Optional

from regaus import time

from utils.timetables.shared import TIMEZONE, get_database
from utils.timetables.static import *
from utils.timetables.realtime import *

__all__ = [
    "SpecificStopTime", "AddedStopTime", "RealStopTime",
    "StopSchedule", "RealTimeStopSchedule", "real_trip_updates"
]


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
        self._destination: str | None = None

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

    def __repr__(self):
        # "SpecificStopTime - 2023-10-14 02:00:00 - Stop #1 for trip 3626_214"
        return f"SpecificStopTime - {self.departure_time} - Stop #{self.sequence} for Trip {self.trip_id}"

        # "SpecificStopTime - 2023-10-14 02:00:00 to Charlesland, stop 7462 (Stop D'Olier Street - #1, Trip 3626_214)"
        # trip = self.trip()
        # stop = self.stop()
        # return f"SpecificStopTime - {self.departure_time} to {trip.headsign} (Stop {stop.name} - #{self.sequence}, Trip {trip.trip_id})"


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
    _destination: str | None
    vehicle: Vehicle | None
    vehicle_id: str | None

    def __init__(self, stop_time: SpecificStopTime | AddedStopTime, real_trips: dict[str, TripUpdate] | None, vehicles: VehicleData | None):
        if isinstance(stop_time, SpecificStopTime):
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
                    if self.real_trip.stop_times[-1].schedule_relationship == "SKIPPED":
                        i = len(self.real_trip.stop_times) - 1
                        stop_time_update = self.real_trip.stop_times[i]
                        while stop_time_update.schedule_relationship == "SKIPPED" and i > 0:
                            i -= 1
                            stop_time_update = self.real_trip.stop_times[i]
                        stop_id = self.real_trip.stop_times[i + 1].stop_id
                        try:
                            # destination_stop: Stop = load_value_from_id(None, "stops.txt", stop_id, None)
                            destination_stop: Stop = load_value(None, Stop, stop_id)
                            # The warning sign doesn't fit properly on desktop, but oh well. It's more noticeable than putting two exclamation marks
                            self._destination = f"⚠️ {destination_stop.name}, stop {destination_stop.code_or_id}"
                        except KeyError:
                            self._destination = f"Unknown Stop {stop_id}"
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
            self.real_trip = None
            self.schedule_relationship = "ADDED"
            self._destination = stop_time.destination
            self.vehicle = stop_time.vehicle
            self.vehicle_id = stop_time.vehicle_id
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


# @dataclass()
# class TripSchedule:
#     trip: Trip
#     stops: list[StopTime]


# This here is for dealing with (static) schedules, getting closer to user-readable output
class StopSchedule:
    """ Get the stop's schedule """

    def __init__(self, data: GTFSData, stop_id: str):
        self.db = get_database()
        self.data = data
        self.stop = load_value(data, Stop, stop_id, self.db)
        # self.stop = load_value_from_id(data, "stops.txt", stop_id, self.db)
        self.stop_id = self.stop.id
        # self.all_stop_times = []
        self.all_trips = []

        # self.stop_times[trip_id] = StopTime(stop_id=self.stop_id)
        self.stop_times: dict[str, StopTime] = {}

        # Load all schedules (trips) that will pass through this stop
        sql_data = self.db.fetch("SELECT * FROM stop_times WHERE stop_id=?", (stop_id,))
        trip_ids_full = set(entry["trip_id"] for entry in sql_data)
        trip_ids_inter = trip_ids_full.intersection(self.data.trips.keys())
        for key in trip_ids_inter:
            self.all_trips.append(self.data.trips[key])

        # Add trips that are not yet loaded into memory
        trip_ids = trip_ids_full.difference(trip_ids_inter)
        if trip_ids:
            for trip_id in trip_ids:
                trip = Trip.from_sql(trip_id, self.db)
                self.all_trips.append(trip)
                self.data.trips[trip_id] = trip

        # Load stop times from trips that were already loaded into memory
        schedule_ids_inter = trip_ids_full.intersection(self.data.stop_times.keys())
        schedule_ids_copy = schedule_ids_inter.copy()
        for trip_id in schedule_ids_inter:  # key1 = trip_id, key2 = stop_id
            if stop_id in self.data.stop_times[trip_id]:
                self.stop_times[trip_id] = self.data.stop_times[trip_id][stop_id]
            else:
                schedule_ids_copy.remove(trip_id)  # False positive: Trip ID exists in memory but this stop's StopTime is not loaded

        # Add stop times from trips that are not yet loaded in memory
        schedule_ids = trip_ids_full.difference(schedule_ids_copy)
        schedule_ids_copy = schedule_ids.copy()
        if schedule_ids:
            for trip_id in schedule_ids:
                stop_time = StopTime.from_sql_specific(trip_id, stop_id, self.db)
                self.stop_times[trip_id] = stop_time
                if trip_id in self.data.stop_times:
                    self.data.stop_times[trip_id][stop_id] = stop_time
                else:
                    self.data.stop_times[trip_id] = {stop_id: stop_time}
                schedule_ids_copy.remove(trip_id)
        if schedule_ids_copy:
            print("Missed Trip IDs: ", schedule_ids_copy)

    def relevant_stop_times_one_day(self, date: time.date) -> list[SpecificStopTime]:
        """ Get the stop times for one day """
        db = get_database()  # This may get called in a separate thread than the one where the schedule was created
        output = []
        weekday = date.weekday
        calendars = self.data.calendars
        calendar_exceptions = self.data.calendar_exceptions
        if not calendars:  # calendars empty = no calendars have been loaded yet
            load_calendars(self.data)
        for trip in self.all_trips:
            if trip.calendar_id in calendars:
                calendar = calendars[trip.calendar_id]
            else:  # Weird but just in case
                calendar = trip.calendar(self.data)
            # calendar = stop_time.trip(self.data).calendar(self.data)
            valid = None  # Whether the trip is valid for the given day

            # Check if the calendar has exceptions for today
            if trip.calendar_id in calendar_exceptions:
                exception = calendar_exceptions[trip.calendar_id].get(date)
                if exception:
                    valid = exception.exception
            else:  # Weird but just in case
                try:
                    calendar_exceptions = load_value(self.data, CalendarException, calendar.service_id, db)
                    # calendar_exceptions = load_value_from_id(self.data, "calendar_dates.txt", calendar.service_id, db)
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
        """ Get the real-time stop times for this schedule """
        output = []
        for stop_time in self.stop_times:
            output.append(RealStopTime(stop_time, self.real_trips, self.vehicle_data))

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
                        vehicle = self.vehicle_data.entities[vehicle_id]
                    else:
                        vehicle = None
                    added_stop_time = AddedStopTime(stop_time, trip_id, route, self.stop_schedule.stop, destination, vehicle)
                    output.append(RealStopTime(added_stop_time, None, None))

        output.sort(key=lambda st: st.available_departure_time)
        return output

    def __repr__(self):
        return f"Real-Time Stop Schedule for {self.stop}"
