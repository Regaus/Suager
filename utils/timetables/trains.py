from __future__ import annotations

from dataclasses import dataclass

import requests
import xmltodict
from regaus import time

from utils.timetables.shared import TIMEZONE
from utils import http

__all__ = (
    "Train", "parse_train_data",
    "StationDeparture", "parse_station_departures", "fetch_station_departures",
    "TrainMovement", "parse_train_movements", "fetch_train_movements",
    "invalid_trips", "TRAIN_STATION_CODE_TO_ID", "TRAIN_STATION_ID_TO_CODE"
)


invalid_trips: set[str] = set()
""" Set of trip codes that point to incorrect trips on the Irish Rail API (i.e. we need to use the regular GTFS-R API) """
station_departure_cache: dict[str, dict[str, StationDeparture]] = {}
""" Cache of station departure data, in case the information was fetched recently """
station_departure_timestamps: dict[str, float] = {}
""" station_departure_timestamps[station_id] = last time we updated the information (as a timestamp) """
train_movement_cache: dict[str, list[TrainMovement]] = {}
""" Cache of movement updates, in case the information about the trip was already fetched recently """
train_movement_timestamps: dict[str, float] = {}
""" train_movement_timestamps[trip_code] = last time we updated the information inside (as a timestamp) """


def _parse_date(date_str: str) -> time.date | None:
    """ Parse a date in DD MMM YYYY (e.g. "25 Oct 2024") format """
    if not date_str:
        return None
    d, m, y = date_str.split(" ", 2)
    day = int(d)
    year = int(y)
    month = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12
    }[m]
    return time.date(year, month, day)


def _parse_time(date: time.date, time_str: str | None) -> time.datetime | None:
    """ Parse a time in HH:MM:SS format """
    if not time_str:
        return None
    if time_str.count(":") == 2:
        h, m, s = time_str.split(":", 2)
    elif time_str.count(":") == 1:
        h, m = time_str.split(":", 1)
        s = "0"
    else:
        raise ValueError(f"Invalid time received: {time_str!r}")
    _time = time.time(int(h), int(m), int(s))
    # If the times run over midnight, they will be reported as if they were from yesterday (i.e. 25/10/2024 23:59 is followed by 25/10/2024 00:00).
    # I manually fix this here to make the times show up properly.
    # This may break some things if a train ever departs after midnight, but hopefully it won't happen.
    if _time.hour < 4:
        return time.datetime.combine(date + time.timedelta(days=1), _time, TIMEZONE)
    return time.datetime.combine(date, _time, TIMEZONE)


@dataclass()
class Train:
    """ Represents a real-time train location

     API link: https://api.irishrail.ie/realtime/realtime.asmx/getCurrentTrainsXML """
    trip_code: str
    """ Irish Rail's 4-letter trip code """
    latitude: float
    longitude: float
    date: time.date
    """ The date on which the trip started """
    public_message: str
    """ Irish Rail's "public message", which contains information about the current state of the trip """
    direction: str
    """ Northbound, Southbound, or To Station Name """
    train_status: str
    """ N = not yet running | R = running | T = terminated """


def parse_train_data(xml: str | bytes | None) -> dict[str, Train]:
    if not xml:
        return {}
    train_data: list[dict[str, str]] = xmltodict.parse(xml)["ArrayOfObjTrainPositions"].get("objTrainPositions", [])
    if isinstance(train_data, dict):  # Apparently the code breaks if there's exactly one entry
        train_data = [train_data]
    trains: dict[str, Train] = {}
    for entry in train_data:
        trip_code: str = entry["TrainCode"]
        latitude: float = float(entry["TrainLatitude"])
        longitude: float = float(entry["TrainLongitude"])
        date: time.date = _parse_date(entry["TrainDate"])
        public_message: str = entry["PublicMessage"].replace("\\n", "\n")
        direction: str = entry["Direction"]
        status: str = entry["TrainStatus"]
        trains[trip_code] = Train(trip_code, latitude, longitude, date, public_message, direction, status)
    return trains


@dataclass()
class StationDeparture:  # Not sure how exactly to call this
    """ Represents a real-time forecast for upcoming arrivals and departures from this station in the next 90 minutes

     By station name: https://api.irishrail.ie/realtime/realtime.asmx/getStationDataByNameXML?StationDesc=Dublin%20Connolly
     By station code: https://api.irishrail.ie/realtime/realtime.asmx/getStationDataByCodeXML?StationCode=CNLLY """
    trip_code: str
    """ Irish Rail's 4-letter trip code """
    station_name: str
    """ The full name of the station """
    station_code: str
    """ Irish Rail's 4-5-letter code for the station """
    date: time.date
    """ The date on which the trip started """
    query_time: time.datetime
    """ Timestamp at which the query was received by the API """
    origin: str
    """ Name of the origin station """
    destination: str
    """ Name of the destination station """
    origin_time: time.datetime
    """ The time when the train left/will leave the origin """
    destination_time: time.datetime
    """ The time when the train will arrive at the destination """
    status: str
    """ Latest known information about this train """
    last_location: str | None
    """ Last known location of the train """
    due_in: time.timedelta
    """ Time when the train is due to arrive, in minutes """
    delay: time.timedelta
    """ Current delay of the train, in minutes """
    expected_arrival: time.datetime
    """ Expected arrival time """
    expected_departure: time.datetime
    """ Expected departure time """
    scheduled_arrival: time.datetime
    """ Scheduled arrival time """
    scheduled_departure: time.datetime
    """ Scheduled departure time """
    direction: str
    """ Northbound, Southbound, or To Station Name """
    train_type: str
    """ DART or other train """
    location_type: str
    """ O = origin | D = destination | S = stop """


def parse_station_departures(xml: str | bytes | None) -> dict[str, StationDeparture]:
    """ Returns a dictionary of real-time data about arrivals and departure at the given station

     Less useful than GTFS-R since it only provides info for departures between right now and in 90 minutes, but useful to have nonetheless """
    if not xml:
        return {}
    station_data: list[dict[str, str]] = xmltodict.parse(xml)["ArrayOfObjStationData"].get("objStationData", [])
    if isinstance(station_data, dict):
        station_data = [station_data]
    departures: dict[str, StationDeparture] = {}
    for entry in station_data:
        # For some reason, keys in this data only have the first letter capitalised.
        trip_code: str = entry["Traincode"]
        station_name: str = entry["Stationfullname"]
        station_code: str = entry["Stationcode"]
        date: time.date = _parse_date(entry["Traindate"])
        query_time: time.datetime = _parse_time(date, entry["Querytime"])
        origin: str = entry["Origin"]
        destination: str = entry["Destination"]
        origin_time: time.datetime = _parse_time(date, entry["Origintime"])
        destination_time: time.datetime = _parse_time(date, entry["Destinationtime"])
        status: str = entry["Status"]
        last_location: str | None = entry["Lastlocation"]
        due_in: time.timedelta = time.timedelta(minutes=int(entry["Duein"]))
        delay: time.timedelta = time.timedelta(minutes=int(entry["Late"]))
        expected_arrival: time.datetime = _parse_time(date, entry["Exparrival"])
        expected_departure: time.datetime = _parse_time(date, entry["Expdepart"])
        scheduled_arrival: time.datetime = _parse_time(date, entry["Scharrival"])
        scheduled_departure: time.datetime = _parse_time(date, entry["Schdepart"])
        # Fix the expected arrival/departure times showing up as "00:00" at the termini
        if station_name == origin:
            expected_arrival = expected_departure
            scheduled_arrival = scheduled_departure
        elif station_name == destination:
            expected_departure = expected_arrival
            scheduled_departure = scheduled_arrival
        direction: str = entry["Direction"]
        train_type: str = entry["Traintype"]
        location_type: str = entry["Locationtype"]
        departures[trip_code] = StationDeparture(trip_code, station_name, station_code, date, query_time, origin, destination, origin_time, destination_time, status, last_location, due_in, delay,
                                                 expected_arrival, expected_departure, scheduled_arrival, scheduled_departure, direction, train_type, location_type)
    return departures


async def fetch_station_departures(station_id: str, debug: bool = False, write: bool = False) -> dict[str, StationDeparture]:
    """ Fetch real-time departure data for a given station

     Station ID refers to the GTFS Stop ID """
    station_code = TRAIN_STATION_ID_TO_CODE[station_id]
    # If we got details from this trip less than 60 seconds ago, just returned the cached data
    now = time.datetime.now().timestamp
    if station_departure_timestamps.get(station_code, 0) > now - 60:
        if departures := station_departure_cache.get(station_code):
            return departures
    xml: bytes = b""
    if debug:
        try:
            with open(f"data/gtfs/train_stations/{station_code}.xml", "rb") as file:
                xml = file.read()
        except FileNotFoundError:
            pass
    if not xml:  # not debug or file not found
        try:
            xml = await http.get(f"https://api.irishrail.ie/realtime/realtime.asmx/getStationDataByCodeXML?StationCode={station_code}", res_method="read")
        except RuntimeError:  # asyncio is stupid
            xml = requests.get(f"https://api.irishrail.ie/realtime/realtime.asmx/getStationDataByCodeXML?StationCode={station_code}").content
    departures = parse_station_departures(xml)
    if departures:
        station_departure_cache[station_code] = departures
        station_departure_timestamps[station_code] = now
        if write:
            with open(f"data/gtfs/train_stations/{station_code}.xml", "wb") as file:
                file.write(xml)
    return departures


@dataclass()
class TrainMovement:
    """ Represents real-time or past information about a certain trip: the times at which it passed each station along the way

     API link: https://api.irishrail.ie/realtime/realtime.asmx/getTrainMovementsXML?TrainId=D574&TrainDate=23%20oct%202024 """
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
    """ O = origin | D = destination | S = stop | T = timing point (non-stop) | C = curtailed (?) """
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


def parse_train_movements(xml: str | bytes | None) -> list[TrainMovement]:
    """ Returns an ordered list of "train movements" - stations the train went/will go past on the given day """
    if not xml:
        return []
    movement_data: list[dict[str, str]] = xmltodict.parse(xml)["ArrayOfObjTrainMovements"].get("objTrainMovements", [])
    if isinstance(movement_data, dict):
        movement_data = [movement_data]
    movements: list[TrainMovement] = []
    last_stop = len(movement_data) - 1
    for idx, entry in enumerate(movement_data):
        trip_code: str = entry["TrainCode"]
        date: time.date = _parse_date(entry["TrainDate"])
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
        if idx == 0:  # location_type == "O":
            scheduled_arrival = scheduled_departure
            expected_arrival = expected_departure
        elif idx == last_stop:  # location_type == "D":
            scheduled_departure = scheduled_arrival
            expected_departure = expected_arrival
        actual_arrival: time.datetime | None = _parse_time(date, entry["Arrival"])
        actual_departure: time.datetime | None = _parse_time(date, entry["Departure"])
        stop_type: str = entry["StopType"]
        movements.append(TrainMovement(trip_code, date, location_code, location_name, location_order, location_type, origin, destination,
                                       scheduled_arrival, scheduled_departure, expected_arrival, expected_departure, actual_arrival, actual_departure, stop_type))
    return movements


async def fetch_train_movements(trip_code: str, date: time.date, debug: bool = False, write: bool = False, *, _bypass_invalid_check: bool = False) -> list[TrainMovement]:
    # If the trip was marked as invalid, return no data
    if trip_code in invalid_trips and not _bypass_invalid_check:
        return []
    # If we got details from this trip less than 60 seconds ago, just returned the cached data
    now = time.datetime.now().timestamp
    if train_movement_timestamps.get(trip_code, 0) > now - 60:
        if movements := train_movement_cache.get(trip_code):
            return movements
    # Note: date might have to be yesterday to properly account for the trip's timing
    xml: bytes = b""
    if debug:
        try:
            with open(f"data/gtfs/train_movements/{trip_code}.xml", "rb") as file:
                xml = file.read()
        except FileNotFoundError:
            pass
    if not xml:  # not debug or file not found
        try:
            xml = await http.get(f"https://api.irishrail.ie/realtime/realtime.asmx/getTrainMovementsXML?TrainId={trip_code}&TrainDate={date:%d %b %Y}", res_method="read")
        except RuntimeError:  # asyncio is stupid
            xml = requests.get(f"https://api.irishrail.ie/realtime/realtime.asmx/getTrainMovementsXML?TrainId={trip_code}&TrainDate={date:%d %b %Y}").content
    movements = parse_train_movements(xml)
    if movements:
        train_movement_cache[trip_code] = movements
        train_movement_timestamps[trip_code] = now
        if write:
            with open(f"data/gtfs/train_movements/{trip_code}.xml", "wb") as file:
                file.write(xml)
    return movements


# Mapping between Irish Rail station codes and GTFS stop IDs
TRAIN_STATION_CODE_TO_ID: dict[str, str] = {
    "BFSTC": "7020IR2162",  # Belfast
    "LBURN": "7020IR0037",  # Lisburn
    "LURGN": "7040IR0090",  # Lurgan
    "PDOWN": "7040IR0045",  # Portadown
    "SLIGO": "8510IR0092",  # Sligo (MacDiarmada)
    "NEWRY": "7040IR0042",  # Newry
    "COLNY": "8510IR0094",  # Collooney
    "BALNA": "8490IR0076",  # Ballina
    "BMOTE": "8510IR0093",  # Ballymote
    "DDALK": "8300IR0075",  # Dundalk (Clarke)
    "FXFRD": "8490IR0080",  # Foxford
    "BOYLE": "8500IR0090",  # Boyle
    "DRMOD": "8480IR0069",  # Dromod
    "CLBAR": "8490IR0081",  # Castlebar
    "MNLAJ": "8490IR0077",  # Manulla Junction
    "WPORT": "8490IR0078",  # Westport
    "BYHNS": "8490IR0079",  # Ballyhaunis
    "CSREA": "8500IR0091",  # Castlerea
    "LFORD": "8290IR0072",  # Longford
    "CLMRS": "8490IR0082",  # Claremorris
    "DGHDA": "8300IR0074",  # Drogheda (MacBride)
    "ETOWN": "8290IR0073",  # Edgeworthstown
    "LTOWN": "8310IR0086",  # Laytown
    "GSTON": "8310IR0019",  # Gormanston
    "RSCMN": "8500IR0089",  # Roscommon
    "BBRGN": "8240IR0018",  # Balbriggan
    "SKRES": "8240IR0023",  # Skerries
    "MLGAR": "8330IR0108",  # Mullingar
    "RLUSK": "8240IR0130",  # Rush and Lusk
    "DBATE": "8240IR0016",  # Donabate
    "MHIDE": "8240IR0020",  # Malahide
    "M3WAY": "8310IR0083",  # M3 Parkway
    "ATLNE": "8330IR0107",  # Athlone
    "DBYNE": "8310IR0084",  # Dunboyne
    "PMNCK": "8240IR0138",  # Portmarnock
    "ENFLD": "8310IR0085",  # Enfield
    "KCOCK": "8260IR0056",  # Kilcock
    "GRGRD": "8220IR0139",  # Clongriffin
    "SUTTN": "8240IR0024",  # Sutton
    "BYSDE": "8240IR0140",  # Bayside
    "HWTHJ": "8240IR0025",  # Howth Junction and Donaghmede
    "HOWTH": "8240IR0017",  # Howth
    "KBRCK": "8220IR0141",  # Kilbarrack
    "HAFLD": "8240IR0030",  # Hansfield
    "CLSLA": "8240IR0041",  # Clonsilla
    "CNOCK": "8240IR0031",  # Castleknock
    "RAHNY": "8220IR0035",  # Raheny
    "HTOWN": "8220IR0131",  # Harmonstown
    "MYNTH": "8260IR0058",  # Maynooth
    "PHNPK": "8240IR0015",  # Navan Road Parkway
    "CMINE": "8240IR0040",  # Coolmine
    "ASHTN": "8220IR0013",  # Ashtown
    "PELTN": "8220IR0014",  # Pelletstown
    "KLSTR": "8220IR3881",  # Killester
    "BBRDG": "8220IR0026",  # Broombridge
    "DCDRA": "8220IR0027",  # Drumcondra
    "CTARF": "8220IR0032",  # Clontarf Road
    "CNLLY": "8220IR0007",  # Dublin Connolly
    "DCKLS": "8220IR0137",  # Docklands
    "TARA": "8220IR0025",   # Tara Street
    "HSTON": "8220IR0132",  # Dublin Heuston
    "PERSE": "8220IR0134",  # Dublin Pearse
    "WLAWN": "8470IR0048",  # Woodlawn
    "GCDK": "8220IR0135",   # Grand Canal Dock
    "CLARA": "8320IR0088",  # Clara
    "BSLOE": "8470IR0046",  # Ballinasloe
    "ADAMS": "8230IR0128",  # Adamstown
    "ADAMF": "8230IR0128",  # Adamstown
    "ADMTN": "8230IR0128",  # Adamstown
    "LDWNE": "8220IR0133",  # Lansdowne Road
    "PWESF": "8220IR0129",  # Park West and Cherry Orchard
    "CHORC": "8220IR0129",  # Park West and Cherry Orchard
    "CLDKN": "8230IR0036",  # Clondalkin Fonthill
    "CLONS": "8230IR0036",  # Clondalkin Fonthill
    "CLONF": "8230IR0036",  # Clondalkin Fonthill
    "SMONT": "8220IR0028",  # Sandymount
    "HZLCH": "8260IR0063",  # Hazelhatch and Celbridge
    "HAZEF": "8260IR0063",  # Hazelhatch and Celbridge
    "HAZES": "8260IR0063",  # Hazelhatch and Celbridge
    "ATMON": "8470IR0047",  # Attymon
    "SIDNY": "8220IR0034",  # Sydney Parade
    "BTSTN": "8250IR0039",  # Booterstown
    "BROCK": "8250IR0030",  # Blackrock
    "ATHRY": "8470IR0043",  # Athenry
    "SEAPT": "8250IR0029",  # Seapoint
    "SHILL": "8250IR0042",  # Salthill and Monkstown
    "DLERY": "8250IR0124",  # Dun Laoghaire (Mallin)
    "SCOVE": "8250IR0111",  # Sandycove and Glasthule
    "GLGRY": "8250IR0037",  # Glenageary
    "DLKEY": "8250IR0014",  # Dalkey
    "ORNMR": "8470IR050",   # Oranmore
    "GALWY": "8460IR0044",  # Galway (Ceannt)
    "TMORE": "8320IR0087",  # Tullamore
    "KILNY": "8250IR0021",  # Killiney
    "SALNS": "8260IR0060",  # Sallins and Naas
    "SKILL": "8250IR0022",  # Shankill
    "CRGHW": "8470IR0049",  # Craughwell
    "BRAY": "8350IR0123",   # Bray (Daly)
    "NBRGE": "8260IR0054",  # Newbridge
    "KDARE": "8260IR0057",  # Kildare
    "ARHAN": "8470IR0042",  # Ardrahan
    "PTRTN": "8280IR0067",  # Portarlington
    "MONVN": "8260IR0059",  # Monasterevin
    "GSTNS": "8350IR0122",  # Greystones
    "KCOOL": "8350IR0121",  # Kilcoole
    "GORT": "8470IR0045",   # Gort
    "PTLSE": "8280IR0068",  # Portlaoise
    "ATHY": "8260IR0055",   # Athy
    "WLOW": "8350IR0120",   # Wicklow
    "RCREA": "8420IR0096",  # Roscrea
    "CJRDN": "8420IR0104",  # Cloughjordan
    "RDRUM": "8350IR0119",  # Rathdrum
    "BBRHY": "8280IR0066",  # Ballybrophy
    "NNAGH": "8420IR0095",  # Nenagh
    "CRLOW": "8210IR0002",  # Carlow
    "ENNIS": "8360IR0003",  # Ennis
    "ARKLW": "8350IR0118",  # Arklow
    "TPMOR": "8420IR0097",  # Templemore Station
    "BHILL": "8420IR0101",  # Birdhill
    "SXMBR": "8360IR0010",  # Sixmilebridge
    "CCONL": "8410IR0071",  # Castleconnell
    "MNEBG": "8210IR0001",  # Muine Bheag (Bagenalstown)
    "THRLS": "8420IR0098",  # Thurles
    "GOREY": "8340IR0110",  # Gorey
    "LMRCK": "8400IR0127",  # Limerick (Colbert)
    "KKNNY": "8270IR0064",  # Kilkenny (MacDonagh)
    "THTWN": "8270IR0065",  # Thomastown
    "ECRTY": "8340IR0109",  # Enniscorthy
    "LMRKJ": "8430IR0100",  # Limerick Junction
    "TIPRY": "8430IR0099",  # Tipperary
    "CAHIR": "8430IR0102",  # Cahir
    "CLMEL": "8430IR0105",  # Clonmel
    "CVILL": "8380IR0006",  # Charleville
    "WXFRD": "8340IR0112",  # Wexford (O Hanrahan)
    "RLSTD": "8340IR0111",  # Rosslare Strand
    "TRLEE": "8390IR0052",  # Tralee Casement Station
    "WFORD": "8440IR0106",  # Waterford (Plunkett)
    "RLEPT": "8340IR0113",  # Rosslare Europort
    "FFORE": "8390IR0053",  # Farranfore
    "MLLOW": "8380IR0004",  # Mallow
    "BTEER": "8380IR0011",  # Banteer
    "RMORE": "8390IR0051",  # Rathmore
    "MLSRT": "8380IR0010",  # Millstreet
    "KLRNY": "8390IR0050",  # Killarney
    "MDLTN": "8380IR0142",  # Midleton
    "CGTWL": "8380IR0016",  # Carrigtwohill
    "GHANE": "8380IR0008",  # Glounthaune
    "CORK": "8370IR0126",   # Cork (Kent)
    "FOTA": "8380IR0009",   # Fota
    "CGLOE": "8380IR0007",  # Carrigaloe
    "RBROK": "8380IR0005",  # Rushbrooke
    "COBH": "8380IR0012",   # Cobh
    "CKOSH": "8480IR0070",  # Carrick-on-Shannon
    "LXCON": "8260IR0062",  # Leixlip(Confey)
    "LXLSA": "8260IR0061",  # Leixlip(Louisa Bridge)
    "KISHO": "8220KISHO",   # Kishoge
    "KISHF": "8220KISHO",   # Kishoge
    "KISHS": "8220KISHO",   # Kishoge
    "PWESS": "8220IR0129",  # Park West and Cherry Orchard
    "CKOSR": "8430IR0103",  # Carrick-on-Suir
    "LSLND": "8380IR0125",  # Little Island
}
TRAIN_STATION_ID_TO_CODE: dict[str, str] = {
    "7020IR2162": "BFSTC",  # Belfast
    "7020IR0037": "LBURN",  # Lisburn
    "7040IR0090": "LURGN",  # Lurgan
    "7040IR0045": "PDOWN",  # Portadown
    "8510IR0092": "SLIGO",  # Sligo (MacDiarmada)
    "7040IR0042": "NEWRY",  # Newry
    "8510IR0094": "COLNY",  # Collooney
    "8490IR0076": "BALNA",  # Ballina
    "8510IR0093": "BMOTE",  # Ballymote
    "8300IR0075": "DDALK",  # Dundalk (Clarke)
    "8490IR0080": "FXFRD",  # Foxford
    "8500IR0090": "BOYLE",  # Boyle
    "8480IR0069": "DRMOD",  # Dromod
    "8490IR0081": "CLBAR",  # Castlebar
    "8490IR0077": "MNLAJ",  # Manulla Junction
    "8490IR0078": "WPORT",  # Westport
    "8490IR0079": "BYHNS",  # Ballyhaunis
    "8500IR0091": "CSREA",  # Castlerea
    "8290IR0072": "LFORD",  # Longford
    "8490IR0082": "CLMRS",  # Claremorris
    "8300IR0074": "DGHDA",  # Drogheda (MacBride)
    "8290IR0073": "ETOWN",  # Edgeworthstown
    "8310IR0086": "LTOWN",  # Laytown
    "8310IR0019": "GSTON",  # Gormanston
    "8500IR0089": "RSCMN",  # Roscommon
    "8240IR0018": "BBRGN",  # Balbriggan
    "8240IR0023": "SKRES",  # Skerries
    "8330IR0108": "MLGAR",  # Mullingar
    "8240IR0130": "RLUSK",  # Rush and Lusk
    "8240IR0016": "DBATE",  # Donabate
    "8240IR0020": "MHIDE",  # Malahide
    "8310IR0083": "M3WAY",  # M3 Parkway
    "8330IR0107": "ATLNE",  # Athlone
    "8310IR0084": "DBYNE",  # Dunboyne
    "8240IR0138": "PMNCK",  # Portmarnock
    "8310IR0085": "ENFLD",  # Enfield
    "8260IR0056": "KCOCK",  # Kilcock
    "8220IR0139": "GRGRD",  # Clongriffin
    "8240IR0024": "SUTTN",  # Sutton
    "8240IR0140": "BYSDE",  # Bayside
    "8240IR0025": "HWTHJ",  # Howth Junction and Donaghmede
    "8240IR0017": "HOWTH",  # Howth
    "8220IR0141": "KBRCK",  # Kilbarrack
    "8240IR0030": "HAFLD",  # Hansfield
    "8240IR0041": "CLSLA",  # Clonsilla
    "8240IR0031": "CNOCK",  # Castleknock
    "8220IR0035": "RAHNY",  # Raheny
    "8220IR0131": "HTOWN",  # Harmonstown
    "8260IR0058": "MYNTH",  # Maynooth
    "8240IR0015": "PHNPK",  # Navan Road Parkway
    "8240IR0040": "CMINE",  # Coolmine
    "8220IR0013": "ASHTN",  # Ashtown
    "8220IR0014": "PELTN",  # Pelletstown
    "8220IR3881": "KLSTR",  # Killester
    "8220IR0026": "BBRDG",  # Broombridge
    "8220IR0027": "DCDRA",  # Drumcondra
    "8220IR0032": "CTARF",  # Clontarf Road
    "8220IR0007": "CNLLY",  # Dublin Connolly
    "8220IR0137": "DCKLS",  # Docklands
    "8220IR0025": "TARA",  # Tara Street
    "8220IR0132": "HSTON",  # Dublin Heuston
    "8220IR0134": "PERSE",  # Dublin Pearse
    "8470IR0048": "WLAWN",  # Woodlawn
    "8220IR0135": "GCDK",  # Grand Canal Dock
    "8320IR0088": "CLARA",  # Clara
    "8470IR0046": "BSLOE",  # Ballinasloe
    # "8230IR0128": "ADAMS",  # Adamstown
    # "8230IR0128": "ADAMF",  # Adamstown
    "8230IR0128": "ADMTN",  # Adamstown
    "8220IR0133": "LDWNE",  # Lansdowne Road
    # "8220IR0129": "PWESF",  # Park West and Cherry Orchard
    "8220IR0129": "CHORC",  # Park West and Cherry Orchard
    # "8220IR0129": "PWESS",  # Park West and Cherry Orchard
    "8230IR0036": "CLDKN",  # Clondalkin Fonthill
    # "8230IR0036": "CLONS",  # Clondalkin Fonthill
    # "8230IR0036": "CLONF",  # Clondalkin Fonthill
    "8220IR0028": "SMONT",  # Sandymount
    "8260IR0063": "HZLCH",  # Hazelhatch and Celbridge
    # "8260IR0063": "HAZEF",  # Hazelhatch and Celbridge
    # "8260IR0063": "HAZES",  # Hazelhatch and Celbridge
    "8470IR0047": "ATMON",  # Attymon
    "8220IR0034": "SIDNY",  # Sydney Parade
    "8250IR0039": "BTSTN",  # Booterstown
    "8250IR0030": "BROCK",  # Blackrock
    "8470IR0043": "ATHRY",  # Athenry
    "8250IR0029": "SEAPT",  # Seapoint
    "8250IR0042": "SHILL",  # Salthill and Monkstown
    "8250IR0124": "DLERY",  # Dun Laoghaire (Mallin)
    "8250IR0111": "SCOVE",  # Sandycove and Glasthule
    "8250IR0037": "GLGRY",  # Glenageary
    "8250IR0014": "DLKEY",  # Dalkey
    "8470IR050": "ORNMR",  # Oranmore
    "8460IR0044": "GALWY",  # Galway (Ceannt)
    "8320IR0087": "TMORE",  # Tullamore
    "8250IR0021": "KILNY",  # Killiney
    "8260IR0060": "SALNS",  # Sallins and Naas
    "8250IR0022": "SKILL",  # Shankill
    "8470IR0049": "CRGHW",  # Craughwell
    "8350IR0123": "BRAY",  # Bray (Daly)
    "8260IR0054": "NBRGE",  # Newbridge
    "8260IR0057": "KDARE",  # Kildare
    "8470IR0042": "ARHAN",  # Ardrahan
    "8280IR0067": "PTRTN",  # Portarlington
    "8260IR0059": "MONVN",  # Monasterevin
    "8350IR0122": "GSTNS",  # Greystones
    "8350IR0121": "KCOOL",  # Kilcoole
    "8470IR0045": "GORT",  # Gort
    "8280IR0068": "PTLSE",  # Portlaoise
    "8260IR0055": "ATHY",  # Athy
    "8350IR0120": "WLOW",  # Wicklow
    "8420IR0096": "RCREA",  # Roscrea
    "8420IR0104": "CJRDN",  # Cloughjordan
    "8350IR0119": "RDRUM",  # Rathdrum
    "8280IR0066": "BBRHY",  # Ballybrophy
    "8420IR0095": "NNAGH",  # Nenagh
    "8210IR0002": "CRLOW",  # Carlow
    "8360IR0003": "ENNIS",  # Ennis
    "8350IR0118": "ARKLW",  # Arklow
    "8420IR0097": "TPMOR",  # Templemore Station
    "8420IR0101": "BHILL",  # Birdhill
    "8360IR0010": "SXMBR",  # Sixmilebridge
    "8410IR0071": "CCONL",  # Castleconnell
    "8210IR0001": "MNEBG",  # Muine Bheag (Bagenalstown)
    "8420IR0098": "THRLS",  # Thurles
    "8340IR0110": "GOREY",  # Gorey
    "8400IR0127": "LMRCK",  # Limerick (Colbert)
    "8270IR0064": "KKNNY",  # Kilkenny (MacDonagh)
    "8270IR0065": "THTWN",  # Thomastown
    "8340IR0109": "ECRTY",  # Enniscorthy
    "8430IR0100": "LMRKJ",  # Limerick Junction
    "8430IR0099": "TIPRY",  # Tipperary
    "8430IR0102": "CAHIR",  # Cahir
    "8430IR0105": "CLMEL",  # Clonmel
    "8380IR0006": "CVILL",  # Charleville
    "8340IR0112": "WXFRD",  # Wexford (O Hanrahan)
    "8340IR0111": "RLSTD",  # Rosslare Strand
    "8390IR0052": "TRLEE",  # Tralee Casement Station
    "8440IR0106": "WFORD",  # Waterford (Plunkett)
    "8340IR0113": "RLEPT",  # Rosslare Europort
    "8390IR0053": "FFORE",  # Farranfore
    "8380IR0004": "MLLOW",  # Mallow
    "8380IR0011": "BTEER",  # Banteer
    "8390IR0051": "RMORE",  # Rathmore
    "8380IR0010": "MLSRT",  # Millstreet
    "8390IR0050": "KLRNY",  # Killarney
    "8380IR0142": "MDLTN",  # Midleton
    "8380IR0016": "CGTWL",  # Carrigtwohill
    "8380IR0008": "GHANE",  # Glounthaune
    "8370IR0126": "CORK",  # Cork (Kent)
    "8380IR0009": "FOTA",  # Fota
    "8380IR0007": "CGLOE",  # Carrigaloe
    "8380IR0005": "RBROK",  # Rushbrooke
    "8380IR0012": "COBH",  # Cobh
    "8480IR0070": "CKOSH",  # Carrick-on-Shannon
    "8260IR0062": "LXCON",  # Leixlip(Confey)
    "8260IR0061": "LXLSA",  # Leixlip(Louisa Bridge)
    "8220KISHO": "KISHO",  # Kishoge
    # "8220KISHO": "KISHF",  # Kishoge
    # "8220KISHO": "KISHS",  # Kishoge
    "8430IR0103": "CKOSR",  # Carrick-on-Suir
    "8380IR0125": "LSLND",  # Little Island
}
