import json
import random
from io import BytesIO

import discord
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from discord.ext import commands

from core.utils import time, database, http, general, emotes
from languages import langs
from suager.utils import settings

max_level = 1000
xp_amounts = [2250, 3000]
money_amounts = [75, 125]


async def catch_colour(ctx: commands.Context, c: int):
    if c == -1:
        await general.send("Value must be either 3 or 6 digits long", ctx.channel)
    if c == -2:
        await general.send("An error occurred. Are you sure the value is HEX (0-9 and A-F)?", ctx.channel)
    # if c == -3:
    #     await general.send("Remove the `#`...", ctx.channel)
    return c >= 0


def get_colour(colour: int):
    a = 256
    r, g = divmod(colour, a ** 2)
    g, b = divmod(g, a)
    return r, g, b


def int_colour(colour: str):
    try:
        if colour[0] == "#":
            colour = colour[1:]
        length = len(colour)
        if length == 3:
            a, b, c = colour
            colour = f"{a}{a}{b}{b}{c}{c}"
        elif length != 6:
            return -1
        return int(colour, base=16)
    except ValueError:
        return -2


def _old_levels():
    req = 0
    xp = []
    # mult = multiplier ** 0.001 if multiplier >= 1 else multiplier ** 0.75
    for x in range(max_level):
        base = 1.25 * x ** 3 + 50 * x ** 2 + 15000 * x + 15000
        req += int(base)
        if x not in [69, 420, 666, 1337]:
            xp.append(int(req))
        else:
            xp.append(xp[-1])
    return xp


def _levels():
    req = 15000
    xp = []
    # mult = multiplier ** 0.001 if multiplier >= 1 else multiplier ** 0.75
    for x in range(max_level):
        # power = 2 + x / 40 if x < 40 else 3 + (x - 40) / 80 if x < 80 else 3.5
        power = 2 + x / 40 if x < 70 else 3.75 - (x - 70) / 200 if x < 220 else 3
        base = x ** power + 125 * x ** (1 + x / 5 if x < 5 else 2) + 7500 * x
        req += int(base)
        if x not in [69, 420, 666, 1337]:
            xp.append(int(req))
        else:
            xp.append(xp[-1])
    return xp


# def _levels_global():
#     req = 15000
#     xp = []
#     for x in range(max_level):
#         base = 125 * x ** 3 + 500 * x ** 2 + 15000 * x
#         req += int(base)
#         if x not in [69, 420, 666, 1337]:
#             xp.append(int(req))
#         else:
#             xp.append(xp[-1])
#     return xp


old_levels = _old_levels()
levels = _levels()
# levels_global = _levels_global()


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database(self.bot.name)

    @commands.command(name="leveling")
    @commands.is_owner()
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def leveling_data(self, ctx: commands.Context):
        """ Levels data """
        __levels = [1, 2, 3, 5, 10, 20, 30, 40, 50, 60, 80, 100, 150, 200, 250, 300, 400, 500, 600, 700, 800, 900, 1000]
        outputs = []
        for level in __levels:
            _level = level - 1
            # lv1, lv2, lv3 = int(levels[_level] / 100), int(old_levels[_level] / 100), int(levels_global[_level] / 100)
            # outputs.append(f"Level {level:>4} | New {lv1:>13,} | Old {lv2:>13,} | Global {lv3:>15,}")
            lv1, lv2 = int(levels[_level] / 100), int(old_levels[_level] / 100)
            outputs.append(f"Level {level:>4} | New {lv1:>13,} | Old {lv2:>13,}")
        output = "\n".join(outputs)
        return await general.send(f"```fix\n{output}```", ctx.channel)

    @commands.Cog.listener()
    async def on_message(self, ctx: discord.Message):
        if ctx.author.bot or ctx.guild is None:
            return
        if ctx.content == "" and ctx.type != discord.MessageType.default:
            return
        _settings = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        xp_disabled = False
        if _settings:
            __settings = json.loads(_settings['data'])
            try:
                if not __settings['leveling']['enabled']:
                    xp_disabled = True
                ic = __settings['leveling']['ignored_channels']
                if ctx.channel.id in ic:
                    return
            except KeyError:
                pass
        else:
            __settings = settings.template.copy()
            xp_disabled = True
        data = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if data:
            level, xp, last, ls = [data['level'], data['xp'], data['last'], data['last_sent']]
        else:
            level, xp, last, ls = [0, 0, 0, 0]
        data2 = self.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if data2:
            money = data2["money"]
        else:
            money = 0
        if ls is None:
            ls = 0
        now = time.now_ts()
        td = now - last
        _td = now - ls
        if td < 5:
            mult = 0
        elif 5 <= td < 60:
            mult = (td - 5) / 55
        else:
            mult = 1
        dc = mult == 0  # didn't count
        x1, x2 = xp_amounts
        x3, x4 = money_amounts
        try:
            sm = float(__settings['leveling']['xp_multiplier'])
        except KeyError:
            sm = 1
        c = 0.67 if ctx.author.id == 667187968145883146 else 1
        new = int(random.uniform(x1, x2) * sm * mult * c)
        new_money = int(random.uniform(x3, x4) * mult * c)
        if ctx.author.id == 592345932062916619:
            new = 0
        if not xp_disabled:
            xp += new
        money += new_money
        if not xp_disabled:
            lu, ld = False, False
            if level >= 0:
                while level < max_level and xp >= levels[level]:
                    level += 1
                    lu = True
                while level > 0 and xp < levels[level - 1]:
                    level -= 1
                    ld = True
                if level == 0 and xp < 0:
                    level = -1
                    ld = True
            elif level == -1:
                if xp >= 0:
                    level = 0
                    lu = True
                if xp < -levels[0]:
                    level -= 1
                    ld = True
            else:
                while -max_level <= level < -1 and xp >= -levels[(-level) - 2]:
                    level += 1
                    lu = True
                while level >= -max_level and xp < -levels[(-level) - 1]:
                    level -= 1
                    ld = True
            if lu:
                try:
                    send = str(__settings['leveling']['level_up_message']).replace('[MENTION]', ctx.author.mention)\
                        .replace('[USER]', ctx.author.name).replace('[LEVEL]', langs.gns(level, langs.gl(ctx.guild, self.db)))
                except KeyError:
                    send = f"{ctx.author.mention} has reached **level {level:,}**! {emotes.ForsenDiscoSnake}"
                try:
                    ac = __settings['leveling']['announce_channel']
                    if ac != 0:
                        ch = self.bot.get_channel(ac)
                        if ch is None or ch.guild.id != ctx.guild.id:
                            ch = ctx.channel
                    else:
                        ch = ctx.channel
                except KeyError:
                    ch = ctx.channel
                try:
                    await general.send(send, ch, u=[ctx.author])
                except discord.Forbidden:
                    pass  # Well, if it can't send it there, too bad.
            if ld:
                send = f"{ctx.author.mention} is now **level {level:,}** {emotes.UmmOK}"
                try:
                    ac = __settings['leveling']['announce_channel']
                    if ac != 0:
                        ch = self.bot.get_channel(ac)
                        if ch is None or ch.guild.id != ctx.guild.id:
                            ch = ctx.channel
                    else:
                        ch = ctx.channel
                except KeyError:
                    ch = ctx.channel
                try:
                    await general.send(send, ch, u=[ctx.author])
                except discord.Forbidden:
                    pass
            reason = f"Level Rewards - Level {level}"
            try:
                rewards = __settings['leveling']['rewards']
                if rewards:  # Don't bother if they're empty
                    l1, l2 = [], []
                    rewards.sort(key=lambda x: x['level'])
                    for i in range(len(rewards)):
                        l1.append(rewards[i]['level'])
                        l2.append(rewards[i]['role'])
                    roles = [r.id for r in ctx.author.roles]
                    for i in range(len(rewards)):
                        role = discord.Object(id=l2[i])
                        has_role = l2[i] in roles
                        if level >= l1[i]:
                            if i < len(rewards) - 1:
                                if level < l1[i + 1]:
                                    if not has_role:
                                        await ctx.author.add_roles(role, reason=reason)
                                else:
                                    if has_role:
                                        await ctx.author.remove_roles(role, reason=reason)
                            else:
                                if not has_role:
                                    await ctx.author.add_roles(role, reason=reason)
                        else:
                            if has_role:
                                await ctx.author.remove_roles(role, reason=reason)
            except KeyError:
                pass  # If no level rewards, don't even bother
            except discord.Forbidden:
                await general.send(f"{ctx.author.name} should receive a level reward right now, but I don't have permissions required to give it.", ctx.channel)
            except Exception as e:
                print(f"{time.time()} > Levels on_message > {type(e).__name__}: {e}")
        _last = last if dc else now
        if data:
            self.db.execute("UPDATE leveling SET level=?, xp=?, last=?, last_sent=?, name=?, disc=? WHERE uid=? AND gid=?",
                            (level, xp, _last, now, ctx.author.name, ctx.author.discriminator, ctx.author.id, ctx.guild.id))
        else:
            self.db.execute("INSERT INTO leveling VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (ctx.author.id, ctx.guild.id, level, xp, now, now, ctx.author.name, ctx.author.discriminator))
        if data2:
            self.db.execute("UPDATE economy SET money=?, last=?, name=?, disc=? WHERE uid=? AND gid=?",
                            (money, now, ctx.author.name, ctx.author.discriminator, ctx.author.id, ctx.guild.id))
        else:
            self.db.execute("INSERT INTO economy VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (ctx.author.id, ctx.guild.id, money, now, 0, ctx.author.name, ctx.author.discriminator))

    @commands.command(name="rewards")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=15, type=commands.BucketType.user)
    async def rewards(self, ctx: commands.Context):
        """ Rewards """
        locale = langs.gl(ctx.guild, self.db)
        _settings = self.db.fetchrow("SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not _settings:
            return await general.send(langs.gls("leveling_rewards_none", locale), ctx.channel)
            # return await general.send("This server seems to have no leveling rewards", ctx.channel)
        else:
            data = json.loads(_settings['data'])
        try:
            rewards = data['leveling']['rewards']
            rewards.sort(key=lambda x: x['level'])
            embed = discord.Embed(colour=general.random_colour())
            embed.set_thumbnail(url=ctx.guild.icon_url)
            # embed.title = f"Rewards for having no life in **{ctx.guild.name}**"
            embed.title = langs.gls("leveling_rewards_title", locale, ctx.guild.name)
            d = ''
            for role in rewards:
                d += langs.gls("leveling_rewards_role", locale, langs.gns(role["level"], locale), role["role"])
                # d += f"Level {role['level']:,}: <@&{role['role']}>\n"
            embed.description = d
            return await general.send(None, ctx.channel, embed=embed)
        except KeyError:
            return await general.send(langs.gls("leveling_rewards_none", locale), ctx.channel)
            # return await general.send("This server seems to have no leveling rewards", ctx.channel)

    @commands.command(name="rank", aliases=["irank", "ranki", "level"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=15, type=commands.BucketType.user)
    async def rank_image(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Check your or someone's rank """
        locale = langs.gl(ctx.guild, self.db)
        async with ctx.typing():
            user = who or ctx.author
            is_self = user.id == self.bot.user.id
            if user.bot and not is_self:
                return await general.send(langs.gls("leveling_rank_bot", locale), ctx.channel)
                # return await general.send("I don't count bots' XP because they're cheaters", ctx.channel)
            data = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
            custom = self.db.fetchrow("SELECT * FROM custom_rank WHERE uid=?", (user.id,))
            if custom:
                font_colour, progress_colour, background_colour = \
                    get_colour(custom["font"]), get_colour(custom["progress"]), get_colour(custom["background"])
            else:
                font_colour, progress_colour, background_colour = (50, 255, 50), (50, 255, 50), 0
            if data:
                level, xp = [data['level'], data['xp']]
            else:
                level, xp = [0, 0]
            width = 2048
            img = Image.new("RGB", (width, 612), color=background_colour)
            dr = ImageDraw.Draw(img)
            try:
                avatar = BytesIO(await http.get(str(user.avatar_url_as(size=512, format="png")), res_method="read"))
                avatar_img = Image.open(avatar)
                avatar_resized = avatar_img.resize((512, 512))
                img.paste(avatar_resized)
            except UnidentifiedImageError:  # Failed to get image
                avatar = Image.open("assets/error.png")
                img.paste(avatar)
            font_dir = "assets/font.ttf"
            font = ImageFont.truetype(font_dir, size=108)
            font_small = ImageFont.truetype(font_dir, size=64)
            text_x = 552
            dr.text((text_x, 20), f"{user}", font=font, fill=font_colour)
            try:
                if level >= 0:
                    req = int(levels[level])  # Requirement to next level
                elif level == -1:
                    req = 0
                else:
                    req = int(-levels[(-level) - 2])
                # r2 = f"{req / 100:,.0f}"
                r2 = langs.gns(int(req / 100), locale)
            except IndexError:
                req = float("inf")
                r2 = langs.gls("generic_max", locale)
            try:
                if level > 0:
                    prev = int(levels[level-1])
                elif level == 0:
                    prev = 0
                else:
                    prev = -int(levels[(-level) - 1])
            except IndexError:
                prev = 0
            _data = self.db.fetch("SELECT * FROM leveling WHERE gid=? AND xp!=0 AND disc!=0 ORDER BY xp DESC", (ctx.guild.id,))
            # place = "Rank Undefined"
            place = langs.gls("leveling_rank_rank", locale, langs.gls("generic_unknown", locale))
            for x in range(len(_data)):
                if _data[x]['uid'] == user.id:
                    # place = f"Rank #{x+1:,}"
                    place = langs.gls("leveling_rank_rank", locale, langs.gls("leaderboards_place", locale, langs.gns(x + 1, locale)))
                    break
            old_level = 0
            for lvl in old_levels:
                if xp >= lvl:
                    old_level += 1
                else:
                    break
            if not is_self:
                progress = (xp - prev) / (req - prev)
                _level = langs.gls("leveling_rank_level", locale, langs.gns(level, locale))
                _old_level = langs.gls("leveling_rank_level_old", locale, langs.gns(old_level, locale))
                dr.text((text_x, 140), f"{place} | {_level} | {_old_level}", font=font_small, fill=font_colour)
                # dr.text((text_x, 190), ), font=font_small, fill=font_colour)
                # dr.text((text_x, 250), ), font=font_small, fill=font_colour)
                # dr.text((552, 300), f"{xp / 100:,.0f}/{r2} XP\nProgress: {progress*100:.2f}%", font=font_small, fill=font_colour)
                r1 = langs.gns(int(xp / 100), locale)
                r3 = langs.gfs(progress, locale, 2, True)
                r4 = langs.gls("leveling_rank_xp_left", locale, langs.gns((req - xp) / 100, locale)) if level < max_level else ""
                dr.text((text_x, (308 if r4 else 372)), langs.gls("leveling_rank_xp", locale, r1, r2, r3, r4), font=font_small, fill=font_colour)
            else:
                progress = 0.5
                place = langs.gls("leaderboards_place", locale, langs.gns(1, locale))
                _rank = langs.gls("leveling_rank_rank", locale, place)
                _level = langs.gls("leveling_rank_level", locale, langs.gns(69420, locale))
                dr.text((text_x, 140), f"{_rank} | {_level}", font=font_small, fill=font_colour)
                # dr.text((text_x, 190), , font=font_small, fill=font_colour)
                dr.text((text_x, 436), langs.gls("leveling_rank_xp_self", locale), font=font_small, fill=font_colour)
            full = width
            done = int(progress * full)
            if done < 0:
                done = 0
            i1 = Image.new("RGB", (done, 90), color=progress_colour)
            i2 = Image.new("RGB", (width, 90), color=(30, 30, 30))
            box1 = (0, 522, done, 612)
            box2 = (0, 522, full, 612)  # 2 px bigger
            img.paste(i2, box2)
            img.paste(i1, box1)
            bio = BytesIO()
            img.save(bio, "PNG")
            bio.seek(0)
            r = langs.gls("leveling_rank", locale, user, ctx.guild.name)
            # r = f"**{user}**'s rank in **{ctx.guild.name}**"
            # if is_self:
            #     r += "That's my own rank, so why should I play fair?"
            return await general.send(r, ctx.channel, file=discord.File(bio, filename="rank.png"))

    @commands.command(name="rankg")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=15, type=commands.BucketType.user)
    async def rank_global(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check your or someone's rank """
        locale = langs.gl(ctx.guild, self.db)
        user = who or ctx.author
        is_self = user.id == self.bot.user.id
        if user.bot and not is_self:
            return await general.send(langs.gls("leveling_rank_bot", locale), ctx.channel)
            # return await general.send("I don't count bots' XP because they're cheaters", ctx.channel)
        _data = self.db.fetch("SELECT * FROM leveling WHERE xp!=0 AND disc!=0")
        coll = {}
        for i in _data:
            if i['uid'] not in coll:
                coll[i['uid']] = [0, f"{i['name']}#{i['disc']:04d}"]
            coll[i['uid']][0] += i['xp']
        sl = sorted(coll.items(), key=lambda a: a[1][0], reverse=True)
        r = len(sl)
        xp = []
        for thing in range(r):
            v = sl[thing][1]
            xp.append(v[0])
        place = langs.gls("generic_unknown", locale)
        _xp = 0
        for someone in range(len(sl)):
            if sl[someone][0] == user.id:
                place = langs.gls("leaderboards_place", locale, langs.gns(someone + 1, locale))
                _xp = xp[someone]
                break
        level = 0
        for lvl in levels:
            if _xp >= lvl:
                level += 1
            else:
                break
        __xp = int(_xp / 100)
        return await general.send(langs.gls("leveling_rank_global", locale, user, langs.gns(__xp, locale), place, langs.gns(level, locale)), ctx.channel)
        # return await general.send(f"**{user}** has **{_xp / 100:,.0f} global XP** and is **{place}** on the leaderboard\nGlobal Level: {level:,}", ctx.channel

    @commands.group(name="crank", aliases=["customrank"])
    @commands.cooldown(rate=1, per=15, type=commands.BucketType.user)
    async def custom_rank(self, ctx: commands.Context):
        """ Customise your rank """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @custom_rank.command(name="font")
    async def crank_font(self, ctx: commands.Context, colour: str):
        """ Font colour """
        c = int_colour(colour)
        cc = await catch_colour(ctx, c)
        if cc:
            data = self.db.fetchrow("SELECT * FROM custom_rank WHERE uid=?", (ctx.author.id,))
            if data:
                self.db.execute("UPDATE custom_rank SET font=? WHERE uid=?", (c, ctx.author.id))
            else:
                self.db.execute("INSERT INTO custom_rank VALUES (?, ?, ?, ?)", (ctx.author.id, c, 0x32ff32, 0))
            return await general.send(f"Set your font colour to #{colour}", ctx.channel)

    @custom_rank.command(name="progress")
    async def crank_progress(self, ctx: commands.Context, colour: str):
        """ Progress bar colour """
        c = int_colour(colour)
        cc = await catch_colour(ctx, c)
        if cc:
            data = self.db.fetchrow("SELECT * FROM custom_rank WHERE uid=?", (ctx.author.id,))
            if data:
                self.db.execute("UPDATE custom_rank SET progress=? WHERE uid=?", (c, ctx.author.id))
            else:
                self.db.execute("INSERT INTO custom_rank VALUES (?, ?, ?, ?)", (ctx.author.id, 0x32ff32, c, 0))
            return await general.send(f"Set your progress bar colour to #{colour}", ctx.channel)

    @custom_rank.command(name="background", aliases=["bg"])
    async def crank_bg(self, ctx: commands.Context, colour: str):
        """ Background colour """
        c = int_colour(colour)
        cc = await catch_colour(ctx, c)
        if cc:
            data = self.db.fetchrow("SELECT * FROM custom_rank WHERE uid=?", (ctx.author.id,))
            if data:
                self.db.execute("UPDATE custom_rank SET background=? WHERE uid=?", (c, ctx.author.id))
            else:
                self.db.execute("INSERT INTO custom_rank VALUES (?, ?, ?, ?)", (ctx.author.id, 0x32ff32, 0x32ff32, c))
            return await general.send(f"Set your background colour to #{colour}", ctx.channel)

    @commands.command(name="xplevel")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def xp_level(self, ctx: commands.Context, level: int):
        """ XP required to achieve a level """
        locale = langs.gl(ctx.guild, self.db)
        if level > max_level or level < max_level * -1 + 1:
            return await general.send(langs.gls("leveling_xplevel_max", locale, langs.gns(max_level, locale)), ctx.channel)
            # return await general.send(f"The max level is {max_level:,}", ctx.channel)
        try:
            if level > 0:
                r = int(levels[level - 1])
            elif level == 0:
                r = 0
            else:
                r = -int(levels[(-level) - 1])
        except IndexError:
            return await general.send(langs.gls("leveling_xplevel_max", locale, langs.gns(max_level, locale)), ctx.channel)
            # return await general.send(f"An error can occurred - make sure the level specified is below the max level ({max_level:,}).", ctx.channel)
        if ctx.guild is not None:
            data = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        else:
            data = None
        if not data:
            xp = float("inf")
        else:
            xp = data['xp']
        _settings = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not _settings:
            dm = 1
        else:
            __settings = json.loads(_settings['data'])
            try:
                dm = __settings['leveling']['xp_multiplier']
            except KeyError:
                dm = 1
        # needed = f"{r / 100:,.0f}"
        # base = f"You need **{needed} XP** to reach **level {level:,}**"
        base = langs.gls("leveling_xplevel_main", locale, langs.gns(int(r / 100), locale), langs.gns(level, locale))
        extra = ""
        if xp < r:
            x1, x2 = [val * dm for val in xp_amounts]
            a1, a2 = [(r - xp) / x2, (r - xp) / x1]
            try:
                # t1, t2 = [time.timedelta(x * 60) for x in [a1, a2]]
                t1, t2 = [langs.td_int(x * 60, locale) for x in [a1, a2]]
            except (OverflowError, OSError):
                error = "Never"
                t1, t2 = [error, error]
            extra = langs.gls("leveling_xplevel_extra", locale, langs.gns(int((r - xp) / 100), locale), t1, t2)
            # extra = f"\nXP left: **{(r - xp) / 100:,.0f}**\nEst. time: **{t1} to {t2}**"
        return await general.send(f"{base}{extra}", ctx.channel)

    @commands.command(name="nextlevel", aliases=["nl"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def next_level(self, ctx: commands.Context):
        """ XP required for next level """
        locale = langs.gl(ctx.guild, self.db)
        data = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not data:
            return await general.send(langs.gls("leveling_next_level_none", locale), ctx.channel)
            # return await general.send("I have no leveling data for you right now...", ctx.channel)
        _settings = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not _settings:
            dm = 1
        else:
            __settings = json.loads(_settings['data'])
            try:
                dm = __settings['leveling']['xp_multiplier']
            except KeyError:
                dm = 1
        level, xp = [data['level'], data['xp']]
        if level == max_level:
            return await general.send(langs.gls("leveling_next_level_max", locale, ctx.author.name), ctx.channel)
            # return await general.send(f"**{ctx.author.name}**, you have already reached the max level. There is nowhere higher for you to go.", ctx.channel)
        # r1 = f"{int(xp / 100):,}"
        r1 = langs.gns(int(xp / 100), locale)
        try:
            if level >= 0:
                r = int(levels[level])  # Requirement to next level
            elif level == -1:
                r = 0
            else:
                r = int(-levels[(-level) - 2])
        except IndexError:
            r = float("inf")
        try:
            if level > 0:
                p = int(levels[level-1])
            elif level == 0:
                p = 0
            else:
                p = -int(levels[(-level) - 1])
        except IndexError:
            p = 0
        req = r - xp
        pr = (xp - p) / (r - p)
        r2, r3, r4 = langs.gns(r / 100, locale), langs.gns(req / 100, locale), langs.gfs(pr if pr < 1 else 1, locale, 1, True)
        r5 = langs.gns(level, locale)
        # r2 = f"{int(r / 100):,}"
        # r3 = f"{int(req / 100):,}"
        normal = 1
        x1, x2 = [val * normal * dm for val in xp_amounts]
        a1, a2 = [(r - xp) / x2, (r - xp) / x1]
        try:
            # t1, t2 = [time.timedelta(x * 60) for x in [a1, a2]]
            t1, t2 = [langs.td_int(x * 60, locale) for x in [a1, a2]]
        except (OverflowError, OSError):
            error = "Never"
            t1, t2 = [error, error]
        return await general.send(langs.gls("leveling_next_level", locale, ctx.author.name, r1, r2, r3, r5, r4, t1, t2), ctx.channel)
        # return await general.send(f"**{ctx.author.name}** - You have **{r1}/{r2} XP**.\nYou need **{r3}** more to reach **level {r5}** (Progress: **{r4}%**)\n
        #                           f"Est. talking time: **{t1} to {t2}**", ctx.channel)

    @commands.command(name="levels", aliases=["ranks"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def levels_lb(self, ctx: commands.Context, top: str = ""):
        """ Server's XP Leaderboard """
        locale = langs.gl(ctx.guild, self.db)
        data = self.db.fetch("SELECT * FROM leveling WHERE gid=? AND xp!=0 AND disc!=0 ORDER BY xp DESC", (ctx.guild.id,))
        if not data:
            return await general.send(langs.gls("leaderboards_no_data", locale), ctx.channel)
            # return await general.send("I have no data saved for this server so far.", ctx.channel)
        block = "```fix\n"
        un = []   # User names
        xp = []   # XP
        xpl = []  # XP string lengths
        for user in data:
            name = f"{user['name']}#{user['disc']:04d}"
            un.append(name)
            # val = f"{user['xp'] / 100:,.0f}"
            val = langs.gns(int(user["xp"] / 100), locale)
            xp.append(val)
            xpl.append(len(val))
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
                # block += f"{i:2d}){s*4}{xp[k]}{s*(spaces-sp)}{who}\n"
                block += f"{langs.gns(i, locale, 2, False)}){s*4}{xp[k]}{s*(spaces-sp)}{who}\n"
        except (ValueError, IndexError):
            block += "No data available"
        s, e, t = langs.gns(start, locale), langs.gns(start + 9, locale), langs.gns(total, locale)
        return await general.send(langs.gls("leaderboards_levels", locale, ctx.guild.name, place, s, e, t, block), ctx.channel)
        # return await general.send(f"Top users in {ctx.guild.name} - Sorted by XP\nYour place: {place}\nShowing places {start:,} to {start + 9:,} of {total}"
        #                           f"\n{block}```", ctx.channel)

    @commands.command(name="glevels")
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def global_levels(self, ctx: commands.Context, top: str = ""):
        """ Global XP Leaderboard """
        locale = langs.gl(ctx.guild, self.db)
        data = self.db.fetch("SELECT * FROM leveling WHERE xp!=0 AND disc!=0", ())
        coll = {}
        for i in data:
            if i['uid'] not in coll:
                coll[i['uid']] = [0, f"{i['name']}#{i['disc']:04d}"]
            coll[i['uid']][0] += i['xp']
        sl = sorted(coll.items(), key=lambda a: a[1][0], reverse=True)
        r = len(sl)
        block = "```fix\n"
        un, xp, xpl = [], [], []
        for thing in range(r):
            v = sl[thing][1]
            un.append(v[1])
            # x = f"{v[0] / 100:,.0f}"
            x = langs.gns(int(v[0] / 100), locale)
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
                _data = sl[(page - 1)*10:page*10]
                start = page * 10 - 9
                spaces = max(xpl[(page - 1)*10:page*10]) + 5
            else:
                _data = sl[n-5:n+5]
                start = n - 4
                spaces = max(xpl[n-5:n+5]) + 5
            for i, d in enumerate(_data, start=start):
                try:
                    k = i - 1
                    who = un[k]
                    if d[0] == ctx.author.id:
                        who = f"-> {who}"
                    sp = xpl[k]
                    block += f"{langs.gns(i, locale, 2, False)}){s*4}{xp[k]}{s*(spaces-sp)}{who}\n"
                    # block += f"{i:2d}){s*4}{xp[k]}{s*(spaces-sp)}{who}\n"
                except IndexError:
                    pass
        except (ValueError, IndexError):
            block += "No data available"
        s, e, t = langs.gns(start, locale), langs.gns(start + 9, locale), langs.gns(total, locale)
        return await general.send(langs.gls("leaderboards_levels_global", locale, place, s, e, t, block), ctx.channel)
        # return await general.send(f"Top users globally - Sorted by XP\nYour place: {place}\nShowing places {start:,} to {start + 9:,} of {total}"
        #                           f"\n{block}```", ctx.channel)


def setup(bot):
    bot.add_cog(Leveling(bot))
