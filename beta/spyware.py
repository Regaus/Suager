from io import BytesIO

import discord
from discord.ext import commands

from beta import main
from utils import time, generic, logs, http


def status_gen(log, to, who, what, old, new, guild):
    send = f"{to} > {guild} > {who}'s {what} is now {new} (from {old})"
    logs.save(log, send)


class Spyware(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # self.log_sl = 650774303192776744

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        logging = generic.get_config()["spyware"]
        if not logging:
            return
        to = time.time()
        # senko = self.bot.get_channel(self.log_sl)
        # log = logs.log_channel(self.bot, 'spyware')
        log = logs.get_place(main.version, "spyware")
        n1, n2 = [before.name, after.name]
        if n1 != n2:
            send = f"{to} > {n1} is now known as {n2}"
            # await senko.send(send)
            logs.save(log, send)
        a1, a2 = [before.avatar, after.avatar]
        if a1 != a2:
            if after.id not in [609423646347231282, 568149836927467542, 520042197391769610]:  # Suager diff versions
                # await senko.send(send)
                al = self.bot.get_channel(676899389977133072)
                send = f"{to} > `{n2}` changed their avatar"
                bio = BytesIO(await http.get(str(after.avatar_url_as(size=1024, static_format="png")),
                                             res_method="read"))
                ani = after.is_avatar_animated()
                fe = "gif" if ani else "png"
                if bio is not None:
                    file = discord.File(bio, filename=f"{after.avatar}.{fe}")
                else:
                    file = None
                if al is not None and main.version == "stable":
                    await al.send(send, file=file)
                logs.save(logs.get_place(main.version, "avatars"), send)
                # await logs.log_channel(self.bot, 'avatars').send(
                #     f"{send}. New avatar: {after.avatar_url_as(size=1024)}")
        d1, d2 = [before.discriminator, after.discriminator]
        if d1 != d2:
            send = f"{to} > {n2}'s discriminator is now {d2} (from {d1})"
            # await senko.send(send)
            # await log.send(send)
            logs.save(log, send)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        logging = generic.get_config()["spyware"]
        if not logging:
            return
        to = time.time()
        log = logs.get_place(main.version, "spyware")
        al = logs.get_place(main.version, "spyware_activity")
        sl = logs.get_place(main.version, "spyware_status")
        guild = after.guild.name
        n = after.name
        a1, a2 = [before.activity, after.activity]
        if a1 != a2:
            # now = time.now_ts()
            if a2 is not None:
                t = f"{a2.type}".replace("ActivityType.", "")
                send = f"{to} > {after.guild.name} > {n}'s activities changed: now {t}: {a2.name}"
            else:
                send = f"{to} > {after.guild.name} > {n} now has no activity."
            logs.save(al, send)
            # if now > last + 15:
            #     logs.log_channel(self.bot, 'activity').send(send)
            #     activity_logged[after.id] = now
        n1, n2 = [before.nick, after.nick]
        is_senko_lair = after.guild.id == 568148147457490954
        ls = [94762492923748352, 246652610747039744]
        if n1 != n2:
            if after.id in ls and is_senko_lair:
                await generic.you_little_shit(self.bot.get_guild(568148147457490954))
            send = f"{to} > {n}'s nickname in {guild} is now {n2} (from {n1})"
            # await log.send(send)
            logs.save(log, send)
        try:
            s1, s1m, s1d, s1w, s2, s2m, s2d, s2w = [before.status, before.mobile_status, before.desktop_status,
                                                    before.web_status, after.status, after.mobile_status,
                                                    after.desktop_status, after.web_status]
        except AttributeError:
            s1, s1m, s1d, s1w, s2, s2m, s2d, s2w = [before.status, None, None, None, after.status, None, None, None]
        # status_log = logs.log_channel(self.bot, 'status')
        if after.id != 302851022790066185:
            if s1 != s2:
                status_gen(sl, to, n, "status", s1, s2, guild)
            if s1m != s2m:
                status_gen(sl, to, n, "mobile status", s1m, s2m, guild)
            if s1d != s2d:
                status_gen(sl, to, n, "desktop status", s1d, s2d, guild)
            if s1w != s2w:
                status_gen(sl, to, n, "web status", s1w, s2w, guild)
        r1, r2 = [before.roles, after.roles]
        if r1 != r2:
            roles_lost = []
            for role in r1:
                if role not in r2:
                    roles_lost.append(role.name)
            roles_gained = []
            for role in r2:
                if role not in r1:
                    roles_gained.append(role.name)
            for role in roles_lost:
                # await log.send(f"{to} > `{guild}` > `{n}` lost role `{role}`")
                logs.save(log, f"{to} > {guild} > {n} lost role {role}")
            for role in roles_gained:
                # await log.send(f"{to} > `{guild}` > `{n}` got role `{role}`")
                logs.save(log, f"{to} > {guild} > {n} got role {role}")


def setup(bot):
    bot.add_cog(Spyware(bot))
