from __future__ import annotations

import asyncio
import json
from typing import override

import discord
from regaus import time

from utils import views, emotes, commands
from utils.general import alphanumeric_sort_string
from utils.timetables.maps import DEFAULT_ZOOM
from utils.timetables.shared import get_data_database, NUMBERS, TIMEZONE
from utils.timetables.viewers import *
from utils.views import NumericInputModal, SelectMenu

__all__ = ("StopScheduleView", "HubScheduleView", "TripDiagramView", "TripMapView", "MapView",
           "VehicleDataView", "RouteVehiclesView", "RouteScheduleView")


class StopScheduleView(views.InteractiveView):
    """ A view for displaying stop schedules for a given stop """
    def __init__(self, sender: discord.Member, message: discord.Message, viewer: StopScheduleViewer, ctx: commands.Context | discord.Interaction = None):
        super().__init__(sender=sender, message=message, timeout=3600, ctx=ctx)
        self.viewer = viewer
        self.data_db = get_data_database()
        self.refreshing: bool = False

        self.update_freeze_button()

        if not self.viewer.real_time:
            self.remove_item(self.refresh_button)
            self.remove_item(self.freeze_unfreeze_schedule)

        self.route_filter_selector = RouteFilterSelector(self)
        if self.route_filter_selector.options:  # Don't add the selector if it's empty
            self.add_item(self.route_filter_selector)
        self.route_line_selector = RouteLineSelector(self)
        if self.route_line_selector.options:  # Don't add the selector if it's empty
            self.add_item(self.route_line_selector)
        self._route_line_selector_shown = bool(self.route_line_selector.options)

        self.reset_route_filter.disabled = not self.viewer.base_schedule.route_filter_exists  # Filter enabled -> button enabled
        self.reset_route_filter.print_override = True

    async def refresh(self):
        """ Refresh the real-time data """
        self.refreshing = True
        try:
            await self.viewer.refresh_real_schedule()
            self.viewer.update_output()
            self.route_line_selector.update_options()
            await self.message.edit(content=self.viewer.output, view=self)
        finally:
            self.refreshing = False

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.primary, row=0)  # Blue, first row
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Refresh the real-time data """
        await interaction.response.defer()  # type: ignore
        if self.refreshing:
            return await interaction.followup.send("The data is already being refreshed, please wait.", ephemeral=True)
        await self.refresh()
        await self.disable_button(self.message, button, cooldown=60)

    def update_freeze_button(self):
        if self.viewer.fixed:
            self.freeze_unfreeze_schedule.label = "Unfreeze schedule"
            self.freeze_unfreeze_schedule.style = discord.ButtonStyle.primary
        else:
            self.freeze_unfreeze_schedule.label = "Freeze schedule"
            self.freeze_unfreeze_schedule.style = discord.ButtonStyle.danger

    @discord.ui.button(label="Freeze schedule", emoji="🕒", style=discord.ButtonStyle.danger, row=0)  # Red/Blue, first row
    async def freeze_unfreeze_schedule(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Freeze the schedule at the current time and index - or let it move again """
        await interaction.response.defer()  # type: ignore
        self.viewer.fixed ^= True
        self.viewer.update_output()
        self.update_freeze_button()
        return await self.message.edit(content=self.viewer.output, view=self)

    def update_compact_mode_button(self):
        labels = {  # Current state number -> next state
            0: "Shorten destinations",
            1: "Compact mode",
            2: "Show full destinations"
        }
        self.mobile_desktop_view.label = labels[self.viewer.compact_mode]

    @discord.ui.button(label="Shorten destinations", style=discord.ButtonStyle.secondary, row=0)  # Grey, first row
    async def mobile_desktop_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Toggle cutting off destination text to make sure that it fits on a mobile screen """
        await interaction.response.defer()  # type: ignore
        self.viewer.compact_mode = (self.viewer.compact_mode + 1) % 3
        self.viewer.update_output()
        self.update_compact_mode_button()
        return await self.message.edit(content=self.viewer.output, view=self)

    @discord.ui.button(label="Hide view", emoji="⏸️", style=discord.ButtonStyle.secondary, row=0)  # Grey, first row
    async def hide_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Hide the view, instead of closing it altogether. """
        await interaction.response.defer()  # type: ignore
        await self.message.edit(view=views.HiddenView(self))
        # return await interaction.followup.send("The view has been hidden. Use the Restore button to restore this view.", ephemeral=True)

    @discord.ui.button(label="Close view", emoji="⏹️", style=discord.ButtonStyle.danger, row=0)  # Red, first row
    async def close_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Close the view """
        await interaction.response.defer()  # type: ignore
        await self.message.edit(view=None)
        # return await interaction.followup.send("The view has been closed. You may still see the schedule, unless you delete this message.", ephemeral=True)

    # async def disable_offset_buttons(self):
    #     """ Put all the buttons on cooldown at the same time """
    #     await self.disable_buttons_light(self.message, self.move_up_1, self.move_up_6, self.move_down_1, self.move_down_6, self.set_offset_button, self.move_offset, self.reset_offset, cooldown=3)

    async def move_indexes(self, interaction: discord.Interaction, indexes: int):
        """ Move the departures by the provided amount of indexes (Wrapper function) """
        await interaction.response.defer()  # type: ignore
        limit_reached = False
        _minimum = -self.viewer.start_idx
        # When the start index moves into the future, the "maximum" value may become out of bounds... Is it worth investigating and fixing though?
        _maximum = len(self.viewer.iterable_stop_times) - self.viewer.start_idx - self.viewer.lines
        if _maximum < _minimum:
            _maximum = _minimum
        if indexes < _minimum:
            indexes = _minimum
            limit_reached = True
        elif indexes > _maximum:
            indexes = _maximum
            limit_reached = True
        self.viewer.index_offset += indexes
        self.viewer.update_output()
        self.route_line_selector.update_options()
        await self.message.edit(content=self.viewer.output, view=self)
        word = "down" if indexes > 0 else "up"
        offset = self.viewer.index_offset
        if offset == 0:
            offset_explanation = "zero"
        else:
            word2 = "down" if offset > 0 else "up"
            offset_explanation = f"{abs(offset)} {word2}"
        _s = "s" if abs(indexes) != 1 else ""
        _limit = ""
        if limit_reached:
            _limit = " Maximum offset reached."
        await interaction.followup.send(f"Moved the schedule {word} by {abs(indexes)} departure{_s}. Total offset: {offset_explanation}.{_limit}", ephemeral=True)
        # await self.disable_offset_buttons()

    async def set_offset(self, interaction: discord.Interaction, offset: int):
        """ Set the index offset to a specific value (Wrapper function) """
        await interaction.response.defer()  # type: ignore
        # The limit behaviour should not be implemented here - otherwise, the "Reset offset" will break for schedules that are too small (Example: stop 835000014)
        self.viewer.index_offset = offset
        self.viewer.update_output()
        self.route_line_selector.update_options()
        await self.message.edit(content=self.viewer.output, view=self)
        if offset == 0:
            content = "The offset has been reset to zero."
        else:
            word = "down" if offset > 0 else "up"
            _s = "s" if abs(offset) != 1 else ""
            content = f"Set the offset to {abs(offset)} departure{_s} {word}."
        await interaction.followup.send(content, ephemeral=True)
        # await self.disable_offset_buttons()

    @staticmethod
    def change_departure_button_text(button: discord.ui.Button, next_lines: int):
        """ Change the text of the Shrink/Expand departures buttons based on the current state """
        emoji = {4: "4️⃣", 7: "7️⃣", 10: "🔟"}
        button.label = f"Show {next_lines} departures"
        button.emoji = emoji[next_lines]

    def change_move_button_text(self):
        lines = self.viewer.lines - 1
        self.move_up_6.label = f"Move up {lines}"
        self.move_down_6.label = f"Move up {lines}"

    @discord.ui.button(label="Move up 1", emoji="🔼", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def move_up_1(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Show 1 departure above the current """
        return await self.move_indexes(interaction, -1)

    @discord.ui.button(label="Move up 6", emoji="⏫", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def move_up_6(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Show 1 departure above the current """
        return await self.move_indexes(interaction, -(self.viewer.lines - 1))

    @discord.ui.button(label="Show 4 departures", emoji="4️⃣", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def shrink_departures(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Show less departures.

         Behaviour depends on current state:
         4 departures -> Expand to 7
         7 departures -> Shrink to 4
         10 departures -> Shrink to 4 """
        await interaction.response.defer()  # type: ignore
        if self.viewer.lines == 4:
            self.viewer.lines = 7
            self.change_departure_button_text(button, 4)
        else:
            self.viewer.lines = 4
            self.change_departure_button_text(button, 7)
        self.change_departure_button_text(self.expand_departures, 10)
        self.change_move_button_text()
        self.viewer.update_output()
        await self.message.edit(content=self.viewer.output, view=self)

    @discord.ui.button(label="Move offset", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def move_offset(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Move offset by a custom amount provided by the user """
        return await interaction.response.send_modal(MoveOffsetModal(self))  # type: ignore

    @discord.ui.button(label="Reset route filter", style=discord.ButtonStyle.primary, row=1)  # Blue, second row
    async def reset_route_filter(self, interaction: discord.Interaction, _: discord.Button):
        """ Reset the route filter - Show all departures regardless of route """
        if not self.viewer.base_schedule.route_filter_exists:
            return await interaction.response.send_message("There is already no route filter applied to this stop!", ephemeral=True)  # type: ignore
        return await self.apply_route_filter(interaction, values=None)

    @discord.ui.button(label="Move down 1", emoji="🔽", style=discord.ButtonStyle.secondary, row=2)  # Grey, third row
    async def move_down_1(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Show 1 departure above the current """
        return await self.move_indexes(interaction, 1)

    @discord.ui.button(label="Move down 6", emoji="⏬", style=discord.ButtonStyle.secondary, row=2)  # Grey, third row
    async def move_down_6(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Show 1 departure above the current """
        return await self.move_indexes(interaction, self.viewer.lines - 1)

    @discord.ui.button(label="Show 10 departures", emoji="🔟", style=discord.ButtonStyle.secondary, row=2)  # Grey, third row
    async def expand_departures(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Show more departures.

         Behaviour depends on current state:
         4 departures -> Expand to 10
         7 departures -> Expand to 10
         10 departures -> Shrink to 7 """
        await interaction.response.defer()  # type: ignore
        if self.viewer.lines == 10:
            self.viewer.lines = 7
            self.change_departure_button_text(button, 10)
        else:
            self.viewer.lines = 10
            self.change_departure_button_text(button, 7)
        self.change_departure_button_text(self.shrink_departures, 4)
        self.change_move_button_text()
        self.viewer.update_output()
        await self.message.edit(content=self.viewer.output, view=self)

    @discord.ui.button(label="Set offset", style=discord.ButtonStyle.secondary, row=2)  # Grey, third row
    async def set_offset_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Set offset to a custom amount provided by the user """
        return await interaction.response.send_modal(SetOffsetModal(self))  # type: ignore

    @discord.ui.button(label="Reset offset", style=discord.ButtonStyle.primary, row=2)  # Blue, third row
    async def reset_offset(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Reset the offset to zero """
        return await self.set_offset(interaction, 0)

    async def apply_route_filter(self, interaction: discord.Interaction, values: list[str] | None):
        await interaction.response.defer()  # type: ignore
        await self.message.edit(content=f"{emotes.Loading} Updating the route filter for this stop... This may take up to a minute.", view=None)
        user_id = self.sender.id
        stop_id = self.viewer.stop.id
        if values is not None:
            db_values = json.dumps(values)
            if self.viewer.base_schedule.route_filter_exists:
                self.data_db.execute("UPDATE route_filters SET routes=? WHERE user_id=? AND stop_id=?", (db_values, user_id, stop_id))
            else:
                self.data_db.execute("INSERT INTO route_filters(user_id, stop_id, routes) VALUES (?, ?, ?)", (user_id, stop_id, db_values))
            self.reset_route_filter.disabled = False
        else:
            self.data_db.execute("DELETE FROM route_filters WHERE user_id=? AND stop_id=?", (user_id, stop_id))
            self.reset_route_filter.disabled = True
        self.viewer = await self.viewer.reload()
        self.route_line_selector.viewer = self.viewer
        self.route_line_selector.update_options()
        if self.route_line_selector.options and not self._route_line_selector_shown:
            self.add_item(self.route_line_selector)
            self._route_line_selector_shown = True
        elif not self.route_line_selector.options and self._route_line_selector_shown:
            self.remove_item(self.route_line_selector)
            self._route_line_selector_shown = False
        await self.message.edit(content=self.viewer.output, view=self)
        if values is not None:
            return await interaction.followup.send(f"From now on, this stop will only show departures for the following routes: {', '.join(values)}.\n"
                                                   f"Note: This setting will persist the next time you look up the schedule for this same stop.\n"
                                                   f"To change the list of routes to filter, simply select your new choices in the menu.\n"
                                                   f"To remove the filter, use the \"Reset route filter\" button.")
        else:
            return await interaction.followup.send("The route filter for this stop has been disabled, and all departures will be shown regardless of route.\n"
                                                   "If you want to only see certain routes again, use the \"Filter Routes\" select menu to choose which routes you want to see.")


class MoveOffsetModal(NumericInputModal):
    """ Modal for moving the offset by a certain number """
    interface: StopScheduleView

    def __init__(self, interface: StopScheduleView):
        super().__init__(interface, "Move Offset")
        self.viewer = self.interface.viewer
        self.minimum = -self.viewer.start_idx  # + self.viewer.index_offset
        self.maximum = len(self.viewer.iterable_stop_times) - self.viewer.start_idx - self.viewer.lines
        if self.maximum < self.minimum:
            self.maximum = self.minimum
        self.text_input.label = f"Amount to move offset by ({self.minimum} - {self.maximum}):"
        self.text_input.min_length = 1
        self.text_input.max_length = max(len(str(self.minimum)), len(str(self.maximum)))

    @override
    async def submit_handler(self, interaction: discord.Interaction, value: int):
        return await self.interface.move_indexes(interaction, value)


class SetOffsetModal(NumericInputModal):
    """ Modal for setting the offset to a certain number """
    interface: StopScheduleView

    def __init__(self, interface: StopScheduleView):
        super().__init__(interface, "Set Offset")
        self.viewer = self.interface.viewer
        self.minimum = -self.viewer.start_idx + self.viewer.index_offset
        self.maximum = len(self.viewer.iterable_stop_times) - self.viewer.start_idx - self.viewer.lines + self.viewer.index_offset
        if self.maximum < self.minimum:
            self.maximum = self.minimum
        self.text_input.label = f"Set new offset to ({self.minimum} - {self.maximum}):"
        self.text_input.min_length = 1
        self.text_input.max_length = max(len(str(self.minimum)), len(str(self.maximum)))

    @override
    async def submit_handler(self, interaction: discord.Interaction, value: int):
        return await self.interface.set_offset(interaction, value)


class RouteFilterSelector(SelectMenu):
    """ Select menu for routes to filter """
    interface: StopScheduleView

    def __init__(self, interface: StopScheduleView | HubRouteFilterView):
        super().__init__(interface, placeholder="Filter Routes", min_values=1, max_values=25, options=[], row=3)

        values = set()

        if isinstance(self.interface, StopScheduleView):
            iterable = self.interface.viewer.base_schedule.all_routes
        elif isinstance(self.interface, HubRouteFilterView):
            iterable = self.interface.original_view.viewer.base_schedules[self.interface.stop_idx].all_routes
        else:
            raise TypeError(f"{self.__class__.__name__} received unexpected interface class {self.interface.__class__.__name__}")

        for route in iterable[:25]:  # If there are more than 25 routes passing through the stop, tough luck.
            name = f"Route {route.short_name}"
            description = route.long_name
            if route.short_name == "rail":
                value = f"{route.short_name} {route.long_name}"
            else:
                value = route.short_name
            # Prevent crashing from duplicate bus route numbers
            if value not in values:
                self.add_option(value=value, label=name, description=description)
                values.add(value)

        self.options.sort(key=lambda x: alphanumeric_sort_string(x.value))
        self.max_values = len(self.options)

    async def callback(self, interaction: discord.Interaction):
        if isinstance(self.interface, StopScheduleView):
            return await self.interface.apply_route_filter(interaction, self.values)
        elif isinstance(self.interface, HubRouteFilterView):
            return await self.interface.original_view.apply_route_filter(interaction, self.interface.stop_idx, self.values, self.interface.message)


class RouteLineSelector(SelectMenu):
    """ Select menu for a trip whose line diagram should be shown """
    interface: StopScheduleView

    def __init__(self, interface: StopScheduleView):
        super().__init__(interface, placeholder="See details about trip", min_values=1, max_values=1, options=[], row=4)

        self.viewer = self.interface.viewer
        self.data = self.viewer.static_data
        self.real_time = self.viewer.real_time
        self.train_departures: dict[str, bool] = {}
        self.set_options()

    def set_options(self):
        """ Set options to the currently shown trips """
        self.train_departures = {}
        stop_times = self.viewer.iterable_stop_times[slice(*self.viewer.get_indexes(custom_lines=10))]
        for i, stop_time in enumerate(stop_times, start=1):
            if stop_time.actual_destination:
                destination = stop_time.actual_destination.replace("Terminates at ", "")
            else:
                destination = stop_time.destination(self.data)
            name = f"{self.viewer.format_time(stop_time.available_departure_time)} to {destination}"
            if stop_time.is_added:
                value = f"|{stop_time.trip_id}"
            elif stop_time.real_time and hasattr(stop_time.real_trip, "entity_id"):
                trip_id = stop_time.trip_id
                real_trip_id = stop_time.real_trip.entity_id
                value = f"{trip_id}|{real_trip_id}"
            else:
                value = f"{stop_time.trip_id}|"
            value = f"{value}|{stop_time.day_modifier}"
            _route = stop_time.route(self.data)
            if _route is None:
                route = "Unknown route"
            else:
                route = f"Route {_route.short_name}"
            self.train_departures[value] = getattr(stop_time, "is_train_departure", False)
            self.add_option(value=value, label=name, description=route, emoji=NUMBERS[i])

    def update_options(self):
        """ Update the list of options """
        self.reset_options()
        self.set_options()

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()  # type: ignore
        message: discord.WebhookMessage = await interaction.followup.send(f"{emotes.Loading} Loading data about the trip...", wait=True)
        if not self.interface.temporary:
            try:
                message: discord.Message = await message.fetch()
            except (discord.HTTPException, discord.Forbidden, discord.NotFound):  # Unable to load the message
                pass
        viewer = TripDiagramViewer(self.interface, self.values[0], self.train_departures[self.values[0]])
        view = TripDiagramView(interaction.user, message, viewer, try_full_fetch=False)
        return await view.update_message()


class HubScheduleView(views.InteractiveView):
    def __init__(self, sender: discord.Member, message: discord.Message, viewer: HubScheduleViewer, ctx: commands.Context | discord.Interaction = None):
        super().__init__(sender=sender, message=message, timeout=3600, ctx=ctx)
        self.viewer = viewer
        self.db = get_data_database()
        self.refreshing: bool = False

        self.update_freeze_button()
        if not self.viewer.real_time:
            self.refresh_button.disabled = True
            self.freeze_button.disabled = True
            # self.remove_item(self.refresh_button)
            # self.remove_item(self.freeze_button)
        if len(self.viewer.stops) >= 7:
            self.compact_mode_button.disabled = True
            # self.remove_item(self.compact_mode_button)

        self.button_delta = time.timedelta(minutes=5)  # The delta to jump by on button presses

        self.stop_selector = HubStopSelector(self)
        self.add_item(self.stop_selector)

    async def refresh(self):
        self.refreshing = True
        try:
            await self.viewer.refresh()
            self.viewer.update_output()
            await self.message.edit(content=self.viewer.output, view=self)
        finally:
            self.refreshing = False

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.primary, row=0)  # Blue, first row
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Refresh the real-time data """
        await interaction.response.defer()  # type: ignore
        if self.refreshing:
            return await interaction.followup.send("The data is already being refreshed, please wait.", ephemeral=True)
        await self.refresh()
        await self.disable_button(self.message, button, cooldown=60)

    def update_freeze_button(self):
        if self.viewer.fixed:
            self.freeze_button.label = "Unfreeze schedule"
            self.freeze_button.style = discord.ButtonStyle.primary
        else:
            self.freeze_button.label = "Freeze schedule"
            self.freeze_button.style = discord.ButtonStyle.danger

    @discord.ui.button(label="Freeze schedule", emoji="🕒", style=discord.ButtonStyle.danger, row=0)  # Red/Blue, first row
    async def freeze_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Freeze the schedule at the current time and index - or let it move again """
        await interaction.response.defer()  # type: ignore
        self.viewer.fixed ^= True
        self.viewer.update_output()
        self.update_freeze_button()
        return await self.message.edit(content=self.viewer.output, view=self)

    def update_compact_mode_button(self):
        self.compact_mode_button.label = "Show full destinations" if self.viewer.compact_mode else "Shorten destinations"

    @discord.ui.button(label="Shorten destinations", style=discord.ButtonStyle.secondary, row=0)  # Grey, first row
    async def compact_mode_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Toggle cutting off destination text to make sure that it fits on a mobile screen """
        await interaction.response.defer()  # type: ignore
        self.viewer.compact_mode ^= True
        self.viewer.update_output()
        self.update_compact_mode_button()
        return await self.message.edit(content=self.viewer.output, view=self)

    @discord.ui.button(label="Hide view", emoji="⏸️", style=discord.ButtonStyle.secondary, row=0)  # Grey, first row
    async def hide_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Hide the view, instead of closing it altogether. """
        await interaction.response.defer()  # type: ignore
        await self.message.edit(view=views.HiddenView(self))

    @discord.ui.button(label="Close view", emoji="⏹️", style=discord.ButtonStyle.danger, row=0)  # Red, first row
    async def close_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Close the view """
        await interaction.response.defer()  # type: ignore
        await self.message.edit(view=None)

    @staticmethod
    def _format_delta(delta: time.timedelta, is_offset: bool) -> tuple[str, str]:
        """ Return a string version of the delta """
        def _s(number: int) -> str:
            return "s" if number != 1 else ""

        seconds = int(delta.total_seconds())
        if seconds < 0:
            seconds *= -1
            word = " behind" if is_offset else "back"
        elif seconds > 0:
            word = " ahead" if is_offset else "forwards"
        else:
            return "zero", ""
        hours, ms = divmod(seconds, 3600)
        minutes, seconds = divmod(ms, 60)
        output = []
        if hours:
            output.append(f"{hours} hour{_s(hours)}")
        if minutes:
            output.append(f"{minutes} minute{_s(minutes)}")
        if seconds:
            output.append(f"{seconds} second{_s(seconds)}")
        return ", ".join(output), word

    async def move_time_offset(self, interaction: discord.Interaction, delta: time.timedelta):
        """ Jump back or forwards by a specified time """
        await interaction.response.defer()  # type: ignore
        self.viewer.now += delta
        self.viewer.timedelta += delta
        self.viewer.update_output()
        await self.message.edit(content=self.viewer.output, view=self)
        delta_str, word1 = self._format_delta(delta, False)
        offset_str, word2 = self._format_delta(self.viewer.timedelta, True)
        return await interaction.followup.send(f"Moved the schedule {word1} by {delta_str}. Total offset: {offset_str}{word2}.", ephemeral=True)

    async def set_time_offset(self, interaction: discord.Interaction, offset: time.timedelta):
        """ Set the time offset to the specified delta """
        await interaction.response.defer()  # type: ignore
        if self.viewer.fixed:
            self.viewer.now = self.viewer.base_now + offset
        else:
            self.viewer.now = time.datetime.now(tz=TIMEZONE) + offset
        self.viewer.timedelta = offset
        self.viewer.update_output()
        await self.message.edit(content=self.viewer.output, view=self)
        if not offset:
            return await interaction.followup.send("The offset has been reset to zero.", ephemeral=True)
        offset_str, word = self._format_delta(self.viewer.timedelta, True)
        return await interaction.followup.send(f"Set the time offset to {offset_str}{word}.", ephemeral=True)

    @discord.ui.button(label="Jump 5 minutes back", emoji="◀️", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def jump_back(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Jump 5 minutes back """
        return await self.move_time_offset(interaction, -self.button_delta)

    @discord.ui.button(label="Jump 5 minutes ahead", emoji="▶️", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def jump_ahead(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Jump 5 minutes forwards """
        return await self.move_time_offset(interaction, self.button_delta)

    @discord.ui.button(label="Set offset", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def set_offset(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Set the offset to a specified delta """
        return await interaction.response.send_modal(SetTimeOffsetModal(self))  # type: ignore

    @discord.ui.button(label="Jump to time", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def jump_to_time(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Jump to a user-specified time """
        return await interaction.response.send_modal(JumpToTimeModal(self))  # type: ignore

    async def jump_to_time_response(self, interaction: discord.Interaction, new_time: time.datetime):
        await interaction.response.defer()  # type: ignore
        self.viewer.now = new_time
        self.viewer.base_now = new_time
        self.viewer.fixed = True  # Make the timetable fixed to the new time
        self.update_freeze_button()
        if self.viewer.today == new_time.date():
            self.viewer.timedelta = time.timedelta()
            self.viewer.update_output()
        else:
            await self.message.edit(content=f"{emotes.Loading} Updating the schedule for the specified time...", view=None)
            self.viewer = await self.viewer.reload()
        # If we go to a time far in the future, disable the real-time and freeze buttons
        self.refresh_button.disabled = not self.viewer.real_time
        self.freeze_button.disabled = not self.viewer.real_time
        await self.message.edit(content=self.viewer.output, view=self)
        return await interaction.followup.send(f"Now showing departures for {self.viewer.now:%d %b %Y, %H:%M:%S}.", ephemeral=True)

    @discord.ui.button(label="Reset offset", style=discord.ButtonStyle.primary, row=1)  # Blurple, second row
    async def reset_offset(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Reset the time back to right now """
        return await self.set_time_offset(interaction, time.timedelta())

    async def apply_route_filter(self, interaction: discord.Interaction, stop_idx: int, values: list[str] | None, message: discord.Message):
        await interaction.response.defer()  # type: ignore
        user_id = self.sender.id
        stop = self.viewer.stops[stop_idx]
        stop_id = stop.id
        await self.message.edit(content=f"{emotes.Loading} Updating the route filter for the stop {stop.name}... This may take up to a minute.", view=None)
        await message.edit(content="The route filter is now being updated.", view=None)
        if values is not None:
            db_values = json.dumps(values)
            if self.viewer.base_schedules[stop_idx].route_filter_exists:
                self.db.execute("UPDATE route_filters SET routes=? WHERE user_id=? AND stop_id=?", (db_values, user_id, stop_id))
            else:
                self.db.execute("INSERT INTO route_filters(user_id, stop_id, routes) VALUES (?, ?, ?)", (user_id, stop_id, db_values))
        else:
            self.db.execute("DELETE FROM route_filters WHERE user_id=? AND stop_id=?", (user_id, stop_id))
        self.viewer = await self.viewer.reload()
        await self.message.edit(content=self.viewer.output, view=self)
        if values is not None:
            return await message.edit(content=f"From now on, the stop {stop.name} will only show departures for the following routes: {', '.join(values)}.")
        else:
            return await message.edit(content=f"The route filter for the stop {stop.name} has been disabled, and all departures will be shown regardless of route.")


class HubStopSelector(SelectMenu):
    """ Select menu for routes to filter """
    interface: HubScheduleView

    def __init__(self, interface: HubScheduleView):
        super().__init__(interface, placeholder="Filter Routes", min_values=1, max_values=1, options=[], row=2)
        for i, stop in enumerate(self.interface.viewer.stops):
            self.add_option(value=str(i), label=stop.name, description=f"Stop {stop.code_or_id}", emoji=NUMBERS[i + 1])
        self.print_override = False

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()  # type: ignore
        new_view = HubRouteFilterView(self.interface, self.interface.message, int(self.values[0]))
        new_view.message = await interaction.followup.send(view=new_view, ephemeral=False)
        return new_view


class HubRouteFilterView(views.InteractiveView):
    def __init__(self, original_view: HubScheduleView, message: discord.Message, stop_idx: int):
        super().__init__(original_view.sender, message, try_full_fetch=False)
        self.original_view = original_view
        self.command = f"{self.original_view.command} > {self.__class__.__name__}: {self.original_view.viewer.stops[stop_idx].name}"
        self.stop_idx = stop_idx
        self.route_filter_selector = RouteFilterSelector(self)
        self.route_filter_selector.row = 0
        self.add_item(self.route_filter_selector)
        self.reset_route_filter.disabled = not self.original_view.viewer.base_schedules[self.stop_idx].route_filter_exists
        self.reset_route_filter.print_override = True

    @discord.ui.button(label="Reset route filter", style=discord.ButtonStyle.primary, row=1)
    async def reset_route_filter(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Reset the route filter - Show all departures regardless of route """
        if not self.original_view.viewer.base_schedules[self.stop_idx].route_filter_exists:
            return await interaction.response.send_message("There is already no route filter applied to this stop!", ephemeral=True)  # type: ignore
        return await self.original_view.apply_route_filter(interaction, self.stop_idx, None, self.message)


class PaginatorView(views.InteractiveView):
    def __init__(self, sender: discord.Member, message: discord.Message, viewer: TripDiagramViewer | RouteScheduleViewer, *,
                 ctx: commands.Context | discord.Interaction = None, try_full_fetch: bool = True):
        super().__init__(sender=sender, message=message, timeout=3600, ctx=ctx, try_full_fetch=try_full_fetch)
        self.viewer = viewer
        self.display_page = 0
        self.update_page_labels()
        # Set special names for logging purposes
        self.first_page.log_label = "First page"
        self.prev_page.log_label = "Previous page"
        self.curr_page.log_label = "Current page"
        self.next_page.log_label = "Next page"
        self.last_page.log_label = "Last page"

    @property
    def pages(self) -> list[str]:
        return self.viewer.output.pages

    @property
    def page_count(self):
        return len(self.pages)

    @property
    def page_size(self) -> int:
        return self.viewer.output.max_size

    @property
    def content(self) -> str:
        if self.pages:
            return self.pages[self.display_page]
        return "No data available"

    async def send_initial(self, destination: discord.abc.Messageable):
        """ Send the initial message """
        self.message = await destination.send(self.content, view=self)
        return self.message

    async def update_message(self):
        """ Update the existing message """
        if self.display_page >= self.page_count:
            self.display_page = self.page_count - 1
        self.update_page_labels()
        self.message = await self.message.edit(content=self.content, view=self)
        return self.message

    def update_page_labels(self):
        """ Update the paginator-related button labels to be accurate """
        self.go_to_page.disabled = not self.pages
        if not self.pages:
            self.first_page.label = "0"
            self.curr_page.label = "N/A"
        else:
            self.curr_page.label = str(self.display_page + 1)
        self.last_page.label = str(self.page_count)
        self.first_page.disabled = self.prev_page.disabled = self.display_page <= 0
        self.last_page.disabled = self.next_page.disabled = self.display_page >= self.page_count - 1

    @discord.ui.button(emoji="⏮️", label="1", style=discord.ButtonStyle.secondary, row=0)  # Grey, first row
    async def first_page(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Go to the first page """
        await interaction.response.defer()  # type: ignore
        self.display_page = 0
        return await self.update_message()

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.primary, row=0)  # Blue, first row
    async def prev_page(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Go to the previous page """
        await interaction.response.defer()  # type: ignore
        if self.display_page <= 0:
            return await interaction.followup.send(f"{emotes.Deny} You are already on the first page.", ephemeral=True)
        self.display_page -= 1
        return await self.update_message()

    @discord.ui.button(label="1", style=discord.ButtonStyle.primary, row=0)  # Blue, first row
    async def curr_page(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Indicates the current page number, does nothing """
        await interaction.response.defer()  # type: ignore
        return await self.update_message()

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.primary, row=0)  # Blue, first row
    async def next_page(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Go to the next page """
        await interaction.response.defer()  # type: ignore
        if self.display_page >= self.page_count - 1:
            return await interaction.followup.send(f"{emotes.Deny} You are already on the last page.", ephemeral=True)
        self.display_page += 1
        return await self.update_message()

    @discord.ui.button(emoji="⏭️", label="1", style=discord.ButtonStyle.secondary, row=0)  # Grey, first row
    async def last_page(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Go to the last page """
        await interaction.response.defer()  # type: ignore
        self.display_page = self.page_count - 1
        return await self.update_message()

    @discord.ui.button(label="Go to page", emoji="➡️", style=discord.ButtonStyle.primary, row=1)  # Blue, second row
    async def go_to_page(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Go to a user-specified page """
        return await interaction.response.send_modal(GoToPageModal(self))  # type: ignore


class GoToPageModal(NumericInputModal):
    """ Modal for setting the offset to a certain number """
    interface: PaginatorView

    def __init__(self, interface: PaginatorView):
        super().__init__(interface, "Go to page")
        self.minimum = 1
        self.maximum = self.interface.page_count
        if self.maximum < self.minimum:
            self.maximum = self.minimum
        self.text_input.label = f"Enter page number to go to ({self.minimum} - {self.maximum}):"
        self.text_input.min_length = 1
        self.text_input.max_length = max(len(str(self.minimum)), len(str(self.maximum)))

    @override
    async def submit_handler(self, interaction: discord.Interaction, value: int):
        await interaction.response.defer()  # type: ignore
        self.interface.display_page = value - 1
        return await self.interface.update_message()


class TripDiagramView(PaginatorView):
    """ A view for displaying the list of all stops in a trip """
    viewer: TripDiagramViewer

    def __init__(self, sender: discord.Member, message: discord.Message, viewer: TripDiagramViewer, *, try_full_fetch: bool = True):
        super().__init__(sender=sender, message=message, viewer=viewer, try_full_fetch=try_full_fetch)
        self.display_page = self.viewer.current_stop_page
        self.command = f"{self.__class__.__name__} {self.viewer.trip_identifier}"
        self._stop = self.viewer.stop
        # self.update_compact_mode_button()
        self.refreshing: bool = False

        if not self.viewer.is_real_time:
            self.remove_item(self.refresh_button)

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.primary, row=1)  # Blue, second row
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Refresh the real-time data """
        await interaction.response.defer()  # type: ignore
        if self.refreshing:
            return await interaction.followup.send("The data is already being refreshed, please wait.", ephemeral=True)
        self.refreshing = True
        try:
            await self.viewer.refresh_real_time_data()
            self.viewer.update_output()
            await self.update_message()
            await self.disable_button(self.message, button, cooldown=60)
        finally:
            self.refreshing = False

    def update_compact_mode_button(self):
        labels = {  # Current state number -> next state
            0: "Shorten stop names",
            1: "Compact mode",
            2: "Show full names"
        }
        self.shorten_stop_names.label = labels[self.viewer.compact_mode]

    @discord.ui.button(label="Shorten stop names", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def shorten_stop_names(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Toggle showing shorter or full stop names """
        await interaction.response.defer()  # type: ignore
        self.viewer.compact_mode = (self.viewer.compact_mode + 1) % 3  # rotate between 0, 1, 2
        self.viewer.update_output()
        self.update_compact_mode_button()
        return await self.update_message()

    @discord.ui.button(label="Hide view", emoji="⏸️", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def hide_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Hide the view, instead of closing it altogether """
        await interaction.response.defer()  # type: ignore
        await self.message.edit(view=views.HiddenView(self))

    @discord.ui.button(label="Close view", emoji="⏹️", style=discord.ButtonStyle.danger, row=1)  # Red, second row
    async def close_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Close the view """
        await interaction.response.defer()  # type: ignore
        await self.message.edit(view=None)

    @discord.ui.button(label="Show on a map", emoji="🗺️", style=discord.ButtonStyle.primary, row=2)  # Blue, third row
    async def show_on_map(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Show the trip diagram on a map """
        await interaction.response.defer()  # type: ignore
        # Can't be pressed again
        button.disabled = True
        await self.message.edit(view=self)
        message: discord.WebhookMessage = await interaction.followup.send(f"{emotes.Loading} Loading the map...")
        if not self.temporary:
            try:
                message: discord.Message = await message.fetch()
            except (discord.HTTPException, discord.Forbidden, discord.NotFound):  # Unable to load the message
                pass
        try:
            map_viewer: TripMapViewer = await TripMapViewer.load(self.viewer)
            # map_viewer: TripMapViewer = await TripMapViewer.load(self.viewer.cog, self.viewer.static_trip, self.viewer.stop, self.viewer)
        except Exception:
            raise
        view = TripMapView(interaction.user, message, map_viewer, try_full_fetch=False)
        return await view.update_message()


class TripMapView(views.InteractiveView):
    """ A view for displaying a trip diagram on a map """
    def __init__(self, sender: discord.Member, message: discord.Message, map_viewer: TripMapViewer, ctx: commands.Context | discord.Interaction = None,
                 *, try_full_fetch: bool = True):
        super().__init__(sender=sender, message=message, timeout=3600, ctx=ctx, try_full_fetch=try_full_fetch)
        self.viewer = map_viewer
        self.command = f"{self.__class__.__name__} {self.viewer.trip_id}"
        self.data_db = get_data_database()
        self.refreshing: bool = False
        self.zoom_updating: bool = False
        self.reset_zoom.disabled = True
        self.zoom_out.disabled = True
        self.min_zoom = self.viewer.zoom  # Minimum allowed zoom = default zoom
        self.max_zoom = DEFAULT_ZOOM      # Maximum allowed zoom: 17

    async def update_message(self):
        """ Update the existing message """
        self.message = await self.message.edit(content=self.viewer.output, attachments=self.viewer.attachment, view=self)
        return self.message

    async def refresh(self):
        """ Refresh the real-time data """
        self.refreshing = True
        try:
            await self.viewer.refresh()
            await self.message.edit(content=self.viewer.output, attachments=self.viewer.attachment, view=self)
        finally:
            self.refreshing = False

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.primary, row=0)  # Blue, first row
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Refresh the real-time data """
        await interaction.response.defer()  # type: ignore
        if self.refreshing:
            return await interaction.followup.send("The data is already being refreshed, please wait.", ephemeral=True)
        await self.refresh()
        await self.disable_button(self.message, button, cooldown=60)

    async def update_zoom_buttons(self):
        """ Change the two buttons to be in an appropriate state after a 5s cooldown """
        await asyncio.sleep(5)
        self.reset_zoom.disabled = self.viewer.custom_zoom is None
        self.zoom_out.disabled = self.viewer.zoom_level <= self.min_zoom
        self.zoom_in.disabled = self.viewer.zoom_level >= self.max_zoom
        await self.message.edit(view=self)

    async def zoom_button_response(self, interaction: discord.Interaction, movement: int):
        """ Zoom in or out - common function for the two buttons """
        await interaction.response.defer()  # type: ignore
        if self.zoom_updating:
            return await interaction.followup.send("The map's zoom is already being updated, please wait.", ephemeral=True)
        self.zoom_updating = True
        try:
            if movement:
                self.viewer.zoom_level += movement
            else:
                self.viewer.custom_zoom = None
            await self.viewer.update_map()
            self.viewer.update_output()
            # Disable the zoom buttons for 5 seconds
            self.reset_zoom.disabled = True
            self.zoom_out.disabled = True
            self.zoom_in.disabled = True
            await self.message.edit(content=self.viewer.output, attachments=self.viewer.attachment, view=self)
            await self.update_zoom_buttons()
        finally:
            self.zoom_updating = False

    @discord.ui.button(label="Reset zoom", style=discord.ButtonStyle.primary, row=0)  # Blue, first row
    async def reset_zoom(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Reset the zoom back to normal """
        return await self.zoom_button_response(interaction, 0)

    @discord.ui.button(label="Zoom out", emoji="🗺️", style=discord.ButtonStyle.primary, row=0)  # Blue, first row
    async def zoom_out(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Zoom out on the map """
        return await self.zoom_button_response(interaction, -1)

    @discord.ui.button(label="Zoom in", emoji="🔎", style=discord.ButtonStyle.primary, row=0)  # Blue, first row
    async def zoom_in(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Zoom in on the map - centred around the current stop """
        return await self.zoom_button_response(interaction, 1)

    # @discord.ui.button(label="Hide view", emoji="⏸️", style=discord.ButtonStyle.secondary, row=0)  # Grey, first row
    # async def hide_view(self, interaction: discord.Interaction, _: discord.ui.Button):
    #     """ Hide the view, instead of closing it altogether. """
    #     await interaction.response.defer()
    #     await self.message.edit(view=views.HiddenView(self))

    @discord.ui.button(label="Close view", emoji="⏹️", style=discord.ButtonStyle.danger, row=0)  # Red, first row
    async def close_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Close the view """
        await interaction.response.defer()  # type: ignore
        await self.message.edit(view=None)


class MapView(views.InteractiveView):
    """ A view for displaying buses near a given stop """
    def __init__(self, sender: discord.Member, message: discord.Message, map_viewer: MapViewer, ctx: commands.Context | discord.Interaction = None):
        super().__init__(sender=sender, message=message, timeout=3600, ctx=ctx)
        self.viewer = map_viewer
        self.data_db = get_data_database()
        self.refreshing: bool = False
        self.zoom_updating: bool = False
        self.reset_zoom.disabled = True
        self.min_zoom = DEFAULT_ZOOM - 1  # Minimum allowed zoom: 16
        self.max_zoom = DEFAULT_ZOOM + 1  # Maximum allowed zoom: 18

    async def refresh(self):
        """ Refresh the real-time data """
        self.refreshing = True
        try:
            await self.viewer.refresh()
            await self.message.edit(content=self.viewer.output, attachments=self.viewer.attachment, view=self)
        finally:
            self.refreshing = False

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.primary, row=0)  # Blue, first row
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Refresh the real-time data """
        await interaction.response.defer()  # type: ignore
        if self.refreshing:
            return await interaction.followup.send("The data is already being refreshed, please wait.", ephemeral=True)
        await self.refresh()
        await self.disable_button(self.message, button, cooldown=60)

    async def update_zoom_buttons(self):
        """ Change the two buttons to be in an appropriate state after a 5s cooldown """
        await asyncio.sleep(5)
        self.reset_zoom.disabled = self.viewer.zoom == DEFAULT_ZOOM
        self.zoom_out.disabled = self.viewer.zoom <= self.min_zoom
        self.zoom_in.disabled = self.viewer.zoom >= self.max_zoom
        await self.message.edit(view=self)

    async def zoom_button_response(self, interaction: discord.Interaction, movement: int):
        """ Zoom in or out - common function for the two buttons """
        await interaction.response.defer()  # type: ignore
        if self.zoom_updating:
            return await interaction.followup.send("The map's zoom is already being updated, please wait.", ephemeral=True)
        self.zoom_updating = True
        try:
            if movement:
                self.viewer.zoom += movement
            else:
                self.viewer.zoom = DEFAULT_ZOOM
            await self.viewer.update_map()
            self.viewer.update_output()
            # Disable the zoom buttons for 5 seconds
            self.reset_zoom.disabled = True
            self.zoom_out.disabled = True
            self.zoom_in.disabled = True
            await self.message.edit(content=self.viewer.output, attachments=self.viewer.attachment, view=self)
            await self.update_zoom_buttons()
        finally:
            self.zoom_updating = False

    @discord.ui.button(label="Reset zoom", style=discord.ButtonStyle.primary, row=0)  # Blue, first row
    async def reset_zoom(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Reset the zoom back to normal """
        return await self.zoom_button_response(interaction, 0)

    @discord.ui.button(label="Zoom out", emoji="🗺️", style=discord.ButtonStyle.primary, row=0)  # Blue, first row
    async def zoom_out(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Zoom out on the map """
        return await self.zoom_button_response(interaction, -1)

    @discord.ui.button(label="Zoom in", emoji="🔎", style=discord.ButtonStyle.primary, row=0)  # Blue, first row
    async def zoom_in(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Zoom in on the map """
        return await self.zoom_button_response(interaction, 1)

    # @discord.ui.button(label="Hide view", emoji="⏸️", style=discord.ButtonStyle.secondary, row=0)  # Grey, first row
    # async def hide_view(self, interaction: discord.Interaction, _: discord.ui.Button):
    #     """ Hide the view, instead of closing it altogether. """
    #     await interaction.response.defer()
    #     await self.message.edit(view=views.HiddenView(self))

    @discord.ui.button(label="Close view", emoji="⏹️", style=discord.ButtonStyle.danger, row=0)  # Red, first row
    async def close_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Close the view """
        await interaction.response.defer()  # type: ignore
        await self.message.edit(view=None)


class VehicleDataView(views.InteractiveView):
    def __init__(self, sender: discord.Member, message: discord.Message, viewer: VehicleDataViewer, ctx: commands.Context | discord.Interaction = None):
        super().__init__(sender=sender, message=message, timeout=3600, ctx=ctx)
        self.viewer = viewer
        self.db = get_data_database()
        self.refreshing: bool = False

    async def refresh(self):
        """ Refresh the real-time data """
        self.refreshing = True
        try:
            await self.viewer.refresh()
            await self.message.edit(content=self.viewer.output, view=self)
        finally:
            self.refreshing = False

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.primary, row=0)  # Blue, first row
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Refresh the real-time data """
        await interaction.response.defer()  # type: ignore
        if self.refreshing:
            return await interaction.followup.send("The data is already being refreshed, please wait.", ephemeral=True)
        await self.refresh()
        await self.disable_button(self.message, button, cooldown=60)

    # @discord.ui.button(label="Hide view", emoji="⏸️", style=discord.ButtonStyle.secondary, row=0)  # Grey, first row
    # async def hide_view(self, interaction: discord.Interaction, _: discord.ui.Button):
    #     """ Hide the view, instead of closing it altogether """
    #     await interaction.response.defer()  # type: ignore
    #     await self.message.edit(view=views.HiddenView(self))

    @discord.ui.button(label="Close view", emoji="⏹️", style=discord.ButtonStyle.danger, row=0)  # Red, first row
    async def close_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Close the view """
        await interaction.response.defer()  # type: ignore
        await self.message.edit(view=None)


class RouteVehiclesView(views.InteractiveView):
    def __init__(self, sender: discord.Member, message: discord.Message, viewer: RouteVehiclesViewer, ctx: commands.Context | discord.Interaction = None):
        super().__init__(sender=sender, message=message, timeout=3600, ctx=ctx)
        self.viewer = viewer
        self.db = get_data_database()
        self.refreshing: bool = False
        self.model_list: RouteVehiclesModelListView | None = None

    async def refresh(self):
        """ Refresh the real-time data """
        self.refreshing = True
        try:
            await self.viewer.refresh()
            await self.message.edit(content=self.viewer.output, view=self)
            if self.model_list:
                await self.model_list.refresh()
        finally:
            self.refreshing = False

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.primary, row=0)  # Blue, first row
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Refresh the real-time data """
        await interaction.response.defer()  # type: ignore
        if self.refreshing:
            return await interaction.followup.send("The data is already being refreshed, please wait.", ephemeral=True)
        await self.refresh()
        await self.disable_button(self.message, button, cooldown=60)

    @discord.ui.button(label="List models", style=discord.ButtonStyle.grey, row=0)  # Grey, first row
    async def list_bus_models(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ List the models of buses currently operating on the route """
        await interaction.response.defer()  # type: ignore
        if self.model_list:  # This shouldn't happen, but just in case.
            return await interaction.followup.send("The model list is already open.", ephemeral=True)
        try:
            self.model_list = await RouteVehiclesModelListView.send(interaction, self)
        except RuntimeError:
            return await interaction.followup.send("There are no real-time vehicles operating on this route at the moment.", ephemeral=True)
        else:
            button.disabled = True  # If the user deletes the message, too bad. It will raise an error, but don't send a new message.
            await self.message.edit(view=self)

    async def enable_bus_models_button(self):
        self.model_list = None
        self.list_bus_models.disabled = False
        if not self.is_finished():
            await self.message.edit(view=self)

    # @discord.ui.button(label="Hide view", emoji="⏸️", style=discord.ButtonStyle.secondary, row=0)  # Grey, first row
    # async def hide_view(self, interaction: discord.Interaction, _: discord.ui.Button):
    #     """ Hide the view, instead of closing it altogether """
    #     await interaction.response.defer()  # type: ignore
    #     await self.message.edit(view=views.HiddenView(self))

    @discord.ui.button(label="Close view", emoji="⏹️", style=discord.ButtonStyle.danger, row=0)  # Red, first row
    async def close_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Close the view """
        await interaction.response.defer()  # type: ignore
        await self.message.edit(view=None)
        self.stop()


class RouteVehiclesModelListView(views.InteractiveView):
    def __init__(self, sender: discord.Member, message: discord.Message, original_view: RouteVehiclesView):
        super().__init__(sender=sender, message=message, try_full_fetch=False)
        self.original_view = original_view
        self.viewer = original_view.viewer

    async def refresh(self):
        await self.message.edit(content=self.viewer.vehicle_list_by_model(), view=self)

    @classmethod
    async def send(cls, interaction: discord.Interaction, original_view: RouteVehiclesView):
        view = cls(original_view.sender, original_view.message, original_view)
        message: discord.WebhookMessage = await interaction.followup.send(view.viewer.vehicle_list_by_model(), view=view)
        if original_view.temporary:
            view.message = message
        else:
            view.message = await message.fetch()
        return view

    @discord.ui.button(label="Close", emoji="⏹️", style=discord.ButtonStyle.danger, row=0)  # Red, first row
    async def close_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Close the view and delete the message """
        await interaction.response.defer()  # type: ignore
        await self.message.delete()
        await self.original_view.enable_bus_models_button()
        self.stop()


class RouteScheduleView(PaginatorView):
    viewer: RouteScheduleViewer

    def __init__(self, sender: discord.Member, message: discord.Message, viewer: RouteScheduleViewer, ctx: commands.Context | discord.Interaction = None):
        super().__init__(sender=sender, message=message, viewer=viewer, ctx=ctx)
        self.bot = ctx.bot
        self.first_page.emoji = "<:23ee_up:1280620615702675588>"
        self.prev_page.emoji = "🔼"
        self.next_page.emoji = "🔽"
        self.last_page.emoji = "<:23ee_down:1280620613752590387>"

        self.update_departure_buttons()
        self.update_direction_button()

    @override
    @property
    def content(self) -> str:
        if not self.pages:
            direction = "inbound" if self.viewer.direction == INBOUND_DIRECTION_ID else "outbound"
            return f"There are no {direction} departures on route {self.viewer.route.short_name} on {self.viewer.today:%d %B %Y}."
        return super().content

    @override
    async def update_message(self):
        self.update_departure_buttons()
        return await super().update_message()

    # def page_from_index(self, index: int):
    #     # This may not always be accurate, but oh well
    #     return (index // self.viewer.departures) + 1

    def update_departure_buttons(self):
        self.jump_to_time.disabled = not self.pages  # "Jump to Time" cannot jump to a different date, unlike the HubScheduleView
        if not self.pages:
            self.first_departure.label = "0"
            self.curr_departures.label = "N/A"
        elif self.viewer.departures > 1:
            self.curr_departures.label = f"{self.viewer.start_idx + 1} - {self.viewer.end_idx}"
        else:
            self.curr_departures.label = str(self.viewer.start_idx + 1)
        self.last_departure.label = str(len(self.viewer.relevant_trips))
        self.next_departures.disabled = self.last_departure.disabled = self.viewer.index_offset >= self.max_offset
        self.prev_departures.disabled = self.first_departure.disabled = self.viewer.index_offset <= self.min_offset
        # self.curr_departures.label = str(self.page_from_index(self.viewer.start_idx))
        # self.last_departure.label = str(self.page_from_index(len(self.viewer.relevant_trips) - self.viewer.departures))

    @property
    def min_offset(self):
        return -self.viewer.start_idx + self.viewer.index_offset

    @property
    def max_offset(self):
        return len(self.viewer.relevant_trips) - self.viewer.start_idx - self.viewer.departures + self.viewer.index_offset

    @discord.ui.button(emoji="⏮️", label="1", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def first_departure(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Go to the first departure for today """
        await interaction.response.defer()  # type: ignore
        self.viewer.index_offset = self.min_offset
        self.viewer.update_output()
        return await self.update_message()

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.primary, row=1)  # Blue, second row
    async def prev_departures(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Show the previous departures """
        await interaction.response.defer()  # type: ignore
        if self.viewer.start_idx <= 0:  # Maybe replace with index calculations?
            return await interaction.followup.send(f"{emotes.Deny} There are no earlier departures on this day.", ephemeral=True)
        if self.viewer.index_offset - self.viewer.departures < self.min_offset:
            self.viewer.index_offset = self.min_offset
        else:
            self.viewer.index_offset -= self.viewer.departures
        self.viewer.update_output()
        return await self.update_message()

    @discord.ui.button(label="1", style=discord.ButtonStyle.primary, row=1)  # Blue, second row
    async def curr_departures(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Indicates the current page number (in terms of departures), does nothing """
        await interaction.response.defer()  # type: ignore
        return await self.update_message()

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.primary, row=1)  # Blue, second row
    async def next_departures(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Show the next departures """
        await interaction.response.defer()  # type: ignore
        if self.viewer.end_idx >= len(self.viewer.relevant_trips):  # Maybe replace with index calculations?
            return await interaction.followup.send(f"{emotes.Deny} There are no later departures on this day.", ephemeral=True)
        if self.viewer.index_offset + self.viewer.departures > self.max_offset:
            self.viewer.index_offset = self.max_offset
        else:
            self.viewer.index_offset += self.viewer.departures
        self.viewer.update_output()
        return await self.update_message()

    @discord.ui.button(emoji="⏭️", label="1", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def last_departure(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Go to the last departure for today """
        await interaction.response.defer()  # type: ignore
        self.viewer.index_offset = self.max_offset
        self.viewer.update_output()
        return await self.update_message()

    @discord.ui.button(label="Go to page", emoji="➡️", style=discord.ButtonStyle.primary, row=2)  # Blue, third row
    async def go_to_page(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Go to a user-specified page """
        return await interaction.response.send_modal(GoToPageModal(self))  # type: ignore

    @discord.ui.button(label="Jump to time", emoji="🕒", style=discord.ButtonStyle.primary, row=2)  # Blue, third row
    async def jump_to_time(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Jump to a given time """
        return await interaction.response.send_modal(JumpToTimeModal(self))  # type: ignore

    async def jump_to_time_response(self, interaction: discord.Interaction, delta: time.timedelta):
        await interaction.response.defer()  # type: ignore
        self.viewer.now = time.datetime.combine(self.viewer.today, time.time(), tz=TIMEZONE) + delta
        self.viewer.index_offset = 0
        self.viewer.update_output()
        await self.update_message()
        new_time = delta.format("%H:%M:%S")
        if delta.days:
            h = int(delta.total_seconds()) // 3600
            ms = delta.format("%M:%S")
            new_time = f"{h}:{ms}"
        return await interaction.followup.send(f"Now showing departures after {new_time}.", ephemeral=True)

    def update_compact_mode_button(self):
        labels = {  # Current state number -> next state
            0: "Shorten stop names",
            1: "Compact mode",
            2: "Show full names"
        }
        self.shorten_stop_names.label = labels[self.viewer.compact_mode]

    @discord.ui.button(label="Shorten stop names", style=discord.ButtonStyle.secondary, row=2)  # Grey, third row
    async def shorten_stop_names(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Toggle showing shorter or full stop names """
        await interaction.response.defer()  # type: ignore
        self.viewer.compact_mode = (self.viewer.compact_mode + 1) % 3  # rotate between 0, 1, 2
        self.viewer.update_output()
        self.update_compact_mode_button()
        return await self.update_message()

    @discord.ui.button(label="Hide view", emoji="⏸️", style=discord.ButtonStyle.secondary, row=2)  # Grey, third row
    async def hide_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Hide the view, instead of closing it altogether """
        await interaction.response.defer()  # type: ignore
        await self.message.edit(view=views.HiddenView(self))

    @discord.ui.button(label="Close view", emoji="⏹️", style=discord.ButtonStyle.danger, row=2)  # Red, third row
    async def close_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Close the view """
        await interaction.response.defer()  # type: ignore
        await self.message.edit(view=None)

    def update_direction_button(self):
        if self.viewer.direction == INBOUND_DIRECTION_ID:
            self.flip_direction.label = "Show outbound trips"
        else:
            self.flip_direction.label = "Show inbound trips"

    @discord.ui.button(label="Flip direction", emoji="🔀", style=discord.ButtonStyle.secondary, row=3)  # Grey, fourth row
    async def flip_direction(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Flip the direction of trips being shown """
        await interaction.response.defer()  # type: ignore
        self.viewer.direction ^= 1
        self.viewer.update_relevant_trips()
        self.viewer.update_output()
        self.update_direction_button()
        await self.update_message()


class TimeModal(views.Modal):
    text_input: discord.ui.TextInput

    @override
    def _interaction_description(self) -> str:
        return self.text_input.value

    @staticmethod
    async def parse_time(interaction: discord.Interaction, time_str: str, return_time: bool, max_h: int = 23) -> time.timedelta | time.time | discord.InteractionMessage:
        """ Parse the given timestamp """
        count = time_str.count(":")
        if count == 1:  # 1 colon = 2 parts
            h, m = time_str.split(":")
            s = "0"
        elif count == 2:
            h, m, s = time_str.split(":")
        else:
            return await interaction.response.send_message("Value must be of format `HH:MM` or `HH:MM:SS`.", ephemeral=True)  # type: ignore
        if not all((h.isdigit(), m.isdigit(), s.isdigit())):
            return await interaction.response.send_message("Value must be of format `HH:MM` or `HH:MM:SS`.", ephemeral=True)  # type: ignore
        h, m, s = int(h), int(m), int(s)
        if h < 0 or h > max_h:  # For whatever reason, departures from the first stop can go up to 31:20:00
            return await interaction.response.send_message(f"Hour must be between 0 and {max_h}.", ephemeral=True)  # type: ignore
        if m < 0 or m > 59:
            return await interaction.response.send_message("Minute must be between 0 and 59.", ephemeral=True),  # type: ignore
        if s < 0 or s > 59:
            return await interaction.response.send_message(f"Second must be between 0 and 59.", ephemeral=True),  # type: ignore
        if return_time:
            return time.time(h, m, s, tz=TIMEZONE)
        return time.timedelta(hours=h, minutes=m, seconds=s)


class SetTimeOffsetModal(TimeModal):
    interface: HubScheduleView
    # TODO: Allow entering a timedelta with text ("2h15m" or "2:15:00")
    text_input: discord.ui.TextInput[SetTimeOffsetModal] = discord.ui.TextInput(label="New offset", placeholder="E.g. \"2h45m\" or \"2:45:00\" or \"45:00\"", style=discord.TextStyle.short)

    def __init__(self, interface: HubScheduleView):
        super().__init__(interface, "Set offset")

    @staticmethod
    async def parse_delta(interaction: discord.Interaction, delta_str: str) -> time.timedelta | discord.InteractionMessage:
        """ Parse the given timedelta """
        if delta_str.startswith("-"):
            delta_str = delta_str[1:]
            mult = -1
        else:
            mult = 1
        count = delta_str.count(":")
        if count == 1:
            m, s = delta_str.split(":")
            h = "0"
        elif count == 2:
            h, m, s = delta_str.split(":")
        else:
            return await interaction.response.send_message("Value must be of format `MM:SS` or `HH:MM:SS`.", ephemeral=True)  # type: ignore
        if not all((h.isdigit(), m.isdigit(), s.isdigit())):
            return await interaction.response.send_message("Value must be of format `MM:SS` or `HH:MM:SS`.", ephemeral=True)  # type: ignore
        h, m, s = int(h), int(m), int(s)
        # Skip validation checks here, the timedelta will normalise the value
        return time.timedelta(hours=h, minutes=m, seconds=s) * mult

    async def on_submit(self, interaction: discord.Interaction):
        try:
            if not self.text_input.value:
                raise ValueError("Value was not filled")
            value = self.text_input.value
            offset = await self.parse_delta(interaction, value)
            if isinstance(offset, time.timedelta):
                if offset.total_seconds() > 86400:
                    return await interaction.response.send_message("Offset cannot be more than 24 hours.", ephemeral=True)  # type: ignore
                self._log_interaction(interaction)
                return await self.interface.set_time_offset(interaction, offset)
        except ValueError:
            if self.text_input.value:
                content = f"`{self.text_input.value}` could not be converted to a valid time."
            else:
                content = f"You need to enter a value."
            return await interaction.response.send_message(content=content, ephemeral=True)  # type: ignore


class JumpToTimeModal(TimeModal):
    interface: RouteScheduleView | HubScheduleView
    text_input: discord.ui.TextInput[JumpToTimeModal] = discord.ui.TextInput(label="Time to jump to", placeholder="HH:MM or HH:MM:SS", style=discord.TextStyle.short)

    def __init__(self, interface: RouteScheduleView | HubScheduleView):
        super().__init__(interface, "Jump to Time")

    @staticmethod
    async def parse_date(interaction: discord.Interaction, date_str: str) -> time.date | discord.InteractionMessage:
        """ Parse the given date """
        try:
            y, m, d = date_str.split("-")
        except ValueError:
            return await interaction.response.send_message("Date must be of format `YYYY-MM-DD`.", ephemeral=True)  # type: ignore
        if not all((y.isdigit(), m.isdigit(), d.isdigit())):
            return await interaction.response.send_message("Date must be of format `YYYY-MM-DD`.", ephemeral=True)  # type: ignore
        y, m, d = int(y), int(m), int(d)
        if y < 2020 or y > 2100:
            return await interaction.response.send_message("Invalid year specified.", ephemeral=True)  # type: ignore
        if m < 1 or m > 12:
            return await interaction.response.send_message("Month must be between 1 and 12.", ephemeral=True)  # type: ignore
        if d < 1 or d > 31:
            return await interaction.response.send_message("Day must be between 1 and 31.", ephemeral=True)  # type: ignore
        try:
            return time.date(y, m, d)
        except ValueError:
            return await interaction.response.send_message("Invalid date specified.", ephemeral=True)  # type: ignore

    async def on_submit(self, interaction: discord.Interaction):
        try:
            if not self.text_input.value:
                raise ValueError("Value was not filled")
            value = self.text_input.value
            is_hub = isinstance(self.interface, HubScheduleView)
            spaces = value.count(" ")
            if spaces == 1 and is_hub:
                _date, _time = value.split(" ")
                new_date = await self.parse_date(interaction, _date)
                if not isinstance(new_date, time.date):
                    return new_date
                new_time = await self.parse_time(interaction, _time, True, 23)
                if not isinstance(new_time, time.time):
                    return new_time
                new_datetime = time.datetime.combine(new_date, new_time)
                return await self.interface.jump_to_time_response(interaction, new_datetime)
            elif spaces == 0:
                max_h = 23 if is_hub else 31
                delta = await self.parse_time(interaction, value, is_hub, max_h)
                if isinstance(delta, (time.timedelta, time.time)):
                    self._log_interaction(interaction)  # Only log the interaction if it is valid
                    if is_hub:
                        new_time = time.datetime.combine(self.interface.viewer.today, delta)
                        return await self.interface.jump_to_time_response(interaction, new_time)
                    return await self.interface.jump_to_time_response(interaction, delta)
            else:
                if is_hub:
                    return await interaction.response.send_message(f"You must either specify a valid time or a date and time as `YYYY-MM-DD HH:MM:SS`.", ephemeral=True)  # type: ignore
                return await interaction.response.send_message(f"Value must be of format `HH:MM` or `HH:MM:SS`.", ephemeral=True)  # type: ignore
        except ValueError:
            if self.text_input.value:
                content = f"`{self.text_input.value}` could not be converted to a valid time."
            else:
                content = f"You need to enter a value."
            return await interaction.response.send_message(content=content, ephemeral=True)  # type: ignore
