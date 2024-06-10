import asyncio
import json
from collections.abc import Callable, Awaitable
from io import BytesIO
from typing import Any, Protocol
from zipfile import ZipFile, BadZipFile

import discord
import luas.api
from aiohttp import ClientError
from discord import app_commands
from regaus import time
from thefuzz import process

from utils import bot_data, commands, http, timetables, logger, emotes, dcu, paginators, general, arg_parser, cpu_burner
from utils.time import time as print_current_time


def dcu_data_access(ctx):
    return ctx.guild is None or ctx.guild.id == 738425418637639775 or ctx.author.id == 302851022790066185
    # return ctx.bot.name == "timetables" or ctx.author.id in [302851022790066185]


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
    @commands.check(dcu_data_access)
    @app_commands.guilds(738425418637639775)
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
                # Push September 2023 to be "January 2024", so that we can start defaulting to COMSCI 2 in Sep 2024
                # Sep 2023 - Aug 2024 -> 1, Sep 2024 - Aug 2025 -> 2, etc.
                year = (time.date.today() + time.relativedelta(months=4, time_class=time.Earth)).year - 2023
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


# Cog for Luas timetables - loaded by Cobble
class Luas(commands.Cog, name="Timetables"):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.command(name="luas")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def luas(self, ctx: commands.Context, *, place: commands.clean_content):
        """ Data for Luas """
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
        self._DEBUG = False  # Debug Mode: Disables sending API requests for GTFS-R and disables pickling the static data
        self._WRITE = True   # Write real-time data to disk
        self.url = "https://api.nationaltransport.ie/gtfsr/v2/TripUpdates?format=json"
        self.vehicle_url = "https://api.nationaltransport.ie/gtfsr/v2/Vehicles?format=json"
        self.gtfs_data_url = "https://www.transportforireland.ie/transitData/Data/GTFS_All.zip"
        self.headers = {
            "Cache-Control": "no-cache",
            "x-api-key": self.bot.config["gtfsr_api_token"]
        }
        self.real_time_data: timetables.GTFSRData | None = None
        self.vehicle_data: timetables.VehicleData | None = None
        self.static_data: timetables.GTFSData | None = None
        self.initialised = False
        self.updating = False
        self.loader_error: Exception | None = None
        self.soft_loader_error: Exception | None = None
        self.last_updated: time.datetime | None = None
        self.soft_limit_warning: bool = False

    @staticmethod
    def get_query_and_timestamp(query: str) -> tuple[str, str | None, bool]:
        """ Split the query and timestamp using argparse """
        parser = arg_parser.Arguments()
        parser.add_argument("--time", nargs="+")
        parser.add_argument("query", nargs="+")
        args, valid_check = parser.parse_args(query)
        if not valid_check:
            return args, None, False
        query = " ".join(args.query)
        if args.time is not None:
            timestamp = " ".join(args.time)
        else:
            timestamp = None
        return query, timestamp, True

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

    async def get_data_from_api(self, *, write: bool = True):
        data: bytes = await http.get(self.url, headers=self.headers, res_method="read")
        if write:
            with open(timetables.real_time_filename, "wb+") as file:
                file.write(data)
            # json.dump(data, open(timetables.real_time_filename, "w+"), indent=2)
        return data

    async def get_vehicles_from_api(self, *, write: bool = True):
        data: bytes = await http.get(self.vehicle_url, headers=self.headers, res_method="read")
        if write:
            with open(timetables.vehicles_filename, "wb+") as file:
                file.write(data)
        return data

    async def load_real_time_data(self, debug: bool = False, *, write: bool = True):
        # Only refresh the data once in 60 seconds
        if self.last_updated is not None and (time.datetime.now() - self.last_updated).total_seconds() < 60:
            return self.real_time_data, self.vehicle_data
        data, vehicle_data = await self.get_real_time_data(debug=debug, write=write)
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
        logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Successfully loaded GTFS-R data")
        self.last_updated = time.datetime.now()
        return self.real_time_data, self.vehicle_data  # just in case

    async def get_real_time_data(self, debug: bool = False, *, write: bool = True):
        """ Gets real-time data from the NTA's API or load from cache if in debug mode """
        if debug or (self.last_updated is not None and (time.datetime.now() - self.last_updated).total_seconds() < 60):
            try:
                with open(timetables.real_time_filename, "rb") as file:
                    data: bytes = file.read()
                with open(timetables.vehicles_filename, "rb") as file:
                    vehicles: bytes = file.read()
            except FileNotFoundError:
                data: bytes = await self.get_data_from_api(write=write)
                vehicles: bytes = await self.get_vehicles_from_api(write=write)
                self.last_updated = time.datetime.now()
        else:
            data: bytes = await self.get_data_from_api(write=write)
            vehicles: bytes = await self.get_vehicles_from_api(write=write)
            self.last_updated = time.datetime.now()
        return json.loads(data), json.loads(vehicles)

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     await asyncio.sleep(60)  # To let the other bots load before we freeze the machine for half a minute

    async def load_data(self, *, force_redownload: bool = False, force_reload: bool = False):
        """ Load the GTFS-R and static GTFS data only when needed """
        static_reload = False
        try:
            cpu_burner.arr[2] = False  # Disable the CPU burner function while loading the GTFS data
            self.loader_error = None  # Reset any previous error encountered
            self.updating = True
            if self.real_time_data is None:
                await self.load_real_time_data(debug=self._DEBUG, write=self._WRITE)
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
        await loop.run_in_executor(None, timetables.read_and_store_gtfs_data)
        self.static_data = timetables.init_gtfs_data()
        logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > {message}")
        self.updating = False

    async def wait_for_initialisation(self, ctx: commands.Context, *, force_redownload: bool = False, force_reload: bool = False) -> discord.Message:
        """ Initialise the data before letting the actual command execute """
        # If self.updating is True, then the data is already being loaded
        # If force_redownload is True, then we need to reload regardless of the status
        if force_redownload or force_reload or (not self.initialised and not self.updating):
            message = await ctx.send(f"{emotes.Loading} The GTFS data has not been initialised yet. This may take a few minutes...")
            await self.load_data(force_redownload=force_redownload, force_reload=force_reload)
        elif self.updating:
            message = await ctx.send(f"{emotes.Loading} The GTFS data used by this bot is currently being updated and is therefore unavailable. This may take a few minutes...")
        else:
            message = await ctx.send(f"{emotes.Loading} Loading the response...")

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
        self._DEBUG ^= True
        return await ctx.send(f"{self._DEBUG=}")

    @placeholder.command(name="write", aliases=["togglewrite"])
    async def toggle_write_mode(self, ctx: commands.Context):
        """ Toggle Write Mode """
        self._WRITE ^= True
        return await ctx.send(f"{self._WRITE=}")

    @placeholder.command(name="refresh")
    async def refresh_real_time_data(self, ctx: commands.Context, force_redownload: bool = False):
        """ Refresh real-time GTFS data """
        debug = False if force_redownload else self._DEBUG
        await self.get_real_time_data(debug=debug, write=self._WRITE)
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

    @placeholder.command(name="check")
    async def check_error(self, ctx: commands.Context):
        """ Check error status """
        flags_status = f"{self.initialised=}\n{self.updating=}"
        if self.loader_error is None:
            return await ctx.send(f"{flags_status}\n{self.loader_error=}")
        error = general.traceback_maker(self.loader_error)
        return await ctx.send(f"{flags_status}\nself.loader_error has an error stored:\n{error[-1900:]}")

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
            if query in route_dict["id"].lower() or query in f"{route_dict['short_name']} {route_dict['long_name']}".lower():
                route = timetables.Route.from_sql(route_dict["id"], self.db)
                # route = timetables.Route.from_dict(route_dict)
                output.append(route)
                self.static_data.routes[route.id] = route
        return output

    @commands.hybrid_group(name="tfi", case_insensitive=True)
    # @commands.is_owner()
    @commands.cooldown(rate=1, per=4, type=commands.BucketType.user)
    @app_commands.guilds(738425418637639775)
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

    @tfi.group(name="schedule", aliases=["schedules", "data", "info", "rtpi"], case_insensitive=True)
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
        return [app_commands.Choice(name=result[1], value=result[0]) for result in results[:25]]

    @tfi_schedules.command(name="stop")
    @app_commands.autocomplete(stop_query=tfi_stop_autocomplete)
    @app_commands.describe(
        stop_query="The ID, code, or name of the stop for which you want to see the schedule",
        timestamp="The time for which to load the schedule (format: `YYYY-MM-DD HH:MM:SS`)"
    )
    async def tfi_schedules_stop(self, ctx: commands.Context, *, stop_query: str, timestamp: str = None):  # timestamp arg will be used by the slash command
        """ Show the next departures for a specific stop """
        message = await self.wait_for_initialisation(ctx)
        # language = ctx.language2("en")
        if ctx.interaction is None:
            stop_query, timestamp, valid_check = self.get_query_and_timestamp(stop_query)
            if not valid_check:
                return await ctx.send(stop_query)
        now, valid_check = self.parse_timestamp(timestamp)
        if not valid_check:
            return await ctx.send("Invalid timestamp. Make sure it is in the following format: `YYYY-MM-DD HH:MM:SS`.")
        stops = self.find_stop(stop_query)
        if len(stops) != 1:
            start = "No stops were found" if len(stops) < 1 else "More than one stop was found"
            return await message.edit(content=f"{start} for your search query ({stop_query}).\n"
                                              f"Use `{ctx.prefix}tfi search stop` to find the specific stop code or provide a more specific query.\n"
                                              "*Hint: You can use both the stop code and the stop name in your query, e.g. `17 Drumcondra`.*")
        stop = stops[0]

        if not self.soft_limit_warning:
            try:
                data_valid = timetables.check_gtfs_data_expiry(self.db)
                if not data_valid:
                    await ctx.send("Warning: The GTFS data currently stored here has become more than a month old. It should be updated soon to prevent it from going out of date.")
                self.soft_limit_warning = True  # The warning is shown only once per bot restart.
            except RuntimeError:  # This should never happen by this stage, but better safe than sorry
                return await ctx.send("The GTFS data available has expired.")

        await self.load_real_time_data(debug=self._DEBUG, write=self._WRITE)
        try:
            schedule = await timetables.StopScheduleViewer.load(self.static_data, stop, self.real_time_data, self.vehicle_data, cog=self, now=now)
        except Exception:
            raise  # For some reason, without this block, exceptions raised are simply silently ignored, this will forward them to the on_command_error listener.
            # await ctx.send(ctx.language2("en").string("events_error_error", err=f"{type(e).__name__}: {e}"))
            # error_message = (f"{time.datetime.now():%d %b %Y, %H:%M:%S} > {self.bot.full_name} > Error occurred while loading stop schedule\n"
            #                  f"{general.traceback_maker(e, text=ctx.message.content, guild=ctx.guild, author=ctx.author, code_block=False)}")
            # general.print_error(error_message)
            # logger.log(self.bot.name, "errors", error_message)
            # return
        return await message.edit(content=schedule.output, view=timetables.StopScheduleView(ctx.author, message, schedule))
        # return await message.edit(view=await timetables.StopScheduleView(ctx.author, message, self.static_data, stop, self.real_time_data, self.vehicle_data))


async def setup(bot: bot_data.Bot):
    if bot.name == "suager":
        await bot.add_cog(University(bot))
    elif bot.name == "cobble":
        await bot.add_cog(Luas(bot))
    else:
        await bot.add_cog(Timetables(bot))
