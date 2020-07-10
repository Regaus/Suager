import json
import random
from io import BytesIO

import discord
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from discord.ext import commands

from core.utils import time, database, http, general, emotes
from suager.utils import settings

max_level = 5000
xp_amounts = [2250, 3000]
money_amounts = [75, 125]


async def catch_colour(ctx: commands.Context, c: int):
    if c == -1:
        await general.send("Value must be either 3 or 6 digits long", ctx.channel)
    if c == -2:
        await general.send("An error occurred. Are you sure the value is HEX (0-9 and A-F)?", ctx.channel)
    if c == -3:
        await general.send("Remove the `#`...", ctx.channel)
    return c >= 0


def get_colour(colour: int):
    a = 256
    r, g = divmod(colour, a ** 2)
    g, b = divmod(g, a)
    return r, g, b


def int_colour(colour: str):
    try:
        if colour[0] == "#":
            return -3
        length = len(colour)
        if length == 3:
            a, b, c = colour
            colour = f"{a}{a}{b}{b}{c}{c}"
        elif length != 6:
            return -1
        return int(colour, base=16)
    except ValueError:
        return -2


def levels():
    req = 0
    xp = []
    # mult = multiplier ** 0.001 if multiplier >= 1 else multiplier ** 0.75
    for x in range(max_level):
        if x not in [69, 420, 666, 1337]:
            base = 1.25 * x ** 3 + 50 * x ** 2 + 15000 * x + 15000
            req += int(base)
            xp.append(req)
        else:
            xp.append(xp[-1])
    return xp


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database(self.bot.name)

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
        new = int(random.uniform(x1, x2) * sm * mult)
        new_money = int(random.uniform(x3, x4) * mult)
        if ctx.author.id == 592345932062916619:
            new = 0
        if not xp_disabled:
            xp += new
        money += new_money
        requirements = levels()
        if not xp_disabled:
            lu, ld = False, False
            if level >= 0:
                while level < max_level and xp >= requirements[level]:
                    level += 1
                    lu = True
                while level > 0 and xp < requirements[level - 1]:
                    level -= 1
                    ld = True
                if level == 0 and xp < 0:
                    level = -1
                    ld = True
            elif level == -1:
                if xp >= 0:
                    level = 0
                    lu = True
                if xp < -requirements[0]:
                    level -= 1
                    ld = True
            else:
                while -max_level <= level < -1 and xp >= -requirements[(-level) - 2]:
                    level += 1
                    lu = True
                while level >= -max_level and xp < -requirements[(-level) - 1]:
                    level -= 1
                    ld = True
            if lu:
                try:
                    send = str(__settings['leveling']['level_up_message']).replace('[MENTION]', ctx.author.mention)\
                        .replace('[USER]', ctx.author.name).replace('[LEVEL]', f"{level:,}")
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
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def rewards(self, ctx: commands.Context):
        """ Rewards """
        _settings = self.db.fetchrow("SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not _settings:
            return await general.send("This server seems to have no leveling rewards", ctx.channel)
        else:
            data = json.loads(_settings['data'])
        try:
            rewards = data['leveling']['rewards']
            rewards.sort(key=lambda x: x['level'])
            embed = discord.Embed(colour=general.random_colour())
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.title = f"Rewards for having no life in **{ctx.guild.name}**"
            d = ''
            for role in rewards:
                d += f"Level {role['level']:,}: <@{role['role']}>"
            embed.description = d
            return await general.send(None, ctx.channel, embed=embed)
        except KeyError:
            return await general.send("This server seems to have no leveling rewards", ctx.channel)

    @commands.command(name="ranke")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def rank_embed(self, ctx, *, who: discord.Member = None):
        """ Rank as embed """
        user = who or ctx.author
        is_self = user.id == self.bot.user.id
        if user.bot and not is_self:
            return await general.send("I don't count bots' XP because they're cheaters", ctx.channel)
        _settings = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not _settings:
            dm = 1
        else:
            __settings = json.loads(_settings['data'])
            try:
                dm = __settings['leveling']['xp_multiplier']
            except KeyError:
                dm = 1
        data = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if data:
            level, xp = [data['level'], data['xp']]
        else:
            level, xp = [0, 0]
        embed = discord.Embed(colour=general.random_colour())
        embed.title = f"**{user}**'s rank in **{ctx.guild.name}**"
        embed.set_thumbnail(url=user.avatar_url)
        if is_self:
            embed.description = "That's my own rank, so I don't have to play fair."
            embed.add_field(name="Experience", value="More than you", inline=False)
            embed.add_field(name="Level", value="Higher than you'll ever reach", inline=False)
        else:
            r1 = f"{xp / 100:,.0f}"
            if level < max_level:
                yes = levels()   # All levels
                try:
                    if level >= 0:
                        req = int(yes[level])  # Requirement to next level
                    elif level == -1:
                        req = 0
                    else:
                        req = int(-yes[(-level) - 2])
                except IndexError:
                    req = float("inf")
                try:
                    if level > 0:
                        prev = int(yes[level-1])
                    elif level == 0:
                        prev = 0
                    else:
                        prev = -int(yes[(-level) - 1])
                except IndexError:
                    prev = 0
                _req = req - xp
                r2 = f"{req / 100:,.0f}"
                r3 = f"{_req / 100:,.0f}"
                progress = (xp - prev) / (req - prev)
                r4 = general.round_value(progress * 100)
                r4 = 100 if r4 > 100 else r4
                embed.add_field(name="Experience", value=f"**{r1}**/{r2}", inline=False)
                embed.add_field(name="Level", value=f"{level:,}", inline=False)
                embed.add_field(name="Progress", value=f"**{r4}%** ({r3} XP to level up)", inline=False)
            else:
                embed.add_field(name="Experience", value=f"**{r1}**", inline=False)
                embed.add_field(name="Level", value=f"{level:,}", inline=False)
            x1, x2 = [val * dm for val in xp_amounts]
            o1, o2 = int(x1), int(x2)
            embed.add_field(name="XP per minute", value=f"{o1 / 100:,.0f}-{o2 / 100:,.0f}", inline=False)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="rank", aliases=["irank", "ranki", "level"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def rank_image(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Check your or someone's rank """
        async with ctx.typing():
            user = who or ctx.author
            is_self = user.id == self.bot.user.id
            if user.bot and not is_self:
                return await general.send("I don't count bots' XP because they're cheaters", ctx.channel)
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
            img = Image.new("RGB", (1536, 512), color=background_colour)
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
            font = ImageFont.truetype(font_dir, size=72)
            font_small = ImageFont.truetype(font_dir, size=48)
            dr.text((552, 20), f"{user}", font=font, fill=font_colour)
            al = levels()   # All levels
            try:
                if level >= 0:
                    req = int(al[level])  # Requirement to next level
                elif level == -1:
                    req = 0
                else:
                    req = int(-al[(-level) - 2])
                r2 = f"{req / 100:,.0f}"
            except IndexError:
                req = float("inf")
                r2 = "MAX"
            try:
                if level > 0:
                    prev = int(al[level-1])
                elif level == 0:
                    prev = 0
                else:
                    prev = -int(al[(-level) - 1])
            except IndexError:
                prev = 0
            _data = self.db.fetch("SELECT * FROM leveling WHERE gid=? AND xp!=0 AND disc!=0 ORDER BY xp DESC", (ctx.guild.id,))
            place = "Rank Undefined"
            for x in range(len(_data)):
                if _data[x]['uid'] == user.id:
                    place = f"Rank #{x+1:,}"
                    break
            if not is_self:
                progress = (xp - prev) / (req - prev)
                dr.text((552, 100), f"Level {level:,}", font=font_small, fill=font_colour)
                dr.text((552, 150), place, font=font_small, fill=font_colour)
                dr.text((552, 300), f"{xp / 100:,.0f}/{r2} XP\nProgress: {progress*100:.2f}%", font=font_small, fill=font_colour)
            else:
                progress = 0.5
                dr.text((552, 100), "Level 69,420", font=font_small, fill=font_colour)
                dr.text((552, 150), "Rank #1", font=font_small, fill=font_colour)
                dr.text((552, 350), "Infinite XP", font=font_small, fill=font_colour)
            full = 800
            done = int(progress * full)
            if done < 0:
                done = 0
            i1 = Image.new("RGB", (done, 60), color=progress_colour)
            i2 = Image.new("RGB", (full + 10, 70), color=(30, 30, 30))
            box1 = (552, 420, 552 + done, 480)
            box2 = (547, 415, 557 + full, 485)  # 2 px bigger
            img.paste(i2, box2)
            img.paste(i1, box1)
            bio = BytesIO()
            img.save(bio, "PNG")
            bio.seek(0)
            r = f"**{user}**'s rank in **{ctx.guild.name}**"
            if is_self:
                r += "That's my own rank, so why should I play fair?"
            return await general.send(r, ctx.channel, file=discord.File(bio, filename="rank.png"))

    @commands.command(name="rankg")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def rank_global(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check your or someone's rank """
        async with ctx.typing():
            user = who or ctx.author
            is_self = user.id == self.bot.user.id
            if user.bot and not is_self:
                return await general.send("I don't count bots' XP because they're cheaters", ctx.channel)
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
            place = "Undefined"
            _xp = 0
            for someone in range(len(sl)):
                if sl[someone][0] == user.id:
                    place = f"#{someone + 1:,}"
                    _xp = xp[someone]
                    break
            return await general.send(f"**{user}** has **{_xp / 100:,.0f} global XP** and is **{place}** on the leaderboard", ctx.channel)

    @commands.group(name="crank", aliases=["customrank"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
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
    async def xp_level(self, ctx: commands.Context, level: int = None):
        """ XP required to achieve a level """
        if level is None:
            return await ctx.send_help(str(ctx.command))
        if level > max_level or level < max_level * -1 + 1:
            return await general.send(f"The max level is {max_level:,}", ctx.channel)
        al = levels()
        try:
            if level > 0:
                r = int(al[level - 1])
            elif level == 0:
                r = 0
            else:
                r = -int(al[(-level) - 1])
        except IndexError:
            return await general.send(f"An error can occurred - make sure the level specified is below the max level ({max_level:,}).", ctx.channel)
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
        needed = f"{r / 100:,.0f}"
        base = f"You need **{needed} XP** to reach **level {level:,}**"
        extra = ""
        if xp < r:
            x1, x2 = [val * dm for val in xp_amounts]
            a1, a2 = [(r - xp) / x2, (r - xp) / x1]
            try:
                t1, t2 = [time.timedelta(x * 60) for x in [a1, a2]]
            except OverflowError:
                error = "Never"
                t1, t2 = [error, error]
            except OSError:
                error = "Error"
                t1, t2 = [error, error]
            extra = f"\nXP left: **{(r - xp) / 100:,.0f}**\nEst. time: **{t1} to {t2}**"
        return await general.send(f"{base}{extra}", ctx.channel)

    @commands.command(name="nextlevel", aliases=["nl"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def next_level(self, ctx: commands.Context):
        """ XP required for next level """
        data = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not data:
            return await general.send("I have no leveling data for you right now...", ctx.channel)
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
            return await general.send(f"**{ctx.author.name}**, you have already reached the max level. There is nowhere higher for you to go.", ctx.channel)
        r1 = f"{int(xp / 100):,}"
        yes = levels()
        try:
            if level >= 0:
                r = int(yes[level])  # Requirement to next level
            elif level == -1:
                r = 0
            else:
                r = int(-yes[(-level) - 2])
        except IndexError:
            r = float("inf")
        try:
            if level > 0:
                p = int(yes[level-1])
            elif level == 0:
                p = 0
            else:
                p = -int(yes[(-level) - 1])
        except IndexError:
            p = 0
        req = r - xp
        r2 = f"{int(r / 100):,}"
        r3 = f"{int(req / 100):,}"
        pr = (xp - p) / (r - p)
        r4 = general.round_value(pr * 100)
        r4 = 100 if r4 > 100 else r4
        r5 = f"{level + 1:,}"
        normal = 1
        x1, x2 = [val * normal * dm for val in xp_amounts]
        a1, a2 = [(r - xp) / x2, (r - xp) / x1]
        try:
            t1, t2 = [time.timedelta(x * 60) for x in [a1, a2]]
        except OverflowError:
            error = "Never"
            t1, t2 = [error, error]
        except OSError:
            error = "Error"
            t1, t2 = [error, error]
        return await general.send(f"**{ctx.author.name}** - You have **{r1}/{r2} XP**.\nYou need **{r3}** more to reach **level {r5}** (Progress: **{r4}%**)\n"
                                  f"Est. talking time: **{t1} to {t2}**", ctx.channel)

    @commands.command(name="levels", aliases=["ranks"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def levels_lb(self, ctx: commands.Context, top: str = ""):
        """ Server's XP Leaderboard """
        data = self.db.fetch("SELECT * FROM leveling WHERE gid=? AND xp!=0 AND disc!=0 ORDER BY xp DESC", (ctx.guild.id,))
        if not data:
            return await general.send("I have no data saved for this server so far.", ctx.channel)
        block = "```fix\n"
        un = []   # User names
        xp = []   # XP
        xpl = []  # XP string lengths
        for user in data:
            name = f"{user['name']}#{user['disc']:04d}"
            un.append(name)
            val = f"{user['xp'] / 100:,.0f}"
            xp.append(val)
            xpl.append(len(val))
        total = len(xp)
        place = "unknown"
        n = 0
        for x in range(len(data)):
            if data[x]['uid'] == ctx.author.id:
                place = f"#{x + 1}"
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
                block += f"{i:2d}){s*4}{xp[k]}{s*(spaces-sp)}{who}\n"
        except ValueError:
            block += "No data available"
        return await general.send(f"Top users in {ctx.guild.name} - Sorted by XP\nYour place: {place}\nShowing places {start:,} to {start + 9:,} of {total}"
                                  f"\n{block}```", ctx.channel)

    @commands.command(name="glevels")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def global_levels(self, ctx: commands.Context, top: str = ""):
        """ Global XP Leaderboard """
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
            x = f"{v[0] / 100:,.0f}"
            xp.append(x)
            xpl.append(len(x))
        total = len(xp)
        place = "unknown"
        n = 0
        for someone in range(len(sl)):
            if sl[someone][0] == ctx.author.id:
                place = f"#{someone + 1}"
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
                    block += f"{i:2d}){s*4}{xp[k]}{s*(spaces-sp)}{who}\n"
                except IndexError:
                    pass
        except ValueError:
            block += "No data available"
        return await general.send(f"Top users globally - Sorted by XP\nYour place: {place}\nShowing places {start:,} to {start + 9:,} of {total}"
                                  f"\n{block}```", ctx.channel)


def setup(bot):
    bot.add_cog(Leveling(bot))
