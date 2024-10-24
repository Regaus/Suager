from __future__ import annotations

from dataclasses import dataclass

import xmltodict
from regaus import time

from utils import http
from utils.timetables.shared import GTFSAPIError, TIMEZONE


__all__ = (
    "empty_real_time_str",
    "load_gtfs_r_data", "GTFSRData", "VehicleData",
    "Header", "TripUpdate", "RealTimeTrip", "StopTimeUpdate", "Vehicle",
    "Train", "parse_train_data", "TrainMovement", "parse_train_movements", "fetch_train_movements"
)


empty_real_time_str: bytes = b'{"header": {"gtfs_realtime_version": "2.0", "incrementality": "EMPTY", "timestamp": "0"}, "entity": {}}'
# empty_train_data_str: bytes = b"<ArrayOfObjTrainPositions><NoData/></ArrayOfObjTrainPositions>"


# These classes handle the GTFS-R Real time information
def load_gtfs_r_data(data: dict | None, vehicle_data: dict | None) -> tuple[GTFSRData | None, VehicleData | None]:
    try:
        return GTFSRData.load(data), VehicleData.load(vehicle_data)
    except Exception as e:
        # We print the error but re-raise it afterwards
        from utils import general
        general.print_error(general.traceback_maker(e, code_block=False))
        raise


@dataclass()
class GTFSRData:
    header: Header
    entities:  dict[str, TripUpdate]
    """ All entities: entity_id -> TripUpdate """
    all_trips: dict[str, TripUpdate]
    """ All trips: trip_id or entity_id -> TripUpdate
     
     Uses trip_id for scheduled trips and entity_id for added trips """
    scheduled: dict[str, TripUpdate]
    """ Scheduled trips: trip_id -> TripUpdate """
    added:     dict[str, TripUpdate]
    """ Added trips: entity_id -> TripUpdate """

    @classmethod
    def load(cls, data: dict | None):
        # If no data is available, keep self.data null until we do get some data
        if data is None:
            return cls.empty()
        # See if the API returned any errors
        if "status_code" in data and "message" in data:
            raise GTFSAPIError(f"{data['status_code']}: {data['message']}", "real-time")
        if "entity" not in data:
            return cls.empty()
        trip_updates: dict[str, TripUpdate] = {}
        all_trips: dict[str, TripUpdate] = {}
        scheduled: dict[str, TripUpdate] = {}
        added: dict[str, TripUpdate] = {}
        for entity in data["entity"]:
            trip_update = TripUpdate.load(entity)
            trip_updates[trip_update.entity_id] = trip_update
            all_trips[trip_update.trip.trip_id or trip_update.entity_id] = trip_update
            if trip_update.trip.schedule_relationship == "ADDED":
                added[trip_update.entity_id] = trip_update
            else:
                scheduled[trip_update.trip.trip_id] = trip_update
        return cls(Header.load(data["header"]), trip_updates, all_trips, scheduled, added)

    @classmethod
    def empty(cls):
        """ Return an empty GTFSRData object """
        return cls(Header.empty(), {}, {}, {}, {})

    @property
    def is_empty(self) -> bool:
        return self.header.is_empty

    def __bool__(self) -> bool:
        return not self.is_empty


@dataclass()
class VehicleData:
    header: Header
    # entities: dict[str, Vehicle]  # vehicle_id -> Vehicle (not entity_id!)
    entities:  dict[str, Vehicle]
    """ All entities: entity_id -> Vehicle """
    vehicles:  dict[str, Vehicle]
    """ All vehicles: vehicle_id -> Vehicle """
    scheduled: dict[str, Vehicle]
    """ Scheduled trips: trip_id -> Vehicle """
    added:     dict[str, Vehicle]
    """ Added trips: vehicle_id -> Vehicle"""

    @classmethod
    def load(cls, data: dict | None):
        if data is None:
            return cls.empty()
        # See if the API returned any errors
        if "status_code" in data and "message" in data:
            raise GTFSAPIError(f"{data['status_code']}: {data['message']}", "vehicles")
        if "entity" not in data:
            return cls.empty()
        entities: dict[str, Vehicle] = {}
        vehicles: dict[str, Vehicle] = {}
        scheduled: dict[str, Vehicle] = {}
        added: dict[str, Vehicle] = {}
        for entity in data["entity"]:
            vehicle = Vehicle.load(entity)
            entities[vehicle.entity_id] = vehicle
            vehicles[vehicle.vehicle_id] = vehicle
            if vehicle.trip.schedule_relationship == "ADDED":
                added[vehicle.vehicle_id] = vehicle
            else:
                scheduled[vehicle.trip.trip_id] = vehicle
        return cls(Header.load(data["header"]), entities, vehicles, scheduled, added)

    @classmethod
    def empty(cls):
        """ Return an empty VehicleData object """
        return cls(Header.empty(), {}, {}, {}, {})

    @property
    def is_empty(self) -> bool:
        return self.header.is_empty

    def __bool__(self) -> bool:
        return not self.is_empty


@dataclass()
class Header:
    gtfsr_version: str
    incrementality: str
    timestamp: time.datetime

    @classmethod
    def load(cls, data: dict):
        return cls(data["gtfs_realtime_version"], data["incrementality"], time.datetime.from_timestamp(int(data["timestamp"]), tz=TIMEZONE))

    @classmethod
    def empty(cls):
        return cls("2.0", "EMPTY", time.datetime.zero)

    @property
    def is_empty(self) -> bool:
        return self.incrementality == "EMPTY"

    def __bool__(self) -> bool:
        return not self.is_empty


@dataclass()
class TripUpdate:
    entity_id: str
    trip: RealTimeTrip
    stop_times: list[StopTimeUpdate] | None
    vehicle_id: str | None
    timestamp: time.datetime  # The timestamp for data about this specific entity

    @classmethod
    def load(cls, data: dict):
        trip_data = data["trip_update"]
        stop_times = [StopTimeUpdate.load(i) for i in trip_data["stop_time_update"]] if "stop_time_update" in trip_data else None
        if "vehicle" in trip_data:
            vehicle_id = trip_data["vehicle"]["id"]
        else:
            vehicle_id = None
        timestamp = trip_data["timestamp"]
        return cls(data["id"], RealTimeTrip.load(trip_data["trip"]), stop_times, vehicle_id, time.datetime.from_timestamp(int(timestamp), tz=TIMEZONE))


@dataclass()
class RealTimeTrip:
    trip_id: str
    route_id: str
    start_date: time.date
    start_time: time.datetime
    schedule_relationship: str  # SCHEDULED, ADDED, UNSCHEDULED, CANCELED, DUPLICATED, DELETED
    direction_id: int

    @classmethod
    def load(cls, data: dict):
        _time: str = data["start_time"]
        _date: str = data["start_date"]
        h, m, s = _time.split(":")
        y, mo, d = _date[0:4], _date[4:6], _date[6:8]
        start_date = time.date(int(y), int(mo), int(d))
        start_time = time.datetime(int(y), int(mo), int(d), int(h) % 24, int(m), int(s), tz=TIMEZONE)
        if int(h) >= 24:
            start_time += time.timedelta(days=1)
        return cls(data.get("trip_id", "Unknown"), data.get("route_id", "Unknown"), start_date, start_time, data.get("schedule_relationship", "Unknown"), data["direction_id"])


@dataclass()
class StopTimeUpdate:
    stop_sequence: int
    stop_id: str
    schedule_relationship: str  # SCHEDULED, SKIPPED, NO_DATA, or UNSCHEDULED
    arrival_delay: time.timedelta = None
    departure_delay: time.timedelta = None
    arrival_time: time.datetime = None
    departure_time: time.datetime = None

    @classmethod
    def load(cls, data: dict):
        arrival_delay = arrival_time = departure_delay = departure_time = None
        if "arrival" in data:
            _arrival_delay = data["arrival"].get("delay")
            if _arrival_delay is not None:
                arrival_delay = time.timedelta(seconds=_arrival_delay)
            _arrival_time = data["arrival"].get("time")
            if _arrival_time is not None:
                arrival_time = time.datetime.from_timestamp(int(_arrival_time), tz=TIMEZONE)
        if "departure" in data:
            _departure_delay = data["departure"].get("delay")
            if _departure_delay is not None:
                departure_delay = time.timedelta(seconds=_departure_delay)
            _departure_time = data["departure"].get("time")
            if _departure_time is not None:
                departure_time = time.datetime.from_timestamp(int(_departure_time), tz=TIMEZONE)
        return cls(data["stop_sequence"], data.get("stop_id", "Unknown"), data.get("schedule_relationship", "Unknown"), arrival_delay, departure_delay, arrival_time, departure_time)


@dataclass()
class Vehicle:
    entity_id: str
    trip: RealTimeTrip
    latitude: float
    longitude: float
    vehicle_id: str
    timestamp: time.datetime  # The timestamp for data about this specific vehicle

    @classmethod
    def load(cls, data: dict):
        entity_id = data["id"]
        vehicle_data = data["vehicle"]
        trip = RealTimeTrip.load(vehicle_data["trip"])
        position = vehicle_data["position"]
        vehicle_id = vehicle_data["vehicle"]["id"]
        timestamp = vehicle_data["timestamp"]
        return cls(entity_id, trip, position["latitude"], position["longitude"], vehicle_id, time.datetime.from_timestamp(int(timestamp), tz=TIMEZONE))


# Used for real-time train locations: https://api.irishrail.ie/realtime/realtime.asmx/getCurrentTrainsXML
@dataclass()
class Train:
    trip_code: str
    """ Irish Rail's 4-letter trip code """
    latitude: float
    longitude: float
    date: str
    """ The date on which the trip started, as a string """
    public_message: str
    """ Irish Rail's "public message", which contains information about the current state of the trip """
    direction: str
    train_status: str
    """ N = not yet running | R = running | T = terminated """


def parse_train_data(xml: str | bytes | None) -> dict[str, Train]:
    if not xml:
        return {}
    train_data: list[dict[str, str]] = xmltodict.parse(xml)["ArrayOfObjTrainPositions"].get("objTrainPositions", [])
    trains: dict[str, Train] = {}
    for entry in train_data:
        trip_code: str = entry["TrainCode"]
        latitude: float = float(entry["TrainLatitude"])
        longitude: float = float(entry["TrainLongitude"])
        date: str = entry["TrainDate"]
        public_message: str = entry["PublicMessage"].replace("\\n", "\n")
        direction: str = entry["Direction"]
        status: str = entry["TrainStatus"]
        trains[trip_code] = Train(trip_code, latitude, longitude, date, public_message, direction, status)
    return trains


# Not currently used - but might as well leave it for the future. Forecast for trains leaving the station in the next 90 minutes
# API link: https://api.irishrail.ie/realtime/realtime.asmx/getStationDataByNameXML?StationDesc=Dublin%20Connolly
@dataclass()
class StationDataTrain:
    """ Train data from Station Data - Irish Rail """
    trip_code: str
    """ Irish Rail's 4-letter trip code """
    station_name: str
    station_code: str
    date: str
    origin: str
    """ Name of the origin station """
    destination: str
    """ Name of the destination station """
    origin_time: time.time
    """ The time when the train left/will leave the origin """
    destination_time: time.time
    """ The time when the train will arrive at the destination """
    status: str
    """ Latest known information about this train """
    last_location: str | None
    """ Last known location of the train """
    due_in: time.timedelta
    """ Time when the train is due to arrive, in minutes """
    delay: time.timedelta
    """ Current delay of the train, in minutes """
    expected_arrival: time.time
    """ Expected arrival time - 00:00 at origin station """
    expected_departure: time.time
    """ Expected departure time - 00:00 at destination """
    scheduled_arrival: time.time
    """ Scheduled arrival time - 00:00 at origin station """
    scheduled_departure: time.time
    """ Scheduled departure time - 00:00 at destination """
    direction: str
    """ Northbound, Southbound, or To Station Name """
    train_type: str
    """ DART or other train """
    location_type: str
    """ O = origin | D = destination | S = stop """


# Information about a train, real-time or past: https://api.irishrail.ie/realtime/realtime.asmx/getTrainMovementsXML?TrainId=D574&TrainDate=23%20oct%202024
@dataclass()
class TrainMovement:
    trip_code: str
    """ Irish Rail's 4-letter trip code """
    date: time.date
    """ The date on which this service operated """
    location_code: str
    """ Irish Rail's 4-5 letter code of the location """
    location_name: str | None
    """ The full name of the location (if available) """
    location_order: int
    """ The sequence of the station/point """
    location_type: str
    """ O = origin | D = destination | S = stop | T = timing point (non-stop) """
    origin: str
    """ Where the train departed from """
    destination: str
    """ Where the train is going to """
    # On the API, the scheduled and expected arrival/departure times show up as 00:00 at the origin/destination respectively
    # My code simply copies the departure/arrival time to the opposite field to not mess with the way my viewers work
    scheduled_arrival: time.datetime
    """ When the train was scheduled to arrive here """
    scheduled_departure: time.datetime
    """ When the train was scheduled to depart from here """
    expected_arrival: time.datetime
    """ When the train is expected to arrive here """
    expected_departure: time.datetime
    """ When the train is expected to depart from here """
    actual_arrival: time.datetime | None
    """ Actual arrival time of the train """
    actual_departure: time.datetime | None
    """ Actual departure time of the train """
    stop_type: str
    """ C = current | N = next | - = other """


def _parse_time(date: time.date, time_str: str | None) -> time.datetime | None:
    """ Parse a time in HH:MM:SS format """
    if not time_str:
        return None
    h, m, s = time_str.split(":", 2)
    return time.datetime.combine(date, time.time(int(h), int(m), int(s)), TIMEZONE)


def parse_train_movements(xml: str | bytes | None, date: time.date) -> list[TrainMovement]:
    """ Returns an ordered list of "train movements" - stations the train went/will go past on the given day """
    if not xml:
        return []
    movement_data: list[dict[str, str]] = xmltodict.parse(xml)["ArrayOfObjTrainMovements"].get("objTrainMovements", [])
    movements: list[TrainMovement] = []
    for entry in movement_data:
        trip_code: str = entry["TrainCode"]
        location_code: str = entry["LocationCode"]
        location_name: str = entry["LocationFullName"]
        location_order: int = int(entry["LocationOrder"])
        location_type: str = entry["LocationType"]
        origin: str = entry["TrainOrigin"]
        destination: str = entry["TrainDestination"]
        scheduled_arrival: time.datetime = _parse_time(date, entry["ScheduledArrival"])
        scheduled_departure: time.datetime = _parse_time(date, entry["ScheduledDeparture"])
        expected_arrival: time.datetime = _parse_time(date, entry["ExpectedArrival"])
        expected_departure: time.datetime = _parse_time(date, entry["ExpectedDeparture"])
        # The API sets these values to 00:00, here we can undo that.
        if location_type == "O":
            scheduled_arrival = scheduled_departure
            expected_arrival = expected_departure
        elif location_type == "D":
            scheduled_departure = scheduled_arrival
            expected_departure = expected_arrival
        actual_arrival: time.datetime | None = _parse_time(date, entry["Arrival"])
        actual_departure: time.datetime | None = _parse_time(date, entry["Departure"])
        stop_type: str = entry["StopType"]
        movements.append(TrainMovement(trip_code, date, location_code, location_name, location_order, location_type, origin, destination,
                                       scheduled_arrival, scheduled_departure, expected_arrival, expected_departure, actual_arrival, actual_departure, stop_type))
    return movements


async def fetch_train_movements(trip_code: str, date: time.date) -> list[TrainMovement]:
    # Note: date might have to be yesterday to properly account for the trip's timing
    xml = await http.get(f"https://api.irishrail.ie/realtime/realtime.asmx/getTrainMovementsXML?TrainId={trip_code}&TrainDate={date:%d %b %Y}", res_method="read")
    return parse_train_movements(xml, date)
