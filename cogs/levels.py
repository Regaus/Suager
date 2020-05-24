import difflib
import json
import random
from io import BytesIO

import discord
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from discord.ext import commands

from utils import time, database, http, generic
from utils.generic import random_colour, value_string, round_value

max_level = 5000
level_xp = [2250, 3000]
money_amounts = [75, 175]


def similarity(a: str, b: str or None):
    if b is None:
        return 0.0
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


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
        base = 1.25 * x ** 3 + 50 * x ** 2 + 15000 * x + 15000
        # base = 1.5 * x ** 2 + 125 * x + 200
        req += int(base)
        xp.append(req)
    return xp


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database()
        # self.ani_emotes = r"<a:(.+):(\d{17,18})>"

    # @commands.Cog.listener()
    # async def on_message_edit(self, before: discord.Message, ctx: discord.Message):
    #     if ctx.author.bot or ctx.guild is None:
    #         return
    #     if before == ctx:
    #         return
    #     if ctx.channel.id in [568148147457490958, 577599230567383058, 570682506127474729, 690254056354087047, 694684764074016799]:
    #         ani = re.findall(self.ani_emotes, ctx.content)
    #         if ani:
    #             await generic.send(f"{ctx.author.mention} smh, nitro", ctx.channel)

    @commands.Cog.listener()
    async def on_message(self, ctx: discord.Message):
        if ctx.author.bot or ctx.guild is None:
            return
        # if ctx.channel.id in [568148147457490958, 577599230567383058, 570682506127474729, 690254056354087047, 694684764074016799]:
        #     ani = re.findall(self.ani_emotes, ctx.content)
        #     if ani:
        #         await generic.send(f"{ctx.author.mention} smh, nitro", ctx.channel)
            # if ctx.author.is_avatar_animated():
            #     await generic.send("imagine having nitro", ctx.channel)
        _settings = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        xp_disabled = False
        anti_spam_xp = False
        if _settings:
            settings = json.loads(_settings['data'])
            try:
                if not settings['leveling']['enabled']:
                    xp_disabled = True
                ic = settings['leveling']['ignored_channels']
                if ctx.channel.id in ic:
                    return
            except KeyError:
                pass
            try:
                anti_spam = settings["anti_spam"]
                if ctx.channel.id in anti_spam["channels"]:
                    anti_spam_xp = True
            except KeyError:
                anti_spam_xp = False
        else:
            settings = generic.settings_template.copy()
            xp_disabled = True
        data = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
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
        data2 = self.db.fetchrow("SELECT * FROM economy WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if data2:
            money = data2["money"]
        else:
            money = 0
        similarities = [similarity(ctx.content, msg) for msg in lm]
        if ls is None:
            ls = 0
        now = time.now_ts()
        td = now - last
        _td = now - ls
        mr = random.uniform(5, 10)
        if (td < 1 or _td < 1) and anti_spam_xp:
            mult = -0.25 / _td
        elif td < mr:
            mult = 0
        elif mr <= td < 60:
            mult = td / 60
        else:
            mult = 1
        dc = mult == 0  # didn't count
        spam = 1
        if anti_spam_xp:
            if ctx.content != "" and ctx.type == discord.MessageType.default:
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
        heresy = 1
        if ctx.author.id in generic.tier_1:
            heresy = 0.95
        if ctx.author.id in generic.tier_2:
            heresy = 0.90
        if ctx.author.id in generic.tier_3:
            heresy = 0.85
        # if last > now - 60:
        #     return
        x1, x2 = level_xp
        x3, x4 = money_amounts
        try:
            sm = float(settings['leveling']['xp_multiplier'])
            sm = 0 if sm < 0 else sm if sm < 10 else 10
        except KeyError:
            sm = 1
        if mult >= 0 and spam >= 0:
            new = int(random.uniform(x1, x2) * sm * mult * spam * heresy)
            new_money = int(random.uniform(x3, x4) * mult * spam)
        else:
            # I honestly don't remember what this shit does, but it works :shrug:
            if abs(spam) < 1:
                st = 1 / spam
            else:
                st = spam
            st = -(1 + (abs(st) - 1) / 2)
            if mult > 0:
                total = -abs((mult / 4) * st)
            elif mult == 0:
                total = st / 4
            else:
                total = -abs(mult * st)
            new = int(random.uniform(x1, x2) * sm * total * (1 / heresy))
            new_money = int(random.uniform(x3, x4) * sm * total)
        if ctx.author.id == 592345932062916619:
            new = 0
        if not xp_disabled:
            xp += new
        money += new_money
        # print(td, _td, xp, cogs, _n, mult)
        requirements = levels()
        if not xp_disabled:
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
                    send = f"{ctx.author.mention} has reached **level {level:,}**! <a:forsendiscosnake:613403121686937601>"
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
                    await generic.send(send, ch, u=[ctx.author])
                    # await ch.send(send)
                except discord.Forbidden:
                    pass  # Well, if it can't send it there, too bad.
            if ld:
                send = f"{ctx.author.mention} is now **level {level:,}** <a:UmmOK:693575304622637087>"
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
                    await generic.send(send, ch, u=[ctx.author])
                    # await ch.send(send)
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
                await generic.send(generic.gls(generic.get_lang(ctx.guild), "level_reward_failed", [ctx.author.name]), ctx.channel)
                # await ctx.send(f"{ctx.author.name} should have got a level reward, "
                #                f"but I do not have sufficient permissions to do so.")
            except Exception as e:
                print(f"{time.time()} > Levels on_message > {type(e).__name__}: {e}")
        _last = last if dc else now
        if data:
            self.db.execute("UPDATE leveling SET level=?, xp=?, last=?, last_sent=?, last_messages=?, name=?, disc=? WHERE uid=? AND gid=?",
                            (level, xp, _last, now, json.dumps(lm), ctx.author.name, ctx.author.discriminator, ctx.author.id, ctx.guild.id))
        else:
            self.db.execute("INSERT INTO leveling VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (ctx.author.id, ctx.guild.id, level, xp, now, now, json.dumps([ctx.content, None, None]),
                             ctx.author.name, ctx.author.discriminator))
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
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "rewards"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        settings = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not settings:
            return await generic.send(generic.gls(locale, "rewards_none"), ctx.channel)
            # return await ctx.send("Doesn't seem like this server has leveling rewards")
        else:
            data = json.loads(settings['data'])
        try:
            rewards = data['leveling']['rewards']
            rewards.sort(key=lambda x: x['level'])
            embed = discord.Embed(colour=random_colour())
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.title = generic.gls(locale, "rewards_title", [ctx.guild.name])
            # embed.title = f"Rewards for having no life in {ctx.guild.name}"
            d = ''
            for role in rewards:
                d += generic.gls(locale, "rewards_reward", [role["level"], role["role"]])
                # d += f"Level {role['level']}: <@&{role['role']}>\n"
            embed.description = d
            return await generic.send(None, ctx.channel, embed=embed)
            # return await ctx.send(embed=embed)
        except KeyError:
            return await generic.send(generic.gls(locale, "rewards_none"), ctx.channel)
            # return await ctx.send("Doesn't seem like this server has leveling rewards...")

    @commands.command(name="erank", aliases=["ranke"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def rank(self, ctx, *, who: discord.Member = None):
        """ Rank as embed """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "ranke"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        user = who or ctx.author
        is_self = user.id == self.bot.user.id
        if user.bot and not is_self:
            return await ctx.send("Bots are cheating, so I don't even bother storing their XP.")
        _settings = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not _settings:
            dm = 1
        else:
            settings = json.loads(_settings['data'])
            try:
                dm = settings['leveling']['xp_multiplier']
                dm = 0 if dm < 0 else dm if dm < 10 else 10
            except KeyError:
                dm = 1
        data = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if data:
            level, xp = [data['level'], data['xp']]
        else:
            level, xp = [0, 0]
        embed = discord.Embed(colour=random_colour())
        embed.set_thumbnail(url=user.avatar_url)
        if is_self:
            embed.description = generic.gls(locale, "rank_self")
            # embed.description = "Imagine playing fair in your own XP system. That'd be boring."
            embed.add_field(name=generic.gls(locale, "experience"), value=generic.gls(locale, "more_than_you"), inline=False)
            embed.add_field(name=generic.gls(locale, "level"), value=generic.gls(locale, "higher_than_yours"), inline=False)
        else:
            # biased = bias.get_bias(self.db, user)
            r1 = f"{xp:,.0f}"
            if level < max_level:
                yes = levels()   # All levels
                req = int(yes[level])  # Requirement to next level
                _req = req - xp
                r2 = f"{req:,.0f}"
                r3 = value_string(_req)
                prev = int(yes[level-1]) if level != 0 else 0
                progress = (xp - prev) / (req - prev)
                r4 = round_value(progress * 100)
                r4 = 100 if r4 > 100 else r4
                embed.add_field(name=generic.gls(locale, "experience"), value=f"**{r1}**/{r2}", inline=False)
                embed.add_field(name=generic.gls(locale, "level"), value=f"{level:,}", inline=False)
                embed.add_field(name=generic.gls(locale, "rank_progress"), value=generic.gls(locale, "rank_progress2", [r4, r3]), inline=False)
                # embed.add_field(name="Progress to next level", value=f"{r4}% - {r3} XP to level up", inline=False)
            else:
                embed.add_field(name=generic.gls(locale, "experience"), value=f"**{r1}**", inline=False)
                embed.add_field(name=generic.gls(locale, "level"), value=f"{level:,}", inline=False)
            x1, x2 = [val * dm for val in level_xp]
            o1, o2 = int(x1), int(x2)
            embed.add_field(name=generic.gls(locale, "xp_per_message"), inline=False, value=f"{o1}-{o2}")
        return await ctx.send(f"**{user}**'s rank in **{ctx.guild.name}:**", embed=embed)

    @commands.command(name="rank", aliases=["irank", "ranki"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def rank_image(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Check your or someone's rank """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "rank"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
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
            # place = "unknown"
            place = generic.gls(locale, "rank_place_unknown")
            for x in range(len(_data)):
                if _data[x]['uid'] == user.id:
                    place = generic.gls(locale, "rank_place_num", [f"{x+1:,}"])
                    # place = f"#{x + 1:,}"
                    break
            if not is_self:
                progress = (xp - prev) / (req - prev)
                dr.text((552, 100), generic.gls(locale, "rank_level", [f"{level:,}"]), font=font_small, fill=font_colour)
                dr.text((552, 150), generic.gls(locale, "rank_rank", [place]), font=font_small, fill=font_colour)
                dr.text((552, 300), generic.gls(locale, "rank_xp", [f"{xp:,}", r2, f"{progress * 100:.2f}"]), font=font_small, fill=font_colour)
            else:
                progress = 0.5
                dr.text((552, 100), generic.gls(locale, "rank_level", ["69,420"]), font=font_small, fill=font_colour)
                dr.text((552, 150), generic.gls(locale, "rank_rank", ["1"]), font=font_small, fill=font_colour)
                dr.text((552, 350), generic.gls(locale, "rank_xp_self"), font=font_small, fill=font_colour)
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
            r = generic.gls(locale, "rank_user", [user, ctx.guild.name])
            # r = f"**{user}**'s rank in **{ctx.guild.name}**"
            if is_self:
                r += generic.gls(locale, "rank_self")
                # r += "\nThat's my card! Did you think I'd play fair?"
            return await generic.send(r, ctx.channel, file=discord.File(bio, filename="rank.png"))
            # return await ctx.send(r, file=discord.File(bio, filename="rank.png"))

    @commands.command(name="grank", aliases=["rankg"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def rank_global(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Check your or someone's rank """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "rankg"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        async with ctx.typing():
            user = who or ctx.author
            is_self = user.id == self.bot.user.id
            if user.bot and not is_self:
                return await ctx.send("Bots are cheating, so I don't even bother storing their XP.")
            # data = self.db.fetch("SELECT * FROM leveling WHERE uid=?", (user.id,))
            _data = self.db.fetch("SELECT * FROM leveling")
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
            place = generic.gls(locale, "rank_place_unknown")
            _xp = 0
            for someone in range(len(sl)):
                if sl[someone][0] == user.id:
                    place = generic.gls(locale, "rank_place_num", [f"{someone + 1:,}"])
                    # place = f"#{someone + 1}"
                    _xp = xp[someone]
                    break
            return await generic.send(generic.gls(locale, "global_rank", [user, f"{_xp:,}", place]), ctx.channel)

    @commands.group(name="crank", aliases=["customrank"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def custom_rank(self, ctx: commands.Context):
        """ Customise your rank """
        if ctx.invoked_subcommand is None:
            locale = generic.get_lang(ctx.guild)
            if generic.is_locked(ctx.guild, "crank"):
                return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
            if ctx.channel.id in generic.channel_locks:
                return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
            await ctx.send_help(str(ctx.command))

    @custom_rank.command(name="font")
    async def crank_font(self, ctx: commands.Context, colour: str):
        """ Font colour """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "crank"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
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
    async def crank_progress(self, ctx: commands.Context, colour: str):
        """ Progress bar colour """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "crank"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
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
    async def crank_bg(self, ctx: commands.Context, colour: str):
        """ Background colour """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "crank"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
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
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def xp_level(self, ctx: commands.Context, level: int = None):
        """ XP required to achieve a level """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "xplevel"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        if level is None:
            return await ctx.send_help(str(ctx.command))
        if level > max_level or level < max_level * -1 + 1:
            return await generic.send(generic.gls(locale, "max_level", [max_level]), ctx.channel)
            # return await ctx.send(f"The max level is {max_level}.")
        try:
            r = levels()[level - 1]
        except IndexError:
            return await generic.send(generic.gls(locale, "xl_index_error", [level, max_level]), ctx.channel)
            # return await ctx.send(f"Level specified - {level:,} gave an IndexError. Max level is {max_level}, btw.")
        if ctx.guild is not None:
            data = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        else:
            data = None
        if not data:
            xp = float("inf")
            # return await ctx.send("It doesn't seem like I have any data saved for you right now...")
        else:
            xp = data['xp']
        _settings = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not _settings:
            dm = 1
        else:
            settings = json.loads(_settings['data'])
            try:
                dm = settings['leveling']['xp_multiplier']
            except KeyError:
                dm = 1
        # x1, x2 = [val * normal * dm for val in level_xp]
        needed = value_string(r, big=True)
        base = generic.gls(locale, "xp_level_base", [ctx.author.name, f"{level:,}", needed])
        extra = ""
        if xp < r:
            x1, x2 = [val * dm for val in level_xp]
            a1, a2 = [(r - xp) / x2, (r - xp) / x1]
            # m1, m2 = int(a1) + 1, int(a2) + 1
            try:
                t1, t2 = [time.timedelta(x * 60, show_seconds=False) for x in [a1, a2]]
            except OverflowError:
                error = "Error"
                t1, t2 = [error, error]
            # t1, t2 = [time.timedelta(x * 60, show_seconds=True) for x in [a1, a2]]
            extra = generic.gls(locale, "xp_level_extra", [value_string(r - xp, big=True), t1, t2])
        return await generic.send(f"{base}{extra}", ctx.channel)
        # tl = ""
        # if xp < r:
        #     tl = f"\nXP left to reach level: **{value_string(r - xp, big=True)}**\n" \
        #          f"That is **{m1:,} to {m2:,}** more messages.\nTalking time: **{t1} to {t2}**"
        # return await ctx.send(f"Well, {ctx.author.name}...\nTo reach level **{level:,}** you will need "
        #                       f"**{needed} XP**{tl}")

    @commands.command(name="nextlevel", aliases=["nl"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def next_level(self, ctx: commands.Context):
        """ XP required for next level """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "nextlevel"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        data = self.db.fetchrow("SELECT * FROM leveling WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not data:
            return await generic.send(generic.gls(locale, "nl_no_data"), ctx.channel)
            # return await ctx.send("It doesn't seem like I have any data saved for you right now...")
        _settings = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
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
        req = r - xp
        r2 = f"{int(r):,}"
        r3 = f"{int(req):,}"
        pr = (xp - p) / (r - p)
        r4 = round_value(pr * 100)
        r4 = 100 if r4 > 100 else r4
        r5 = f"{level + 1:,}"
        normal = 1
        x1, x2 = [val * normal * dm for val in level_xp]
        a1, a2 = [(r - xp) / x2, (r - xp) / x1]
        # m1, m2 = int(a1) + 1, int(a2) + 1
        try:
            t1, t2 = [time.timedelta(x * 60, show_seconds=True) for x in [a1, a2]]
        except OverflowError:
            error = "Error"
            t1, t2 = [error, error]
        return await generic.send(generic.gls(locale, "next_level_data", [ctx.author.name, r1, r2, r3, r5, r4, t1, t2]), ctx.channel)
        # return await ctx.send(f"Alright, **{ctx.author.name}**:\nYou currently have **{r1}/{r2}** XP.\nYou need "
        #                       f"**{r3}** more to reach level **{r5}** (Progress: **{r4}%**).\nMessages left: "
        #                       f"**{m1} to {m2}**\nEstimated talking time: **{t1} to {t2}**")

    @commands.command(name="levels")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def levels_lb(self, ctx: commands.Context, top: str = ""):
        """ Server's XP Leaderboard """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "levels"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        async with ctx.typing():
            data = self.db.fetch("SELECT * FROM leveling WHERE gid=? ORDER BY xp DESC", (ctx.guild.id,))
            if not data:
                return await generic.send(generic.gls(locale, "levels_no_data"), ctx.channel)
                # return await ctx.send("I have no data at all for this server... Weird")
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
            try:
                page = int(top)
            except ValueError:
                page = None
            if (n <= 10 or top.lower() == "top") and page is None:
                _data = data[:10]
                start = 1
            elif page is not None:
                _data = data[(page - 1)*10:page*10]
                start = page * 10 - 9
            else:
                _data = data[n-5:n+5]
                start = n - 4
            if _data:
                for i, val in enumerate(_data, start=start):
                    k = i - 1
                    who = un[k]
                    if val['uid'] == ctx.author.id:
                        who = f"-> {who}"
                    s = ' '
                    sp = xpl[k]
                    block += f"{i:2d}){s*4}{xp[k]}{s*(spaces-sp)}{who}\n"
            else:
                block += "No data available"
            return await generic.send(generic.gls(locale, "levels_lb", [ctx.guild.name, place, block, start, start + 9]), ctx.channel)
            # return await ctx.send(f"Top users in {ctx.guild.name} - Sorted by XP\nYour place: {place}\n{block}```")

    @commands.command(name="glevels")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def global_levels(self, ctx: commands.Context, top: str = ""):
        """ Global XP Leaderboard """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "glevels"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        async with ctx.typing():
            data = self.db.fetch("SELECT * FROM leveling", ())
            coll = {}
            for i in data:
                if i['uid'] not in coll:
                    coll[i['uid']] = [0, f"{i['name']}#{i['disc']:04d}"]
                coll[i['uid']][0] += i['xp']
            sl = sorted(coll.items(), key=lambda a: a[1][0], reverse=True)
            r = len(sl)
            # r = len(sl) if len(sl) < 10 else 10
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
            n = 0
            for someone in range(len(sl)):
                if sl[someone][0] == ctx.author.id:
                    place = f"#{someone + 1}"
                    n = someone + 1
                    break
            s = ' '
            try:
                page = int(top)
            except ValueError:
                page = None
            if (n <= 10 or top.lower() == "top") and page is None:
                _data = sl[:10]
                start = 1
            elif page is not None:
                _data = sl[(page - 1)*10:page*10]
                start = page * 10 - 9
            else:
                _data = sl[n-5:n+5]
                start = n - 4
            # for i, d in enumerate(sl[:10], start=1):
            if _data:
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
            else:
                block += "No data available"
            return await generic.send(generic.gls(locale, "levels_global", [place, block, start, start + 9]), ctx.channel)
            # return await ctx.send(f"Top users globally - Sorted by XP\nYour place: {place}\n{block}```")


def setup(bot):
    bot.add_cog(Leveling(bot))
