version = "alpha"
folder = "alpha"


def setup(bot):
    a = [a for a in bot.users if a.id == -1]
    if a:
        print(a)
