import json
from typing import override

import discord

from utils import views, emotes, commands
from utils.general import alphanumeric_sort_string
from utils.timetables.shared import get_data_database, NUMBERS
from utils.timetables.viewers import StopScheduleViewer, TripDiagramViewer
from utils.views import NumericInputModal, SelectMenu

__all__ = ["StopScheduleView", "TripDiagramView"]


# noinspection PyUnresolvedReferences
class StopScheduleView(views.InteractiveView):
    """ A view for displaying stop schedules for a given stop """
    def __init__(self, sender: discord.Member, message: discord.Message, schedule: StopScheduleViewer, ctx: commands.Context | discord.Interaction = None):
        super().__init__(sender=sender, message=message, timeout=3600, ctx=ctx)
        self.schedule = schedule
        self.data_db = get_data_database()
        self.refreshing: bool = False

        self.update_freeze_button()

        if not self.schedule.real_time:
            self.remove_item(self.refresh_button)
            self.remove_item(self.freeze_unfreeze_schedule)

        self.route_filter_selector = RouteFilterSelector(self)
        self.add_item(self.route_filter_selector)
        self.route_line_selector = RouteLineSelector(self)
        self.add_item(self.route_line_selector)

        self.reset_route_filter.disabled = not self.schedule.base_schedule.route_filter_exists  # Filter enabled -> button enabled

    async def refresh(self):
        """ Refresh the real-time data """
        self.refreshing = True
        try:
            await self.schedule.refresh_real_schedule()
            self.schedule.update_output()
            self.route_line_selector.update_options()
            await self.message.edit(content=self.schedule.output, view=self)
        finally:
            self.refreshing = False

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.primary, row=0)  # Blue, first row
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Refresh the real-time data """
        await interaction.response.defer()
        if self.refreshing:
            return await interaction.followup.send("The data is already being refreshed, please wait.", ephemeral=True)
        await self.refresh()
        await self.disable_button(self.message, button, cooldown=30)

    def update_freeze_button(self):
        if self.schedule.fixed:
            self.freeze_unfreeze_schedule.label = "Unfreeze schedule"
            self.freeze_unfreeze_schedule.style = discord.ButtonStyle.primary
        else:
            self.freeze_unfreeze_schedule.label = "Freeze schedule"
            self.freeze_unfreeze_schedule.style = discord.ButtonStyle.danger

    @discord.ui.button(label="Freeze schedule", emoji="🕒", style=discord.ButtonStyle.danger, row=0)  # Red/Blue, first row
    async def freeze_unfreeze_schedule(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Freeze the schedule at the current time and index - or let it move again """
        await interaction.response.defer()
        self.schedule.fixed ^= True
        self.schedule.update_output()
        self.update_freeze_button()
        return await self.message.edit(content=self.schedule.output, view=self)

    @discord.ui.button(label="Shorten destinations", style=discord.ButtonStyle.secondary, row=0)  # Grey, first row
    async def mobile_desktop_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Toggle cutting off destination text to make sure that it fits on a mobile screen """
        await interaction.response.defer()
        self.schedule.truncate_destination ^= True
        self.schedule.update_output()
        if self.schedule.truncate_destination:
            button.label = "Show full destinations"
            # button.emoji = "➡️"  # If I ever decide to add an emoji to this button
        else:
            button.label = "Shorten destinations"
            # button.emoji = "⬅️"
        return await self.message.edit(content=self.schedule.output, view=self)

    @discord.ui.button(label="Hide view", emoji="⏸️", style=discord.ButtonStyle.secondary, row=0)  # Grey, first row
    async def hide_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Hide the view, instead of closing it altogether. """
        await interaction.response.defer()
        await self.message.edit(view=views.HiddenView(self))
        # return await interaction.followup.send("The view has been hidden. Use the Restore button to restore this view.", ephemeral=True)

    @discord.ui.button(label="Close view", emoji="⏹️", style=discord.ButtonStyle.danger, row=0)  # Red, first row
    async def close_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Close the view """
        await interaction.response.defer()
        await self.message.edit(view=None)
        # return await interaction.followup.send("The view has been closed. You may still see the schedule, unless you delete this message.", ephemeral=True)

    # async def disable_offset_buttons(self):
    #     """ Put all the buttons on cooldown at the same time """
    #     await self.disable_buttons_light(self.message, self.move_up_1, self.move_up_6, self.move_down_1, self.move_down_6, self.set_offset_button, self.move_offset, self.reset_offset, cooldown=3)

    async def move_indexes(self, interaction: discord.Interaction, indexes: int):
        """ Move the departures by the provided amount of indexes (Wrapper function) """
        await interaction.response.defer()
        limit_reached = False
        _minimum = -self.schedule.start_idx
        # When the start index moves into the future, the "maximum" value may become out of bounds... Is it worth investigating and fixing though?
        _maximum = len(self.schedule.iterable_stop_times) - self.schedule.start_idx - self.schedule.lines
        if _maximum < _minimum:
            _maximum = _minimum
        if indexes < _minimum:
            indexes = _minimum
            limit_reached = True
        elif indexes > _maximum:
            indexes = _maximum
            limit_reached = True
        self.schedule.index_offset += indexes
        self.schedule.update_output()
        self.route_line_selector.update_options()
        await self.message.edit(content=self.schedule.output, view=self)
        word = "down" if indexes > 0 else "up"
        offset = self.schedule.index_offset
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
        await interaction.response.defer()
        # The limit behaviour should not be implemented here - otherwise, the "Reset offset" will break for schedules that are too small (Example: stop 835000014)
        self.schedule.index_offset = offset
        self.schedule.update_output()
        self.route_line_selector.update_options()
        await self.message.edit(content=self.schedule.output, view=self)
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
        lines = self.schedule.lines - 1
        self.move_up_6.label = f"Move up {lines}"
        self.move_down_6.label = f"Move up {lines}"

    @discord.ui.button(label="Move up 1", emoji="🔼", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def move_up_1(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Show 1 departure above the current """
        return await self.move_indexes(interaction, -1)

    @discord.ui.button(label="Move up 6", emoji="⏫", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def move_up_6(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Show 1 departure above the current """
        return await self.move_indexes(interaction, -(self.schedule.lines - 1))

    @discord.ui.button(label="Show 4 departures", emoji="4️⃣", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def shrink_departures(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Show less departures.

         Behaviour depends on current state:
         4 departures -> Expand to 7
         7 departures -> Shrink to 4
         10 departures -> Shrink to 4 """
        await interaction.response.defer()
        if self.schedule.lines == 4:
            self.schedule.lines = 7
            self.change_departure_button_text(button, 4)
        else:
            self.schedule.lines = 4
            self.change_departure_button_text(button, 7)
        self.change_departure_button_text(self.expand_departures, 10)
        self.change_move_button_text()
        self.schedule.update_output()
        await self.message.edit(content=self.schedule.output, view=self)

    @discord.ui.button(label="Move offset", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def move_offset(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Move offset by a custom amount provided by the user """
        return await interaction.response.send_modal(MoveOffsetModal(self))

    @discord.ui.button(label="Reset route filter", style=discord.ButtonStyle.primary, row=1)  # Blue, second row
    async def reset_route_filter(self, interaction: discord.Interaction, _: discord.Button):
        """ Reset the route filter - Show all departures regardless of route """
        if not self.schedule.base_schedule.route_filter_exists:
            return await interaction.response.send_message("There is already no route filter applied to this stop!", ephemeral=True)
        return await self.apply_route_filter(interaction, values=None)

    @discord.ui.button(label="Move down 1", emoji="🔽", style=discord.ButtonStyle.secondary, row=2)  # Grey, third row
    async def move_down_1(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Show 1 departure above the current """
        return await self.move_indexes(interaction, 1)

    @discord.ui.button(label="Move down 6", emoji="⏬", style=discord.ButtonStyle.secondary, row=2)  # Grey, third row
    async def move_down_6(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Show 1 departure above the current """
        return await self.move_indexes(interaction, self.schedule.lines - 1)

    @discord.ui.button(label="Show 10 departures", emoji="🔟", style=discord.ButtonStyle.secondary, row=2)  # Grey, third row
    async def expand_departures(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Show more departures.

         Behaviour depends on current state:
         4 departures -> Expand to 10
         7 departures -> Expand to 10
         10 departures -> Shrink to 7 """
        await interaction.response.defer()
        if self.schedule.lines == 10:
            self.schedule.lines = 7
            self.change_departure_button_text(button, 10)
        else:
            self.schedule.lines = 10
            self.change_departure_button_text(button, 7)
        self.change_departure_button_text(self.shrink_departures, 4)
        self.change_move_button_text()
        self.schedule.update_output()
        await self.message.edit(content=self.schedule.output, view=self)

    @discord.ui.button(label="Set offset", style=discord.ButtonStyle.secondary, row=2)  # Grey, third row
    async def set_offset_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Set offset to a custom amount provided by the user """
        return await interaction.response.send_modal(SetOffsetModal(self))

    @discord.ui.button(label="Reset offset", style=discord.ButtonStyle.primary, row=2)  # Blue, third row
    async def reset_offset(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Reset the offset to zero """
        return await self.set_offset(interaction, 0)

    async def apply_route_filter(self, interaction: discord.Interaction, values: list[str] | None):
        await interaction.response.defer()
        await self.message.edit(content=f"{emotes.Loading} Updating the route filter for this stop... This may take up to a minute.", view=None)
        user_id = self.sender.id
        stop_id = self.schedule.stop.id
        if values is not None:
            db_values = json.dumps(values)
            if self.schedule.base_schedule.route_filter_exists:
                self.data_db.execute("UPDATE route_filters SET routes=? WHERE user_id=? AND stop_id=?", (db_values, user_id, stop_id))
            else:
                self.data_db.execute("INSERT INTO route_filters(user_id, stop_id, routes) VALUES (?, ?, ?)", (user_id, stop_id, db_values))
            self.reset_route_filter.disabled = False
        else:
            self.data_db.execute("DELETE FROM route_filters WHERE user_id=? AND stop_id=?", (user_id, stop_id))
            self.reset_route_filter.disabled = True
        self.schedule = await self.schedule.reload()
        self.route_line_selector.schedule = self.schedule
        self.route_line_selector.update_options()
        await self.message.edit(content=self.schedule.output, view=self)
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
        self.schedule = self.interface.schedule
        self.minimum = -self.schedule.start_idx  # + self.schedule.index_offset
        self.maximum = len(self.schedule.iterable_stop_times) - self.schedule.start_idx - self.schedule.lines
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
        self.schedule = self.interface.schedule
        self.minimum = -self.schedule.start_idx + self.schedule.index_offset
        self.maximum = len(self.schedule.iterable_stop_times) - self.schedule.start_idx - self.schedule.lines + self.schedule.index_offset
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

    def __init__(self, interface: StopScheduleView):
        super().__init__(interface, placeholder="Filter Routes", min_values=1, max_values=25, options=[], row=3)

        for route in self.interface.schedule.base_schedule.all_routes:
            name = f"Route {route.short_name}"
            description = route.long_name
            if route.short_name == "rail":
                value = f"{route.short_name} {route.long_name}"
            else:
                value = route.short_name
            self.add_option(value=value, label=name, description=description)

        self.options.sort(key=lambda x: alphanumeric_sort_string(x.value))
        self.max_values = len(self.options)

    async def callback(self, interaction: discord.Interaction):
        return await self.interface.apply_route_filter(interaction, self.values)


class RouteLineSelector(SelectMenu):
    """ Select menu for a trip whose line diagram should be shown """
    interface: StopScheduleView

    def __init__(self, interface: StopScheduleView):
        super().__init__(interface, placeholder="See details about trip", min_values=1, max_values=1, options=[], row=4)

        self.schedule = self.interface.schedule
        self.data = self.schedule.data
        self.real_time = self.schedule.real_time
        self.set_options()

    def set_options(self):
        """ Set options to the currently shown trips """
        stop_times = self.schedule.iterable_stop_times[slice(*self.schedule.get_indexes(custom_lines=10))]
        for i, stop_time in enumerate(stop_times, start=1):
            destination = stop_time.actual_destination or stop_time.destination(self.data)
            name = f"{self.schedule.format_time(stop_time.available_departure_time)} to {destination}"
            if stop_time.is_added:
                value = f"|{stop_time.trip_id}"
            elif stop_time.real_time:
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
            self.add_option(value=value, label=name, description=route, emoji=NUMBERS[i])

    def update_options(self):
        """ Update the list of options """
        self.reset_options()
        self.set_options()

    async def callback(self, interaction: discord.Interaction):
        # noinspection PyUnresolvedReferences
        await interaction.response.defer()
        _message: discord.WebhookMessage = await interaction.followup.send(f"{emotes.Loading} Loading data about the trip...", wait=True)
        message = await _message.fetch()
        viewer = TripDiagramViewer(self.interface, self.values[0])
        view = TripDiagramView(interaction.user, message, viewer)
        return await view.update_message()


# noinspection PyUnresolvedReferences
class TripDiagramView(views.InteractiveView):
    """ A view for displaying the list of all stops in a trip """
    def __init__(self, sender: discord.Member, message: discord.Message, viewer: TripDiagramViewer):
        super().__init__(sender=sender, message=message, timeout=3600)
        self.viewer = viewer
        self.command = f"{self.__class__.__name__} {self.viewer.trip_identifier}"
        self._stop = self.viewer.stop
        self.display_page = self.viewer.current_stop_page
        self.update_page_labels()
        self.refreshing: bool = False

        # Set special names for logging purposes
        self.first_page.log_label = "First page"
        self.prev_page.log_label = "Previous page"
        self.curr_page.log_label = "Current page"
        self.next_page.log_label = "Next page"
        self.last_page.log_label = "Last page"

        if not self.viewer.is_real_time:
            self.remove_item(self.refresh_button)

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
        self.update_page_labels()
        self.message = await self.message.edit(content=self.content, view=self)
        return self.message

    def update_page_labels(self):
        """ Update the paginator-related button labels to be accurate """
        # self.first_page.label = "1 ⏮️"
        # self.prev_page.label = "◀️"
        self.curr_page.label = str(self.display_page + 1)
        # self.next_page.label = "▶️"
        # self.last_page.label = f"⏭️ {self.page_count}"
        self.last_page.label = str(self.page_count)

    @discord.ui.button(emoji="⏮️", label="1", style=discord.ButtonStyle.secondary, row=0)  # Grey, first row
    async def first_page(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Go to the first page """
        await interaction.response.defer()
        self.display_page = 0
        return await self.update_message()

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.primary, row=0)  # Blue, first row
    async def prev_page(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Go to the previous page """
        await interaction.response.defer()
        if self.display_page <= 0:
            return await interaction.followup.send(f"{emotes.Deny} You are already on the first page.", ephemeral=True)
        self.display_page -= 1
        return await self.update_message()

    @discord.ui.button(label="1", style=discord.ButtonStyle.primary, row=0)  # Blue, first row
    async def curr_page(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Indicates the current page number, does nothing """
        await interaction.response.defer()
        return await self.update_message()

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.primary, row=0)  # Blue, first row
    async def next_page(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Go to the next page """
        await interaction.response.defer()
        if self.display_page >= self.page_count - 1:
            return await interaction.followup.send(f"{emotes.Deny} You are already on the last page.", ephemeral=True)
        self.display_page += 1
        return await self.update_message()

    @discord.ui.button(emoji="⏭️", label="1", style=discord.ButtonStyle.secondary, row=0)  # Grey, first row
    async def last_page(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Go to the last page """
        await interaction.response.defer()
        self.display_page = self.page_count - 1
        return await self.update_message()

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.primary, row=1)  # Blue, second row
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Refresh the real-time data """
        await interaction.response.defer()
        if self.refreshing:
            return await interaction.followup.send("The data is already being refreshed, please wait.", ephemeral=True)
        self.refreshing = True
        try:
            await self.viewer.refresh_real_time_data()
            self.viewer.update_output()
            await self.update_message()
            await self.disable_button(self.message, button, cooldown=30)
        finally:
            self.refreshing = False

    @discord.ui.button(label="Go to page", emoji="➡️", style=discord.ButtonStyle.primary, row=1)  # Blue, second row
    async def go_to_page(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Go to a user-specified page """
        return await interaction.response.send_modal(GoToPageModal(self))

    @discord.ui.button(label="Hide view", emoji="⏸️", style=discord.ButtonStyle.secondary, row=1)  # Grey, second row
    async def hide_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Hide the view, instead of closing it altogether """
        await interaction.response.defer()
        await self.message.edit(view=views.HiddenView(self))

    @discord.ui.button(label="Close view", emoji="⏹️", style=discord.ButtonStyle.danger, row=1)  # Red, second row
    async def close_view(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ Close the view """
        await interaction.response.defer()
        await self.message.edit(view=None)


class GoToPageModal(NumericInputModal):
    """ Modal for setting the offset to a certain number """
    interface: TripDiagramView

    def __init__(self, interface: TripDiagramView):
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
        # noinspection PyUnresolvedReferences
        await interaction.response.defer()
        self.interface.display_page = value - 1
        return await self.interface.update_message()
