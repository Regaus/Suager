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

## v1.0.0 - 19 January 2022
- Made temporaries log their initialisation messages instead of printing
- Reminders are now dealt with separately from temporary punishments
- Massively improved the way the temporary mutes code looks like
- Moderation commands should now log their actions to the mod log channels
- You can no longer unmute a user who is not muted

## v1.0.1 - 21 January 2022
- Fix reminders commands still using the old system
- Fix mute list command still using the old system
- The mute list command can now also show permanent mutes

## v1.0.2 - 2 February 2022
- Made temporary events handle muted users leaving and rejoining

## v1.0.3 - 9 February 2022
- Updated discord.py to v2.0
- Improved error handling for commands
- The `m!guild` command can now show other guilds (if available)
- The `m!reminders` command will no longer send into DMs unless invoked there
- The help command should no longer send into DMs unless invoked there
- Commands you don't have perms for should now show up in the help command
- Changed owner-only commands to use the discord.py is_owner() check

## v1.0.3.1 - 10 February 2022
- Made failed permissions check raise MissingPermissions error for the custom error message

## v1.0.4 - 10 February 2022
- Made the help command work the way it's supposed to
- Commands that can't be used in the current channel are simply crossed out instead of not showing up at all
- Made it possible to show some extra text alongside the help embed
- The help command will no longer send reactions when responding

## v1.0.4.1 - 10 February 2022
- Fix events errors to actually log what happened

## v1.0.5 - 11 February 2022
- Updated `//birthday set` to no longer require zeros at front
- Made the "crossed out commands" warning only show up in the help output for the entire bot

## v1.0.6 - 12 February 2022
- Make it possible to see what files were sent to the bots' DMs

## v1.0.7 - 17 February 2022
- Allow `//timesince` to go beyond the 0-9999 year range
- Fixed admin eval error traceback breaking

## v1.0.8 - 18 February 2022
- `//timesince` now uses proper `YYYY-MM-DD hh:mm:ss` format for specifying time

## v1.1.0 - 18-20 March 2022
- Added warning settings
- Kick and ban now try to make sure the user can be kicked/banned before doing so
- Ban and massban now check if the user has already been banned from the server
- Massban command now checks for members first and then the reason as the last argument
- Improved the way the massban command works

## v1.1.1 - 20 March 2022
- Improved output for massban command
- Added massunban and masskick commands

## v1.1.2 - 3-5 April 2022
- Mass-mute command

## v1.1.3 - 7 April 2022
- Made the mute list command show the Case ID
- Improved the output of the mute list command

## v1.1.4 - 12-13 April 2022
- The author is no longer appended to the reason shown in mod logs and database (since the author is stated anyways)
- The mod log messages will now state the user IDs
- Mass-unmute command
- Set the avatar commands to output in size=4096

## v1.1.5 - 19 April 2022
- Warning command

## v1.1.6 - 20 April 2022
- Mass-warn command
- Made the mute length when reaching too many warnings scale properly
- Warns list command

## v1.1.7 - 29 April 2022
- Fixed reminders not deleting
- Pardon command

## v1.2.0 - 2 May 2022
- Mod log command

## v1.2.1 - 7-8 May 2022
- Class-based birthdays structure
- Support for timezones in birthdays

## v1.2.1.1 - 9 May 2022
- Fixed the birthdays incorrectly switching themselves between UTC and their actual timezone

## v1.2.2 - 9 May 2022
- Massively improved the way the command to set your timezone works

## v1.2.3 - 9 May 2022
- Timezone support for input and output

## v1.2.4 - 11 May 2022
- Made it possible to see a user's local time

## v1.2.5 - 17 May 2022
- `m!birthday` now shows how long is left until the user's next birthday
- Bumped versions to v1 since all the main requested features are present

## v1.2.6 - 17 May 2022
- Better base conversion command syntax

## v1.2.7 - 17 May 2022
- Greatly reduced the amount of default values for `m!timesince`
- Fixed `m!timesince` ignoring the user's timezone in the default values

## v1.2.7.1 - 17 May 2022
- Added Kyomi's useless bots

## v1.2.8 - 22 May 2022
- Updated some social commands' responses when Mizuki or another bot is the target
- Added `m!smug`, `m!nibble`, and `m!feed`
- Made the images load up when the bot is ready
- Made the counters separate per bot
- As a result, Mizuki's social counters have been reset

## v1.2.9 - 24 May 2022
- `m!handhold` command

## v1.2.10 - 17 June 2022
- Language strings now use keywords for better understandability
- Ship now only shows one name (chosen randomly)
- Improved how translation completion is counted (made all language names count as one large "string")
- West Kargadian translation for discord-related commands and various error messages

## v1.2.11 - 18 June - 13 August 2022
- West Kargadian translation for the rest of the commands
- Updated discord.py and other dependencies to the latest versions
- Commands using a single MemberID will now show the invalid input
- Fix `m!reminders edit` improperly converting timezones because datetime was designed by monkeys
- Numbers should no longer show up as links on Android

## v1.2.11.1 - 21 August 2022
- Handle emotes kwarg no longer being added in Regaus.py v2.0

## v1.2.11.2 - 3 September 2022
- The database builder now uses the actual type string instead of the number abstraction
- Added new converters for datetime, which will hopefully bring less issues

## v1.2.11.3 - 3 September 2022
- Made a "protected" list for social commands so that my bots could also be protected from being slapped or whatever

## v1.2.11.4 - 4 September 2022
- Fixed mod commands breaking when multiple bots have settings saved for the server

## v1.2.11.5 - 20 October 2022
- Updated to Python 3.11
- Improved code for showing versions of libraries used

## v1.2.11.6 - 15 November 2022
- Database errors will now be logged instead of getting silently ignored

## v1.2.12 - 5 December 2022
- Changed the font used in the `m!colour` command to JetBrains Mono
- Improved text alignment in `m!rank` and `m!colour`

## v1.2.13 - 6 December 2022
- Improved how translation completion is counted in `m!settings`

## v1.2.13.1 - 12 December 2022
- Changed the default happy birthday message

## v1.3.0-pre1 - 14-16 December 2022
- Added an anti-ad filter that can remove unwanted Discord links
- Added an images-only filter that can remove text messages from specified channels

## v1.3.0-pre2 - 16 December 2022
- Added ability to change the duration of the warning given to advertisers
- Discord links don't have to start with `https://` to be detected
- The channel lists for anti-ads and image-only will now detect if you try to add a channel already in the list
- Changed the mute length for warnings to be shown in full when set

## v1.3.0-pre3 - 16 December 2022
- Anti-ads and image-only will now detect if they can send the warning message. If not, they will silently do their job
- Turned FakeContext into a dataclass

## v1.3.0 - 16 December 2022
- All links are now treated as valid for image-only, regardless of whether they actually contain an image or not
- Message-related auto-moderation (image-only and anti-ads) will now also handle message edits

## v1.3.1 - 16 December 2022
- Popular discord server listings are now also blocked if anti-ads are enabled

## v1.3.1.1 - 9 March 2023
- Slightly idiot-proofed reminders

## v1.3.1.2 - 11 March 2023
- Created a local copy of Jishaku's reaction-based paginator, since it was removed from the library

## v1.3.2 - 23 March 2023
- Permission checks for moderation commands can no longer be bypassed by the bot owner

## v1.3.3 - 29 March 2023
- Added a command to give people some cheese

## v1.3.3.1 - 1 April 2023
- Playing statuses are now written in reverse during 1st April

## v1.3.4 - 6 April 2023
- Added command to tuck someone into bed
- Added new emotes to the emote list and rearranged the list
- Replaced the old Alex emotes with new ones

## v1.3.5 - 10 April 2023
- Made get_data() into a staticmethod
- Tried to more strictly make sure that the lists for social commands don't magically become a string
- Made social command responses more adaptive when there is a difference in the counters

## v1.3.6 - 11 April 2023
- Added a command to wave at someone
- The "target has only x'd author back" string is now used if the counters difference is 5 or more, rather than 6 or move

## v1.3.7 - 11 April 2023
- The strings are now also adjusted if the author did the action 5+ times less than the target

## v1.3.7.1 - 15 April 2023
- The starboard now tracks which bot saw the message
- The starboard now tracks star count better when two bots see the message at the same time

## v1.3.7.2 - 15 April 2023
- Star count is now read from the reaction count on the actual message

## v1.3.8 - 15 April 2023
- The starboard now tries to embed attachments and links, and if it fails, sends links to them
- The starboard now prints error messages

## v1.4.0a1 - 27 April - 13 May 2023
- Reformatted settings to make more sense UX-wise and look better code-wise
- If anything is written together with the `m!settings` command, it now shows the help instead of current settings
- Added a command to specifically see the current settings (`m!settings current`)
- Made message logs settings actually possible to view
- Made edited messages actually go to the channel for edited message logs (instead of the channel for deleted messages)
- The language translation counter now just shows the ratio of values which are equal to English, and no longer has special behaviour for different value types

## v1.4.0a2 - 31 May 2023
- The `m!embed` command's description now tells you to use `\n` for newlines
- Social commands now only trigger the "only" response if the difference in counters is more than 20% of the sum

## v1.4.0a3 - 8 June 2023
- Updated discord.py to a new (alpha) version, so most commands should now behave better with Discord's new username system
- Updated most commands to use display names in the output, where it makes sense to

## v1.4.0a4 - 15 June 2023
- Updated the "translations may not be accurate" notice
- Made the weather command translate to natural languages again (once Regaus.py v3 is made)

## v1.4.0a5 - 24 June 2023
- Fix reminders list using the username instead of display name

## v1.4.0a6 - 9 July 2023
- Rewrote birthday settings to the new standard
- Birthday-related settings now have specific commands to disable things, rather than being reset when input is empty

## v1.4.0a7 - 30 July 2023
- Log files now ignore encoding errors and replace them with a special character instead of spamming errors to chat
- Log files should now be sorted alphabetically before being appended to the output

## v1.4.0a8 - 30 July, 4 August 2023
- Rewrote message logs settings
- There are now separate commands to set the channel for edited and deleted messages, as well as a command to set both at once

## v1.4.0a9 - 4 August 2023
- Fixed reaction roles trying to remove a role that the member doesn't have

## v1.4.0a10 - 22 August 2023
- Counters now only require a 5% difference rather than 10% to give the "user has only done it x times" response

## v1.4.0a11 - 23, 25 August 2023
- Rewrote join roles, welcome/farewell, mod DMs, mod logs, and user logs settings to the new standard
- These settings now have specific commands to disable things, rather than being reset when the input is empty
- Mod DM and mod log settings now have separate commands for each setting, as well as a command to enable/disable all the settings at once
- Role preservation has been moved to a separate command rather than being a subcommand of user logs

## v1.4.0a12 - 8 September 2023
- Rewrote warnings, anti-ads, and image-only settings to the new standard
- The anti-ads now have specific commands for changing the list mode
- The anti-ads and image-only settings now have separate commands for adding and removing channels
- The anti-ads warning length can no longer be set above 5 years
- The anti-ads warning length is now shown in full form, rather than showing the short string stored in the settings
- Warnings now have a separate text when the duration is more than 5 years, rather than using the same text as the mute command

## v1.4.0 - 8 September 2023
- Added removeall commands to prefixes, leveling ignored channels, leveling role rewards, and message logs ignored channels

## v1.4.1 - 9 September 2023
- Updated to Regaus.py v3.0
- Made the old time module use `datetime.min` instead of `datetime.now()` to measure length of relativedeltas
- Changed "Developers" in the bot stats command to "Developer"
- Birthdays are now stored as a `date` rather than `datetime` in the database
- Changed some of the statuses to Custom Status now that it is possible

## v1.4.1.1 - 24 September 2023
- Fixed `m!eval` crashing when the error traceback is very long

## v1.4.1.2 - 6 December 2023
- Fixed glitchy custom statuses

## v1.4.2 - 7 December 2023
- Improved the code for choosing a status
- Turned version and countdown statuses into custom status

## v1.4.3 - 15 December 2023
- Added a paginator with a fixed amount of lines per page, rather than max characters
- Added paginators to `m!warns` and `m!punishments`
  - These will default to the last page, thereby showing the latest warnings/punishments first

## v1.4.4 - 15 December 2023
- Paginated the embed for the server's current settings (Embeds for subcategories, e.g. leveling, keep their normal embeds)

## v1.4.4.1 - 5 February 2024
- Fixed the `m!laugh` command not working when a user was mentioned

## v1.4.5 - 5 February 2024
- Added a command to sync slash commands (`m!sync`)
- Made command completion and command error handlers deal with the existence of slash commands
  - Note: Mizuki currently has no slash commands

## v1.5.0 - 30 May 2024
- Added ability to show certain stats about the server using voice channel names

## v1.5.1 - 5 June 2024
- Turned `m!time` into an embed

## v1.6.0 - 15-25 August 2024
- Rewrote reaction roles to have a more intuitive UI/UX
  - Old groups should (hopefully) keep working as before, but might not necessarily work well if you try to edit them
  - The bot is now required to have access to the emotes when creating or editing the reaction roles, which was not the case before
- The bot can no longer give itself reaction roles while adding reactions to the message
- Unlocked reaction roles for all servers
- Views now have their context as `message.clean_content` rather than `message.content` for text commands (for consistency with command logs)

## v1.6.0.1 - 25 August 2024
- Temporaries: put the `asyncio.sleep()` calls into `finally:` blocks to make the functions sleep even if an error is raised

## v1.6.0.2 - 8 December 2024
- Error logs will now be forwarded to the #error-logs channel

## v2.0.0a1 - 8 December 2024
- Converted birthday-related commands into hybrid commands
- Added a user context menu to check someone's birthday

## v2.0.0a2 - 21 December 2024
- Converted commands from the Fun category into hybrid commands with interactive views
- Incorporated the Language into all Views, with the language being an optional argument (since many views don't need it)

## v2.0.0a3 - 21-22 December 2024
- Commands in the Images category will no longer use any API
  - `m!colourify` and `m!filter` actually work now and use local code
- Made Images commands hybrid

## v2.0.0a4 - 22 December 2024
- Made Bot Information commands hybrid
  - The `m!invite` command only has a slash equivalent on Suager, as the other bots are private.

## v2.0.0a5 - 2-15 January 2025
- Made Moderation commands hybrid
  - These test for permissions as a regular check, even though slash commands allow server owners to set up a different system. That may be changed if it ever is necessary.
  - Mass commands (`m!masskick`, `m!massban`) take the users as a string, as slash commands don't have an equivalent to `Greedy[]`
  - The responses to moderation commands (`m!kick`, `m!ban`, etc.) are non-ephemeral
  - Commands like `m!mute` and `m!warn` which allow for specifying a duration have the duration as a separate argument in the slash command form
- The commands `m!mute`, `m!massmute`, `m!unmute`, `m!massunmute`, `m!mutelist`, `m!warn`, `m!masswarn`, `m!pardon`, and `m!modlog` now require Moderate Members permission instead of Kick Members
- `m!mutelist` now uses a proper paginator, just like `m!warnings`
- `m!warnings` now requires the Moderate Members permission to see the warnings of other members
- `m!find` now requires the Moderate Members permission instead of Ban Members
- Updated the "specified user ID matches this bot's user ID" check on Moderation commands to run before permissions checks (so that the appropriate response is actually shown)
- Replaced "You've" with "You have" in the moderation DMs
- Mass commands no longer terminate early if one of the specified users doesn't pass the check
- Added an on_error handler to the Leveling context menus

## v2.0.0a6 - 17 January 2025
- Unified the handling of text and slash command errors into one common function
- Added an `on_error` handler for all slash commands, so that I no longer have to add error handlers individually
- Added an `interactions.log_interaction()` call to the slash versions of Moderation commands
- Fixed `m!colourify` not working due to a missing await

## v2.0.0a7 - 19 January 2025
- Made Social commands hybrid
  - These commands are now user-installable and available in DMs
  - Made the text versions no longer guild-only too
- Updated all Social commands' cooldowns to 5 seconds
- Fixed the guild name showing up empty in user-install contexts

## v2.0.0a8 - 20 January 2025
- Made a generic handler for slash command invocations that automatically defers the interaction
- Made Ratings commands hybrid
- Removed a lot of the custom values for Ratings commands
- Changed the `m!iq` command to use `random.gauss(100, 15)` instead of `random.uniform(50, 150)`
- Added a way to create a subgroup inside a slash command

## v2.0.0a9 - 22-24 January 2025
- Made the `m!stars` command hybrid
  - Changed the primary name to `m!starboard`
  - Split the server and user stats into separate subcommands
- Lowered the limit of embeds within one starboard entry to 5 (actual message + 4 more embeds)
- Improved the way attachments, embeds, and stickers are handled in Starboard and message logs
- Forwarded messages in Starboard and deleted message logs now show the forwarded contents
- Improved handling of Starboard reaction clear and message deletion events
  - If all or star emoji reactions are cleared from the message, it is deleted from the database and the starboard channel
  - If a message from the starboard is deleted, it is retained on the starboard, however it is marked as having been deleted

## v2.0.0a10 - 25 Jan - 2 Feb 2025
- Made Utility commands hybrid
- `m!base` will now remove trailing zeros from floating-point conversions
- Split `m!settz` into several subcommands and added autocomplete for country and timezone names
- Improved the outputs of `m!weather`
  - The command now looks up the inputted place name and returns the weather at the first result's lat/long coordinates
  - The autocomplete function returns the places based on the API's geolocation data
- Improved brightness calculation in `m!colour`
- Split the roles list into a `m!role list` subcommand
- Merged `m!user` and `m!whois` into one command, simply having a different level of detail for members vs users
- Added new details to the `m!role`, `m!user`, and `m!server` commands
- `m!role members` and `m!server bots` now have a proper paginator for the outputs
- `m!joinedat` and `m!createdat` now show the user's global name rather than their unique username
- `m!emoji` can now handle emojis that aren't properly available to the bot
- Added a `m!sticker` command
  - The text version allows for a sticker to be attached with the command message
- `m!embed` now requires Manage Messages permission to run
- Split `m!remind` into `m!remind in` and `m!remind on`, thereby making it possible to specify a date and time when to send the reminder
- Moved `m!reminders` to `m!reminders list` to have the same signature on text and slash commands
- Fixed type hint on `interactions.slash_command()` causing issues on commands with more than one argument
- Created `interactions.init_slash_command()` which simply logs and defers the interaction, returning the context