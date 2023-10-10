import asyncio
import json

from utils import bot_data, commands, http, linenvurteat, logger, time


class Linenvurteat(commands.Cog, name="Linenvürteat"):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        self._DEBUG = True  # Only matters for updates while the command is running - on_ready() will always read from the file
        self.url = "https://api.nationaltransport.ie/gtfsr/v2/TripUpdates?format=json"
        self.headers = {
            "Cache-Control": "no-cache",
            "x-api-key": self.bot.config["gtfsr_api_token"]
        }
        self.real_time_data: linenvurteat.GTFSRData | None = None
        self.static_data: linenvurteat.GTFSData | None = None

    async def get_data_from_api(self, *, write: bool = True):
        data: bytes = await http.get(self.url, headers=self.headers, res_method="read")
        if write:
            with open(linenvurteat.real_time_filename, "wb+") as file:
                file.write(data)
            # json.dump(data, open(linenvurteat.real_time_filename, "w+"), indent=2)
        return data

    async def get_real_time_data(self, debug: bool = False, *, write: bool = True):
        """ Gets real-time data from the NTA's API or load from cache if debugging """
        if debug:
            try:
                data: str = open(linenvurteat.real_time_filename, "r").read()
            except FileNotFoundError:
                data: bytes = await self.get_data_from_api(write=write)
        else:
            data: bytes = await self.get_data_from_api(write=write)
        return json.loads(data)

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(60)  # To let the other bots load before we freeze the machine for half a minute
        if self.real_time_data is None:
            data = await self.get_real_time_data(debug=True, write=True)
            self.real_time_data = linenvurteat.load_gtfs_r_data(data)
            logger.log(self.bot.name, "data", f"{time.time()} > {self.bot.full_name} > Successfully loaded GTFS-R data")
        if self.static_data is None:
            self.static_data = linenvurteat.load_gtfs_data_from_pickle(write=True)
            logger.log(self.bot.name, "data", f"{time.time()} > {self.bot.full_name} > Successfully loaded static GTFS data")

    @commands.command(name="placeholder")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def placeholder(self, ctx: commands.Context, write: str = None):
        """ Placeholder """
        if write == "write":
            await self.get_real_time_data(self._DEBUG, write=True)
        return await ctx.send("placeholder")


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Linenvurteat(bot))
