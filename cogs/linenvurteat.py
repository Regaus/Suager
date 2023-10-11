import json
from io import BytesIO
from zipfile import ZipFile

from utils import bot_data, commands, http, linenvurteat, logger, time


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
        if self.real_time_data is None:
            data = await self.get_real_time_data(debug=True, write=True)
            self.real_time_data = linenvurteat.load_gtfs_r_data(data)
            logger.log(self.bot.name, "data", f"{time.time()} > {self.bot.full_name} > Successfully loaded GTFS-R data")
        if self.static_data is None:
            self.static_data = linenvurteat.load_gtfs_data_from_pickle(write=not self._DEBUG)  # Don't write pickles while we're in Debug Mode
            logger.log(self.bot.name, "data", f"{time.time()} > {self.bot.full_name} > Successfully loaded static GTFS data")
        self.initialised = True

    async def download_new_static_gtfs(self):
        """ Download new static GTFS data and extract them, overwriting the existing data, then refresh loaded data """
        # Make the existing data unavailable
        self.updating = True
        self.static_data = None
        # Download the data
        data = await http.get(self.gtfs_data_url, res_method="read")
        # Extract the data
        zip_file = ZipFile(BytesIO(data))
        zip_file.extractall("assets/gtfs")
        # Update the loaded data
        self.static_data = linenvurteat.load_gtfs_data(write=not self._DEBUG)
        self.updating = False

    @commands.command(name="placeholder")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.is_owner()
    async def placeholder(self, ctx: commands.Context, write: str = None):
        """ Placeholder """
        if write == "write":
            await self.get_real_time_data(debug=self._DEBUG, write=True)
        return await ctx.send("placeholder")


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Linenvurteat(bot))
