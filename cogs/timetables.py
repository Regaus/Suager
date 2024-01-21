import asyncio
import functools
import json
from io import BytesIO
from collections.abc import Callable, Awaitable
from zipfile import ZipFile, BadZipFile

import discord
from aiohttp import ClientError
from regaus import time

from utils import bot_data, commands, http, timetables, logger, emotes, dcu, paginators, general, conworlds
from utils.errors import GTFSAPIError
from utils.time import time as print_current_time


def dcu_data_access(ctx):
    return ctx.bot.name == "timetables" or ctx.author.id in [302851022790066185]


# Cog for university timetables - loaded by Suager
class University(commands.Cog, name="Timetables"):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.group(name="dcu", case_insensitive=True)
    @commands.check(dcu_data_access)
    async def dcu_stuff(self, ctx: commands.Context):
        """ Access stuff related to DCU and its timetables """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @dcu_stuff.group(name="timetable", aliases=["timetables", "tt"], case_insensitive=True, invoke_without_command=True)
    async def dcu_timetable(self, ctx: commands.Context, course_code: str = "COMSCI1", custom_week: str = ""):
        """ Fetch DCU timetables for current week - Defaults to COMSCI1 course """
        if ctx.invoked_subcommand is None:
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
    async def dcu_timetable_modules(self, ctx: commands.Context, *module_codes: str):
        """ Fetch DCU timetables for specified modules for the current week"""
        try:
            date = None
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
    async def dcu_timetable_room(self, ctx: commands.Context, room_code: str, custom_week: str = ""):
        """ Fetch DCU timetables for a given room for the current week"""
        try:
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
    async def dcu_courses(self, ctx: commands.Context, search: str = None):
        """ Fetch DCU course list """
        async with ctx.typing():
            return await self.dcu_list(ctx, dcu.get_courses, "DCU Course Codes", search)

    @dcu_search.command(name="modules", aliases=["module", "modulelist"])
    async def dcu_modules(self, ctx: commands.Context, search: str = None):
        """ Fetch DCU module list """
        async with ctx.typing():
            return await self.dcu_list(ctx, dcu.get_modules, "DCU Module Codes", search,
                                       notes="Note: Some of the modules may have been parsed incorrectly, however I tried to reduce the chance of this happening")

    @dcu_search.command(name="rooms", aliases=["room", "roomlist", "locations", "location", "locationlist"])
    async def dcu_rooms(self, ctx: commands.Context, search: str = None):
        """ Fetch DCU module list """
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
        import luas.api
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
        self.db = timetables.db
        self._DEBUG = False  # Debug Mode: Disables sending API requests for GTFS-R and disables pickling the static data
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
        data, vehicle_data = await self.get_real_time_data(debug=debug, write=write)
        try:
            self.real_time_data, self.vehicle_data = timetables.load_gtfs_r_data(data, vehicle_data)
        except GTFSAPIError as e:
            error_place = e.error_place
            # Load new data for the valid part, and leave the other one as-is
            if error_place == "real-time":
                self.vehicle_data = timetables.load_gtfs_r_data(None, vehicle_data)[1]
            elif error_place == "vehicles":
                self.real_time_data = timetables.load_gtfs_r_data(data, None)[0]
            logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Real-Time API Error for {error_place}: {type(e).__name__}: {str(e)}")
        logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Successfully loaded GTFS-R data")
        return self.real_time_data, self.vehicle_data  # just in case

    async def get_real_time_data(self, debug: bool = False, *, write: bool = True):
        """ Gets real-time data from the NTA's API or load from cache if in debug mode """
        if debug:
            try:
                with open(timetables.real_time_filename, "rb") as file:
                    data: bytes = file.read()
                with open(timetables.vehicles_filename, "rb") as file:
                    vehicles: bytes = file.read()
            except FileNotFoundError:
                data: bytes = await self.get_data_from_api(write=write)
                vehicles: bytes = await self.get_vehicles_from_api(write=write)
        else:
            data: bytes = await self.get_data_from_api(write=write)
            vehicles: bytes = await self.get_vehicles_from_api(write=write)
        return json.loads(data), json.loads(vehicles)

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     await asyncio.sleep(60)  # To let the other bots load before we freeze the machine for half a minute

    async def load_data(self, *, force_redownload: bool = False, force_reload: bool = False):
        """ Load the GTFS-R and static GTFS data only when needed """
        static_reload = False
        try:
            self.loader_error = None  # Reset any previous error encountered
            self.updating = True
            if self.real_time_data is None:
                # data = await self.get_real_time_data(debug=True, write=True)
                # self.real_time_data = timetables.load_gtfs_r_data(data)
                # logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Successfully loaded GTFS-R data")
                await self.load_real_time_data(debug=True, write=True)
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
                        # try:
                        #     self.static_data = timetables.load_gtfs_data_from_pickle(write=not self._DEBUG)  # Don't write pickles while we're in Debug Mode
                        #     logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Successfully loaded static GTFS data")
                        # except (FileNotFoundError, RuntimeError) as e:
                        #     # If the static GTFS data is not available or is expired, download new data and then extract and load.
                        #     logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Error loading static GTFS data: {type(e).__name__}: {e}")
                        #     await self.download_new_static_gtfs()
                except (ClientError, BadZipFile):
                    # If the GTFS data cannot be downloaded due to an error with the powers above, try to load from existing data while ignoring expiry errors
                    logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Can't download data, falling back to existing dataset.")
                    self.static_data = timetables.init_gtfs_data(ignore_expiry=True)
                    # self.static_data = timetables.load_gtfs_data_from_pickle(write=not self._DEBUG, ignore_expiry=True)
                    # If we crash here yet again, then it would make sense to give up and catch on fire.
            self.initialised = True
        except Exception as e:
            self.loader_error = e
            self.initialised = False
            raise e from None
        # This can only be called if we are not reloading GTFS data, as we can only be sure the data is finished updating after that function returns
        finally:
            if not static_reload:
                self.updating = False

    async def download_new_static_gtfs(self):
        """ Download new static GTFS data and extract them, overwriting the existing data, then refresh loaded data """
        # Make the existing data unavailable
        self.updating = True
        self.static_data = None
        # Uncomment this to fake an error
        # await asyncio.sleep(10)
        # raise RuntimeError("This is a test")
        # Download the data
        data = await http.get(self.gtfs_data_url, res_method="read")
        # Extract the data
        zip_file = ZipFile(BytesIO(data))
        zip_file.extractall("assets/gtfs")
        # Set the data to expire two weeks from now - This is now handled in the updater
        # with open("assets/gtfs/expiry.txt", "w+", encoding="utf-8") as file:
        #     file.write(str(int(time.datetime.now().timestamp) + 86400 * 14))
        # Update the loaded data
        # timetables.read_and_store_gtfs_data()
        asyncio.get_running_loop().run_in_executor(None, functools.partial(timetables.read_and_store_gtfs_data, self))
        self.static_data = timetables.init_gtfs_data()
        # self.static_data = timetables.load_gtfs_data(write=not self._DEBUG)
        logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Downloaded new GTFS data and successfully loaded it")
        # self.updating = False

    async def reload_static_gtfs(self):
        self.updating = True
        asyncio.get_running_loop().run_in_executor(None, functools.partial(timetables.read_and_store_gtfs_data, self))
        self.static_data = timetables.init_gtfs_data()
        logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Reloaded static GTFS data")

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
                raise RuntimeError("Detected that an error was raised while loading GTFS data, crashing this loop...")
            await asyncio.sleep(5)

        return message

    @commands.group(name="placeholder", invoke_without_command=True, case_insensitive=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @commands.is_owner()
    async def placeholder(self, ctx: commands.Context, action: str = None, force_redownload: str = None):
        """ Placeholder """
        if ctx.invoked_subcommand is None:
            if action == "write":
                if force_redownload == "force-redownload":
                    debug = False
                else:
                    debug = self._DEBUG
                await self.get_real_time_data(debug=debug, write=True)
            return await ctx.send("Placeholder")

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
        """ Reset error status """
        self.loader_error = None
        return await ctx.send(f"{print_current_time()} > Reset the loader error status")

    def find_stop(self, query: str) -> list[timetables.Stop]:
        """ Find a specific stop """
        return timetables.load_values_from_key(self.static_data, "stops.txt", query.lower())
        # output = []
        # query = query.lower()
        # for stop in self.static_data.stops.values():
        #     # Make the search case-insensitive
        #     if query in stop.id.lower() or query in stop.code.lower() or query in stop.name.lower():
        #         output.append(stop)
        # return output

    def find_route(self, query: str) -> list[timetables.Route]:
        """ Find a specific route """
        # This might be a bit less effective at catching routes than the previous examples, but it's possible to do it on-database this way
        return timetables.load_values_from_key(self.static_data, "routes.txt", query.lower())
        # output = []
        # query = query.lower()
        # for route in self.static_data.routes.values():
        #     # Make the search case-insensitive
        #     if query in route.id.lower() or query in route.short_name.lower() or query in route.long_name.lower():
        #         output.append(route)
        # return output

    @commands.group(name="tfi")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def tfi(self, ctx: commands.Context):
        """ Base command for TFI-related things """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @tfi.group(name="search")
    async def tfi_search(self, ctx: commands.Context):
        """ Search for a stop or route """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @tfi_search.command(name="stop")
    async def tfi_search_stop(self, ctx: commands.Context, *, query: str):
        """ Search for a specific stop """
        message = await self.wait_for_initialisation(ctx)
        stops = self.find_stop(query=query)
        output = []
        for stop in stops:
            if stop.code:
                output.append(f"`{stop.id}` (Stop code `{stop.code}`) - {stop.name}")
            else:
                output.append(f"`{stop.id}` - {stop.name}")
        output_content = ("Here are the stops found for your query:\n\n" + "\n".join(output) +
                          "\n\n*Note that if more than one stop is found for your search, then the schedule and real-time commands will need a more precise query to function.*")
        return await message.edit(content=output_content)

    @tfi_search.command(name="route")
    async def tfi_search_route(self, ctx: commands.Context, *, query: str):
        """ Search for a specific route """
        message = await self.wait_for_initialisation(ctx)
        routes = self.find_route(query=query)
        output = []
        route_types = {
            0: "Tram",
            1: "Subway",
            2: "Rail",
            3: "Bus"
        }
        for route in routes:
            output.append(f"`{route.id}` (Route {route.short_name}) - {route.long_name} ({route_types[route.route_type]})")
        output_content = ("Here are the routes found for your query:\n\n" + "\n".join(output) +
                          "\n\n*Note that if more than one route is found for your search, then the schedule command will need a more precise query to function.*")
        return await message.edit(content=output_content)

    @tfi.group(name="data", aliases=["schedule", "info", "rtpi"])
    async def tfi_schedules(self, ctx: commands.Context):
        """ Commands that deal with schedules and real-time information """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @tfi_schedules.command(name="stop")
    async def tfi_schedules_stop(self, ctx: commands.Context, *, stop_query: str):
        """ Show the next departures for a specific stop """
        message = await self.wait_for_initialisation(ctx)
        language = ctx.language2("en")
        stops = self.find_stop(stop_query)
        if len(stops) > 1:
            return await message.edit(content=f"More than one stop was found for your search query ({stop_query}).\n"
                                              f"Use `{ctx.prefix}tfi search stop` to find the specific stop ID or provide a more specific query.")
        stop = stops[0]
        await self.load_real_time_data(debug=self._DEBUG, write=True)
        schedule = timetables.RealTimeStopSchedule(self.static_data, stop.id, self.real_time_data, self.vehicle_data)
        real_stop_times = schedule.real_stop_times()
        lat1, long1 = stop.latitude, stop.longitude

        # now = time.datetime(2023, 10, 23, 5, 0, 0, 0, tz=timetables.TIMEZONE)
        now = time.datetime.now(tz=timetables.TIMEZONE)

        start_idx = 0
        for idx, stop_time in enumerate(real_stop_times):  # type: int, timetables.RealStopTime
            # Start at the first departure after right now
            if (stop_time.departure_time or stop_time.scheduled_departure_time) >= now:
                start_idx = idx
                break
        end_idx = start_idx + 7  # Leave this hardcoded for now

        output_data: list[list[str]] = [["Route", "Destination", "Schedule", "RealTime", "Distance"]]
        column_sizes = [5, 11, 8, 8, 8]  # Longest member of the column
        for stop_time in real_stop_times[start_idx:end_idx]:
            if stop_time.schedule_relationship == "CANCELED":
                departure_time = "CANCELLED"
            elif stop_time.schedule_relationship == "SKIPPED":
                departure_time = "SKIPPED"
            elif stop_time.departure_time is not None:
                departure_time = stop_time.departure_time.format("%H:%M")  # :%S
            else:
                departure_time = "--:--"  # "Unknown"

            if stop_time.scheduled_departure_time is not None:
                scheduled_departure_time = stop_time.scheduled_departure_time.format("%H:%M")  # :%S
            else:
                scheduled_departure_time = "--:--"  # "Unknown"

            _route = stop_time.route(schedule.data)
            if _route is None:
                route = "Unknown"
            else:
                route = _route.short_name

            destination = stop_time.destination(schedule.data)

            if stop_time.vehicle is not None:
                lat2, long2 = stop_time.vehicle.latitude, stop_time.vehicle.longitude
                distance_km = conworlds.distance_between_places(lat1, long1, lat2, long2, "Earth")
                if distance_km >= 1:  # > 1 km
                    distance = language.length(distance_km * 1000, precision=2).split(" | ")[0]
                else:  # < 1 km
                    distance = language.length(round(distance_km * 1000, -2), precision=0).split(" | ")[0]
                distance = distance.replace("\u200c", "")  # Remove ZWS
            else:
                distance = "-"  # "Unknown"

            # Update column_sizes if needed
            column_sizes[0] = max(column_sizes[0], len(route))
            column_sizes[1] = max(column_sizes[1], len(destination))
            column_sizes[2] = max(column_sizes[2], len(scheduled_departure_time))
            column_sizes[3] = max(column_sizes[3], len(departure_time))
            column_sizes[4] = max(column_sizes[4], len(distance))

            output_data.append([route, destination, scheduled_departure_time, departure_time, distance])

        # Calculate the last line first, in case we need more characters for the destination field
        line_length = sum(column_sizes) + len(column_sizes) - 1
        spaces = line_length - len(stop.name) - 18
        extra = 0
        # Add more spaces to destination if there's too few between stop name and current time
        if spaces < 8:
            extra = 8 - spaces
            spaces = 8
        # Example:   "Ballinacurra Close       23 Oct 2023, 18:00"
        last_line = f"{stop.name}{' ' * spaces}{now:%d %b %Y, %H:%M}```"
        column_sizes[1] += extra  # [1] is destination

        stop_code = f"Code `{stop.code}`, " if stop.code else ""
        stop_id = f"ID `{stop.id}`"
        output = f"Real-Time data for the stop {stop.name} ({stop_code}{stop_id})\n" \
                 "*Please note that the distance shown is straight-line distance and as such may not be accurate*\n" \
                 "```fix\n"
        for line in output_data:
            assert len(column_sizes) == len(line)
            line_data = []
            for i in range(len(line)):
                size = column_sizes[i]
                line_part = line[i]
                # Left-align route and destination to fixed number of spaces
                # Right-align the schedule, real-time info, and distance
                alignment = "<" if i < 2 else ">"
                line_data.append(f"{line_part:{alignment}{size}}")
            output += f"{' '.join(line_data)}\n"
        output += last_line
        return await message.edit(content=output)


async def setup(bot: bot_data.Bot):
    if bot.name == "suager":
        await bot.add_cog(University(bot))
    elif bot.name == "cobble":
        await bot.add_cog(Luas(bot))
    else:
        await bot.add_cog(Timetables(bot))
