from io import BytesIO

import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

from core.utils import emotes, general

# achievement_colours = ["808080", "ffffff", "ff0000", "ff4000", "ff8000", "ffff00", "80ff00", "32ff32", "00ff80", "00ffff", "ff00ff", "ff00a0", "ff0057"]
achievement_colours = [(128, 128, 128), (255, 255, 255), (255, 0, 0), (255, 64, 0), (255, 128, 0), (255, 255, 0), (128, 255, 128), (50, 255, 50), (0, 255, 128),
                       (0, 255, 255), (255, 0, 255), (255, 0, 160), (255, 0, 87)]


class Achievements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="achievements", aliases=["accomplishments", "ah"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def achievements(self, ctx: commands.Context, who: discord.User = None):
        """ See what you or someone else has accomplished """
        # locale = langs.gl(ctx)
        user = who or ctx.author
        achievement_levels = [10, 20, 30, 40, 50, 60, 75, 100, 125, 150, 175, 200]
        achievement_xp = [10000, 50000, 100000, 250000, 500000, 750000, 1000000, 1500000, 2000000, 2500000, 3000000, 4000000, 5000000, 7500000, 10000000]
        achievements = 2
        width = 1152
        large_size = 96
        img = Image.new("RGB", (width, 256 * achievements + large_size), color=(0, 0, 0))
        dr = ImageDraw.Draw(img)
        font_dir = "assets/font.ttf"
        try:
            font = ImageFont.truetype(font_dir, size=large_size)
            font_med = ImageFont.truetype(font_dir, size=64)
            font_small = ImageFont.truetype(font_dir, size=32)
        except ImportError:
            await general.send(f"{emotes.Deny} It seems that image generation does not work properly here...", ctx.channel)
            font, font_med, font_small = None, None, None
        w, _ = dr.textsize(f"{user}", font=font)
        dr.text(((width - w) / 2, -15), f"{user}", font=font, fill=(255, 0, 87))
        max_description = "Highest achievement tier reached!"

        def get_colour(level: int):
            try:
                return achievement_colours[level]
            except IndexError:
                return achievement_colours[-1]

        def generate_box(index: int, level: int, name: str, details: str, current: int, requirement: int):
            y = large_size + index * 256
            colour = get_colour(level)
            i1 = Image.new("RGB", (width - 32, 224), color=colour)
            i2 = Image.new("RGB", (width - 64, 192), color=(0, 0, 0))
            box1 = (16, y + 16, width - 16, y + 240)
            box2 = (32, y + 32, width - 32, y + 224)
            img.paste(i1, box1)
            img.paste(i2, box2)
            text_x = 48
            dr.text((text_x, y + 28), name, font=font_med, fill=colour)
            progress = current / requirement
            progress = 1 if progress > 1 else progress
            dr.text((text_x, y + 96), f"Current Tier: {level}", font=font_small, fill=colour)
            desc = f"Tier {level + 1} Goal: {details} ({current:,}/{requirement:,})" if requirement > current else max_description
            dr.text((text_x, y + 128), desc, font=font_small, fill=colour)
            fill = width - 172
            done = int(fill * progress)
            i3 = Image.new("RGB", (done, 32), color=colour)
            i4 = Image.new("RGB", (fill + 4, 36), color=(30, 30, 30))
            box3 = (text_x + 2, y + 176, text_x + done + 2, y + 208)
            box4 = (text_x, y + 174, text_x + fill + 4, y + 210)
            img.paste(i4, box4)
            img.paste(i3, box3)
            dr.text((text_x + fill + 10, y + 170), f"{progress:.0%}", font=font_small, fill=colour)

        user_xp = self.bot.db.fetch("SELECT * FROM leveling WHERE uid=? ORDER BY xp DESC", (user.id,))
        try:
            max_level = user_xp[0]["level"]
        except IndexError:
            max_level = 0
        lvl, tier = 0, 0
        for lvl in achievement_levels:
            if max_level >= lvl:
                tier += 1
            else:
                break
        generate_box(0, tier, "XP Levels", f"Reach Cobble XP Level {lvl} in a server", max_level, lvl)
        total_xp = sum(part["xp"] for part in user_xp)
        req, tier = 0, 0
        for req in achievement_xp:
            if total_xp >= req:
                tier += 1
            else:
                break
        generate_box(1, tier, "Experience", f"Collect {req:,} XP in total", total_xp, req)
        bio = BytesIO()
        img.save(bio, "PNG")
        bio.seek(0)
        return await general.send(f"**{ctx.author}**'s accomplishments", ctx.channel, file=discord.File(bio, filename="achievements.png"))


def setup(bot):
    bot.add_cog(Achievements(bot))
