from discord.ext import commands

from utils import languages, time


async def leaderboard(self, ctx: commands.Context, query: str, statement: tuple, top: str, string: str, language: languages.Language, guild: str = None):
    """ Generate server Leaderboard """
    _af = -1 if time.april_fools() else 1
    data = self.bot.db.fetch(query, statement)
    if not data:
        return await ctx.send(language.string("leaderboards_no_data"))
    block = "```fix\n"
    un = []   # User names
    xp = []   # XP
    xpl = []  # XP string lengths
    for user in data:
        name = f"{user['name']} ({user['disc']})"
        un.append(name)
        val = language.number(user["xp"], precision=0)
        xp.append(val)
        xpl.append(len(val))
    total = len(xp)
    place = language.string("generic_unknown")
    n = 0
    for x in range(len(data)):
        if data[x]['uid'] == ctx.author.id:
            place = language.string("leaderboards_place", val=language.number((x + 1) * _af))
            n = x + 1
            break
    try:
        page = int(top)
        if page < 1:
            page = None
    except ValueError:
        page = None
    start = 0
    try:
        if (n <= 10 or top.lower() == "top") and page is None:
            _data = data[:10]
            start = 1
            spaces = max(xpl[:10])  # + 5
        elif page is not None:
            _data = data[(page - 1)*10:page*10]
            start = page * 10 - 9
            spaces = max(xpl[(page - 1)*10:page*10])  # + 5
        else:
            _data = data[n-5:n+5]
            start = n - 4
            spaces = max(xpl[n-5:n+5])  # + 5
        pad = len(str(start + 9)) + (_af < 0)  # This later part adds an extra padding point if it's april fools
        for i, val in enumerate(_data, start=start):
            k = i - 1
            who = un[k]
            if val['uid'] == ctx.author.id:
                who = f"-> {who}"
            # s = ' '
            # sp = xpl[k]
            # Place -> 4 spaces -> XP (aligned right) -> 4 spaces -> Name
            block += f"{i * _af:0{pad}d})  {xp[k]:>{spaces}}    {who}\n"
    except (ValueError, IndexError):
        block += "No data available"
    s, e, t = language.number(start * _af), language.number((start + 9) * _af), language.number(total)
    block += "```"
    output = language.string(string, server=guild, place=place, start=s, end=e, total=t, data=block)
    return await ctx.send(output)


async def leaderboard2(self, ctx: commands.Context, query: str, statement: tuple, top: str, string: str, language: languages.Language, guild: str = None):
    """ Generate global leaderboard """
    _af = -1 if time.april_fools() else 1
    data = self.bot.db.fetch(query, statement)
    coll = {}
    for i in data:
        if i['uid'] not in coll:
            coll[i['uid']] = [0, f"{i['name']} ({i['disc']})"]
        coll[i['uid']][0] += i["xp"]
    sl = sorted(coll.items(), key=lambda a: a[1][0], reverse=True)
    r = len(sl)
    block = "```fix\n"
    un, xp, xpl = [], [], []
    for thing in range(r):
        v = sl[thing][1]
        un.append(v[1])
        x = language.number(v[0], precision=0)
        xp.append(x)
        xpl.append(len(x))
    total = len(xp)
    place = language.string("generic_unknown")
    n = 0
    for someone in range(len(sl)):
        if sl[someone][0] == ctx.author.id:
            place = language.string("leaderboards_place", val=language.number((someone + 1) * _af))
            n = someone + 1
            break
    try:
        page = int(top)
        if page < 1:
            page = None
    except ValueError:
        page = None
    start = 0
    try:
        if (n <= 10 or top.lower() == "top") and page is None:
            _data = sl[:10]
            start = 1
            spaces = max(xpl[:10])  # + 5
        elif page is not None:
            _data = sl[(page - 1) * 10:page * 10]
            start = page * 10 - 9
            spaces = max(xpl[(page - 1) * 10:page * 10])  # + 5
        else:
            _data = sl[n - 5:n + 5]
            start = n - 4
            spaces = max(xpl[n - 5:n + 5])  # + 5
        pad = len(str(start + 9)) + (_af < 0)  # This later part adds an extra padding point if it's april fools
        for i, d in enumerate(_data, start=start):
            try:
                k = i - 1
                who = un[k]
                if d[0] == ctx.author.id:
                    who = f"-> {who}"
                # s = ' '
                # sp = xpl[k]
                # Place -> 4 spaces -> XP (aligned right) -> 4 spaces -> Name
                block += f"{i * _af:0{pad}d})  {xp[k]:>{spaces}}    {who}\n"
                # block += f"{i:02d}){s * 4}{xp[k]}{s * (spaces - sp)}{who}\n"
            except IndexError:
                pass
    except (ValueError, IndexError):
        block += "No data available"
    s, e, t = language.number(start * _af), language.number((start + 9) * _af), language.number(total)
    block += "```"
    return await ctx.send(language.string(string, server=guild, place=place, start=s, end=e, total=t, data=block))
