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
    }
}
