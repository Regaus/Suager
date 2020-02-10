import discord


def friend_bias(bot, member: discord.Member):
    if member.guild.id != 568148147457490954:  # Senko Lair
        yes = bot.get_guild(568148147457490954).get_member(member.id)
        if yes is None:
            return 1
        member = yes
    bias = {
        610107382067888138: 2.5,
        671816195564896298: 2,
        641423169454080051: 1.5,
        655428243716964352: 0.5
    }
    result = 1
    for role in member.roles:
        result *= bias.get(role.id, 1)
    return result
