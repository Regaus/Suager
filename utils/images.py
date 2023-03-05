# This utility module has functions and data regarding image generation
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

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


def font_tester():
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
