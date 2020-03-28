import asyncio
import random
from io import BytesIO

import discord
from discord.ext import commands

from utils import http, emotes, database

roles = {  # ServerID: [male, female, invalid]
    568148147457490954: [651339885013106688, 651339932681371659, 651339982652571648],
    690162603275714574: [690338734264418338, 690338806746185758, 0]
}
select = "SELECT * FROM genders WHERE uid=?"
insert = "INSERT INTO genders VALUES (?, ?)"  # uid, gender
update = "UPDATE genders SET gender=? WHERE uid=?"


class HumanInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database()

    @commands.command(name="pickle", aliases=["cucumber", "banana", "eggplant"])
    async def pickle_size(self, ctx, *, user: discord.Member = None):
        """ Pickle size! """
        if user is None:
            user = ctx.author
        random.seed(user.id)
        result = round(random.uniform(12, 30), 1)
        if user.id == self.bot.user.id:
            result = 42.0
        if user.id == 682321712779493429:  # imagine being you
            result = 0.0
        if user.id == 302851022790066185:
            result = 29.9
        message = await ctx.send(f"<a:loading:651883385878478858> Checking {user.name}'s {ctx.invoked_with} size...")
        await asyncio.sleep(3)
        return await message.edit(content=f"**{user.name}**'s {ctx.invoked_with} size is **{result}cm**")

    @commands.command(name="breast", aliases=["boobs", "tiddies"])
    async def boob_size(self, ctx, *, user: discord.Member = None):
        """ Boob size! """
        if user is None:
            user = ctx.author
        random.seed(user.id - 1)
        result = round(random.uniform(7, 25), 1)
        if user.id == 682321712779493429:  # imagine being you
            result = 0.0
        if user.id == 302851022790066185:
            result = 17.5
        message = await ctx.send(f"<a:loading:651883385878478858> Checking {user.name}'s {ctx.invoked_with} size...")
        await asyncio.sleep(3)
        return await message.edit(content=f"**{user.name}**'s' {ctx.invoked_with} size is **{result}cm**")

    @commands.command(name="gender")
    @commands.guild_only()
    async def assign_gender(self, ctx, gender: str):
        """ Assign your gender """
        data = self.db.fetchrow(select, (ctx.author.id,))
        if data:
            return await ctx.send(f"{ctx.author.mention} I already know your gender! You can't change it...")
        valid_genders = ["male", "female", "other", "invalid"]
        choice = gender.lower()
        if choice not in valid_genders:
            return await ctx.send(f"{choice} is not a valid gender now, is it?\n"
                                  f"Valid genders: `{', '.join(valid_genders)}`")
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
            return await ctx.send("Are you sure your choice is either `male`, `female`, `other` or `invalid`?")
        if choice == "other":
            choice = "invalid"
        r = self.db.execute(insert, (ctx.author.id, choice))
        if ctx.guild.id in roles:
            for role in remove:
                await ctx.author.remove_roles(role, reason="User assigned gender")
            await ctx.author.add_roles(rid, reason="User assigned gender")
        # open(f"data/gender/{ctx.author.id}.json", "w+").write(json.dumps(data))
        return await ctx.send(f"{ctx.author.mention} Set your gender to {choice}.\n{r}")

    @commands.command(name="setgender")
    @commands.is_owner()
    @commands.guild_only()
    async def set_gender(self, ctx, user: discord.Member, gender: str):
        """ Set gender """
        valid_genders = ["male", "female", "other", "invalid"]
        choice = gender.lower()
        if choice not in valid_genders:
            return await ctx.send(f"{choice} is not a valid gender, is it?\n"
                                  f"Valid genders: `{', '.join(valid_genders)}`")
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
            return await ctx.send("Are you sure your choice is either `male`, `female`, `other` or `invalid`?")
        if choice == "other":
            choice = "invalid"
        d = self.db.fetchrow(select, (ctx.author.id,))
        if d:
            r = self.db.execute(update, (choice, ctx.author.id))
        else:
            r = self.db.execute(insert, (ctx.author.id, choice))
        if ctx.guild.id in roles:
            await ctx.author.remove_roles(remove, reason="User assigned gender")
            await ctx.author.add_roles(rid, reason="User assigned gender")
        return await ctx.send(f"{ctx.author.mention} Set {user.name}'s gender to {choice}.\n{r}")

    @commands.command(name="ship")
    @commands.guild_only()
    async def ship(self, ctx, user1: discord.Member, user2: discord.Member):
        """ Build a ship """
        if user1.id == self.bot.user.id or user2.id == self.bot.user.id:
            return await ctx.send(f"Sorry, but I wasn't programmed to feel love :( {emotes.AlexHeartBroken}")
        if user1.bot or user2.bot:
            return await ctx.send(f"Bots can't be shipped, they can't love :( {emotes.AlexHeartBroken}")
        ls = [94762492923748352, 246652610747039744]
        if user1.id in ls or user2.id in ls:
            return await ctx.send("These 2 users cannot be shipped together.")
        av1 = user1.avatar_url_as(size=1024)
        av2 = user2.avatar_url_as(size=1024)
        link = f"https://api.alexflipnote.dev/ship?user={av1}&user2={av2}"
        bio = BytesIO(await http.get(link, res_method="read"))
        if bio is None:
            return await ctx.send("Something went wrong, couldn't generate image")
        __names = [len(user1.name), len(user2.name)]
        _names = [int(x / 2) for x in __names]
        names = [user1.name[:_names[0]], user2.name[_names[1]:]]
        name = ''.join(names)
        names2 = [user2.name[:_names[1]], user1.name[_names[0]:]]
        name2 = ''.join(names2)
        message = f"Nice shipping there!\nShip names: **{name}** or **{name2}**"
        return await ctx.send(message, file=discord.File(bio, filename=f"shipping_services.png"))


def setup(bot):
    bot.add_cog(HumanInfo(bot))
