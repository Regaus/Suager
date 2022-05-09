# Changelog for Mizuki (Kyomi's Bot)

## v0.1 - 17 June 2021
- Disabled certain commands for the bot

## v0.1.1 - 17 June 2021
- Added more statuses

## v0.1.2 - 17 June 2021
- Added another 2 statuses

## v0.1.3 - 17 June 2021
- Added pineapple command

## v0.1.3.1 - 20 June 2021
- Split Mizuki birthdays database from Suager's

## v0.1.4 - 21 June 2021
- Removed confirmation on setting your birthday
- Added ability to change your birthday
- Added command to delete your birthday

## v0.1.5 - 21 June 2021
- Added dance command

## v0.1.6 - 23 June 2021
- Added Midnight Desserts to the birthdays list

## v0.1.7 - 4 July 2021
- Added reminders to the bot

## v0.1.8 - 4 July 2021
- Improved birthdays invalid date output

## v0.1.9 - 8 July 2021
- Added a command to generate custom embeds

## v0.2.0 - 11 July 2021
- Added unicode garbage to the nickname designs and birthday message

## v0.2.1 - 11 July 2021
- Removed "Average members" stat from the stats command
- Improved the nickname designs message

## v0.3.0 - 18 July 2021
- Added reaction roles

## v0.3.1 - 18 July 2021
- Updated emotes to be usable outside of Senko Lair

## v0.3.1.1 - 18 July 2021
- Moved the reaction role note to the command description
- Fixed reaction group types description not having newlines

## v0.3.2 - 2 August 2021
- Enabled settings

## v0.3.3 - 3 August 2021
- Added more statuses

## v0.3.4 - 22 August 2021
- Slightly changed nick designs message

## v0.3.5 - 27 August 2021
- Automatic ~~unicode garbage~~ nickname designs for new MD members and boosters
- Make the embed command try to have newlines with \n

## v0.3.5.1 - 2 September 2021
- Made settings command not load irrelevant settings, and made the template only contain relevant settings
- Fix booster nickname detection

## v0.3.5.2 - 13 September 2021
- Made the playing status update speed 2 minutes rather than 2m30s

## v0.3.6 - 15 September 2021
- Made birthday statuses show up 20% of the time, while other playing statuses are 80%

## v0.3.7 - 18 September 2021
- Improved the invite command

## v0.3.8 - 22 September 2021
- Added ability to give multiple roles at once

## v0.4.0 - 12 October 2021
- Added message logs

## v0.4.1 - 22 December 2021
- Added ability to send users a DM when a mod action is taken against them

## v0.4.2 - 28 December 2021
- Enabled mute commands (why were they disabled in the first place?)
- Improved the Message Edited embed on message logs

## v0.4.2.1 - 29 December 2021
- Removed "by x" part from the mod DMs

## v0.5.0 - 19 January 2022
- Made temporaries log their initialisation messages instead of printing
- Reminders are now dealt with separately from temporary punishments
- Massively improved the way the temporary mutes code looks like
- Moderation commands should now log their actions to the mod log channels
- You can no longer unmute a user who is not muted

## v0.5.1 - 21 January 2022
- Fix reminders commands still using the old system
- Fix mute list command still using the old system
- The mute list command can now also show permanent mutes

## v0.5.2 - 2 February 2022
- Made temporary events handle muted users leaving and rejoining

## v0.5.3 - 9 February 2022
- Updated discord.py to v2.0
- Improved error handling for commands
- The `m!guild` command can now show other guilds (if available)
- The `m!reminders` command will no longer send into DMs unless invoked there
- The help command should no longer send into DMs unless invoked there
- Commands you don't have perms for should now show up in the help command
- Changed owner-only commands to use the discord.py is_owner() check

## v0.5.3.1 - 10 February 2022
- Made failed permissions check raise MissingPermissions error for the custom error message

## v0.5.4 - 10 February 2022
- Made the help command work the way it's supposed to
- Commands that can't be used in the current channel are simply crossed out instead of not showing up at all
- Made it possible to show some extra text alongside the help embed
- The help command will no longer send reactions when responding

## v0.5.4.1 - 10 February 2022
- Fix events errors to actually log what happened

## v0.5.5 - 11 February 2022
- Updated `//birthday set` to no longer require zeros at front
- Made the "crossed out commands" warning only show up in the help output for the entire bot

## v0.5.6 - 12 February 2022
- Make it possible to see what files were sent to the bots' DMs

## v0.5.7 - 17 February 2022
- Allow `//timesince` to go beyond the 0-9999 year range
- Fixed admin eval error traceback breaking

## v0.5.8 - 18 February 2022
- `//timesince` now uses proper `YYYY-MM-DD hh:mm:ss` format for specifying time

## v0.6.0 - 18-20 March 2022
- Added warning settings
- Kick and ban now try to make sure the user can be kicked/banned before doing so
- Ban and massban now check if the user has already been banned from the server
- Massban command now checks for members first and then the reason as the last argument
- Improved the way the massban command works

## v0.6.1 - 20 March 2022
- Improved output for massban command
- Added massunban and masskick commands

## v0.6.2 - 3-5 April 2022
- Mass-mute command

## v0.6.3 - 7 April 2022
- Made the mute list command show the Case ID
- Improved the output of the mute list command

## v0.6.4 - 12-13 April 2022
- The author is no longer appended to the reason shown in mod logs and database (since the author is stated anyways)
- The mod log messages will now state the user IDs
- Mass-unmute command
- Set the avatar commands to output in size=4096

## v0.6.5 - 19 April 2022
- Warning command

## v0.6.6 - 20 April 2022
- Mass-warn command
- Made the mute length when reaching too many warnings scale properly
- Warns list command

## v0.6.7 - 29 April 2022
- Fixed reminders not deleting
- Pardon command

## v0.7.0 - 2 May 2022
- Mod log command

## v0.7.1 - 7-8 May 2022
- Class-based birthdays structure
- Support for timezones in birthdays

## v0.7.1.1 - 9 May 2022
- Fixed the birthdays incorrectly switching themselves between UTC and their actual timezone

## v0.7.2 - 9 May 2022
- Massively improved the way the command to set your timezone works