import asyncio
import json
from io import BytesIO
from zipfile import ZipFile

from regaus import time

from utils import bot_data, commands, http, linenvurteat, logger, emotes
from utils.time import time as print_current_time


class Linenvurteat(commands.Cog, name="Linenvürteat"):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        self._DEBUG = True  # Disables sending API requests for GTFS-R and disables pickling the static data
        self.url = "https://api.nationaltransport.ie/gtfsr/v2/TripUpdates?format=json"
        self.gtfs_data_url = "https://www.transportforireland.ie/transitData/Data/GTFS_All.zip"
        self.headers = {
            "Cache-Control": "no-cache",
            "x-api-key": self.bot.config["gtfsr_api_token"]
        }
        self.real_time_data: linenvurteat.GTFSRData | None = None
        self.static_data: linenvurteat.GTFSData | None = None
        self.initialised = False
        self.updating = False
        self.loader_error: Exception | None = None

    async def get_data_from_api(self, *, write: bool = True):
        data: bytes = await http.get(self.url, headers=self.headers, res_method="read")
        if write:
            with open(linenvurteat.real_time_filename, "wb+") as file:
                file.write(data)
            # json.dump(data, open(linenvurteat.real_time_filename, "w+"), indent=2)
        return data

    async def get_real_time_data(self, debug: bool = False, *, write: bool = True):
        """ Gets real-time data from the NTA's API or load from cache if in debug mode """
        if debug:
            try:
                data: str = open(linenvurteat.real_time_filename, "r").read()
            except FileNotFoundError:
                data: bytes = await self.get_data_from_api(write=write)
        else:
            data: bytes = await self.get_data_from_api(write=write)
        return json.loads(data)

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     await asyncio.sleep(60)  # To let the other bots load before we freeze the machine for half a minute

    async def load_data(self):
        """ Load the GTFS-R and static GTFS data only when needed """
        try:
            self.loader_error = None  # Reset any previous error encountered
            self.updating = True
            if self.real_time_data is None:
                data = await self.get_real_time_data(debug=True, write=True)
                self.real_time_data = linenvurteat.load_gtfs_r_data(data)
                logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Successfully loaded GTFS-R data")
            if self.static_data is None:
                try:
                    self.static_data = linenvurteat.load_gtfs_data_from_pickle(write=not self._DEBUG)  # Don't write pickles while we're in Debug Mode
                    logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Successfully loaded static GTFS data")
                except (FileNotFoundError, RuntimeError) as e:
                    # If the static GTFS data is not available or is expired, download new data and then extract and load.
                    logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Error loading static GTFS data: {type(e).__name__}: {e}")
                    await self.download_new_static_gtfs()
            self.initialised = True
        except Exception as e:
            self.loader_error = e
            self.initialised = False
            raise e from e
        finally:
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
        # Set the data to expire two weeks from now
        with open("assets/gtfs/expiry.txt", "w+", encoding="utf-8") as file:
            file.write(str(int(time.datetime.now().timestamp) + 86400 * 14))
        # Update the loaded data
        self.static_data = linenvurteat.load_gtfs_data(write=not self._DEBUG)
        logger.log(self.bot.name, "gtfs", f"{print_current_time()} > {self.bot.full_name} > Downloaded new GTFS data and successfully loaded it")
        self.updating = False

    async def wait_for_initialisation(self, ctx: commands.Context):
        """ Initialise the data before letting the actual command execute """
        if not self.initialised and not self.updating:  # If self.updating is True, then the data is already being loaded
            await ctx.send(f"{emotes.Loading} The GTFS data has not been initialised yet. This may take a few minutes...")
            await self.load_data()
        elif self.updating:
            await ctx.send(f"{emotes.Loading} The GTFS data used by this bot is currently being updated and is therefore unavailable. This may take a few minutes...")

        # Keep the function alive until the bot is initialised and the data has been updated
        while not self.initialised or self.updating:
            if self.loader_error is not None:
                raise RuntimeError("Detected that an error was raised while loading GTFS data, crashing this loop...")
            await asyncio.sleep(5)

    @commands.command(name="placeholder")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @commands.is_owner()
    async def placeholder(self, ctx: commands.Context, action: str = None):
        """ Placeholder """
        if action == "write":
            await self.get_real_time_data(debug=self._DEBUG, write=True)
        elif action == "load":
            await self.wait_for_initialisation(ctx)
            return await ctx.send(f"{print_current_time()} > Data has been loaded")
        return await ctx.send("Placeholder")


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Linenvurteat(bot))
