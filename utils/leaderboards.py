from typing import Literal

from discord.ext import commands

from utils import languages, time, paginators


async def leaderboard(self, ctx: commands.Context, query: str, statement: tuple, top: int | Literal["top"], string: str, language: languages.Language, guild: str = None):
    """ Generate server Leaderboard """
    _af = -1 if time.april_fools() else 1
    data = self.bot.db.fetch(query, statement)
    if not data:
        return await ctx.send(language.string("leaderboards_no_data"))
    un = []   # User names
    xp = []   # XP
    xpl = []  # XP string lengths
    for user in data:
        name = f"{user['name']} ({user['disc']})"
        un.append(name)
        val = language.number(user["xp"], precision=0)
        xp.append(val)
        xpl.append(len(val))
    place = language.string("generic_unknown")
    n = 0
    for x in range(len(data)):
        if data[x]['uid'] == ctx.author.id:
            place = language.string("leaderboards_place", val=language.number((x + 1) * _af))
            n = x + 1
            break
    if isinstance(top, int):
        page = top - 1
    elif isinstance(top, str):  # top = "top"
        page = 0
    else:
        page = (n - 1) // 10  # 1st -> Page 1, 10th -> Page 1, 11th -> Page 2
    header = language.string(string, server=guild, place=place, total=language.number(len(xp)))
    paginator = paginators.LinePaginator(prefix=header + "\n```fix", suffix="```", max_lines=10, max_size=1000)
    for i, val in enumerate(data, start=1):
        k = i - 1
        who = un[k]
        if val['uid'] == ctx.author.id:
            who = f"-> {who}"
        current_page = k // 10
        spaces = max(xpl[current_page*10:(current_page + 1)*10])
        pad = len(str((current_page + 1) * 10)) + (_af < 0)  # This later part adds an extra padding point if it's april fools
        # Place -> 2 spaces -> XP (aligned right) -> 4 spaces -> Name
        paginator.add_line(f"{i * _af:0{pad}d})  {xp[k]:>{spaces}}    {who}")
    interface = paginators.PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
    interface.display_page = page  # Set the page to the user's current or chosen page
    return await interface.send_to(ctx)


async def leaderboard2(self, ctx: commands.Context, query: str, statement: tuple, top: int | Literal["top"], string: str, language: languages.Language, guild: str = None):
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
    # block = "```fix\n"
    un, xp, xpl = [], [], []
    for thing in range(r):
        v = sl[thing][1]
        un.append(v[1])
        x = language.number(v[0], precision=0)
        xp.append(x)
        xpl.append(len(x))
    # total = len(xp)
    place = language.string("generic_unknown")
    n = 0
    for someone in range(len(sl)):
        if sl[someone][0] == ctx.author.id:
            place = language.string("leaderboards_place", val=language.number((someone + 1) * _af))
            n = someone + 1
            break
    if isinstance(top, int):
        page = top - 1
    elif isinstance(top, str):  # top = "top"
        page = 0
    else:
        page = (n - 1) // 10  # 1st -> Page 1, 10th -> Page 1, 11th -> Page 2
    header = language.string(string, server=guild, place=place, total=language.number(len(xp)))
    paginator = paginators.LinePaginator(prefix=header + "\n```fix", suffix="```", max_lines=10, max_size=1000)
    for i, val in enumerate(sl, start=1):
        k = i - 1
        who = un[k]
        if val[0] == ctx.author.id:
            who = f"-> {who}"
        current_page = k // 10
        spaces = max(xpl[current_page*10:(current_page + 1)*10])
        pad = len(str((current_page + 1) * 10)) + (_af < 0)  # This later part adds an extra padding point if it's april fools
        # Place -> 2 spaces -> XP (aligned right) -> 4 spaces -> Name
        paginator.add_line(f"{i * _af:0{pad}d})  {xp[k]:>{spaces}}    {who}")
    interface = paginators.PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
    interface.display_page = page  # Set the page to the user's current or chosen page
    return await interface.send_to(ctx)
