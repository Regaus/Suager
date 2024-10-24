from __future__ import annotations

import asyncio
import io
import re

import discord
import nest_asyncio
from regaus import time

from utils import paginators
from utils.timetables.shared import TIMEZONE, WEEKDAYS, WARNING, CANCELLED, get_database, TRAIN_STATION_CODE_TO_ID
from utils.timetables.realtime import GTFSRData, VehicleData, TripUpdate, Vehicle, Train, TrainMovement, fetch_train_movements
from utils.timetables.static import GTFSData, Stop, load_value, Trip, StopTime, Route, FleetVehicle
from utils.timetables.schedules import trip_validity, SpecificStopTime, RealStopTime, ScheduledTrip, StopSchedule, RealTimeStopSchedule, RouteSchedule
from utils.timetables.maps import DEFAULT_ZOOM, get_map_with_buses, get_trip_diagram, distance_between_bus_and_stop, get_nearest_stop

__all__ = ("INBOUND_DIRECTION_ID", "StopScheduleViewer", "HubScheduleViewer", "TripDiagramViewer", "TripMapViewer", "MapViewer",
           "VehicleDataViewer", "RouteVehiclesViewer", "RouteScheduleViewer")


FLEET_REGEX = re.compile(r"^([A-Z]{2,3})([0-9]{1,3})$")
INBOUND_DIRECTION_ID = 1
PAGINATOR_MAX_LINES = 20
PAGINATOR_MAX_LENGTH = 1500


def get_model_code(fleet_number: str) -> str:
    """ Returns the model code of the bus (e.g. AX or 11500) """
    match = re.match(FLEET_REGEX, fleet_number)
    if match:
        return match.group(1)
    if fleet_number.isdigit():  # Go-Ahead buses
        match int(fleet_number) // 100:
            case 115 | 116:
                return "11500"  # Ex-SG
            case 117:
                return "11700"  # Ex-AX
            case 119:
                return "11900"  # Ex-GT
            case 121:
                return "12100"  # Single decker
            case 313:
                return "31300"
            case 324:
                return "32400"
            case _:
                return "Unknown"
    return "Unknown"


def format_time(provided_time: time.datetime, today: time.date) -> str:
    """ Format the provided time, showing when a given trip happens outside the current day """
    formatted = provided_time.format("%H:%M")
    # If the date is not the date of the lookup, then append the weekday of the time
    # If self.now is Tuesday 23:59, then trips at Wednesday 00:00 will be treated as "tomorrow"
    # If self.now is Wednesday 00:00, then trips at Wednesday 00:00 will be treated as "today"
    if provided_time.date() != today:
        formatted = f"{WEEKDAYS[provided_time.weekday]} {formatted}"
    return formatted


def format_timestamp(data_timestamp: time.datetime) -> str:
    return f"{data_timestamp:%Y-%m-%d %H:%M:%S} (<t:{int(data_timestamp.timestamp)}:R>)"


def format_departure(self: StopScheduleViewer | HubScheduleViewer, stop_time: RealStopTime | SpecificStopTime):
    hub = isinstance(self, HubScheduleViewer)
    destination = stop_time.destination(self.static_data)

    if self.real_time:
        if stop_time.scheduled_departure_time is not None:
            scheduled_departure_time = self.format_time(stop_time.scheduled_departure_time)
        else:
            scheduled_departure_time = "--:--"  # "Unknown"

        if stop_time.schedule_relationship == "CANCELED":
            real_departure_time = "CANCELD" if hub else "CANCELLED"
            destination = CANCELLED + destination
        elif stop_time.schedule_relationship == "SKIPPED":
            real_departure_time = "SKIPPED"
            destination = WARNING + destination
        elif stop_time.departure_time is not None:
            real_departure_time = self.format_time(stop_time.departure_time)
        elif stop_time.trip().block_id:  # Try to get real-time data from the previous trip to be able to tell what will happen with this one
            real_departure_time = "--:--"  # Default if no value is found
            prev_trips, _ = get_prev_next_trips(stop_time.trip(), self.today, self.static_data, self.cog.db)
            if prev_trips:
                prev_trip_id, _, _, _ = prev_trips[-1]  # Load last trip
                prev_trip: Trip = load_value(self.static_data, Trip, prev_trip_id, self.cog.db)
                prev_real_time: TripUpdate | None = self.cog.real_time_data.scheduled.get(prev_trip_id)
                # prev_real_time: TripUpdate | None = None
                # for entity in self.cog.real_time_data.entities.values():  # type: TripUpdate
                #     if entity.trip.trip_id == prev_trip_id:
                #         prev_real_time = entity
                #         break
                if prev_real_time:
                    prev_arrival_time: time.datetime = time.datetime.zero

                    def _handle_trip(_delay: time.timedelta) -> time.datetime:
                        _stop_time = StopTime.from_sql_sequence(prev_trip_id, prev_trip.total_stops, self.cog.db)
                        departure_time = time.datetime.combine(self.today, time.time(), TIMEZONE) + time.timedelta(seconds=_stop_time.departure_time)
                        return departure_time + _delay

                    for stop_time_update in prev_real_time.stop_times[::-1]:
                        # Find the last stop that has an arrival or departure time available
                        # Departure times take priority since they are later
                        if stop_time_update.departure_time is not None:
                            prev_arrival_time = stop_time_update.departure_time
                            break
                        if stop_time_update.arrival_time is not None:
                            prev_arrival_time = stop_time_update.arrival_time
                            break
                        if stop_time_update.departure_delay is not None:
                            prev_arrival_time = _handle_trip(stop_time_update.departure_delay)
                            break
                        if stop_time_update.arrival_delay is not None:
                            prev_arrival_time = _handle_trip(stop_time_update.arrival_delay)
                            break

                    first_stop = StopTime.from_sql_sequence(stop_time.trip_id, 1, self.cog.db)
                    this_departure_time = time.datetime.combine(self.today, time.time(), TIMEZONE) + time.timedelta(seconds=first_stop.departure_time)
                    # If the last trip is expected to arrive later than this one is scheduled to depart
                    if prev_arrival_time > this_departure_time:
                        delay = prev_arrival_time - this_departure_time
                        real_departure_time = self.format_time(stop_time.scheduled_departure_time + delay) + "*"
                    else:
                        real_departure_time = self.format_time(stop_time.scheduled_departure_time) + "*"
        else:
            real_departure_time = "--:--"
    else:
        scheduled_departure_time = self.format_time(stop_time.departure_time)
        real_departure_time = ""

    if not hub and stop_time.pickup_type == 1:
        scheduled_departure_time = "D " + scheduled_departure_time
    elif not hub and stop_time.drop_off_type == 1:
        scheduled_departure_time = "P " + scheduled_departure_time

    _route = stop_time.route(self.static_data)
    if _route is None:
        route = "Unknown"
    else:
        route = _route.short_name

    if hub and stop_time.actual_destination:
        destination = WARNING + stop_time.actual_destination.lstrip("Terminates at ")
    elif not hub and (stop_time.actual_destination or stop_time.actual_start) and not destination.startswith(WARNING):
        destination = WARNING + destination

    def _handle_fleet_vehicle(_vehicle: FleetVehicle) -> str:
        fleet = _vehicle.fleet_number
        match = re.match(FLEET_REGEX, fleet)
        return f"{match.group(1)}{match.group(2):>3}" if match else fleet

    def _format_distance(_vehicle: Vehicle | Train) -> str:
        trip = stop_time.real_trip if stop_time.is_added else stop_time.trip(self.static_data)
        _distance_m, colour = distance_between_bus_and_stop(trip, self.stop, _vehicle, self.static_data)
        if _distance_m >= 1000:
            if self.compact_mode == 1:
                _distance = f"{_distance_m / 1000:.1f}k"
            else:
                _distance = f"{_distance_m / 1000:.2f}km"
        else:
            _distance = f"{round(_distance_m, -1):.0f}m"
        _distance += {-1: "🟠", 0: "🟢", 1: "🟡", 2: "🔴"}.get(colour, "🟠") + "\u2060"
        return _distance

    if hub or not self.real_time or self.compact_mode >= 2:
        distance = vehicle = ""
    elif getattr(stop_time, "is_train_departure", False):
        vehicle = trip_code = stop_time.trip().short_name  # The "Bus" column is used to show the trip code
        train: Train | None = self.cog.train_data.get(trip_code)
        if train is None:
            distance = "-"
        elif train.latitude == 0 and train.longitude == 0:
            distance = "-"
        else:
            distance = _format_distance(train)
    elif stop_time.vehicle is not None:
        vehicle_data: FleetVehicle | None = self.cog.fleet_data.get(stop_time.vehicle_id)
        if vehicle_data:
            vehicle = _handle_fleet_vehicle(vehicle_data)
        else:
            vehicle = str(stop_time.vehicle_id)
        if stop_time.vehicle.latitude == 0 and stop_time.vehicle.longitude == 0:
            distance = "-"
        else:
            distance = _format_distance(stop_time.vehicle)
    elif getattr(stop_time.trip(), "block_id", None):  # Similarly to the real-time departure time, try to guess the vehicle that will depart on this trip
        vehicle = "-"  # Default if no value is found
        prev_trips, _ = get_prev_next_trips(stop_time.trip(), self.today, self.static_data, self.cog.db)
        if prev_trips:
            prev_trip_id, _, _, _ = prev_trips[-1]  # Load last trip
            prev_trip: Trip = load_value(self.static_data, Trip, prev_trip_id, self.cog.db)
            prev_real_time: TripUpdate | None = self.cog.real_time_data.scheduled.get(prev_trip_id)
            # prev_real_time: TripUpdate | None = None
            # for entity in self.cog.real_time_data.entities.values():  # type: TripUpdate
            #     if entity.trip.trip_id == prev_trip_id:
            #         prev_real_time = entity
            #         break
            if prev_real_time and prev_real_time.vehicle_id:
                vehicle_data: FleetVehicle | None = self.cog.fleet_data.get(prev_real_time.vehicle_id)
                if vehicle_data:
                    vehicle = _handle_fleet_vehicle(vehicle_data) + "*"
                else:
                    vehicle = str(prev_real_time.vehicle_id) + "*"
        distance = "-"  # Don't bother trying to guess the distance
    else:
        distance = vehicle = "-"

    if hub:
        output_line = [route, destination, scheduled_departure_time, real_departure_time]
    else:
        actual_destination = stop_time.actual_destination or ""
        actual_start = stop_time.actual_start or ""
        output_line = [route, destination, scheduled_departure_time, real_departure_time, vehicle, distance, actual_destination, actual_start]

    return output_line


def get_vehicle_data(self: TripDiagramViewer | TripMapViewer) -> str:
    """ Get data about the bus that is serving this trip """
    bus_data = []
    if getattr(self.trip, "short_name", None) in self.train_data:  # A real-time trip wouldn't have a "short_name", so this is fine
        vehicle = self.train_data.get(self.trip.short_name)
        if vehicle is not None and vehicle.latitude != 0 and vehicle.latitude != 0:
            nearest_stop = get_nearest_stop(self.trip, vehicle, self.static_data)
            bus_data.append(f"The train is currently near the stop {nearest_stop.name} (stop {nearest_stop.code_or_id}).")
            bus_data.append(f"Information provided by Irish Rail: {vehicle.public_message}")
    else:
        vehicle = self.vehicle_data.vehicles.get(self.vehicle_id)
        if vehicle is not None and vehicle.latitude != 0 and vehicle.longitude != 0:
            nearest_stop = get_nearest_stop(self.trip, vehicle, self.static_data)
            bus_data.append(f"The bus is currently near the stop {nearest_stop.name} (stop {nearest_stop.code_or_id}).")
        fleet_vehicle: FleetVehicle | None = self.cog.fleet_data.get(self.vehicle_id)
        if fleet_vehicle is not None:
            bus_data.append(f"This trip is served by the bus {fleet_vehicle.fleet_number} ({fleet_vehicle.reg_plates}).")
            bus_data.append(f"-# Model: {fleet_vehicle.model} | Notable features: {fleet_vehicle.trivia}")
    return "\n".join(bus_data)


# Cache for the next/previous trips: prev_next_trips[trip_id] = ([prev_trips], [next_trips])
prev_next_trips_cache: dict[str, tuple[list[tuple[str, time.datetime, str, str]], list[tuple[str, time.datetime, str, str]]]] = {}


def get_prev_next_trips(current_trip: Trip, today_date: time.date, static_data: GTFSData, db) \
        -> tuple[list[tuple[str, time.datetime, str, str]], list[tuple[str, time.datetime, str, str]]]:
    """ Returns the previous and upcoming trips along the given route

    Inner tuple format: (trip_id, start_time, route, destination) """
    # If we have already calculated this for this block before, don't bother doing it again
    if current_trip.trip_id in prev_next_trips_cache:
        return prev_next_trips_cache[current_trip.trip_id]
    block_id = current_trip.block_id
    if block_id:
        # Fetch all relevant trips
        calendar_id = current_trip.calendar_id
        block = None
        if block_id in static_data.trip_blocks:
            block = static_data.trip_blocks[block_id].get(calendar_id)
        else:
            static_data.trip_blocks[block_id] = {}  # Make sure an empty dictionary is initialised
        if not block:
            block = Trip.from_block(block_id, calendar_id)
            static_data.trip_blocks[block_id][calendar_id] = block

        prev_trips: list[tuple[str, time.datetime, str, str]] = []
        next_trips: list[tuple[str, time.datetime, str, str]] = []
        today = time.datetime.combine(today_date, time.time(), tz=TIMEZONE)
        stop_time = StopTime.from_sql_sequence(current_trip.trip_id, 1, db)
        now = today + time.timedelta(seconds=stop_time.departure_time)
        for trip in block:
            if trip.trip_id == current_trip.trip_id:  # Ignore current trip
                continue
            # This shouldn't be necessary anymore, since the calendar ID is already filtered
            # valid = trip_validity(static_data, trip, today_date, db)
            # if not valid:  # Only include the trip if it actually runs today
            #     continue
            stop_time = StopTime.from_sql_sequence(trip.trip_id, 1, db)
            departure = today + time.timedelta(seconds=stop_time.departure_time)
            # print(trip.trip_id, today_date, today, departure, now, departure > now)
            _route = trip.route(static_data, db)
            if _route:
                route = f"Route {_route.short_name}"
            else:
                route = f"Unknown route {trip.route_id}"  # Should never happen, but just in case.
            trip_data = (trip.trip_id, departure, route, trip.headsign)
            if departure > now:
                next_trips.append(trip_data)
            else:
                prev_trips.append(trip_data)
        prev_trips.sort(key=lambda t: t[1])
        next_trips.sort(key=lambda t: t[1])
        prev_next_trips_cache[current_trip.trip_id] = (prev_trips, next_trips)
        return prev_trips, next_trips
    prev_next_trips_cache[current_trip.trip_id] = ([], [])
    return [], []


class StopScheduleViewer:
    """ A loader for stop schedules"""

    def __init__(self, static_data: GTFSData, now: time.datetime, real_time: bool, fixed: bool, today: time.date, stop: Stop, lines: int,
                 base_schedule: StopSchedule, base_stop_times: list[SpecificStopTime],
                 real_schedule: RealTimeStopSchedule | None, real_stop_times: list[RealStopTime] | None, cog):
        self.static_data = static_data
        self.cog = cog  # The Timetables cog
        self.real_time_data: GTFSRData = cog.real_time_data
        self.vehicle_data: VehicleData = cog.vehicle_data
        self.fleet_data: dict[str, FleetVehicle] = cog.fleet_data
        self.train_data: dict[str, Train] = cog.train_data
        self.stop = stop
        self.latitude = stop.latitude
        self.longitude = stop.longitude
        self.base_schedule = base_schedule
        self.base_stop_times = base_stop_times
        self.real_schedule = real_schedule
        self.real_stop_times = real_stop_times

        self.now = now
        self.today = today
        self.real_time = real_time
        self.fixed = fixed
        # self.fixed_time = fixed
        self.lines = lines

        self.compact_mode: int = 0  # Don't cut off destinations by default
        self.index_offset = 0
        self.day_offset = 0  # Offset for date changes (prevents confusion when launching the TripDiagramViewer)
        self.empty: bool = False  # Whether there are any departures or arrivals shown by the viewer

        self.start_idx, self.end_idx = self.get_indexes()
        self.output = self.create_output()

    @classmethod
    async def load(cls, data: GTFSData, stop: Stop, cog, now: time.datetime | None = None, lines: int = 7, hide_terminating: bool = True, user_id: int = None):
        """ Load the data and return a working instance """
        if now is not None:
            real_time: bool = abs((now - time.datetime.now()).total_microseconds()) < 28_800_000_000
            fixed = True
        else:
            now = time.datetime.now(tz=TIMEZONE)
            real_time = True
            fixed = False
        today = now.date()
        event_loop = asyncio.get_event_loop()
        base_schedule, base_stop_times = await event_loop.run_in_executor(None, cls.load_base_schedule, data, stop.id, today, hide_terminating, user_id)
        if real_time:
            real_schedule, real_stop_times = await event_loop.run_in_executor(None, cls.load_real_schedule, cog, base_schedule, base_stop_times)
        else:
            real_schedule = real_stop_times = None
        return cls(data, now, real_time, fixed, today, stop, lines, base_schedule, base_stop_times, real_schedule, real_stop_times, cog)

    async def reload(self):
        new_schedule = await self.load(self.static_data, self.stop, self.cog, self.now, self.lines, self.base_schedule.hide_terminating, self.base_schedule.route_filter_userid)
        # These will change in the new_schedule because the "now" parameter is set
        new_schedule.fixed = self.fixed
        new_schedule.real_time = self.real_time
        new_schedule.compact_mode = self.compact_mode
        # new_schedule.index_offset = self.index_offset  # It's probably better to reset this to zero since we have changed the routes that appear here
        new_schedule.update_output()
        return new_schedule

    @staticmethod
    def load_base_schedule(data: GTFSData, stop_id: str, today: time.date, hide_terminating: bool = True, user_id: int = None):
        """ Load the static StopSchedule """
        base_schedule = StopSchedule(data, stop_id, hide_terminating=hide_terminating, route_filter_userid=user_id)
        base_stop_times = base_schedule.relevant_stop_times(today)
        return base_schedule, base_stop_times

    @staticmethod
    def load_real_schedule(cog, base_schedule: StopSchedule, base_stop_times: list[SpecificStopTime]):
        """ Load the RealTimeStopSchedule """
        real_schedule = RealTimeStopSchedule.from_existing_schedule(base_schedule, cog.real_time_data, cog.vehicle_data, base_stop_times)
        real_stop_times = real_schedule.real_stop_times()
        return real_schedule, real_stop_times

    async def refresh_real_schedule(self):
        """ Refresh the RealTimeStopSchedule """
        event_loop = asyncio.get_event_loop()
        self.real_time_data, self.vehicle_data, self.train_data = await self.cog.load_real_time_data(debug=self.cog.DEBUG, write=self.cog.WRITE)
        self.real_schedule, self.real_stop_times = await event_loop.run_in_executor(None, self.load_real_schedule, self.cog, self.base_schedule, self.base_stop_times)
        if not self.fixed:  # _time:
            prev_today = self.today
            self.now = time.datetime.now(tz=TIMEZONE)
            self.today = self.now.date()
            if prev_today != self.today:
                self.day_offset = (prev_today - self.today).days

    def get_indexes(self, custom_lines: int = None) -> tuple[int, int]:
        """ Get the value of start_idx and end_idx for the output """
        start_idx = 0
        lines = custom_lines or self.lines
        # Set start_idx to the first departure after now
        departure_time_attr = self.departure_time_attr
        for idx, stop_time in enumerate(self.iterable_stop_times):
            if getattr(stop_time, departure_time_attr) >= self.now:
                start_idx = idx
                break
        max_idx = len(self.iterable_stop_times)
        start_idx += self.index_offset
        start_idx = max(0, min(start_idx, max_idx - lines))
        end_idx = min(start_idx + lines, max_idx)
        return start_idx, end_idx

    @property
    def iterable_stop_times(self) -> list[RealStopTime] | list[SpecificStopTime]:
        """ Returns the stop times we can iterate over """
        return self.real_stop_times if self.real_time else self.base_stop_times

    @property
    def departure_time_attr(self) -> str:
        return "available_departure_time" if self.real_time else "departure_time"

    @property
    def data_timestamp(self) -> str:
        """ Returns the timestamp of the real-time data """
        if self.real_time_data:
            return format_timestamp(self.real_time_data.header.timestamp)
        return "Real-time data unavailable"

    def create_output(self):
        """ Create the output from available information and send it to the user """
        # language = languages.Language("en")
        output_data: list[list[str | None]] = [["Route", "Destination", "Sched", "Real", "Bus", "Dist", None, None]]
        column_sizes = [5, 11, 5, 5, 3, 4, 0, 0]  # Longest member of the column
        if self.base_schedule.has_trains:  # Replace "Bus" with "Train" if we are on a train schedule
            output_data[0][4] = "Train"
            column_sizes[4] = 5
        # if self.compact_mode == 2:
        #     output_data[0][3] = "Departure"
        #     column_sizes[3] = 9
        #     for idx in (4, 2):
        #         output_data[0].pop(idx)
        #         column_sizes.pop(idx)
        has_vehicle_info = False
        self.start_idx, self.end_idx = self.get_indexes()
        # iterable_stop_times = self.real_stop_times if self.real_time else self.base_stop_times

        for stop_time in self.iterable_stop_times[self.start_idx:self.end_idx]:
            output_line = format_departure(self, stop_time)
            if output_line[4] not in ("", "-") or output_line[5] not in ("", "-"):
                has_vehicle_info = True
            for i, element in enumerate(output_line):
                column_sizes[i] = max(column_sizes[i], len(element))

            output_data.append(output_line)

        self.empty = len(output_data) == 1
        if self.empty:
            if self.base_schedule.hide_terminating:
                return f"There are no departures from the stop {self.stop.name} on {self.today:%d %B %Y}."
            return f"There are no departures or arrivals at the stop {self.stop.name} on {self.today:%d %B %Y}."

        if column_sizes[2] >= 8:
            output_data[0][2] = "Schedule"
        if column_sizes[3] >= 8:
            output_data[0][3] = "RealTime"
        if column_sizes[5] >= 8:
            output_data[0][5] = "Distance"

        data_end = _end = -2  # Last index with data to show
        skip_idx = []
        # if self.compact_mode == 1:
        #     skip_idx = [_end - 2]  # Hide fleet data
        if self.compact_mode == 2 or not has_vehicle_info:
            data_end = _end - 2  # Hide vehicle and distance data
        if not self.real_time:
            data_end = _end - 3  # Hide real-time, vehicle, distance

        # Calculate the last line first, in case we need more characters for the destination field
        line_length = sum(column_sizes[:data_end]) + len(column_sizes) - 1 + data_end
        cutoff = 0
        skip = column_sizes[0] + 1
        line_length_limit = None
        if self.compact_mode:  # >= 1
            if self.compact_mode == 1:
                line_length_limit = 50
            else:
                line_length_limit = 36
            if line_length > line_length_limit:
                cutoff = column_sizes[1] - (line_length - line_length_limit)  # Max length of the destination to fit the line
                line_length = line_length_limit
        else:
            # If the extra lines are too long, expand the normal lines to fit
            if any(column_sizes[-2:]):  # Only do this if the lines are actually there
                max_length = max(column_sizes[-2:]) + skip
                if max_length > line_length:
                    new_line_length = min(100, max_length)
                    column_sizes[1] += new_line_length - line_length
                    line_length = new_line_length
                    del new_line_length
        extra_line_length = line_length - skip
        spaces = line_length - len(self.stop.name) - 18
        extra = 0
        # Add more spaces to destination if there's too few between stop name and current time
        spaces_requirement = 4 if self.compact_mode else 8
        if spaces < spaces_requirement:
            extra = spaces_requirement - spaces
            spaces = spaces_requirement
        if self.compact_mode and (line_length + extra) > line_length_limit:
            extra = line_length_limit - line_length
            # 23 chars: 18 for time + 4 spaces + 1 for ellipsis
            last_line = f"{self.stop.name[:line_length_limit - 23]}…{' ' * spaces}{self.now:%d %b %Y, %H:%M}```"
        else:
            # Example:   "Ballinacurra Close       23 Oct 2023, 18:00"
            last_line = f"{self.stop.name}{' ' * spaces}{self.now:%d %b %Y, %H:%M}```"
        column_sizes[1] += extra  # [1] is destination
        extra_line_length += extra

        stop_code = f"Code `{self.stop.code}`, " if self.stop.code else ""
        stop_id = f"ID `{self.stop.id}`"
        additional_text = "\n-# D = Drop-off/Alighting only | P = Pick-up/Boarding only\n-# Departure times marked by an asterisk are guesses made by this bot"
        if has_vehicle_info:
            additional_text += "\n-# Distance indicators: Red = Bus already passed stop | Yellow = Bus approaching | Green = Bus not nearby yet"
        if self.real_time:
            additional_text += f"\n-# Real-time data timestamp: {self.data_timestamp}"
        output = f"Real-Time data for the stop {self.stop.name} ({stop_code}{stop_id})\n" \
                 "-# Note: Vehicle locations and distances may not always be accurate" \
                 f"{additional_text}\n```fix\n"

        for line in output_data:
            assert len(column_sizes) == len(line)
            line_data = []
            for i in range(len(line) + data_end):  # Excluding the "actual_destination" and "actual_start"
                if i not in skip_idx:
                    size = column_sizes[i]
                    line_part = line[i]
                    if i == 1 and cutoff:
                        size = cutoff
                        if len(line_part) > cutoff:
                            line_part = line_part[:cutoff - 1] + "…"  # Truncate destination field if necessary
                    # Left-align route and destination to fixed number of spaces
                    # Right-align the schedule, real-time info, and distance
                    alignment = "<" if i < 2 else ">"
                    line_data.append(f"{line_part:{alignment}{size}}")
            output += f"{' '.join(line_data)}\n"
            # If actual_destination and actual_start are not empty, insert them at the line below
            # These lines will start at the Destination field, and can occupy space up to the end of the line
            for i in (-2, -1):
                if line[i]:
                    length = len(line[i])
                    if length > extra_line_length:
                        output += f"{' ' * column_sizes[0]} {line[i][:extra_line_length - 1]}…\n"
                    else:
                        output += f"{' ' * column_sizes[0]} {line[i]}\n"
        output += last_line
        if len(output) > 2000:
            output = output[:2000]
        return output

    def update_output(self):
        self.output = self.create_output()

    def format_time(self, provided_time: time.datetime) -> str:
        """ Format the provided time, showing when a given trip happens outside the current day """
        return format_time(provided_time, self.today)


class HubScheduleViewer:
    """ Shows multiple schedules at once """
    def __init__(self, hub_id: str, stops: list[Stop], now: time.datetime, real_time: bool, fixed: bool, static_data: GTFSData, cog,
                 hide_terminating: bool, user_id: int | None,
                 base_schedules: list[StopSchedule], base_stop_times: list[list[SpecificStopTime]],
                 real_schedules: list[RealTimeStopSchedule] | None, real_stop_times: list[list[RealStopTime]] | None):
        self.static_data: GTFSData = static_data
        self.cog = cog
        self.hub_id: str = hub_id  # Only used for output here
        self.stops: list[Stop] = stops
        self.base_schedules: list[StopSchedule] = base_schedules
        self.base_stop_times: list[list[SpecificStopTime]] = base_stop_times
        self.real_schedules: list[RealTimeStopSchedule] = real_schedules
        self.real_stop_times: list[list[RealStopTime]] = real_stop_times

        self.now: time.datetime = now
        self.base_now: time.datetime = now
        self.today: time.date = now.date()
        self.real_time: bool = real_time
        self.fixed: bool = fixed
        self.hide_terminating: bool = hide_terminating
        self.user_id: int | None = user_id

        self.compact_mode: bool = False
        self.timedelta: time.timedelta = time.timedelta()  # Time-based equivalent to index offsets - only applied automatically for refreshing
        self.day_offset: int = 0    # Not currently used, but left just in case.
        self.lines: int = 4 if len(stops) < 10 else 3  # I don't think I'll ever have 10 or more stops for one hub, but just in case.

        self.indexes = self.get_indexes()
        self.output = self.create_output()

    @classmethod
    async def load(cls, hub_id: str, stops: list[Stop], now: time.datetime | None, hide_terminating: bool, user_id: int | None, static_data: GTFSData, cog):
        """ Load the data and return a working instance """
        # print(f"{time.datetime.now():%d %b %Y, %H:%M:%S} > Started loading hub {hub_id}")
        if now is not None:
            real_time: bool = abs((now - time.datetime.now()).total_microseconds()) < 28_800_000_000
            fixed = True
        else:
            now = time.datetime.now(tz=TIMEZONE)
            real_time = True
            fixed = False
        today = now.date()
        event_loop = asyncio.get_event_loop()
        base_schedules, base_stop_times = await event_loop.run_in_executor(None, cls.load_base_schedules, static_data, stops, today, hide_terminating, user_id)
        # print(f"{time.datetime.now():%d %b %Y, %H:%M:%S} > Loaded base schedules")
        if real_time:
            real_schedules, real_stop_times = await event_loop.run_in_executor(None, cls.load_real_schedules, cog, base_schedules, base_stop_times)
        else:
            real_schedules = real_stop_times = None
        # print(f"{time.datetime.now():%d %b %Y, %H:%M:%S} > Loaded real-time schedules")
        return cls(hub_id, stops, now, real_time, fixed, static_data, cog, hide_terminating, user_id, base_schedules, base_stop_times, real_schedules, real_stop_times)

    @staticmethod
    def load_base_schedules(data: GTFSData, stops: list[Stop], today: time.date, hide_terminating: bool, user_id: int | None):
        base_schedules: list[StopSchedule] = []
        base_stop_times: list[list[SpecificStopTime]] = []
        for stop in stops:
            schedule = StopSchedule(data, stop.id, hide_terminating, user_id)
            base_schedules.append(schedule)
            base_stop_times.append(schedule.relevant_stop_times(today))
            # print(f"{time.datetime.now():%d %b %Y, %H:%M:%S} > Loaded base schedule for stop {stop.name} ({stop.code_or_id})")
        return base_schedules, base_stop_times

    @staticmethod
    def load_real_schedules(cog, base_schedules: list[StopSchedule], base_stop_times: list[list[SpecificStopTime]]):
        real_schedules: list[RealTimeStopSchedule] = []
        real_stop_times: list[list[RealStopTime]] = []
        for schedule, stop_times in zip(base_schedules, base_stop_times):
            real_schedule = RealTimeStopSchedule.from_existing_schedule(schedule, cog.real_time_data, cog.vehicle_data, stop_times)
            real_schedules.append(real_schedule)
            real_stop_times.append(real_schedule.real_stop_times())
            # print(f"{time.datetime.now():%d %b %Y, %H:%M:%S} > Loaded real-time schedule for stop {schedule.stop.name} ({schedule.stop.code_or_id})")
        return real_schedules, real_stop_times

    async def reload(self):
        new_schedule = await self.load(self.hub_id, self.stops, self.now, self.hide_terminating, self.user_id, self.static_data, self.cog)
        new_schedule.fixed = self.fixed
        # new_schedule.real_time = self.real_time
        new_schedule.base_now = self.base_now
        new_schedule.compact_mode = self.compact_mode
        new_schedule.update_output()
        return new_schedule

    async def refresh(self):
        event_loop = asyncio.get_event_loop()
        await self.cog.load_real_time_data(debug=self.cog.DEBUG, write=self.cog.WRITE)
        self.real_schedules, self.real_stop_times = await event_loop.run_in_executor(None, self.load_real_schedules, self.cog, self.base_schedules, self.base_stop_times)
        if not self.fixed:
            prev_today = self.today
            self.now = time.datetime.now(tz=TIMEZONE) + self.timedelta
            self.today = self.now.date()
            if prev_today != self.today:
                self.day_offset += (prev_today - self.today).days

    def get_indexes(self) -> list[tuple[int, int]]:
        """ Get start_idx and end_idx for each schedule """
        outputs = []
        departure_time_attr = self.departure_time_attr
        for stop_times in self.iterable_stop_times:
            start_idx = 0
            for idx, stop_time in enumerate(stop_times):
                if getattr(stop_time, departure_time_attr) >= self.now:
                    start_idx = idx
                    break
            max_idx = len(stop_times)
            start_idx = max(0, min(start_idx, max_idx - self.lines))
            end_idx = min(start_idx + self.lines, max_idx)
            outputs.append((start_idx, end_idx))
        return outputs

    @property
    def iterable_stop_times(self) -> list[list[RealStopTime]] | list[list[SpecificStopTime]]:
        return self.real_stop_times if self.real_time else self.base_stop_times

    @property
    def departure_time_attr(self) -> str:
        return "available_departure_time" if self.real_time else "departure_time"

    @property
    def data_timestamp(self) -> str:
        """ Returns the timestamp of the real-time data """
        if self.cog.real_time_data:
            if len(self.stops) < 9:
                return format_timestamp(self.cog.real_time_data.header.timestamp)
            return f"{self.cog.real_time_data.header.timestamp:%Y-%m-%d %H:%M:%S}"  # The timestamp doesn't fit for 9 stops
        return "Real-time data unavailable"

    def create_output(self):
        if self.real_time:
            output: list[str] = [f"Real-time data for stop hub {self.hub_id}"]
        else:
            output: list[str] = [f"Schedule for stop hub {self.hub_id}"]
        output_data_header: list[str | None] = ["Rt", "Destination", "Sched", "Real"]
        output_data: list[list[list[str | None]]] = []  # output_data[stop][line][column]
        column_sizes: list[int] = [2, 11, 5, 5]
        assert len(output_data_header) == len(column_sizes)
        if len(self.stops) >= 9:  # The text just barely doesn't fit for 9 stops
            line_length_limit = 32
        elif self.compact_mode or len(self.stops) >= 7:
            line_length_limit = 36
        elif len(self.stops) >= 5:
            line_length_limit = 40
        else:
            line_length_limit = 45

        self.indexes = self.get_indexes()
        empty_stops = set()  # Stops that do not have any departures on the day
        header_set = False   # In case the first stop has no departures

        for i, stop_times in enumerate(self.iterable_stop_times):
            if not stop_times:
                empty_stops.add(i)
                output_data.append([])
            else:
                start_idx, end_idx = self.indexes[i]
                output_stop: list[list[str | None]] = [output_data_header] if not header_set else []
                header_set = True
                for stop_time in stop_times[start_idx:end_idx]:
                    output_line = format_departure(self, stop_time)
                    for j, element in enumerate(output_line):
                        column_sizes[j] = max(column_sizes[j], len(element))
                    output_stop.append(output_line)
                output_data.append(output_stop)

        data_end = 0
        if not self.real_time:
            data_end = -1
            output_data_header[2] = "Depart"
            column_sizes[2] = max(column_sizes[2], 6)
            column_sizes[3] = 0
        if 3 <= column_sizes[0] < 5:
            output_data_header[0] = "Rte"
        elif column_sizes[0] >= 5:
            output_data_header[0] = "Route"

        line_length = sum(column_sizes) + len(column_sizes) - 1 + data_end
        if line_length > line_length_limit:
            column_sizes[1] = column_sizes[1] - (line_length - line_length_limit)
            # line_length = line_length_limit
        # print(line_length, line_length_limit, *column_sizes)

        for stop, stop_data in zip(self.stops, output_data):  # type: Stop, list[list[str | None]]
            stop_code = f"Code `{stop.code}`, " if stop.code else ""
            stop_id = f"ID `{stop.id}`"
            stop_output = [f"Data for stop {stop.name} ({stop_code}{stop_id})", "```fix"]
            for line in stop_data:
                line_data = []
                for i in range(len(line) + data_end):
                    size = column_sizes[i]
                    line_part = line[i]
                    # print(i, size, len(line_part))
                    if i == 1 and len(line_part) > size:
                        line_part = line_part[:size - 1] + "…"
                    alignment = "<" if i < 2 else ">"
                    line_data.append(f"{line_part:{alignment}{size}}")
                stop_output.append(" ".join(line_data))
            if len(stop_output) == 2:
                output.append(f"There are no departures from stop {stop.name} ({stop_code}{stop_id}) on {self.today:%d %B %Y}.\n")
            else:
                stop_output.append("```")
                output.append("\n".join(stop_output))

        output.append(f"-# Showing departures after {self.now:%d %b %Y, %H:%M}")
        if self.real_time:
            output.append(f"-# Real-time data timestamp: {self.data_timestamp}")
        output_str = "\n".join(output)
        if len(output_str) > 2000:
            output_str = output_str[:2000]
        return output_str

    def update_output(self):
        self.output = self.create_output()

    def format_time(self, provided_time: time.datetime) -> str:
        return format_time(provided_time, self.today)


class TripDiagramViewer:
    """ Viewer for a route diagram of an existing trip (called from a select menu in the StopScheduleView) """

    def __init__(self, original_view, trip_id: str):
        # I don't think the StopScheduleView and -Viewer should be stored as attrs
        # self.original_view = original_view  # views.StopScheduleView
        stop_schedule: StopScheduleViewer = original_view.viewer
        self.static_data = stop_schedule.static_data
        self.stop = stop_schedule.stop
        # self.fixed = stop_schedule.fixed  # Do we even need this here?
        self.cog = stop_schedule.cog
        self.real_time_data: GTFSRData = self.cog.real_time_data
        self.vehicle_data: VehicleData = self.cog.vehicle_data
        self.train_data: dict[str, Train] = self.cog.train_data
        self.is_real_time = stop_schedule.real_time

        self.static_trip: Trip | None = None
        self.real_trip: TripUpdate | None = None
        self.is_real_time_train: bool = False  # Whether the train has real-time info (in case it is available here but not on GTFS)
        self.trip_identifier: str = trip_id
        self.cancelled: bool = False
        self.vehicle_id: str | None = None
        # _type = 0
        static_trip_id, real_trip_id, _day_modifier = trip_id.split("|")
        if static_trip_id:
            self.static_trip: Trip = load_value(self.static_data, Trip, static_trip_id)
            self.is_real_time_train = self.static_trip.short_name in self.train_data
            # _type += 1
        if real_trip_id:
            self.real_trip: TripUpdate = self.real_time_data.entities[real_trip_id]
            self.cancelled = self.real_trip.trip.schedule_relationship == "CANCELED"
            self.vehicle_id = self.real_trip.vehicle_id
            # _type += 2
        # self.type: int = _type
        # self.type_name: str = ("static", "added", "real")[_type - 1]

        self.timedelta = time.timedelta(days=int(_day_modifier) + stop_schedule.day_offset)
        if stop_schedule.fixed:
            self.now = stop_schedule.now
            self.today = stop_schedule.today
        else:
            prev_today = stop_schedule.today
            self.now = time.datetime.now(tz=TIMEZONE)
            self.today = self.now.date()
            if prev_today != self.today:
                self.timedelta += prev_today - self.today

        self.compact_mode: int = stop_schedule.compact_mode  # 0 -> disabled | 1 -> shorter stop names | 2 -> mobile-friendly mode
        self.current_stop_page: int | None = None
        self.route = self.get_route()
        self.is_train: bool = self.route.route_type == 2  # Whether we are dealing with a train

        # Attributes for the output generator
        self.skipped: set[int] = set()
        self.pickup_only: set[int] = set()
        self.drop_off_only: set[int] = set()
        self.stops: list[Stop] = []
        self.arrivals: list[time.datetime] = []
        self.departures: list[time.datetime] = []
        self.total_stops: int = -1
        self.get_output_values()
        self.output = self.create_output()

    @property
    def trip(self) -> Trip | TripUpdate:
        """ Returns the available trip data (used for the vehicle data part of the output) """
        return self.static_trip or self.real_trip

    def get_route(self) -> Route | None:
        try:
            if self.static_trip:
                return self.static_trip.route(self.static_data)
            return load_value(self.static_data, Route, self.real_trip.trip.route_id)
        except KeyError:
            return None

    async def refresh_real_time_data(self):
        self.real_time_data, self.vehicle_data, self.train_data = await self.cog.load_real_time_data(debug=self.cog.DEBUG, write=self.cog.WRITE)  # type: GTFSRData, VehicleData, dict[str, Train]
        if self.real_trip or self.is_real_time:
            # Find new real-time information about this trip
            real_trip = None
            if not self.static_trip:  # Added trip
                for entity in self.real_time_data.added.values():
                    trip_update = entity.trip
                    current_trip = self.real_trip.trip
                    if trip_update.route_id == current_trip.route_id and \
                            trip_update.start_time == current_trip.start_time and \
                            trip_update.direction_id == current_trip.direction_id:
                        real_trip = entity
                        break
            else:
                real_trip = self.real_time_data.scheduled.get(self.static_trip.trip_id)
                # for entity in self.real_time_data.entities.values():
                #     if entity.trip.trip_id == self.static_trip.trip_id:
                #         real_trip = entity
                #         break
            if real_trip:
                self.real_trip = real_trip
                self.cancelled = self.real_trip.trip.schedule_relationship == "CANCELED"
        # if not self.fixed:
        prev_today = self.today
        self.now = time.datetime.now(tz=TIMEZONE)
        self.today = self.now.date()
        if prev_today != self.today:
            self.timedelta += prev_today - self.today
        self.get_output_values()  # Update the values with the new real-time data

    @property
    def data_timestamp(self) -> str:
        """ Returns the timestamp of the real-time data """
        if self.real_trip:
            return format_timestamp(self.real_trip.timestamp)
        if self.real_time_data:
            return format_timestamp(self.real_time_data.header.timestamp)
        return "Real-time data unavailable"

    def get_output_values(self):
        """ Sets the values for stop time-related values used in the output generator

        Values set:
         - Set of skipped stops
         - Set of pick up-only stops
         - Set of drop off-only stops
         - List of all stops for the trip
         - List of arrival times at each stop
         - List of departure times at each stop
        """
        self.skipped: set[int] = set()
        self.pickup_only: set[int] = set()
        self.drop_off_only: set[int] = set()
        self.stops: list[Stop] = []
        self.arrivals: list[time.datetime] = []
        self.departures: list[time.datetime] = []

        def get_stop_times():
            _total_stops = self.static_trip.total_stops
            _trip_id = self.static_trip.trip_id
            base_stop_times: list[StopTime] = []
            if _trip_id in self.static_data.stop_times:
                _stop_times = self.static_data.stop_times[_trip_id].values()
                if len(_stop_times) == _total_stops:
                    base_stop_times = list(_stop_times)
                del _stop_times
            if not base_stop_times:
                base_stop_times = StopTime.from_sql(_trip_id)
                for _stop_time in base_stop_times:
                    if _trip_id not in self.static_data.stop_times:
                        self.static_data.stop_times[_trip_id] = {}
                    self.static_data.stop_times[_trip_id][_stop_time.stop_id] = _stop_time
            # Apparently they need to be sorted because they may somehow come out in the wrong order
            return sorted([SpecificStopTime(_stop_time, self.today + self.timedelta) for _stop_time in base_stop_times], key=lambda st: st.sequence)

        if self.is_train:
            # This assumes that added trips won't happen on Irish rail, which is hopefully the case.
            self.total_stops = self.static_trip.total_stops
            stop_times = get_stop_times()
            movements: list[TrainMovement] = []
            if self.is_real_time:
                trip_code = self.static_trip.short_name
                nest_asyncio.apply()
                # TODO: Implement some caching logic to only request this once per minute | Write this to a file for debug
                movements = asyncio.get_event_loop().run_until_complete(asyncio.create_task(fetch_train_movements(trip_code, self.today + self.timedelta)))
                # Sanity check: discard real-time trip data if we got the wrong information
                # TODO: Discard real-time if we become aware that the data isn't real and don't look up again
                if TRAIN_STATION_CODE_TO_ID.get(movements[0].location_code) != stop_times[0].stop_id or movements[0].scheduled_departure != stop_times[0].departure_time:
                    movements = []
            if movements:
                stops = 0
                for movement in movements:
                    if movement.location_type == "T":  # Ignore transit stops
                        continue
                    stop_id = TRAIN_STATION_CODE_TO_ID.get(movement.location_code)
                    if stop_id:
                        self.arrivals.append(movement.actual_arrival or movement.expected_arrival)
                        self.departures.append(movement.actual_departure or movement.expected_departure)
                        self.stops.append(load_value(self.static_data, Stop, stop_id, None))
                        if movement.location_type == "O":  # Origin is pick-up only
                            self.pickup_only.add(stops)
                        elif movement.location_type == "D":  # Destination is drop-off only
                            self.drop_off_only.add(stops)
                        elif movement.location_type == "C":
                            self.skipped.add(stops)
                        stops += 1

                if self.arrivals[0] > self.departures[0]:
                    minimum_delay = self.departures[0] - self.arrivals[0]
                    self.departures[0] = self.arrivals[0]
                    for i in range(1, stops + 1):
                        self.arrivals[i] += minimum_delay
                        self.departures[i] += minimum_delay
                # If the amount of total stops somehow differs from the expected amount, update it
                self.total_stops = stops
            else:
                for stop_time in stop_times:
                    self.arrivals.append(stop_time.arrival_time)
                    self.departures.append(stop_time.departure_time)
                    self.stops.append(stop_time.stop(self.static_data))
                    if stop_time.pickup_type == 1:
                        self.drop_off_only.add(stop_time.sequence - 1)
                    elif stop_time.drop_off_type == 1:
                        self.pickup_only.add(stop_time.sequence - 1)
        else:
            if self.real_trip and not self.cancelled:
                def extend_list(iterable: list, _repetitions: int):
                    if _repetitions > 0:
                        iterable.extend([iterable[-1]] * _repetitions)

                prev_sequence: int = 0
                real_time_statuses: list[bool] = []  # True = stop served | False = stop skipped
                arrival_delays: list[time.timedelta] = []
                departure_delays: list[time.timedelta] = []
                custom_arrival_times: dict[int, time.datetime] = {}
                custom_departure_times: dict[int, time.datetime] = {}
                for stop_time_update in self.real_trip.stop_times:
                    sequence: int = stop_time_update.stop_sequence
                    repetitions: int = sequence - prev_sequence - 1
                    is_skipped = stop_time_update.schedule_relationship == "SKIPPED"
                    if prev_sequence == 0:
                        if sequence > 1:
                            arrival_delays.extend([time.timedelta()] * repetitions)
                            departure_delays.extend([time.timedelta()] * repetitions)
                            real_time_statuses.extend([not is_skipped] * repetitions)
                        repetitions = 0
                    extend_list(real_time_statuses, repetitions)
                    extend_list(departure_delays, repetitions)
                    real_time_statuses.append(not is_skipped)
                    if is_skipped:
                        departure_delays.append(departure_delays[-1])
                        if repetitions > 0:
                            arrival_delays.append(departure_delays[prev_sequence - 1])
                            extend_list(arrival_delays, repetitions - 1)
                        arrival_delays.append(arrival_delays[-1])
                    else:
                        departure_delays.append(stop_time_update.departure_delay)
                        if repetitions > 0:
                            arrival_delays.append(departure_delays[prev_sequence - 1])
                            extend_list(arrival_delays, repetitions - 1)
                        arrival_delays.append(stop_time_update.arrival_delay)
                    if stop_time_update.arrival_time is not None:
                        custom_arrival_times[sequence] = stop_time_update.arrival_time
                    if stop_time_update.departure_time is not None:
                        custom_departure_times[sequence] = stop_time_update.departure_time
                    prev_sequence = sequence
                if self.static_trip:
                    self.total_stops = self.static_trip.total_stops
                    remaining = self.total_stops - len(real_time_statuses)
                    extend_list(real_time_statuses, remaining)
                    if remaining > 0:
                        arrival_delays.append(departure_delays[-1])
                        extend_list(arrival_delays, remaining - 1)
                    elif arrival_delays[-1] is None:
                        arrival_delays[-1] = departure_delays[-1]
                    if departure_delays[-1] is None:
                        if remaining > 0:
                            departure_delays.append(arrival_delays[-1])
                            extend_list(departure_delays, remaining - 1)
                        else:
                            departure_delays[-1] = arrival_delays[-1]
                    else:
                        extend_list(departure_delays, remaining)
                    stop_times = get_stop_times()
                    for stop_time in stop_times:
                        sequence = stop_time.sequence
                        index = sequence - 1
                        if sequence in custom_arrival_times:
                            self.arrivals.append(custom_arrival_times[sequence])
                        else:
                            arrival_delay = arrival_delays[index]
                            if arrival_delay is None:
                                arrival_delay = time.timedelta()
                            self.arrivals.append(stop_time.arrival_time + arrival_delay)
                        if sequence in custom_departure_times:
                            self.departures.append(custom_departure_times[sequence])
                        else:
                            departure_delay = departure_delays[index]
                            if departure_delay is None:
                                departure_delay = time.timedelta()
                            self.departures.append(stop_time.departure_time + departure_delay)
                        self.stops.append(stop_time.stop(self.static_data))
                        if stop_time.pickup_type == 1:
                            self.drop_off_only.add(sequence - 1)
                        elif stop_time.drop_off_type == 1:
                            self.pickup_only.add(sequence - 1)
                    for idx in range(len(real_time_statuses)):
                        if not real_time_statuses[idx]:
                            self.skipped.add(idx)
                else:
                    self.total_stops = len(real_time_statuses)
                    for sequence in range(1, self.total_stops + 1):
                        self.arrivals.append(custom_arrival_times.get(sequence, None))
                        self.departures.append(custom_departure_times.get(sequence, None))
                    for stop_time in self.real_trip.stop_times:
                        self.stops.append(load_value(self.static_data, Stop, stop_time.stop_id))
            else:
                self.total_stops = self.static_trip.total_stops
                stop_times = get_stop_times()
                for stop_time in stop_times:
                    self.arrivals.append(stop_time.arrival_time)
                    self.departures.append(stop_time.departure_time)
                    self.stops.append(stop_time.stop(self.static_data))
                    if stop_time.pickup_type == 1:
                        self.drop_off_only.add(stop_time.sequence - 1)
                    elif stop_time.drop_off_type == 1:
                        self.pickup_only.add(stop_time.sequence - 1)

            # Fix arrival and departure times: if the next stop is left before the previous one, mark all previous stops as already departed from
            for idx in range(self.total_stops - 1, 1, -1):
                arr_time, dep_time = self.arrivals[idx], self.departures[idx]
                if arr_time is None:
                    arr_time = time.datetime().min
                if dep_time is None:
                    dep_time = time.datetime().max
                if dep_time < arr_time:
                    self.arrivals[idx] = arr_time = dep_time

                prev_arr_time = self.arrivals[idx - 1]
                if prev_arr_time is None:
                    prev_arr_time = time.datetime().min
                prev_dep_time = self.departures[idx - 1]
                if prev_dep_time is None:
                    prev_dep_time = time.datetime().min
                if prev_dep_time > arr_time or prev_arr_time > arr_time:
                    self.arrivals[idx - 1] = self.departures[idx - 1] = arr_time

    def create_output(self) -> paginators.LinePaginator:
        output_data: list[list[str]] = [["Seq", "Code", "Stop Name", "Arrival", "Departure"]]
        column_sizes: list[int] = [3, 4, 9, 9, 9]
        alignments: list[str] = ["<", ">", "<", ">", ">"]
        stop_name_idx = 2
        if self.compact_mode:  # >= 1
            output_data[0][3] = "Arr"
            output_data[0][4] = "Dep"
            column_sizes[3] = column_sizes[4] = 5
        if self.compact_mode == 2:
            # Remove the arrival time (3) and the stop code (1)
            for idx in (3, 1):
                output_data[0].pop(idx)
                column_sizes.pop(idx)
                alignments.pop(idx)
            stop_name_idx = 1

        # This is used in the for loop below
        def add_letter(ltr: str):
            if self.compact_mode == 2:
                nonlocal departure
                departure = ltr + departure
            else:
                nonlocal arrival
                arrival = ltr + arrival

        current_stop_marked: bool = False
        fill = len(str(self.total_stops))
        for idx in range(self.total_stops):
            seq = f"{idx + 1:0{fill}d})"
            stop = self.stops[idx]
            code = stop.code_or_id
            name = stop.name

            _arrival = self.arrivals[idx]
            if _arrival is not None:
                arrival = self.format_time(_arrival)
            else:
                arrival = "  N/A"
                _arrival = time.datetime().min

            _departure = self.departures[idx]
            if _departure is not None:
                departure = self.format_time(_departure)
            else:
                departure = "  N/A"
                _departure = time.datetime().max

            if idx in self.pickup_only:
                add_letter("P ")
            elif idx in self.drop_off_only:
                add_letter("D ")

            if self.cancelled:
                emoji = CANCELLED
            elif idx in self.skipped:
                emoji = WARNING
                departure = "Skipped"
            elif not current_stop_marked and (self.now < _arrival or self.now < _departure):
                route_types = {0: "🚈", 1: "🚇", 2: "🚄", 3: "🚌", 4: "🚢", 5: "🚠", 6: "🚟", 7: "🚟", 11: "🚎", 12: "🚝"}
                emoji = f"{route_types.get(self.route.route_type, '🚌')}\u2060 "
                current_stop_marked = True
            elif self.stop.id == stop.id:
                emoji = "➡️ "
            else:
                emoji = ""

            if self.compact_mode == 2:
                output_line = [seq, emoji + name, departure]
            else:
                output_line = [seq, code, emoji + name, arrival, departure]

            for i, element in enumerate(output_line):
                column_sizes[i] = max(column_sizes[i], len(element))

            output_data.append(output_line)

        if self.cancelled:
            note = f"\n{WARNING}Note: This trip was cancelled."
        elif self.real_trip and not self.static_trip:  # Added trip
            note = f"\n{WARNING}Note: This trip was not scheduled."
        elif self.static_trip and not (self.real_trip or self.is_real_time_train):  # Static trip
            note = "\nNote: This trip has no real-time information."
        else:
            note = ""

        extra_text = ""
        if self.pickup_only or self.drop_off_only:
            extra_text = "\n-# D = Drop-off/Alighting only | P = Pick-up/Boarding only"

        if self.is_real_time:
            extra_text += f"\n-# Real-time data timestamp: {self.data_timestamp}"

        if self.static_trip:
            trip_id = self.static_trip.trip_id
            destination = self.static_trip.headsign
            route = f"Route {self.route.short_name}"
        else:
            trip_id = self.real_trip.entity_id
            destination = self.stops[-1].name
            if self.route:
                route = f"Route {self.route.short_name}"
            else:
                route = "Unknown route"

        if self.real_trip or self.is_real_time_train:
            bus_data = get_vehicle_data(self)
            if bus_data:
                extra_text += "\n\n" + bus_data

        line_length = sum(column_sizes) + len(column_sizes) - 1
        spaces = line_length - len(self.stop.name) - 18
        extra = 0
        # Add more spaces to destination if there's too few between stop name and current time
        if spaces < 8:
            extra = 8 - spaces
            spaces = 8
        column_sizes[stop_name_idx] += extra
        line_length += extra
        # cutoff = column_sizes[2]
        output_end = f"{self.stop.name}{' ' * spaces}{self.now:%d %b %Y, %H:%M}```"

        def update_output_end(stop_name_length: int):
            nonlocal output_end
            if len(self.stop.name) > stop_name_length:
                output_end = f"{self.stop.name[:stop_name_length - 1]}…{' ' * 4}{self.now:%d %b %Y, %H:%M}```"
            else:
                _spaces = line_length_limit - len(self.stop.name) - 18
                output_end = f"{self.stop.name}{' ' * _spaces}{self.now:%d %b %Y, %H:%M}```"

        if self.compact_mode == 1 and line_length > (line_length_limit := 50):
            column_sizes[2] = column_sizes[2] - (line_length - line_length_limit)
            update_output_end(line_length_limit - 18 - 4)
        elif self.compact_mode == 2 and line_length > (line_length_limit := 36):
            column_sizes[1] = column_sizes[1] - (line_length - line_length_limit)  # Stop name is now [1] because the stop code is removed
            update_output_end(line_length_limit - 18 - 4)

        def generate_line(_line: list[str]):
            line_data = []
            for _i in range(len(_line)):
                size = column_sizes[_i]
                line_part = _line[_i]
                if len(line_part) > size:
                    line_data.append(f"{line_part[:size - 1]}…")  # Text cut off
                else:
                    alignment = alignments[_i]
                    line_data.append(f"{line_part:{alignment}{size}}")
            return " ".join(line_data).rstrip()

        first_line = generate_line(output_data[0])
        output_start = f"All stops for Trip {trip_id} to {destination} ({route}){note}{extra_text}\n```fix\n{first_line}"

        paginator = paginators.LinePaginator(prefix=output_start, suffix=output_end, max_lines=PAGINATOR_MAX_LINES, max_size=PAGINATOR_MAX_LENGTH)
        for idx, line in enumerate(output_data[1:], start=0):
            assert len(column_sizes) == len(line)
            paginator.add_line(generate_line(line))
            if self.stops[idx].id == self.stop.id:
                self.current_stop_page = len(paginator.pages) - 1
        return paginator

    def update_output(self):
        self.output = self.create_output()

    def format_time(self, provided_time: time.datetime) -> str:
        """ Format the provided time, showing when a given trip happens outside the current day """
        return format_time(provided_time, self.today)


class TripMapViewer:
    """ Map viewer for the trip diagram """
    def __init__(self, image: io.BytesIO, viewer: TripDiagramViewer, zoom: int):
        self.image: io.BytesIO = image
        self.zoom: int = zoom
        self.custom_zoom: int | None = None
        self.original_viewer: TripDiagramViewer = viewer
        self.trip: Trip | TripUpdate = viewer.static_trip or viewer.real_trip
        self.real_trip: TripUpdate | None = viewer.real_trip
        self.is_real_time_train: bool = viewer.is_real_time_train
        self.trip_id: str = viewer.trip_identifier
        self.stop: Stop = viewer.stop
        self.cog = viewer.cog
        self.static_data: GTFSData = viewer.cog.static_data
        self.real_time_data: GTFSRData = viewer.cog.real_time_data
        self.vehicle_data: VehicleData = viewer.cog.vehicle_data
        self.train_data: dict[str, Train] = viewer.cog.train_data
        self.vehicle_id: str | None = viewer.vehicle_id
        self.cancelled: bool = viewer.cancelled
        self.skipped: set[int] = viewer.skipped
        self.pickup_only: set[int] = viewer.pickup_only
        self.drop_off_only: set[int] = viewer.drop_off_only
        self.stops: list[Stop] = viewer.stops
        self.arrivals: list[time.datetime] = viewer.arrivals
        self.departures: list[time.datetime] = viewer.departures
        self.total_stops: int = viewer.total_stops
        self.output: str = self.create_output()

    @classmethod
    async def load(cls, viewer: TripDiagramViewer):
        departures = viewer.departures.copy()
        if departures[-1] is None:
            departures[-1] = viewer.arrivals[-1]
        args = (viewer.stop, viewer.cog.static_data, viewer.cog.vehicle_data, viewer.cog.fleet_data, viewer.cog.train_data,
                departures, viewer.drop_off_only, viewer.pickup_only, viewer.skipped, viewer.cancelled)
        if viewer.static_trip:
            image_bio, zoom = await get_trip_diagram(viewer.static_trip, *args)
        else:
            image_bio, zoom = await get_trip_diagram(viewer.real_trip, *args)
        return cls(image_bio, viewer, zoom)
        # image_bio = await get_trip_diagram(trip, stop, cog.static_data, cog.vehicle_data)
        # return cls(cog, image_bio, trip, stop, trip_diagram_viewer)

    @property
    def zoom_level(self) -> int:
        return self.custom_zoom or self.zoom

    @zoom_level.setter
    def zoom_level(self, zoom_level: int):
        self.custom_zoom = zoom_level
        if self.custom_zoom == self.zoom:
            self.custom_zoom = None

    @property
    def attachment(self) -> tuple[discord.File]:
        """ The Discord attachment with the map image """
        return (discord.File(self.image, f"{self.trip_id.replace("|", "_")}.png"),)

    async def refresh(self):
        """ Refresh the map with new data """
        # _, self.vehicle_data = await self.cog.load_real_time_data(debug=self.cog.DEBUG, write=self.cog.WRITE)
        await self.original_viewer.refresh_real_time_data()
        self.real_time_data = self.original_viewer.real_time_data
        self.vehicle_data = self.original_viewer.vehicle_data
        self.train_data = self.original_viewer.train_data
        self.real_trip = self.original_viewer.real_trip
        if isinstance(self.trip, TripUpdate):
            self.trip = self.original_viewer.real_trip
        self.skipped: set[int] = self.original_viewer.skipped
        self.pickup_only: set[int] = self.original_viewer.pickup_only
        self.drop_off_only: set[int] = self.original_viewer.drop_off_only
        self.arrivals: list[time.datetime] = self.original_viewer.arrivals
        self.departures: list[time.datetime] = self.original_viewer.departures.copy()
        if self.departures[-1] is None:
            self.departures[-1] = self.arrivals[-1]
        await self.update_map()
        self.update_output()

    async def update_map(self):
        """ Update the map output without refreshing the vehicle data """
        self.image, _ = await get_trip_diagram(self.trip, self.stop, self.cog.static_data, self.cog.vehicle_data, self.cog.fleet_data, self.cog.train_data,
                                               self.departures, self.drop_off_only, self.pickup_only, self.skipped, self.cancelled, self.custom_zoom)

    @property
    def data_timestamp(self) -> str:
        """ Returns the timestamp of the vehicle data """
        if self.real_trip:
            return format_timestamp(self.real_trip.timestamp)
        if self.real_time_data:
            return format_timestamp(self.real_time_data.header.timestamp)
        return "Real-time data unavailable"

    def create_output(self) -> str:
        """ Create the text part of the output """
        if isinstance(self.trip, Trip):
            trip_id = self.trip.trip_id
        else:
            trip_id = self.trip.entity_id
        output = (f"Map overview of Trip {trip_id}\n"
                  "-# Stop colours: Blue = current stop | Yellow = pick up only | Orange = drop off only | Green = regular stop | Red = skipped stop\n"
                  f"-# Real-time data timestamp: {self.data_timestamp}")
        if self.vehicle_id or self.is_real_time_train:
            bus_data = get_vehicle_data(self)
            if bus_data:
                output += "\n\n" + bus_data
        return output

    def update_output(self):
        self.output = self.create_output()


class MapViewer:
    """ Viewer for the map around a bus stop """
    def __init__(self, cog, image: io.BytesIO, stop: Stop, zoom: int = DEFAULT_ZOOM):
        self.cog = cog
        self.static_data: GTFSData = cog.static_data
        # self.vehicle_data: VehicleData = cog.vehicle_data
        # self.train_data: dict[str, Train] = cog.train_data
        self.stop: Stop = stop
        self.lat: float = stop.latitude
        self.lon: float = stop.longitude
        self.zoom: int = zoom
        self.image: io.BytesIO = image
        self.output: str = self.create_output()

    @classmethod
    async def load(cls, cog, stop: Stop, zoom: int = DEFAULT_ZOOM):
        image_bio = await get_map_with_buses(stop.latitude, stop.longitude, zoom, cog.vehicle_data, cog.static_data, cog.fleet_data, cog.train_data)
        return cls(cog, image_bio, stop, zoom)

    @property
    def attachment(self) -> tuple[discord.File]:
        """ The Discord attachment with the map image """
        return (discord.File(self.image, f"{self.stop.id}.png"),)

    async def refresh(self):
        """ Refresh the map with new data """
        # _, self.vehicle_data =
        await self.cog.load_real_time_data(debug=self.cog.DEBUG, write=self.cog.WRITE)
        await self.update_map()
        self.update_output()

    async def update_map(self):
        """ Update the map output without refreshing the vehicle data """
        self.image = await get_map_with_buses(self.stop.latitude, self.stop.longitude, self.zoom, self.cog.vehicle_data, self.cog.static_data, self.cog.fleet_data, self.cog.train_data)

    @property
    def data_timestamp(self) -> str:
        """ Returns the timestamp of the vehicle data """
        return format_timestamp(self.cog.vehicle_data.header.timestamp)

    def create_output(self) -> str:
        """ Create the text part of the output """
        stop_code = f"Code `{self.stop.code}`, " if self.stop.code else ""
        stop_id = f"ID `{self.stop.id}`"
        output = (f"Buses currently near the stop {self.stop.name} ({stop_code}{stop_id})\n"
                  "The blue circle represents your stop's location, while the green rectangles represent the buses.\n"
                  f"-# Vehicle data timestamp: {self.data_timestamp}\n"
                  "-# Note: This only shows vehicles whose location is tracked by TFI's real-time data. A vehicle may not show up on this map despite being there in reality.\n"
                  "-# Note: The direction displayed on the map may sometimes be inaccurate.")
        return output

    def update_output(self):
        self.output = self.create_output()


class VehicleDataViewer:
    """ Shows data about a specific vehicle """
    # This view doesn't require any hard calculations to initialise, so we don't need a load method
    def __init__(self, cog, vehicle: FleetVehicle):
        self.cog = cog
        self.static_data: GTFSData = cog.static_data
        self.real_time_data: GTFSRData = cog.real_time_data
        self.vehicle_data: VehicleData = cog.vehicle_data
        self.fleet_vehicle: FleetVehicle = vehicle
        self.real_time_vehicle: Vehicle | None = self.vehicle_data.vehicles.get(vehicle.vehicle_id)
        self.db = get_database()
        self.output: str = self.create_output()

    async def refresh(self):
        """ Refresh the map with new data """
        self.real_time_data, self.vehicle_data, _ = await self.cog.load_real_time_data(debug=self.cog.DEBUG, write=self.cog.WRITE)
        self.real_time_vehicle = self.vehicle_data.vehicles.get(self.fleet_vehicle.vehicle_id, self.real_time_vehicle)
        self.update_output()

    @property
    def data_timestamp(self) -> str:
        """ Returns the timestamp of the vehicle data """
        if self.real_time_vehicle:
            return format_timestamp(self.real_time_vehicle.timestamp)
        if self.vehicle_data:
            return format_timestamp(self.vehicle_data.header.timestamp)
        return "Vehicle data unavailable"

    def create_output(self) -> str:
        header = (f"Data about vehicle {self.fleet_vehicle.fleet_number}\n\n"
                  f"API ID: {self.fleet_vehicle.vehicle_id}\n"
                  f"Fleet Number: {self.fleet_vehicle.fleet_number}\n"
                  f"Reg plates: {self.fleet_vehicle.reg_plates}\n"
                  f"Model: {self.fleet_vehicle.model}\n"
                  f"Notable features: {self.fleet_vehicle.trivia}")
        if not self.real_time_vehicle:
            vehicle_data = "Real-time data about this vehicle is currently unavailable."
        else:
            real_trip = self.real_time_vehicle.trip
            unknown_trip = False
            try:
                static_trip: Trip | None = load_value(self.static_data, Trip, real_trip.trip_id, self.db)
                _route = static_trip.route(self.static_data, self.db)
                if _route:
                    route = f"Route {_route.short_name}"
                else:
                    route = f"Unknown route {static_trip.route_id}"
                trip_info = f"Current trip: {real_trip.start_time:%H:%M} to {static_trip.headsign} on {route}"
            except KeyError:  # Added trip or other trip
                static_trip = None
                try:
                    _route = load_value(self.static_data, Route, real_trip.route_id, self.db)
                    route = f"Route {_route.short_name}"
                except KeyError:
                    route = f"Unknown route {real_trip.route_id}"
                stop_times = None
                for real_time_trip in self.real_time_data.entities.values():
                    trip_update = real_time_trip.trip
                    if trip_update.start_time == real_trip.start_time and \
                            trip_update.route_id == real_trip.route_id and \
                            trip_update.direction_id == real_trip.direction_id:
                        stop_times = real_time_trip.stop_times
                        break
                # Only do this for added trips - scheduled trips that have an invalid ID should get marked as unknown
                if real_trip.schedule_relationship == "ADDED" and stop_times:
                    try:
                        last_stop: Stop = load_value(self.static_data, Stop, stop_times[-1].stop_id, self.db)
                        destination = f"{last_stop.name} (stop {last_stop.code_or_id})"
                    except KeyError:
                        destination = f"Unknown stop {stop_times[-1].stop_id}"
                    trip_info = f"Currently trip: Unscheduled {real_trip.start_time:%H:%M} to {destination} on {route}"
                else:
                    unknown_trip = True
                    trip_info = f"Currently trip: Unknown trip {real_trip.trip_id}, departed terminus at {real_trip.start_time:%H:%M} on {route}"
            if self.real_time_vehicle.latitude == 0 or self.real_time_vehicle.longitude == 0:
                location = "The bus's current location is unavailable."
            elif unknown_trip:
                def deg_m_s(deg: float):
                    m, s = divmod(abs(deg)*3600, 60)
                    d, m = divmod(m, 60)
                    return f"{int(d)}° {int(m):02d}' {int(s):02d}\""

                latitude = deg_m_s(self.real_time_vehicle.latitude)
                longitude = deg_m_s(self.real_time_vehicle.longitude)
                location = f"The bus is currently at the coordinates {latitude} N, {longitude} W."  # Assume this is always the case, since we are in Ireland
            else:
                # I don't think it's possible to guess the stop here, since we have a RealTimeTrip rather than a TripUpdate
                nearest_stop = get_nearest_stop(static_trip, self.real_time_vehicle, self.static_data)
                location = f"The bus is currently near the stop {nearest_stop.name} (stop {nearest_stop.code_or_id})."
            current_trip = f"{trip_info}\n{location}"
            vehicle_data = current_trip  # Fallback for unavailable static Trip data or block data
            if static_trip:
                # This uses the vehicle's trip's start_date to account for trips that started yesterday (or belong to yesterday)
                prev_trips, next_trips = get_prev_next_trips(static_trip, self.real_time_vehicle.trip.start_date, self.static_data, self.db)
                output_data = [current_trip]

                def format_trip(_departure: time.datetime, _route: str, _destination: str):
                    return f"- {_departure:%H:%M} to {_destination} ({_route})"

                # Show up to 10 previous trips and up to 10 future trips
                if prev_trips:
                    _s = "s" if len(prev_trips) > 1 else ""
                    prev_trips_str = f"Previous trip{_s}:\n" + "\n".join(format_trip(departure, route, destination) for _, departure, route, destination in prev_trips[-10:])
                    output_data.append(prev_trips_str)
                if next_trips:
                    _s = "s" if len(next_trips) > 1 else ""
                    next_trips_str = f"Upcoming trip{_s}:\n" + "\n".join(format_trip(departure, route, destination) for _, departure, route, destination in next_trips[:10])
                    output_data.append(next_trips_str)
                vehicle_data = "\n\n".join(output_data)
        timestamp = f"\n-# Vehicle data timestamp: {self.data_timestamp}" if self.vehicle_data else ""
        link = f"https://bustimes.org/vehicles/ie-{self.fleet_vehicle.vehicle_id}"
        notice = ("-# Note: This data is based on the bus's current real-time data. The list of past and future journeys is based on the current trip (if that data is available at all).\n"
                  f"-# For more accurate information about past trips, or if the bus has no real-time information at the moment, try using [bustimes.org]({link}).{timestamp}")
        output = "\n\n".join([header, vehicle_data, notice])
        if len(output) > 2000:
            output = output[:2000]
        return output

    def update_output(self):
        self.output = self.create_output()


class RouteVehiclesViewer:
    """ Lists all vehicles currently on a route """
    # This view doesn't require any hard calculations to initialise, so we don't need a load method
    def __init__(self, cog, route: Route):
        self.cog = cog
        self.static_data: GTFSData = cog.static_data
        self.real_time_data: GTFSRData = cog.real_time_data
        self.vehicle_data: VehicleData = cog.vehicle_data
        self.fleet_data: dict[str, FleetVehicle] = cog.fleet_data
        self.route = route
        self.db = get_database()
        self.output: str = self.create_output()

    async def refresh(self):
        """ Refresh the map with new data """
        self.real_time_data, self.vehicle_data, _ = await self.cog.load_real_time_data(debug=self.cog.DEBUG, write=self.cog.WRITE)
        self.update_output()

    @property
    def data_timestamp(self) -> str:
        """ Returns the timestamp of the vehicle data """
        if self.vehicle_data:
            return format_timestamp(self.vehicle_data.header.timestamp)
        return "Vehicle data unavailable"

    def get_all_vehicles(self) -> list[Vehicle]:
        """ Returns all vehicles currently tracking on this route """
        return list(vehicle for vehicle in self.vehicle_data.entities.values() if vehicle.trip.route_id == self.route.id)

    def vehicle_list_by_model(self) -> str:
        """ List the buses currently operating on a route by their model """
        all_vehicles = self.get_all_vehicles()
        if not all_vehicles:
            raise RuntimeError("No vehicles operating on the route")
        models: dict[str, list[str]] = {}

        def add_to_dict(key: str, value: str):
            if key in models:
                models[key].append(value)
            else:
                models[key] = [value]

        for vehicle in all_vehicles:
            fleet_vehicle = self.fleet_data.get(vehicle.vehicle_id)
            if not fleet_vehicle:
                add_to_dict("Unknown", f"Vehicle {vehicle.vehicle_id}")
            else:
                fleet_number = fleet_vehicle.fleet_number
                model = get_model_code(fleet_number)
                add_to_dict(model, fleet_number)

        output = []
        for model, vehicles in models.items():
            vehicles.sort()  # Sort the list of vehicles alphabetically
            amount = len(vehicles)
            _s = "s" if amount > 1 else ""
            output.append(f"- {model}: {amount} vehicle{_s} ({', '.join(vehicles)})")
        return "\n".join(output)

    def create_output(self) -> str:
        route_full = f"Route {self.route.short_name} ({self.route.long_name})"
        # all_vehicles = self.get_all_vehicles()
        header = f"Vehicles currently operating on {route_full}"
        operator = f"Operator: {self.route.agency(self.static_data, self.db).name}"
        timestamp = f"-# Vehicle data timestamp: {self.data_timestamp}"
        today_date = time.date.today()
        yesterday_date = today_date - time.timedelta(days=1)
        today = time.datetime.combine(today_date, time.time(), tz=TIMEZONE)
        yesterday = time.datetime.combine(yesterday_date, time.time(), tz=TIMEZONE)
        now = time.datetime.now(tz=TIMEZONE)
        today_trips = []
        yesterday_trips = []
        for trip in Trip.from_route(self.route.id, self.db):
            if trip_validity(self.static_data, trip, today_date, self.db):
                today_trips.append(trip)
            if trip_validity(self.static_data, trip, yesterday_date, self.db):
                yesterday_trips.append(trip)
        # tuple(departure, headsign, vehicle_data, next_dep)
        inbound: list[tuple[time.datetime, str, str, str]] = []
        outbound: list[tuple[time.datetime, str, str, str]] = []
        vehicle_ids: dict[str, str] = {}  # vehicle_ids[trip_id] = vehicle_id
        visited_trips: set[tuple[str, time.date]] = set()  # Ignore static trips for which we already gathered real-time data

        def handle_trip(_trip: Trip | TripUpdate, day: time.datetime | time.date, is_static: bool, cancelled: bool = False):
            if isinstance(_trip, Trip):
                if (_trip.trip_id, day) in visited_trips:
                    return
                visited_trips.add((_trip.trip_id, day))
                first_stop = StopTime.from_sql_sequence(_trip.trip_id, 1, self.db)
                last_stop: StopTime = StopTime.from_sql_sequence(_trip.trip_id, _trip.total_stops, self.db)
                _departure = day + time.timedelta(seconds=first_stop.departure_time)
                _arrival = day + time.timedelta(seconds=last_stop.arrival_time)
                direction = _trip.direction_id
                _destination = _trip.headsign
            else:
                _departure = _trip.stop_times[0].departure_time
                _arrival = _trip.stop_times[-1].arrival_time
                direction = _trip.trip.direction_id
                try:
                    last_stop: Stop = load_value(self.static_data, Stop, _trip.stop_times[-1].stop_id, self.db)
                    _destination = f"{last_stop.name} (stop {last_stop.code_or_id})"
                except KeyError:
                    _destination = f"Stop {_trip.stop_times[-1].stop_id}"
            if isinstance(day, time.datetime):
                date = day.date()
            else:
                date = day
            if not is_static:  # Only check time bounds for non-real-time trips, but don't overwrite actual departure time
                _check_departure = time.datetime.min
                _check_arrival = time.datetime.max
            else:
                _check_departure = _departure
                _check_arrival = _arrival
            # This might show buses that have already arrived at the terminus or have not yet departed, but it should be fine.
            if _check_departure < now < _check_arrival:  # The trip is currently running
                relevant_list = inbound if direction == INBOUND_DIRECTION_ID else outbound
                if cancelled:
                    _vehicle_data = "Cancelled"
                    _next_departure = ""
                else:
                    if isinstance(_trip, Trip):
                        vehicle_id = vehicle_ids.get(_trip.trip_id)
                    else:
                        vehicle_id = _trip.vehicle_id
                    vehicle = self.vehicle_data.vehicles.get(vehicle_id)
                    if not vehicle:
                        _vehicle_data = "No bus tracked"
                    else:
                        fleet_vehicle = self.fleet_data.get(vehicle_id)
                        if fleet_vehicle:
                            fleet_number = fleet_vehicle.fleet_number
                        else:
                            fleet_number = f"Unknown vehicle {vehicle_id}"
                        nearest_stop = get_nearest_stop(_trip, vehicle, self.static_data)
                        _vehicle_data = f"{fleet_number} - Currently near {nearest_stop.name}"
                    _next_departure = ""
                    if isinstance(_trip, Trip):
                        _, next_trips = get_prev_next_trips(_trip, date, self.static_data, self.db)
                        if next_trips:
                            _, _next_departure, _, next_destination = next_trips[0]
                            _next_departure = f"\n  -# Next departure: {_next_departure:%H:%M} to {next_destination}"
                trip_output = (_departure, _destination, _vehicle_data, _next_departure)
                relevant_list.append(trip_output)

        for trip_update in self.real_time_data.entities.values():
            if trip_update.trip.route_id == self.route.id:
                is_cancelled = trip_update.trip.schedule_relationship == "CANCELED"
                if trip_update.trip.trip_id:
                    vehicle_ids[trip_update.trip.trip_id] = trip_update.vehicle_id
                # This ignores added trips that show up in vehicle data but not real-time data, but I'm not really bothered to fix that
                if trip_update.trip.schedule_relationship == "ADDED":
                    handle_trip(trip_update, trip_update.trip.start_date, False)  # The day variable doesn't matter for added trips
                # If there is a vehicle on this trip or the trip is cancelled, try to show the trip if it exists in static data or it is cancelled
                elif trip_update.vehicle_id or is_cancelled:
                    try:
                        trip: Trip = load_value(self.static_data, Trip, trip_update.trip.trip_id)
                        start_date = time.datetime.combine(trip_update.trip.start_date, time.time(), tz=TIMEZONE)
                        handle_trip(trip, start_date, False, is_cancelled)
                    except KeyError:
                        continue
        for trip in today_trips:
            handle_trip(trip, today, True)
        for trip in yesterday_trips:
            handle_trip(trip, yesterday, True)

        if not inbound and not outbound:
            return f"There are currently no vehicles operating on {route_full}."
        inbound.sort(key=lambda t: t[0])
        outbound.sort(key=lambda t: t[0])

        def format_trip(idx: int, _departure: time.datetime, _destination: str, _vehicle_data: str, _next_departure: str) -> str:
            return f"{idx}. {_departure:%H:%M} to {_destination} - {_vehicle_data}{_next_departure}"

        output_data = [header, operator, timestamp]
        if inbound:
            output_data.append("\nInbound:")
            for i, (departure, destination, vehicle_data, next_departure) in enumerate(inbound, start=1):
                output_data.append(format_trip(i, departure, destination, vehicle_data, next_departure))
        if outbound:
            output_data.append("\nOutbound:")
            for i, (departure, destination, vehicle_data, next_departure) in enumerate(outbound, start=1):
                output_data.append(format_trip(i, departure, destination, vehicle_data, next_departure))
        output = "\n".join(output_data)
        if len(output) > 2000:
            # Apparently "  " should be " {2}" according to PyCharm.
            output = re.sub(r"\n {2}-# Next departure: [^\n]+", "", output)
            output = output[:2000]
        return output

    def update_output(self):
        self.output = self.create_output()


class RouteScheduleViewer:
    # This does not interact with real-time data, so we don't need to import it here
    def __init__(self, static_data: GTFSData, route_schedule: RouteSchedule, trips: list[ScheduledTrip], now: time.datetime, direction: int = 0):
        self.static_data: GTFSData = static_data
        self.route_schedule: RouteSchedule = route_schedule
        self.route: Route = self.route_schedule.route
        self.route_id: str = self.route_schedule.route_id
        self.direction: int = direction  # Show trips with direction 0 by default, unless otherwise specified
        self.all_trips: list[ScheduledTrip] = trips
        self.now = now
        self.today = self.now.date()
        self.db = get_database()
        self.compact_mode: int = 0
        self.index_offset: int = 0
        self.inbound_stop_order, self.outbound_stop_order = self.get_stop_order()  # stop_id -> sequence
        self.relevant_trips: list[ScheduledTrip] = self.get_relevant_trips()
        self.start_idx, self.end_idx = self.get_indexes()
        self.output: paginators.LinePaginator = self.create_output()

    @classmethod
    async def load(cls, static_data: GTFSData, route: Route, now: time.datetime = None, direction: int = 0):
        if now is None:
            now = time.datetime.now(tz=TIMEZONE)
        today = now.date()
        event_loop = asyncio.get_event_loop()
        route_schedule: RouteSchedule = await event_loop.run_in_executor(None, RouteSchedule, static_data, route)
        trips: list[ScheduledTrip] = await event_loop.run_in_executor(None, route_schedule.relevant_trips, today)
        return cls(static_data, route_schedule, trips, now, direction)

    @property
    def departures(self) -> int:
        """ Returns the amount of departures being shown at once """
        # Normal -> 6 departures, compact mode 1 -> 3 departures, compact mode 2 -> 1 departure
        return {0: 6, 1: 3, 2: 1}[self.compact_mode]

    def get_indexes(self):
        # TODO: Try to find a more accurate way to do this (accounting for trips that don't originate at the first stop)
        start_idx = 0
        for i, trip in enumerate(self.relevant_trips):
            if trip.departure_time < self.now:  # Do show trips that depart exactly now
                start_idx += 1
            else:
                break
        max_idx = len(self.relevant_trips)
        start_idx = max(0, min(start_idx + self.index_offset, max_idx - self.departures))
        end_idx = min(start_idx + self.departures, max_idx)
        return start_idx, end_idx

    def get_stop_order(self) -> tuple[dict[str, int], dict[str, int]]:
        """ Arrange the stops throughout the trip """
        inbound_stops = []
        outbound_stops = []
        for trip in self.all_trips:
            relevant_list = inbound_stops if trip.direction_id == INBOUND_DIRECTION_ID else outbound_stops
            stop_ids = [stop_time.stop_id for stop_time in trip.stop_times]
            for stop_time in trip.stop_times:
                stop_id = stop_time.stop_id
                if stop_id in relevant_list:
                    continue
                else:
                    # First stop or middle of journey -> insert at appropriate index
                    # Last stop -> append to end of list
                    # Quite simple, but should work unless a route is extremely silly
                    if stop_time.sequence >= len(relevant_list):
                        relevant_list.append(stop_id)
                    elif stop_time.sequence == trip.total_stops:
                        relevant_list.append(stop_id)
                    elif relevant_list[0] in stop_ids:  # This stop is before the existing first stop
                        relevant_list.insert(stop_time.sequence - 1, stop_id)
                    else:
                        relevant_list.insert(stop_time.sequence, stop_id)

        inbound_output: dict[str, int] = {}
        outbound_output: dict[str, int] = {}
        for i, stop in enumerate(inbound_stops):
            inbound_output[stop] = i
        for i, stop in enumerate(outbound_stops):
            outbound_output[stop] = i
        return inbound_output, outbound_output

    def get_relevant_trips(self) -> list[ScheduledTrip]:
        """ List of trips that are going in the specified direction """
        # output[idx] = trip | times[idx][seq] = departure_time
        output: list[ScheduledTrip] = []
        times: list[dict[int, time.datetime]] = []
        stop_order = self.relevant_stop_order
        # prev_stops: set = set()
        for trip in filter(lambda t: t.direction_id == self.direction, self.all_trips):  # type: ScheduledTrip
            stop_times: list[SpecificStopTime] = trip.stop_times
            trip_times: dict[int, time.datetime] = {stop_order[stop_time.stop_id]: stop_time.departure_time for stop_time in stop_times}
            trip_stops: set[int] = set(trip_times)   # set of stop sequences at which this trip calls
            # trip_stops: set = {stop_order[stop_time.stop_id] for stop_time in stop_times}
            if not output:  # If no trips exist yet, just add it
                output.append(trip)
                times.append(trip_times)
            else:
                idx = len(output)
                for other_times in times[::-1]:
                    shared = trip_stops.intersection(other_times)
                    if shared:
                        seq = min(shared)
                        if other_times[seq] > trip_times[seq]:
                            idx -= 1
                        else:
                            break
                    else:  # This shouldn't happen on a normal route, but if it does, try to find a trip that does share at least some of the stops...
                        continue
                        # other_trip = output[idx - 1]
                        # if other_trip.departure_time > trip.departure_time:
                        #     idx -= 1
                        # else:
                        #     break
                output.insert(idx, trip)
                times.insert(idx, trip_times)
            # prev_stops = trip_stops
        return output

    def update_relevant_trips(self):
        self.relevant_trips = self.get_relevant_trips()

    @property
    def relevant_stop_order(self) -> dict[str, int]:
        """ Dictionary with orders and stop IDs of all stops made in the specified direction """
        return self.inbound_stop_order if self.direction == INBOUND_DIRECTION_ID else self.outbound_stop_order

    def create_output(self) -> paginators.LinePaginator:
        # Seq - Stop - Code - Dep 1 - Dep 2 - Dep 3 - Dep 4
        header_line = ["Seq", "Stop", "Code"]
        output_data: list[list[str]] = []
        column_sizes = [2, 0, 0]
        self.start_idx, self.end_idx = self.get_indexes()
        # Create initial list of all stops along the route
        stop_order = self.relevant_stop_order
        stop_idx_len = len(str(len(stop_order)))
        for stop_id, idx in stop_order.items():
            stop: Stop = load_value(self.static_data, Stop, stop_id, self.db)
            index = f"{idx + 1:0{stop_idx_len}d})"
            output_line = [index, stop.name, stop.code_or_id]
            output_data.append(output_line)
            for i, element in enumerate(output_line):
                column_sizes[i] = max(column_sizes[i], len(element))
        output_data.sort(key=lambda _line: _line[0])  # Sort by stop order

        for trip in self.relevant_trips[self.start_idx:self.end_idx]:
            longest = 0
            for stop_time in trip.stop_times:
                seq = stop_order[stop_time.stop_id]
                departure_time = self.format_time(stop_time.departure_time)
                if stop_time.pickup_type == 1:
                    departure_time = "D " + departure_time
                elif stop_time.drop_off_type == 1:
                    departure_time = "P " + departure_time
                output_data[seq].append(departure_time)
                longest = max(longest, len(departure_time))
            column_sizes.append(longest)
            header_line.append("Dep.")
            # Add "-" to any stops not served by this trip
            columns = len(column_sizes)
            for line in output_data:
                if len(line) < columns:
                    line.append("-")

        # skipped = ()  # Indexes of columns not shown
        # line_length = sum(column_sizes) + len(column_sizes) - 1
        # cutoff = 0
        if self.compact_mode:
            skipped = (2,)  # Skip the stop code
            if self.compact_mode == 1:
                line_length_limit = 50
            else:
                # Extra departure columns will remove themselves as they're empty
                line_length_limit = 36
            for idx in skipped:
                column_sizes.pop(idx)
                header_line.pop(idx)
                for line in output_data:
                    line.pop(idx)
            line_length = sum(column_sizes) + len(column_sizes) - 1
            if line_length > line_length_limit:
                column_sizes[1] -= (line_length - line_length_limit)
                # cutoff = column_sizes[1] - (line_length - line_length_limit)
                # line_length = line_length_limit

        def generate_line(_line: list[str]):
            line_data = []
            for j, (size, column) in enumerate(zip(column_sizes, _line)):
                if size == 0:  # Skip empty columns (e.g. routes that have less than 4 daily departures)
                    continue
                elif len(column) > size:
                    line_data.append(f"{column[:size - 1]}…")
                else:
                    alignment = "<" if j < 2 else ">"
                    line_data.append(f"{column:{alignment}{size}}")
            return " ".join(line_data).rstrip()

        direction = "inbound" if self.direction == INBOUND_DIRECTION_ID else "outbound"
        operator = self.route.agency(self.static_data, self.db).name
        output = (f"Route schedule for the route {self.route.short_name} ({self.route.long_name}).\nShowing {direction} trips\n"
                  f"-# Route operated by {operator}\n```fix\n{generate_line(header_line)}")
        suffix = ("```\n-# Note: This schedule is static and does not take real-time data into account.\n"
                  "-# Use the first row of buttons to scroll through the list of stops.\n"
                  "-# Use the second row of buttons to see earlier or later departures.")
        paginator = paginators.LinePaginator(prefix=output, suffix=suffix, max_lines=PAGINATOR_MAX_LINES, max_size=PAGINATOR_MAX_LENGTH)
        for line in output_data:
            paginator.add_line(generate_line(line))
        return paginator

    def update_output(self):
        self.output = self.create_output()

    def format_time(self, provided_time: time.datetime) -> str:
        return format_time(provided_time, self.today)
