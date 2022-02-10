import json
from io import BytesIO

import discord
from discord.ext import commands

from cogs.leveling import max_level
from utils import bot_data, general, languages, permissions, settings, time


class Settings(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        self.template = {
            "cobble": settings.template_cobble,
            "kyomi": settings.template_mizuki,
            "suager": settings.template_suager
        }.get(self.bot.name).copy()

    @commands.command(name="languages", aliases=["language", "langs", "lang"])
    async def languages(self, ctx: commands.Context):
        """ List of all supported languages """
        nat, con, rsl = [], [], []
        _en = languages.Language("en")
        exclude = ["_self", "_en", "_valid", "_conlang"]
        for language in list(languages.languages.languages.keys()):
            _language = languages.Language(language)
            if language == "en":
                completeness = 1
            else:
                strings = 0
                matching = 0
                for k in languages.languages.languages["en"].keys():
                    if k.startswith("country_") or k in exclude:
                        continue
                    d1, d2 = _en.data(k), _language.data(k)

                    # Well they should never be different, but better make sure
                    # Behaviour for when the data is a list
                    if isinstance(d1, list) and isinstance(d2, list):
                        if len(d1) == len(d2):
                            # If the lengths are the same, then check through every single string inside
                            for i, s1 in enumerate(d1):
                                strings += 1
                                s2 = d2[i]
                                if s1 == s2:
                                    matching += 1
                        else:
                            # If the lengths are somehow different, then we count it all as just one big string
                            # Don't bother checking if any strings inside there match or not...
                            strings += 1

                    # Behaviour for when the data is a dict
                    elif isinstance(d1, dict) and isinstance(d2, dict):
                        for key, s1 in d1.items():
                            s2 = d2.get(key)
                            strings += 1
                            if s1 == s2:
                                matching += 1

                    # Behaviour for when the data is something else (so, a string)
                    else:
                        strings += 1
                        if d1 == d2:
                            matching += 1
                completeness = 1 - (matching / strings)

            out = f"`{language}`: {_language.string('_self')} - {_language.string('_en')} - {completeness:.1%} translated"
            conlang = _language.data("_conlang")
            if not _language.data("_valid"):
                continue
            add_list = rsl if conlang == 2 else con if conlang == 1 else nat
            add_list.append(out)
        # Regaus, Suager, Five, Leitoxz, 1337xp, Potato,
        # Chikin, Karmeck, Kyomi, Shawn, Mid, Aya
        trusted = [302851022790066185, 517012611573743621, 430891116318031872, 291665491221807104, 679819572278198272, 374853432168808448,
                   441028310789783563, 857360761135431730, 417390734690484224, 236884090651934721, 581206591051923466, 527729196688998415]
        # wanderer, neppkun, dragon, bowser
        no_conlangs = [411996407642456076, 350199484246130690, 443363116504580117,  94762492923748352]
        # Senko Lair, RK, 3tk4
        trusted_servers = [568148147457490954, 738425418637639775, 430945139142426634]
        # List of trusted people and servers last updated 27/06/2021 AD
        output = "__List of supported languages:__\n" + "\n".join(nat)
        # If the person is in a trusted server while not being in the No Conlangs list, or if the person is in a DM while they're trusted
        if ((ctx.guild is not None and ctx.guild.id in trusted_servers) and ctx.author.id not in no_conlangs) or (ctx.guild is None and ctx.author.id in trusted):
            output += "\n\n__Conlangs supported:__\n" + "\n".join(con)
            if ctx.author.id in trusted:
                output += "\n\n__RSLs supported:__\n" + "\n".join(rsl)
        return await general.send(output, ctx.channel)

    @commands.group(name="settings", aliases=["set"], case_insensitive=True)
    @commands.guild_only()
    @permissions.has_permissions(manage_guild=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def settings(self, ctx: commands.Context):
        """ Server settings """
        if ctx.invoked_subcommand is None:
            language = self.bot.language(ctx)
            data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
            if not data:
                return await ctx.send_help(str(ctx.command))
            setting = json.loads(data["data"])
            embed = discord.Embed(colour=general.random_colour())
            embed.title = language.string("settings_current", ctx.guild.name)
            embed.set_thumbnail(url=str(ctx.guild.icon.replace(size=1024)))
            embed.set_footer(text=language.string("settings_current_footer", ctx.prefix))
            embed.add_field(name=language.string("settings_current_language"), value=language.string("_self"), inline=False)
            dp, cp = self.prefix_list(ctx)
            embed.add_field(name=language.string("settings_current_prefix"), value=f"`{'`, `'.join(dp + cp)}`", inline=False)
            if self.bot.name in ["kyomi", "suager"]:
                mute_role = language.string("generic_none")
                if "mute_role" in setting:
                    if setting["mute_role"] != 0:
                        mute_role = f"<@&{setting['mute_role']}>"
                embed.add_field(name=language.string("settings_current_mute"), value=mute_role, inline=False)
                # if ctx.guild.id in [568148147457490954, 738425418637639775]:
                #     mod, users, messages = language.string("settings_current_disabled"), language.string("settings_current_disabled"), language.string("settings_current_disabled")
                #     message_ignore = False
                #     if "audit_logs" in setting:
                #         if setting["audit_logs"]:
                #             mod = f"<#{setting['audit_logs']}>"
                #     if "user_logs" in setting:
                #         if setting["user_logs"]:
                #             users = f"<#{setting['user_logs']}>"
                #     if "message_logs" in setting:
                #         if setting["message_logs"]:
                #             messages = f"<#{setting['message_logs']}>"
                #             message_ignore = True
                #     embed.add_field(name=language.string("settings_current_logs"), value=language.string("settings_current_logs2", mod, users, messages), inline=False)
                #     if message_ignore:
                #         ignore = language.string("generic_none")
                #         if "message_ignore" in setting:
                #             if setting["message_ignore"]:
                #                 ignore = ", ".join([f"<#{channel}>" for channel in setting["message_ignore"]])
                #         embed.add_field(name=language.string("settings_current_messages_ignore"), value=ignore, inline=False)
                sb = language.string("settings_current_disabled")
                if "starboard" in setting:
                    starboard = setting["starboard"]
                    if starboard["enabled"]:
                        sb = language.string("settings_current_starboard", language.number(starboard["minimum"]), starboard["channel"])
                embed.add_field(name=language.string("settings_starboard"), value=sb, inline=False)

                if self.bot.name in ["suager"]:
                    lvl = language.string("settings_current_disabled")
                    if "leveling" in setting:
                        if setting["leveling"]["enabled"]:
                            lvl = language.string("settings_current_leveling", ctx.prefix)
                    embed.add_field(name=language.string("settings_leveling"), value=lvl, inline=False)

                bd = language.string("settings_current_disabled")
                if "birthdays" in setting:
                    if setting["birthdays"]["enabled"]:
                        bd = language.string("settings_current_birthdays", ctx.prefix)
                embed.add_field(name=language.string("settings_birthdays"), value=bd, inline=False)

                if self.bot.name in ["suager"]:
                    polls_channel, polls_anonymity = language.string("settings_current_polls_channel_none"), language.yes(True)  # Default settings
                    if "polls" in setting:
                        polls = setting["polls"]
                        if polls["channel"]:
                            polls_channel = f"<#{polls['channel']}>"
                        polls_anonymity = language.yes(polls["voter_anonymity"])
                    embed.add_field(name=language.string("settings_current_polls"), value=language.string("settings_current_polls2", polls_channel, polls_anonymity), inline=False)

                members, bots = language.string("generic_none"), language.string("generic_none")
                if "join_roles" in setting:
                    join_roles = setting["join_roles"]
                    if join_roles["members"]:
                        # members = f"<@&{join_roles['members']}>"
                        members = language.join([f"<@&{role}>" for role in join_roles["members"]])
                    else:
                        members = language.string("generic_none")
                    if join_roles["bots"]:
                        bots = language.join([f"<@&{role}>" for role in join_roles["bots"]])
                    else:
                        bots = language.string("generic_none")
                embed.add_field(name=language.string("settings_current_join_roles"), value=language.string("settings_current_join_roles2", members, bots), inline=False)

                welcome_channel, welcome_message = language.string("settings_current_disabled"), None
                if "welcome" in setting:
                    welcome = setting["welcome"]
                    if welcome["channel"]:
                        welcome_channel = language.string("settings_current_welcome_channel", welcome["channel"])
                        welcome_message = f"{welcome['message'][:1021]}..." if len(welcome["message"]) > 1024 else welcome["message"]
                embed.add_field(name=language.string("settings_current_welcome"), value=welcome_channel, inline=False)
                if welcome_message:
                    embed.add_field(name=language.string("settings_current_welcome_message"), value=welcome_message, inline=False)

                goodbye_channel, goodbye_message = language.string("settings_current_disabled"), None
                if "goodbye" in setting:
                    goodbye = setting["goodbye"]
                    if goodbye["channel"]:
                        goodbye_channel = language.string("settings_current_goodbye_channel", goodbye["channel"])
                        goodbye_message = f"{goodbye['message'][:1021]}..." if len(goodbye["message"]) > 1024 else goodbye["message"]
                embed.add_field(name=language.string("settings_current_goodbye"), value=goodbye_channel, inline=False)
                if goodbye_message:
                    embed.add_field(name=language.string("settings_current_goodbye_message"), value=goodbye_message, inline=False)

                msg = language.string("settings_current_disabled")
                if "message_logs" in setting:
                    if setting["message_logs"]["enabled"]:
                        msg = language.string("settings_current_messages", ctx.prefix)
                embed.add_field(name=language.string("settings_messages"), value=msg, inline=False)

                mod_dms_text = language.string("settings_current_mod_dms_disabled", ctx.prefix)
                if "mod_dms" in setting:
                    mod_dms = setting["mod_dms"]
                    warn, mute, kick, ban = mod_dms["warn"], mod_dms["mute"], mod_dms["kick"], mod_dms["ban"]
                    mod_dms_text = language.string("settings_current_mod_dms2", warn=language.yes(warn), mute=language.yes(mute), kick=language.yes(kick), ban=language.yes(ban))
                embed.add_field(name=language.string("settings_current_mod_dms"), value=mod_dms_text, inline=False)

                mod_logs_text = language.string("settings_current_mod_logs_disabled", ctx.prefix)
                if "mod_logs" in setting:
                    def channel(cid: int):
                        if cid == 0:
                            return language.string("settings_current_disabled")
                        return f"<#{cid}>"

                    mod_logs = setting["mod_logs"]
                    warn, mute, kick, ban, roles = mod_logs["warn"], mod_logs["mute"], mod_logs["kick"], mod_logs["ban"], mod_logs["roles"]
                    mod_logs_text = language.string("settings_current_mod_logs2", warn=channel(warn), mute=channel(mute), kick=channel(kick), ban=channel(ban), roles=channel(roles))
                embed.add_field(name=language.string("settings_current_mod_logs"), value=mod_logs_text, inline=False)

                return await general.send(None, ctx.channel, embed=embed)
            # return await ctx.send_help(str(ctx.command))

    @settings.command(name="current")
    @commands.is_owner()
    # @permissions.has_permissions(administrator=True)
    async def settings_current(self, ctx: commands.Context):
        """ Current settings (in JSON) """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if not data:
            return await general.send(f"Settings for {ctx.guild.name} not found.", ctx.channel)
        stuff = json.dumps(json.loads(data["data"]), indent=2)
        bio = BytesIO(stuff.encode("utf-8"))
        return await general.send(f"Current settings for {ctx.guild.name}", ctx.channel, file=discord.File(bio, time.file_ts("settings", "json")))

    @settings.command(name="template")
    @commands.is_owner()
    async def settings_template(self, ctx: commands.Context):
        """ Settings template (in JSON) """
        stuff = json.dumps(self.template.copy(), indent=2)
        bio = BytesIO(stuff.encode("utf-8"))
        return await general.send("Settings template", ctx.channel, file=discord.File(bio, "template.json"))

    @settings.command(name="upload")
    @commands.is_owner()
    # @permissions.has_permissions(administrator=True)
    async def settings_upload(self, ctx: commands.Context):
        """ Upload settings using a JSON file """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
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
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(f"Settings for {ctx.guild.name} have been updated.", ctx.channel)

    @settings.command(name="language", aliases=["lang"])
    async def set_language(self, ctx: commands.Context, new_language: str):
        """ Change the bot's language in this server """
        old_language = self.bot.language(ctx)
        new_language = new_language.lower()  # Make it case-insensitive just in case
        if new_language not in languages.languages.languages.keys():
            return await general.send(old_language.string("settings_locale_invalid", new_language, ctx.prefix), ctx.channel)
        elif not languages.Language(new_language).data("_valid"):
            return await general.send(old_language.string("settings_locale_invalid", new_language, ctx.prefix), ctx.channel)
        locale = self.bot.db.fetchrow("SELECT * FROM locales WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if locale:
            self.bot.db.execute("UPDATE locales SET locale=? WHERE gid=? AND bot=?", (new_language, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO locales VALUES (?, ?, ?)", (ctx.guild.id, new_language, self.bot.name))
        return await general.send(self.bot.language2(new_language).string("settings_locale_set"), ctx.channel)

    @settings.group(name="prefixes", aliases=["prefix", "p"], case_insensitive=True)
    async def set_prefixes(self, ctx: commands.Context):
        """ Change server prefixes

        See //prefixes to see the list of active prefixes for the server"""
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @set_prefixes.command(name="add")
    async def prefix_add(self, ctx: commands.Context, prefix: str):
        """ Add a new custom prefix """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        _settings["prefixes"].append(prefix)
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(self.bot.language(ctx).string("settings_prefix_add", prefix), ctx.channel)
        # return await general.send(f"Added {prefix} to the custom prefix list", ctx.channel)

    @set_prefixes.command(name="remove")
    async def prefix_remove(self, ctx: commands.Context, prefix: str):
        """ Remove a custom prefix """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        try:
            _settings["prefixes"].remove(prefix)
        except ValueError:
            return await general.send(self.bot.language(ctx).string("settings_prefix_remove_none", prefix), ctx.channel)
            # return await general.send(f"{prefix} is not a prefix in this server", ctx.channel)
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(self.bot.language(ctx).string("settings_prefix_remove", prefix), ctx.channel)
        # return await general.send(f"Removed {prefix} from the prefix list", ctx.channel)

    @set_prefixes.command(name="default")
    async def prefix_default(self, ctx: commands.Context, action: str):
        """ Enable or disable the use of default prefixes """
        language = self.bot.language(ctx)
        if action not in ["enable", "disable"]:
            return await general.send(language.string("settings_prefix_default_invalid"), ctx.channel)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        _settings["use_default"] = action == "enable"
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(language.string("settings_prefix_default" if action == "enable" else "settings_prefix_default2"), ctx.channel)
        # return await general.send(f"Default prefixes are now {'enabled' if t else 'disabled'} in this server.", ctx.channel)

    @settings.group(name="leveling", aliases=["levels", "lvl"], case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["suager"])
    async def set_lvl(self, ctx: commands.Context):
        """ Leveling settings """
        if ctx.invoked_subcommand is None:
            language = self.bot.language(ctx)
            data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
            if not data:
                return await general.send(language.string("settings_none"), ctx.channel)
            setting = json.loads(data["data"])
            if "leveling" not in setting:
                return await general.send(language.string("settings_leveling_none"), ctx.channel)
            leveling = setting["leveling"]
            embed = discord.Embed(colour=general.random_colour())
            embed.title = language.string("settings_leveling", ctx.guild.name)
            embed.set_thumbnail(url=str(ctx.guild.icon.replace(size=1024)))
            embed.set_footer(text=language.string("settings_leveling_footer", ctx.prefix))
            embed.add_field(name=language.string("settings_leveling_enabled2"), value=language.yes(leveling["enabled"]), inline=False)
            embed.add_field(name=language.string("settings_leveling_multiplier"), value="x" + language.number(leveling["xp_multiplier"], precision=2), inline=False)
            ac = leveling["announce_channel"]
            if ac == -1:
                embed.add_field(name=language.string("settings_leveling_announcements"), value=language.string("settings_current_disabled"), inline=False)
            else:
                if ac == 0:
                    embed.add_field(name=language.string("settings_leveling_announcements"), value=language.string("settings_leveling_announcements_zero"), inline=False)
                else:
                    embed.add_field(name=language.string("settings_leveling_announcements"), value=f"<#{ac}>", inline=False)
                message = f"{leveling['level_up_message'][:1021]}..." if len(leveling["level_up_message"]) > 1024 else leveling["level_up_message"]
                embed.add_field(name=language.string("settings_leveling_message"), value=message, inline=False)
                if "level_up_role" in leveling:
                    if leveling["level_up_role"]:
                        message = f"{leveling['level_up_role'][:1021]}..." if len(leveling["level_up_role"]) > 1024 else leveling["level_up_role"]
                        embed.add_field(name=language.string("settings_leveling_message_role"), value=message, inline=False)
                if "level_up_highest" in leveling:
                    if leveling["level_up_highest"]:
                        message = f"{leveling['level_up_highest'][:1021]}..." if len(leveling["level_up_highest"]) > 1024 else leveling["level_up_highest"]
                        embed.add_field(name=language.string("settings_leveling_message_highest"), value=message, inline=False)
                if "level_up_max" in leveling:
                    if leveling["level_up_max"]:
                        message = f"{leveling['level_up_max'][:1021]}..." if len(leveling["level_up_max"]) > 1024 else leveling["level_up_max"]
                        embed.add_field(name=language.string("settings_leveling_message_max"), value=message, inline=False)
            if not leveling["ignored_channels"]:
                ignored = language.string("generic_none")
            else:
                length = len(leveling["ignored_channels"])
                if length <= 48:
                    ignored = "\n".join(f"<#{channel}>" for channel in leveling["ignored_channels"])
                else:
                    ignored = "\n".join(f"<#{channel}>" for channel in leveling["ignored_channels"][:45])
                    ignored += language.string("settings_leveling_ignored_many", language.number(length - 45))
            embed.add_field(name=language.string("settings_leveling_ignored"), value=ignored, inline=False)
            embed.add_field(name=language.string("settings_leveling_rewards"), value=language.string("settings_leveling_rewards2", ctx.prefix), inline=False)
            return await general.send(None, ctx.channel, embed=embed)

    @set_lvl.command(name="enable")
    async def lvl_enable(self, ctx: commands.Context):
        """ Enable leveling """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "leveling" not in _settings:
            _settings["leveling"] = self.template["leveling"].copy()
            _settings["leveling"]["rewards"] = []
        _settings["leveling"]["enabled"] = True
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(self.bot.language(ctx).string("settings_leveling_enabled"), ctx.channel)
        # return await general.send("Leveling is now enabled.", ctx.channel)

    @set_lvl.command(name="disable")
    async def lvl_disable(self, ctx: commands.Context):
        """ Disable leveling """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "leveling" not in _settings:
            _settings["leveling"] = self.template["leveling"].copy()
            _settings["leveling"]["rewards"] = []
        _settings["leveling"]["enabled"] = False
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(self.bot.language(ctx).string("settings_leveling_disabled"), ctx.channel)
        # return await general.send("Leveling is now disabled.", ctx.channel)

    @set_lvl.command(name="multiplier", aliases=["mult"])
    async def lvl_multiplier(self, ctx: commands.Context, value: float):
        """ Set the XP gain multiplier """
        language = self.bot.language(ctx)
        if value > 10:
            return await general.send(language.string("settings_leveling_multiplier_max"), ctx.channel)
            # return await general.send("The multiplier cannot be above 10.", ctx.channel)
        if value < 0.04:  # Used to be 0.001, but bumped up to 0.04 so that you could get at least 1 XP at the 27 rate.
            return await general.send(language.string("settings_leveling_multiplier_min"), ctx.channel)
            # return await general.send("The multiplier cannot be below 0.001.", ctx.channel)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "leveling" not in _settings:
            _settings["leveling"] = self.template["leveling"].copy()
            _settings["leveling"]["rewards"] = []
        _settings["leveling"]["xp_multiplier"] = value
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(language.string("settings_leveling_multiplier_set", language.number(value, precision=2)), ctx.channel)
        # return await general.send(f"The XP multiplier is now {value}", ctx.channel)

    @set_lvl.group(name="message", aliases=["msg"], invoke_without_command=True, case_insensitive=True)
    async def lvl_message(self, ctx: commands.Context, *, value: str):
        """ Set level up message

        See `//settings leveling message variables` for the list of available variables"""
        if ctx.invoked_subcommand is None:
            return await self.level_up_message_general(ctx, value, {
                "key": "level_up_message",
                "level": 17,
                "current_reward_level": 15,
                "next_reward": "settings_leveling_reward_placeholder2",
                "next_reward_level": 20,
                "next_reward_progress": 3,
                "output": "settings_leveling_message_set"
            })

    @lvl_message.command(name="newrole", aliases=["newreward", "nr"])
    async def level_up_message_new_role(self, ctx: commands.Context, *, value: str):
        """ Add a custom level up message when the user has achieved a new level reward """
        return await self.level_up_message_general(ctx, value, {
            "key": "level_up_role",
            "level": 10,
            "current_reward_level": 10,
            "next_reward": "settings_leveling_reward_placeholder2",
            "next_reward_level": 15,
            "next_reward_progress": 5,
            "output": "settings_leveling_message_set4"
        })

    @lvl_message.command(name="highestrole", aliases=["hr"])
    async def level_up_message_highest_role(self, ctx: commands.Context, *, value: str):
        """ Add a custom level up message when the user has achieved the highest available level reward """
        return await self.level_up_message_general(ctx, value, {
            "key": "level_up_highest",
            "level": 175,
            "current_reward_level": 150,
            "next_reward": "leveling_rewards_max",
            "next_reward_level": max_level,
            "next_reward_progress": max_level - 175,
            "output": "settings_leveling_message_set2"
        })

    @lvl_message.command(name="highestlevel", aliases=["hl", "max", str(max_level)])
    async def level_up_message_highest_level(self, ctx: commands.Context, *, value: str):
        """ Add a custom level up message when the user has reached the max level """
        return await self.level_up_message_general(ctx, value, {
            "key": "level_up_max",
            "level": 200,
            "current_reward_level": 150,
            "next_reward": "leveling_rewards_max",
            "next_reward_level": max_level,
            "next_reward_progress": 0,
            "output": "settings_leveling_message_set3"
        })

    async def level_up_message_general(self, ctx: commands.Context, value: str, variables: dict):
        """ For all level up message functions """
        key = variables["key"]
        language = self.bot.language(ctx)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "leveling" not in _settings:
            _settings["leveling"] = self.template["leveling"].copy()
            _settings["leveling"]["rewards"] = []
        value = value.replace("\\n", "\n")
        _settings["leveling"][key] = value
        message2 = value \
            .replace("[MENTION]", ctx.author.mention) \
            .replace("[USER]", ctx.author.name) \
            .replace("[LEVEL]", language.number(variables["level"])) \
            .replace("[CURRENT_REWARD]", language.string("settings_leveling_reward_placeholder")) \
            .replace("[CURRENT_REWARD_LEVEL]", language.number(variables["current_reward_level"])) \
            .replace("[NEXT_REWARD]", language.string(variables["next_reward"])) \
            .replace("[NEXT_REWARD_LEVEL]", language.number(variables["next_reward_level"])) \
            .replace("[NEXT_REWARD_PROGRESS]", language.number(variables["next_reward_progress"])) \
            .replace("[MAX_LEVEL]", language.number(max_level))
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(language.string(variables["output"], value, message2), ctx.channel)

    @lvl_message.command(name="variables", aliases=["vars"])
    async def level_up_message_variables(self, ctx: commands.Context):
        """ Level up message variables """
        return await general.send(self.bot.language(ctx).string("settings_leveling_message_variables"), ctx.channel)

    @set_lvl.group(name="ignore", aliases=["ignored", "blacklist", "ic"], case_insensitive=True)
    async def lvl_ignored(self, ctx: commands.Context):
        """ Disable XP gain in channels """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @lvl_ignored.command(name="add")
    async def ic_add(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Disable XP gain in a channel """
        language = self.bot.language(ctx)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "leveling" not in _settings:
            _settings["leveling"] = self.template["leveling"].copy()
            _settings["leveling"]["rewards"] = []
        if channel.id in _settings["leveling"]["ignored_channels"]:
            return await general.send(language.string("settings_leveling_ignored_already", channel.mention), ctx.channel)
            # return await general.send(f"Leveling is already disabled in {channel.mention}", ctx.channel)
        _settings["leveling"]["ignored_channels"].append(channel.id)
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(language.string("settings_leveling_ignored_add", channel.mention), ctx.channel)
        # return await general.send(f"Leveling will now be disabled in {channel.mention}", ctx.channel)

    @lvl_ignored.command(name="remove")
    async def ic_remove(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Enable XP gain in a channel """
        language = self.bot.language(ctx)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "leveling" not in _settings:
            _settings["leveling"] = self.template["leveling"].copy()
            _settings["leveling"]["rewards"] = []
        try:
            _settings["leveling"]["ignored_channels"].remove(channel.id)
        except ValueError:
            return await general.send(language.string("settings_leveling_ignored_already2", channel.mention), ctx.channel)
            # return await general.send(f"Leveling is already enabled in {channel.mention}", ctx.channel)
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(language.string("settings_leveling_ignored_remove", channel.mention), ctx.channel)
        # return await general.send(f"Leveling is now enabled in {channel.mention}", ctx.channel)

    @set_lvl.group(name="announcements", aliases=["announcement", "ac"], invoke_without_command=True, case_insensitive=True)
    async def lvl_announcements(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ Set level up announcement channel

        Type a channel to set the channel as the level up channel
        Don't type a channel to make level ups announced where the level up occurs
        Type "disable" to disable level up announcements altogether"""
        if ctx.invoked_subcommand is None:
            data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
            if data:
                _settings = json.loads(data["data"])
            else:
                _settings = self.template.copy()
            if "leveling" not in _settings:
                _settings["leveling"] = self.template["leveling"].copy()
                _settings["leveling"]["rewards"] = []
            if channel is None:
                _settings["leveling"]["announce_channel"] = 0
            else:
                _settings["leveling"]["announce_channel"] = channel.id
            stuff = json.dumps(_settings)
            if data:
                self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
            else:
                self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
            if channel is not None:
                return await general.send(self.bot.language(ctx).string("settings_leveling_announcements_set", channel.mention), ctx.channel)
                # return await general.send(f"Level ups will now be announced in {channel.mention}", ctx.channel)
            else:
                return await general.send(self.bot.language(ctx).string("settings_leveling_announcements_none"), ctx.channel)
                # return await general.send(f"Level ups will now be announced where they happen", ctx.channel)

    @lvl_announcements.command(name="disable")
    async def lvl_announcements_disable(self, ctx: commands.Context):
        """ Disable level up announcements """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "leveling" not in _settings:
            _settings["leveling"] = self.template["leveling"].copy()
            _settings["leveling"]["rewards"] = []
        _settings["leveling"]["announce_channel"] = -1
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(self.bot.language(ctx).string("settings_leveling_announcements_disabled"), ctx.channel)

    @set_lvl.group(name="rewards", aliases=["rr", "lr"], case_insensitive=True)
    async def lvl_rewards(self, ctx: commands.Context):
        """ Set level rewards for the server """
        if ctx.invoked_subcommand is None:
            # return await level_rewards(self, ctx)
            return await ctx.send_help(str(ctx.command))

    @lvl_rewards.command(name="add", aliases=["a", "+"])
    async def level_rewards_add(self, ctx: commands.Context, role: discord.Role, level: int):
        """ Add a level reward """
        language = self.bot.language(ctx)
        if level > max_level or level <= -max_level:
            return await general.send(language.string("settings_leveling_rewards_max", language.number(max_level)), ctx.channel)
            # return await general.send(f"The level cannot be above the max level ({max_level:,})", ctx.channel)
        if role.is_default():
            return await general.send(language.string("settings_leveling_rewards_default"), ctx.channel)
            # return await general.send("You can't award the default role", ctx.channel)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "leveling" not in _settings:
            _settings["leveling"] = self.template["leveling"].copy()
            _settings["leveling"]["rewards"] = []
        try:
            rr = _settings["leveling"]["rewards"]
        except KeyError:
            rr = []
        # roles = [i["role"] for i in rr]
        # if role.id in roles:
        for reward in rr:
            if role.id == reward["role"]:
                return await general.send(language.string("settings_leveling_rewards_already_role", language.number(reward["level"]), ctx.prefix), ctx.channel)
            if level == reward["level"]:
                role = ctx.guild.get_role(reward["role"])
                return await general.send(language.string("settings_leveling_rewards_already_level", role, ctx.prefix), ctx.channel)
            # return await general.send("This role is already rewarded", ctx.channel)
        # levels = [i["level"] for i in rr]
        # if level in levels:
        #     return await general.send("There is already a reward for this level", ctx.channel)
        rr.append({"level": level, "role": role.id})
        _settings["leveling"]["rewards"] = rr
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(language.string("settings_leveling_rewards_add", role.name, language.number(level)), ctx.channel)
        # return await general.send(f"The role {role.name} will now be rewarded at level {level:,}", ctx.channel)

    @lvl_rewards.command(name="remove", aliases=["r", "-"])
    async def level_rewards_remove(self, ctx: commands.Context, role: discord.Role):
        """ Remove a role reward """
        language = self.bot.language(ctx)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "leveling" not in _settings:
            _settings["leveling"] = self.template["leveling"].copy()
            _settings["leveling"]["rewards"] = []
        try:
            rr = _settings["leveling"]["rewards"]
        except KeyError:
            return await general.send(language.string("settings_leveling_rewards_none"), ctx.channel)
            # return await general.send("There are no level rewards right now anyway", ctx.channel)
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
                self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
            else:
                self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
            return await general.send(language.string("settings_leveling_rewards_remove", role.name), ctx.channel)
            # return await general.send(f"The role {role.name} will no longer be rewarded", ctx.channel)
        else:
            return await general.send(language.string("settings_leveling_rewards_not_found", role.name), ctx.channel)
            # return await general.send(f"The role {role.name} was not removed from the level rewards list.", ctx.channel)

    @lvl_rewards.command(name="deleted", aliases=["del", "d"])
    async def level_rewards_deleted(self, ctx: commands.Context):
        """ Remove roles that no longer exist from the role rewards """
        language = self.bot.language(ctx)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "leveling" not in _settings:
            _settings["leveling"] = self.template["leveling"].copy()
            _settings["leveling"]["rewards"] = []
        try:
            rr = _settings["leveling"]["rewards"]
        except KeyError:
            return await general.send(language.string("settings_leveling_rewards_none"), ctx.channel)
            # return await general.send("There are no level rewards right now anyway", ctx.channel)
        removed = 0
        roles = [role.id for role in await ctx.guild.fetch_roles()]  # Get IDs of all roles in a server
        for _role in rr:
            if _role["role"] not in roles:
                rr.remove(_role)
                removed += 1
        if removed > 0:
            _settings["leveling"]["rewards"] = rr
            stuff = json.dumps(_settings)
            if data:
                self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
            else:
                self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
            return await general.send(language.string("settings_leveling_rewards_deleted", language.number(removed)), ctx.channel)
            # return await general.send(f"Removed {removed} roles from the level rewards list.", ctx.channel)
        else:
            return await general.send(language.string("settings_leveling_rewards_deleted_none"), ctx.channel)
            # return await general.send("No deleted roles were found. Nothing has changed", ctx.channel)

    @lvl_rewards.command(name="editrole", aliases=["er"])
    async def level_rewards_edit_role(self, ctx: commands.Context, level: int, new_role: discord.Role):
        """ Change what role is awarded at a certain level """
        language = self.bot.language(ctx)
        if level > max_level or level <= -max_level:
            return await general.send(language.string("settings_leveling_rewards_max", language.number(max_level)), ctx.channel)
            # return await general.send(f"The level cannot be above the max level ({max_level:,})", ctx.channel)
        if new_role.is_default():
            return await general.send(language.string("settings_leveling_rewards_default"), ctx.channel)
            # return await general.send("You can't award the default role", ctx.channel)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            return await general.send(language.string("settings_leveling_rewards_none"), ctx.channel)
            # return await general.send("You don't seem to have any role rewards to begin with...", ctx.channel)
            # _settings = settings.template.copy()
        if "leveling" not in _settings:
            return await general.send(language.string("settings_leveling_rewards_none"), ctx.channel)
            # return await general.send("You don't seem to have any role rewards to begin with...", ctx.channel)
            # _settings["leveling"] = settings.template["leveling"].copy()
            # _settings["leveling"]["rewards"] = []
        try:
            rr = _settings["leveling"]["rewards"]
        except KeyError:
            rr = []
        roles = [i["role"] for i in rr]
        if new_role.id in roles:
            return await general.send(language.string("settings_leveling_rewards_already_role2", ctx.prefix), ctx.channel)
            # return await general.send("This role is already rewarded", ctx.channel)
        u = False
        for i, reward in enumerate(rr):
            if level == reward["level"]:
                rr[i] = {"level": level, "role": new_role.id}
                u = True
                break
        if u:
            _settings["leveling"]["rewards"] = rr
            stuff = json.dumps(_settings)
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
            return await general.send(language.string("settings_leveling_rewards_edit", new_role.name, language.number(level)), ctx.channel)
            # return await general.send(f"The role {new_role.name} will now be rewarded at level {level:,}", ctx.channel)
        else:
            return await general.send(language.string("settings_leveling_rewards_edit_fail", language.number(level)), ctx.channel)
            # return await general.send("I don't think that worked... There might be no reward at the specified level.", ctx.channel)

    @lvl_rewards.command(name="editlevel", aliases=["el"])
    async def level_rewards_edit_level(self, ctx: commands.Context, role: discord.Role, new_level: int):
        """ Change at which level the role is awarded """
        language = self.bot.language(ctx)
        if new_level > max_level or new_level <= -max_level:
            return await general.send(language.string("settings_leveling_rewards_max", language.number(max_level)), ctx.channel)
            # return await general.send(f"The level cannot be above the max level ({max_level:,})", ctx.channel)
        if role.is_default():
            return await general.send(language.string("settings_leveling_rewards_default"), ctx.channel)
            # return await general.send("You can't award the default role", ctx.channel)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            return await general.send(language.string("settings_leveling_rewards_none"), ctx.channel)
            # return await general.send("You don't seem to have any role rewards to begin with...", ctx.channel)
            # _settings = settings.template.copy()
        if "leveling" not in _settings:
            return await general.send(language.string("settings_leveling_rewards_none"), ctx.channel)
            # return await general.send("You don't seem to have any role rewards to begin with...", ctx.channel)
            # _settings["leveling"] = settings.template["leveling"].copy()
            # _settings["leveling"]["rewards"] = []
        try:
            rr = _settings["leveling"]["rewards"]
        except KeyError:
            rr = []
        levels = [i["level"] for i in rr]
        if new_level in levels:
            return await general.send(language.string("settings_leveling_rewards_already_level2", ctx.prefix), ctx.channel)
            # return await general.send("There is already a reward for this level", ctx.channel)
        u = False
        for i, r in enumerate(rr):
            if role.id == r["role"]:
                rr[i] = {"level": new_level, "role": role.id}
                u = True
                break
        if u:
            _settings["leveling"]["rewards"] = rr
            stuff = json.dumps(_settings)
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
            return await general.send(language.string("settings_leveling_rewards_edit", role.name, language.number(new_level)), ctx.channel)
            # return await general.send(f"The role {role.name} will now be rewarded at level {new_level:,}", ctx.channel)
        else:
            return await general.send(language.string("settings_leveling_rewards_edit_fail2", role.name), ctx.channel)
            # return await general.send("I don't think that worked... Maybe the role is not awarded at all.", ctx.channel)

    @settings.command(name="muterole", aliases=["mutedrole", "muted", "mute"])
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_mute_role(self, ctx: commands.Context, role: discord.Role):
        """ Set the Muted role """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        _settings["mute_role"] = role.id
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(self.bot.language(ctx).string("settings_mute_role", role.name), ctx.channel)
        # return await general.send(f"The muted role has been set to {role.name}", ctx.channel)

    @settings.group(name="starboard", aliases=["stars", "sb"], case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_starboard(self, ctx: commands.Context):
        """ Starboard settings """
        if ctx.invoked_subcommand is None:
            language = self.bot.language(ctx)
            data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
            if not data:
                return await general.send(language.string("settings_none"), ctx.channel)
            setting = json.loads(data["data"])
            if "starboard" not in setting:
                return await general.send(language.string("settings_starboard_none"), ctx.channel)
            starboard = setting["starboard"]
            embed = discord.Embed(colour=general.random_colour())
            embed.title = language.string("settings_starboard", ctx.guild.name)
            embed.set_thumbnail(url=str(ctx.guild.icon.replace(size=1024)))
            embed.set_footer(text=language.string("settings_starboard_footer", ctx.prefix))
            embed.add_field(name=language.string("settings_starboard_enabled2"), value=language.yes(starboard["enabled"]), inline=False)
            channel = f"<#{starboard['channel']}>" if starboard["channel"] != 0 else language.string("settings_starboard_channel_none")
            embed.add_field(name=language.string("settings_starboard_channel"), value=channel, inline=False)
            embed.add_field(name=language.string("settings_starboard_requirement"), value=language.number(starboard["minimum"]), inline=False)
            return await general.send(None, ctx.channel, embed=embed)

    @set_starboard.command(name="enable")
    async def starboard_enable(self, ctx: commands.Context):
        """ Enable starboard """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "starboard" not in _settings:
            _settings["starboard"] = self.template["starboard"].copy()
        _settings["starboard"]["enabled"] = True
        # is_or_not = "enabled" if _settings["starboard"]["enabled"] else "disabled"
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(self.bot.language(ctx).string("settings_starboard_enabled"), ctx.channel)
        # return await general.send(f"Starboard is now {is_or_not} in this server.", ctx.channel)

    @set_starboard.command(name="disable")
    async def starboard_disable(self, ctx: commands.Context):
        """ Disable starboard """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "starboard" not in _settings:
            _settings["starboard"] = self.template["starboard"].copy()
        _settings["starboard"]["enabled"] = False
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(self.bot.language(ctx).string("settings_starboard_disabled"), ctx.channel)

    @set_starboard.command(name="channel")
    async def starboard_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Set the channel for starboard messages """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "starboard" not in _settings:
            _settings["starboard"] = self.template["starboard"].copy()
        _settings["starboard"]["channel"] = channel.id
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(self.bot.language(ctx).string("settings_starboard_channel_set", channel.mention), ctx.channel)
        # return await general.send(f"Starboard messages will now be sent to {channel.mention}.", ctx.channel)

    @set_starboard.command(name="minimum", aliases=["requirement", "min", "req"])
    async def starboard_requirement(self, ctx: commands.Context, requirement: int):
        """ Set the minimum amount of stars before the message is sent to the starboard """
        language = self.bot.language(ctx)
        if requirement < 1:
            return await general.send(language.string("settings_starboard_requirement_min"), ctx.channel)
            # return await general.send("The requirement has to be 1 or above.", ctx.channel)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "starboard" not in _settings:
            _settings["starboard"] = self.template["starboard"].copy()
        _settings["starboard"]["minimum"] = requirement
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(language.string("settings_starboard_requirement_set", language.number(requirement)), ctx.channel)
        # return await general.send(f"The minimum amount of stars to appear on the starboard is now {requirement}.", ctx.channel)

    @settings.group(name="birthdays", aliases=["birthday", "bd", "b"], case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_birthday(self, ctx: commands.Context):
        """ Birthday settings """
        if ctx.invoked_subcommand is None:
            language = self.bot.language(ctx)
            data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
            if not data:
                return await general.send(f"{language.string('settings_none')}\n{language.string('settings_birthdays_footer', ctx.prefix)}", ctx.channel)
            setting = json.loads(data["data"])
            if "birthdays" not in setting:
                return await general.send(f"{language.string('settings_birthdays_none')}\n{language.string('settings_birthdays_footer', ctx.prefix)}", ctx.channel)
            birthdays = setting["birthdays"]
            embed = discord.Embed(colour=general.random_colour())
            embed.title = language.string("settings_birthdays", ctx.guild.name)
            embed.set_thumbnail(url=str(ctx.guild.icon.replace(size=1024)))
            embed.set_footer(text=language.string("settings_birthdays_footer", ctx.prefix))
            embed.add_field(name=language.string("settings_birthdays_enabled2"), value=language.yes(birthdays["enabled"]), inline=False)
            if birthdays["channel"] != 0:
                embed.add_field(name=language.string("settings_birthdays_channel"), value=f"<#{birthdays['channel']}>", inline=False)
                if birthdays["message"] and len(birthdays["message"]) > 1024:
                    message = f"{birthdays['message'][:1021]}..."
                else:
                    message = birthdays["message"]
                embed.add_field(name=language.string("settings_birthdays_message"), value=message, inline=False)
            else:
                embed.add_field(name=language.string("settings_birthdays_channel"), value=language.string("settings_birthdays_channel_none"), inline=False)
            role = f"<@&{birthdays['role']}>" if birthdays["role"] != 0 else language.string("settings_birthdays_role_none")
            embed.add_field(name=language.string("settings_birthdays_role"), value=role, inline=False)
            return await general.send(None, ctx.channel, embed=embed)

    @set_birthday.command(name="enable")
    async def birthday_enable(self, ctx: commands.Context):
        """ Enable birthdays in your server """
        language = self.bot.language(ctx)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "birthdays" not in _settings:
            _settings["birthdays"] = self.template["birthdays"].copy()
        _settings["birthdays"]["enabled"] = True
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(language.string("settings_birthdays_enabled"), ctx.channel)

    @set_birthday.command(name="disable")
    async def birthday_disable(self, ctx: commands.Context):
        """ Disable birthdays in your server """
        language = self.bot.language(ctx)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "birthdays" not in _settings:
            _settings["birthdays"] = self.template["birthdays"].copy()
        _settings["birthdays"]["enabled"] = False
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(language.string("settings_birthdays_disabled", ctx.prefix), ctx.channel)

    @set_birthday.command(name="channel")
    async def birthday_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ Set the channel for birthday messages """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "birthdays" not in _settings:
            _settings["birthdays"] = self.template["birthdays"].copy()
        if channel is None:
            _settings["birthdays"]["channel"] = 0
        else:
            _settings["birthdays"]["channel"] = channel.id
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        if channel is not None:
            return await general.send(self.bot.language(ctx).string("settings_birthdays_channel_set", channel.mention), ctx.channel)
        else:
            return await general.send(self.bot.language(ctx).string("settings_birthdays_channel_none2"), ctx.channel)

    @set_birthday.command(name="role")
    async def birthday_role(self, ctx: commands.Context, role: discord.Role = None):
        """ Set the birthday role """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "birthdays" not in _settings:
            _settings["birthdays"] = self.template["birthdays"].copy()
        if role is None:
            _settings["birthdays"]["role"] = 0
        else:
            _settings["birthdays"]["role"] = role.id
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        if role is not None:
            return await general.send(self.bot.language(ctx).string("settings_birthdays_role_set", role.name), ctx.channel)
        else:
            return await general.send(self.bot.language(ctx).string("settings_birthdays_role_none2"), ctx.channel)

    @set_birthday.command(name="message")
    async def birthday_message(self, ctx: commands.Context, *, text: str = ""):
        """ Set the happy birthday message

        Variables:
        [MENTION] - Mention the user who has birthday
        [USER] - The name of the user who has birthday"""
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "birthdays" not in _settings:
            _settings["birthdays"] = self.template["birthdays"].copy()
        text = text.replace("\\n", "\n")
        _settings["birthdays"]["message"] = text
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        if text:
            filled = text.replace("[MENTION]", ctx.author.mention).replace("[USER]", ctx.author.name)
            return await general.send(self.bot.language(ctx).string("settings_birthdays_message_set", text, filled), ctx.channel)
        else:
            return await general.send(self.bot.language(ctx).string("settings_birthdays_channel_none2"), ctx.channel)

    @settings.group(name="messagelogs", aliases=["messages", "message", "msg"], case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_messages(self, ctx: commands.Context):
        """ Log deleted and edited messages to a channel """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @set_messages.command(name="disable")
    async def set_message_disable(self, ctx: commands.Context):
        """ Disable message logs """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "message_logs" not in _settings:
            _settings["message_logs"] = self.template["message_logs"].copy()
        _settings["message_logs"]["enabled"] = False
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(self.bot.language(ctx).string("settings_messages_disable"), ctx.channel)

    @set_messages.command(name="enable")
    async def set_message_enable(self, ctx: commands.Context):
        """ Enable message logs """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "message_logs" not in _settings:
            _settings["message_logs"] = self.template["message_logs"].copy()
        _settings["message_logs"]["enabled"] = True
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(self.bot.language(ctx).string("settings_messages_enable"), ctx.channel)

    @set_messages.command(name="channel", aliases=["set"])
    async def set_message_channel(self, ctx: commands.Context, log_type: str, channel: discord.TextChannel = None):
        """ Set the channel for the message logs
        log_type must be either "edit" or "delete" """
        language = self.bot.language(ctx)
        if log_type not in ["edit", "delete"]:
            return await general.send(language.string("settings_messages_type_invalid"), ctx.channel)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "message_logs" not in _settings:
            _settings["message_logs"] = self.template["message_logs"].copy()
        if channel is None:
            _settings["message_logs"][log_type] = 0
        else:
            _settings["message_logs"][log_type] = channel.id
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        output = "settings_messages_set_edit" if log_type == "edit" else "settings_messages_set_delete"
        return await general.send(language.string(output, channel.mention, ctx.prefix), ctx.channel)

    @set_messages.group(name="ignore", aliases=["ignoredchannels", "ignorechannels", "ic"], case_insensitive=True)
    async def set_message_ignore(self, ctx: commands.Context):
        """ Ignore edited and deleted messages in certain channels """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.channel)

    @set_message_ignore.command(name="add", aliases=["+"])
    async def message_ignore_add(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Ignore edited and deleted messages in this channel """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "message_logs" not in _settings:
            _settings["message_logs"] = self.template["message_logs"].copy()
        _settings["message_logs"]["ignore_channels"].append(channel.id)
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(self.bot.language(ctx).string("settings_messages_ignore_add", channel.mention), ctx.channel)

    @set_message_ignore.command(name="remove", aliases=["-"])
    async def message_ignore_remove(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Don't ignore edited and deleted messages in this channel anymore """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        try:
            _settings["message_logs"]["ignore_channels"].remove(channel.id)
        except (ValueError, KeyError):
            return await general.send(self.bot.language(ctx).string("settings_messages_ignore_invalid"), ctx.channel)
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(self.bot.language(ctx).string("settings_messages_ignore_remove", channel.mention), ctx.channel)

    @set_messages.command(name="ignorebots", aliases=["bots"])
    async def prefix_default(self, ctx: commands.Context, action: str):
        """ Ignore bots' messages """
        language = self.bot.language(ctx)
        if action not in ["enable", "disable"]:
            return await general.send(language.string("settings_prefix_default_invalid"), ctx.channel)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "message_logs" not in _settings:
            _settings["message_logs"] = self.template["message_logs"].copy()
        _settings["message_logs"]["ignore_bots"] = action == "enable"
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(language.string("settings_messages_bots_enable" if action == "enable" else "settings_messages_bots_disable"), ctx.channel)

    @settings.group(name="polls", case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["suager"])
    async def set_polls(self, ctx: commands.Context):
        """ Polls settings """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @set_polls.command(name="channel")
    async def set_poll_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ Set the channel where poll updates and results will go """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "polls" not in _settings:
            _settings["polls"] = self.template["polls"].copy()
        if channel is None:
            _settings["polls"]["channel"] = 0
        else:
            _settings["polls"]["channel"] = channel.id
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        if channel is not None:
            return await general.send(self.bot.language(ctx).string("settings_poll_channel_set", channel.mention), ctx.channel)
        else:
            return await general.send(self.bot.language(ctx).string("settings_poll_channel_none"), ctx.channel)

    @set_polls.command(name="anonymity", aliases=["anon"])
    async def set_poll_anonymity(self, ctx: commands.Context, value: str):
        """ Set whether voters will be shown at the end of the poll or not (yes = anonymous, no = log voters) """
        language = self.bot.language(ctx)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "polls" not in _settings:
            _settings["polls"] = self.template["polls"].copy()
        if value.lower() == "yes":
            _settings["polls"]["voter_anonymity"] = True
        elif value.lower() == "no":
            _settings["polls"]["voter_anonymity"] = False
        else:
            return await general.send(language.string("settings_polls_anonymity_invalid"), ctx.channel)
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        if _settings["polls"]["voter_anonymity"]:
            return await general.send(self.bot.language(ctx).string("settings_poll_anonymity_yes"), ctx.channel)
        else:
            return await general.send(self.bot.language(ctx).string("settings_poll_anonymity_no"), ctx.channel)

    @settings.group(name="joinrole", aliases=["autorole", "join", "jr"], case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_join_role(self, ctx: commands.Context):
        """ Automatically give new members a role """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @set_join_role.group(name="members", aliases=["member"])
    async def set_member_join_role(self, ctx: commands.Context):
        """ Set the role to give to new human members """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @set_member_join_role.command(name="add")
    async def add_member_join_role(self, ctx: commands.Context, role: discord.Role):
        """ Give this role to new human members """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "join_roles" not in _settings:
            _settings["join_roles"] = self.template["join_roles"].copy()
        members = _settings["join_roles"]["members"]
        if type(members) == int:  # If it is old
            if members == 0:
                _settings["join_roles"]["members"] = []
            else:
                _settings["join_roles"]["members"] = [members]
        _settings["join_roles"]["members"].append(role.id)
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        # if role is not None:
        return await general.send(self.bot.language(ctx).string("settings_join_members_add", role.name), ctx.channel)
        # else:
        #     return await general.send(self.bot.language(ctx).string("settings_join_members_none"), ctx.channel)

    @set_member_join_role.command(name="remove")
    async def remove_member_join_role(self, ctx: commands.Context, role: discord.Role):
        """ Don't give this role new human members """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "join_roles" not in _settings:
            _settings["join_roles"] = self.template["join_roles"].copy()
        members = _settings["join_roles"]["members"]
        if type(members) == int:  # If it is old
            if members == 0:
                _settings["join_roles"]["members"] = []
            else:
                _settings["join_roles"]["members"] = [members]
        try:
            _settings["join_roles"]["members"].remove(role.id)
        except (IndexError, ValueError):
            return await general.send(self.bot.language(ctx).string("settings_join_members_error", role.name), ctx.channel)
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        # if role is not None:
        return await general.send(self.bot.language(ctx).string("settings_join_members_remove", role.name), ctx.channel)
        # else:
        #     return await general.send(self.bot.language(ctx).string("settings_join_members_none"), ctx.channel)

    @set_join_role.group(name="bots", aliases=["bot"])
    async def set_bot_join_role(self, ctx: commands.Context):
        """ Set the role to give to new bots """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @set_bot_join_role.command(name="add")
    async def add_bot_join_role(self, ctx: commands.Context, role: discord.Role):
        """ Give this role to new bots """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "join_roles" not in _settings:
            _settings["join_roles"] = self.template["join_roles"].copy()
        members = _settings["join_roles"]["bots"]
        if type(members) == int:  # If it is old
            if members == 0:
                _settings["join_roles"]["bots"] = []
            else:
                _settings["join_roles"]["bots"] = [members]
        _settings["join_roles"]["bots"].append(role.id)
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        # if role is not None:
        return await general.send(self.bot.language(ctx).string("settings_join_bots_add", role.name), ctx.channel)
        # else:
        #     return await general.send(self.bot.language(ctx).string("settings_join_members_none"), ctx.channel)

    @set_bot_join_role.command(name="remove")
    async def remove_bot_join_role(self, ctx: commands.Context, role: discord.Role):
        """ Don't give this role new bots """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "join_roles" not in _settings:
            _settings["join_roles"] = self.template["join_roles"].copy()
        members = _settings["join_roles"]["bots"]
        if type(members) == int:  # If it is old
            if members == 0:
                _settings["join_roles"]["bots"] = []
            else:
                _settings["join_roles"]["bots"] = [members]
        try:
            _settings["join_roles"]["bots"].remove(role.id)
        except (IndexError, ValueError):
            return await general.send(self.bot.language(ctx).string("settings_join_bots_error", role.name), ctx.channel)
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        # if role is not None:
        return await general.send(self.bot.language(ctx).string("settings_join_bots_remove", role.name), ctx.channel)
        # else:
        #     return await general.send(self.bot.language(ctx).string("settings_join_members_none"), ctx.channel)

    @settings.group(name="welcome", case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_welcome(self, ctx: commands.Context):
        """ Welcome new members to your server """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @set_welcome.command(name="channel")
    async def set_welcome_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ Set the channel for welcome messages """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "welcome" not in _settings:
            _settings["welcome"] = self.template["welcome"].copy()
        if channel is None:
            _settings["welcome"]["channel"] = 0
        else:
            _settings["welcome"]["channel"] = channel.id
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        if channel is not None:
            return await general.send(self.bot.language(ctx).string("settings_welcome_channel_set", channel.mention), ctx.channel)
        else:
            return await general.send(self.bot.language(ctx).string("settings_welcome_channel_none"), ctx.channel)

    @set_welcome.group(name="message", invoke_without_command=True, case_insensitive=True)
    async def welcome_message(self, ctx: commands.Context, *, value: str):
        """ Set the welcome message """
        if ctx.invoked_subcommand is None:
            language = self.bot.language(ctx)
            data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
            if data:
                _settings = json.loads(data["data"])
            else:
                _settings = self.template.copy()
            if "welcome" not in _settings:
                _settings["welcome"] = self.template["welcome"].copy()
            value = value.replace("\\n", "\n")
            _settings["welcome"]["message"] = value
            message2 = value \
                .replace("[MENTION]", ctx.author.mention)\
                .replace("[USER]", ctx.author.name)\
                .replace("[SERVER]", ctx.guild.name)\
                .replace("[CREATED_AT]", language.time(ctx.author.created_at, short=1, dow=False, seconds=False, tz=False))\
                .replace("[JOINED_AT]", language.time(ctx.author.joined_at, short=1, dow=False, seconds=False, tz=False))\
                .replace("[ACCOUNT_AGE]", language.delta_dt(ctx.author.created_at, accuracy=3, brief=False, affix=False))\
                .replace("[MEMBERS]", language.number(ctx.guild.member_count))
            stuff = json.dumps(_settings)
            if data:
                self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
            else:
                self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
            return await general.send(language.string("settings_welcome_message", value, message2), ctx.channel)

    @welcome_message.command(name="variables", aliases=["vars"])
    async def welcome_message_vars(self, ctx: commands.Context):
        """ Welcome message variables """
        return await general.send(self.bot.language(ctx).string("settings_welcome_message_variables"), ctx.channel)

    @settings.group(name="goodbye", aliases=["farewell"], case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_goodbye(self, ctx: commands.Context):
        """ Say something when a user leaves your server """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @set_goodbye.command(name="channel")
    async def set_goodbye_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ Set the channel for goodbye messages """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "goodbye" not in _settings:
            _settings["goodbye"] = self.template["goodbye"].copy()
        if channel is None:
            _settings["goodbye"]["channel"] = 0
        else:
            _settings["goodbye"]["channel"] = channel.id
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        if channel is not None:
            return await general.send(self.bot.language(ctx).string("settings_goodbye_channel_set", channel.mention), ctx.channel)
        else:
            return await general.send(self.bot.language(ctx).string("settings_goodbye_channel_none"), ctx.channel)

    @set_goodbye.group(name="message", invoke_without_command=True, case_insensitive=True)
    async def goodbye_message(self, ctx: commands.Context, *, value: str):
        """ Set the goodbye message """
        if ctx.invoked_subcommand is None:
            language = self.bot.language(ctx)
            data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
            if data:
                _settings = json.loads(data["data"])
            else:
                _settings = self.template.copy()
            if "goodbye" not in _settings:
                _settings["goodbye"] = self.template["goodbye"].copy()
            value = value.replace("\\n", "\n")
            _settings["goodbye"]["message"] = value
            message2 = value \
                .replace("[MENTION]", ctx.author.mention)\
                .replace("[USER]", ctx.author.name)\
                .replace("[SERVER]", ctx.guild.name)\
                .replace("[CREATED_AT]", language.time(ctx.author.created_at, short=1, dow=False, seconds=False, tz=False))\
                .replace("[JOINED_AT]", language.time(ctx.author.joined_at, short=1, dow=False, seconds=False, tz=False))\
                .replace("[ACCOUNT_AGE]", language.delta_dt(ctx.author.created_at, accuracy=3, brief=False, affix=False))\
                .replace("[LENGTH_OF_STAY]", language.delta_dt(ctx.author.joined_at, accuracy=3, brief=False, affix=False))\
                .replace("[MEMBERS]", language.number(ctx.guild.member_count))
            stuff = json.dumps(_settings)
            if data:
                self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
            else:
                self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
            return await general.send(language.string("settings_goodbye_message", value, message2), ctx.channel)

    @goodbye_message.command(name="variables", aliases=["vars"])
    async def goodbye_message_vars(self, ctx: commands.Context):
        """ Goodbye message variables """
        return await general.send(self.bot.language(ctx).string("settings_goodbye_message_variables"), ctx.channel)

    @settings.group(name="moddm", aliases=["moddms", "dmonmod", "dms"], case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_mod_dms(self, ctx: commands.Context, punishment: str, action: str = None):
        """ Send a DM to the user when a punishment is applied against them
        Punishment values: warn, mute, kick, ban
        Action: enable, disable (leave empty to see current value)"""
        language = self.bot.language(ctx)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "mod_dms" not in _settings:
            _settings["mod_dms"] = self.template["mod_dms"].copy()
        punishment = punishment.lower()
        if punishment not in ["warn", "mute", "kick", "ban"]:
            return await general.send(language.string("settings_mod_dms_invalid", punishment), ctx.channel)
        if action is None:
            try:
                enabled = _settings["mod_dms"][punishment]
                text = "enabled2" if enabled else "disabled2"
                return await general.send(language.string(f"settings_mod_dms_{punishment}_{text}"), ctx.channel)
            except KeyError:
                # return await general.send(language.string(f"settings_mod_dms_{punishment}_disabled2"), ctx.channel)
                return await general.send(language.string("settings_mod_dms_invalid", punishment), ctx.channel)
        else:
            action = action.lower()
            if action not in ["enable", "disable"]:
                return await general.send(language.string("settings_mod_dms_invalid2", action), ctx.channel)
            enable = action == "enable"
            _settings["mod_dms"][punishment] = enable
            stuff = json.dumps(_settings)
            if data:
                self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
            else:
                self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
            text = "enabled" if enable else "disabled"
            return await general.send(language.string(f"settings_mod_dms_{punishment}_{text}"), ctx.channel)

    @settings.group(name="modlogs", aliases=["ml"], case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_mod_logs(self, ctx: commands.Context, punishment: str, channel: discord.TextChannel = None):
        """ Log all moderation actions taken with this bot
        Punishment values: warn, mute, kick, ban, roles
        ("Roles" means logging when a user gains or loses a role)

        To disable, don't specify the channel (Mod logs are disabled by default anyway)
        To enable, specify a channel where all actions of the given type will be logged.
        """
        language = self.bot.language(ctx)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = self.template.copy()
        if "mod_logs" not in _settings:
            _settings["mod_logs"] = self.template["mod_logs"].copy()
        punishment = punishment.lower()
        if punishment not in ["warn", "mute", "kick", "ban", "roles"]:
            return await general.send(language.string("settings_mod_logs_invalid", punishment), ctx.channel)
        if channel is None:
            _settings["mod_logs"][punishment] = 0
            text = language.string(f"settings_mod_logs_disable_{punishment}")
        else:
            _settings["mod_logs"][punishment] = channel.id
            text = language.string(f"settings_mod_logs_enable_{punishment}", channel=channel.mention)
        stuff = json.dumps(_settings)
        if data:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?)", (ctx.guild.id, self.bot.name, stuff))
        return await general.send(text, ctx.channel)

    @commands.command(name="prefixes", aliases=["prefix"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def prefix(self, ctx: commands.Context):
        """ Server prefixes """
        language = self.bot.language(ctx)
        dp, cp = self.prefix_list(ctx)
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("settings_prefixes_title", self.bot.user.name, ctx.guild.name)
        # embed.title = f"Prefixes for {self.bot.user.name} in {ctx.guild.name}"
        embed.set_thumbnail(url=str(ctx.guild.icon.replace(size=1024)))
        embed.add_field(name=language.string("settings_prefixes_default"), value='\n'.join(dp), inline=True)
        if cp:
            embed.add_field(name=language.string("settings_prefixes_custom"), value='\n'.join(cp), inline=True)
        return await general.send(None, ctx.channel, embed=embed)

    def prefix_list(self, ctx: commands.Context):
        _data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if not _data:
            dp = self.bot.local_config["prefixes"].copy()
            cp = []
        else:
            data = json.loads(_data['data'])
            dp = self.bot.local_config["prefixes"].copy() if data['use_default'] else []
            cp = data['prefixes']
        dp.append(self.bot.user.mention)
        return dp, cp


def setup(bot: bot_data.Bot):
    bot.add_cog(Settings(bot))
