import json

from utils import bot_data, commands, http


class Linenvurteat(commands.Cog, name="Linenvürteat"):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        self._DEBUG = True
        self.url = "https://api.nationaltransport.ie/gtfsr/v1?format=json"
        self.headers = {
            "Cache-Control": "no-cache",
            "x-api-key": self.bot.config["gtfsr_api_token"]
        }

    async def get_data(self):
        """ Gets real-time data from the NTA's API """
        if self._DEBUG:
            data: str = open("assets/gtfs/data.json", "r").read()
        else:
            data: bytes = await http.get(self.url, headers=self.headers, res_method="read")
        return json.loads(data)

    @commands.command(name="placeholder")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def placeholder(self, ctx: commands.Context, write: str = None):
        """ Placeholder """
        if write == "write":
            out = await self.get_data()
            json.dump(out, open("assets/gtfs/data.json", "w+"), indent=2)
        return await ctx.send("placeholder")


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Linenvurteat(bot))
