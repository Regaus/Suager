from discord.ext import commands

from core.utils import bases, general
from languages import langs


def is_rsl1_eligible(ctx: commands.Context):
    # Regaus, Leitoxz, Alex Five, HatKid, Potato
    # Chuck, Mid, Ash, 1337xp, Shawn
    if ctx.author.id not in [302851022790066185, 291665491221807104, 430891116318031872, 418151634087182359, 374853432168808448,
                             593736085327314954, 581206591051923466, 499038637631995906, 679819572278198272, 236884090651934721]:
        return False
    if ctx.guild is None:
        return True
    else:
        # rsl-1, hidden-commands, secretive-commands, secretive-commands-2
        # sr2, sr8, sr10, sr11, sr12
        return ctx.channel.id in [787340111963881472, 610482988123422750, 742885168997466196, 753000962297299005,
                                  672535025698209821, 725835449502924901, 798513492697153536, 799714065256808469, 841106370203090994]


def rsl_number(value: int, base: int, version: str):
    """ Convert number to RSL-1 """
    # limit = int("9" * 36)
    limit = 16 ** 72 - 1 if base == 16 else 10 ** 36 - 1
    limit_str = "4.97 x 10^86" if base == 16 else "10^36 - 1"
    if base not in [10, 16]:
        return "Error: Only base-10 and base-16 are supported."
    if value > limit:
        return f"Error: Highest allowed number for base-{base} is {limit:,} ({limit_str})."
    if value < 0:
        return "Error: Negative values are not supported."
    if value == 0:
        return "inti"
    numbers = {
        "rsl-1k": {
            10: {
                1: {0: "", 1: "ukka", 2: "devi", 3: "teri", 4: "cegi", 5: "paki", 6: "senki", 7: "eki", 8: "oni", 9: "zeki"},
                11: {11: "uveri", 12: "deveri", 13: "teveri", 14: "ceveri", 15: "paveri", 16: "severi", 17: "everi", 18: "overi", 19: "zeveri"},
                10: {1: "veri", 2: "deveire", 3: "teveire", 4: "ceveire", 5: "paveire", 6: "seneire", 7: "eveire", 8: "oneire", 9: "zeveire"},
                20: {2: "deveire", 3: "teveire", 4: "ceveire", 5: "paveire", 6: "seneire", 7: "eveire", 8: "oneire", 9: "zeveire"},
                21: {0: "", 1: "ukku", 2: "devu", 3: "teru", 4: "cegu", 5: "paku", 6: "senku", 7: "eku", 8: "onu", 9: "zeku"},
                100: ["arkia", "arkiain"],
                1000: ["kirraa", "kirrain"],
                1000000: ["ukkaristu", "devaristu", "teraristu", "cegaristu", "paaristu", "sennaristu", "ekaristu", "onaristu", "zekaristu", "veraristu"]
            },
            16: {
                1: {0: "", 1: "ukka", 2: "devi", 3: "teri", 4: "cegi", 5: "paki", 6: "senki", 7: "eki", 8: "oni",
                    9: "zeha", 10: "davi", 11: "tari", 12: "cagi", 13: "bai", 14: "sanki", 15: "aki"},
                11: {17: "uhki", 18: "dehki", 19: "tehki", 20: "cehki", 21: "pahki", 22: "sehki", 23: "ehki", 24: "ohki",
                     25: "zehki", 26: "dahki", 27: "tahki", 28: "cahki", 29: "bahki", 30: "sahki", 31: "ahki"},
                10: {1: "hekki", 2: "degeki", 3: "tegeki", 4: "cegeki", 5: "pageki", 6: "segeki", 7: "egeki", 8: "ogeki",
                     9: "zegeki", 10: "dageki", 11: "tageki", 12: "cageki", 13: "bageki", 14: "sageki", 15: "ageki"},
                20: {2: "degeki", 3: "tegeki", 4: "cegeki", 5: "pageki", 6: "segeki", 7: "egeki", 8: "ogeki",
                     9: "zegeki", 10: "dageki", 11: "tageki", 12: "cageki", 13: "bageki", 14: "sageki", 15: "ageki"},
                21: {0: "", 1: "ukku", 2: "devu", 3: "teru", 4: "cegu", 5: "paku", 6: "senku", 7: "eku", 8: "onu",
                     9: "zehu", 10: "davu", 11: "taru", 12: "cagu", 13: "bau", 14: "sanku", 15: "aku"},
                100: ["arraikä", "arraikäin"],
                4096: ["karta", "kartain"],
                1000: ["mirra", "mirrain"],
                1000000: ["ukkaneru", "devaneru", "teraneru", "ceganeru", "pakaneru", "senkaneru", "ekaneru", "onaneru",
                          "zehaneru", "davaneru", "taraneru", "caganeru", "baaneru", "sankaneru", "akaneru", "hekkaneru"]
            }
        },
        "rsl-1i": {
            10: {
                1: {0: "", 1: "ua", 2: "dei", 3: "tei", 4: "cei", 5: "paa", 6: "sei", 7: "ei", 8: "oi", 9: "zei"},
                11: {11: "uuri", 12: "deeri", 13: "teeri", 14: "ceeri", 15: "paari", 16: "seeri", 17: "eeri", 18: "oori", 19: "zeeri"},
                10: {1: "vei", 2: "dejere", 3: "tejere", 4: "cejere", 5: "pajere", 6: "sejere", 7: "ejere", 8: "ojere", 9: "zejere"},
                20: {2: "deire", 3: "teire", 4: "ceire", 5: "paire", 6: "seire", 7: "heire", 8: "koire", 9: "zeire"},
                21: {0: "", 1: "uu", 2: "dee", 3: "tee", 4: "cee", 5: "paa", 6: "see", 7: "ee", 8: "oo", 9: "zee"},
                100: ["arja", "arjain"],
                1000: ["kirra", "kirrain"],
                1000000: ["urrist", "derrist", "terrist", "cerrist", "paarist", "sennist", "errist", "onnist", "zerrist", "verrist"]
            },
            16: {
                1: {0: "", 1: "ua", 2: "dei", 3: "tei", 4: "cei", 5: "paa", 6: "sei", 7: "ei", 8: "oo",
                    9: "zea", 10: "daa", 11: "taa", 12: "caa", 13: "baa", 14: "saa", 15: "aa"},
                11: {17: "ukki", 18: "dehi", 19: "tehk", 20: "cehi", 21: "pahi", 22: "sehi", 23: "ehi", 24: "ohi",
                     25: "zehi", 26: "dahi", 27: "tahi", 28: "cahi", 29: "bahi", 30: "sahi", 31: "ahi"},
                10: {1: "hei", 2: "dekki", 3: "tekki", 4: "cekki", 5: "pakki", 6: "sekki", 7: "ekki", 8: "okki",
                     9: "zekki", 10: "dakki", 11: "takki", 12: "cakki", 13: "bakki", 14: "sakki", 15: "akki"},
                20: {2: "dekki", 3: "tekki", 4: "cekki", 5: "pakki", 6: "sekki", 7: "hekki", 8: "gokki",
                     9: "zekki", 10: "dakki", 11: "takki", 12: "cakki", 13: "bakki", 14: "sakki", 15: "akki"},
                21: {0: "", 1: "u", 2: "de", 3: "te", 4: "ce", 5: "pa", 6: "se", 7: "e", 8: "o",
                     9: "ze", 10: "da", 11: "ta", 12: "ca", 13: "ba", 14: "sa", 15: "a"},
                100: ["arraija", "arraijin"],
                4096: ["karta", "kartain"],
                1000: ["mira", "mirain"],
                1000000: ["uknar", "devnar", "ternar", "cegnar", "pankar", "senkar", "einar", "oonar",
                          "zenhar", "davnar", "tarnar", "cagnar", "bainar", "sankar", "ankar", "henkar"]
            }
        }
    }
    # one = {0: "", 1: "ukka", 2: "devi", 3: "tei", 4: "sei", 5: "paa/paki", 6: "senki", 7: "ei", 8: "oo/oni", 9: "zee/zehi"}
    # teen = {11: "uveri", 12: "deveri", 13: "teveri", 14: "severi", 15: "paveri", 16: "seneri", 17: "eijeri", 18: "overi", 19: "zegheri"}
    # ten = {1: "verri", 2: "devveire", 3: "tevveire", 4: "sevveire", 5: "pavveire", 6: "senneire", 7: "evveire", 8: "onneire", 9: "zegheire"}
    # _21 = {0: "", 1: "ukku", 2: "deu", 3: "teiju", 4: "seiju", 5: "pau", 6: "senku", 7: "eiju", 8: "ou", 9: "zeu"}
    # hundred = ["arraiki", "arraikädan"]
    # exp_1000 = ["kirraa", "kirraadan"]
    # exp = ["ugaristu", "devaristu", "tevaristu", "sekaristu", "pakkaristu", "sennaristu", "eijaristu", "onaristu", "zeharistu", "verraristu"]
    _ten, _11, _20, _hundred, _thousand = (16, 17, 32, 256, 65536) if base == 16 else (10, 11, 20, 100, 1000)
    _numbers = numbers[version][base]

    def hundred(_val: int):
        if _val < _ten:
            _99v = _numbers[1][_val]
        elif _11 <= _val < _20:
            _99v = _numbers[11][_val]
        else:
            _v, _u = divmod(_val, _ten)
            _99v = f"{_numbers[21][_u]}{_numbers[20][_v]}" if _u > 0 else _numbers[10][_v]
        return _99v

    def thousand(_val: int):
        _999 = _val % _thousand
        if base == 16 and _999 % 4096 == 0 and _999 > 0:
            _4096 = _999 // 4096
            return f"{_numbers[1][1]} {_numbers[4096][0]}" if _4096 == 1 else f"{hundred(_4096)} {_numbers[4096][1]}"
        _99 = _999 % _hundred
        _99v = hundred(_99)
        _100 = _999 // _hundred
        _100v = "" if _100 == 0 else ((f"{_numbers[1][1]} {_numbers[100][0]}" if _100 == 1 else f"{hundred(_100)} {_numbers[100][1]}") + (", " if _99 != 0 else ""))
        return _100v + _99v

    _1000 = value % _thousand
    outputs = [thousand(_1000)] if _1000 > 0 else []
    large = []
    _value = value
    _range = len(_numbers[1000000]) + 1
    for i in range(_range):
        _value //= _thousand
        large.append(_value % _thousand)
    for i in range(_range):
        val = large[i]
        if val > 0:
            n1, n2 = _numbers[1000] if i == 0 else ((_name := _numbers[1000000][i - 1]), (_name[:-1] if version == "rsl-1k" else _name) + "ain")
            name = n1 if val % _hundred == 1 else n2
            outputs.append(f"{('ukkar' if version == 'rsl-1k' else 'ur') if (val == 1 and i != 0) else thousand(val)} {name}")
    return ", ".join(outputs[::-1])


class Conlangs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="rsl-1", aliases=["rsl1", "rsl"])
    @commands.check(is_rsl1_eligible)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def rsl1(self, ctx: commands.Context):
        """ RSL-1k Documentation

        This command will try to explain to you how RSL-1k works.
        **Note: Do __not__ share any RSL-1 translations outside of this channel (or DMs with me or others with RSL-1 access) without my permission**
        **If choco suddenly starts understanding RSL-1, I __will__ kill you**"""
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @rsl1.command(name="numbers", aliases=["n", "number"])
    async def rsl1_numbers(self, ctx: commands.Context, number: int = None, *, _base: str = "10"):
        """ Translate a number to RSL-1 """
        if number is None:
            return await general.send(f"This command can translate a number to RSL-1. For example, `{ctx.prefix}rsl1 {ctx.invoked_with} 1` "
                                      f"will translate the number 1 to RSL-1.", ctx.channel)
        _split = _base.split(" ", 1)
        try:
            base = int(_split[0])
        except ValueError:
            return await general.send("Base must be either `10` or `16`.", ctx.channel)
        if base not in [10, 16]:
            return await general.send("RSL-1 only supports decimal (base-10) and hexadecimal (base-16).", ctx.channel)
        _version = "rsl-1k"
        if len(_split) > 1:
            if _split[1] in ["rsl-1i", "1i", "i"]:
                _version = "rsl-1i"
        output = rsl_number(number, base, _version)
        if "Error: " in output:
            return await general.send(output, ctx.channel)
        if base == 10:
            return await general.send(f"{number:,} = {output}", ctx.channel)
        if base == 16:
            _hex = langs.splits(bases.to_base(number, 16, True), 4, " ")
            return await general.send(f"Base-10: {number:,}\nBase-16: {_hex}\nRSL-{_version.split('-')[1]}: {output}", ctx.channel)


def setup(bot):
    bot.add_cog(Conlangs(bot))
