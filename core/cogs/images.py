import random
import urllib.parse
from io import BytesIO

import discord
from discord.ext import commands

from core.utils import arg_parser, emotes, general, http
from languages import langs


async def image_gen(ctx: commands.Context, user: discord.User or discord.Member, link, filename=None, extra_args=None):
    # async with ctx.typing():
    if filename is None:
        filename = link
    avatar = user.avatar_url_as(size=512, format="png")
    extra = f"&{extra_args}" if extra_args is not None else ''
    return await api_img_creator(ctx, f"https://api.alexflipnote.dev/{link}?image={avatar}{extra}", f"{filename}.png", None)


async def api_img_creator(ctx: commands.Context, url, filename, content=None):
    filename += filename  # This is so that it won't complain about "filename" arg not being used for now
    embed = discord.Embed()
    embed.set_image(url=url)
    embed.set_footer(icon_url=ctx.author.avatar_url, text=f"Rendered by: {ctx.author}")
    return await general.send(content, ctx.channel, embed=embed)
    # a = await general.send("There appears to be a network problem at the moment... This message will be deleted when response is received.", ctx.channel)
    # async with ctx.channel.typing():
    #     req = await http.get(url, res_method="read")
    #     await a.delete()
    #     if req is None:
    #         return await general.send("An error occurred creating the image, try again later.", ctx.channel)
    #     bio = BytesIO(req)
    #     bio.seek(0)
    #     return await general.send(content, ctx.channel, file=discord.File(bio, filename=filename))


async def vac_api(ctx: commands.Context, link, filename=None, content=None):
    return await api_img_creator(ctx, f"https://vacefron.nl/api/{link}", f"{filename}.png" or f"{link.split('?')[0]}.png", content)


async def af_text(ctx: commands.Context, link, content=None):
    return await api_img_creator(ctx, f"https://api.alexflipnote.dev/{link}", f"{link.split('?')[0]}.png", content)


class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="colourify", aliases=["blurple", "colorify"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def colourify(self, ctx: commands.Context, user: discord.User = None, colour: str = "7289da", colour2: str = None):
        """ Turn a user's avatar into a certain colour """
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
        return await image_gen(ctx, user, x, f"{x}_{b}", f"c={b}{j}")

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
            return await general.send(langs.gls("images_filter_filters", langs.gl(ctx), "`, `".join(filters)), ctx.channel)
            # return await general.send(f"The allowed filter names are:\n`{'`, `'.join(filters)}`", ctx.channel)
        return await image_gen(ctx, user, f"filter/{_filter}", f"{_filter}_filter")

    @commands.command(name="woosh", aliases=["jokeoverhead"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def joke_over_head(self, ctx: commands.Context, who: discord.User = None):
        """ Joke over head """
        user = who or ctx.author
        return await image_gen(ctx, user, "jokeoverhead", "joke-over-head")

    @commands.command(name="amiajoke")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def am_i_a_joke(self, ctx: commands.Context, *, who: discord.User = None):
        """ Is a user a joke? """
        user = who or ctx.author
        return await image_gen(ctx, user, "amiajoke", f"is_{user.name.lower()}_a_joke")

    @commands.command(name="salty")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def salty(self, ctx: commands.Context, *, who: discord.User = None):
        """ Salty user """
        user = who or ctx.author
        return await image_gen(ctx, user, "salty", f"salty_{user.name.lower()}")

    @commands.command(name="floor")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
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

    @commands.command(name="achievement")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def achievement(self, ctx: commands.Context, *, text: str):
        """ Minecraft Achievement """
        return await af_text(ctx, f"achievement?text={urllib.parse.quote(text)}")

    @commands.command(name="challenge")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def challenge(self, ctx: commands.Context, *, text: str):
        """ Minecraft Challenge """
        return await af_text(ctx, f"challenge?text={urllib.parse.quote(text)}")

    @commands.command(name="calling")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def calling(self, ctx: commands.Context, *, text: str):
        return await af_text(ctx, f"calling?text={urllib.parse.quote(text)}")

    @commands.command(name="captcha")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def captcha(self, ctx: commands.Context, *, text: str):
        """ You are a robot. """
        return await af_text(ctx, f"captcha?text={urllib.parse.quote(text)}")

    @commands.command(name="facts")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def facts(self, ctx: commands.Context, *, text: str):
        """ That is by now a fact """
        return await af_text(ctx, f"facts?text={urllib.parse.quote(text)}")

    @commands.command(name="scroll")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def scroll(self, ctx: commands.Context, *, text: str):
        """ Scroll of truth """
        return await af_text(ctx, f"scroll?text={urllib.parse.quote(text)}")

    @commands.command(name="didyoumean")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def didyoumean(self, ctx: commands.Context, *, text: commands.clean_content(fix_channel_mentions=True)):
        """ Did you mean something else """
        _text = str(text)
        _split = _text.split(" | ", 1)
        if len(_split) != 2:
            return await general.send(langs.gls("images_npc_split", langs.gl(ctx)), ctx.channel)
        t1, t2 = _split
        return await af_text(ctx, f"didyoumean?top={urllib.parse.quote(t1)}&bottom={urllib.parse.quote(t2)}")

    @commands.command(name="drake")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def drake(self, ctx: commands.Context, *, text: commands.clean_content(fix_channel_mentions=True)):
        _text = str(text)
        _split = _text.split(" | ", 1)
        if len(_split) != 2:
            return await general.send(langs.gls("images_npc_split", langs.gl(ctx)), ctx.channel)
        t1, t2 = _split
        return await af_text(ctx, f"didyoumean?top={urllib.parse.quote(t1)}&bottom={urllib.parse.quote(t2)}")

    @commands.command()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def supreme(self, ctx: commands.Context, *, text: commands.clean_content(fix_channel_mentions=True)):
        """ Make a Supreme logo

        Arguments:
            --dark | Make the background dark
            --light | Make background light
        """
        locale = langs.gl(ctx)
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
        dol = ""
        if args.dark:
            dol = "&dark=true"
        if args.light:
            dol = "&light=true"
        if args.dark and args.light:
            return await general.send(langs.gls("images_supreme_dark_light", locale), ctx.channel)
        return await api_img_creator(ctx, f"https://api.alexflipnote.dev/supreme?text={input_text}{dol}", "supreme.png")

    @commands.command(name="carreverse")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def car_reverse(self, ctx: commands.Context, *, text: commands.clean_content(fix_channel_mentions=True)):
        """ You see something and drive away """
        return await vac_api(ctx, f"carreverse?text={urllib.parse.quote(str(text))}")

    @commands.command(name="changemymind")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def change_my_mind(self, ctx: commands.Context, *, text: commands.clean_content(fix_channel_mentions=True)):
        """ Change my mind """
        return await vac_api(ctx, f"changemymind?text={urllib.parse.quote(str(text))}")

    @commands.command(name="distracted")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def distracted(self, ctx: commands.Context, boyfriend: discord.User, woman: discord.User, girlfriend: discord.User):
        """ Boyfriend getting distracted """
        a1, a2, a3 = [x.avatar_url_as(format="png", size=1024) for x in [boyfriend, woman, girlfriend]]
        return await vac_api(ctx, f"distractedbf?boyfriend={a1}&woman={a2}&girlfriend={a3}")

    @commands.command(name="water")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def no_water(self, ctx: commands.Context, *, text: commands.clean_content(fix_channel_mentions=True)):
        """ Why go to water? """
        return await vac_api(ctx, f"water?text={urllib.parse.quote(str(text))}")

    @commands.command(name="firsttime")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def first_time(self, ctx: commands.Context, *, who: discord.User = None):
        """ First time? """
        user = who or ctx.author
        return await vac_api(ctx, f"firsttime?user={user.avatar_url_as(format='png')}")

    @commands.command(name="grave")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def grave(self, ctx: commands.Context, *, who: discord.User = None):
        """ Someone died """
        user = who or ctx.author
        return await vac_api(ctx, f"grave?user={user.avatar_url_as(format='png')}")

    @commands.command(name="iamspeed")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def iamspeed(self, ctx: commands.Context, *, who: discord.User = None):
        """ I am speed """
        user = who or ctx.author
        return await vac_api(ctx, f"iamspeed?user={user.avatar_url_as(format='png')}")

    @commands.command(name="milk")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def i_can_milk_you(self, ctx: commands.Context, user1: discord.User, user2: discord.User = None):
        """ I can milk you """
        out = f"icanmilkyou?user1={user1.avatar_url_as(format='png')}"
        fn = f"milk_{user1.id}"
        if user2 is not None:
            out += f"&user2={user2.avatar_url_as(format='png')}"
            fn += f"_{user2.id}"
        return await vac_api(ctx, out, fn)

    @commands.command(name="heaven")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def heaven(self, ctx: commands.Context, *, who: discord.User = None):
        """ Stairs to Heaven """
        user = who or ctx.author
        return await vac_api(ctx, f"heaven?user={user.avatar_url_as(format='png')}")

    @commands.command(name="stonks")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def stonks(self, ctx: commands.Context, *, who: discord.User = None):
        """ Stonks """
        user = who or ctx.author
        return await vac_api(ctx, f"stonks?user={user.avatar_url_as(format='png')}")

    @commands.command(name="tableflip")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def tableflip(self, ctx: commands.Context, *, who: discord.User = None):
        """ Someone be angry """
        user = who or ctx.author
        return await vac_api(ctx, f"tableflip?user={user.avatar_url_as(format='png')}")

    @commands.command(name="npc")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def npc(self, ctx: commands.Context, *, text: commands.clean_content(fix_channel_mentions=True)):
        """ NPC meme """
        _text = str(text)
        _split = _text.split(" | ", 1)
        if len(_split) != 2:
            return await general.send(langs.gls("images_npc_split", langs.gl(ctx)), ctx.channel)
        t1, t2 = _split
        return await vac_api(ctx, f"npc?text1={urllib.parse.quote(t1)}&text2={urllib.parse.quote(t2)}")

    @commands.command(name="ship")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def ship(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Build a ship """
        locale = langs.gl(ctx)
        pr = False
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            if user1.id != 302851022790066185 and user2.id != 302851022790066185:
                return await general.send(f"{emotes.Deny} {langs.gls('generic_no', locale)}.", ctx.channel)
            pr = True
        if (user1.bot ^ user2.bot) and not pr:
            return await general.send(langs.gls("social_ship_bot", locale), ctx.channel)
        if user1 == user2:
            return await general.send(langs.gls("social_alone", locale), ctx.channel)
        av1 = user1.avatar_url_as(size=1024)
        av2 = user2.avatar_url_as(size=1024)
        link = f"https://api.alexflipnote.dev/ship?user={av1}&user2={av2}"
        bio = BytesIO(await http.get(link, res_method="read"))
        if bio is None:
            return await general.send("The image was not generated...", ctx.channel)
        __names = [len(user1.name), len(user2.name)]
        _names = [int(x / 2) for x in __names]
        n1 = user1.name[:_names[0]]
        n2 = user1.name[_names[0]:]
        n3 = user2.name[:_names[1]]
        n4 = user2.name[_names[1]:]
        names = [f"{n1}{n3}", f"{n1}{n4}", f"{n2}{n3}", f"{n2}{n4}", f"{n3}{n1}", f"{n4}{n1}", f"{n3}{n2}", f"{n4}{n2}"]
        message = langs.gls("social_ship", locale)
        for i, j in enumerate(names, start=1):
            message += f"\n{langs.gns(i, locale)}) **{j}**"
        return await general.send(message, ctx.channel, file=discord.File(bio, filename="ship.png"))

    @commands.command(name="bad")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def bad(self, ctx: commands.Context, user: discord.User):
        """ Bad user """
        locale = langs.gl(ctx)
        bad_self = False
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.id == 302851022790066185:
            bad_self = True
        elif user.id == self.bot.user.id:
            return await general.send(langs.gls("social_bad_suager", locale), ctx.channel)
        if bad_self:
            user = ctx.author
        return await image_gen(ctx, user, "bad", f"bad_{user.id}")

    @commands.command(name="trash")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def trash(self, ctx, user: discord.User):
        """ Show someone their home """
        locale = langs.gl(ctx)
        if user == ctx.author:
            return await general.send(emotes.AlexPat, ctx.channel)
        if user.id == self.bot.user.id:
            return await general.send(langs.gls("social_bad_suager", locale), ctx.channel)
        a1, a2 = [ctx.author.avatar_url, user.avatar_url]
        if user.id == 302851022790066185:
            a2, a1 = a1, a2
        bio = BytesIO(await http.get(f"https://api.alexflipnote.dev/trash?face={a1}&trash={a2}", res_method="read"))
        if bio is None:
            return await general.send("An error occurred...", ctx.channel)
        return await general.send(None, ctx.channel, file=discord.File(bio, filename=f"trash_{user.id}.png"))


def setup(bot):
    bot.add_cog(Images(bot))
