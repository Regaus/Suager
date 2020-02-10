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
            'activity': 676540472839110676}
