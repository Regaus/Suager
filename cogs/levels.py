import difflib
import json
import random
from io import BytesIO

import discord
from discord.ext import commands

from cogs import main
from utils import time, database, http
from utils.generic import random_colour, value_string, round_value
from PIL import Image, ImageDraw, ImageFont

max_level = 5000
level_xp = [21, 30]


def similarity(a: str, b: str or None):
    if b is None:
        return 0.0
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def similarity_nc(a: str, b: str):
    return difflib.SequenceMatcher(None, a, b).ratio()


def caps_spam(a: str):
    split = a.split(" ")
    if len(split) == 1:
        sim = similarity_nc(a, a.upper())
        return int(sim > 0.9 and len(a) > 10), 1
    if len(split) == 2:
        return -1, -1
    caps = [word.upper() for word in split]
    similarities = [similarity_nc(split[i], caps[i]) for i in range(len(split)) if len(split[i]) > 2]
    spammed = [sim for sim in similarities if sim > 0.85]
    return len(spammed), len(split)


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
    for x in range(max_level):
        base = 1.5 * x ** 2 + 125 * x + 200
        req += base
        xp.append(req)
    return xp


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database()
        self.type = main.version
        self.banned = [690254056354087047, 694684764074016799]

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.bot or ctx.guild is None:
            return
        _settings = self.db.fetchrow(f"SELECT * FROM data_{self.type} WHERE type=? AND id=?",
                                     ("settings", ctx.guild.id))
        if not _settings:
            settings = main.settings_template.copy()
        else:
            settings = json.loads(_settings['data'])
        try:
            if not settings['leveling']['enabled']:
                return
            ic = settings['leveling']['ignored_channels']
            if ctx.channel.id in ic:
                return
        except KeyError:
            pass
        data = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        caps = False
        if ctx.guild.id == 690162603275714574:
            # if ctx.content.startswith("/"):
            #     return
            cs, ls = caps_spam(ctx.content)
            if ls == 1 and cs == 1:
                caps = True
            elif cs > 2:
                caps = True
        if data:
            level, xp, last, ls = [data['level'], data['xp'], data['last'], data['last_sent']]
            dm = data["last_messages"]
            if dm is None:
                lm = [None, None, None]
            else:
                lm = json.loads(data["last_messages"])
        else:
            level, xp, last, ls = [0, 0, 0, 0]
            lm = [None, None, None]
        similarities = [similarity(ctx.content, msg) for msg in lm]
        if ls is None:
            ls = 0
        now = time.now_ts()
        td = now - last
        _td = now - ls
        mr = random.uniform(5, 10)
        naughty_list = [424472476106489856, 648671430686277651, 661439493055971350, 273916273732222979]
        # canvas, WeebLord, Mari, Adde
        um = 0.95 if ctx.author.id in naughty_list else 1
        if td < 1.5 or _td < 1.5:
            mult = 0.2 / _td
        elif 1 <= td < mr:
            mult = 0
        elif mr <= td < 60:
            mult = td / 60
        else:
            mult = 1
        dc = mult == 0  # didn't count
        spam = 1
        if similarities[0] == 1:
            spam = -1 if mult > 0 else 2.5
        if similarities[0] > 0.9:
            spam = -0.3 if mult > 0 else 1.75
        elif 0.9 > similarities[0] > 0.8:
            spam = 0.3 if mult > 0 else 4 / 7
        if td < 90:
            if 1 > similarities[1] > 0.8:
                spam *= 1.5 if spam < 0 else 0.25
            elif similarities[1] == 1:
                spam *= 2 if spam < 0 else 0.125
            if similarities[2] > 0.85:
                spam *= 1.5 if spam < 0 else 0.33
        lm[2] = lm[1]
        lm[1] = lm[0]
        lm[0] = ctx.content
        # if last > now - 60:
        #     return
        x1, x2 = level_xp
        try:
            sm = float(settings['leveling']['xp_multiplier'])
            sm = 0 if sm < 0 else sm if sm < 10 else 10
        except KeyError:
            sm = 1
        if mult > 0 and spam > 0:
            new = int(random.uniform(x1, x2) * sm * um * mult * spam)
        else:
            total = -abs(mult * spam * (1 / um))
            new = int(random.uniform(x1, x2) * sm * total)
        if (ctx.author.id == 592345932062916619) or caps:
            new = 0
        xp += new
        # print(td, _td, xp, new, _n, mult)
        requirements = levels()
        lu, ld = False, False
        if level == -1 and xp > 0:
            level = 0
            lu = True
        while level < max_level and xp >= requirements[level]:
            level += 1
            lu = True
        while level > 0 and xp < requirements[level - 1]:
            level -= 1
            ld = True
        if level == 0 and xp < 0:
            level = -1
            ld = True
        if lu:
            try:
                send = str(settings['leveling']['level_up_message']).replace('[MENTION]', ctx.author.mention)\
                    .replace('[USER]', ctx.author.name).replace('[LEVEL]', f"{level:,}")
            except KeyError:
                send = f"{ctx.author.mention} has reached **level {level:,}**! " \
                       f"<a:forsendiscosnake:613403121686937601>"
            try:
                ac = settings['leveling']['announce_channel']
                if ac != 0:
                    ch = self.bot.get_channel(ac)
                    if ch is None or ch.guild.id != ctx.guild.id:
                        ch = ctx.channel
                else:
                    ch = ctx.channel
            except KeyError:
                ch = ctx.channel
            try:
                await ch.send(send)
            except discord.Forbidden:
                pass  # Well, if it can't send it there, too bad.
        if ld:
            send = f"{ctx.author.mention} is now **level {level:,}** " \
                   f"<a:UmmOK:693575304622637087>"
            try:
                ac = settings['leveling']['announce_channel']
                if ac != 0:
                    ch = self.bot.get_channel(ac)
                    if ch is None or ch.guild.id != ctx.guild.id:
                        ch = ctx.channel
                else:
                    ch = ctx.channel
            except KeyError:
                ch = ctx.channel
            try:
                await ch.send(send)
            except discord.Forbidden:
                pass  # Well, if it can't send it there, too bad.
        reason = f"Level Rewards - Level {level}"
        try:
            rewards = settings['leveling']['rewards']
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
            await ctx.send(f"{ctx.author.name} should have got a level reward, "
                           f"but I do not have sufficient permissions to do so.")
        except Exception as e:
            print(f"{time.time()} > Levels on_message > {type(e).__name__}: {e}")
        _last = last if dc else now
        if data:
            self.db.execute(
                "UPDATE leveling SET level=?, xp=?, last=?, last_sent=?, last_messages=?, name=?, disc=? WHERE uid=? "
                "AND gid=?", (level, xp, _last, now, json.dumps(lm), ctx.author.name, ctx.author.discriminator,
                              ctx.author.id, ctx.guild.id))
        else:
            self.db.execute(
                "INSERT INTO leveling VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (ctx.author.id, ctx.guild.id, level, xp, now, now, json.dumps([ctx.content, None, None]),
                 ctx.author.name, ctx.author.discriminator))

    @commands.command(name="rewards")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def rewards(self, ctx):
        """ Rewards """
        if ctx.channel.id in self.banned:
            return
        settings = self.db.fetchrow(f"SELECT * FROM data_{self.type} WHERE type=? AND id=?", ("settings", ctx.guild.id))
        if not settings:
            return await ctx.send("Doesn't seem like this server has leveling rewards")
        else:
            data = json.loads(settings['data'])
        try:
            rewards = data['leveling']['rewards']
            rewards.sort(key=lambda x: x['level'])
            embed = discord.Embed(colour=random_colour())
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.title = f"Rewards for having no life in {ctx.guild.name}"
            d = ''
            for role in rewards:
                d += f"Level {role['level']}: <@&{role['role']}>\n"
            embed.description = d
            return await ctx.send(embed=embed)
        except KeyError:
            return await ctx.send("Doesn't seem like this server has leveling rewards...")

    @commands.command(name="rank")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def rank_image(self, ctx, *, who: discord.Member = None):
        """ Check your or someone's rank """
        if ctx.channel.id in self.banned:
            return
        async with ctx.typing():
            user = who or ctx.author
            is_self = user.id == self.bot.user.id
            if user.bot and not is_self:
                return await ctx.send("Bots are cheating, so I don't even bother storing their XP.")
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
            avatar = BytesIO(await http.get(str(user.avatar_url_as(size=512, format="png")), res_method="read"))
            avatar_img = Image.open(avatar)
            avatar_resized = avatar_img.resize((512, 512))
            img.paste(avatar_resized)
            font_dir = "assets/font.ttf"
            font = ImageFont.truetype(font_dir, size=72)
            font_small = ImageFont.truetype(font_dir, size=48)
            dr.text((552, 20), f"{user}", font=font, fill=font_colour)
            al = levels()   # All levels
            try:
                req = int(al[level])  # Requirement to next level
                if level == -1:
                    req = 0
                # re = req - xp
                r2 = f"{req:,.0f}"
            except IndexError:
                req = float("inf")
                r2 = "MAX"
            # r3 = value_string(re)
            try:
                prev = int(al[level-1]) if level != 0 else 0
                if level == -1:
                    prev = -int(al[0])
            except IndexError:
                prev = 0
            _data = self.db.fetch("SELECT * FROM leveling WHERE gid=? ORDER BY xp DESC", (ctx.guild.id,))
            place = "unknown"
            for x in range(len(_data)):
                if _data[x]['uid'] == user.id:
                    place = f"#{x + 1:,}"
                    break
            if not is_self:
                progress = (xp - prev) / (req - prev)
                dr.text((552, 100), f"Level {level:,}", font=font_small, fill=font_colour)
                dr.text((552, 150), f"Rank {place}", font=font_small, fill=font_colour)
                dr.text((552, 350), f"{xp:,}/{r2} XP", font=font_small, fill=font_colour)
            else:
                progress = 0.5
                dr.text((552, 100), f"Level 69,420", font=font_small, fill=font_colour)
                dr.text((552, 150), f"Rank #1", font=font_small, fill=font_colour)
                dr.text((552, 350), f"9,999,999,999,999 XP", font=font_small, fill=font_colour)
            full = 800
            done = int(progress * full)
            if done < 0:
                done = 0
            # left = full - done
            i1 = Image.new("RGB", (done, 60), color=progress_colour)
            i2 = Image.new("RGB", (full + 10, 70), color=(30, 30, 30))
            box1 = (552, 420, 552 + done, 480)
            box2 = (547, 415, 557 + full, 485)  # 2 px bigger
            img.paste(i2, box2)
            img.paste(i1, box1)
            bio = BytesIO()
            img.save(bio, "PNG")
            # img.save("test.png", "PNG")
            bio.seek(0)
            r = f"**{user}**'s rank in **{ctx.guild.name}**"
            if is_self:
                r += "\nThat's my card! Did you think I'd play fair?"
            return await ctx.send(r, file=discord.File(bio, filename="rank.png"))

    @commands.group(name="crank", aliases=["customrank"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def custom_rank(self, ctx):
        """ Customise your rank """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @custom_rank.command(name="font")
    async def crank_font(self, ctx, colour: str):
        """ Font colour """
        c = int_colour(colour)
        if c == -1:
            return await ctx.send("The colour must be either 3 or 6 digits long")
        if c == -2:
            return await ctx.send("An error occurred. Are you sure the colour is a HEX value (0-9 and A-F)?")
        if c == -3:
            return await ctx.send("Remove the `#`...")
        data = self.db.fetchrow("SELECT * FROM custom_rank WHERE uid=?", (ctx.author.id,))
        if data:
            db = self.db.execute("UPDATE custom_rank SET font=? WHERE uid=?", (c, ctx.author.id))
        else:
            db = self.db.execute("INSERT INTO custom_rank VALUES (?, ?, ?, ?)", (ctx.author.id, c, 0x32ff32, 0))
        return await ctx.send(f"Updated your font colour to #{colour}\nDatabase status: {db}")

    @custom_rank.command(name="progress")
    async def crank_progress(self, ctx, colour: str):
        """ Progress bar colour """
        c = int_colour(colour)
        if c == -1:
            return await ctx.send("The colour must be either 3 or 6 digits long")
        if c == -2:
            return await ctx.send("An error occurred. Are you sure the colour is a HEX value (0-9 and A-F)?")
        if c == -3:
            return await ctx.send("Remove the `#`...")
        data = self.db.fetchrow("SELECT * FROM custom_rank WHERE uid=?", (ctx.author.id,))
        if data:
            db = self.db.execute("UPDATE custom_rank SET progress=? WHERE uid=?", (c, ctx.author.id))
        else:
            db = self.db.execute("INSERT INTO custom_rank VALUES (?, ?, ?, ?)", (ctx.author.id, 0x32ff32, c, 0))
        return await ctx.send(f"Updated your progress bar colour to #{colour}\nDatabase status: {db}")

    @custom_rank.command(name="background", aliases=["bg"])
    async def crank_bg(self, ctx, colour: str):
        """ Background colour """
        c = int_colour(colour)
        if c == -1:
            return await ctx.send("The colour must be either 3 or 6 digits long")
        if c == -2:
            return await ctx.send("An error occurred. Are you sure the colour is a HEX value (0-9 and A-F)?")
        if c == -3:
            return await ctx.send("Remove the `#`...")
        data = self.db.fetchrow("SELECT * FROM custom_rank WHERE uid=?", (ctx.author.id,))
        if data:
            db = self.db.execute("UPDATE custom_rank SET background=? WHERE uid=?", (c, ctx.author.id))
        else:
            db = self.db.execute("INSERT INTO custom_rank VALUES (?, ?, ?, ?)", (ctx.author.id, 0x32ff32, 0x32ff32, c))
        return await ctx.send(f"Updated your progress bar colour to #{colour}\nDatabase status: {db}")

    @commands.command(name="xplevel")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def xp_level(self, ctx, level: int = None):
        """ XP required to achieve a level """
        if ctx.channel.id in self.banned:
            return
        if level is None:
            return await ctx.send_help(str(ctx.command))
        if level > max_level or level < max_level * -1 + 1:
            return await ctx.send(f"The max level is {max_level}.")
        try:
            r = levels()[level - 1]
        except IndexError:
            return await ctx.send(f"Level specified - {level:,} gave an IndexError. Max level is {max_level}, btw.")
        data = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not data:
            return await ctx.send("It doesn't seem like I have any data saved for you right now...")
        _settings = self.db.fetchrow(f"SELECT * FROM data_{self.type} WHERE type=? AND id=?",
                                     ("settings", ctx.guild.id))
        if not _settings:
            dm = 1
        else:
            settings = json.loads(_settings['data'])
            try:
                dm = settings['leveling']['xp_multiplier']
            except KeyError:
                dm = 1
        xp = data['xp']
        x1, x2 = [val * dm for val in level_xp]
        a1, a2 = [(r - xp) / x2, (r - xp) / x1]
        m1, m2 = int(a1) + 1, int(a2) + 1
        t1, t2 = [time.timedelta(x * 60, show_seconds=False) for x in [m1, m2]]
        # x1, x2 = [val * normal * dm for val in level_xp]
        needed = value_string(r, big=True)
        tl = ""
        if xp < r:
            tl = f"\nXP left to reach level: **{value_string(r - xp, big=True)}**\n" \
                 f"That is **{m1:,} to {m2:,}** more messages.\nTalking time: **{t1} to {t2}**"
        return await ctx.send(f"Well, {ctx.author.name}...\nTo reach level **{level:,}** you will need "
                              f"**{needed} XP**{tl}")

    @commands.command(name="nextlevel", aliases=["nl"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def next_level(self, ctx):
        """ XP required for next level """
        if ctx.channel.id in self.banned:
            return
        data = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not data:
            return await ctx.send("It doesn't seem like I have any data saved for you right now...")
        _settings = self.db.fetchrow(f"SELECT * FROM data_{self.type} WHERE type=? AND id=?",
                                     ("settings", ctx.guild.id))
        if not _settings:
            dm = 1
        else:
            settings = json.loads(_settings['data'])
            try:
                dm = settings['leveling']['xp_multiplier']
            except KeyError:
                dm = 1
        level, xp = [data['level'], data['xp']]
        r1 = f"{int(xp):,}"
        # biased = bias.get_bias(self.db, ctx.author)
        yes = levels()
        try:
            r = int(yes[level])
        except IndexError:
            r = -1
        try:
            p = int(yes[level-1]) if level != 0 else 0
        except IndexError:
            p = 0
        if level == -1:
            r = 0
            p = -int(yes[0])
        # r, p = [int(yes[level]), ]
        re = r - xp
        r2 = f"{int(r):,}"
        r3 = f"{int(re):,}"
        pr = (xp - p) / (r - p)
        r4 = round_value(pr * 100)
        r4 = 100 if r4 > 100 else r4
        r5 = f"{level + 1:,}"
        normal = 1
        x1, x2 = [val * normal * dm for val in level_xp]
        a1, a2 = [(r - xp) / x2, (r - xp) / x1]
        m1, m2 = int(a1) + 1, int(a2) + 1
        t1, t2 = [time.timedelta(x * 60, show_seconds=False) for x in [m1, m2]]
        return await ctx.send(f"Alright, **{ctx.author.name}**:\nYou currently have **{r1}/{r2}** XP.\nYou need "
                              f"**{r3}** more to reach level **{r5}** (Progress: **{r4}%**).\nMessages left: "
                              f"**{m1} to {m2}**\nEstimated talking time: **{t1} to {t2}**")

    @commands.command(name="levels")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def levels_lb(self, ctx, top: str = ""):
        """ Server's XP Leaderboard """
        if ctx.channel.id in self.banned:
            return
        async with ctx.typing():
            data = self.db.fetch("SELECT * FROM leveling WHERE gid=? ORDER BY xp DESC", (ctx.guild.id,))
            if not data:
                return await ctx.send("I have no data at all for this server... Weird")
            block = "```fix\n"
            un = []   # User names
            xp = []   # XP
            # unl = []  # User name lengths
            xpl = []  # XP string lengths
            for user in data:
                name = f"{user['name']}#{user['disc']:04d}"
                un.append(name)
                # unl.append(len(name))
                val = f"{value_string(user['xp'])}"
                xp.append(val)
                xpl.append(len(val))
            spaces = max(xpl) + 5
            place = "unknown"
            n = 0
            for x in range(len(data)):
                if data[x]['uid'] == ctx.author.id:
                    place = f"#{x + 1}"
                    n = x + 1
                    break
            if n <= 10 or top.lower() == "top":
                _data = data[:10]
                start = 1
            else:
                _data = data[n-5:n+5]
                start = n - 4
            for i, val in enumerate(_data, start=start):
                k = i - 1
                who = un[k]
                if val['uid'] == ctx.author.id:
                    who = f"-> {who}"
                s = ' '
                sp = xpl[k]
                block += f"{str(i).zfill(2)}){s*4}{xp[k]}{s*(spaces-sp)}{who}\n"
            return await ctx.send(f"Top users in {ctx.guild.name} - Sorted by XP\nYour place: {place}\n{block}```")

    @commands.command(name="glevels")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def global_levels(self, ctx):
        """ Global XP Leaderboard """
        if ctx.channel.id in self.banned:
            return
        async with ctx.typing():
            data = self.db.fetch("SELECT * FROM leveling", ())
            coll = {}
            for i in data:
                if i['uid'] not in coll:
                    coll[i['uid']] = [0, f"{i['name']}#{i['disc']:04d}"]
                coll[i['uid']][0] += i['xp']
            sl = sorted(coll.items(), key=lambda a: a[1][0], reverse=True)
            r = len(sl) if len(sl) < 10 else 10
            block = "```fix\n"
            un, xp, xpl = [], [], []
            for thing in range(r):
                v = sl[thing][1]
                un.append(v[1])
                x = value_string(v[0])
                xp.append(x)
                xpl.append(len(x))
            spaces = max(xpl) + 5
            place = "unknown"
            for someone in range(len(sl)):
                if sl[someone][0] == ctx.author.id:
                    place = f"#{someone + 1}"
            s = ' '
            for i, d in enumerate(sl[:10], start=1):
                k = i - 1
                who = un[k]
                if d[0] == ctx.author.id:
                    who = f"-> {who}"
                sp = xpl[k]
                block += f"{str(i).zfill(2)}){s*4}{xp[k]}{s*(spaces-sp)}{who}\n"
            return await ctx.send(f"Top users globally - Sorted by XP\nYour place: {place}\n{block}```")


def setup(bot):
    bot.add_cog(Leveling(bot))
