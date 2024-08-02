import io
import json
import os.path
from contextlib import suppress
from math import radians as rad, degrees as deg, cos, sinh, tan, atan, pi, log

from PIL import Image, UnidentifiedImageError, ImageFont, ImageDraw
from regaus import time

from utils import http, logger
from utils.general import print_error, make_dir


__all__ = (
    "MAP_SIZE", "TILE_SIZE", "DEFAULT_ZOOM",
    "deg_to_xy_float", "deg_to_xy", "xy_to_deg", "download_images", "get_map_with_buses"
)

from utils.timetables import VehicleData, Route, get_database

DELTA = range(-2, 3)
START = min(DELTA)
END = max(DELTA)
MAP_SIZE = len(DELTA)
TILE_SIZE = 256
DEFAULT_ZOOM = 17


def deg_to_xy_float(lat: float, lon: float, zoom: int) -> tuple[float, float]:
    """ Convert lat/long in degrees to x,y coordinates (as floats) """
    lat_rad: float = rad(lat)
    n: float = 2. ** zoom
    x: float = (lon + 180) / 360 * n
    y: float = (1 - log(tan(lat_rad) + (1 / cos(lat_rad))) / pi) / 2 * n
    return x, y


def deg_to_xy(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    """ Convert lat/long in degrees to x,y coordinates (as integers) """
    x, y = deg_to_xy_float(lat, lon, zoom)
    return int(x), int(y)


def xy_to_deg(x: float, y: float, zoom: int) -> tuple[float, float]:
    """ Convert x,y coordinates to lat/long in degrees """
    n: float = 2. ** zoom
    lon: float = x / n * 360 - 180
    lat: float = deg(atan(sinh(pi * (1 - 2 * y / n))))
    return lat, lon


async def download_images(lat: float, lon: float, zoom: int = DEFAULT_ZOOM):  # -> tuple[Image, int, int]
    """ Download an image of the area surrounding (lat, long) at a particular zoom level.

    Returns an image instance and the x,y coordinates of the top left corner of the map. """
    base_url = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    x, y = deg_to_xy(lat, lon, zoom)
    img_size = TILE_SIZE * MAP_SIZE

    output = Image.new("RGB", (img_size, img_size))
    for dx in DELTA:
        for dy in DELTA:
            req_download = True
            _x = x + dx
            _y = y + dy
            tile = None
            try:
                path = "data/maps/{z}/{x}/{y}".format(z=zoom, x=_x, y=_y)
                if os.path.isdir(path):
                    listdir = os.listdir(path)
                    if len(listdir) == 1 and os.path.isfile(file_path := os.path.join(path, listdir[0])):
                        expiry = int(os.path.splitext(listdir[0])[0])  # The rest of the path doesn't matter, only the filename
                        if time.datetime.now().timestamp < expiry:
                            # print(f"Debug: Found cached tile at {file_path}")
                            tile = Image.open(file_path)
                            req_download = False
            except (FileNotFoundError, ValueError):
                pass  # Require downloading if there are problems getting the file
            if req_download:
                # print(f"Debug: Tile for {zoom}/{_x}/{_y} not found. Downloading...")
                tile_url = base_url.format(z=zoom, x=_x, y=_y)
                try:
                    version = json.load(open("version.json", "r"))["timetables"]["version"]
                except (FileNotFoundError, KeyError):
                    version = "1.0.0"
                bio = io.BytesIO(await http.get(tile_url, res_method="read", headers={"User-Agent": f"RegausGTFSBot/{version}"}))
                try:
                    tile = Image.open(bio)
                    try:
                        expiry = int(time.datetime.now().timestamp + 86400 * 30)  # The cached image will expire 30 days from now
                        make_dir(f"data/maps/{zoom}")
                        make_dir(f"data/maps/{zoom}/{_x}")
                        make_dir(f"data/maps/{zoom}/{_x}/{_y}")
                        path = f"data/maps/{zoom}/{_x}/{_y}/{expiry}.png"
                        tile.save(path, "PNG")
                    except OSError:
                        # If there's an error while saving the file, silently try to remove whatever was left
                        with suppress(FileNotFoundError, UnboundLocalError):
                            # noinspection PyUnboundLocalVariable
                            os.remove(path)
                except UnidentifiedImageError:
                    message = f"{time.datetime.now():%d %b %Y, %H:%M:%S} > Failed to load map tile: {zoom=}, x={_x}, y={_y}."
                    print_error(message)
                    logger.log("timetables", "errors", message)
                    tile = Image.open("assets/error_256.png")
            if tile is None:
                tile = Image.open("assets/error_256.png")
            output.paste(tile, box=((dx + END) * 256, (dy + END) * 256))
    return output, x + START, y + START


async def get_map_with_buses(lat: float, lon: float, zoom: int, vehicle_data: VehicleData) -> io.BytesIO:
    """ Get the """
    image, x1, y1 = await download_images(lat, lon, zoom)
    x2, y2 = x1 + MAP_SIZE, y1 + MAP_SIZE
    w, h = image.size
    font = ImageFont.truetype("assets/fonts/font.ttf", 24)
    font_bus = ImageFont.truetype("assets/fonts/font.ttf", 24)
    draw = ImageDraw.Draw(image)
    # Add map attribution text
    draw.text((w - 4, h), "Map data from OpenStreetMap", fill=(48, 48, 48), font=font, anchor="rd")  # Draw on bottom right

    # Draw the location of the stop you're looking at
    stop_x, stop_y = deg_to_xy_float(lat, lon, zoom)
    start_x = (stop_x - x1) * TILE_SIZE
    start_y = (stop_y - y1) * TILE_SIZE
    draw.circle((start_x, start_y), radius=12, fill=(1, 64, 132), outline=(0, 0, 0), width=2)

    # Draw all the buses in the area
    db = get_database()
    lat1, lon1 = xy_to_deg(x1, y1, zoom)
    lat2, lon2 = xy_to_deg(x2, y2, zoom)
    lat_min, lat_max = min((lat1, lat2)), max((lat1, lat2))
    lon_min, lon_max = min((lon1, lon2)), max((lon1, lon2))
    del lat1, lon1, lat2, lon2
    for vehicle in vehicle_data.entities.values():
        if lat_min <= vehicle.latitude <= lat_max and lon_min <= vehicle.longitude <= lon_max:
            try:
                route = Route.from_sql(vehicle.trip.route_id, db).short_name
            except KeyError:
                route = vehicle.trip.route_id
            map_x, map_y = deg_to_xy_float(vehicle.latitude, vehicle.longitude, zoom)
            img_x = (map_x - x1) * TILE_SIZE
            img_y = (map_y - y1) * TILE_SIZE
            draw.rectangle((img_x - 30, img_y - 15, img_x + 30, img_y + 15), fill=(1, 133, 64), outline=(0, 0, 0), width=2)
            draw.text((img_x, img_y), text=route, fill=(255, 255, 255), font=font_bus, anchor="mm", stroke_width=1, stroke_fill=(0, 255, 114))

    bio = io.BytesIO()
    image.save(bio, "PNG")
    bio.seek(0)
    return bio
