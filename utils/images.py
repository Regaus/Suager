# This utility module has functions and data regarding image generation
from io import BytesIO
from typing import Callable, Concatenate

import numpy as np
import seam_carving
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageEnhance
from PIL.Image import Palette, Resampling
from PIL.ImageSequence import Iterator

MAX_SIZE = 512 * 512
MAX_FRAMES = 100

font_files = {
    "gg sans": "assets/fonts/gg_sans.ttf",
    "jetbrains mono": "assets/fonts/mono.ttf",
    "rajdhani": "assets/fonts/rajdhani.ttf",
    "whitney": "assets/fonts/font.ttf",
    "exo2": "assets/fonts/exo2.ttf",
}

# String used to test various fonts - English pangram, Russian pangram, Numbers and special chars
font_test_text = "The quick brown fox jumps over the lazy dog.\n" \
                 "Разъяренный чтец эгоистично бьёт пятью жердями шустрого фехтовальщика.\n" \
                 "0123456789 .:,; '\" (!?) +-*/= áéíóú àèìòù äöü ãõñ å æø ı šž şç đ þð ğ ħ œ ß"


def font_tester() -> BytesIO:
    """ Generates an image that displays currently available fonts """
    width = 2560
    height = 320 * len(font_files)
    img = Image.new("RGB", (width, height), color=(0, 0, 0))
    dr = ImageDraw.Draw(img)
    text_colour = (255, 255, 255)
    for i, (font_name, font_dir) in enumerate(font_files.items(), start=0):
        y = 320 * i
        font = ImageFont.truetype(font_dir, size=64)
        text = f"Font Name: {font_name}\n" + font_test_text
        dr.text((10, 160 + y), text, font=font, fill=text_colour, anchor="lm")
        dr.rectangle((0, 315 + y, width, 320 + y), fill=text_colour)
    bio = BytesIO()
    img.save(bio, "PNG")
    bio.seek(0)
    return bio


def load_from_bytes(image: bytes) -> Image.Image:
    """ Load an image from a bytes object"""
    return Image.open(BytesIO(image))


def save_to_bio(image: Image.Image | list[Image.Image]) -> BytesIO:
    """ Save an image to a BytesIO object """
    bio = BytesIO()
    if isinstance(image, list):  # A sequence of frames of an animated image
        # The loop parameter is stored in the frame info, but specify it here just in case
        # The disposal=2 parameter means that frames do not linger, which prevents weird outputs for transparent gifs
        image[0].save(bio, format="GIF", append_images=image[1:], save_all=True, loop=image[0].info.get("loop", 1), disposal=2)
    else:
        image.save(bio, "PNG")
    bio.seek(0)
    return bio


def save_to_bytes(image: Image.Image | list[Image.Image]) -> bytes:
    """ Save an image into a regular Python bytes object """
    bio = save_to_bio(image)
    return bio.read()


class InvalidLength(ValueError):
    """ Exception raised when the specified colour is of invalid length """
    def __init__(self, text: str, value: str, length: int):
        super().__init__(text)
        self.value = value
        self.length = length
        """ The actual length of the provided colour """


class InvalidColour(ValueError):
    """ Exception raised when the specified colour cannot be converted to a valid integer """
    def __init__(self, text: str, value: str, error: Exception):
        super().__init__(text)
        self.value = value
        self.error = error


def colour_hex_to_tuple(colour: str) -> tuple[int, int, int]:
    """ Convert a hexadecimal colour string into an (r, g, b) tuple """
    return colour_int_to_tuple(colour_hex_to_int(colour))


def colour_hex_to_int(colour: str) -> int:
    """ Convert a hexadecimal colour string into an integer """
    if colour[0] == "#":
        colour = colour[1:]
    length = len(colour)
    if length == 3:
        a, b, c = colour
        colour = f"{a}{a}{b}{b}{c}{c}"
    elif length != 6:
        raise InvalidLength("The colour value must be either 3 or 6 characters long.", colour, length)
    try:
        return int(colour, base=16)
    except ValueError as e:
        raise InvalidColour("Colour cannot be converted from HEX", colour, e) from None


def colour_int_to_tuple(colour: int) -> tuple[int, int, int]:
    """ Convert an integer colour into an (r, g, b) tuple """
    r, g = divmod(colour, 256 ** 2)
    g, b = divmod(g, 256)
    return r, g, b


# These functions are used by the Images cog
def _resize_image(image: Image.Image) -> Image.Image:
    """ Resize the image to have no more than 512x512 pixels and return the new image"""
    image = image.convert("RGBA")
    width, height = image.size
    pixels = width * height
    if pixels > MAX_SIZE:
        fraction: float = (pixels / MAX_SIZE) ** 0.5
        width: int = int(width / fraction)
        height: int = int(height / fraction)
        image = image.resize((width, height))
    return image


def _wrap_animated[**P](image: Image.Image, function: Callable[Concatenate[Image.Image, P], Image.Image], *fn_args: P, max_frames: int = MAX_FRAMES) -> Image.Image | list[Image.Image]:
    """ Generic wrapper around the if-statement regarding animated and still images """
    if max_frames > 1 and getattr(image, "is_animated", False):  # Magik is too resource-intensive to support gifs
        return _handle_animated(image, function, *fn_args, max_frames=max_frames)
    else:
        return function(image, *fn_args)


def _handle_animated[**P](image: Image.Image, function: Callable[Concatenate[Image.Image, P], Image.Image], *fn_args: P, max_frames: int = MAX_FRAMES) -> list[Image.Image]:
    """ Handle animated images

     Function signature: function(image, *everything_else) -> new_image """
    frames = []
    loop = image.info.get("loop", 1)
    n_frames = getattr(image, "n_frames", 1)
    idx = saved_frames = 0
    fraction = (n_frames / max_frames) if n_frames > max_frames else 1
    for frame in Iterator(image):
        idx += 1
        if n_frames > max_frames and (idx / n_frames * max_frames) < saved_frames:
            continue  # If there are over 100 frames, skip some to only have up to 100 in the output
        saved_frames += 1
        new_frame = function(frame, *fn_args)
        new_frame.info["duration"] = frame.info["duration"] * fraction  # Extend the duration of each frame by the ratio of skipped frames
        new_frame.info["loop"] = loop
        frames.append(new_frame)
    return frames


def _rgb_operation(image: Image.Image, function: Callable[[Image.Image], Image.Image]) -> Image.Image:
    """ Wrapper around functions that only support RGB operations """
    image = _resize_image(image)
    r, g, b, a = image.split()
    rgb_image = Image.merge("RGB", (r, g, b))
    rgb_image = function(rgb_image)
    r, g, b = rgb_image.split()
    return Image.merge("RGBA", (r, g, b, a))


def _colourify(image: Image.Image, colour1: tuple[int, int, int], colour2: tuple[int, int, int]) -> Image.Image:
    """ Reduce the image to a work of art with just two colours """
    image = _resize_image(image)
    pixels = image.getdata()
    # This iterates over the image twice, which I guess might not be ideal, but whatever. it works.
    brightnesses = []
    for r, g, b, _ in pixels:
        # https://stackoverflow.com/a/596243
        brightnesses.append(0.2126 * r + 0.7152 * g + 0.0722 * b)
    middle = sum(brightnesses) / len(brightnesses)
    # middle = sum(px[0] for px in pixels) / len(pixels)
    output_pixels = []
    for r, g, b, alpha in pixels:
        brightness = 0.2126 * r + 0.7152 * g + 0.0722 * b
        if brightness > middle:
            output_pixels.append((*colour1, alpha))
        else:
            output_pixels.append((*colour2, alpha))
    new_image = Image.new("RGBA", image.size)
    new_image.putdata(output_pixels)
    return new_image


def _overlay_filter(image: Image.Image, overlay: str) -> Image.Image:
    """ Overlay an image over an existing image """
    image = _resize_image(image)
    overlay = Image.open(f"assets/filters/{overlay}.png")
    width, height = image.size
    overlay = overlay.resize((width, height))
    image.paste(overlay, (0, 0), overlay)
    return image


def _blur(image: Image.Image) -> Image.Image:
    """ Blur the image """
    image = _resize_image(image)
    return image.filter(ImageFilter.GaussianBlur(radius=2.5))


def _deepfry(image: Image.Image) -> Image.Image:
    """ Deep-fry the image """
    # https://github.com/KagChi/alex_api_archive/blob/master/render/filter.py#L62-L77
    image = _resize_image(image)
    image = image.convert("RGB")
    width, height = image.size
    image = image.resize((int(width ** 0.75), int(height ** 0.75)), resample=Resampling.LANCZOS)
    image = image.resize((int(width ** 0.88), int(height ** 0.88)), resample=Resampling.BILINEAR)
    image = image.resize((int(width ** 0.90), int(height ** 0.90)), resample=Resampling.BICUBIC)
    image = image.resize((width, height), resample=Resampling.BICUBIC)
    image = ImageOps.posterize(image, 4)  # Reduce the 8-bit channels to just 4 bits
    red = image.split()[0]
    red = ImageEnhance.Contrast(red).enhance(2.0)
    red = ImageEnhance.Brightness(red).enhance(1.5)
    red = ImageOps.colorize(red, (254, 0, 2), (255, 255, 15))
    image = Image.blend(image, red, 0.75)
    image = ImageEnhance.Sharpness(image).enhance(100.0)
    return image


def _equalise(image: Image.Image) -> Image.Image:
    """ Equalise the image histogram """
    return _rgb_operation(image, ImageOps.equalize)


def _flip_vertically(image: Image.Image) -> Image.Image:
    """ Flip the image vertically """
    image = _resize_image(image)
    return ImageOps.flip(image)


def _flip_horizontally(image: Image.Image) -> Image.Image:
    """ Flip the image horizontally """
    image = _resize_image(image)
    return ImageOps.mirror(image)


def _grayscale(image: Image.Image) -> Image.Image:
    """ Make the image black and white """
    image = _resize_image(image)
    return image.convert("LA")


def _invert(image: Image.Image) -> Image.Image:
    """ Invert the colours of the image """
    return _rgb_operation(image, ImageOps.invert)


def _jpegify(image: Image.Image) -> Image.Image:
    """ Apply the beauties of JPEG to the image """
    # https://github.com/KagChi/alex_api_archive/blob/master/render/filter.py#L41-L43
    image = _resize_image(image)
    image = image.convert("RGB")  # JPEG doesn't support the alpha channel
    bio = BytesIO()
    image.save(bio, format="JPEG", quality=10)  # 10 is very low
    bio.seek(0)
    return Image.open(bio)


def _magik(image: Image.Image) -> Image.Image:
    """ Apply seam-carving ("magik") to the image """
    image = _resize_image(image)

    def _rgb_magik(img: Image.Image) -> Image.Image:
        src = np.array(img)
        height, width, _ = src.shape
        dst = seam_carving.resize(src, (width // 2, height // 2), energy_mode="backward", order="width-first", keep_mask=None)
        out = seam_carving.resize(dst, (width, height), energy_mode="forward", order="height-first", keep_mask=None)
        return Image.fromarray(out)
    return _rgb_operation(image, _rgb_magik)


def _pixelate(image: Image.Image) -> Image.Image:
    """ Pixelate the image """
    # https://github.com/KagChi/alex_api_archive/blob/master/render/filter.py#L27-L40
    image = _resize_image(image)
    original_size = image.size
    image = ImageEnhance.Color(image).enhance(1.25)     # Boost image saturation
    image = ImageEnhance.Contrast(image).enhance(1.25)  # Boost image contrast
    image = image.convert("P", palette=Palette.ADAPTIVE)
    pixel_size = 8
    reduced_size = (original_size[0] // pixel_size, original_size[1] // pixel_size)
    image = image.resize(reduced_size, resample=Resampling.BICUBIC)
    image = image.resize(original_size, resample=Resampling.NEAREST)
    return image


def _rank(image: Image.Image) -> Image.Image:
    """ Apply a rank filter to the image """
    image = _resize_image(image)
    return _rgb_operation(image, lambda img: img.filter(ImageFilter.RankFilter(size=5, rank=0)))


def _rotate(image: Image.Image, degrees: int) -> Image.Image:
    """ Rotate the image by a given amount of degrees """
    image = _resize_image(image)
    return image.rotate(degrees, expand=True)


def _sepia(image: Image.Image) -> Image.Image:
    """ Apply a sepia filter over the image """
    image = _resize_image(image)
    pixels = image.getdata()
    output_pixels = []
    for r, g, b, alpha in pixels:
        # https://stackoverflow.com/a/9449159
        new_r = min(int(0.393 * r + 0.769 * g + 0.189 * b), 255)
        new_g = min(int(0.349 * r + 0.686 * g + 0.168 * b), 255)
        new_b = min(int(0.272 * r + 0.534 * g + 0.131 * b), 255)
        output_pixels.append((new_r, new_g, new_b, alpha))
    new_image = Image.new("RGBA", image.size)
    new_image.putdata(output_pixels)
    return new_image


def _spread(image: Image.Image) -> Image.Image:
    """ Randomly spread pixels of the image """
    image = _resize_image(image)
    return image.effect_spread(distance=16)


def _wide(image: Image.Image) -> Image.Image:
    """ Make the image wider """
    # https://github.com/KagChi/alex_api_archive/blob/master/render/filter.py#L78-L82
    image = _resize_image(image)
    width, height = image.size
    return image.resize((int(width * 1.25), int(height / 1.5)))


def colourify(image: Image.Image, colour1: tuple[int, int, int], colour2: tuple[int, int, int]) -> Image.Image | list[Image.Image]:
    """ Reduce the image to a work of art with just two colours """
    return _wrap_animated(image, _colourify, colour1, colour2)


def overlay_filter(image: Image.Image, overlay: str) -> Image.Image | list[Image.Image]:
    """ Overlay an image over an existing image """
    return _wrap_animated(image, _overlay_filter, overlay)


def blur(image: Image.Image) -> Image.Image | list[Image.Image]:
    """ Blur the image """
    return _wrap_animated(image, _blur)


def deepfry(image: Image.Image) -> Image.Image | list[Image.Image]:
    """ Deep-fry the image """
    return _wrap_animated(image, _deepfry)


def equalise(image: Image.Image) -> Image.Image | list[Image.Image]:
    """ Equalise the image histogram """
    return _wrap_animated(image, _equalise)


def flip_vertically(image: Image.Image) -> Image.Image | list[Image.Image]:
    """ Flip the image vertically """
    return _wrap_animated(image, _flip_vertically)


def flip_horizontally(image: Image.Image) -> Image.Image | list[Image.Image]:
    """ Flip the image horizontally """
    return _wrap_animated(image, _flip_horizontally)


def grayscale(image: Image.Image) -> Image.Image | list[Image.Image]:
    """ Make the image black and white """
    return _wrap_animated(image, _grayscale)


def invert(image: Image.Image) -> Image.Image | list[Image.Image]:
    """ Invert the colours of the image """
    return _wrap_animated(image, _invert)


def jpegify(image: Image.Image) -> Image.Image | list[Image.Image]:
    """ Apply the beauties of JPEG to the image """
    return _wrap_animated(image, _jpegify)


def magik(image: Image.Image) -> Image.Image | list[Image.Image]:
    """ Apply a seam-carving ("magik") effect on the image """
    return _wrap_animated(image, _magik, max_frames=1)  # Magik is too resource-intensive to allow gifs


def pixelate(image: Image.Image) -> Image.Image | list[Image.Image]:
    """ Pixelate the image """
    return _wrap_animated(image, _pixelate)


def rank(image: Image.Image) -> Image.Image | list[Image.Image]:
    """ Apply a rank filter to the image """
    return _wrap_animated(image, _rank)


def rotate(image: Image.Image, degrees: int) -> Image.Image | list[Image.Image]:
    """ Rotate the image by a given amount of degrees """
    return _wrap_animated(image, _rotate, degrees)


def sepia(image: Image.Image) -> Image.Image | list[Image.Image]:
    """ Apply a sepia filter over the image """
    return _wrap_animated(image, _sepia)


def spread(image: Image.Image) -> Image.Image | list[Image.Image]:
    """ Randomly spread pixels of the image """
    return _wrap_animated(image, _spread)


def wide(image: Image.Image) -> Image.Image | list[Image.Image]:
    """ Make the image wider """
    return _wrap_animated(image, _wide)
