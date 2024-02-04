import asyncio

import discord
from regaus import time

from utils import views, conworlds, languages
from utils.timetables.shared import TIMEZONE
from utils.timetables.realtime import GTFSRData, VehicleData
from utils.timetables.static import GTFSData, Stop
from utils.timetables.schedules import SpecificStopTime, RealStopTime, StopSchedule, RealTimeStopSchedule


__all__ = ["StopScheduleView"]


class StopScheduleView(views.InteractiveView):
    """ A view for displaying stop schedules for a given stop """
    # TODO: Rewrite this in a less sinful way
    async def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        await self.__init__(*args, **kwargs)
        return self

    async def __init__(self, sender: discord.Member, message: discord.Message, data: GTFSData, stop: Stop,
                 real_time_data: GTFSRData, vehicle_data: VehicleData, now: time.datetime | None = None, lines: int = 6):
        super().__init__(sender=sender, message=message, timeout=900)
        self.data: GTFSData = data
        # Custom time provided
        if now is not None:
            self.now: time.datetime = now
            # Load real-time if the difference is less than 8 hours (8 * 3600 * 1000000)
            self.real_time: bool = abs((now - time.datetime.now()).total_microseconds()) < 28_800_000_000
            self.fixed = True
        # Custom time not provided
        else:
            self.now: time.datetime = time.datetime.now(tz=TIMEZONE)
            self.real_time: bool = True
            self.fixed = False
        self.today: time.date = self.now.date()
        self._stop: Stop = stop
        self.latitude = self._stop.latitude
        self.longitude = self._stop.longitude
        # TODO: Link this to the real_time_data and vehicle_data of the Timetables cog, so that it can be updated properly
        self.real_time_data: GTFSRData = real_time_data
        self.vehicle_data: VehicleData = vehicle_data
        self.lines = lines  # Number of departures to output (default 6, hubs 4)

        # Load the schedules
        self.base_schedule: StopSchedule | None = None
        self.base_stop_times: list[SpecificStopTime] | None = None
        self.real_schedule: RealTimeStopSchedule | None = None
        self.real_stop_times: list[RealStopTime] | None = None
        event_loop = asyncio.get_event_loop()
        await event_loop.run_in_executor(None, self.load_base_schedule)
        # schedule_future = event_loop.run_in_executor(None, self.load_base_schedule)
        # event_loop.run_until_complete(schedule_future)
        # event_loop.create_task(schedule_future)
        if self.real_time:
            await event_loop.run_in_executor(None, self.load_real_schedule)
            # real_time_future = event_loop.run_in_executor(None, self.load_real_schedule)
            # event_loop.run_until_complete(real_time_future)
            # event_loop.create_task(real_time_future)

        self.start_idx, self.end_idx = self.get_indexes()
        # event_loop.run_until_complete(self.create_output())
        # event_loop.create_task(self.create_output())
        await self.create_output()

    def load_base_schedule(self):
        """ Load the static StopSchedule """
        self.base_schedule = StopSchedule(self.data, self._stop.id)
        self.base_stop_times = self.base_schedule.relevant_stop_times(self.today)

    def load_real_schedule(self):
        """ Load the real-time StopSchedule """
        self.real_schedule = RealTimeStopSchedule.from_existing_schedule(self.base_schedule, self.real_time_data, self.vehicle_data, self.base_stop_times)
        self.real_stop_times = self.real_schedule.real_stop_times()

    def get_indexes(self):
        """ Get the value of start_idx and end_idx for the output """
        start_idx = 0
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
        end_idx = start_idx + self.lines + 1
        return start_idx, end_idx

    async def create_output(self):
        """ Create the output from available information and send it to the user """
        language = languages.Language("en")
        output_data: list[list[str]] = [["Route", "Destination", "Schedule", "RealTime", "Distance"]]
        column_sizes = [5, 11, 8, 8, 8]  # Longest member of the column
        extras = False
        if not self.fixed:
            self.start_idx, self.end_idx = self.get_indexes()
        iterable_stop_times = self.real_stop_times if self.real_time else self.base_stop_times
        for stop_time in iterable_stop_times[self.start_idx:self.end_idx]:
            if self.real_time:
                if stop_time.scheduled_departure_time is not None:
                    scheduled_departure_time = stop_time.scheduled_departure_time.format("%H:%M")  # :%S
                else:
                    scheduled_departure_time = "--:--"  # "Unknown"

                if stop_time.schedule_relationship == "CANCELED":
                    real_departure_time = "CANCELLED"
                elif stop_time.schedule_relationship == "SKIPPED":
                    real_departure_time = "SKIPPED"
                elif stop_time.departure_time is not None:
                    real_departure_time = stop_time.departure_time.format("%H:%M")  # :%S
                else:
                    real_departure_time = "--:--"
            else:
                scheduled_departure_time = stop_time.departure_time.format("%H:%M")
                real_departure_time = "N/A"

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

            if self.real_time and stop_time.vehicle is not None:
                distance_km = conworlds.distance_between_places(self.latitude, self.longitude, stop_time.vehicle.latitude, stop_time.vehicle.longitude, "Earth")
                if distance_km >= 1:  # > 1 km
                    distance = language.length(distance_km * 1000, precision=2).split(" | ")[0]
                else:  # < 1 km
                    distance = language.length(round(distance_km * 1000, -2), precision=0).split(" | ")[0]
                distance = distance.replace("\u200c", "")  # Remove ZWS
            elif not self.real_time:
                distance = "N/A"
            else:
                distance = "-"

            column_sizes[0] = max(column_sizes[0], len(route))
            column_sizes[1] = max(column_sizes[1], len(destination))
            column_sizes[2] = max(column_sizes[2], len(scheduled_departure_time))
            column_sizes[3] = max(column_sizes[3], len(real_departure_time))
            column_sizes[4] = max(column_sizes[4], len(distance))

            output_data.append([route, destination, scheduled_departure_time, real_departure_time, distance])

        # Calculate the last line first, in case we need more characters for the destination field
        line_length = sum(column_sizes) + len(column_sizes) - 1
        spaces = line_length - len(self._stop.name) - 18
        extra = 0
        # Add more spaces to destination if there's too few between stop name and current time
        if spaces < 8:
            extra = 8 - spaces
            spaces = 8
        # Example:   "Ballinacurra Close       23 Oct 2023, 18:00"
        last_line = f"{self._stop.name}{' ' * spaces}{self.now:%d %b %Y, %H:%M}```"
        column_sizes[1] += extra  # [1] is destination

        stop_code = f"Code `{self._stop.code}`, " if self._stop.code else ""
        stop_id = f"ID `{self._stop.id}`"
        additional_text = ""
        if extras:
            additional_text += "*D = Drop-off only; P = Pick-up only*\n"
        output = f"Real-Time data for the stop {self._stop.name} ({stop_code}{stop_id})\n" \
                 "*Please note that the distance shown is straight-line distance and as such may not be accurate*\n" \
                 f"{additional_text}```fix\n"
        for line in output_data:
            assert len(column_sizes) == len(line)
            line_data = []
            for i in range(len(line)):
                size = column_sizes[i]
                line_part = line[i]
                # Left-align route and destination to fixed number of spaces
                # Right-align the schedule, real-time info, and distance
                alignment = "<" if i < 2 else ">"
                line_data.append(f"{line_part:{alignment}{size}}")
            output += f"{' '.join(line_data)}\n"
        output += last_line
        if len(output) > 2000:
            output = output[:2000]
        return await self.message.edit(content=output, view=self)
