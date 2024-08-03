import asyncio
import io

import discord
from regaus import time

from utils import conworlds, languages, paginators
from utils.timetables.realtime import GTFSRData, VehicleData, TripUpdate
from utils.timetables.schedules import SpecificStopTime, RealStopTime, StopSchedule, RealTimeStopSchedule
from utils.timetables.shared import TIMEZONE, WEEKDAYS, WARNING, CANCELLED
from utils.timetables.static import GTFSData, Stop, load_value, Trip, StopTime, Route
from utils.timetables.maps import DEFAULT_ZOOM, get_map_with_buses

__all__ = ["StopScheduleViewer", "TripDiagramViewer", "MapViewer"]


def format_time(provided_time: time.datetime, today: time.date) -> str:
    """ Format the provided time, showing when a given trip happens outside the current day """
    formatted = provided_time.format("%H:%M")
    # If the date is not the date of the lookup, then append the weekday of the time
    # If self.now is Tuesday 23:59, then trips at Wednesday 00:00 will be treated as "tomorrow"
    # If self.now is Wednesday 00:00, then trips at Wednesday 00:00 will be treated as "today"
    if provided_time.date() != today:
        formatted = f"{WEEKDAYS[provided_time.weekday]} {formatted}"
    return formatted


# TODO: Link these to the real_time_data and vehicle_data of the Timetables cog, so that it can be updated properly
class StopScheduleViewer:
    """ A loader for stop schedules"""

    def __init__(self, data: GTFSData, now: time.datetime, real_time: bool, fixed: bool, today: time.date,
                 stop: Stop, real_time_data: GTFSRData, vehicle_data: VehicleData, lines: int,
                 base_schedule: StopSchedule, base_stop_times: list[SpecificStopTime],
                 real_schedule: RealTimeStopSchedule | None, real_stop_times: list[RealStopTime] | None, cog):
        self.data = data
        self.now = now
        self.today = today
        self.real_time = real_time
        self.fixed = fixed
        # self.fixed_time = fixed
        self.stop = stop
        self.latitude = stop.latitude
        self.longitude = stop.longitude
        self.real_time_data = real_time_data
        self.vehicle_data = vehicle_data
        self.lines = lines
        self.base_schedule = base_schedule
        self.base_stop_times = base_stop_times
        self.real_schedule = real_schedule
        self.real_stop_times = real_stop_times
        self.cog = cog  # The Timetables cog

        self.compact_mode: int = 0  # Don't cut off destinations by default
        self.index_offset = 0
        self.day_offset = 0  # Offset for date changes (prevents confusion when launching the TripDiagramViewer)

        self.start_idx, self.end_idx = self.get_indexes()
        self.output = self.create_output()

    @classmethod
    async def load(cls, data: GTFSData, stop: Stop, real_time_data: GTFSRData, vehicle_data: VehicleData, cog,
                   now: time.datetime | None = None, lines: int = 7, hide_terminating: bool = True, user_id: int = None):
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
            real_schedule, real_stop_times = await event_loop.run_in_executor(None, cls.load_real_schedule, base_schedule, real_time_data, vehicle_data, base_stop_times)
        else:
            real_schedule = real_stop_times = None
        return cls(data, now, real_time, fixed, today, stop, real_time_data, vehicle_data, lines, base_schedule, base_stop_times, real_schedule, real_stop_times, cog)

    async def reload(self):
        new_schedule = await self.load(self.data, self.stop, self.real_time_data, self.vehicle_data, self.cog, self.now, self.lines,
                                       self.base_schedule.hide_terminating, self.base_schedule.route_filter_userid)
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
    def load_real_schedule(base_schedule: StopSchedule, real_time_data: GTFSRData, vehicle_data: VehicleData, base_stop_times: list[SpecificStopTime]):
        """ Load the RealTimeStopSchedule """
        real_schedule = RealTimeStopSchedule.from_existing_schedule(base_schedule, real_time_data, vehicle_data, base_stop_times)
        real_stop_times = real_schedule.real_stop_times()
        return real_schedule, real_stop_times

    async def refresh_real_schedule(self):
        """ Refresh the RealTimeStopSchedule """
        event_loop = asyncio.get_event_loop()
        self.real_time_data, self.vehicle_data = await self.cog.load_real_time_data(debug=self.cog.DEBUG, write=self.cog.WRITE)
        self.real_schedule, self.real_stop_times = await event_loop.run_in_executor(None, self.load_real_schedule, self.base_schedule, self.real_time_data, self.vehicle_data, self.base_stop_times)
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
        if self.real_time:
            for idx, stop_time in enumerate(self.real_stop_times):
                if stop_time.available_departure_time >= self.now:
                    start_idx = idx
                    break
        else:
            for idx, stop_time in enumerate(self.base_stop_times):
                if stop_time.departure_time >= self.now:
                    start_idx = idx
                    break
        max_idx = len(self.iterable_stop_times)
        start_idx += self.index_offset
        start_idx = max(0, min(start_idx, max_idx - lines))
        end_idx = start_idx + lines  # We don't need the + 1 here
        end_idx = min(end_idx, max_idx)
        return start_idx, end_idx

    @property
    def iterable_stop_times(self) -> list[RealStopTime] | list[SpecificStopTime]:
        """ Returns the stop times we can iterate over """
        return self.real_stop_times if self.real_time else self.base_stop_times

    def create_output(self):
        """ Create the output from available information and send it to the user """
        language = languages.Language("en")
        output_data: list[list[str | None]] = [["Route", "Destination", "Schedule", "RealTime", "Distance", None, None]]
        column_sizes = [5, 11, 8, 8, 8, 0, 0]  # Longest member of the column
        if self.compact_mode == 2:
            output_data[0][3] = "Departure"
            column_sizes[3] = 9
            for idx in (4, 2):
                output_data[0].pop(idx)
                column_sizes.pop(idx)
        extras = False
        # I don't think this should be there - for fixed schedules, self.now should not change
        # if not self.fixed:
        self.start_idx, self.end_idx = self.get_indexes()
        # iterable_stop_times = self.real_stop_times if self.real_time else self.base_stop_times

        # This is used in the for loop below
        def add_letter(ltr: str):
            if self.compact_mode == 2:
                nonlocal departure_time
                departure_time = ltr + departure_time
            else:
                nonlocal scheduled_departure_time
                scheduled_departure_time = ltr + scheduled_departure_time
            nonlocal extras
            extras = True

        for stop_time in self.iterable_stop_times[self.start_idx:self.end_idx]:
            cancelled = skipped = False
            departure_time = scheduled_departure_time = real_departure_time = ""
            if self.compact_mode == 2:
                if stop_time.schedule_relationship == "CANCELED":
                    cancelled = True
                    departure_time = "CANCELLED"
                elif stop_time.schedule_relationship == "SKIPPED":
                    skipped = True
                    departure_time = "SKIPPED"
                else:
                    departure_time = self.format_time(stop_time.available_departure_time)
            else:
                if self.real_time:
                    if stop_time.scheduled_departure_time is not None:
                        scheduled_departure_time = self.format_time(stop_time.scheduled_departure_time)
                        # scheduled_departure_time = stop_time.scheduled_departure_time.format("%H:%M")  # :%S
                    else:
                        scheduled_departure_time = "--:--"  # "Unknown"

                    if stop_time.schedule_relationship == "CANCELED":
                        real_departure_time = "CANCELLED"
                        cancelled = True
                    elif stop_time.schedule_relationship == "SKIPPED":
                        real_departure_time = "SKIPPED"
                        skipped = True
                    elif stop_time.departure_time is not None:
                        real_departure_time = self.format_time(stop_time.departure_time)
                        # real_departure_time = stop_time.departure_time.format("%H:%M")  # :%S
                    else:
                        real_departure_time = "--:--"
                else:
                    scheduled_departure_time = self.format_time(stop_time.departure_time)
                    # scheduled_departure_time = stop_time.departure_time.format("%H:%M")
                    real_departure_time = ""

            if stop_time.pickup_type == 1:
                add_letter("D ")
            elif stop_time.drop_off_type == 1:
                add_letter("P ")

            _route = stop_time.route(self.data)
            if _route is None:
                route = "Unknown"
            else:
                route = _route.short_name

            destination = stop_time.destination(self.data)
            # If the bus terminates early or departs later than scheduled, show a warning sign at the destination field
            if stop_time.actual_destination is not None or stop_time.actual_start is not None or skipped:
                destination = WARNING + destination
            if cancelled:
                destination = CANCELLED + destination

            if self.compact_mode < 2 and self.real_time and stop_time.vehicle is not None:  # "Compact mode" does not show vehicle distance
                distance_km = conworlds.distance_between_places(self.latitude, self.longitude, stop_time.vehicle.latitude, stop_time.vehicle.longitude, "Earth")
                if distance_km >= 1:  # > 1 km
                    distance = language.length(distance_km * 1000, precision=2).split(" | ")[0]  # Precision: 0.01km (=10m)
                else:  # < 1 km
                    distance = language.length(round(distance_km * 1000, -1), precision=0).split(" | ")[0]  # Round to nearest 10m
                distance = distance.replace("\u200c", "")  # Remove ZWS
            elif not self.real_time:
                distance = ""
            else:
                distance = "-"

            actual_destination_line = stop_time.actual_destination or ""
            actual_start_line = stop_time.actual_start or ""

            if self.compact_mode == 2:
                output_line = [route, destination, departure_time, actual_destination_line, actual_start_line]
            else:
                output_line = [route, destination, scheduled_departure_time, real_departure_time, distance, actual_destination_line, actual_start_line]
            for i, element in enumerate(output_line):
                # noinspection PyUnresolvedReferences
                column_sizes[i] = max(column_sizes[i], len(element))

            output_data.append(output_line)

        data_end = -2  # Last index with data to show
        if not self.real_time:
            data_end -= 2  # Hide real-time and distance data for non-real-time schedules

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
        additional_text = ""
        if extras:
            additional_text += "*D = Drop-off/Alighting only; P = Pick-up/Boarding only*\n"
        output = f"Real-Time data for the stop {self.stop.name} ({stop_code}{stop_id})\n" \
                 "*Please note that the vehicle locations and distances may not be accurate*\n" \
                 f"{additional_text}```fix\n"

        for line in output_data:
            assert len(column_sizes) == len(line)
            line_data = []
            for i in range(len(line) + data_end):  # Excluding the "actual_destination" and "actual_start"
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


class TripDiagramViewer:
    """ Viewer for a route diagram of an existing trip (called from a select menu in the StopScheduleView) """

    def __init__(self, original_view, trip_id: str):
        # I don't think the StopScheduleView and -Viewer should be stored as attrs
        # self.original_view = original_view  # views.StopScheduleView
        stop_schedule: StopScheduleViewer = original_view.schedule
        self.static_data = stop_schedule.data
        self.stop = stop_schedule.stop
        # self.fixed = stop_schedule.fixed  # Do we even need this here?
        self.real_time_data = stop_schedule.real_time_data
        self.vehicle_data = stop_schedule.vehicle_data  # Not used here right now, but might be useful later.
        self.cog = stop_schedule.cog
        self.is_real_time = stop_schedule.real_time

        self.static_trip: Trip | None = None
        self.real_trip: TripUpdate | None = None
        self.trip_identifier: str = trip_id
        self.cancelled: bool = False
        # _type = 0
        static_trip_id, real_trip_id, _day_modifier = trip_id.split("|")
        if static_trip_id:
            self.static_trip: Trip = load_value(self.static_data, Trip, static_trip_id)
            # _type += 1
        if real_trip_id:
            self.real_trip: TripUpdate = self.real_time_data.entities[real_trip_id]
            self.cancelled = self.real_trip.trip.schedule_relationship == "CANCELED"
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
        self.output = self.create_output()

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

        skipped: set[int] = set()
        pickup_only: set[int] = set()
        drop_off_only: set[int] = set()
        stops: list[Stop] = []
        arrivals: list[time.datetime] = []
        departures: list[time.datetime] = []

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
                if prev_sequence == 0:
                    if sequence > 1:
                        arrival_delays.extend([time.timedelta()] * repetitions)
                        departure_delays.extend([time.timedelta()] * repetitions)
                        real_time_statuses.extend([stop_time_update.schedule_relationship != "SKIPPED"] * repetitions)
                    repetitions = 0
                extend_list(real_time_statuses, repetitions)
                extend_list(departure_delays, repetitions)
                real_time_statuses.append(stop_time_update.schedule_relationship != "SKIPPED")
                departure_delays.append(stop_time_update.departure_delay)
                # if prev_sequence == 1 and arrival_delays[0] is None:
                #     if repetitions > 0:
                #         arrival_delays.append(departure_delays[0])
                #         extend_list(arrival_delays, repetitions - 1)
                #     else:
                #         arrival_delays.append(stop_time_update.arrival_delay)
                # else:
                #     extend_list(arrival_delays, repetitions)
                #     arrival_delays.append(stop_time_update.arrival_delay)
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
                total_stops = self.static_trip.total_stops
                remaining = total_stops - len(real_time_statuses)
                extend_list(real_time_statuses, remaining)
                # if arrival_delays[-1] is None:
                #     if remaining > 0:
                #         arrival_delays.append(departure_delays[-1])
                #         extend_list(arrival_delays, remaining - 1)
                #     else:
                #         arrival_delays[-1] = departure_delays[-1]
                # else:
                #     extend_list(arrival_delays, remaining)
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
                        arrivals.append(custom_arrival_times[sequence])
                    else:
                        arrival_delay = arrival_delays[index]
                        if arrival_delay is None:
                            arrival_delay = time.timedelta()
                        arrivals.append(stop_time.arrival_time + arrival_delay)
                    if sequence in custom_departure_times:
                        departures.append(custom_departure_times[sequence])
                    else:
                        departure_delay = departure_delays[index]
                        if departure_delay is None:
                            departure_delay = time.timedelta()
                        departures.append(stop_time.departure_time + departure_delay)
                    stops.append(stop_time.stop(self.static_data))
                    if stop_time.pickup_type == 1:
                        drop_off_only.add(sequence - 1)
                    elif stop_time.drop_off_type == 1:
                        pickup_only.add(sequence - 1)
                for idx in range(len(real_time_statuses)):
                    if not real_time_statuses[idx]:
                        skipped.add(idx)
            else:
                total_stops = len(real_time_statuses)
                for sequence in range(1, total_stops + 1):
                    arrivals.append(custom_arrival_times.get(sequence, None))
                    departures.append(custom_departure_times.get(sequence, None))
                for stop_time in self.real_trip.stop_times:
                    stops.append(load_value(self.static_data, Stop, stop_time.stop_id))
        else:
            total_stops = self.static_trip.total_stops
            stop_times = get_stop_times()
            for stop_time in stop_times:
                arrivals.append(stop_time.arrival_time)
                departures.append(stop_time.departure_time)
                stops.append(stop_time.stop(self.static_data))
                if stop_time.pickup_type == 1:
                    drop_off_only.add(stop_time.sequence - 1)
                elif stop_time.drop_off_type == 1:
                    pickup_only.add(stop_time.sequence - 1)

        # Fix arrival and departure times: if the next stop is left before the previous one, mark all previous stops as already departed from
        for idx in range(total_stops - 1, 1, -1):
            arr_time, dep_time = arrivals[idx], departures[idx]
            if arr_time is None:
                arr_time = time.datetime().min
            if dep_time is None:
                dep_time = time.datetime().max
            if dep_time < arr_time:
                arrivals[idx] = arr_time = dep_time

            prev_arr_time = arrivals[idx - 1]
            if prev_arr_time is None:
                prev_arr_time = time.datetime().min
            prev_dep_time = departures[idx - 1]
            if prev_dep_time is None:
                prev_dep_time = time.datetime().min
            if prev_dep_time > arr_time or prev_arr_time > arr_time:
                arrivals[idx - 1] = departures[idx - 1] = arr_time

        # This is used in the for loop below
        def add_letter(ltr: str):
            if self.compact_mode == 2:
                nonlocal departure
                departure = ltr + departure
            else:
                nonlocal arrival
                arrival = ltr + arrival

        current_stop_marked: bool = False
        fill = len(str(total_stops))
        for idx in range(total_stops):
            seq = f"{idx + 1:0{fill}d})"
            stop = stops[idx]
            code = stop.code_or_id
            name = stop.name

            _arrival = arrivals[idx]
            if _arrival is not None:
                arrival = self.format_time(_arrival)
            else:
                arrival = "  N/A"
                _arrival = time.datetime().min

            _departure = departures[idx]
            if _departure is not None:
                departure = self.format_time(_departure)
            else:
                departure = "  N/A"
                _departure = time.datetime().max

            if idx in pickup_only:
                add_letter("P ")
            elif idx in drop_off_only:
                add_letter("D ")

            if self.cancelled:
                emoji = CANCELLED
            elif idx in skipped:
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

        if pickup_only or drop_off_only:
            extra_text = "\n*D = Drop-off/Alighting only; P = Pick-up/Boarding only*"
        else:
            extra_text = ""

        if self.static_trip:
            trip_id = self.static_trip.trip_id
            destination = self.static_trip.headsign
            route = f"Route {self.route.short_name}"
        else:
            trip_id = self.real_trip.entity_id
            destination = stops[-1].name
            if self.route:
                route = f"Route {self.route.short_name}"
            else:
                route = "Unknown route"

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
            if stops[idx].id == self.stop.id:
                self.current_stop_page = len(paginator.pages) - 1
        return paginator

    def update_output(self):
        self.output = self.create_output()

    def format_time(self, provided_time: time.datetime) -> str:
        """ Format the provided time, showing when a given trip happens outside the current day """
        return format_time(provided_time, self.today)


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
        self.attachment = self.get_attachment()
        self.output: str = self.create_output()

    @classmethod
    async def load(cls, cog, stop: Stop, zoom: int = DEFAULT_ZOOM):
        image_bio = await get_map_with_buses(stop.latitude, stop.longitude, zoom, cog.vehicle_data, cog.static_data)
        return cls(cog, image_bio, stop, zoom)

    def get_attachment(self):
        """ Generate the Discord attachment from the map image """
        attachment: tuple[discord.File] = (discord.File(self.image, f"{self.stop.id}.png"),)
        return attachment

    async def refresh(self):
        """ Refresh the map with new data """
        _, self.vehicle_data = await self.cog.load_real_time_data(debug=self.cog.DEBUG, write=self.cog.WRITE)
        await self.update_map()
        self.update_output()

    async def update_map(self):
        """ Update the map output without refreshing the vehicle data """
        self.image = await get_map_with_buses(self.stop.latitude, self.stop.longitude, self.zoom, self.cog.vehicle_data, self.cog.static_data)
        self.attachment = self.get_attachment()

    def create_output(self) -> str:
        """ Create the text part of the output """
        stop_code = f"Code `{self.stop.code}`, " if self.stop.code else ""
        stop_id = f"ID `{self.stop.id}`"
        data_timestamp = self.vehicle_data.header.timestamp
        output = (f"Buses currently near the stop {self.stop.name} ({stop_code}{stop_id})\n"
                  "The blue circle represents your stop's location, while the green rectangles represent the buses.\n"
                  f"-# Vehicle data timestamp: {data_timestamp:%Y-%m-%d %H:%M:%S} (<t:{int(data_timestamp.timestamp)}:R>)\n"
                  "-# Note: This only shows vehicles whose location is tracked by TFI's real-time data. A vehicle may not show up on this map despite being there in reality.\n"
                  "-# Note: The direction displayed on the map may sometimes be inaccurate.")
        return output

    def update_output(self):
        self.output = self.create_output()
