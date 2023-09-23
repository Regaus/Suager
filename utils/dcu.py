from __future__ import annotations

import json

import discord
import pytz
from regaus import time, print_error

from utils import http, logger
from utils.time import time as now_time

# Most of the code related to fetching the data from the API was made by novanai
# Let's define some constants
BASE_URL = "https://scientia-eu-v4-api-d1-03.azurewebsites.net/api/Public"  # URL for the API
INSTITUTION_IDENTITY = "a1fdee6b-68eb-47b8-b2ac-a4c60c8e6177"  # Identity for DCU
# CategoryTypes: whether we sort by Modules, Locations, or Programmes of Study
MODULES_CATEGORY = "525fe79b-73c3-4b5c-8186-83c652b3adcc"
LOCATIONS_CATEGORY = "1e042cb1-547d-41d4-ae93-a1f2c3d34538"
PROGRAMMES_OF_STUDY = "241e4d36-60e0-49f8-b27e-99416745d98d"
# Identity for Computer Science 1
# COMSCI1 = "db214724-e16c-82a1-8b07-5edb97d78f2d"
# The timezone we're using
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


def get_times(course_code: str = "COMSCI1") -> tuple[time.datetime, time.datetime]:
    """ Returns the start and end times for the current week """
    now = time.datetime.now(tz=TZ)
    first_week = time.datetime(2023, 9, 11, tz=TZ)
    if course_code.endswith("1"):  # First-year courses start on 25 September
        first_week = time.datetime(2023, 9, 25, tz=TZ)
    if now < first_week:
        start = first_week
        # start = time.datetime(2024, 2, 5, tz=TZ)  # Test for semester 2 timetables
    else:
        start: time.datetime = (now - time.timedelta(days=now.weekday)).replace(hour=0, minute=0, second=0, microsecond=0)
    end: time.datetime = start + time.timedelta(weeks=1) - time.timedelta(seconds=1)

    return start, end


async def get_data(url: str, headers: dict, json_data: dict = None, name: str = "DCU Timetable Fetcher") -> dict:
    """ Get any data from the API and then spit out the result """
    async with http.session.post(url, headers=headers, json=json_data) as res:
        if not res.ok:
            if res.content_type == "application/json":
                data = await res.json()
                ts = f"{now_time()} > Suager > {name} > Encountered an error:\n"
                logger.log("Suager", "dcu", ts + data)
            res.raise_for_status()

        data = await res.json()
        return data


async def get_courses_from_api() -> dict:
    """ Get the list of courses currently available """
    total_pages = 28
    output = {"TotalPages": 28, "CurrentPage": 1, "Results": [], "Count": 554}
    i = 0
    while i < total_pages:
        i += 1
        data = await get_data(
            f"{BASE_URL}/CategoryTypes/{PROGRAMMES_OF_STUDY}/Categories/FilterWithCache/{INSTITUTION_IDENTITY}?pageNumber={i}&query=",
            headers={
                "Authorization": "Anonymous",
                "Content-type": "application/json"
            },
            name="DCU Course List Fetcher"
        )
        if data["TotalPages"] != total_pages:
            print_error(f"There are {data['TotalPages']} pages of data, expected {total_pages}. Update the hardcoded limit.")
            output["TotalPages"] = data["TotalPages"]
        output["CurrentPage"] = data["CurrentPage"]
        output["Count"] = data["Count"]
        output["Results"] += data["Results"]  # This should make it so that the returned results are the complete list of courses
    if output["CurrentPage"] != output["TotalPages"]:
        raise ValueError(f"Current page does not equal total pages: {output['CurrentPages']} != {output['TotalPages']}")
    return output


async def get_courses_from_cache() -> dict:
    """ Get the list of courses from cache. If it is too old, download the course list from the API again """
    data = None
    must_renew = False
    timestamp = time.datetime.now().timestamp
    try:
        with open("data/dcu/courses.json", "r") as file:
            data = json.loads(file.read())
            # If the data is more than a month old
            if data["timestamp"] - timestamp > 86400 * 30:
                must_renew = True
    except FileNotFoundError:
        must_renew = True
    if must_renew:
        data = await get_courses_from_api()
        data["timestamp"] = timestamp
        with open("data/dcu/courses.json", "w+") as file:
            file.write(json.dumps(data))
    return data


async def get_course_identities() -> dict[str, Course]:
    """ Make a dict of course identities to be used by the timetables API """
    data = await get_courses_from_cache()
    output = {}
    for course_data in data["Results"]:
        code = course_data["Name"]
        # Don't overwrite the course data if there is a duplicate
        if code not in output:
            output[code] = Course(course_data)
    return output


async def get_courses(search: str = None) -> list[str]:
    """ Get the list of course names """
    data = await get_course_identities()
    output: list[str] = [str(course) for course in data.values()]
    if search is not None:
        # Filter the output to only include courses that contain the search string
        output = [course for course in output if search.lower() in course.lower()]
    return output


async def get_timetable_data(course: Course):
    """ Get the timetable for the Computer Science course for the current week (or Week 3 if it is earlier than 25/09/2023) """
    start, end = get_times(course.code)
    start = start.as_timezone(time.utc)
    end = end.as_timezone(time.utc)

    return await get_data(
        f"{BASE_URL}/CategoryTypes/Categories/Events/Filter/{INSTITUTION_IDENTITY}?startRange={start.iso()}.000Z&endRange={end.iso()}.999Z",
        headers={
            "Authorization": "Anonymous",
            "Content-type": "application/json"
        },
        json_data={
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
                    "CategoryIdentities": [course.identity],
                }
            ],
        },
        name="DCU Timetable Fetcher"
    )


async def get_timetable(course_code: str = "COMSCI1") -> discord.Embed:
    """ Get the timetables data and return a human-readable embed with the current week's timetable """
    start, end = get_times(course_code)

    courses = await get_course_identities()
    try:
        course = courses[course_code.upper()]
    except KeyError:
        raise KeyError(f"Course not found: {course_code}")
    data = await get_timetable_data(course)
    course_name = course.name
    if course.code[-1].isdigit():
        course_name += f" - Year {course.code[-1]}"

    embed = discord.Embed(title="DCU Timetables", description=f"Timetable for course: **{course_name} ({course.code})**\nTimetables for the week: **{start:%d %B} to {end:%d %B %Y}**")
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
        self.start = self.iso_to_datetime(data["StartDateTime"])                      # Start datetime
        self.end = self.iso_to_datetime(data["EndDateTime"])                          # End datetime
        self.location: str = data["Location"]                                         # Code for building and room
        # self.description = data["Description"]                                       # Lecture / Lab / Tutorial
        self.name: str = data["Name"]                                                 # Coded name of the event
        self.event_type: str = data["EventType"]                                      # On Campus
        self.module_name = self.get_module_name(data["ExtraProperties"][0]["Value"])  # Module name in English

        # Decode description -> Lecture / Lab / Tutorial (since some modules show module name instead of actual type)
        # if self.description.startswith("IT Mathematics"):
        lecture_type = self.name.split("/")[-2]
        letter = lecture_type[0]
        description = {
            "L": "Lecture",
            "P": "Practical",
            "T": "Tutorial",
            "W": "Workshop",
            "S": "Seminar"
        }.get(letter, letter)
        if letter == "T" and "IT Mathematics" in data["Description"]:
            description += data["Description"][-8:]  # " Group X"
        elif letter in ["T", "W", "S"]:
            group = self.name.split("/")[2]
            description += f" Group {group}"
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
        module_code, module_name = data.split(' ', 1)
        try:
            module_name = MODULES[module_code]
        except KeyError:
            pass  # Leave the module name as-is
        return f"**[{module_code[:-3]}]** {module_name}"

    def building_and_room(self) -> str:
        """ Convert the location code into human-readable format """
        rooms = self.location.split(", ")
        building_code = rooms[0][4:-3]  # Assume the building is the same for all labs
        rooms_list = ", ".join([room[-3:] for room in rooms])
        return f"{BUILDINGS[building_code]} {rooms_list}"

    def __str__(self) -> str:
        return f"**{self.start:%H:%M} - {self.end:%H:%M}** - {self.description} - {self.module_name} - {self.building_and_room()}"


class Course(object):
    def __init__(self, data: dict):
        self.code: str = data["Name"]          # Course code (e.g. AC1, COMSCI1)
        self.name: str = data["Description"]   # Human-readable course name
        self.identity: str = data["Identity"]  # Course UUID

    def __str__(self) -> str:
        return f"**{self.code}** - {self.name}"
