from regaus import languages

from utils import bases, commands, conlangs


def is_rsl1_eligible(ctx: commands.Context):
    # Users:                 Regaus,             Leitoxz,            Alex Five,          Potato,             Chuck,              Mid,
    # Users:                 Shawn,              LostCandle,         Ash,                1337xp,             Aya,                Maza,
    # Users:                 Karmeck,            Steiri,             PandaBoi
    if ctx.author.id not in [302851022790066185, 291665491221807104, 430891116318031872, 374853432168808448, 593736085327314954, 581206591051923466,
                             236884090651934721, 659879737509937152, 499038637631995906, 679819572278198272, 527729196688998415, 735902817151090691,
                             857360761135431730, 230313032956248064, 301091858354929674]:
        return False
    if ctx.guild is None:
        return True
    else:
        # Channels:               rsl-1,              hidden-commands,    secretive-commands, secretive-commands-2, secret-room-1,
        # Channels:               secret-room-2,      secret-room-3,      secret-room-8,      secret-room-10,     secret-room-11
        return ctx.channel.id in [787340111963881472, 610482988123422750, 742885168997466196, 753000962297299005, 671520521174777869,
                                  672535025698209821, 681647810357362786, 725835449502924901, 798513492697153536, 799714065256808469]


class Conlangs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="rsl-1", aliases=["rsl1", "rsl"])
    @commands.check(is_rsl1_eligible)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def rsl1(self, ctx: commands.Context):
        """ Some ~~mostly unmaintained~~ tools to interact with RSL-1 """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @rsl1.command(name="numbers", aliases=["n", "number"])
    async def rsl1_numbers(self, ctx: commands.Context, number: int = None, *, _base: str = "10"):
        """ Translate a number to RSL-1 """
        if number is None:
            return await ctx.send(f"This command can translate a number to RSL-1. For example, `{ctx.prefix}rsl1 {ctx.invoked_with} 1` will translate the number 1 to RSL-1.")
        _split = _base.split(" ", 1)
        try:
            base = int(_split[0])
        except ValueError:
            return await ctx.send("Base must be either `10` or `16`.")
        if base not in [10, 16]:
            return await ctx.send("RSL-1 only supports decimal (base-10) and hexadecimal (base-16).")
        _version = "rsl-1k"
        if len(_split) > 1:
            if _split[1] in ["rsl-1i", "1i", "i"]:
                _version = "rsl-1i"
        output = conlangs.rsl_number(number, base, _version)
        if "Error: " in output:
            return await ctx.send(output)
        if base == 10:
            return await ctx.send(f"{number:,} = {output}")
        if base == 16:
            _hex = languages.splits(bases.to_base(number, 16, True), 4, " ")
            return await ctx.send(f"Base-10: {number:,}\nBase-16: {_hex}\nRSL-{_version.split('-')[1]}: {output}")

    @rsl1.command(name="decline", aliases=["dec", "d"])
    async def rsl1_decline(self, ctx: commands.Context, language: str, *, word: str):
        """ Decline an RSL-1 noun """
        if word.startswith("debug "):
            word = word[6:]
            # This will only test for the cases that Suager will use, so the extra cases (like MWK) will not be shown here.
            cases = ["default", "nominative", "vocative", "accusative", "genitive", "dative", "instrumental", "locative", "inessive", "high_five", "at", "for", "in", "ago"]
        else:
            case_lists = {
                "ka_an": ["nominative", "accusative", "genitive", "dative", "instrumental", "comitative", "locative", "ablative", "vocative"],
                "ka_ow": ["nominative", "accusative", "genitive", "dative", "instrumental", "locative", "ablative"],
                "ka_mw": ["nominative", "accusative", "genitive", "dative", "instrumental", "abessive", "locative", "ablative"],
                "ka_re": ["nominative", "accusative", "genitive", "dative", "instrumental", "locative"],
                "ka_ne": ["nominative", "accusative", "genitive", "dative", "instrumental"],
                "ka_ni": ["nominative", "accusative", "genitive", "dative", "instrumental", "abessive", "locative", "ablative"],
                "ka_tb": ["nominative", "accusative", "genitive", "dative", "instrumental", "abessive", "locative", "ablative"],
            }
            try:
                cases = case_lists[language]
            except KeyError:
                return await ctx.send("This language is currently not supported.")
        numbers = ["singular", "plural"]
        _language = ctx.language2(language)
        out = []
        for number in numbers:
            data = [number.title() + ":"]
            for case in cases:
                # \u200b = zero width space, makes it also align on mobile
                data.append(f"`{case:<12}\u200b` -> {_language.case(word, case, number)}")
            out.append("\n".join(data))
        return await ctx.send("\n\n".join(out))


def setup(bot):
    bot.add_cog(Conlangs(bot))
