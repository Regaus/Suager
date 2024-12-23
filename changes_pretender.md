# Changelog for Pretender Bot - Changes since Regaus's version

## v0.1.0 - 20 July 2022
- Made the base of the bot built off of original source but using sqlite instead of MongoDB

## v0.1.1 - 20 July 2022
- Update prefix to `a.`

## v1.0.0 - 20 July 2022
- Incorporated the code into the code for all the other bots

## v1.1.0 - 21 July 2022
- Added permission checks for `a.impersonate`
- Reduced cooldowns for `a.count` and `a.impersonate`
- Added more channels for message logging
- Senko Lair's Secret Rooms will have separate message logs for impersonation, while all other channels will have their messages mashed together

## v1.1.1 - 21 July 2022
- Ignore messages starting with `a.` in the logs

## v1.1.2 - 22 July 2022
- Changed the cooldown for `a.impersonate` to 7.5s per user (from 5s per channel)
- Reduced the Markov chain generator's dataset length limit to 50,000 (from 100,000) 
- The generator will now use random entries of the dataset if the overall length exceeds the max limit

## v1.1.2.1 - 3 September 2022
- The database builder now uses the actual type string instead of the number abstraction

## v1.1.2.2 - 20 October 2022
- Updated to Python 3.11
- Improved code for showing versions of libraries used

## v1.2.0 - 27 October 2022
- Message ID is now stored in the database
- The bot can now handle message edits and deletion
- Links will now be removed from message content before getting saved into the database
- Raw message content will now be stored, instead of the "clean content"
- As such, the response will use AllowedMentions set to all False to avoid pinging people in the replies
- Added the bot to Satan's Rib server, currently only using messages from the general chat
- Satan's Rib will also qualify the message content to be separated (i.e. stored with a channel ID saved rather than null)
- Reduced message limit to 10,000 in an attempt to reduce lag on loading the impersonate command
- Added more detail to opt-out command's confirmation message

## v1.2.1 - 9 November 2022
- Added Pretender to a new server
- Added a smarter behaviour for impersonating users who are inactive in separated channels

## v1.2.1.1 - 10 November 2022
- Fixed impersonator breaking in separated channels

## v1.2.1.2 - 15 November 2022
- Database errors will now be logged instead of getting silently ignored

## v1.2.1.3 - 15 November 2022
- Fixed the bot breaking when the message with the impersonate command is deleted before the bot deletes it

## v1.2.1.4 - 11 March 2023
- Created a local copy of Jishaku's reaction-based paginator, since it was removed from the library

## v1.2.1.5 - 19 March 2023
- Added Overheating Brakes, Wobbe's new server

## v1.2.1.6 - 1 April 2023
- Playing statuses are now written in reverse during 1st April

## v1.2.1.7 - 12 May 2023
- Added Huskie's Generous Cabin

## v1.2.1.8 - 23 May 2023
- Added "Mr.Dan Fan Club"

## v1.2.2 - 8 June 2023
- Updated discord.py to a new (alpha) version, so most commands should now behave better with Discord's new username system
- Updated most commands to use display names in the output, where it makes sense to
- The `a.impersonate` command now shows the member's name instead of username (nickname -> display name -> username)

## v1.2.2.1 - 24 September 2023
- Fixed `a.eval` crashing when the error traceback is very long

## v1.2.2.2 - 25 October 2023
- Fixed the `a.optout` command crashing

## v1.2.2.3 - 6 December 2023
- Fixed glitchy custom statuses

## v1.2.3 - 7 December 2023
- Improved the code for choosing a status
- Turned version and countdown statuses into custom status
- Added some new statuses

## v1.3.0 - 26 December 2023
- Separated the Pretender database into a separate file

## v1.3.1 - 5 February 2024
- Added a command to sync slash commands (`a.sync`)
- Made command completion and command error handlers deal with the existence of slash commands
  - Note: Pretender currently has no slash commands

## v1.3.1.1 - 24 May 2024
- Changed the error re-raising statements to not modify error context when they don't need to

## v1.3.1.2 - 8 December 2024
- Error logs will now be forwarded to the #error-logs channel

## v1.4.0a1 - 22 December 2024
- Made Bot Information commands hybrid
  - The `a.invite` command only has a slash equivalent on Suager, as the other bots are private.