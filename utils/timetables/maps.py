import io
import json
import os.path
from contextlib import suppress
from math import radians as rad, degrees as deg, cos, sinh, tan, atan, pi, log, asin

import numpy
from PIL import Image, UnidentifiedImageError, ImageFont, ImageDraw
from regaus import time

from utils import http, logger, conworlds
from utils.general import print_error, make_dir
from utils.timetables.shared import get_database
from utils.timetables.realtime import VehicleData
from utils.timetables.static import GTFSData, Route, Trip, Shape, load_value


__all__ = (
    "MAP_SIZE", "TILE_SIZE", "DEFAULT_ZOOM",
    "deg_to_xy_float", "deg_to_xy", "xy_to_deg", "download_images", "get_map_with_buses"
)


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

    output = Image.new("RGBA", (img_size, img_size))
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
                        else:
                            # Delete the file if it has expired
                            with suppress(FileNotFoundError):
                                os.remove(file_path)
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


async def get_map_with_buses(lat: float, lon: float, zoom: int, vehicle_data: VehicleData, static_data: GTFSData) -> io.BytesIO:
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
            # Get route data and draw the bus on a temporary image
            try:
                # route = Route.from_sql(vehicle.trip.route_id, db).short_name
                route = load_value(static_data, Route, vehicle.trip.route_id, db).short_name
            except KeyError:
                route = vehicle.trip.route_id
            map_x, map_y = deg_to_xy_float(vehicle.latitude, vehicle.longitude, zoom)
            img_x = int((map_x - x1) * TILE_SIZE)
            img_y = int((map_y - y1) * TILE_SIZE)
            bus_image = Image.new("RGBA", (100, 30), (0, 0, 0, 0))
            bus_draw = ImageDraw.Draw(bus_image)
            bus_draw.rectangle((20, 0, 80, 30), fill=(1, 133, 64), outline=(0, 0, 0), width=2)
            bus_draw.text((50, 15), text=route, fill=(255, 255, 255), font=font_bus, anchor="mm", stroke_width=1, stroke_fill=(0, 255, 114))
            # Calculate the direction the bus is moving in
            try:
                # trip = Trip.from_sql(vehicle.trip.trip_id, db)
                # shape = Shape.from_sql(trip.shape_id, db)
                trip: Trip = load_value(static_data, Trip, vehicle.trip.trip_id, db)
                shape: Shape = trip.shape()
                lat1, lon1 = vehicle.latitude, vehicle.longitude
                distances: dict[int, float] = {}
                min_distance = float("inf")
                sequence1 = 0
                for point in shape.shape_points.values():
                    distance = conworlds.distance_between_places(lat1, lon1, point.latitude, point.longitude, "Earth")
                    distances[point.sequence] = distance
                    if distance < min_distance:
                        min_distance = distance
                        sequence1 = point.sequence
                step = 5  # Try to get the general direction, as going by precise points causes ridiculous results
                try:
                    prev_distance = distances[sequence1 - step]
                except KeyError:
                    prev_distance = float("inf")
                try:
                    next_distance = distances[sequence1 + step]
                except KeyError:
                    next_distance = float("inf")
                if prev_distance < next_distance:  # Closer to previous point than the next one
                    sequence1 -= step
                #     sequence2 = sequence1 - step
                # else:  # next_distance < prev_distance:  # Closer to next point than the previous one
                #     sequence2 = sequence1 + step
                sequence2 = sequence1 + step
                point1 = shape.shape_points[sequence1]
                point2 = shape.shape_points[sequence2]
                vector_x = point2.longitude - point1.longitude
                vector_y = point2.latitude - point1.latitude
                vector1 = numpy.array([vector_x, vector_y, 0])  # Remove the zero if the normalisation line below is uncommented
                # vector1 = (vector1 / numpy.expand_dims(numpy.atleast_1d(numpy.linalg.norm(vector1, ord=-numpy.inf, axis=0)), 0))[0]  # normalise the vector
                # vector2 = numpy.array([0, 1])
                magnitude1 = (vector1[0] ** 2 + vector1[1] ** 2) ** 0.5
                # magnitude2 = (vector2[0] ** 2 + vector2[1] ** 2) ** 0.5
                # dot_product: numpy.float64 = vector1.dot(vector2)
                # direction: float = deg(acos(dot_product / (magnitude1 * magnitude2)))
                # _cross_product = numpy.linalg.cross(numpy.array([vector1[0], vector1[1], 0]), numpy.array([0, 1, 0]), axis=0)
                _cross_product = numpy.linalg.cross(vector1, numpy.array([0, 1, 0]), axis=0)
                cross_product = _cross_product[numpy.nonzero(_cross_product)[0][0]]
                direction: float = deg(asin(cross_product / magnitude1))
                # If the bus is moving south (down), the direction has to be flipped manually
                if vector_y < 0:
                    if direction < 0:
                        direction = -180 - direction
                    else:
                        direction = 180 - direction
                # Decide the side on which to draw the triangle and rotate the rectangle accordingly
                if direction < 0:
                    rotation = -90 - direction
                    bus_draw.regular_polygon((10, 15, 7.5), n_sides=3, rotation=90, fill=(96, 96, 96), outline=(0, 0, 0), width=1)
                else:
                    rotation = 90 - direction
                    bus_draw.regular_polygon((90, 15, 7.5), n_sides=3, rotation=270, fill=(96, 96, 96), outline=(0, 0, 0), width=1)
                # print(f"{route=:>4s} x={vector_x*1000:.4f} y={vector_y*1000:.4f} {direction=:.4f} {rotation=:.4f}")
                # for var, val in locals().items():
                #     print(f"{var} -> {val}")
            except KeyError:  # Trip or shape not found
                rotation = 0.
            # Rotate the bus box based on its direction and add to the original image
            bus_image = bus_image.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0))
            bus_width, bus_height = bus_image.size
            img_x1, img_y1 = img_x - bus_width // 2, img_y - bus_height // 2
            # img_x2, img_y2 = img_x + bus_width // 2, img_y + bus_height // 2
            image.paste(bus_image, (img_x1, img_y1), mask=bus_image)  # Otherwise it will replace the map with transparency
    bio = io.BytesIO()
    image.save(bio, "PNG")
    bio.seek(0)
    return bio
