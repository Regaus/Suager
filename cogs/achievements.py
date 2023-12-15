from io import BytesIO

import discord
from PIL import Image, ImageDraw, ImageFont

from utils import bot_data, commands, emotes, images
from utils.general import username

achievement_colours = [
    (96, 96, 96),     # Tier 0
    (255, 255, 255),  # Tier 1
    # (255, 96, 96),    # Tier (2)
    (255, 0, 0),      # Tier 2 (3)
    (255, 64, 0),     # Tier 3 (4)
    (255, 170, 0),    # Tier 4 (5)
    (255, 255, 0),    # Tier 5 (6)
    (50, 255, 50),    # Tier 6 (7)
    (0, 0, 255),      # Tier 7 (8)
    (0, 255, 255),    # Tier 8 (9)
    (0, 255, 128),    # Tier 9 (10)
    # (0, 128, 128),    # Tier (11)
    (128, 0, 255),    # Tier 10 (12)
    # (255, 0, 255),    # Tier (13)
    (255, 0, 160),    # Tier 11 (14)
    (255, 0, 87)      # Tier 12 (15)
]
# achievement_colours = ["808080", "ffffff", "ff0000", "ff4000", "ff8000", "ffff00", "80ff00", "32ff32", "00ff80", "00ffff", "ff00ff", "ff00a0", "ff0057"]


class Achievements(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.command(name="achievements", aliases=["accomplishments", "ah"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def achievements(self, ctx: commands.Context, who: discord.User = None):
        """ See your progress within my bots """
        # locale = languages.gl(ctx)
        language = self.bot.language(ctx)
        user = who or ctx.author
        # achievement_levels = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200]
        achievement_levels = [10, 20, 30, 40, 50, 60, 75, 100, 125, 150, 175, 200]
        achievement_xp = [10000, 25000, 50000, 100000, 250000, 500000, 750000, 1000000, 1250000, 1500000, 1750000, 2000000, 2500000, 3000000, 4000000, 5000000]
        # achievement_xp = [10000, 25000, 50000, 100000, 200000, 500000, 750000, 1000000, 1750000, 2500000, 3750000, 5000000]
        # rows = 6 if not player.is_new else 2
        # shelves = 1
        if self.bot.name == "cobble":  # and langs.get_data("_conlang", locale) is None:
            rows = 2
            shelves = 1
        else:
            rows = 2
            shelves = 1
        width = 1152
        large_size = 96
        img = Image.new("RGBA", ((width + 20) * shelves - 20, 256 * rows + large_size), color=(0, 0, 0, 64))
        dr = ImageDraw.Draw(img)
        # font_dir = "assets/font.ttf"
        font_dir = images.font_files["whitney"]
        try:
            font = ImageFont.truetype(font_dir, size=large_size)
            font_med = ImageFont.truetype(font_dir, size=64)
            font_small = ImageFont.truetype(font_dir, size=32)
        except ImportError:
            await ctx.send(f"{emotes.Deny} It seems that image generation does not work properly here...")
            font, font_med, font_small = None, None, None
        w = dr.textlength(username(user), font=font)
        max_description = language.string("achievements_highest")
        # max_description = "Highest achievement tier reached!"

        def get_colour(level: int):
            try:
                return achievement_colours[level]
            except IndexError:
                return achievement_colours[-1]

        def generate_box(shelf: int, index: int, level: int, tier_count: int, name: str, details: str, current: int, requirement: int, previous: int):
            x = shelf * (width + 20)
            y = large_size + index * 256
            colour_level = round(level * (12 / tier_count))
            if level >= 1 > colour_level:
                colour_level = 1
            colour = get_colour(colour_level)
            i1 = Image.new("RGBA", (width - 32, 224), color=colour)
            i2 = Image.new("RGBA", (width - 64, 192), color=(0, 0, 0, 64))
            box1 = (x + 16, y + 16, x + width - 16, y + 240)
            box2 = (x + 32, y + 32, x + width - 32, y + 224)
            img.paste(i1, box1)
            img.paste(i2, box2)
            text_x = 48
            dr.text((x + text_x, y + 28), name, font=font_med, fill=colour)
            try:
                progress = (current - previous) / (requirement - previous)
                progress = 1 if progress > 1 else progress
            except ZeroDivisionError:
                progress = 1
            # These values are 1-2 digit numbers, so there isn't really a point in translating them, but oh well
            dr.text((x + text_x, y + 96), language.string("achievements_current", current=language.number(level), max=language.number(tier_count)), font=font_small, fill=colour)
            # dr.text((x + text_x, y + 96), f"Current Tier: {level} of {tier_count}", font=font_small, fill=colour)
            r1, r3, r4 = language.number(level + 1), language.number(current, precision=0), language.number(requirement, precision=0)
            desc = language.string("achievements_goal", level=r1, goal=details, current=r3, target=r4) if requirement > current else max_description
            # desc = f"Tier {level + 1} Goal: {details} ({current:,}/{requirement:,})" if requirement > current else max_description
            dr.text((x + text_x, y + 128), desc, font=font_small, fill=colour)
            fill = width - 192
            done = int(fill * progress)
            if done < 0:
                done = 0
            i3 = Image.new("RGBA", (fill + 20, 42), color=colour)
            i4 = Image.new("RGBA", (fill + 10, 32), color=(30, 30, 30, 64))
            i5 = Image.new("RGBA", (done, 22), color=colour)
            # box4 = (x + text_x, y + 174, x + text_x + fill + 4, y + 210)
            # box5 = (x + text_x + 2, y + 176, x + text_x + done + 2, y + 208)
            box3, box4, box5 = (x + text_x, y + 174), (x + text_x + 5, y + 179), (x + text_x + 10, y + 184)
            img.paste(i3, box3)
            img.paste(i4, box4)
            img.paste(i5, box5)
            dr.text((x + text_x + fill + 30, y + 170), language.number(progress, percentage=True, precision=0), font=font_small, fill=colour)

        tiers = []
        user_xp = self.bot.db.fetch(f"SELECT * FROM leveling WHERE uid=? AND bot=? ORDER BY xp DESC", (user.id, self.bot.name))
        try:
            max_level = user_xp[0]["level"]
        except IndexError:
            max_level = 0
        req, prev, tier = 0, 0, 0
        for req in achievement_levels:
            if max_level >= req:
                tier += 1
                prev = req
            else:
                break
        tiers.append(tier)
        generate_box(0, 0, tier, 12, language.string("achievements_leveling_levels"), language.string("achievements_leveling_levels_desc", target=language.number(req)),
                     max_level, req, prev)
        total_xp = sum(part["xp"] for part in user_xp)
        req, prev, tier = 0, 0, 0
        for req in achievement_xp:
            if total_xp >= req:
                tier += 1
                prev = req
            else:
                break
        tiers.append(round(tier * 0.75))
        generate_box(0, 1, tier, 16, language.string("achievements_leveling_xp"), language.string("achievements_leveling_xp_desc", target=language.number(req)),
                     total_xp, req, prev)
        # After TBL v2 is done - Remove Leveling achievements from Cobble's version of the command, only show them with Suager
        # TBL v2 achievements - Shelf 1
        # CC2 - Depth - Shelf 2
        # CC2 - Cobble Levels - Shelf 2
        # CC2 - Cobble Mined - Shelf 2
        # Aqos achievements - Shelf 2
        # DLRAM achievements - Shelf 3
        # min_tier = min(tiers)
        max_tier = max(tiers)
        # req = min_tier + 1 if min_tier < 12 else 12
        # generate_box(2, 5, min_tier, 12, "Achievements", f"Reach tier {req} on all achievements", min_tier, req, min_tier)
        dr.text(((((width + 20) * shelves - 20) - w) / 2, -15), username(user), font=font, fill=achievement_colours[max_tier])
        bio = BytesIO()
        img.save(bio, "PNG")
        bio.seek(0)
        # f"This is what **{user}** has accomplished so far."
        return await ctx.send(language.string("achievements_achievements", user=username(user)), file=discord.File(bio, filename="achievements.png"))

    @commands.command(name="tiers")
    @commands.is_owner()
    async def tier_test(self, ctx: commands.Context):
        """ Test tier colours """
        from PIL import Image, ImageDraw, ImageFont
        from io import BytesIO
        img = Image.new("RGBA", (2000, 200 * len(achievement_colours)), color=(0, 0, 0, 0))
        dr = ImageDraw.Draw(img)
        font = ImageFont.truetype(images.font_files["whitney"], size=128)  # "assets/font.ttf"
        for i in range(len(achievement_colours)):
            paste = Image.new("RGBA", (1500, 150), color=achievement_colours[i])
            img.paste(paste, (500, 200 * i + 25))
            dr.text((75, 200 * i + 12), f"Tier {i:>2d}", font=font, fill=(255, 255, 255, 255))
        bio = BytesIO()
        img.save(bio, "PNG")
        bio.seek(0)
        return await ctx.send(file=discord.File(bio, filename="test.png"))


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Achievements(bot))
