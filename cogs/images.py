from __future__ import annotations

import random
from io import BytesIO
from typing import Callable, Concatenate

import discord
from PIL import Image, UnidentifiedImageError
from discord import app_commands

from utils import bot_data, commands, emotes, http, images, languages
from utils.general import username

ALL_FILTERS: list[str] = ["blur", "communist", "deepfry", "flip", "gay", "grayscale", "invert", "jpegify", "magik", "mirror",
                          "pixelate", "rank", "rotate_90", "rotate_180", "rotate_270", "sepia", "snow", "spread", "wide"]
FILTER_CHOICES: list[app_commands.Choice[str]] = [
    # app_commands.Choice(name="List available filters", value="list"),
    app_commands.Choice(name="Random filter", value="random"),
    app_commands.Choice(name="Blur", value="blur"),
    app_commands.Choice(name="Communist", value="communist"),
    app_commands.Choice(name="Deepfry", value="deepfry"),
    app_commands.Choice(name="Equalise", value="equalise"),
    app_commands.Choice(name="Flip vertically", value="flip"),
    app_commands.Choice(name="Gay", value="gay"),
    app_commands.Choice(name="Grayscale (Black and white)", value="grayscale"),
    app_commands.Choice(name="Invert colours", value="invert"),
    app_commands.Choice(name="Jpegify", value="jpegify"),
    app_commands.Choice(name="Magik", value="magik"),
    app_commands.Choice(name="Mirror (Flip horizontally)", value="mirror"),
    app_commands.Choice(name="Pixelate", value="pixelate"),
    app_commands.Choice(name="Rank filter", value="rank"),
    app_commands.Choice(name="Rotate by 90 degrees", value="rotate_90"),
    app_commands.Choice(name="Rotate by 180 degrees", value="rotate_180"),
    app_commands.Choice(name="Rotate by 270 degrees", value="rotate_270"),
    app_commands.Choice(name="Sepia", value="sepia"),
    app_commands.Choice(name="Snow", value="snow"),
    app_commands.Choice(name="Spread pixels", value="spread"),
    app_commands.Choice(name="Wide", value="wide"),
]


# Note: Because the commands are deferred with ephemeral=False, error outputs have to be permanent messages too, rather than being ephemeral.
class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def _process_image[**P](ctx: commands.Context, language: languages.Language, asset: discord.Asset | discord.Attachment,
                                  function: Callable[Concatenate[Image.Image, P], Image.Image | list[Image.Image]], *fn_args: P, filename: str):
        """ Generic function to process the image and apply a certain filter to it """
        async with ctx.typing(ephemeral=False):
            bio = BytesIO()
            await asset.save(bio)
            try:
                image = Image.open(bio)
            except UnidentifiedImageError:
                return await ctx.send(language.string("images_image_invalid"))
            output = function(image, *fn_args)
            output_bio = images.save_to_bio(output)
            if (filesize := output_bio.getbuffer().nbytes) <= ctx.filesize_limit:
                file_format = "gif" if isinstance(output, list) else "png"
                return await ctx.send(file=discord.File(output_bio, filename=f"{filename}.{file_format}"))
            else:
                return await ctx.send(language.string("images_filesize_too_large", size=language.bytes(filesize, precision=2), limit=language.bytes(ctx.filesize_limit, precision=2)))

    async def _colourify(self, ctx: commands.Context, asset: discord.Asset | discord.Attachment, _colour1: str, _colour2: str):
        language = ctx.language()
        try:
            colour1 = images.colour_hex_to_tuple(_colour1)
            colour2 = images.colour_hex_to_tuple(_colour2)
        except images.InvalidLength as e:
            return await ctx.send(language.string("images_colour_invalid_value", value=e.value, length=e.length), ephemeral=True)
        except images.InvalidColour as e:
            return await ctx.send(language.string("images_colour_invalid", value=e.value, err=e.error), ephemeral=True)
        return self._process_image(ctx, language, asset, images.colourify, colour1, colour2, filename="colourify")

    @commands.hybrid_group("colourify")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def colourify(self, ctx: commands.Context):
        """ Filter an image around certain colours """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @colourify.command(name="avatar", aliases=["user"])
    @app_commands.describe(user="The user whose avatar to colourify",
                           colour1="The RGB colour that will replace the brighter parts of the image",
                           colour2="The RGB colour that will replace the darker parts of the image")
    async def colourify_avatar(self, ctx: commands.Context, user: discord.User = None, colour1: str = "7289da", colour2: str = "000000"):
        """ Colourify a user's avatar

         colour1 is the colour to replace brighter parts of the image with.
         colour2 is the colour to replace darker parts of the image with. """
        user = user or ctx.author
        return await self._colourify(ctx, user.avatar, colour1, colour2)

    @colourify.command(name="image", aliases=["file", "attachment"])
    @app_commands.rename(attachment="image")
    @app_commands.describe(attachment="The image to colourify",
                           colour1="The RGB colour that will replace the brighter parts of the image",
                           colour2="The RGB colour that will replace the darker parts of the image")
    async def colourify_attachment(self, ctx: commands.Context, attachment: discord.Attachment, colour1: str = "7289da", colour2: str = "000000"):
        """ Colourify an attached image

         When using as a text-based command, attach the image with the command message: `//colourify image 7289da 000000` + file attached

         colour1 is the colour to replace brighter parts of the image with.
         colour2 is the colour to replace darker parts of the image with. """
        return await self._colourify(ctx, attachment, colour1, colour2)

    async def _filter(self, ctx: commands.Context, asset: discord.Asset | discord.Attachment, filter_name: str):
        language = ctx.language()
        filter_name = filter_name.lower()
        if filter_name == "random":
            filter_name = random.choice(ALL_FILTERS)
        elif filter_name == "list":
            return await ctx.send(language.string("images_filter_filters", filters="`, `".join(ALL_FILTERS)), ephemeral=True)
        match filter_name:
            case "communist" | "gay" | "snow":  # Overlay filters
                return await self._process_image(ctx, language, asset, images.overlay_filter, filter_name, filename=filter_name)
            case "b&w" | "grayscale" | "greyscale":  # b&w is an alias of grayscale
                return await self._process_image(ctx, language, asset, images.grayscale, filename="grayscale")
            case "flip":
                return await self._process_image(ctx, language, asset, images.flip_vertically, filename=filter_name)
            case "mirror":
                return await self._process_image(ctx, language, asset, images.flip_horizontally, filename=filter_name)
            case "rotate_90" | "rotate_180" | "rotate_270":
                degrees = int(filter_name.removeprefix("rotate_"))
                return await self._process_image(ctx, language, asset, images.rotate, degrees, filename=filter_name)
            case "blur" | "deepfry" | "equalise" | "invert" | "jpegify" | "magik" | "pixelate" | "rank" | "sepia" | "spread" | "wide":
                # These filters' names match the internal function name
                return await self._process_image(ctx, language, asset, getattr(images, filter_name), filename=filter_name)
            case _:
                return await ctx.send(language.string("images_filter_invalid", filter_name=filter_name), ephemeral=True)

    @commands.hybrid_group("filter")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def filter(self, ctx: commands.Context):
        """ Filter an image around certain colours

         Note: The magik filter does not support animated images """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @filter.command(name="list", aliases=["help"])
    async def filter_list(self, ctx: commands.Context):
        """ List available filters """
        return await ctx.send(ctx.language().string("images_filter_filters", filters="`, `".join(ALL_FILTERS)), ephemeral=True)

    @filter.command(name="avatar", aliases=["user"])
    @app_commands.rename(filter_name="filter")
    @app_commands.describe(user="The user whose avatar to apply the filter on",
                           filter_name="The filter to apply. Defaults to random.")
    @app_commands.choices(filter_name=FILTER_CHOICES)
    async def filter_avatar(self, ctx: commands.Context, user: discord.User = None, filter_name: str = "random"):
        """ Apply a filter to a user's avatar """
        user = user or ctx.author
        return await self._filter(ctx, user.avatar, filter_name)

    @filter.command(name="image", aliases=["file", "attachment"])
    @app_commands.rename(attachment="image", filter_name="filter")
    @app_commands.describe(attachment="The image to apply the filter on",
                           filter_name="The filter to apply. Defaults to random.")
    @app_commands.choices(filter_name=FILTER_CHOICES)
    async def filter_attachment(self, ctx: commands.Context, attachment: discord.Attachment, filter_name: str = "random"):
        """ Apply a filter to a given image

         When using as a text-based command, attach the image with the command message: `//filter image random` + file attached """
        return await self._filter(ctx, attachment, filter_name)

    @commands.hybrid_command(name="ship")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.rename(user1="member1", user2="member2")
    @app_commands.describe(user1="The member to put on the left hand side", user2="The member to put on the right hand side")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)  # Can't be used in the bot's DMs
    @app_commands.allowed_installs(guilds=True, users=True)
    async def ship(self, ctx: commands.Context, user1: discord.User, user2: discord.User):
        """ Ship two members together """
        language = self.bot.language(ctx)
        pr = False
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            if user1.id != 302851022790066185 and user2.id != 302851022790066185:
                return await ctx.send(f"{emotes.Deny} {language.string('generic_no')}.", ephemeral=True)
            pr = True
        if (user1.bot ^ user2.bot) and not pr:
            return await ctx.send(language.string("social_ship_bot"), ephemeral=True)
        if user1 == user2:
            return await ctx.send(language.string("social_ship_alone"), ephemeral=True)
        av1 = str(user1.display_avatar.replace(size=512, format="png"))
        av2 = str(user2.display_avatar.replace(size=512, format="png"))
        # link = f"https://api.alexflipnote.dev/ship?user={av1}&user2={av2}"
        name1 = username(user1)
        name2 = username(user2)
        __names = [len(name1), len(name2)]
        _names = [int(x / 2) for x in __names]
        n1 = name1[:_names[0]]
        n2 = name1[_names[0]:]
        n3 = name2[:_names[1]]
        n4 = name2[_names[1]:]
        names = [f"{n1}{n3}", f"{n1}{n4}", f"{n2}{n3}", f"{n2}{n4}", f"{n3}{n1}", f"{n4}{n1}", f"{n3}{n2}", f"{n4}{n2}"]
        message = language.string("social_ship", name=random.choice(names))
        # for i, j in enumerate(names, start=1):
        #     message += f"\n{i}) **{j}**"
        # img = Image.new("RGB", (1536, 512), color=(0, 0, 0))
        async with ctx.typing(ephemeral=False):
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
            return await ctx.send(message, file=discord.File(bio, filename="ship.png"), ephemeral=False)
        # return await af_img_creator(ctx, link, "ship.png", message)


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Images(bot))
