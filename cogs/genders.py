import random

import discord
from discord.ext import commands

from utils import database, generic

roles = {  # ServerID: [male, female, invalid]
    568148147457490954: [651339885013106688, 651339932681371659, 651339982652571648],
    690162603275714574: [690338734264418338, 690338806746185758, 0]
}
select = "SELECT * FROM genders WHERE uid=?"
insert = "INSERT INTO genders VALUES (?, ?)"  # uid, gender
update = "UPDATE genders SET gender=? WHERE uid=?"


class Genders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database()

    @commands.command(name="pickle")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def pickle_size(self, ctx, *, who: discord.Member = None):
        """ Measure someone's pickle """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "pickle"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        user = who or ctx.author
        random.seed(user.id)
        _result = round(random.uniform(12, 30), 1)
        custom = {
            self.bot.user.id: 42.0,
            302851022790066185: 29.9
        }
        result = custom.get(user.id, _result)
        return await generic.send(generic.gls(locale, "pickle", [user.name, result]), ctx.channel)

    @commands.command(name="gender")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def assign_gender(self, ctx, gender: str):
        """ Assign your gender """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "gender"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        data = self.db.fetchrow(select, (ctx.author.id,))
        if data:
            return await generic.send(generic.gls(locale, "gender_already_assigned", [ctx.author.name, data["gender"]]), ctx.channel)
        valid_genders = ["male", "female", "other", "invalid"]
        choice = gender.lower()
        if choice not in valid_genders:
            return await generic.send(generic.gls(locale, "gender_invalid", [choice, ", ".join(valid_genders)]), ctx.channel)
        gr = roles.get(ctx.guild.id, [0, 0, 0])
        if choice == "male":
            remove = [ctx.guild.get_role(x) for x in [gr[1], gr[2]]]
            rid = ctx.guild.get_role(gr[0])
        elif choice == "female":
            remove = [ctx.guild.get_role(x) for x in [gr[0], gr[2]]]
            rid = ctx.guild.get_role(gr[1])
        elif choice == "invalid" or choice == "other":
            remove = [ctx.guild.get_role(x) for x in [gr[0], gr[1]]]
            rid = ctx.guild.get_role(gr[2])
        else:
            return await generic.send(generic.gls(locale, "gender_invalid2"), ctx.channel)
        r = self.db.execute(insert, (ctx.author.id, choice))
        if ctx.guild.id in roles:
            for role in remove:
                if role is not None:
                    await ctx.author.remove_roles(role, reason="User assigned gender")
            if rid is not None:
                await ctx.author.add_roles(rid, reason="User assigned gender")
        return await generic.send(generic.gls(locale, "gender_set", [ctx.author.name, choice, r]), ctx.channel)

    @commands.command(name="setgender")
    @commands.is_owner()
    @commands.guild_only()
    async def set_gender(self, ctx, user: discord.Member, gender: str):
        """ Set gender """
        locale = generic.get_lang(ctx.guild)
        valid_genders = ["male", "female", "other", "invalid"]
        choice = gender.lower()
        if choice not in valid_genders:
            return await generic.send(generic.gls(locale, "gender_invalid", [choice, ", ".join(valid_genders)]), ctx.channel)
        gr = roles.get(ctx.guild.id, [0, 0, 0])
        if choice == "male":
            remove = [ctx.guild.get_role(x) for x in [gr[1], gr[2]]]
            rid = ctx.guild.get_role(gr[0])
        elif choice == "female":
            remove = [ctx.guild.get_role(x) for x in [gr[0], gr[2]]]
            rid = ctx.guild.get_role(gr[1])
        elif choice == "invalid" or choice == "other":
            remove = [ctx.guild.get_role(x) for x in [gr[0], gr[1]]]
            rid = ctx.guild.get_role(gr[2])
        else:
            return await generic.send(generic.gls(locale, "gender_invalid2"), ctx.channel)
        d = self.db.fetchrow(select, (user.id,))
        if d:
            r = self.db.execute(update, (choice, user.id))
        else:
            r = self.db.execute(insert, (user.id, choice))
        if ctx.guild.id in roles:
            for role in remove:
                if role is not None:
                    await user.remove_roles(role, reason="User assigned gender")
            if rid is not None:
                await user.add_roles(rid, reason="User assigned gender")
        return await generic.send(generic.gls(locale, "gender_force_set", [user.name, choice, r]), ctx.channel)


def setup(bot):
    bot.add_cog(Genders(bot))
