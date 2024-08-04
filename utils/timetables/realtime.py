from __future__ import annotations

from dataclasses import dataclass

from regaus import time

from utils.timetables.shared import GTFSAPIError, TIMEZONE


__all__ = [
    "load_gtfs_r_data", "GTFSRData", "VehicleData",
    "Header", "TripUpdate", "RealTimeTrip", "StopTimeUpdate", "Vehicle"
]


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
    entities: dict[str, TripUpdate]  # real_trip_id -> TripUpdate

    @classmethod
    def load(cls, data: dict | None):
        # If no data is available, keep self.data null until we do get some data
        if data is None:
            return None
        # See if the API returned any errors
        if "status_code" in data and "message" in data:
            raise GTFSAPIError(f"{data['status_code']}: {data['message']}", "real-time")
        if "entity" not in data:
            return None
        trip_updates: dict[str, TripUpdate] = {}
        for entity in data["entity"]:
            trip_update = TripUpdate.load(entity)
            trip_updates[trip_update.entity_id] = trip_update
        return cls(Header.load(data["header"]), trip_updates)


@dataclass()
class VehicleData:
    header: Header
    entities: dict[str, Vehicle]

    @classmethod
    def load(cls, data: dict | None):
        if data is None:
            return None
        # See if the API returned any errors
        if "status_code" in data and "message" in data:
            raise GTFSAPIError(f"{data['status_code']}: {data['message']}", "vehicles")
        if "entity" not in data:
            return None
        vehicles: dict[str, Vehicle] = {}
        for entity in data["entity"]:
            vehicle = Vehicle.load(entity)
            vehicles[vehicle.vehicle_id] = vehicle
        return cls(Header.load(data["header"]), vehicles)


@dataclass()
class Header:
    gtfsr_version: str
    incrementality: str
    timestamp: time.datetime

    @classmethod
    def load(cls, data: dict):
        return cls(data["gtfs_realtime_version"], data["incrementality"], time.datetime.from_timestamp(int(data["timestamp"]), tz=TIMEZONE))


@dataclass()
class TripUpdate:
    entity_id: str
    trip: RealTimeTrip
    stop_times: list[StopTimeUpdate] | None
    vehicle_id: str | None

    @classmethod
    def load(cls, data: dict):
        trip_data = data["trip_update"]
        stop_times = [StopTimeUpdate.load(i) for i in trip_data["stop_time_update"]] if "stop_time_update" in trip_data else None
        if "vehicle" in trip_data:
            vehicle_id = trip_data["vehicle"]["id"]
        else:
            vehicle_id = None
        return cls(data["id"], RealTimeTrip.load(trip_data["trip"]), stop_times, vehicle_id)


@dataclass()
class RealTimeTrip:
    trip_id: str
    route_id: str
    start_time: time.datetime
    schedule_relationship: str  # SCHEDULED, ADDED, UNSCHEDULED, CANCELED, DUPLICATED, DELETED
    direction_id: int

    @classmethod
    def load(cls, data: dict):
        _time: str = data["start_time"]
        _date: str = data["start_date"]
        h, m, s = _time.split(":")
        y, mo, d = _date[0:4], _date[4:6], _date[6:8]
        start_time = time.datetime(int(y), int(mo), int(d), int(h) % 24, int(m), int(s), tz=TIMEZONE)
        if int(h) >= 24:
            start_time += time.timedelta(days=1)
        return cls(data.get("trip_id", "Unknown"), data["route_id"], start_time, data.get("schedule_relationship", "Unknown"), data["direction_id"])


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

    @classmethod
    def load(cls, data: dict):
        entity_id = data["id"]
        vehicle_data = data["vehicle"]
        trip = RealTimeTrip.load(vehicle_data["trip"])
        position = vehicle_data["position"]
        vehicle_id = vehicle_data["vehicle"]["id"]
        return cls(entity_id, trip, position["latitude"], position["longitude"], vehicle_id)
