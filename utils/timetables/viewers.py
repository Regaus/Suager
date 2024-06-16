import asyncio

from regaus import time

from utils import conworlds, languages, paginators
from utils.timetables.realtime import GTFSRData, VehicleData, TripUpdate
from utils.timetables.schedules import SpecificStopTime, RealStopTime, StopSchedule, RealTimeStopSchedule
from utils.timetables.shared import TIMEZONE, WEEKDAYS, WARNING
from utils.timetables.static import GTFSData, Stop, load_value, Trip, StopTime, Route

__all__ = ["StopScheduleViewer", "TripDiagramViewer"]


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

        self.truncate_destination = False  # Don't cut off destinations by default
        self.index_offset = 0

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
        new_schedule.truncate_destination = self.truncate_destination
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
        self.real_time_data, self.vehicle_data = await self.cog.load_real_time_data(debug=False, write=False)
        self.real_schedule, self.real_stop_times = await event_loop.run_in_executor(None, self.load_real_schedule, self.base_schedule, self.real_time_data, self.vehicle_data, self.base_stop_times)
        if not self.fixed:  # _time:
            self.now = time.datetime.now(tz=TIMEZONE)
            self.today = self.now.date()

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
        extras = False
        # I don't think this should be there - for fixed schedules, self.now should not change
        # if not self.fixed:
        self.start_idx, self.end_idx = self.get_indexes()
        # iterable_stop_times = self.real_stop_times if self.real_time else self.base_stop_times
        for stop_time in self.iterable_stop_times[self.start_idx:self.end_idx]:
            if self.real_time:
                if stop_time.scheduled_departure_time is not None:
                    scheduled_departure_time = self.format_time(stop_time.scheduled_departure_time)
                    # scheduled_departure_time = stop_time.scheduled_departure_time.format("%H:%M")  # :%S
                else:
                    scheduled_departure_time = "--:--"  # "Unknown"

                if stop_time.schedule_relationship == "CANCELED":
                    real_departure_time = "CANCELLED"
                elif stop_time.schedule_relationship == "SKIPPED":
                    real_departure_time = "SKIPPED"
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
                scheduled_departure_time = "D " + scheduled_departure_time
                extras = True
            elif stop_time.drop_off_type == 1:
                scheduled_departure_time = "P " + scheduled_departure_time
                extras = True

            _route = stop_time.route(self.data)
            if _route is None:
                route = "Unknown"
            else:
                route = _route.short_name

            destination = stop_time.destination(self.data)
            # If the bus terminates early or departs later than scheduled, show a warning sign at the destination field
            if stop_time.actual_destination is not None or stop_time.actual_start is not None:
                destination = WARNING + destination

            if self.real_time and stop_time.vehicle is not None:
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
        if self.truncate_destination:
            if line_length > 50:
                cutoff = column_sizes[1] - (line_length - 50)  # Max length of the destination to fit the line
                line_length = 50
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
        if spaces < 8:
            extra = 8 - spaces
            spaces = 8
        if self.truncate_destination and (line_length + extra) > 50:
            extra = 50 - line_length
            last_line = f"{self.stop.name[:23]}…{' ' * spaces}{self.now:%d %b %Y, %H:%M}```"
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
        self.now = stop_schedule.now
        self.today = stop_schedule.today
        # self.fixed = stop_schedule.fixed  # Do we even need this here?
        self.real_time_data = stop_schedule.real_time_data
        self.vehicle_data = stop_schedule.vehicle_data  # Not used here right now, but might be useful later.
        self.cog = stop_schedule.cog

        self.static_trip: Trip | None = None
        self.real_trip: TripUpdate | None = None
        self.trip_identifier: str = trip_id
        self.cancelled: bool = False
        _type = 0
        static_trip_id, real_trip_id, _day_modifier = trip_id.split("|")
        if static_trip_id:
            self.static_trip: Trip = load_value(self.static_data, Trip, static_trip_id)
            _type += 1
        if real_trip_id:
            self.real_trip: TripUpdate = self.real_time_data.entities[real_trip_id]
            if self.real_trip.trip.schedule_relationship == "CANCELED":
                self.cancelled = True
            _type += 2
        self.type: int = _type
        self.type_name: str = ("static", "added", "real")[_type - 1]
        self.timedelta = time.timedelta(days=int(_day_modifier))

        self.current_stop_page: int | None = None
        self.output = self.create_output()

    async def refresh_real_time_data(self):
        self.real_time_data, self.vehicle_data = await self.cog.load_real_time_data()  # type: GTFSRData, VehicleData
        if self.real_trip:
            # Find new real-time information about this trip
            real_trip = None
            if self.type_name == "added":
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
            # real_trip = self.real_time_data.entities.get(self.real_trip.entity_id, None)
            # if (not real_trip and self.static_trip) or (self.static_trip and real_trip.trip.trip_id != self.static_trip.trip_id):
            #     for entity in self.real_time_data.entities.values():
            #         if entity.trip.trip_id == self.static_trip.trip_id:
            #             real_trip = entity
            #             break
            if real_trip:
                self.real_trip = real_trip
        # if not self.fixed:
        self.now = time.datetime.now(tz=TIMEZONE)
        self.today = self.now.date()

    def create_output(self) -> paginators.LinePaginator:
        output_data: list[list[str]] = [["Seq", "Code", "Stop Name", "Arrival", "Departure", "Status"]]
        column_sizes: list[int] = [3, 4, 9, 9, 9, 6]
        alignments: tuple[str, ...] = ("<", ">", "<", ">", ">", "<")

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
                extend_list(arrival_delays, repetitions)
                extend_list(departure_delays, repetitions)
                real_time_statuses.append(stop_time_update.schedule_relationship != "SKIPPED")
                arrival_delays.append(stop_time_update.arrival_delay)
                departure_delays.append(stop_time_update.departure_delay)
                if stop_time_update.arrival_time is not None:
                    custom_arrival_times[sequence] = stop_time_update.arrival_time
                if stop_time_update.departure_time is not None:
                    custom_departure_times[sequence] = stop_time_update.departure_time
                prev_sequence = sequence
            if self.static_trip:
                total_stops = self.static_trip.total_stops
                remaining = total_stops - len(real_time_statuses)
                extend_list(real_time_statuses, remaining)
                extend_list(arrival_delays, remaining)
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
            if idx in pickup_only:
                arrival = "P " + arrival
            elif idx in drop_off_only:
                arrival = "D " + arrival

            _departure = departures[idx]
            if _departure is not None:
                departure = self.format_time(_departure)
            else:
                departure = "  N/A"
                _departure = time.datetime().max

            if self.cancelled:
                status = "Cancelled"
            elif idx in skipped:
                status = "Stop Skipped"
            elif self.now < _arrival:
                status = "Not yet arrived"
            elif self.now < _departure:
                status = "Arrived"
            else:
                status = "Departed"

            output_line = [seq, code, name, arrival, departure, status]
            for i, element in enumerate(output_line):
                column_sizes[i] = max(column_sizes[i], len(element))

            output_data.append(output_line)

        if self.cancelled:
            note = f"\n{WARNING}Note: This trip was cancelled."
        elif self.type_name == "added":
            note = f"\n{WARNING}Note: This trip was not scheduled."
        elif self.type_name == "static":
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
            _route: Route = self.static_trip.route(self.static_data)
            route = f"Route {_route.short_name}"
        else:
            trip_id = self.real_trip.entity_id
            destination = stops[-1].name
            try:
                _route: Route = load_value(self.static_data, Route, self.real_trip.trip.route_id)
                route = f"Route {_route.short_name}"
            except KeyError:
                route = "Unknown route"

        line_length = sum(column_sizes) + len(column_sizes) - 1
        spaces = line_length - len(self.stop.name) - 18
        extra = 0
        # Add more spaces to destination if there's too few between stop name and current time
        if spaces < 8:
            extra = 8 - spaces
            spaces = 8
        column_sizes[2] += extra  # [1] is destination
        output_end = f"{self.stop.name}{' ' * spaces}{self.now:%d %b %Y, %H:%M}```"

        def generate_line(_line: list[str]):
            line_data = []
            for _i in range(len(_line)):
                size = column_sizes[_i]
                line_part = _line[_i]
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
