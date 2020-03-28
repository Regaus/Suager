version = "alpha"
folder = "alpha"
prefix_template = {'prefixes': [], 'default': True}
settings_template = {
    'prefixes': [],
    'use_default': True,
    'leveling': {
        'enabled': True,
        'xp_multiplier': 1.0,
        'level_up_message': "[MENTION] is now level **[LEVEL]**! <a:forsendiscosnake:613403121686937601>",
        'ignored_channels': [],
        'announce_channel': 0,
        'rewards': [
            {'level': 5001, 'role': 0},
            {'level': 5002, 'role': 0}
        ]
    },
    "muted_role": 0,
    "warn_limit": 3,
    "word_filter": [],
}


def setup(bot):
    a = [a for a in bot.users if a.id == -1]
    if a:
        print(a)
