import json
from io import BytesIO

import discord
from discord.ext import commands

from core.utils import general, permissions, time
from languages import langs
from suager.cogs.leveling import max_level
from suager.utils import settings


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="languages")
    async def languages(self, ctx: commands.Context):
        """ List of all supported languages """
        languages = [f"`{key}`: {langs.gls('_name', key)}" for key in langs.languages.keys()]
        real, con, = [], []
        for language in languages:
            if language.startswith("`rsl-"):
                con.append(language)
            else:
                real.append(language)
        trusted = [302851022790066185, 577637595392245770, 651179888988127270, 430891116318031872, 291665491221807104]
        trusted_servers = [568148147457490954, 738425418637639775, 430945139142426634]
        if ctx.author.id in trusted and ctx.guild.id in trusted_servers:
            out = "Here are supported real languages:\n" + "\n".join(real) + "\nAnd here are Regaus' conlangs, which can also be used:\n" + "\n".join(con)
        else:
            out = "Here are supported languages:\n" + "\n".join(real)
        return await general.send(out, ctx.channel)
        # return await general.send("Here is a list of supported languages:\n" + "\n".join(languages), ctx.channel)

    @commands.group(name="settings", aliases=["set"])
    @commands.guild_only()
    @permissions.has_permissions(manage_guild=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def settings(self, ctx: commands.Context):
        """ Server settings """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @settings.command(name="current")
    @permissions.has_permissions(administrator=True)
    async def settings_current(self, ctx: commands.Context):
        """ Current settings (in JSON) """
        data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not data:
            return await general.send(f"Settings for {ctx.guild.name} not found.", ctx.channel)
        stuff = json.dumps(json.loads(data["data"]), indent=2)
        bio = BytesIO(stuff.encode("utf-8"))
        return await general.send(f"Current settings for {ctx.guild.name}", ctx.channel, file=discord.File(bio, time.file_ts("settings", "json")))

    @settings.command(name="template")
    @commands.is_owner()
    async def settings_template(self, ctx: commands.Context):
        """ Settings template (in JSON) """
        stuff = json.dumps(settings.template.copy(), indent=2)
        bio = BytesIO(stuff.encode("utf-8"))
        return await general.send("Settings template", ctx.channel, file=discord.File(bio, "template.json"))

    @settings.command(name="upload")
    @permissions.has_permissions(administrator=True)
    async def settings_upload(self, ctx: commands.Context):
        """ Upload settings using a JSON file """
        data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        ma = ctx.message.attachments
        if len(ma) == 1:
            name = ma[0].filename
            if not name.endswith('.json'):
                return await ctx.send("This must be a JSON file.")
            try:
                stuff = await ma[0].read()
            except discord.HTTPException or discord.NotFound:
                return await ctx.send("There was an error getting the file.")
        else:
            return await ctx.send("There must be exactly one JSON file.")
        try:
            json.loads(stuff)
        except Exception as e:
            return await ctx.send(f"Error loading file:\n{type(e).__name__}: {e}")
        stuff = json.dumps(json.loads(stuff), indent=0)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await general.send(f"Settings for {ctx.guild.name} have been updated.", ctx.channel)

    @settings.command(name="locale", aliases=["language"])
    async def set_locale(self, ctx: commands.Context, new_locale: str):
        """ Change the bot's language in this server """
        old_locale = langs.gl(ctx)
        if new_locale not in langs.languages.keys():
            return await general.send(langs.gls("settings_locale_invalid", old_locale, new_locale, ctx.prefix), ctx.channel)
        locale = self.bot.db.fetchrow("SELECT * FROM locales WHERE gid=?", (ctx.guild.id,))
        if locale:
            self.bot.db.execute("UPDATE locales SET locale=? WHERE gid=?", (new_locale, ctx.guild.id))
        else:
            self.bot.db.execute("INSERT INTO locales VALUES (?, ?)", (ctx.guild.id, new_locale))
        return await general.send(langs.gls("settings_locale_set", new_locale, new_locale, langs.gls("_name", new_locale)), ctx.channel)

    # @settings.command(name="currency")
    # async def set_currency(self, ctx: commands.Context, new: str):
    #     """ Change server currency """
    #     data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
    #     if data:
    #         _settings = json.loads(data["data"])
    #     else:
    #         _settings = settings.template.copy()
    #     _settings["currency"] = new
    #     stuff = json.dumps(_settings)
    #     if data:
    #         self.bot.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
    #     else:
    #         self.bot.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
    #     return await general.send(f"Updated the currency to {new}.", ctx.channel)

    @settings.group(name="prefixes")
    async def set_prefixes(self, ctx: commands.Context):
        """ Change server prefixes """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @set_prefixes.command(name="add")
    async def prefix_add(self, ctx: commands.Context, prefix: str):
        """ Add a new custom prefix """
        data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = settings.template.copy()
        _settings["prefixes"].append(prefix)
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            self.bot.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await general.send(f"Added {prefix} to the custom prefix list", ctx.channel)

    @set_prefixes.command(name="remove")
    async def prefix_remove(self, ctx: commands.Context, prefix: str):
        """ Remove a custom prefix """
        data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = settings.template.copy()
        try:
            _settings["prefixes"].remove(prefix)
        except ValueError:
            return await general.send(f"{prefix} is not a prefix in this server", ctx.channel)
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            self.bot.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await general.send(f"Removed {prefix} from the prefix list", ctx.channel)

    @set_prefixes.command(name="default")
    async def prefix_default(self, ctx: commands.Context):
        """ Toggle the use of default prefixes """
        data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = settings.template.copy()
        _settings["use_default"] ^= True
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            self.bot.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        t = _settings["use_default"]
        return await general.send(f"Default prefixes are now {'enabled' if t else 'disabled'} in this server.", ctx.channel)

    @settings.group(name="leveling", aliases=["levels", "lvl"])
    async def set_lvl(self, ctx: commands.Context):
        """ Leveling settings """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @set_lvl.command(name="enable")
    async def lvl_enable(self, ctx: commands.Context):
        """ Enable leveling """
        data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = settings.template.copy()
        if "leveling" not in _settings:
            _settings["leveling"] = settings.template["leveling"].copy()
            _settings["leveling"]["rewards"] = []
        _settings["leveling"]["enabled"] = True
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            self.bot.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await general.send("Leveling is now enabled.", ctx.channel)

    @set_lvl.command(name="disable")
    async def lvl_disable(self, ctx: commands.Context):
        """ Disable leveling """
        data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = settings.template.copy()
        if "leveling" not in _settings:
            _settings["leveling"] = settings.template["leveling"].copy()
            _settings["leveling"]["rewards"] = []
        _settings["leveling"]["enabled"] = False
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            self.bot.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await general.send("Leveling is now disabled.", ctx.channel)

    @set_lvl.command(name="multiplier", aliases=["xpm", "mult"])
    async def lvl_xpm(self, ctx: commands.Context, value: float):
        """ Set XP multiplier """
        if value > 10:
            return await general.send("The multiplier cannot be above 10.", ctx.channel)
        if value < 0.001:
            return await general.send("The multiplier cannot be below 0.001.", ctx.channel)
        data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = settings.template.copy()
        if "leveling" not in _settings:
            _settings["leveling"] = settings.template["leveling"].copy()
            _settings["leveling"]["rewards"] = []
        _settings["leveling"]["xp_multiplier"] = value
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            self.bot.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await general.send(f"The XP multiplier is now {value}", ctx.channel)

    @set_lvl.command(name="message", aliases=["lum", "msg"])
    async def lvl_lum(self, ctx: commands.Context, *, value: str):
        """ Set level up message """
        data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = settings.template.copy()
        if "leveling" not in _settings:
            _settings["leveling"] = settings.template["leveling"].copy()
            _settings["leveling"]["rewards"] = []
        _settings["leveling"]["level_up_message"] = value
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            self.bot.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await general.send(f"The level up message is now:\n{value}", ctx.channel)

    @set_lvl.group(name="ignored", aliases=["ic"])
    async def lvl_ic(self, ctx: commands.Context):
        """ Change ignored channels for leveling """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @lvl_ic.command(name="add")
    async def ic_add(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Add a channel to the list """
        data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = settings.template.copy()
        if "leveling" not in _settings:
            _settings["leveling"] = settings.template["leveling"].copy()
            _settings["leveling"]["rewards"] = []
        if channel.id in _settings["leveling"]["ignored_channels"]:
            return await general.send(f"Leveling is already disabled in {channel.mention}", ctx.channel)
        _settings["leveling"]["ignored_channels"].append(channel.id)
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            self.bot.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await general.send(f"Leveling will now be disabled in {channel.mention}", ctx.channel)

    @lvl_ic.command(name="remove")
    async def ic_remove(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Remove a channel from the list """
        data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = settings.template.copy()
        if "leveling" not in _settings:
            _settings["leveling"] = settings.template["leveling"].copy()
            _settings["leveling"]["rewards"] = []
        try:
            _settings["leveling"]["ignored_channels"].remove(channel.id)
        except ValueError:
            return await general.send(f"Leveling is already enabled in {channel.mention}", ctx.channel)
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            self.bot.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await general.send(f"Leveling is now enabled in {channel.mention}", ctx.channel)

    @set_lvl.command(name="announcement", aliases=["ac"])
    async def lvl_ac(self, ctx: commands.Context, channel: discord.TextChannel or None):
        """ Set level up announcement channel """
        data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = settings.template.copy()
        if "leveling" not in _settings:
            _settings["leveling"] = settings.template["leveling"].copy()
            _settings["leveling"]["rewards"] = []
        if channel is None:
            _settings["leveling"]["announce_channel"] = 0
        else:
            _settings["leveling"]["announce_channel"] = channel.id
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            self.bot.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        if channel is not None:
            return await general.send(f"Level ups will now be announced in {channel.mention}", ctx.channel)
        else:
            return await general.send(f"Level ups will now be announced where they happen", ctx.channel)

    @set_lvl.group(name="rewards", aliases=["rr", "lr"])
    async def lvl_rr(self, ctx: commands.Context):
        """ Set level rewards for the server """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @lvl_rr.command(name="add")
    async def rr_add(self, ctx: commands.Context, role: discord.Role, level: int):
        """ Add a level reward """
        if level > max_level or level <= -max_level:
            return await general.send(f"The level cannot be above the max level ({max_level:,})", ctx.channel)
        if role.is_default():
            return await general.send("You can't award the default role", ctx.channel)
        data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = settings.template.copy()
        if "leveling" not in _settings:
            _settings["leveling"] = settings.template["leveling"].copy()
            _settings["leveling"]["rewards"] = []
        try:
            rr = _settings["leveling"]["rewards"]
        except KeyError:
            rr = []
        roles = [i["role"] for i in rr]
        if role.id in roles:
            return await general.send("This role is already rewarded", ctx.channel)
        levels = [i["level"] for i in rr]
        if level in levels:
            return await general.send("There is already a reward for this level", ctx.channel)
        rr.append({"level": level, "role": role.id})
        _settings["leveling"]["rewards"] = rr
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            self.bot.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await general.send(f"The role {role.name} will now be rewarded at level {level:,}", ctx.channel)

    @lvl_rr.command(name="remove")
    async def rr_remove(self, ctx: commands.Context, role: discord.Role):
        """ Remove a role reward """
        data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = settings.template.copy()
        if "leveling" not in _settings:
            _settings["leveling"] = settings.template["leveling"].copy()
            _settings["leveling"]["rewards"] = []
        try:
            rr = _settings["leveling"]["rewards"]
        except KeyError:
            return await general.send("There are no level rewards right now anyway", ctx.channel)
        r = False
        for _role in rr:
            if _role["role"] == role.id:
                rr.remove(_role)
                r = True
                break
        if r:
            _settings["leveling"]["rewards"] = rr
            stuff = json.dumps(_settings)
            if data:
                self.bot.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
            else:
                self.bot.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
            return await general.send(f"The role {role.name} will no longer be rewarded", ctx.channel)
        else:
            return await general.send(f"The role {role.name} was not removed from the level rewards list.", ctx.channel)

    @settings.group(name="roles")
    async def set_shop(self, ctx: commands.Context):
        """ Let people get free roles """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @set_shop.command(name="add")
    async def shop_add(self, ctx: commands.Context, role: discord.Role):
        """ Add a shop item """
        data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = settings.template.copy()
        try:
            roles = _settings["roles"]
        except KeyError:
            roles = []
        if role.id in roles:
            return await general.send("This role is already available", ctx.channel)
        roles.append(role.id)
        _settings["roles"] = roles
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            self.bot.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await general.send(f"The role {role.name} is now available for available roles.", ctx.channel)

    @set_shop.command(name="remove")
    async def shop_remove(self, ctx: commands.Context, role: discord.Role):
        """ Remove a shop item """
        data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = settings.template.copy()
        try:
            rr = _settings["roles"]
        except KeyError:
            return await general.send("There are already no roles", ctx.channel)
        r = False
        for _role in rr:
            if _role == role.id:
                rr.remove(_role)
                r = True
                break
        if r:
            _settings["roles"] = rr
            stuff = json.dumps(_settings)
            if data:
                self.bot.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
            else:
                self.bot.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
            return await general.send(f"The role {role.name} has been removed from the available roles", ctx.channel)
        else:
            return await general.send(f"The role {role.name} was not removed from the available roles", ctx.channel)

    @settings.command(name="muterole")
    async def set_mute_role(self, ctx: commands.Context, role: discord.Role):
        """ Set the mute role """
        data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = settings.template.copy()
        _settings["mute_role"] = role.id
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            self.bot.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await general.send(f"The muted role has been set to {role.name}", ctx.channel)

    @settings.group(name="starboard")
    async def set_starboard(self, ctx: commands.Context):
        """ Starboard settings """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @set_starboard.command(name="toggle")
    async def starboard_toggle(self, ctx: commands.Context):
        """ Toggle starboard on or off """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = settings.template.copy()
        if "starboard" not in _settings:
            _settings["starboard"] = settings.template["starboard"].copy()
        _settings["starboard"]["enabled"] ^= True
        is_or_not = "enabled" if _settings["starboard"]["enabled"] else "disabled"
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            self.bot.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await general.send(f"Starboard is now {is_or_not} in this server.", ctx.channel)

    @set_starboard.command(name="channel")
    async def starboard_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Set the channel for starboard messages """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = settings.template.copy()
        if "starboard" not in _settings:
            _settings["starboard"] = settings.template["starboard"].copy()
        _settings["starboard"]["channel"] = channel.id
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            self.bot.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await general.send(f"Starboard messages will now be sent to {channel.mention}.", ctx.channel)

    @set_starboard.command(name="minimum", aliases=["requirement"])
    async def starboard_requirement(self, ctx: commands.Context, requirement: int):
        """ Set the minimum amount of stars before the message is sent to the starboard """
        if requirement < 1:
            return await general.send("The requirement has to be 1 or above.", ctx.channel)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = settings.template.copy()
        if "starboard" not in _settings:
            _settings["starboard"] = settings.template["starboard"].copy()
        _settings["starboard"]["minimum"] = requirement
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            self.bot.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await general.send(f"The minimum amount of stars to appear on the starboard is now {requirement}.", ctx.channel)

    @commands.command(name="prefix")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def prefix(self, ctx: commands.Context):
        """ Server prefixes """
        _data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if not _data:
            dp = self.bot.local_config["prefixes"].copy()
            cp = None
        else:
            data = json.loads(_data['data'])
            dp = self.bot.local_config["prefixes"].copy() if data['use_default'] else []
            cp = data['prefixes']
        dp.append(self.bot.user.mention)
        embed = discord.Embed(colour=general.random_colour())
        embed.title = f"Prefixes for {self.bot.user.name} in {ctx.guild.name}"
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(name="Default", value='\n'.join(dp), inline=True)
        if cp is not None and cp != []:
            embed.add_field(name="Custom", value='\n'.join(cp), inline=True)
        return await general.send(None, ctx.channel, embed=embed)

    @commands.command(name="addrole", aliases=["getrole", "giverole", "joinrole"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def give_role(self, ctx: commands.Context, role: discord.Role = None):
        """ Add a role """
        _data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        data = {}
        if not _data or "roles" not in (data := json.loads(_data['data'])):
            return await general.send("There are no roles available like that.", ctx.channel)
        roles = data["roles"]
        if role is not None:
            if role.id in roles:
                try:
                    await ctx.author.add_roles(role, reason="Free roles")
                    return await general.send(f"Successfully gave {ctx.author.name} the role {role}", ctx.channel)
                except Exception as e:
                    return await general.send(f"Unable to give you the role:\n`{type(e).__name__}: {e}`", ctx.channel)
            else:
                return await general.send("You can't have that role.", ctx.channel)
        else:
            embed = discord.Embed(description="\n".join(f"<@&{r}>" for r in roles), colour=general.random_colour())
            embed.set_thumbnail(url=ctx.guild.icon_url)
            return await general.send(f"Roles available in {ctx.guild}", ctx.channel, embed=embed)

    @commands.command(name="removerole", aliases=["takerole", "leaverole"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def leave_role(self, ctx: commands.Context, role: discord.Role):
        """ Remove a role """
        _data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        data = {}
        if not _data or "roles" not in (data := json.loads(_data['data'])):
            return await general.send("There are no roles available in these commands in this server.", ctx.channel)
        roles = data["roles"]
        if role.id in roles:
            try:
                await ctx.author.remove_roles(role, reason="Free roles")
                return await general.send(f"Successfully removed {role} from {ctx.author.name}", ctx.channel)
            except Exception as e:
                return await general.send(f"Unable to remove the role from you:\n`{type(e).__name__}: {e}`", ctx.channel)
        else:
            return await general.send("You can't remove that role.", ctx.channel)


def setup(bot):
    bot.add_cog(Settings(bot))
