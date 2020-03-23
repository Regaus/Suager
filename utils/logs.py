import os


def log_channel(bot, log: str = "main"):
    ch = channels.get(log, 673247912746287134)
    return bot.get_channel(ch)


channels = {'main': 673247776234012674,
            'playing': 673247799504011284,
            'senko': 673248425269264545,
            'errors': 673247912746287134,
            'servers': 673249399379460126,
            'uptime': 673255207567622148,
            'changes': 673620954915536906,
            'spyware': 673979546902724648,
            'status': 676540443592359957,
            'activity': 676540472839110676,
            'avatars': 676899389977133072}


error_channel = 691442857537568789


def get_place(version: str, what: str):
    return f"logs/{version}/{what}.rsf"


def create():
    for version in ["stable", "beta", "alpha"]:
        for folder in ["logs", "data"]:
            try:
                os.makedirs(f"{folder}/{version}")
            except FileExistsError:
                pass


def save(file: str, data: str, ow: bool = False):
    p = "w" if ow else "a"
    stuff = open(file, f"{p}+")
    stuff.write(f"{data}\n")  # Add in an extra newline just in case
    stuff.close()
