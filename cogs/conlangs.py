from utils import bot_data, commands, conlangs, lists


def is_rsl1_eligible(ctx: commands.Context):
    if ctx.author.id not in lists.trusted_users:
        return False
    if ctx.guild is None:
        return True
    else:
        return ctx.channel.id in lists.trusted_channels


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
    async def rsl1_decline(self, ctx: commands.Context, word: str, language: str = "re_nu"):
        """ Decline a Kargadian noun """
        if word.startswith("debug "):
            word = word[6:]
            # This will only test for the cases that Suager will use, so the extra cases (like MWK) will not be shown here.
            cases = ["default", "nominative", "vocative", "accusative", "genitive", "dative", "high_five", "laugh_at", "for", "in", "ago"]  # , "instrumental", "locative", "inessive"
        else:
            case_lists = {
                "na": ["nominative", "accusative", "genitive", "dative", "instrumental", "locative", "ablative"],
                "kt": ["nominative", "accusative", "genitive", "dative", "instrumental", "locative", "ablative"],
                "re_kl": ["nominative", "accusative", "genitive", "dative", "instrumental", "locative"],
                "re_nu": ["nominative", "accusative", "genitive", "dative", "instrumental", "locative"],
                "re_mu": ["nominative", "accusative", "genitive", "dative", "instrumental", "locative"],
                "re_kv": ["nominative", "accusative", "genitive", "dative", "instrumental", "locative"],
                "vv": ["nominative", "accusative", "genitive", "dative", "instrumental", "locative"],
                "kz": ["nominative", "accusative", "genitive", "dative", "instrumental", "locative"],

                "lh": ["nominative", "vocative", "accusative", "genitive", "dative", "locative", "ablative", "instrumental", "comitative"]
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


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Conlangs(bot))
