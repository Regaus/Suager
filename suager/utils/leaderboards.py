from discord.ext import commands

from core.utils import general, time
from languages import langs


_year = time.now(None).year


async def leaderboard(self, ctx: commands.Context, query: str, statement: tuple, top: str, string: str, locale, key: str, guild: str = None):
    """ Generate Leaderboard """
    data = self.bot.db.fetch(query, statement)
    if not data:
        if key.isnumeric():
            return await general.send(langs.gls("leveling_rank_yearly_no", locale, key), ctx.channel)
        return await general.send(langs.gls("leaderboards_no_data", locale), ctx.channel)
    block = "```fix\n"
    un = []   # User names
    xp = []   # XP
    xpl = []  # XP string lengths
    try:
        for user in data:
            name = f"{user['name']}#{user['disc']:04d}"
            un.append(name)
            val = langs.gns(int(user[key]), locale)
            xp.append(val)
            xpl.append(len(val))
    except KeyError:
        return await general.send(langs.gls("leveling_rank_yearly_no", locale, key), ctx.channel)
    total = len(xp)
    place = langs.gls("generic_unknown", locale)
    n = 0
    for x in range(len(data)):
        if data[x]['uid'] == ctx.author.id:
            place = langs.gls("leaderboards_place", locale, langs.gns(x + 1, locale, 0, False))
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
            spaces = max(xpl[:10]) + 5
        elif page is not None:
            _data = data[(page - 1)*10:page*10]
            start = page * 10 - 9
            spaces = max(xpl[(page - 1)*10:page*10]) + 5
        else:
            _data = data[n-5:n+5]
            start = n - 4
            spaces = max(xpl[n-5:n+5]) + 5
        for i, val in enumerate(_data, start=start):
            k = i - 1
            who = un[k]
            if val['uid'] == ctx.author.id:
                who = f"-> {who}"
            s = ' '
            sp = xpl[k]
            block += f"{langs.gns(i, locale, 2, False)}){s*4}{xp[k]}{s*(spaces-sp)}{who}\n"
    except (ValueError, IndexError):
        block += "No data available"
    s, e, t = langs.gns(start, locale), langs.gns(start + 9, locale), langs.gns(total, locale)
    args = [guild] if guild else []
    args += [place, s, e, t, block]
    if key.isnumeric():
        args.append(key)
    output = langs.gls(string, locale, *args)
    if int(key) == 2021:
        cobble_servers = [568148147457490954, 738425418637639775, 58221533031156941, 662845241207947264]
        if ctx.guild.id not in cobble_servers:
            output += langs.gls("leveling_rank_yearly21", locale, ctx.guild.name)
    return await general.send(output, ctx.channel)


async def leaderboard2(self, ctx: commands.Context, query: str, statement: tuple, top: str, string: str, locale, key: str, guild: str = None):
    data = self.bot.db.fetch(query, statement)
    coll = {}
    for i in data:
        if i['uid'] not in coll:
            coll[i['uid']] = [0, f"{i['name']}#{i['disc']:04d}"]
        coll[i['uid']][0] += i[key]
    sl = sorted(coll.items(), key=lambda a: a[1][0], reverse=True)
    r = len(sl)
    block = "```fix\n"
    un, xp, xpl = [], [], []
    for thing in range(r):
        v = sl[thing][1]
        un.append(v[1])
        x = langs.gns(int(v[0]), locale)
        xp.append(x)
        xpl.append(len(x))
    total = len(xp)
    place = langs.gls("generic_unknown", locale)
    n = 0
    for someone in range(len(sl)):
        if sl[someone][0] == ctx.author.id:
            place = langs.gls("leaderboards_place", locale, langs.gns(someone + 1, locale, 0, False))
            n = someone + 1
            break
    s = ' '
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
            spaces = max(xpl[:10]) + 5
        elif page is not None:
            _data = sl[(page - 1) * 10:page * 10]
            start = page * 10 - 9
            spaces = max(xpl[(page - 1) * 10:page * 10]) + 5
        else:
            _data = sl[n - 5:n + 5]
            start = n - 4
            spaces = max(xpl[n - 5:n + 5]) + 5
        for i, d in enumerate(_data, start=start):
            try:
                k = i - 1
                who = un[k]
                if d[0] == ctx.author.id:
                    who = f"-> {who}"
                sp = xpl[k]
                block += f"{langs.gns(i, locale, 2, False)}){s * 4}{xp[k]}{s * (spaces - sp)}{who}\n"
            except IndexError:
                pass
    except (ValueError, IndexError):
        block += "No data available"
    s, e, t = langs.gns(start, locale), langs.gns(start + 9, locale), langs.gns(total, locale)
    args = [guild] if guild else []
    args += [place, s, e, t, block]
    return await general.send(langs.gls(string, locale, *args), ctx.channel)
