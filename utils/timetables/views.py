import asyncio
from typing import override

import discord
from regaus import time

from utils import views, conworlds, languages
from utils.timetables.shared import TIMEZONE
from utils.timetables.realtime import GTFSRData, VehicleData
from utils.timetables.static import GTFSData, Stop
from utils.timetables.schedules import SpecificStopTime, RealStopTime, StopSchedule, RealTimeStopSchedule


__all__ = ["StopScheduleViewer", "StopScheduleView"]


WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


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
                   now: time.datetime | None = None, lines: int = 7):
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
        base_schedule, base_stop_times = await event_loop.run_in_executor(None, cls.load_base_schedule, data, stop.id, today)
        if real_time:
            real_schedule, real_stop_times = await event_loop.run_in_executor(None, cls.load_real_schedule, base_schedule, real_time_data, vehicle_data, base_stop_times)
        else:
            real_schedule = real_stop_times = None
        return cls(data, now, real_time, fixed, today, stop, real_time_data, vehicle_data, lines, base_schedule, base_stop_times, real_schedule, real_stop_times, cog)

    @staticmethod
    def load_base_schedule(data: GTFSData, stop_id: str, today: time.date):
        """ Load the static StopSchedule """
        base_schedule = StopSchedule(data, stop_id)
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
        start_idx += self.index_offset
        end_idx = start_idx + self.lines  # We don't need the + 1 here
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
        if not self.fixed:
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
            # If the bus terminates early or departs later than scheduled, show a warning sign at the destination field
            if stop_time.actual_destination is not None or stop_time.actual_start is not None:
                destination = "⚠️ " + destination

            if self.real_time and stop_time.vehicle is not None:
                distance_km = conworlds.distance_between_places(self.latitude, self.longitude, stop_time.vehicle.latitude, stop_time.vehicle.longitude, "Earth")
                if distance_km >= 1:  # > 1 km
                    distance = language.length(distance_km * 1000, precision=2).split(" | ")[0]  # Precision: 0.01km (=10m)
                else:  # < 1 km
                    distance = language.length(round(distance_km * 1000, -1), precision=0).split(" | ")[0]  # Round to nearest 10m
                distance = distance.replace("\u200c", "")  # Remove ZWS
            elif not self.real_time:
                distance = "N/A"
            else:
                distance = "-"

            actual_destination_line = stop_time.actual_destination or ""
            actual_start_line = stop_time.actual_start or ""

            column_sizes[0] = max(column_sizes[0], len(route))
            column_sizes[1] = max(column_sizes[1], len(destination))
            column_sizes[2] = max(column_sizes[2], len(scheduled_departure_time))
            column_sizes[3] = max(column_sizes[3], len(real_departure_time))
            column_sizes[4] = max(column_sizes[4], len(distance))
            column_sizes[5] = max(column_sizes[5], len(actual_destination_line))
            column_sizes[6] = max(column_sizes[6], len(actual_start_line))

            output_data.append([route, destination, scheduled_departure_time, real_departure_time, distance, actual_destination_line, actual_start_line])

        # Calculate the last line first, in case we need more characters for the destination field
        line_length = sum(column_sizes[:-2]) + len(column_sizes) - 3
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
        # Example:   "Ballinacurra Close       23 Oct 2023, 18:00"
        last_line = f"{self.stop.name}{' ' * spaces}{self.now:%d %b %Y, %H:%M}```"
        column_sizes[1] += extra  # [1] is destination
        extra_line_length += extra

        stop_code = f"Code `{self.stop.code}`, " if self.stop.code else ""
        stop_id = f"ID `{self.stop.id}`"
        additional_text = ""
        if extras:
            additional_text += "*D = Drop-off only; P = Pick-up only*\n"
        output = f"Real-Time data for the stop {self.stop.name} ({stop_code}{stop_id})\n" \
                 "*Please note that the vehicle locations and distances may not be accurate*\n" \
                 f"{additional_text}```fix\n"

        for line in output_data:
            assert len(column_sizes) == len(line)
            line_data = []
            for i in range(len(line) - 2):  # Excluding the "actual_destination" and "actual_start"
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

    def format_time(self, provided_time: time.datetime):
        """ Format the provided time, showing when a given trip happens outside the current day """
        formatted = provided_time.format("%H:%M")
        # If the date is not the date of the lookup, then append the weekday of the time
        # If self.now is Tuesday 23:59, then trips at Wednesday 00:00 will be treated as "tomorrow"
        # If self.now is Wednesday 00:00, then trips at Wednesday 00:00 will be treated as "today"
        if provided_time.date() != self.today:
            formatted = f"{WEEKDAYS[provided_time.weekday]} {formatted}"
        return formatted


# noinspection PyUnresolvedReferences
class StopScheduleView(views.InteractiveView):
    """ A view for displaying stop schedules for a given stop """
    def __init__(self, sender: discord.Member, message: discord.Message, schedule: StopScheduleViewer):
        super().__init__(sender=sender, message=message, timeout=3600)
        self.schedule = schedule

        if not self.schedule.fixed:
            self.remove_item(self.unfreeze_schedule)  # Hide the "unfreeze schedule" button
        else:
            self.remove_item(self.freeze_schedule)
        self.remove_item(self.desktop_view)  # Hide the "desktop view" button

    async def refresh(self):
        """ Refresh the real-time data """
        await self.schedule.refresh_real_schedule()
        self.schedule.update_output()
        return await self.message.edit(content=self.schedule.output)

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.primary, row=0)  # Purple, first row
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Refresh the real-time data """
        await interaction.response.defer()
        await self.refresh()
        await self.disable_button(self.message, button, cooldown=30)

    @discord.ui.button(label="Freeze schedule", emoji="🕒", style=discord.ButtonStyle.danger, row=0)  # Red, first row
    async def freeze_schedule(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Freeze the schedule at the current time and index """
        await interaction.response.defer()
        self.schedule.fixed = True
        self.schedule.update_output()
        self.remove_item(button)
        self.remove_item(self.close_view)
        self.add_item(self.unfreeze_schedule)
        self.add_item(self.close_view)
        await self.message.edit(content=self.schedule.output, view=self)

    @discord.ui.button(label="Unfreeze schedule", emoji="🕒", style=discord.ButtonStyle.primary, row=0)  # Red, first row
    async def unfreeze_schedule(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Unfreeze the schedule """
        await interaction.response.defer()
        self.schedule.fixed = False
        self.schedule.update_output()
        self.remove_item(button)
        self.remove_item(self.close_view)
        self.add_item(self.freeze_schedule)
        self.add_item(self.close_view)
        await self.message.edit(content=self.schedule.output, view=self)

    # @discord.ui.button(label="Freeze time", emoji="", style=discord.ButtonStyle.danger, row=0)  # Red, first row
    # async def freeze_time(self, interaction: discord.Interaction, button: discord.ui.Button):
    #     """ Freeze the time being shown """
    #     await interaction.response.defer()
    #     self.schedule.fixed_time = True
    #     self.update_output()
    #     await self.message.edit(content=self.schedule.output, view=self)

    @discord.ui.button(label="Close view", emoji="⏹️", style=discord.ButtonStyle.danger, row=0)  # Red, first row
    async def close_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Close the view """
        await interaction.response.defer()
        await self.message.edit(view=None)
        return await interaction.followup.send("The view has been closed. You may still see the schedule, unless you delete this message.", ephemeral=True)

    async def disable_offset_buttons(self):
        """ Put all the buttons on cooldown at the same time """
        await self.disable_buttons_light(self.message, self.move_up_1, self.move_up_6, self.move_down_1, self.move_down_6, cooldown=3)

    async def move_indexes(self, interaction: discord.Interaction, indexes: int):
        """ Move the departures by the provided amount of indexes (Wrapper function) """
        await interaction.response.defer()
        self.schedule.index_offset += indexes
        self.schedule.update_output()
        await self.message.edit(content=self.schedule.output, view=self)
        word = "down" if indexes > 0 else "up"
        offset = self.schedule.index_offset
        if offset == 0:
            offset_explanation = "zero"
        else:
            word2 = "down" if offset > 0 else "up"
            offset_explanation = f"{abs(offset)} {word2}"
        _s = "s" if abs(indexes) != 1 else ""
        await interaction.followup.send(f"Moved the schedule {word} by {abs(indexes)} departure{_s}. Total offset: {offset_explanation}.", ephemeral=True)
        await self.disable_offset_buttons()

    async def set_offset(self, interaction: discord.Interaction, offset: int):
        """ Set the index offset to a specific value (Wrapper function) """
        await interaction.response.defer()
        self.schedule.index_offset = offset
        self.schedule.update_output()
        await self.message.edit(content=self.schedule.output, view=self)
        if offset == 0:
            content = "The offset has been reset to zero."
        else:
            word = "down" if offset > 0 else "up"
            _s = "s" if abs(offset) != 1 else ""
            content = f"Set the offset to {abs(offset)} departure{_s} {word}."
        await interaction.followup.send(content, ephemeral=True)
        await self.disable_offset_buttons()

    @discord.ui.button(label="Move up 1", emoji="🔼", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def move_up_1(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Show 1 departure above the current """
        return await self.move_indexes(interaction, -1)

    @discord.ui.button(label="Move up 6", emoji="⏫", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def move_up_6(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Show 1 departure above the current """
        return await self.move_indexes(interaction, -6)

    @discord.ui.button(label="Move offset", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def move_offset(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Move offset by a custom amount provided by the user """
        return await interaction.response.send_modal(MoveOffsetModal(self))

    @discord.ui.button(label="Move down 1", emoji="🔽", style=discord.ButtonStyle.secondary, row=2)  # Grey, third row
    async def move_down_1(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Show 1 departure above the current """
        return await self.move_indexes(interaction, 1)

    @discord.ui.button(label="Move down 6", emoji="⏬", style=discord.ButtonStyle.secondary, row=2)  # Grey, third row
    async def move_down_6(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Show 1 departure above the current """
        return await self.move_indexes(interaction, 6)

    @discord.ui.button(label="Set offset", style=discord.ButtonStyle.secondary, row=2)  # Grey, third row
    async def set_offset_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Set offset to a custom amount provided by the user """
        return await interaction.response.send_modal(SetOffsetModal(self))

    @discord.ui.button(label="Reset offset", style=discord.ButtonStyle.primary, row=2)  # Blue, third row
    async def reset_offset(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Reset the offset to zero """
        return await self.set_offset(interaction, 0)

    @discord.ui.button(label="Shorten destinations", style=discord.ButtonStyle.secondary, row=3)  # Grey, last row
    async def mobile_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Mobile-optimised view: Make the text cut off so that it fits on mobile screens """
        await interaction.response.defer()
        self.schedule.truncate_destination = True
        self.schedule.update_output()
        self.remove_item(button)
        self.add_item(self.desktop_view)
        return await self.message.edit(content=self.schedule.output, view=self)

    @discord.ui.button(label="Show full destinations", style=discord.ButtonStyle.secondary, row=3)  # Grey, last row
    async def desktop_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Desktop-optimised view: Stop cutting off text (default behaviour) """
        await interaction.response.defer()
        self.schedule.truncate_destination = False
        self.schedule.update_output()
        self.remove_item(button)
        self.add_item(self.mobile_view)
        return await self.message.edit(content=self.schedule.output, view=self)


class InputModal(discord.ui.Modal):
    """Modal that prompts users for the page number to change to"""
    text_input: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(label="Enter value", style=discord.TextStyle.short, placeholder="0")

    def __init__(self, interface: StopScheduleView, title: str = "Modal"):
        super().__init__(title=title, timeout=interface.timeout)
        self.interface = interface
        self.minimum = 0  # Override this in subclasses
        self.maximum = 0  # Override this in subclasses

    async def submit_handler(self, interaction: discord.Interaction, value: int):
        """ Handle the user input """
        raise NotImplementedError("This method must be implemented by subclasses")

    # noinspection PyUnresolvedReferences
    async def on_submit(self, interaction: discord.Interaction):
        """ This is called when a value is submitted to this modal """
        try:
            if not self.text_input.value:
                raise ValueError("Value was not filled")
            value = int(self.text_input.value)
            if value < self.minimum:
                return await interaction.response.send_message(f"Value must be greater than {self.minimum}.", ephemeral=True)
            if value > self.maximum:
                return await interaction.response.send_message(f"Value must be less than {self.maximum}.", ephemeral=True)
            return await self.submit_handler(interaction, value)
        except ValueError:
            if self.text_input.value:
                content = f"`{self.text_input.value}` could not be converted to a valid number."
            else:
                content = f"You need to enter a value."
            await interaction.response.send_message(content=content, ephemeral=True)


class MoveOffsetModal(InputModal):
    def __init__(self, interface: StopScheduleView):
        super().__init__(interface, "Move Offset")
        self.schedule = self.interface.schedule
        self.minimum = -self.schedule.start_idx  # + self.schedule.index_offset
        self.maximum = len(self.schedule.iterable_stop_times) - self.schedule.start_idx - self.schedule.lines
        self.text_input.label = f"Amount to move offset by ({self.minimum} - {self.maximum}):"
        self.text_input.min_length = 1
        self.text_input.max_length = max(len(str(self.minimum)), len(str(self.maximum)))

    @override
    async def submit_handler(self, interaction: discord.Interaction, value: int):
        return await self.interface.move_indexes(interaction, value)


class SetOffsetModal(InputModal):
    def __init__(self, interface: StopScheduleView):
        super().__init__(interface, "Set Offset")
        self.schedule = self.interface.schedule
        self.minimum = -self.schedule.start_idx + self.schedule.index_offset
        self.maximum = len(self.schedule.iterable_stop_times) - self.schedule.start_idx - self.schedule.lines + self.schedule.index_offset
        self.text_input.label = f"Set new offset to ({self.minimum} - {self.maximum}):"
        self.text_input.min_length = 1
        self.text_input.max_length = max(len(str(self.minimum)), len(str(self.maximum)))

    @override
    async def submit_handler(self, interaction: discord.Interaction, value: int):
        return await self.interface.set_offset(interaction, value)
