import json
import random
import urllib.parse
from io import BytesIO

import discord
from discord.ext import commands

from PIL import Image, ImageDraw, ImageFont

from core.utils import http, general, arg_parser, database
from languages import langs


async def image_gen(ctx: commands.Context, user: discord.User or discord.Member, link, filename=None, extra_args=None):
    async with ctx.typing():
        if filename is None:
            filename = link
        avatar = user.avatar_url_as(size=512, format="png")
        extra = f"&{extra_args}" if extra_args is not None else ''
        bio = BytesIO(await http.get(f"https://api.alexflipnote.dev/{link}?image={avatar}{extra}", res_method="read"))
        if bio is None:
            return await general.send("An error occurred creating the image, try again later.", ctx.channel)
        return await general.send(None, ctx.channel, file=discord.File(bio, filename=f"{filename}.png"))


async def api_img_creator(ctx: commands.Context, url, filename, content=None):
    async with ctx.channel.typing():
        req = await http.get(url, res_method="read")
        if req is None:
            return await general.send("An error occurred creating the image, try again later.", ctx.channel)
        bio = BytesIO(req)
        bio.seek(0)
        return await general.send(content, ctx.channel, file=discord.File(bio, filename=filename))


class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database(self.bot.name)

    @commands.command(name="colour", aliases=["color"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def colour(self, ctx: commands.Context, colour: str):
        """ Information on a colour """
        locale = langs.gl(ctx.guild, self.db)
        async with ctx.typing():
            # c = str(ctx.invoked_with)
            if colour.lower() == "random":
                _colour = hex(random.randint(0, 0xffffff))[2:]
                a = 6
            else:
                try:
                    _colour = hex(int(colour, base=16))[2:]
                    a = len(colour)
                    if a != 3 and a != 6:
                        return await general.send(langs.gls("images_colour_invalid_value", locale), ctx.channel)
                        # return await general.send("The value must be either 3 or 6 digits long.", ctx.channel)
                except Exception as e:
                    return await general.send(langs.gls("images_colour_invalid", locale, type(e).__name__, str(e)), ctx.channel)
                    # return await general.send(f"Invalid {c} - `{type(e).__name__}: {e}`", ctx.channel)
            try:
                _data = await http.get(f"https://api.alexflipnote.dev/colour/{_colour}", res_method="read")
                data = json.loads(_data)
            except json.JSONDecodeError:
                return await general.send("An error occurred with the API. Try again later.", ctx.channel)
            if a == 3:
                d, e, f = colour
                g = int(f"{d}{d}{e}{e}{f}{f}", base=16)
                embed = discord.Embed(colour=g)
            else:
                embed = discord.Embed(colour=int(_colour, base=16))
            embed.title = langs.gls("images_colour_name", locale, data['name'])
            embed.add_field(name=langs.gls("images_colour_hex", locale), value=data["hex"], inline=True)
            embed.add_field(name=langs.gls("images_colour_rgb", locale), value=data["rgb"], inline=True)
            embed.add_field(name=langs.gls("images_colour_int", locale), value=data["int"], inline=True)
            embed.add_field(name=langs.gls("images_colour_brightness", locale), value=langs.gns(data["brightness"], locale), inline=True)
            embed.add_field(name=langs.gls("images_colour_font", locale), value=data["blackorwhite_text"], inline=True)
            embed.set_thumbnail(url=data["image"])
            embed.set_image(url=data["image_gradient"])
            return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="colourify", aliases=["blurple", "colorify"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def colourify(self, ctx: commands.Context, user: discord.User = None, colour: str = "7289da"):
        """ Turn a user's avatar into a certain colour """
        if user is None:
            user = ctx.author
        z, y, x = "7289da", "Invalid value, using default.", "colourify"
        a = len(colour)
        c = colour
        try:
            int(c, base=16)
        except ValueError:
            await general.send(y, ctx.channel)
            c, a = z, 6
        if a == 3:
            d, e, f = c
            b = f"{d}{d}{e}{e}{f}{f}"
        elif a == 6:
            b = c
        else:
            await general.send(y, ctx.channel)
            b = z
        return await image_gen(ctx, user, x, f"{x}_{b}", f"c={b}")

    @commands.command(name="filter")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def filter(self, ctx: commands.Context, filter_name: str, *, who: discord.User = None):
        """ Let someone go through a filter
        Do //filter help to see allowed filters """
        user = who or ctx.author
        filters = ["blur", "invert", "b&w", "deepfry", "pixelate", "snow", "gay", "magik", "jpegify", "communist", "wide"]
        _filter = filter_name.lower()
        if _filter not in filters or _filter == "help":
            return await general.send(langs.gls("images_filter_filters", langs.gl(ctx.guild, self.db), "`, `".join(filters)), ctx.channel)
            # return await general.send(f"The allowed filter names are:\n`{'`, `'.join(filters)}`", ctx.channel)
        return await image_gen(ctx, user, f"filter/{_filter}", f"{_filter}_filter")

    @commands.command(name="woosh", aliases=["jokeoverhead"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def joke_over_head(self, ctx: commands.Context, who: discord.User = None):
        """ Joke over head """
        user = who or ctx.author
        return await image_gen(ctx, user, "jokeoverhead", "joke-over-head")

    @commands.command(name="amiajoke")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def am_i_a_joke(self, ctx: commands.Context, *, who: discord.User = None):
        """ Is a user a joke? """
        user = who or ctx.author
        return await image_gen(ctx, user, "amiajoke", f"is_{user.name.lower()}_a_joke")

    @commands.command(name="salty")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def salty(self, ctx: commands.Context, *, who: discord.User = None):
        """ Salty user """
        user = who or ctx.author
        return await image_gen(ctx, user, "salty", f"salty_{user.name.lower()}")

    @commands.command(name="floor")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def the_floor_is(self, ctx: commands.Context, user: discord.User, *text):
        """ The floor is... """
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
        locale = langs.gl(ctx.guild, self.db)
        parser = arg_parser.Arguments()
        parser.add_argument('input', nargs="+", default=None)
        parser.add_argument('-d', '--dark', action='store_true')
        parser.add_argument('-l', '--light', action='store_true')
        args, valid_check = parser.parse_args(text)
        if not valid_check:
            return await general.send(args, ctx.channel)
        input_text = urllib.parse.quote(' '.join(args.input))
        if len(input_text) > 500:
            return await general.send(langs.gls("images_supreme_limit", locale), ctx.channel)
            # return await general.send("The API for this command is limited to 500 characters.", ctx.channel)
        dol = ""
        if args.dark:
            dol = "&dark=true"
        if args.light:
            dol = "&light=true"
        if args.dark and args.light:
            return await general.send(langs.gls("images_supreme_dark_light", locale), ctx.channel)
            # return await general.send("You can't use both dark and light at the same time...", ctx.channel)
        return await api_img_creator(ctx, f"https://api.alexflipnote.dev/supreme?text={input_text}{dol}", "supreme.png")

    @commands.command(name="meme")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def meme_generator(self, ctx: commands.Context, *, text: commands.clean_content(fix_channel_mentions=True)):
        """ Create a meme """
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
            return await general.send(str(ctx.author), ctx.channel, file=discord.File(bio, filename="meme.png"))


def setup(bot):
    bot.add_cog(Images(bot))
