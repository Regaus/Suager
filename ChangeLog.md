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