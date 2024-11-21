import asyncio
import importlib
import json
import os
from collections.abc import Callable, Awaitable
from contextlib import suppress
from io import BytesIO
from typing import Any, Protocol
from zipfile import ZipFile, BadZipFile

import aiohttp
import discord
import luas.api
from aiohttp import ClientError
from bs4 import BeautifulSoup
from discord import app_commands
from regaus import time
from thefuzz import process

from utils import bot_data, commands, http, timetables, logger, emotes, dcu, paginators, general, arg_parser, cpu_burner
from utils.time import time as print_current_time

# def dcu_data_access(ctx):
#     return ctx.guild is None or ctx.guild.id == 738425418637639775 or ctx.author.id == 302851022790066185
#     # return ctx.bot.name == "timetables" or ctx.author.id in [302851022790066185]


STOP_HUBS: dict[str, list[str]] = {
    "Abbey St Lower":     ["8220DB007591", "8220DB000289", "8220DB000288", "8220DB000292"],
    "Abbey St Luas":      ["8220GA00409",  "8220GA00408",  "8220GA00444",  "8220GA00034",  "8220000150",   "8220DB000271"],
    "Aston Quay":         ["8220DB000325", "8220DB004720", "8220DB007392", "8220DB000328", "8220DB000329"],
    "Bachelors Walk":     ["8220B1021101", "8220DB000316", "8220DB000315", "8220DB007622"],
    "Bray Station":       ["8350IR0123",   "8350DB004167", "8350DB004168", "8350DB004169"],
    "Broombridge":        ["8220IR0026",   "8220GA00459",  "8220DB007672", "8220GD8340",   "8220GD8341"],
    "Busaras":            ["8220B135001",  "8220DB000496", "8220B134961",  "8220GA00421",  "8220GA00420"],
    "Clontarf":           ["8220IR0032",   "8220DB004794", "8220DB007863", "8220DB001738", "8220DB001740"],
    "College Green East": ["8220DB001358", "8220DB007582", "8220DB001359"],
    "College Green West": ["8220DB004521", "8220DB004522", "8220DB001278", "8220DB001279", "8220DB007581"],
    "Connolly":           ["8220IR0007",   "8220GA00423",  "8220DB001500", "8220B1351201", "8220DB000497"],
    "D'Olier":            ["8220DB000273", "8220DB000333", "8220DB000334", "8220DB000335", "8220DB000336", "8220GA00035"],
    "Dawson":             ["8220DB000791", "8220DB000790", "8220DB000792", "8220DB000793", "8220GA00031",  "8220GA00441"],
    "DCU":                ["8220DB007571", "8220DB004680", "8220DB000037", "8220DB001644", "8220DB001646", "8220DB000205", "8220DB000213", "8220DB008307", "8220DB008246"],
    "Drumcondra":         ["8220IR0027",   "8220DB000017", "8220DB000047"],
    "Dundrum":            ["8250GA00286",  "8250GA00287",  "8250DB002825", "8250DB006041", "8250DB002866", "8250DB007981", "8250GD10160",  "8250DB007719"],
    "Eden Quay East":     ["8220B1353501", "8220DB007359", "8220DB000297", "8220DB000298", "8220DB000299", "8220DB000300"],
    "Eden Quay West":     ["8220DB000303", "8220DB000302", "8220DB000301"],
    "Heuston Station":    ["8220IR0132",   "8220GA00387",  "8220GA00386",  "8220DB004319",  "8220DB004320", "8220DB004425"],
    "Heuston North":      ["8220DB007078", "8220DB001474", "8220CO10996"],
    "Heuston South":      ["8220DB004413", "8220DB002637", "8220B10995",   "8220B1354001"],
    "Killester":          ["8220IR3881",   "8220DB004390", "8220DB004791", "8220DB000530", "8220DB000608"],
    "Nassau":             ["8220DB000403", "8220DB000404", "8220DB000406", "8220DB000405", "8220DB007585", "8220DB007586"],
    "Red Cow":            ["8230GA00354",  "8230GA00353",  "8230DB007791", "8230DB007887", "8230DB007886", "8230DB004379"],
    "Red Cow Coaches":    ["8230CO11059",  "8230CO11058",  "8230CO11056",  "8230CO11057"],
    "Regaus Northbound":  ["8220IR0134",   "8220DB000495", "8220DB000319", "8220DB000320", "8220DB000288", "8220DB000292", "8220IR0032",   "8220DB001738"],
    "Pearse Station":     ["8220IR0134",   "8220DB000399", "8220DB000495", "8220B100111",  "8220DB002809", "8220B111761"],
    "Pearse Street":      ["8220DB000342", "8220DB000346", "8220DB000345", "8220DB007588", "8220DB000400", "8220DB007859", "8220DB007587"],
    "Tara":               ["8220IR0025",   "8220DB001502", "8220DB007732", "8220DB007564"],
    "Townsend":           ["8220DB000340", "8220DB000341", "8220DB005192", "8220DB004495"],
    "UCD":                ["8250DB000768", "8250DB002007", "8250B1350601", "8250DB000767", "8250DB000765", "8250DB004953", "8250DB004952"],
    "Westmoreland":       ["8220GA00443",  "8220DB000319", "8220DB000320"],
}


class GTFSSearchFunction(Protocol):
    def __call__(self, query: str) -> list:
        ...


# Cog for university timetables - loaded by Suager
class University(commands.Cog, name="Timetables"):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        self.cache_sync = {
            "courses": dcu.get_course_identities,
            "modules": dcu.get_module_identities,
            "rooms": dcu.get_room_identities
        }

    @commands.hybrid_group(name="dcu", case_insensitive=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    # @commands.check(dcu_data_access)
    # @app_commands.guilds(738425418637639775)
    async def dcu_stuff(self, ctx: commands.Context):
        """ Access stuff related to DCU and its timetables """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    async def dcu_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """ Autocomplete for course/module/room searches """
        cache_type = interaction.command.name.split()[-1]
        if not cache_type.endswith("s"):
            cache_type += "s"
        cache = dcu.cache[cache_type]
        # If the cache is empty, call the function to load all courses/modules/rooms from cache
        if len(cache) == 0:
            await self.cache_sync[cache_type]()
            cache = dcu.cache[cache_type]
        # results: [(code, full_name, similarity), ...]
        results: list[tuple[str, str, int]] = []
        for code, full_name in cache.items():
            ratios = [process.default_scorer(current, code), process.default_scorer(current, full_name)]
            results.append((code, full_name, max(ratios)))
        results.sort(key=lambda x: x[2], reverse=True)
        # print(results)
        return [app_commands.Choice(name=result[1], value=result[0]) for result in results][:25]

    # TODO: Try to implement an autocomplete for module codes
    # async def module_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    #     """ Autocomplete function for module searches, as these are different """
    #     pass

    @dcu_stuff.group(name="timetable", aliases=["timetables", "tt"], case_insensitive=True, invoke_without_command=True, fallback="course")
    @app_commands.autocomplete(course_code=dcu_autocomplete)
    @app_commands.describe(
        course_code="The code for the course whose timetable you want to see.",  # Defaults to the COMSCI course for my current year (first year in 2023/2024).
        custom_week="The week for which you want to see the timetable. Defaults to current week."  # (or next week if it's Saturday or Sunday)
    )
    async def dcu_timetable(self, ctx: commands.Context, course_code: str = "", custom_week: str = ""):
        """ Fetch DCU timetables for a given course for the current week

        If no course code provided, defaults to COMSCI course for my current year (first year in 2023/2024) """
        if ctx.invoked_subcommand is None:
            await ctx.defer()
            if not course_code:
                course_code = "COMSCI"
                # Push August 2023 to be "January 2024", so that we can start defaulting to COMSCI 2 in Aug 2024
                # Aug 2023 - Jul 2024 -> 1, Aug 2024 - Jul 2025 -> 2, etc.
                year = (time.date.today() + time.relativedelta(months=5, time_class=time.Earth)).year - 2023
                if year > 4:
                    # After I graduate, fall back to COMSCI1
                    year = 1
                course_code += str(year)
            try:
                date = None
                if custom_week:
                    date = time.date.from_iso(custom_week)
                    date = time.datetime.combine(date, time.time(), dcu.TZ)
                return await ctx.send(embed=await dcu.get_timetable_course(course_code, date))
            except KeyError as e:
                # await ctx.send(general.traceback_maker(e))
                return await ctx.send(f"{emotes.Deny} An error occurred: {type(e).__name__}: {str(e)}\nUse `{ctx.prefix}dcu search courses` to find your course code.")
            except Exception as e:
                # await ctx.send(general.traceback_maker(e))
                return await ctx.send(f"{emotes.Deny} An error occurred: {type(e).__name__}: {str(e)}")

    @dcu_timetable.command(name="regaus", aliases=["my_timetable", "mine", "custom"])
    @commands.is_owner()
    @app_commands.describe(custom_week="The week for which you want to see the timetable. Defaults to current week.")
    # @app_commands.guilds(738425418637639775)
    async def dcu_timetable_regaus(self, ctx: commands.Context, custom_week: str = ""):
        """ Fetch DCU timetables for my course but include the first year labs I'm involved in """
        await ctx.defer()
        date = time.datetime.now()
        if custom_week:
            date = time.date.from_iso(custom_week)
            date = time.datetime.combine(date, time.time(), dcu.TZ)

        if time.datetime(2024, 8) <= date < time.datetime(2025, 8):
            course_code = "COMSCI2"
            extra_labs = ("CSC1003[1]", "CSC1004[2]")
            description = "Regaus's Timetable: **COMSCI2** + Programming Labs"
        else:
            return await ctx.send("Error: The timetable for this academic year is not defined.")
            # raise RuntimeError("The timetable for this academic year is not defined.")

        course = (await dcu.get_course_identities())[course_code]
        modules_all = await dcu.get_module_identities()
        modules = []
        for module in extra_labs:
            modules.append(modules_all[module])
        data = await dcu.get_timetable_data_regaus(course, modules, date)
        start, end = dcu.get_times(date)
        return await ctx.send(embed=dcu.get_timetable_regaus(data, modules, description, start, end))

    @dcu_timetable.command(name="modules", aliases=["module", "m"])
    # @app_commands.autocomplete(module_codes=dcu_autocomplete)
    @app_commands.describe(
        module_codes="List of all modules whose timetables you want to see, separated by space. No autocomplete yet.",  # Make sure to include semester number, e.g. CA116[1] or CA170[2].
        custom_week="The week for which you want to see the timetable. Defaults to current week."
        # (or next week if it's Saturday or Sunday). May also be provided as the last argument in `module_codes`
    )
    async def dcu_timetable_modules(self, ctx: commands.Context, *, module_codes: str, custom_week: str = ""):
        """ Fetch DCU timetables for specified modules for the current week"""
        try:
            await ctx.defer()
            module_codes = module_codes.split()
            date = None
            if custom_week:
                date = time.date.from_iso(custom_week)
                date = time.datetime.combine(date, time.time(), dcu.TZ)
            else:
                try:
                    date = time.date.from_iso(module_codes[-1])
                    date = time.datetime.combine(date, time.time(), dcu.TZ)
                    module_codes = module_codes[:-1]
                except ValueError:
                    pass
            return await ctx.send(embed=await dcu.get_timetable_module(module_codes, date))
        except KeyError as e:
            return await ctx.send(f"{emotes.Deny} An error occurred: {str(e)}\nUse `{ctx.prefix}dcu search modules` to find your module code(s).")
        except Exception as e:
            # await ctx.send(general.traceback_maker(e))
            return await ctx.send(f"{emotes.Deny} An error occurred: {type(e).__name__}: {str(e)}")

    @dcu_timetable.command(name="room", aliases=["rooms", "r"])
    @app_commands.autocomplete(room_code=dcu_autocomplete)
    @app_commands.describe(
        room_code="The code for the room whose timetable you want to see.",
        custom_week="The week for which you want to see the timetable. Defaults to current week."  # (or next week if it's Saturday or Sunday)
    )
    async def dcu_timetable_room(self, ctx: commands.Context, room_code: str, custom_week: str = ""):
        """ Fetch DCU timetables for a given room for the current week"""
        try:
            await ctx.defer()
            date = None
            if custom_week:
                date = time.date.from_iso(custom_week)
                date = time.datetime.combine(date, time.time(), dcu.TZ)
            return await ctx.send(embed=await dcu.get_timetable_room(room_code, date))
        except KeyError as e:
            return await ctx.send(f"{emotes.Deny} An error occurred: {str(e)}\nUse `{ctx.prefix}dcu search rooms` to find your room code.")
        except Exception as e:
            # await ctx.send(general.traceback_maker(e))
            return await ctx.send(f"{emotes.Deny} An error occurred: {type(e).__name__}: {str(e)}")

    @dcu_stuff.group(name="search", aliases=["list"], case_insensitive=True)
    async def dcu_search(self, ctx: commands.Context):
        """ Find a course, module or room """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    async def dcu_list(self, ctx: commands.Context, get_function: Callable[[str | None], Awaitable[list[str]]], title: str, search: str, *, notes: str = None):
        data = await get_function(search)
        if not data:
            return await ctx.send("No data has been found. Try a different search?")
        # paginator = commands.Paginator(prefix="", suffix="", max_size=1000)
        paginator = paginators.LinePaginator(prefix=None, suffix=None, max_lines=15, max_size=1000)
        for line in data:
            paginator.add_line(line)
        embed = discord.Embed(title=title, colour=general.random_colour())
        if notes is not None:
            embed.set_footer(text=notes)
        interface = paginators.PaginatorEmbedInterface(self.bot, paginator, owner=ctx.author, embed=embed)
        return await interface.send_to(ctx)

    @dcu_search.command(name="courses", aliases=["course", "courselist"])
    @app_commands.describe(search="The code of the course you're looking for")
    async def dcu_courses(self, ctx: commands.Context, search: str = None):
        """ Fetch DCU course list or look for a specific course """
        async with ctx.typing():
            return await self.dcu_list(ctx, dcu.get_courses, "DCU Course Codes", search)

    @dcu_search.command(name="modules", aliases=["module", "modulelist"])
    @app_commands.describe(search="The code of the module you're looking for")
    async def dcu_modules(self, ctx: commands.Context, search: str = None):
        """ Fetch DCU module list or look for a specific module """
        async with ctx.typing():
            return await self.dcu_list(ctx, dcu.get_modules, "DCU Module Codes", search,
                                       notes="Note: Some of the modules may have been parsed incorrectly, however I tried to reduce the chance of this happening")

    @dcu_search.command(name="rooms", aliases=["room", "roomlist", "locations", "location", "locationlist"])
    @app_commands.describe(search="The code of the room you're looking for")
    async def dcu_rooms(self, ctx: commands.Context, search: str = None):
        """ Fetch DCU room list or look for a specific room """
        async with ctx.typing():
            return await self.dcu_list(ctx, dcu.get_rooms, "DCU Room Codes", search)

    @dcu_stuff.command(name="invalidatecache", with_app_command=False)
    @commands.is_owner()
    async def dcu_invalidate_cache(self, ctx: commands.Context, cache: str = "all"):
        """ Invalidate the cache for courses, modules, and rooms """
        courses = modules = rooms = False
        cache = cache.lower()
        if cache == "all":
            courses = modules = rooms = True
        elif cache == "courses":
            courses = True
        elif cache == "modules":
            modules = True
        elif cache == "rooms":
            rooms = True
        else:
            return await ctx.send(f"Invalid cache value {cache!r} received.")
        if courses:
            with suppress(FileNotFoundError):
                os.remove("data/dcu/courses.json")
            dcu.cache["courses"] = {}
        if modules:
            with suppress(FileNotFoundError):
                os.remove("data/dcu/modules.json")
            dcu.cache["modules"] = {}
        if rooms:
            with suppress(FileNotFoundError):
                os.remove("data/dcu/rooms.json")
            dcu.cache["rooms"] = {}
        return await ctx.send(f"Successfully removed {cache} cache.")


# Cog for Luas timetables - loaded by Cobble
class Luas(commands.Cog, name="Timetables"):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.hybrid_command(name="luas")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(place="The Luas stop whose data should be loaded")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def luas(self, ctx: commands.Context, *, place: commands.clean_content):
        """ Fetch real-time data for a Luas stop """
        client = luas.api.LuasClient()
        _place = str(place).title() if len(str(place)) != 3 else str(place)
        data = client.stop_details(_place)
        status = data['status']
        trams = ''
        for i in data['trams']:
            if i['due'] == 'DUE':
                _time = 'DUE'
            else:
                _time = f"{i['due']} mins"
            trams += f"{i['destination']}: {_time}\n"
        return await ctx.send(f"Data for {_place}:\n{status}\n{trams}")


# Cog for GTFS timetables - loaded by Linenvürteat
class Timetables(University, Luas, name="Timetables"):
    def __init__(self, bot: bot_data.Bot):
        super().__init__(bot)
        # self.db = timetables.db
        self.db = timetables.get_database()
        self.DEBUG = False  # Debug Mode: Disables sending API requests for GTFS-R and disables pickling the static data
        self.WRITE = True   # Write real-time data to disk
        self.url = "https://api.nationaltransport.ie/gtfsr/v2/TripUpdates?format=json"
        self.vehicle_url = "https://api.nationaltransport.ie/gtfsr/v2/Vehicles?format=json"
        self.train_locations_url = "https://api.irishrail.ie/realtime/realtime.asmx/getCurrentTrainsXML"
        self.gtfs_data_url = "https://www.transportforireland.ie/transitData/Data/GTFS_All.zip"
        self.fleet_list_urls: tuple[tuple[str, str], ...] = (  # (agency, link)
            ("Dublin Bus",       "https://bustimes.org/operators/dublin-bus/vehicles"),
            ("Bus Éireann",      "https://bustimes.org/operators/bus-eireann/vehicles"),
            ("Go-Ahead Ireland", "https://bustimes.org/operators/go-ahead-ireland/vehicles")
        )
        self.headers = {
            "Cache-Control": "no-cache",
            "x-api-key": self.bot.config["gtfsr_api_token"]
        }
        self.real_time_data: timetables.GTFSRData = timetables.GTFSRData.empty()
        self.vehicle_data: timetables.VehicleData = timetables.VehicleData.empty()
        self.static_data: timetables.GTFSData | None = None
        self.fleet_data: dict[str, timetables.FleetVehicle] = {}  # fleet_data[vehicle_id] = FleetVehicle
        self.train_data: dict[str, timetables.Train] = {}         # train_data[trip_code] = Train
        self.initialised = False
        self.updating = False
        self.updating_real_time = False
        self.loader_error: Exception | None = None
        self.soft_loader_error: Exception | None = None
        self.last_updated: time.datetime | None = None
        self.soft_limit_warning: bool = False
        self.updating_vehicles: bool = False

    @staticmethod
    def get_stop_query_and_timestamp(query: str) -> tuple[str, str | None, bool, bool]:
        """ Split the stop query and timestamp using argparse """
        parser = arg_parser.Arguments()
        parser.add_argument("--time", nargs="+")
        parser.add_argument("--show-terminating", default=False, action="store_true")
        parser.add_argument("--hide-terminating", dest="show-terminating", action="store_false")
        parser.add_argument("query", nargs="+")
        args, valid_check = parser.parse_args(query)
        if not valid_check:
            return args, None, False, False
        query = " ".join(args.query)
        if args.time is not None:
            timestamp = " ".join(args.time)
        else:
            timestamp = None
        return query, timestamp, args.show_terminating, True

    @staticmethod
    def get_route_query_and_timestamp(query: str) -> tuple[str, str | None, int, bool]:
        """ Split the route query and timestamp using argparse """
        parser = arg_parser.Arguments()
        parser.add_argument("--time", nargs="+")
        parser.add_argument("query", nargs="+")
        parser.add_argument("--outbound", "-o", default=True, action="store_true")
        parser.add_argument("--inbound", "-i", dest="outbound", action="store_false")
        args, valid_check = parser.parse_args(query)
        if not valid_check:
            return args, None, -1, False
        query = " ".join(args.query)
        if args.time is not None:
            timestamp = " ".join(args.time)
        else:
            timestamp = None
        # direction 0 = outbound, direction 1 = inbound
        return query, timestamp, int(not args.outbound), True

    @staticmethod
    def parse_timestamp(timestamp: str | None) -> tuple[time.datetime | None, bool]:
        """ Parse a timestamp """
        if timestamp is not None:
            data = timestamp.split(" ", 1)
            if len(data) == 1:
                date_str = data[0]
                time_str = ""
            elif len(data) == 2:
                date_str, time_str = data
            else:
                return None, False
            if not time_str:
                time_part = time.time()  # 0:00:00
            else:
                _h, _m, *_s = time_str.split(":")
                h, m, s = int(_h), int(_m), int(_s[0]) if _s else 0
                time_part = time.time(h, m, s, 0)
            _y, _m, _d = date_str.split("-")
            y, m, d = int(_y), int(_m), int(_d)
            date_part = time.date(y, m, d)
            return time.datetime.combine(date_part, time_part, timetables.TIMEZONE), True
        return None, True

    @staticmethod
    async def get_from_api(url: str, filename: str, headers: dict | None, *, write: bool = True, is_json: bool = True) -> bytes | None:
        """ Generic function to get data from the real-time API - for the real-time and vehicles """
        try:
            data: bytes = await http.get(url, headers=headers, res_method="read")
            if write:
                with open(filename, "wb+") as file:
                    file.write(data)
            return data
        except (aiohttp.ClientError, TimeoutError):
            if is_json:
                return timetables.empty_real_time_str
            return None

    async def get_data_from_api(self, *, write: bool = True) -> bytes:
        return await self.get_from_api(self.url, timetables.real_time_filename, self.headers, write=write, is_json=True)

    async def get_vehicles_from_api(self, *, write: bool = True) -> bytes:
        return await self.get_from_api(self.vehicle_url, timetables.vehicles_filename, self.headers, write=write, is_json=True)

    async def get_train_locations_from_api(self, *, write: bool = True) -> bytes:
        return await self.get_from_api(self.train_locations_url, timetables.trains_filename, None, write=write, is_json=False)

    async def load_real_time_data(self, debug: bool = False, *, write: bool = True) -> tuple[timetables.GTFSRData, timetables.VehicleData, dict[str, timetables.Train]]:
        while self.updating_real_time:
            await asyncio.sleep(1)
        try:
            self.updating_real_time = True
            # Only refresh the data once in 60 seconds
            if self.last_updated is not None and (time.datetime.now() - self.last_updated).total_seconds() < 60:
                return self.real_time_data, self.vehicle_data, self.train_data
            if self.last_updated is None:
                prev_real_time_data_d, prev_vehicle_data_d, prev_train_data_d = await self.get_real_time_data(debug=True, write=False)
                prev_real_time_data, prev_vehicle_data = timetables.load_gtfs_r_data(prev_real_time_data_d, prev_vehicle_data_d)
                ts1, ts2 = prev_real_time_data.header.timestamp.timestamp, prev_vehicle_data.header.timestamp.timestamp
                now = time.datetime.now().timestamp
                if (now - max(ts1, ts2)) < 75:  # Less than 75s passed since the data header's timestamp (vehicle data has a 60s cooldown, add 15s to be sure to not hit it)
                    self.real_time_data = prev_real_time_data
                    self.vehicle_data = prev_vehicle_data
                    self.train_data = prev_train_data_d
                    self.last_updated = time.datetime.from_timestamp(max(ts1, ts2))
                    logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Loaded GTFS-R data stored on disk (too recent to update)")
                    return self.real_time_data, self.vehicle_data, self.train_data
            data, vehicle_data, train_data = await self.get_real_time_data(debug=debug, write=write)
            try:
                new_real_time_data, new_vehicle_data = timetables.load_gtfs_r_data(data, vehicle_data)
                if new_real_time_data:
                    self.real_time_data = new_real_time_data
                if new_vehicle_data:
                    self.vehicle_data = new_vehicle_data
            except timetables.GTFSAPIError as e:
                error_place = e.error_place
                # Load new data for the valid part, and leave the other one as-is
                if error_place == "real-time":
                    self.vehicle_data = timetables.load_gtfs_r_data(None, vehicle_data)[1]
                elif error_place == "vehicles":
                    self.real_time_data = timetables.load_gtfs_r_data(data, None)[0]
                logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Real-Time API Error for {error_place}: {type(e).__name__}: {str(e)}")
            self.train_data = train_data
            logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Successfully loaded GTFS-R data")
            self.last_updated = time.datetime.now()
            return self.real_time_data, self.vehicle_data, self.train_data  # just in case
        finally:
            self.updating_real_time = False

    async def get_real_time_data(self, debug: bool = False, *, write: bool = True) -> tuple[dict, dict, dict[str, timetables.Train]]:
        """ Gets real-time data from the NTA's API or load from cache if in debug mode """
        if debug or (self.last_updated is not None and (time.datetime.now() - self.last_updated).total_seconds() < 60):  # type: ignore
            updated = False
            try:
                with open(timetables.real_time_filename, "rb") as file:
                    data: bytes = file.read()
            except FileNotFoundError:
                data: bytes = await self.get_data_from_api(write=write)
            try:
                with open(timetables.vehicles_filename, "rb") as file:
                    vehicles: bytes = file.read()
            except FileNotFoundError:
                vehicles: bytes = await self.get_vehicles_from_api(write=write)
            try:
                with open(timetables.trains_filename, "rb") as file:
                    trains: bytes = file.read()
            except FileNotFoundError:
                trains: bytes = await self.get_train_locations_from_api(write=write)
            if updated:
                self.last_updated = time.datetime.now()
        else:
            data: bytes = await self.get_data_from_api(write=write)
            vehicles: bytes = await self.get_vehicles_from_api(write=write)
            trains: bytes = await self.get_train_locations_from_api(write=write)
            self.last_updated = time.datetime.now()
        return json.loads(data), json.loads(vehicles), timetables.parse_train_data(trains)

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     await asyncio.sleep(60)  # To let the other bots load before we freeze the machine for half a minute

    async def load_data(self, *, force_redownload: bool = False, force_reload: bool = False, ignore_real_time: bool = False):
        """ Load the GTFS-R and static GTFS data only when needed """
        static_reload = False
        try:
            cpu_burner.arr[2] = False  # Disable the CPU burner function while loading the GTFS data
            self.loader_error = None  # Reset any previous error encountered
            self.updating = True
            if not ignore_real_time and not self.real_time_data:
                await self.load_real_time_data(debug=self.DEBUG, write=self.WRITE)
            if force_redownload or force_reload or self.static_data is None:
                try:
                    if force_redownload:
                        static_reload = True
                        logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Received force download call, re-downloading static GTFS data")
                        await self.download_new_static_gtfs()
                    else:
                        try:
                            if force_reload:
                                static_reload = True
                                await self.reload_static_gtfs()
                            self.static_data = timetables.init_gtfs_data()
                            logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Successfully loaded static GTFS data")
                        except RuntimeError as e:
                            static_reload = True
                            logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Error loading static GTFS data: {type(e).__name__}: {e}")
                            await self.download_new_static_gtfs()
                except (ClientError, BadZipFile) as e:
                    # If the GTFS data cannot be downloaded due to an error with the powers above, try to load from existing data while ignoring expiry errors
                    self.soft_loader_error = e
                    logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Can't download data, falling back to existing dataset.")
                    self.static_data = timetables.init_gtfs_data(ignore_expiry=True)
                    self.updating = False
                    # self.static_data = timetables.load_gtfs_data_from_pickle(write=not self._DEBUG, ignore_expiry=True)
                    # If we crash here yet again, then it would make sense to give up and catch on fire.
            self.initialised = True
        except Exception as e:
            self.loader_error = e
            self.initialised = False
            self.updating = False  # That should cause the waiting loop to exit, we are no longer updating data
            raise
        # This can only be called if we are not reloading GTFS data, as we can only be sure the data is finished updating after that function returns
        finally:
            cpu_burner.arr[2] = True
            if not static_reload:  # I'm not sure why it's written like this. Should it be?
                self.updating = False

    async def download_new_static_gtfs(self):
        """ Download new static GTFS data and extract them, overwriting the existing data, then refresh loaded data """
        # Make the existing data unavailable
        self.updating = True
        self.static_data = None
        # Uncomment this to fake an error
        # await asyncio.sleep(10)
        # raise RuntimeError("This is a test")
        # raise BadZipFile("This is a test")
        # Download the data
        data = await http.get(self.gtfs_data_url, res_method="read")
        # Extract the data
        zip_file = ZipFile(BytesIO(data))
        zip_file.extractall("assets/gtfs")
        await self.reload_static_gtfs(message="Downloaded new GTFS data and successfully loaded it")

    async def reload_static_gtfs(self, message: str = "Reloaded static GTFS data"):
        self.updating = True
        # await asyncio.get_event_loop().run_in_executor(None, functools.partial(timetables.read_and_store_gtfs_data, self))
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, timetables.read_and_store_gtfs_data)  # type: ignore
        self.static_data = timetables.init_gtfs_data()
        logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > {message}")
        self.updating = False

    async def wait_for_initialisation(self, ctx: commands.Context, *, force_redownload: bool = False, force_reload: bool = False, ignore_real_time: bool = False) -> discord.Message:
        """ Initialise the data before letting the actual command execute """
        # If self.updating is True, then the data is already being loaded
        # If force_redownload is True, then we need to reload regardless of the status
        if force_redownload or force_reload or (not self.initialised and not self.updating):
            message = await ctx.send(f"{emotes.Loading} The GTFS data has not been initialised yet. This may take a few minutes...")
            await self.load_data(force_redownload=force_redownload, force_reload=force_reload, ignore_real_time=ignore_real_time)
        elif self.updating:
            message = await ctx.send(f"{emotes.Loading} The GTFS data used by this bot is currently being updated and is therefore unavailable. This may take a few minutes...")
        else:
            message = await ctx.send(f"{emotes.Loading} Loading the response...")

        await self.update_fleet(force_update=False)

        # Keep the function alive until the bot is initialised and the data has been updated
        while not self.initialised or self.updating:
            if self.loader_error is not None:
                raise RuntimeError("An error occurred while loading GTFS data, crashing initialisation loop.") from self.loader_error
            await asyncio.sleep(1)

        # Report soft errors loading data to the error logs channel instead of silently ignoring them
        if self.soft_loader_error is not None:
            prefix = "Non-critical error downloading GTFS data (existing static data loaded)"
            command = ctx.message.content if ctx.interaction is None else general.build_interaction_content(ctx.interaction)
            ec = self.bot.get_channel(self.bot.local_config["error_channel"])
            if ec is not None:
                error = general.traceback_maker(self.soft_loader_error, command[:750], ctx.guild, ctx.author)
                await ec.send(f"{prefix}\n\n{error}")
            error_message = (f"{print_current_time()} > {self.bot.full_name} > {ctx.guild} > {ctx.author} ({ctx.author.id}) > {command} > "
                             f"{prefix}: {type(self.soft_loader_error).__name__}: {str(self.soft_loader_error)}")
            general.print_error(error_message)
            self.soft_loader_error = None

        # Make sure an error is raised if it occurred above
        if self.loader_error is not None:
            raise self.loader_error from None

        return message

    async def get_fleet_list_web(self) -> list[timetables.FleetVehicle]:
        """ Get vehicle data from bustimes """
        def strip(string: str | None):
            if string:
                return string.strip()
            return string

        all_vehicles: list[timetables.FleetVehicle] = []
        for agency, url in self.fleet_list_urls:
            # This depends on the layout of the website not changing. Oh well.
            data = await http.get(url, res_method="text")
            soup = BeautifulSoup(data, "html.parser")
            vehicles = soup.body.main.find(name="div", id="content").find(name="div", class_="table-wrapper").table.tbody.find_all(name="tr")
            # trivia_idx = 7 if i == 0 else 6
            for vehicle in vehicles:
                vehicle_id = vehicle["id"][3:]
                columns = vehicle.find_all(name="td")
                fleet_number = strip(columns[0].a.string)
                try:
                    reg_plates = strip(columns[1].a.string)
                except AttributeError:
                    reg_plates = "Unknown"
                model = strip(columns[4].string)
                trivia = strip(columns[-3].string)  # Always third last column
                all_vehicles.append(timetables.FleetVehicle(vehicle_id, fleet_number, reg_plates, model, trivia, agency))
                # all_vehicles.append({"vehicle_id": vehicle_id, "fleet_number": fleet_number, "reg_plates": reg_plates, "model": model, "trivia": trivia})
        return all_vehicles

    async def update_fleet(self, force_update: bool = False):
        """ Save or update vehicle data from bustimes """
        # This function shouldn't really have to run more than once per uptime, but let's keep this here in case the bot stays up for more than two weeks
        if self.updating_vehicles:
            return
        try:
            self.updating_vehicles = True
            # Check if the existing data has expired
            expiry = self.db.fetchrow("SELECT * FROM expiry WHERE type=2")
            if not expiry:
                force_update = True
            elif time.date.today() > time.date.from_datetime(expiry["date"]):
                force_update = True
            # Download the new data, if necessary
            if force_update:
                all_vehicles: list[timetables.FleetVehicle] = await self.get_fleet_list_web()
                # noinspection SqlWithoutWhere
                statements = ["BEGIN", "DELETE FROM vehicles"]
                for vehicle in all_vehicles:
                    statements.append(vehicle.save_to_sql())
                    self.fleet_data[vehicle.vehicle_id] = vehicle
                    # vehicle_id = vehicle["vehicle_id"]
                    # fleet_number = vehicle["fleet_number"]
                    # reg_plates = vehicle["reg_plates"]
                    # model = vehicle["model"]
                    # trivia = vehicle["trivia"]
                    # statements.append(f"INSERT INTO vehicles(vehicle_id, fleet_number, reg_plates, model, trivia) VALUES ({vehicle_id!r}, {fleet_number!r}, {reg_plates!r}, {model!r}, {trivia!r})")
                new_expiry = (time.date.today() + time.timedelta(days=14)).iso()
                if expiry:
                    statements.append(f"UPDATE expiry SET date={new_expiry!r} WHERE type=2")
                else:
                    statements.append(f"INSERT INTO expiry(type, date) VALUES (2, {new_expiry!r})")
                statements.append("COMMIT;")
                self.db.executescript("; ".join(statements))
                logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Loaded new fleet data from bustimes")
            else:
                if not self.fleet_data:  # Only reload the data if it does not yet exist
                    self.fleet_data = timetables.FleetVehicle.fetch_all(self.db)
                    logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Loaded existing fleet data from storage")
        finally:
            self.updating_vehicles = False

    @commands.group(name="placeholder", case_insensitive=True)  # , invoke_without_command=True
    # @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @commands.is_owner()
    async def placeholder(self, ctx: commands.Context):  # , action: str = None, force_redownload: str = None
        """ Placeholder """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)
            # if action == "write":
            #     if force_redownload == "force-redownload":
            #         debug = False
            #     else:
            #         debug = self._DEBUG
            #     await self.get_real_time_data(debug=debug, write=self._WRITE)
            # return await ctx.send("Placeholder")

    @placeholder.command(name="debug", aliases=["toggledebug"])
    async def toggle_debug_mode(self, ctx: commands.Context):
        """ Toggle Debug Mode """
        self.DEBUG ^= True
        return await ctx.send(f"{self.DEBUG=}")

    @placeholder.command(name="write", aliases=["togglewrite"])
    async def toggle_write_mode(self, ctx: commands.Context):
        """ Toggle Write Mode """
        self.WRITE ^= True
        return await ctx.send(f"{self.WRITE=}")

    @placeholder.command(name="refresh")
    async def refresh_real_time_data(self, ctx: commands.Context, force_redownload: bool = False):
        """ Refresh real-time GTFS data """
        debug = False if force_redownload else self.DEBUG
        await self.get_real_time_data(debug=debug, write=self.WRITE)
        return await ctx.send(f"Refreshed real-time data. {debug=}")

    @placeholder.command(name="load")
    async def load_gtfs(self, ctx: commands.Context):
        """ Load GTFS data """
        message = await self.wait_for_initialisation(ctx)
        return await message.edit(content=f"{print_current_time()} > Data has been loaded")

    @placeholder.command(name="reload")
    async def reload_gtfs(self, ctx: commands.Context):
        """ Reload static GTFS data without downloading updates from the server """
        message = await self.wait_for_initialisation(ctx, force_redownload=False, force_reload=True)
        return await message.edit(content=f"{print_current_time()} > Data has been reloaded")

    @placeholder.command(name="redownload")
    async def redownload_gtfs(self, ctx: commands.Context):
        """ Download new static GTFS data and reload it """
        message = await self.wait_for_initialisation(ctx, force_redownload=True)
        return await message.edit(content=f"{print_current_time()} > Data has been re-downloaded")

    @placeholder.command(name="reset")
    async def reset_error(self, ctx: commands.Context):
        """ Reset the cog's flags to initial state """
        self.loader_error = None
        self.initialised = False
        self.updating = False
        return await ctx.send(f"{print_current_time()} > Reset the loader error status and reset the initialised and updating values to False.")

    @placeholder.command(name="reloadmodule", aliases=["rm"])
    async def reload_modules(self, ctx: commands.Context, debug: bool = True, write: bool = False):
        modules = ("utils.timetables.shared", "utils.timetables.realtime", "utils.timetables.trains", "utils.timetables.static", "utils.timetables.schedules",
                   "utils.timetables.maps", "utils.timetables.viewers", "utils.timetables.views", "utils.timetables", "cogs.timetables")
        for module_name in modules:
            module = importlib.import_module(module_name)
            importlib.reload(module)
        self.initialised = True
        self.updating = False
        self.DEBUG = debug
        self.WRITE = write
        self.static_data = timetables.init_gtfs_data(ignore_expiry=True)
        await self.load_real_time_data(debug=self.DEBUG, write=self.WRITE)
        return await ctx.send(f"Reloaded modules and data. {self.DEBUG=}, {self.WRITE=}")

    @placeholder.command(name="check")
    async def check_error(self, ctx: commands.Context):
        """ Check error status """
        flags_status = f"{self.DEBUG=}\n{self.WRITE=}\n{self.initialised=}\n{self.updating=}"
        if self.loader_error is None:
            return await ctx.send(f"{flags_status}\n{self.loader_error=}")
        error = general.traceback_maker(self.loader_error)
        return await ctx.send(f"{flags_status}\nself.loader_error has an error stored:\n{error[-1900:]}")

    @placeholder.command(name="vehicles")
    async def update_vehicle_data(self, ctx: commands.Context):
        """ Update the vehicle data from bustimes """
        await self.update_fleet(force_update=True)
        return await ctx.send(f"{print_current_time()} > Fleet data has been successfully updated.")

    def find_stop(self, query: str) -> list[timetables.Stop]:
        """ Find a specific stop """
        query = query.lower()
        all_stops = self.db.fetch("SELECT id, code, name FROM stops")
        output = []
        for stop_dict in all_stops:
            if query in stop_dict["id"].lower() or query in f"{stop_dict['code']} {stop_dict['name']}".lower():
                stop = timetables.Stop.from_sql(stop_dict["id"], self.db)  # We need to fetch the rest of the data now
                # stop = timetables.Stop.from_dict(stop_dict)
                output.append(stop)
                self.static_data.stops[stop.id] = stop
        return output

    def find_route(self, query: str) -> list[timetables.Route]:
        """ Find a specific route """
        query = query.lower()
        all_routes = self.db.fetch("SELECT id, short_name, long_name FROM routes")
        output = []
        for route_dict in all_routes:
            # Require exact match to ID, but allow partial matches for the route number + destinations
            if query == route_dict["id"].lower() or query in f"{route_dict['short_name']} {route_dict['long_name']}".lower():
                route = timetables.Route.from_sql(route_dict["id"], self.db)
                # route = timetables.Route.from_dict(route_dict)
                output.append(route)
                self.static_data.routes[route.id] = route
        return output

    def find_specific_vehicle(self, query: str) -> timetables.FleetVehicle | None:
        vehicle = self.db.fetchrow("SELECT * FROM vehicles WHERE vehicle_id=?1 OR fleet_number=?1", (query,))
        if not vehicle:
            return None
        return timetables.FleetVehicle.from_dict(vehicle)

    async def _soft_limit_warning(self, ctx: commands.Context):
        """ Show the warning about the soft expiry of static data """
        if not self.soft_limit_warning:
            try:
                data_valid = timetables.check_gtfs_data_expiry(self.db)
                if not data_valid:
                    await ctx.send("Warning: The GTFS data currently stored here has become more than a month old. It should be updated soon to prevent it from going out of date.")
                self.soft_limit_warning = True  # The warning is shown only once per bot restart.
            except RuntimeError:  # This should never happen by this stage, but better safe than sorry
                return await ctx.send("The GTFS data available has expired.")

    @commands.hybrid_group(name="tfi", case_insensitive=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    # @commands.is_owner()
    @commands.cooldown(rate=1, per=4, type=commands.BucketType.user)
    # @app_commands.guilds(738425418637639775)
    async def tfi(self, ctx: commands.Context):
        """ Base command for TFI-related things """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @tfi.group(name="search", case_insensitive=True)
    async def tfi_search(self, ctx: commands.Context):
        """ Search for a stop or route """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    async def tfi_search_function(self, ctx: commands.Context, query: str, search_function: GTFSSearchFunction, iteration_handler: Callable[[Any], str], title: str, footer: str):
        """ Wrapper function for search commands """
        message = await self.wait_for_initialisation(ctx)
        iterable = search_function(query=query)  # (str) -> list[Stop | Route]
        if not iterable:
            return await message.edit(content=f"{emotes.Deny} No data was found for your query.")
        paginator = paginators.LinePaginator(prefix=None, suffix=None, max_lines=20, max_size=1000)
        for entry in iterable:  # Stop or Route
            paginator.add_line(iteration_handler(entry))
        embed = discord.Embed(title=title, colour=general.random_colour())
        embed.set_footer(text=footer)
        interface = paginators.PaginatorEmbedInterface(self.bot, paginator, owner=ctx.author, embed=embed)
        return await interface.set_message(message, clear_content=True)

    @tfi_search.command(name="stop")
    @app_commands.describe(query="The ID, code, or name of the stop you want to look for")
    async def tfi_search_stop(self, ctx: commands.Context, *, query: str):
        """ Search for a specific stop """
        def add_stop(stop: timetables.Stop) -> str:
            if stop.code:
                return f"`{stop.id}` (Stop code `{stop.code}`) - {stop.name}"
            else:
                return f"`{stop.id}` - {stop.name}"
        return await self.tfi_search_function(ctx, query, search_function=self.find_stop, iteration_handler=add_stop, title="Stops found for your query",
                                              footer="Note: If more than one stop is found for your search, the schedule command will need a more precise query to function.\n"
                                              "Try using both the stop code and stop name in your query, for example `17 Drumcondra`.")

    @tfi_search.command(name="route")
    @app_commands.describe(query="The ID, name, or end points of the route you want to look for")
    async def tfi_search_route(self, ctx: commands.Context, *, query: str):
        """ Search for a specific route """
        route_types = {0: "Tram", 1: "Subway", 2: "Rail", 3: "Bus", 4: "Ferry", 5: "Cable tram", 6: "Aerial lift", 7: "Funicular", 11: "Trolleybus", 12: "Monorail"}

        def add_route(route: timetables.Route) -> str:
            return f"`{route.id}` - Route {route.short_name} - {route.long_name} ({route_types[route.route_type]})"

        return await self.tfi_search_function(ctx, query, search_function=self.find_route, iteration_handler=add_route, title="Routes found for your query",
                                              footer="Note: If more than our route is found for your search, the schedule command will need a more precise query to function."
                                                     "Try using the route ID or combining the route number with the origin point (e.g. `155 Bray` or `4 Monkstown`).")
        # output_content = ("Here are the routes found for your query:\n\n" + "\n".join(output) +
        #                   "\n\n*Note that if more than one route is found for your search, then the schedule command will need a more precise query to function.*\n"
        #                   "*You can use both the route number and route destinations in your query, e.g. `155 Bray` or `4 Monkstown`. "
        #                   "However, the words have to match the beginning of the route's description (i.e. if it says \"Bray - IKEA Ballymun\", you cannot use `155 IKEA`).*")

    @tfi.group(name="schedule", aliases=["schedules", "timetable", "timetables", "data", "info", "rtpi", "tt"], case_insensitive=True)
    async def tfi_schedules(self, ctx: commands.Context):
        """ Commands that deal with schedules and real-time information """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    async def tfi_stop_autocomplete(self, _interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """ Autocomplete for the stop search """
        search = "%" + current.replace("!", "!!").replace("%", "!%").replace("_", "!_").replace("[", "![") + "%"
        data = self.db.fetch("SELECT id, code, name FROM stops WHERE id LIKE ?1 ESCAPE '!' OR (code || ' ' || name) LIKE ?1 ESCAPE '!'", (search,))
        # results: [(code, name, similarity), ...]
        results: list[tuple[str, str, int]] = []
        for entry in data:
            ratios = (process.default_scorer(current, entry["id"]), process.default_scorer(current, f"{entry['code']} {entry['name']}"))
            if entry["code"]:
                stop_name = f"{entry['name']} (stop code {entry['code']})"
            else:
                stop_name = f"{entry['name']} (stop ID {entry['id']})"
            results.append((entry["id"], stop_name, max(ratios)))
        results.sort(key=lambda x: x[2], reverse=True)
        return [app_commands.Choice(name=stop_name, value=stop_id) for stop_id, stop_name, _ in results[:25]]

    @staticmethod
    def get_hub_suggestions(current: str) -> list[tuple[str, int]]:
        current = current.replace("á", "a")  # Busáras key
        results: list[tuple[str, int]] = []
        for key in STOP_HUBS.keys():
            results.append((key, process.default_scorer(current, key)))
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    async def tfi_hub_autocomplete(self, _interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """ Autocomplete for the stop hub search """
        results = self.get_hub_suggestions(current)
        return [app_commands.Choice(name=result, value=result) for result, _ in results[:25]]

    async def tfi_vehicle_autocomplete(self, _interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """ Autocomplete for the specific vehicle search """
        if not self.fleet_data:
            await self.update_fleet(force_update=False)
        results: list[tuple[str, str, int]] = []
        for vehicle in self.fleet_data.values():
            ratios = (process.default_scorer(current, vehicle.vehicle_id), process.default_scorer(current, vehicle.fleet_number))
            results.append((vehicle.vehicle_id, f"{vehicle.fleet_number} ({vehicle.agency}, API ID {vehicle.vehicle_id})", max(ratios)))  # f"{vehicle.fleet_number} ({vehicle.reg_plates})"
        results.sort(key=lambda x: x[2], reverse=True)
        return [app_commands.Choice(name=fleet_and_reg, value=vehicle_id) for vehicle_id, fleet_and_reg, _ in results[:25]]

    async def tfi_route_autocomplete(self, _interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """ Autocomplete for route search """
        search = "%" + current.replace("!", "!!").replace("%", "!%").replace("_", "!_").replace("[", "![") + "%"
        data = self.db.fetch("SELECT id, short_name, long_name FROM routes WHERE id LIKE ?1 ESCAPE '!' OR (short_name || ' ' || long_name) LIKE ?1 ESCAPE '!'", (search,))
        # results: [(code, name, similarity), ...]
        results: list[tuple[str, str, int]] = []
        for entry in data:
            ratios = (process.default_scorer(current, entry["id"]), process.default_scorer(current, f"{entry['short_name']} {entry['long_name']}"))
            route_name = f"Route {entry['short_name']} ({entry['long_name']})"
            results.append((entry["id"], route_name, max(ratios)))
        results.sort(key=lambda x: x[2], reverse=True)
        return [app_commands.Choice(name=route_name, value=route_id) for route_id, route_name, _ in results[:25]]

    @tfi_schedules.command(name="stop")
    @app_commands.rename(stop_query="stop")
    @app_commands.autocomplete(stop_query=tfi_stop_autocomplete)
    @app_commands.describe(
        stop_query="The ID, code, or name of the stop for which you want to see the schedule",
        timestamp="The time for which to load the schedule (format: `YYYY-MM-DD HH:MM:SS`)",
        show_terminating="Leave empty to hide arrivals that terminate at this stop. Add any text here to show them."
    )
    async def tfi_schedules_stop(self, ctx: commands.Context, *, stop_query: str, timestamp: str = None, show_terminating: str = None):  # timestamp arg will be used by the slash command
        """ Show the next departures for a specific stop """
        message = await self.wait_for_initialisation(ctx)
        # language = ctx.language2("en")
        if ctx.interaction is None:
            stop_query, timestamp, show_terminating, valid_check = self.get_stop_query_and_timestamp(stop_query)
            if not valid_check:
                return await message.edit(content=stop_query)
        else:
            show_terminating = bool(show_terminating)
        now, valid_check = self.parse_timestamp(timestamp)
        if not valid_check:
            return await message.edit(content="Invalid timestamp. Make sure it is in the following format: `YYYY-MM-DD HH:MM:SS`.")
        stops = self.find_stop(stop_query)
        if len(stops) != 1:
            start = "No stops were found" if len(stops) < 1 else "More than one stop was found"
            return await message.edit(content=f"{start} for your search query ({stop_query}).\n"
                                              f"Use `{ctx.prefix}tfi search stop` to find the specific stop code or provide a more specific query.\n"
                                              "*Hint: You can use both the stop code and the stop name in your query, e.g. `17 Drumcondra`.*")
        stop = stops[0]

        await self._soft_limit_warning(ctx)

        await self.load_real_time_data(debug=self.DEBUG, write=self.WRITE)
        try:
            schedule = await timetables.StopScheduleViewer.load(self.static_data, stop, self, now, hide_terminating=not show_terminating, user_id=ctx.author.id)
        except Exception:
            # For some reason, without this block, exceptions raised are simply silently ignored, this will forward them to the on_command_error listener.
            raise
            # await ctx.send(ctx.language2("en").string("events_error_error", err=f"{type(e).__name__}: {e}"))
            # error_message = (f"{time.datetime.now():%d %b %Y, %H:%M:%S} > {self.bot.full_name} > Error occurred while loading stop schedule\n"
            #                  f"{general.traceback_maker(e, text=ctx.message.content, guild=ctx.guild, author=ctx.author, code_block=False)}")
            # general.print_error(error_message)
            # logger.log(self.bot.name, "errors", error_message)
            # return
        return await message.edit(content=schedule.output, view=timetables.StopScheduleView(ctx.author, message, schedule, ctx=ctx) if not schedule.empty else None)
        # return await message.edit(view=await timetables.StopScheduleView(ctx.author, message, self.static_data, stop, self.real_time_data, self.vehicle_data))

    @tfi_schedules.command(name="hub", aliases=["collection"])
    @app_commands.rename(hub_id="hub")
    @app_commands.autocomplete(hub_id=tfi_hub_autocomplete)
    @app_commands.describe(
        hub_id="The stop hub for which schedules should be fetched",
        timestamp="The time for which to load the schedule (format: `YYYY-MM-DD HH:MM:SS`)",
        show_terminating="Leave empty to hide arrivals that terminate at this stop. Add any text here to show them."
    )
    async def tfi_schedules_hub(self, ctx: commands.Context, *, hub_id: str, timestamp: str = None, show_terminating: str = None):  # timestamp arg will be used by the slash command
        """ Show the next departures for a specific stop """
        message = await self.wait_for_initialisation(ctx)
        # language = ctx.language2("en")
        if ctx.interaction is None:
            hub_id, timestamp, show_terminating, valid_check = self.get_stop_query_and_timestamp(hub_id)
            if not valid_check:
                return await message.edit(content=hub_id)
        else:
            show_terminating = bool(show_terminating)
        now, valid_check = self.parse_timestamp(timestamp)
        if not valid_check:
            return await message.edit(content="Invalid timestamp. Make sure it is in the following format: `YYYY-MM-DD HH:MM:SS`.")

        hub_id = hub_id.replace("á", "a")  # Busáras key
        try:
            hub = STOP_HUBS[hub_id]
        except KeyError:
            suggestions = [suggestion for suggestion, ratio in self.get_hub_suggestions(hub_id) if ratio > 70][:3]
            if suggestions:
                return await message.edit(content=f"The specified hub does not exist. Did you mean: `{'`, `'.join(suggestions)}`?")
            return await message.edit(content="The specified hub does not exist. Make sure the spelling and capitalisation are correct.")

        await self._soft_limit_warning(ctx)

        await self.load_real_time_data(debug=self.DEBUG, write=self.WRITE)
        try:
            stops: list[timetables.Stop] = []
            for stop_id in hub:
                stops.append(timetables.load_value(self.static_data, timetables.Stop, stop_id, self.db))
            schedule = await timetables.HubScheduleViewer.load(hub_id, stops, now, not show_terminating, ctx.author.id, self.static_data, self)
        except Exception:
            raise
        return await message.edit(content=schedule.output, view=timetables.HubScheduleView(ctx.author, message, schedule, ctx=ctx))

    @tfi_schedules.command(name="route")
    @app_commands.rename(route_query="route")
    @app_commands.autocomplete(route_query=tfi_route_autocomplete)
    @app_commands.describe(
        route_query="The number (and optionally destinations) of the route or its ID",
        timestamp="The time for which to load the schedule (format: `YYYY-MM-DD HH:MM:SS`)",
        direction="The direction for which to look up the timetable (inbound or outbound)"
    )
    async def tfi_schedules_route(self, ctx: commands.Context, *, route_query: str, timestamp: str = None, direction: str = "outbound"):
        """ Show the timetable for a route """
        message = await self.wait_for_initialisation(ctx, ignore_real_time=True)
        if ctx.interaction is None:
            route_query, timestamp, direction_id, valid_check = self.get_route_query_and_timestamp(route_query)
            if not valid_check:
                return await message.edit(content=route_query)
        else:
            direction = direction.lower()
            if direction in ("0", "in", "inbound"):
                direction_id = timetables.INBOUND_DIRECTION_ID
            elif direction in ("1", "out", "outbound"):
                direction_id = timetables.INBOUND_DIRECTION_ID ^ 1  # Opposite of that value
            else:
                return await message.edit(content=f"Unknown direction {direction} - Must be either \"inbound\" or \"outbound\"")
        now, valid_check = self.parse_timestamp(timestamp)
        if not valid_check:
            return await message.edit(content="Invalid timestamp. Make sure it is in the following format: `YYYY-MM-DD HH:MM:SS`.")
        routes = self.find_route(route_query)
        if len(routes) != 1:
            start = "No routes were found" if len(routes) < 1 else "More than one route was found"
            return await message.edit(content=f"{start} for your search query ({route_query}).\nUse `{ctx.prefix}tfi search route` to find your specific route's ID, or provide a more specific query.")
        route = routes[0]
        await self._soft_limit_warning(ctx)
        try:
            schedule = await timetables.RouteScheduleViewer.load(self.static_data, route, now, direction_id)
        except Exception:
            raise
        view = timetables.RouteScheduleView(ctx.author, message, schedule, ctx=ctx)
        return await message.edit(content=view.content, view=view)

    @tfi.command(name="map")
    @app_commands.rename(stop_query="stop")
    @app_commands.autocomplete(stop_query=tfi_stop_autocomplete)
    @app_commands.describe(stop_query="The ID, code, or name of the stop for which you want to see the schedule")
    async def tfi_stop_map(self, ctx: commands.Context, *, stop_query: str):
        """ Show a map of the area around a stop, including any buses nearby. """
        message = await self.wait_for_initialisation(ctx)
        stops = self.find_stop(stop_query)
        if len(stops) != 1:
            start = "No stops were found" if len(stops) < 1 else "More than one stop was found"
            return await message.edit(content=f"{start} for your search query ({stop_query}).\n"
                                              f"Use `{ctx.prefix}tfi search stop` to find the specific stop code or provide a more specific query.\n"
                                              "*Hint: You can use both the stop code and the stop name in your query, e.g. `17 Drumcondra`.*")
        stop = stops[0]

        await self._soft_limit_warning(ctx)

        await self.load_real_time_data(debug=self.DEBUG, write=self.WRITE)
        if not self.vehicle_data:
            return await message.edit(content="Vehicle data seems to be unavailable at the moment. Try again in a minute.")
        try:
            map_viewer: timetables.MapViewer = await timetables.MapViewer.load(self, stop, zoom=timetables.DEFAULT_ZOOM)
        except Exception:
            raise
        return await message.edit(content=map_viewer.output, attachments=map_viewer.attachment, view=timetables.MapView(ctx.author, message, map_viewer, ctx))

    @tfi.group(name="vehicles", aliases=["vehicle", "buses", "bus"], case_insensitive=True)
    async def tfi_vehicles(self, ctx: commands.Context):
        """ Commands related to information about vehicles """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @tfi_vehicles.command(name="specific")
    @app_commands.autocomplete(vehicle_id=tfi_vehicle_autocomplete)
    @app_commands.describe(vehicle_id="The fleet number of the vehicle or its API vehicle ID")
    async def tfi_vehicles_specific(self, ctx: commands.Context, *, vehicle_id: str):
        """ Show information about a specific vehicle """
        message = await self.wait_for_initialisation(ctx)
        vehicle = self.find_specific_vehicle(vehicle_id)
        if not vehicle:
            return await message.edit(content=f"The specified vehicle {vehicle_id} was not found.")
        await self._soft_limit_warning(ctx)
        await self.load_real_time_data(debug=self.DEBUG, write=self.WRITE)
        try:
            viewer = timetables.VehicleDataViewer(self, vehicle)
        except Exception:
            raise
        return await message.edit(content=viewer.output, view=timetables.VehicleDataView(ctx.author, message, viewer, ctx))

    @tfi_vehicles.command(name="route")
    @app_commands.rename(route_query="route")
    @app_commands.autocomplete(route_query=tfi_route_autocomplete)
    @app_commands.describe(route_query="The number (and optionally destinations) of the route or its ID")
    async def tfi_vehicles_route(self, ctx: commands.Context, *, route_query: str):
        """ List of vehicles currently serving a specific route """
        """ Show information about a specific vehicle """
        message = await self.wait_for_initialisation(ctx)
        routes = self.find_route(route_query)
        if len(routes) != 1:
            start = "No routes were found" if len(routes) < 1 else "More than one route was found"
            return await message.edit(content=f"{start} for your search query ({route_query}).\nUse `{ctx.prefix}tfi search route` to find your specific route's ID, or provide a more specific query.")
        route = routes[0]
        await self._soft_limit_warning(ctx)
        await self.load_real_time_data(debug=self.DEBUG, write=self.WRITE)
        try:
            viewer = timetables.RouteVehiclesViewer(self, route)
        except Exception:
            raise
        return await message.edit(content=viewer.output, view=timetables.RouteVehiclesView(ctx.author, message, viewer, ctx))

    # If this command is uncommented, it will still get synced to a slash command for whatever reason
    # @tfi.command(name="debug", enabled=False)
    # @commands.is_owner()
    # async def tfi_debug_command(self, ctx: commands.Context):  # , trip: str = "155"
    #     """ Debug certain commands """
    #     import importlib
    #     modules = ("utils.timetables.shared", "utils.timetables.realtime", "utils.timetables.static", "utils.timetables.schedules", "utils.timetables.maps",
    #                "utils.timetables.viewers", "utils.timetables.views", "utils.timetables")
    #     for module_name in modules:
    #         module = importlib.import_module(module_name)
    #         importlib.reload(module)
    #     self.initialised = True
    #     self.updating = False
    #     self.DEBUG = True
    #     self.WRITE = False
    #     self.static_data = timetables.init_gtfs_data(ignore_expiry=True)
    #     await self.load_real_time_data(debug=self.DEBUG, write=self.WRITE)
    #     message = await ctx.send(f"{emotes.Loading} Debug: Initialisation bypassed and modules reloaded")
    #     # trip_id = {
    #     #     "16": "4159_5535||0",
    #     #     "16B": "4159_70418||0",
    #     #     "16D": "4159_5774||0",
    #     #     "33N": "4175_21||0",
    #     #     "44": "4159_10812|T1001|0",
    #     #     "46A": "4159_11162||0",
    #     #     "46B": "4159_10876||0",
    #     #     "46U": "4159_10875||0",
    #     #     "99": "4159_14592|T185|0",
    #     #     "155": "4159_4567|T184|0",
    #     #     "155B": "4159_4414||0",
    #     #     "225": "4174_101560||0",
    #     #     "225B": "4174_71091||0",
    #     #     "N4": "4159_18353|T1002|0",
    #     #     "N4B": "4159_18609|T186|0",
    #     #     "DARTM": "4176_2046||0",
    #     #     "DARTH": "4176_2047||0",
    #     #     "CORK": "4176_5358||0",
    #     #     "ADDED": "|T183|0"
    #     # }.get(trip.upper(), "4159_4567||0")
    #     stop = timetables.load_value(self.static_data, timetables.Stop, "8220DB001738", self.db)  # 8350DB004153
    #     schedule_viewer = await timetables.StopScheduleViewer.load(self.static_data, stop, self.real_time_data, self.vehicle_data, self,
    #                                                                time.datetime(2024, 8, 8, 7, 17, tz=timetables.TIMEZONE), user_id=ctx.author.id)
    #     schedule_view = timetables.StopScheduleView(ctx.author, message, schedule_viewer, ctx)
    #     return await message.edit(content=schedule_viewer.output, view=schedule_view)
    #     # diagram_viewer = timetables.TripDiagramViewer(schedule_view, trip_id)
    #     # # diagram_view = timetables.TripDiagramView(ctx.author, message, diagram_viewer, try_full_fetch=False)
    #     # map_viewer = await timetables.TripMapViewer.load(diagram_viewer)
    #     # return await message.edit(content=map_viewer.output, attachments=map_viewer.attachment, view=timetables.TripMapView(ctx.author, message, map_viewer, ctx))


async def setup(bot: bot_data.Bot):
    # if bot.name == "suager":
    #     await bot.add_cog(University(bot))
    # elif bot.name == "cobble":
    #     await bot.add_cog(Luas(bot))
    # else:
    await bot.add_cog(Timetables(bot))
