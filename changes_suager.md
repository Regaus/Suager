# Changelog for Suager
# Logs since v5

## v5.0.0 - 1 June
- Moved Infidel Lists away from config
 
## v5.0.1 - 2 June
- Improved locks and //stats

## v5.0.2 - 2 June
- Removed value strings (now shows `1,000,000` instead of `1 million`)
- Improved on_ready loop

## v5.0.2.1 - 2 June
- Improved readme
- Updated license

## v5.1.0 - 2 June
- Major change in how the Infidel List works
- Fixed floats in //rate

## v5.1.1 - 2 June
- Fixed Infidel List adding and removal

## v5.1.2 - 3 June
- //tell can now ping people

## v5.1.3 - 4 June
- Fixed leveling for infidels
- Fixed social commands
- //infidels down will now move *down* the list
- You can't lick me anymore

## v5.1.4 - 7 June
- Better logging system

## v5.1.5 - 7 June
- Leveling leaderboards will no longer show people who still have Undefined#0000 as name and people who have 0 XP

## v5.1.6 - 7 June
- Bank command: shows leaderboard by money
- Levels and glevels will now output total users amount
- Almost finished the Russian translation

## v5.1.6.1 - 7 June
- Drip can lick me
- Licking yourself will no longer have any message

## v5.1.6.2 - 7 June
- Settings template no longer has placeholders 
- Send should no longer error out if it doesn't have permissions to embed links or attach files

## v5.1.7 - 7 June
- You can no longer add channels to anti-spam or ignore channels if they are already on the list
- Fixed some Russian strings

## v5.1.7.1 - 8 June
- Banging me will no longer work

## v5.1.8 - 9 June
- A "google" command

## v5.1.8.1 - 10 June
- requirements.txt should now install the correct version of discord.py (1.4.0a)

## v5.1.9 - 12 June
- Searching logs for a specific date
- Levels will no longer show people with negative level

## v5.1.10 - 14 June
- Anyone except choco can lick me
- Anyone except choco can sniff me
- Licc is now an alias of lick 
- Added some 8ball responses

## v5.1.10.1 - 14 June
- Changing Suager's nickname in odashi won't work anymore
- Added kith and kish as aliases for kiss

## v5.1.10.2 - 15 June
- Locked Cryptic from lick
- Better love lock message

## v5.1.11 - 16 June
- Improved lock command
- Unlocked choco's commands

## v5.1.12 - 16 June
- Command for base conversions
- Time for Kargadia
- Owoify command

## v5.1.12.1 - 19 June
- Improved time2
- Slightly changed owoify

## v5.1.12.2 - 21 June
- Improved time2

## v5.1.12.3 - 21 June
- Hopefully done with time2
- Fixed bases command

## v5.1.13 - 22 June
- More ship names

## v5.2.0b1 - 22 June
- Removed Stages 5, 6, and 7
- timedelta now uses human_timedelta
- Fixed vibe check
- Restructured admin commands a bit
- Tags system

## v5.2.0 - 22 June
- Fixed love exception list
- Updated invalid tag names list
- Russian translation for tags

## v5.2.1 - 23 June
- No more counters in embeds

## v5.3.0 - 26 June
- Negative leveling
- You can't bang bots
- You can't feed bots
- Made Suager narcissistic in terms of hotness
- Fixed shop settings description
- Fixed weather command breaking when country is not available
- Renamed USA to Enslaved Shooting Range in weather

## v5.3.1 - 26 June
- Level -2 command now sets to level -5001

## v5.3.2 - 27 June
- Meme generation

## v5.3.3 - 27 June
- Meme command should now stretch image if you input long text
- Moderation commands should now account for user permissions
- Fixed some cooldowns

## v5.3.4 - 27 June
- //colour random should now work properly
- You should no longer be able to rename a tag to a name that is already used

## v5.3.4.1 - 28 June
- owoify will no longer show the !?'s and just replace them

## v5.3.4.2 - 28 June
- Added another forbidden tag name
- Made grant role actually work

## v6.0-alpha1 - 7 July
- Support for multiple bots running
- Removed Infidel List
- Removed language support, at least for now.
- Removed gender support
- XP displayed will now be 100x smaller
- XP requirements will no longer depend on server multiplier
- Added some stuff that will never matter

## v6.0-alpha2 - 7 July
- Time for Zeivela and Kaltaryna proof-of-concept created
- `ri` as alias for reload images command

## v6.0-alpha3 - 10 July
- TBL with stats and clan
- Improved handling of SS23 time
- SS23 "Weather"

## v6.0-alpha4 - 13 July
- Hopefully fixed data_io encoding issues
- Ratings now remind you that you're talking to a bot
- Fixed some stuff with ss23 weather

## v6.0-alpha5 - 16 July
- Improved TBL and added some details
- Added DLRAM
- Added timetb command
- Added some stuff which will be later used for translations

## v6.0-alpha6 - 17 July
- Added TBL Seasons
- Added ability to set your location in TBL
- Improved stats command
- Improved DLRAM energy regeneration speeds

## v6.0-beta1 - 4 August
- Added nlc command for NEWorld lat/lo calculation
- Updated RSL-1 month names in SS23
- Nuts and XP multiplier events
- Support for multiple languages
- Updated some TBL details
- Improved DLRAM recharging
- Improved DLRAM leveling
- Improved DLRAM game outputs
- Social counters will now be per-user instead of per-guild

## v6.0-beta2 - 4 August
- Float outputs in different bases
- Added "random" filter
- Added sepia filter
- Improved some command outputs

## v6.0-beta3 - 4 August
- Support for floats in base conversions from base 10
- Removed owoify and neon commands due to no usage

## v6.0-beta4 - 5 August
- Removed global levels
- Improved levels
- Fixed some broken outputs

## v6.0-beta5 - 5 August
- Added some meme commands from VAC Efron's API
- Moved colour command to Utility
- Fixed some leveling commands breaking
- Improved leveling reset on leave

## v6.0-beta6 - 6 August
- Improved cooldowns
- Russian translation almost done

## v6.0-beta7 - 7 August
- Fixed a few minor bugs
- RSL-1 translations for birthdays and discord cogs

## v6.0-beta8 - 8 August
- Updated cooldowns to be a little bit less strict
- RSL-1 translation for DLRAM and economy
- The list of languages can now be accessed as a separate command

## v6.0-beta9 - 11 August
- `//bases from` now works again
- RSL-1 translations for Entertainment, Images, Bot info, Leaderboards, Leveling, Ratings, and Social commands
- Improved blocked message logger

## v6.0-beta10 - 12 August
- When the bot is removed from a server, it will now delete data associated with it
- Welcome and goodbye messages for Senko Lair

## v6.0-beta11 - 12 August
- Improved how blocked logs work
- Suager updates will now be sent from Suager testing server

## v6.0-beta12 - 12 August
- Improved leveling for the lower levels
- "Old level" now shows the level before this update, instead of v5 leveling
- Improved DLRAM charge limit and recharge speed
- Improved TBL energy limits

## v6.0-beta13 - 12 August
- RSL-1 for Tags and Utility, and also some of TBL

## v6.0-beta14 - 13 August
- Hopefully done messing around with DLRAM
- Fixed the server icon command not showing any output

## v6.0.0 - 15 August
- Removed "old levels"
- Updated DLRAM levels, and reduced energy amount
- Removed "core bot" from config example
- Updating short version will no longer change the last update time

## v6.0.1 - 18 August
- Fixed level rewards allowing default role to be rewarded, and allowing to set levels below -256
- Fixed tag info breaking when content was too long
- //tbl run is now an alias to //tbl play
- Fixed DLRAM skipping level 69 and alike
- Fixed playing status changing quicker than it was supposed to
- Fixed logs not opening properly
- Added support for float conversions to base 10 from other bases

## v6.0.2 - 19 August
- Fixed Suager status changes and added some more
- Ability to change the activity type for Suager
- Improved the way the log command works
- Removed core_bot from database tables

## v6.0.3 - 19 August
- Logging avatars again

## v6.0.4 - 21 August
- Fixed user statuses showing up incorrectly
- Updated the playing statuses of Suager

## v6.0.5 - 22 August
- Fixed some output bugs
- Added partial translation to Ancient RSL-3

## v6.0.6 - 24 August
- Continued the RSL-3a translation
- Added //pain command, which displays your rank in RLS-3a

## v6.0.7 - 24 August
- Fixed //nextlevel showing incorrect level
- Changed TBL energy limits slightly

## v6.0.8 - 25 August
- Made plurals work better in English
- Fixed a bug which broke the //user command when they had above 15 roles

## v6.1.0 - 28 August
- Added Aqos
- Improved language support
- Updated social cooldowns

## v6.1.1 - 31 August
- De-hoisting for SL

## v6.1.2 - 1 September
- Fixed a bug breaking leveling down
- Fixed a bug breaking leave server event
- Fixed a bug breaking TBL season update
- Fixed a bug that sometimes prevented update messages from sending

## v6.1.2.1 - 4 September
- Fixed bases trying to treat an integer as a float
- Fixed Suager on_ready breaking because playing is no longer a key in the config
- SL time is now also displayed in the test server

## v6.1.2.2 - 4 September
- Hopefully fixed image gen not working from ImportError if a package is not supported

## v6.1.3 - 4 September
- Updated the leveling system

## v6.1.4 - 5 September
- Fixed Aqos stats energy output
- Added score to Aqos stats
- Added number translation to RSL-1

## v6.1.5 - 6 September
- The max level is now 250
- The first level's requirement is now 250 XP
- Improved RSL-1 number translation algorithm
- Tag pages should no longer show that there are more pages than there actually are
- Suager will now use base-10 even in RSL mode

## v6.1.6 - 8 September
- The max level is now 500
- Added old levels command, which shows information about older leveling systems
- Added s u c c command
- Suppress the existence of RSLs in //languages unless the person and guild are trusted with that shit

## v6.1.7 - 11-12 September
- Updated level 69 behaviour
- Removed hat kid from the "trusted" in //languages
- Updated RSL-1 and RSL-3 time outputs
- Removed Kaltaryna RSL-1
- //time will only output SL time in RSL-1
- Translated Aqos into Russian and RSL-1
- Added RSL-1 translation for TBL details commands, location descriptions, and totems
- TBL events end times will now be translated into their target language
- Generally updated RSL-1 locale
- Choco now won't be able to use //say. You're blocked for a fucking reason, god damn it.
- Avatar changes will now just get logged in their channel, and no longer be saved onto disk.

## v6.1.8 - 14-15 September
- Added RSL-5 Kargadia time
- Added RSL-5 locale (WIP)
- Custom messages for //time in RSL-1 and -5
- Timesince will no longer allow dates before 277 AD in RSL-1 and -5 locales
- Updated plurals function
- Updated time output functions
- Time23 will no longer works with dates after 9500 AD
- Removed timetb
- Fixed server status showing activity percentages from all members, instead of from online members

## v6.1.9 - 16 September
- Time23 will now work up to 1687 AD
- Updated Zeivela-2 output for time23
- Improved Kargadia time output in RSL-5
- Added RSL-5 Earth time output
- Updated case for months in RSL-1 and -2 (both time23 and generic time)

## v6.1.10 - 17 September
- Added Blacklist
- Added owner-only commands to add and remove people from the blacklist

## v6.1.11 - 20 September
- Updated TBL location activity calculation
- TBL XP levels now go up to 250
- TBL Clan levels now go up to 225
- Added 2 new locations to TBL (Unlock on XP levels 225 and 250)
- Removed TBL round limit
- TBL now speeds up at further rounds
- TBL now updates every 1 second instead of 1.5
- TBL now caps out at 250,000 people activity
- TBL location now automatically updates on levelup
- TBL now has a small chance to boost your rewards
- Fixed TBL stats next shaman level XP requirement output
- Added chocolatt to the Blacklist
- Removed meme command

## v6.1.11.1 - 21 September
- The "Magic Help" no longer boosts player count in TBL

## v6.1.12 - 23 September
- Updated time23 and added time24

## v6.1.12.1 - 29 September
- Renamed 23.6 to planet name instead of place name in time23
- Connectors have been set to ssl=False to work on my old laptop that I'm trying to host the bot on now

## v6.2.0 - 3 October
- Removed RSL-3 and RSL-5 locales
- Removed Aqos, TBL and DLRAM
- Updated and slightly improved time23 outputs
- Changed rank font to Whitney
- Updated some of the strings for Russian and RSL-1 locales
- Removed pain command

## v6.2.1 - 3 October
- Updated discord.py to v1.5
- Commands removed because they no longer work properly:
  - server status
- Commands altered because they no longer work properly:
  - user (will no longer show status and activity)
- Commands removed due to lack of usage:
  - amiowner
  - epic
  - frogge
  - notwork
- Commands added:
  - achievement
  - challenge
  - calling
  - captcha
  - facts
  - scroll
  - didyoumean
  - drake
  - distracted
  - role members
- Fixed createdat
- Updated server bots
- Colourify now supports 2 colours specified
- Social commands will now use embed description instead of title

## v6.2.2 - 3 October
- Improved and updated playing statuses

## v6.2.3 - 4 October
- Improved logs command
- Social commands back to title embed
- Ship, bad, and trash now use User instead of Member
- Kuastall-11 for time24

## v6.2.4 - 4 October
- Finally added mute command (does not support duration)
- Locked more social actions from being done on me
- Updated settings mute role response

## v6.2.4.1 - 5 October
- Updated leveling bias

## v6.2.5 - 9 October
- Fixed economy shop command
- Added message read to ping command

## v6.2.6 - 9 October
- Improved de-hoist
- Fixed birthday output

## v6.3.0 - 10 October
- Message delete and edit logs for Senko Lair
- Locked poke from being used on me
- Message on ban and unban from Senko Lair
- Added tag search and tag unclaimed
- Added rape command for SR 9

## v6.3.0.1 - 10 October
- Removed message read from ping
- Removed cooldown from rape

## v6.3.0.2 - 11 October
- Made the network warning different
- Made Leitoxz 99.9% hot and rated 100%

## v6.3.1 - 20 October
- Senko Lair time now shows both Earth and Kargadia equivalents
- Updates Kargadia RSL-1 month names
- Added Kuastall RSL-1 locale
- Images cog now uses embeds so that you don't have to wait for a minute to see a single image

## v6.3.1.1 - 21 October
- Added some test code to birthdays, maybe will help it not send happy birthdays 4 times in a row

## v6.3.2 - 30 October
- Fixed weather command time outputs in RSL-1
- Turned trash and ship into embeds
- Most of Kuastall RSL-1 translation done

## v6.3.3 - 31 October
- Finished Kuastall RSL-1 translation

## v6.3.4 - 7 November
- Added a semi-broken tts command
- Fixed one cause of errors breaking the bot

## v6.3.5 - 16 November
- Updated locks for social commands aimed at me
- Added laugh, tickle, punch, kill

## v6.3.6 - 19 November
- Updated kill command output
- Added kill counter
- Updated dehoist nick updater

## v6.3.7 - 22 November
- Fixed AlexFlipnote API
- Added another message encryption method (beta)
- Improved colour command

## v6.4.0-pre1 - 23 November
- Renamed old Economy to Social Interaction
- Replaced currency with Social Interaction Points
- Removed bal, donate, buy, shop (will return with new Economy)
- Renamed profile to sip
- Updated SIP calculations algorithm
- Updated tables command
- Updated RSL-1 Kuastall strings

## v6.4.0-pre2 - 23 November
- SIP now accepts User instead of Member
- Added Economy extension
- Accounts can now be created
- Added balance command
- Moved all leaderboards to one command

## v6.4.0-pre3 - 23 November
- Put leaderboards back as separate commands
- Improved the way it gets the data to not repeat too much code

## v6.4.0 - 26 November
- Kill no longer changes nickname
- Added work and daily commands
- Re-added buy

## v6.4.1 - 27 November
- Added a few more NSFW actions
- Updated 8ball to use strings

## v6.4.2 - 6 December
- Removed Social Interaction Points
- Moved Economy and SS23 to CobbleBot
- Created CobbleBot
- Moved leaderboard generator outside of Leveling class
- Max level reduced to 200

## v6.4.3 - 8 December
- Removed a lot of commands from Fun and Images that were not used at all and that don't matter to me
- Made ship command generated by Suager instead of using the API
- Merged Discord into Utility and moved dm, atell, tell, say into Utility

## v7.0-pre1 - 16 December
- Added new leveling system that should come into effect on 1st January 2020
- Combined leveling and leaderboards with CobbleBot
- Shared database
- Removed changes.json since it's useless by now

## v7.0-pre2 - 19 December
- Updated RSL-1 locale

## v7.0-pre3 - 20 December
- Replaced shop with roles
- Fixed beer reason