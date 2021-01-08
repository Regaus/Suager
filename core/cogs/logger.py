from io import BytesIO

import discord
from discord.ext import commands

from core.utils import http, logger, time


class Spyware(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.self = [609423646347231282, 568149836927467542, 520042197391769610, 577608850316853251, 610040320280887296]

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        if not self.bot.local_config["logs"]:
            return
        to = time.time()
        log = "names"
        uid = after.id
        n1, n2 = [before.name, after.name]
        if n1 != n2:
            send = f"{to} > {n1} ({uid}) is now known as {n2}"
            logger.log(self.bot.name, log, send)
        if self.bot.user.id == 609423646347231282:
            a1, a2 = [before.avatar, after.avatar]
            al = self.bot.get_channel(745760639955370083)
            if a1 != a2:
                send = f"{to} > {n2} ({uid}) changed their avatar"
                logger.log(self.bot.name, "user_avatars", send)
                if uid not in self.self:
                    avatar = BytesIO(await http.get(str(after.avatar_url_as(static_format="png", size=4096)), res_method="read"))
                    ext = "gif" if after.is_avatar_animated() else "png"
                    if al is None:
                        print("No avatar log channel found.")
                    else:
                        await al.send(f"{time.time()} > {n2} ({uid}) changed their avatar", file=discord.File(avatar, filename=f"{a2}.{ext}"))
        d1, d2 = [before.discriminator, after.discriminator]
        if d1 != d2:
            send = f"{to} > {n2}'s ({uid}) discriminator is now {d2} (from {d1})"
            logger.log(self.bot.name, log, send)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if not self.bot.local_config["logs"]:
            return
        to = time.time()
        log = "member_roles"
        guild = after.guild.name
        n = after.name
        uid = after.id
        if after.guild.id in [568148147457490954, 738425418637639775] and uid not in [302851022790066185]:
            if after.display_name[0] < "A":
                await after.edit(reason="De-hoist", nick=f"\u17b5{after.display_name[:31]}")
        if after.guild.id in [430945139142426634] and uid == self.bot.user.id:
            await after.guild.me.edit(nick=None)
        if after.guild.id == 784357864482537473 and uid == 302851022790066185:
            if after.nick != "Regaboy Prime":
                await after.edit(nick="Regaboy Prime", reason="I told you I'll do it")
        n1, n2 = before.nick, after.nick
        if n1 != n2:
            logger.log(self.bot.name, "names", f"{to} > {guild} > {n}'s ({uid}) nickname is now {n2} (from {n1})")
        r1, r2 = before.roles, after.roles
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
                logger.log(self.bot.name, log, f"{to} > {guild} > {n} ({uid}) lost role {role}")
            for role in roles_gained:
                logger.log(self.bot.name, log, f"{to} > {guild} > {n} ({uid}) got role {role}")


def setup(bot):
    bot.add_cog(Spyware(bot))
