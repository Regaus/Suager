from utils import emotes


template_cobble = {
    "prefixes": [],
    "use_default": True
}


template_mizuki = {
    "prefixes": [],
    "use_default": True,
    "mute_role": 0,
    "starboard": {
        "enabled": False,
        "minimum": 3,
        "channel": 0
    },
    "birthdays": {
        "enabled": False,
        "role": 0,
        "channel": 0,
        "message": "Happy birthday [MENTION], have a nice one! 🎂🎉"
    },
    "join_roles": {
        "members": [],
        "bots": []
    },
    "welcome": {
        "channel": 0,
        "message": "Welcome [MENTION] to [SERVER]!"
    },
    "goodbye": {
        "channel": 0,
        "message": "[USER] has left [SERVER]..."
    },
    "mod_logs": {  # Note: These will only work if the user is warned/muted/kicked/banned using the bot.
        "warnings": 0,
        "mutes": 0,
        "kicks": 0,
        "bans": 0,
        "roles": 0  # Log when the user gets or loses a new role - Try to fetch data from audit logs, just show who got what role if audit logs are not available
    },
    "mod_dms": {
        "warnings": 0,
        "mutes": 0,
        "kicks": 0,
        "bans": 0
    },
    "user_logs": {
        "join": 0,   # Channel ID where users who join are logged (Username, ID, created at, joined at)
        "leave": 0,  # Channel ID where users who leave are logged (Username, ID, created at, joined at, roles they had) -- Time of leaving as footer timestamp
        "preserve_roles": False  # Save a list of the user's role when they leave the server, so it can be recovered when they come back
    },
    "message_logs": {
        "edit": 0,
        "delete": 0,
        "enabled": False,
        "ignore_bots": True,    # Ignore edited/deleted messages if they're sent by a bot
        "ignore_channels": []  # List of channels in which edited/deleted messages are ignored
    }
}

template_suager = {
    "prefixes": [],
    "use_default": True,
    "leveling": {
        "enabled": False,
        "xp_multiplier": 1.0,
        "level_up_message": f"[MENTION] is now level **[LEVEL]**! {emotes.ForsenDiscoSnake}",  # General level up message
        "level_up_role": None,     # Level up message for when you reach a new level reward
        "level_up_highest": None,  # Level up message for when you reach the highest level reward
        "level_up_max": None,      # Level up message for level 200
        "ignored_channels": [],
        "announce_channel": 0,
        "rewards": []
    },
    "mute_role": 0,
    "starboard": {
        "enabled": False,
        "minimum": 3,
        "channel": 0
    },
    "birthdays": {
        "enabled": False,
        "role": 0,
        "channel": 0,
        "message": "Happy birthday [MENTION], have a nice one! 🎂🎉"
    },
    "polls": {
        "channel": 0,
        "voter_anonymity": True
    },
    "join_roles": {
        "members": [],
        "bots": []
    },
    "welcome": {
        "channel": 0,
        "message": "Welcome [MENTION] to [SERVER]!"
    },
    "goodbye": {
        "channel": 0,
        "message": "[USER] has left [SERVER]..."
    },
    "mod_logs": {  # Note: These will only work if the user is warned/muted/kicked/banned using the bot.
        "warnings": 0,
        "mutes": 0,
        "kicks": 0,
        "bans": 0,
        "roles": 0  # Log when the user gets or loses a new role - Try to fetch data from audit logs, just show who got what role if audit logs are not available
    },
    "mod_dms": {
        "warnings": 0,
        "mutes": 0,
        "kicks": 0,
        "bans": 0
    },
    "user_logs": {
        "join": 0,   # Channel ID where users who join are logged (Username, ID, created at, joined at)
        "leave": 0,  # Channel ID where users who leave are logged (Username, ID, created at, joined at, roles they had) -- Time of leaving as footer timestamp
        "preserve_roles": False  # Save a list of the user's role when they leave the server, so it can be recovered when they come back
    },
    "message_logs": {
        "edit": 0,
        "delete": 0,
        "enabled": False,
        "ignore_bots": True,    # Ignore edited/deleted messages if they're sent by a bot
        "ignore_channels": []  # List of channels in which edited/deleted messages are ignored
    }
}
