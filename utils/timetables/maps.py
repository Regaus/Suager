import io
import os.path
from contextlib import suppress
from math import radians as rad, degrees as deg, cos, sinh, tan, atan, pi, log, asin

import numpy
from PIL import Image, UnidentifiedImageError, ImageFont, ImageDraw
from regaus import time

from utils import http, logger, conworlds
from utils.general import print_error, make_dir
from utils.timetables.realtime import VehicleData, Vehicle
from utils.timetables.shared import get_database, __version__
from utils.timetables.static import GTFSData, Route, Trip, Stop, StopTime, Shape, load_value

__all__ = (
    "MAP_SIZE", "TILE_SIZE", "DEFAULT_ZOOM", "BASE_MAP_URL",
    "deg_to_xy_float", "deg_to_xy", "xy_to_deg", "find_fitting_coords_and_zoom",
    "download_tile", "download_map", "download_map_lat_lon",
    "draw_vehicle", "paste_vehicle_on_map", "add_map_attribution", "draw_shape", "draw_stop", "draw_all_stops",
    "get_map_with_buses", "get_trip_diagram"
)


DELTA = range(-2, 3)
START = min(DELTA)
END = max(DELTA)
MAP_SIZE = len(DELTA)
TILE_SIZE = 256
DEFAULT_ZOOM = 17
BASE_MAP_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"


def deg_to_xy_float(lat: float, lon: float, zoom: int) -> tuple[float, float]:
    """ Convert latitude and longitude in degrees to (x, y) coordinates (as floats) """
    lat_rad: float = rad(lat)
    n: float = 2. ** zoom
    x: float = (lon + 180) / 360 * n
    y: float = (1 - log(tan(lat_rad) + (1 / cos(lat_rad))) / pi) / 2 * n
    return x, y


def deg_to_xy(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    """ Convert latitude and longitude in degrees to (x, y) coordinates (as integers) """
    x, y = deg_to_xy_float(lat, lon, zoom)
    return int(x), int(y)


def xy_to_deg(x: float, y: float, zoom: int) -> tuple[float, float]:
    """ Convert (x, y) coordinates to latitude and longitude in degrees """
    n: float = 2. ** zoom
    lon: float = x / n * 360 - 180
    lat: float = deg(atan(sinh(pi * (1 - 2 * y / n))))
    return lat, lon


def find_fitting_coords_and_zoom(shape: Shape) -> tuple[int, int, int]:
    """ Find the best-fitting (x, y) coordinates and zoom level for a shape """
    points = len(shape.shape_points)
    start_point = shape.shape_points[1]
    start_x, start_y = deg_to_xy(start_point.latitude, start_point.longitude, DEFAULT_ZOOM)
    mid_point = shape.shape_points[points // 2]
    mid_x, mid_y = deg_to_xy(mid_point.latitude, mid_point.longitude, DEFAULT_ZOOM)
    end_point = shape.shape_points[points]
    end_x, end_y = deg_to_xy(end_point.latitude, end_point.longitude, DEFAULT_ZOOM)

    min_x = min(start_x, mid_x, end_x)
    min_y = min(start_y, mid_y, end_y)
    max_x = max(start_x, mid_x, end_x)
    max_y = max(start_y, mid_y, end_y)

    dist_x = max_x - min_x
    dist_y = max_y - min_y
    # print(f"{dist_x=} {dist_y=}", end=" ")
    zoom = DEFAULT_ZOOM
    centre_x = (max_x + min_x) // 2
    centre_y = (max_y + min_y) // 2
    while dist_x > MAP_SIZE or dist_y > MAP_SIZE:
        zoom -= 1
        dist_x /= 2
        dist_y /= 2
        centre_x //= 2
        centre_y //= 2
    # print(f"{zoom=}")
    return centre_x, centre_y, zoom


async def download_tile(x: int, y: int, zoom: int) -> Image.Image:
    """ Download a specific tile at the given (x, y) coordinates. Returns an Image instance of it """
    req_download = True
    tile = None
    try:
        path = "data/maps/{z}/{x}/{y}".format(z=zoom, x=x, y=y)
        if os.path.isdir(path):
            listdir = os.listdir(path)
            if len(listdir) == 1 and os.path.isfile(file_path := os.path.join(path, listdir[0])):
                expiry = int(os.path.splitext(listdir[0])[0])  # The rest of the path doesn't matter, only the filename
                if time.datetime.now().timestamp < expiry:
                    # print(f"Debug: Found cached tile at {file_path}")
                    return Image.open(file_path)
                else:
                    # Delete the file if it has expired
                    with suppress(FileNotFoundError):
                        os.remove(file_path)
    except (FileNotFoundError, ValueError):
        pass  # Require downloading if there are problems getting the file
    if req_download:
        # print(f"Debug: Tile for {zoom}/{x}/{y} not found. Downloading...")
        tile_url = BASE_MAP_URL.format(z=zoom, x=x, y=y)
        bio = io.BytesIO(await http.get(tile_url, res_method="read", headers={"User-Agent": f"RegausGTFSBot/{__version__}"}))
        try:
            tile = Image.open(bio)
            try:
                expiry = int(time.datetime.now().timestamp + 86400 * 30)  # The cached image will expire 30 days from now
                make_dir(f"data/maps/{zoom}")
                make_dir(f"data/maps/{zoom}/{x}")
                make_dir(f"data/maps/{zoom}/{x}/{y}")
                path = f"data/maps/{zoom}/{x}/{y}/{expiry}.png"
                tile.save(path, "PNG")
            except OSError:
                # If there's an error while saving the file, silently try to remove whatever was left
                with suppress(FileNotFoundError, UnboundLocalError):
                    # noinspection PyUnboundLocalVariable
                    os.remove(path)
        except UnidentifiedImageError:
            message = f"{time.datetime.now():%d %b %Y, %H:%M:%S} > Failed to load map tile: {zoom=}, x={x}, y={y}."
            print_error(message)
            logger.log("timetables", "errors", message)
            tile = Image.open("assets/error_256.png")
    if tile is None:
        tile = Image.open("assets/error_256.png")
    return tile


async def download_map(x: int, y: int, zoom: int = DEFAULT_ZOOM) -> Image.Image:
    """ Download an image of the area around (x, y). Returns an Image instance of it """
    img_size = TILE_SIZE * MAP_SIZE
    output = Image.new("RGBA", (img_size, img_size))
    for dx in DELTA:
        for dy in DELTA:
            tile = await download_tile(x + dx, y + dy, zoom)
            output.paste(tile, box=((dx + END) * 256, (dy + END) * 256))
    return output


async def download_map_lat_lon(lat: float, lon: float, zoom: int = DEFAULT_ZOOM) -> tuple[Image.Image, int, int]:
    """ Download an image of the area around (lat, lon) at a particular zoom level.

    Returns an image instance and the x,y coordinates of the top left corner of the map. """
    x, y = deg_to_xy(lat, lon, zoom)
    output = await download_map(x, y, zoom)
    return output, x + START, y + START


def draw_vehicle(vehicle: Vehicle, tile_x: int, tile_y: int, zoom: int, static_data: GTFSData) -> tuple[Image.Image, int, int]:
    """ Return an image of a vehicle and its coordinates on the map image (in pixels) """
    # Get route data and draw the bus on a temporary image
    font = ImageFont.truetype("assets/fonts/univers.ttf", 24)
    db = get_database()
    try:
        # route = Route.from_sql(vehicle.trip.route_id, db).short_name
        route = load_value(static_data, Route, vehicle.trip.route_id, db).short_name
    except KeyError:
        route = vehicle.trip.route_id
    map_x, map_y = deg_to_xy_float(vehicle.latitude, vehicle.longitude, zoom)
    img_x = int((map_x - tile_x) * TILE_SIZE)
    img_y = int((map_y - tile_y) * TILE_SIZE)
    image = Image.new("RGBA", (100, 30), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 0, 80, 30), fill=(1, 133, 64), outline=(0, 0, 0), width=2)
    draw.text((50, 15), text=route, fill=(255, 255, 255), font=font, anchor="mm", stroke_width=1, stroke_fill=(0, 255, 114))
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
            draw.regular_polygon((10, 15, 7.5), n_sides=3, rotation=90, fill=(96, 96, 96), outline=(0, 0, 0), width=1)
        else:
            rotation = 90 - direction
            draw.regular_polygon((90, 15, 7.5), n_sides=3, rotation=270, fill=(96, 96, 96), outline=(0, 0, 0), width=1)
        # print(f"{route=:>4s} x={vector_x*1000:.4f} y={vector_y*1000:.4f} {direction=:.4f} {rotation=:.4f}")
        # for var, val in locals().items():
        #     print(f"{var} -> {val}")
    except KeyError:  # Trip or shape not found
        rotation = 0.
    # Rotate the bus box based on its direction and add to the original image
    return image.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0)), img_x, img_y


def paste_vehicle_on_map(map_image: Image.Image, vehicle_image: Image.Image, map_x: int, map_y: int) -> Image.Image:
    """ Paste the image of the vehicle on the map """
    vehicle_width, vehicle_height = vehicle_image.size
    x1, y1 = map_x - vehicle_width // 2, map_y - vehicle_height // 2
    map_image.paste(vehicle_image, (x1, y1), mask=vehicle_image)
    return map_image


def add_map_attribution(image: Image.Image) -> Image.Image:
    """ Add the map attribution to the map image """
    width, height = image.size
    font = ImageFont.truetype("assets/fonts/univers.ttf", 24)
    draw = ImageDraw.Draw(image)
    draw.text((width - 4, height), "Map data from OpenStreetMap", fill=(48, 48, 48), font=font, anchor="rd")  # Draw on bottom right
    return image


def draw_shape(draw: ImageDraw.ImageDraw, shape: Shape, map_x1: int, map_y1: int, zoom: int, colour: tuple[int, int, int] = (128, 128, 128)) -> None:
    """ Draw the shape of the trip onto the map. Takes in an existing Draw instance and returns nothing. """
    # img_size = TILE_SIZE * MAP_SIZE
    # image = Image.new("RGBA", (img_size, img_size))
    # draw = ImageDraw.Draw(image)
    points = list(shape.shape_points.values())
    image_points: list[tuple[float, float]] = []
    for point in points:
        tile_x, tile_y = deg_to_xy_float(point.latitude, point.longitude, zoom)
        image_points.append(((tile_x - map_x1) * TILE_SIZE, (tile_y - map_y1) * TILE_SIZE))
    draw.line(image_points, fill=colour, width=4, joint=None)
    # return image


def draw_stop(draw: ImageDraw.ImageDraw, image_x: int | float, image_y: int | float, colour: tuple[int, int, int] = (1, 64, 132)) -> None:
    """ Draw a bus stop onto the map. Takes in an existing Draw instance and returns nothing. """
    draw.circle((image_x, image_y), radius=12, fill=colour, outline=(0, 0, 0), width=2)


def draw_all_stops(draw: ImageDraw.ImageDraw, trip_id: str, map_x1: int, map_y1: int, zoom: int, current_stop_id: str, static_data: GTFSData) -> None:
    """ Draw all stops along a route. Takes in an existing Draw instance and returns nothing. """
    db = get_database()
    if trip_id not in static_data.stop_times:
        static_data.stop_times[trip_id] = {}
    trip_data = static_data.stop_times[trip_id]
    stop_times = StopTime.from_sql(trip_id, db)
    for stop_time in stop_times:
        if stop_time.stop_id not in trip_data:
            trip_data[stop_time.stop_id] = stop_time
        stop = stop_time.stop(static_data, db)
        stop_x, stop_y = deg_to_xy_float(stop.latitude, stop.longitude, zoom)
        stop_img_x = (stop_x - map_x1) * TILE_SIZE
        stop_img_y = (stop_y - map_y1) * TILE_SIZE
        if stop.id == current_stop_id:
            colour = (1, 64, 132)   # Dark blue
        elif stop_time.drop_off_type == 1:  # Pickup only
            colour = (178, 178, 0)  # Yellow
        elif stop_time.pickup_type == 1:    # Drop off only
            colour = (204, 102, 0)  # Orange
        else:                               # Regular stop
            colour = (153, 204, 0)  # Lime-green
        draw_stop(draw, stop_img_x, stop_img_y, colour)


async def get_map_with_buses(lat: float, lon: float, zoom: int, vehicle_data: VehicleData, static_data: GTFSData) -> io.BytesIO:
    """ Show the map of the area around a bus stop, including all buses nearby.

    Returns a BytesIO instance with the image inside """
    image, tile_x1, tile_y1 = await download_map_lat_lon(lat, lon, zoom)
    tile_x2, tile_y2 = tile_x1 + MAP_SIZE, tile_y1 + MAP_SIZE
    image = add_map_attribution(image)
    draw = ImageDraw.Draw(image)

    # Draw the location of the stop you're looking at
    stop_tile_x, stop_tile_y = deg_to_xy_float(lat, lon, zoom)
    stop_img_x = (stop_tile_x - tile_x1) * TILE_SIZE
    stop_img_y = (stop_tile_y - tile_y1) * TILE_SIZE
    draw_stop(draw, stop_img_x, stop_img_y)
    # draw.circle((stop_img_x, stop_img_y), radius=12, fill=(1, 64, 132), outline=(0, 0, 0), width=2)

    # Draw all the buses in the area
    lat1, lon1 = xy_to_deg(tile_x1, tile_y1, zoom)
    lat2, lon2 = xy_to_deg(tile_x2, tile_y2, zoom)
    lat_min, lat_max = min((lat1, lat2)), max((lat1, lat2))
    lon_min, lon_max = min((lon1, lon2)), max((lon1, lon2))
    del lat1, lon1, lat2, lon2
    for vehicle in vehicle_data.entities.values():
        if lat_min <= vehicle.latitude <= lat_max and lon_min <= vehicle.longitude <= lon_max:
            bus_image, bus_x, bus_y = draw_vehicle(vehicle, tile_x1, tile_y1, zoom, static_data)
            image = paste_vehicle_on_map(image, bus_image, bus_x, bus_y)
    bio = io.BytesIO()
    image.save(bio, "PNG")
    bio.seek(0)
    return bio


async def get_trip_diagram(trip: Trip, current_stop: Stop, static_data: GTFSData, vehicle_data: VehicleData) -> io.BytesIO:
    """ Show the diagram of a trip, including stops along the trip and the vehicle's current location (if available).

    Returns a BytesIO instance with the image inside."""
    db = get_database()
    trip_id = trip.trip_id
    shape = trip.shape(static_data, db)
    x, y, zoom = find_fitting_coords_and_zoom(shape)
    x1, y1 = x + START, y + START
    image = await download_map(x, y, zoom)
    image = add_map_attribution(image)
    draw = ImageDraw.Draw(image)

    # Draw the shape of the route
    draw_shape(draw, shape, x1, y1, zoom)
    # shape_image = draw_shape(shape, x1, y1, zoom)
    # image.paste(shape_image, (0, 0), mask=shape_image)

    # Draw all the stops along the route
    draw_all_stops(draw, trip_id, x1, y1, zoom, current_stop.id, static_data)

    # Draw the bus along the route
    for vehicle in vehicle_data.entities.values():
        if vehicle.trip.trip_id == trip_id:
            bus_image, bus_x, bus_y = draw_vehicle(vehicle, x1, y1, zoom, static_data)
            image = paste_vehicle_on_map(image, bus_image, bus_x, bus_y)

    bio = io.BytesIO()
    image.save(bio, "PNG")
    bio.seek(0)
    return bio
