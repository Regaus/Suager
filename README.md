# Suager
Suager - a bot by Regaus

## Requirements
- [Python 3.8](https://www.python.org/downloads/)
- discord.py v1.4+
- Pillow

## Setup
1. [Create a bot here](https://discord.com/developers/applications)
2. Copy config_v6_ex.json and name it config_v6.json
3. Copy your bot's token to config_v6.json
4. For the weather command, get a key [here](https://home.openweathermap.org/api_keys)
5. Configure user prefixes and owner-only prefixes, playing statuses, etc.<br>
Note: Statuses have been moved to core.utils.events.playing_changer
6. Run `pip install -r requirements.txt`
7. Start the bot using `python index_v6.py`

If this works, it works. If it doesn't, it doesn't.

To add your bot to your server use [this URL](https://discord.com/oauth2/authorize?client_id=CLIENT_ID&scope=bot) 
with your bot's user ID in place of CLIENT_ID