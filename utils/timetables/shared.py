import json

import pytz

from utils import database

__all__ = (
    "__version__",
    "real_time_filename", "vehicles_filename", "trains_filename",
    "TIMEZONE", "CHUNK_SIZE", "WEEKDAYS", "NUMBERS", "WARNING", "CANCELLED",
    "get_database", "get_data_database",
    "GTFSAPIError",
    "TRAIN_STATION_CODE_TO_ID", "TRAIN_STATION_ID_TO_CODE"
)


# Constants
__version__ = json.load(open("version.json", "r"))["timetables"]["version"]

real_time_filename = "data/gtfs/real_time.json"
vehicles_filename = "data/gtfs/vehicles.json"
trains_filename = "data/gtfs/trains.xml"
TIMEZONE = pytz.timezone("Europe/Dublin")
CHUNK_SIZE = 256

WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
NUMBERS = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
WARNING = "⚠️ "
CANCELLED = "⛔\u2060 "  # Insert a zero-width non-breaking space to even out the string length


def get_database() -> database.Database:
    """ Returns the database for static GTFS data """
    return database.Database("gtfs/static.db")


def get_data_database() -> database.Database:
    """ Returns the database for general bot data (including Timetables bot's route filter) """
    return database.Database("database.db")


class GTFSAPIError(RuntimeError):
    """ An error occurred when requesting data from the GTFS API """
    def __init__(self, text=None, error_place: str = None):
        # error_place = whether the error occurred at real-time data or vehicle data
        super().__init__(text)
        self.error_place = error_place


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
