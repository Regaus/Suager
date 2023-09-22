import discord
import pytz
from regaus import time

from utils import http, logger
from utils.time import time as now_time

# Most of the code related to fetching the data from the API was made by novanai
BASE_URL = "https://scientia-eu-v4-api-d1-03.azurewebsites.net/api/Public"
INSTITUTION_IDENTITY = "a1fdee6b-68eb-47b8-b2ac-a4c60c8e6177"
PROGRAMMES_OF_STUDY = "241e4d36-60e0-49f8-b27e-99416745d98d"
COMSCI1 = "db214724-e16c-82a1-8b07-5edb97d78f2d"
TZ = pytz.timezone("Europe/Dublin")

# Building names
BUILDINGS = {
    "C": "Henry Grattan",
    "H": "Nursing",
    "L": "McNulty",
    "N": "Marconi",
    "Q": "Business",
    "S": "Stokes",
    "SA": "Stokes Annex",
    "T": "Terence Larkin",
    "X": "Lonsdale"
}
# Shortened module names
MODULES = {
    # Semester 1
    "CA103": "Computer Systems",
    "CA106": "Web Design",
    "CA116": "Computer Programming",
    "CA172": "Problem-Solving & Critical Thinking",
    "MS134": "IT Mathematics",

    # Semester 2
    "CA115": "Digital Innovation Management",
    "CA117": "Computer Programming",
    "CA169": "Networks & Internet",
    "CA170": "Operating Systems",
    "MS135": "IT Mathematics"
}


def get_times() -> tuple[time.datetime, time.datetime]:
    """ Returns the start and end times for the current week """
    now = time.datetime.now(tz=TZ)
    if now < time.datetime(2023, 9, 25, tz=TZ):
        start = time.datetime(2023, 9, 25, tz=TZ)
        # start = time.datetime(2024, 2, 5, tz=TZ)  # Test for semester 2 timetables
    else:
        start: time.datetime = (now - time.timedelta(days=now.weekday)).replace(hour=0, minute=0, second=0, microsecond=0)
    end: time.datetime = start + time.timedelta(weeks=1) - time.timedelta(seconds=1)

    return start, end


async def get_timetable():
    """ Get the timetable for the Computer Science course for the current week (or Week 3 if it is earlier than 25/09/2023) """
    start, end = get_times()
    start = start.as_timezone(time.utc)
    end = end.as_timezone(time.utc)

    async with http.session.post(
            f"{BASE_URL}/CategoryTypes/Categories/Events/Filter/{INSTITUTION_IDENTITY}?startRange={start.iso()}.000Z&endRange={end.iso()}.999Z",
            headers={
                "Authorization": "Anonymous",
                "Content-type": "application/json"
            },
            json={
                "ViewOptions": {
                    "Days": [
                        {"DayOfWeek": 1},
                        {"DayOfWeek": 2},
                        {"DayOfWeek": 3},
                        {"DayOfWeek": 4},
                        {"DayOfWeek": 5},
                    ],
                },
                "CategoryTypesWithIdentities": [
                    {
                        "CategoryTypeIdentity": PROGRAMMES_OF_STUDY,
                        "CategoryIdentities": [COMSCI1],
                    }
                ],
            }
    ) as res:
        if not res.ok:
            if res.content_type == "application/json":
                data = await res.json()
                ts = f"{now_time()} > Suager > DCU Timetable Fetcher > Encountered an error:\n"
                logger.log("Suager", "dcu", ts + data)
            res.raise_for_status()

        data = await res.json()
        return data


async def timetable_embed() -> discord.Embed:
    start, end = get_times()
    embed = discord.Embed(title="Timetable for DCU Computer Science - Year 1", description=f"Timetables for the week: **{start:%d %B} to {end:%d %B %Y}**")
    data = await get_timetable()
    events_str = data["CategoryEvents"][0]["Results"]
    events = [Event(event) for event in events_str]
    events.sort(key=lambda x: x.start)  # Sort by starting time
    event_days: dict[int, list[str]] = {0: [], 1: [], 2: [], 3: [], 4: []}  # Mon - Fri
    for event in events:
        event_days[event.start.weekday].append(str(event))

    for day, event_list in event_days.items():
        name = (start + time.timedelta(days=day)).format("%A, %d %B %Y")
        value = "\n".join(event_list)
        if not value:
            value = "No lectures this day!"
        embed.add_field(name=name, value=value, inline=False)
    return embed


class Event(object):
    def __init__(self, data: dict):
        self.start = self.iso_to_datetime(data["StartDateTime"])                        # Start datetime
        self.end = self.iso_to_datetime(data["EndDateTime"])                            # End datetime
        self.location = data["Location"]                                                # Code for building and room
        # self.description = data["Description"]                                          # Lecture / Lab / Tutorial
        self.name = data["Name"]                                                        # Coded name of the event
        self.event_type = data["EventType"]                                             # On Campus
        self.module_name = self.get_module_name(data["ExtraProperties"][0]["Value"])    # Module name in English

        # Decode description -> Lecture / Lab / Tutorial (since some modules show module name instead of actual type)
        # if self.description.startswith("IT Mathematics"):
        lecture_type = self.name.split("/")[1]
        letter = lecture_type[0]
        description = {
            "L": "Lecture",
            "P": "Lab",
            "T": "Tutorial"
        }.get(letter)
        if letter == "T":
            description += data["Description"][-8:]  # " Group X"
        self.description = description

    @staticmethod
    def iso_to_datetime(data: str) -> time.datetime:
        """ Convert ISO timestamp to datetime in Europe/Dublin timezone """
        date_str, time_str = data.split("T")
        event_date = time.date.from_iso(date_str)
        event_time = time.time.from_iso(time_str)
        return time.datetime.combine(event_date, event_time).to_timezone(TZ)

    @staticmethod
    def get_module_name(data: str) -> str:
        module = data[:5]
        module_name = MODULES[module]
        return f"**[{module}]** {module_name}"

    def building_and_room(self) -> str:
        """ Convert the location code into human-readable format """
        rooms = self.location.split(", ")
        building_code = rooms[0][4:-3]  # Assume the building is the same for all labs
        rooms_list = ", ".join([room[-3:] for room in rooms])
        return f"{BUILDINGS[building_code]} {rooms_list}"

    def __str__(self) -> str:
        return f"**{self.start:%H:%M} - {self.end:%H:%M}** - {self.description} - {self.module_name} - {self.building_and_room()}"
