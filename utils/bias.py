import json

import discord


# def _friend_bias(bot, member: discord.Member):  # Bias by who you are in Senko Lair
#     result = 1
#     if member.guild.id == 679055998186553344 and member.id == 302851022790066185:
#         result *= 0.33
#     cool = False
#     sl = bot.get_guild(568148147457490954)
#     if member.guild.id != 568148147457490954:  # Senko Lair
#         ms = [m.id for m in sl.members]
#         if member.id in ms:
#            cool = True
#     else:
#         cool = True
#     if cool:
#         member = sl.get_member(member.id)
#         bias = {
#             641423339671257118: 2.5,   # Tier 4 Friend
#             610107382067888138: 2.25,  # Tier 3 Friend
#             671816195564896298: 2,     # Tier 2 Friend
#             641423169454080051: 1.5,   # Tier 1 Friend
#             660880373894610945: 0.2,   # Bowser65
#             673189353014689818: 1.33,  # Nuriki Cult
#             655428243716964352: 0.5,   # Heretics
#             571034792754413598: 0.33,  # Sinners
#             571034926107852801: 0.25,  # Infidels 1
#             646343824775446548: 0.2,   # Infidels 2
#             668108494196441121: 1.25,  # R. P. S. (Secret Room)
#             642563763538755604: 1.2,   # AlexFlipnote's server
#             572535688801812500: 1.2,   # IRL Friends
#             568157600156221460: 1.2,   # Members of Senko Lair - just for the fact you're there
#         }
#         for role in member.roles:
#             result *= bias.get(role.id, 1)
#     for server in bot.guilds:
#         people = [m.id for m in server.members]
#         for person in people:
#             if person == member.id:
#                 result *= 1.1
#                 break
#     asked = {
#         486620915669401600: 1.5,  # Rosey
#         302851022790066185: 0.6,  # Myself - tbh it's too high at this point
#     }
#     result *= asked.get(member.id, 1)
#     return result


servers = {
    568148147457490954: {          # Senko Lair
        641423339671257118: 3,     # Tier 4 Friend
        610107382067888138: 2.5,   # Tier 3 Friend
        671816195564896298: 2,     # Tier 2 Friend
        641423169454080051: 1.5,   # Tier 1 Friend
        660880373894610945: 0.15,  # Bowser65
        673189353014689818: 1.5,   # Nuriki Cult
        655428243716964352: 0.5,   # Heretics
        571034792754413598: 0.3,   # Sinners
        571034926107852801: 0.2,   # Infidels 1
        646343824775446548: 0.15,  # Infidels 2
        668108494196441121: 1.33,  # R. P. S. (Secret Room)
        642563763538755604: 1.25,  # AlexFlipnote's server
        572535688801812500: 1.25,  # IRL Friends
        568157600156221460: 1.25,  # Members of Senko Lair - just for the fact you're there
    },
    679055998186553344: {          # Rosey's Server
        679063210241949736: 1.5,   # Fire Foxes
        679058176620101742: 1.5,   # Moderators
        679058793589374997: 1.25,  # Owner
    },
    430945139142426634: {
        668893445347213322: 1.25,  # Friends
        676147948996001793: 1.25,  # Magic Basement
        430946753097760768: 1.25,  # Owner
    }
}
extra = {
    302851022790066185: 1,  # Myself
}
special = {
    679055998186553344: {  # Rosey's Server
        486620915669401600: 2.5,  # Rosey_Scarlet_Thorns#2608
        302851022790066185: 1,  # Regaus
    }
}


def friend_bias(db, member: discord.Member):
    stuff = db.fetch("SELECT * FROM data WHERE type=? AND id=?", ("roles", member.id))
    result = 1
    if stuff:
        for thing in stuff:
            result *= 1.1
            data = json.loads(thing['data'])
            gid = thing['extra']
            bias = servers.get(gid, {})
            for role in data:
                result *= bias.get(role, 1)
    result *= extra.get(member.id, 1)
    yes = special.get(member.guild.id, {})
    result *= yes.get(member.id, 1)
    return result


def gender_bias(member: discord.Member):  # Bias by gender
    try:
        gender = json.loads(open(f"data/gender/{member.id}.json", "r").read())
        if gender['male']:
            return 1
        elif gender['female']:
            return 0.5
        else:
            return 0.15
    except FileNotFoundError or KeyError or ValueError:
        return 0.4


def so_bias(member: discord.Member):  # Bias by S.O.
    try:
        data = json.loads(open(f"data/orientation/{member.id}.json", "r").read())
        if data['straight']:
            return 1
        elif data['gay_lesbian'] or data['bisexual']:
            return 0.75
        else:
            return 0.2
    except FileNotFoundError or KeyError or ValueError:
        return 0.75


def get_bias(db, user: discord.Member):
    value = friend_bias(db, user) * gender_bias(user) * so_bias(user)
    return value if value < 20 else 20
