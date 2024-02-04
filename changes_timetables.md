# Changelog for Linenvürteat

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