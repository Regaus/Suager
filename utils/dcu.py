from __future__ import annotations

import json
import re
from collections.abc import Callable, Awaitable
from typing import Type, TypeVar

import discord
import pytz
from icalendar import Calendar, Event as CalendarEvent
from regaus import time, print_error

from utils import http, logger, general
from utils.time import time as now_time

# The original code related to fetching the timetables from the API was made by novanai
# Let's define some constants
BASE_URL = "https://scientia-eu-v4-api-d1-03.azurewebsites.net/api/Public"  # URL for the API
INSTITUTION_IDENTITY = "a1fdee6b-68eb-47b8-b2ac-a4c60c8e6177"  # Identity for DCU
# CategoryTypes: whether we sort by Modules, Locations, or Programmes of Study
MODULES_CATEGORY = "525fe79b-73c3-4b5c-8186-83c652b3adcc"
LOCATIONS_CATEGORY = "1e042cb1-547d-41d4-ae93-a1f2c3d34538"
PROGRAMMES_OF_STUDY = "241e4d36-60e0-49f8-b27e-99416745d98d"
# Identity for Computer Science 1
COMSCI1 = "db214724-e16c-82a1-8b07-5edb97d78f2d"
# The timezone we're using
TZ = pytz.timezone("Europe/Dublin")
# Building names
BUILDINGS_SHORT = {
    "A": "Albert",
    "B": "Invent",
    "C": "Henry Grattan",
    "CA": "Henry Grattan Ext",
    "D": "BEA Orpen",
    "G": "NICB",
    "GA": "NRF",
    "H": "Nursing",
    "J": "Hamilton",
    "KA": "Student Centre",
    "L": "McNulty",
    "N": "Marconi",
    "Q": "Business",
    "S": "Stokes",
    "SA": "Stokes Annex",
    "T": "Terence Larkin",
    "X": "Lonsdale",
    "Y": "Library",
    "Z": "Helix"
}
BUILDINGS = {
    "GLA": {
        "A":  "Albert College",
        "B":  "Invent Building",
        "C":  "Henry Grattan Building",
        "CA": "Henry Grattan Extension",
        "D":  "BEA Orpen Building",
        "E":  "Estates Office",
        "F":  "Multi-Storey Car Park",
        "G":  "NICB Building",
        "GA": "NRF Building",
        "H":  "Nursing Building",
        "J":  "Hamilton Building",
        "KA": "U Building / Student Centre",
        "L":  "McNulty Building",
        "M":  "Interfaith Centre",
        "N":  "Marconi Building",
        "P":  "Pavilion",
        "PR": "Restaurant",
        "Q":  "Business School",
        "QA": "MacCormac Reception",
        "R":  "Creche",
        "S":  "Stokes Building",
        "SA": "Stokes Annex",
        "T":  "Terence Larkin Theatre",
        "U":  "Accommodation & Sports Club",
        "V1": "Larkfield Residences",
        "V2": "Hampstead Residences",
        "VA": "Postgraduate Residences A",
        "VB": "Postgraduate Residences B",
        "W":  "College Park Residences",
        "X":  "Lonsdale Building",
        "Y":  "O'Reilly Library",
        "Z":  "The Helix"
    },
    "SPC": {
        "A": "Block A",
        "B": "Block B",
        "C": "Block C",
        "D": "Block D",
        "E": "Block E",
        "F": "Block F",
        "G": "Block G",
        "S": "Block S / Sports Hall"
    },
    "AHC": {
        "C":  "Chapel",
        "OD": "O'Donnell House",
        "P":  "Purcell House",
        "S":  "Senior House"
    }
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
# Campus Codes
CAMPUSES = {
    "AHC": "All Hallows",
    "GLA": "Glasnevin",
    "SPC": "St Patrick's"
}
MODULE_REGEX = re.compile(r"^(?:[A-Z]{2}\d+[A-Za-z]{0,2}(?:[\[\(]\d[\]\)])?/?){1,2}")


def get_module_name(name: str) -> tuple[str, str, int | None]:
    """ Return module code, name, and semester """
    match = re.match(MODULE_REGEX, name)
    if match:
        code = match.group(0)
        module = name[len(code):].lstrip()
    else:
        # code = module = name
        try:
            code, module = name.split(" ", 1)
            # If the code is a word, e.g. "Basic" - Tries to reduce the number of incorrectly parsed modules and codes
            if re.match(r"^[A-Z][a-z]+", code):
                code = module = name
            # Similarly, try to reduce the number of incorrectly parsed modules by detecting certain keywords
            elif "Talk" in name or "Orientation" in name or "workshop" in name.lower() or "Meeting" in name:
                code = module = name
            elif name == "BREAK ROOM":
                code = module = name
        except ValueError:
            # Try to avoid having "error" as a name
            code = module = name
    try:
        semester = code[-2]  # 0, 1, or 2
        semester = int(semester)
    except (ValueError, IndexError):
        semester = None
    return code, module, semester


def get_times_course(course_code: str = "COMSCI1", custom_week: time.datetime = None) -> tuple[time.datetime, time.datetime]:
    """ Returns the start and end times for the current week in a given course """
    now = custom_week or time.datetime.now(tz=TZ)
    if course_code.endswith("1"):  # First-year courses start on 25 September
        first_week = time.datetime(2023, 9, 25, tz=TZ)
        if now < first_week:
            return get_times(time.datetime(2023, 9, 25, tz=TZ))
    return get_times(now)


def get_times(custom_week: time.datetime = None) -> tuple[time.datetime, time.datetime]:
    """ Returns the start and end times for the current week """
    now = custom_week or time.datetime.now(tz=TZ)
    first_week = time.datetime(2023, 9, 11, tz=TZ)
    if now < first_week:
        start = first_week
    else:
        start: time.datetime = (now - time.timedelta(days=now.weekday)).replace(hour=0, minute=0, second=0, microsecond=0)
    end: time.datetime = start + time.timedelta(weeks=1) - time.timedelta(seconds=1)  # type: ignore
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


async def get_list_from_api(total_pages: int, count: int, identity: str, name: str) -> dict:
    """ Common function to get the list of courses, modules, or rooms currently available """
    output = {"TotalPages": total_pages, "CurrentPage": 1, "Results": [], "Count": count}
    i = 0
    while i < total_pages:
        i += 1
        data = await get_data(
            f"{BASE_URL}/CategoryTypes/{identity}/Categories/FilterWithCache/{INSTITUTION_IDENTITY}?pageNumber={i}&query=",
            headers={
                "Authorization": "Anonymous",
                "Content-type": "application/json"
            },
            name=name
        )
        if data["TotalPages"] != total_pages:
            print_error(f"There are {data['TotalPages']} pages of data, expected {total_pages}. Update the hardcoded limit.")
            output["TotalPages"] = data["TotalPages"]
        output["CurrentPage"] = data["CurrentPage"]
        output["Count"] = data["Count"]
        output["Results"] += data["Results"]  # This should make it so that the returned results are the complete list of courses
    if output["CurrentPage"] != output["TotalPages"]:
        raise ValueError(f"Current page does not equal total pages: {output['CurrentPages']} != {output['TotalPages']}")
    logger.log("Suager", "dcu", f"{now_time()} > Suager > {name} > Downloaded new data from API")
    return output


async def get_list_from_cache(filename: str, renew_function: Callable[[], Awaitable[dict]]) -> dict:
    """ Common function to get the list of courses, modules, or rooms currently available from the cache """
    data = None
    must_renew = False
    timestamp = time.datetime.now().timestamp
    try:
        with open("data/dcu/" + filename, "r") as file:
            data = json.loads(file.read())
            # If the data is more than a month old - The list of courses, modules, and rooms should not change often
            if timestamp - data["timestamp"] > 86400 * 30:
                must_renew = True
                logger.log("Suager", "dcu", f"{now_time()} > Suager > DCU Cache Fetcher > Data from {filename} has expired")
    except FileNotFoundError:
        must_renew = True
        logger.log("Suager", "dcu", f"{now_time()} > Suager > DCU Cache Fetcher > File {filename} does not exist")
    if must_renew:
        data = await renew_function()
        data["timestamp"] = timestamp
        with open("data/dcu/" + filename, "w+") as file:
            file.write(json.dumps(data))
    return data


async def get_list_identities(cache_function: Callable[[], Awaitable[dict]], cls: Type[BaseID]) -> dict[str, BaseID]:
    """ Make a dict of course/module/room identities to be used by the timetables API """
    data = await cache_function()
    output = {}
    for entry in data["Results"]:
        result = cls(entry)
        # Don't overwrite the data if there is a duplicate
        if result.code not in output:
            output[result.code] = result
    return output


async def get_list(identities_function: Callable[[], Awaitable[dict[str, BaseID]]], search: str = None) -> list[str]:
    """ Get the list of available courses, modules, or rooms """
    data = await identities_function()
    output: list[str] = [str(result) for result in data.values()]
    if search is not None:
        output = [result for result in output if search.lower() in result.lower()]
    return output


async def get_courses_from_api() -> dict:
    """ Get the list of courses currently available """
    return await get_list_from_api(28, 554, PROGRAMMES_OF_STUDY, "DCU Course List Fetcher")


async def get_courses_from_cache() -> dict:
    """ Get the list of courses from cache. If it is too old, download the course list from the API again """
    return await get_list_from_cache("courses.json", get_courses_from_api)


async def get_course_identities() -> dict[str, Course]:
    """ Make a dict of course identities to be used by the timetables API """
    return await get_list_identities(get_courses_from_cache, Course)


async def get_courses(search: str = None) -> list[str]:
    """ Get the list of course names """
    return await get_list(get_course_identities, search)


async def get_modules_from_api() -> dict:
    """ Get the list of modules currently available """
    return await get_list_from_api(92, 4552, MODULES_CATEGORY, "DCU Module List Fetcher")


async def get_modules_from_cache() -> dict:
    """ Get the list of modules from cache. If it is too old, download the module list from the API again """
    return await get_list_from_cache("modules.json", get_modules_from_api)


async def get_module_identities() -> dict[str, Module]:
    """ Make a dict of module identities to be used by the timetables API """
    return await get_list_identities(get_modules_from_cache, Module)


async def get_modules(search: str = None) -> list[str]:
    """ Get the list of module names """
    return await get_list(get_module_identities, search)


async def get_rooms_from_api() -> dict:
    """ Get the list of rooms currently available """
    return await get_list_from_api(2, 349, LOCATIONS_CATEGORY, "DCU Room List Fetcher")


async def get_rooms_from_cache() -> dict:
    """ Get the list of rooms from cache. If it is too old, download the room list from the API again """
    return await get_list_from_cache("rooms.json", get_rooms_from_api)


async def get_room_identities() -> dict[str, Room]:
    """ Make a dict of room identities to be used by the timetables API """
    return await get_list_identities(get_rooms_from_cache, Room)


async def get_rooms(search: str = None) -> list[str]:
    """ Get the list of room names """
    return await get_list(get_room_identities, search)


async def get_timetable_data(type_identity: str, category_identities: list[str], start: time.datetime, end: time.datetime):
    """ Get the timetable for specified identities (a course, a room, or a list of modules) for a given week """
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
                    "CategoryTypeIdentity": type_identity,
                    "CategoryIdentities": category_identities,
                }
            ],
        },
        name="DCU Timetable Fetcher"
    )


async def get_timetable_data_course(course: Course, custom_week: time.datetime):
    """ Get the timetable for the specified course for the current week """
    start, end = get_times_course(course.code, custom_week)
    return await get_timetable_data(PROGRAMMES_OF_STUDY, [course.identity], start, end)


async def get_timetable_data_module(modules: list[Module], custom_week: time.datetime):
    """ Get the timetable for the specified modules for the current week """
    start, end = get_times(custom_week)
    return await get_timetable_data(MODULES_CATEGORY, [module.identity for module in modules], start, end)


async def get_timetable_data_room(room: Room, custom_week: time.datetime):
    """ Get the timetable for the specified room for the current week """
    start, end = get_times(custom_week)
    return await get_timetable_data(LOCATIONS_CATEGORY, [room.identity], start, end)


def get_timetable(data: dict, description: str, start: time.datetime, end: time.datetime) -> discord.Embed:
    """ Return a human-readable embed with the current week's timetable """
    embed = discord.Embed(title="DCU Timetables", description=f"{description}\nTimetables for the week: **{start:%d %B} to {end:%d %B %Y}**", colour=general.random_colour())
    # events_str = data["CategoryEvents"][0]["Results"]
    event_list = []
    for event_category in data["CategoryEvents"]:
        event_list += event_category["Results"]
    events = [Event(event) for event in event_list]
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


async def get_timetable_course(course_code: str = "COMSCI1", custom_week: time.datetime = None) -> discord.Embed:
    """ Get the timetables data and return a human-readable embed with the current week's timetable """
    start, end = get_times_course(course_code, custom_week)

    courses = await get_course_identities()
    try:
        course = courses[course_code.upper()]
    except KeyError:
        raise KeyError(f"Course not found: `{course_code}`")
    data = await get_timetable_data_course(course, custom_week)
    course_name = course.name
    if course.code[-1].isdigit():
        course_name += f" - Year {course.code[-1]}"
    return get_timetable(data, f"Timetable for course: **{course_name} ({course.code})**", start, end)


async def get_timetable_module(module_codes: list[str] | tuple[str, ...], custom_week: time.datetime = None) -> discord.Embed:
    """ Get the timetables data for a list of modules """
    start, end = get_times(custom_week)

    modules = await get_module_identities()
    module_cls = []
    for module in module_codes:
        try:
            module_cls.append(modules[module])
        except KeyError:
            raise KeyError(f"Module not found: `{module}`")
    data = await get_timetable_data_module(module_cls, custom_week)
    module_names = [module.code for module in module_cls]
    return get_timetable(data, f"Timetable for modules: **{', '.join(module_names)}** (Total: {len(module_names)})", start, end)


async def get_timetable_room(room_code: str, custom_week: time.datetime = None) -> discord.Embed:
    """ Get the timetables data for a specific room """
    start, end = get_times(custom_week)

    rooms = await get_room_identities()
    try:
        room = rooms[room_code.upper()]
    except KeyError:
        raise KeyError(f"Room not found: `{room_code}`")
    data = await get_timetable_data_room(room, custom_week)
    return get_timetable(data, f"Timetable for room: **{room.code}** ({room.location})", start, end)


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
        try:
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
        except IndexError:
            # If it doesn't conform to the regular class names (something other than, say, "CA116[1]OC/L1/01")
            description = data["Description"]
        self.description = description

        self.last_modified = self.iso_to_datetime(data["LastModified"])
        # self.data = data  # So that I can access the data that the event class ignores

    @staticmethod
    def iso_to_datetime(data: str) -> time.datetime:
        """ Convert ISO timestamp to datetime in Europe/Dublin timezone """
        date_str, time_str = data.split("T")
        event_date = time.date.from_iso(date_str)
        event_time = time.time.from_iso(time_str)
        return time.datetime.combine(event_date, event_time).to_timezone(TZ)

    @staticmethod
    def get_module_name(data: str) -> str:
        code, name, semester = get_module_name(data)
        if re.search(r"[\[\(]\d[\]\)]$", code):
            code = code[:-3]  # Remove the semester information - [0], [1], [2]
        try:
            name = MODULES[code]
        except KeyError:
            pass  # Leave the module name as-is
        return f"**[{code}]** {name}"

    def building_and_room(self) -> str:
        """ Convert the location code into human-readable format """
        rooms = self.location.split(", ")
        if rooms[0][:3] == "GLA":
            building_code = rooms[0][4:-3]  # Assume the building is the same for all labs
            rooms_list = ", ".join([room[4:] for room in rooms])  # Include building code, e.g. HG20, since most signs have that room code included
            return f"{BUILDINGS_SHORT[building_code]} {rooms_list}"
        else:
            rooms_list = ", ".join([room[4:] for room in rooms])
            return f"{CAMPUSES[rooms[0][:3]]} {rooms_list}"

    def coordinates(self) -> tuple[str, str]:
        """ Convert the location code into map coordinates + room name """
        rooms = self.location.split(", ")
        assert rooms[0][:3] == "GLA"  # This should never encounter SPC/AHC rooms, since it's only used by my calendar
        building_code = rooms[0][4:-3]
        location = {
            "C":  "53.38625149, -6.25983371",
            "CA": "53.38598334, -6.25914272",
            "H":  "53.38583436, -6.25490563",
            "L":  "53.38563562, -6.25742329",
            "N":  "53.38505261, -6.25585218",
            "Q":  "53.38620605, -6.25744379",
            "S":  "53.38556896, -6.25609541",
            "SA": "53.38587691, -6.25643261",
            "T":  "53.38618517, -6.25816241",
            "X":  "53.38497192, -6.25494111"
        }.get(building_code)
        rooms_list = ", ".join([room[4:] for room in rooms])
        return location, rooms_list

    def __str__(self) -> str:
        return f"**{self.start:%H:%M} - {self.end:%H:%M}** - {self.description} - {self.module_name} - {self.building_and_room()}"


class BaseIdentity(object):
    def __init__(self, data: dict):
        self.code: str = data["Name"]          # Code
        self.name: str = data["Description"]   # Human-readable name / Room description
        self.identity: str = data["Identity"]  # UUID

    def __str__(self) -> str:
        return f"**{self.code}** - {self.name}"


class Course(BaseIdentity):
    def __str__(self) -> str:
        # "COMSCI1 - BSc in Computer Science"
        return f"**{self.code}** - {self.name}"


class Module(BaseIdentity):
    def __init__(self, data: dict):
        super().__init__(data)
        name: str = data["Name"]  # "AB101[0] Social Media, Wellbeing and Society"
        self.code, self.name, self.semester = get_module_name(name)
        self.identity: str = data["Identity"]

    def __str__(self) -> str:
        # "CA116 - Computer Programming 1 (Sem. 1)"
        if self.semester is None:
            semester = ""
        elif self.semester == 0:
            semester = " (All Year)"
        else:
            semester = f" (Sem. {self.semester})"
        return f"**{self.code}** - {self.name}{semester}"


class Room(BaseIdentity):
    def __init__(self, data: dict):
        super().__init__(data)
        self.code = self.name = data["Name"]    # "GLA.HG06"
        self.description = data["Description"]  # not always useful, e.g. "Flat Classroom"
        campus, room_code = self.code.split(".")
        self.campus = CAMPUSES[campus]
        if re.search(r"[A-Z]{1,2}[BG1-9]\d+", room_code):
            letter = room_code[0]
            index = 1
            if room_code[1] == "A" or room_code[:2] == "VB" or room_code[:2] == "OD":
                letter = room_code[:2]
                index = 2
            self.building = BUILDINGS[campus].get(letter, "Unknown Building")
            floor = room_code[index]
            self.floor = {
                "B": "Basement",
                "G": "Ground Floor",
                "1": "First Floor",
                "2": "Second Floor",
                "3": "Third Floor",
                "4": "Fourth Floor"
            }.get(floor, "Unknown Floor")
            self.room_code = room_code         # e.g. HG20
            self.room = room_code[index + 1:]  # Only the room number
            self.location = f"{self.campus} {self.building} - {self.floor} - Room {self.room}"
        else:
            self.building = self.room_code = room_code
            self.floor = None
            self.room = None
            self.location = f"{self.campus} {self.building}"

    def __str__(self):
        # "GLA.HG06 - Glasnevin Nursing Building - Flat Classroom"
        # "GLA.HG20 - Glasnevin Nursing Building - Tiered Lecture Theatre-Mella Carroll Theatre"
        return f"**{self.code}** - {self.location} - {self.description}"


BaseID = TypeVar("BaseID", bound=BaseIdentity)


async def generate_ical() -> bytes:
    """ Generate the icalendar files for COMSCI1 for the current academic year """
    now = time.datetime.now()
    start = time.datetime(2023, 9, 25)
    end = time.datetime(2024, 5, 4) - time.timedelta(seconds=1)
    time_format = "%Y%m%dT%H%M%SZ"  # "20230924T165500Z"

    data = await get_timetable_data(PROGRAMMES_OF_STUDY, [COMSCI1], start, end)

    event_list = []
    for event_category in data["CategoryEvents"]:
        event_list += event_category["Results"]
    events = [Event(event) for event in event_list]
    events.sort(key=lambda x: x.start)  # Sort by starting time

    calendar = Calendar()
    calendar.add("METHOD", "PUBLISH")
    calendar.add("PRODID", "-//Regaus//DCU Timetables Reader//EN")
    calendar.add("VERSION", "2.0")  # Seems to represent the version of the format
    for i, item in enumerate(events, start=1):  # type: int, Event
        location, room = item.coordinates()
        event = CalendarEvent()
        event.add("UID", i)
        event["DTSTAMP"] = now.strftime(time_format)
        event["LAST-MODIFIED"] = item.last_modified.to_timezone(time.utc).strftime(time_format)
        event["DTSTART"] = item.start.to_timezone(time.utc).strftime(time_format)
        event["DTEND"] = item.end.to_timezone(time.utc).strftime(time_format)
        # event.add("DTSTAMP", now.strftime(time_format))
        # event.add("LAST-MODIFIED", item.last_modified.strftime(time_format))
        # event.add("DTSTART", item.start.strftime(time_format))
        # event.add("DTEND", item.end.strftime(time_format))
        event.add("SUMMARY", f"({room}) {item.description} - {item.module_name.replace('*', '')}")  # "(HG20) Lecture - [CA116] Computer Programming"
        event.add("LOCATION", location)
        event.add("DESCRIPTION", f"{item.description} - {item.building_and_room()}")
        event.add("CLASS", "PUBLIC")
        calendar.add_component(event)

    with open("data/dcu/calendar.ics", "wb+") as file:
        output = calendar.to_ical()
        file.write(output)
        return output
