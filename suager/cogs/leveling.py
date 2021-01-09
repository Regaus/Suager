import json
import random
from io import BytesIO

import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from core.utils import emotes, general, http, time
from languages import langs
from suager.cogs.birthdays import Ctx
from suager.utils import settings


async def catch_colour(ctx: commands.Context, c: int):
    if c == -1:
        await general.send("Value must be either 3 or 6 digits long", ctx.channel)
    if c == -2:
        await general.send("An error occurred. Are you sure the value is HEX (0-9 and A-F)?", ctx.channel)
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


def _levels():
    req = 0
    xp = []
    for x in range(max_level):
        # base = 1.25 * x ** 2 + x * 80 + 250
        base = x ** 2 + 99 * x + 175
        req += int(base)
        if x not in bad:
            xp.append(int(req))
        else:
            xp.append(xp[-1])
    return xp


def _level_history():
    keys = ["v3", "v4", "v5", "v6_beta4", "v6_beta12", "v615", "v616", "v7"]
    req = {}
    xp = {}
    for key in keys:
        req[key] = 0
        xp[key] = []
    req["v6_beta4"] = 150
    req["v6_beta12"] = 250
    # 25000
    for x in range(max_level):
        v3 = x ** 2 + x * 75 + 200
        req["v3"] += v3
        v4 = 1.5 * x ** 2 + 125 * x + 200
        req["v4"] += v4
        v5 = 1.25 * x ** 3 + 50 * x ** 2 + 15000 * x + 15000
        req["v5"] += v5 / 100
        power_6b = 2 + x / 40 if x < 70 else 3.75 - (x - 70) / 200 if x < 220 else 3
        v6b = x ** power_6b + 125 * x ** (1 + x / 5 if x < 5 else 2) + 7500 * x
        req["v6_beta4"] += v6b / 100
        v6b12 = x ** power_6b + 200 * x ** 2 + 7500 * x + 25000
        req["v6_beta12"] += v6b12 / 100
        power_61 = 2 + x / 40 if x < 60 else 3.5 - (x - 60) / 100 if x < 110 else 3 - (x - 110) / 180 if x < 200 else 2.5
        v615 = x ** power_61 + 200 * x ** 2 + 7500 * x + 25000
        req["v615"] += v615 / 100
        power_616 = 2 + x / 40 if x < 60 else 3.5 - (x - 60) / 100 if x < 160 else 2.5 - (x - 160) / 400 if x < 360 else 2
        multiplier_616 = 200 if x < 100 else (200 - (x - 100) / 2.5) if x < 400 else 80 - (x - 400) / 4 if x < 500 else 55
        v616 = x ** power_616 + multiplier_616 * x ** 2 + 7500 * x + 25000
        req["v616"] += v616 / 100
        v7 = x ** 2 + 99 * x + 175
        req["v7"] += v7
        if x not in bad:
            for key in keys:
                xp[key].append(req[key])
        else:
            for key in keys:
                xp[key].append(xp[key][-1])
    return xp


# def convert_xp(xp: float):
#     return int(xp / 100)


max_level = 200
bad = [69, 420, 666, 1337]
levels = _levels()
level_history = _level_history()
# xp_amounts = [2250, 3000]
xp_amounts = [20, 27]
custom_rank_blacklist = [746173049174229142]


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lvl = "leveling" if bot.name == "suager" else "leveling2"

    @commands.command(name="leveling")
    @commands.is_owner()
    async def leveling_data(self, ctx: commands.Context):
        """ Levels data """
        # __levels = [1, 2, 3, 5, 10, 20, 36, 50, 60, 75, 85, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500]
        # [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200]
        __levels = [1, 2, 3, 5, 10, 15, 20, 30, 40, 50, 60, 69, 80, 90, 100, 120, 140, 160, 180, 200]
        outputs = []
        for level in __levels:
            _level = level - 1
            lv1 = int(levels[_level])
            diff = lv1 - int(levels[_level - 1]) if level > 1 else lv1
            outputs.append(f"Level {level:>3} | Req {lv1:>9,} | Diff {diff:>6,}")
        output = "\n".join(outputs)
        return await general.send(f"```fix\n{output}```", ctx.channel)

    @commands.command(name="oldlevels")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def old_levels(self, ctx: commands.Context, level: int = None):
        """ See previous Suager leveling systems """
        names = {"v3": "Suager v3", "v4": "Suager v4", "v5": "Suager v5", "v6_beta4": "Suager v6-beta4", "v6_beta12": "Suager v6-beta12",
                 "v615": "Suager v6.1.5", "v616": "Suager v6.1.6", "v7": "Suager v7"}
        if level is not None:
            if level > max_level:
                return await general.send(f"The max level is {max_level:,}", ctx.channel)
            output = ""
            for key, name in names.items():
                output += f"\n`{name:<16} -> {level_history[key][level - 1]:>10,.0f} XP`"
            return await general.send(f"{ctx.author.name}, for **level {level}**:{output}", ctx.channel)
        else:
            xp_ = self.bot.db.fetchrow(f"SELECT xp FROM {self.lvl} WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
            xp = xp_["xp"] if xp_ else 0
            output = ""
            for key, name in names.items():
                level = 0
                for level_req in level_history[key]:
                    if xp >= level_req:
                        level += 1
                    else:
                        break
                output += f"\n`{name:<16} -> Level {level:>3}`"
            return await general.send(f"{ctx.author.name}, you have **{xp:,} XP** in this server. Here are the levels you would have been on "
                                      f"in the older leveling systems:{output}", ctx.channel)

    @commands.Cog.listener()
    async def on_message(self, ctx: discord.Message):
        if self.bot.name == "cobble" and time.now(None) < time.dt(2021, 1, 2):
            return
        if ctx.author.bot or ctx.guild is None:
            return
        if ctx.content == "" and ctx.type != discord.MessageType.default:
            return
        _settings = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        xp_disabled = False
        if _settings:
            __settings = json.loads(_settings['data'])
            try:
                if not __settings['leveling']['enabled']:
                    xp_disabled = True
                ic = __settings['leveling']['ignored_channels']
                if ctx.channel.id in ic:
                    xp_disabled = True
                    # return
            except KeyError:
                pass
        else:
            __settings = settings.template.copy()
            xp_disabled = True
        data = self.bot.db.fetchrow(f"SELECT * FROM {self.lvl} WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if data:
            level, xp, last, ls = [data['level'], data['xp'], data['last'], data['last_sent']]
        else:
            level, xp, last, ls = [0, 0, 0, 0]
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
        if _td > 60:
            mult = 1
        full = mult == 1
        dc = mult == 0  # didn't count
        x1, x2 = xp_amounts
        try:
            sm = float(__settings['leveling']['xp_multiplier'])
        except KeyError:
            sm = 1
        c = 0.87 if ctx.author.id in [667187968145883146, 742929135713910815, 579369168797958163, 740262813049684069, 402250088673574913,
                                      746173049174229142] else 1
        new = int(random.uniform(x1, x2) * sm * mult * c)
        if ctx.author.id == 592345932062916619:
            new = 0
        if not xp_disabled:
            xp += new
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
            if ctx.author.id == 430891116318031872 and level >= 5:
                lu, ld = False, False
                level = 5
            if self.bot.name == "suager":
                if lu or ld:
                    try:
                        send = str(__settings['leveling']['level_up_message']).replace('[MENTION]', ctx.author.mention)\
                            .replace('[USER]', ctx.author.name).replace('[LEVEL]', langs.gns(level, langs.gl(Ctx(ctx.guild, self.bot))))
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
                    await general.send(f"{ctx.author.name} should receive a level reward right now, but I don't have permissions required to give it.",
                                       ctx.channel)
                except Exception as e:
                    print(f"{time.time()} > Levels on_message > {type(e).__name__}: {e}")
        # _last = last if dc else now
        last_send = last if dc else now
        minute = now if full else ls
        if data:
            self.bot.db.execute(f"UPDATE {self.lvl} SET level=?, xp=?, last=?, last_sent=?, name=?, disc=? WHERE uid=? AND gid=?",
                                (level, xp, last_send, minute, ctx.author.name, ctx.author.discriminator, ctx.author.id, ctx.guild.id))
        else:
            self.bot.db.execute(f"INSERT INTO {self.lvl} VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                (ctx.author.id, ctx.guild.id, level, xp, now, now, ctx.author.name, ctx.author.discriminator))

    @commands.command(name="rewards")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=15, type=commands.BucketType.user)
    async def rewards(self, ctx: commands.Context):
        """ Rewards """
        locale = langs.gl(ctx)
        _settings = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not _settings:
            return await general.send(langs.gls("leveling_rewards_none", locale), ctx.channel)
        else:
            data = json.loads(_settings['data'])
        try:
            rewards = data['leveling']['rewards']
            rewards.sort(key=lambda x: x['level'])
            embed = discord.Embed(colour=general.random_colour())
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.title = langs.gls("leveling_rewards_title", locale, ctx.guild.name)
            d = ''
            for role in rewards:
                d += langs.gls("leveling_rewards_role", locale, langs.gns(role["level"], locale), role["role"])
            embed.description = d
            return await general.send(None, ctx.channel, embed=embed)
        except KeyError:
            return await general.send(langs.gls("leveling_rewards_none", locale), ctx.channel)

    async def level(self, ctx: commands.Context, who: discord.Member or None, locale: str):
        async with ctx.typing():
            user = who or ctx.author
            is_self = user.id == self.bot.user.id
            if user.bot and not is_self:
                return await general.send(langs.gls("leveling_rank_bot", locale), ctx.channel)
            data = self.bot.db.fetchrow(f"SELECT * FROM {self.lvl} WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
            r = langs.gls("leveling_rank", locale, user, ctx.guild.name)
            if user.id in custom_rank_blacklist:
                custom = None
                # r += "\nCongrats on setting yourself to a rank card that makes the text invisible. Now enjoy the consequences of your actions. :^)"
            else:
                custom = self.bot.db.fetchrow("SELECT * FROM custom_rank WHERE uid=?", (user.id,))
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
            try:
                font = ImageFont.truetype(font_dir, size=128)
                font_small = ImageFont.truetype(font_dir, size=64)
            except ImportError:
                await general.send(f"{emotes.Deny} It seems that image generation does not work properly here...", ctx.channel)
                font, font_small = None, None
            text_x = 542
            dr.text((text_x, -10), f"{user}", font=font, fill=font_colour)
            try:
                if level >= 0:
                    req = int(levels[level])  # Requirement to next level
                elif level == -1:
                    req = 0
                else:
                    req = int(-levels[(-level) - 2])
                r2 = langs.gns(int(req), locale)
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
            _data = self.bot.db.fetch(f"SELECT * FROM {self.lvl} WHERE gid=? AND xp!=0 AND disc!=0 ORDER BY xp DESC", (ctx.guild.id,))
            place = langs.gls("leveling_rank_rank", locale, langs.gls("generic_unknown", locale))
            if user.id == 430891116318031872:  # Alex Five is always fifth
                place = langs.gls("leveling_rank_rank", locale, langs.gls("leaderboards_place", locale, langs.gns(5, locale)))
            else:
                for x in range(len(_data)):
                    if _data[x]['uid'] == user.id:
                        place = langs.gls("leveling_rank_rank", locale, langs.gls("leaderboards_place", locale, langs.gns(x + 1, locale)))
                        break
            if not is_self:
                progress = (xp - prev) / (req - prev)
                _level = langs.gls("leveling_rank_level", locale, langs.gns(level, locale))
                dr.text((text_x, 130), f"{place} | {_level} ", font=font_small, fill=font_colour)
                r1 = langs.gns(int(xp), locale)
                r3 = langs.gfs(progress, locale, 2, True)
                r4 = langs.gls("leveling_rank_xp_left", locale, langs.gns((req - xp), locale)) if level < max_level else ""
                dr.text((text_x, (298 if r4 else 362)), langs.gls("leveling_rank_xp", locale, r1, r2, r3, r4), font=font_small, fill=font_colour)
            else:
                progress = 0.5
                place = langs.gls("leaderboards_place", locale, langs.gns(1, locale))
                _rank = langs.gls("leveling_rank_rank", locale, place)
                _level = langs.gls("leveling_rank_level", locale, langs.gns(69420, locale))
                dr.text((text_x, 130), f"{_rank} | {_level}", font=font_small, fill=font_colour)
                dr.text((text_x, 426), langs.gls("leveling_rank_xp_self", locale), font=font_small, fill=font_colour)
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
            if self.bot.name == "cobble":
                r += "\nCobbleBot XP is counted since 2 January 2020 AD."
            return await general.send(r, ctx.channel, file=discord.File(bio, filename="rank.png"))

    @commands.command(name="rank", aliases=["level"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def rank_image(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Check your or someone's rank """
        locale = langs.gl(ctx)
        return await self.level(ctx, who, locale)

    @commands.command(name="rankg", aliases=["grank"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def rank_global(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check your or someone's rank """
        locale = langs.gl(ctx)
        user = who or ctx.author
        is_self = user.id == self.bot.user.id
        if user.bot and not is_self:
            return await general.send(langs.gls("leveling_rank_bot", locale), ctx.channel)
        _data = self.bot.db.fetch(f"SELECT * FROM {self.lvl} WHERE xp!=0 AND disc!=0")
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
        __xp = int(_xp)
        return await general.send(langs.gls("leveling_rank_global", locale, user, langs.gns(__xp, locale), place, langs.gns(level, locale)), ctx.channel)

    @commands.group(name="crank", aliases=["customrank"])
    @commands.check(lambda ctx: ctx.author.id not in custom_rank_blacklist)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
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
            data = self.bot.db.fetchrow("SELECT * FROM custom_rank WHERE uid=?", (ctx.author.id,))
            if data:
                self.bot.db.execute("UPDATE custom_rank SET font=? WHERE uid=?", (c, ctx.author.id))
            else:
                self.bot.db.execute("INSERT INTO custom_rank VALUES (?, ?, ?, ?)", (ctx.author.id, c, 0x32ff32, 0))
            return await general.send(f"Set your font colour to #{colour}", ctx.channel)

    @custom_rank.command(name="progress")
    async def crank_progress(self, ctx: commands.Context, colour: str):
        """ Progress bar colour """
        c = int_colour(colour)
        cc = await catch_colour(ctx, c)
        if cc:
            data = self.bot.db.fetchrow("SELECT * FROM custom_rank WHERE uid=?", (ctx.author.id,))
            if data:
                self.bot.db.execute("UPDATE custom_rank SET progress=? WHERE uid=?", (c, ctx.author.id))
            else:
                self.bot.db.execute("INSERT INTO custom_rank VALUES (?, ?, ?, ?)", (ctx.author.id, 0x32ff32, c, 0))
            return await general.send(f"Set your progress bar colour to #{colour}", ctx.channel)

    @custom_rank.command(name="background", aliases=["bg"])
    async def crank_bg(self, ctx: commands.Context, colour: str):
        """ Background colour """
        c = int_colour(colour)
        cc = await catch_colour(ctx, c)
        if cc:
            data = self.bot.db.fetchrow("SELECT * FROM custom_rank WHERE uid=?", (ctx.author.id,))
            if data:
                self.bot.db.execute("UPDATE custom_rank SET background=? WHERE uid=?", (c, ctx.author.id))
            else:
                self.bot.db.execute("INSERT INTO custom_rank VALUES (?, ?, ?, ?)", (ctx.author.id, 0x32ff32, 0x32ff32, c))
            return await general.send(f"Set your background colour to #{colour}", ctx.channel)

    @commands.command(name="xplevel")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def xp_level(self, ctx: commands.Context, level: int):
        """ XP required to achieve a level """
        locale = langs.gl(ctx)
        if level > max_level or level < max_level * -1 + 1:
            return await general.send(langs.gls("leveling_xplevel_max", locale, langs.gns(max_level, locale)), ctx.channel)
        try:
            if level > 0:
                r = int(levels[level - 1])
            elif level == 0:
                r = 0
            else:
                r = -int(levels[(-level) - 1])
        except IndexError:
            return await general.send(langs.gls("leveling_xplevel_max", locale, langs.gns(max_level, locale)), ctx.channel)
        if ctx.guild is not None:
            data = self.bot.db.fetchrow(f"SELECT * FROM {self.lvl} WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        else:
            data = None
        if not data:
            xp = float("inf")
        else:
            xp = data['xp']
        _settings = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not _settings:
            dm = 1
        else:
            __settings = json.loads(_settings['data'])
            try:
                dm = __settings['leveling']['xp_multiplier']
            except KeyError:
                dm = 1
        base = langs.gls("leveling_xplevel_main", locale, langs.gns(int(r), locale), langs.gns(level, locale))
        extra = ""
        if xp < r:
            x1, x2 = [val * dm for val in xp_amounts]
            a1, a2 = [(r - xp) / x2, (r - xp) / x1]
            try:
                t1, t2 = [langs.td_int(x * 60, locale) for x in [a1, a2]]
            except (OverflowError, OSError):
                error = "Never"
                t1, t2 = [error, error]
            extra = langs.gls("leveling_xplevel_extra", locale, langs.gns(int((r - xp)), locale), t1, t2)
        return await general.send(f"{base}{extra}", ctx.channel)

    @commands.command(name="nextlevel", aliases=["nl"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def next_level(self, ctx: commands.Context):
        """ XP required for next level """
        locale = langs.gl(ctx)
        data = self.bot.db.fetchrow(f"SELECT * FROM {self.lvl} WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not data:
            return await general.send(langs.gls("leveling_next_level_none", locale), ctx.channel)
        _settings = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
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
        r1 = langs.gns(int(xp), locale)
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
        r2, r3, r4 = langs.gns(r, locale), langs.gns(req, locale), langs.gfs(pr if pr < 1 else 1, locale, 1, True)
        r5 = langs.gns(level + 1, locale)
        normal = 1
        x1, x2 = [val * normal * dm for val in xp_amounts]
        a1, a2 = [(r - xp) / x2, (r - xp) / x1]
        try:
            t1, t2 = [langs.td_int(x * 60, locale) for x in [a1, a2]]
        except (OverflowError, OSError):
            error = "Never"
            t1, t2 = [error, error]
        return await general.send(langs.gls("leveling_next_level", locale, ctx.author.name, r1, r2, r3, r5, r4, t1, t2), ctx.channel)


def setup(bot):
    bot.add_cog(Leveling(bot))
