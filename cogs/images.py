import json
import random
import urllib.parse
from io import BytesIO

import discord
from discord.ext import commands

from PIL import Image, ImageDraw, ImageFont
from utils import http, argparser, generic


async def image_gen(ctx: commands.Context, user: discord.Member, link, filename=None, extra_args=None):
    async with ctx.typing():
        if filename is None:
            filename = link
        avatar = user.avatar_url_as(size=512, format="png")
        extra = f"&{extra_args}" if extra_args is not None else ''
        bio = BytesIO(await http.get(f"https://api.alexflipnote.dev/{link}?image={avatar}{extra}", res_method="read"))
        if bio is None:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "image_not_created"), ctx.channel)
        return await generic.send(None, ctx.channel, file=discord.File(bio, filename=f"{filename}.png"))


async def api_img_creator(ctx: commands.Context, url, filename, content=None):
    async with ctx.channel.typing():
        req = await http.get(url, res_method="read")
        if req is None:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "image_not_created"), ctx.channel)
        bio = BytesIO(req)
        bio.seek(0)
        return await generic.send(content, ctx.channel, file=discord.File(bio, filename=filename))


class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="colour", aliases=["color"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def colour(self, ctx: commands.Context, colour: str):
        """ Information on a colour """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "colour"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        async with ctx.typing():
            c = generic.gls(locale, str(ctx.invoked_with).lower())
            c2 = c.capitalize()
            if colour.lower() == "random":
                _colour = hex(random.randint(0, 0xffffff))[2:]
                a = 6
            else:
                try:
                    _colour = hex(int(colour, base=16))[2:]
                    a = len(colour)
                    if a != 3 and a != 6:
                        return await generic.send(generic.gls(locale, "colour_value_len"), ctx.channel)
                except Exception as e:
                    return await generic.send(generic.gls(locale, "invalid_colour2", [c, c2, e]), ctx.channel)
            try:
                _data = await http.get(f"https://api.alexflipnote.dev/colour/{_colour}", res_method="read")
                data = json.loads(_data)
            except json.JSONDecodeError:
                try:
                    _data = await http.get(f"https://api.alexflipnote.dev/colour/{colour}", res_method="read")
                    data = json.loads(_data)
                except json.JSONDecodeError:
                    return await generic.send(generic.gls(locale, "col_error"), ctx.channel)
            if a == 3:
                d, e, f = colour
                g = int(f"{d}{d}{e}{e}{f}{f}", base=16)
                embed = discord.Embed(colour=g)
            else:
                embed = discord.Embed(colour=int(colour, base=16) if colour.lower() != "random" else int(_colour, base=16))
            embed.add_field(name=generic.gls(locale, "hex_value"), value=data["hex"], inline=True)
            embed.add_field(name=generic.gls(locale, "rgb_value"), value=data["rgb"], inline=True)
            embed.add_field(name=generic.gls(locale, "integer"), value=data["int"], inline=True)
            embed.add_field(name=generic.gls(locale, "brightness"), value=data["brightness"], inline=True)
            embed.add_field(name=generic.gls(locale, "font_col", [c]), value=data["blackorwhite_text"], inline=True)
            embed.set_thumbnail(url=data["image"])
            embed.set_image(url=data["image_gradient"])
            return await generic.send(None, ctx.channel, embed=embed)

    @commands.command(name="colourify", aliases=["blurple", "colorify"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def colourify(self, ctx: commands.Context, user: discord.Member = None, colour: str = "7289da"):
        """ Colourify """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "colourify"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        if user is None:
            user = ctx.author
        z, y, x = "7289da", generic.gls(locale, "invalid_colour"), "colourify"
        a = len(colour)
        c = colour
        try:
            int(c, base=16)
        except ValueError:
            await generic.send(y, ctx.channel)
            c, a = z, 6
        if a == 3:
            d, e, f = c
            b = f"{d}{d}{e}{e}{f}{f}"
        elif a == 6:
            b = c
        else:
            await generic.send(y, ctx.channel)
            b = z
        return await image_gen(ctx, user, x, f"{x}_{b}", f"c={b}")

    @commands.command(name="filter")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def filter(self, ctx: commands.Context, filter_name: str, *, who: discord.Member = None):
        """ Let someone go through a filter
        Do //filter help to see allowed filters """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "filter"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        user = who or ctx.author
        filters = ["blur", "invert", "b&w", "deepfry", "pixelate", "snow", "gay", "magik", "jpegify", "communist"]
        _filter = filter_name.lower()
        if _filter not in filters or _filter == "help":
            return await generic.send(generic.gls(locale, "allowed_filters", ["`, `".join(filters)]), ctx.channel)
        return await image_gen(ctx, user, f"filter/{_filter}", f"{_filter}_filter")

    @commands.command(name="woosh", aliases=["jokeoverhead"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def joke_over_head(self, ctx: commands.Context, who: discord.Member = None):
        """ Joke over head """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "woosh"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        user = who or ctx.author
        return await image_gen(ctx, user, "jokeoverhead", "joke-over-head")

    @commands.command(name="amiajoke")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def am_i_a_joke(self, ctx: commands.Context, *, who: discord.member = None):
        """ Is a user a joke? """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "amiajoke"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        user = who or ctx.author
        return await image_gen(ctx, user, "amiajoke", f"is_{user.name.lower()}_a_joke")

    @commands.command(name="salty")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def sodium_chloride(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Salty user """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "salty"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        user = who or ctx.author
        return await image_gen(ctx, user, "salty", f"sodium_chloride_{user.name.lower()}")

    @commands.command(name="floor")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def the_floor_is(self, ctx: commands.Context, user: discord.Member, *text):
        """ The floor is... """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "floor"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        __text = '+'.join(text)
        _text = str(__text).replace("#", "%23")
        if len(a := _text.split("+")) > 1:
            _filename = a[0]
        else:
            _filename = _text
        if len(_filename) > 32:
            _filename = _filename[:32]
        filename = _filename.lower()
        return await image_gen(ctx, user, "floor", f"the_floor_is_{filename}", f"text={_text}")

    @commands.command()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def supreme(self, ctx: commands.Context, *, text: commands.clean_content(fix_channel_mentions=True)):
        """ Make a Supreme logo

        Arguments:
            --dark | Make the background dark
            --light | Make background light
        """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "supreme"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        parser = argparser.Arguments()
        parser.add_argument('input', nargs="+", default=None)
        parser.add_argument('-d', '--dark', action='store_true')
        parser.add_argument('-l', '--light', action='store_true')
        args, valid_check = parser.parse_args(text)
        if not valid_check:
            return await generic.send(args, ctx.channel)
        input_text = urllib.parse.quote(' '.join(args.input))
        if len(input_text) > 500:
            return await generic.send(generic.gls(locale, "supreme_limit", [ctx.author.name]), ctx.channel)
        dol = ""
        if args.dark:
            dol = "&dark=true"
        if args.light:
            dol = "&light=true"
        if args.dark and args.light:
            return await generic.send(generic.gls(locale, "supreme_dark_light", [ctx.author.name]), ctx.channel)
        return await api_img_creator(ctx, f"https://api.alexflipnote.dev/supreme?text={input_text}{dol}", "supreme.png")

    @commands.command(name="meme")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def meme_generator(self, ctx: commands.Context, *, text: commands.clean_content(fix_channel_mentions=True)):
        """ Create a meme """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "meme"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        async with ctx.typing():
            font_colour = (255, 0, 0)
            width = 1200
            img = Image.new("RGB", (width, 600), color=(0, 0, 0))
            dr = ImageDraw.Draw(img)
            font_dir = "assets/impact.ttf"
            font = ImageFont.truetype(font_dir, size=72)
            tw, _th = dr.textsize(text.upper(), font=font)
            if tw > 1200:
                width = tw + 20
                img = Image.new("RGB", (width, 600), color=(0, 0, 0))
                dr = ImageDraw.Draw(img)
            bw, _bh = dr.textsize("BOTTOM TEXT", font=font)
            dr.text(((width - tw) // 2, 20), text.upper(), font=font, fill=font_colour)
            dr.text(((width - bw) // 2, 510), "BOTTOM TEXT", font=font, fill=font_colour)
            bio = BytesIO()
            img.save(bio, "PNG")
            bio.seek(0)
            return await generic.send(None, ctx.channel, file=discord.File(bio, filename="meme.png"))


def setup(bot):
    bot.add_cog(Images(bot))
