import json
from copy import deepcopy
from io import BytesIO
from typing import Tuple

import discord
from regaus import time as time2

from cogs.leveling import max_level
from utils import bot_data, commands, general, languages, permissions, settings, time, paginators


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
        # Values never considered for translation completion
        exclude = ["_self", "_en", "_valid", "_conlang", "time_ago_p", "time_ago_s", "time_in_p", "time_in_s", "weather78_regions", "weather78_trivia_data"]
        # Get values that are valid to count for translation completion
        always_valid = ["_languages", "_language_alt", "generic", "frequency", "time", "discord", "events", "info", "settings"]
        valid_prefixes = {
            "suager": ["achievements", "birthdays", "fun", "images", "leaderboards", "leveling", "mod", "polls", "ratings", "social", "starboard", "tags", "trials", "util"],
            "cobble": ["weather78", "achievements", "birthdays", "kuastall", "leaderboards", "leveling", "placeholder", "util"],
            "kyomi":  ["birthdays", "fun", "images", "mod", "ratings", "social", "starboard", "util"]
        }
        valid = always_valid + valid_prefixes.get(self.bot.name, [])
        for language in list(languages.languages.languages.keys()):
            _language = languages.Language(language)
            if not _language.data("_valid"):
                continue
            if language == "en":
                completeness = 1
            else:
                strings = 0
                matching = 0
                for k in languages.languages.languages["en"].keys():
                    # Check if the string is always excluded
                    if k.startswith("country_") or k.startswith("data_holidays_") or k in exclude:
                        continue
                    # Check if the string prefix is applicable to this bot
                    is_valid = False
                    for p in valid:
                        if k.startswith(p):
                            is_valid = True
                            break
                    if not is_valid:
                        continue

                    d1, d2 = _en.data(k), _language.data(k)

                    strings += 1
                    if d1 == d2:
                        matching += 1
                completeness = 1 - (matching / strings)
                # print(f"{self.bot.name} > {language} > Translated {strings - matching}/{strings}")

            out = f"`{language}`: {_language.string('_self')} - {_language.string('_en')} - {completeness:.1%} translated"
            conlang = _language.data("_conlang")
            add_list = rsl if conlang == 2 else con if conlang == 1 else nat
            add_list.append(out)

        # List of trusted people last updated 23/05/2022, list of trusted servers last updated 05/05/2023
        # Users:   Regaus,             Leitoxz,            Alex Five,          Potato,             Chuck,              Mid,                Noodle
        # Users:   Shawn,              LostCandle,         Ash,                1337xp,             Aya,                Maza,               HatKid
        # Users:   Karmeck,            Steir,              PandaBoi,           Suager,             Mary,               Wight,              Back,
        # Users:   Ash/Kollu,          Drip
        trusted = [302851022790066185, 291665491221807104, 430891116318031872, 374853432168808448, 593736085327314954, 581206591051923466, 411925326780825602,
                   236884090651934721, 659879737509937152, 499038637631995906, 679819572278198272, 527729196688998415, 735902817151090691, 418151634087182359,
                   857360761135431730, 230313032956248064, 301091858354929674, 517012611573743621, 660639108674224158, 505486500314611717, 454599329232191488,
                   690895816914763866, 381870347814830081]
        is_trusted = ctx.author.id in trusted
        # Anyone in the Kargadia server is also automatically trusted
        ka = self.bot.get_guild(928745963877720144)
        if ka is not None:
            is_in_server = ka.get_member(ctx.author.id) is not None
            is_trusted |= is_in_server

        # Bad Users:   neppkun,             bowser
        no_conlangs = [350199484246130690,  94762492923748352]
        is_untrusted = ctx.author.id in no_conlangs
        # Servers:         Senko Lair,         Regaus'tar Koankadu, Kargadia,          3tk4
        trusted_servers = [568148147457490954, 738425418637639775, 928745963877720144, 430945139142426634]
        is_trusted_server = ctx.guild is not None and ctx.guild.id in trusted_servers

        output = "__List of supported languages:__\n" + "\n".join(nat)
        # If the person is in a trusted server while not being in the No Conlangs list, or if the person is in a DM while they're trusted
        if (is_trusted_server and not is_untrusted) or (ctx.guild is None and is_trusted):
            output += "\n\n__Conlangs supported:__\n" + "\n".join(con)
            if is_trusted:
                output += "\n\n__RSLs supported:__\n" + "\n".join(rsl)
        output += "\n\n*Please note that some of these translations may be incorrect or outdated. Even if someone else helped with these translations, I could not guarantee 100% accuracy.*"
        return await ctx.send(output)

    async def set_language(self, ctx: commands.Context, new_language: str, _id: int, _type: str, key: str, valid: bool = True):
        """ Function to update language settings """
        old_language = self.bot.language(ctx)
        new_language = new_language.lower()  # Make it case-insensitive just in case
        if new_language not in languages.languages.languages.keys():
            return await ctx.send(old_language.string("settings_locale_invalid", language=new_language, p=ctx.prefix))
        elif not languages.Language(new_language).data("_valid"):
            return await ctx.send(old_language.string("settings_locale_invalid", language=new_language, p=ctx.prefix))

        if not valid:  # This is the only validity check - A channel not being in the same server as where the command was run
            return await ctx.send(old_language.string("settings_anti_ads_channel_invalid2"))

        locale = self.bot.db.fetchrow("SELECT * FROM locales WHERE id=? AND bot=? AND type=?", (_id, self.bot.name, _type))
        if locale:
            self.bot.db.execute("UPDATE locales SET locale=? WHERE id=? AND bot=? AND type=?", (new_language, _id, self.bot.name, _type))
        else:
            self.bot.db.execute("INSERT INTO locales VALUES (?, ?, ?, ?)", (_id, new_language, self.bot.name, _type))
        return await ctx.send(ctx.language2(new_language).string("settings_locale_set" + key, channel=f"<#{_id}>"))

    @commands.command(name="setpersonallanguage", aliases=["spl"], hidden=True)
    async def set_personal_language(self, ctx: commands.Context, new_language: str):
        """ Set your own personal language """
        return await self.set_language(ctx, new_language, ctx.author.id, "user", "_personal")

    async def settings_current_embed(self, ctx: commands.Context):
        """ Embed of current settings """
        language = self.bot.language(ctx)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if not data:
            setting = self.template.copy()
        else:
            setting = json.loads(data["data"])
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("settings_current", server=ctx.guild.name)
        if ctx.guild.icon:
            embed.set_thumbnail(url=str(ctx.guild.icon.replace(size=1024, static_format="png")))
        embed.set_footer(text=language.string("settings_current_footer", p=ctx.prefix))
        interface = paginators.EmbedFieldPaginatorInterface(paginator=paginators.EmbedFieldPaginator(max_fields=7, max_size=3000),
                                                            bot=ctx.bot, owner=ctx.author, embed=embed)

        # Language
        await interface.add_field(name=language.string("settings_current_language"), value=language.string("_self"), inline=False)

        # Prefix
        dp, cp = self.prefix_list(ctx)
        await interface.add_field(name=language.string("settings_current_prefix"), value=f"`{'`, `'.join(dp + cp)}`", inline=False)

        def channel(cid: int):
            if cid == 0:
                return language.string("settings_current_disabled")
            return f"<#{cid}>"

        # Levels
        if self.bot.name in ["suager"]:
            lvl = language.string("settings_current_disabled")
            if "leveling" in setting:
                if setting["leveling"]["enabled"]:
                    lvl = language.string("settings_current_leveling2", p=ctx.prefix)
            await interface.add_field(name=language.string("settings_current_leveling"), value=lvl, inline=False)

        # Starboard
        if self.bot.name in ["kyomi", "suager"]:
            sb = language.string("settings_current_disabled")
            if "starboard" in setting:
                starboard = setting["starboard"]
                if starboard["enabled"]:
                    sb = language.string("settings_current_starboard2", stars=language.number(starboard["minimum"]), channel=starboard["channel"])
            await interface.add_field(name=language.string("settings_current_starboard"), value=sb, inline=False)

        # Birthdays
        bd = language.string("settings_current_disabled")
        if "birthdays" in setting:
            if setting["birthdays"]["enabled"]:
                bd = language.string("settings_current_birthdays2", p=ctx.prefix)
        await interface.add_field(name=language.string("settings_current_birthdays"), value=bd, inline=False)

        if self.bot.name in ["kyomi", "suager"]:
            # Polls
            if self.bot.name in ["suager"] and ctx.guild.id in [869975256566210641, 738425418637639775]:
                polls_channel, polls_anonymity = language.string("settings_current_polls_channel_none"), language.yes(True)  # Default settings
                if "polls" in setting:
                    polls = setting["polls"]
                    if polls["channel"]:
                        polls_channel = f"<#{polls['channel']}>"
                    polls_anonymity = language.yes(polls["voter_anonymity"])
                await interface.add_field(name=language.string("settings_current_polls"), inline=False,
                                          value=language.string("settings_current_polls2", channel=polls_channel, anon=polls_anonymity))

            # Join roles
            members, bots = language.string("generic_none"), language.string("generic_none")
            if "join_roles" in setting:
                join_roles = setting["join_roles"]
                if join_roles["members"]:
                    members = language.join([f"<@&{role}>" for role in join_roles["members"]])
                else:
                    members = language.string("generic_none")
                if join_roles["bots"]:
                    bots = language.join([f"<@&{role}>" for role in join_roles["bots"]])
                else:
                    bots = language.string("generic_none")
            await interface.add_field(name=language.string("settings_current_join_roles"), value=language.string("settings_current_join_roles2", humans=members, bots=bots), inline=False)

            # Welcomes
            welcome_channel, welcome_message = language.string("settings_current_disabled"), None
            if "welcome" in setting:
                welcome = setting["welcome"]
                if welcome["channel"]:
                    welcome_channel = language.string("settings_current_welcome_channel", channel=welcome["channel"])
                    welcome_message = f"{welcome['message'][:1023]}…" if len(welcome["message"]) > 1024 else welcome["message"]
            await interface.add_field(name=language.string("settings_current_welcome"), value=welcome_channel, inline=False)
            if welcome_message:
                await interface.add_field(name=language.string("settings_current_welcome_message"), value=welcome_message, inline=False)

            # Goodbyes
            goodbye_channel, goodbye_message = language.string("settings_current_disabled"), None
            if "goodbye" in setting:
                goodbye = setting["goodbye"]
                if goodbye["channel"]:
                    goodbye_channel = language.string("settings_current_goodbye_channel", channel=goodbye["channel"])
                    goodbye_message = f"{goodbye['message'][:1023]}…" if len(goodbye["message"]) > 1024 else goodbye["message"]
            await interface.add_field(name=language.string("settings_current_goodbye"), value=goodbye_channel, inline=False)
            if goodbye_message:
                await interface.add_field(name=language.string("settings_current_goodbye_message"), value=goodbye_message, inline=False)

            # Mute role
            mute_role = language.string("generic_none")
            if "mute_role" in setting:
                if setting["mute_role"] != 0:
                    mute_role = f"<@&{setting['mute_role']}>"
            await interface.add_field(name=language.string("settings_current_mute"), value=mute_role, inline=False)

            # Warnings
            warnings = language.string("settings_current_warnings_disabled", p=ctx.prefix)
            if "warnings" in setting:
                warning = setting["warnings"]
                mute_requirement = warning["required_to_mute"]  # Warnings required to mute
                mute_length = warning["mute_length"]  # Starting mute length
                scaling = warning["scaling"]  # The multiplier for mute length
                warnings = language.string("settings_current_warnings2", mute_req=mute_requirement, mute_len=mute_length, scaling=language.number(scaling))
            await interface.add_field(name=language.string("settings_current_warnings"), value=warnings, inline=False)

            # Message Logs
            msg = language.string("settings_current_messages_disabled", p=ctx.prefix)
            if "message_logs" in setting:
                message_logs = setting["message_logs"]
                enabled = message_logs["enabled"]
                edit, delete = message_logs["edit"], message_logs["delete"]
                ignore_bots = message_logs["ignore_bots"]
                if not message_logs["ignore_channels"]:
                    ignored_channels = language.string("generic_none")
                else:
                    length = len(message_logs["ignore_channels"])
                    if length <= 12:
                        ignored_channels = ", ".join(f"<#{channel}>" for channel in message_logs["ignore_channels"])
                    else:
                        ignored_channels = ", ".join(f"<#{channel}>" for channel in message_logs["ignore_channels"][:12])
                        ignored_channels += language.string("settings_leveling_ignored_many", val=language.number(length - 12))
                msg = language.string("settings_current_messages2", enabled=language.yes(enabled), edit=channel(edit), delete=channel(delete),
                                      ignore_bots=language.yes(ignore_bots), ignored_channels=ignored_channels)
            await interface.add_field(name=language.string("settings_current_messages"), value=msg, inline=False)

            # Mod DMs
            mod_dms_text = language.string("settings_current_mod_dms_disabled", p=ctx.prefix)
            if "mod_dms" in setting:
                mod_dms = setting["mod_dms"]
                warn, mute, kick, ban = mod_dms["warn"], mod_dms["mute"], mod_dms["kick"], mod_dms["ban"]
                mod_dms_text = language.string("settings_current_mod_dms2", warn=language.yes(warn), mute=language.yes(mute), kick=language.yes(kick), ban=language.yes(ban))
            await interface.add_field(name=language.string("settings_current_mod_dms"), value=mod_dms_text, inline=False)

            # Mod Logs
            mod_logs_text = language.string("settings_current_mod_logs_disabled", p=ctx.prefix)
            if "mod_logs" in setting:
                mod_logs = setting["mod_logs"]
                warn, mute, kick, ban, roles = mod_logs["warn"], mod_logs["mute"], mod_logs["kick"], mod_logs["ban"], mod_logs["roles"]
                mod_logs_text = language.string("settings_current_mod_logs2", warn=channel(warn), mute=channel(mute), kick=channel(kick), ban=channel(ban), roles=channel(roles))
            await interface.add_field(name=language.string("settings_current_mod_logs"), value=mod_logs_text, inline=False)

            # User Logs
            user_logs_text = language.string("settings_current_user_logs_disabled", p=ctx.prefix)
            if "user_logs" in setting:
                user_logs = setting["user_logs"]
                join, leave = user_logs["join"], user_logs["leave"]
                user_logs_text = language.string("settings_current_user_logs2", join=channel(join), leave=channel(leave))
            await interface.add_field(name=language.string("settings_current_user_logs"), value=user_logs_text, inline=False)

            # Role Preservation
            role_preservation_text = language.string("settings_current_roles_disabled", p=ctx.prefix)
            if "user_logs" in setting:
                if setting["user_logs"]["preserve_roles"]:
                    role_preservation_text = language.string("settings_current_roles_enabled", p=ctx.prefix)
            await interface.add_field(name=language.string("settings_current_roles"), value=role_preservation_text, inline=False)

            # Image-only channels settings
            image_only_text = language.string("settings_current_image_only_disabled", p=ctx.prefix)
            if "image_only" in setting:
                image_only = setting["image_only"]
                image_only_text = ", ".join([channel(c) for c in image_only["channels"]]) or language.string("generic_none")
            await interface.add_field(name=language.string("settings_current_image_only"), value=image_only_text, inline=False)

            # Anti-ads
            anti_ads_text = language.string("settings_current_anti_ads_disabled", p=ctx.prefix)
            if "anti_ads" in setting:
                anti_ads = setting["anti_ads"]
                idx = 3 if anti_ads["whitelist"] else 2
                if anti_ads["warning"] is not None:
                    # warning_length = anti_ads["warning"]
                    warning_length = language.delta_rd(time.interpret_time(anti_ads["warning"]), accuracy=7, brief=False, affix=False)
                else:
                    warning_length = language.string("settings_current_anti_ads_permanent")
                anti_ads_text = language.string(f"settings_current_anti_ads{idx}", enabled=language.yes(anti_ads["enabled"]),
                                                channels=", ".join([channel(c) for c in anti_ads["channels"]]) or language.string("generic_none"),
                                                warning=warning_length)
            await interface.add_field(name=language.string("settings_current_anti_ads"), value=anti_ads_text, inline=False)

        if self.bot.name == "kyomi":
            vc_server_stats_text = language.string("settings_current_server_stats_disabled", p=ctx.prefix)
            if "vc_server_stats" in setting:
                vc_server_stats: dict[str, dict[str, int | str]] = setting["vc_server_stats"]
                outputs: dict[str, str] = {}  # outputs[category] = channel
                for category, cat_data in vc_server_stats.items():
                    channel = cat_data["channel"]
                    if channel == 0:
                        cat_text = language.string("settings_current_disabled")
                    else:
                        cat_text = f"<#{channel}>"
                    outputs[category] = cat_text
                    # Text is not shown in the summary
                vc_server_stats_text = language.string("settings_current_server_stats2", **outputs)
            await interface.add_field(name=language.string("settings_current_server_stats"), value=vc_server_stats_text, inline=False)

        interface.display_page = 0  # Start from first page
        return await interface.send_to(ctx)
        # return await ctx.send(embed=embed)

    # @commands.hybrid_group(name="settings", aliases=["set"], case_insensitive=True, fallback="current")
    # @app_commands.guilds(738425418637639775)
    @commands.group(name="settings", aliases=["set"], case_insensitive=True, invoke_without_command=True)
    @commands.guild_only()
    @permissions.has_permissions(manage_guild=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def settings(self, ctx: commands.Context, _: str = None):
        """ Server settings """
        if ctx.invoked_subcommand is None:
            if _ is not None:
                return await ctx.send_help(ctx.command)
            return await self.settings_current_embed(ctx)

    @settings.command(name="current")
    async def settings_current(self, ctx: commands.Context):
        """ See the current settings in a server """
        return await self.settings_current_embed(ctx)

    @settings.command(name="json")
    @commands.is_owner()
    # @permissions.has_permissions(administrator=True)
    async def settings_current_json(self, ctx: commands.Context):
        """ Current settings (in JSON) """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if not data:
            return await ctx.send(f"Settings for {ctx.guild.name} not found.")
        stuff = json.dumps(json.loads(data["data"]), indent=2)
        bio = BytesIO(stuff.encode("utf-8"))
        return await ctx.send(f"Current settings for {ctx.guild.name}", file=discord.File(bio, time.file_ts("settings", "json")))

    @settings.command(name="template")
    @commands.is_owner()
    async def settings_template_json(self, ctx: commands.Context):
        """ Settings template (in JSON) """
        stuff = json.dumps(self.template.copy(), indent=2)
        bio = BytesIO(stuff.encode("utf-8"))
        return await ctx.send("Settings template", file=discord.File(bio, "template.json"))

    @settings.command(name="upload")
    @commands.is_owner()
    # @permissions.has_permissions(administrator=True)
    async def settings_upload_json(self, ctx: commands.Context):
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
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?, ?)", (ctx.guild.id, self.bot.name, stuff, None))
        return await ctx.send(f"Settings for {ctx.guild.name} have been updated.")

    @settings.group(name="language", aliases=["lang"])
    async def set_language_command(self, ctx: commands.Context):
        """ Change the bot's language in this server or in a specific channel """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @set_language_command.command(name="server", aliases=["guild"])
    async def set_server_language(self, ctx: commands.Context, new_language: str):
        """ Set the bot's language for this server """
        return await self.set_language(ctx, new_language, ctx.guild.id, "guild", "_guild")

    @set_language_command.command(name="channel")
    async def set_channel_language(self, ctx: commands.Context, channel: discord.TextChannel | discord.Thread, new_language: str):
        """ Set the bot's language for a certain channel """
        return await self.set_language(ctx, new_language, channel.id, "channel", "_channel", valid=channel.guild.id == ctx.guild.id)

    async def settings_start(self, ctx: commands.Context, key: str) -> Tuple[dict, bool]:
        """ Template start of a settings command (loading data) """
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if data:
            _settings = json.loads(data["data"])
        else:
            _settings = deepcopy(self.template)

        if key not in _settings:
            _settings[key] = deepcopy(self.template[key])

        return _settings, bool(data)

    async def settings_end(self, ctx: commands.Context, _settings: dict, existent: bool, output_key: str, **kwargs):
        """ Template end of a settings command (saving data) """
        stuff = json.dumps(_settings)
        if existent:
            self.bot.db.execute("UPDATE settings SET data=? WHERE gid=? AND bot=?", (stuff, ctx.guild.id, self.bot.name))
        else:
            self.bot.db.execute("INSERT INTO settings VALUES (?, ?, ?, ?)", (ctx.guild.id, self.bot.name, stuff, None))
        # The "allowed mentions" is here just for settings like the level up message, to avoid sending unnecessary pings
        return await ctx.send(ctx.language().string(output_key, **kwargs), allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    @settings.group(name="prefixes", aliases=["prefix", "p"], case_insensitive=True)
    async def set_prefixes(self, ctx: commands.Context):
        """ Change server prefixes

        See //prefixes to see the list of active prefixes for the server"""
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @set_prefixes.command(name="add")
    async def prefix_add(self, ctx: commands.Context, prefix: str):
        """ Add a new custom prefix """
        _settings, existent = await self.settings_start(ctx, "prefixes")
        _settings["prefixes"].append(prefix)
        return await self.settings_end(ctx, _settings, existent, "settings_prefix_add", prefix=prefix)

    @set_prefixes.command(name="remove")
    async def prefix_remove(self, ctx: commands.Context, prefix: str):
        """ Remove a custom prefix """
        _settings, existent = await self.settings_start(ctx, "prefixes")
        try:
            _settings["prefixes"].remove(prefix)
        except ValueError:
            return await ctx.send(ctx.language().string("settings_prefix_remove_none", prefix=prefix))
        return await self.settings_end(ctx, _settings, existent, "settings_prefix_remove", prefix=prefix)

    @set_prefixes.command(name="removeall", aliases=["deleteall", "rall", "dall"])
    async def prefix_removeall(self, ctx: commands.Context):
        """ Remove all custom prefixes (Warning: this cannot be undone) """
        _settings, existent = await self.settings_start(ctx, "prefixes")
        _settings["prefixes"] = []
        return await self.settings_end(ctx, _settings, existent, "settings_prefix_removeall")

    @set_prefixes.group(name="default")
    async def prefix_default(self, ctx: commands.Context):
        """ Enable or disable the use of default prefixes

        Use `//settings prefixes default enable` to enable
        Use `//settings prefixes default disable` to disable """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    async def prefix_default_toggle(self, ctx: commands.Context, toggle: bool):
        """ Toggle the use of default prefixes """
        _settings, existent = await self.settings_start(ctx, "use_default")
        _settings["use_default"] = toggle
        output = "settings_prefix_default_enable" if toggle else "settings_prefix_default_disable"
        return await self.settings_end(ctx, _settings, existent, output)

    @prefix_default.command(name="enable")
    async def prefix_default_enable(self, ctx: commands.Context):
        """ Enable the use of default prefixes """
        return await self.prefix_default_toggle(ctx, True)

    @prefix_default.command(name="disable")
    async def prefix_default_disable(self, ctx: commands.Context):
        """ Disable the use of default prefixes """
        return await self.prefix_default_toggle(ctx, False)

    async def settings_current_leveling(self, ctx: commands.Context):
        """ Current leveling settings"""
        language = self.bot.language(ctx)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if not data:
            return await ctx.send(language.string("settings_none"))
        setting = json.loads(data["data"])
        if "leveling" not in setting:
            return await ctx.send(language.string("settings_leveling_none"))
        leveling = setting["leveling"]
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("settings_leveling", ctx.guild.name)
        if ctx.guild.icon:
            embed.set_thumbnail(url=str(ctx.guild.icon.replace(size=1024, static_format="png")))
        embed.set_footer(text=language.string("settings_leveling_footer", p=ctx.prefix))
        embed.add_field(name=language.string("settings_leveling_enabled2"), value=language.yes(leveling["enabled"]), inline=False)
        embed.add_field(name=language.string("settings_leveling_data_retention"), value=language.yes(leveling.get("retain_data", False)), inline=False)
        embed.add_field(name=language.string("settings_leveling_multiplier"), value="x" + language.number(leveling["xp_multiplier"], precision=2), inline=False)
        ac = leveling["announce_channel"]
        if ac == -1:
            embed.add_field(name=language.string("settings_leveling_announcements"), value=language.string("settings_current_disabled"), inline=False)
        else:
            if ac == 0:
                embed.add_field(name=language.string("settings_leveling_announcements"), value=language.string("settings_leveling_announcements_zero"), inline=False)
            else:
                embed.add_field(name=language.string("settings_leveling_announcements"), value=f"<#{ac}>", inline=False)
            message = f"{leveling['level_up_message'][:1023]}…" if len(leveling["level_up_message"]) > 1024 else leveling["level_up_message"]
            embed.add_field(name=language.string("settings_leveling_message"), value=message, inline=False)
            if "level_up_role" in leveling:
                if leveling["level_up_role"]:
                    message = f"{leveling['level_up_role'][:1023]}…" if len(leveling["level_up_role"]) > 1024 else leveling["level_up_role"]
                    embed.add_field(name=language.string("settings_leveling_message_role"), value=message, inline=False)
            if "level_up_highest" in leveling:
                if leveling["level_up_highest"]:
                    message = f"{leveling['level_up_highest'][:1023]}…" if len(leveling["level_up_highest"]) > 1024 else leveling["level_up_highest"]
                    embed.add_field(name=language.string("settings_leveling_message_highest"), value=message, inline=False)
            if "level_up_max" in leveling:
                if leveling["level_up_max"]:
                    message = f"{leveling['level_up_max'][:1023]}…" if len(leveling["level_up_max"]) > 1024 else leveling["level_up_max"]
                    embed.add_field(name=language.string("settings_leveling_message_max"), value=message, inline=False)
        if not leveling["ignored_channels"]:
            ignored = language.string("generic_none")
        else:
            length = len(leveling["ignored_channels"])
            if length <= 48:
                ignored = "\n".join(f"<#{channel}>" for channel in leveling["ignored_channels"])
            else:
                ignored = "\n".join(f"<#{channel}>" for channel in leveling["ignored_channels"][:45])
                ignored += language.string("settings_leveling_ignored_many", val=language.number(length - 45))
        embed.add_field(name=language.string("settings_leveling_ignored"), value=ignored, inline=False)
        embed.add_field(name=language.string("settings_leveling_rewards"), value=language.string("settings_leveling_rewards2", p=ctx.prefix), inline=False)
        return await ctx.send(embed=embed)

    @settings.group(name="leveling", aliases=["levels", "lvl"], case_insensitive=True, invoke_without_command=True)
    @commands.check(lambda ctx: ctx.bot.name in ["suager"])
    async def set_lvl(self, ctx: commands.Context, _: str = None):
        """ Leveling settings """
        if ctx.invoked_subcommand is None:
            if _ is not None:
                return await ctx.send_help(ctx.command)
            return await self.settings_current_leveling(ctx)

    async def leveling_toggle(self, ctx: commands.Context, toggle: bool):
        """ Toggle the leveling system """
        _settings, existent = await self.settings_start(ctx, "leveling")
        _settings["leveling"]["enabled"] = toggle
        output = "settings_leveling_enabled" if toggle else "settings_leveling_disabled"
        return await self.settings_end(ctx, _settings, existent, output)

    @set_lvl.command(name="enable")
    async def lvl_enable(self, ctx: commands.Context):
        """ Enable leveling """
        return await self.leveling_toggle(ctx, True)

    @set_lvl.command(name="disable")
    async def lvl_disable(self, ctx: commands.Context):
        """ Disable leveling """
        return await self.leveling_toggle(ctx, False)

    @set_lvl.command(name="multiplier", aliases=["mult"])
    async def lvl_multiplier(self, ctx: commands.Context, value: float):
        """ Set the XP gain multiplier """
        _settings, existent = await self.settings_start(ctx, "leveling")
        if value > 10:
            return await ctx.send(ctx.language().string("settings_leveling_multiplier_max"))
        if value < 0.04:  # Used to be 0.001, but bumped up to 0.04 so that you could get at least 1 XP at the 27 rate.
            return await ctx.send(ctx.language().string("settings_leveling_multiplier_min"))
        _settings["leveling"]["xp_multiplier"] = value
        return await self.settings_end(ctx, _settings, existent, "settings_leveling_multiplier_set", value=ctx.language().number(value, precision=2))

    @staticmethod
    def format_leveling_message(ctx: commands.Context, value: str, language: "languages.Language", **kwargs):
        """ Format the leveling message (since this happens in multiple places) """
        return value \
            .replace("[MENTION]", ctx.author.mention) \
            .replace("[USER]", general.username(ctx.author)) \
            .replace("[LEVEL]", language.number(kwargs["level"])) \
            .replace("[CURRENT_REWARD]", language.string("settings_leveling_reward_placeholder")) \
            .replace("[CURRENT_REWARD_LEVEL]", language.number(kwargs["current_reward_level"])) \
            .replace("[NEXT_REWARD]", language.string(kwargs["next_reward"])) \
            .replace("[NEXT_REWARD_LEVEL]", language.number(kwargs["next_reward_level"])) \
            .replace("[NEXT_REWARD_PROGRESS]", language.number(kwargs["next_reward_progress"])) \
            .replace("[MAX_LEVEL]", language.number(max_level))

    async def level_up_message_general(self, ctx: commands.Context, value: str, **kwargs):
        """ For all level up message functions """
        _settings, existent = await self.settings_start(ctx, "leveling")
        language = self.bot.language(ctx)
        key = kwargs["key"]
        # If a new message was not specified
        if not value:
            value = _settings["leveling"].get(key, None)
            # If the message content is None or otherwise absent
            if not value:
                return await ctx.send(language.string(kwargs["output_none"]))
            # If the message does exist
            example = language.string("settings_leveling_message_example", formatted=self.format_leveling_message(ctx, value, language, **kwargs))
            return await ctx.send(language.string(kwargs["output_current"], message=value+example), allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))
        # If the message is "reset", reset back to the default value
        if value.lower() == "reset":
            _settings["leveling"][key] = self.template["leveling"][key].copy()
            return await self.settings_end(ctx, _settings, existent, kwargs["output_reset"])
        # If a new message was specified
        value = value.replace("\\n", "\n")
        _settings["leveling"][key] = value
        example = language.string("settings_leveling_message_example", formatted=self.format_leveling_message(ctx, value, language, **kwargs))
        return await self.settings_end(ctx, _settings, existent, kwargs["output"], message=value+example)

    @set_lvl.group(name="message", aliases=["msg"], invoke_without_command=True, case_insensitive=True)
    async def lvl_message(self, ctx: commands.Context, *, value: str = None):
        """ Set level up message

        See `//settings leveling message variables` for the list of available variables
        Enter "reset" to reset back to the default value """
        if ctx.invoked_subcommand is None:
            return await self.level_up_message_general(ctx, value, **{
                "key": "level_up_message",
                "level": 17,
                "current_reward_level": 15,
                "next_reward": "settings_leveling_reward_placeholder2",
                "next_reward_level": 20,
                "next_reward_progress": 3,
                "output": "settings_leveling_message_set",
                "output_current": "settings_leveling_message_current",
                "output_none": "settings_leveling_message_none",
                "output_reset": "settings_leveling_message_reset"
            })

    @lvl_message.command(name="newrole", aliases=["newreward", "nr"])
    async def level_up_message_new_role(self, ctx: commands.Context, *, value: str = None):
        """ Add a custom level up message when the user has achieved a new level reward

        Use `//settings leveling message newrole reset` to remove the custom message for this scenario """
        return await self.level_up_message_general(ctx, value, **{
            "key": "level_up_role",
            "level": 10,
            "current_reward_level": 10,
            "next_reward": "settings_leveling_reward_placeholder2",
            "next_reward_level": 15,
            "next_reward_progress": 5,
            "output": "settings_leveling_message_set2",
            "output_current": "settings_leveling_message_current2",
            "output_none": "settings_leveling_message_none2",
            "output_reset": "settings_leveling_message_reset2"
        })

    @lvl_message.command(name="highestrole", aliases=["hr"])
    async def level_up_message_highest_role(self, ctx: commands.Context, *, value: str = None):
        """ Add a custom level up message when the user has achieved the highest available level reward

        Use `//settings leveling message highestrole reset` to remove the custom message for this scenario """
        return await self.level_up_message_general(ctx, value, **{
            "key": "level_up_highest",
            "level": 175,
            "current_reward_level": 150,
            "next_reward": "leveling_rewards_max",
            "next_reward_level": max_level,
            "next_reward_progress": max_level - 175,
            "output": "settings_leveling_message_set3",
            "output_current": "settings_leveling_message_current3",
            "output_none": "settings_leveling_message_none3",
            "output_reset": "settings_leveling_message_reset3"
        })

    @lvl_message.command(name="highestlevel", aliases=["hl", "max", str(max_level)])
    async def level_up_message_highest_level(self, ctx: commands.Context, *, value: str = None):
        """ Add a custom level up message when the user has reached the max level

        Use `//settings leveling message highestlevel reset` to remove the custom message for this scenario """
        return await self.level_up_message_general(ctx, value, **{
            "key": "level_up_max",
            "level": 200,
            "current_reward_level": 150,
            "next_reward": "leveling_rewards_max",
            "next_reward_level": max_level,
            "next_reward_progress": 0,
            "output": "settings_leveling_message_set4",
            "output_current": "settings_leveling_message_current4",
            "output_none": "settings_leveling_message_none4",
            "output_reset": "settings_leveling_message_reset4"
        })

    @lvl_message.command(name="variables", aliases=["vars"])
    async def level_up_message_variables(self, ctx: commands.Context):
        """ Level up message variables """
        return await ctx.send(self.bot.language(ctx).string("settings_leveling_message_variables"))

    @set_lvl.group(name="ignore", aliases=["ignored", "blacklist", "ic"], case_insensitive=True)
    async def lvl_ignored(self, ctx: commands.Context):
        """ Disable XP gain in channels """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @lvl_ignored.command(name="add", aliases=["a", "+"])
    async def lvl_ic_add(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Disable XP gain in a channel """
        _settings, existent = await self.settings_start(ctx, "leveling")
        if channel.id in _settings["leveling"]["ignored_channels"]:
            return await ctx.send(ctx.language().string("settings_leveling_ignored_already", channel=channel.mention))
        _settings["leveling"]["ignored_channels"].append(channel.id)
        return await self.settings_end(ctx, _settings, existent, "settings_leveling_ignored_add", channel=channel.mention)

    @lvl_ignored.command(name="remove", aliases=["delete", "r", "d", "-"])
    async def lvl_ic_remove(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Enable XP gain in a channel """
        _settings, existent = await self.settings_start(ctx, "leveling")
        try:
            _settings["leveling"]["ignored_channels"].remove(channel.id)
        except ValueError:
            return await ctx.send(ctx.language().string("settings_leveling_ignored_already2", channel=channel.mention))
        return await self.settings_end(ctx, _settings, existent, "settings_leveling_ignored_remove", channel=channel.mention)

    @lvl_ignored.command(name="removeall", aliases=["deleteall", "rall", "dall"])
    async def lvl_ic_removeall(self, ctx: commands.Context):
        """ Enable XP gain in all channels again (Warning: this cannot be undone) """
        _settings, existent = await self.settings_start(ctx, "leveling")
        _settings["leveling"]["ignored_channels"] = []
        return await self.settings_end(ctx, _settings, existent, "settings_leveling_ignored_removeall")

    @set_lvl.group(name="announcements", aliases=["announcement", "ac"], invoke_without_command=True, case_insensitive=True)
    async def lvl_announcements(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ Set level up announcement channel

        Enter a channel to set the channel as the level up channel
        Enter "default" to make level ups announced where the level up occurs
        Enter "disable" to disable level up announcements altogether"""
        if ctx.invoked_subcommand is None:
            _settings, existent = await self.settings_start(ctx, "leveling")
            if channel is None:
                _channel = _settings["leveling"]["announce_channel"]
                if _channel == -1:
                    return await ctx.send(ctx.language().string("settings_leveling_announcements_disabled2"))
                elif _channel == 0:
                    return await ctx.send(ctx.language().string("settings_leveling_announcements_zero2"))
                return await ctx.send(ctx.language().string("settings_leveling_announcements_set2", channel=f"<#{_channel}>"))
            else:
                _settings["leveling"]["announce_channel"] = channel.id
                return await self.settings_end(ctx, _settings, existent, "settings_leveling_announcements_set", channel=channel.mention)

    @lvl_announcements.command(name="default", aliases=["reset"])
    async def lvl_announcements_default(self, ctx: commands.Context):
        """ Make level up announcements show up in the channel where they occur """
        _settings, existent = await self.settings_start(ctx, "leveling")
        _settings["leveling"]["announce_channel"] = 0
        return await self.settings_end(ctx, _settings, existent, "settings_leveling_announcements_none")

    @lvl_announcements.command(name="disable")
    async def lvl_announcements_disable(self, ctx: commands.Context):
        """ Disable level up announcements """
        _settings, existent = await self.settings_start(ctx, "leveling")
        _settings["leveling"]["announce_channel"] = -1
        return await self.settings_end(ctx, _settings, existent, "settings_leveling_announcements_disabled")

    @set_lvl.group(name="rewards", aliases=["rr", "lr"], case_insensitive=True)
    async def lvl_rewards(self, ctx: commands.Context):
        """ Set level rewards for the server """
        if ctx.invoked_subcommand is None:
            # return await level_rewards(self, ctx)
            return await ctx.send_help(str(ctx.command))

    @lvl_rewards.command(name="add", aliases=["new", "a", "+"])
    async def level_rewards_add(self, ctx: commands.Context, role: discord.Role, level: int):
        """ Add a level reward """
        _settings, existent = await self.settings_start(ctx, "leveling")
        language = ctx.language()
        if level > max_level or level <= -max_level:
            return await ctx.send(language.string("settings_leveling_rewards_max", max_level=language.number(max_level)))
        if role.is_default():
            return await ctx.send(language.string("settings_leveling_rewards_default"))
        try:
            rr = _settings["leveling"]["rewards"]
        except KeyError:
            rr = []
        for reward in rr:
            if role.id == reward["role"]:
                return await ctx.send(language.string("settings_leveling_rewards_already_role", level=language.number(reward["level"]), p=ctx.prefix))
            if level == reward["level"]:
                role = ctx.guild.get_role(reward["role"])
                return await ctx.send(language.string("settings_leveling_rewards_already_level", role=role, p=ctx.prefix))
        rr.append({"level": level, "role": role.id})
        _settings["leveling"]["rewards"] = rr
        return await self.settings_end(ctx, _settings, existent, "settings_leveling_rewards_add", role=role.name, level=language.number(level))

    @lvl_rewards.command(name="remove", aliases=["delete", "del", "r", "d", "-"])
    async def level_rewards_remove(self, ctx: commands.Context, role: discord.Role):
        """ Remove a role reward """
        _settings, existent = await self.settings_start(ctx, "leveling")
        language = ctx.language()
        try:
            rr = _settings["leveling"]["rewards"]
        except KeyError:
            return await ctx.send(language.string("settings_leveling_rewards_none"))
        r = False
        for _role in rr:
            if _role["role"] == role.id:
                rr.remove(_role)
                r = True
                break
        if r:
            _settings["leveling"]["rewards"] = rr
            return await self.settings_end(ctx, _settings, existent, "settings_leveling_rewards_remove", role=role.name)
        else:
            return await ctx.send(language.string("settings_leveling_rewards_not_found", role=role.name))

    @lvl_rewards.command(name="removeall", aliases=["deleteall", "rall", "dall"])
    async def level_rewards_removeall(self, ctx: commands.Context):
        """ Remove all role rewards (Warning: this cannot be undone) """
        _settings, existent = await self.settings_start(ctx, "leveling")
        _settings["leveling"]["rewards"] = []
        return await self.settings_end(ctx, _settings, existent, "settings_leveling_rewards_removeall")

    @lvl_rewards.command(name="cleanup", aliases=["c"])
    async def level_rewards_deleted(self, ctx: commands.Context):
        """ Remove roles that no longer exist from the role rewards """
        _settings, existent = await self.settings_start(ctx, "leveling")
        language = ctx.language()
        try:
            rr = _settings["leveling"]["rewards"]
        except KeyError:
            return await ctx.send(language.string("settings_leveling_rewards_none"))
        removed = 0
        roles = [role.id for role in await ctx.guild.fetch_roles()]  # Get IDs of all roles in a server
        for _role in rr:
            if _role["role"] not in roles:
                rr.remove(_role)
                removed += 1
        if removed > 0:
            _settings["leveling"]["rewards"] = rr
            return await self.settings_end(ctx, _settings, existent, "settings_leveling_rewards_deleted", value=language.number(removed))
        else:
            return await ctx.send(language.string("settings_leveling_rewards_deleted_none"))

    @lvl_rewards.command(name="editrole", aliases=["er"])
    async def level_rewards_edit_role(self, ctx: commands.Context, level: int, new_role: discord.Role):
        """ Change what role is awarded at a certain level """
        _settings, existent = await self.settings_start(ctx, "leveling")
        language = self.bot.language(ctx)
        if level > max_level or level <= -max_level:
            return await ctx.send(language.string("settings_leveling_rewards_max", max_level=language.number(max_level)))
        if new_role.is_default():
            return await ctx.send(language.string("settings_leveling_rewards_default"))
        try:
            rr = _settings["leveling"]["rewards"]
        except KeyError:
            rr = []
        roles = [i["role"] for i in rr]
        if new_role.id in roles:
            return await ctx.send(language.string("settings_leveling_rewards_already_role2", p=ctx.prefix))
        u = False
        for i, reward in enumerate(rr):
            if level == reward["level"]:
                rr[i] = {"level": level, "role": new_role.id}
                u = True
                break
        if u:
            _settings["leveling"]["rewards"] = rr
            return await self.settings_end(ctx, _settings, existent, "settings_leveling_rewards_edit", role=new_role.name, level=language.number(level))
        else:
            return await ctx.send(language.string("settings_leveling_rewards_edit_fail", level=language.number(level)))

    @lvl_rewards.command(name="editlevel", aliases=["el"])
    async def level_rewards_edit_level(self, ctx: commands.Context, role: discord.Role, new_level: int):
        """ Change at which level the role is awarded """
        _settings, existent = await self.settings_start(ctx, "leveling")
        language = self.bot.language(ctx)
        if new_level > max_level or new_level <= -max_level:
            return await ctx.send(language.string("settings_leveling_rewards_max", max_level=language.number(max_level)))
        if role.is_default():
            return await ctx.send(language.string("settings_leveling_rewards_default"))
        try:
            rr = _settings["leveling"]["rewards"]
        except KeyError:
            rr = []
        levels = [i["level"] for i in rr]
        if new_level in levels:
            return await ctx.send(language.string("settings_leveling_rewards_already_level2", p=ctx.prefix))
        u = False
        for i, r in enumerate(rr):
            if role.id == r["role"]:
                rr[i] = {"level": new_level, "role": role.id}
                u = True
                break
        if u:
            _settings["leveling"]["rewards"] = rr
            return await self.settings_end(ctx, _settings, existent, "settings_leveling_rewards_edit", role=role.name, level=language.number(new_level))
        else:
            return await ctx.send(language.string("settings_leveling_rewards_edit_fail2", role=role.name))

    @set_lvl.group(name="retaindata", aliases=["dataretention", "dr"], case_insensitive=True)
    async def lvl_data_retention(self, ctx: commands.Context):
        """ Set whether to keep a user's XP after they leave the server or not """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    async def lvl_data_retention_toggle(self, ctx: commands.Context, toggle: bool):
        """ Enable or disable leveling data retention """
        _settings, existent = await self.settings_start(ctx, "leveling")
        _settings["leveling"]["retain_data"] = toggle
        output = "settings_leveling_data_retention_enable" if toggle else "settings_leveling_data_retention_disable"
        return await self.settings_end(ctx, _settings, existent, output)

    @lvl_data_retention.command(name="disable")
    async def lvl_data_retention_disable(self, ctx: commands.Context):
        """ Disable leveling data retention """
        return await self.lvl_data_retention_toggle(ctx, False)

    @lvl_data_retention.command(name="enable")
    async def lvl_data_retention_enable(self, ctx: commands.Context):
        """ Enable leveling data retention """
        # Cancel the deletion of users' leveling data
        self.bot.db.execute("UPDATE leveling SET remove=NULL WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        return await self.lvl_data_retention_toggle(ctx, True)

    @settings.command(name="muterole", aliases=["mutedrole", "muted", "mute"])
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_mute_role(self, ctx: commands.Context, role: discord.Role):
        """ Set the Muted role """
        _settings, existent = await self.settings_start(ctx, "mute_role")
        _settings["mute_role"] = role.id
        return await self.settings_end(ctx, _settings, existent, "settings_mute_role", role=role.name)

    async def settings_current_starboard(self, ctx: commands.Context):
        """ Current starboard settings """
        language = self.bot.language(ctx)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if not data:
            return await ctx.send(language.string("settings_none"))
        setting = json.loads(data["data"])
        if "starboard" not in setting:
            return await ctx.send(language.string("settings_starboard_none"))
        starboard = setting["starboard"]
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("settings_starboard", ctx.guild.name)
        if ctx.guild.icon:
            embed.set_thumbnail(url=str(ctx.guild.icon.replace(size=1024, static_format="png")))
        embed.set_footer(text=language.string("settings_starboard_footer", p=ctx.prefix))
        embed.add_field(name=language.string("settings_starboard_enabled2"), value=language.yes(starboard["enabled"]), inline=False)
        channel = f"<#{starboard['channel']}>" if starboard["channel"] != 0 else language.string("settings_starboard_channel_none")
        embed.add_field(name=language.string("settings_starboard_channel"), value=channel, inline=False)
        embed.add_field(name=language.string("settings_starboard_requirement"), value=language.number(starboard["minimum"]), inline=False)
        return await ctx.send(embed=embed)

    @settings.group(name="starboard", aliases=["stars", "sb"], case_insensitive=True, invoke_without_command=True)
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_starboard(self, ctx: commands.Context, _: str = None):
        """ Starboard settings """
        if ctx.invoked_subcommand is None:
            if _ is not None:
                return await ctx.send_help(ctx.command)
            return await self.settings_current_starboard(ctx)

    async def starboard_toggle(self, ctx: commands.Context, toggle: bool):
        """ Enable or disable the starboard """
        _settings, existent = await self.settings_start(ctx, "starboard")
        _settings["starboard"]["enabled"] = toggle
        output = "settings_starboard_enabled" if toggle else "settings_starboard_disabled"
        return await self.settings_end(ctx, _settings, existent, output)

    @set_starboard.command(name="enable")
    async def starboard_enable(self, ctx: commands.Context):
        """ Enable starboard """
        return await self.starboard_toggle(ctx, True)

    @set_starboard.command(name="disable")
    async def starboard_disable(self, ctx: commands.Context):
        """ Disable starboard """
        return await self.starboard_toggle(ctx, False)

    @set_starboard.command(name="channel")
    async def starboard_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Set the channel for starboard messages """
        _settings, existent = await self.settings_start(ctx, "starboard")
        _settings["starboard"]["channel"] = channel.id
        return await self.settings_end(ctx, _settings, existent, "settings_starboard_channel_set", channel=channel.mention)

    @set_starboard.command(name="minimum", aliases=["requirement", "min", "req"])
    async def starboard_requirement(self, ctx: commands.Context, requirement: int):
        """ Set the minimum amount of stars before the message is sent to the starboard """
        _settings, existent = await self.settings_start(ctx, "starboard")
        language = self.bot.language(ctx)
        if requirement < 1:
            return await ctx.send(language.string("settings_starboard_requirement_min"))
        _settings["starboard"]["minimum"] = requirement
        return await self.settings_end(ctx, _settings, existent, "settings_starboard_requirement_set", value=language.number(requirement))

    async def settings_current_birthdays(self, ctx: commands.Context):
        """ Current birthday settings """
        language = self.bot.language(ctx)
        data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
        if not data:
            return await ctx.send(f"{language.string('settings_none')}\n{language.string('settings_birthdays_footer', ctx.prefix)}")
        setting = json.loads(data["data"])
        if "birthdays" not in setting:
            return await ctx.send(f"{language.string('settings_birthdays_none')}\n{language.string('settings_birthdays_footer', ctx.prefix)}")
        birthdays = setting["birthdays"]
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("settings_birthdays", ctx.guild.name)
        if ctx.guild.icon:
            embed.set_thumbnail(url=str(ctx.guild.icon.replace(size=1024, static_format="png")))
        embed.set_footer(text=language.string("settings_birthdays_footer", p=ctx.prefix))
        embed.add_field(name=language.string("settings_birthdays_enabled2"), value=language.yes(birthdays["enabled"]), inline=False)
        if birthdays["channel"] != 0:
            embed.add_field(name=language.string("settings_birthdays_channel"), value=f"<#{birthdays['channel']}>", inline=False)
            if birthdays["message"] and len(birthdays["message"]) > 1024:
                message = f"{birthdays['message'][:1023]}…"
            else:
                message = birthdays["message"]
            embed.add_field(name=language.string("settings_birthdays_message"), value=message, inline=False)
        else:
            embed.add_field(name=language.string("settings_birthdays_channel"), value=language.string("settings_birthdays_channel_none"), inline=False)
        role = f"<@&{birthdays['role']}>" if birthdays["role"] != 0 else language.string("settings_birthdays_role_none")
        embed.add_field(name=language.string("settings_birthdays_role"), value=role, inline=False)
        return await ctx.send(embed=embed)

    @settings.group(name="birthdays", aliases=["birthday", "bd", "b"], case_insensitive=True, invoke_without_command=True)
    # @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_birthday(self, ctx: commands.Context, _: str = None):
        """ Birthday settings """
        if ctx.invoked_subcommand is None:
            if _ is not None:
                return await ctx.send_help(ctx.command)
            return await self.settings_current_birthdays(ctx)

    async def birthdays_toggle(self, ctx: commands.Context, toggle: bool):
        """ Enable or disable birthdays """
        _settings, existent = await self.settings_start(ctx, "birthdays")
        _settings["birthdays"]["enabled"] = toggle
        output = "settings_birthdays_enabled" if toggle else "settings_birthdays_disabled"
        return await self.settings_end(ctx, _settings, existent, output, p=ctx.prefix)

    @set_birthday.command(name="enable")
    async def birthday_enable(self, ctx: commands.Context):
        """ Enable birthdays in your server """
        return await self.birthdays_toggle(ctx, True)

    @set_birthday.command(name="disable")
    async def birthday_disable(self, ctx: commands.Context):
        """ Disable birthdays in your server """
        return await self.birthdays_toggle(ctx, False)

    @set_birthday.group(name="channel", case_insensitive=True, invoke_without_command=True)
    async def birthday_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ Set the channel for birthday messages

        Enter "disable" to disable birthday messages """
        _settings, existent = await self.settings_start(ctx, "birthdays")
        if channel is None:
            _channel = _settings["birthdays"]["channel"]
            if _channel == 0:
                return await ctx.send(ctx.language().string("settings_birthdays_channel_unset"))
            return await ctx.send(ctx.language().string("settings_birthdays_channel_set2", channel=f"<#{_channel}>"))
        else:
            _settings["birthdays"]["channel"] = channel.id
            return await self.settings_end(ctx, _settings, existent, "settings_birthdays_channel_set", channel=channel.mention)

    @birthday_channel.command(name="disable", aliases=["reset"])
    async def birthday_channel_disable(self, ctx: commands.Context):
        """ Disable birthday messages """
        _settings, existent = await self.settings_start(ctx, "birthdays")
        _settings["birthdays"]["channel"] = 0
        return await self.settings_end(ctx, _settings, existent, "settings_birthdays_channel_none2")

    @set_birthday.group(name="role", case_insensitive=True, invoke_without_command=True)
    async def birthday_role(self, ctx: commands.Context, role: discord.Role = None):
        """ Set the birthday role

        Enter "disable" to not give a birthday role"""
        _settings, existent = await self.settings_start(ctx, "birthdays")
        if role is None:
            _role = _settings["birthdays"]["role"]
            if _role == 0:
                return await ctx.send(ctx.language().string("settings_birthdays_role_unset"))
            return await ctx.send(ctx.language().string("settings_birthdays_role_set2", role=f"<@&{_role}>"), allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))
        else:
            _settings["birthdays"]["role"] = role.id
            return await self.settings_end(ctx, _settings, existent, "settings_birthdays_role_set", role=role.name)

    @birthday_role.command(name="disable", aliases=["remove", "reset"])
    async def birthday_role_disable(self, ctx: commands.Context):
        """ Disable giving a role to people who have a birthday """
        _settings, existent = await self.settings_start(ctx, "birthdays")
        _settings["birthdays"]["role"] = 0
        return await self.settings_end(ctx, _settings, existent, "settings_birthdays_role_none2")

    @set_birthday.group(name="message")
    async def birthday_message(self, ctx: commands.Context, *, text: str = None):
        """ Set the happy birthday message

        Enter "default" or "reset" to go back to the default message

        Variables:
        [MENTION] - Mention the user who has birthday
        [USER] - The name of the user who has birthday"""
        _settings, existent = await self.settings_start(ctx, "birthdays")
        if text is None:
            _message = _settings["birthdays"]["message"]
            return await ctx.send(ctx.language().string("settings_birthdays_message_set2", message=_message, allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False)))
        else:
            text = text.replace("\\n", "\n")
            _settings["birthdays"]["message"] = text
            filled = text.replace("[MENTION]", ctx.author.mention).replace("[USER]", ctx.author.name)
            return await self.settings_end(ctx, _settings, existent, "settings_birthdays_message_set", message=text, formatted=filled)

    @birthday_message.command(name="default", aliases=["reset"])
    async def birthday_message_default(self, ctx: commands.Context):
        """ Reset the birthday message to the default value """
        _settings, existent = await self.settings_start(ctx, "birthdays")
        _settings["birthdays"]["message"] = self.template["birthdays"]["message"]
        return await self.settings_end(ctx, _settings, existent, "settings_birthdays_message_reset")

    @settings.group(name="messagelogs", aliases=["messages", "message", "msg"], case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_messages(self, ctx: commands.Context):
        """ Log deleted and edited messages to a channel """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    async def messages_toggle(self, ctx: commands.Context, toggle: bool):
        """ Enable or disable the message logs """
        _settings, existent = await self.settings_start(ctx, "message_logs")
        _settings["message_logs"]["enabled"] = toggle
        output = "settings_messages_enable" if toggle else "settings_messages_disable"
        return await self.settings_end(ctx, _settings, existent, output)

    @set_messages.command(name="disable")
    async def set_messages_disable(self, ctx: commands.Context):
        """ Disable message logs """
        return await self.messages_toggle(ctx, False)

    @set_messages.command(name="enable")
    async def set_messages_enable(self, ctx: commands.Context):
        """ Enable message logs """
        return await self.messages_toggle(ctx, True)

    @staticmethod
    def current_edit_channel(ctx: commands.Context, _settings: dict):
        """ Return the current edit channel """
        _channel = _settings["message_logs"]["edit"]
        if _channel == 0:
            return ctx.language().string("settings_messages_current_edit_disabled")
        return ctx.language().string("settings_messages_current_edit", channel=f"<#{_channel}>")

    @set_messages.group(name="editchannel", aliases=["edits", "edit"], invoke_without_command=True, case_insensitive=True)
    async def set_messages_channel_edit(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ Set the channel for edited message logs """
        if ctx.invoked_subcommand is None:
            _settings, existent = await self.settings_start(ctx, "message_logs")
            if channel is None:
                return await ctx.send(self.current_edit_channel(ctx, _settings))
            else:
                _settings["message_logs"]["edit"] = channel.id
                return await self.settings_end(ctx, _settings, existent, "settings_messages_set_edit", channel=channel.mention, p=ctx.prefix)

    @set_messages_channel_edit.command(name="disable")
    async def set_messages_channel_edit_disable(self, ctx: commands.Context):
        """ Disable logging edited messages """
        _settings, existent = await self.settings_start(ctx, "message_logs")
        _settings["message_logs"]["edit"] = 0
        return await self.settings_end(ctx, _settings, existent, "settings_messages_disable_edit")

    @staticmethod
    def current_delete_channel(ctx: commands.Context, _settings: dict):
        """ Return the current deleted channel """
        _channel = _settings["message_logs"]["delete"]
        if _channel == 0:
            return ctx.language().string("settings_messages_current_delete_disabled")
        return ctx.language().string("settings_messages_current_delete", channel=f"<#{_channel}>")

    @set_messages.group(name="deletechannel", aliases=["deletes", "delete"], invoke_without_command=True, case_insensitive=True)
    async def set_messages_channel_delete(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ Set the channel for delete message logs """
        if ctx.invoked_subcommand is None:
            _settings, existent = await self.settings_start(ctx, "message_logs")
            if channel is None:
                return await ctx.send(self.current_delete_channel(ctx, _settings))
            else:
                _settings["message_logs"]["delete"] = channel.id
                return await self.settings_end(ctx, _settings, existent, "settings_messages_set_delete", channel=channel.mention, p=ctx.prefix)

    @set_messages_channel_delete.command(name="disable")
    async def set_messages_channel_delete_disable(self, ctx: commands.Context):
        """ Disable logging deleted messages """
        _settings, existent = await self.settings_start(ctx, "message_logs")
        _settings["message_logs"]["delete"] = 0
        return await self.settings_end(ctx, _settings, existent, "settings_messages_disable_delete")

    @set_messages.command(name="channel", aliases=["set"])
    async def set_messages_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ Set the channel for message logs - both edited and deleted messages """
        _settings, existent = await self.settings_start(ctx, "message_logs")
        if channel is None:
            edits = self.current_edit_channel(ctx, _settings)
            deletes = self.current_delete_channel(ctx, _settings)
            return await ctx.send(f"{edits}\n{deletes}")
        else:
            _settings["message_logs"]["edit"] = channel.id
            _settings["message_logs"]["delete"] = channel.id
            return await self.settings_end(ctx, _settings, existent, "settings_messages_set", channel=channel.mention, p=ctx.prefix)

    @set_messages.group(name="ignore", aliases=["ignoredchannels", "ignorechannels", "ic"], case_insensitive=True)
    async def set_messages_ignore(self, ctx: commands.Context):
        """ Ignore edited and deleted messages in certain channels """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.channel)

    @set_messages_ignore.command(name="add", aliases=["a", "+"])
    async def messages_ignore_add(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Ignore edited and deleted messages in the specified channel """
        _settings, existent = await self.settings_start(ctx, "message_logs")
        _settings["message_logs"]["ignore_channels"].append(channel.id)
        return await self.settings_end(ctx, _settings, existent, "settings_messages_ignore_add", channel=channel.mention)

    @set_messages_ignore.command(name="remove", aliases=["delete", "r", "d", "-"])
    async def messages_ignore_remove(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Don't ignore edited and deleted messages in the specified channel anymore """
        _settings, existent = await self.settings_start(ctx, "message_logs")
        try:
            _settings["message_logs"]["ignore_channels"].remove(channel.id)
        except (ValueError, KeyError):
            return await ctx.send(self.bot.language(ctx).string("settings_messages_ignore_invalid"))
        return await self.settings_end(ctx, _settings, existent, "settings_messages_ignore_remove", channel=channel.mention)

    @set_messages_ignore.command(name="removeall", aliases=["deleteall", "rall", "dall"])
    async def messages_ignore_removeall(self, ctx: commands.Context):
        """ Stop ignoring edited and deleted messages in any channels (Warning: this cannot be undone) """
        _settings, existent = await self.settings_start(ctx, "message_logs")
        _settings["message_logs"]["ignore_channels"] = []
        return await self.settings_end(ctx, _settings, existent, "settings_messages_ignore_removeall")

    async def messages_ignore_bots_toggle(self, ctx: commands.Context, toggle: bool):
        """ Enable or disable ignoring bots' messages """
        _settings, existent = await self.settings_start(ctx, "message_logs")
        _settings["message_logs"]["ignore_bots"] = toggle
        output = "settings_messages_bots_enable" if toggle else "settings_messages_bots_disable"
        return await self.settings_end(ctx, _settings, existent, output)

    @set_messages.group(name="ignorebots", aliases=["bots"])
    async def set_messages_ignore_bots(self, ctx: commands.Context):
        """ Ignore bots' messages """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.channel)

    @set_messages_ignore_bots.command(name="enable")
    async def messages_ignore_bots_enable(self, ctx: commands.Context):
        """ Enable ignoring bots' messages """
        return await self.messages_ignore_bots_toggle(ctx, True)

    @set_messages_ignore_bots.command(name="disable")
    async def messages_ignore_bots_disable(self, ctx: commands.Context):
        """ Disable ignoring bots' messages """
        return await self.messages_ignore_bots_toggle(ctx, False)

    @settings.group(name="polls", case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["suager"] and ctx.guild is not None and ctx.guild.id in [869975256566210641, 738425418637639775])
    async def set_polls(self, ctx: commands.Context):
        """ Polls settings """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @set_polls.group(name="channel", case_insensitive=True, invoke_without_command=True)
    async def set_poll_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ Set the channel where poll updates and results will go """
        if ctx.invoked_subcommand is None:
            _settings, existent = await self.settings_start(ctx, "polls")
            if channel is None:
                _channel = _settings["polls"]["channel"]
                if _channel == 0:
                    return await ctx.send(ctx.language().string("settings_poll_channel_none2"))
                return await ctx.send(ctx.language().string("settings_poll_channel_set2", channel=f"<#{_channel}>"))
            else:
                _settings["polls"]["channel"] = channel.id
                return await self.settings_end(ctx, _settings, existent, "settings_poll_channel_set", channel=channel.mention)

    @set_poll_channel.command(name="default", aliases=["reset"])
    async def set_poll_channel_default(self, ctx: commands.Context):
        """ Reset the poll channel """
        _settings, existent = await self.settings_start(ctx, "polls")
        _settings["polls"]["channel"] = 0
        return await self.settings_end(ctx, _settings, existent, "settings_poll_channel_none")

    @set_polls.command(name="anonymity", aliases=["anon"])
    async def set_poll_anonymity(self, ctx: commands.Context, value: str):
        """ Set whether voters will be shown at the end of the poll or not (yes = anonymous, no = log voters) """
        _settings, existent = await self.settings_start(ctx, "polls")
        if value.lower() == "yes":
            _settings["polls"]["voter_anonymity"] = True
        elif value.lower() == "no":
            _settings["polls"]["voter_anonymity"] = False
        else:
            return await ctx.send(ctx.language().string("settings_poll_anonymity_invalid"))
        output = "settings_poll_anonymity_yes" if _settings["polls"]["voter_anonymity"] else "settings_poll_anonymity_no"
        return await self.settings_end(ctx, _settings, existent, output)

    @settings.group(name="joinrole", aliases=["autorole", "join", "jr"], case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_join_role(self, ctx: commands.Context):
        """ Automatically give new members a role """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @set_join_role.group(name="members", aliases=["member"], case_insensitive=True)
    async def set_member_join_role(self, ctx: commands.Context):
        """ Set the role to give to new human members """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @set_member_join_role.command(name="add", aliases=["a", "+"])
    async def add_member_join_role(self, ctx: commands.Context, role: discord.Role):
        """ Give this role to new human members """
        _settings, existent = await self.settings_start(ctx, "join_roles")
        members = _settings["join_roles"]["members"]
        if isinstance(members, int):  # If it is old
            if members == 0:
                _settings["join_roles"]["members"] = []
            else:
                _settings["join_roles"]["members"] = [members]
        _settings["join_roles"]["members"].append(role.id)
        return await self.settings_end(ctx, _settings, existent, "settings_join_members_add", role=role.name)

    @set_member_join_role.command(name="remove", aliases=["r", "delete", "d", "-"])
    async def remove_member_join_role(self, ctx: commands.Context, role: discord.Role):
        """ Don't give this role new human members """
        _settings, existent = await self.settings_start(ctx, "join_roles")
        members = _settings["join_roles"]["members"]
        if isinstance(members, int):  # If it is old
            if members == 0:
                _settings["join_roles"]["members"] = []
            else:
                _settings["join_roles"]["members"] = [members]
        try:
            _settings["join_roles"]["members"].remove(role.id)
        except (IndexError, ValueError):
            return await ctx.send(ctx.language().string("settings_join_members_error", role=role.name))
        return await self.settings_end(ctx, _settings, existent, "settings_join_members_remove", role=role.name)

    @set_member_join_role.command(name="removeall", aliases=["deleteall", "rall", "dall"])
    async def remove_all_member_join_roles(self, ctx: commands.Context):
        """ Stop giving any roles to new human members (Warning: this cannot be undone) """
        _settings, existent = await self.settings_start(ctx, "join_roles")
        _settings["join_roles"]["members"] = []
        return await self.settings_end(ctx, _settings, existent, "settings_join_members_removeall")

    @set_join_role.group(name="bots", aliases=["bot"], case_insensitive=True)
    async def set_bot_join_role(self, ctx: commands.Context):
        """ Set the role to give to new bots """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @set_bot_join_role.command(name="add", aliases=["a", "+"])
    async def add_bot_join_role(self, ctx: commands.Context, role: discord.Role):
        """ Give this role to new bots """
        _settings, existent = await self.settings_start(ctx, "join_roles")
        members = _settings["join_roles"]["bots"]
        if isinstance(members, int):  # If it is old
            if members == 0:
                _settings["join_roles"]["bots"] = []
            else:
                _settings["join_roles"]["bots"] = [members]
        _settings["join_roles"]["bots"].append(role.id)
        return await self.settings_end(ctx, _settings, existent, "settings_join_bots_add", role=role.name)

    @set_bot_join_role.command(name="remove", aliases=["r", "delete", "d", "-"])
    async def remove_bot_join_role(self, ctx: commands.Context, role: discord.Role):
        """ Don't give this role new bots """
        _settings, existent = await self.settings_start(ctx, "join_roles")
        members = _settings["join_roles"]["bots"]
        if isinstance(members, int):  # If it is old
            if members == 0:
                _settings["join_roles"]["bots"] = []
            else:
                _settings["join_roles"]["bots"] = [members]
        try:
            _settings["join_roles"]["bots"].remove(role.id)
        except (IndexError, ValueError):
            return await ctx.send(ctx.language().string("settings_join_bots_error", role=role.name))
        return await self.settings_end(ctx, _settings, existent, "settings_join_bots_remove", role=role.name)

    @set_bot_join_role.command(name="removeall", aliases=["deleteall", "rall", "dall"])
    async def remove_all_bot_join_roles(self, ctx: commands.Context):
        """ Stop giving any roles to new bots (Warning: this cannot be undone) """
        _settings, existent = await self.settings_start(ctx, "join_roles")
        _settings["join_roles"]["bots"] = []
        return await self.settings_end(ctx, _settings, existent, "settings_join_bots_removeall")

    @settings.group(name="welcome", case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_welcome(self, ctx: commands.Context):
        """ Welcome new members to your server """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @set_welcome.command(name="channel", case_insensitive=True, invoke_without_command=True)
    async def set_welcome_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ Set the channel for welcome messages """
        if ctx.invoked_subcommand is None:
            _settings, existent = await self.settings_start(ctx, "welcome")
            if channel is None:
                _channel = _settings["welcome"]["channel"]
                if _channel == 0:
                    return await ctx.send(ctx.language().string("settings_welcome_channel_none2"))
                return await ctx.send(ctx.language().string("settings_welcome_channel_set2", channel=f"<#{_channel}>"))
            else:
                _settings["welcome"]["channel"] = channel.id
                return await self.settings_end(ctx, _settings, existent, "settings_welcome_channel_set", channel=channel.mention)

    @set_welcome.command(name="disable", aliases=["reset"])
    async def set_welcome_channel_default(self, ctx: commands.Context):
        """ Disable welcome messages """
        _settings, existent = await self.settings_start(ctx, "welcome")
        _settings["welcome"]["channel"] = 0
        return await self.settings_end(ctx, _settings, existent, "settings_welcome_channel_none")

    @set_welcome.group(name="message", invoke_without_command=True, case_insensitive=True)
    async def welcome_message(self, ctx: commands.Context, *, value: str):
        """ Set the welcome message """
        if ctx.invoked_subcommand is None:
            language = self.bot.language(ctx)
            _settings, existent = await self.settings_start(ctx, "welcome")
            value = value.replace("\\n", "\n")
            _settings["welcome"]["message"] = value
            message2 = value \
                .replace("[MENTION]", ctx.author.mention)\
                .replace("[USER]", general.username(ctx.author))\
                .replace("[SERVER]", ctx.guild.name)\
                .replace("[CREATED_AT]", language.time(ctx.author.created_at, short=1, dow=False, seconds=False, tz=True))\
                .replace("[JOINED_AT]", language.time(ctx.author.joined_at, short=1, dow=False, seconds=False, tz=True))\
                .replace("[ACCOUNT_AGE]", language.delta_dt(ctx.author.created_at, accuracy=3, brief=False, affix=False))\
                .replace("[MEMBERS]", language.number(ctx.guild.member_count))
            return await self.settings_end(ctx, _settings, existent, "settings_welcome_message", message=value, formatted=message2)

    @welcome_message.command(name="variables", aliases=["vars"])
    async def welcome_message_vars(self, ctx: commands.Context):
        """ Welcome message variables """
        return await ctx.send(ctx.language().string("settings_welcome_message_variables"))

    @settings.group(name="goodbye", aliases=["farewell"], case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_goodbye(self, ctx: commands.Context):
        """ Say something when a user leaves your server """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @set_goodbye.command(name="channel", case_insensitive=True, invoke_without_command=True)
    async def set_goodbye_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ Set the channel for goodbye messages """
        _settings, existent = await self.settings_start(ctx, "goodbye")
        if channel is None:
            _channel = _settings["goodbye"]["channel"]
            if _channel == 0:
                return await ctx.send(ctx.language().string("settings_goodbye_channel_none2"))
            return await ctx.send(ctx.language().string("settings_goodbye_channel_set2", channel=f"<#{_channel}>"))
        else:
            _settings["goodbye"]["channel"] = channel.id
            return await self.settings_end(ctx, _settings, existent, "settings_goodbye_channel_set", channel=channel.mention)

    @set_goodbye.command(name="disable", aliases=["reset"])
    async def set_goodbye_channel_default(self, ctx: commands.Context):
        """ Disable goodbye messages """
        _settings, existent = await self.settings_start(ctx, "goodbye")
        _settings["goodbye"]["channel"] = 0
        return await self.settings_end(ctx, _settings, existent, "settings_goodbye_channel_none")

    @set_goodbye.group(name="message", invoke_without_command=True, case_insensitive=True)
    async def goodbye_message(self, ctx: commands.Context, *, value: str):
        """ Set the goodbye message """
        if ctx.invoked_subcommand is None:
            language = self.bot.language(ctx)
            _settings, existent = await self.settings_start(ctx, "goodbye")
            value = value.replace("\\n", "\n")
            _settings["goodbye"]["message"] = value
            message2 = value \
                .replace("[MENTION]", ctx.author.mention)\
                .replace("[USER]", general.username(ctx.author))\
                .replace("[SERVER]", ctx.guild.name)\
                .replace("[CREATED_AT]", language.time(ctx.author.created_at, short=1, dow=False, seconds=False, tz=True))\
                .replace("[JOINED_AT]", language.time(ctx.author.joined_at, short=1, dow=False, seconds=False, tz=True))\
                .replace("[ACCOUNT_AGE]", language.delta_dt(ctx.author.created_at, accuracy=3, brief=False, affix=False))\
                .replace("[LENGTH_OF_STAY]", language.delta_dt(ctx.author.joined_at, accuracy=3, brief=False, affix=False))\
                .replace("[MEMBERS]", language.number(ctx.guild.member_count))
            return await self.settings_end(ctx, _settings, existent, "settings_goodbye_message", message=value, formatted=message2)

    @goodbye_message.command(name="variables", aliases=["vars"])
    async def goodbye_message_vars(self, ctx: commands.Context):
        """ Goodbye message variables """
        return await ctx.send(ctx.language().string("settings_goodbye_message_variables"))

    @settings.group(name="moddms", aliases=["moddm", "dmonmod", "dms", "md"], case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_mod_dms(self, ctx: commands.Context):
        """ Send a DM to the user when a moderation action is applied against them """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    async def set_mod_dms_generic_check(self, ctx: commands.Context, punishment: str):
        _settings, _ = await self.settings_start(ctx, "mod_dms")
        enabled = _settings["mod_dms"][punishment]
        text = "enabled2" if enabled else "disabled2"
        command_part = "disable" if enabled else "enable"
        command = f"`{ctx.prefix}settings moddms {ctx.invoked_with} {command_part}`"
        return await ctx.send(ctx.language().string(f"settings_mod_dms_{punishment}_{text}", command=command))

    async def set_mod_dms_generic_enable(self, ctx: commands.Context, punishment: str):
        _settings, existent = await self.settings_start(ctx, "mod_dms")
        if punishment == "all":
            _settings["mod_dms"]["ban"] = True
            _settings["mod_dms"]["kick"] = True
            _settings["mod_dms"]["mute"] = True
            _settings["mod_dms"]["warn"] = True
        else:
            _settings["mod_dms"][punishment] = True
        return await self.settings_end(ctx, _settings, existent, f"settings_mod_dms_{punishment}_enabled")

    async def set_mod_dms_generic_disable(self, ctx: commands.Context, punishment: str):
        _settings, existent = await self.settings_start(ctx, "mod_dms")
        if punishment == "all":
            _settings["mod_dms"]["ban"] = False
            _settings["mod_dms"]["kick"] = False
            _settings["mod_dms"]["mute"] = False
            _settings["mod_dms"]["warn"] = False
        else:
            _settings["mod_dms"][punishment] = False
        return await self.settings_end(ctx, _settings, existent, f"settings_mod_dms_{punishment}_disabled")

    @set_mod_dms.command(name="enableall", aliases=["enable", "onall", "on"])
    async def set_mod_dms_enableall(self, ctx: commands.Context):
        """ Enable mod DMs for all punishments at once """
        return await self.set_mod_dms_generic_enable(ctx, "all")

    @set_mod_dms.command(name="disableall", aliases=["disable", "offall", "off"])
    async def set_mod_dms_disableall(self, ctx: commands.Context):
        """ Disable mod DMs for all punishments at once """
        return await self.set_mod_dms_generic_disable(ctx, "all")

    @set_mod_dms.group(name="bans", aliases=["ban"], case_insensitive=True)
    async def set_mod_dms_bans(self, ctx: commands.Context):
        """ Send a DM to the user when they get banned """
        if ctx.invoked_subcommand is None:
            return await self.set_mod_dms_generic_check(ctx, "ban")

    @set_mod_dms_bans.command(name="enable", aliases=["on"])
    async def set_mod_dm_bans_enable(self, ctx: commands.Context):
        """ Enable DMs for bans """
        return await self.set_mod_dms_generic_enable(ctx, "ban")

    @set_mod_dms_bans.command(name="disable", aliases=["off", "reset"])
    async def set_mod_dm_bans_disable(self, ctx: commands.Context):
        """ Disable DMs for bans """
        return await self.set_mod_dms_generic_disable(ctx, "ban")

    @set_mod_dms.group(name="kicks", aliases=["kick"], case_insensitive=True)
    async def set_mod_dms_kicks(self, ctx: commands.Context):
        """ Send a DM to the user when they get kicked """
        if ctx.invoked_subcommand is None:
            return await self.set_mod_dms_generic_check(ctx, "kick")

    @set_mod_dms_kicks.command(name="enable", aliases=["on"])
    async def set_mod_dm_kicks_enable(self, ctx: commands.Context):
        """ Enable DMs for kicks """
        return await self.set_mod_dms_generic_enable(ctx, "kick")

    @set_mod_dms_kicks.command(name="disable", aliases=["off", "reset"])
    async def set_mod_dm_kicks_disable(self, ctx: commands.Context):
        """ Disable DMs for kicks """
        return await self.set_mod_dms_generic_disable(ctx, "kick")

    @set_mod_dms.group(name="mutes", aliases=["mute"], case_insensitive=True)
    async def set_mod_dms_mutes(self, ctx: commands.Context):
        """ Send a DM to the user when they get muted """
        if ctx.invoked_subcommand is None:
            return await self.set_mod_dms_generic_check(ctx, "mute")

    @set_mod_dms_mutes.command(name="enable", aliases=["on"])
    async def set_mod_dm_mutes_enable(self, ctx: commands.Context):
        """ Enable DMs for mutes """
        return await self.set_mod_dms_generic_enable(ctx, "mute")

    @set_mod_dms_mutes.command(name="disable", aliases=["off", "reset"])
    async def set_mod_dm_mutes_disable(self, ctx: commands.Context):
        """ Disable DMs for mutes """
        return await self.set_mod_dms_generic_disable(ctx, "mute")

    @set_mod_dms.group(name="warnings", aliases=["warning", "warns", "warn"], case_insensitive=True)
    async def set_mod_dms_warnings(self, ctx: commands.Context):
        """ Send a DM to the user when they get warned """
        if ctx.invoked_subcommand is None:
            return await self.set_mod_dms_generic_check(ctx, "warn")

    @set_mod_dms_warnings.command(name="enable", aliases=["on"])
    async def set_mod_dm_warnings_enable(self, ctx: commands.Context):
        """ Enable DMs for warnings """
        return await self.set_mod_dms_generic_enable(ctx, "warn")

    @set_mod_dms_warnings.command(name="disable", aliases=["off", "reset"])
    async def set_mod_dm_warnings_disable(self, ctx: commands.Context):
        """ Disable DMs for warnings """
        return await self.set_mod_dms_generic_disable(ctx, "warn")

    @settings.group(name="modlogs", aliases=["modlog", "ml"], case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_mod_logs(self, ctx: commands.Context):
        """ Log moderation actions taken using this bot """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    async def set_mod_logs_generic_check(self, ctx: commands.Context, punishment: str):
        _settings, _ = await self.settings_start(ctx, "mod_logs")
        language = ctx.language()
        enabled = _settings["mod_logs"][punishment]
        text = "enabled" if enabled else "disabled"
        command_part = "disable" if enabled else language.string("settings_mod_dms_channel")
        command = f"`{ctx.prefix}settings modlogs {ctx.invoked_with} {command_part}`"
        return await ctx.send(language.string(f"settings_mod_logs_{text}_{punishment}", command=command, channel=f"<#{enabled}>"))

    async def set_mod_logs_generic_enable(self, ctx: commands.Context, punishment: str, channel: discord.TextChannel):
        _settings, existent = await self.settings_start(ctx, "mod_logs")
        if punishment.startswith("all"):
            _settings["mod_logs"]["ban"] = channel.id
            _settings["mod_logs"]["kick"] = channel.id
            _settings["mod_logs"]["mute"] = channel.id
            _settings["mod_logs"]["warn"] = channel.id
            if punishment == "all2":
                _settings["mod_logs"]["roles"] = channel.id
        else:
            _settings["mod_logs"][punishment] = channel.id
        return await self.settings_end(ctx, _settings, existent, f"settings_mod_logs_enable_{punishment}", channel=channel.mention)

    async def set_mod_logs_generic_disable(self, ctx: commands.Context, punishment: str):
        _settings, existent = await self.settings_start(ctx, "mod_logs")
        if punishment.startswith("all"):
            _settings["mod_logs"]["ban"] = 0
            _settings["mod_logs"]["kick"] = 0
            _settings["mod_logs"]["mute"] = 0
            _settings["mod_logs"]["warn"] = 0
            if punishment == "all2":
                _settings["mod_logs"]["roles"] = 0
        else:
            _settings["mod_logs"][punishment] = 0
        return await self.settings_end(ctx, _settings, existent, f"settings_mod_logs_disable_{punishment}")

    @set_mod_logs.command(name="enableall", aliases=["enable", "onall", "on"])
    async def set_mod_logs_enable_all(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Log all moderation actions **except role changes** to the specified channel """
        return await self.set_mod_logs_generic_enable(ctx, "all", channel)

    @set_mod_logs.command(name="enableall2", aliases=["enable2", "onall2", "on2", "enableroles", "onroles"])
    async def set_mod_logs_enable_all2(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Log all moderation actions **including role changes** to the specified channel """
        return await self.set_mod_logs_generic_enable(ctx, "all2", channel)

    @set_mod_logs.command("disableall", aliases=["disable", "offall", "off"])
    async def set_mod_logs_disable_all(self, ctx: commands.Context):
        """ Disable logging of any moderation actions (except role changes) """
        return await self.set_mod_logs_generic_disable(ctx, "all")

    @set_mod_logs.command("disableall2", aliases=["disable2", "offall2", "off2", "disableroles", "offroles"])
    async def set_mod_logs_disable_all2(self, ctx: commands.Context):
        """ Disable logging of any moderation actions (including role changes) """
        return await self.set_mod_logs_generic_disable(ctx, "all2")

    @set_mod_logs.group("bans", aliases=["ban"], case_insensitive=True, invoke_without_command=True)
    async def set_mod_logs_bans(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ Log bans to the specified channel """
        if ctx.invoked_subcommand is None:
            if channel is None:
                return await self.set_mod_logs_generic_check(ctx, "ban")
            return await self.set_mod_logs_generic_enable(ctx, "ban", channel)

    @set_mod_logs_bans.command(name="disable", aliases=["reset", "off"])
    async def set_mod_logs_bans_disable(self, ctx: commands.Context):
        """ Disable mod logs for bans """
        return await self.set_mod_logs_generic_disable(ctx, "ban")

    @set_mod_logs.group("kicks", aliases=["kick"], case_insensitive=True, invoke_without_command=True)
    async def set_mod_logs_kicks(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ Log kicks to the specified channel """
        if ctx.invoked_subcommand is None:
            if channel is None:
                return await self.set_mod_logs_generic_check(ctx, "kick")
            return await self.set_mod_logs_generic_enable(ctx, "kick", channel)

    @set_mod_logs_kicks.command(name="disable", aliases=["reset", "off"])
    async def set_mod_logs_kicks_disable(self, ctx: commands.Context):
        """ Disable mod logs for kicks """
        return await self.set_mod_logs_generic_disable(ctx, "kick")

    @set_mod_logs.group("mutes", aliases=["mute"], case_insensitive=True, invoke_without_command=True)
    async def set_mod_logs_mutes(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ Log mutes to the specified channel """
        if ctx.invoked_subcommand is None:
            if channel is None:
                return await self.set_mod_logs_generic_check(ctx, "mute")
            return await self.set_mod_logs_generic_enable(ctx, "mute", channel)

    @set_mod_logs_mutes.command(name="disable", aliases=["reset", "off"])
    async def set_mod_logs_mutes_disable(self, ctx: commands.Context):
        """ Disable mod logs for mutes """
        return await self.set_mod_logs_generic_disable(ctx, "mute")

    @set_mod_logs.group("warnings", aliases=["warning", "warns", "warn"], case_insensitive=True, invoke_without_command=True)
    async def set_mod_logs_warns(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ Log warnings to the specified channel """
        if ctx.invoked_subcommand is None:
            if channel is None:
                return await self.set_mod_logs_generic_check(ctx, "warn")
            return await self.set_mod_logs_generic_enable(ctx, "warn", channel)

    @set_mod_logs_warns.command(name="disable", aliases=["reset", "off"])
    async def set_mod_logs_warns_disable(self, ctx: commands.Context):
        """ Disable mod logs for warnings """
        return await self.set_mod_logs_generic_disable(ctx, "warn")

    @set_mod_logs.group("roles", aliases=["role"], case_insensitive=True, invoke_without_command=True)
    async def set_mod_logs_roles(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ Log changes in members' roles to the specified channel """
        if ctx.invoked_subcommand is None:
            if channel is None:
                return await self.set_mod_logs_generic_check(ctx, "roles")
            return await self.set_mod_logs_generic_enable(ctx, "roles", channel)

    @set_mod_logs_roles.command(name="disable", aliases=["reset", "off"])
    async def set_mod_logs_roles_disable(self, ctx: commands.Context):
        """ Disable mod logs for changes in members' roles """
        return await self.set_mod_logs_generic_disable(ctx, "roles")

    @settings.group(name="userlogs", aliases=["users"], case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_user_logs(self, ctx: commands.Context):
        """ Settings for user logs """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    async def user_logs_check(self, ctx: commands.Context, action: str):
        _settings, _ = await self.settings_start(ctx, "user_logs")
        language = ctx.language()
        enabled = _settings["user_logs"][action]
        text = "set2" if enabled else "none2"
        command_part = "disable" if enabled else language.string("settings_mod_dms_channel")
        command = f"`{ctx.prefix}settings userlogs {ctx.invoked_with} {command_part}`"
        return await ctx.send(language.string(f"settings_users_{action}_{text}", command=command, channel=f"<#{enabled}>"))

    async def user_logs_enable(self, ctx: commands.Context, action: str, channel: discord.TextChannel):
        _settings, existent = await self.settings_start(ctx, "user_logs")
        _settings["user_logs"][action] = channel.id
        return await self.settings_end(ctx, _settings, existent, f"settings_users_{action}_set", channel=channel.mention)

    async def user_logs_disable(self, ctx: commands.Context, action: str):
        _settings, existent = await self.settings_start(ctx, "user_logs")
        _settings["user_logs"][action] = 0
        return await self.settings_end(ctx, _settings, existent, f"settings_users_{action}_none")

    @set_user_logs.group(name="join", case_insensitive=True, invoke_without_command=True)
    async def set_join_logs_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ Set the channel for logging people who join the server """
        if ctx.invoked_subcommand is None:
            if channel is None:
                return await self.user_logs_check(ctx, "join")
            return await self.user_logs_enable(ctx, "join", channel)

    @set_join_logs_channel.command(name="disable", aliases=["reset"])
    async def set_join_logs_disable(self, ctx: commands.Context):
        """ Disable logging people joining the server """
        return await self.user_logs_disable(ctx, "join")

    @set_user_logs.group(name="leave", case_insensitive=True, invoke_without_command=True)
    async def set_leave_logs_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ Set the channel for logging people who leave the server """
        if ctx.invoked_subcommand is None:
            if channel is None:
                return await self.user_logs_check(ctx, "leave")
            return await self.user_logs_enable(ctx, "leave", channel)

    @set_leave_logs_channel.command(name="disable", aliases=["reset"])
    async def set_leave_logs_disable(self, ctx: commands.Context):
        """ Disable logging people leaving the server """
        return await self.user_logs_disable(ctx, "leave")

    @set_user_logs.group(name="all", aliases=["both"], case_insensitive=True, invoke_without_command=True)
    async def set_user_logs_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Set the channel for logging both people joining and leaving the server in one command """
        if ctx.invoked_subcommand is None:
            _settings, existent = await self.settings_start(ctx, "user_logs")
            _settings["user_logs"]["join"] = channel.id
            _settings["user_logs"]["leave"] = channel.id
            return await self.settings_end(ctx, _settings, existent, "settings_users_all_set", channel=channel.mention)

    @set_user_logs_channel.command(name="disable", aliases=["reset"])
    async def set_user_logs_disable(self, ctx: commands.Context):
        """ Disable logging people joining and leaving the server """
        _settings, existent = await self.settings_start(ctx, "user_logs")
        _settings["user_logs"]["join"] = 0
        _settings["user_logs"]["leave"] = 0
        return await self.settings_end(ctx, _settings, existent, "settings_users_all_none")

    @settings.group(name="rolepreservation", aliases=["roles", "preservation"], case_insensitive=True)
    async def set_role_preservation(self, ctx: commands.Context):
        """ Keep the roles the user had when they left if they ever rejoin """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @set_role_preservation.command(name="enable", aliases=["on"])
    async def enable_role_preservation(self, ctx: commands.Context):
        """ Enable giving back the roles the user had when they left if they rejoin """
        _settings, existent = await self.settings_start(ctx, "user_logs")
        _settings["user_logs"]["preserve_roles"] = True
        return await self.settings_end(ctx, _settings, existent, "settings_users_roles_enable")

    @set_role_preservation.command(name="disable", aliases=["off"])
    async def disable_role_preservation(self, ctx: commands.Context):
        """ Disable giving back the roles the user had when they left if they rejoin """
        _settings, existent = await self.settings_start(ctx, "user_logs")
        _settings["user_logs"]["preserve_roles"] = False
        return await self.settings_end(ctx, _settings, existent, "settings_users_roles_disable")

    @settings.group(name="warnings", aliases=["warns", "warn"], case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_warnings(self, ctx: commands.Context):
        """ Settings for warnings """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @set_warnings.command(name="requirement")
    async def set_warning_requirement(self, ctx: commands.Context, warnings: int):
        """ Set the amount of warnings to be reached before the user is muted

         Default value: 3
         This means that the user would get muted when they get the 3rd warning"""
        _settings, existent = await self.settings_start(ctx, "warnings")
        _settings["warnings"]["required_to_mute"] = warnings
        return await self.settings_end(ctx, _settings, existent, "settings_warnings_requirement", warnings=warnings)

    @set_warnings.command(name="length")
    async def set_warning_length(self, ctx: commands.Context, mute_length: str):
        """ Set the starting mute length when reaching the mute requirement

        Default value: 12h
        This works together with the scaling value:
        If the requirement is 3 warnings, the mute length is 12 hours and the scaling is x2,
        then the person is muted for 12 hours on 3rd warning, then for 1 day on 4th warning, etc...

        Note that if the mute length value is specified using months or years, the scaling might not work correctly.
        Instead, specify the amount of days (30 days for a month and 365 days for a year). This will give more accurate scaling results.
        If the mute length exceeds 5 years, the resulting mute will be permanent."""
        _settings, existent = await self.settings_start(ctx, "warnings")
        language = ctx.language()
        value = time.interpret_time(mute_length)
        if time.rd_is_zero(value):
            return await ctx.send(language.string("settings_warnings_length_invalid"))
        _settings["warnings"]["mute_length"] = mute_length
        return await self.settings_end(ctx, _settings, existent, "settings_warnings_length", length=language.delta_rd(value, accuracy=7, brief=False, affix=False))

    @set_warnings.command(name="scaling", aliases=["scale", "multiplier"])
    async def set_warning_scaling(self, ctx: commands.Context, scaling: float):
        """ Set the scaling to apply to mute length

        Default value: 1
        At x2 scaling, the 3rd warning would result in a 12-hour mute, the 4th in a 1-day mute, etc.
        Note that if the mute length value is specified using months or years, the scaling might not work correctly.
        If the mute length exceeds 5 years, the resulting mute will be permanent."""
        language = ctx.language()
        _settings, existent = await self.settings_start(ctx, "warnings")
        _settings["warnings"]["scaling"] = scaling
        return await self.settings_end(ctx, _settings, existent, "settings_warnings_scaling", scaling=language.number(scaling))

    @settings.group(name="antiads", aliases=["ads", "adblock", "invites"], case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_anti_ads(self, ctx: commands.Context):
        """ Settings for anti-ads (blocking unwanted Discord invite links) """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    async def set_anti_ads_toggle(self, ctx: commands.Context, enabled: bool):
        """ Enable anti-ads """
        _settings, existent = await self.settings_start(ctx, "anti_ads")
        _settings["anti_ads"]["enabled"] = enabled
        output = "settings_anti_ads_enable" if enabled else "settings_anti_ads_disable"
        return await self.settings_end(ctx, _settings, existent, output)

    @set_anti_ads.command(name="enable")
    async def set_anti_ads_enable(self, ctx: commands.Context):
        """ Enable anti-ads """
        return await self.set_anti_ads_toggle(ctx, True)

    @set_anti_ads.command(name="disable")
    async def set_anti_ads_disable(self, ctx: commands.Context):
        """ Disable anti-ads """
        return await self.set_anti_ads_toggle(ctx, False)

    @set_anti_ads.group(name="mode", case_insensitive=True)
    async def set_anti_ads_mode(self, ctx: commands.Context):
        """ Set the mode in which the anti-ads channel filter will work

        Default mode: blacklist
        Use `//settings antiads channels` to add or remove channels to/from the list """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    async def set_anti_ads_mode_generic(self, ctx: commands.Context, whitelist: bool):
        _settings, existent = await self.settings_start(ctx, "anti_ads")
        _settings["anti_ads"]["whitelist"] = whitelist
        output = "settings_anti_ads_whitelist" if whitelist else "settings_anti_ads_blacklist"
        return await self.settings_end(ctx, _settings, existent, output, p=ctx.prefix)

    @set_anti_ads_mode.command(name="whitelist")
    async def set_anti_ads_whitelist(self, ctx: commands.Context):
        """ Set the anti-ads channel filter to whitelist mode - Only messages in specified channels will be scanned """
        return await self.set_anti_ads_mode_generic(ctx, True)

    @set_anti_ads_mode.command(name="blacklist")
    async def set_anti_ads_blacklist(self, ctx: commands.Context):
        """ Set the anti-ads channel filter to blacklist mode - Messages in specified channels will be ignored """
        return await self.set_anti_ads_mode_generic(ctx, False)

    @set_anti_ads.group(name="channels", aliases=["channel", "ch"], case_insensitive=True)
    async def set_anti_ads_channels(self, ctx: commands.Context):
        """ Add or remove channels to the blacklist or whitelist

        Use `//settings antiads mode` to set whether this list will be treated as a whitelist or blacklist """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @set_anti_ads_channels.command(name="add", aliases=["a", "+"])
    async def set_anti_ads_channel_add(self, ctx: commands.Context, channel: discord.TextChannel | discord.Thread):
        """ Add a channel to the list """
        _settings, existent = await self.settings_start(ctx, "anti_ads")
        if channel.guild.id != ctx.guild.id:
            return await ctx.send(ctx.language().string("settings_anti_ads_channel_invalid2"))
        if channel.id in _settings["anti_ads"]["channels"]:  # Channel was already added before
            return await ctx.send(ctx.language().string("settings_anti_ads_channel_already"))
        _settings["anti_ads"]["channels"].append(channel.id)
        return await self.settings_end(ctx, _settings, existent, "settings_anti_ads_channel_add", channel=channel.mention)

    @set_anti_ads_channels.command(name="remove", aliases=["delete", "r", "d", "-"])
    async def set_anti_ads_channel_remove(self, ctx: commands.Context, channel: discord.TextChannel | discord.Thread):
        """ Remove a channel to the list """
        _settings, existent = await self.settings_start(ctx, "anti_ads")
        if channel.guild.id != ctx.guild.id:
            return await ctx.send(ctx.language().string("settings_anti_ads_channel_invalid2"))
        try:
            _settings["anti_ads"]["channels"].remove(channel.id)
        except ValueError:
            return await ctx.send(ctx.language().string("settings_anti_ads_channel_invalid3"))
        return await self.settings_end(ctx, _settings, existent, "settings_anti_ads_channel_remove", channel=channel.mention)

    @set_anti_ads_channels.command(name="removeall", aliases=["deleteall", "rall", "dall"])
    async def set_anti_ads_channel_removeall(self, ctx: commands.Context):
        """ Remove all channels from the list (Warning: this cannot be undone) """
        _settings, existent = await self.settings_start(ctx, "anti_ads")
        _settings["anti_ads"]["channels"] = []
        return await self.settings_end(ctx, _settings, existent, "settings_anti_ads_channel_remove2")

    @set_anti_ads.command(name="warning", aliases=["warninglength", "length", "warningduration", "duration"])
    async def set_anti_ad_warning_length(self, ctx: commands.Context, warning_length: str = None):
        """ Set the duration of the warnings given for an advertisement

        Leave empty to set a permanent warning, or specify a valid warning duration.
        Default value: *Permanent*
        If the warning length exceeds 5 years, the warning will be permanent."""
        language = ctx.language()
        _settings, existent = await self.settings_start(ctx, "anti_ads")
        if warning_length is not None:
            value = time.interpret_time(warning_length)
            if time.rd_is_zero(value):
                return await ctx.send(language.string("settings_anti_ads_warning_invalid"))
            if time.rd_is_above_5y(value):
                output = "settings_anti_ads_warning3"
                length = None
                warning_length = None
            else:
                output = "settings_anti_ads_warning"
                length = language.delta_rd(value, accuracy=7, brief=False, affix=False)
        else:
            output = "settings_anti_ads_warning2"
            length = None
        _settings["anti_ads"]["warning"] = warning_length
        return await self.settings_end(ctx, _settings, existent, output, length=length)

    @settings.group(name="imageonly", aliases=["imagesonly", "images"], case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi", "suager"])
    async def set_image_only_channels(self, ctx: commands.Context):
        """ Add or remove channels to the list of image-only channels """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @set_image_only_channels.command(name="add", aliases=["a", "+"])
    async def set_image_only_channels_add(self, ctx: commands.Context, channel: discord.TextChannel | discord.Thread):
        """ Enable the image-only filter in a channel """
        _settings, existent = await self.settings_start(ctx, "image_only")
        if channel.guild.id != ctx.guild.id:
            return await ctx.send(ctx.language().string("settings_anti_ads_channel_invalid2"))
        if channel.id in _settings["image_only"]["channels"]:  # Channel was already added before
            return await ctx.send(ctx.language().string("settings_image_only_channel_already"))
        _settings["image_only"]["channels"].append(channel.id)
        return await self.settings_end(ctx, _settings, existent, "settings_image_only_channel_add", channel=channel.mention)

    @set_image_only_channels.command(name="remove", aliases=["delete", "r", "d", "-"])
    async def set_image_only_channels_remove(self, ctx: commands.Context, channel: discord.TextChannel | discord.Thread):
        """ Disable the image-only filter in a channel """
        _settings, existent = await self.settings_start(ctx, "image_only")
        if channel.guild.id != ctx.guild.id:
            return await ctx.send(ctx.language().string("settings_anti_ads_channel_invalid2"))
        try:
            _settings["image_only"]["channels"].remove(channel.id)
        except ValueError:
            return await ctx.send(ctx.language().string("settings_image_only_channel_invalid"))
        return await self.settings_end(ctx, _settings, existent, "settings_image_only_channel_remove", channel=channel.mention)

    @set_image_only_channels.command(name="removeall", aliases=["deleteall", "rall", "dall"])
    async def set_image_only_channels_removeall(self, ctx: commands.Context):
        """ Disable the image-only filter in all channels (Warning: this cannot be undone) """
        _settings, existent = await self.settings_start(ctx, "image_only")
        _settings["image_only"]["channels"] = []
        return await self.settings_end(ctx, _settings, existent, "settings_image_only_channel_remove2")

    @settings.group(name="serverstats", aliases=["vcserverstats", "vcss", "ss"], case_insensitive=True)
    @commands.check(lambda ctx: ctx.bot.name in ["kyomi"])
    async def set_vc_server_stats(self, ctx: commands.Context):
        """ Show server stats as voice channel names

         Note: Channel names are only updated once in 6 hours and whenever the settings are changed.
         Usage: `m!settings serverstats <category> <channel|text> [...]` """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    async def set_vc_server_stats_channel(self, ctx: commands.Context, category: str, channel: discord.VoiceChannel | None):
        """ Wrapper function for setting a channel to use for VC server stats """
        language = ctx.language()
        if not isinstance(channel, (discord.VoiceChannel, type(None))):
            return await ctx.send(language.string("settings_server_stats_channel_invalid"))
        if channel is not None and channel.guild.id != ctx.guild.id:
            return await ctx.send(language.string("settings_anti_ads_channel_invalid2"))
        _settings, existent = await self.settings_start(ctx, "vc_server_stats")
        if category not in _settings["vc_server_stats"]:
            _settings["vc_server_stats"][category] = self.template["vc_server_stats"][category].copy()
        if channel is not None:
            channel_id = channel.id
            channel_name = f"<#{channel_id}>"
            mode = "set"
        else:
            channel_id = 0
            channel_name = ""
            mode = "disable"
        _settings["vc_server_stats"][category]["channel"] = channel_id
        if channel is not None:
            name = self.format_server_stats_text(ctx, category, _settings["vc_server_stats"][category]["text"])
            try:
                await channel.edit(name=name)
            except discord.Forbidden:
                return await ctx.send(language.string("settings_server_stats_forbidden"))
            except discord.HTTPException:  # This shouldn't happen, but if it does, ignore.
                pass
        return await self.settings_end(ctx, _settings, existent, f"settings_server_stats_{category}_channel_{mode}", channel=channel_name)

    async def current_server_stats_channel(self, ctx: commands.Context, category: str):
        _settings, _ = await self.settings_start(ctx, "vc_server_stats")
        language = ctx.language()
        if category not in _settings["vc_server_stats"]:
            return await ctx.send(language.string(f"settings_server_stats_{category}_disabled"))
        cat_settings = _settings["vc_server_stats"][category]
        if cat_settings["channel"] == 0:
            return await ctx.send(language.string(f"settings_server_stats_{category}_disabled"))
        channel = f"<#{cat_settings['channel']}>"
        return await ctx.send(language.string(f"settings_server_stats_{category}_channel_current", channel=channel))

    @staticmethod
    def format_server_stats_text(ctx: commands.Context, category: str, text: str):
        match category:
            case "total_members":
                formatted = text.replace("[MEMBERS]", str(len(ctx.guild.members)))
            case "human_members":
                formatted = text.replace("[MEMBERS]", str(sum(1 for m in ctx.guild.members if not m.bot)))
            case "bot_members":
                formatted = text.replace("[MEMBERS]", str(sum(1 for m in ctx.guild.members if m.bot)))
            case "today_date":
                formatted = text.replace("[TODAY]", format(time2.date.today(), "%d %b %Y"))
            case _:
                formatted = text
        return formatted

    async def set_vc_server_stats_text(self, ctx: commands.Context, category: str, text: str | None):
        """ Wrapper function for setting the text format to use on the voice channel """
        _settings, existent = await self.settings_start(ctx, "vc_server_stats")
        language = ctx.language()
        if category not in _settings["vc_server_stats"]:
            _settings["vc_server_stats"][category] = self.template["vc_server_stats"][category].copy()
        if text is None:
            text: str = self.template["vc_server_stats"][category]["text"]
            mode = "reset"
        else:
            mode = "set"
        _settings["vc_server_stats"][category]["text"] = text
        formatted = self.format_server_stats_text(ctx, category, text)
        text_and_formatted = language.string("settings_server_stats_text_and_formatted", text=text, formatted=formatted)
        if _settings["vc_server_stats"][category]["channel"] != 0:
            channel = ctx.guild.get_channel(_settings["vc_server_stats"][category]["channel"])
            try:
                await channel.edit(name=formatted)
            except discord.Forbidden:
                await ctx.send(language.string("settings_server_stats_forbidden2"))
            except discord.HTTPException:  # This shouldn't happen, but if it does, ignore.
                pass
        return await self.settings_end(ctx, _settings, existent, f"settings_server_stats_{category}_text_{mode}", text_and_formatted=text_and_formatted)

    async def current_server_stats_text(self, ctx: commands.Context, category: str):
        _settings, _ = await self.settings_start(ctx, "vc_server_stats")
        language = ctx.language()
        if category not in _settings["vc_server_stats"]:
            return await ctx.send(language.string(f"settings_server_stats_{category}_disabled"))
        cat_settings = _settings["vc_server_stats"][category]
        text = cat_settings["text"]
        formatted = self.format_server_stats_text(ctx, category, text)
        text_and_formatted = language.string("settings_server_stats_text_and_formatted", text=text, formatted=formatted)
        return await ctx.send(language.string(f"settings_server_stats_{category}_text_current", text_and_formatted=text_and_formatted))

    async def server_stats_channel_command(self, ctx: commands.Context, category: str, channel: discord.VoiceChannel = None):
        if channel is not None:
            return await self.set_vc_server_stats_channel(ctx, category, channel)
        return await self.current_server_stats_channel(ctx, category)

    async def server_stats_text_command(self, ctx: commands.Context, category: str, text: str = None):
        if text is not None:
            return await self.set_vc_server_stats_text(ctx, category, text)
        return await self.current_server_stats_text(ctx, category)

    # TODO: Find a way to do this without having to copy-paste identical subcommands for each category
    @set_vc_server_stats.group(name="members", aliases=["total_members", "tm", "m"], case_insensitive=True)
    async def vc_server_stats_total_members(self, ctx: commands.Context):
        """ Show the total number of members in the server (humans and bots) """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @vc_server_stats_total_members.command(name="channel", aliases=["ch", "c"])
    async def total_members_channel(self, ctx: commands.Context, channel: discord.VoiceChannel = None):
        """ Set the voice channel to use to show the total number of members """
        return await self.server_stats_channel_command(ctx, "total_members", channel)

    @vc_server_stats_total_members.command(name="disable")
    async def total_members_disable(self, ctx: commands.Context):
        """ Disable showing the total number of members """
        return await self.set_vc_server_stats_channel(ctx, "total_members", None)

    @vc_server_stats_total_members.command(name="text", aliases=["format", "t", "f"])
    async def total_members_text(self, ctx: commands.Context, *, text: str = None):
        """ Set the format for the name of the voice channel """
        return await self.server_stats_text_command(ctx, "total_members", text)

    @vc_server_stats_total_members.command(name="reset")
    async def total_members_reset(self, ctx: commands.Context):
        """ Reset the format for the name of the voice channel back to the default """
        return await self.set_vc_server_stats_text(ctx, "total_members", None)

    @set_vc_server_stats.group(name="humans", aliases=["human_members", "hm", "h"], case_insensitive=True)
    async def vc_server_stats_human_members(self, ctx: commands.Context):
        """ Show the current number of human members in the server """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @vc_server_stats_human_members.command(name="channel", aliases=["ch", "c"])
    async def human_members_channel(self, ctx: commands.Context, channel: discord.VoiceChannel = None):
        """ Set the voice channel to use to show the number of human members """
        return await self.server_stats_channel_command(ctx, "human_members", channel)

    @vc_server_stats_human_members.command(name="disable")
    async def human_members_disable(self, ctx: commands.Context):
        """ Disable showing the number of human members """
        return await self.set_vc_server_stats_channel(ctx, "human_members", None)

    @vc_server_stats_human_members.command(name="text", aliases=["format", "t", "f"])
    async def human_members_text(self, ctx: commands.Context, *, text: str = None):
        """ Set the format for the name of the voice channel """
        return await self.server_stats_text_command(ctx, "human_members", text)

    @vc_server_stats_human_members.command(name="reset")
    async def human_members_reset(self, ctx: commands.Context):
        """ Reset the format for the name of the voice channel back to the default """
        return await self.set_vc_server_stats_text(ctx, "human_members", None)

    @set_vc_server_stats.group(name="bots", aliases=["bot_members", "bm", "b"], case_insensitive=True)
    async def vc_server_stats_bot_members(self, ctx: commands.Context):
        """ Show the current number of bots in the server """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @vc_server_stats_bot_members.command(name="channel", aliases=["ch", "c"])
    async def _bot_members_channel(self, ctx: commands.Context, channel: discord.VoiceChannel = None):
        """ Set the voice channel to use to show the number of bots """
        return await self.server_stats_channel_command(ctx, "bot_members", channel)

    @vc_server_stats_bot_members.command(name="disable")
    async def _bot_members_disable(self, ctx: commands.Context):
        """ Disable showing the number of bots """
        return await self.set_vc_server_stats_channel(ctx, "bot_members", None)

    @vc_server_stats_bot_members.command(name="text", aliases=["format", "t", "f"])
    async def _bot_members_text(self, ctx: commands.Context, *, text: str = None):
        """ Set the format for the name of the voice channel """
        return await self.server_stats_text_command(ctx, "bot_members", text)

    @vc_server_stats_bot_members.command(name="reset")
    async def _bot_members_reset(self, ctx: commands.Context):
        """ Reset the format for the name of the voice channel back to the default """
        return await self.set_vc_server_stats_text(ctx, "bot_members", None)

    @set_vc_server_stats.group(name="today", aliases=["today_date", "td", "t", "d"], case_insensitive=True)
    async def vc_server_stats_today_date(self, ctx: commands.Context):
        """ Show the current number of bots in the server """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @vc_server_stats_today_date.command(name="channel", aliases=["ch", "c"])
    async def today_date_channel(self, ctx: commands.Context, channel: discord.VoiceChannel = None):
        """ Set the voice channel to use to show today's date """
        return await self.server_stats_channel_command(ctx, "today_date", channel)

    @vc_server_stats_today_date.command(name="disable")
    async def today_date_disable(self, ctx: commands.Context):
        """ Disable showing today's date """
        return await self.set_vc_server_stats_channel(ctx, "today_date", None)

    @vc_server_stats_today_date.command(name="text", aliases=["format", "t", "f"])
    async def today_date_text(self, ctx: commands.Context, *, text: str = None):
        """ Set the format for the name of the voice channel """
        return await self.server_stats_text_command(ctx, "today_date", text)

    @vc_server_stats_today_date.command(name="reset")
    async def today_date_reset(self, ctx: commands.Context):
        """ Reset the format for the name of the voice channel back to the default """
        return await self.set_vc_server_stats_text(ctx, "today_date", None)

    @commands.command(name="prefixes", aliases=["prefix"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def prefix(self, ctx: commands.Context):
        """ Server prefixes """
        language = self.bot.language(ctx)
        dp, cp = self.prefix_list(ctx)
        embed = discord.Embed(colour=general.random_colour())
        embed.title = language.string("settings_prefixes_title", bot=self.bot.user.display_name, server=ctx.guild.name)
        # embed.title = f"Prefixes for {self.bot.user.name} in {ctx.guild.name}"
        if ctx.guild.icon:
            embed.set_thumbnail(url=str(ctx.guild.icon.replace(size=1024, static_format="png")))
        embed.add_field(name=language.string("settings_prefixes_default"), value='\n'.join(dp), inline=True)
        if cp:
            embed.add_field(name=language.string("settings_prefixes_custom"), value='\n'.join(cp), inline=True)
        return await ctx.send(embed=embed)

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


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Settings(bot))
