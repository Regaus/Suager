from __future__ import annotations

import json
import random
from io import BytesIO
from typing import Literal

import discord
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from utils import bot_data, commands, emotes, general, http, images, languages, logger, settings, time
from utils.leaderboards import leaderboard, leaderboard2


async def catch_colour(ctx: commands.Context, c: int):
    if c == -1:
        await ctx.send("Value must be either 3 or 6 digits long")
    if c == -2:
        await ctx.send("An error occurred. Are you sure the value is HEX (0-9 and A-F)?")
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

sql_server = "SELECT uid, name, disc, (xp*APRILMULT())xp FROM leveling WHERE gid=? AND bot=? ORDER BY xp DESC"
sql_global = "SELECT uid, name, disc, (xp*APRILMULT())xp FROM leveling WHERE bot=?"


class Leveling(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

        # Default colours and font for custom ranks
        # Note: when saving to the database, the default values are null, in case they ever get changed
        self.default_text = 0x32ff32
        self.default_progress = 0x32ff32
        self.default_background = 0x000000
        self.default_font = "whitney"
        # Blocked from custom rank: Caffey,
        self.blocked = []  # 249141823778455552

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
        return await ctx.send(f"```fix\n{output}```")

    @commands.command(name="oldlevels", aliases=["levelhistory"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def old_levels(self, ctx: commands.Context, level: int = None):
        """ See Suager's previous leveling systems """
        names = {"v3": "Suager v3", "v4": "Suager v4", "v5": "Suager v5", "v6": "Suager v6", "v7": "Suager v7"}
        if level is not None:
            if level > max_level:
                return await ctx.send(f"The max level is {max_level:,}")
            output = ""
            for key, name in names.items():
                output += f"\n`{name:<9} -> {level_history[key][level - 1]:>9,.0f} XP`"
            return await ctx.send(f"{general.username(ctx.author)}, for **level {level}** you would've needed:{output}")
        else:
            xp_ = self.bot.db.fetchrow(f"SELECT xp FROM leveling WHERE uid=? AND gid=? AND bot=?", (ctx.author.id, ctx.guild.id, self.bot.name))
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
            return await ctx.send(f"{general.username(ctx.author)}, you have **{xp:,} XP** in this server. Here are the levels you would have been on in the older leveling systems:{output}")

    @commands.Cog.listener()
    async def on_message(self, ctx: discord.Message):
        if self.bot.name == "cobble":
            return
        if ctx.author.bot or ctx.guild is None:
            return
        if ctx.content == "" and ctx.type != discord.MessageType.default:
            return
        _settings = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
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
                xp_disabled = True  # If the settings are somehow broken, do nothing
        else:
            __settings = settings.template_suager.copy()
            xp_disabled = True

        if xp_disabled:  # Why did we even need to execute any of the previous code if leveling is disabled???
            return

        # Load current data, or set everything to zeros
        data = self.bot.db.fetchrow(f"SELECT * FROM leveling WHERE uid=? AND gid=? AND bot=?", (ctx.author.id, ctx.guild.id, self.bot.name))
        if data:
            level, xp, last, ls = data['level'], data['xp'], data['last'], data['last_sent']
        else:
            level, xp, last, ls = 0, 0, 0, 0
        if ls is None:
            ls = 0

        # Determine time multiplier
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

        # Server multiplier
        try:
            server_mult = float(__settings['leveling']['xp_multiplier'])
        except KeyError:
            server_mult = 1
        # Extra multipliers
        extra = 1
        if ctx.guild.id == 568148147457490954:  # Senko Lair
            if 571034926107852801 in [role.id for role in ctx.author.roles]:  # if muted
                extra *= 0.25
        elif ctx.author.id == 592345932062916619:  # Egzorcysta
            extra = 0

        x1, x2 = xp_amounts
        new = int(random.uniform(x1, x2) * server_mult * mult * extra)

        xp += new
        # yearly += new
        # old_level = level

        # Level up/down
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

        if ctx.author.id == 430891116318031872 and level >= 5:  # Alex five stays on level 5
            lu, ld = False, False
            level = 5

        # Handle level rewards
        reason = f"Level Rewards - Level {level}"
        language = self.bot.language(commands.FakeContext(ctx.guild, self.bot))
        current_reward, next_reward = {"role": language.string("generic_none"), "level": 0}, {"role": language.string("generic_unknown"), "level": 0}
        top_role = False
        new_role = False
        try:
            rewards = __settings['leveling']['rewards']
            if rewards:  # Don't bother if they're empty
                rewards.sort(key=lambda x: x['level'])
                nr: discord.Role = ctx.guild.get_role(rewards[0]["role"])
                next_reward = {"role": nr.name if nr is not None else language.string("generic_unknown"), "level": rewards[0]["level"]}
                roles = [r.id for r in ctx.author.roles]
                for i, reward in enumerate(rewards):
                    role: discord.Role = ctx.guild.get_role(reward["role"])  # discord.Object(id=l2[i])
                    if role is None:
                        continue  # Skip the role
                    has_role = reward["role"] in roles
                    if level >= reward["level"]:
                        if i < len(rewards) - 1:
                            next_role = rewards[i + 1]
                            if level < next_role["level"]:
                                current_reward = {"role": role.name, "level": reward["level"]}
                                nr = ctx.guild.get_role(next_role["role"])
                                next_reward = {"role": nr.name if nr is not None else language.string("generic_unknown"), "level": next_role["level"]}
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
        except AttributeError:  # This means a role was deleted and somehow didn't get skipped...
            pass
        except discord.Forbidden:
            await ctx.channel.send(f"{general.username(ctx.author)} should receive a level reward right now, but I don't have permissions required to give it.")
        except Exception as e:
            out = f"{time.time()} > Levels on_message > {ctx.guild.name} ({ctx.guild.id}) > {type(e).__name__}: {e}"
            general.print_error(out)
            logger.log(self.bot.name, "errors", out)

        # Handle level ups
        if lu or ld:
            _af = -1 if time.april_fools() else 1
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
                    .replace("[USER]", general.username(ctx.author))\
                    .replace("[LEVEL]", language.number(level * _af))\
                    .replace("[CURRENT_REWARD]", current_reward["role"])\
                    .replace("[CURRENT_REWARD_LEVEL]", language.number(current_reward["level"] * _af))\
                    .replace("[NEXT_REWARD]", next_reward["role"])\
                    .replace("[NEXT_REWARD_LEVEL]", language.number(next_reward["level"] * _af))\
                    .replace("[NEXT_REWARD_PROGRESS]", language.number(next_left * _af))\
                    .replace("[MAX_LEVEL]", language.number(max_level))
            except KeyError:
                send = f"{ctx.author.mention} has reached **level {level * _af:,}**! {emotes.ForsenDiscoSnake}"
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
                    await ch.send(send)
            except discord.Forbidden:
                pass  # Well, if it can't send it there, too bad.

        # Save data
        last_send = last if dc else now
        minute = now if full else ls

        if data:
            self.bot.db.execute("UPDATE leveling SET level=?, xp=?, last=?, last_sent=?, name=?, disc=? WHERE uid=? AND gid=? AND bot=?",
                                (level, xp, last_send, minute, general.username(ctx.author), str(ctx.author), ctx.author.id, ctx.guild.id, self.bot.name))
        else:
            if xp != 0:  # No point in saving data if XP is zero...
                self.bot.db.execute(f"INSERT INTO leveling VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                    (ctx.author.id, ctx.guild.id, level, xp, now, now, general.username(ctx.author), str(ctx.author), self.bot.name))

    @commands.command(name="rewards")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=15, type=commands.BucketType.user)
    async def rewards(self, ctx: commands.Context):
        """ Level rewards in a server """
        language = self.bot.language(ctx)
        _af = -1 if time.april_fools() else 1
        _settings = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if not _settings:
            return await ctx.send(language.string("leveling_rewards_none"))
        else:
            data = json.loads(_settings['data'])
        try:
            rewards = data['leveling']['rewards']
            rewards.sort(key=lambda x: x['level'])
            embed = discord.Embed(colour=general.random_colour())
            if ctx.guild.icon:
                embed.set_thumbnail(url=str(ctx.guild.icon.replace(size=1024, static_format="png")))
            embed.title = language.string("leveling_rewards_title", server=ctx.guild.name)
            d = ''
            for role in rewards:
                d += language.string("leveling_rewards_role", level=language.number(role["level"] * _af), role_id=role["role"])
            if d:
                embed.description = d
            else:
                embed.description = language.string("leveling_rewards_none")
            return await ctx.send(embed=embed)
        except KeyError:
            return await ctx.send(language.string("leveling_rewards_none"))

    async def level(self, ctx: commands.Context, who: discord.Member | None, language: languages.Language):
        """ Wrapper for image rank card commands """
        user = who or ctx.author
        is_self = user.id == self.bot.user.id
        if user.bot and not is_self:
            return await ctx.send(language.string("leveling_rank_bot"))
        _af = -1 if time.april_fools() else 1

        async with ctx.typing():
            data = self.bot.db.fetchrow(f"SELECT * FROM leveling WHERE uid=? AND gid=? AND bot=?", (user.id, ctx.guild.id, self.bot.name))
            r = language.string("leveling_rank", user=general.username(user), server=ctx.guild.name)
            # Load custom rank data from database
            custom = self.bot.db.fetchrow("SELECT * FROM custom_rank WHERE uid=?", (user.id,))
            if not custom or user.id in self.blocked:
                text, progress, background, font_name = None, None, None, None
            else:
                text: int | None = custom["font"]
                progress: int | None = custom["progress"]
                background: int | None = custom["background"]
                font_name: str | None = custom["custom_font"]
            # Fill with default values
            if text is None:
                text = self.default_text
            if progress is None:
                progress = self.default_progress
            if background is None:
                background = self.default_background
            if font_name is None:
                font_name = self.default_font
            # Load font file and interpret colours into tuples
            font_colour = get_colour(text)
            progress_colour = get_colour(progress)
            background_colour = get_colour(background)
            font_dir = images.font_files.get(font_name, images.font_files[self.default_font])  # Back up by default font in case the custom font is ever deleted
            # Load leveling data
            if data:
                xp = data["xp"]
                level = data["level"]
            else:
                level, xp = 0, 0
            # Image setup
            width = 2048
            img = Image.new("RGB", (width, 612), color=background_colour)
            dr = ImageDraw.Draw(img)
            # Get the user's avatar
            try:
                avatar = BytesIO(await http.get(str(user.display_avatar.replace(size=512, format="png")), res_method="read"))
                avatar_img = Image.open(avatar)
                avatar_resized = avatar_img.resize((512, 512))
                img.paste(avatar_resized)
            except UnidentifiedImageError:  # Failed to get image
                avatar = Image.open("assets/error.png")
                img.paste(avatar)
            # Set up font
            try:
                font = ImageFont.truetype(font_dir, size=128)
                font_small = ImageFont.truetype(font_dir, size=64)
            except ImportError:
                await ctx.send(f"{emotes.Deny} It seems that image generation does not work properly here...")
                font, font_small = None, None
            # Write user's name to the top of the rank card
            text_x = 542
            dr.text((text_x, -10), general.username(user), font=font, fill=font_colour)
            # Calculate XP required to reach the next level
            try:
                if level >= 0:
                    req = int(levels[level])  # Requirement to next level
                elif level == -1:
                    req = 0
                else:
                    req = int(-levels[(-level) - 2])
                r2 = language.number(req * _af, precision=0)
            except IndexError:
                req = float("inf")
                r2 = language.string("generic_max")
            # Calculate XP required to reach the current level
            try:
                if level > 0:
                    prev = int(levels[level-1])
                elif level == 0:
                    prev = 0
                else:
                    prev = -int(levels[(-level) - 1])
            except IndexError:
                prev = 0
            # Get the user's rank within the current server
            _data = self.bot.db.fetch(sql_server, (ctx.guild.id, self.bot.name))
            place = language.string("leveling_rank_unknown")
            for x in range(len(_data)):
                if _data[x]['uid'] == user.id:
                    place = language.string("leveling_rank_rank", place=language.string("leaderboards_place", val=language.number((x + 1) * _af)), total=language.number(len(_data)))
                    break
            # Draw the details of the rank card (rank, level, XP amounts)
            text_y = 512  # 495
            if not is_self:
                progress = (xp - prev) / (req - prev)
                _level = language.string("leveling_rank_level", level=language.number(level * _af))
                dr.text((text_x, 130), f"{place} | {_level}", font=font_small, fill=font_colour)
                r1 = language.number(xp * _af, precision=0)
                if level < max_level:
                    # Remove the zero-width spaces from the progress text
                    r3 = language.string("leveling_rank_progress", progress=language.number(progress, precision=2, percentage=True).replace("\u200c", ""))
                    r4 = language.string("leveling_rank_xp_left", left=language.number((req - xp) * _af, precision=0))
                else:
                    progress = 1
                    r3, r4 = language.string("leveling_rank_max_1"), random.choice(language.data("leveling_rank_max_2"))
                dr.text((text_x, text_y), language.string("leveling_rank_xp", xp=r1, next=r2, progress=r3, left=r4), font=font_small, fill=font_colour, anchor="ld")
            else:
                progress = 1  # 0.5
                place = language.string("leaderboards_place", val=1)
                _rank = language.string("leveling_rank_rank2", place=place)
                _level = language.string("leveling_rank_level", level=language.number(69420))
                dr.text((text_x, 130), f"{_rank} | {_level}", font=font_small, fill=font_colour)
                dr.text((text_x, text_y), language.string("leveling_rank_xp_self"), font=font_small, fill=font_colour, anchor="ld")
            # Draw progress bar
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
            # Save image and return it
            bio = BytesIO()
            img.save(bio, "PNG")
            bio.seek(0)
            return await ctx.send(r, file=discord.File(bio, filename="rank.png"))

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
        if language not in languages.languages.languages.keys():
            return await ctx.send(self.bot.language(ctx).string("settings_locale_invalid", language=language, p=ctx.prefix))
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
            return await ctx.send(language.string("leveling_rank_bot"))
        _af = -1 if time.april_fools() else 1
        data = self.bot.db.fetchrow(f"SELECT * FROM leveling WHERE uid=? AND gid=? AND bot=?", (user.id, ctx.guild.id, self.bot.name))
        r = language.string("leveling_rank", user=general.username(user), server=ctx.guild.name)
        if data:
            level, xp = [data['level'], data['xp']]
        else:
            level, xp = [0, 0]
        _settings = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if _settings:
            __settings = json.loads(_settings['data'])
            try:
                sm = __settings['leveling']['xp_multiplier']
            except KeyError:
                sm = 1
        else:
            sm = 1
        embed = discord.Embed(colour=general.random_colour(), title=r)
        embed.set_thumbnail(url=str(user.display_avatar.replace(size=512, format="png")))
        try:
            if level >= 0:
                req = int(levels[level])  # Requirement to next level
            elif level == -1:
                req = 0
            else:
                req = int(-levels[(-level) - 2])
            r2 = language.number(req * _af, precision=0, zws_end=True)
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
        _data = self.bot.db.fetch(sql_server, (ctx.guild.id, self.bot.name))
        place = language.string("leveling_rank_unknown")
        for x in range(len(_data)):
            if _data[x]['uid'] == user.id:
                place = language.string("leveling_rank_rank", place=general.bold(language.string("leaderboards_place", val=language.number((x + 1) * _af))), total=language.number(len(_data)))
                break
        if not is_self:
            progress = (xp - prev) / (req - prev)
            _level = language.string("leveling_rank_level", level=general.bold(language.number(level * _af)))
            r1 = language.number(xp * _af, precision=0, zws_end=True)
            r3 = language.number(progress, precision=2, percentage=True)
            r4 = language.string("leveling_rank_xp_left", left=language.number((req - xp) * _af))
            embed.add_field(name=language.string("leveling_rank_embed_xp"), value=f"**{r1}**/{r2}", inline=False)
            embed.add_field(name=language.string("leveling_rank_embed_level"), value=_level, inline=False)
            embed.add_field(name=language.string("leveling_rank_embed_rank"), value=place, inline=False)
            if level < max_level:
                embed.add_field(name=language.string("leveling_rank_embed_progress"), value=f"**{r3}**\n{r4}", inline=False)
        else:
            _rank = language.string("leveling_rank_rank2", place=general.bold(language.string("leaderboards_place", val="1")))
            _level = language.string("leveling_rank_level", level=language.number(69420))
            embed.add_field(name=language.string("leveling_rank_embed_xp"), value=language.string("leveling_rank_xp_self"), inline=False)
            embed.add_field(name=language.string("leveling_rank_embed_level"), value=_level, inline=False)
            embed.add_field(name=language.string("leveling_rank_embed_rank"), value=_rank, inline=False)
        x1, x2 = [val * sm for val in xp_amounts]
        o1, o2 = int(x1), int(x2)
        embed.add_field(name=language.string("leveling_rank_embed_rate"), value=f"{o1}-{o2}", inline=False)
        return await ctx.send(embed=embed)

    @commands.command(name="rankglobal", aliases=["rankg", "grank"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def rank_global(self, ctx: commands.Context, *, who: discord.User = None):
        """ Check your or someone's global XP """
        language = self.bot.language(ctx)
        user = who or ctx.author
        if user.bot:
            return await ctx.send(language.string("leveling_rank_bot"))
        _af = -1 if time.april_fools() else 1
        _data = self.bot.db.fetch(sql_global, (self.bot.name,))
        coll = {}
        for i in _data:
            if i['uid'] not in coll:
                coll[i['uid']] = 0
            coll[i['uid']] += i['xp']
        sl = sorted(coll.items(), key=lambda a: a[1], reverse=True)
        place = language.string("generic_unknown")
        xp = 0
        for i, _user in enumerate(sl):
            uid, _xp = _user
            if uid == user.id:
                place = language.string("leaderboards_place", val=language.number((i + 1) * _af))
                xp = _xp
                break
        level = 0
        for lvl in levels:
            if xp * _af >= lvl:
                level += 1
            else:
                break
        return await ctx.send(language.string("leveling_rank_global", user=user, xp=language.number(xp, precision=0), place=place, level=language.number(level * _af)))

    @commands.group(name="customrank", aliases=["crank"])
    # @commands.check(lambda ctx: ctx.author.id not in custom_rank_blacklist)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def custom_rank(self, ctx: commands.Context):
        """ Customise your rank card
        Change the colour of the text, the background, progress bar. You can also choose a font to use."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @custom_rank.command(name="text", aliases=["fontcolour", "font2"])
    async def crank_font_colour(self, ctx: commands.Context, colour: str):
        """ Font colour - Provide a hex colour (6-letter rgb code) """
        c = int_colour(colour)
        cc = await catch_colour(ctx, c)
        if cc:
            data = self.bot.db.fetchrow("SELECT * FROM custom_rank WHERE uid=?", (ctx.author.id,))
            if data:
                self.bot.db.execute("UPDATE custom_rank SET font=? WHERE uid=?", (c, ctx.author.id))
            else:
                self.bot.db.execute("INSERT INTO custom_rank VALUES (?, ?, ?, ?, ?)", (ctx.author.id, c, None, None, None))
            return await ctx.send(f"Set your font colour to #{colour}")

    @custom_rank.command(name="progress")
    async def crank_progress(self, ctx: commands.Context, colour: str):
        """ Progress bar colour - Provide a hex colour (6-letter rgb code) """
        c = int_colour(colour)
        cc = await catch_colour(ctx, c)
        if cc:
            data = self.bot.db.fetchrow("SELECT * FROM custom_rank WHERE uid=?", (ctx.author.id,))
            if data:
                self.bot.db.execute("UPDATE custom_rank SET progress=? WHERE uid=?", (c, ctx.author.id))
            else:
                self.bot.db.execute("INSERT INTO custom_rank VALUES (?, ?, ?, ?, ?)", (ctx.author.id, None, c, None, None))
            return await ctx.send(f"Set your progress bar colour to #{colour}")

    @custom_rank.command(name="background", aliases=["bg"])
    async def crank_bg(self, ctx: commands.Context, colour: str):
        """ Background colour - Provide a hex colour (6-letter rgb code) """
        c = int_colour(colour)
        cc = await catch_colour(ctx, c)
        if cc:
            data = self.bot.db.fetchrow("SELECT * FROM custom_rank WHERE uid=?", (ctx.author.id,))
            if data:
                self.bot.db.execute("UPDATE custom_rank SET background=? WHERE uid=?", (c, ctx.author.id))
            else:
                self.bot.db.execute("INSERT INTO custom_rank VALUES (?, ?, ?, ?, ?)", (ctx.author.id, None, None, c, None))
            return await ctx.send(f"Set your background colour to #{colour}")

    @custom_rank.command(name="font", aliases=["customfont", "font1"])
    async def crank_font(self, ctx: commands.Context, *, font: str = None):
        """ Change the font used in your rank card
        Leave empty to see list of valid fonts"""
        if font is not None:
            font = font.lower()  # Font names are not case-sensitive
        valid_fonts = list(images.font_files.keys())
        if font == "-i":
            message = "This is how the currently available fonts look.\n" \
                      "The first row is the font name.\nThe second row shows sample text in English.\n" \
                      "The third row shows sample text in Russian.\nThe last row shows numbers and special characters."
            bio = images.font_tester()
            return await ctx.send(message, file=discord.File(bio, filename="fonts.png"))
        if font not in valid_fonts:  # This includes if the font is not specified
            message = f"No font was specified or an invalid font was passed.\n" \
                      f"The currently available fonts are: `{'`, `'.join(list(images.font_files))}`\n" \
                      f"Type the name of the font you want to use with this command to set it.\n" \
                      f"The default font is `{self.default_font}`.\n" \
                      f"Type `{ctx.prefix}crank font -i` to see how these fonts look."
            return await ctx.send(message)
        data = self.bot.db.fetchrow("SELECT * FROM custom_rank WHERE uid=?", (ctx.author.id,))
        if data:
            self.bot.db.execute("UPDATE custom_rank SET custom_font=? WHERE uid=?", (font, ctx.author.id))
        else:
            self.bot.db.execute("INSERT INTO custom_rank VALUES (?, ?, ?, ?, ?)", (ctx.author.id, None, None, None, font))
        return await ctx.send(f"Set your rank card font to `{font}`.")

    @commands.command(name="xplevel")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def xp_level(self, ctx: commands.Context, level: int):
        """ XP required to achieve a level """
        language = self.bot.language(ctx)
        _af = -1 if time.april_fools() else 1
        if level > max_level or level < max_level * -1 + 1:
            return await ctx.send(language.string("leveling_xplevel_max", level=language.number(max_level)))
        try:
            if level > 0:
                r = int(levels[level - 1])
            elif level == 0:
                r = 0
            else:
                r = -int(levels[(-level) - 1])
        except IndexError:
            return await ctx.send(language.string("leveling_xplevel_max", level=language.number(max_level)))
        if ctx.guild is not None:
            data = self.bot.db.fetchrow(f"SELECT * FROM leveling WHERE uid=? AND gid=? AND bot=?", (ctx.author.id, ctx.guild.id, self.bot.name))
        else:
            data = None
        if not data:
            xp = float("inf")
        else:
            xp = data['xp']
        _settings = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if not _settings:
            dm = 1
        else:
            __settings = json.loads(_settings['data'])
            try:
                dm = __settings['leveling']['xp_multiplier']
            except KeyError:
                dm = 1
        base = language.string("leveling_xplevel_main", xp=language.number(r * _af, precision=0), level=language.number(level * _af))
        extra = ""
        if xp < r:
            x1, x2 = [val * dm for val in xp_amounts]
            a1, a2 = [(r - xp) / x2, (r - xp) / x1]
            try:
                t1, t2 = [language.delta_int(x * 60, accuracy=3, brief=True, affix=False) for x in [a1, a2]]
            except (OverflowError, OSError):
                error = "Never"
                t1, t2 = [error, error]
            extra = language.string("leveling_xplevel_extra", left=language.number((r - xp) * _af, precision=0), min=t1, max=t2)
        return await ctx.send(f"{base}{extra}")

    @commands.command(name="nextlevel", aliases=["nl"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def next_level(self, ctx: commands.Context):
        """ XP required for next level """
        language = self.bot.language(ctx)
        _af = -1 if time.april_fools() else 1
        data = self.bot.db.fetchrow(f"SELECT * FROM leveling WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not data:
            return await ctx.send(language.string("leveling_next_level_none"))
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
            return await ctx.send(language.string("leveling_next_level_max", user=general.username(ctx.author)))
        r1 = language.number(xp * _af, precision=0)
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
        r2, r3, r4 = language.number(r * _af, zws_end=True), language.number(req * _af, zws_end=True), language.number(pr if pr < 1 else 1, precision=1, percentage=True)
        r5 = language.number((level + 1) * _af)
        normal = 1
        x1, x2 = [val * normal * dm for val in xp_amounts]
        a1, a2 = [(r - xp) / x2, (r - xp) / x1]
        try:
            t1, t2 = [language.delta_int(x * 60, accuracy=3, brief=True, affix=False) for x in [a1, a2]]
        except (OverflowError, OSError):
            error = "Never"
            t1, t2 = [error, error]
        return await ctx.send(language.string("leveling_next_level", user=general.username(ctx.author), xp=r1, next=r2, left=r3, level=r5, prog=r4, min=t1, max=t2))

    @commands.command(name="levels", aliases=["ranks", "lb"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def levels_lb(self, ctx: commands.Context, top: int | Literal["top"] = None):
        """ Server's XP Leaderboard """
        language = self.bot.language(ctx)
        return await leaderboard(self, ctx, sql_server, (ctx.guild.id, self.bot.name), top, "leaderboards_levels", language, ctx.guild.name)

    @commands.command(name="levelsglobal", aliases=["levelsg", "glevels"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def global_levels(self, ctx: commands.Context, top: int | Literal["top"] = None):
        """ Global XP Leaderboard """
        language = self.bot.language(ctx)
        return await leaderboard2(self, ctx, sql_global, (self.bot.name,), top, "leaderboards_levels_global", language)


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Leveling(bot))
