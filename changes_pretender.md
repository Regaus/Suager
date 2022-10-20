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
- Reduced the Markov chain generator's dataset length limit to 50,000 (from 10,000) 
- The generator will now use random entries of the dataset if the overall length exceeds the max limit

## v1.1.2.1 - 3 September 2022
- The database builder now uses the actual type string instead of the number abstraction

## v1.1.2.2 - 20 October 2022
- Updated to Python 3.11
- Improved code for showing versions of libraries used