import asyncio
from math import ceil

import discord
from discord.ext import commands

from cobble.utils import ss23, tbl
from core.utils import general
from languages import langs


def tbl_locale(ctx: commands.Context):
    locale = langs.gl(ctx)
    if not locale.startswith("rsl") and ctx.channel.id not in [725835449502924901, 742885168997466196, 610482988123422750]:  # SR8 and my command channels
        locale = "rsl-1e"  # if locale is not an RSL, force it to be RSL-1
    return locale


def invite_send_allowed(ctx: commands.Context):
    player = tbl.Player.from_db(ctx.author, ctx.guild)
    clan = player.clan
    if not clan:
        return False
    if clan.type == 2:
        return ctx.author.id == clan.owner
    return True


def is_clan_owner(ctx: commands.Context):
    player = tbl.Player.from_db(ctx.author, ctx.guild)
    clan = player.clan
    if not clan:
        return False
    return ctx.author.id == clan.owner


class Kuastall(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="tbl")
    # @commands.max_concurrency(1, per=commands.BucketType.guild, wait=True)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def tbl(self, ctx: commands.Context):
        """ Teampall na Bylkan'de Liidenvirkallde """
        # RSL-1e: Tenval na Bylkan'dar Laikännvurkalu
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))
            # locale = tbl_locale(ctx)
            # return await general.send(langs.gls("placeholder", locale), ctx.channel)

    @tbl.command(name="run", aliases=["play", "p", "r"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def tbl_run(self, ctx: commands.Context):
        """ Koar TBL'a """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        return await player.play(ctx, locale, None)

    @tbl.command(name="beginning", aliases=["explanation", "define", "definition", "explain"])
    async def tbl_beginning(self, ctx: commands.Context):
        """ What TBL is """
        locale = tbl_locale(ctx)
        return await general.send(langs.gls("kuastall_tbl_beginning", locale), ctx.channel)

    @tbl.command(name="leveling")
    @commands.is_owner()
    async def tbl_levels(self, ctx: commands.Context):
        """ See how TBL levels work """
        __levels = [2, 3, 5, 10, 15, 20, 30, 40, 50, 60, 75, 85, 100, 125, 150, 175, 200, 225, 250]
        outputs = []
        for level in __levels:
            _level = level - 1
            lv1 = tbl.player_levels[_level] if level <= tbl.player_max else -1
            lv2 = tbl.shaman_levels[_level] if level <= tbl.shaman_max else -1
            lv3 = tbl.guild_levels[_level] if level <= tbl.guild_max else -1
            lv4 = tbl.clan_levels[_level] if level <= tbl.clan_max else -1
            # lv1 = int(levels[_level])
            # diff = lv1 - int(levels[_level - 1]) if level > 1 else lv1
            outputs.append(f"Level {level:>3} | Player {lv1:>10,} | Shaman {lv2:>10,} | Guild {lv3:>11,} | Clan {lv4:>11,}")
        output = "\n".join(outputs)
        # print(len(output))
        return await general.send(f"```fix\n{output}```", ctx.channel)

    @tbl.command(name="time")
    async def tbl_time(self, ctx: commands.Context):
        """ TBL Time """
        return await general.send(ss23.date_kargadia(tz=2, tzn="TBT"), ctx.channel)

    @tbl.command(name="stats", aliases=["s"])
    async def tbl_stats(self, ctx: commands.Context, who: discord.User = None):
        """ Check yours or someone else's TBL stats """
        locale = tbl_locale(ctx)
        user = who or ctx.author
        player = tbl.Player.from_db(user, ctx.guild)
        embed = player.status(locale, user.avatar_url)
        return await general.send(None, ctx.channel, embed=embed)

    @tbl.group(name="invites", aliases=["invite", "i"])
    async def tbl_invites(self, ctx: commands.Context):
        """ Check your invites """
        locale = tbl_locale(ctx)
        invites = tbl.Invite.from_db_user(ctx.author.id)
        if not invites:
            return await general.send(langs.gls("kuastall_tbl_invites_none", locale, ctx.author.name), ctx.channel)
        output = []
        types = langs.get_data("kuastall_tbl_invite_type", locale)
        for invite in invites:
            user = self.bot.get_user(invite.user_id)
            clan = tbl.Clan.from_db(invite.clan_id)
            name = clan.name if clan is not None else "Clan not found"
            inv_type = types[invite.type]
            output.append(langs.gls("kuastall_tbl_invite", locale, user, name, inv_type, invite.id))
        return await general.send(langs.gls("kuastall_tbl_invites", locale, ctx.author, "\n\n".join(output)), ctx.channel)

    @tbl_invites.command(name="accept", aliases=["a"])
    async def tbl_pi_accept(self, ctx: commands.Context, invite_id: int):
        """ Accept an invite """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if player.level < 7:
            return await general.send(langs.gls("kuastall_tbl_clan_player_lvl", locale), ctx.channel)
        clan = player.clan
        if clan:
            return await general.send(langs.gls("kuastall_tbl_clan_already", locale), ctx.channel)
        invite = tbl.Invite.from_db_id(invite_id)
        if not invite:
            return await general.send(langs.gls("kuastall_tbl_invite_not_found", locale, invite_id), ctx.channel)
        if invite.type == 0:
            return await general.send(langs.gls("kuastall_tbl_invite_forbidden4", locale), ctx.channel)
        invite.accept()
        user = self.bot.get_user(invite.user_id)
        return await general.send(langs.gls("kuastall_tbl_invite_accepted", locale, user), ctx.channel)

    @tbl_invites.command(name="reject", aliases=["r", "cancel", "c"])
    async def tbl_pi_reject(self, ctx: commands.Context, invite_id: int):
        """ Reject/cancel an invite """
        locale = tbl_locale(ctx)
        invite = tbl.Invite.from_db_id(invite_id)
        if not invite:
            return await general.send(langs.gls("kuastall_tbl_invite_not_found", locale, invite_id), ctx.channel)
        invite.delete()
        return await general.send(langs.gls("kuastall_tbl_invite_rejected", locale, invite_id), ctx.channel)

    @tbl.group(name="clan", aliases=["c"])
    async def tbl_clan(self, ctx: commands.Context):
        """ TBL Clan related commands """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @tbl_clan.command(name="stats")
    async def tbl_clan_stats(self, ctx: commands.Context, clan_id: int = None):
        """ TBL Clan stats """
        locale = tbl_locale(ctx)
        if clan_id:
            clan = tbl.Clan.from_db(clan_id)
        else:
            player = tbl.Player.from_db(ctx.author, ctx.guild)
            clan = player.clan
        if not clan:
            return await general.send(langs.gls("kuastall_tbl_clan_none", locale), ctx.channel)
        embed = clan.status(ctx, locale)
        return await general.send(None, ctx.channel, embed=embed)

    @tbl_clan.group(name="invites", aliases=["invite", "i"])
    async def tbl_clan_invites(self, ctx: commands.Context):
        """ Interact with the clan invites """
        if ctx.invoked_subcommand is None:
            locale = tbl_locale(ctx)
            player = tbl.Player.from_db(ctx.author, ctx.guild)
            clan = player.clan
            if not clan:
                return await general.send(langs.gls("kuastall_tbl_clan_none", locale), ctx.channel)
            if ctx.author.id == clan.owner:
                invites = tbl.Invite.from_db_clan(clan.id)
                if not invites:
                    return await general.send(langs.gls("kuastall_tbl_invites_none", locale, clan.name), ctx.channel)
                output = []
                types = langs.get_data("kuastall_tbl_invite_type2", locale)
                for invite in invites:
                    user = self.bot.get_user(invite.user_id)
                    clan = tbl.Clan.from_db(invite.clan_id)
                    name = clan.name if clan is not None else "Clan not found"
                    inv_type = types[invite.type]
                    output.append(langs.gls("kuastall_tbl_invite", locale, user, name, inv_type, invite.id))
                return await general.send(langs.gls("kuastall_tbl_invites", locale, clan.name, "\n\n".join(output)), ctx.channel)
            return await general.send(langs.gls("kuastall_tbl_invite_forbidden2", locale), ctx.channel)

    @tbl_clan_invites.command(name="send")
    @commands.check(invite_send_allowed)
    async def tbl_ci_send(self, ctx: commands.Context, user: discord.User):
        """ Send someone an invite to your clan """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        clan = player.clan
        if not clan:
            return await general.send(langs.gls("kuastall_tbl_clan_none", locale), ctx.channel)
        invite = tbl.Invite.from_db(user.id, clan.id)
        if invite:
            if clan.type == 1 and ctx.author.id == clan.owner:  # Invite-only clan owned by the author
                if invite.type == 0:  # There is an incoming invite by the user to join the clan
                    accept = invite.accept()
                    return await general.send(langs.gls("kuastall_tbl_invite_send_accept", locale, accept), ctx.channel)
            if invite.type == 1:
                return await general.send(langs.gls("kuastall_tbl_invite_already", locale), ctx.channel)
        is_allowed = True
        if clan.type == 2:
            is_allowed = ctx.author.id == clan.owner
        if not is_allowed:
            return await general.send(langs.gls("kuastall_tbl_invite_forbidden", locale), ctx.channel)
        invite = tbl.Invite.new(user.id, clan.id, 1)
        invite.save()
        try:
            await user.send(f"[TBL] You have been invited by {ctx.author} to join the clan {clan.name}\n"
                            f"To accept: `..tbl invite accept {invite.id}`\nTo reject: `..tbl invite reject {invite.id}`")
            sent = True
        except discord.Forbidden:
            sent = False
        output = langs.gls("kuastall_tbl_invite_dm" if sent else "kuastall_tbl_invite_dm2", locale)
        return await general.send(langs.gls("kuastall_tbl_invite_sent", locale, user, output), ctx.channel)

    @tbl_clan_invites.command(name="accept", aliases=["a"])
    @commands.check(is_clan_owner)
    async def tbl_ci_accept(self, ctx: commands.Context, invite_id: int):
        """ Accept an invite """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        clan = player.clan
        if not clan:
            return await general.send(langs.gls("kuastall_tbl_clan_none", locale), ctx.channel)
        if ctx.author.id != clan.owner:
            return await general.send(langs.gls("kuastall_tbl_invite_forbidden3", locale), ctx.channel)
        invite = tbl.Invite.from_db_id(invite_id)
        if not invite:
            return await general.send(langs.gls("kuastall_tbl_invite_not_found", locale, invite_id), ctx.channel)
        if invite.clan_id != clan.id:
            return await general.send(langs.gls("kuastall_tbl_invite_forbidden5", locale), ctx.channel)
        if invite.type == 1:
            return await general.send(langs.gls("kuastall_tbl_invite_forbidden4", locale), ctx.channel)
        invite.accept()
        user = self.bot.get_user(invite.user_id)
        return await general.send(langs.gls("kuastall_tbl_invite_accepted", locale, user), ctx.channel)

    @tbl_clan_invites.command(name="reject", aliases=["r", "cancel", "c"])
    @commands.check(is_clan_owner)
    async def tbl_ci_reject(self, ctx: commands.Context, invite_id: int):
        """ Reject/cancel an invite """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        clan = player.clan
        if not clan:
            return await general.send(langs.gls("kuastall_tbl_clan_none", locale), ctx.channel)
        if ctx.author.id != clan.owner:
            return await general.send(langs.gls("kuastall_tbl_invite_forbidden3", locale), ctx.channel)
        invite = tbl.Invite.from_db_id(invite_id)
        if not invite:
            return await general.send(langs.gls("kuastall_tbl_invite_not_found", locale, invite_id), ctx.channel)
        invite.delete()
        return await general.send(langs.gls("kuastall_tbl_invite_rejected", locale, invite_id), ctx.channel)

    @tbl_clan.command(name="create")
    async def tbl_clan_create(self, ctx: commands.Context, *, name: str):
        """ Create a new Clan """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if player.clan is not None:
            return await general.send(langs.gls("kuastall_tbl_clan_already", locale), ctx.channel)
        if player.level < 7:
            return await general.send(langs.gls("kuastall_tbl_clan_player_lvl", locale), ctx.channel)
        types = langs.get_data("kuastall_tbl_clan_types", locale)
        output = "\n".join([f"`{i}` = {v}" for i, v in enumerate(types)])
        # await general.send(langs.gls("kuastall_tbl_clan_type2", locale, output), ctx.channel)
        message = await general.send(langs.gls("kuastall_tbl_clan_create_type", locale, output), ctx.channel)
        invite_type = 0

        def check_confirm(m):
            if m.author == ctx.author and m.channel == ctx.channel:
                if int(m.content) in [0, 1, 2]:
                    nonlocal invite_type
                    invite_type = int(m.content)
                    return True
            return False
        try:
            await self.bot.wait_for('message', timeout=30.0, check=check_confirm)
        except asyncio.TimeoutError:
            return await message.edit(content=langs.gls("generic_timed_out", locale, message.clean_content))
        invite = types[invite_type]
        message = await general.send(langs.gls("kuastall_tbl_clan_create_confirm", locale, ctx.author, name, invite), ctx.channel)

        def check_confirm(m):
            if m.author == ctx.author and m.channel == ctx.channel:
                if m.content == "yes":
                    return True
            return False
        try:
            await self.bot.wait_for('message', timeout=30.0, check=check_confirm)
        except asyncio.TimeoutError:
            return await message.edit(content=langs.gls("generic_timed_out", locale, message.clean_content))
        clan = tbl.Clan.new(name, invite_type[0], ctx.author.id)
        player.clan = clan
        player.save()
        return await general.send(langs.gls("kuastall_tbl_clan_create", locale, name, ctx.author), ctx.channel)

    @tbl_clan.command(name="members")
    @commands.check(is_clan_owner)
    async def tbl_clan_members(self, ctx: commands.Context, page: int = 1):
        """ Lists all clan members """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        clan = player.clan
        if not clan:
            return await general.send(langs.gls("kuastall_tbl_clan_none", locale), ctx.channel)
        if ctx.author.id != clan.owner:
            return await general.send(langs.gls("kuastall_tbl_clan_members_forbidden", locale), ctx.channel)
        members_data = self.bot.db.fetch("SELECT * FROM tbl_player WHERE clan=?", (clan.id,))
        members = [f"{member['name']}#{member['disc']}" for member in members_data]
        members.sort(key=lambda x: x.lower())
        if page < 1:
            page = 1
        _data = members[(page - 1) * 20:page * 20]
        start = page * 20 - 19
        output = langs.gls("kuastall_tbl_clan_members_list", locale, clan.name, langs.gns(page, locale), langs.gns(ceil(len(members) / 20), locale))
        output += " ```fix\n"
        for i, d in enumerate(_data, start=start):
            output += f"{langs.gns(i, locale, 2, False)}){' '*4}{d}\n"
        output += "```"
        return await general.send(output, ctx.channel)

    @tbl_clan.command(name="join")
    async def tbl_clan_join(self, ctx: commands.Context, clan_id: int):
        """ Join a clan """
        return await general.send("Placeholder", ctx.channel)

    @tbl_clan.command(name="search")
    async def tbl_clan_search(self, ctx: commands.Context, *, name: str):
        """ Search for a clan with a specific name """
        return await general.send("Placeholder", ctx.channel)

    @tbl.group(name="guild", aliases=["g", "server"])
    async def tbl_guild(self, ctx: commands.Context):
        """ TBL Guild related commands """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @tbl_guild.command(name="stats")
    async def tbl_guild_stats(self, ctx: commands.Context, guild_id: int = None):
        """ TBL Guild stats """
        locale = tbl_locale(ctx)
        server = self.bot.get_guild(guild_id) if guild_id else ctx.guild
        if not server:
            return await general.send("Guild not found", ctx.channel)
        guild = tbl.Guild.from_db(server)
        embed = guild.status(locale, server.icon_url)
        return await general.send(None, ctx.channel, embed=embed)

    @tbl.command(name="locations", aliases=["location", "loc", "l"])
    async def tbl_locations(self, ctx: commands.Context, location_id: int = None):
        """ TBL Locations """
        locale = tbl_locale(ctx)
        if location_id is None or location_id not in range(1, len(tbl.locations) + 1):
            names = langs.get_data("kuastall_tbl_locations", locale)
            output = []
            for i, location in enumerate(tbl.locations):
                output.append(langs.gls("kuastall_tbl_location_list2", locale, location.id, names[i], location.level_req))
            return await general.send(langs.gls("kuastall_tbl_location_list", locale, "\n".join(output)), ctx.channel)
        location = tbl.locations[location_id - 1]
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        embed = location.status(locale, player.level)
        return await general.send(None, ctx.channel, embed=embed)

    # TODO: clan join/leave
    # TODO: clan search
    # TODO: donate coins to clan/guild
    # TODO: clan locations and playing on them
    # TODO: use shaman feathers
    # TODO: use clan upgrade points
    # TODO: use guild coins
    # TODO: Challenge Renewal system
    # TODO: translations into Russian and RSL-1e ("kuastall_*")


def setup(bot):
    bot.add_cog(Kuastall(bot))
