# Changelog for CobbleBot

## v0.1.0 - 6 December 2020
- Added Cobble XP and transferred Economy and SS23 from Suager

## v0.2.0 - 7 December 2020
- Achievements, currently only for Cobble XP and levels.

## v0.2.1 - 8 December 2020
- Achievements now show progress from last tier instead of from zero

## v0.3-pre1 - 12 December 2020
- Slightly updated language for levels and achievements
- Renamed SS23 to GA78
- Updated GA78 commands to mostly no longer being hidden (as most people can't access them anyways)
- RSL-1 documentation command
- Removed RSL numbers as separate command

## v0.3-pre2 - 13 December 2020
- Added ga78 command, added data for SS-23

## v0.3-pre3 - 13 December 2020
- SS-24 data

## v0.3-pre4 - 14 December 2020
- Added achievement for achieving tiers on others
- Owner-only command to see the achievement tier colours

## v1.0-pre1 - 16 December 2020
- Combined leveling and leaderboards with Suager
- Shared database

## v1.0-pre2 - 19 December 2020
- Updated RSL-1 locale

## v1.0-pre3 - 20 December 2020
- Removed shop and buy commands

## v1.0.0 - 20 December 2020
- Generate colour on the bot instead of using the AlexFlipnote API

## v1.0.1 - 23 December 2020
- Transparent background in achievements
- Updated XP achievements
- Renamed RSL-1_kg to RSL-1d

## v1.0.2 - 24 December 2020
- Added hot chocolate command

## v1.0.3 - 26 December 2020
- RSL-1 noun declensions

## v1.0.4 - 2 January 2021
- CobbleBot now uses separate leveling

## v1.0.4.1 - 4 January 2021
- Fixed data_io not updating config example anymore

## v1.0.5 - 7 January 2021
- timein and timeago
- Improved the way the bot handles the extra parameters I use

## v1.0.6 - 7 January 2021
- Removed Suager XP achievements

## v1.0.7 - 9 January 2021
- Removed tts command

## v1.0.8 - 9 January 2021
- Moved version to a separate file

## v1.0.9 - 13 January 2021
- Added Chuck and Potato to RSL-1 command
- Added RSL-1 warning
- Created declensions subcommand

## v1.0.10 - 13 January 2021
- Added dictionaries placeholders

## v1.0.11 - 14 January 2021
- Dictionary commands should now be functional
- A command that shows how RSL-1 was intended to be pronounced
- A command that explains RSL-1 grammar

## v1.0.12 - 15 January 2021
- More grammar

## v1.0.13 - 17 January 2021
- RSL-1 pronouns

## v1.0.14 - 18 January 2021
- added what and who to pronouns

## v1.1-pre1 - 19 January 2021
- Added RSL-1 declensions command

## v1.1-pre2 - 19 January 2021
- Adverbs and small are now in the dictionary
- Fixed the output for RSL-1 dictionary

## v1.1-pre3 - 20 January 2021
- Searchable RSL-1 phrases

## v1.1-pre4 - 24 January 2021
- Reduced available achievement tiers to 12 (from 15)

## v1.1-pre5 - 3 February 2021
- RSL-1g vocabulary

## v1.1-pre6 - 7 February 2021
- Slightly updated the grammar stuff

## v1.1-pre7 - 14 February 2021
- RSL-1e verbs
- Moved phrases into main dictionary

## v1.1 - 22 March 2021
- TBL
- TBL-related achievements
- Updated ss23 and ss24 times to be in 24:60:60 format
- Removed CobbleBot XP notice

## v1.1.1 - 22 March 2021
- Weather78, better weather data for GA78 locations
- Preparations to switch time78 algorithm

## v1.1.2 - 22 March 2021
- Time78 instead of time23 and time24
- Removed ss23 and ss24

## v1.1.2.1 - 24 March 2021
- Fixed weather78 offsets
- Fixed Kargadia and Qevenerus weekday outputs
- Updated tbl time output
- Added #secretive-commands-2 to also allow RSL-1 command

## v1.1.2.2 - 26 March 2021
- Fix TBL locations not updating their activity properly
- Improve time78

## v1.1.3 - 6 April 2021
- Ability to join, leave, delete, and transfer ownership of TBL clans
- Ability to donate player coins to Clans and Guilds
- Made TBL unable to function in DMs (as it crashes)

## v1.1.4 - 11 April 2021
- Buying and playing on Clan Locations

## v1.1.5 - 21 April 2021
- Ability to refund Clan Locations
- Removed economy

## v1.1.6 - 26 April 2021
- Made TBL activity hours more accurate (old way was 6 hours ahead of actual time)
- Made TBL store Shaman, Clan and Guild boosts as levels, and only calculate the actual boosts while loading
- Ability to convert Player Coins to Shaman Feathers
- Ability to use Shaman Feathers to upgrade your Shaman stats
- Made TBL player place at end of round more accurate
- Cancelled Challenge Renewal

## v1.1.7 - 1 May 2021
- TBL Clan upgrades
- TBL Guild upgrades

## v1.1.8 - 8-11 May 2021
- Removed TBL beginning
- Split Shaman skills into separate embed field for TBL stats
- Reduced the Clan and Guild reward boost limit, increased max energy regen speed boost
- You now get extra coins for XP after level 250
- Added more Leagues
- TBL now stores the highest amount of League Points you've ever had
- Improved TBL-related achievements to reflect the new changes
- Changed how energy is regenerated while playing
- Improved plurals for TBL
- Made CobbleBot show how long is left until his birthday and until my birthday
- Changed playing status update rate to 2 minutes 30 seconds

## v1.1.9 - 17 May 2021
- The Floating Islands are now unlocked at XP Level 1 (instead of 0)
- Improved achievements progress bar
- Finished Russian translation of TBL
- Improved TBL locales

## v1.1.10 - 20 May 2021
- Finished RSL-1e translation of TBL

## v1.1.11 - 21 May 2021
- Achievements now uses Suager XP values

## v1.1.12 - 22 May 2021
- Achievements can now be translated
- Achievements now only show TBL in RSL locales (and only while used with CobbleBot), instead of depending on TBL player data
- TBL Clan Energy Regen Boost changed to -0.7s/level, max -105s (Now only 150 levels)
- TBL per-round energy generation rate capped to 60s
- TBL Shaman energy boost per save maxed out at round cost - 2

## v1.1.13 - 27 May 2021
- Switched default locale of TBL to RSL-1i
- Made SS-23 days 2.7x shorter
- Added RSL-1k and RSL-1i Kargadia date format
- TBL now uses updated Kargadia date format

## v1.1.14 - 31 May 2021
- Better weather for SS-23
- Ability to see local time in a specific place in GA78
- Added Reggar to list of places
- Renamed GA78 to Conworlds

## v1.1.15 - 1 June 2021
- Fixed timezone scaling with weather78
- Updated weathers and places to new Kargadia
- Added command to see latitude and longitude location for places in Kargadia, also shows list of all places in Kargadia
- Added many new cities to Kargadia
- Temporarily removed the weather bit, will be added back soon with updated climates

## v1.1.16 - 4 June 2021
- Improved description of the locations command, added some more cities to Kargadia

## v1.1.16.1 - 4 June 2021
- Increased weather78 sun accuracy - Kargadian years start at the march equinox, not our new year

## v1.1.17 - 5 June 2021
- Updated TBL to follow the new -7:00 timezone of Sentatebaria
- Improved accuracy of Kargadian locations

## v1.1.18 - 7 June 2021
- Moved the centre of Kargadia to Sertangar
- Added TBL locations to the map of Kargadia and made its locations available

## v1.1.19 - 8 June 2021
- Updated RSL encode and decode commands

## v1.1.20 - 13 June 2021
- Updated Zeivela and Kargadia year lengths
- Improved the script for calculation of solar calendars for ga78

## v1.1.21 - 15 June 2021
- Made time78 place not found error more readable

## v1.1.22 - 15 June 2021
- Made weather78 represent cases when the sun doesn't rise or set at high latitudes

## v1.1.23 - 15 June 2021
- Separated data about Kargadian places from the conworlds time file
- Moved some Kargadian cities around and added new ones

## v1.1.24 - 17 June 2021
- Renamed conworlds util to times
- Removed RSL-1e locale
- Removed RSL-1e documentation command
- Removed TBL v1

## v1.1.25 - 21 June 2021
- Updated RSL-1 months

## v1.1.26 - 24 June 2021
- Data about dawn and dusk for Kargadia

## v1.1.27 - 25 June 2021
- More solar accuracy, hopefully

## v1.1.28 - 25 June 2021
- Converted Kargadian places to 3600x1800 map format
- Made latitude/longitude output more precise
- Removed "month of" parts from Zeivela and Qevenerus time generation

## v1.1.29 - 1 July 2021
- Added more data about the sun's location to weather78

## v1.1.30 - 3 July 2021
- Added data78 as alias to weather78

## v1.1.31 - 5 July 2021
- Improved accuracy of solar time
- Removed dawn and dusk values if they don't happen

## v1.2-pre1 - 5 July 2021
- Added weather patterns for Reggar
- Improved weather generation algorithms

## v1.2-pre2 - 7 July 2021
- Added more places to Kargadia
- Added humidity to weather78
- Made locations command split messages by 20 when there are too many of them

## v1.2-pre3 - 8 July 2021
- Added regions and local time to weather78

## v1.2-pre4 - 12 July 2021
- Squished all weather data into one field

## v1.2-pre5 - 18 July 2021
- Added command to see a specific location's time
- time78 now shows times based on planet
- Moved weathers to their own file

## v1.2.0 - 25 July 2021
- Added weathers to Pakigar, Shonangar, Orlagar and Leitagar

## v1.2.1 - 4 August 2021
- Added settings
- Added Suvagar to data78

## v1.2.2 - 7 August 2021
- weather78 now shows where the sun should be
- Changed Qevenerus eccentricity

## v1.2.3 - 9 August 2021
- Added Virkada

## v1.2.4 - 11 August 2021
- Updated RSL-1h month and weekday names

## v1.2.5 - 13 August 2021
- Added Usturian time
- Added support of dates outside of years 1-9999 for time generation (using numpy datetime64)
- Added support for Usturian place names on Qevenerus

## v1.2.6 - 18 August 2021
- Improved the data for cities of Virkada, Kargadia and Qevenerus

## v1.2.7 - 18 August 2021
- Made weather78 place names case-insensitive
- Added some more playing statuses

## v1.2.7.1 - 2 September 2021
- Made settings command not load irrelevant settings, and made the template only contain relevant settings

## v1.2.7.2 - 4 September 2021
- Fixed weather78 to actually show weather

## v1.2.8 - 8 September 2021
- Moved the location list to new "weather78 list" subcommand
- Location now only shows the location of a specific place

## v1.2.8.1 - 11 September 2021
- Fix Usturian calendar to actually align the dates properly
- Improved Kargadian weekday calculation

## v1.3.0-pre1 - 12 September 2021
- Improved language support to weather78
- Added support for other languages to weather78
- The "Real offset" is now shown as hh:mm rather than as a fraction of the hour
- Updated language strings for proper support of RSL-1 in the future

## v1.3.0-pre2 - 13 September 2021
- Fixed weather78 crashing if a city name has an apostrophe in it
- Fixed weather78 list command
- Made the playing status update speed 2 minutes rather than 2m30s
- Added a clock that shows current time and weather in Kargadian cities

## v1.3.0-pre2.1 - 13 September 2021
- Made the city data, city time, and playing updater scripts adjust themselves for lag caused

## v1.3.0-pre2.2 - 14 September 2021
- Added Lailagar

## v1.3.0-pre3 - 15 September 2021
- The playing status now shows Kargadian holidays and Kargadian time and weather
- Made types of status only show up at set probabilities

## v1.3.0-pre3.1 - 18 September 2021
- Funnier responses on polar days/nights in weather78
- Fixed bug that showed dawn and dusk even when not necessary

## v1.3.0 - 18 September 2021
- Improved the invite command

## v1.4.0a1 - 26 September 2021
- Created custom datetime system, to later improve the way time works in Kargadia

## v1.4.0a2 - 30 September 2021
- Improved the Regaus time system
- Started integrating Regaus time into the conworld systems
- Updated strings for playing statuses (types 1 and 4)

## v1.4.0a3 - 2 October 2021
- Improved the way local time is shown in weather78
- Translated time to Kaltarena Kargadian

## v1.4.0a4 - 3 October 2021
- Added ability to set cases for times, which will later be used to more accurately show times for both `datetime.datetime` and `regaus.time`

## v1.4.0a5 - 25 October 2021
- Converted `regaus` into its own module
- Made the sun heading values more accurate
- Now shows current version of Regaus.py in `..stats`

## v1.4.0 - 25 January 2022
- Implemented new places and times from Regaus.py v1.2
- Made the `..time78` use place names instead of indexes (you can also enter a planet name though)
- Removed `..tl` (replaced by new time78 behaviour)
- Added support for Levels of Detail for weather78
- ka-time now shows new places sorted by area/continent, and then by timezone
- The playing status stays as it used to be, simply updated to show the new places instead of old ones
- Removed references to old games until I actually make them again (if ever...)

## v1.4.1 - 25 January 2022
- Made languages use the Language class from Regaus.py

## v1.4.2 - 25 January 2022
- Language list now shows how much the language translation is complete

## v1.4.3 - 26 January 2022
- Added new cities to the ka-time list
- Made the messages split to avoid hitting the message length limit
- The ka-time now only updates every 5 minutes

## v1.4.4 - 29 January 2022
- You can now decline Kargadian nouns

## v1.4.4.1 - 30 January 2022
- Better case update handling

## v1.4.4.2 - 30 January 2022
- Fix alignment on mobile
- Add new people to system

## v1.4.5 - 31 January 2022
- Added weather icons for weather78

## v1.4.5.1 - 3 February 2022
- Fix time78 not using the given time

## v1.4.6 - 13 February 2022
- The location command can now show the place's location on the map

## v1.4.7 - 13 February 2022
- Moved time channel to the Kargadia server

## v1.4.7.1 - 13 February 2022
- Now Kargadian time is shown in both servers instead

## v1.4.8 - 17 February 2022
- Added support for Senko Lair holidays in CobbleBot's status
- The bot will now celebrate Kargadian and Senko Lair holidays
- Kargadian time data is now only updated when something involving Kargadia happens (checking for holidays, updating the time channels, Kargadian statuses)

## v1.4.8.1 - 18 February 2022
- Holidays are now logged as they occur

## v1.4.9 - 18 February 2022
- Added a command to calculate your current age on Kargadia

## v1.4.10 - 18 February 2022
- `..timesince` now uses proper `YYYY-MM-DD hh:mm:ss` format for specifying time
- `..timesince`, `..timeago` and `..timein` now support non-Earth time classes

## v1.4.11 - 21 February 2022
- Updated Kargadian cases
- Added Kargadian unit conversions for length, speed and temperature

## v1.4.12 - 22 February 2022
- Added command where CobbleBot briefly tells about himself in Tebarian

## v1.4.12.1 - 29 April 2022
- Added SR-14 and SR-15 to LOD 1 list

## v1.4.12.2 - 4 May 2022
- Added SR-16 to LOD 1 list

## v1.4.13 - 6 May 2022
- Added Kargadia db table (not yet used)
- Added new cities to Nittavia time display

## v1.5.0 - 7-8 May 2022
- Added a system of birthdays for Kargadia

## v1.5.0.1 - 9 May 2022
- Fixed the birthdays incorrectly switching themselves between UTC and their actual timezone
- Added SR-17 to LOD 1 list

## v1.5.1 - 9 May 2022
- Better relativedelta conversion for timein/timeago commands

## v1.5.2 - 9 May 2022
- Timezone support for input and output

## v1.5.2.1 - 9 May 2022
- Add a Citizen ID field to the Kargadia database table

## v1.5.3 - 9 May 2022
- Kargadia citizen profiles
- CobbleBot can now actually process people's birthdays

## v1.5.4 - 9 May 2022
- CobbleBot now shows Kargadian time on `..time`

## v1.5.4.1 - 9 May 2022
- Fixed Kargadian birthdays not saving "has_role" status

## v1.5.4.2 - 10 May 2022
- Fixed the bot crashing when no Kargadian location is set for birthday

## v1.5.5 - 10 May 2022
- You can now only access your own citizen ID, mine, and the bots'
- The User ID is no longer shown
- Better showing for null birthday or location

## v1.5.6 - 11 May 2022
- Made it possible to see a user's local time

## v1.5.7 - 11 May 2022
- Command to show someone's Kargadian birthday

## v1.5.7.1 - 11 May 2022
- Added a separate channel for holidays and birthdays on the Kargadia server

## v1.5.7.2 - 17 May 2022
- Made the city shown in the bot's playing statuses more random
- Better weights system for the Kargadian cities list

## v1.5.8 - 17 May 2022
- `..birthday` now shows how long is left until the user's next birthday

## v1.5.9 - 17 May 2022
- Made the relative time commands use Kargadia time by default
- The `..timesince` command will default to certain Kargadian dates if no date is specified
- Fixed `..timesince` ignoring the user's timezone in the default values

## v1.5.10 - 17 May 2022
- Arnattia time class now also uses the Kargadian citizen database for timezones (since it's the same calendar)
- Added a command to convert between different time classes

## v1.5.10.1 - 18 May 2022
- Added LOD 3 support (Regaus.py v1.2.19)

## v1.5.11 - 18 May 2022
- Hide P2 places from place list
- Added "place" as aliases to `..weather78`

## v1.5.12 - 23 May 2022
- Updated syntax for RSL-1 commands
- Updated the number translator to use up-to-date number systems
- Updated list of trusted people and channels for the RSL-1 command

## v1.5.12.1 - 24 May 2022
- Try to fix the holiday scripts showing negative days remaining after a holiday passes

## v1.5.13 - 4 June 2022
- Fixed timezone finder crashing when a user's Kargadian place is unavailable
- Changed the UTC field name in `..time` to Virsetgar
- The UTC timezone in Kargadia is now replaced with Virsetgar
- Fixed citizen profile crashing when the user has no profile

## v1.5.14 - 17 June 2022
- Improved how translation completion is counted (made all language names count as one large "string")
- West Kargadian translation for discord-related commands and various error messages

## v1.6.0 - 18 June - 13 August 2022
- West Kargadian translation for the rest of the commands
- Updated discord.py and other dependencies to the latest versions
- Kargadia citizen profile and Kargadian birthdays can now be accessed by citizen ID
- Fixed timezone misbehaviour for Kargadian birthdays
- Fixed Kargadian birthdays breaking when the user does not have a Kargadian citizen profile
- Updated status messages used while loading and just afterwards
- Command to see distance between two places on Kargadia and other planets
- Numbers should no longer show up as links on Android

## v1.6.0.1 - 21 August 2022
- Handle emotes kwarg no longer being added in Regaus.py v2.0
- Fix `..distance` not accepting longitude coordinates with 3 digits

## v1.6.0.2 - 3 September 2022
- The database builder now uses the actual type string instead of the number abstraction
- Added new converters for datetime, which will hopefully bring less issues

## v1.6.1 - 3 September 2022
- Made it possible to calculate distance between two places using map coordinates instead of lat/long

## v1.7.0 - 10 September 2022
- Regaus.py v2.0 compatibility: Renamed Kargadian language translation files and language translation counter
- Updated the list of places for Kargadian time to suit the new v2.0 structure
- Improved the way the places are shown on the Kargadian time list and in CobbleBot's playing status
- Updated the Playing status translations to use up-to-date forms of the language
- Fixed holiday countdowns yet again (hopefully this time it will actually work)

## v1.7.0.1 - 5 October 2022
- Fixed error where playing status couldn't calculate how long was left until a holiday because the date got converted into a datetime

## v1.7.0.2 - 20 October 2022
- Updated to Python 3.11
- Improved code for showing versions of libraries used

## v1.7.1 - 1 November 2022
- Added new places to Kargadia time
- Fixed issues arising from pytz timezones in places where Earth time is handled

## v1.7.2 - 9 November 2022
- `..time78` now takes the input time in your Earth timezone
- `..time78` now shows the timezone name for both Earth and Kargadia
- The time converter now also takes in the time in your Earth timezone and output in English

## v1.7.2.1 - 13 November 2022
- Fixed incorrect cases on Kargadian holiday names

## v1.7.2.2 - 29 November 2022
- Fixed timezone name causing `..time78` to break

## v1.7.3 - 5 December 2022
- Made it possible to use different fonts for your rank card (`..crank font`)
- Text colour customisation moved to `..crank text`
- Custom rank database values can now be null, in case the default values ever change
- Changed the font used in the `..colour` command to JetBrains Mono
- Improved text alignment in `..rank` and `..colour`

## v1.7.4 - 6 December 2022
- Improved how translation completion is counted in `..settings`

## v1.7.4.1 - 7 December 2022
- Better Kargadian timezone conversion for the birthdays loader

## v1.8.0-alpha1 - 9-11 December 2022
- Created a Kargadian name generator and citizen generator

## v1.8.0-alpha2 - 12 December 2022
- Added command to be able to actually see the generated names
- Fixed encoding issues with the names' json files
- Fixed the generator not being properly random for some reason
- ~~Generated birthdays will now be shown in the birthplace's timezone~~ (once the underlying Regaus.py code is fixed)

## v1.8.0-alpha3 - 12 December 2022
- Made generated birthdays younger - most people are now around 15-50 Kargadian years old

## v1.8.0-pre1 - 12 December 2022
- Added more error checking to try to prevent the bot from crashing due to connection errors
- Added button interactions to the Kargadian name/citizen generator
- Made places for birth, residence, and origin more random by removing population weights

## v1.8.0 - 12 December 2022
- Moved Kargadian events and holidays to a separate channel
- CobbleBot update announcements will now be shown in the Kargadia server

## v1.8.0.1 - 13 December 2022
- Fixed generator command going into an infinite while loop and breaking the bots when generating a surname from origin

## v1.8.1 - 18 December 2022
- Updated Senko Lair and Kargadian holidays

## v1.8.1.1 - 20 December 2022
- Reduced the frequency of origin surnames in the Kargadian name generator

## v1.8.1.2 - 3 January 2023
- Slightly changed Kargadian surnames

## v1.8.1.3 - 14 January 2023
- Added new Kargadian first name, Kista

## v1.8.2 - 14 January 2023
- Kargadia profile: Added support for surnames and protected profiles
- Kargadia profile: Added support for non-binary gender
- Kargadia profile: Made cult join date nullable
- Kargadia profile: Moved the profile to the top-level command (instead of `profile` subcommand)

## v1.8.2.1 - 14 January 2023
- Fixed `..timein` and `..timeago` breaking when an invalid time interval is specified (now it just zero seconds in the appropriate time class)

## v1.8.2.2 - 14 January 2023
- Kargadia profile now also shows the user's age (in Kargadian time)

## v1.8.3 - 4 February 2023
- Kargadian holidays and birthdays will now start and end at 6am
- Improved behaviour with update time adjustments for temporaries
- Added Mel's Twin Mountains, Kionagar, and Reksigar to Kargadian time display
- Rearranged Kargadian places in the time list to keep up with previously updated timezones
- Added comments to the Kargadian time display list, stating each place's timezone

## v1.8.3.1 - 22 February 2023
- Fixed the Kargadian birthday command always jumping a year ahead of itself
- Improved behaviour for the Kargadian time output when a place is not available

## v1.8.3.2 - 11 March 2023
- Created a local copy of Jishaku's reaction-based paginator, since it was removed from the library

## v1.8.4 - 23 March 2023
- Kargadian birthdays now show when they will begin in Earth time

## v1.8.4.1 - 1 April 2023
- Unloaded leveling from Cobble (I don't know why it was enabled to begin with?)

## v1.8.4.2 - 1 April 2023
- Playing statuses are now written in reverse during 1st April

## v1.8.5 - 22 April 2023
- Made it possible to set a personal language or have channel-specific languages

## v1.8.6 - 23 April 2023
- Added a few new first names
- Removed "origin" surnames
- Added "profile" as an alias to the Kargadian profile

## v1.8.6.1 - 24 April 2023
- The Kargadian name generator will now use places' habitability markers to determine whether a citizen could live or be born there

## v1.8.6.2 - 25-26 April 2023
- Updated spelling of certain Kargadian surnames
- Added a few new surnames and removed duplicates

## v1.8.7 - 27 April - 12 May 2023
- Reformatted the settings to make more sense UX-wise and look better code-wise
- If anything is written together with the `//settings` command, it now shows the help instead of current settings
- Added a command to specifically see the current settings (`//settings current`)
- The language translation counter now just shows the ratio of values which are equal to English, and no longer has special behaviour for different value types

## v1.8.8 - 12 May 2023
- Added new Kargadian first names
- Updated spellings of several male parent names
- Added 3 new places to the Kargadian time channel

## v1.8.9 - 18-19 May 2023
- Added Kaltelan (North Regaazdallian) language to the name generator
- Updated word-mix surnames for Nuunvallian (Central Regaazdallian) and updated the spellings for a few others

## v1.8.10 - 26 May 2023
- Once again updated spellings for names and surnames
- Reduced duplicates in the first names pool
- Added Munearan and Kovanerran names

## v1.8.11 - 27-28 May 2023
- Added Vaidanvallian names

## v1.8.12 - 28-29 May 2023
- Added Kaltanazdallian names

## v1.8.13 - 8 June 2023
- Updated discord.py to a new (alpha) version, so most commands should now behave better with Discord's new username system
- Updated most commands to use display names in the output, where it makes sense to
- Fixed Kargadian incorrectly declining "Regaus" in the lowercase

## v1.8.13.1 - 15 June 2023
- Updated the "translations may not be accurate" notice
- Made the weather command translate to natural languages again (once Regaus.py v3 is made)

## v1.8.14 - 21 August 2023
- Updated the declensions command to new language codes and to include Larihalian declension

## v1.8.15 - 8 September 2023
- Added removeall command to prefixes

## v1.9.0 - 9 September 2023
- Updated to Regaus.py v3.0
- Updated list of places used by the ka-time channels
- Changed "Developers" in the bot stats command to "Developer"
- Updated the hidden `..cobble` command to modern versions of Regaazdallian
- Changed some of the statuses to Custom Status now that it is possible

## v1.9.0.1 - 9 September 2023
- Updated the code to new language codes

## v1.9.0.2 - 24 September 2023
- Fixed `..eval` crashing when the error traceback is very long

## v1.9.0.3 - 23 October 2023
- Fixed Larihalian calendar not applying Kargadian timezone

## v1.9.1 - 7 December 2023
- Improved the code for choosing a status
- Switched all statuses to CustomActivity so they show up completely in Regaazdallian
- Added some new statuses
- Rearranged the chances so that 45% of the statuses are playing statuses while 20% are time and weather (instead of 40% and 25% respectively)
- Improved grammar on the hidden `..cobble` command

## v1.9.1.1 - 15 December 2023
- Fixed `..achievements` breaking due to using a method that no longer exists

## v1.9.2 - 15 December 2023
- Paginated the embed for the server's current settings

## v1.9.3 - 22 December 2023
- Made it possible to hide your age on the Kargadian profile (Enabled by default)
- Added commands to show or hide your age from the Kargadian profile
- Made the Kargadian birthdays say when it is your birthday instead of saying "your next birthday is 1 minute ago"
- Fixed the age shown on the Kargadian profile not taking the user's timezone into account

## v1.9.3.1 - 8 January 2024
- Fixed certain functions to work with Regaus.py v3.1 (after the change of behaviour in `.replace()` methods)