import json
from datetime import datetime, timezone
from io import BytesIO
from math import ceil

import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

from cobble.utils import ss23, ss24
from core.utils import arg_parser, emotes, general, time


def is_rsl1_eligible(ctx):
    if ctx.author.id not in [302851022790066185, 291665491221807104, 230313032956248064, 430891116318031872, 418151634087182359, 374853432168808448,
                             593736085327314954, 581206591051923466]:
        return False
    if ctx.guild is None:
        return True
    else:
        return ctx.channel.id in [610482988123422750, 787340111963881472, 725835449502924901, 742885168997466196, 798513492697153536, 672535025698209821,
                                  799714065256808469]


def rsl_number(value: int):
    """ Convert number to RSL-1 """
    limit = int("9" * 36)
    if value > limit:
        return f"Highest allowed number is {limit:,} (1e36 - 1)"
    if value < 0:
        return f"Negative values will not work"
    if value == 0:
        return "deneda"
    one = {0: "", 1: "ukka", 2: "devi", 3: "tei", 4: "sei", 5: "paa/paki", 6: "senki", 7: "ei", 8: "oni", 9: "zehi"}
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


def load_rsl1(key: str, order: int) -> list:
    _data = json.loads(open("cobble/utils/rsl-1.json", "r").read())
    data = _data[key]
    data.sort(key=lambda entry: entry[order].lower())
    return data


def rsl1_args(text: str):
    """ Interpret RSL-1 args """
    parser = arg_parser.Arguments()
    parser.add_argument('-s', '--search', nargs="+", default="")
    parser.add_argument('-o', '--order', nargs=1, default=0)
    parser.add_argument('-p', '--page', nargs=1, default=1)
    args, valid = parser.parse_args(text)
    if valid and type(args.search) == list:
        args.search = " ".join(args.search)
    return args, valid


async def rsl1_args_handler(ctx: commands.Context, args: str, key: str):
    args, valid = rsl1_args(args)
    if not valid:
        return await general.send(args, ctx.channel)
    stuff = load_rsl1(key, args.order)
    # return stuff, args.search, args.page, True
    if args.page < 1:
        return await general.send("Page must be a number above 1.", ctx.channel)
    if args.order not in [0, 1]:
        return await general.send("Order must be either 0 or 1.", ctx.channel)
    _min = (args.page - 1) * 20
    _max = args.page * 20
    _stuff = []
    for rsl1, en in stuff[_min:_max]:
        if args.search:
            if args.search in rsl1 or args.search in en:
                _stuff.append(f"{en} = {rsl1}" if args.order == 0 else f"{rsl1} = {en}")
        else:
            _stuff.append(f"{en} = {rsl1}" if args.order == 0 else f"{rsl1} = {en}")
    _len = ceil(len(stuff) / 20)
    _search = f"Search `{args.search}`" if args.search else "No search term"
    output = f"RSL-1 {key.replace('_', ' ').title()} - {_search} - Page {args.page} of {_len}\n"
    output += "\n".join(_stuff)
    return await general.send(output, ctx.channel)


rsl1_pronunciation = """This is how RSL-1 was intended to sound.
Format: Letter - IPA - English Approximation
A - [a] or [ɑ] - ah
B - [b] - b
C - [ts] - Japanese "tsunami", Russian "tsar"
D - [d] - d
E - [ɛ] or [e] - 'eh', the 'e' in 'bed'
F - [f] - f
G - [g] - g
H - [x] or [h] - 'h' in words like 'hello', 'ch' in 'loch', often written as 'kh'
I - [i] or [ɪ] - 'ee' in 'free'
J - [j] - 'y' in 'yeah'
K - [k] - k
L - [l] - l
M - [m] - m
N - [n] - n
O - [o] or [ɔ] - 'o' in 'not'
P - [p] - p
Q - [ʒ] or [ʐ] - zh, 's' in 'vision'
R - [r] or [ɾ] or [ɹ] - however you pronounce the letter 'r'
S - [s] - s
T - [t] - t
U - [u] - 'oo' in words like 'book', 'boot'
V - [v] - v
X - [ɕ] or [ç] - Russian 'щ', 'ch' in German 'ich', 'nicht'
Y\\* - [e] - 'eh', but 'softens' previous consonant
Z - [z] - z
Ä\\* - [æ] - the 'a' in 'at', Finnish 'ä'
Ö\\* - [ø] - like German and Finnish 'ö'
Ü\\* - [y] - English 'ew', German 'ü', Finnish 'y'

Letter combinations:
sh - [ʃ] or [ʂ] - sh
ch - [tʃ] or [tɕ] - ch (does not occur in any RSL-1e words as of right now, but was present in earlier versions)
gh - [ɣ] - not present in English | a sound similar to 'g', and the voiced version of [x] (the Russian h)

\\*Note: after ä, ö, ü and y, the preceding consonants is supposed to become a 'soft consonant' - something you don't have in English.
It's like the 'n' in Russian 'niet'

The stress in the word is usually on the first syllable, sometimes the second. In compound words, all of the parts are stressed:
seijantaikka - [ˌsɛj:an'tajk:a] (compound word from 'seija' and 'taikka')

`´` (á, é, í, ó, ú) simply denote the stressed syllable(s) in a word and is entirely optional for use.

There are some of the exceptions to the spelling system:
`ke` and `ge` and pronounced as if they were `ky` and `gy` ([kʲe] and [gʲe]) - but some words are still written with ky, gy"""


rsl1_grammar = ["""RSL-1 Grammar and Structure - Part 1: Nouns and adjectives
RSL-1 nouns have 3 genders:
1. Masculine - words ending with `-u` or a consonant
2. Feminine - words ending with `-a` or `-i`
3. Neuter - words ending with `-o` or -`e`
The noun's gender affects the adjective ending and the 3rd person pronoun form

Nouns and adjectives have 9 cases:
Nominative (NOM) - the subject of a sentence (I, he, we)
Accusative (ACC) - the object of a sentence (me, him, us)
Dative (DAT) - the indirect object of a sentence ("I give something **to you**")
Genitive (GEN) - English preposition 'of'
Instrumental (INS) - 'with the aid of...', 'using...', 'by...'
Comitative (COM) - '(together) with'
Abessive (ABE) - 'without', '-less'
Locative (LOC) - in, inside something
Lative (LAT) - 'towards'
Ablative (ABL) - 'away from'
These case abbreviations will be used so I don't have to write the full name of the case while writing literal translations

Nouns and pronouns also have a possessive form (like English `'s`): Regaus'ta vahtaa = vahtaa Regaus'un = Regaus' life.
Adjectives can be turned into adverbs by replacing the ending with `-i`: zeranvar = fast, quick -> zeranvi = quickly
Further data will be available on `..rsl1 changes nouns` and `..rsl1 changes adjectives`""",
                """RSL-1 Grammar and Structure - Part 2: Verbs
RSL-1 verbs change for person and tense.
They have separate endings, depending on who does the action. (Like German, Russian, Finnish and many other languages)
They are then followed by a suffix for tense.
RSL-1 distinguishes 4 tenses:
Present - Something happens or is happening
Past - Something happened or was happening
Future - Something will happen
Conditional - Something would happen

In the past tense, the verb also has a prefix if the action is complete. The incomplete form usually corresponds to the English "was ...-ing" form of the verb.
paikaillan = to happen -> paikallak = was happening -> kipaikallak = happened

They also have an imperative form (e.g. "Do this!")
dejan = to do -> dejar = do

For reflexive verbs (doing something to oneself), most of the time they have a `-sa` suffix. 
kiltastan = to prepare (something) -> kiltastansa = to prepare (oneself)

If you want to form a yes/no question from the verb, you can do so with a `-ta`/`-da` suffix.
hideran = to create -> mu hiderava = I will create -> hideravada mu? = will I create?
ittean = to go -> te itteas = you go/you are going -> itteasta? - are you going?

Some verbs have separable prefixes like German.
Further data will be available on `..rsl1 changes verbs`""",
                """RSL-1 Grammar and Structure - Part 3: Participles and Converbs
RSL-1 also has participles and converbs. Participles are used for passive constructions.
As participles also act like adjectives, you can drop "the one who is..." part of the sentence. (This works like in Russian.)
From dejan - to do, you can form:
Active participles:
dejannar = doing (делающий)
dejadar = (the one who) was doing (делавший)
kidejadar = (the one who) has/had done (сделавший)

Passive participles:
dejamar = doable, or (something that) is done (делаемый)
dejattar = (something that) was being done (деланный)
kydejattar = (something that) was/has been done (сделанный)

Converbs:
dejavi - while doing (делая)
deijad - having done (сделав)""",
                """RSL-1 Grammar and Structure - Part 4: Syntax and sentence structure
The basic word order is SVO, similar to English, German, or Russian:
Mu saiqanara = I exist
Mu deja nedaa = I do something
Mu kihittak tev uu aivallou = I gave you an apple
It is, however, flexible if you want to emphasise a specific part of the sentence:
An daa saidalluu naat ua liarta = There is a book on the table (lit. On the table is a book)

For questions, the word order is also similar to English and Russian:
Dejada mu edou? = Am I doing this?
Ne kaidas (te)? = What do you want?
Nai naat on zeide? = Why is he here?

To negate a sentence, you can use the negative particle `de` (= "not"):
Mu de zaiva idou = I don't know what
For the verbs "to be", just the word is enough:
On de Regaus = He's not Regaus (lit. he not Regaus)

There is no verb form or construction for impersonal commands (such as "Let's go") at the moment, however you can use other verbs of similar meaning:
Me taitan zeidead ittean = We should go away from here""",
                """RSL-1 Grammar and Structure - Part 5: Compound and complex sentences
Compound sentences are formed similar to English and Russian:
An naat zeide, no mu de haida aan zeide veitean - She is here, but I don't want to see her here
lit. She is here, but I not want her here see

Mu ivja ei kaadazan si u haida kedaa murannan - I am 7 years old and want to kill someone
lit. I have seven years in-self and want someone-acc kill

Var mu kaina Senkadari Laikaduri, mu kivideak vu - While I was in Senko Lair, I met you (plural)
lit. While I was Senko's-loc Lair-loc, I met you-pl.

Te saikarna zaivasva, ken mu delvaa - You will soon know, whom I hate
lit. You soon will-know, who-acc I hate

Nai haidas te zaivan, ne mu kiara? - Why do you want to know what I say?
lit. Why want you know, what-acc I say

Dar gar, nei mu vahtaa, naat kai Senkagar invamar - The city I live in is called Senkotown
lit. The city, what-loc I live, is as/like Senko-town called (pres. passive)""",
                """RSL-1 Grammar and Structure - Part 6: Numbers and Time
Numerals are followed similar to German:
6 = senki
10 = verri
16 = seneri
60 = senneire
66 = senki u senneire (lit. six and sixty)
1234 = ukka kirraa, devi arraikädan, sei u tevveire (lit. one thousand, two hundreds, four and thirty)

ukka neda = one thing - the noun is in nominative case singular when you are talking about one thing
devi nedadan = two things - the noun is in genitive case plural when you are talking about more (or less) than one thing

Mu deja devia nedadan = I am doing two things
The number takes the accusative case (as the two things are the object of the sentence), while the things themselves stay in the genitive plural

However, if you are talking about one thing, both the number and the thing will take the accusative case:
Mu deja ukkaa nedaa = I am doing one thing

This is how to tell time:
Esea naat na devveirede Navattun na 1745'dan kaadun, esaa naat ukka u devveire saadan u tei u sevveire arhasaadan
Today is the 20th of January 1745, right now it's 21:43
lit. Today is the 20th-nom January-gen the 1745th-gen year-gen, now is 1 and 20-nom hours-gen and 3 and 40-nom minutes-gen 

devveiredei Navattun na 1745'dan kaadun, ij ukka u devveirei saadan u tei u sevveirei arhasaadan
on the 20th of January 1745, at 21:43
lit. 20th-loc January-gen the 1745th-gen year-gen, at 1 and 20-loc hours-gen and 3 and 40-loc minutes-gen"""]


rsl1_pronouns = """Pronouns           | 1sg     | 2sg   | 3sg m | 3sg f | 3sg n | 1pl i  | 1pl e  | 2pl   | 3pl   | self   | what   | who
English            | I       | you   | he    | she   | it    | we*    | we*    | you   | they  | self   | what   | who
Nominative         | mu      | te    | on    | an    | e/en  | me     | ma     | ve    | in    | se     | ne     | ke
Accusative         | mut/mun | tu    | ou    | aan   | ev/en | men    | man    | vu    | if    | su/sa  | ne/nea | kea/ken/ku
Dative             | muv     | tev   | ov    | aav   | ev    | mev    | mav    | vev   | iv    | sev    | nev    | kev
Genitive           | mun     | ta    | óan   | aan   | en    | men    | man    | va    | ían   | sa     | nen    | ken
Instrumental       | mur     | ter   | or    | ar    | er    | mer    | mar    | ver   | íur   | ser    | ner    | ker
Comitative         | muar    | tear  | oor   | aar   | ear   | meir   | mair   | veir  | iin   | seir   | near   | kear
Abessive           | muh     | tah   | oh    | ah    | eh    | meh    | mah    | vah   | ih    | sah    | neh    | kah
Locative           | mi      | ti    | oi    | ai    | ei    | mei    | mai    | vi    | ii    | si/sei | nei    | kei
Lative             | mut     | tet   | ot    | at    | et    | met    | mat    | vet   | it    | set    | net    | ket
Ablative           | muad    | tead  | oad   | aad   | ead   | mead   | maad   | vead  | íad   | sead   | nead   | kead
Possessive         | munnar  | tar   | onnar | annar | ennar | mennar | mannar | var   | innar | sar    | nennar | kennar"""


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
    @commands.check(is_rsl1_eligible)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def rsl1(self, ctx: commands.Context):
        """ RSL-1 data

        This is the command that can try to explain how RSL-1 works and what is going on here.
        **Warning: While I don't mind if you speak the language, or even have your custom status in it,
        I do __not__ want the RSL-1 translations to be shared outside of this channel or DMs (with me or others in this channel) without my permission**
        (Basically: do whatever you want with RSL-1, just don't share the translations with people not here) """
        if ctx.invoked_subcommand is None:
            # await general.send("", ctx.channel)
            return await ctx.send_help(str(ctx.command))

    @rsl1.command(name="numbers", aliases=["n", "number"])
    async def rsl1_numbers(self, ctx: commands.Context, number: int = None):
        """ Translate a number to RSL-1 """
        if number is None:
            return await general.send(f"This command can translate a number to RSL-1. For example, `{ctx.prefix}rsl1 {ctx.invoked_with} 1` "
                                      f"will translate the number 1 to RSL-1.", ctx.channel)
        return await general.send(f"{number:,} = {rsl_number(number)}", ctx.channel)

    @commands.is_owner()
    @rsl1.group(name="changes", aliases=["declensions", "decline", "conjugations", "conjugate", "c"])
    async def rsl1_decline(self, ctx: commands.Context):
        """ RSL-1 word changing thingies (WIP)

        Shows how the RSL-1 words change in different places and contexts """
        if ctx.invoked_subcommand is None:
            # await general.send("This command will show you how the RSL-1 words change in different places", ctx.channel)
            return await ctx.send_help(str(ctx.command))

    @rsl1_decline.command(name="nouns", aliases=["declensions", "decline", "n"])
    async def rsl1_decl_nouns(self, ctx: commands.Context, word: str):
        """ RSL-1 noun declensions """
        font = ImageFont.truetype("assets/mono.ttf", size=64)
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
                                     .replace("euu", "eusu").replace("iuu", "iusu").replace("uuu", "uusu").replace("eaa", "eata")
        # if word == "regaus":
        #    singular[10] = "regaustar"
        case_len, sin_len, plu_len = [len(i) for i in cases], [len(i) for i in singular], [len(i) for i in plural]
        case_fill, sin_fill, plu_fill = max(case_len), max(sin_len), max(plu_len)
        outputs = []
        for i in range(len(cases)):
            case, sin, plu = cases[i], singular[i], plural[i]
            outputs.append(f"{case:<{case_fill}} | {sin:<{sin_fill}} | {plu:<{plu_fill}}")
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
    async def rsl1_decl_adjectives(self, ctx: commands.Context, word: str):
        """ How RSL-1 adjectives work """
        return await general.send("Coming later. Insert that you can convert adjectives to adverbs by replacing -ar with -i" + word, ctx.channel)

    @rsl1_decline.command(name="verbs", aliases=["v", "conjugations", "c"])
    async def rsl1_decl_verbs(self, ctx: commands.Context, word: str):
        """ How RSL-1 verb conjugations work """
        return await general.send("Coming later." + word, ctx.channel)

    @rsl1.group(name="words", aliases=["w", "dictionary", "dict", "d"])
    # @commands.is_owner()
    async def rsl1_dict(self, ctx: commands.Context):
        """ Lists RSL-1 words

        Commands' arguments:
            `--search`, `-s`: Search for words containing the search string
            `--order`, `-o`: 0 = A-Z by English translation, 1 = A-Z by RSL-1 word
            `--page`, `-p`: The page of the output """
        if ctx.invoked_subcommand is None:
            # await general.send("", ctx.channel)
            return await ctx.send_help(str(ctx.command))

    @rsl1_dict.command(name="nouns", aliases=["n"])
    # turn them into arguments: --order, --search, --page
    async def rsl1_nouns(self, ctx: commands.Context, *, args: str = ""):
        """ RSL-1 nouns dictionary """
        # return await general.send(rsl1_args(args), ctx.channel)
        # stuff = load_rsl1()["nouns"]
        return await rsl1_args_handler(ctx, args, "nouns")

    @rsl1_dict.command(name="adjectives", aliases=["a", "adj"])
    async def rsl1_adjectives(self, ctx: commands.Context, *, args: str = ""):
        """ RSL-1 adjectives dictionary """
        # stuff = load_rsl1()["adjectives"]
        return await rsl1_args_handler(ctx, args, "adjectives")

    @rsl1_dict.command(name="adverbs", aliases=["adv"])
    async def rsl1_adverbs(self, ctx: commands.Context, *, args: str = ""):
        """ RSL-1 adverb dictionary """
        # stuff = load_rsl1()["adverbs"]
        return await rsl1_args_handler(ctx, args, "adverbs")

    @rsl1_dict.command(name="verbs", aliases=["v"])
    async def rsl1_verbs(self, ctx: commands.Context, *, args: str = ""):
        """ RSL-1 verbs dictionary """
        # stuff = load_rsl1()["verbs"]
        return await rsl1_args_handler(ctx, args, "verbs")

    @rsl1_dict.command(name="small", aliases=["s", "smallwords"])
    async def rsl1_small_words(self, ctx: commands.Context, *, args: str = ""):
        """ RSL-1 small words (e.g. prepositions and stuff) dictionary """
        # stuff = load_rsl1()["small_words"]
        return await rsl1_args_handler(ctx, args, "small_words")

    @rsl1_dict.command(name="pronouns", aliases=["p"])
    async def rsl1_pronouns(self, ctx: commands.Context):
        """ RSL-1 pronouns """
        font = ImageFont.truetype("assets/mono.ttf", size=64)
        image = Image.new("RGB", (2000, 2000), (0, 0, 0))
        width, height = ImageDraw.Draw(image).textsize(rsl1_pronouns, font=font)
        image = image.resize((width + 10, height + 15))
        draw = ImageDraw.Draw(image)
        draw.text((10, 0), rsl1_pronouns, fill=(255, 255, 255), font=font)
        bio = BytesIO()
        image.save(bio, "PNG")
        bio.seek(0)
        return await general.send(f"RSL-1 Pronouns\n\\*Inclusive 'we' is when you are talking about 'me', 'you' (and possibly someone else) - so, 1st, 2nd "
                                  f"(and 3rd) persons\nExclusive 'we' is when you're talking about 'me' and someone else - so, only 1st and 3rd persons\n\n"
                                  f"For the declension of the possessive forms, see `..rsl1 changes adjectives`",
                                  ctx.channel, file=discord.File(bio, "pronouns.png"))
        # return await general.send("Coming later.", ctx.channel)

    @rsl1.command(name="phrases", aliases=["p"])
    async def rsl1_phrases(self, ctx: commands.Context):
        """ Some RSL-1 words and phrases """
        stuff = load_rsl1("phrases", 0)
        # stuff.sort(key=lambda x: x[0].lower())
        output = [f'{en} = {rsl}' for en, rsl in stuff]
        return await general.send("Certain phrases you can say in RSL-1:\n" + "\n".join(output), ctx.channel)

    @rsl1.command(name="pronunciation")
    async def rsl1_pronunciations(self, ctx: commands.Context):
        """ How RSL-1 is intended to sound """
        return await general.send(rsl1_pronunciation, ctx.channel)

    @rsl1.command(name="grammar")
    async def rsl1_grammar(self, ctx: commands.Context, page: int = 0):
        """ RSL-1 grammar and structure (split into several parts) """
        pages = len(rsl1_grammar)
        if 1 <= page <= pages:
            return await general.send(rsl1_grammar[page - 1], ctx.channel)
        else:
            parts = [part.splitlines()[0].replace("RSL-1 Grammar and Structure - ", "") for part in rsl1_grammar]
            return await general.send(f"There are currently {pages} parts/pages of information about RSL-1 grammar and structure:\n" +
                                      "\n".join(parts), ctx.channel)

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
