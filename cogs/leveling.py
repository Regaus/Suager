import json
import random
from io import BytesIO

import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from utils import bot_data, emotes, general, http, languages, settings, time
from utils.leaderboards import leaderboard, leaderboard2


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
    keys = ["v3", "v4", "v5", "v6", "v7"]
    req = {}
    xp = {}
    for key in keys:
        req[key] = 0
        xp[key] = []
    for x in range(max_level):
        v3 = x ** 2 + x * 75 + 200
        req["v3"] += v3
        v4 = 1.5 * x ** 2 + 125 * x + 200
        req["v4"] += v4
        v5 = 1.25 * x ** 3 + 50 * x ** 2 + 15000 * x + 15000
        req["v5"] += v5 / 100
        power_6 = 2 + x / 40 if x < 60 else 3.5 - (x - 60) / 100 if x < 160 else 2.5 - (x - 160) / 400 if x < 360 else 2
        multiplier_6 = 200 if x < 100 else (200 - (x - 100) / 2.5) if x < 400 else 80 - (x - 400) / 4 if x < 500 else 55
        v6 = x ** power_6 + multiplier_6 * x ** 2 + 7500 * x + 25000
        req["v6"] += v6 / 100
        v7 = x ** 2 + 99 * x + 175
        req["v7"] += v7
        if x not in bad:
            for key in keys:
                xp[key].append(req[key])
        else:
            for key in keys:
                xp[key].append(xp[key][-1])
    return xp


max_level = 200
bad = [69, 420, 666, 1337]
levels = _levels()
level_history = _level_history()
xp_amounts = [20, 27]
# custom_rank_blacklist = [746173049174229142]
# _year = time.now(None).year


class Leveling(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.command(name="leveling")
    @commands.is_owner()
    async def leveling_data(self, ctx: commands.Context):
        """ Levels data """
        # __levels = [1, 2, 3, 5, 10, 20, 36, 50, 60, 75, 85, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500]
        # [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200]
        __levels = [1, 2, 3, 5, 10, 15, 20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200]
        outputs = []
        for level in __levels:
            _level = level - 1
            lv1 = int(levels[_level])
            diff = lv1 - int(levels[_level - 1]) if level > 1 else lv1
            outputs.append(f"Level {level:>3} | Req {lv1:>9,} | Diff {diff:>6,}")
        output = "\n".join(outputs)
        return await general.send(f"```fix\n{output}```", ctx.channel)

    @commands.command(name="oldlevels", aliases=["levelhistory"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def old_levels(self, ctx: commands.Context, level: int = None):
        """ See Suager's previous leveling systems """
        names = {"v3": "Suager v3", "v4": "Suager v4", "v5": "Suager v5", "v6": "Suager v6", "v7": "Suager v7"}
        if level is not None:
            if level > max_level:
                return await general.send(f"The max level is {max_level:,}", ctx.channel)
            output = ""
            for key, name in names.items():
                output += f"\n`{name:<9} -> {level_history[key][level - 1]:>9,.0f} XP`"
            return await general.send(f"{ctx.author.name}, for **level {level}** you would've needed:{output}", ctx.channel)
        else:
            xp_ = self.bot.db.fetchrow(f"SELECT xp FROM leveling WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
            xp = xp_["xp"] if xp_ else 0
            output = ""
            for key, name in names.items():
                level = 0
                for level_req in level_history[key]:
                    if xp >= level_req:
                        level += 1
                    else:
                        break
                output += f"\n`{name:<9} -> Level {level:>3}`"
            return await general.send(f"{ctx.author.name}, you have **{xp:,} XP** in this server. Here are the levels you would have been on "
                                      f"in the older leveling systems:{output}", ctx.channel)

    @commands.Cog.listener()
    async def on_message(self, ctx: discord.Message):
        if self.bot.name == "cobble":
            return
        if ctx.author.bot or ctx.guild is None:
            return
        if ctx.content == "" and ctx.type != discord.MessageType.default:
            return
        # if time.now(None) < time.dt(2021, 5, 21):
        #     return
        # elif time.dt(2022) > time.now(None) > time.dt(2021, 5, 21):
        #     year = "2021"
        # else:
        #     year = "2022"
        year = str(time.now(None).year)
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
            __settings = settings.template_suager.copy()
            xp_disabled = True
        data = self.bot.db.fetchrow(f"SELECT * FROM leveling WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if data:
            level, xp, last, ls, yearly = data['level'], data['xp'], data['last'], data['last_sent'], data[year]
        else:
            level, xp, last, ls, yearly = 0, 0, 0, 0, 0
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
        c = 1
        # c = 0.87 if ctx.author.id in [561164743562493952] else 1
        if ctx.guild.id == 568148147457490954:
            if 571034926107852801 in [role.id for role in ctx.author.roles]:
                c *= 0.33
        # c = 0.91 if ctx.author.id in [377467233401831424] else c
        # c *= 0.9 if 796009343539347496 in [role.id for role in ctx.author.roles] and ctx.author.id != 593736085327314954 else 1
        # "Feminist" role on chill crew
        new = int(random.uniform(x1, x2) * sm * mult * c)
        if ctx.author.id == 592345932062916619:
            new = 0
        if not xp_disabled:
            xp += new
            yearly += new
            # old_level = level
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
            reason = f"Level Rewards - Level {level}"
            language = self.bot.language(languages.FakeContext(ctx.guild, self.bot))
            current_reward, next_reward = {"role": language.string("generic_none"), "level": 0}, {"role": language.string("generic_unknown"), "level": 0}
            top_role = False
            new_role = False
            try:
                rewards = __settings['leveling']['rewards']
                if rewards:  # Don't bother if they're empty
                    # l1, l2 = [], []
                    rewards.sort(key=lambda x: x['level'])
                    next_reward = {"role": ctx.guild.get_role(rewards[0]["role"]).name, "level": rewards[0]["level"]}
                    # for i in range(len(rewards)):
                    #     l1.append(rewards[i]['level'])
                    #     l2.append(rewards[i]['role'])
                    roles = [r.id for r in ctx.author.roles]
                    # for i in range(len(rewards)):
                    for i, reward in enumerate(rewards):
                        role: discord.Role = ctx.guild.get_role(reward["role"])  # discord.Object(id=l2[i])
                        has_role = reward["role"] in roles
                        if level >= reward["level"]:
                            if i < len(rewards) - 1:
                                next_role = rewards[i + 1]
                                if level < next_role["level"]:
                                    current_reward = {"role": role.name, "level": reward["level"]}
                                    next_reward = {"role": ctx.guild.get_role(next_role["role"]).name, "level": next_role["level"]}
                                    if not has_role:
                                        await ctx.author.add_roles(role, reason=reason)
                                        new_role = True
                                else:
                                    if has_role:
                                        await ctx.author.remove_roles(role, reason=reason)
                            else:
                                current_reward = {"role": role.name, "level": reward["level"]}
                                next_reward = {"role": language.string("leveling_rewards_max"), "level": max_level}
                                top_role = True
                                if not has_role:
                                    await ctx.author.add_roles(role, reason=reason)
                                    new_role = True
                        else:
                            if has_role:
                                await ctx.author.remove_roles(role, reason=reason)
            except KeyError:
                pass  # If no level rewards, don't even bother
            except AttributeError:  # This means a role was deleted...
                # FIXME: Try to ignore deleted roles instead of skipping the entire role rewards script
                pass
            except discord.Forbidden:
                await general.send(f"{ctx.author.name} should receive a level reward right now, but I don't have permissions required to give it.", ctx.channel)
            except Exception as e:
                general.print_error(f"{time.time()} > Levels on_message > {ctx.guild.name} ({ctx.guild.id}) > {type(e).__name__}: {e}")
            if lu or ld:
                try:
                    next_left = next_reward["level"] - level
                    level_up_message: str = __settings["leveling"]["level_up_message"]
                    if new_role:
                        if "level_up_role" in __settings["leveling"]:
                            if __settings["leveling"]["level_up_role"]:
                                level_up_message = __settings["leveling"]["level_up_role"]
                    if top_role:
                        if "level_up_highest" in __settings["leveling"]:
                            if __settings["leveling"]["level_up_highest"]:
                                level_up_message = __settings["leveling"]["level_up_highest"]
                    if level == max_level:
                        if "level_up_max" in __settings["leveling"]:
                            if __settings["leveling"]["level_up_max"]:
                                level_up_message = __settings["leveling"]["level_up_max"]
                    # This allows to fall back to the default level up message if the highest/max one isn't available
                    send = level_up_message\
                        .replace("[MENTION]", ctx.author.mention)\
                        .replace("[USER]", ctx.author.name)\
                        .replace("[LEVEL]", language.number(level))\
                        .replace("[CURRENT_REWARD]", current_reward["role"])\
                        .replace("[CURRENT_REWARD_LEVEL]", language.number(current_reward["level"]))\
                        .replace("[NEXT_REWARD]", next_reward["role"])\
                        .replace("[NEXT_REWARD_LEVEL]", language.number(next_reward["level"]))\
                        .replace("[NEXT_REWARD_PROGRESS]", language.number(next_left))\
                        .replace("[MAX_LEVEL]", language.number(max_level))
                except KeyError:
                    send = f"{ctx.author.mention} has reached **level {level:,}**! {emotes.ForsenDiscoSnake}"
                try:
                    ac = __settings["leveling"]["announce_channel"]
                    if ac == -1:  # -1 means level up announcements are disabled
                        ch = None
                    elif ac != 0:
                        ch = self.bot.get_channel(ac)
                        if ch is None or ch.guild.id != ctx.guild.id:
                            ch = ctx.channel
                    else:
                        ch = ctx.channel
                except KeyError:
                    ch = ctx.channel
                try:
                    if ch is not None:
                        await general.send(send, ch, u=[ctx.author])
                except discord.Forbidden:
                    pass  # Well, if it can't send it there, too bad.
            # _last = last if dc else now
            last_send = last if dc else now
            minute = now if full else ls
            if data:
                self.bot.db.execute(f"UPDATE leveling SET level=?, xp=?, last=?, last_sent=?, name=?, disc=?, {year!r}=? WHERE uid=? AND gid=?",
                                    (level, xp, last_send, minute, ctx.author.name, ctx.author.discriminator, yearly, ctx.author.id, ctx.guild.id))
            else:
                if xp != 0:
                    _2021, _2022 = yearly if year == "2021" else 0, yearly if year == "2022" else 0
                    self.bot.db.execute(f"INSERT INTO leveling VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                        (ctx.author.id, ctx.guild.id, level, xp, now, now, ctx.author.name, ctx.author.discriminator, _2021, _2022))
                # No point in saving data if XP is zero anyways...
            # No point in saving data if XP system is not enabled in the first place...

    @commands.command(name="rewards")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=15, type=commands.BucketType.user)
    async def rewards(self, ctx: commands.Context):
        """ Level rewards in a server """
        language = self.bot.language(ctx)
        _settings = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not _settings:
            return await general.send(language.string("leveling_rewards_none"), ctx.channel)
        else:
            data = json.loads(_settings['data'])
        try:
            rewards = data['leveling']['rewards']
            rewards.sort(key=lambda x: x['level'])
            embed = discord.Embed(colour=general.random_colour())
            embed.set_thumbnail(url=ctx.guild.icon_url_as(size=1024))
            embed.title = language.string("leveling_rewards_title", ctx.guild.name)
            d = ''
            for role in rewards:
                d += language.string("leveling_rewards_role", language.number(role["level"]), role["role"])
            if d:
                embed.description = d
            else:
                embed.description = language.string("leveling_rewards_none")
            return await general.send(None, ctx.channel, embed=embed)
        except KeyError:
            return await general.send(language.string("leveling_rewards_none"), ctx.channel)

    async def level(self, ctx: commands.Context, who: discord.Member or None, language: languages.Language):
        user = who or ctx.author
        is_self = user.id == self.bot.user.id
        if user.bot and not is_self:
            return await general.send(language.string("leveling_rank_bot"), ctx.channel)
        async with ctx.typing():
            data = self.bot.db.fetchrow(f"SELECT * FROM leveling WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
            # if key.isnumeric():
            #     r = language.string("leveling_rank_yearly", user, ctx.guild.name, key)
            #     if str(key) == "2021":
            #         cobble_servers = [568148147457490954, 738425418637639775, 58221533031156941, 662845241207947264]
            #         if ctx.guild.id not in cobble_servers:
            #             r += language.string("leveling_rank_yearly21", ctx.guild.name)
            # else:
            r = language.string("leveling_rank", user, ctx.guild.name)
            # if user.id in custom_rank_blacklist:
            #     custom = None
            #     # r += "\nCongrats on setting yourself to a rank card that makes the text invisible. Now enjoy the consequences of your actions. :^)"
            # else:
            custom = self.bot.db.fetchrow("SELECT * FROM custom_rank WHERE uid=?", (user.id,))
            if custom:
                font_colour, progress_colour, background_colour = \
                    get_colour(custom["font"]), get_colour(custom["progress"]), get_colour(custom["background"])
            else:
                font_colour, progress_colour, background_colour = (50, 255, 50), (50, 255, 50), 0
            if data:
                # try:
                xp = data["xp"]
                # except KeyError:
                #     return await general.send(language.string("leveling_rank_yearly_no", key), ctx.channel)
                # if key == "xp":
                level = data["level"]
                # else:
                #     level = 0
                #     for lvl in levels:
                #         if xp >= lvl:
                #             level += 1
                #         else:
                #             break
            else:
                level, xp = 0, 0
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
                r2 = language.number(req, precision=0)
            except IndexError:
                req = float("inf")
                r2 = language.string("generic_max")
            try:
                if level > 0:
                    prev = int(levels[level-1])
                elif level == 0:
                    prev = 0
                else:
                    prev = -int(levels[(-level) - 1])
            except IndexError:
                prev = 0
            _data = self.bot.db.fetch(f"SELECT * FROM leveling WHERE gid=? ORDER BY xp DESC", (ctx.guild.id,))
            place = language.string("leveling_rank_unknown")
            for x in range(len(_data)):
                if _data[x]['uid'] == user.id:
                    place = language.string("leveling_rank_rank", language.string("leaderboards_place", language.number(x + 1)))
                    break
            if not is_self:
                progress = (xp - prev) / (req - prev)
                _level = language.string("leveling_rank_level", language.number(level))
                dr.text((text_x, 130), f"{place} | {_level} ", font=font_small, fill=font_colour)
                r1 = language.number(xp, precision=0)
                if level < max_level:
                    r3 = language.string("leveling_rank_progress", language.number(progress, precision=2, percentage=True))
                    r4 = language.string("leveling_rank_xp_left", language.number((req - xp), precision=0))
                    y = 288
                else:
                    progress = 1
                    r3, r4 = language.string("leveling_rank_max_1"), random.choice(language.data("leveling_rank_max_2"))
                    y = 288
                    # y = 426
                dr.text((text_x, y), language.string("leveling_rank_xp", r1, r2, r3, r4), font=font_small, fill=font_colour)
            else:
                progress = 1  # 0.5
                place = language.string("leaderboards_place", 1)
                _rank = language.string("leveling_rank_rank", place)
                _level = language.string("leveling_rank_level", language.number(69420))
                dr.text((text_x, 130), f"{_rank} | {_level}", font=font_small, fill=font_colour)
                dr.text((text_x, 357), language.string("leveling_rank_xp_self"), font=font_small, fill=font_colour)  # 426
            full = width - 20
            done = int(progress * full)
            if done < 0:
                done = 0
            i1 = Image.new("RGB", (width, 100), color=progress_colour)
            i2 = Image.new("RGB", (width - 10, 90), color=(30, 30, 30))
            i3 = Image.new("RGB", (done, 80), color=progress_colour)
            box1, box2, box3 = (0, 512), (5, 517), (10, 522)
            # box1 = (0, 512, width, 612)
            # box2 = (5, 517, width - 5, 607)  # 2 px bigger
            # box3 = (10, 522, done, 602)
            img.paste(i1, box1)
            img.paste(i2, box2)
            img.paste(i3, box3)
            bio = BytesIO()
            img.save(bio, "PNG")
            bio.seek(0)
            return await general.send(r, ctx.channel, file=discord.File(bio, filename="rank.png"))

    @commands.command(name="rank", aliases=["level", "xp"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def rank_image(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Check your or someone's rank """
        language = self.bot.language(ctx)
        return await self.level(ctx, who, language)

    @commands.command(name="ranklang", aliases=["rank4"], hidden=True)
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def rank_language(self, ctx: commands.Context, language: str, *, who: discord.Member = None):
        """ Check your or someone's rank - In a different language """
        _language = self.bot.language2(language)
        if language not in languages.languages.keys():
            return await general.send(self.bot.language(ctx).string("settings_locale_invalid", language, ctx.prefix), ctx.channel)
        return await self.level(ctx, who, _language)

    @commands.command(name="rankembed", aliases=["rank2", "ranke"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def rank_embed(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Check your or someone's rank - as an embed """
        language = self.bot.language(ctx)
        user = who or ctx.author
        is_self = user.id == self.bot.user.id
        if user.bot and not is_self:
            return await general.send(language.string("leveling_rank_bot"), ctx.channel)
        data = self.bot.db.fetchrow(f"SELECT * FROM leveling WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        r = language.string("leveling_rank", user, ctx.guild.name)
        if data:
            level, xp = [data['level'], data['xp']]
        else:
            level, xp = [0, 0]
        _settings = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if _settings:
            __settings = json.loads(_settings['data'])
            try:
                sm = __settings['leveling']['multiplier']
            except KeyError:
                sm = 1
        else:
            sm = 1
        embed = discord.Embed(colour=general.random_colour(), title=r)
        embed.set_thumbnail(url=user.avatar_url_as(size=512, format="png"))
        # dr.text((text_x, -10), f"{user}", font=font, fill=font_colour)
        try:
            if level >= 0:
                req = int(levels[level])  # Requirement to next level
            elif level == -1:
                req = 0
            else:
                req = int(-levels[(-level) - 2])
            r2 = language.number(req, precision=0)
        except IndexError:
            req = float("inf")
            r2 = language.string("generic_max")
        try:
            if level > 0:
                prev = int(levels[level - 1])
            elif level == 0:
                prev = 0
            else:
                prev = -int(levels[(-level) - 1])
        except IndexError:
            prev = 0
        _data = self.bot.db.fetch(f"SELECT * FROM leveling WHERE gid=? ORDER BY xp DESC", (ctx.guild.id,))
        place = language.string("leveling_rank_unknown")
        # if user.id == 430891116318031872:  # Alex Five is always fifth
        #     place = langs.gls("leveling_rank_rank", locale, langs.gls("leaderboards_place", locale, f"**{langs.gns(5, locale)}**"))
        # else:
        for x in range(len(_data)):
            if _data[x]['uid'] == user.id:
                place = language.string("leveling_rank_rank", language.string("leaderboards_place", general.bold(language.number(x + 1))))
                break
        if not is_self:
            progress = (xp - prev) / (req - prev)
            _level = language.string("leveling_rank_level", general.bold(language.number(level)))
            r1 = language.number(xp, precision=0)
            r3 = language.number(progress, precision=2, percentage=True)
            r4 = language.string("leveling_rank_xp_left", language.number((req - xp)))
            embed.add_field(name=language.string("leveling_rank_embed_xp"), value=f"**{r1}**/{r2}", inline=False)
            embed.add_field(name=language.string("leveling_rank_embed_level"), value=_level, inline=False)
            embed.add_field(name=language.string("leveling_rank_embed_rank"), value=place, inline=False)
            if level < max_level:
                embed.add_field(name=language.string("leveling_rank_embed_progress"), value=f"**{r3}**{r4}", inline=False)
        else:
            # place = languages.gls("leaderboards_place", locale, languages.gns(1, locale))
            _rank = language.string("leveling_rank_rank", language.string("leaderboards_place", "**1**"))
            _level = language.string("leveling_rank_level", language.number(69420))
            embed.add_field(name=language.string("leveling_rank_embed_xp"), value=language.string("leveling_rank_xp_self"), inline=False)
            embed.add_field(name=language.string("leveling_rank_embed_level"), value=_level, inline=False)
            embed.add_field(name=language.string("leveling_rank_embed_rank"), value=_rank, inline=False)
        x1, x2 = [val * sm for val in xp_amounts]
        o1, o2 = int(x1), int(x2)
        embed.add_field(name=language.string("leveling_rank_embed_rate"), value=f"{o1}-{o2}", inline=False)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="rankyearly", aliases=["rank3", "ranky", "rankyear"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def rank_yearly(self, ctx: commands.Context, year: int = None, *, who: discord.Member = None):
        """ Check someone's activity during a certain year """
        if not year:
            year = time.now(None).year
        language = self.bot.language(ctx)
        # return await self.level(ctx, who, locale, str(year))
        user = who or ctx.author
        if user.bot:
            return await general.send(language.string("leveling_rank_bot"), ctx.channel)
        data = self.bot.db.fetchrow(f"SELECT * FROM leveling WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if data:
            try:
                xp = data[str(year)]
            except KeyError:
                return await general.send(language.string("leveling_rank_yearly_no", year), ctx.channel)
            level = 0
            for lvl in levels:
                if xp >= lvl:
                    level += 1
                else:
                    break
        else:
            return await general.send(language.string("leveling_rank_none", ctx.author, year), ctx.channel)
        _data = self.bot.db.fetch(f"SELECT * FROM leveling WHERE gid=? ORDER BY \"{year}\" DESC", (ctx.guild.id,))
        place = language.string("generic_unknown")
        for x in range(len(_data)):
            if _data[x]['uid'] == user.id:
                place = language.string("leaderboards_place", language.number(x + 1))
                break
        r1 = language.number(xp, precision=0)
        r2 = language.number(level)

        output = language.string("leveling_rank_yearly", user, ctx.guild.name, year, r1, r2, place)
        if str(year) == "2021":
            cobble_servers = [568148147457490954, 738425418637639775, 58221533031156941, 662845241207947264]
            if ctx.guild.id not in cobble_servers:
                output += language.string("leveling_rank_yearly21", ctx.guild.name)
        return await general.send(output, ctx.channel)

    @commands.command(name="rankglobal", aliases=["rankg", "grank"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def rank_global(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check your or someone's global XP """
        language = self.bot.language(ctx)
        user = who or ctx.author
        # is_self = user.id == self.bot.user.id
        if user.bot:
            return await general.send(language.string("leveling_rank_bot"), ctx.channel)
        _data = self.bot.db.fetch(f"SELECT * FROM leveling")
        coll = {}
        for i in _data:
            if i['uid'] not in coll:
                coll[i['uid']] = 0
            coll[i['uid']] += i['xp']
        sl = sorted(coll.items(), key=lambda a: a[1], reverse=True)
        # r = len(sl)
        # xp = []
        # for thing in sl:
        #     xp.append(thing[1])
        place = language.string("generic_unknown")
        xp = 0
        for i, _user in enumerate(sl):
            uid, _xp = _user
            if uid == user.id:
                place = language.string("leaderboards_place", language.number(i + 1))
                xp = _xp
                break
        level = 0
        for lvl in levels:
            if xp >= lvl:
                level += 1
            else:
                break
        # __xp = int(_xp)
        return await general.send(language.string("leveling_rank_global", user, language.number(xp, precision=0), place, language.number(level)), ctx.channel)

    @commands.group(name="customrank", aliases=["crank"])
    # @commands.check(lambda ctx: ctx.author.id not in custom_rank_blacklist)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def custom_rank(self, ctx: commands.Context):
        """ Customise your rank card """
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
        language = self.bot.language(ctx)
        if level > max_level or level < max_level * -1 + 1:
            return await general.send(language.string("leveling_xplevel_max", language.number(max_level)), ctx.channel)
        try:
            if level > 0:
                r = int(levels[level - 1])
            elif level == 0:
                r = 0
            else:
                r = -int(levels[(-level) - 1])
        except IndexError:
            return await general.send(language.string("leveling_xplevel_max", language.number(max_level)), ctx.channel)
        if ctx.guild is not None:
            data = self.bot.db.fetchrow(f"SELECT * FROM leveling WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
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
        base = language.string("leveling_xplevel_main", language.number(r, precision=0), language.number(level))
        extra = ""
        if xp < r:
            x1, x2 = [val * dm for val in xp_amounts]
            a1, a2 = [(r - xp) / x2, (r - xp) / x1]
            try:
                t1, t2 = [language.delta_int(x * 60, accuracy=3, brief=True, affix=False) for x in [a1, a2]]
            except (OverflowError, OSError):
                error = "Never"
                t1, t2 = [error, error]
            extra = language.string("leveling_xplevel_extra", language.number(r - xp, precision=0), t1, t2)
        return await general.send(f"{base}{extra}", ctx.channel)

    @commands.command(name="nextlevel", aliases=["nl"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def next_level(self, ctx: commands.Context):
        """ XP required for next level """
        language = self.bot.language(ctx)
        data = self.bot.db.fetchrow(f"SELECT * FROM leveling WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not data:
            return await general.send(language.string("leveling_next_level_none"), ctx.channel)
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
            return await general.send(language.string("leveling_next_level_max", ctx.author.name), ctx.channel)
        r1 = language.number(xp, precision=0)
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
        r2, r3, r4 = language.number(r), language.number(req), language.number(pr if pr < 1 else 1, precision=1, percentage=True)
        r5 = language.number(level + 1)
        normal = 1
        x1, x2 = [val * normal * dm for val in xp_amounts]
        a1, a2 = [(r - xp) / x2, (r - xp) / x1]
        try:
            t1, t2 = [language.delta_int(x * 60, accuracy=3, brief=True, affix=False) for x in [a1, a2]]
        except (OverflowError, OSError):
            error = "Never"
            t1, t2 = [error, error]
        return await general.send(language.string("leveling_next_level", ctx.author.name, r1, r2, r3, r5, r4, t1, t2), ctx.channel)

    @commands.command(name="levels", aliases=["ranks", "lb"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def levels_lb(self, ctx: commands.Context, top: str = ""):
        """ Server's XP Leaderboard """
        language = self.bot.language(ctx)
        return await leaderboard(self, ctx, f"SELECT * FROM leveling WHERE gid=? ORDER BY xp DESC", (ctx.guild.id,),
                                 top, "leaderboards_levels", language, "xp", ctx.guild.name)

    @commands.command(name="levelsyear", aliases=["ranksyear", "levelsy", "ylevels", "lby", "levels3"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def levels_lb_yearly(self, ctx: commands.Context, year: int = None, top: str = ""):
        """ Server's Yearly XP Leaderboard """
        if not year:
            year = time.now(None).year
        language = self.bot.language(ctx)
        return await leaderboard(self, ctx, f"SELECT * FROM leveling WHERE gid=? AND \"{year}\"!=0 ORDER BY \"{year}\" DESC", (ctx.guild.id,),
                                 top, "leaderboards_levels_yearly", language, str(year), ctx.guild.name)

    @commands.command(name="levelsglobal", aliases=["levelsg", "glevels"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def global_levels(self, ctx: commands.Context, top: str = ""):
        """ Global XP Leaderboard """
        language = self.bot.language(ctx)
        return await leaderboard2(self, ctx, f"SELECT * FROM leveling", (), top, "leaderboards_levels_global", language, "xp")


def setup(bot: bot_data.Bot):
    bot.add_cog(Leveling(bot))
