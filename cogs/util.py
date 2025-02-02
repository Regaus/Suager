from __future__ import annotations

import json
import random
import re
import urllib.parse
from dataclasses import dataclass
from functools import wraps
from io import BytesIO
from typing import Any, Callable, Coroutine

import discord
import pytz
from PIL import Image, ImageDraw
from discord import app_commands
from regaus import conworlds, time as time2
from thefuzz import process

from utils import arg_parser, bases, bot_data, commands, emotes, general, http, interactions, images, languages, paginators, permissions, time


EMOJI_NAME_REGEX = re.compile(r"^:?\w+:?$")
TIME_CLASSES: list[app_commands.Choice[str]] = [
    app_commands.Choice(name="Earth", value="Earth"),
    app_commands.Choice(name="Kargadia (Kargadian calendar)", value="Kargadia"),
    app_commands.Choice(name="Kargadia (Arnattian calendar)", value="Arnattia"),
    app_commands.Choice(name="Kargadia (Larihalian calendar)", value="Larihalia"),
    app_commands.Choice(name="Zhevenerus (Kargadian calendar)", value="QevenerusKa"),
    app_commands.Choice(name="Zhevenerus (Usturian calendar)", value="QevenerusUs"),
    app_commands.Choice(name="Virkada", value="Virkada")
]


def custom_role_enabled(ctx):
    return ctx.guild is not None and ctx.guild.id in [568148147457490954, 430945139142426634, 738425418637639775, 784357864482537473, 759095477979054081]


async def duration_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """ Autocomplete for durations """
    return await interactions.duration_autocomplete(interaction, current, moderation_limit=False)


async def reminder_duration_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """ Autocomplete for reminder durations - includes the 5-year limit """
    return await interactions.duration_autocomplete(interaction, current, moderation_limit=True)


@dataclass
class Location:
    name: str
    localised_name: str
    state: str | None
    country_code: str
    lat: float
    lon: float


_ratelimit: dict[int, tuple[float, list[Location]]] = {}
_cache: dict[str, list[Location]] = {}


def _cache_geolocation_values(func: Callable[[bot_data.Bot, commands.Context | discord.Interaction, str, bool], Coroutine[Any, Any, list[Location]]]) \
        -> Callable[[bot_data.Bot, commands.Context | discord.Interaction, str, bool], Coroutine[Any, Any, list[Location]]]:
    """ Cache geolocation responses and ratelimit users to one API request per second """
    @wraps(func)
    async def wrapper(bot: bot_data.Bot, ctx: commands.Context | discord.Interaction, value: str, final: bool = False) -> list[Location]:
        if value in _cache:
            return _cache[value]
        if isinstance(ctx, commands.Context):
            user = ctx.author.id
        elif isinstance(ctx, discord.Interaction):
            user = ctx.user.id
        else:
            raise TypeError(f"Invalid context type {type(ctx).__name__}")
        now = time2.datetime.now().timestamp
        if not final and user in _ratelimit and now < _ratelimit[user][0]:  # Only ratelimit API calls if this is not the final response
            return _ratelimit[user][1]
        ret: list[Location] = await func(bot, ctx, value, final)
        _cache[value] = ret
        _ratelimit[user] = (now + 1, ret)
        return ret
    return wrapper


# TODO: Try to parse the values locally using https://bulk.openweathermap.org/sample/city.list.json.gz
@_cache_geolocation_values
async def _get_location_suggestions(bot: bot_data.Bot, ctx: commands.Context | discord.Interaction, current: str, _final: bool = False) -> list[Location]:
    """ Find places that have the given name """
    language = bot.language(ctx)
    lang = "en" if language.data("_conlang") else language.string("_short")
    token = bot.config["weather_api_token"]
    params = {"q": current, "limit": 5, "appid": token}
    locations_res: str = await http.get(f"https://api.openweathermap.org/geo/1.0/direct?" + urllib.parse.urlencode(params), res_method="text")
    locations = json.loads(locations_res)
    results: list[Location] = []
    for location in locations:
        value = location["name"]
        if "local_names" in location:
            name = location["local_names"].get(lang, value)
        else:
            name = value
        state = location.get("state")
        country_code = location.get("country")
        lat, lon = location["lat"], location["lon"]
        results.append(Location(value, name, state, country_code, lat, lon))
    return results


class Utility(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        self.sticker_packs: list[discord.StickerPack] | None = None

    @commands.hybrid_command(name="time")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.describe(user="(Optional) The user whose time to check")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def current_time(self, ctx: commands.Context, *, user: discord.User = None):
        """ Look up your or someone else's local time """
        await ctx.defer(ephemeral=True)
        language = self.bot.language(ctx)
        user = user or ctx.author
        if self.bot.name == "cobble":
            place = conworlds.Place("Virsetgar")
            now = time2.datetime.now(place.tz, time2.Kargadia)
            utc_name = language.string("util_time_utc_kargadia")
        else:
            now = time2.datetime.now()
            utc_name = language.string("util_time_utc")
        embed = discord.Embed(colour=general.random_colour(), title=language.string("util_time_current"))
        utc_time = language.time(now, short=0, dow=True, seconds=True, tz=True)
        own_time = language.time(now, short=0, dow=True, seconds=True, tz=True, uid=ctx.author.id)
        user_time = language.time(now, short=0, dow=True, seconds=True, tz=True, uid=user.id)
        embed.add_field(name=utc_name, value=utc_time, inline=False)
        embed.add_field(name=language.string("util_time_your"), value=own_time, inline=False)
        if user.id != ctx.author.id:
            embed.add_field(name=language.string("util_time_user", user=general.username(user)), value=user_time, inline=False)
        return await ctx.send(embed=embed)

    @commands.hybrid_command(name="base", aliases=["bases", "bc"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.choices(caps=[
        app_commands.Choice(name="Capitalise letters", value="caps"),
        app_commands.Choice(name="Don't capitalise letters", value=""),
    ])
    @app_commands.describe(
        base_from="The base from which to convert the number",
        base_to="The base to which to convert the number",
        number="The number to convert between bases",
        float_precision="For non-whole numbers, the precision after the dot. Defaults to 5",
        caps="Whether or not to capitalise letters for bases higher than 10 (e.g. \"1AA\" instead of \"1aa\")"
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    # async def base_conversions(self, ctx: commands.Context, number: str, conversion: str, base: int, caps: bool = False):
    async def base_conversions(self, ctx: commands.Context, base_from: int, base_to: int, number: str, float_precision: int = 5, caps: str = ""):
        """ Convert numbers between different number bases

        The float precision argument controls how many places after the dot will be shown
        Write `"caps"` after the number if you want letters outputted in uppercase (ie. "1AA" instead of "1aa" for bases 11 and up)
        Usage example: `//base 10 16 420.69 5 caps` will convert 420.69 from decimal to hexadecimal with precision of 5 places (420.69 -> 1A4.B0A3D)

        Note: The conversions may not always be precise, and numbers closer to the end may get lost """
        await ctx.defer(ephemeral=True)
        if not (2 <= base_from <= 36):
            return await ctx.send("The base value must be between 2 and 36...")
        if not (2 <= base_to <= 36):
            return await ctx.send("The base value must be between 2 and 36...")
        if not (0 <= float_precision <= 100):
            return await ctx.send("The precision must be between 0 and 100...")
        try:
            float_conv = "." in number
            if base_from == 10:
                mid = float(number) if float_conv else int(number, base=10)
            else:
                mid = bases.from_base_float(number, base_from, 160) if float_conv else bases.from_base(number, base_from)
            caps = caps.lower() == "caps"
            end = bases.to_base_float(mid, base_to, float_precision, caps) if float_conv else bases.to_base(mid, base_to, caps)
            return await ctx.send(f"{general.username(ctx.author)}: {number} (base {base_from}) -> {end} (base {base_to})")
        except ValueError:
            return await ctx.send(f"{general.username(ctx.author)}, this number is invalid.")
        except OverflowError:
            return await ctx.send(f"{general.username(ctx.author)}, the number specified is too large to convert to a proper value.")

    @commands.hybrid_group(name="timezones", aliases=["timezone", "settimezone", "settz", "tz"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def timezones(self, ctx: commands.Context):
        """ Manage timezones """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @timezones.command(name="list")
    async def timezones_list(self, ctx: commands.Context):
        """ See the list of all available timezones """
        await ctx.defer(ephemeral=True)
        language = ctx.language()
        paginator = paginators.LinePaginator(max_lines=20, max_size=1000)
        paginator.add_lines(pytz.all_timezones)
        embed = discord.Embed(title=language.string("util_time_tz_list"), colour=general.random_colour())
        interface = paginators.PaginatorEmbedInterface(self.bot, paginator, owner=ctx.author, embed=embed)
        return await interface.send_to(ctx)

    async def country_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """ Autocomplete for the timezone country """
        language = self.bot.language(interaction)
        results: list[tuple[str, str, int]] = []
        countries = pytz.country_timezones.keys()
        current = current.lower()
        for country in countries:
            country_name = language.string(f"country_{country.lower()}")
            ratios = (process.default_scorer(current, country.lower()), process.default_scorer(current, country_name.lower()))
            results.append((country, country_name, max(ratios)))
        results.sort(key=lambda x: x[2], reverse=True)
        return [app_commands.Choice(name=full_name, value=code) for code, full_name, _ in results[:25]]

    @timezones.command(name="country")
    @app_commands.autocomplete(country=country_autocomplete)
    @app_commands.describe(country="The name of the country for which to list timezones")
    async def timezones_country(self, ctx: commands.Context, country: str):
        """ List all timezones that exist in the specified country """
        await ctx.defer(ephemeral=True)
        language = ctx.language()

        def human_offset(_zone):
            return time2.format_offset(offset(_zone))

        def offset(_zone):
            return pytz.timezone(_zone).utcoffset(now)

        actual_country = None
        _country = country.lower()
        for country_key in pytz.country_timezones.keys():
            country_name = language.string(f"country_{country_key.lower()}").lower()
            if country_name == _country or country_key.lower() == _country:
                actual_country = country_key.lower()
                break
        if actual_country is None:
            return await ctx.send(language.string("util_time_tz_country_none", country=country))

        try:
            country_name = language.string(f"country_{actual_country}")
            now = time.now2()
            timezones = "\n".join([f"`{human_offset(zone)} {zone}`" for zone in sorted(pytz.country_timezones[actual_country.upper()], key=offset, reverse=True)])
            return await ctx.send(language.string("util_time_tz_country", country=country_name, timezones=timezones))
        except KeyError:
            return await ctx.send(language.string("util_time_tz_country_none", country=country))

    # There's no reason for this to be outside. It is just there to stop discord.py from thinking that the autocomplete is "not a coroutine" (even though it is)
    @staticmethod
    def timezone_suggestions(current: str) -> list[tuple[str, int]]:
        results: list[tuple[str, int]] = []
        for timezone in pytz.all_timezones:
            results.append((timezone, process.default_scorer(current, timezone)))
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    async def timezone_autocomplete(self, _interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """ Autocomplete for the timezone name """
        results = self.timezone_suggestions(current)
        return [app_commands.Choice(name=result, value=result) for result, _ in results[:25]]

    @timezones.command(name="set")
    @app_commands.autocomplete(timezone=timezone_autocomplete)
    @app_commands.describe(timezone="The name of your timezone")
    async def timezones_set(self, ctx: commands.Context, timezone: str):
        """ Set your timezone """
        await ctx.defer(ephemeral=True)
        language = ctx.language()
        try:
            data = self.bot.db.fetchrow("SELECT * FROM timezones WHERE uid=?", (ctx.author.id,))
            _tz = pytz.timezone(timezone)
            if data:
                self.bot.db.execute("UPDATE timezones SET tz=? WHERE uid=?", (str(_tz), ctx.author.id))
            else:
                self.bot.db.execute("INSERT INTO timezones VALUES (?, ?)", (ctx.author.id, str(_tz)))
            return await ctx.send(language.string("util_time_tz", tz=str(_tz)))
        except pytz.UnknownTimeZoneError:
            return await ctx.send(language.string("util_time_tz_error", tz=timezone))

    @timezones.command(name="reset", aliases=["unset"])
    async def timezones_reset(self, ctx: commands.Context):
        """ Reset your timezone """
        await ctx.defer(ephemeral=True)
        language = ctx.language()
        self.bot.db.execute("DELETE FROM timezones WHERE uid=?", (ctx.author.id,))
        return await ctx.send(language.string("util_time_tz_reset"))

    def _parse_time(self, ctx: commands.Context, _date: str, _time: str | None, _time_class: str = "Earth"):
        tz = self.bot.timezone(ctx.author.id, _time_class)
        _y, _m, _d = _date.split("-")
        y, m, d = int(_y), int(_m), int(_d)
        date_part = time2.date(y, m, d, getattr(time2, _time_class))  # The time class should be validated by the command
        if _time is not None:
            _h, _m, *_s = _time.split(":")
            h, m, s = int(_h), int(_m), int(_s[0]) if _s else 0
            time_part = time2.time(h, m, s, 0, time2.utc)
        else:
            time_part = time2.time()
        datetime = time2.datetime.combine(date_part, time_part, time2.utc)
        datetime2 = datetime.as_timezone(tz)
        return datetime.replace(tz=datetime2.tzinfo)

    async def time_since_command(self, ctx: commands.Context, _date: str | None, _time: str | None, _time_class: str | None):
        """ Wrapper for the timesince command for Suager and CobbleBot """
        await ctx.defer(ephemeral=True)
        language = ctx.language()
        try:
            time_class = getattr(time2, _time_class)
        except AttributeError:
            return await ctx.send(language.string("util_time_class_not_found"))
        else:
            if not issubclass(time_class, time2.Earth):
                return await ctx.send(language.string("util_time_class_invalid"))
        try:
            now = time2.datetime.now(time_class=time_class)
            date = time2.datetime(now.year, 1, 1, time_class=time_class)
            tz = self.bot.timezone(ctx.author.id, _time_class)
            if _date is None and _time_class in ("Earth", "Kargadia"):
                def dt(_month, _day):
                    return time2.datetime(now.year, _month, _day, tz=tz, time_class=time_class)
                if _time_class == "Earth":
                    dates = [dt(1, 27), dt(3, 17), dt(4, 1), dt(4, 17), dt(5, 13), dt(8, 8), dt(10, 31), dt(11, 19), dt(12, 5),
                             time2.datetime(now.year + 1, 1, 1, tz=tz, time_class=time_class)]
                elif _time_class == "Kargadia":
                    dates = [dt(1, 6), dt(3, 12), dt(4, 8), dt(7, 9), dt(8, 11), dt(11, 2), dt(14, 1), dt(16, 5),
                             time2.datetime(now.year + 1, 1, 1, tz=tz, time_class=time_class)]
                else:
                    raise ValueError(f"No predefined dates are available for time class {_time_class}")
                for _date in dates:
                    if now < _date:
                        date = _date
                        break
            else:
                try:
                    date = self._parse_time(ctx, _date, _time, _time_class)
                except ValueError:
                    return await ctx.send(language.string("util_timesince_format"))
            difference = language.delta_dt(date, accuracy=7, brief=False, affix=True)
            current_time = language.time(now, short=0, dow=False, seconds=True, tz=True, uid=ctx.author.id)
            specified_time = language.time(date, short=0, dow=False, seconds=True, tz=True, uid=ctx.author.id)
            return await ctx.send(language.string("util_timesince", now=current_time, then=specified_time, delta=difference))
        except Exception as e:
            return await ctx.send(language.string("util_timesince_error", err=f"{type(e).__name__}: {str(e)}"))

    @commands.hybrid_command(name="timesince", aliases=["timeuntil"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.rename(_date="date", _time="time")
    @app_commands.describe(_date="The date to compare (Format: YYYY-MM-DD)", _time="The time to compare (Format: HH:MM:SS)")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def time_since(self, ctx: commands.Context, _date: str = None, _time: str = None):
        """ Calculate how long it has been since a given time

        If you don't specify any time, it will simply default to an arbitrary date within the near future """
        return await self.time_since_command(ctx, _date, _time, "Earth")

    @staticmethod
    async def time_diff(ctx: commands.Context, string: str, multiplier: int, _time_class: str = "Earth"):
        await ctx.defer(ephemeral=True)
        language = ctx.language()
        try:
            time_class = getattr(time2, _time_class)
        except AttributeError:
            return await ctx.send(language.string("util_time_class_not_found"))
        else:
            if not issubclass(time_class, time2.Earth):
                return await ctx.send(language.string("util_time_class_invalid"))
        try:
            # _delta = time.interpret_time(string) * multiplier
            # delta = time2.relativedelta(years=_delta.years, months=_delta.months, days=_delta.days, hours=_delta.hours, minutes=_delta.minutes, seconds=_delta.seconds)
            delta = time.interpret_time(string, time2.relativedelta, time_class) * multiplier
            now = time2.datetime.now(time_class=time_class)
            then = now + delta  # type: ignore
        except (ValueError, OverflowError) as e:
            return await ctx.send(language.string("util_timediff_error", err=f"{type(e).__name__}: {str(e)}"))
        difference = language.delta_rd(delta, accuracy=7, brief=False, affix=True)
        time_now = language.time(now, short=0, dow=False, seconds=True, tz=True, uid=ctx.author.id)
        time_then = language.time(then, short=0, dow=False, seconds=True, tz=True, uid=ctx.author.id)
        return await ctx.send(language.string("util_timediff", now=time_now, delta=difference, then=time_then))

    @commands.hybrid_command(name="timein")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.autocomplete(time_period=duration_autocomplete)
    @app_commands.describe(time_period="The duration of time to look in the future (Format: 1y1mo1d1h1m1s)")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def time_in(self, ctx: commands.Context, time_period: str):
        """ Check what time it will be in a specified period """
        return await self.time_diff(ctx, time_period, 1)

    @commands.hybrid_command(name="timeago")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.autocomplete(time_period=duration_autocomplete)
    @app_commands.describe(time_period="The duration of time to look in the past (Format: 1y1mo1d1h1m1s)")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def time_ago(self, ctx: commands.Context, time_period: str):
        """ Check what time it was a specified period ago """
        return await self.time_diff(ctx, time_period, -1)

    async def _parse_place_name(self, ctx: commands.Context, place_name: str) -> tuple[float, float] | None:
        """ Parse place name and return a tuple of (lat, long) coordinates """
        if "\u2060" in place_name:  # Zero-width no-break space - Sentinel character for autocomplete results (which already return a position)
            lat, lon = place_name.split("\u2060,")
            return float(lat), float(lon)
        locations = await _get_location_suggestions(self.bot, ctx, place_name, True)
        if locations:
            location = locations[0]
            return location.lat, location.lon
        return None

    async def place_name_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """ Autocomplete for weather place names """
        if not current:
            return []  # Don't send API requests for an empty place name
        language = self.bot.language(interaction)
        locations = await _get_location_suggestions(self.bot, interaction, current, False)
        results: list[app_commands.Choice[str]] = []
        for location in locations:
            country = language.string(f"country_{location.country_code.lower()}")
            state = f", {location.state}" if location.state else ""
            name = f"{location.localised_name}{state}, {country}"
            value = f"{location.lat}\u2060,{location.lon}"
            results.append(app_commands.Choice(name=name, value=value))
        return results

    @staticmethod
    def _flag_emoji(country_code: str) -> str:
        out = ""
        for char in country_code:
            out += chr(ord(char) + 127397)
        return out

    @commands.hybrid_command(name="weather")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.autocomplete(place=place_name_autocomplete)
    @app_commands.describe(place="The name of the place for which to check the weather")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def weather(self, ctx: commands.Context, *, place: str):
        """ Check the current weather in a place """
        language = self.bot.language(ctx)
        lang = "en" if language.data("_conlang") else language.string("_short")
        async with ctx.typing(ephemeral=True):
            coords = await self._parse_place_name(ctx, place)
            if not coords:
                return await ctx.send(language.string("util_weather_error_not_found", place=place))
            lat, lon = coords
            token = self.bot.config["weather_api_token"]
            params = {"lat": lat, "lon": lon, "appid": token, "units": "metric", "lang": lang}
            res = await http.get(f"https://api.openweathermap.org/data/2.5/weather?" + urllib.parse.urlencode(params), res_method="text")
            data = json.loads(res)
            if data["cod"] != 200:
                return await ctx.send(language.string("util_weather_error", place=place, err=f"{data["cod"]}: {data["message"]}"))
            embed = discord.Embed(colour=general.random_colour())
            place_name = data.get("name", language.string("generic_unknown"))
            country_code = data["sys"].get("country", "")
            if country_code:
                country_name = language.string(f"country_{country_code.lower()}")
                flag_emoji = self._flag_emoji(country_code) + " "
            else:
                country_name = language.string("util_weather_unknown_country")
                flag_emoji = ""
            embed.title = language.string("util_weather_title", place=place_name, country=country_name, emote=flag_emoji)
            tz_offset = data.get("timezone", 0)
            timezone = time2.timezone(time2.datetime_timedelta(seconds=tz_offset))
            local_time = time2.datetime.now(timezone)
            local_time_str = language.time(local_time, short=1, dow=False, seconds=False, tz=False)
            embed.description = language.string("util_weather_desc", time=local_time_str)
            weather = data["weather"][0]
            weather_icon = weather["icon"]
            embed.set_thumbnail(url=f"https://openweathermap.org/img/wn/{weather_icon}@2x.png")
            embed.add_field(name=language.string("util_weather_weather"), value=weather["description"].capitalize(), inline=False)
            main_data = data["main"]
            embed.add_field(name=language.string("util_weather_temperature"), value=general.bold(language.temperature(main_data["temp"], precision=1)), inline=True)
            if "feels_like" in main_data:
                embed.add_field(name=language.string("util_weather_temperature2"), value=language.temperature(main_data["feels_like"], precision=1), inline=True)
            pressure = main_data.get("grnd_level", main_data["pressure"])
            embed.add_field(name=language.string("util_weather_pressure"), value=general.bold(f"{language.number(pressure)} hPa"), inline=False)
            embed.add_field(name=language.string("util_weather_humidity"), value=general.bold(language.number(main_data["humidity"] / 100, precision=0, percentage=True)), inline=False)
            if "visibility" in data:
                embed.add_field(name=language.string("util_weather_visibility"), value=general.bold(language.length(data["visibility"], precision=1)), inline=False)
            wind_data = data["wind"]
            wind_speed = language.speed(wind_data["speed"] * 3.6, precision=2)
            wind_direction = wind_data["deg"] if "deg" in wind_data else language.string("generic_unknown")
            wind_gusts = language.speed(wind_data["gust"] * 3.6, precision=2) if "gust" in wind_data else language.string("generic_unknown")
            embed.add_field(name=language.string("util_weather_wind"), inline=False,
                            value=language.string("util_weather_wind_data", wind_speed=wind_speed, wind_gusts=wind_gusts, wind_direction=wind_direction))
            embed.add_field(name=language.string("util_weather_clouds"), value=general.bold(language.number(data["clouds"]["all"] / 100, precision=0, percentage=True)), inline=False)
            if "rain" in data:
                embed.add_field(name=language.string("util_weather_rainfall"), value=language.string("util_weather_precipitation_unit", value=data["rain"]["1h"]), inline=False)
            if "snow" in data:
                embed.add_field(name=language.string("util_weather_snowfall"), value=language.string("util_weather_precipitation_unit", value=data["snow"]["1h"]), inline=False)
            sunrise = data["sys"]["sunrise"]
            if sunrise != 0:
                sunrise_time = time2.datetime.from_timestamp(sunrise, timezone)
                sunrise_time_str = language.time2(sunrise_time, seconds=False, tz=False)
                sunrise_delta_str = language.delta_dt(sunrise_time, source=local_time, accuracy=2, brief=True, affix=True)
                embed.add_field(name=language.string("util_weather_sunrise"), value=f"**{sunrise_time_str}**\n{sunrise_delta_str}", inline=True)
            sunset = data["sys"]["sunset"]
            if sunset != 0:
                sunset_time = time2.datetime.from_timestamp(sunset, timezone)
                sunset_time_str = language.time2(sunset_time, seconds=False, tz=False)
                sunset_delta_str = language.delta_dt(sunset_time, source=local_time, accuracy=2, brief=True, affix=True)
                embed.add_field(name=language.string("util_weather_sunset"), value=f"**{sunset_time_str}**\n{sunset_delta_str}", inline=True)
            if "coord" in data:
                lat, long = data["coord"]["lat"], data["coord"]["lon"]
                n, e = "N" if lat >= 0 else "S", "E" if long >= 0 else "W"
                if lat < 0:
                    lat *= -1
                if long < 0:
                    long *= -1
                embed.add_field(name=language.string("util_weather_location"), value=f"{language.number(lat, precision=3)}°{n}, {language.number(long, precision=3)}°{e}", inline=False)
            embed.timestamp = local_time.to_datetime()
            return await ctx.send(embed=embed)

    @commands.hybrid_command(name="colour", aliases=["color"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.describe(colour="The hex code of the colour. Type \"random\" for a random colour.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def colour(self, ctx: commands.Context, *, colour: str = "random"):
        """ Information on a colour """
        async with ctx.typing(ephemeral=True):
            language = self.bot.language(ctx)
            if colour.endswith(" -i"):
                colour = colour[:-3]
                image_only = True
            else:
                image_only = False

            if colour.lower() == "random":
                int_6 = random.randint(0, 0xffffff)
                hex_6 = hex(int_6)[2:]  # Remove the 0x prefix
                rgb_255 = images.colour_int_to_tuple(int_6)
            else:
                try:
                    hex_6 = colour
                    int_6 = images.colour_hex_to_int(colour)
                    rgb_255 = images.colour_int_to_tuple(int_6)
                except images.InvalidLength as e:
                    return await ctx.send(language.string("images_colour_invalid_value", value=e.value, length=e.length), ephemeral=True)
                except images.InvalidColour as e:
                    return await ctx.send(language.string("images_colour_invalid", value=e.value, err=e.error), ephemeral=True)

            if image_only:
                image1 = Image.new(mode="RGBA", size=(512, 512), color=rgb_255)
                bio1 = BytesIO()
                image1.save(bio1, "PNG")
                bio1.seek(0)
                return await ctx.send(file=discord.File(bio1, "colour.png"))

            embed = discord.Embed(colour=int_6)
            rgb_1 = tuple(round(value / 255, 4) for value in rgb_255)
            red, green, blue = rgb_255
            brightness = images.calculate_brightness(red, green, blue)
            embed.add_field(name=language.string("images_colour_hex"), value="#" + hex_6, inline=False)
            embed.add_field(name=language.string("images_colour_int"), value=str(int_6), inline=False)
            embed.add_field(name=language.string("images_colour_rgb") + " (0-255)", value=str(rgb_255), inline=False)
            embed.add_field(name=language.string("images_colour_rgb") + " (0-1)", value=str(rgb_1), inline=False)
            embed.add_field(name=language.string("images_colour_brightness"), value=language.number(brightness, precision=4), inline=False)
            embed.add_field(name=language.string("images_colour_font"), inline=False, value="#000000" if brightness >= 128 else "#ffffff")
            image1 = Image.new(mode="RGBA", size=(512, 512), color=rgb_255)
            bio1 = BytesIO()
            image1.save(bio1, "PNG")
            bio1.seek(0)
            embed.set_thumbnail(url="attachment://colour.png")
            rows = 2  # 4
            size = 256
            font = images.load_font("jetbrains_mono", size=48)
            image2 = Image.new(mode="RGBA", size=(size * 11, size * rows), color=(0, 0, 0, 1))
            up_red, up_green, up_blue = (255 - red) / 10, (255 - green) / 10, (255 - blue) / 10
            down_red, down_green, down_blue = red / 10, green / 10, blue / 10

            def _hex(value: int):
                return f"{value:02X}"

            for i in range(11):
                start2a = (size * i, 0)
                start2b = (size * i, size)
                red2a, green2a, blue2a = int(red + up_red * i), int(green + up_green * i), int(blue + up_blue * i)
                red2b, green2b, blue2b = int(red - down_red * i), int(green - down_green * i), int(blue - down_blue * i)
                image2a = Image.new(mode="RGBA", size=(size, size), color=(red2a, green2a, blue2a, 255))
                image2b = Image.new(mode="RGBA", size=(size, size), color=(red2b, green2b, blue2b, 255))
                draw2a = ImageDraw.Draw(image2a)
                draw2b = ImageDraw.Draw(image2b)
                hex2a = "#" + _hex(red2a) + _hex(green2a) + _hex(blue2a)
                hex2b = "#" + _hex(red2b) + _hex(green2b) + _hex(blue2b)
                sum2a = images.calculate_brightness(red2a, green2a, blue2a)
                sum2b = images.calculate_brightness(red2b, green2b, blue2b)
                fill2a = (0, 0, 0, 255) if sum2a >= 128 else (255, 255, 255, 255)
                fill2b = (0, 0, 0, 255) if sum2b >= 128 else (255, 255, 255, 255)
                draw2a.text((size // 2, size), hex2a, font=font, fill=fill2a, anchor="md")
                draw2b.text((size // 2, size), hex2b, font=font, fill=fill2b, anchor="md")
                image2.paste(image2a, start2a)
                image2.paste(image2b, start2b)

            bio2 = BytesIO()
            image2.save(bio2, "PNG")
            bio2.seek(0)
            embed.set_image(url="attachment://gradient.png")
            return await ctx.send(embed=embed, files=[discord.File(bio1, "colour.png"), discord.File(bio2, "gradient.png")])

    @commands.hybrid_command(name="roll")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.describe(num1="The lower number", num2="The higher number")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def roll(self, ctx: commands.Context, num1: int = 6, num2: int = 1):
        """ Rolls a number between given range """
        await ctx.defer(ephemeral=True)
        language = self.bot.language(ctx)
        if num1 > num2:
            v1, v2 = [num2, num1]
        else:
            v1, v2 = [num1, num2]
        r = random.randint(v1, v2)
        n1, n2, no = language.number(v1), language.number(v2), language.number(r)
        return await ctx.send(language.string("fun_roll", name=general.username(ctx.author), num1=n1, num2=n2, output=no))

    @commands.hybrid_command(name="reverse")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.describe(text="The text you want to reverse")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def reverse_text(self, ctx: commands.Context, *, text: str):
        """ Reverses text """
        await ctx.defer(ephemeral=True)  # If the user wants a permanent message, they can copy the reversed text themselves
        reverse = text[::-1].replace("@", "@\u200B").replace("&", "&\u200B")
        return await ctx.send(f"🔁 {general.username(ctx.author)}:\n{reverse}")

    @commands.command(name="dm")
    @commands.is_owner()
    async def dm(self, ctx: commands.Context, user_id: int, *, message: str):
        """ DM a user """
        try:
            await ctx.message.delete()
        except Exception as e:
            await ctx.send(f"Message deletion failed: `{type(e).__name__}: {e}`", delete_after=5)
        user = self.bot.get_user(user_id)
        if not user:
            return await ctx.send(f"Could not find a user with ID {user_id}")
        try:
            await user.send(message)
            return await ctx.send(f"✉ Sent DM to {user}", delete_after=5)
        except discord.Forbidden:
            return await ctx.send(f"Failed to send DM - the user might have blocked DMs, or be a bot.")

    @commands.hybrid_command(name="tell")
    @permissions.has_permissions(manage_messages=True)
    @app_commands.default_permissions(manage_messages=True)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.describe(channel="The channel to send the message in", message="The message to send")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def tell(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str):
        """ Say something to a channel """
        await ctx.defer(ephemeral=True)
        language = self.bot.language(ctx)
        if not ctx.interaction:  # Slash commands wouldn't have a message to delete
            try:
                await ctx.message.delete()
            except Exception as e:
                await ctx.send(language.string("fun_say_delete_fail", err=f"{type(e).__name__}: {str(e)}"), delete_after=5)
        if channel.guild != ctx.guild:
            return await ctx.send(language.string("fun_tell_guilds"))
        try:
            await channel.send(message)
        except Exception as e:
            return await ctx.send(language.string("fun_tell_fail", err=f"{type(e).__name__}: {str(e)}"))
        return await ctx.send(language.string("fun_tell_success", channel=channel.mention), delete_after=5)

    @commands.command(name="atell")
    @commands.is_owner()
    async def admin_tell(self, ctx: commands.Context, channel_id: int, *, message: str):
        """ Say something to a channel """
        channel = self.bot.get_channel(channel_id)
        try:
            await ctx.message.delete()
        except Exception as e:
            await ctx.send(f"Message deletion failed: `{type(e).__name__}: {e}`", delete_after=5)
        try:
            await channel.send(message)
        except Exception as e:
            return await ctx.send(f"{emotes.Deny} Failed to send the message: `{type(e).__name__}: {e}`")
        return await ctx.send(f"{emotes.Allow} Successfully sent the message to {channel.mention}", delete_after=5)

    @commands.hybrid_command(name="vote")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.describe(text="What you want to vote on")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def vote(self, ctx: commands.Context, *, text: str):
        """ Start a simple vote """
        await ctx.defer(ephemeral=False)
        language = self.bot.language(ctx)
        message = await ctx.send(language.string("fun_vote", name=general.username(ctx.author), text=text))
        await message.add_reaction(emotes.Allow)
        await message.add_reaction(emotes.Meh)
        await message.add_reaction(emotes.Deny)

    @commands.hybrid_command(name="avatar", aliases=["av"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.describe(user="The user whose avatar you want to see")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def avatar(self, ctx: commands.Context, *, user: discord.User = None):
        """ Get someone's avatar """
        await ctx.defer(ephemeral=True)
        user: discord.User | discord.Member = user or ctx.author
        return await ctx.send(self.bot.language(ctx).string("discord_avatar", user=general.username(user), avatar=str(user.display_avatar.replace(size=4096, static_format='png'))))

    @commands.command(name="avatar2", aliases=["av2", "a2", "ay"])
    @commands.is_owner()
    async def avatar_fetch(self, ctx: commands.Context, *users: int):
        """ Fetch and yoink avatars """
        for user in users:
            try:
                await ctx.send(str((await self.bot.fetch_user(user)).display_avatar.replace(size=4096, static_format="png")))
            except Exception as e:
                await ctx.send(f"{user} -> {type(e).__name__}: {e}")

    @commands.command(name="avatar3", aliases=["av3", "a3", "ag"])
    @commands.is_owner()
    async def avatar_guild(self, ctx: commands.Context, user_id: int, guild_id: int):
        """ Try to get a member's guild avatar """
        guild: discord.Guild = self.bot.get_guild(guild_id)
        if not guild:
            return await ctx.send(f"Guild {guild_id} was not found...")
        member: discord.Member = guild.get_member(user_id)
        if not member:
            return await ctx.send(f"Member {user_id} is not in {guild.name}...")
        avatar = member.guild_avatar
        if not avatar:
            return await ctx.send(f"{member} does not have a guild avatar in {guild.name}...")
        return await ctx.send(f"**{member}**'s avatar in **{guild.name}**:\n{avatar.replace(size=4096, static_format='png')}")

    @commands.hybrid_group(name="role", invoke_without_command=True, fallback="info")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.describe(role="The role for which to show details")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def role_info(self, ctx: commands.Context, *, role: discord.Role):
        """ Information on roles in the current server """
        if ctx.invoked_subcommand is None:
            await ctx.defer(ephemeral=True)
            language = self.bot.language(ctx)
            embed = discord.Embed(colour=role.colour)
            embed.title = language.string("discord_role_about", role=role.name)
            if role.icon:
                embed.set_thumbnail(url=str(role.icon.replace(size=1024, static_format="png")))
            elif ctx.guild.icon:
                embed.set_thumbnail(url=str(ctx.guild.icon.replace(size=1024, static_format="png")))
            embed.add_field(name=language.string("discord_role_name"), value=role.name, inline=True)
            embed.add_field(name=language.string("discord_role_id"), value=str(role.id), inline=True)
            embed.add_field(name=language.string("discord_members"), value=language.number(len(role.members)), inline=True)
            if role.unicode_emoji:
                embed.add_field(name=language.string("discord_role_emoji"), value=role.unicode_emoji, inline=True)
            embed.add_field(name=language.string("discord_role_colour"), value=str(role.colour), inline=True)
            embed.add_field(name=language.string("discord_role_mentionable"), value=language.yes(role.mentionable), inline=True)
            embed.add_field(name=language.string("discord_role_hoisted"), value=language.yes(role.hoist), inline=True)
            embed.add_field(name=language.string("discord_role_position"), value=language.number(role.position), inline=True)
            created_time = language.time(role.created_at, short=0, dow=False, seconds=False, tz=True, at=True, uid=ctx.author.id)
            created_delta = language.delta_dt(role.created_at, accuracy=2, brief=False, affix=True)
            embed.add_field(name=language.string("discord_created_at"), value=f"{created_time}\n{created_delta}", inline=True)
            embed.add_field(name=language.string("discord_role_default"), value=language.yes(role.is_default()), inline=True)
            embed.add_field(name=language.string("discord_role_managed"), value=language.yes(role.managed), inline=True)
            perms = []
            for permission, value in role.permissions:
                if value:
                    perms.append(language.data2("generic_permissions", permission, permission))
            embed.add_field(name=language.string("discord_role_permissions"), value="\n".join(perms), inline=False)
            return await ctx.send(embed=embed)

    @role_info.command(name="list")
    async def role_list(self, ctx: commands.Context):
        """ List the roles in the current server """
        await ctx.defer(ephemeral=True)
        language = ctx.language()
        paginator = paginators.LinePaginator(max_lines=20, max_size=1000)
        for i, role in enumerate(ctx.guild.roles[::-1], start=1):
            paginator.add_line(f"{i:02d}) {role.mention} ({role.id}) - {language.plural(len(role.members), "discord_word_member")}")
        embed = discord.Embed(title=language.string("discord_role_list", server=ctx.guild.name), colour=general.random_colour())
        interface = paginators.PaginatorEmbedInterface(self.bot, paginator, owner=ctx.author, embed=embed)
        return await interface.send_to(ctx)

    @role_info.command(name="members")
    @app_commands.describe(role="The role whose members to list")
    async def role_members(self, ctx: commands.Context, *, role: discord.Role):
        """ List members who have a certain role """
        await ctx.defer(ephemeral=True)
        language = self.bot.language(ctx)
        if not role.members:
            return await ctx.send(language.string("discord_role_members_none", role=role.name))
        members = sorted(role.members, key=lambda m: m.display_name.lower())  # Sort members by name
        paginator = paginators.LinePaginator(max_lines=20, max_size=1000)
        for i, member in enumerate(members, start=1):
            paginator.add_line(f"**{i:02d})** {member.mention} ({member})")
        embed = discord.Embed(title=language.string("discord_role_members", role=role.name), colour=general.random_colour())
        interface = paginators.PaginatorEmbedInterface(self.bot, paginator, owner=ctx.author, embed=embed)
        return await interface.send_to(ctx)

    @commands.hybrid_command(name="joinedat", aliases=["joindate", "jointime"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.describe(user="The member whose join time to check")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def joined_time(self, ctx: commands.Context, *, user: discord.Member = None):
        """ Check when someone joined the server """
        await ctx.defer(ephemeral=True)
        user = user or ctx.author
        language = self.bot.language(ctx)
        joined_time = language.time(user.joined_at, short=0, dow=False, seconds=False, tz=True, at=True, uid=ctx.author.id)
        return await ctx.send(language.string("discord_command_joined_at", user=general.username(user), server=ctx.guild.name, time=joined_time))

    @commands.hybrid_command(name="createdat")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.describe(user="The user whose account creation date to check")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def created_time(self, ctx: commands.Context, *, user: discord.User = None):
        """ Check when someone created their account """
        await ctx.defer(ephemeral=True)
        user = user or ctx.author
        language = self.bot.language(ctx)
        created_time = language.time(user.created_at, short=0, dow=False, seconds=False, tz=True, at=True, uid=ctx.author.id)
        return await ctx.send(language.string("discord_command_created_at", user=general.username(user), time=created_time))

    @staticmethod
    async def _user_command(ctx: commands.Context, user: discord.Member | discord.User = None):
        """ General command for checking user data """
        user = user or ctx.author
        member: discord.Member | None = ctx.guild.get_member(user.id)  # Try to find the user in the current guild
        language = ctx.language()
        embed = discord.Embed(title=language.string("discord_user_about", name=general.username(user)), colour=general.random_colour())
        embed.set_thumbnail(url=str(user.display_avatar.replace(size=1024, static_format="png")))
        embed.add_field(name=language.string("discord_user_username"), value=user.name, inline=True)
        if user.global_name:
            embed.add_field(name=language.string("discord_user_username_global"), value=user.global_name, inline=True)
        if member is not None:
            embed.add_field(name=language.string("discord_user_nickname"), value=member.nick, inline=True)
        embed.add_field(name=language.string("discord_user_id"), value=str(user.id), inline=True)
        created_time = language.time(user.created_at, short=0, dow=False, seconds=False, tz=True, at=True, uid=ctx.author.id)
        created_delta = language.delta_dt(user.created_at, accuracy=2, brief=False, affix=True)
        embed.add_field(name=language.string("discord_created_at"), value=f"{created_time}\n{created_delta}", inline=True)
        if member is not None:
            joined_time = language.time(member.joined_at, short=0, dow=False, seconds=False, tz=True, at=True, uid=ctx.author.id)
            joined_delta = language.delta_dt(member.joined_at, accuracy=2, brief=False, affix=True)
            embed.add_field(name=language.string("discord_user_joined_at"), value=f"{joined_time}\n{joined_delta}", inline=True)
        embed.add_field(name=language.string("discord_user_bot"), value=language.yes(user.bot), inline=True)
        embed.add_field(name=language.string("discord_user_mutual"), value=language.plural(len(user.mutual_guilds), "discord_word_server"), inline=True)
        if member is not None:
            if member.premium_since is not None:
                boost_time = language.time(member.premium_since, short=0, dow=False, seconds=False, tz=True, at=True, uid=ctx.author.id)
                boost_delta = language.delta_dt(member.premium_since, accuracy=2, brief=False, affix=True, case="for")
                boost_str = language.string("discord_user_boost_since", time=boost_time, delta=boost_delta)
            else:
                boost_str = language.string("discord_user_boost_none")
            embed.add_field(name=language.string("discord_user_boost"), value=boost_str, inline=True)
            if member.is_timed_out():
                timeout_time = language.time(member.timed_out_until, short=0, dow=False, seconds=False, tz=True, at=True, uid=ctx.author.id)
                timeout_delta = language.delta_dt(member.timed_out_until, accuracy=2, brief=False, affix=False)
                timeout_str = language.string("discord_user_timed_out_details", time=timeout_time, delta=timeout_delta)
                embed.add_field(name=language.string("discord_user_timed_out"), value=timeout_str, inline=True)
            if not member.roles:
                roles_str = language.string("generic_none")
            elif len(member.roles) > 15:
                roles_str = language.string("discord_user_roles_many", count=language.plural(len(member.roles), "discord_word_role"))
            else:
                roles = [role.mention for role in member.roles[::-1] if not role.is_default()]
                roles_str = language.string("discord_user_roles_list", roles="\n".join(roles), count=language.plural(len(roles), "discord_word_role"))
            embed.add_field(name=language.string("discord_user_roles"), value=roles_str, inline=False)
        return await ctx.send(embed=embed)

    @commands.command(name="user")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def user(self, ctx: commands.Context, *, user: commands.UserID = None):
        """ Get details about a certain user """
        _user = self.bot.get_user(user or ctx.author.id)  # type: ignore
        if _user is None:
            try:
                _user = await self.bot.fetch_user(user)  # type: ignore
            except discord.NotFound:
                return await ctx.send(ctx.language().string("events_error_not_found_user", value=user))
        return await self._user_command(ctx, _user)

    @app_commands.command(name="user")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.describe(user="The user whose details to check")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def slash_user(self, interaction: discord.Interaction, user: discord.User = None):
        """ Get details about a certain user """
        return await interactions.slash_command(self._user_command, interaction, user, ephemeral=True)

    @commands.hybrid_command(name="emoji", aliases=["emote"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.describe(emoji="The emoji for which to show details")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def emoji(self, ctx: commands.Context, emoji: str):
        """ See details about an emoji """
        await ctx.defer(ephemeral=True)
        language = ctx.language()
        partial_emoji: discord.PartialEmoji | discord.Emoji | None = None
        full_emoji: discord.Emoji | None = None
        if emoji.isnumeric():  # If just the ID is provided, load that but leave the name blank
            partial_emoji = discord.PartialEmoji(name=None, id=int(emoji))  # type: ignore
        elif re.match(EMOJI_NAME_REGEX, emoji):
            emoji_name = emoji.replace(":", "")  # type: ignore
            for emote in self.bot.emojis:
                if emote.name == emoji_name:
                    full_emoji = emote
                    partial_emoji = emote  # type: ignore
                    break
        if partial_emoji is None:  # If the emoji hasn't been found yet
            partial_emoji: discord.PartialEmoji = discord.PartialEmoji.from_str(emoji)
        if partial_emoji is None or getattr(partial_emoji, "is_unicode_emoji", lambda: False)():  # In case we get an emoji from name
            return await ctx.send(language.string("discord_emoji_error", emoji=emoji))
        if partial_emoji.id is not None:  # Try to fetch the whole emoji
            full_emoji: discord.Emoji | None = self.bot.get_emoji(partial_emoji.id)
        name = full_emoji.name if full_emoji is not None else (partial_emoji.name or language.string("generic_unknown"))
        embed = discord.Embed(title=language.string("discord_emoji_about", emoji=name), colour=general.random_colour())
        embed.add_field(name=language.string("discord_emoji_name"), value=name, inline=True)
        embed.add_field(name=language.string("discord_emoji_id"), value=partial_emoji.id, inline=True)
        embed.add_field(name=language.string("discord_emoji_animated"), value=language.yes(partial_emoji.animated), inline=True)
        created_time = language.time(partial_emoji.created_at, short=0, dow=False, seconds=False, tz=True, at=True, uid=ctx.author.id)
        created_delta = language.delta_dt(partial_emoji.created_at, accuracy=2, brief=False, affix=True)
        embed.add_field(name=language.string("discord_created_at"), value=f"{created_time}\n{created_delta}", inline=True)
        if full_emoji is not None:
            embed.add_field(name=language.string("discord_origin_server"), value=full_emoji.guild.name, inline=True)
        embed.add_field(name=language.string("discord_emoji_link"), value=language.string("generic_link_mask", url=partial_emoji.url), inline=True)
        embed.set_image(url=partial_emoji.url)
        return await ctx.send(embed=embed)

    async def _find_sticker(self, sticker: str) -> discord.Sticker | None:
        """ Find a sticker with the provided name or ID """
        # Try to find a custom sticker with the given name
        for sticker_item in self.bot.stickers:
            if sticker_item.name == sticker or str(sticker_item.id) == sticker:
                return sticker_item
        # Try to find a standard sticker with the given name
        if not self.sticker_packs:
            self.sticker_packs = await self.bot.fetch_premium_sticker_packs()
        for sticker_pack in self.sticker_packs:
            for sticker_item in sticker_pack.stickers:
                if sticker_item.name == sticker or str(sticker_item.id) == sticker:
                    return sticker_item

    @staticmethod
    async def _sticker_command(ctx: commands.Context, sticker: discord.Sticker):
        """ Wrapper around the sticker command """
        language = ctx.language()
        embed = discord.Embed(title=language.string("discord_sticker_about", sticker=sticker.name), colour=general.random_colour())
        embed.add_field(name=language.string("discord_sticker_name"), value=sticker.name, inline=True)
        embed.add_field(name=language.string("discord_sticker_id"), value=sticker.id, inline=True)
        embed.add_field(name=language.string("discord_sticker_format"), value=sticker.format.name, inline=True)  # type: ignore
        created_time = language.time(sticker.created_at, short=0, dow=False, seconds=False, tz=True, at=True, uid=ctx.author.id)
        created_delta = language.delta_dt(sticker.created_at, accuracy=2, brief=False, affix=True)
        embed.add_field(name=language.string("discord_created_at"), value=f"{created_time}\n{created_delta}", inline=True)
        embed.add_field(name=language.string("discord_sticker_link"), value=language.string("generic_link_mask", url=sticker.url), inline=True)
        if isinstance(sticker, discord.GuildSticker):
            embed.add_field(name=language.string("discord_sticker_emoji"), value=sticker.emoji, inline=True)
            if sticker.guild is not None:
                embed.add_field(name=language.string("discord_origin_server"), value=sticker.guild, inline=True)
        if sticker.description:
            embed.add_field(name=language.string("discord_sticker_description"), value=sticker.description, inline=False)
        if isinstance(sticker, discord.StandardSticker):
            embed.add_field(name=language.string("discord_sticker_tags"), value=", ".join(sticker.tags), inline=False)
        embed.set_image(url=sticker.url)
        return await ctx.send(embed=embed)

    @commands.command(name="sticker")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def sticker(self, ctx: commands.Context, sticker: str = None):
        """ See details about a sticker

         You can either specify the name or ID of the sticker, or attach the sticker with the command """
        language = ctx.language()
        if sticker is None:
            if ctx.message.stickers:
                sticker_item = await ctx.message.stickers[0].fetch()
            else:
                return await ctx.send(language.string("discord_sticker_none"))
        else:
            sticker_item = await self._find_sticker(sticker)
            if not sticker_item:
                return await ctx.send(language.string("discord_sticker_not_found", name=sticker))
        return await self._sticker_command(ctx, sticker_item)

    @app_commands.command(name="sticker")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.describe(sticker="The name of the sticker for which to show details")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def slash_sticker(self, interaction: discord.Interaction, sticker: str):
        """ See details about a sticker """
        ctx = await interactions.init_slash_command(interaction, ephemeral=True)
        sticker_item = await self._find_sticker(sticker)
        if not sticker_item:
            return await ctx.send(ctx.language().string("discord_sticker_not_found", name=sticker))
        return await self._sticker_command(ctx, sticker_item)

    @commands.hybrid_group(name="server", aliases=["guild"], invoke_without_command=True, fallback="info")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.describe(server="The server for which to show information")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def server(self, ctx: commands.Context, server: discord.Guild = None):
        """ Information about the current server """
        if ctx.invoked_subcommand is None:
            await ctx.defer(ephemeral=True)
            guild: discord.Guild = server or ctx.guild
            language = self.bot.language(ctx)
            bots = sum(1 for member in guild.members if member.bot)
            bots_ratio = bots / guild.member_count
            embed = discord.Embed(title=language.string("discord_server_about", server=guild.name), colour=general.random_colour())
            if ctx.guild.icon:
                embed.set_thumbnail(url=str(guild.icon.replace(size=1024, static_format="png")))
            embed.add_field(name=language.string("discord_server_name"), value=guild.name, inline=True)
            embed.add_field(name=language.string("discord_server_id"), value=guild.id, inline=True)
            embed.add_field(name=language.string("discord_server_owner"), inline=True, value=f"{guild.owner.mention} ({str(guild.owner)})")
            embed.add_field(name=language.string("discord_members"), value=language.number(guild.member_count), inline=True)
            embed.add_field(name=language.string("discord_server_bots"), value=f"{language.number(bots)} ({language.number(bots_ratio, percentage=True)})", inline=True)
            embed.add_field(name=language.string("discord_server_roles"), value=language.number(len(guild.roles)), inline=True)
            if ctx.channel.permissions_for(guild.me).ban_members:  # This has the side effect of not showing ban counts if a different server was requested, but I don't think that's a problem.
                embed.add_field(name=language.string("discord_server_bans"), value=language.number(sum([1 async for _ in ctx.guild.bans(limit=None)])), inline=True)
            preferred_locale = language.data2("generic_locales", guild.preferred_locale.name, guild.preferred_locale.name)  # type: ignore
            embed.add_field(name=language.string("discord_server_locale"), value=preferred_locale, inline=True)
            boost_level = language.number(guild.premium_tier)
            boosts = language.number(guild.premium_subscription_count)
            boosters = language.number(len(guild.premium_subscribers))
            embed.add_field(name=language.string("discord_server_boosts"), value=language.string("discord_server_boosts_data", boosts=boosts, level=boost_level, users=boosters), inline=True)
            if guild.premium_subscriber_role:
                embed.add_field(name=language.string("discord_server_boost_role"), value=guild.premium_subscriber_role.mention, inline=True)
            embed.add_field(name=language.string("discord_server_boost_progress_bar"), value=language.enabled(guild.premium_progress_bar_enabled), inline=True)
            embed.add_field(name=language.string("discord_server_filesize_limit"), value=language.bytes(guild.filesize_limit), inline=True)
            embed.add_field(name=language.string("discord_server_bitrate_limit"), value=language.bitrate(guild.bitrate_limit), inline=True)
            embed.add_field(name=language.string("discord_server_stage_users"), value=language.number(guild.max_stage_video_users), inline=True)
            notification_level = language.data2("discord_server_notifications_values", guild.default_notifications.name, guild.default_notifications.name)  # type: ignore
            embed.add_field(name=language.string("discord_server_notifications"), value=notification_level, inline=True)
            verification_level = language.data2("discord_server_verification_levels", guild.verification_level.name, guild.verification_level.name)  # type: ignore
            embed.add_field(name=language.string("discord_server_verification"), value=verification_level, inline=True)
            content_filter = language.data2("discord_server_content_filter_values", guild.explicit_content_filter.name, guild.explicit_content_filter.name)  # type: ignore
            embed.add_field(name=language.string("discord_server_content_filter"), value=content_filter, inline=True)
            mfa_level = language.data2("discord_server_mfa_values", guild.mfa_level.name, guild.mfa_level.name)  # type: ignore
            embed.add_field(name=language.string("discord_server_mfa"), value=mfa_level, inline=True)
            nsfw_level = language.data2("discord_server_nsfw_level_values", guild.nsfw_level.name, guild.nsfw_level.name)  # type: ignore
            embed.add_field(name=language.string("discord_server_nsfw_level"), value=nsfw_level, inline=True)
            embed.add_field(name=language.string("discord_server_widget"), value=language.enabled(guild.widget_enabled), inline=True)
            if guild.afk_channel:
                embed.add_field(name=language.string("discord_server_afk_channel"), value=guild.afk_channel.mention, inline=True)
            if guild.system_channel:
                embed.add_field(name=language.string("discord_server_system_channel"), value=guild.system_channel.mention, inline=True)
            if guild.vanity_url:
                embed.add_field(name=language.string("discord_server_vanity_url"), value=guild.vanity_url, inline=True)
            if guild.rules_channel:
                embed.add_field(name=language.string("discord_server_rules_channel"), value=guild.rules_channel.mention, inline=True)
            if guild.public_updates_channel:
                embed.add_field(name=language.string("discord_server_announcements_channel"), value=guild.public_updates_channel.mention, inline=True)
            if guild.safety_alerts_channel:
                embed.add_field(name=language.string("discord_server_alerts_channel"), value=guild.safety_alerts_channel.mention, inline=True)
            embed.add_field(name=language.string("discord_server_events"), value=language.number(len(guild.scheduled_events)), inline=True)
            created_time = language.time(guild.created_at, short=0, dow=False, seconds=False, tz=True, at=True, uid=ctx.author.id)
            created_delta = language.delta_dt(guild.created_at, accuracy=2, brief=False, affix=True)
            embed.add_field(name=language.string("discord_created_at"), value=f"{created_time}\n{created_delta}", inline=False)
            channel_types = {
                "text": 0,
                "voice": 0,
                "category": 0,
                "news": 0,
                "stage_voice": 0,
                "forum": 0,
                "media": 0,
            }
            for channel in guild.channels:
                channel_types[channel.type.name] += 1  # type: ignore
            channel_types["thread"] = len(guild.threads)
            for channel_type, value in channel_types.items():
                channel_types[channel_type] = language.number(value)
            embed.add_field(name=language.string("discord_server_channels"), value=language.string("discord_server_channels_data", **channel_types), inline=False)
            total_emotes = len(guild.emojis)
            emote_limit = guild.emoji_limit
            animated = sum(1 for emote in guild.emojis if emote.animated)
            static = total_emotes - animated
            total_emotes_str = language.number(total_emotes)
            emote_limit_str = language.number(emote_limit)
            animated_str = language.number(animated)
            static_str = language.number(static)
            embed.add_field(name=language.string("discord_server_emotes"), inline=False,
                            value=language.string("discord_server_emotes_data", static=static_str, ani=animated_str, limit=emote_limit_str, total=total_emotes_str))
            total_stickers = language.number(len(guild.stickers))
            sticker_limit = language.number(guild.sticker_limit)
            embed.add_field(name=language.string("discord_server_stickers"), value=f"{total_stickers}/{sticker_limit}", inline=False)
            embed.add_field(name=language.string("discord_server_sounds"), value=language.number(len(guild.soundboard_sounds)), inline=False)
            if guild.description:
                embed.add_field(name=language.string("discord_server_description"), value=guild.description, inline=False)
            interface = paginators.EmbedFieldPaginatorInterface(paginator=paginators.EmbedFieldPaginator(max_fields=12, max_size=3000), bot=ctx.bot, owner=ctx.author, embed=embed)
            interface.display_page = 0  # Start from first page
            return await interface.send_to(ctx)

    @server.command(name="icon", aliases=["avatar"])
    async def server_icon(self, ctx: commands.Context):
        """ Get server's icon """
        await ctx.defer(ephemeral=True)
        language = ctx.language()
        if ctx.guild.icon:
            return await ctx.send(language.string("discord_server_icon", server=ctx.guild.name, url=str(ctx.guild.icon.replace(size=4096, static_format='png'))))
        else:
            return await ctx.send(language.string("discord_server_icon_none", server=ctx.guild.name))

    @server.command(name="banner")
    async def server_banner(self, ctx: commands.Context):
        """ Get server's banner """
        await ctx.defer(ephemeral=True)
        language = ctx.language()
        if ctx.guild.banner:
            return await ctx.send(language.string("discord_server_banner", server=ctx.guild.name, url=str(ctx.guild.banner.replace(size=4096, static_format="png"))))
        else:
            return await ctx.send(language.string("discord_server_banner_none", server=ctx.guild.name))

    @server.command(name="splash", aliases=["invitebg", "invite"])
    async def server_invite(self, ctx: commands.Context):
        """ Get server's invite splash """
        await ctx.defer(ephemeral=True)
        language = ctx.language()
        if ctx.guild.splash:
            return await ctx.send(language.string("discord_server_inv_bg", server=ctx.guild.name, url=str(ctx.guild.splash.replace(size=4096, static_format="png"))))
        else:
            return await ctx.send(language.string("discord_server_inv_bg_none", server=ctx.guild.name))

    @server.command(name="discovery")
    async def server_discovery(self, ctx: commands.Context):
        """ Get server's discovery splash """
        await ctx.defer(ephemeral=True)
        language = ctx.language()
        if ctx.guild.discovery_splash:
            return await ctx.send(language.string("discord_server_discovery", server=ctx.guild.name, url=str(ctx.guild.discovery_splash.replace(size=4096, static_format="png"))))
        else:
            return await ctx.send(language.string("discord_server_discovery_none", server=ctx.guild.name))

    @server.command(name="bots")
    async def server_bots(self, ctx: commands.Context):
        """ Bots in the server """
        await ctx.defer(ephemeral=True)
        language = ctx.language()
        members = sorted(filter(lambda m: m.bot, ctx.guild.members), key=lambda m: m.display_name.lower())  # Sort all bots by name
        paginator = paginators.LinePaginator(max_lines=20, max_size=1000)
        for i, member in enumerate(members, start=1):
            paginator.add_line(f"**{i:02d})** {member.mention} ({member})")
        embed = discord.Embed(title=language.string("discord_server_bots_command", server=ctx.guild.name), colour=general.random_colour())
        interface = paginators.PaginatorEmbedInterface(self.bot, paginator, owner=ctx.author, embed=embed)
        return await interface.send_to(ctx)

    @staticmethod
    async def _embed_command(ctx: commands.Context, title: str | None, description: str | None, footer: str | None,
                             thumbnail: str | None, image: str | None, colour: str | None, include_author: bool):
        """ Wrapper for the embed command """
        language = ctx.language()
        embed = discord.Embed()
        if title:
            embed.title = title.replace("\\n", "\n")
            if len(embed.title) > 256:
                return await ctx.send(language.string("util_embed_title_length"))
        if description:
            embed.description = description.replace("\\n", "\n")
        if footer:
            embed.set_footer(text=footer.replace("\\n", "\n"))
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        if image:
            embed.set_image(url=image)
        if colour:
            try:
                int_colour = images.colour_hex_to_int(colour)
            except images.InvalidLength as e:
                return await ctx.send(language.string("images_colour_invalid_value", value=e.value, length=e.length))
            except images.InvalidColour as e:
                return await ctx.send(language.string("images_colour_invalid", value=e.value, err=e.error))
            embed.colour = int_colour
        if include_author:
            embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
        if ctx.interaction:
            await ctx.send(language.string("util_embed_success"), ephemeral=True, delete_after=5)
        return await ctx.channel.send(embed=embed)

    @commands.command(name="embed")
    @permissions.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(embed_links=True)
    async def embed_creator(self, ctx: commands.Context, *, args: str):
        """ Create a custom embed
        -t/--title: Embed's title text
        -d/--description: Embed's description text
        -f/--footer: Embed's footer text
        -th/--thumbnail: URL to embed's thumbnail
        -i/--image: URL to embed's image
        -c/--colour: A hex code for embed's colour
        -a/--author: Whether to set the author of the command as the embed author

        All the arguments are optional, so if you don't fill them they will simply be empty.
        Use "\n" to add newlines - The current implementation of the code doesn't insert them otherwise
        Example: //embed --title Good evening --description Some very interesting text --colour ff0057"""
        parser = arg_parser.Arguments()
        parser.add_argument('-t', '--title', nargs="+")
        parser.add_argument('-d', '--description', nargs="+")
        parser.add_argument('-f', '--footer', nargs="+")
        parser.add_argument('-th', '--thumbnail', nargs=1)
        parser.add_argument('-i', '--image', nargs=1)
        parser.add_argument('-c', '--colour', nargs=1)
        parser.add_argument('-a', '--author', action='store_true')

        args, valid_check = parser.parse_args(args)
        if not valid_check:
            return await ctx.send(args)
        title = " ".join(args.title) if args.title else None
        description = " ".join(args.description) if args.description else None
        footer = " ".join(args.footer) if args.footer else None
        thumbnail = args.thumbnail[0] if args.thumbnail else None
        image = args.image[0] if args.image else None
        colour = args.colour[0] if args.colour else None
        author = args.author
        return await self._embed_command(ctx, title, description, footer, thumbnail, image, colour, author)

    @app_commands.command(name="embed")
    @permissions.has_permissions(manage_messages=True)
    @app_commands.default_permissions(manage_messages=True)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.describe(
        title="The title text of the embed",
        description="The description text of the embed",
        footer="The text at the bottom of the embed",
        thumbnail="The URL to the thumbnail of the embed",
        image="The URL to the big image of the embed",
        colour="The colour of the embed",
        include_author="Whether to set the author of the command as the embed author",
    )
    @app_commands.allowed_installs(guilds=True, users=False)  # Disable for user installs in case of permission issues
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def slash_embed(self, interaction: discord.Interaction, title: str = None, description: str = None, footer: str = None,
                          thumbnail: str = None, image: str = None, colour: str = None, include_author: bool = False):
        """ Create a custom embed

         All the arguments are optional, and will be empty if not filled. Use "\n" to add newlines. """
        return await interactions.slash_command(self._embed_command, interaction, title, description, footer, thumbnail, image, colour, include_author, ephemeral=True)


class Reminders(Utility, name="Utility"):
    @commands.hybrid_group(name="remind", aliases=["remindme"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def remind_me(self, ctx: commands.Context):
        """ Set yourself a reminder """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    async def _set_reminder(self, ctx: commands.Context, language: languages.Language, time_dt: time2.datetime, reminder: str):
        """ Wrapper for the two reminder types """
        delta_str = language.delta_dt(time_dt, accuracy=7, brief=False, affix=True)
        time_str = language.time(time_dt, short=1, dow=False, seconds=True, tz=True, uid=ctx.author.id, at=True)
        # noinspection SqlInsertValues
        self.bot.db.execute("INSERT INTO reminders(uid, expiry, message, handled, bot) VALUES (?, ?, ?, ?, ?)", (ctx.author.id, time_dt, reminder, 0, self.bot.name))
        return await ctx.send(language.string("util_reminders_success", author=general.username(ctx.author), delta=delta_str, time=time_str, p=ctx.prefix))

    @remind_me.command(name="in", aliases=["duration"])
    @app_commands.autocomplete(duration=reminder_duration_autocomplete)
    @app_commands.describe(duration="How long from now to set the reminder for (Format: 1y1mo1d1h1m1s)", message="The text of the reminder to send you")
    async def remind_in(self, ctx: commands.Context, duration: str, *, message: str):
        """ Set yourself a reminder for a given time period

         Example: //remind 2d12h Do something fun """
        await ctx.defer(ephemeral=True)
        language = ctx.language()
        delta = time.interpret_time(duration)
        if time.rd_is_above_5y(delta):
            return await ctx.send(language.string("util_reminders_limit"))
        expiry, error = time.add_time(delta)
        if error:
            return await ctx.send(language.string("util_reminders_error", err=expiry))
        return await self._set_reminder(ctx, language, expiry, message)

    @remind_me.command(name="on", aliases=["time"])
    @app_commands.rename(_date="date", _time="time")
    @app_commands.describe(_date="The date on which to send the reminder", _time="The time at which to send the reminder", reminder="The text of the reminder to send you")
    async def remind_on(self, ctx: commands.Context, _date: str, _time: str, *, reminder: str):
        """ Set yourself a reminder for a given time and date

         Example: //reminder 2025-01-27 23:00 Do something fun """
        await ctx.defer(ephemeral=True)
        language = ctx.language()
        try:
            datetime = self._parse_time(ctx, _date, _time)
        except ValueError:
            return await ctx.send(language.string("util_reminders_format_time"))
        now = time2.datetime.now()
        if datetime < now:
            return await ctx.send(language.string("util_reminders_past"))
        elif (datetime - now).days > 5 * 365 + 2:  # 5 years
            return await ctx.send(language.string("util_reminders_limit"))
        time_dt = datetime.to_timezone(time2.timezone.utc).to_datetime().replace(tzinfo=None)  # convert into a datetime object with null tzinfo
        return await self._set_reminder(ctx, language, time_dt, reminder)

    async def _reminders_list_command(self, ctx: commands.Context):
        """ Wrapper for the reminders list command """
        language = ctx.language()
        reminders = self.bot.db.fetch("SELECT * FROM reminders WHERE uid=? AND bot=? ORDER BY expiry", (ctx.author.id, self.bot.name))
        if not reminders:
            return await ctx.send(language.string("util_reminders_none", author=general.username(ctx.author)))
        header = language.string("util_reminders_list", author=general.username(ctx.author))
        footer = language.string("util_reminders_list_end", p=ctx.prefix) if not ctx.interaction else None
        paginator = paginators.LinePaginator(prefix=header, suffix=footer, max_lines=5, max_size=2000, linesep="\n\n")
        for i, reminder in enumerate(reminders, start=1):
            expiry = reminder["expiry"]
            expires_on = language.time(expiry, short=1, dow=False, seconds=True, tz=True, at=True, uid=ctx.author.id)
            expires_in = language.delta_dt(expiry, accuracy=3, brief=False, affix=True)
            paginator.add_line(language.string("util_reminders_item", i=i, message=reminder["message"], id=reminder["id"], time=expires_on, delta=expires_in))
        interface = paginators.PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
        return await interface.send_to(ctx)

    async def _reminders_edit_command(self, ctx: commands.Context, reminder_id: int, new_message: str | None, new_time: str | None):
        """ Wrapper for the reminders edit command """
        language = ctx.language()
        reminder = self.bot.db.fetchrow("SELECT * FROM reminders WHERE id=? AND uid=? AND bot=?", (reminder_id, ctx.author.id, self.bot.name))
        if not reminder:
            return await ctx.send(language.string("util_reminders_edit_none", id=reminder_id))
        message = new_message or reminder["message"]
        time_dt = reminder["expiry"]
        if new_time is not None:
            try:
                time_tuple = new_time.split(" ")
                if len(time_tuple) == 1:
                    _date = time_tuple[0]
                    _time = None
                elif len(time_tuple) == 2:
                    _date, _time = time_tuple
                else:
                    return await ctx.send(language.string("util_reminders_edit_time2"))
                datetime = self._parse_time(ctx, _date, _time)
            except ValueError:
                return await ctx.send(language.string("util_reminders_format_time"))
            now = time2.datetime.now()
            if datetime < now:
                return await ctx.send(language.string("util_reminders_past"))
            elif (datetime - now).days > 5 * 365 + 2:  # 5 years
                return await ctx.send(language.string("util_reminders_limit"))
            time_dt = datetime.to_timezone(time2.timezone.utc).to_datetime().replace(tzinfo=None)
        time_str = language.time(time_dt, short=1, dow=False, seconds=True, tz=True, at=True, uid=ctx.author.id)
        self.bot.db.execute("UPDATE reminders SET message=?, expiry=? WHERE id=?", (message, time_dt, reminder_id))
        return await ctx.send(language.string("util_reminders_edit", id=reminder_id, message=message, time=time_str))

    async def _reminders_delete_command(self, ctx: commands.Context, reminder_id: int):
        """ Wrapper for the reminders delete command """
        language = ctx.language()
        reminder = self.bot.db.fetchrow("SELECT * FROM reminders WHERE id=? AND uid=? AND bot=?", (reminder_id, ctx.author.id, self.bot.name))
        if not reminder:
            return await ctx.send(language.string("util_reminders_edit_none", id=reminder_id))
        self.bot.db.execute("DELETE FROM reminders WHERE id=? AND uid=? AND bot=?", (reminder_id, ctx.author.id, self.bot.name))
        return await ctx.send(language.string("util_reminders_delete", id=reminder_id))

    @commands.group(name="reminders", aliases=["reminder"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def reminders(self, ctx: commands.Context):
        """ Interact with your existing reminders """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @reminders.command(name="list")
    async def reminders_list(self, ctx: commands.Context):
        """ See the list of your currently active reminders """
        return await self._reminders_list_command(ctx)

    @reminders.command(name="edit")
    async def reminders_edit(self, ctx: commands.Context, reminder_id: int, *, args: str):
        """ Edit a reminder
        -m/--message/--text: Edit the reminder's text
        -t/--time/--expiry: Edit when you want to be reminded (Format: `YYYY-MM-DD hh:mm:ss`)
        Time part optional, and may be just `hh:mm`. Time must be in 24-hour format.

        Example: //reminders edit 1048576 --time 2021-06-08 17:00:00 --message Insert something interesting here"""
        parser = arg_parser.Arguments()
        parser.add_argument('-m', '--message', '--text', nargs="+")
        parser.add_argument('-t', '--time', '--expiry', nargs="+")
        args, valid_check = parser.parse_args(args)
        if not valid_check:
            return await ctx.send(args)
        message = " ".join(args.message) if args.message else None
        time_str = " ".join(args.time) if args.time else None
        return await self._reminders_edit_command(ctx, reminder_id, message, time_str)

    @reminders.command(name="delete", aliases=["del", "remove", "cancel"])
    async def reminders_delete(self, ctx: commands.Context, reminder_id: int):
        """ Delete a reminder """
        return await self._reminders_delete_command(ctx, reminder_id)

    async def reminder_autocomplete(self, interaction: discord.Interaction, current: int) -> list[app_commands.Choice[int]]:
        """ Autocomplete for reminder IDs """
        language = self.bot.language(interaction)
        reminders = self.bot.db.fetch("SELECT * FROM reminders WHERE uid=? AND bot=?", (interaction.user.id, self.bot.name))
        results: list[app_commands.Choice[int]] = []
        for reminder in reminders:
            if not current or str(current) in str(reminder["id"]):
                reminder_id = reminder["id"]
                expiry = language.time(reminder["expiry"], short=1, dow=False, seconds=False, tz=interaction.user.id, at=True)
                message = reminder["message"]
                reminder_value = f"[{reminder_id}] {message} ({expiry})"
                results.append(app_commands.Choice(name=reminder_value[:100], value=reminder_id))
        return results

    @commands.slash_group(name="reminders")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def slash_reminders(self):
        """ Interact with your existing reminders """
        pass

    @slash_reminders.command(name="list")
    async def slash_reminders_list(self, interaction: discord.Interaction):
        """ See the list of your currently active reminders """
        return await interactions.slash_command(self._reminders_list_command, interaction, ephemeral=True)

    @slash_reminders.command(name="edit")
    @app_commands.autocomplete(reminder_id=reminder_autocomplete)
    @app_commands.describe(reminder_id="The ID of the reminder to edit", new_time="The new time at which to send the reminder", new_message="The new message for the reminder")
    async def slash_reminders_edit(self, interaction: discord.Interaction, reminder_id: int, new_time: str = None, new_message: str = None):
        """ Edit an existing reminder """
        return await interactions.slash_command(self._reminders_edit_command, interaction, reminder_id, new_message, new_time, ephemeral=True)

    @slash_reminders.command(name="delete")
    @app_commands.autocomplete(reminder_id=reminder_autocomplete)
    @app_commands.describe(reminder_id="The ID of the reminder to delete")
    async def slash_reminders_delete(self, interaction: discord.Interaction, reminder_id: int):
        """ Delete a reminder """
        return await interactions.slash_command(self._reminders_delete_command, interaction, reminder_id, ephemeral=True)


class UtilitySuager(Reminders, name="Utility"):
    @commands.command(name="customrole", aliases=["cr"])
    @commands.guild_only()
    @commands.check(custom_role_enabled)
    @commands.cooldown(rate=1, per=20, type=commands.BucketType.user)
    async def custom_role(self, ctx: commands.Context, *, stuff: str):
        """ Set up your custom role
        -c/--colour/--color: Set role colour
        -n/--name: Set role name

        Example: //customrole --name Role Name --colour ff0057"""
        data = self.bot.db.fetchrow("SELECT * FROM custom_role WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
        if not data:
            return await ctx.send(f"Doesn't seem like you have a custom role in this server, {general.username(ctx.author)}")
        parser = arg_parser.Arguments()
        parser.add_argument('-c', '--colour', '--color', nargs=1)
        parser.add_argument('-n', '--name', nargs="+")
        args, valid_check = parser.parse_args(stuff)
        if not valid_check:
            return await ctx.send(args)
        role = ctx.guild.get_role(data['rid'])
        if args.colour is not None:
            c = args.colour[0]
            a = len(c)
            if c == "random":
                col = general.random_colour()
            else:
                if c.startswith("#"):
                    c = c[1:]
                    a = len(c)
                if a == 6 or a == 3:
                    try:
                        col = int(c, base=16)
                    except Exception as e:
                        return await ctx.send(f"Invalid colour - {type(e).__name__}: {e}")
                else:
                    return await ctx.send("Colour must be either 3 or 6 HEX digits long.")
            colour = discord.Colour(col)
        else:
            colour = role.colour
        try:
            name = ' '.join(args.name)
        except TypeError:
            name = role.name
        try:
            await role.edit(name=name, colour=colour, reason="Custom Role change")
        except Exception as e:
            return await ctx.send(f"An error occurred while updating custom role: {type(e).__name__}: {e}")
        return await ctx.send(f"Successfully updated your custom role, {general.username(ctx.author)}")

    @commands.command(name="grantrole")
    @commands.guild_only()
    @commands.check(custom_role_enabled)
    @permissions.has_permissions(administrator=True)
    async def grant_custom_role(self, ctx: commands.Context, user: discord.Member, role: discord.Role):
        """ Grant custom role """
        already = self.bot.db.fetchrow("SELECT * FROM custom_role WHERE uid=? AND gid=?", (user.id, ctx.guild.id))
        if not already:
            self.bot.db.execute("INSERT INTO custom_role VALUES (?, ?, ?)", (user.id, role.id, ctx.guild.id))
            try:
                await user.add_roles(role, reason="Custom Role grant")
                return await ctx.send(f"Granted {role.name} to {general.username(ctx.author)}")
            except discord.Forbidden:
                return await ctx.send(f"{role.name} could not be granted to {general.username(ctx.author)}. It has, however, been saved to the database.")
        else:
            self.bot.db.execute("UPDATE custom_role SET rid=? WHERE uid=? AND gid=?", (role.id, user.id, ctx.guild.id))
            return await ctx.send(f"Updated custom role of {general.username(ctx.author)} to {role.name}")


class UtilityCobble(Utility, name="Utility"):
    @commands.hybrid_command(name="timesince", aliases=["timeuntil"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.choices(_time_class=TIME_CLASSES)
    @app_commands.rename(_date="date", _time="time", _time_class="time_class")
    @app_commands.describe(
        _date="The date to compare (Format: YYYY-MM-DD)",
        _time="The time to compare (Format: HH:MM:SS)",
        _time_class="The calendar in which to compare times"
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def time_since(self, ctx: commands.Context, _date: str = None, _time: str = None, _time_class: str = "Kargadia"):
        """ Calculate how long it has been since a given time

        If you don't specify any time, it will simply default to an arbitrary date within the near future """
        return await self.time_since_command(ctx, _date, _time, _time_class)

    @commands.hybrid_command(name="timein")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.autocomplete(time_period=duration_autocomplete)
    @app_commands.choices(time_class=TIME_CLASSES)
    @app_commands.describe(time_period="The duration of time to look in the future (Format: 1y1mo1d1h1m1s)", time_class="The calendar in which to compare times")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def time_in(self, ctx: commands.Context, time_period: str, time_class: str = "Kargadia"):
        """ Check what time it will be in a specified period """
        return await self.time_diff(ctx, time_period, 1, time_class)

    @commands.hybrid_command(name="timeago")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.autocomplete(time_period=duration_autocomplete)
    @app_commands.choices(time_class=TIME_CLASSES)
    @app_commands.describe(time_period="The duration of time to look in the past (Format: 1y1mo1d1h1m1s)", time_class="The calendar in which to compare times")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def time_ago(self, ctx: commands.Context, time_period: str, time_class: str = "Kargadia"):
        """ Check what time it was a specified period ago """
        return await self.time_diff(ctx, time_period, -1, time_class)

    @commands.hybrid_command(name="converttimes", aliases=["time2", "times", "timeconvert", "convert"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @app_commands.choices(source_time_class=TIME_CLASSES)
    @app_commands.rename(_date="date", _time="time", source_time_class="time_class")
    @app_commands.describe(
        source_time_class="The source calendar to convert from",
        _date="The date to convert (Format: YYYY-MM-DD)",
        _time="The time to convert (Format: HH:MM:SS)"
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def time_convert(self, ctx: commands.Context, source_time_class: str = "Earth", _date: str = None, _time: str = None):
        """ Convert times between different calendars

        Example: `..times Kargadia Earth 2152-08-11 12:00:00` would output 10 August 2022 18:59:58
        Leave the command empty to convert to the current time on Kargadia
        Only specify the two calendars if you want to see the current time in a specific time class """
        await ctx.defer(ephemeral=True)
        language = ctx.language()
        try:
            time_class1 = getattr(time2, source_time_class)
        except AttributeError:
            return await ctx.send(language.string("util_time_class_not_found"))
        else:
            if not issubclass(time_class1, time2.Earth):
                return await ctx.send(language.string("util_time_class_invalid"))

        if not _date:
            source_date = time2.datetime.now(time2.timezone.utc, time_class1)
        else:
            try:
                source_date = self._parse_time(ctx, _date, _time, source_time_class)
            except ValueError:
                return await ctx.send(language.string("util_timesince_format"))
        embed = discord.Embed(title=language.string("util_time_convert"), colour=general.random_colour())
        for time_class in time2.time_classes.values():
            output_date = source_date.convert_time_class(time_class, False)
            class_name = language.data2("generic_time_classes", time_class.__name__, time_class.__name__)
            output_str = language.time(output_date, short=0, dow=True, seconds=True, tz=True, uid=ctx.author.id)
            embed.add_field(name=class_name, value=output_str, inline=False)
        return await ctx.send(embed=embed)


async def setup(bot: bot_data.Bot):
    if bot.name == "suager":
        await bot.add_cog(UtilitySuager(bot))
    elif bot.name == "kyomi":
        await bot.add_cog(Reminders(bot))
    elif bot.name == "cobble":
        await bot.add_cog(UtilityCobble(bot))
    else:
        await bot.add_cog(Utility(bot))
