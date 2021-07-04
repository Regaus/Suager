# Changelog for CobbleBot

## v0.1 - 6 December 2020
- Added Cobble XP and transferred Economy and SS23 from Suager

## v0.2 - 7 December 2020
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