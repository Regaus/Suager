import io
import os.path
from contextlib import suppress
from math import radians as rad, degrees as deg, cos, sinh, tan, atan, pi, log, asin, ceil

import numpy
from PIL import Image, UnidentifiedImageError, ImageFont, ImageDraw
from regaus import time

from utils import http, logger, conworlds
from utils.general import print_error, make_dir
from utils.timetables import ShapePoint
from utils.timetables.realtime import VehicleData, Vehicle, TripUpdate, Train
from utils.timetables.shared import get_database, __version__
from utils.timetables.static import GTFSData, Route, Trip, Stop, StopTime, Shape, FleetVehicle, load_value

__all__ = (
    "MAP_SIZE", "TILE_SIZE", "DEFAULT_ZOOM", "BASE_MAP_URL",
    "deg_to_xy_float", "deg_to_xy", "xy_to_deg", "find_fitting_coords_and_zoom", "distance_between_bus_and_stop", "get_nearest_stop",
    "download_tile", "download_map", "download_map_lat_lon",
    "draw_vehicle", "paste_vehicle_on_map", "add_map_attribution", "draw_shape", "draw_stop", "draw_all_stops",
    "get_map_with_buses", "get_trip_diagram",
    "debug_generate_real_time_trip", "debug_generate_added_trip", "debug_generate_fake_vehicle"
)


DELTA = range(-2, 3)
START = min(DELTA)
END = max(DELTA)
MAP_SIZE = len(DELTA)
TILE_SIZE = 256
DEFAULT_ZOOM = 17
BASE_MAP_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
MAP_ATTR_FONT = ImageFont.truetype("assets/fonts/univers.ttf", 24)
VEHICLE_FONT = ImageFont.truetype("assets/fonts/univers.ttf", 24)
DEPARTURE_TIME_FONT = ImageFont.truetype("assets/fonts/univers.ttf", 16)


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


def find_fitting_coords_and_zoom(shape: Shape | list[Stop], custom_centre: tuple[int, int] = None, custom_zoom: int = -1) -> tuple[int, int, int]:
    """ Find the best-fitting (x, y) coordinates and zoom level for a shape """
    # TODO: Try to find a solution for maps that just barely don't fit into 5 tiles so they don't look stupid with a lot of empty space
    min_x, min_y = float("inf"), float("inf")
    max_x, max_y = float("-inf"), float("-inf")

    # Get coordinates for every 20th point to be more likely to make them fit
    # for point in list(shape.shape_points.values())[::20]:  # TypeError: 'dict_values' object is not subscriptable - Python devs in their infinite wisdom
    if isinstance(shape, Shape):
        # points = islice(shape.shape_points, 0, None, 20)
        points = shape.shape_points[::20]
    else:
        points = shape
    for point in points:
        x, y = deg_to_xy_float(point.latitude, point.longitude, DEFAULT_ZOOM)
        if x < min_x:
            min_x = x
        if x > max_x:
            max_x = x
        if y < min_y:
            min_y = y
        if y > max_y:
            max_y = y

    # Ensure the points stay reasonably far away from the edges
    min_x, min_y = int(min_x - 0.25), int(min_y - 0.25)
    max_x, max_y = ceil(max_x + 0.25), ceil(max_y + 0.25)
    dist_x = max_x - min_x
    dist_y = max_y - min_y
    # print(f"{dist_x=} {dist_y=}", end=" ")
    zoom = DEFAULT_ZOOM
    # print(f"{dist_x=} {dist_y=} {min_x=} {min_y=} {max_x=} {max_y=} {zoom=}")
    while (dist_x > MAP_SIZE or dist_y > MAP_SIZE) and zoom > custom_zoom:
        zoom -= 1
        min_x, min_y = int(min_x / 2), int(min_y / 2)
        max_x, max_y = ceil(max_x / 2), ceil(max_y / 2)
        dist_x = max_x - min_x
        dist_y = max_y - min_y
        # print(f"{dist_x=} {dist_y=} {min_x=} {min_y=} {max_x=} {max_y=} {zoom=}")
        # dist_x /= 2
        # dist_y /= 2
        # centre_x //= 2
        # centre_y //= 2
    # print(f"{zoom=}")
    if custom_centre:
        # Adjust the given coordinates to fit as many points as possible
        centre_x, centre_y = custom_centre
        if centre_x + START < min_x:
            centre_x = min_x - START
        if centre_x + END > max_x:
            centre_x = max_x - END
        if centre_y + START < min_y:
            centre_y = min_y - START
        if centre_y + END > max_y:
            centre_y = max_y - END
    else:
        centre_x = (max_x + min_x) // 2
        centre_y = (max_y + min_y) // 2
    return centre_x, centre_y, zoom


def distance_between_bus_and_stop(trip: Trip | TripUpdate, stop: Stop, vehicle: Vehicle | Train, static_data: GTFSData) -> tuple[float, int]:
    """ Return the distance between the bus and the current bus stop in metres and an indication of whether the bus has passed the stop.

    Second return value denotes the colour of the circle that denotes whether the bus has passed or not.
     -1 = Orange = Unknown / can't tell (this should never be returned)
     0 = Green = Bus hasn't passed the stop yet
     1 = Yellow = Bus near stop
     2 = Red = Bus passed the stop
    """
    # if not isinstance(trip, Trip):  # Added trip or otherwise invalid data
    #     return conworlds.distance_between_places(stop.latitude, stop.longitude, vehicle.latitude, vehicle.longitude, "Earth") * 1000, -1
    db = get_database()
    points: list[ShapePoint] | list[Stop]
    if isinstance(trip, Trip):
        try:
            shape = trip.shape(static_data, db)
            points = shape.shape_points
            added = False
        except KeyError:
            stop_times = StopTime.from_sql(trip.trip_id, db)
            points = [stop_time.stop(static_data, db) for stop_time in stop_times]
            added = True
    else:
        # points = {stop_time_update.stop_sequence: load_value(static_data, Stop, stop_time_update.stop_id, db) for stop_time_update in trip.stop_times}
        points = [load_value(static_data, Stop, stop_time_update.stop_id, db) for stop_time_update in trip.stop_times]
        added = True
    lat1, lon1 = vehicle.latitude, vehicle.longitude
    distances1: dict[int, float] = {}
    min_distance1 = float("inf")
    sequence1 = 0
    lat2, lon2 = stop.latitude, stop.longitude
    distances2: dict[int, float] = {}
    min_distance2 = float("inf")
    sequence2 = 0
    for seq, point in enumerate(points):
        lat3, lon3 = point.latitude, point.longitude
        distance1 = conworlds.distance_between_places(lat1, lon1, lat3, lon3, "Earth") * 1000
        distance2 = conworlds.distance_between_places(lat2, lon2, lat3, lon3, "Earth") * 1000
        distances1[seq] = distance1
        distances2[seq] = distance2
        if distance1 < min_distance1:
            min_distance1 = distance1
            sequence1 = seq
        if distance2 < min_distance2:
            min_distance2 = distance2
            sequence2 = seq
    if sequence1 == sequence2:
        return min_distance1 + min_distance2, 1

    if added:
        distance = min_distance1 + min_distance2
        colour = 0
        if sequence1 > sequence2:
            _range = range(sequence2, sequence1)
            colour = 2
        else:
            _range = range(sequence1, sequence2)
        for i in _range:
            stop = points[i]
            next_stop = points[i + _range.step]
            distance += conworlds.distance_between_places(stop.latitude, stop.longitude, next_stop.latitude, next_stop.longitude, "Earth") * 1000
        if distance < 150 and colour != 2:
            return distance, 1
        return distance, colour
    else:
        point1: ShapePoint = points[sequence1]
        point2: ShapePoint = points[sequence2]
        if sequence1 > sequence2:  # Bus already passed stop
            distance = point1.distance_travelled - point2.distance_travelled + min_distance1 + min_distance2
            return distance, 2
        else:
            distance = point2.distance_travelled - point1.distance_travelled + min_distance1 + min_distance2
            if distance < 150:
                return distance, 1
            return distance, 0


def get_nearest_stop(trip: Trip | TripUpdate, vehicle: Vehicle, static_data: GTFSData) -> Stop:
    """ Returns the stop nearest to the vehicle's current position """
    db = get_database()
    if isinstance(trip, Trip):
        stops = list(stop_time.stop(static_data, db) for stop_time in StopTime.from_sql(trip.trip_id, db))
    else:
        stops = list(load_value(static_data, Stop, stop_time_update.stop_id, db) for stop_time_update in trip.stop_times)
    lat1, lon1 = vehicle.latitude, vehicle.longitude
    distances: dict[int, float] = {}
    min_distance = float("inf")
    sequence = 0
    for seq, stop in enumerate(stops):
        distance = conworlds.distance_between_places(lat1, lon1, stop.latitude, stop.longitude, "Earth")
        distances[seq] = distance
        if distance < min_distance:
            min_distance = distance
            sequence = seq
    return stops[sequence]


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


def draw_vehicle(vehicle: Vehicle, tile_x: int, tile_y: int, zoom: int, static_data: GTFSData, fleet_data: dict[str, FleetVehicle]) -> tuple[Image.Image, int, int]:
    """ Return an image of a vehicle and its coordinates on the map image (in pixels) """
    # Get route data and draw the bus on a temporary image
    db = get_database()
    try:
        # route = Route.from_sql(vehicle.trip.route_id, db).short_name
        route = load_value(static_data, Route, vehicle.trip.route_id, db).short_name
    except KeyError:
        route = vehicle.trip.route_id
    fleet_vehicle: FleetVehicle | None = fleet_data.get(vehicle.vehicle_id, None)
    if not fleet_vehicle:
        # Unknown vehicles - Green with green-ish highlight
        bus_colour = (1, 133, 64)
        text_colour = (255, 255, 255)
        stroke_colour = (0, 255, 114)
    elif fleet_vehicle.agency == "Dublin Bus":
        # Dublin Bus - Yellow
        bus_colour = (253, 221, 1)
        text_colour = (0, 0, 0)
        stroke_colour = (153, 132, 1)
    elif fleet_vehicle.agency == "Bus Éireann":
        # Bus Éireann - Red
        bus_colour = (234, 29, 26)
        text_colour = (255, 255, 255)
        stroke_colour = (229, 58, 52)
    elif fleet_vehicle.agency == "Go-Ahead Ireland":
        # Go-Ahead Ireland - Cyan-ish
        bus_colour = (79, 199, 204)
        text_colour = (0, 0, 0)
        stroke_colour = (58, 149, 153)
    else:
        raise RuntimeError(f"Unknown fleet vehicle agency {fleet_vehicle.agency!r}")
    map_x, map_y = deg_to_xy_float(vehicle.latitude, vehicle.longitude, zoom)
    img_x = int((map_x - tile_x) * TILE_SIZE)
    img_y = int((map_y - tile_y) * TILE_SIZE)
    image = Image.new("RGBA", (100, 30), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 0, 80, 30), fill=bus_colour, outline=(0, 0, 0), width=2)
    draw.text((50, 15), text=route, fill=text_colour, font=VEHICLE_FONT, anchor="mm", stroke_width=1, stroke_fill=stroke_colour)
    # Calculate the direction the bus is moving in
    try:
        # trip = Trip.from_sql(vehicle.trip.trip_id, db)
        # shape = Shape.from_sql(trip.shape_id, db)
        trip: Trip = load_value(static_data, Trip, vehicle.trip.trip_id, db)
        shape: Shape = trip.shape(static_data, db)
        lat1, lon1 = vehicle.latitude, vehicle.longitude
        distances: dict[int, float] = {}
        min_distance = float("inf")
        sequence1 = 0
        for point in shape.shape_points:
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
    draw = ImageDraw.Draw(image)
    draw.text((width - 4, height), "Map data from OpenStreetMap", fill=(48, 48, 48), font=MAP_ATTR_FONT, anchor="rd")  # Draw on bottom right
    return image


def draw_shape(draw: ImageDraw.ImageDraw, shape: Shape | list[Stop], map_x1: int, map_y1: int, zoom: int, colour: tuple[int, int, int] = (128, 128, 128)) -> None:
    """ Draw the shape of the trip onto the map. Takes in an existing Draw instance and returns nothing. """
    # img_size = TILE_SIZE * MAP_SIZE
    # image = Image.new("RGBA", (img_size, img_size))
    # draw = ImageDraw.Draw(image)
    if isinstance(shape, Shape):
        points = shape.shape_points
    else:
        points = shape
    image_points: list[tuple[float, float]] = []
    for point in points:
        tile_x, tile_y = deg_to_xy_float(point.latitude, point.longitude, zoom)
        image_points.append(((tile_x - map_x1) * TILE_SIZE, (tile_y - map_y1) * TILE_SIZE))
    draw.line(image_points, fill=colour, width=4, joint=None)
    # return image


def draw_stop(draw: ImageDraw.ImageDraw, image_x: int | float, image_y: int | float, colour: tuple[int, int, int] = (1, 64, 132)) -> None:
    """ Draw a bus stop onto the map. Takes in an existing Draw instance and returns nothing. """
    draw.circle((image_x, image_y), radius=12, fill=colour, outline=(0, 0, 0), width=2)


def draw_all_stops(draw: ImageDraw.ImageDraw, trip_id: str | list[Stop], map_x1: int, map_y1: int, zoom: int, current_stop_id: str,
                   static_data: GTFSData, departure_times: list[time.datetime], drop_off_only: set[int], pickup_only: set[int], skipped: set[int], is_cancelled: bool) -> None:
    """ Draw all stops along a route. Takes in an existing Draw instance and returns nothing. """
    text_coordinates: list[tuple[float, float, str]] = []

    def handle_stop(idx, _stop: Stop):
        stop_x, stop_y = deg_to_xy_float(_stop.latitude, _stop.longitude, zoom)
        stop_img_x = (stop_x - map_x1) * TILE_SIZE
        stop_img_y = (stop_y - map_y1) * TILE_SIZE
        if stop.id == current_stop_id:        # Current stop  = dark blue
            colour = (1, 64, 132)
        elif idx in skipped or is_cancelled:  # Skipped stop  = red
            colour = (255, 0, 0)
        elif idx in drop_off_only:            # Pickup only   = orange
            colour = (204, 102, 0)
        elif idx in pickup_only:              # Drop off only = yellow
            colour = (178, 178, 0)
        else:                                 # Regular stop  = lime-green
            colour = (153, 204, 0)
        draw_stop(draw, stop_img_x, stop_img_y, colour)
        nonlocal text_coordinates
        text_coordinates.append((stop_img_x, stop_img_y, departure_times[idx].format("%H:%M", "en")))
        # draw.text((stop_img_x, stop_img_y + 20), departure_times[idx].format("%H:%M", "en"), fill=(64, 64, 64), font=DEPARTURE_TIME_FONT, anchor="mm")

    db = get_database()
    if isinstance(trip_id, str):
        if trip_id not in static_data.stop_times:
            static_data.stop_times[trip_id] = {}
        trip_data = static_data.stop_times[trip_id]
        stop_times = StopTime.from_sql(trip_id, db)
        for i, stop_time in enumerate(stop_times):
            if stop_time.stop_id not in trip_data:
                trip_data[stop_time.stop_id] = stop_time
            stop = stop_time.stop(static_data, db)
            handle_stop(i, stop)
    else:
        for i, stop in enumerate(trip_id):  # trip_id = list[Stop]
            handle_stop(i, stop)

    total_stops: int = len(text_coordinates)
    modifiers_x: dict[str, int] = {"c": 0, "l": -15, "r": 15}
    modifiers_y: dict[str, int] = {"c": 0, "u": -15, "d": 15}
    prev_anchor: str = "mtcd"
    for i in range(total_stops):
        # anchor: horizontal, vertical, x coordinate modifier, y coordinate modifier
        # x modifiers: c - centre, l - left, r - right
        # y modifiers: c - centre, u - up/above, d - down/below
        anchor: str = "mtcd"
        curr_x, curr_y, text = text_coordinates[i]       # type: float, float, str
        if i > 0:
            prev_x, prev_y, _ = text_coordinates[i - 1]  # type: float | None, float | None, str
            # prev_x += modifiers_x.get(prev_anchor[2], 0)
            # prev_y += modifiers_y.get(prev_anchor[3], 0)
        else:
            prev_x, prev_y = (None, None)                  # type: float | None, float | None
        if i < total_stops - 1:
            next_x, next_y, _ = text_coordinates[i + 1]  # type: float | None, float | None, str
        else:
            next_x, next_y = (None, None)                  # type: float | None, float | None
        if prev_x is None or prev_y is None:
            dx, dy = next_x - curr_x, next_y - curr_y
            if 0 < dx < 40:  # next stop on the right -> draw time on centre left
                anchor = "rmlc"
            elif 0 > dx > -40:  # next stop on the left -> draw time on centre right
                anchor = "lmrc"
        elif next_x is None or next_y is None:
            dx, dy = prev_x - curr_x, prev_y - curr_y
            if 0 < dx < 40:  # prev stop on the right -> draw time on centre left
                anchor = "rmlc"
            elif 0 > dx > -40:  # prev stop on the left -> draw time on centre right
                anchor = "lmrc"
        else:
            dx1, dy1 = next_x - curr_x, next_y - curr_y
            dx2, dy2 = prev_x - curr_x, prev_y - curr_y
            if -40 < dx1 < 40 and -40 < dx2 < 40 and 5 > dy1 > -10 and 5 > dy2 > -10 and prev_anchor[3] == "c":
                anchor = "mtcd"
            elif -40 < dx1 < 40 and -40 < dx2 < 40 and -5 < dy1 < 10 and -5 < dy2 < 10 and prev_anchor[3] == "c":
                anchor = "mscu"
            elif 0 < dx1 < 40 and abs(dy1) + abs(dy2) < 40:
                anchor = "rmlc"
            elif 0 > dx1 > -40 and abs(dy1) + abs(dy2) < 40:
                anchor = "lmrc"
        # # Prevents formatting errors for the print statement below
        # prev_x, prev_y, next_x, next_y = prev_x or -1, prev_y or -1, next_x or -1, next_y or -1
        # try:
        #     # noinspection PyUnboundLocalVariable
        #     deltas = f"{dx=:4.0f} {dy=:4.0f}"
        #     del dx, dy
        # except UnboundLocalError:
        #     # noinspection PyUnboundLocalVariable
        #     deltas = f"{dx1=:3.0f} {dy1=:3.0f} {dx2=:3.0f} {dy2=:3.0f}"
        #     del dx1, dy1, dx2, dy2
        # print(f"{i=:02d} {curr_x=:4.0f} {curr_y=:4.0f} {prev_x=:4.0f} {prev_y=:4.0f} {next_x=:4.0f} {next_y=:4.0f} {deltas} {anchor=}")
        if i not in skipped:  # Don't draw the departure time for skipped stops, but still do the rest of the calculations
            mod_x = modifiers_x.get(anchor[2], 0)
            mod_y = modifiers_y.get(anchor[3], 0)
            draw.text((curr_x + mod_x, curr_y + mod_y), text, fill=(64, 64, 64), font=DEPARTURE_TIME_FONT, anchor=anchor[:2])
        prev_anchor = anchor
    # draw.text((0, 0), "Debug: This is a Test", fill=(255, 0, 0), font=DEPARTURE_TIME_FONT, anchor="la")


async def get_map_with_buses(lat: float, lon: float, zoom: int, vehicle_data: VehicleData, static_data: GTFSData, fleet_data: dict[str, FleetVehicle]) -> io.BytesIO:
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
            bus_image, bus_x, bus_y = draw_vehicle(vehicle, tile_x1, tile_y1, zoom, static_data, fleet_data)
            image = paste_vehicle_on_map(image, bus_image, bus_x, bus_y)
    bio = io.BytesIO()
    image.save(bio, "PNG")
    bio.seek(0)
    return bio


async def get_trip_diagram(trip: Trip | TripUpdate, current_stop: Stop, static_data: GTFSData, vehicle_data: VehicleData, fleet_data: dict[str, FleetVehicle],
                           departure_times: list[time.datetime], drop_off_only: set[int], pickup_only: set[int], skipped: set[int],
                           is_cancelled: bool = False, custom_zoom: int = None) -> tuple[io.BytesIO, int]:
    """ Show the diagram of a trip, including stops along the trip and the vehicle's current location (if available).

    Returns a BytesIO instance with the image inside and the map's zoom level."""
    db = get_database()
    trip_id: str | list[Stop]
    shape: Shape | list[Stop]
    if isinstance(trip, Trip):
        trip_id = trip.trip_id
        try:
            shape = trip.shape(static_data, db)
        except KeyError:
            shape = list(stop_time.stop(static_data, db) for stop_time in StopTime.from_sql(trip_id, db))
    else:
        trip_id = shape = list(load_value(static_data, Stop, stop_time_update.stop_id, db) for stop_time_update in trip.stop_times)
    if custom_zoom:
        x, y = deg_to_xy(current_stop.latitude, current_stop.longitude, custom_zoom)
        x, y, zoom = find_fitting_coords_and_zoom(shape, (x, y), custom_zoom)
    else:
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
    draw_all_stops(draw, trip_id, x1, y1, zoom, current_stop.id, static_data, departure_times, drop_off_only, pickup_only, skipped, is_cancelled)

    # Draw the bus along the route
    # bus: Vehicle | None = None
    if isinstance(trip, Trip):
        bus = vehicle_data.scheduled.get(trip.trip_id)
        # for vehicle in vehicle_data.entities.values():
        #     if vehicle.trip.trip_id == trip_id:
        #         bus = vehicle
        #         break
    else:
        bus = vehicle_data.vehicles.get(trip.vehicle_id)
        # vehicle_id = trip.vehicle_id
        # for vehicle in vehicle_data.entities.values():
        #     if vehicle.vehicle_id == vehicle_id:
        #         bus = vehicle
        #         break
    if bus is not None:
        bus_image, bus_x, bus_y = draw_vehicle(bus, x1, y1, zoom, static_data, fleet_data)
        image = paste_vehicle_on_map(image, bus_image, bus_x, bus_y)

    bio = io.BytesIO()
    image.save(bio, "PNG")
    bio.seek(0)
    return bio, zoom


def debug_generate_real_time_trip(real_trip_id: str, fake_entity_id: str = "T2002", vehicle_id: str = "10001") -> str:
    """ Generate a fake real-time trip that can be added to real_time.json """
    import json
    import random
    from utils.timetables.shared import TIMEZONE
    today = time.datetime.combine(time.date.today(), time.time(), TIMEZONE)
    today_ts = int(today.timestamp)
    stop_time_updates = []
    stop_times = StopTime.from_sql(real_trip_id)
    skip_a_segment: bool = random.random() < 0.75
    skipped_segment_start = random.randint(1, len(stop_times) - 5)
    skipped_segment_end = skipped_segment_start + random.randint(0, 11)
    prev_delay = 0
    for stop_time in stop_times:
        delay = prev_delay + random.randint(-120, 120)
        if skip_a_segment and skipped_segment_start <= stop_time.sequence <= skipped_segment_end:
            stop_time_updates.append({
                "stop_sequence": stop_time.sequence,
                "stop_id": stop_time.stop_id,
                "schedule_relationship": "SKIPPED"
            })
        else:
            stop_time_updates.append({
                "stop_sequence": stop_time.sequence,
                "arrival": {"delay": prev_delay},
                "departure": {"delay": delay},
                "stop_id": stop_time.stop_id,
                "schedule_relationship": "SCHEDULED"
            })
        prev_delay = delay
    trip = Trip.from_sql(real_trip_id)
    output = {
        "id": fake_entity_id,
        "trip_update": {
            "trip": {
                "trip_id": real_trip_id,
                "start_time": time.timedelta(seconds=stop_times[0].arrival_time).format("%H:%M:%S"),
                "start_date": today.format("%Y%m%d"),
                "schedule_relationship": "SCHEDULED",
                "route_id": trip.route_id,
                "direction_id": trip.direction_id
            },
            "stop_time_update": stop_time_updates,
            "vehicle": {
                "id": vehicle_id
            },
            "timestamp": str(today_ts)
        }
    }
    # return json.dumps(output, indent=1)
    # Add extra spaces before each line to make it fit in with the other data
    json_output = json.dumps(output, indent=1)
    indentation = []
    for line in json_output.splitlines():
        indentation.append("  " + line)
    return "\n".join(indentation)


def debug_generate_added_trip(real_trip_id: str, fake_entity_id: str = "T2001", vehicle_id: str = "10001") -> str:
    """ Generate a fake added trip that can be added to real_time.json """
    import json
    from utils.timetables.shared import TIMEZONE
    today = time.datetime.combine(time.date.today(), time.time(), TIMEZONE)
    today_ts = int(today.timestamp)
    stop_time_updates = []
    stop_times = StopTime.from_sql(real_trip_id)
    for stop_time in stop_times:
        stop_time_updates.append({
            "stop_sequence": stop_time.sequence,
            "arrival": {"time": str(today_ts + stop_time.arrival_time)},
            "departure": {"time": str(today_ts + stop_time.departure_time)},
            "stop_id": stop_time.stop_id
        })
    trip = Trip.from_sql(real_trip_id)
    output = {
        "id": fake_entity_id,
        "trip_update": {
            "trip": {
                "start_time": time.timedelta(seconds=stop_times[0].arrival_time).format("%H:%M:%S"),
                "start_date": today.format("%Y%m%d"),
                "schedule_relationship": "ADDED",
                "route_id": trip.route_id,
                "direction_id": trip.direction_id
            },
            "stop_time_update": stop_time_updates,
            "vehicle": {
                "id": vehicle_id
            },
            "timestamp": str(today_ts)
        }
    }
    # return json.dumps(output, indent=1)
    # Add extra spaces before each line to make it fit in with the other data
    json_output = json.dumps(output, indent=1)
    indentation = []
    for line in json_output.splitlines():
        indentation.append("  " + line)
    return "\n".join(indentation)


def debug_generate_fake_vehicle(real_trip_id: str, current_stop: str | int, fake_entity_id: str = "V2001", vehicle_id: str = "10001") -> str:
    """ Generate fake vehicle location data that can be added to vehicles.json """
    import json
    from utils.timetables.shared import TIMEZONE
    today = time.datetime.combine(time.date.today(), time.time(), TIMEZONE)
    today_ts = int(today.timestamp)
    trip = Trip.from_sql(real_trip_id)
    if isinstance(current_stop, str):
        stop = Stop.from_sql(current_stop)
    else:
        stop_time = StopTime.from_sql_sequence(real_trip_id, current_stop)
        stop = stop_time.stop()
    departure_time = time.timedelta(seconds=StopTime.from_sql_sequence(real_trip_id, 1).arrival_time).format("%H:%M:%S")
    output = {
        "id": fake_entity_id,
        "vehicle": {
            "trip": {
                "trip_id": real_trip_id,
                "start_time": departure_time,
                "start_date": today.format("%Y%m%d"),
                "schedule_relationship": "SCHEDULED",
                "route_id": trip.route_id,
                "direction_id": trip.direction_id
            },
            "position": {
                "latitude": round(stop.latitude, 5),
                "longitude": round(stop.longitude, 5)
            },
            "timestamp": today_ts,
            "vehicle": {
                "id": vehicle_id
            }
        }
    }
    # return json.dumps(output, indent=1)
    # Add extra spaces before each line to make it fit in with the other data
    json_output = json.dumps(output, indent=1)
    indentation = []
    for line in json_output.splitlines():
        indentation.append("  " + line)
    return "\n".join(indentation)
