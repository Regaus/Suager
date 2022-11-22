from __future__ import annotations

from dataclasses import dataclass

from regaus import time


@dataclass()
class GTFSData:
    header: Header
    entities: list[...]

    @classmethod
    def load(cls, data: dict):
        # If no data is available, keep self.data null until we do get some data
        if data is None:
            return None
        return cls(Header.load(data["Header"]), [Entity.load(e) for e in data["Entity"]])


@dataclass()
class Header:
    gtfsr_version: str
    incrementality: str
    timestamp: time.datetime

    @classmethod
    def load(cls, data: dict):
        return cls(data["GtfsRealtimeVersion"], data["Incrementality"], time.datetime.from_timestamp(data["Timestamp"]))


@dataclass()
class Entity:
    id: str
    is_deleted: bool
    trip_update: TripUpdate

    # def __post_init__(self):
    #     print(f"Entity {self.id} initialised")

    @classmethod
    def load(cls, data: dict):
        return cls(data["Id"], data["IsDeleted"], TripUpdate.load(data["TripUpdate"]))


@dataclass()
class TripUpdate:
    trip: Trip
    stop_times: list[StopTimeUpdate] | None

    @classmethod
    def load(cls, data: dict):
        stop_times = [StopTimeUpdate.load(i) for i in data["StopTimeUpdate"]] if "StopTimeUpdate" in data else None
        return cls(data["Trip"], stop_times)


@dataclass()
class Trip:
    trip_id: str
    route_id: str
    start_time: time.datetime
    schedule: str

    @classmethod
    def load(cls, data: dict):
        _time: str = data["StartTime"]
        _date: str = data["StartDate"]
        h, m, s = _time.split(":")
        y, mo, d = _date[0:4], _date[4:6], _date[6:8]
        # This might have to be in Europe/Dublin timezone, but we'll ignore that for now
        # TODO: See what happens in March when daylight savings kick back in
        start_time = time.datetime(int(y), int(mo), int(d), int(h), int(m), int(s))
        return cls(data["TripId"], data["RouteId"], start_time, data["ScheduleRelationship"])


@dataclass()
class StopTimeUpdate:
    stop_sequence: int
    stop_id: str
    schedule: str
    arrival_delay: time.timedelta = None
    departure_delay: time.timedelta = None

    @classmethod
    def load(cls, data: dict):
        try:
            arrival = time.timedelta(seconds=data["Arrival"]["Delay"]) if "Arrival" in data else None
        except KeyError:
            arrival = None
        try:
            departure = time.timedelta(seconds=data["Departure"]["Delay"]) if "Departure" in data else None
        except KeyError:
            departure = None
        return cls(data["StopSequence"], data["StopId"], data["ScheduleRelationship"], arrival, departure)
