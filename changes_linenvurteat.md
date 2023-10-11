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