from __future__ import annotations

from dataclasses import dataclass

from regaus import time

from utils.timetables.shared import GTFSAPIError, TIMEZONE

__all__ = (
    "empty_real_time_str",
    "load_gtfs_r_data", "GTFSRData", "VehicleData",
    "Header", "TripUpdate", "RealTimeTrip", "StopTimeUpdate", "Vehicle",
)


empty_real_time_str: bytes = b'{"header": {"gtfs_realtime_version": "2.0", "incrementality": "EMPTY", "timestamp": "0"}, "entity": {}}'


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
    arrival_delay: time.timedelta | None = None
    departure_delay: time.timedelta | None = None
    arrival_time: time.datetime | None = None
    departure_time: time.datetime | None = None

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
