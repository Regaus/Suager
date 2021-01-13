import json
from datetime import datetime, timezone
from io import BytesIO

import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

from cobble.utils import ss23, ss24
from core.utils import emotes, general, time


def rsl_number(value: int):
    """ Convert number to RSL-1 """
    limit = int("9" * 36)
    if value > limit:
        return f"Highest allowed number is {limit:,} (1e36 - 1)"
    if value < 0:
        return f"Negative values will not work"
    if value == 0:
        return "deneda"
    one = {0: "", 1: "ukka", 2: "devi", 3: "tei", 4: "sei", 5: "paa", 6: "senki", 7: "ei", 8: "oni", 9: "zehi"}
    teen = {11: "uveri", 12: "deveri", 13: "teveri", 14: "severi", 15: "paveri", 16: "seneri", 17: "eijeri", 18: "overi", 19: "zegheri"}
    ten = {1: "verri", 2: "devveire", 3: "tevveire", 4: "sevveire", 5: "pavveire", 6: "senneire", 7: "evveire", 8: "onneire", 9: "zegheire"}
    hundred = ["arraiki", "arraikädan"]
    exp_1000 = ["kirraa", "kirraadan"]
    exp = ["ugaristu", "devaristu", "tevaristu", "sekaristu", "pakkaristu", "sennaristu", "eijaristu", "onaristu", "zeharistu", "verraristu"]

    def thousand(_val: int):
        _999 = _val % 1000
        _99 = _999 % 100
        _99v = ""
        if _99 < 10:
            _99v = one[_99]
        elif 11 <= _99 < 20:
            _99v = teen[_99]
        else:
            _v, _u = divmod(_99, 10)
            _99v = f"{one[_u]} u {ten[_v]}" if _u > 0 else ten[_v]
        _100 = _999 // 100
        _100v = "" if _100 == 0 else ((f"{one[1]} {hundred[0]}" if _100 == 1 else f"{one[_100]} {hundred[1]}") + (", " if _99 != 0 else ""))
        return _100v + _99v
    _1000 = value % 1000
    outputs = [thousand(_1000)] if _1000 > 0 else []
    large = []
    _value = value
    _range = len(exp) + 1
    for i in range(_range):
        _value //= 1000
        large.append(_value % 1000)
    for i in range(_range):
        val = large[i]
        if val > 0:
            n1, n2 = exp_1000 if i == 0 else ((_name := exp[i - 1]), _name[:-1] + "azan")
            name = n1 if val % 100 == 1 else n2
            outputs.append(f"{thousand(val)}{'r' if val == 1 and i > 0 else ''} {name}")
    return ", ".join(outputs[::-1])


class GA78(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="time23")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def time23(self, ctx: commands.Context, year: int = None, month: int = 1, day: int = 1, hour: int = 0, minute: int = 0, second: int = 0):
        """ Compare times from Earth with SS23 """
        if year is None:
            dt = time.now(None)
        else:
            if year < 1687:
                return await general.send(f"{emotes.Deny} This command does not work with dates before **1 January 1687 AD**.", ctx.channel)
            if year >= 8200:
                return await general.send(f"{emotes.Deny} This command does not work with dates after **31 December 8199 AD, 23:59:59 UTC**", ctx.channel)
            try:
                dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
            except ValueError as e:
                return await general.send(f"{emotes.Deny} {type(e).__name__}: {e}", ctx.channel)
        ti = dt.strftime("%A, %d %B %Y, %H:%M:%S %Z")  # Time IRL
        tk = ss23.date_kargadia(dt)        # Time in Kargadia RSL-1
        tz = ss23.date_zeivela(dt)         # Time on Zeivela RSL-2
        tq = ss23.date_kaltaryna(dt)       # Time in Qevenerus/Kaltaryna RSL-1
        td = ss23.date_kargadia_5(dt)      # Time on Kargadia RSL-5
        td2 = ss23.time_earth_5(dt, True)  # Time on Earth RSL-5 DT
        months_1 = ["Seldan Masailnaran", "Nuannaran", "Seimannaran", "Veisanaran", "Eilannaran", "Havazdallarinnaran",
                    "Sanvaggannaran", "Kailaggannaran", "Semardannaran", "Addanvaran", "Halltuavaran", "Masailnaran"]
        months_5 = ["Chìlderaljanselaljan", "Anveraijanselaljan", "Síldarinselaljan", "Kûstanselaljan",
                    "Vullastenselaljan", "Khavastalgèrinselaljan", "Senkanselaljan", "Dhárelanselaljan",
                    "Silaljanselaljan", "Eijelovvanselaljan", "Haldúvaranselaljan", "Massalanselaljan"]
        tn = time.kargadia_convert(dt)
        tn1 = tn.strftime(f"%A, %d {months_1[tn.month % 12]} %Y, %H:%M:%S %Z")
        tn5 = tn.strftime(f"%A, %d {months_5[tn.month % 12]} %Y, %H:%M:%S %Z")
        return await general.send(f"Time on this Earth (English): **{ti}**\nTime on this Earth (RSL-1_kg): **{tn1}**\n"
                                  f"Time on this Earth (RSL-5 NE): **{tn5}**\nTime on this Earth (RSL-5 DT): **{td2}**\n"
                                  f"Time on 23.4 Zeivela (Local): **{tz}**\n"
                                  f"Time on 23.5 Kargadia (RSL-1_kg): **{tk}**\nTime on 23.5 Kargadia (RSL-5): **{td}**\n"
                                  f"Time on 23.6 Qevenerus (RSL-1_ka): **{tq}**", ctx.channel)

    @commands.command(name="time24")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def time24(self, ctx: commands.Context, year: int = None, month: int = 1, day: int = 1, hour: int = 0, minute: int = 0, second: int = 0):
        """ Compare times from Earth with SS24 """
        if year is None:
            dt = time.now(None)
        else:
            if year < 1743:
                return await general.send(f"{emotes.Deny} This command does not work with dates before **1 January 1743 AD**.", ctx.channel)
            try:
                dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
            except ValueError as e:
                return await general.send(f"{emotes.Deny} {type(e).__name__}: {e}", ctx.channel)
        ti = dt.strftime("%A, %d %B %Y, %H:%M:%S %Z")  # Time IRL
        t24_4_local = ss24.time_sinvimania(dt).str()   # 24.4 Sinvimania Local
        t24_5_local = ss24.time_hosvalnerus(dt).str()  # 24.5 Hosvalnerus local
        t24_11_1 = ss24.time_kuastall_11(dt).str()
        return await general.send(f"Time on this Earth (English): **{ti}**\n"
                                  f"Time on 24.4 Sinvimania (Local Solar): **{t24_4_local}**\n"
                                  f"Time on 24.5 Hosvalnerus (Local): **{t24_5_local}**\n"
                                  f"Time on 24.11 Kuastall-11 (RSL-1_ku): **{t24_11_1}**", ctx.channel)

    @commands.command(name="weather23")
    @commands.is_owner()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def weather23(self, ctx: commands.Context, *, place: str):
        """ Weather in a place in SS23 """
        try:
            weather = ss23.Weather(place.title())
            embed = discord.Embed(colour=general.random_colour())
            embed.title = f"Weather in **{weather.city}, {weather.planet}**"
            embed.description = f"Local Time: **{weather.time_out}**"
            temp_c = round(weather.temperature, 1)
            embed.add_field(name="Temperature", value=f"{temp_c}°C | **placeholder**", inline=False)
            speed_kmh = round(weather.wind_speed, 1)
            if weather.planet == "Kargadia":
                kp_base = 0.8192
                kp_hour = 37.49865756 / 32
                m_name = "ks/h (kp/c)"
            elif weather.planet == "Kaltaryna":
                kp_base = 0.8192
                kp_hour = 51.642812 / 64
                m_name = "ks/h (kp/c)"
            else:
                kp_base = 1
                kp_hour = 1
                m_name = "unknown"
            speed_kpc = round(weather.wind_speed / kp_base * kp_hour, 1)
            embed.add_field(name="Wind Speed", value=f"{speed_kmh} km/h | **{speed_kpc} {m_name}**", inline=False)
            if weather.is_raining:
                rain = "It's raining" if temp_c > 0 else "It's snowing"
            else:
                rain = "It's dry so far"
            embed.add_field(name="Precipitation", value=rain, inline=False)
            embed.timestamp = time.now(None)
            return await general.send(None, ctx.channel, embed=embed)
        except Exception as e:
            if ctx.channel.id == 610482988123422750:
                await general.send(general.traceback_maker(e), ctx.channel)
            return await general.send(f"An error occurred: `{type(e).__name__}: {e}`.\nThe place {place} may not exist.", ctx.channel)

    @commands.command(name="nlc")
    @commands.is_owner()
    async def ne_world_ll_calc(self, ctx: commands.Context, x: int, z: int, border: int = 100000):
        """ Calculate latitude, local offset of position - NEWorld """
        lat = -z / border * 90  # Latitude value
        long = x / border * 180
        tzl = 48 / 180
        tz = round(long / tzl)
        tzo = tz / tzl - long  # Local Offset
        return await general.send(f"At {x=:,} and {z=:,} (World Border at {border:,}):\nLatitude: {lat:.3f}\nLocal Offset: {tzo:.3f}", ctx.channel)

    @commands.command("rslt")
    @commands.check(lambda ctx: ctx.author.id in [302851022790066185, 236884090651934721, 291665491221807104])
    async def rsl_encode(self, ctx: commands.Context, s: int, *, t: str):
        """ Laikattart Sintuvut """
        if not (1 <= s <= 8700):
            return await general.send("De dejava idou, no sa maikazo ir te edou kihtemal. ", ctx.channel)
        shift = s * 128
        code = rsl_number(s)
        try:
            text = "".join([chr(ord(letter) + shift) for letter in t])
        except ValueError:
            return await general.send(f"Sil valse, alteknaar ka uvaar kuarhaavar qeraduar", ctx.channel)
        return await general.send(f"{code} {text}", ctx.channel)

    @commands.command("rslf")
    @commands.check(lambda ctx: ctx.author.id in [302851022790066185, 236884090651934721, 291665491221807104])
    async def rsl_decode(self, ctx: commands.Context, s: int, *, t: str):
        """ Laikattarad Sintuvuad """
        if not (1 <= s <= 8700):
            return await general.send("De dejava idou, no sa maikazo ir te edou kihtemal", ctx.channel)
        shift = s * 128
        text = ""
        for letter in t:
            try:
                a = chr(ord(letter) - shift)
            except ValueError:
                a = chr(0)
            text += a
        return await general.send(text, ctx.channel)

    @commands.group(name="rsl1", aliases=["rsl-1", "rsl"])
    @commands.check(lambda ctx: ctx.channel.id in [610482988123422750, 787340111963881472, 725835449502924901, 742885168997466196, 798513492697153536] and
                    ctx.author.id in [302851022790066185, 291665491221807104, 230313032956248064, 430891116318031872, 418151634087182359, 374853432168808448,
                                      593736085327314954])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def rsl1(self, ctx: commands.Context):
        """ RSL-1 data """
        if ctx.invoked_subcommand is None:
            await general.send("This is the command that can try to explain how RSL-1 works and what is going on here.\n\n"
                               "**Warning: While I don't mind if you speak the language, do __not__ be sending the translations outside of this channel "
                               "or in DMs (other than between me or other people here)**", ctx.channel)
            return await ctx.send_help(str(ctx.command))

    @rsl1.command(name="numbers", aliases=["n", "number"])
    async def rsl1_numbers(self, ctx: commands.Context, number: int = None):
        """ Translate a number to RSL-1 """
        if number is None:
            return await general.send(f"This command can translate a number to RSL-1. For example, `{ctx.prefix}rsl1 {ctx.invoked_with} 1` "
                                      f"will translate the number 1 to RSL-1.", ctx.channel)
        return await general.send(f"{number:,} = {rsl_number(number)}", ctx.channel)

    @commands.is_owner()
    @rsl1.group(name="declensions", aliases=["decline", "conjugations", "conjugate", "c"])
    async def rsl1_decline(self, ctx: commands.Context):
        """ RSL-1 word changing thingies """
        if ctx.invoked_subcommand is None:
            await general.send("This command will show you how the RSL-1 words change in different places", ctx.channel)
            return await ctx.send_help(str(ctx.command))

    @rsl1_decline.command(name="nous", aliases=["declensions", "decline"])
    async def rsl1_decl_nouns(self, ctx: commands.Context, word: str = None):
        """ RSL-1 noun declensions """
        font = ImageFont.truetype("assets/mono.ttf", size=64)
        if not word:
            await general.send("Here are noun declensions in RSL-1. Note, that RSL-1 also has noun genders, which then affect adjective endings.\n"
                               "Also note: Nouns ending with `-s` (e.g. -as, -os, -us, **but not something like -ks, -ts**) drop the s when not in the "
                               "nominative case, and use the declension of the preceding vowel (very few exceptions). They, however, still say masculine."
                               "For example: (nominative) riadus -> (genitive) riadu**n**", ctx.channel)
            image = Image.new("RGB", (2000, 2000), (0, 0, 0))
            text1 = "Masculine nouns - end in either a consonant or -u.\n" \
                    "Noun Case    | Singular (cons.) | Singular (-u) | Plural\n" \
                    "Nominative   |        consonant |            -u |    -as\n" \
                    "Genitive     |              -un |           -un |  -azan\n" \
                    "Dative       |              -uv |           -uv |  -azav\n" \
                    "Accusative   |           -u/-uu |           -uu |   -azu\n" \
                    "Instrumental |              -ur |           -ur |  -azur\n" \
                    "Comitative   |             -uar |          -uar |  -azir\n" \
                    "Locative     |               -i |          -uri |   -azi\n" \
                    "Lative       |              -ut |           -ut |  -azat\n" \
                    "Ablative     |              -ad |          -uad |  -azid\n" \
                    "Possessive*  |        -tar/-dar |         -udar | -azdar\n"
            text2 = "Feminine nouns - end in either -a or -i.\n" \
                    "Noun Case    | Singular (-a) | Singular (-i) | Plural\n" \
                    "Nominative   |            -a |            -i |    -at\n" \
                    "Genitive     |           -an |           -in |  -adan\n" \
                    "Dative       |           -av |           -iv |  -adav\n" \
                    "Accusative   |           -aa |           -ia |   -ada\n" \
                    "Instrumental |           -ar |           -ir |  -adar\n" \
                    "Comitative   |          -air |          -air |  -adir\n" \
                    "Locative     |           -ai |           -ii |   -adi\n" \
                    "Lative       |          -ait |           -it |  -adat\n" \
                    "Ablative     |          -aad |          -iad |  -adid\n" \
                    "Possessive*  |         -adar |         -inar | -addar\n"
            text3 = "Neuter nouns - end in either -e or -o.\n" \
                    "Noun Case    | Singular (-e) | Singular (-o) | Plural\n" \
                    "Nominative   |            -e |            -o |    -on\n" \
                    "Genitive     |           -en |           -on |  -onan\n" \
                    "Dative       |           -ev |           -ov |  -onav\n" \
                    "Accusative   |           -ee |           -ou |   -onu\n" \
                    "Instrumental |           -er |           -or |  -onor\n" \
                    "Comitative   |          -our |          -our |  -onir\n" \
                    "Locative     |           -ei |           -oi |   -oni\n" \
                    "Lative       |           -et |           -ot |  -onat\n" \
                    "Ablative     |          -ead |          -oad |  -onid\n" \
                    "Possessive*  |         -enar |         -odar | -onnar\n"
            draw = ImageDraw.Draw(image)
            width1, height1 = draw.textsize(text1, font=font)
            width2, height2 = draw.textsize(text2, font=font)
            width3, height3 = draw.textsize(text3, font=font)
            image1 = image.resize((width1 + 20, height1 - 30))
            image2 = image.resize((width2 + 20, height2 - 30))
            image3 = image.resize((width3 + 20, height3 - 30))
            draw1 = ImageDraw.Draw(image1)
            draw2 = ImageDraw.Draw(image2)
            draw3 = ImageDraw.Draw(image3)
            draw1.text((10, 10), text1, font=font, fill=(255, 255, 255))
            draw2.text((10, 10), text2, font=font, fill=(255, 255, 255))
            draw3.text((10, 10), text3, font=font, fill=(255, 255, 255))
            bio1, bio2, bio3 = BytesIO(), BytesIO(), BytesIO()
            image1.save(bio1, "PNG")
            image2.save(bio2, "PNG")
            image3.save(bio3, "PNG")
            bio1.seek(0)
            bio2.seek(0)
            bio3.seek(0)
            await general.send(None, ctx.channel,
                               files=[discord.File(bio1, "masculine.png"), discord.File(bio2, "feminine.png"), discord.File(bio3, "neuter.png")])
            # await general.send(text1, ctx.channel)
            return await general.send("\\*Possession is showed either using the possessive form of the noun, of putting the word to the genitive case: "
                                      "Regaus'ta vahtaa = vahtaa Regaun = Regaus' life\nIf you want to see the declension of a specific noun, "
                                      "you can enter a word after this command to make the bot ~~suffer~~ show you the declension of the word. "
                                      "Especially since not all weirdnesses of RSL-1 can be shown here easily.\n"
                                      f"For adjectives, use `{ctx.prefix}rsl1 adjectives`.", ctx.channel)
        else:
            word = word.lower()
            is_s = word[-1] == "s"
            li = -2 if is_s else -1  # last letter's index
            ll = word[li]  # Last letter of the word
            if word == "regaus":
                declension = 7
                li = 0
            elif ll == "a":
                declension = 1
            elif ll == "ä":
                declension = 2
            elif ll == "i":
                declension = 3
            elif ll == "e":
                declension = 4
            elif ll == "o":
                declension = 5
            elif ll == "u":
                declension = 6
            else:
                declension = 7
                li = 0
            declined = word[:li] if li < 0 else word
            cases = ["Case", "Nominative", "Genitive", "Dative", "Accusative", "Instrumental", "Comitative", "Locative", "Lative", "Ablative", "Possessive"]
            singular = ["Singular", word] + [declined] * (len(cases) - 2)
            plural = ["Plural"] + [declined] * (len(cases) - 1)
            endings = {
                1: [["", "an", "av", "aa", "ar", "air", "ai", "ait", "aad", "adar"],
                    ["at", "adan", "adav", "ada", "adar", "adir", "adi", "adat", "adid", "addar"]],
                2: [["", "än", "äv", "äa", "är", "äir", "äi", "äit", "äad", "ädar"],
                    ["ät", "ädan", "ädav", "äda", "ädar", "ädir", "ädi", "ädat", "ädid", "äddar"]],
                3: [["", "in", "iv", "ia", "ir", "air", "ii", "it", "iad", "inar"],
                    ["ät", "ädan", "ädav", "äda", "ädar", "ädir", "ädi", "ädat", "ädid", "äddar"]],
                4: [["", "en", "ev", "ee", "er", "our", "ei", "et", "ead", "enar"],
                    ["on", "onan", "onav", "onu", "onor", "onir", "oni", "onat", "onid", "onnar"]],
                5: [["", "on", "ov", "ou", "or", "our", "oi", "ot", "oad", "odar"],
                    ["on", "onan", "onav", "onu", "onor", "onir", "oni", "onat", "onid", "onnar"]],
                6: [["", "un", "uv", "uu", "ur", "uar", "uri", "ut", "uad", "udar"],
                    ["as", "azan", "azav", "azu", "azur", "azir", "azi", "azat", "azid", "azdar"]],
                7: [["", "un", "uv", "u", "ur", "uar", "i", "ut", "ad", "tar"],
                    ["as", "azan", "azav", "azu", "azur", "azir", "azi", "azat", "azid", "azdar"]],
            }
            _s, _p = endings[declension]  # Singular and Plural endings
            if word == "riadus":
                _p = endings[1][1]
            for i in range(1, len(cases)):
                singular[i] += _s[i - 1]
                plural[i] += _p[i - 1]
                singular[i] = singular[i].replace("aaa", "aata").replace("iii", "iiti").replace("eee", "eete").replace("iia", "iita").replace("auu", "ausu") \
                                         .replace("euu", "eusu").replace("iuu", "iusu").replace("uuu", "uusu")
            # if word == "regaus":
            #    singular[10] = "regaustar"
            case_len, sin_len, plu_len = [len(i) for i in cases], [len(i) for i in singular], [len(i) for i in plural]
            case_fill, sin_fill, plu_fill = max(case_len), max(sin_len), max(plu_len)
            outputs = []
            for i in range(len(cases)):
                case, sin, plu = cases[i], singular[i], plural[i]
                outputs.append(f"{case:<{case_fill}} | {sin:>{sin_fill}} | {plu:>{plu_fill}}")
            output = "\n".join(outputs)
            image = Image.new("RGB", (2000, 2000), (0, 0, 0))
            width, height = ImageDraw.Draw(image).textsize(output, font=font)
            image = image.resize((width + 10, height + 15))
            draw = ImageDraw.Draw(image)
            draw.text((10, 0), output, fill=(255, 255, 255), font=font)
            bio = BytesIO()
            image.save(bio, "PNG")
            bio.seek(0)
            return await general.send(f'Declension for word "{word}"', ctx.channel, file=discord.File(bio, "declension.png"))

    @rsl1_decline.command(name="adjectives", aliases=["a", "adj"])
    async def rsl1_decl_adjectives(self, ctx: commands.Context, word: str = None):
        """ How RSL-1 adjectives work """
        return await general.send("Coming later. Insert that you can convert adjectives to adverbs by replacing -ar with -i", ctx.channel)

    @rsl1_decline.command(name="verbs", aliases=["v", "conjugations", "c"])
    async def rsl1_decl_verbs(self, ctx: commands.Context, word: str = None):
        """ How RSL-1 verb conjugations work """
        return await general.send("Coming later.", ctx.channel)

    @rsl1.group(name="words", aliases=["w", "dictionary", "dict", "d"])
    @commands.is_owner()
    async def rsl1_dict(self, ctx: commands.Context):
        """ RSL-1 word changing thingies """
        if ctx.invoked_subcommand is None:
            await general.send("This command is the list of words of RSL-1.\nOrder: 0 = A-Z by English translation, 1 = A-Z by RSL-1 word", ctx.channel)
            return await ctx.send_help(str(ctx.command))

    @rsl1_dict.command(name="nouns", aliases=["n"])
    # turn them into arguments: --order, --search, --page
    async def rsl1_nouns(self, ctx: commands.Context, order: int = 0, search: str = ""):
        """ RSL-1 nouns dictionary """

    @rsl1_dict.command(nname="adjectives", aliases=["a", "adj"])
    async def rsl1_adjectives(self, ctx: commands.Context, order: int = 0, search: str = ""):
        """ RSL-1 adjectives dictionary """

    @rsl1_dict.command(nname="adverbs", aliases=["adv"])
    async def rsl1_adverbs(self, ctx: commands.Context, order: int = 0, search: str = ""):
        """ RSL-1 adverb dictionary """

    @rsl1_dict.command(nname="verbs", aliases=["v"])
    async def rsl1_verbs(self, ctx: commands.Context, order: int = 0, search: str = ""):
        """ RSL-1 verbs dictionary """

    @rsl1_dict.command(nname="small", aliases=["s"])
    async def rsl1_small_words(self, ctx: commands.Context, order: int = 0, search: str = ""):
        """ RSL-1 small words (e.g. prepositions and stuff) dictionary """

    @rsl1_dict.command(name="pronouns", aliases=["p"])
    async def rsl1_pronouns(self, ctx: commands.Context):
        """ RSL-1 pronouns """
        return await general.send("Wonders of RSL-1, there are two ways to say I. Coming later.", ctx.channel)

    @rsl1.command(name="phrases", aliases=["p", "words", "w"])
    async def rsl1_phrases(self, ctx: commands.Context):
        """ Some RSL-1 words and phrases """
        stuff = [
            ["thanks", "hallera"],
            ["please", "kinnelli"],
            ["hello", "liarustu"],
            ["good morning", "hiaran rean"],
            ["good afternoon", "hiaran sean"],
            ["good evening", "hiaran vean"],
            ["good night (greeting)", "hiaran tean"],
            ["good night, sleep well", "hiaran sehlun"],
            ["goodbye", "lankuvurru"],
            ["good luck", "ivjar lettuman"],
            ["idiot, cunt, and other synonyms", "arhaneda"],
            ["worst person ever or something", "igvalarhaneda"],
            ["I love you", "sa/mu leivaa tu"],
            ["I like you", "sa/mu altikaa tu"],
            ["I hate you", "sa/mu delvaa tu"],
            ["what do you want", "ne kaidas"],
            ["you are cute", "te jas millar/leitakar"],
            ["you are beautiful/hot", "te jas leidannar"],
            ["you are ugly", "te jas arkantar"],
            ["I am 7 years old", "sa/muv ivja 7 kaadazan si"],
            ["yes", "to"],
            ["no", "des"],
            ["die in a fire", "senardar aigynnuri"],
            ["I don't care", "e jat sav/muv vuntevo"],
            ["I couldn't care less", "e ar de maikat sav/muv kuvuntevo vian"],
            ["congrats", "nilkirriza"],
            ["heaven, paradise", "Naivur"],
            ["hell", "Eideru/Eilarru"],
            ["school", "eitaru"],
            ["happy birthday", "kovanan reidesean"],
            ["Happy Halloween", "Kovanan Savainun"],
            ["Happy New Year", "Kovanan Nuan Kaadun"],
            ["Merry Christmas", "Kovanon Raivasten"],
            ["son of a bitch", "seijanseunu"],
            ["fuck off/fuck you", "heilarsa"],
            ["I'm on her", "naa an aan"],
            ["Senko Lair", "Senkadar Laikadu"]
        ]
        stuff.sort(key=lambda x: x[0].lower())
        output = [f'{en} = {rsl}' for en, rsl in stuff]
        return await general.send("A dictionary-like thing is coming soon, but here are some things you can say in RSL-1:\n" + "\n".join(output) +
                                  "\nNote on wonders of RSL-1 - there are 2 words for 'I', yes.", ctx.channel)

    @commands.command(name="ga78")
    @commands.check(lambda ctx: ctx.author.id in [302851022790066185, 291665491221807104])
    async def ga78_info(self, ctx: commands.Context, ss: int = None, p: int = None):
        """ Details on GA-78
         ss = solar system """
        data = json.loads(open("cobble/utils/ga78.json").read())
        if ss is None:  # Solar system not specified
            systems = []
            for number, system in data.items():
                systems.append(f"SS-{number}: {system['name']}")
            return await general.send(f"Here is the list of all solar systems. For details on a specific one, enter `{ctx.prefix}{ctx.invoked_with} x` "
                                      f"(replace x with system number)", ctx.channel, embed=discord.Embed(colour=0xff0057, description="\n".join(systems)))
        try:
            system = data[str(ss)]
        except KeyError:
            return await general.send(f"No data is available for SS-{ss}.", ctx.channel)
        if p is None:
            sun = system["sun"]
            output = f"Sun:\nName in RSL-1: {sun['name']}\n"
            mass = sun['mass']  # Mass
            lum = mass ** 3.5   # Luminosity
            d = mass ** 0.74    # Diameter
            st = mass ** 0.505  # Surface temperature
            lt = mass ** -2.5   # Lifetime
            output += f"Mass: {mass:.2f} Solar\nLuminosity: {lum:.2f} Solar\nDiameter: {d:.2f} Solar\nSurface Temp.: {st:.2f} Solar\nLifetime: {lt:.2f} Solar" \
                      f"\n\nPlanets:\n"
            planets = []
            for number, planet in system["planets"].items():
                planets.append(f"{number}) {planet['name']}")
            output += "\n".join(planets)
            return await general.send(f"Here is the data on SS-{ss}. For details on a specific planet, use `{ctx.prefix}{ctx.invoked_with} {ss} x`\n"
                                      f"__Note: Yes, planet numbers start from 2. That is because the star was counted as the number 1.__",
                                      ctx.channel, embed=discord.Embed(colour=0xff0057, description=output))
        try:
            planet = system["planets"][str(p)]
        except KeyError:
            return await general.send(f"No data is available for planet {p} of SS-{ss}.", ctx.channel)
        output = f"Name in RSL-1: {planet['name']}\nLocal name(s): {planet['local']}\n"
        output += f"Distance from sun: {planet['distance']:.2f} AU\nAverage temperature: {planet['temp']:.2f}°C\n"
        day = planet["day"]
        days = day / 24
        year = planet["year"]
        years = year / 365.256
        local = year / days
        output += f"Day length: {day:,.2f} Earth hours ({days:,.2f} Earth days)\n"
        output += f"Year length: {year:,.2f} Earth days ({years:,.2f} Earth years) | {local:,.2f} local solar days"
        return await general.send(f"Information on planet `87.78.{ss}.{p}`:", ctx.channel, embed=discord.Embed(colour=0xff0057, description=output))


def setup(bot):
    bot.add_cog(GA78(bot))
