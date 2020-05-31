import json
import random
import urllib.parse
from io import BytesIO

import discord
from discord.ext import commands

from utils import http, argparser, generic


async def image_gen(ctx: commands.Context, user: discord.Member, link, filename=None, extra_args=None):
    async with ctx.typing():
        if filename is None:
            filename = link
        avatar = user.avatar_url_as(size=512, format="png")
        # print(avatar)
        extra = f"&{extra_args}" if extra_args is not None else ''
        bio = BytesIO(await http.get(f"https://api.alexflipnote.dev/{link}?image={avatar}{extra}", res_method="read"))
        if bio is None:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "image_not_created"), ctx.channel)
            # return await ctx.send("Something went wrong, couldn't generate image")
        return await generic.send(None, ctx.channel, file=discord.File(bio, filename=f"{filename}.png"))
        # return await ctx.send(file=discord.File(bio, filename=f"{filename}.png"))


async def api_img_creator(ctx: commands.Context, url, filename, content=None):
    async with ctx.channel.typing():
        req = await http.get(url, res_method="read")
        if req is None:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "image_not_created"), ctx.channel)
            # return await ctx.send("I couldn't create the image ;-;")
        bio = BytesIO(req)
        bio.seek(0)
        return await generic.send(content, ctx.channel, file=discord.File(bio, filename=filename))
        # await ctx.send(content=content, file=discord.File(bio, filename=filename))


class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="colour", aliases=["color"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def colour(self, ctx: commands.Context, colour: str):
        """ Colours! """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "colour"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        async with ctx.typing():
            # c = ctx.invoked_with
            c = generic.gls(locale, str(ctx.invoked_with).lower())
            c2 = c.capitalize()
            if colour == "random":
                _colour = hex(random.randint(0, 0xffffff))[2:]
                a = 6
            else:
                try:
                    _colour = hex(int(colour, base=16))[2:]
                    a = len(colour)
                    if a != 3 and a != 6:
                        return await generic.send(generic.gls(locale, "colour_value_len"), ctx.channel)
                        # return await ctx.send(f"Value must be either 3 or 6 digits long")
                except Exception as e:
                    return await generic.send(generic.gls(locale, "invalid_colour2", [c, c2, e]), ctx.channel)
                    # return await ctx.send(f"Invalid {c}: {e}\n{c.capitalize()} must be either `random` or a HEX value")
            try:
                _data = await http.get(f"https://api.alexflipnote.dev/colour/{_colour}", res_method="read")
                data = json.loads(_data)
            except json.JSONDecodeError:
                try:
                    _data = await http.get(f"https://api.alexflipnote.dev/colour/{colour}", res_method="read")
                    data = json.loads(_data)
                except json.JSONDecodeError:
                    return await generic.send(generic.gls(locale, "col_error"), ctx.channel)
                    # return await ctx.send("Something went wrong, try again")
            if a == 3:
                d, e, f = colour
                g = int(f"{d}{d}{e}{e}{f}{f}", base=16)
                embed = discord.Embed(colour=g)
            else:
                embed = discord.Embed(colour=int(colour, base=16))
            embed.add_field(name=generic.gls(locale, "hex_value"), value=data["hex"], inline=True)
            embed.add_field(name=generic.gls(locale, "rgb_value"), value=data["rgb"], inline=True)
            embed.add_field(name=generic.gls(locale, "integer"), value=data["int"], inline=True)
            embed.add_field(name=generic.gls(locale, "brightness"), value=data["brightness"], inline=True)
            embed.add_field(name=generic.gls(locale, "font_col", [c]), value=data["blackorwhite_text"], inline=True)
            embed.set_thumbnail(url=data["image"])
            embed.set_image(url=data["image_gradient"])
            return await generic.send(None, ctx.channel, embed=embed)
            # return await ctx.send(f"{c.capitalize()} name: **{data['name']}**", embed=embed)

    @commands.command(name="colourify", aliases=["blurple", "colorify"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
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
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
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
            # return await ctx.send(f"The allowed filter names are:\n`{filters}`")
        return await image_gen(ctx, user, f"filter/{_filter}", f"{_filter}_filter")

    @commands.command(name="woosh", aliases=["jokeoverhead"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
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
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
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
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
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
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
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
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
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
            # return await ctx.send(args)

        input_text = urllib.parse.quote(' '.join(args.input))
        if len(input_text) > 500:
            return await generic.send(generic.gls(locale, "supreme_limit", [ctx.author.name]), ctx.channel)
            # return await ctx.send(f"**{ctx.author.name}**, the Supreme API is only limited to 500 characters...")

        dol = ""
        if args.dark:
            dol = "&dark=true"
        if args.light:
            dol = "&light=true"
        if args.dark and args.light:
            return await generic.send(generic.gls(locale, "supreme_dark_light", [ctx.author.name]), ctx.channel)
            # return await ctx.send(f"**{ctx.author.name}**, can't you don't do both dark and light at the same time")

        return await api_img_creator(ctx, f"https://api.alexflipnote.dev/supreme?text={input_text}{dol}", "supreme.png")
        # await api_img_creator(ctx, f"https://api.alexflipnote.dev/supreme?text={input_text}{dol}", "supreme.png")


def setup(bot):
    bot.add_cog(Images(bot))
