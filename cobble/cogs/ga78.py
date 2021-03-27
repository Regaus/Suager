import json
from datetime import datetime, timezone
from io import BytesIO
from math import ceil

import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

from cobble.utils import ga78
from core.utils import arg_parser, emotes, general, time
from languages import langs


def is_rsl1_eligible(ctx: commands.Context):
    if ctx.author.id not in [302851022790066185, 291665491221807104, 430891116318031872, 418151634087182359, 374853432168808448,
                             593736085327314954, 581206591051923466, 499038637631995906, 679819572278198272, 236884090651934721]:
        return False
    if ctx.guild is None:
        return True
    else:
        return ctx.channel.id in [610482988123422750, 787340111963881472, 725835449502924901, 742885168997466196, 798513492697153536, 672535025698209821,
                                  799714065256808469, 753000962297299005]


def rsl_number(value: int):
    """ Convert number to RSL-1 """
    limit = int("9" * 36)
    if value > limit:
        return f"Highest allowed number is {limit:,} (1e36 - 1)"
    if value < 0:
        return "Negative values will not work"
    if value == 0:
        return "deneda"
    one = {0: "", 1: "ukka", 2: "devi", 3: "tei", 4: "sei", 5: "paa/paki", 6: "senki", 7: "ei", 8: "oo/oni", 9: "zee/zehi"}
    teen = {11: "uveri", 12: "deveri", 13: "teveri", 14: "severi", 15: "paveri", 16: "seneri", 17: "eijeri", 18: "overi", 19: "zegheri"}
    ten = {1: "verri", 2: "devveire", 3: "tevveire", 4: "sevveire", 5: "pavveire", 6: "senneire", 7: "evveire", 8: "onneire", 9: "zegheire"}
    _21 = {0: "", 1: "ukku", 2: "deu", 3: "teiju", 4: "seiju", 5: "pau", 6: "senku", 7: "eiju", 8: "ou", 9: "zeu"}
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
            _99v = f"{_21[_u]}{ten[_v]}" if _u > 0 else ten[_v]
            # _99v = f"{one[_u]} u {ten[_v]}" if _u > 0 else ten[_v]
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
            n1, n2 = exp_1000 if i == 0 else ((_name := exp[i - 1]), _name[:-1] + "adan")
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
    if valid:
        if type(args.search) == list:
            args.search = " ".join(args.search)
        if type(args.page) != int:
            args.page = int(args.page[0])
        if type(args.order) != int:
            args.order = int(args.order[0])
        # print(args.search, args.page, args.order)
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
    # for en, rsl1 in stuff[_min:_max]:
    for en, rsl1 in stuff:
        if args.search:
            if args.search.lower() in rsl1.lower() or args.search.lower() in en.lower():
                _stuff.append(f"{en} = {rsl1}" if args.order == 0 else f"{rsl1} = {en}")
        else:
            _stuff.append(f"{en} = {rsl1}" if args.order == 0 else f"{rsl1} = {en}")
    _len = ceil(len(_stuff) / 20)
    _stuff = _stuff[_min:_max]  # cut it to only 20 words
    _search = f"Search `{args.search}`" if args.search else "No search term"
    output = f"RSL-1 {key.replace('_', ' ').title()} - {_search} - Page {args.page} of {_len}\n"
    output += "\n".join(_stuff)
    if _len == 0:
        output += "\nIt seems that nothing was found. The word might not exist. Try searching similar words or ask Regaus."
    return await general.send(output, ctx.channel)


rsl1_pronunciation = """This is how RSL-1 was intended to sound.
Format: Letter - IPA - English Approximation
A - [a] or [ɑ] - ah
B - [b] - b
C - [ts] - 'ts' in Japanese "tsunami" or 'ц' in Russian "царь/tsar"
D - [d] - d
E - [ɛ] or [e] - 'eh', the 'e' in 'bed'
F - [f] - f
G - [g] - g
H - [x] or [h] - 'h' in words like 'hello', more closely 'ch' in 'loch', Russian `х`, often written as 'kh'
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
X - [ɕ] or [ç] - Russian 'щ', 'ch' in some pronunciations of German 'ich', 'nicht'
Y\\* - [e] - 'eh', but 'softens' previous consonant
Z - [z] - z
Ä\\* - [æ] - the 'a' in 'at', Finnish 'ä'
Ö\\* - [ø] - like German and Finnish 'ö'
Ü\\* - [y] - English 'ew', German 'ü', Finnish 'y'

Letter combinations:
sh - [ʃ] or [ʂ] - sh
ch - [tʃ] or [tɕ] - ch
gh - [ɣ] - not present in English | a sound similar to 'g', and the voiced version of [x] (the Russian h)
kh - [x] - same as `h`

\\*Note: after ä, ö, ü and y, the preceding consonants is supposed to become a 'soft consonant' - something you don't have in English.
It's like the 'n' in Russian 'niet'

The stress in the word is usually on the first syllable, sometimes the second. In compound words, all of the parts are stressed:
seijantaikka - [ˌsɛj:an'tajk:a] (compound word from 'seija' and 'taikka')

`´` (á, é, í, ó, ú) simply denote the stressed syllable(s) in a word and is entirely optional for use."""


rsl1_grammar = ["""RSL-1 Grammar and Structure - Part 1: Nouns and adjectives
RSL-1 nouns have 3 genders:
1. Masculine - words ending with `-u` or a consonant
2. Feminine - words ending with `-a` or `-i`
3. Neuter - words ending with `-o` or -`e`
The noun's gender affects the adjective ending and the 3rd person pronoun form

Nouns and adjectives have 10 cases:
Nominative (NOM) - the subject of a sentence (I, he, we)
Genitive (GEN) - basically, 'of'
Dative (DAT) - the indirect object of a sentence ("I give something **to you**")
Accusative (ACC) - the object of a sentence (me, him, us)
Instrumental (INS) - 'with the aid of...', 'using...', 'by...'
Comitative (COM) - '(together) with'
Abessive (ABE) - 'without', '-less'
Locative (LOC) - 'in', inside something
Lative (LAT) - 'towards'
Ablative (ABL) - 'away from'
The case name abbreviations will be used so I don't have to write the full name of the case in the sentence structure

Nouns and pronouns also have a possessive form (like English `'s`), like this: Regaus'ta vahtaa = vahtaa Regaus'an = Regaus' life.
Adjectives can be turned into adverbs by replacing the ending with `-i`: zeranvar = fast, quick -> zeranvi = quickly
To decline a certain noun or adjective, use `..rsl1 changes nouns` and `..rsl1 changes adjectives`

For adjectives, you can add `ku-` for the `-er` form (e.g. millar = cute -> kumillar = cuter), `iga-` for `-est` (igamillar = cutest)""",
                """RSL-1 Grammar and Structure - Part 2: Verbs
RSL-1 verbs change for person and tense. The person is usually only marked in the present tense.

RSL-1 distinguishes 4 tense forms:
Present - Something happens or is happening
Past - Something happened or was happening
Future - Something will happen
Conditional - Something would happen

In the past tense, the verb gets a prefix if the action is complete. The incomplete form usually corresponds to the English "was ...-ing" form of the verb.
paikallan = to happen -> paikallah = was happening -> paikallak = happened

They also have an imperative form (commands, for example "Do this!")
dejan = to do -> dejar = do (to one person), dejart = do (to multiple people)

For reflexive verbs (doing something to oneself), most of the time they have a `-sa` suffix. 
kiltastan = to prepare (something) -> kiltastansa = to prepare (oneself)

If you want to form a yes/no question from the verb, you can do so with a `-ta`/`-da` suffix.
hideran = to create -> mu hiderava = I will create -> hideravada mu? = will I create?
ittean = to go -> te itteas = you go/are going -> itteasta? - are you going?

To conjugate a certain verb, ~~just ask Regaus, that shit is a fucking mess~~ use `..rsl1 changes verbs`""",
                """RSL-1 Grammar and Structure - Part 3: Participles and Converbs
RSL-1 also has participles and converbs. Participles are used for passive constructions.
As participles also act like adjectives, you can drop "the one who is..." part of the sentence. (This works kinda like in Russian.)
From dejan - to do, you can form:
Active participles:
dejannar = doing (делающий)
dejattar = (the one who) was doing (делавший)
dejadar = (the one who) has/had done (сделавший)

Passive participles:
dejamar = doable, or (something that) is being done (делаемый)
dejaghar = (something that) was being done (деланный)
dejakar = (something that) was/has been done (сделанный)

Converbs:
dejavi - while doing (делая)
deijad - having done (сделав)""",
                """RSL-1 Grammar and Structure - Part 4: Basic syntax and sentence structure
The basic word order is SVO (Subject-Verb-Object):
Mu saiqanara = I exist
Mu deja nedaa = I do something
Mu hittak tev uu aivallou = I gave you an apple
The word order in the above sentences matches the English.

The order is, however, somewhat flexible if you want to emphasise or focus on a specific part of the sentence:
An na saidalluu naat ua liarta = There is a book on the table (lit. On the table is a book)
Ua liarta naat an na saidalluu = There is a book on the table (lit. A book is on the table)
In the first sentence the focus is on the table, while the second one focuses on the book.

For questions, the word order is also similar to English:
Dejada mu edou? = Am I doing this?
Ne haidas (te)? = What do you want?
Nai naat on zeide? = Why is he here?

To negate a sentence, you can use the negative particle `de` (= "not"), which is put *before* the verb:
Mu de zaiva idou = I don't know what (lit. I know not that)

For the verbs "to be", you may drop it in the present tense:
On de Regaus = He's not Regaus (lit. he not Regaus) (however "on de naat Regaus" makes sense too)
On de kaina Regaus = He wasn't Regaus (lit. he not was Regaus)

To form impersonal commands like "Let's go", you can use the (singular) imperative form together with the pronoun:
Ittear me = Let's go (lit. "Go-imp we")""",
                """RSL-1 Grammar and Structure - Part 5: Compound and complex sentences
Compound sentences are formed not too differently from European languages:
An naat zeide, no mu de haida aan zeide veitean - She is here, but I don't want to see her here
lit. She is here, but I not want her here see

Mu ivja ei kaadadan si u haida kedaa murannan - I am 7 years old and want to kill someone
lit. I have seven years in-self and want someone-acc kill

Var mu kaina Senkadari Laikaduri, mu videak vu - While I was in Senko Lair, I met you (plural)
lit. While I was Senko's-loc Lair-loc, I met you-pl.

Te saikarna zaivasva, ken mu delvaa - You will soon know, whom I hate
lit. You soon will-know, who-acc I hate

Nai haidas te zaivan, ne mu kiara? - Why do you want to know what I say?
lit. Why want you know, what-acc I say

Dar gar, nei mu vahtaa, naat kai Senkagar invamar - The city I live in is called Senkagar (Senkotown/Senko City)
lit. The city, what-loc I live, is as/like Senko-town called-pres.""",
                """RSL-1 Grammar and Structure - Part 6: Numbers
Numerals are formed similar to German:
6 = senki
10 = verri
16 = seneri
60 = senneire
66 = senkusenneire (six-and-sixty)
1234 = ukka kirraa, devi arraikädan, seijutevveire (lit. one thousand, two hundreds, four-and-thirty)
To translate a specific number to RSL-1, use `..rsl1 number <number>`

The noun is in nominative case singular when you are talking about one thing:
ukka neda = one thing

The noun is in the genitive case singular when you are talking about a fraction of a thing (more than zero, but less than one):
ua alva nedan = a half of (a) thing

The noun is in genitive case plural when you are talking about any other number of things:
ukka u ua alva nedadan = one and a half things
devi nedadan = two things

The number takes the case-marking in these forms, while the things themselves don't get changed:
Mu deja devia nedadan = I am doing two things
Mu kiara av devin nedadan = I am talking about two things

However, when talking about one thing, both the number one and the thing will take the case:
Mu deja ukkaa nedaa = I am doing one thing
Mu kaira av ukkan nedan = I am talking about one thing

little/few = virse
less = kuvirse
least = ivvirse

many/much = valse
more = kuvalse
most = ivvalse""",
                """RSL-1 Grammar and Structure - Part 7: Weird Time Things
Telling time can be a bit weird compared to English:
Esea naat na 20'de Navattun 1745 - Full: Esea naat na devveirede Navattun (na) 1745'dan (kaadun)
Today is the 20th of January 1745
lit. Today is the 20th-nom January-gen (the) 1745th-gen (year-gen)

Esaa naat 21:43 - Full: Esaa naat ukkudevveire saadan teijusevveire
It's 21:43 (right now)
lit. Now is 21-nom hours-gen 43-nom

20'i Navattun 1745 ij 21:43 - Full: Devveiredei Navattun (na) 1745'dan (kaadun), ij ukkudevveirei saadan sevveirei
on the 20th of January 1745, at 21:43
lit. 20th-loc January-gen (the) 1745th-gen (year-gen), at 21-loc hours-gen 43-loc"""]


rsl1_pronouns = """Pronouns           | 1sg     | 2sg      | 3sg m | 3sg f | 3sg n | 1pl i  | 1pl e  | 2pl      | 3pl   | self   | what   | who
English            | I       | you      | he    | she   | it    | we*    | we*    | you      | they  | self   | what   | who
Nominative         | mu      | te       | on    | an    | e/en  | me     | ma     | ve       | in    | se     | ne     | ke
Genitive           | mun     | ta       | oan   | aan   | en    | men    | man    | va       | ian   | sa     | nen    | ken
Dative             | muv     | tev      | ov    | aav   | ev    | mev    | mav    | vev      | iv    | sev    | nev    | kev
Accusative         | mut/mun | tu       | ou    | aan   | ev/en | men    | man    | vu       | if    | su/sa  | ne/nea | kea/ken/ku
Instrumental       | mur     | ter      | or    | ar    | er    | mer    | mar    | ver      | iur   | ser    | ner    | ker
Comitative         | muar    | tear     | oor   | aar   | ear   | meir   | mair   | veir     | iir   | seir   | near   | kear
Abessive           | muh     | tah      | oh    | ah    | eh    | meh    | mah    | vah      | ih    | sah    | neh    | kah
Locative           | mi      | ti       | oi    | ai    | ei    | mei    | mai    | vi       | ii    | si/sei | nei    | kei
Lative             | mut     | tet      | ot    | at    | et    | met    | mat    | vet      | it    | set    | net    | ket
Ablative           | muad    | tead/tad | oad   | aad   | ead   | mead   | maad   | vead/vad | iad   | sead   | nead   | kead
Possessive         | munnar  | tar      | onnar | annar | ennar | mennar | mannar | var      | innar | sar    | nennar | kennar"""


class GA78(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="time78", aliases=["t78"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def time78(self, ctx: commands.Context, ss: int, _date: str = None, _time: str = None):
        """ Times for GA-78
        Date format: YYYY-MM-DD
        Time format: hh:mm or hh:mm:ss (24-hour)"""
        if ss < 1 or ss > 100:
            return await general.send("The SS number must be between 1 and 100.", ctx.channel)
        if _date is None:
            dt = time.now(None)
        else:
            try:
                if not _time:
                    _time = "00:00:00"
                else:
                    _time = _time.replace(".", ":")
                    c = _time.count(":")
                    if c == 1:
                        _time = f"{_time}:00"
                dt = time.from_ts(time.get_ts(datetime.strptime(f"{_date} {_time}", "%Y-%m-%d %H:%M:%S")), None)
            except ValueError:
                return await general.send("Failed to convert date. Make sure it is in the format YYYY-MM-DD hh:mm:ss (time part optional)", ctx.channel)
        time_earth = langs.gts(dt, "en_gb", True, False, True, True, False)
        output = f"Time on this Earth (English): **{time_earth}**"
        if ss == 23:
            if dt < datetime(1686, 11, 22, tzinfo=timezone.utc):
                return await general.send(f"{emotes.Deny} SS-23 times are not available for dates earlier than **22 November 1686 AD**", ctx.channel)
            time_earth1d = langs.gts(dt, "rsl-1d", True, False, True, True, False)
            time_23_4 = ga78.time_zeivela(dt, 0).str()    # 23.4 Zeivela Local
            time_23_5d = ga78.time_kargadia(dt, 0).str()  # 23.5 Kargadia RSL-1d
            time_23_6 = ga78.time_kaltaryna(dt, 0).str()  # 23.6 Qevenerus RSL-1h
            output += f"\nTime on this Earth (RSL-1d): **{time_earth1d}**" \
                      f"\nTime on 23.4 Zeivela (Local): **{time_23_4}**" \
                      f"\nTime on 23.5 Kargadia (RSL-1d): **{time_23_5d}**" \
                      f"\nTime on 23.6 Qevenerus (RSL-1h): **{time_23_6}**"
        elif ss == 24:
            if dt < datetime(1742, 1, 28, tzinfo=timezone.utc):
                return await general.send(f"{emotes.Deny} SS-24 times are not available for dates earlier than **28 January 1742 AD**", ctx.channel)
            z = time.kargadia_convert(time.now(None))
            w = ["Senarsea", "Sillava Sea", "Sertansea", "Ahtarunsea", "Vastansea", "Hauvinsea", "Sehlunsea"]
            m = ["Vahkannun", "Navattun", "Senkavun", "Tevillun", "Leitavun", "Haltavun", "Arhanvun", "Nürivun", "Kovavun", "Eiderrun", "Raivazun", "Suvaghun"]
            time_earth1e = f"{w[z.weekday()]}, {z.day:02d} {m[z.month % 12]} {z.year}, {z.hour:02d}:{z.minute:02d}:{z.second:02d}"
            time_earth1g = langs.gts(z, "rsl-1g", True, False, True, True, False)
            time_24_4_10 = ga78.time_sinvimania(dt, 0).str()  # 24.4 Sinvimania RLC-10
            time_24_5l = ga78.time_hosvalnerus(dt, 0).str()   # 24.5 Hosvalnerus Local
            time_24_11e = ga78.time_kuastall_11(dt).str()     # 24.11 Kuastall-11 RSL-1e
            output += f"\nTime on this Earth (RSL-1e): **{time_earth1e}**" \
                      f"\nTime on this Earth (RSL-1g): **{time_earth1g}**" \
                      f"\nTime on 24.4 Sinvimania (RLC-10): **{time_24_4_10}**" \
                      f"\nTime on 24.5 Hosvalnerus (Local): **{time_24_5l}**" \
                      f"\nTime on 24.11 Kuastall (RSL-1e/g): **{time_24_11e}**"
        else:
            output += f"\nNo times are available for SS-{ss}."
        return await general.send(output, ctx.channel)

    @commands.command(name="weather78", aliases=["w78"])
    # @commands.is_owner()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def weather78(self, ctx: commands.Context, *, where: str):
        """ Weather for a place in GA78 """
        try:
            place = ga78.Place(where)
        except ga78.PlaceDoesNotExist:
            return await general.send(f"Location {where!r} not found.", ctx.channel)
        embed = place.status()
        return await general.send(None, ctx.channel, embed=embed)

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
            return await general.send("De dejava idou, no mu maikal ir te edoa kihtemal. ", ctx.channel)
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
            return await general.send("De dejava idou, no mu maikal ir te edoa kihtemal", ctx.channel)
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

    # @commands.is_owner()
    @rsl1.group(name="changes", aliases=["declensions", "decline", "conjugations", "conjugate", "c"])
    async def rsl1_decline(self, ctx: commands.Context):
        """ RSL-1 word changing thingies

        Shows how the RSL-1 words change in different places and contexts """
        if ctx.invoked_subcommand is None:
            # await general.send("This command will show you how the RSL-1 words change in different places", ctx.channel)
            return await ctx.send_help(str(ctx.command))

    @rsl1_decline.command(name="nouns", aliases=["declensions", "decline", "n"])
    async def rsl1_decl_nouns(self, ctx: commands.Context, word: str):
        """ Decline an RSL-1 noun """
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
        cases = ["Case", "Nominative", "Genitive", "Dative", "Accusative", "Instrumental", "Comitative",
                 "Abessive", "Locative", "Lative", "Ablative", "Possessive"]
        singular = ["Singular", word] + [declined] * (len(cases) - 2)
        plural = ["Plural"] + [declined] * (len(cases) - 1)
        endings = {
            1: [["", "an", "av", "aa", "ar", "air", "ah", "i", "ait", "aad", "adar"],
                ["at", "adan", "adav", "ada", "adar", "adir", "adah", "adi", "adat", "adid", "addar"]],
            2: [["", "än", "äv", "ää", "är", "äir", "äh", "i", "äit", "ääd", "ädar"],
                ["ät", "ädan", "ädav", "äda", "ädar", "ädir", "ädah", "ädi", "ädat", "ädid", "äddar"]],
            3: [["", "in", "iv", "ia", "ir", "air", "ih", "ii", "it", "iad", "idar"],
                ["ät", "ädan", "ädav", "äda", "ädar", "ädir", "ädah", "ädi", "ädat", "ädid", "äddar"]],
            4: [["", "en", "ev", "ea", "er", "our", "eh", "ei", "et", "ead", "edar"],
                ["at", "adan", "adav", "ada", "adar", "adir", "adah", "adi", "adat", "adid", "addar"]],
            5: [["", "on", "ov", "ou", "or", "our", "oh", "oi", "ot", "oad", "odar"],
                ["at", "adan", "adav", "ada", "adar", "adir", "adah", "adi", "adat", "adid", "addar"]],
            6: [["", "un", "uv", "uu", "ur", "uar", "uh", "uri", "ut", "uad", "udar"],
                ["at", "adan", "adav", "ada", "adar", "adir", "adah", "adi", "adat", "adid", "addar"]],
            7: [["", "an", "u", "a", "ur", "ar", "ah", "i", "ut", "id", "udar"],
                ["at", "adan", "adav", "ada", "adar", "adir", "adah", "adi", "adat", "adid", "addar"]],
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
        """ Forms of RSL-1 adjectives """
        font = ImageFont.truetype("assets/mono.ttf", size=64)
        word = word.lower()
        if word[-2:] != "ar" and word not in ["dar", "der", "ur"]:
            return await general.send("All RSL-1 adjectives end in -ar.", ctx.channel)
        li = -2
        # ll = word[li]  # Last letter of the word
        declined = word[:li] if word not in ["dar", "der", "ur"] else ""
        if word in ["tar", "var", "sar"]:
            declined += "ar"
        cases = ["Case", "Nominative", "Genitive", "Dative", "Accusative", "Instrumental", "Comitative", "Abessive", "Locative", "Lative", "Ablative"]
        singular = ["Masculine"] + [declined] * (len(cases) - 1)
        singular2 = ["Feminine"] + [declined] * (len(cases) - 1)
        singular3 = ["Neuter"] + [declined] * (len(cases) - 1)
        plural = ["Plural"] + [declined] * (len(cases) - 1)
        if word in ["tar", "var", "sar"]:
            singular[1] = word[:li]
        endings = [
            ["ar", "an", "av", "aa", "aar", "aur", "ah", "ari", "art", "arad"],
            ["a", "an", "av", "aa", "aar", "air", "ah", "ai", "at", "aad"],
            ["o", "on", "ov", "ou", "or", "our", "oh", "oi", "ot", "oud"],
            ["an", "anan", "anav", "ana", "anar", "anir", "anah", "ani", "anat", "anid"]
        ]
        dar = [
            ["dar", "dan", "dav", "daa", "daar", "daur", "dah", "dari", "dart", "daad"],
            ["da", "dan", "dav", "dan", "daar", "dair", "dah", "dai", "dat", "daad"],
            ["da", "dan", "dav", "dau", "dor", "dour", "dah", "dai", "dat", "daad"],
            ["dan", "danan", "danav", "dana", "danor", "danir", "danah", "dani", "danat", "danid"]
        ]
        der = [
            ["der", "den", "dev", "dea", "dear", "deur", "deh", "deri", "dert", "dead"],
            ["de", "den", "dev", "dea", "dear", "deir", "deh", "dei", "det", "dead"],
            ["de", "den", "dev", "deu", "deor", "deur", "deh", "dei", "det", "dead"],
            ["den", "denan", "denav", "dena", "denor", "denir", "denah", "deni", "denat", "denid"]
        ]
        ur = [
            ["ur", "un", "uv", "uu", "uar", "uur", "uh", "ui", "ut", "uad"],
            ["ua", "un", "uv", "uu", "uar", "uir", "uh", "ui", "ut", "uad"],
            ["uo", "un", "uv", "uu", "uar", "uur", "uh", "ui", "ut", "uad"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-"]
        ]
        _s, _f, _n, _p = dar if word == "dar" else der if word == "der" else ur if word == "ur" else endings
        # if word == "riadus":
        #     _p = endings[1][1]
        for i in range(1, len(cases)):
            singular[i] += _s[i - 1]
            singular2[i] += _f[i - 1]
            singular3[i] += _n[i - 1]
            plural[i] += _p[i - 1]
            # singular[i] = singular[i].replace("aaa", "aata").replace("iii", "iiti").replace("eee", "eete").replace("iia", "iita").replace("auu", "ausu") \
            #                          .replace("euu", "eusu").replace("iuu", "iusu").replace("uuu", "uusu").replace("eaa", "eata")
        # if word == "regaus":
        #    singular[10] = "regaustar"
        case_len, sin_len, fem_len, neu_len, plu_len = [len(i) for i in cases], [len(i) for i in singular], [len(i) for i in singular2], \
                                                       [len(i) for i in singular3], [len(i) for i in plural]
        case_fill, sin_fill, fem_fill, neu_fill, plu_fill = max(case_len), max(sin_len), max(fem_len), max(neu_len), max(plu_len)
        outputs = []
        for i in range(len(cases)):
            case, sin, fem, neu, plu = cases[i], singular[i], singular2[i], singular3[i], plural[i]
            outputs.append(f"{case:<{case_fill}} | {sin:<{sin_fill}} | {fem:<{fem_fill}} | {neu:<{neu_fill}} | {plu:<{plu_fill}}")
        output = "\n".join(outputs)
        image = Image.new("RGB", (2000, 2000), (0, 0, 0))
        width, height = ImageDraw.Draw(image).textsize(output, font=font)
        image = image.resize((width + 10, height + 15))
        draw = ImageDraw.Draw(image)
        draw.text((10, 0), output, fill=(255, 255, 255), font=font)
        bio = BytesIO()
        image.save(bio, "PNG")
        bio.seek(0)
        a = f"\nAdverb form: {word[:-2]}i (Note: does not work for some words)" if word not in \
            ["dar", "der", "ur", "munnar", "tar", "onnar", "annar", "ennar", "mennar", "mannar", "var", "innar", "sar", "nennar", "kennar"] else ''
        return await general.send(f'Forms of the adjective "{word}"{a}', ctx.channel, file=discord.File(bio, "declension.png"))
        # return await general.send("Coming later. Insert that you can convert adjectives to adverbs by replacing -ar with -i" + word, ctx.channel)

    @rsl1_decline.command(name="verbs", aliases=["v", "conjugations", "c"])
    async def rsl1_decl_verbs(self, ctx: commands.Context, word: str):
        """ RSL-1 verb conjugations """
        font = ImageFont.truetype("assets/mono.ttf", size=64)
        word = word.lower()
        if word[-2:] not in ["an", "sa"]:
            return await general.send("All RSL-1 verbs end in -an or -ansa.", ctx.channel)
        sa = word[-2:] == "sa"
        li = -4 if sa else -2
        declined = word[:li] if word not in ["naan", "vian"] else ""
        conj = ["Form", "1sg", "2sg", "3sg", "1pl", "2pl", "3pl", "Past Imperf.", "Past Perfective", "Future", "Conditional", "Imperative sg", "Imperative pl"]
        normal = ["Conjugation"] + [declined] * (len(conj) - 1)
        endings = ["a", "as", "at", "an", "az", "an", "ah", "ak", "av", "al", "ar", "art"]
        naan = ["naa", "naas", "naat", "naam", "naaz", "nain/niin", "kaina", "-", "vaina", "saina", "naar", "naart"]
        vian = ["ja", "jas", "jat/vön", "vim", "viz", "viin", "kaina", "-", "vaina", "saina", "viar/vär", "viart/värt"]
        _n = naan if word == "naan" else vian if word == "vian" else endings
        # _s, _f, _n, _p = dar if word == "dar" else der if word == "der" else ur if word == "ur" else endings
        # if word == "riadus":
        #     _p = endings[1][1]
        for i in range(1, len(conj)):
            normal[i] += _n[i - 1]
            # interrogative[i] += _i[i - 1]
            if sa:
                normal[i] += "sa"
        conj_len, normal_len = [len(i) for i in conj], [len(i) for i in normal]
        conj_fill, normal_fill = max(conj_len), max(normal_len)
        outputs = []
        for i in range(len(conj)):
            co, no = conj[i], normal[i]
            outputs.append(f"{co:<{conj_fill}} | {no:<{normal_fill}}")
        output = "\n".join(outputs)
        image = Image.new("RGB", (2000, 2000), (0, 0, 0))
        width, height = ImageDraw.Draw(image).textsize(output, font=font)
        image = image.resize((width + 10, height + 15))
        draw = ImageDraw.Draw(image)
        draw.text((10, 0), output, fill=(255, 255, 255), font=font)
        bio = BytesIO()
        image.save(bio, "PNG")
        bio.seek(0)
        a = ""
        if word not in ["naan", "vian"]:
            a += f"\nActive Participles:\nPast (Complete) -> {declined}adar\nPast (Incomplete) -> {declined}attar\nPresent -> {declined}annar\n\n" \
                 f"Passive Participles:\nPast (Complete) -> {declined}akar\nPast (Incomplete) -> {declined}aghar\nPresent -> {declined}amar\n\n" \
                 f"Converbs:\nPast -> {declined}{'ij' if word[-3] != 'j' else ''}ad\nPresent -> {declined}avi"
        return await general.send(f'Verb conjugation for "{word}"{a}', ctx.channel, file=discord.File(bio, "conjugation.png"))
        # return await general.send("Coming later." + word, ctx.channel)

    @rsl1.group(name="dictionary", aliases=["words", "w", "dict", "d"])
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
        """ RSL-1 small words (e.g. prepositions and stuff) """
        # stuff = load_rsl1()["small_words"]
        return await rsl1_args_handler(ctx, args, "small_words")

    @rsl1_dict.command(name="bad", aliases=["b", "badwords"])
    async def rsl1_bad_words(self, ctx: commands.Context, *, args: str = ""):
        """ RSL-1 bad words """
        return await rsl1_args_handler(ctx, args, "bad")

    @rsl1_dict.command(name="phrases", aliases=["p"])
    async def rsl1_phrases(self, ctx: commands.Context, *, args: str = ""):
        """ RSL-1 phrases """
        return await rsl1_args_handler(ctx, args, "phrases")

    @rsl1_dict.command(name="pronouns")
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

    # @rsl1.command(name="phrases", aliases=["p"])
    # async def rsl1_phrases(self, ctx: commands.Context, *, search: str = None):
    #     """ Some RSL-1 words and phrases """
    #     stuff = load_rsl1("phrases", 0)
    #     # stuff.sort(key=lambda x: x[0].lower())
    #     if search:
    #         stuff = [[en, rsl] for en, rsl in stuff if (search.lower() in en.lower() or search.lower() in rsl.lower())]
    #     output = [f'{en} = {rsl}' for en, rsl in stuff]
    #     return await general.send("Certain phrases you can say in RSL-1:\n" + "\n".join(output), ctx.channel)

    @rsl1.command(name="pronunciation")
    async def rsl1_pronunciations(self, ctx: commands.Context):
        """ How RSL-1 is intended to sound """
        return await general.send(rsl1_pronunciation, ctx.channel)

    @rsl1.command(name="grammar")
    async def rsl1_grammar(self, ctx: commands.Context, page: int = 0):
        """ RSL-1 grammar and structure stuff """
        pages = len(rsl1_grammar)
        if 1 <= page <= pages:
            return await general.send(rsl1_grammar[page - 1], ctx.channel)
        else:
            parts = [part.splitlines()[0].replace("RSL-1 Grammar and Structure - ", "") for part in rsl1_grammar]
            return await general.send(f"There are currently {pages} parts/pages of information about RSL-1 grammar and structure:\n" +
                                      "\n".join(parts), ctx.channel)

    @commands.command(name="ga78")
    @commands.is_owner()
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
