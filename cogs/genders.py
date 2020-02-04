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


class HumanInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def pb_size(self, user: discord.Member):
        random.seed(user.id)
        ___random = random.randint(0, 69)
        __random = random.randint(87, 147) / 100
        result = ___random / __random
        if user.id == self.bot.user.id:
            result = 420.69
        return result

    @commands.command(name="pickle", aliases=["cucumber", "banana", "eggplant"])
    async def pickle_size(self, ctx, user: discord.Member = None):
        """ Pickle size! """
        if user is None:
            user = ctx.author
        try:
            gender = json.loads(open(f"data/gender/{user.id}.json", "r").read())
            if gender["male"]:
                result = self.pb_size(user)
            elif gender["female"]:
                u = "You are" if user == ctx.author else f"{user.name} is"
                return await ctx.send(f"{u} female though!")
            else:
                u = "you even have" if user == ctx.author else f"{user.name} even has"
                return await ctx.send(f"Neither male or female? How can I know {u} one?")
        except FileNotFoundError or KeyError or ValueError:
            if user.bot:
                return await ctx.send(f"But {user.name} is a bot!")
            return await ctx.send(f"To know the {ctx.invoked_with} size, I need to know {user.name}'s gender.\n"
                                  f"Use `{ctx.prefix}gender <gender>` to do so.")
        message = await ctx.send(f"<a:loading:651883385878478858> Checking {user.name}'s {ctx.invoked_with} size...")
        await asyncio.sleep(3)
        return await message.edit(content=f"**{user.name}**'s {ctx.invoked_with} size is **{result:.2f}cm**")

    @commands.command(name="breast", aliases=["boobs", "tiddies"])
    async def boob_size(self, ctx, user: discord.Member = None):
        """ Boob size! """
        if user is None:
            user = ctx.author
        try:
            gender = json.loads(open(f"data/gender/{user.id}.json", "r").read())
            if gender["female"]:
                result = self.pb_size(user) / 2.5
            elif gender["male"]:
                u = "You are" if user == ctx.author else f"{user.name} is"
                return await ctx.send(f"{u} male though!")
            else:
                u = "you even have" if user == ctx.author else f"{user.name} even has"
                return await ctx.send(f"Neither male or female? How can I know {u} them?")
        except FileNotFoundError or KeyError or ValueError:
            if user.bot:
                return await ctx.send(f"But {user.name} is a bot!")
            return await ctx.send(f"To know the {ctx.invoked_with} size, I need to know {user.name}'s gender.\n"
                                  f"Use `{ctx.prefix}gender <gender>` to do so.")
        message = await ctx.send(f"<a:loading:651883385878478858> Checking {user.name}'s {ctx.invoked_with} size...")
        await asyncio.sleep(3)
        return await message.edit(content=f"**{user.name}**'s {ctx.invoked_with} size is **{result:.2f}cm**")

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
                if male:
                    g = "male"
                elif female:
                    g = "female"
                elif invalid:
                    g = "invalid"
                else:
                    g = "undefined, Regaus broke something"
                return await ctx.send(f"{ctx.author.mention} you are already **{g}**!")
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
            if choice == "male":
                data["male"] = True
                rid = ctx.guild.get_role(651339885013106688)
            elif choice == "female":
                data["female"] = True
                rid = ctx.guild.get_role(651339932681371659)
            elif choice == "invalid":
                data["invalid"] = True
                rid = ctx.guild.get_role(651339982652571648)
            else:
                return await ctx.send("Are you sure you choice either male, female or invalid?")
            if ctx.guild.id == 568148147457490954:
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
            return await ctx.send("File already exists though")
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
            if choice == "male":
                data["male"] = True
                rid = ctx.guild.get_role(651339885013106688)
            elif choice == "female":
                data["female"] = True
                rid = ctx.guild.get_role(651339932681371659)
            elif choice == "invalid":
                data["invalid"] = True
                rid = ctx.guild.get_role(651339982652571648)
            else:
                return await ctx.send("Are you sure you choice either male, female or invalid?")
            if ctx.guild.id == 568148147457490954:
                await user.add_roles(rid, reason="User assigned gender")
            open(f"data/gender/{user.id}.json", "w+").write(json.dumps(data))
            return await ctx.send(f"{ctx.author.mention} Set {user.name}'s gender to {choice}.")

    @commands.command(name="setorientation")
    @commands.is_owner()
    @commands.guild_only()
    async def set_orientation(self, ctx, user: discord.Member, orientation: str):
        try:
            gender = json.loads(open(f"data/gender/{user.id}.json", "r").read())
            male, female = [gender["male"], gender["female"]]
        except FileNotFoundError or KeyError or ValueError:
            return await ctx.send(f"I need to know {user.name}'s gender first. "
                                  f"(`{ctx.prefix}setgender {user.id} <gender>`)")
        try:
            json.loads(open(f"data/orientation/{user.id}.json", "r").read())
            return await ctx.send("File already exists though")
        except FileNotFoundError or KeyError or ValueError:
            try:
                os.makedirs(f"data/orientation")
            except FileExistsError:
                pass
            if male:
                valid_choices = ["gay", "straight", "bi", "bisexual"]
            elif female:
                valid_choices = ["lesbian", "straight", "bi", "bisexual"]
            else:
                valid_choices = ["pansexual", "frying_pan"]
            choice = orientation.lower()
            if choice not in valid_choices:
                _gender = "male" if male else "female" if female else "invalid"
                return await ctx.send(f"Valid choices for {_gender}: `{', '.join(valid_choices)}`")
            data = orientations.copy()
            _orientation = "undefined"
            if choice == "gay" or choice == "lesbian":
                data["gay_lesbian"] = True
                if choice == "gay":
                    _orientation = "gay"
                if choice == "lesbian":
                    _orientation = "lesbian"
            elif choice == "straight":
                data["straight"] = True
                _orientation = "straight"
            elif choice == "bi" or choice == "bisexual":
                data["bisexual"] = True
                _orientation = "bisexual"
            elif choice == "frying_pan" or choice == "pansexual":
                data["frying_pan"] = True
                _orientation = "a frying pan"
            else:
                return await ctx.send("Are you sure your choice is one of the valid ones?")
            open(f"data/orientation/{user.id}.json", "w+").write(json.dumps(data))
            return await ctx.send(f"{ctx.author.mention} Set {user.name}'s orientation to {_orientation}.")

    @commands.command(name="orientation", aliases=["sexuality"])
    @commands.guild_only()
    async def sexual_orientation(self, ctx, orientation: str):
        """ Set your sexual orientation """
        # Valid choices:
        # Female -> Lesbian, Straight, Bi
        # Male -> Gay, Straight, Bi
        # Invalid -> Frying Pan
        try:
            gender = json.loads(open(f"data/gender/{ctx.author.id}.json", "r").read())
            male, female = [gender["male"], gender["female"]]
        except FileNotFoundError or KeyError or ValueError:
            return await ctx.send(f"I need to know your gender first. (`{ctx.prefix}gender <gender>`)")
        try:
            data = json.loads(open(f"data/orientation/{ctx.author.id}.json", "r").read())
            lg = data["gay_lesbian"]
            straight = data["straight"]
            bi = data["bisexual"]
            pan = data["frying_pan"]
            if lg or straight or bi or pan:
                _orientation = "gay/lesbian" if lg else "straight" if straight else "bisexual" if bi else "a frying pan"
                return await ctx.send(f"{ctx.author.mention} But you're already **{_orientation}**!")
        except FileNotFoundError or KeyError or ValueError:
            try:
                os.makedirs(f"data/orientation")
            except FileExistsError:
                pass
            if male:
                valid_choices = ["gay", "straight", "bi", "bisexual"]
            elif female:
                valid_choices = ["lesbian", "straight", "bi", "bisexual"]
            else:
                valid_choices = ["pansexual", "frying_pan"]
            choice = orientation.lower()
            if choice not in valid_choices:
                _gender = "male" if male else "female" if female else "invalid"
                return await ctx.send(f"Valid choices for {_gender}: `{', '.join(valid_choices)}`")
            data = orientations.copy()
            _orientation = "undefined"
            if choice == "gay" or choice == "lesbian":
                data["gay_lesbian"] = True
                if choice == "gay":
                    _orientation = "gay"
                if choice == "lesbian":
                    _orientation = "lesbian"
            elif choice == "straight":
                data["straight"] = True
                _orientation = "straight"
            elif choice == "bi" or choice == "bisexual":
                data["bisexual"] = True
                _orientation = "bisexual"
            elif choice == "frying_pan" or choice == "pansexual":
                data["frying_pan"] = True
                _orientation = "a frying pan"
            else:
                return await ctx.send("Are you sure your choice is one of the valid ones?")
            open(f"data/orientation/{ctx.author.id}.json", "w+").write(json.dumps(data))
            return await ctx.send(f"{ctx.author.mention} You are now {_orientation}")

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
        if user1 == user2:
            return await ctx.send("I don't think that's how it works...")
        try:
            gender = json.loads(open(f"data/gender/{user1.id}.json", "r").read())
            u1m, u1f, u1i = [gender["male"], gender["female"], gender["invalid"]]
        except FileNotFoundError:
            return await ctx.send(f"I need to know {user1.name}'s gender first.")
        try:
            gender = json.loads(open(f"data/gender/{user2.id}.json", "r").read())
            u2m, u2f, u2i = [gender["male"], gender["female"], gender["invalid"]]
        except FileNotFoundError:
            return await ctx.send(f"I need to know {user2.name}'s gender first.")
        try:
            data = json.loads(open(f"data/orientation/{user1.id}.json", "r").read())
            u1lg = data["gay_lesbian"]
            u1s = data["straight"]
            # u1bi = data["bisexual"]
            u1fp = data["frying_pan"]
        except FileNotFoundError:
            return await ctx.send(f"I need to know {user1.name}'s orientation first.")
        try:
            data = json.loads(open(f"data/orientation/{user2.id}.json", "r").read())
            u2lg = data["gay_lesbian"]
            u2s = data["straight"]
            u2bi = data["bisexual"]
            u2fp = data["frying_pan"]
        except FileNotFoundError:
            return await ctx.send(f"I need to know {user2.name}'s orientation first.")
        av1 = user1.avatar_url_as(size=1024, format="png")
        av2 = user2.avatar_url_as(size=1024, format="png")
        main_link = f"https://media.bowser65.xyz/imgen/misc/ship?image1={av1}&image2={av2}&variant="
        variant = "default"
        if u1m:
            if u1lg:
                if u2m:
                    if u2lg:
                        variant = "gay"
                    elif u2bi:
                        variant = "bi"
                    else:
                        return await ctx.send("Ship invalid: Gay male + Straight male")
                else:
                    return await ctx.send("Ship invalid: Gay males can only match other gay or bi males.")
            elif u1s:
                if u2f:
                    if u2s:
                        variant = "default"
                    elif u2bi:
                        variant = "bi"
                    else:
                        return await ctx.send("Ship invalid: Male + Lesbian female")
                else:
                    return await ctx.send("Ship invalid: Straight males can only match with straight or bi females.")
            else:
                if u2m:
                    if u2lg or u2bi:
                        variant = "bi"
                    else:
                        return await ctx.send("Ship invalid: Bisexual males can't match straight males.")
                elif u2f:
                    if u2bi or u2s:
                        variant = "bi"
                    else:
                        return await ctx.send("Ship invalid: Male + Lesbian female")
                else:
                    return await ctx.send("Ship invalid: Bisexuals cannot match with people of invalid gender.")
        elif u1f:
            if u1lg:
                if u2f:
                    if u2lg:
                        variant = "lesbian"
                    elif u2bi:
                        variant = "bi"
                    else:
                        return await ctx.send("Ship invalid: Lesbian female + Straight female")
                else:
                    return await ctx.send("Ship invalid: Lesbian females can only match other lesbians or bi females.")
            elif u1s:
                if u2m:
                    if u2s:
                        variant = "default"
                    elif u2bi:
                        variant = "bi"
                    else:
                        return await ctx.send("Ship invalid: Female + Gay male")
                else:
                    return await ctx.send("Ship invalid: Straight females can only match with straight or bi males.")
            else:
                if u2m:
                    if u2bi or u2s:
                        variant = "bi"
                    else:
                        return await ctx.send("Ship invalid: Female + Gay male")
                elif u2f:
                    if u2lg or u2bi:
                        variant = "bi"
                    else:
                        return await ctx.send("Ship invalid: Bisexuals cannot match with people of invalid gender.")
        else:
            if u1fp:
                if u2i:
                    if u2fp:
                        variant = "fryingpan"
                    else:
                        return await ctx.send("Ship invalid: Frying pans can only match other frying pans.")
                else:
                    return await ctx.send("Ship invalid: Invalid frying pans can only match other frying pans.")
            else:
                return await ctx.send("Ship invalid: Invalid people can only be a frying pan.")
        link = main_link + variant
        bio = BytesIO(await http.get(link, res_method="read"))
        if bio is None:
            return await ctx.send("Something went wrong, couldn't generate image")
        __names = [len(user1.name), len(user2.name)]
        _names = [int(x / 2) for x in __names]
        names = [user1.name[:_names[0]], user2.name[_names[1]:]]
        name = ''.join(names)
        message = f"Nice shipping there!\nShip name: **{name}**"
        return await ctx.send(message, file=discord.File(bio, filename=f"shipping_services.png"))


def setup(bot):
    bot.add_cog(HumanInfo(bot))
