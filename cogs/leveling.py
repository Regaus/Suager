from __future__ import annotations

import json
import random
from dataclasses import dataclass
from io import BytesIO

import discord
from PIL import Image, ImageDraw, UnidentifiedImageError, ImageFont
from discord import app_commands

from utils import bot_data, commands, emotes, general, images, languages, logger, settings, time, interactions, paginators


def _levels():
    req = 0
    xp = []
    for x in range(MAX_LEVEL):
        # base = 1.25 * x ** 2 + x * 80 + 250
        base = x ** 2 + 99 * x + 175
        req += int(base)
        if x not in DISALLOWED_LEVELS:
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
    for x in range(MAX_LEVEL):
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
        if x not in DISALLOWED_LEVELS:
            for key in keys:
                xp[key].append(req[key])
        else:
            for key in keys:
                xp[key].append(xp[key][-1])
    return xp


MAX_LEVEL = 200
DISALLOWED_LEVELS = (69, 420, 666, 1337)
LEVELS = _levels()
LEVEL_HISTORY = _level_history()
XP_AMOUNTS = (20, 27)
LEADERBOARD_PAGE_SIZE = 10

# noinspection SqlResolve,SqlShadowingAlias
SQL_SERVER = "SELECT uid, name, disc, (xp*APRILMULT())xp, level FROM leveling WHERE gid=? AND bot=? ORDER BY xp DESC"  # Level is used for rank
# noinspection SqlResolve,SqlShadowingAlias
SQL_GLOBAL = "SELECT uid, name, disc, (xp*APRILMULT())xp FROM leveling WHERE bot=?"


@dataclass
class LeaderboardEntry:
    user_id: int
    username: str
    xp: int
    xp_str: str
    xp_len: int


class Leveling(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        # Default colours and font for custom ranks
        # Note: when saving to the database, the default values are null, in case they ever get changed
        self.default_text = 0x32ff32
        self.default_progress = 0x32ff32
        self.default_background = 0x000000
        self.default_font = "whitney"
        self.blocked = []

    @commands.command(name="leveling")
    @commands.is_owner()
    async def leveling_data(self, ctx: commands.Context):
        """ Levels data """
        # __levels = [1, 2, 3, 5, 10, 20, 36, 50, 60, 75, 85, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500]
        # [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200]
        __levels = (1, 2, 3, 5, 10, 15, 20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200)
        outputs = []
        for level in __levels:
            _level = level - 1
            lv1 = int(LEVELS[_level])
            diff = lv1 - int(LEVELS[_level - 1]) if level > 1 else lv1
            outputs.append(f"Level {level:>3} | Req {lv1:>9,} | Diff {diff:>6,}")
        output = "\n".join(outputs)
        return await ctx.send(f"```fix\n{output}```")

    @commands.hybrid_command(name="oldlevels", aliases=["levelhistory"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.describe(level="The level to compare XP requirements for")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app_commands.allowed_installs(guilds=True, users=False)
    async def old_levels(self, ctx: commands.Context, level: int = None):
        """ Information about Suager's previous leveling systems """
        await ctx.defer(ephemeral=True)
        names = {"v3": "Suager v3", "v4": "Suager v4", "v5": "Suager v5", "v6": "Suager v6", "v7": "Suager v7"}
        if level is not None:
            if level > MAX_LEVEL:
                return await ctx.send(f"The max level is {MAX_LEVEL:,}")
            output = ""
            for key, name in names.items():
                output += f"\n`{name:<9} -> {LEVEL_HISTORY[key][level - 1]:>9,.0f} XP`"
            return await ctx.send(f"{general.username(ctx.author)}, for **level {level}** you would've needed:{output}")
        else:
            xp_ = self.bot.db.fetchrow(f"SELECT xp FROM leveling WHERE uid=? AND gid=? AND bot=?", (ctx.author.id, ctx.guild.id, self.bot.name))
            xp = xp_["xp"] if xp_ else 0
            output = ""
            for key, name in names.items():
                level = 0
                for level_req in LEVEL_HISTORY[key]:
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
            level, xp, last_xp, last_full = data['level'], data['xp'], data['last'], data['last_sent']
        else:
            level, xp, last_xp, last_full = 0, 0, 0, 0
        if last_full is None:
            last_full = 0

        # Determine time multiplier
        now = time.now_ts()
        delta_xp = now - last_xp
        delta_full = now - last_full
        if delta_xp < 5:
            time_mult = 0
        elif 5 <= delta_xp < 60:
            time_mult = (delta_xp - 5) / 55
        else:
            time_mult = 1
        if delta_full > 60:
            time_mult = 1

        # Server multiplier
        try:
            server_mult = float(__settings['leveling']['xp_multiplier'])
        except KeyError:
            server_mult = 1
        # Extra multipliers
        extra_mult = 1
        if ctx.guild.id == 568148147457490954:  # Senko Lair
            if 571034926107852801 in [role.id for role in ctx.author.roles]:  # if muted
                extra_mult *= 0.25

        xp1, xp2 = XP_AMOUNTS
        xp_gain = int(random.uniform(xp1, xp2) * server_mult * time_mult * extra_mult)

        xp += xp_gain
        # yearly += new
        # old_level = level

        # Level up/down
        level_up, level_down = False, False
        if level >= 0:
            while level < MAX_LEVEL and xp >= LEVELS[level]:
                level += 1
                level_up = True
            while level > 0 and xp < LEVELS[level - 1]:
                level -= 1
                level_down = True
            if level == 0 and xp < 0:
                level = -1
                level_down = True
        elif level == -1:
            if xp >= 0:
                level = 0
                level_up = True
            if xp < -LEVELS[0]:
                level -= 1
                level_down = True
        else:
            while -MAX_LEVEL <= level < -1 and xp >= -LEVELS[(-level) - 2]:
                level += 1
                level_up = True
            while level >= -MAX_LEVEL and xp < -LEVELS[(-level) - 1]:
                level -= 1
                level_down = True

        if ctx.author.id == 430891116318031872 and level >= 5:  # Alex five stays on level 5
            level_up, level_down = False, False
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
                            next_reward = {"role": language.string("leveling_rewards_max"), "level": MAX_LEVEL}
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
            logger.log(self.bot.name, "leveling", f"{time.time()} > Levels on_message > {ctx.guild.name} ({ctx.guild.id}) > Forbidden to give {ctx.author} their level reward")
        except Exception as e:
            general.log_error(self.bot, "leveling", f"{time.time()} > Levels on_message > {ctx.guild.name} ({ctx.guild.id}) > {type(e).__name__}: {e}")

        # Handle level ups
        if level_up or level_down:
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
                if level == MAX_LEVEL:
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
                    .replace("[MAX_LEVEL]", language.number(MAX_LEVEL))
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
        last_xp = last_xp if time_mult == 0 else now      # If this message didn't count, don't update the "last counted" time
        last_full = now if time_mult == 1 else last_full  # If this message got full XP, update the "last full" time

        if data:
            self.bot.db.execute("UPDATE leveling SET level=?, xp=?, last=?, last_sent=?, name=?, disc=? WHERE uid=? AND gid=? AND bot=?",
                                (level, xp, last_xp, last_full, general.username(ctx.author), str(ctx.author), ctx.author.id, ctx.guild.id, self.bot.name))
        else:
            if xp != 0:  # No point in saving data if XP is zero...
                self.bot.db.execute(f"INSERT INTO leveling VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                    (ctx.author.id, ctx.guild.id, level, xp, now, now, general.username(ctx.author), str(ctx.author), self.bot.name, None))

    @commands.hybrid_command(name="rewards")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=15, type=commands.BucketType.user)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app_commands.allowed_installs(guilds=True, users=False)
    async def rewards(self, ctx: commands.Context):
        """ Check out the level rewards available in a server """
        await ctx.defer(ephemeral=True)
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
            description = ''
            for role in rewards:
                description += language.string("leveling_rewards_role", level=language.number(role["level"] * _af), role_id=role["role"])
            if description:
                embed.description = description
            else:
                embed.description = language.string("leveling_rewards_none")
            return await ctx.send(embed=embed)
        except KeyError:
            return await ctx.send(language.string("leveling_rewards_none"))

    def get_global_ranks(self) -> dict[int, int]:
        """ Get the global leveling ranks and return a dictionary of the mapping to each user """
        data = self.bot.db.fetch(SQL_GLOBAL, (self.bot.name,))
        output: dict[int, int] = {}
        for entry in data:
            user_id = entry["uid"]
            if user_id not in output:
                output[user_id] = 0
            output[user_id] += entry["xp"]
        return dict(sorted(output.items(), key=lambda x: x[1], reverse=True))

    async def generate_rank_card(self, ctx: commands.Context | discord.Interaction, member: discord.Member | None, *,
                                 language: languages.Language = None, global_rank: bool = False, sample_font: str = None):
        """ Wrapper for image rank card commands """
        if isinstance(ctx, discord.Interaction):
            ctx = await commands.Context.from_interaction(ctx)
        if language is None:
            language = ctx.language()
        user = member or ctx.author
        is_self = user.id == self.bot.user.id
        if user.bot and not is_self:
            return await ctx.send(language.string("leveling_rank_bot"), ephemeral=True)
        _af = -1 if time.april_fools() else 1

        async with ctx.typing(ephemeral=bool(sample_font)):  # Ranks are shown as regular messages, unless this is a sample from the font generation
            # Calculate the user's current XP, level and rank
            if global_rank:
                data = self.get_global_ranks()
                xp = 0
                place_str = language.string("leveling_rank_unknown")
                for place, (entry_uid, entry_xp) in enumerate(data.items(), start=1):
                    if entry_uid == user.id:
                        xp = entry_xp
                        place_str = language.string("leveling_rank_rank", place=language.string("leaderboards_place", val=language.number(place * _af)), total=language.number(len(data)))
                        break
                level = 0
                while level < MAX_LEVEL and xp >= LEVELS[level]:
                    level += 1
                rank_header = language.string("leveling_rank_global", user=general.username(user))
            else:
                xp = level = 0
                place_str = language.string("leveling_rank_unknown")
                data = self.bot.db.fetch(SQL_SERVER, (ctx.guild.id, self.bot.name))
                for place, entry in enumerate(data, start=1):
                    if entry["uid"] == user.id:
                        xp = entry["xp"]
                        level = entry["level"]
                        place_str = language.string("leveling_rank_rank", place=language.string("leaderboards_place", val=language.number(place * _af)), total=language.number(len(data)))
                        break
                rank_header = language.string("leveling_rank", user=general.username(user), server=ctx.guild.name)
            if sample_font:
                rank_header = language.string("leveling_custom_rank_font_sample", font=sample_font)
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
            # Override the font setting with the selected font if this is a sample
            if sample_font is not None:
                font_name = sample_font
            # Load font file and interpret colours into tuples
            font_colour = images.colour_int_to_tuple(text)
            progress_colour = images.colour_int_to_tuple(progress)
            background_colour = images.colour_int_to_tuple(background)
            # Image setup
            width, height = 2048, 612
            avatar_end = 512
            image = Image.new("RGB", (width, height), color=background_colour)
            draw = ImageDraw.Draw(image)
            # Get the user's avatar
            try:
                avatar_bio = BytesIO()
                await user.display_avatar.replace(size=512, format="png").save(avatar_bio)
                avatar = Image.open(avatar_bio)
                image.paste(avatar.resize((512, 512)), (0, 0))
            except UnidentifiedImageError:  # Failed to get image
                image.paste(Image.open("assets/error.png"), (0, 0))
            # Set up font
            try:
                font = images.load_font(font_name, size=128)
                font_small = font.font_variant(size=64)
            except ImportError:
                await ctx.send(f"{emotes.Deny} It seems that image generation does not work properly here...")
                font, font_small = None, None
            # Write user's name to the top of the rank card
            text_x = 542
            draw.text((text_x, -10), general.username(user), font=font, fill=font_colour)
            # Calculate XP required to reach the next level
            try:
                if level >= 0:
                    req = int(LEVELS[level])  # Requirement to next level
                elif level == -1:
                    req = 0
                else:
                    req = int(-LEVELS[(-level) - 2])
                next_str = language.number(req * _af, precision=0)
            except IndexError:
                req = float("inf")
                next_str = language.string("generic_max")
            # Calculate XP required to reach the current level
            try:
                if level > 0:
                    prev = int(LEVELS[level - 1])
                elif level == 0:
                    prev = 0
                else:
                    prev = -int(LEVELS[(-level) - 1])
            except IndexError:
                prev = 0
            # Draw the details of the rank card (rank, level, XP amounts)
            text_y = 512  # 495
            if not is_self:
                progress = (xp - prev) / (req - prev)
                level_str = language.string("leveling_rank_level_global" if global_rank else "leveling_rank_level", level=language.number(level * _af))
                draw.text((text_x, 130), f"{place_str} | {level_str}", font=font_small, fill=font_colour)
                xp_str = language.number(xp * _af, precision=0)
                if level < MAX_LEVEL:
                    # Remove the zero-width spaces from the progress text
                    progress_str = language.string("leveling_rank_progress", progress=language.number(progress, precision=2, percentage=True))
                    xp_left_str = language.string("leveling_rank_xp_left", left=language.number((req - xp) * _af, precision=0))
                else:
                    progress = 1
                    progress_str, xp_left_str = language.string("leveling_rank_max_1"), random.choice(language.data("leveling_rank_max_2"))
                draw.text((text_x, text_y), language.string("leveling_rank_xp", xp=xp_str, next=next_str, progress=progress_str, left=xp_left_str), font=font_small, fill=font_colour, anchor="ld")
            else:
                progress = 1  # 0.5
                rank = language.string("leveling_rank_rank2", place=language.string("leaderboards_place", val=1))
                level_str = language.string("leveling_rank_level", level=language.number(69420))
                draw.text((text_x, 130), f"{rank} | {level_str}", font=font_small, fill=font_colour)
                draw.text((text_x, text_y), language.string("leveling_rank_xp_self"), font=font_small, fill=font_colour, anchor="ld")
            # Draw progress bar
            full = width - 20
            done = int(progress * full)
            if done < 0:
                done = 0
            draw.rectangle((0, avatar_end, width, height), fill=(30, 30, 30), outline=progress_colour, width=5)
            draw.rectangle((10, avatar_end + 10, done + 10, height - 10), fill=progress_colour)
            # Save image and return it
            bio = images.save_to_bio(image)
            return await ctx.send(rank_header, file=discord.File(bio, filename="rank.png"))

    # The grouping means that the global rank can only be checked inside a server, but that shouldn't be an issue.
    @commands.hybrid_group(name="rank", aliases=["level", "xp"], fallback="local", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.describe(member="The user whose rank to check. Shows your own rank by default.")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app_commands.allowed_installs(guilds=True, users=False)
    async def rank_image(self, ctx: commands.Context, *, member: discord.Member = None):
        """ Check your or someone's rank in this server """
        if ctx.invoked_subcommand is None:
            return await self.generate_rank_card(ctx, member, global_rank=False)

    @rank_image.command(name="lang", aliases=["language", "rank4"], hidden=True, with_app_command=False)
    async def rank_language(self, ctx: commands.Context, language: str, *, member: discord.Member = None):
        """ Check your or someone's rank in a different language """
        _language = self.bot.language2(language)
        if language not in languages.languages.languages.keys():
            return await ctx.send(ctx.language().string("settings_locale_invalid", language=language, p=ctx.prefix))
        return await self.generate_rank_card(ctx, member, language=_language, global_rank=False)

    @rank_image.command(name="global", aliases=["g", "grank"])
    @app_commands.describe(member="The user whose global rank to check. Shows your own rank by default.")
    async def rank_global(self, ctx: commands.Context, *, member: discord.User = None):
        """ Check your or someone's global rank """
        return await self.generate_rank_card(ctx, member, global_rank=True)

    @rank_image.group(name="customise", aliases=["custom", "crank"])
    async def custom_rank(self, ctx: commands.Context):
        """ Customise your rank card

        You are able to customise the colour of the text, the colour of the background, and the colour of the progress bar.
        You can also choose which font to use for your rank. """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    async def _customise_colour(self, ctx: commands.Context, colour: str, db_key: str, output_key: str):
        await ctx.defer(ephemeral=True)
        language = ctx.language()
        try:
            int_colour = images.colour_hex_to_int(colour)
        except images.InvalidLength as e:
            return await ctx.send(language.string("images_colour_invalid_value", value=e.value, length=e.length))
        except images.InvalidColour as e:
            return await ctx.send(language.string("images_colour_invalid", value=e.value, err=e.error))
        data = self.bot.db.fetchrow("SELECT * FROM custom_rank WHERE uid=?", (ctx.author.id,))
        if data:
            self.bot.db.execute(f"UPDATE custom_rank SET {db_key}=? WHERE uid=?", (int_colour, ctx.author.id))
        else:
            match db_key:
                case "font":
                    output_data = (int_colour, None, None)
                case "progress":
                    output_data = (None, int_colour, None)
                case "background":
                    output_data = (None, None, int_colour)
                case _:
                    raise ValueError(f"Invalid database key {db_key!r}")
            self.bot.db.execute("INSERT INTO custom_rank VALUES (?, ?, ?, ?, ?)", (ctx.author.id, *output_data, None))
        return await ctx.send(language.string(f"leveling_custom_rank_{output_key}", colour=colour))

    @custom_rank.command(name="text")
    @app_commands.describe(colour="New text colour. Provide a valid hexadecimal colour (6-letter RGB code)")
    async def crank_font_colour(self, ctx: commands.Context, colour: str):
        """ Change the colour of the text

         Provide a valid hexadecimal colour (6-letter RGB code) """
        return await self._customise_colour(ctx, colour, db_key="font", output_key="text")

    @custom_rank.command(name="progressbar", aliases=["progress"])
    @app_commands.describe(colour="New progress bar colour. Provide a valid hexadecimal colour (6-letter RGB code)")
    async def crank_progress(self, ctx: commands.Context, colour: str):
        """ Change the colour of the progress bar

        Provide a valid hexadecimal colour (6-letter RGB code) """
        return await self._customise_colour(ctx, colour, db_key="progress", output_key="progress")

    @custom_rank.command(name="background", aliases=["bg"])
    @app_commands.describe(colour="New background colour. Provide a valid hexadecimal colour (6-letter RGB code)")
    async def crank_bg(self, ctx: commands.Context, colour: str):
        """ Change the colour of the background

        Provide a valid hexadecimal colour (6-letter RGB code) """
        return await self._customise_colour(ctx, colour, db_key="background", output_key="background")

    @custom_rank.command(name="font")
    @app_commands.choices(font=images.FONT_CHOICES)
    @app_commands.describe(font="The name of the font to use")
    async def crank_font(self, ctx: commands.Context, *, font: str):
        """ Change the font used in your rank card """
        await ctx.defer(ephemeral=True)
        language = ctx.language()
        chosen_font = None
        for shown_name, internal_name, _ in images.FONTS:
            if font == shown_name or font.lower() == internal_name:
                chosen_font = (shown_name, internal_name)
                break
        if chosen_font is None:
            return await ctx.send(language.string("leveling_custom_rank_font_invalid", font=font, valid="`, `".join(shown_name for shown_name, _, _ in images.FONTS)))
        # The database stores the "internal name" of the font, while the user is shown the proper name
        data = self.bot.db.fetchrow("SELECT * FROM custom_rank WHERE uid=?", (ctx.author.id,))
        if data:
            self.bot.db.execute("UPDATE custom_rank SET custom_font=? WHERE uid=?", (chosen_font[1], ctx.author.id))
        else:
            self.bot.db.execute("INSERT INTO custom_rank VALUES (?, ?, ?, ?, ?)", (ctx.author.id, None, None, None, chosen_font[1]))
        return await ctx.send(language.string("leveling_custom_rank_font", font=chosen_font[0]))

    @custom_rank.command(name="font-sample", aliases=["sample"])
    @app_commands.choices(font=images.FONT_CHOICES)
    @app_commands.describe(font="Specify a font to see your rank card using it. Leave empty to see all available fonts.")
    async def crank_font_sample(self, ctx: commands.Context, *, font: str = None):
        """ Generate a sample image that shows how a certain font looks """
        language = ctx.language()
        if font is None:
            await ctx.defer(ephemeral=True)
            width = 1024
            mid_x = width // 2
            height_per_font = 64
            height = height_per_font * len(images.FONTS)
            image = Image.new("RGBA", (width, height), color=(0, 0, 0))
            draw = ImageDraw.Draw(image)
            text_colour = (255, 255, 255)
            draw.rectangle((mid_x - 2, 0, mid_x + 2, height), fill=text_colour)
            for i, (font_name, _, filename) in enumerate(images.FONTS, start=0):
                y = height_per_font * i
                text_y = y + height_per_font // 2
                font = ImageFont.truetype(f"assets/fonts/{filename}", size=height_per_font * 0.75)
                draw.text((10, text_y), font_name, font=font, fill=text_colour, anchor="lm")
                draw.text((mid_x + 10, text_y), general.username(ctx.author), font=font, fill=text_colour, anchor="lm")
                if y + height_per_font < height:  # Draw the vertical line unless we are at the last value.
                    draw.rectangle((0, y + height_per_font - 2, width, y + height_per_font), fill=text_colour)
            bio = images.save_to_bio(image)
            return await ctx.send(language.string("leveling_custom_rank_font_list"), file=discord.File(bio, filename=f"fonts.png"))
        else:
            for shown_name, internal_name, _ in images.FONTS:
                if font == shown_name or font.lower() == internal_name:
                    return await self.generate_rank_card(ctx, ctx.author, language=language, global_rank=False, sample_font=shown_name)
            return await ctx.send(language.string("leveling_custom_rank_font_invalid", font=font, valid="`, `".join(shown_name for shown_name, _, _ in images.FONTS)), ephemeral=True)

    @commands.hybrid_command(name="xplevel")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @app_commands.describe(level="The level for which to check XP requirements")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)  # This command does not require being in a guild
    @app_commands.allowed_installs(guilds=True, users=False)  # While the command is ephemeral, it wouldn't make sense to allow leveling commands on a user install
    async def xp_level(self, ctx: commands.Context, level: int):
        """ Check the amount of XP required to achieve a level """
        await ctx.defer(ephemeral=True)
        language = self.bot.language(ctx)
        _af = -1 if time.april_fools() else 1
        if level > MAX_LEVEL or level < MAX_LEVEL * -1 + 1:
            return await ctx.send(language.string("leveling_xplevel_max", level=language.number(MAX_LEVEL)))
        try:
            if level > 0:
                req = int(LEVELS[level - 1])
            elif level == 0:
                req = 0
            else:
                req = -int(LEVELS[(-level) - 1])
        except IndexError:
            return await ctx.send(language.string("leveling_xplevel_max", level=language.number(MAX_LEVEL)))
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
            server_mult = 1
        else:
            __settings = json.loads(_settings['data'])
            try:
                server_mult = __settings['leveling']['xp_multiplier']
            except KeyError:
                server_mult = 1
        base = language.string("leveling_xplevel_main", xp=language.number(req * _af, precision=0), level=language.number(level * _af))
        extra = ""
        if xp < req:
            xp1, xp2 = (val * server_mult for val in XP_AMOUNTS)
            delta_min, delta_max = (req - xp) / xp2, (req - xp) / xp1  # The min and max time to reach that level as number minutes
            try:
                time_min, time_max = (language.delta_int(x * 60, accuracy=3, brief=True, affix=False) for x in (delta_min, delta_max))  # The time to reach the level as a timedelta string
            except (OverflowError, OSError):
                time_min = time_max = "Never"
            extra = language.string("leveling_xplevel_extra", left=language.number((req - xp) * _af, precision=0), min=time_min, max=time_max)
        return await ctx.send(f"{base}{extra}")

    @commands.hybrid_command(name="nextlevel", aliases=["nl"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app_commands.allowed_installs(guilds=True, users=False)
    async def next_level(self, ctx: commands.Context):
        """ XP required for next level """
        await ctx.defer(ephemeral=True)
        language = self.bot.language(ctx)
        _af = -1 if time.april_fools() else 1
        data = self.bot.db.fetchrow(f"SELECT * FROM leveling WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not data:
            return await ctx.send(language.string("leveling_next_level_none"))
        _settings = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not _settings:
            server_mult = 1
        else:
            __settings = json.loads(_settings['data'])
            try:
                server_mult = __settings['leveling']['xp_multiplier']
            except KeyError:
                server_mult = 1
        level, xp = [data['level'], data['xp']]
        if level == MAX_LEVEL:
            return await ctx.send(language.string("leveling_next_level_max", user=general.username(ctx.author)))
        xp_str = language.number(xp * _af, precision=0)
        try:
            if level >= 0:
                req = int(LEVELS[level])  # Requirement to next level
            elif level == -1:
                req = 0
            else:
                req = int(-LEVELS[(-level) - 2])
        except IndexError:
            req = float("inf")
        try:
            if level > 0:
                prev = int(LEVELS[level - 1])
            elif level == 0:
                prev = 0
            else:
                prev = -int(LEVELS[(-level) - 1])
        except IndexError:
            prev = 0
        xp_left = req - xp
        progress = (xp - prev) / (req - prev)
        next_str = language.number(req * _af)
        left_str = language.number(xp_left * _af)
        progress_str = language.number(progress if progress < 1 else 1, precision=1, percentage=True)
        level_str = language.number((level + 1) * _af)
        xp1, xp2 = (val * server_mult for val in XP_AMOUNTS)
        delta_min, delta_max = (req - xp) / xp2, (req - xp) / xp1
        try:
            time_min, time_max = (language.delta_int(x * 60, accuracy=3, brief=True, affix=False) for x in (delta_min, delta_max))
        except (OverflowError, OSError):
            time_min = time_max = "Never"
        return await ctx.send(language.string("leveling_next_level", user=general.username(ctx.author), xp=xp_str, next=next_str, left=left_str,
                                              level=level_str, prog=progress_str, min=time_min, max=time_max))

    async def generate_leaderboard(self, ctx: commands.Context, *, is_global: bool, page: int | None):
        """ Wrapper for the two leaderboard commands """
        await ctx.defer(ephemeral=False)
        language = ctx.language()
        if is_global:
            _data = self.bot.db.fetch(SQL_GLOBAL, (self.bot.name,))
        else:
            _data = self.bot.db.fetch(SQL_SERVER, (ctx.guild.id, self.bot.name))
        if not _data:
            return await ctx.send(language.string("leaderboards_no_data"))
        data: dict[int, LeaderboardEntry] = {}
        if is_global:
            for entry in _data:
                if entry["uid"] in data:
                    data[entry["uid"]].xp += entry["xp"]
                else:
                    username = f"{entry["name"]} ({entry["disc"]})"
                    data[entry["uid"]] = LeaderboardEntry(entry["uid"], username, entry["xp"], "", 0)
            for entry in data.values():
                entry.xp_str = language.number(entry.xp, precision=0)
                entry.xp_len = len(entry.xp_str)
        else:
            for entry in _data:
                username = f"{entry["name"]} ({entry["disc"]})"
                xp_str = language.number(entry["xp"], precision=0)
                data[entry["uid"]] = LeaderboardEntry(entry["uid"], username, entry["xp"], xp_str, len(xp_str))
        _af = -1 if time.april_fools() else 1
        sorted_data = sorted(data.values(), key=lambda x: x.xp, reverse=True)
        total = len(sorted_data)
        place = 0
        place_str = language.string("generic_unknown")
        for idx, entry in enumerate(sorted_data, start=1):
            if entry.user_id == ctx.author.id:
                place = idx
                place_str = language.string("leaderboards_place", val=language.number(place * _af))
                break
        if page is None:
            page = (place - 1) // LEADERBOARD_PAGE_SIZE
        header = language.string("leaderboards_levels_global" if is_global else "leaderboards_levels",
                                 server=str(ctx.guild), place=place_str, total=language.number(total))
        paginator = paginators.LinePaginator(prefix=header + "\n```fix", suffix="```", max_lines=LEADERBOARD_PAGE_SIZE, max_size=1000)
        for idx, entry in enumerate(sorted_data, start=1):
            username = f"-> {entry.username}" if entry.user_id == ctx.author.id else entry.username
            current_page = (idx - 1) // LEADERBOARD_PAGE_SIZE
            page_start = current_page * LEADERBOARD_PAGE_SIZE
            page_end = page_start + LEADERBOARD_PAGE_SIZE
            spaces = max(e.xp_len for e in sorted_data[page_start:page_end])
            padding = len(str((current_page + 1) * LEADERBOARD_PAGE_SIZE)) + (_af < 0)
            # Place -> ZWNJ -> 2 spaces -> XP (aligned right) -> 4 spaces -> Name
            paginator.add_line(f"{idx * _af:0{padding}d})\u200c  {entry.xp_str:>{spaces}}    {username}")
        interface = paginators.PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
        interface.display_page = page  # Set the page to the user's current or chosen page
        return await interface.send_to(ctx)

    @commands.hybrid_group(name="leaderboard", aliases=["levels"], fallback="local", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.describe(page="Page number")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app_commands.allowed_installs(guilds=True, users=False)
    async def leaderboard(self, ctx: commands.Context, page: int = None):
        """ Show the server's XP Leaderboard """
        if ctx.invoked_subcommand is None:
            return await self.generate_leaderboard(ctx, is_global=False, page=page)

    @leaderboard.command(name="global")
    @app_commands.describe(page="Page number")
    async def global_leaderboard(self, ctx: commands.Context, page: int = None):
        """ Show the global XP Leaderboard """
        return await self.generate_leaderboard(ctx, is_global=True, page=page)


async def setup(bot: bot_data.Bot):
    cog = Leveling(bot)
    await bot.add_cog(cog)

    @bot.tree.context_menu(name="Check Server Rank")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app_commands.allowed_installs(guilds=True, users=False)
    async def ctx_check_local_rank(interaction: discord.Interaction, user: discord.Member):
        """ Context menu to check a user's rank in the server """
        interactions.log_interaction(interaction)
        return await cog.generate_rank_card(interaction, user, global_rank=False)

    @bot.tree.context_menu(name="Check Global Rank")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app_commands.allowed_installs(guilds=True, users=False)
    async def ctx_check_global_rank(interaction: discord.Interaction, user: discord.Member):
        """ Context menu to check a user's global rank """
        interactions.log_interaction(interaction)
        return await cog.generate_rank_card(interaction, user, global_rank=True)
