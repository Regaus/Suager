from utils import commands, conlangs


def is_rsl1_eligible(ctx: commands.Context):
    # Users:                 Regaus,             Leitoxz,            Alex Five,          Potato,             Chuck,              Mid,                Noodle
    # Users:                 Shawn,              LostCandle,         Ash,                1337xp,             Aya,                Maza,               HatKid
    # Users:                 Karmeck,            Steir,              PandaBoi,           Suager,             Mary,               Wight,              Back,
    # Users:                 Ash/Kollu,          Drip
    if ctx.author.id not in [302851022790066185, 291665491221807104, 430891116318031872, 374853432168808448, 593736085327314954, 581206591051923466, 411925326780825602,
                             236884090651934721, 659879737509937152, 499038637631995906, 679819572278198272, 527729196688998415, 735902817151090691, 418151634087182359,
                             857360761135431730, 230313032956248064, 301091858354929674, 517012611573743621, 660639108674224158, 505486500314611717, 454599329232191488,
                             690895816914763866, 381870347814830081]:
        return False
    if ctx.guild is None:
        return True
    else:
        # Channels:               rsl-1,              hidden-commands,    secretive-commands, secretive-commands-2, Ka. commands,     Ka. discussion,     Ka. lang. disc.
        # Channels:               secret-room-1,      secret-room-2,      secret-room-3,      secret-room-8,      secret-room-10,     secret-room-11,     secret-room-13,
        # Channels:               secret-room-14,     secret-room-15,     secret-room-16,     secret-room-17
        return ctx.channel.id in [787340111963881472, 610482988123422750, 742885168997466196, 753000962297299005, 938582514166034514, 938587178680864788, 938587585415086140,
                                  671520521174777869, 672535025698209821, 681647810357362786, 725835449502924901, 798513492697153536, 799714065256808469, 958489459672891452,
                                  965801985716666428, 969720792457822219, 971195522830442527, 972112792624726036]


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
    async def rsl1_numbers(self, ctx: commands.Context, number: int = None, language: str = "ka_ne"):
        """ Translate a number to Kargadian """
        if number is None:
            return await ctx.send(f"This command can translate a number to Kargadian. For example, `{ctx.prefix}rsl {ctx.invoked_with} 1` will tell you how to say 1 in Kargadian.")
        # _split = _base.split(" ", 1)
        # try:
        #     base = int(_split[0])
        # except ValueError:
        #     return await ctx.send("Base must be either `10` or `16`.")
        # if base not in [10, 16]:
        #     return await ctx.send("RSL-1 only supports decimal (base-10) and hexadecimal (base-16).")
        # _version = "rsl-1k"
        # if len(_split) > 1:
        #     if _split[1] in ["rsl-1i", "1i", "i"]:
        #         _version = "rsl-1i"
        output = conlangs.rsl_number(number, language)
        if "Error: " in output:
            return await ctx.send(output)
        # if base == 10:
        return await ctx.send(f"{number:,} = {output}")
        # if base == 16:
        #     _hex = languages.splits(bases.to_base(number, 16, True), 4, " ")
        #     return await ctx.send(f"Base-10: {number:,}\nBase-16: {_hex}\nRSL-{_version.split('-')[1]}: {output}")

    @rsl1.command(name="decline", aliases=["dec", "d"])
    async def rsl1_decline(self, ctx: commands.Context, word: str, language: str = "ka_ne"):
        """ Decline a Kargadian noun """
        if word.startswith("debug "):
            word = word[6:]
            # This will only test for the cases that Suager will use, so the extra cases (like MWK) will not be shown here.
            cases = ["default", "nominative", "vocative", "accusative", "genitive", "dative", "high_five", "laugh_at", "for", "in", "ago"]  # , "instrumental", "locative", "inessive"
        else:
            case_lists = {
                "ka_an": ["nominative", "accusative", "genitive", "dative", "instrumental", "comitative", "locative", "ablative", "vocative"],
                "ka_ow": ["nominative", "accusative", "genitive", "dative", "instrumental", "locative", "ablative"],
                "ka_mw": ["nominative", "accusative", "genitive", "dative", "instrumental", "abessive", "locative", "ablative"],
                "ka_re": ["nominative", "accusative", "genitive", "dative", "instrumental", "locative"],
                "ka_ne": ["nominative", "accusative", "genitive", "dative", "instrumental"],
                "ka_ni": ["nominative", "accusative", "genitive", "dative", "instrumental", "abessive", "locative", "ablative"],
                "ka_tb": ["nominative", "accusative", "genitive", "dative", "instrumental", "abessive", "locative", "ablative"],
                "ka_ka": ["subjective", "objective"]
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
                max_len = len(max(cases, key=len))  # Length of the longest string
                data.append(f"`{case:<{max_len}}\u200b` -> {_language.case(word, case, number)}")
            out.append("\n".join(data))
        return await ctx.send("\n\n".join(out))


def setup(bot):
    bot.add_cog(Conlangs(bot))
