from core.utils import emotes

template = {
    'prefixes': [],
    'use_default': True,
    'leveling': {
        'enabled': False,
        'xp_multiplier': 1.0,
        'level_up_message': f"[MENTION] is now level **[LEVEL]**! {emotes.ForsenDiscoSnake}",
        'ignored_channels': [],
        'announce_channel': 0,
        'rewards': []
    },
    "currency": "€",
    # "shop_items": [],
    "roles": [],
    "mute_role": 0,
    "starboard": {
        "enabled": False,
        "minimum": 3,
        "channel": 0,
    }
}
