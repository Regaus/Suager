import json
from io import BytesIO

import discord
from discord.ext import commands

from cogs.levels import max_level
from utils import database, permissions, generic, time, argparser, http
from utils.generic import settings_template


class Discord(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database()

    @commands.group(name="settings", aliases=["set"])
    @commands.guild_only()
    @permissions.has_permissions(manage_guild=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def settings(self, ctx: commands.Context):
        """ Server settings """
        if ctx.invoked_subcommand is None:
            data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
            if data:
                try:
                    send = BytesIO(data['data'].encode('utf-8'))
                except AttributeError:
                    send = BytesIO(data['data'])
                return await generic.send(
                    generic.gls(generic.get_lang(ctx.guild), "settings_current", [ctx.guild.name, ctx.prefix]),
                    ctx.channel, file=discord.File(send, filename=time.file_ts("Settings", "json")))
            else:
                send = BytesIO(json.dumps(settings_template.copy(), indent=4).encode('utf-8'))
                return await generic.send(generic.gls(generic.get_lang(ctx.guild), "settings_template", [ctx.prefix]), ctx.channel,
                                          file=discord.File(send, filename=time.file_ts("SettingsTemplate", "json")))

    @settings.command(name="template")
    async def settings_template(self, ctx: commands.Context):
        """ Settings template """
        send = BytesIO(json.dumps(settings_template.copy(), indent=4).encode('utf-8'))
        return await generic.send(generic.gls(generic.get_lang(ctx.guild), "settings_template_detailed", [ctx.prefix]), ctx.channel,
                                  file=discord.File(send, filename=time.file_ts("SettingsTemplate", "json")))

    @settings.command(name="upload")
    async def settings_upload(self, ctx: commands.Context):
        """ Upload cogs server settings """
        ma = ctx.message.attachments
        if len(ma) == 1:
            name = ma[0].filename
            if not name.endswith('json'):
                return await generic.send(generic.gls(generic.get_lang(ctx.guild), "settings_upload_no1"), ctx.channel)
            try:
                stuff = await ma[0].read()
            except discord.HTTPException or discord.NotFound:
                return await generic.send(generic.gls(generic.get_lang(ctx.guild), "settings_upload_no2"), ctx.channel)
        else:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "settings_upload_no3"), ctx.channel)
        try:
            json.loads(stuff)
        except Exception as e:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "settings_upload_no4",
                                                  [f"{type(e).__name__}: {e}"]), ctx.channel)
        data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            res = self.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            res = self.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await generic.send(generic.gls(generic.get_lang(ctx.guild), "settings_upload_yes", [res]), ctx.channel)

    @settings.command(name="locale")
    async def set_locale(self, ctx: commands.Context, new_locale: str):
        """ Change server locale """
        data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            settings = json.loads(data["data"])
        else:
            settings = settings_template.copy()
        settings["locale"] = new_locale
        stuff = json.dumps(settings)
        if data:
            res = self.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            res = self.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_locale", [new_locale, res]), ctx.channel)

    @settings.command(name="currency")
    async def set_currency(self, ctx: commands.Context, new: str):
        """ Change server currency """
        data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            settings = json.loads(data["data"])
        else:
            settings = settings_template.copy()
        settings["currency"] = new
        stuff = json.dumps(settings)
        if data:
            res = self.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            res = self.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_currency", [new, res]), ctx.channel)

    @settings.group(name="prefixes")
    async def set_prefixes(self, ctx: commands.Context):
        """ Change server prefixes """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @set_prefixes.command(name="add")
    async def prefix_add(self, ctx: commands.Context, prefix: str):
        """ Add a new custom prefix """
        data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            settings = json.loads(data["data"])
        else:
            settings = settings_template.copy()
        settings["prefixes"].append(prefix)
        stuff = json.dumps(settings)
        if data:
            res = self.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            res = self.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_pa", [prefix, res]), ctx.channel)

    @set_prefixes.command(name="remove")
    async def prefix_remove(self, ctx: commands.Context, prefix: str):
        """ Remove a custom prefix """
        data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            settings = json.loads(data["data"])
        else:
            settings = settings_template.copy()
        try:
            settings["prefixes"].remove(prefix)
        except ValueError:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_prf", [prefix]), ctx.channel)
        stuff = json.dumps(settings)
        if data:
            res = self.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            res = self.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_pr", [prefix, res]), ctx.channel)

    @set_prefixes.command(name="default")
    async def prefix_default(self, ctx: commands.Context):
        """ Toggle the use of default prefixes """
        data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            settings = json.loads(data["data"])
        else:
            settings = settings_template.copy()
        settings["use_default"] ^= True
        stuff = json.dumps(settings)
        if data:
            res = self.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            res = self.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        t = settings["use_default"]
        return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_pde" if t else "su_pdd", [res]), ctx.channel)

    @settings.group(name="antispam", aliases=["as"])
    async def set_as(self, ctx: commands.Context):
        """ Change anti-spam channels """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @set_as.command(name="add")
    async def as_add(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Add a channel to the list """
        data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            settings = json.loads(data["data"])
        else:
            settings = settings_template.copy()
        if "anti_spam" not in settings:
            settings["anti_spam"] = {"channels": []}
        if channel.id in settings["anti_spam"]["channels"]:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_asaa", [channel.name]), ctx.channel)
        settings["anti_spam"]["channels"].append(channel.id)
        stuff = json.dumps(settings)
        if data:
            res = self.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            res = self.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_asa", [channel.name, res]), ctx.channel)

    @set_as.command(name="remove")
    async def as_remove(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Remove a channel from the list """
        data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            settings = json.loads(data["data"])
        else:
            settings = settings_template.copy()
        if "anti_spam" not in settings:
            settings["anti_spam"] = {"channels": []}
        try:
            settings["anti_spam"]["channels"].remove(channel.id)
        except ValueError:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_asdf", [channel.name]), ctx.channel)
        stuff = json.dumps(settings)
        if data:
            res = self.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            res = self.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_asd", [channel.name, res]), ctx.channel)

    @settings.group(name="leveling", aliases=["levels"])
    async def set_lvl(self, ctx: commands.Context):
        """ Leveling settings """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @set_lvl.command(name="enable")
    async def lvl_enable(self, ctx: commands.Context):
        """ Enable leveling """
        data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            settings = json.loads(data["data"])
        else:
            settings = settings_template.copy()
        if "leveling" not in settings:
            settings["leveling"] = settings_template["leveling"].copy()
            settings["leveling"]["rewards"] = []
        settings["leveling"]["enabled"] = True
        stuff = json.dumps(settings)
        if data:
            res = self.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            res = self.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_le", [res]), ctx.channel)

    @set_lvl.command(name="disable")
    async def lvl_disable(self, ctx: commands.Context):
        """ Disable leveling """
        data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            settings = json.loads(data["data"])
        else:
            settings = settings_template.copy()
        if "leveling" not in settings:
            settings["leveling"] = settings_template["leveling"].copy()
            settings["leveling"]["rewards"] = []
        settings["leveling"]["enabled"] = False
        stuff = json.dumps(settings)
        if data:
            res = self.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            res = self.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_ld", [res]), ctx.channel)

    @set_lvl.command(name="multiplier", aliases=["xpm", "mult"])
    async def lvl_xpm(self, ctx: commands.Context, value: float):
        """ Set XP multiplier """
        data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            settings = json.loads(data["data"])
        else:
            settings = settings_template.copy()
        if "leveling" not in settings:
            settings["leveling"] = settings_template["leveling"].copy()
            settings["leveling"]["rewards"] = []
        settings["leveling"]["xp_multiplier"] = value
        stuff = json.dumps(settings)
        if data:
            res = self.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            res = self.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_lm", [value, res]), ctx.channel)

    @set_lvl.command(name="message", aliases=["lum", "msg"])
    async def lvl_lum(self, ctx: commands.Context, *, value: str):
        """ Set level up message """
        data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            settings = json.loads(data["data"])
        else:
            settings = settings_template.copy()
        if "leveling" not in settings:
            settings["leveling"] = settings_template["leveling"].copy()
            settings["leveling"]["rewards"] = []
        settings["leveling"]["level_up_message"] = value
        stuff = json.dumps(settings)
        if data:
            res = self.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            res = self.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_lm2", [value, res]), ctx.channel)

    @set_lvl.group(name="ignored", aliases=["ic"])
    async def lvl_ic(self, ctx: commands.Context):
        """ Change ignored channels for leveling """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @lvl_ic.command(name="add")
    async def ic_add(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Add a channel to the list """
        data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            settings = json.loads(data["data"])
        else:
            settings = settings_template.copy()
        if "leveling" not in settings:
            settings["leveling"] = settings_template["leveling"].copy()
            settings["leveling"]["rewards"] = []
        if channel.id in settings["leveling"]["ignored_channels"]:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_liaa", [channel.name]), ctx.channel)
        settings["leveling"]["ignored_channels"].append(channel.id)
        stuff = json.dumps(settings)
        if data:
            res = self.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            res = self.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_lia", [channel.name, res]), ctx.channel)

    @lvl_ic.command(name="remove")
    async def ic_remove(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Remove a channel from the list """
        data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            settings = json.loads(data["data"])
        else:
            settings = settings_template.copy()
        if "leveling" not in settings:
            settings["leveling"] = settings_template["leveling"].copy()
            settings["leveling"]["rewards"] = []
        try:
            settings["leveling"]["ignored_channels"].remove(channel.id)
        except ValueError:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_lidf", [channel.name]), ctx.channel)
        stuff = json.dumps(settings)
        if data:
            res = self.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            res = self.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_lid", [channel.name, res]), ctx.channel)

    @set_lvl.command(name="announcement", aliases=["ac"])
    async def lvl_ac(self, ctx: commands.Context, channel: discord.TextChannel or None):
        """ Set level up announcement channel """
        data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            settings = json.loads(data["data"])
        else:
            settings = settings_template.copy()
        if "leveling" not in settings:
            settings["leveling"] = settings_template["leveling"].copy()
            settings["leveling"]["rewards"] = []
        if channel is None:
            settings["leveling"]["announce_channel"] = 0
        else:
            settings["leveling"]["announce_channel"] = channel.id
        stuff = json.dumps(settings)
        if data:
            res = self.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            res = self.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        if channel is not None:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_la", [channel.name, res]), ctx.channel)
        else:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_lar", [res]), ctx.channel)

    @set_lvl.group(name="rewards", aliases=["rr", "lr"])
    async def lvl_rr(self, ctx: commands.Context):
        """ Set level rewards for the server """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @lvl_rr.command(name="add")
    async def rr_add(self, ctx: commands.Context, role: discord.Role, level: int):
        """ Add a level reward """
        if level < 0:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_lra_nl"), ctx.channel)
        elif level > max_level:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_lra_hl", [max_level]), ctx.channel)
        data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            settings = json.loads(data["data"])
        else:
            settings = settings_template.copy()
        if "leveling" not in settings:
            settings["leveling"] = settings_template["leveling"].copy()
            settings["leveling"]["rewards"] = []
        try:
            rr = settings["leveling"]["rewards"]
        except KeyError:
            rr = []
        roles = [i["role"] for i in rr]
        if role.id in roles:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_lra_ra"), ctx.channel)
        levels = [i["level"] for i in rr]
        if level in levels:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_lra_la"), ctx.channel)
        rr.append({"level": level, "role": role.id})
        # settings["leveling"]["ignored_channels"].append(channel.id)
        settings["leveling"]["rewards"] = rr
        stuff = json.dumps(settings)
        if data:
            res = self.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            res = self.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_lra", [role.name, level, res]), ctx.channel)

    @lvl_rr.command(name="remove")
    async def rr_remove(self, ctx: commands.Context, role: discord.Role):
        """ Remove a role reward """
        data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            settings = json.loads(data["data"])
        else:
            settings = settings_template.copy()
        if "leveling" not in settings:
            settings["leveling"] = settings_template["leveling"].copy()
            settings["leveling"]["rewards"] = []
        try:
            rr = settings["leveling"]["rewards"]
        except KeyError:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_lrd_nr"), ctx.channel)
        r = False
        for _role in rr:
            if _role["role"] == role.id:
                rr.remove(_role)
                r = True
                break
        if r:
            settings["leveling"]["rewards"] = rr
            stuff = json.dumps(settings)
            if data:
                res = self.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
            else:
                res = self.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_lrd", [role.name, res]), ctx.channel)
        else:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_lrdf", [role.name]), ctx.channel)

    @settings.group(name="shop")
    async def set_shop(self, ctx: commands.Context):
        """ Set level rewards for the server """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @set_shop.command(name="add")
    async def shop_add(self, ctx: commands.Context, role: discord.Role, cost: int):
        """ Add a shop item """
        if cost < 0:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_sa_nc"), ctx.channel)
        data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            settings = json.loads(data["data"])
        else:
            settings = settings_template.copy()
        try:
            rr = settings["shop_items"]
        except KeyError:
            rr = []
        roles = [i["role"] for i in rr]
        if role.id in roles:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_sa_ra"), ctx.channel)
        rr.append({"cost": cost, "role": role.id})
        settings["shop_items"] = rr
        stuff = json.dumps(settings)
        if data:
            res = self.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
        else:
            res = self.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
        return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_sa", [role.name, f"{cost:,}", res]), ctx.channel)

    @set_shop.command(name="remove")
    async def shop_remove(self, ctx: commands.Context, role: discord.Role):
        """ Remove a shop item """
        data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        if data:
            settings = json.loads(data["data"])
        else:
            settings = settings_template.copy()
        try:
            rr = settings["shop_items"]
        except KeyError:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_sd_nr"), ctx.channel)
        r = False
        for _role in rr:
            if _role["role"] == role.id:
                rr.remove(_role)
                r = True
                break
        if r:
            settings["shop_items"] = rr
            stuff = json.dumps(settings)
            if data:
                res = self.db.execute(f"UPDATE settings SET data=? WHERE gid=?", (stuff, ctx.guild.id))
            else:
                res = self.db.execute(f"INSERT INTO settings VALUES (?, ?)", (ctx.guild.id, stuff))
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_sd", [role.name, res]), ctx.channel)
        else:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "su_sdf", [role.name]), ctx.channel)

    @commands.command(name="emojis")
    @commands.is_owner()
    async def get_all_emotes(self, ctx: commands.Context):
        """ Yoink all emotes """
        channel = self.bot.get_channel(676154789159239740)
        await generic.send(f"This stash of emotes was made on {time.time()}", channel)
        # await channel.send(f"This stash of emotes was made on {time.time()}")
        for guild in self.bot.guilds:
            emotes = sorted([e for e in guild.emojis if len(e.roles) == 0 and e.available], key=lambda e: e.name)
            paginator = commands.Paginator(suffix='', prefix='')
            for emote in emotes:
                paginator.add_line(f'{emote.name} = "`{emote}`"')
            await generic.send(f"Next lot -> {guild.name}\n\n\n", channel)
            # await channel.send(f"Next lot -> {guild.name}\n\n\n")
            for page in paginator.pages:
                await generic.send(page, channel)
                # await channel.send(page)
        return await generic.send(f"Done yoinking emotes, {ctx.author.mention}, you may fuck off now.", ctx.channel, u=True)
        # return await ctx.send(f"Done yoinking emotes, {ctx.author.mention}, you may fuck off now.")

    @commands.command(name="emojis2")
    @commands.is_owner()
    async def get_all_emotes2(self, ctx: commands.Context):
        """ Yoink all emotes images """
        channel = self.bot.get_channel(712703923793952780)
        await generic.send("Yoinking emotes...", ctx.channel)
        await generic.send(f"This stash of emotes was made on {time.time()}", channel)
        # await channel.send(f"This stash of emotes was made on {time.time()}")
        for guild in self.bot.guilds:
            # len(e.roles) == 0 and
            emotes = sorted([e for e in guild.emojis if e.available], key=lambda e: e.name)
            # paginator = commands.Paginator(suffix='', prefix='')
            # for emote in emotes:
            #     paginator.add_line(f'{emote.name} = "`{emote}`"')
            await generic.send(f"Next lot -> {guild.name}\n\n\n", channel)
            for emote in emotes:
                # embed = discord.Embed(colour=generic.random_colour())
                # embed.set_image(url=emote.url)
                bio = BytesIO(await http.get(str(emote.url), res_method="read"))
                ext = "gif" if emote.animated else "png"
                await generic.send(f"{emote.name} - {emote.id}", channel, file=discord.File(bio, filename=f"{emote.name}_{emote.id}.{ext}"))
            # # await channel.send(f"Next lot -> {guild.name}\n\n\n")
            # for page in paginator.pages:
            #     await generic.send(page, channel)
            #     # await channel.send(page)
        return await generic.send(f"Done yoinking emotes, {ctx.author.mention}, you may fuck off now.", ctx.channel, u=True)
        # return await ctx.send(f"Done yoinking emotes, {ctx.author.mention}, you may fuck off now.")

    @commands.command(name="avatar")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def avatar(self, ctx: commands.Context, *, who: discord.User = None):
        """ Get someone's avatar """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "avatar"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        # if ctx.channel.id in self.banned:
        #     return
        user = who or ctx.author
        return await generic.send(generic.gls(locale, "avatar", [user.name, user.avatar_url_as(size=1024, static_format="png")]), ctx.channel)
        # return await ctx.send(f"Avatar to **{user.name}**\n{user.avatar_url_as(size=1024, static_format='png')}")

    @commands.command(name="roles")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def roles(self, ctx: commands.Context):
        """ Get all roles in current server """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "roles"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        all_roles = ""
        for num, role in enumerate(sorted(ctx.guild.roles, reverse=True), start=1):
            all_roles += f"[{str(num).zfill(2)}] {role.id}\t{role.name}\t[ Users: {len(role.members)} ]\r\n"
        data = BytesIO(all_roles.encode('utf-8'))
        return await generic.send(generic.gls(locale, "roles_in_server", [ctx.guild.name]), ctx.channel,
                                  file=discord.File(data, filename=f"{time.file_ts('Roles')}"))
        # return await ctx.send(content=f"Roles in **{ctx.guild.name}**",
        #                       file=discord.File(data, filename=f"{time.file_ts('Roles')}"))

    @commands.command(name="joinedat")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def joined_at(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Check when someone joined server """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "joinedat"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        user = who or ctx.author
        return await generic.send(generic.gls(locale, "user_joined_at", [user, ctx.guild.name, time.time_output(user.joined_at)]), ctx.channel)
        # return await ctx.send(f"**{user}** joined **{ctx.guild.name}** on {time.time_output(user.joined_at)}")

    @commands.command(name="user")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def user(self, ctx: commands.Context, *, who: discord.Member = None):
        """ Get info about user """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "user"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        user = who or ctx.author
        embed = discord.Embed(colour=generic.random_colour())
        embed.title = generic.gls(locale, "about_user", [user])
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name=generic.gls(locale, "username"), value=user, inline=True)
        embed.add_field(name=generic.gls(locale, "nickname"), value=user.nick, inline=True)
        embed.add_field(name=generic.gls(locale, "user_id"), value=user.id, inline=True)
        embed.add_field(name=generic.gls(locale, "created_at"), value=time.time_output(user.created_at), inline=True)
        embed.add_field(name=generic.gls(locale, "joined_at"), value=time.time_output(user.joined_at), inline=True)
        embed.add_field(name=generic.gls(locale, "current_status"), value=str(user.status), inline=True)
        try:
            a = list(user.activities)
            if not a:
                embed.add_field(name="Current activity", value="None", inline=False)
            else:
                b = a[0]
                if b.type == discord.ActivityType.custom:
                    e = f"{b.emoji} " if b.emoji is not None else ''
                    n = b.name if b.name is not None else ''
                    embed.add_field(name=generic.gls(locale, "current_activity"), value=f"Custom Status:\n{e}{n}", inline=False)
                elif b.type == discord.ActivityType.streaming:
                    c = b.platform
                    d = b.name if b.name else ''
                    e = f" {b.game} " if b.game else ''
                    embed.add_field(name=generic.gls(locale, "current_activity"), value=f"Streaming {e} on {c}\n{d}", inline=False)
                elif b.type == discord.ActivityType.playing:
                    embed.add_field(name=generic.gls(locale, "current_activity"), value=f"Playing {b.name}", inline=False)
                elif b.type == discord.ActivityType.listening:
                    embed.add_field(name=generic.gls(locale, "current_activity"), inline=False,
                                    value=f"Listening to {b.name}\n{b.title} by {', '.join(b.artists)} - {b.album}")
            # embed.add_field(name="Activity", value=who.activity)
        except AttributeError:
            embed.add_field(name=generic.gls(locale, "current_activity"), value=generic.gls(locale, "no"), inline=False)
        if len(user.roles) < 15:
            r = user.roles
            r.sort(key=lambda x: x.position, reverse=True)
            # roles = ', '.join([f"<@&{x.id}>" for x in user.roles if x is not ctx.guild.default_role]) \
            #     if len(user.roles) > 1 else 'None' + f"\n({len(user.roles)} roles overall)"
            ar = [f"<@&{x.id}>" for x in r if x.id != ctx.guild.default_role.id]
            roles = ', '.join(ar) if ar else 'None'
            b = len(user.roles) - 1
            roles += f"\n({b} role{'s' if b != 1 else ''} overall)"
        else:
            roles = f"There's {len(user.roles) - 1} of them"
        embed.add_field(name=generic.gls(locale, "roles"), value=roles, inline=False)
        return await generic.send(None, ctx.channel, embed=embed)
        # await ctx.send(f"", embed=embed)

    @commands.command(name="emoji", aliases=["emote"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def emoji(self, ctx: commands.Context, emoji: discord.Emoji):
        """ View bigger version of a Custom Emoji """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "emoji"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        return await generic.send(f"{ctx.author.name}:", ctx.channel, embed=discord.Embed(
            description=generic.gls(locale, "emoji_desc", [emoji.name, emoji.id, emoji.animated, emoji.guild.name, time.time_output(emoji.created_at),
                                                           emoji.url]), colour=generic.random_colour()
        ).set_image(url=emoji.url).set_author(name=ctx.author, icon_url=ctx.author.avatar_url))
        # return await ctx.send(f"{ctx.author.name}:", embed=discord.Embed(
        #     description=f"Name: {emoji.name}\nID: {emoji.id}\nAnimated: {emoji.animated}\nServer: {emoji.guild.name}\n"
        #                 f"Created: {time.time_output(emoji.created_at)}\n[Copy Link]({emoji.url})",
        #     colour=generic.random_colour()).set_image(url=emoji.url).set_author(
        #     name=ctx.author, icon_url=ctx.author.avatar_url))

    @commands.command(name="customrole", aliases=["cr"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=30, type=commands.BucketType.user)
    async def custom_role(self, ctx: commands.Context, *, stuff: str):
        """ Custom Role (only in supported servers)

         Arguments:
        -c/--colour/--color: Set role colour
        -n/--name: Set role name """
        if ctx.guild.id in generic.config["custom_role"]:
            data = self.db.fetchrow("SELECT * FROM custom_role WHERE uid=? AND gid=?", (ctx.author.id, ctx.guild.id))
            if not data:
                return await generic.send(f"Doesn't seem like you have a custom role in this server, {ctx.author.name}", ctx.channel)
                # return await ctx.send(f"Doesn't seem like you have a custom role, {ctx.author.name}")
            parser = argparser.Arguments()
            # parser.add_argument('input', nargs="+", default=None)
            parser.add_argument('-c', '--colour', '--color', nargs=1)
            parser.add_argument('-n', '--name', nargs="+")

            args, valid_check = parser.parse_args(stuff)
            if not valid_check:
                return await generic.send(args, ctx.channel)
                # return await ctx.send(args)

            role = ctx.guild.get_role(data['rid'])

            if args.colour is not None:
                c = args.colour[0]
                a = len(c)
                if c == "random":
                    col = generic.random_colour()
                else:
                    if a == 6 or a == 3:
                        try:
                            col = int(c, base=16)
                        except Exception as e:
                            return await generic.send(f"Invalid colour - {type(e).__name__}: {e}", ctx.channel)
                            # return await ctx.send(f"Invalid colour - {type(e).__name__}: {e}")
                    else:
                        return await generic.send("Colour must be either 3 or 6 HEX digits long.", ctx.channel)
                        # return await ctx.send("Colour must be either 3 or 6 HEX digits long.")
                colour = discord.Colour(col)
            else:
                colour = role.colour

            try:
                name = ' '.join(args.name)
            except TypeError:
                name = role.name

            try:
                await role.edit(name=name, colour=colour, reason="Custom Role change")
            except Exception as e:
                return await generic.send(f"An error occurred while updating custom role: {type(e).__name__}: {e}", ctx.channel)
                # return await ctx.send(f"An error occurred while updating custom role: {type(e).__name__}: {e}")
            return await generic.send(f"Successfully updated your custom role, {ctx.author.name}", ctx.channel)
            # return await ctx.send(f"Successfully updated your custom role, {ctx.author.name}")
        else:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "cr_not_available"), ctx.channel)
            # return await generic.send(generic.gls(generic.get_lang(ctx.guild), "only_in_senko_lair"), ctx.channel)
            # return await ctx.send("This command is only available in Senko Lair.")

    @commands.command(name="grantrole")
    @commands.guild_only()
    # @commands.is_owner()
    @permissions.has_permissions(administrator=True)
    async def grant_custom_role(self, ctx: commands.Context, user: discord.Member, role: discord.Role):
        """ Grant custom role """
        if ctx.guild.id in generic.config["custom_role"]:
            # if ctx.guild.id == 568148147457490954:
            already = self.db.fetchrow("SELECT * FROM custom_role WHERE uid=?, gid=?", (user.id, ctx.guild.id))
            if not already:
                result = self.db.execute("INSERT INTO custom_role VALUES (?, ?, ?)", (user.id, role.id, ctx.guild.id))
                await user.add_roles(role, reason="Custom Role grant")
                return await generic.send(f"Granted {role.name} to {user.name}: {result}", ctx.channel)
                # return await ctx.send(f"Granted {role.name} to {user.name}: {result}")
            else:
                result = self.db.execute("UPDATE custom_role SET rid=? WHERE uid=? AND gid=?", (role.id, user.id, ctx.guild.id))
                return await generic.send(f"Updated custom role of {user.name} to {role.name}: {result}", ctx.channel)
                # return await ctx.send(f"Updated custom role of {user.name} to {role.name}: {result}")
        else:
            return await generic.send(generic.gls(generic.get_lang(ctx.guild), "cr_not_available"), ctx.channel)
            # return await ctx.send("This is only available in Senko Lair")

    @commands.group(name="server", aliases=["guild"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def server(self, ctx: commands.Context):
        """ Check info about current server """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "server"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        # if ctx.channel.id in self.banned:
        #     return
        if ctx.invoked_subcommand is None:
            bots = sum(1 for member in ctx.guild.members if member.bot)
            embed = discord.Embed(colour=generic.random_colour())
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.title = generic.gls(locale, "about_server", [ctx.guild.name])
            embed.add_field(name=generic.gls(locale, "server_name"), value=ctx.guild.name, inline=True)
            embed.add_field(name=generic.gls(locale, "server_id"), value=ctx.guild.id, inline=True)
            embed.add_field(name=generic.gls(locale, "owner"), inline=True,
                            value=f"{ctx.guild.owner}\n({ctx.guild.owner.display_name})")
            embed.add_field(name=generic.gls(locale, "members"), value=ctx.guild.member_count, inline=True)
            embed.add_field(name=generic.gls(locale, "bots"), value=str(bots), inline=True)
            embed.add_field(name=generic.gls(locale, "region"), value=ctx.guild.region, inline=True)
            embed.add_field(name=generic.gls(locale, "roles"), value=str(len(ctx.guild.roles)), inline=True)
            try:
                embed.add_field(name=generic.gls(locale, "ban_count"), value=str(len(await ctx.guild.bans())), inline=True)
            except discord.Forbidden:
                embed.add_field(name=generic.gls(locale, "ban_count"), value=generic.gls(locale, "access_denied"), inline=True)
            embed.add_field(name=generic.gls(locale, "verification_level"), inline=True, value=generic.gls(locale, str(ctx.guild.verification_level)))
            embed.add_field(name=generic.gls(locale, "channels"), inline=True,
                            value=generic.gls(locale, "channels2", [len(ctx.guild.text_channels), len(ctx.guild.categories), len(ctx.guild.voice_channels)]))
            embed.add_field(name=generic.gls(locale, "boosts"), inline=True,
                            value=generic.gls(locale, "boosts2", [ctx.guild.premium_subscription_count, ctx.guild.premium_tier,
                                                                  len(ctx.guild.premium_subscribers)]))
            ani_emotes = len([emote for emote in ctx.guild.emojis if emote.animated])
            total_emotes = len(ctx.guild.emojis)
            embed.add_field(name=generic.gls(locale, "emotes"), inline=True,
                            value=generic.gls(locale, "emotes2", [ctx.guild.emoji_limit, ani_emotes, total_emotes - ani_emotes, total_emotes]))
            # value=f"{len(ctx.guild.text_channels)} text channels\n"
            #       f"{len(ctx.guild.categories)} categories\n"
            #       f"{len(ctx.guild.voice_channels)} voice channels")
            embed.add_field(name=generic.gls(locale, "created_at"), inline=False,  # value=generic.gls(locale, "server_ca"))
                            value=f"{time.time_output(ctx.guild.created_at)} - "
                                  f"{time.human_timedelta(ctx.guild.created_at)}")
            return await generic.send(None, ctx.channel, embed=embed)
            # return await ctx.send(f"About **{ctx.guild.name}**", embed=embed)

    @server.command(name="icon", aliases=["avatar"])
    async def server_icon(self, ctx: commands.Context):
        """ Get server icon """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "server"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        return await generic.send(generic.gls(locale, "server_icon", [ctx.guild.name, ctx.guild.icon_url_as(size=1024, static_format="png")]), ctx.channel)
        # return await ctx.send(f"Icon of **{ctx.guild.name}**:\n{ctx.guild.icon_url_as(size=1024)}")

    @server.command(name="banner")
    async def server_banner(self, ctx: commands.Context):
        """ Get server banner """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "server"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        link = ctx.guild.banner_url_as(size=4096, format="png")
        if link:
            return await generic.send(generic.gls(locale, "server_banner", [ctx.guild.name, link]), ctx.channel)
        else:
            return await generic.send(generic.gls(locale, "server_banner_none", [ctx.guild.name]), ctx.channel)
        # return await generic.send(generic.gls(locale, "server_banner", [ctx.guild.name, ctx.guild.banner_url_as(size=4096, format="png")]), ctx.channel)
        # return await ctx.send(f"Icon of **{ctx.guild.name}**:\n{ctx.guild.icon_url_as(size=1024)}")

    @server.command(name="invite", aliases=["splash"])
    async def server_invite(self, ctx: commands.Context):
        """ Get server invite splash """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "server"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        link = ctx.guild.splash_url_as(size=4096, format="png")
        if link:
            return await generic.send(generic.gls(locale, "server_splash", [ctx.guild.name, link]), ctx.channel)
        else:
            return await generic.send(generic.gls(locale, "server_splash_none", [ctx.guild.name]), ctx.channel)
        # return await ctx.send(f"Icon of **{ctx.guild.name}**:\n{ctx.guild.icon_url_as(size=1024)}")

    @server.command(name="bots")
    async def server_bots(self, ctx: commands.Context):
        """ Bots in servers """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "server"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        bots = [a for a in ctx.guild.members if a.bot]
        m = ''
        for i in range(len(bots)):
            n = str(i+1) if i >= 9 else f"0{i+1}"
            m += f"[{n}] {bots[i]}\n"
        return await generic.send(generic.gls(locale, "bots_in_server", [ctx.guild.name, m]), ctx.channel)
        # return await ctx.send(f"Bots in **{ctx.guild.name}**: ```ini\n{m}```")

    @server.command(name="status")
    async def server_status(self, ctx: commands.Context):
        """ Server status """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "server"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        so, si, sd, sn = 0, 0, 0, 0
        mo, mi, md, do, di, dd, wo, wi, wd = 0, 0, 0, 0, 0, 0, 0, 0, 0
        al, ag, at, ac, an = 0, 0, 0, 0, 0
        m = 0
        for member in ctx.guild.members:
            m += 1
            s, s1, s2, s3 = member.status, member.mobile_status, member.desktop_status, member.web_status
            if s == discord.Status.online:
                so += 1
            if s1 == discord.Status.online:
                mo += 1
            if s2 == discord.Status.online:
                do += 1
            if s3 == discord.Status.online:
                wo += 1
            if s == discord.Status.idle:
                si += 1
            if s1 == discord.Status.idle:
                mi += 1
            if s2 == discord.Status.idle:
                di += 1
            if s3 == discord.Status.idle:
                wi += 1
            if s == discord.Status.dnd:
                sd += 1
            if s1 == discord.Status.dnd:
                md += 1
            if s2 == discord.Status.dnd:
                dd += 1
            if s3 == discord.Status.dnd:
                wd += 1
            if s == discord.Status.offline:
                sn += 1
            else:
                activities = list(member.activities)
                if not activities:
                    an += 1
                else:
                    for a in activities:
                        if a.type == discord.ActivityType.custom:
                            ac += 1
                        if a.type == discord.ActivityType.streaming:
                            at += 1
                        if a.type == discord.ActivityType.playing:
                            ag += 1
                        if a.type == discord.ActivityType.listening:
                            al += 1
        embed = discord.Embed(colour=generic.random_colour(), description=generic.gls(locale, "status_of_users", [ctx.guild.name]))
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(name=generic.gls(locale, "total_members"), value=f"{m:,}", inline=False)
        e1, e2, e3, e4 = "<:online:679052892514287635>", "<:idle:679052892828598303>", "<:dnd:679052892782723114> ", \
                         "<:offline:679052892782592033>"
        a1, a2, a3, a4, a5 = "🎮", "<:streaming:679055367346323478>", "<:listening:679055367396917250> ", \
                             "<:pikathink:674330001151229963>", "<:awoogoodnight:613410343359873054>"
        po, pi, pd, pn = so / m * 100, si / m * 100, sd / m * 100, sn / m * 100
        embed.add_field(name=generic.gls(locale, "status"), inline=False,
                        value=generic.gls(locale, "status2", [e1, f"{so:,}", f"{po:.2f}", f"{mo:,}", f"{do:,}", f"{wo:,}", e2, f"{si:,}",
                                                              f"{pi:.2f}", f"{mi:,}", f"{di:,}", f"{wi:,}", e3, f"{sd:,}", f"{pd:.2f}", f"{md:,}",
                                                              f"{dd:,}", f"{wd:,}", e4, f"{sn:,}", f"{pn:.2f}"]))
        # embed.add_field(name="Status", inline=False, value=f"{e1} Online: {so:,} - {po:.2f}%, of which:\n"
        #                                                    f"Mobile: {mo:,} | Desktop: {do:,} | Web: {wo:,}\n\n"
        #                                                    f"{e2} Idle: {si:,} - {pi:.2f}%, of which:\n"
        #                                                    f"Mobile: {mi:,} | Desktop: {di:,} | Web: {wi:,}\n\n"
        #                                                    f"{e3} Dungeons and Dragons: {sd:,} - {pd:.2f}%, of which:\n"
        #                                                    f"Mobile: {md:,} | Desktop: {dd:,} | Web: {wd:,}\n\n"
        #                                                    f"{e4} Offline: {sn:,} - {pn:.2f}%")
        o = m - sn
        apg, apt, apl, apc, apn = ag / o * 100, at / o * 100, al / o * 100, ac / o * 100, an / o * 100
        embed.add_field(name=generic.gls(locale, "activities"), inline=False,
                        value=generic.gls(locale, "activities2", [f"{o:,}", a1, f"{ag:,}", f"{apg:.2f}", a4, f"{ac:,}", f"{apc:.2f}", a2, f"{at:,}",
                                                                  f"{apt:.2f}", a3, f"{al:,}", f"{apl:.2f}", a5, f"{an:,}", f"{apn:.2f}"]))
        # embed.add_field(name="Activities", inline=False, value=f"Out of {o:,} people online:\n"
        #                                                        f"{a1} Playing a game: {ag:,} - {apg:.2f}%\n"
        #                                                        f"{a4} Playing Custom Status: {ac:,} - {apc:.2f}%\n"
        #                                                        f"{a2} Streaming: {at:,} - {apt:.2f}%\n"
        #                                                        f"{a3} Listening: {al:,} - {apl:.2f}%\n"
        #                                                        f"{a5} Doing nothing: {an:,} - {apn:.2f}%")
        # return await ctx.send(embed=embed)
        return await generic.send(None, ctx.channel, embed=embed)

    @commands.command(name="prefix")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def prefix(self, ctx: commands.Context):
        """ Server prefixes """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "prefix"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        if ctx.channel.id in generic.channel_locks:
            return await generic.send(generic.gls(locale, "channel_locked"), ctx.channel)
        _data = self.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (ctx.guild.id,))
        # _data = self.db.fetchrow(f"SELECT * FROM data_{self.type} WHERE type=? AND id=?", ("settings", ctx.guild.id))
        if not _data:
            dp = generic.get_config()["prefixes"]
            cp = None
            dp.append(self.bot.user.mention)
        else:
            data = json.loads(_data['data'])
            dp = generic.get_config()["prefixes"] if data['use_default'] else []
            cp = data['prefixes']
            dp.append(self.bot.user.mention)
        embed = discord.Embed(colour=generic.random_colour())
        embed.title = generic.gls(locale, "server_prefixes", [ctx.guild.name])
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(name=generic.gls(locale, "default_prefixes"), value='\n'.join(dp), inline=True)
        if cp is not None and cp != []:
            embed.add_field(name=generic.gls(locale, "custom_prefixes"), value='\n'.join(cp), inline=True)
        return await generic.send(None, ctx.channel, embed=embed)
        # return await ctx.send(f"Prefixes for {ctx.guild.name}", embed=embed)


def setup(bot):
    bot.add_cog(Discord(bot))
