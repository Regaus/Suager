from discord.ext import commands

from core.utils import logger, time


class Spyware(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if not self.bot.local_config["logs"]:
            return
        to = time.time()
        log = "names"
        uid = after.id
        n1, n2 = [before.name, after.name]
        if n1 != n2:
            send = f"{to} > {n1} ({uid}) is now known as {n2}"
            logger.log(self.bot.name, log, send)
        a1, a2 = [before.avatar, after.avatar]
        if a1 != a2:
            send = f"{to} > {n2} ({uid}) changed their avatar"
            logger.log(self.bot.name, "user_avatars", send)
        d1, d2 = [before.discriminator, after.discriminator]
        if d1 != d2:
            send = f"{to} > {n2}'s ({uid}) discriminator is now {d2} (from {d1})"
            logger.log(self.bot.name, log, send)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if not self.bot.local_config["logs"]:
            return
        to = time.time()
        log = "member_roles"
        guild = after.guild.name
        n = after.name
        uid = after.id
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
