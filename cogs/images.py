import random
from io import BytesIO

import discord
from discord.ext import commands
from PIL import Image, UnidentifiedImageError

from utils import emotes, general, http


async def af_image_gen(ctx: commands.Context, user: discord.User or discord.Member, link, filename=None, extra_args=None):
    # async with ctx.typing():
    if filename is None:
        filename = link
    avatar = user.avatar_url_as(size=2048, format="png")
    extra = f"&{extra_args}" if extra_args is not None else ''
    return await af_img_creator(ctx, f"https://api.alexflipnote.dev/{link}?image={avatar}{extra}", f"{filename}.png", None)


async def af_img_creator(ctx: commands.Context, url, filename, content=None):
    token = ctx.bot.config["alex_api_token"]
    lag = await general.send(f"{emotes.Loading} Getting response from the API... This may sometimes take a while...", ctx.channel)
    req = await http.get(url, headers={"Authorization": token}, res_method="read")
    # req = await http.get(url)
    await lag.delete()
    if req is None:
        return await general.send("No response was received, try again later.", ctx.channel)
    if type(req) == str:
        bio = BytesIO(req.encode("utf-8"))
        filename = filename[:-3] + "json"
    else:
        bio = BytesIO(req)
    bio.seek(0)
    return await general.send(content, ctx.channel, file=discord.File(bio, filename=filename))


async def api_img_creator(ctx: commands.Context, url, filename, content=None):
    filename += filename  # This is so that it won't complain about "filename" arg not being used for now
    embed = discord.Embed()
    embed.set_image(url=url)
    embed.set_footer(icon_url=ctx.author.avatar_url, text=f"Rendered by: {ctx.author}")
    return await general.send(content, ctx.channel, embed=embed)


async def vac_api(ctx: commands.Context, link, filename=None, content=None):
    return await api_img_creator(ctx, f"https://vacefron.nl/api/{link}", f"{filename}.png" or f"{link.split('?')[0]}.png", content)


async def af_text(ctx: commands.Context, link, content=None):
    return await af_img_creator(ctx, f"https://api.alexflipnote.dev/{link}", f"{link.split('?')[0]}.png", content)


class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="colourify", aliases=["blurple", "colorify"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def colourify(self, ctx: commands.Context, user: discord.User = None, colour: str = "7289da", colour2: str = None):
        """ Turn a user's avatar into a certain colour """
        # TODO: Rewrite this to use proper variable names...
        if user is None:
            user = ctx.author
        z, y, x = "7289da", "Invalid values", "colourify"
        a = len(colour)
        h = len(colour2) if colour2 is not None else 0
        c = colour
        try:
            int(c, base=16)
        except ValueError:
            await general.send(y, ctx.channel)
            c, a = z, 6
        g = colour2
        if g is not None:
            try:
                int(g, base=16)
            except ValueError:
                await general.send(y, ctx.channel)
                g, h = None, 0
        if a == 3:
            d, e, f = c
            b = f"{d}{d}{e}{e}{f}{f}"
        elif a == 6:
            b = c
        else:
            await general.send(y, ctx.channel)
            b = z
        if h == 3:
            k, l, m = g
            i = f"{k}{k}{l}{l}{m}{m}"
        elif h == 6:
            i = g
        elif h == 0:
            i = None
        else:
            await general.send(y, ctx.channel)
            i = None
        j = f"&b={i}" if i is not None else ""
        return await af_image_gen(ctx, user, x, f"{x}_{b}", f"c={b}{j}")

    @commands.command(name="filter")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def filter(self, ctx: commands.Context, filter_name: str, *, who: discord.User = None):
        """ Let someone go through a filter
        Enter "help" as filter name to see allowed filters
        Enter "random" for a random filter
        """
        user = who or ctx.author
        filters = ["blur", "invert", "b&w", "deepfry", "pixelate", "snow", "gay", "magik", "jpegify", "communist", "wide", "sepia"]
        _filter = filter_name.lower()
        if _filter == "random":
            _filter = random.choice(filters)
        elif _filter not in filters or _filter == "help":
            return await general.send(self.bot.language(ctx).string("images_filter_filters", "`, `".join(filters)), ctx.channel)
        return await af_image_gen(ctx, user, f"filter/{_filter}", f"{_filter}_filter")

    @commands.command(name="ship")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def ship(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Build a ship """
        language = self.bot.language(ctx)
        pr = False
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            if user1.id != 302851022790066185 and user2.id != 302851022790066185:
                return await general.send(f"{emotes.Deny} {language.string('generic_no')}.", ctx.channel)
            pr = True
        if (user1.bot ^ user2.bot) and not pr:
            return await general.send(language.string("social_ship_bot"), ctx.channel)
        if user1 == user2:
            return await general.send(language.string("social_alone"), ctx.channel)
        av1 = str(user1.avatar_url_as(size=512, format="png"))
        av2 = str(user2.avatar_url_as(size=512, format="png"))
        # link = f"https://api.alexflipnote.dev/ship?user={av1}&user2={av2}"
        __names = [len(user1.name), len(user2.name)]
        _names = [int(x / 2) for x in __names]
        n1 = user1.name[:_names[0]]
        n2 = user1.name[_names[0]:]
        n3 = user2.name[:_names[1]]
        n4 = user2.name[_names[1]:]
        names = [f"{n1}{n3}", f"{n1}{n4}", f"{n2}{n3}", f"{n2}{n4}", f"{n3}{n1}", f"{n4}{n1}", f"{n3}{n2}", f"{n4}{n2}"]
        message = language.string("social_ship")
        for i, j in enumerate(names, start=1):
            message += f"\n{i}) **{j}**"
        # img = Image.new("RGB", (1536, 512), color=(0, 0, 0))
        async with ctx.typing():
            img = Image.open("assets/ship.png")
            # First avatar
            try:
                avatar = BytesIO(await http.get(av1, res_method="read"))
                avatar_img = Image.open(avatar)
                avatar_resized = avatar_img.resize((512, 512))
                img.paste(avatar_resized)
            except UnidentifiedImageError:  # Failed to get image
                avatar = Image.open("assets/error.png")
                img.paste(avatar)
            # Second avatar
            try:
                avatar = BytesIO(await http.get(av2, res_method="read"))
                avatar_img = Image.open(avatar)
                avatar_resized = avatar_img.resize((512, 512))
                img.paste(avatar_resized, (1024, 0))
            except UnidentifiedImageError:  # Failed to get image
                avatar = Image.open("assets/error.png")
                img.paste(avatar, (1024, 0))
            bio = BytesIO()
            img.save(bio, "PNG")
            bio.seek(0)
            return await general.send(message, ctx.channel, file=discord.File(bio, filename="ship.png"))
        # return await af_img_creator(ctx, link, "ship.png", message)


def setup(bot):
    bot.add_cog(Images(bot))
