import asyncio
import json
import os
import random
from io import BytesIO

import discord
from discord.ext import commands

from utils import http, emotes

genders = {
    "male": False,
    "female": False,
    "invalid": False
}
orientations = {
    "gay_lesbian": False,
    "straight": False,
    "bisexual": False,
    "frying_pan": False
}
roles = {  # ServerID: [male, female, invalid]
    568148147457490954: [651339885013106688, 651339932681371659, 651339982652571648],
    690162603275714574: [690338734264418338, 690338806746185758, -1]
}


class HumanInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # self.db = sqlite.Database()

    def pb_size(self, user: discord.Member):
        random.seed(user.id)
        lr, ur = 150, 300
        ___random = random.randint(lr, ur)
        __random = 10
        result = ___random / __random
        # result *= bias.friend_bias(self.db, user) * bias.gender_bias(user) * bias.so_bias(user)
        if user.id == self.bot.user.id:
            result = 420.69
        if user.id == 682321712779493429:  # imagine being you
            result = 0
        if user.id == 302851022790066185:
            result = ur - (1 / __random)
        return result

    @commands.command(name="pickle", aliases=["cucumber", "banana", "eggplant"])
    async def pickle_size(self, ctx, *, user: discord.Member = None):
        """ Pickle size! """
        if user is None:
            user = ctx.author
        result = self.pb_size(user)
        message = await ctx.send(f"<a:loading:651883385878478858> Checking {user.name}'s {ctx.invoked_with} size...")
        await asyncio.sleep(3)
        return await message.edit(content=f"If **{user.name}** was male, their {ctx.invoked_with} "
                                          f"size would be **{result:.1f}cm**")

    @commands.command(name="breast", aliases=["boobs", "tiddies"])
    async def boob_size(self, ctx, *, user: discord.Member = None):
        """ Boob size! """
        if user is None:
            user = ctx.author
        result = self.pb_size(user)
        message = await ctx.send(f"<a:loading:651883385878478858> Checking {user.name}'s {ctx.invoked_with} size...")
        await asyncio.sleep(3)
        return await message.edit(content=f"If **{user.name}** was female, their {ctx.invoked_with} "
                                          f"size would be **{result:.1f}cm**")

    @commands.command(name="gender")
    @commands.guild_only()
    async def assign_gender(self, ctx, gender: str):
        """ Assign your gender """
        try:
            data = json.loads(open(f"data/gender/{ctx.author.id}.json", "r").read())
            male = data["male"]
            female = data["female"]
            invalid = data["invalid"]
            if male or female or invalid:
                return await ctx.send(f"{ctx.author.mention} I already know your gender! You can't change it...")
        except FileNotFoundError or KeyError or ValueError:
            try:
                os.makedirs(f"data/gender")
            except FileExistsError:
                pass
            valid_genders = ["male", "female", "invalid"]
            choice = gender.lower()
            if choice not in valid_genders:
                return await ctx.send(f"{choice} is not a valid gender.\nValid genders: `{', '.join(valid_genders)}`")
            data = genders.copy()
            gr = roles.get(ctx.guild.id, [-1, -1, -1])
            if choice == "male":
                data["male"] = True
                rid = ctx.guild.get_role(gr[0])
            elif choice == "female":
                data["female"] = True
                rid = ctx.guild.get_role(gr[1])
            elif choice == "invalid":
                data["invalid"] = True
                rid = ctx.guild.get_role(gr[2])
            else:
                return await ctx.send("Are you sure your choice is either `male`, `female` or `invalid`?")
            if ctx.guild.id in roles:
                await ctx.author.add_roles(rid, reason="User assigned gender")
            open(f"data/gender/{ctx.author.id}.json", "w+").write(json.dumps(data))
            return await ctx.send(f"{ctx.author.mention} Set your gender to {choice}.")

    @commands.command(name="setgender")
    @commands.is_owner()
    @commands.guild_only()
    async def set_gender(self, ctx, user: discord.Member, gender: str):
        """ Set gender """
        try:
            json.loads(open(f"data/gender/{user.id}.json", "r").read())
            await ctx.send("I've already saved something but ok.")
        except FileNotFoundError or KeyError or ValueError:
            try:
                os.makedirs(f"data/gender")
            except FileExistsError:
                pass
            valid_genders = ["male", "female", "invalid"]
            choice = gender.lower()
            if choice not in valid_genders:
                return await ctx.send(f"{choice} is not a valid gender.\nValid genders: `{', '.join(valid_genders)}`")
            data = genders.copy()
            gr = roles.get(ctx.guild.id, [-1, -1, -1])
            if choice == "male":
                data["male"] = True
                rid = ctx.guild.get_role(gr[0])
            elif choice == "female":
                data["female"] = True
                rid = ctx.guild.get_role(gr[1])
            elif choice == "invalid":
                data["invalid"] = True
                rid = ctx.guild.get_role(gr[2])
            else:
                return await ctx.send("Are you sure your choice is either `male`, `female` or `invalid`?")
            if ctx.guild.id in roles:
                await user.add_roles(rid, reason="User assigned gender")
            open(f"data/gender/{user.id}.json", "w+").write(json.dumps(data))
            return await ctx.send(f"{ctx.author.mention} Set {user.name}'s gender to {choice}.")

    # @commands.command(name="setorientation")
    # @commands.is_owner()
    # @commands.guild_only()
    # async def set_orientation(self, ctx, user: discord.Member, orientation: str):
    #     """ Set orientation """
    #     try:
    #         gender = json.loads(open(f"data/gender/{user.id}.json", "r").read())
    #         male, female = [gender["male"], gender["female"]]
    #     except FileNotFoundError or KeyError or ValueError:
    #         return await ctx.send(f"I need to know {user.name}'s gender first. "
    #                               f"(`{ctx.prefix}setgender {user.id} <gender>`)")
    #     try:
    #         json.loads(open(f"data/orientation/{user.id}.json", "r").read())
    #         return await ctx.send("File already exists though")
    #     except FileNotFoundError or KeyError or ValueError:
    #         try:
    #             os.makedirs(f"data/orientation")
    #         except FileExistsError:
    #             pass
    #         if male:
    #             valid_choices = ["gay", "straight", "bi", "bisexual"]
    #         elif female:
    #             valid_choices = ["lesbian", "straight", "bi", "bisexual"]
    #         else:
    #             valid_choices = ["pansexual", "frying_pan"]
    #         choice = orientation.lower()
    #         if choice not in valid_choices:
    #             _gender = "male" if male else "female" if female else "invalid"
    #             return await ctx.send(f"Valid choices for {_gender}: `{', '.join(valid_choices)}`")
    #         data = orientations.copy()
    #         _orientation = "undefined"
    #         if choice == "gay" or choice == "lesbian":
    #             data["gay_lesbian"] = True
    #             if choice == "gay":
    #                 _orientation = "gay"
    #             if choice == "lesbian":
    #                 _orientation = "lesbian"
    #         elif choice == "straight":
    #             data["straight"] = True
    #             _orientation = "straight"
    #         elif choice == "bi" or choice == "bisexual":
    #             data["bisexual"] = True
    #             _orientation = "bisexual"
    #         elif choice == "frying_pan" or choice == "pansexual":
    #             data["frying_pan"] = True
    #             _orientation = "a frying pan"
    #         else:
    #             return await ctx.send("Are you sure your choice is one of the valid ones?")
    #         open(f"data/orientation/{user.id}.json", "w+").write(json.dumps(data))
    #         return await ctx.send(f"{ctx.author.mention} Set {user.name}'s orientation to {_orientation}.")

    # @commands.command(name="orientation", aliases=["sexuality"])
    # @commands.guild_only()
    # async def sexual_orientation(self, ctx, orientation: str):
    #     """ Set your sexual orientation """
    #     # Valid choices:
    #     # Female -> Lesbian, Straight, Bi
    #     # Male -> Gay, Straight, Bi
    #     # Invalid -> Frying Pan
    #     try:
    #         gender = json.loads(open(f"data/gender/{ctx.author.id}.json", "r").read())
    #         male, female = [gender["male"], gender["female"]]
    #     except FileNotFoundError or KeyError or ValueError:
    #         return await ctx.send(f"I need to know your gender first. (`{ctx.prefix}gender <gender>`)")
    #     try:
    #         data = json.loads(open(f"data/orientation/{ctx.author.id}.json", "r").read())
    #         lg = data["gay_lesbian"]
    #         straight = data["straight"]
    #         bi = data["bisexual"]
    #         pan = data["frying_pan"]
    #         if lg or straight or bi or pan:
    #             return await ctx.send(f"{ctx.author.mention} I already know what you are!")
    #     except FileNotFoundError or KeyError or ValueError:
    #         try:
    #             os.makedirs(f"data/orientation")
    #         except FileExistsError:
    #             pass
    #         if male:
    #             valid_choices = ["gay", "straight", "bi", "bisexual"]
    #         elif female:
    #             valid_choices = ["lesbian", "straight", "bi", "bisexual"]
    #         else:
    #             valid_choices = ["pansexual", "frying_pan"]
    #         choice = orientation.lower()
    #         if choice not in valid_choices:
    #             _gender = "male" if male else "female" if female else "invalid"
    #             return await ctx.send(f"Valid choices for {_gender}: `{', '.join(valid_choices)}`")
    #         data = orientations.copy()
    #         _orientation = "undefined"
    #         if choice == "gay" or choice == "lesbian":
    #             data["gay_lesbian"] = True
    #            if choice == "gay":
    #                 _orientation = "gay"
    #             if choice == "lesbian":
    #                 _orientation = "lesbian"
    #          elif choice == "straight":
    #            data["straight"] = True
    #             _orientation = "straight"
    #         elif choice == "bi" or choice == "bisexual":
    #             data["bisexual"] = True
    #             _orientation = "bisexual"
    #         elif choice == "frying_pan" or choice == "pansexual":
    #             data["frying_pan"] = True
    #             _orientation = "a frying pan"
    #         else:
    #             return await ctx.send("Are you sure your choice is one of the valid ones?")
    #         open(f"data/orientation/{ctx.author.id}.json", "w+").write(json.dumps(data))
    #         return await ctx.send(f"{ctx.author.mention} You are now {_orientation}")

    # Ship: see #bot-incoming-feats-area for orientation rules
    # If a bot is shipped, return that they cannot be
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
