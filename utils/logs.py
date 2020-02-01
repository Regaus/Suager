def log_channel(bot, log: str = "main"):
    ch = 0
    if log == "main":
        ch = 673247776234012674
    elif log == "playing":
        ch = 673247799504011284
    elif log == "senko":
        ch = 673248425269264545
    elif log == "errors":
        ch = 673247912746287134
    elif log == "servers":
        ch = 673249399379460126
    elif log == "uptime":
        ch = 673255207567622148
    return bot.get_channel(ch)
