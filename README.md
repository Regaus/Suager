# Suager
A bot by Regaus

## Requirements
- [Python 3.9+](https://www.python.org/downloads/)
- discord.py v1.7+
- Pillow

## Setup
1. [Create a bot here](https://discord.com/developers/applications)
2. Copy config_ex.json and rename it to config.json
3. Configure your bot: set your bot's token in config.json, change any other required settings
4. For the weather command, get a key [here](https://home.openweathermap.org/api_keys)
5. Configure user prefixes and owner-only prefixes, playing statuses, etc<br>
Note: Statuses have been moved to utils.temporaries.playing_changer
6. Run `pip install -r requirements.txt`
7. Start the bot with `python index.py`

If this works, it works. If it doesn't, it doesn't.

To add your bot to your server use [this URL](https://discord.com/oauth2/authorize?client_id=CLIENT_ID&scope=bot) 
with your bot's user ID in place of CLIENT_ID