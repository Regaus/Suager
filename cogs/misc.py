import random
from io import BytesIO

import discord
from discord.ext import commands


class Miscellaneous(commands.Cog):
    @commands.command(name="lx2", hidden=True)
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.user)
    async def lx2_ct_gen(self, ctx):
        """ Relative Time Delta """
        sc = {
            "easy": [
                {  # Stage 1
                    "normal": get_colours(4),
                    "hard": get_colours(5)
                },
                {  # Stage 2
                    "normal": get_colours(4)
                },
                {  # Stage 3
                    "normal": get_colours(4),
                    "hard": get_colours(5)
                },
                {  # Stage 4
                    "normal": get_colours(5),
                    "hard": get_colours(6)
                },
                {  # Stage 5
                    "normal": get_colours(5)
                },
                {  # Stage 6
                    "normal": get_colours(5),
                    "hard": get_colours(6)
                },
                {  # Stage 7
                    "normal": get_colours(6),
                    "hard": get_colours(7)
                },
                {  # Stage 8
                    "normal": get_colours(6)
                },
                {  # Stage 9
                    "normal": get_colours(6),
                    "hard": get_colours(7)
                },
                {  # Stage 10
                    "normal": get_colours(7),
                    "hard": get_colours(8)
                },
                {  # Stage 11
                    "normal": get_colours(7)
                },
                {  # Stage 12
                    "normal": get_colours(7),
                    "hard": get_colours(8)
                },
                {  # Stage 13/14
                    "normal": get_colours(8),
                    "hard": get_colours(9)
                },
            ],
            "normal": [
                {  # Stage 1
                    "normal": get_colours(5),
                    "hard": get_colours(6)
                },
                {  # Stage 2
                    "normal": get_colours(5)
                },
                {  # Stage 3
                    "normal": get_colours(5),
                    "hard": get_colours(6)
                },
                {  # Stage 4
                    "normal": get_colours(6),
                    "hard": get_colours(7)
                },
                {  # Stage 5
                    "normal": get_colours(6)
                },
                {  # Stage 6
                    "normal": get_colours(6),
                    "hard": get_colours(7)
                },
                {  # Stage 7
                    "normal": get_colours(7),
                    "hard": get_colours(8)
                },
                {  # Stage 8
                    "normal": get_colours(7)
                },
                {  # Stage 9
                    "normal": get_colours(7),
                    "hard": get_colours(8)
                },
                {  # Stage 10
                    "normal": get_colours(8),
                    "hard": get_colours(9)
                },
                {  # Stage 11
                    "normal": get_colours(8)
                },
                {  # Stage 12
                    "normal": get_colours(8),
                    "hard": get_colours(9)
                },
                {  # Stage 13/14
                    "normal": get_colours(9),
                    "hard": get_colours(9)
                },
            ],
            "hard": [
                {  # Stage 1
                    "normal": get_colours(6),
                    "hard": get_colours(7)
                },
                {  # Stage 2
                    "normal": get_colours(6)
                },
                {  # Stage 3
                    "normal": get_colours(6),
                    "hard": get_colours(7)
                },
                {  # Stage 4
                    "normal": get_colours(7),
                    "hard": get_colours(8)
                },
                {  # Stage 5
                    "normal": get_colours(7)
                },
                {  # Stage 6
                    "normal": get_colours(7),
                    "hard": get_colours(8)
                },
                {  # Stage 7
                    "normal": get_colours(8),
                    "hard": get_colours(9)
                },
                {  # Stage 8
                    "normal": get_colours(8)
                },
                {  # Stage 9
                    "normal": get_colours(8),
                    "hard": get_colours(9)
                },
                {  # Stage 10
                    "normal": get_colours(9),
                    "hard": get_colours(9)
                },
                {  # Stage 11
                    "normal": get_colours(9)
                },
                {  # Stage 12
                    "normal": get_colours(9),
                    "hard": get_colours(9)
                },
                {  # Stage 13/14
                    "normal": get_colours(9),
                    "hard": get_colours(9)
                },
            ]
        }
        st = [
            {  # Stage 1
                "normal": get_tr(1, False),
                "hard": get_tr(1, True)
            },
            {  # Stage 2
                "normal": get_tr(2, False),
            },
            {  # Stage 3
                "normal": get_tr(3, False),
                "hard": get_tr(3, True)
            },
            {  # Stage 4
                "normal": get_tr(4, False),
                "hard": get_tr(4, True)
            },
            {  # Stage 5
                "normal": get_tr(5, False),
            },
            {  # Stage 6
                "normal": get_tr(6, False),
                "hard": get_tr(6, True)
            },
            {  # Stage 7
                "normal": get_tr(7, False),
                "hard": get_tr(7, True)
            },
            {  # Stage 8
                "normal": get_tr(8, False),
            },
            {  # Stage 9
                "normal": get_tr(9, False),
                "hard": get_tr(9, True)
            },
            {  # Stage 10
                "normal": get_tr(10, False),
                "hard": get_tr(10, True)
            },
            {  # Stage 11
                "normal": get_tr(11, False),
            },
            {  # Stage 12
                "normal": get_tr(12, False),
                "hard": get_tr(12, True)
            },
            {  # Stage 13 / 14
                "normal": get_tr(13, False),
                "hard": get_tr(13, True)
            },
        ]
        on = []
        oh = []
        for i in range(13):
            ce = "Easy\n{\n"
            cm = "}\nMedium\n{\n"
            ch = "}\nHard\n{\n"
            cc = "}\nInsane\n{\n   spawnColor_1 = true\n   spawnColor_2 = true\n   spawnColor_3 = true\n   " \
                 "spawnColor_4 = true\n   spawnColor_5 = true\n   spawnColor_6 = true\n   spawnColor_7 = true\n" \
                 "   spawnColor_8 = true\n   spawnColor_9 = true\n}"
            for c in range(1, 10):
                if c in sc["easy"][i]["normal"]:
                    ce += f"   spawnColor_{c} = true\n"
                else:
                    ce += f"   spawnColor_{c} = false\n"
                if c in sc["normal"][i]["normal"]:
                    cm += f"   spawnColor_{c} = true\n"
                else:
                    cm += f"   spawnColor_{c} = false\n"
                if c in sc["hard"][i]["normal"]:
                    ch += f"   spawnColor_{c} = true\n"
                else:
                    ch += f"   spawnColor_{c} = false\n"
            on.append(ce + cm + ch + cc)
            if "hard" in sc["easy"][i]:
                ce = "Easy\n{\n"
                cm = "}\nMedium\n{\n"
                ch = "}\nHard\n{\n"
                cc = "}\nInsane\n{\n   spawnColor_1 = true\n   spawnColor_2 = true\n   spawnColor_3 = true\n   " \
                     "spawnColor_4 = true\n   spawnColor_5 = true\n   spawnColor_6 = true\n   spawnColor_7 = true\n" \
                     "   spawnColor_8 = true\n   spawnColor_9 = true\n}"
                for c in range(1, 10):
                    if c in sc["easy"][i]["hard"]:
                        ce += f"   spawnColor_{c} = true\n"
                    else:
                        ce += f"   spawnColor_{c} = false\n"
                    if c in sc["normal"][i]["hard"]:
                        cm += f"   spawnColor_{c} = true\n"
                    else:
                        cm += f"   spawnColor_{c} = false\n"
                    if c in sc["hard"][i]["hard"]:
                        ch += f"   spawnColor_{c} = true\n"
                    else:
                        ch += f"   spawnColor_{c} = false\n"
                oh.append(ce + cm + ch + cc)
            else:
                oh.append("No hard")
        op = ""
        for i in range(13):
            fb = f"spheres_{i+1}"
            op += f"{fb}.uis\n\n{on[i]}\n\n{fb}h.uis\n\n{oh[i]}\n\n"
        tn = []
        th = []
        to = ""
        for i in range(13):
            ts = ""
            for t in range(1, 16):
                if t in st[i]["normal"]:
                    ts += f"reward_gem_{t} = true\n"
                else:
                    ts += f"reward_gem_{t} = false\n"
            tn.append(ts)
            if "hard" in st[i]:
                ts = ""
                for t in range(1, 16):
                    if t in st[i]["hard"]:
                        ts += f"reward_gem_{t} = true\n"
                    else:
                        ts += f"reward_gem_{t} = false\n"
                th.append(ts)
            else:
                th.append("No hard")
        for i in range(13):
            fb = f"treasure_{i+1}"
            to += f"{fb}.uis\n\n{tn[i]}\n\n{fb}h.uis\n\n{th[i]}\n\n"
        out = f"Spheres\n\n{op}\n\nTreasure\n\n{to}"
        bio = BytesIO(out.encode("utf-8"))
        return await ctx.send("Good luck understanding what this is.", file=discord.File(bio, filename="lx2_ctg.rsf"))
        # return await ctx.send("Fuck off, command not in use.")
        # return await ctx.send(string)
        # return await ctx.send("Fuck off, command not in use. " + str(bias.get_bias(sqlite.Database(), user)))


def get_colours(total: int = 4):
    if total == 9:
        return [1, 2, 3, 4, 5, 6, 7, 8, 9]
    c = []
    for i in range(total):
        r = random.randint(1, 9)
        if r not in c:
            c.append(r)
        else:
            while r in c:
                r = random.randint(1, 9)
            else:
                c.append(r)
    c.sort()
    return c


def get_tr(stage: int, h: bool = False):
    if not h:
        return [stage, stage + 1, stage + 2]
    else:
        c = []
        mt = 15 - stage
        rt = random.randint(3, 5)
        tr = rt if rt < mt else mt
        for i in range(tr):
            r = random.randint(stage, 15)
            if r not in c:
                c.append(r)
            else:
                while r in c:
                    r = random.randint(stage, 15)
                else:
                    c.append(r)
            c.sort()
        return c


def setup(bot):
    bot.add_cog(Miscellaneous(bot))
