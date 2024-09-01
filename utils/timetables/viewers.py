from __future__ import annotations

import asyncio
import io
import re

import discord
from regaus import time

from utils import paginators
from utils.timetables.shared import TIMEZONE, WEEKDAYS, WARNING, CANCELLED, get_database
from utils.timetables.realtime import GTFSRData, VehicleData, TripUpdate, Vehicle
from utils.timetables.static import GTFSData, Stop, load_value, Trip, StopTime, Route, FleetVehicle
from utils.timetables.schedules import SpecificStopTime, RealStopTime, StopSchedule, RealTimeStopSchedule, trip_validity
from utils.timetables.maps import DEFAULT_ZOOM, get_map_with_buses, get_trip_diagram, distance_between_bus_and_stop, get_nearest_stop

__all__ = ("StopScheduleViewer", "HubScheduleViewer", "TripDiagramViewer", "TripMapViewer", "MapViewer", "VehicleDataViewer")


FLEET_REGEX = re.compile(r"^([A-Z]{2,3})([0-9]{1,3})$")


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

    if hub or not self.real_time:
        distance = vehicle = ""
    elif self.compact_mode < 2 and self.real_time and stop_time.vehicle is not None:
        vehicle_data: FleetVehicle | None = self.cog.fleet_data.get(stop_time.vehicle_id)
        if vehicle_data:
            fleet = vehicle_data.fleet_number
            match = re.match(FLEET_REGEX, fleet)
            vehicle = f"{match.group(1)}{match.group(2):>3}" if match else fleet
        else:
            vehicle = "-"
        if stop_time.vehicle.latitude == 0 and stop_time.vehicle.longitude == 0:
            distance = "-"
        else:
            trip = stop_time.real_trip if stop_time.is_added else stop_time.trip(self.static_data)
            distance_m, colour = distance_between_bus_and_stop(trip, self.stop, stop_time.vehicle, self.static_data)
            if self.compact_mode == 1:
                distance = f"{distance_m / 1000:.1f}k"
            else:
                if distance_m >= 1000:
                    distance = f"{distance_m / 1000:.2f}km"
                else:
                    distance = f"{round(distance_m, -1):.0f}m"
            distance += {-1: "🟠", 0: "🟢", 1: "🟡", 2: "🔴"}.get(colour, "🟠") + "\u2060"
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
    vehicle = self.vehicle_data.entities.get(self.vehicle_id)
    if vehicle is not None and vehicle.latitude != 0 and vehicle.longitude != 0:
        nearest_stop = get_nearest_stop(self.trip, vehicle, self.static_data)
        bus_data.append(f"The bus is currently near the stop {nearest_stop.name} (stop {nearest_stop.code_or_id}).")
    fleet_vehicle: FleetVehicle | None = self.cog.fleet_data.get(self.vehicle_id)
    if fleet_vehicle is not None:
        bus_data.append(f"This trip is served by the bus {fleet_vehicle.fleet_number} ({fleet_vehicle.reg_plates}).")
        bus_data.append(f"-# Model: {fleet_vehicle.model} | Notable features: {fleet_vehicle.trivia}")
    return "\n".join(bus_data)


class StopScheduleViewer:
    """ A loader for stop schedules"""

    def __init__(self, static_data: GTFSData, now: time.datetime, real_time: bool, fixed: bool, today: time.date, stop: Stop, lines: int,
                 base_schedule: StopSchedule, base_stop_times: list[SpecificStopTime],
                 real_schedule: RealTimeStopSchedule | None, real_stop_times: list[RealStopTime] | None, cog):
        self.static_data = static_data
        self.cog = cog  # The Timetables cog
        self.real_time_data = cog.real_time_data
        self.vehicle_data = cog.vehicle_data
        self.fleet_data = cog.fleet_data
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
        self.real_time_data, self.vehicle_data = await self.cog.load_real_time_data(debug=self.cog.DEBUG, write=self.cog.WRITE)
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
        additional_text = "\n-# D = Drop-off/Alighting only | P = Pick-up/Boarding only"
        if has_vehicle_info:
            additional_text += "\n-# Distance indicators: Red = Bus already passed stop | Yellow = Bus approaching | Green = Bus not nearby yet"
        if self.real_time:
            additional_text += f"\n-# Real-time data timestamp: {self.data_timestamp}"
        output = f"Real-Time data for the stop {self.stop.name} ({stop_code}{stop_id})\n" \
                 "-# Note: Vehicle locations and distances may not be accurate" \
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
        self.today: time.date = now.date()
        self.real_time: bool = real_time
        self.fixed: bool = fixed
        self.hide_terminating: bool = hide_terminating
        self.user_id: int | None = user_id

        self.compact_mode: bool = False
        self.index_offset: int = 0  # Not currently used, but left just in case.
        self.day_offset: int = 0    # Not currently used, but left just in case.
        self.lines: int = 4 if len(stops) < 8 else 3

        self.indexes = self.get_indexes()
        self.output = self.create_output()

    @classmethod
    async def load(cls, hub_id: str, stops: list[Stop], now: time.datetime | None, hide_terminating: bool, user_id: int | None, static_data: GTFSData, cog):
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
        base_schedules, base_stop_times = await event_loop.run_in_executor(None, cls.load_base_schedules, static_data, stops, today, hide_terminating, user_id)
        if real_time:
            real_schedules, real_stop_times = await event_loop.run_in_executor(None, cls.load_real_schedules, cog, base_schedules, base_stop_times)
        else:
            real_schedules = real_stop_times = None
        return cls(hub_id, stops, now, real_time, fixed, static_data, cog, hide_terminating, user_id, base_schedules, base_stop_times, real_schedules, real_stop_times)

    @staticmethod
    def load_base_schedules(data: GTFSData, stops: list[Stop], today: time.date, hide_terminating: bool, user_id: int | None):
        base_schedules: list[StopSchedule] = []
        base_stop_times: list[list[SpecificStopTime]] = []
        for stop in stops:
            schedule = StopSchedule(data, stop.id, hide_terminating, user_id)
            base_schedules.append(schedule)
            base_stop_times.append(schedule.relevant_stop_times(today))
        return base_schedules, base_stop_times

    @staticmethod
    def load_real_schedules(cog, base_schedules: list[StopSchedule], base_stop_times: list[list[SpecificStopTime]]):
        real_schedules: list[RealTimeStopSchedule] = []
        real_stop_times: list[list[RealStopTime]] = []
        for schedule, stop_times in zip(base_schedules, base_stop_times):
            real_schedule = RealTimeStopSchedule.from_existing_schedule(schedule, cog.real_time_data, cog.vehicle_data, stop_times)
            real_schedules.append(real_schedule)
            real_stop_times.append(real_schedule.real_stop_times())
        return real_schedules, real_stop_times

    async def reload(self):
        new_schedule = await self.load(self.hub_id, self.stops, self.now, self.hide_terminating, self.user_id, self.static_data, self.cog)
        new_schedule.fixed = self.fixed
        new_schedule.real_time = self.real_time
        new_schedule.compact_mode = self.compact_mode
        new_schedule.update_output()
        return new_schedule

    async def refresh(self):
        event_loop = asyncio.get_event_loop()
        await self.cog.load_real_time_data(debug=self.cog.DEBUG, write=self.cog.WRITE)
        self.real_schedules, self.real_stop_times = await event_loop.run_in_executor(None, self.load_real_schedules, self.cog, self.base_schedules, self.base_stop_times)
        if not self.fixed:
            prev_today = self.today
            self.now = time.datetime.now(tz=TIMEZONE)
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
            start_idx += self.index_offset
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
            return format_timestamp(self.cog.real_time_data.header.timestamp)
        return "Real-time data unavailable"

    def create_output(self):
        if self.real_time:
            header = f"Real-time data for stop hub {self.hub_id}\n-# Real-time data timestamp: {self.data_timestamp}"
        else:
            header = f"Schedule for stop hub {self.hub_id}"
        output: list[str] = [header + f"\n-# Lookup time: {self.now:%d %b %Y, %H:%M}"]
        output_data_header: list[str | None] = ["Rt", "Destination", "Sched", "Real"]
        output_data: list[list[list[str | None]]] = []  # output_data[stop][line][column]
        column_sizes: list[int] = [2, 11, 5, 5]
        assert len(output_data_header) == len(column_sizes)
        if self.compact_mode or len(self.stops) >= 7:
            line_length_limit = 36
        elif len(self.stops) >= 5:
            line_length_limit = 40
        else:
            line_length_limit = 45

        self.indexes = self.get_indexes()

        for i, stop_times in enumerate(self.iterable_stop_times):
            start_idx, end_idx = self.indexes[i]
            output_stop: list[list[str | None]] = [output_data_header]
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
            stop_output.append("```")
            output.append("\n".join(stop_output))

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
        self.real_time_data = stop_schedule.real_time_data
        self.vehicle_data = stop_schedule.vehicle_data
        self.cog = stop_schedule.cog
        self.is_real_time = stop_schedule.real_time

        self.static_trip: Trip | None = None
        self.real_trip: TripUpdate | None = None
        self.trip_identifier: str = trip_id
        self.cancelled: bool = False
        self.vehicle_id: str | None = None
        # _type = 0
        static_trip_id, real_trip_id, _day_modifier = trip_id.split("|")
        if static_trip_id:
            self.static_trip: Trip = load_value(self.static_data, Trip, static_trip_id)
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
        self.real_time_data, self.vehicle_data = await self.cog.load_real_time_data(debug=self.cog.DEBUG, write=self.cog.WRITE)  # type: GTFSRData, VehicleData
        if self.real_trip or self.is_real_time:
            # Find new real-time information about this trip
            real_trip = None
            if not self.static_trip:  # Added trip
                for entity in self.real_time_data.entities.values():
                    trip_update = entity.trip
                    current_trip = self.real_trip.trip
                    if trip_update.route_id == current_trip.route_id and \
                            trip_update.start_time == current_trip.start_time and \
                            trip_update.direction_id == current_trip.direction_id:
                        real_trip = entity
                        break
            else:
                for entity in self.real_time_data.entities.values():
                    if entity.trip.trip_id == self.static_trip.trip_id:
                        real_trip = entity
                        break
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
        elif self.static_trip and not self.real_trip:  # Static trip
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

        if self.real_trip:
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

        paginator = paginators.LinePaginator(prefix=output_start, suffix=output_end, max_lines=20, max_size=1500)
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
        self.trip_id: str = viewer.trip_identifier
        self.stop: Stop = viewer.stop
        self.cog = viewer.cog
        self.static_data: GTFSData = viewer.cog.static_data
        self.real_time_data: GTFSRData = viewer.cog.real_time_data
        self.vehicle_data: VehicleData = viewer.cog.vehicle_data
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
        args = (viewer.stop, viewer.cog.static_data, viewer.cog.vehicle_data, departures, viewer.drop_off_only, viewer.pickup_only, viewer.skipped, viewer.cancelled)
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
        self.image, _ = await get_trip_diagram(self.trip, self.stop, self.cog.static_data, self.cog.vehicle_data, self.departures,
                                               self.drop_off_only, self.pickup_only, self.skipped, self.cancelled, self.custom_zoom)

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
        if self.vehicle_id:
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
        self.vehicle_data: VehicleData = cog.vehicle_data
        self.stop: Stop = stop
        self.lat: float = stop.latitude
        self.lon: float = stop.longitude
        self.zoom: int = zoom
        self.image: io.BytesIO = image
        self.output: str = self.create_output()

    @classmethod
    async def load(cls, cog, stop: Stop, zoom: int = DEFAULT_ZOOM):
        image_bio = await get_map_with_buses(stop.latitude, stop.longitude, zoom, cog.vehicle_data, cog.static_data)
        return cls(cog, image_bio, stop, zoom)

    @property
    def attachment(self) -> tuple[discord.File]:
        """ The Discord attachment with the map image """
        return (discord.File(self.image, f"{self.stop.id}.png"),)

    async def refresh(self):
        """ Refresh the map with new data """
        _, self.vehicle_data = await self.cog.load_real_time_data(debug=self.cog.DEBUG, write=self.cog.WRITE)
        await self.update_map()
        self.update_output()

    async def update_map(self):
        """ Update the map output without refreshing the vehicle data """
        self.image = await get_map_with_buses(self.stop.latitude, self.stop.longitude, self.zoom, self.cog.vehicle_data, self.cog.static_data)

    @property
    def data_timestamp(self) -> str:
        """ Returns the timestamp of the vehicle data """
        return format_timestamp(self.vehicle_data.header.timestamp)

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
        self.real_time_vehicle: Vehicle | None = self.vehicle_data.entities.get(vehicle.vehicle_id)
        self.db = get_database()
        self.output: str = self.create_output()

    async def refresh(self):
        """ Refresh the map with new data """
        self.real_time_data, self.vehicle_data = await self.cog.load_real_time_data(debug=self.cog.DEBUG, write=self.cog.WRITE)
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
                if stop_times:
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
                nearest_stop = get_nearest_stop(static_trip or real_trip, self.real_time_vehicle, self.static_data)
                location = f"The bus is currently near the stop {nearest_stop.name} (stop {nearest_stop.code_or_id})."
            current_trip = f"{trip_info}\n{location}"
            vehicle_data = current_trip  # Fallback for unavailable static Trip data or block data
            if static_trip:
                block_id = static_trip.block_id
                if block_id:
                    block = Trip.from_block(block_id)
                    # tuple(trip_id, start_time, destination)
                    prev_trips: list[tuple[str, time.datetime, str, str]] = []
                    next_trips: list[tuple[str, time.datetime, str, str]] = []
                    today_date = time.date.today()
                    today = time.datetime.combine(today_date, time.time(), tz=TIMEZONE)
                    now = time.datetime.now(tz=TIMEZONE)
                    for trip in block:
                        if trip.trip_id == static_trip.trip_id:  # Ignore current trip
                            continue
                        valid = trip_validity(self.static_data, trip, today_date, self.db)
                        if not valid:  # Only include the trip if it actually runs today
                            continue
                        stop_time = StopTime.from_sql_sequence(trip.trip_id, 1, self.db)
                        departure = today + time.timedelta(seconds=stop_time.departure_time)
                        _route = trip.route(self.static_data, self.db)
                        if _route:
                            route = f"Route {_route.short_name}"
                        else:
                            route = f"Unknown route {trip.route_id}"  # Should never happen, but just in case.
                        trip_data = (trip.trip_id, departure, route, trip.headsign)
                        if departure > now:
                            next_trips.append(trip_data)
                        else:
                            prev_trips.append(trip_data)
                    output_data = [current_trip]

                    def format_trip(_departure: time.datetime, _route: str, _destination: str):
                        return f"- {_departure:%H:%M} to {_destination} ({_route})"
                    # Show up to 10 previous trips and up to 10 future trips
                    if prev_trips:
                        prev_trips.sort(key=lambda t: t[1])  # sort by departure time
                        _s = "s" if len(prev_trips) > 1 else ""
                        prev_trips_str = f"Previous trip{_s}:\n" + "\n".join(format_trip(departure, route, destination) for _, departure, route, destination in prev_trips[-10:])
                        output_data.append(prev_trips_str)
                    if next_trips:
                        next_trips.sort(key=lambda t: t[1])
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
