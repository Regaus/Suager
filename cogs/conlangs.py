from discord.ext import commands

from utils import bases, conlangs, general, languages


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
        output = conlangs.rsl_number(number, base, _version)
        if "Error: " in output:
            return await general.send(output, ctx.channel)
        if base == 10:
            return await general.send(f"{number:,} = {output}", ctx.channel)
        if base == 16:
            _hex = languages.splits(bases.to_base(number, 16, True), 4, " ")
            return await general.send(f"Base-10: {number:,}\nBase-16: {_hex}\nRSL-{_version.split('-')[1]}: {output}", ctx.channel)


def setup(bot):
    bot.add_cog(Conlangs(bot))
