# Changelog for Timetables Bot

## v0.0.1 - 20 November 2022
- Initial setup for the bot to get it to load
- Loads the data from the API and stores it in a file, so I don't have to constantly request data from the API while I create the bot

## v0.0.2 - 21 November 2022
- It is now possible to load the real-time data provided by the API into dataclasses

## v0.0.3 - 10 October 2023
- Made it possible to read the available GTFS data and load it into dataclasses

## v0.0.4 - 10 October 2023
- The static GTFS data is now stored in one big dataclass that contains all the other data
- The static GTFS data can now be pickled and then loaded from that instead of wasting processing power every time

## v0.0.4.1 - 10 October 2023
- Fixed the bot to be able to read GTFS-R v2 data instead of v1

## v0.0.5 - 10 October 2023
- Fixed the calendar not loading whether a service runs on the given weekday correctly
- Made it possible to look up the schedule for yesterday, today, and tomorrow for a certain stop

## v0.0.6 - 11 October 2023
- The bot will now only initialise the GTFS data when a command using the data is run, instead of doing it on startup
- Added a method to download the lastest GTFS data archive and update the stored static data

## v0.0.6.1 - 11 October 2023
- Merged the Linenvürteat bot to the main branch
- Added reprs to the dataclasses for static GTFS

## v0.0.7 - 11 October 2023
- The static GTFS data will now expire after two weeks
- If the GTFS data can't be loaded or has expired, the bot will download the new data and try to load it again
- Added a method for loading the GTFS data if the bot is not yet initialised and tell the user to wait
- The method will crash the current command if an error occurs while loading the data (this is intended behaviour)

## v0.1.0 - 20 October 2023
- Added a command to search stops and routes

## v0.1.1 - 22 October 2023
- Made it possible to forcibly redownload the realtime and static data

## v0.2.0 - 23 October 2023
- Added a command to view the next 6 departures at a given stop
- Added classes and functions to use real-time trip information to view a stop's departures

## v0.2.1 - 23 October 2023
- The time now shows "--:--" instead of "Unknown" if the data is unavailable
- Disabled Debug Mode

## v0.2.2 - 6 December 2023
- Changed internal name from "Linenvürteat" to "Timetables"

## v0.2.3 - 6 December 2023
- Added statuses to the bot, instead of just defaulting to the statuses from Suager

## v0.2.3.1 - 6 December 2023
- Fixed glitchy custom statuses

## v0.2.4 - 7 December 2023
- Improved the code for choosing a status
- Turned version and countdown statuses into custom status
- Added some new statuses

## v0.2.5 - 8 January 2024
- Added `i.dcu` and `i.luas` into the Timetables cog from Suager and CobbleBot respectively

## v0.3.0a1 - 13-15 January 2024
- The location of GTFS data is now stored in a database and only loaded into memory on demand
- GTFS dataclasses now don't reference each other, instead only providing the ID and a method to load the actual instance if needed
- Fixed real-time GTFS data crashing when the hour is 24 or higher
- Fixed ADDED trips crashing the feed if they have an arrival time but no departure time
- Fixed various other issues, although most of them were caused by this rewrite to begin with

## v0.3.0a2 - 21 January 2024
- Changed agencies, calendars, and calendar exceptions to use string IDs for consistency (and to not have to cast ints to strs and vice versa)
- Stop times are now stored in the database individually
- Greatly optimised the loading of StopSchedule
- Stopped reloading of GTFS data from blocking the rest of the bots' activity by putting it in a separate thread

## v0.3.0a3 - 21 January 2024
- Improved the "placeholder" debug/control command 
- Made it possible to load data from the Vehicles API endpoint
- Made it possible to get the straight-line distance between a vehicle and the current stop (if available)
- Fixed the loader getting stuck in an infinite loop if the static GTFS data was not being reloaded

## v0.3.0a4 - 22-23 January 2024
- Static Trips can now be looked up by Route ID
- Fixed the code breaking when an ADDED trip has no trip information (how is this even possible?)
- Fixed the code crashing when the vehicles data is not available (due to an API ratelimit or otherwise)

## v0.3.0a5 - 24 January 2024
- Locked the `i.tfi` command to be owner-only until it is ready for production
- Added a command to toggle debug mode
- Fixed the code crashing when a trip is loaded into memory, but the specific StopTime for a stop is not available
- Fixed `i.tfi search stop` breaking if no stop was found for the query
- Added a hint that you can use both stop code and stop name together to search for a stop or route

## v0.3.0a6 - 28 January 2024
- All timetable-related functions now load the database themselves
- Removed Route ID from the "search key" for routes
- Made the process of loading the schedule asynchronous so the rest of the bots don't freeze

## v0.3.0a7 - 28 January 2024
- Removed the `self` parameter from `timetables.read_and_store_gtfs_data()`, as you can just use `await` instead
- Optimised `self.download_new_static_data()` to simply call `self.reload_static_gtfs()` instead of repeating the code
- Fixed `luas.api` failing to load because a dependency could not be loaded

## v0.3.0a8 - 28 January 2024
- Made it possible to toggle "write mode" for real-time data
- Added a command to toggle write mode
- Added a command to refresh the real-time data and removed that functionality from the base `i.placeholder` command

## v0.3.0a9 - 30 January 2024
- The stop schedule now shows when a stop is drop-off only or pick-up only

## v0.3.0 - 30 January 2024
- Separated the real-time, static, and schedule code into separate files for better readability and navigability of code

## v0.4.0a1 - 3 February 2024
- Changed the skipped lines on the stop schedule loader to be a list rather than a set
- Moved the real-time stop schedule code into a View, so that I can later add buttons to it

## v0.4.0a2 - 3 February 2024
- Made a better way to load the real-time schedule

## v0.4.0a3 - 5 February 2024
- Added a command to sync slash commands (`i.sync`)
- Made command completion and command error handlers deal with the existence of slash commands
  - Note: Timetables Bot currently has no slash commands
- Fixed the header of the changelog file to say "Timetables Bot" instead of the old "Linenvürteat"
- Changed the access requirements for the DCU command: only accessible in Regaus'tar Koankadu, or by Regaus anywhere

## v0.4.0a4 - 6 February 2024
- Made it possible to specify a timestamp for `i.tfi schedule stop` (shows departures at that time, instead of now)

## v0.4.0a5 - 6 February 2024
- Made it possible to refresh the bus stop departures

## v0.4.0a6 - 11 February 2024
- Made it possible to show when a bus terminates early
- Made it possible to shorten the destinations (so it fits in one line on my phone)
- Made it possible to stop the view from updating the index and time when refreshed

## v0.4.0a7 - 12 February 2024
- Made the default button be "unfreeze schedule" when a specific time is specified (i.e. the view is already frozen at the start)

## v0.4.0a8 - 12 February 2024
- Changed the "button on cooldown" prompt to be grey instead of red
- Added a way to put a button on cooldown without changing its name
- Heavily improved the amount of time it takes to load stop information by optimising the schedule load function
- Changed the stop schedule view to timeout after 1 hour (instead of 15 minutes)
- Changed the refresh button cooldown to 30 seconds (instead of 60 seconds)
- Added buttons to move up and down the schedule

## v0.4.0a9 - 12 February 2024
- The schedule now shows when a trip is supposed to happen on a different date (e.g. before/after midnight)
- Changed the distance to round to the nearest 10m instead of 100m
- Fixed internal code saying there are 6 departure lines when there was actually 7
- Changed the cooldown of the `i.tfi` command to 4 seconds (instead of 5)

## v0.4.0a10 - 13 February 2024
- Added buttons to move the offset by a custom amount or set the offset to a custom number

## v0.4.0a11 - 14 February 2024
- Made `Language.get()` be able to deal with slash commands and interactions
- Made buttons on interactive views automatically detect whether the person is allowed to use that button
- Added error handling to buttons, which should hopefully reduce the amount of silent errors during debugging

## v0.5.0a1 - 8-9 Jan 2024, 23 May 2024
- Rewrote the code to store static GTFS data in an SQL database, instead of only storing the locations in the file on disk
- Made errors upon loading the schedule no longer fail silently
- Made there be a soft limit and a hard limit to the expiry of GTFS data (although the soft limit is currently not indicated to the end user)
- Made the traceback maker function able to include further context even when code block mode is disabled

## v0.5.0a2 - 24 May 2024
- Cleaned some of the old commented-out code to make the modern code more readable
- Made the functions that load supplementary information (such as the `Trip` associated with a `StopTime`) use the `load_value()` function instead of directly calling `cls.from_sql()`

## v0.5.0a3 - 24 May 2024
- Fixed the `load_value()` function breaking when `data` is None but the value is successfully retrieved from the database
- Changed the ratelimit for requesting data from the live API to 60 seconds
- (Hopefully) Fixed the real-time schedule sometimes incorrectly showing the last stop served by the bus

## v0.5.0a4 - 24 May 2024
- Changed the error re-raising statements to not modify error context when they don't need to

## v0.5.0a5 - 24 May 2024
- Fixed direct calls to `self.get_real_time_data()` not checking for the ratelimit
- Put the warning about a bus terminating early on a separate line
- Added a warning about a bus departing from a later stop than scheduled
- When the destination is truncated, an ellipsis is now added at the end to show that
  - The warnings for buses not going the whole way are similarly truncated
- Fixed the current time showing up in UTC after refreshing the view

## v0.5.0a6 - 25 May 2024
- Added a warning for when the GTFS data has reached its soft expiry limit (shown only once per bot restart)
- Changed the schedules command to simply forward any errors in the loading of the schedule to the `on_command_error()` event listener, instead of handling them separately

## v0.5.0a7 - 26 May 2024
- The CPU burner module will be disabled while the GTFS data is being loaded, and will now only active 15 minutes after the last command usage

## v0.5.0 - 26 May 2024
- The `__repr__()` for StopTime will now show the stop ID

## v0.5.1 - 29 May 2024
- Hid the "real-time" and "distance" columns for non-real-time schedules
- Hid "Refresh" and "Unfreeze schedule" buttons from non-real-time schedules
- Fixed inability to change the offset for fixed schedules
- Changed the "Button on Cooldown" text to be "Cooldown" followed by the length of the cooldown

## v0.5.2 - 29 May 2024
- Added a "hide view" button that replaces the view with a "restore" button (alternative to closing the view entirely)
- The "close view" button no longer produces any output

## v0.5.3 - 29 May 2024
- Added buttons to shrink/expand the view to show 4, 7, or 10 departures at a time (By default, 7 departures are shown)

## v0.5.3.1 - 29 May 2024
- Fixed the issue where anyone could restore a hidden view (instead of only the original sender)

## v0.5.3.2 - 29 May 2024
- Prevented the start and end indexes on the departures list from going out of bounds
  - Sometimes the offset may still shoot out of bounds, however there still would be the same amount of departures shown
- Fixed added trips breaking the schedule because they didn't have the "actual_destination" and "actual_start" attributes

## v0.5.4 - 30 May 2024
- Fixed issue where the maximum offset value was smaller than the minimum offset
- Made the "Move up/down 6" buttons respond to the current amount of departures shown
  - 4 departures shown -> move up/down by 3
  - 7 departures shown -> move up/down by 6
  - 10 departures shown -> move up/down by 9

## v0.5.5 - 3 June 2024
- Added "Close view" button to HiddenView
- Turned "swapping" buttons (such as freeze/unfreeze schedule) into one button whose behaviour depends on the current state
- Moved the desktop/mobile view button on the first row

## v0.6.0a1 - 3 June 2024
- Added paginators to `i.tfi search` commands
  - This means they can no longer go over the message length limit
  - The output is now an embed
  - There is now an intuitive message when no stop/route is found for the query

## v0.6.0 - 4 June 2024
- Turned `i.tfi` into a hybrid command
- The `i.tfi` command is no longer owner-only
- Added autocomplete to the schedule command
- Made the `i.sync` command more intuitive

## v0.6.1 - 5 June 2024
- InteractiveView now forces loading the full message when the view is created from a slash command interaction
  - The way this is implemented may allegedly have side effects, but we'll see if this breaks anything

## v0.7.0a1 - 7 June 2024
- Trips now store the number of stops associated with it

## v0.7.0a2 - 10 June 2024
- Errors when loading static GTFS data are now more likely to be shown and be handled properly
  - Errors when downloading data (ClientError or BadZipFile) will now be reported to the error logs channel, despite being non-critical (instead of being silently ignored)
  - `self.loader_error` should always be raised if it is there and not handled yet (it should be reset to None the next time data is loaded when things are handled properly)
- `i.placeholder reset` now resets the values of `self.initialised` and `self.updating` as well as setting the `self.loader_error` to None
- Added `i.placeholder check` that sends the current state of the initialised and updating flags, and whether there is an error state stored

## v0.7.0 - 11 June 2024
- Made it possible to hide arrivals that terminate at the current stop
- Fixed errors not being sent to the error logs channel when the traceback is very long
- Fixed the schedule viewer raising an error when loading non-real-time schedules

## v0.8.0 - 12 June 2024
- Added ability to filter the routes for which to show departures at a given stop

## v0.9.0a1 - 13 June 2024
- Rearranged the buttons in the schedule view to fit in just three rows (instead of four)

## v0.9.0a2 - 13 June 2024
- Improved the way the actual start/end of the trip is (for those that don't go the full way)
- Improved handling of calendar exceptions

## v0.9.0a3 - 14 June 2024
- Made the list of routes in the route filter select menu sorted in a more human-friendly way
- Separated the base class for the numeric input modal and select menu into the general views utility, so that they can be reused by other views if needed

## v0.9.0 - 14-15 June 2024
- Added ability to see all the stops for a given trip
- Slightly changed the way real-time data is stored to be more efficient
- Made the "shorten destinations" button work even when the name of the stop is extremely long

## v0.9.1 - 16 June 2024
- The TripDiagramViewer now stores the trip identifier string so that it can be identified in the future
- The lines on the TripDiagramViewer are now stripped to remove extra spaces on the right side
- Made the TripDiagramViewer more reliably find new real-time information about the trip
- Removed the cooldown on offset-related buttons in the StopScheduleView

## v0.9.2 - 16 June 2024
- The RouteLineSelector will now include the route as the description
- Fixed the RouteLineSelector options not updating when refreshing the view

## v0.9.3 - 16 June 2024
- Changed the TripDiagramView paginator buttons to use the emoji fields
- Added a "log_label" attribute to buttons whose labels are not identifiable (for interaction/error logs)

## v0.9.4 - 17 June 2024
- Improved the times shown in the TripDiagramViewer: if the bus arrives to the next stop earlier than the previous one, then the previous stop is marked as already departed from
- Made it possible to track which command spawned a view
- Made it possible to log buttons and other interactions on views
- The refresh buttons on StopScheduleView and TripDiagramView now tell the user to be patient if the view is already being refreshed
- The TripDiagramViewer now updates the time to current time upon loading, unless the original view was fixed
  - The viewer also handles the changes in the current date (e.g. when the time rolls over midnight)

## v0.9.5 - 19 June 2024
- Data about non-real-time trips can no longer be refreshed
- The TripDiagramViewer now properly reflects changes if there is real-time information about a trip that was not available before
- The `i.placeholder check` command now also shows the values of the debug and write flags

## v0.9.6 - 19 June 2024
- Replaced the Status field in the TripDiagramViewer with emojis to represent the stop where the vehicle currently is, skipped stops, and cancelled trips
- Added an indicator to the currently selected stop

## v0.9.7 - 20-22 June 2024
- Added more compact view options for the TripDiagramViewer
- Better handling of skipped stops and cancelled trips on the StopScheduleViewer
- Added a compact view mode for the StopScheduleViewer

## v0.9.7.1 - 27 June 2024
- Fixed the TripDiagramViewer breaking for added trips
- Fixed the TripDiagramViewer and StopScheduleViewer incorrectly showing the times when departure delay is provided but arrival delay is not

## v0.10.0 - 25 July 2024
- Added a way to see my DCU timetable that combines a course and extra modules
- Made the DCU timetable commands be able to adjust the dates in August and early September to the start of the next academic year (dates are currently known for 2023-2026)
- Made `i.dcu` no longer accessible on Suager
- Made `i.luas` no longer accessible on CobbleBot
- Made `i.dcu`, `i.luas`, and `i.tfi` global slash commands

## v0.10.1 - 30 July 2024
- Made `i.dcu`, `i.luas`, and `i.tfi` user-installable, usable in all contexts
- Made InteractiveViews be able to handle cases when the original message cannot be fetched (the timeout is set to 15 minutes and the view closes upon receiving an "invalid webhook token" error)
- Changed the date limits for `i.dcu timetable regaus`: the specified/current time is assumed to belong to the 2024/25 academic year if it's between 2024-08-01 and 2025-08-01 (exclusive)
- Fixed `Language.get()` to load the user from an interaction for personal responses
- Made Views not raise errors if it fails to edit the message when disabling the view

## v0.11.0 - 3 August 2024
- Added ability to see buses currently near a bus stop on a map image
- Made static GTFS dataclasses raise a KeyError instead of a TypeError when the value passed is invalid or None

## v0.11.1 - 3 August 2024
- Improved the algorithm for getting the arrival and departure delays for the TripDiagramViewer, the results should now be more accurate

## v0.11.2 - 3 August 2024
- The map can now estimate the direction in which the bus is moving
- The database now stores Shapes (sets of lat/long coordinates for displaying the route of the bus on a map)

## v0.11.3 - 3 August 2024
- Created a Viewer and View for the map command
- Added ability to zoom out to level 16 (and back in to level 17) on the map view
- Added ability to refresh the map view
- Changed the cog's debug and write values to be public, and made the real-time data refreshing commands use those values

## v0.11.3.1 - 4 August 2024
- Changed the real-time GTFS data header's timestamp to show up in Irish time rather than UTC

## v0.11.3.2 - 4 August 2024
- Made the notes on the StopScheduleViewer and TripDiagramViewer to show up in small text (`-#`)

## v0.11.3.3 - 5 August 2024
- Refactored the timetables maps submodule to have more consistent variable names and make it easier to customise the map generation afterwards
- Changed the `__all__` declarations to use tuples instead of lists

## v0.12.0 - 5 August 2024
- Made it possible to look up a diagram of a trip on the map
- Added a failsafe to prevent the map command from loading if the vehicle data is unavailable
- Changed the font on the maps to Univers

## v0.12.0.1 - 5 August 2024
- Added a real-time data timestamp for StopScheduleViewer and TripDiagramViewer

## v0.12.0.2 - 6 August 2024
- Changed the "find fitting coordinates and zoom" algorithm to be more likely to produce a map where all the points fit

## v0.12.1 - 6 August 2024
- Changed the highest available zoom to be 18 (making the limit 16-18 rather than 16-17)

## v0.12.2 - 6 August 2024
- Fixed the TripDiagramView and TripMapView breaking after 15 minutes
- The TripMapViewer now gets its data from the TripDiagramViewer, including information about arrival and departure times
- The departure times for stops are now rendered on the TripDiagramViewer
- Made the TripMapViewer be able to handle added trips
- Fixed the TripMapViewer breaking if the trip had no vehicle tracked

## v0.12.3 - 6-7 August 2024
- The TripMapViewer map should no longer be able to go out of bounds
- The times shown on the TripMapViewer will now try to not overlap with each other (not perfect, but decent enough to leave for now)
- Stopped TripDiagramViewer from breaking if no stop time was ever loaded for the trip before
- Added a special debug command for testing the TripMapViewer
- Added special debug functions to generate fake real-time and added trips and create fake vehicles

## v0.12.3.1 - 8 August 2024
- Fixed the RouteFilterSelector crashing when two bus routes running through a bus stop happened to have the same number

## v0.12.4 - 8 August 2024
- The StopScheduleViewer now shows a more accurate distance between the bus and the stop using the map shape
- Stop times for added trips now hold their relevant trip update with them
- Disabled the debug command

## v0.12.4.1 - 8 August 2024
- GTFSRData and VehicleData classes now return an empty instance instead of None if the data is not available
- When first loading data, the bot will now check the timestamp of the data stored on disk, only loading from API if more than 75s passed since last update
  - This will prevent the vehicle API from complaining when I reload the bot a lot during debugging

## v0.12.4.2 - 8 August 2024
- Prevented from real-time data from being loaded twice at the same time, causing rate limit errors on the API
- Changed refresh button cooldowns to 60 seconds (the underlying code only calls the API once a minute anyways)

## v0.12.5 - 8 August 2024
- Removed the "Hide view" button from TripMapView and MapView, since they have few buttons to begin with
- Added a "Reset zoom" button to MapView, which resets the zoom level back to default

## v0.12.5.1 - 8 August 2024
- Skipped stops no longer set the arrival/departure delay to zero
- Skipped stops will no longer have their departure times rendered
- Skipped stops will always be rendered red, even if they are pickup-only or drop off-only
- Vehicles whose coordinates are 0, 0 will no longer show their distance

## v0.12.6 - 8 August 2024
- The TripMapViewer now supports zooming in (centres around the current stop)

## v0.12.6.1 - 8 August 2024
- Trips that terminate early no longer show the "Terminates at" part on the RouteLineSelector (only the destination)

## v0.12.6.2 - 8 August 2024
- Cancelled trips will now have all stops (except the current stop) rendered in red on the map, but still show the departure times

## v0.12.6.3 - 8 August 2024
- Improved the TripMapViewer coordinates algorithm to fit more stops when zooming in, instead of blindly centering at the current stop even if it's near the end of the route

## v0.12.6.4 - 8 August 2024
- Fixed StopScheduleView crashing when there's no departures available from a stop (because RouteLineSelector was empty)

## v0.12.6.5 - 21 August 2024
- Added quotes around the key and ID in the KeyError raised by `load_value()`
- Fixed `timetables.maps` throwing an error when a trip somehow doesn't have the shape data associated with a trip
- Fixed shapes breaking the uniqueness constraint (shape ID + sequence)
  - The shapes will now use zero-based indexes so that they can be converted to a list
- Changed shapes to use a list of shape points rather than a dictionary

## v0.12.6.6 - 25 August 2024
- Replaced the "unresolved references" noinspection comment with `type: ignore`

## v0.13.0 - 26 August 2024
- Added "stop hubs" (shows schedules for multiple stops nearby at the same time)
  - Currently only has stop hubs for locations around Dublin

## v0.13.1 - 26 August 2024
- The command will no longer crash if there are no trips passing by a stop after a route filter is applied
- The stop hub route filter view will now edit its own message instead of sending a new one once the filter is set
- The "reset route filter" button will now be disabled if there is no route filter currently active
- The "reset route filter" button presses will now print to stdout, while the HubStopSelector won't

## v0.13.2 - 28 August 2024
- Changed the DCU module to log to Timetables instead of Suager
- Tried to prevent errors caused by the API timing out
- Updated the bot to handle the new module codes

## v0.13.3 - 29 August 2024
- The bot now handles new course codes that contain the course name in them
- Added a command to delete existing cache and fetch new data from server (`i.dcu invalidatecache`)

## v0.13.4 - 31 August 2024
- Renamed TripDiagramMapViewer and TripDiagramMapView to TripMapViewer and TripMapView respectively
- StopScheduleViewer will now show data about the vehicle (if available)
- The code for generating departure data for StopScheduleViewer and HubScheduleViewer is now combined into a common function, since they mostly do the same thing
- Renamed the `schedule` attribute of StopScheduleView to `viewer` for consistency
- Data about vehicle distances is no longer shown if no such data is available for any shown trip

## v0.13.5 - 31 August 2024
- TripDiagramViewer and TripMapViewer can now show information about the bus serving the trip
  - It states the current nearest stop as well as the fleet number, reg plates, model, and any features of the bus

## v0.13.5.1 - 1 September 2024
- Turned the `is_empty` function into a property for GTFSRData and VehicleData
- Added an `.empty()` classmethod to the Header class

## v0.14.0a1 - 1 September 2024
- Added command to show data about specific buses
- Added ability to see timestamp for specific TripUpdates and Vehicles

## v0.14.0 - 1 September 2024
- Added ability to see the list of vehicles currently operating on a route
  - The view can also list the buses by model
- Fixed fleet vehicle autocomplete not working
  - Replaced the reg plates with the API vehicle ID
- Added `start_date` field to RealTimeTrips (so that you can tell if the trip belongs to a different day)
- When specifying a route, IDs now require a full match (but only a partial match for route number + destinations)

## v0.14.1 - 2 September 2024
- Added a command to hot-reload the timetables module and set the debug value without restarting the bot
- Changed the static data expiry to be 14 days for a soft warning and 45 days as hard limit
- The RouteVehiclesViewer can now show buses that are associated with the route even if it is outside the scheduled departure and arrival times

## v0.14.1.1 - 3 September 2024
- Fixed trips not showing up on the RouteVehiclesViewer where they are valid for yesterday but not today

## v1.0.0a1 - 3 September 2024
- Added a command to view the schedule of a route
  - Only uses static data

## v1.0.0 - 3 September 2024
- The RouteScheduleViewer no longer loads real-time data (since it is not used)
- Added buttons to show earlier and later departures
  - Also added a button to jump to a specific time
- Added buttons to flip the direction without having to call the command again
- Fixed the route schedule completely breaking on routes that do weird stuff

## v1.0.1 - 5 September 2024
- The RouteVehiclesViewer now shows cancelled trips

## v1.0.2 - 10 September 2024
- Added a new stop hub: "Regaus Northbound"
  - Includes the stops I usually transfer at when getting to university

## v1.0.3 - 10, 15 September 2024
- Added ability to move the HubScheduleView by 5 minutes or to jump to a given time

## v1.0.3.1 - 15 September 2024
- Added Drumcondra stop hub

## v1.0.3.2 - 15 September 2024
- Added "timetables" as an alias to `i.tfi schedule` command group

## v1.0.4 - 18 September 2024
- Added new stops for route N2 to the DCU stop hub
- The StopScheduleViewer and HubScheduleViewer now show an error message if there are no departures from the stop on a given day
- The RouteScheduleViewer now also shows a better output when the data is empty
- The HubScheduleViewer no longer shows the header for every stop (it is now only shown once)
  - As such, the view can now display 4 departures even for hubs with a lot of stops

## v1.0.5 - 21 September 2024
- Improved the table parsing to correctly get the "trivia" section of vehicle data
- FleetVehicles now store which operator they're associated with
- The colours of the bus on the map will be changed depending on the operator

## v1.0.6 - 27 September 2024
- The StopScheduleViewer and HubScheduleViewer can now guess the next departure time if it is not available from the API, based on the data for the previous trip
  - These times are shown with an asterisk, as they are guesses rather than actual real-time data
  - If the previous journey is expected to reach the terminus later than the current trip is scheduled to depart, that will be shown as the delay
  - The current implementation does not sort these guessed times together with the rest of the data, but realistically that shouldn't be a big problem
- Fixed the Bus Éireann stop at Drumcondra station no longer existing
- HubScheduleViewer: Changed "Lookup time" to "Showing departures after" in the output text

## v1.0.6.1 - 1 October 2024
- Added the eastbound N4 stop at Clontarf station to the stop hub
- Slightly reduced the line length limit for hubs with 9 stops, so that they wouldn't overflow over 2000 characters

## v1.0.6.2 - 8 October 2024
- Real-time commands should no longer crash when the real-time API is not accessible
- Scheduled trips that are on real-time but are not in the database (old static data) will no longer cause `i.tfi vehicles specific` to crash
- Added the N2 stop to the Heuston station hub
- Renamed the hub from "Heuston" to "Heuston Station"