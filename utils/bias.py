import json

import discord


def friend_bias(bot, member: discord.Member):  # Bias by who you are in Senko Lair
    if member.guild.id != 568148147457490954:  # Senko Lair
        yes = bot.get_guild(568148147457490954).get_member(member.id)
        if yes is None:
            return 1
        member = yes
    bias = {
        641423339671257118: 3,     # Tier 4 Friend
        610107382067888138: 2.5,   # Tier 3 Friend
        671816195564896298: 2,     # Tier 2 Friend
        641423169454080051: 1.5,   # Tier 1 Friend
        660880373894610945: 0.4,   # Bowser65
        673189353014689818: 1.5,   # Nuriki Cult
        655428243716964352: 0.5,   # Heretics
        571034792754413598: 0.5,   # Sinners
        571034926107852801: 0.33,  # Infidels 1
        646343824775446548: 0.25,  # Infidels 2
        668108494196441121: 1.25,  # R. P. S. (Secret Room)
    }
    result = 1
    for role in member.roles:
        result *= bias.get(role.id, 1)
    return result


def gender_bias(member: discord.Member):  # Bias by gender
    try:
        gender = json.loads(open(f"data/gender/{member.id}.json", "r").read())
        if gender['male']:
            return 1
        elif gender['female']:
            return 0.7
        else:
            return 0.2
    except FileNotFoundError or KeyError or ValueError:
        return 0.5


def sexuality_bias(member: discord.Member):  # Bias by S.O.
    try:
        data = json.loads(open(f"data/orientation/{member.id}.json", "r").read())
        if data['straight']:
            return 1
        elif data['gay_lesbian'] or data['bisexual']:
            return 0.8
        else:
            return 0.3
    except FileNotFoundError or KeyError or ValueError:
        return 0.75
