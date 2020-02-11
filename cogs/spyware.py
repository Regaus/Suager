from discord.ext import commands

from utils import time, generic, logs


async def status_gen(log, to, who, what, old, new, guild, uid):
    send = f"{to} > `{guild}` > `{who}`'s {what} is now `{new}` (from `{old}`)"
    now = time.now_ts()
    _last = recently_logged.get(uid, [0, ''])
    last, _what = _last
    if what == _what:
        if now > last + 15:
            await log.send(send)
            recently_logged[uid] = [now, what]
    else:
        await log.send(send)
        recently_logged[uid] = [now, what]


recently_logged = {}
activity_logged = {}


class Spyware(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_sl = 650774303192776744

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        logging = generic.get_config().spyware
        if not logging:
            return
        to = time.time()
        senko = self.bot.get_channel(self.log_sl)
        log = logs.log_channel(self.bot, 'spyware')
        n1, n2 = [before.name, after.name]
        if n1 != n2:
            send = f"{to} > `{n1}` is now known as `{n2}`"
            await senko.send(send)
            await log.send(send)
        a1, a2 = [before.avatar, after.avatar]
        if a1 != a2:
            send = f"{to} > `{n2}` changed their avatar"
            if after.id != 520042197391769610:  # Suager v3
                await senko.send(send)
            await logs.log_channel(self.bot, 'avatars').send(
                f"{send}. New avatar: {after.avatar_url_as(size=1024, format='png')}")
        d1, d2 = [before.discriminator, after.discriminator]
        if d1 != d2:
            send = f"{to} > `{n2}`'s discriminator is now `{d2}` (from `{d1}`)"
            await senko.send(send)
            await log.send(send)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        logging = generic.get_config().spyware
        if not logging:
            return
        to = time.time()
        senko = self.bot.get_channel(self.log_sl)
        log = logs.log_channel(self.bot, 'spyware')
        guild = after.guild.name
        n = after.name
        a1, a2 = [before.activity, after.activity]
        if a1 != a2:
            now = time.now_ts()
            last = activity_logged.get(after.id, 0)
            if a2 is not None:
                t = f"{a2.type}".replace("ActivityType.", "")
                send = f"{to} > {after.guild.name} > `{n}`'s activities changed: now {t}: `{a2.name}`"
            else:
                send = f"{to} > {after.guild.name} > `{n}` now has no activity."
            if now > last + 15:
                await logs.log_channel(self.bot, 'activity').send(send)
                activity_logged[after.id] = now
        n1, n2 = [before.nick, after.nick]
        is_senko_lair = after.guild.id == 568148147457490954
        if n1 != n2:
            send = f"{to} > `{n}`'s nickname in `{guild}` is now `{n2}` (from `{n1}`)"
            if is_senko_lair:
                await senko.send(send)
            await log.send(send)
        try:
            s1, s1m, s1d, s1w, s2, s2m, s2d, s2w = [before.status, before.mobile_status, before.desktop_status,
                                                    before.web_status, after.status, after.mobile_status,
                                                    after.desktop_status, after.web_status]
        except AttributeError:
            s1, s1m, s1d, s1w, s2, s2m, s2d, s2w = [before.status, None, None, None, after.status, None, None, None]
        status_log = logs.log_channel(self.bot, 'status')
        if after.id != 302851022790066185:
            if s1 != s2:
                await status_gen(status_log, to, n, "status", s1, s2, guild, after.id)
            if s1m != s2m:
                await status_gen(status_log, to, n, "mobile status", s1m, s2m, guild, after.id)
            if s1d != s2d:
                await status_gen(status_log, to, n, "desktop status", s1d, s2d, guild, after.id)
            if s1w != s2w:
                await status_gen(status_log, to, n, "web status", s1w, s2w, guild, after.id)
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
                await log.send(f"{to} > `{guild}` > `{n}` lost role `{role}`")
            for role in roles_gained:
                await log.send(f"{to} > `{guild}` > `{n}` got role `{role}`")


def setup(bot):
    bot.add_cog(Spyware(bot))
