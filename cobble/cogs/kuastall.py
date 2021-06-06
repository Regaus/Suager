import asyncio
from math import ceil

import discord
from discord.ext import commands

from cobble.utils import conworlds, tbl
from core.utils import general, permissions, time
from languages import langs


def tbl_locale(ctx: commands.Context, default: str = "rsl-1i"):
    locale = langs.gl(ctx)
    if langs.get_data("_conlang", locale) is False and ctx.channel.id not in [725835449502924901, 742885168997466196, 610482988123422750]:
        locale = default
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
    @commands.guild_only()
    @commands.check(lambda ctx: ctx.author.id in [302851022790066185, 517012611573743621])  # Temporarily lock TBL while it's not finished
    # @commands.max_concurrency(1, per=commands.BucketType.guild, wait=True)
    # @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def tbl(self, ctx: commands.Context):
        """ Teampall na Bylkan'de Liidenvirkallde """
        # RSL-1e: Tenval na Bylkan'dar Laikännvurkalu
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))
            # locale = tbl_locale(ctx)
            # return await general.send(langs.gls("placeholder", locale), ctx.channel)

    @tbl.command(name="run", aliases=["play", "p", "r"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=True)
    async def tbl_run(self, ctx: commands.Context):
        """ Koar TBL'a """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        return await player.play(ctx, locale, None)

    # @tbl.command(name="beginning", aliases=["explanation", "define", "definition", "explain"])
    # async def tbl_beginning(self, ctx: commands.Context):
    #     """ What TBL is """
    #     locale = tbl_locale(ctx)
    #     return await general.send(langs.gls("kuastall_tbl_beginning", locale), ctx.channel)

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
        return await general.send(conworlds.time_kargadia(tz=-7).str(dow=True, era=None, month=False), ctx.channel)
        # return await general.send(ss23.date_kargadia(tz=2, tzn="TBT"), ctx.channel)

    @tbl.command(name="stats", aliases=["s"])
    async def tbl_stats(self, ctx: commands.Context, who: discord.User = None):
        """ Check yours or someone else's TBL stats """
        locale = tbl_locale(ctx)
        user = who or ctx.author
        player = tbl.Player.from_db(user, ctx.guild)
        embed = player.status(locale, user.avatar_url_as(size=1024))
        return await general.send(None, ctx.channel, embed=embed)

    @tbl.group(name="shaman", aliases=["sh"])
    async def tbl_shaman(self, ctx: commands.Context):
        """ Interact with your Shaman skills """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(str(ctx.command))

    @tbl_shaman.command(name="convert", aliases=["c"])
    async def tbl_sh_convert(self, ctx: commands.Context, coins: int):
        """ Convert your Player Coins into Shaman Feathers (1 Coin -> 2 Feathers) """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if coins < 1:
            return await general.send(langs.gls("kuastall_tbl_donate_negative", locale), ctx.channel)
        if player.coins < coins:
            return await general.send(langs.gls("kuastall_tbl_donate_balance", locale, langs.plural(player.coins, "kuastall_tbl_pl_coins", locale)), ctx.channel)
        player.coins -= coins
        player.shaman_feathers += coins * 2
        player.save()
        # r1, r2 = langs.gns(coins, locale), langs.gfs(coins * 2, locale, 1)
        r1, r2 = langs.plural(coins, "kuastall_tbl_pl_coins", locale), langs.plural(coins * 2, "kuastall_tbl_pl_shaman_feathers", locale)
        return await general.send(langs.gls("kuastall_tbl_donate3", locale, r1, r2), ctx.channel)

    @tbl_shaman.command(name="probability", aliases=["p"])
    async def tbl_sh_probability(self, ctx: commands.Context, levels: int = 1):
        """ Upgrade your Shaman Probability """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if levels < 1:
            return await general.send(langs.gls("kuastall_tbl_upgrade_negative", locale), ctx.channel)
        if player.shaman_feathers < levels:
            return await general.send(langs.gls("kuastall_tbl_upgrade_balance", locale,
                                                langs.plural(player.shaman_feathers, "kuastall_tbl_pl_shaman_feathers", locale)), ctx.channel)
        max_level = 64
        reached = False
        if player.shaman_probability_level + levels > max_level:
            levels = max_level - player.shaman_probability_level
            reached = True
        player.shaman_feathers -= levels
        player.shaman_probability_level += levels
        player.save()
        r1, r2, r3 = langs.plural(levels, "generic_times", locale), langs.gns(player.shaman_probability_level, locale), langs.gns(max_level, locale)
        r4 = langs.gls("kuastall_tbl_upgrade_max", locale) if reached else ""
        return await general.send(langs.gls("kuastall_tbl_upgrade_shaman_probability", locale, r1, r2, r3, r4), ctx.channel)

    @tbl_shaman.command(name="xp")
    async def tbl_sh_xp_boost(self, ctx: commands.Context, levels: int = 1):
        """ Upgrade your Shaman XP Boost """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if levels < 1:
            return await general.send(langs.gls("kuastall_tbl_upgrade_negative", locale), ctx.channel)
        if player.shaman_feathers < levels:
            return await general.send(langs.gls("kuastall_tbl_upgrade_balance", locale,
                                                langs.plural(player.shaman_feathers, "kuastall_tbl_pl_shaman_feathers", locale)), ctx.channel)
        max_level = 75
        reached = False
        if player.shaman_xp_boost_level + levels > max_level:
            levels = max_level - player.shaman_xp_boost_level
            reached = True
        player.shaman_feathers -= levels
        player.shaman_xp_boost_level += levels
        player.save()
        r1, r2, r3 = langs.plural(levels, "generic_times", locale), langs.gns(player.shaman_xp_boost_level, locale), langs.gns(max_level, locale)
        r4 = langs.gls("kuastall_tbl_upgrade_max", locale) if reached else ""
        return await general.send(langs.gls("kuastall_tbl_upgrade_shaman_xp", locale, r1, r2, r3, r4), ctx.channel)

    @tbl_shaman.command(name="saves")
    async def tbl_sh_saves(self, ctx: commands.Context, levels: int = 1):
        """ Upgrade your Shaman Saves Boost """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if levels < 1:
            return await general.send(langs.gls("kuastall_tbl_upgrade_negative", locale), ctx.channel)
        if player.shaman_feathers < levels:
            return await general.send(langs.gls("kuastall_tbl_upgrade_balance", locale,
                                                langs.plural(player.shaman_feathers, "kuastall_tbl_pl_shaman_feathers", locale)), ctx.channel)
        max_level = 100
        reached = False
        if player.shaman_save_boost_level + levels > max_level:
            levels = max_level - player.shaman_save_boost_level
            reached = True
        player.shaman_feathers -= levels
        player.shaman_save_boost_level += levels
        player.save()
        r1, r2, r3 = langs.plural(levels, "generic_times", locale), langs.gns(player.shaman_save_boost_level, locale), langs.gns(max_level, locale)
        r4 = langs.gls("kuastall_tbl_upgrade_max", locale) if reached else ""
        return await general.send(langs.gls("kuastall_tbl_upgrade_shaman_saves", locale, r1, r2, r3, r4), ctx.channel)

    @tbl.group(name="invites", aliases=["invite", "i"])
    async def tbl_invites(self, ctx: commands.Context):
        """ Check your invites """
        if ctx.invoked_subcommand is None:
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
        if invite.user_id != ctx.author.id:
            return await general.send(langs.gls("kuastall_tbl_invite_forbidden5", locale), ctx.channel)
        invite.accept()
        # user = self.bot.get_user(invite.user_id)
        clan = tbl.Clan.from_db(invite.clan_id).name
        return await general.send(langs.gls("kuastall_tbl_clan_join_success", locale, clan), ctx.channel)

    @tbl_invites.command(name="reject", aliases=["r", "cancel", "c"])
    async def tbl_pi_reject(self, ctx: commands.Context, invite_id: int):
        """ Reject/cancel an invite """
        locale = tbl_locale(ctx)
        invite = tbl.Invite.from_db_id(invite_id)
        if not invite:
            return await general.send(langs.gls("kuastall_tbl_invite_not_found", locale, invite_id), ctx.channel)
        if invite.user_id != ctx.author.id:
            return await general.send(langs.gls("kuastall_tbl_invite_forbidden5", locale), ctx.channel)
        invite.delete()
        return await general.send(langs.gls("kuastall_tbl_invite_rejected", locale, invite_id), ctx.channel)

    @tbl.group(name="clan", aliases=["c"])
    async def tbl_clan(self, ctx: commands.Context):
        """ Interact with TBL Clans """
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
        # try:
        #     await user.send(f"[TBL] You have been invited by {ctx.author} to join the clan {clan.name}\n"
        #                     f"To accept: `..tbl invite accept {invite.id}`\nTo reject: `..tbl invite reject {invite.id}`")
        #     sent = True
        # except discord.Forbidden:
        #     sent = False
        # output = langs.gls("kuastall_tbl_invite_dm" if sent else "kuastall_tbl_invite_dm2", locale)
        return await general.send(langs.gls("kuastall_tbl_invite_sent", locale, user), ctx.channel)

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
        if invite.clan_id != clan.id:
            return await general.send(langs.gls("kuastall_tbl_invite_forbidden5", locale), ctx.channel)
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
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if player.level < 7:
            return await general.send(langs.gls("kuastall_tbl_clan_player_lvl", locale), ctx.channel)
        if player.clan:
            return await general.send(langs.gls("kuastall_tbl_clan_already", locale), ctx.channel)
        clan = tbl.Clan.from_db(clan_id)
        if not clan:
            return await general.send(langs.gls("kuastall_tbl_clan_none2", locale, clan_id), ctx.channel)
        if clan.type == 0:
            player.clan = clan
            player.save()
            return await general.send(langs.gls("kuastall_tbl_clan_join_success", locale, clan.name), ctx.channel)
        if clan.type == 1:
            invite = tbl.Invite.from_db(ctx.author.id, clan.id)
            if invite:
                if invite.type == 1:
                    work = invite.accept()
                    if work:
                        return await general.send(langs.gls("kuastall_tbl_clan_join_success", locale, clan.name), ctx.channel)
                    else:
                        return await general.send(langs.gls("kuastall_tbl_clan_join_failure", locale, clan.name), ctx.channel)
            invite = tbl.Invite.new(ctx.author.id, clan.id, 0)
            invite.save()
            # owner = self.bot.get_user(clan.owner)
            # try:
            #     await owner.send(f"[TBL] {ctx.author} has asked to join your clan {clan.name}\n"
            #                      f"To accept: `..tbl invite accept {invite.id}`\nTo reject: `..tbl invite reject {invite.id}`")
            return await general.send(langs.gls("kuastall_tbl_clan_join_invite", locale, clan.name), ctx.channel)
            # except discord.Forbidden:
            #     return await general.send(langs.gls("kuastall_tbl_clan_join_invite2", locale, clan.name), ctx.channel)
        if clan.type == 2:
            return await general.send(langs.gls("kuastall_tbl_clan_join_forbidden", locale, clan.name), ctx.channel)

    @tbl_clan.command(name="leave")
    async def tbl_clan_leave(self, ctx: commands.Context):
        """ Leave your clan """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if not player.clan:
            return await general.send(langs.gls("kuastall_tbl_clan_none3", locale), ctx.channel)
        if player.clan.owner == ctx.author.id:
            return await general.send(langs.gls("kuastall_tbl_clan_leave_forbidden", locale), ctx.channel)
        player.clan = None
        player.save()
        return await general.send(langs.gls("kuastall_tbl_clan_leave", locale), ctx.channel)

    @tbl_clan.command(name="delete")
    @commands.check(is_clan_owner)
    async def tbl_clan_delete(self, ctx: commands.Context):
        """ Delete the clan """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if not player.clan:
            return await general.send(langs.gls("kuastall_tbl_clan_none3", locale), ctx.channel)
        if player.clan.owner != ctx.author.id:
            return await general.send(langs.gls("kuastall_tbl_clan_delete_forbidden", locale), ctx.channel)
        message = await general.send(langs.gls("kuastall_tbl_clan_delete_confirm", locale, player.clan.name), ctx.channel)

        def check_confirm(m):
            if m.author == ctx.author and m.channel == ctx.channel:
                if m.content == "yes":
                    return True
            return False
        try:
            await self.bot.wait_for('message', timeout=30.0, check=check_confirm)
        except asyncio.TimeoutError:
            return await message.edit(content=langs.gls("generic_timed_out", locale, message.clean_content))

        invites = tbl.Invite.from_db_clan(player.clan.id)
        for invite in invites:
            invite.delete()
        self.bot.db.execute("UPDATE tbl_player SET clan=? WHERE clan=?", (None, player.clan.id))
        self.bot.db.execute("DELETE FROM tbl_clan WHERE clan_id=?", (player.clan.id,))
        return await general.send(langs.gls("kuastall_tbl_clan_delete", locale, player.clan.name), ctx.channel)

    @tbl_clan.command(name="transfer")
    @commands.check(is_clan_owner)
    async def tbl_clan_transfer(self, ctx: commands.Context, user: discord.User):
        """ Transfer the ownership of your clan to someone else """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if not player.clan:
            return await general.send(langs.gls("kuastall_tbl_clan_none3", locale), ctx.channel)
        if player.clan.owner != ctx.author.id:
            return await general.send(langs.gls("kuastall_tbl_clan_transfer_forbidden", locale), ctx.channel)
        player2 = tbl.Player.from_db(user, ctx.guild)
        if not player2.clan or player.clan.id != player2.clan.id:
            return await general.send(langs.gls("kuastall_tbl_clan_transfer_same", locale, user), ctx.channel)
        message = await general.send(langs.gls("kuastall_tbl_clan_transfer_confirm", locale, player.clan.name, user), ctx.channel)

        def check_confirm(m):
            if m.author == ctx.author and m.channel == ctx.channel:
                if m.content == "yes":
                    return True
            return False
        try:
            await self.bot.wait_for('message', timeout=30.0, check=check_confirm)
        except asyncio.TimeoutError:
            return await message.edit(content=langs.gls("generic_timed_out", locale, message.clean_content))

        player.clan.owner = user.id
        player.clan.save()
        return await general.send(langs.gls("kuastall_tbl_clan_transfer", locale, user, player.clan.name), ctx.channel)

    @tbl_clan.command(name="donate", aliases=["contribute"])
    async def tbl_clan_donate(self, ctx: commands.Context, coins: int):
        """ Donate some of your Coins to the clan (5 Player Coins -> 1 Upgrade Point) """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if not player.clan:
            return await general.send(langs.gls("kuastall_tbl_clan_none3", locale), ctx.channel)
        if coins < 1:
            return await general.send(langs.gls("kuastall_tbl_donate_negative", locale), ctx.channel)
        if player.coins < coins:
            return await general.send(langs.gls("kuastall_tbl_donate_balance", locale, langs.plural(player.coins, "kuastall_tbl_pl_coins", locale)), ctx.channel)
        player.coins -= coins
        player.clan.points += coins / 5
        player.save()
        # r1, r2 = langs.gns(coins, locale), langs.gfs(coins / 5, locale, 1)
        r1, r2 = langs.plural(coins, "kuastall_tbl_pl_coins", locale), langs.plural(coins / 5, "kuastall_tbl_pl_upgrade_points", locale, 1)
        return await general.send(langs.gls("kuastall_tbl_donate", locale, r1, r2, player.clan.name), ctx.channel)

    @tbl_clan.group(name="locations")
    async def tbl_clan_locations(self, ctx: commands.Context):
        """ Clan Locations """
        if ctx.invoked_subcommand is None:
            return await general.send(langs.gls("kuastall_tbl_clan_locations_help", tbl_locale(ctx)), ctx.channel)

    @tbl_clan_locations.command(name="buy")
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=True)
    async def tbl_clan_loc_buy(self, ctx: commands.Context, location_id: int):
        """ Buy a Clan Location """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if not player.clan:
            return await general.send(langs.gls("kuastall_tbl_clan_none3", locale), ctx.channel)
        if location_id < 1 or location_id > len(tbl.locations):
            return await general.send(langs.gls("kuastall_tbl_clan_locations_buy_id", locale), ctx.channel)
        location = tbl.locations[location_id - 1]
        if location.level_req > player.level:
            return await general.send(langs.gls("kuastall_tbl_clan_locations_buy_level", locale, langs.gns(location.level_req, locale)), ctx.channel)
        location_name = langs.get_data("kuastall_tbl_locations", locale)[location_id - 1]
        locations_active = [location for location in player.clan.locations if location["expiry"] > time.now_ts()]
        lids = [location["id"] for location in locations_active]
        index = -1
        if location_id in lids:
            index = lids.index(location_id)
            cost = 1000 * (2 ** index)
            current = True
        else:
            active = len(locations_active)
            cost = 1000 * (2 ** active)
            current = False
        if ctx.author.id == player.clan.owner:
            if player.clan.araksat > cost:
                cost_clan, cost_player = cost, 0
                confirmation = langs.gls("kuastall_tbl_clan_locations_buy_confirm", locale, location_name, langs.plural(cost_clan, "kuastall_tbl_pl_araksat_clan", locale))
            else:
                cost_clan = int(player.clan.araksat)
                cost_player = cost - cost_clan
                # r1, r2 = langs.gns(cost_clan, locale), langs.gns(cost_player, locale)
                r1, r2 = langs.plural(cost_clan, "kuastall_tbl_pl_araksat_clan", locale), langs.plural(cost_player, "kuastall_tbl_pl_araksat_player", locale)
                confirmation = langs.gls("kuastall_tbl_clan_locations_buy_confirm2", locale, location_name, r1, r2)
        else:
            cost_clan, cost_player = 0, cost
            confirmation = langs.gls("kuastall_tbl_clan_locations_buy_confirm3", locale, location_name, langs.plural(cost_player, "kuastall_tbl_pl_araksat_player", locale))
        if player.araksat < cost_player:
            return await general.send(langs.gls("kuastall_tbl_clan_locations_buy_player", locale), ctx.channel)
        message = await general.send(confirmation, ctx.channel)

        def check_confirm(m):
            if m.author == ctx.author and m.channel == ctx.channel:
                if m.content == "yes":
                    return True
            return False
        try:
            await self.bot.wait_for('message', timeout=30.0, check=check_confirm)
        except asyncio.TimeoutError:
            return await message.edit(content=langs.gls("generic_timed_out", locale, message.clean_content))

        expiry = locations_active[index]["expiry"] + 86400 if current else time.now_ts() + 86400
        expires = langs.gts(time.from_ts(expiry, None), locale, seconds=True)
        if current:
            locations_active[index]["expiry"] = expiry
        else:
            locations_active.append({"id": location_id, "expiry": expiry})
        player.araksat -= cost_player
        player.clan.araksat -= cost_clan
        player.clan.locations = locations_active
        player.save()
        return await general.send(langs.gls("kuastall_tbl_clan_locations_buy_success", locale, location_name, expires), ctx.channel)

    @tbl_clan_locations.command(name="play", aliases=["p"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=True)
    async def tbl_clan_loc_play(self, ctx: commands.Context, location_id: int):
        """ Play TBL on a Clan Location """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if not player.clan:
            return await general.send(langs.gls("kuastall_tbl_clan_none3", locale), ctx.channel)
        if location_id < 1 or location_id > len(tbl.locations):
            return await general.send(langs.gls("kuastall_tbl_clan_locations_buy_id", locale), ctx.channel)
        exists = False
        for location in player.clan.locations:
            if location["id"] == location_id:
                if location["expiry"] > time.now_ts():
                    exists = True
        if not exists:
            return await general.send(langs.gls("kuastall_tbl_clan_locations_unavailable", locale), ctx.channel)
        return await player.play(ctx, locale, tbl.locations[location_id - 1])

    @tbl_clan_locations.command(name="refund", aliases=["r", "return", "remove"])
    @commands.check(is_clan_owner)
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=True)
    async def tbl_clan_loc_refund(self, ctx: commands.Context, location_id: int):
        """ Refund a Clan Location """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if not player.clan:
            return await general.send(langs.gls("kuastall_tbl_clan_none3", locale), ctx.channel)
        if location_id < 1 or location_id > len(tbl.locations):
            return await general.send(langs.gls("kuastall_tbl_clan_locations_buy_id", locale), ctx.channel)
        if player.clan.owner != ctx.author.id:
            return await general.send(langs.gls("kuastall_tbl_clan_locations_refund_forbidden", locale), ctx.channel)
        exists = False
        index = -1
        locations = []
        for location in player.clan.locations:
            if location["expiry"] > time.now_ts():
                locations.append(location)
                if location["id"] == location_id:
                    exists = True
                    index = locations.index(location)
        if not exists:
            return await general.send(langs.gls("kuastall_tbl_clan_locations_unavailable", locale), ctx.channel)

        location_name = langs.get_data("kuastall_tbl_locations", locale)[location_id - 1]
        expiry = locations[index]["expiry"] - time.now_ts()
        days = expiry / 86400  # How many days the location had left
        cost = 850 * (2 ** index) * days  # Refunded cost (15% lost)
        r1 = langs.td_int(int(expiry), locale, 3, True, True, False)
        # r2 = langs.gns(cost, locale)
        r2 = langs.plural(cost, "kuastall_tbl_pl_araksat", locale)
        message = await general.send(langs.gls("kuastall_tbl_clan_locations_refund_confirm", locale, location_name, r1, r2), ctx.channel)

        def check_confirm(m):
            if m.author == ctx.author and m.channel == ctx.channel:
                if m.content == "yes":
                    return True
            return False
        try:
            await self.bot.wait_for('message', timeout=30.0, check=check_confirm)
        except asyncio.TimeoutError:
            return await message.edit(content=langs.gls("generic_timed_out", locale, message.clean_content))

        locations.pop(index)
        player.clan.araksat += cost
        player.clan.locations = locations
        player.save()
        return await general.send(langs.gls("kuastall_tbl_clan_locations_refund_success", locale, location_name, r2), ctx.channel)

    @tbl_clan.command(name="taxgain", aliases=["tax", "tg", "t"])
    @commands.check(is_clan_owner)
    async def tbl_clan_tax(self, ctx: commands.Context, levels: int = 1):
        """ Upgrade the Clan's Tax Gain """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if not player.clan:
            return await general.send(langs.gls("kuastall_tbl_clan_none3", locale), ctx.channel)
        if player.clan.owner != ctx.author.id:
            return await general.send(langs.gls("kuastall_tbl_upgrade_forbidden", locale), ctx.channel)
        if levels < 1:
            return await general.send(langs.gls("kuastall_tbl_upgrade_negative", locale), ctx.channel)
        if player.clan.points < levels:
            return await general.send(langs.gls("kuastall_tbl_upgrade_balance", locale, langs.plural(player.clan.points, "kuastall_tbl_pl_upgrade_points", locale)), ctx.channel)
        max_level = 225
        reached = False
        if player.clan.tax_gain_level + levels > max_level:
            levels = max_level - player.clan.tax_gain_level
            reached = True
        player.clan.points -= levels
        player.clan.tax_gain_level += levels
        player.save()
        r1, r2, r3 = langs.plural(levels, "generic_times", locale), langs.gns(player.clan.tax_gain_level, locale), langs.gns(max_level, locale)
        r4 = langs.gls("kuastall_tbl_upgrade_max", locale) if reached else ""
        return await general.send(langs.gls("kuastall_tbl_upgrade_clan_tax", locale, r1, r2, r3, r4), ctx.channel)

    @tbl_clan.command(name="rewards", aliases=["reward", "rb"])
    @commands.check(is_clan_owner)
    async def tbl_clan_rewards(self, ctx: commands.Context, levels: int = 1):
        """ Upgrade the Clan's Reward Boost """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if not player.clan:
            return await general.send(langs.gls("kuastall_tbl_clan_none3", locale), ctx.channel)
        if player.clan.owner != ctx.author.id:
            return await general.send(langs.gls("kuastall_tbl_upgrade_forbidden", locale), ctx.channel)
        if levels < 1:
            return await general.send(langs.gls("kuastall_tbl_upgrade_negative", locale), ctx.channel)
        if player.clan.points < levels:
            return await general.send(langs.gls("kuastall_tbl_upgrade_balance", locale, langs.plural(player.clan.points, "kuastall_tbl_pl_upgrade_points", locale)), ctx.channel)
        max_level = 200
        reached = False
        if player.clan.reward_boost_level + levels > max_level:
            levels = max_level - player.clan.reward_boost_level
            reached = True
        player.clan.points -= levels
        player.clan.reward_boost_level += levels
        player.save()
        r1, r2, r3 = langs.plural(levels, "generic_times", locale), langs.gns(player.clan.reward_boost_level, locale), langs.gns(max_level, locale)
        r4 = langs.gls("kuastall_tbl_upgrade_max", locale) if reached else ""
        return await general.send(langs.gls("kuastall_tbl_upgrade_clan_reward", locale, r1, r2, r3, r4), ctx.channel)

    @tbl_clan.command(name="energylimit", aliases=["limit", "elb", "el"])
    @commands.check(is_clan_owner)
    async def tbl_clan_elb(self, ctx: commands.Context, levels: int = 1):
        """ Upgrade the Clan's Energy Limit Boost """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if not player.clan:
            return await general.send(langs.gls("kuastall_tbl_clan_none3", locale), ctx.channel)
        if player.clan.owner != ctx.author.id:
            return await general.send(langs.gls("kuastall_tbl_upgrade_forbidden", locale), ctx.channel)
        if levels < 1:
            return await general.send(langs.gls("kuastall_tbl_upgrade_negative", locale), ctx.channel)
        if player.clan.points < levels:
            return await general.send(langs.gls("kuastall_tbl_upgrade_balance", locale, langs.plural(player.clan.points, "kuastall_tbl_pl_upgrade_points", locale)), ctx.channel)
        max_level = 250
        reached = False
        if player.clan.energy_limit_boost_level + levels > max_level:
            levels = max_level - player.clan.energy_limit_boost_level
            reached = True
        player.clan.points -= levels
        player.clan.energy_limit_boost_level += levels
        player.save()
        r1, r2, r3 = langs.plural(levels, "generic_times", locale), langs.gns(player.clan.energy_limit_boost_level, locale), langs.gns(max_level, locale)
        r4 = langs.gls("kuastall_tbl_upgrade_max", locale) if reached else ""
        return await general.send(langs.gls("kuastall_tbl_upgrade_clan_elb", locale, r1, r2, r3, r4), ctx.channel)

    @tbl_clan.command(name="energyregen", aliases=["regen", "erb", "er"])
    @commands.check(is_clan_owner)
    async def tbl_clan_erb(self, ctx: commands.Context, levels: int = 1):
        """ Upgrade the Clan's Energy Regen Boost """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if not player.clan:
            return await general.send(langs.gls("kuastall_tbl_clan_none3", locale), ctx.channel)
        if player.clan.owner != ctx.author.id:
            return await general.send(langs.gls("kuastall_tbl_upgrade_forbidden", locale), ctx.channel)
        if levels < 1:
            return await general.send(langs.gls("kuastall_tbl_upgrade_negative", locale), ctx.channel)
        if player.clan.points < levels:
            return await general.send(langs.gls("kuastall_tbl_upgrade_balance", locale, langs.plural(player.clan.points, "kuastall_tbl_pl_upgrade_points", locale)), ctx.channel)
        max_level = 150
        reached = False
        if player.clan.energy_regen_boost_level + levels > max_level:
            levels = max_level - player.clan.energy_regen_boost_level
            reached = True
        player.clan.points -= levels
        player.clan.energy_regen_boost_level += levels
        player.save()
        r1, r2, r3 = langs.plural(levels, "generic_times", locale), langs.gns(player.clan.energy_regen_boost_level, locale), langs.gns(max_level, locale)
        r4 = langs.gls("kuastall_tbl_upgrade_max", locale) if reached else ""
        return await general.send(langs.gls("kuastall_tbl_upgrade_clan_erb", locale, r1, r2, r3, r4), ctx.channel)

    @tbl.group(name="guild", aliases=["g", "server"])
    async def tbl_guild(self, ctx: commands.Context):
        """ Interact with TBL Guilds """
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
        embed = guild.status(locale, server.icon_url_as(size=1024))
        return await general.send(None, ctx.channel, embed=embed)

    @tbl_guild.command(name="donate", aliases=["contribute"])
    async def tbl_guild_donate(self, ctx: commands.Context, coins: int):
        """ Donate some of your Coins to the guild (10 Player Coins -> 1 Guild Coin) """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if coins < 1:
            return await general.send(langs.gls("kuastall_tbl_donate_negative", locale), ctx.channel)
        if player.coins < coins:
            return await general.send(langs.gls("kuastall_tbl_donate_balance", locale, langs.plural(player.coins, "kuastall_tbl_pl_coins", locale)), ctx.channel)
        player.coins -= coins
        player.guild.coins += coins / 10
        player.save()
        # r1, r2 = langs.gns(coins, locale), langs.gfs(coins / 10, locale, 1)
        r1, r2 = langs.plural(coins, "kuastall_tbl_pl_coins", locale), langs.plural(coins / 10, "kuastall_tbl_pl_guild_coins", locale, 1)
        return await general.send(langs.gls("kuastall_tbl_donate2", locale, r1, r2, player.guild.name), ctx.channel)

    @tbl_guild.command(name="araksatboost", aliases=["araksat", "ab"])
    @permissions.has_permissions(administrator=True)
    async def tbl_guild_araksat(self, ctx: commands.Context, levels: int = 1):
        """ Upgrade the Guild's Araksat Boost """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if levels < 1:
            return await general.send(langs.gls("kuastall_tbl_upgrade_negative", locale), ctx.channel)
        if player.guild.coins < levels:
            return await general.send(langs.gls("kuastall_tbl_upgrade_balance", locale, langs.plural(player.guild.coins, "kuastall_tbl_pl_guild_coins", locale)), ctx.channel)
        max_level = 150
        reached = False
        if player.guild.araksat_boost_level + levels > max_level:
            levels = max_level - player.guild.araksat_boost_level
            reached = True
        player.guild.coins -= levels
        player.guild.araksat_boost_level += levels
        player.save()
        r1, r2, r3 = langs.plural(levels, "generic_times", locale), langs.gns(player.guild.araksat_boost_level, locale), langs.gns(max_level, locale)
        r4 = langs.gls("kuastall_tbl_upgrade_max", locale) if reached else ""
        return await general.send(langs.gls("kuastall_tbl_upgrade_guild_araksat", locale, r1, r2, r3, r4), ctx.channel)

    @tbl_guild.command(name="xpboost", aliases=["xp"])
    @permissions.has_permissions(administrator=True)
    async def tbl_guild_xp(self, ctx: commands.Context, levels: int = 1):
        """ Upgrade the Guild's XP Boost """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if levels < 1:
            return await general.send(langs.gls("kuastall_tbl_upgrade_negative", locale), ctx.channel)
        if player.guild.coins < levels:
            return await general.send(langs.gls("kuastall_tbl_upgrade_balance", locale, langs.plural(player.guild.coins, "kuastall_tbl_pl_guild_coins", locale)), ctx.channel)
        max_level = 150
        reached = False
        if player.guild.xp_boost_level + levels > max_level:
            levels = max_level - player.guild.xp_boost_level
            reached = True
        player.guild.coins -= levels
        player.guild.xp_boost_level += levels
        player.save()
        r1, r2, r3 = langs.plural(levels, "generic_times", locale), langs.gns(player.guild.xp_boost_level, locale), langs.gns(max_level, locale)
        r4 = langs.gls("kuastall_tbl_upgrade_max", locale) if reached else ""
        return await general.send(langs.gls("kuastall_tbl_upgrade_guild_xp", locale, r1, r2, r3, r4), ctx.channel)

    @tbl_guild.command(name="energy")
    @permissions.has_permissions(administrator=True)
    async def tbl_guild_energy(self, ctx: commands.Context, levels: int = 1):
        """ Upgrade the Guild's Round Energy Cost Boost """
        locale = tbl_locale(ctx)
        player = tbl.Player.from_db(ctx.author, ctx.guild)
        if levels < 1:
            return await general.send(langs.gls("kuastall_tbl_upgrade_negative", locale), ctx.channel)
        if player.guild.coins < levels:
            return await general.send(langs.gls("kuastall_tbl_upgrade_balance", locale, langs.plural(player.guild.coins, "kuastall_tbl_pl_guild_coins", locale)), ctx.channel)
        max_level = 50
        reached = False
        if player.guild.energy_reduction_level + levels > max_level:
            levels = max_level - player.guild.energy_reduction_level
            reached = True
        player.guild.coins -= levels
        player.guild.energy_reduction_level += levels
        player.save()
        r1, r2, r3 = langs.plural(levels, "generic_times", locale), langs.gns(player.guild.energy_reduction_level, locale), langs.gns(max_level, locale)
        r4 = langs.gls("kuastall_tbl_upgrade_max", locale) if reached else ""
        return await general.send(langs.gls("kuastall_tbl_upgrade_guild_energy", locale, r1, r2, r3, r4), ctx.channel)

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

    # TODO: use clan upgrade points
    # TODO: use guild coins
    # TODO: translations into Russian and RSL-1e ("kuastall_*")


def setup(bot):
    bot.add_cog(Kuastall(bot))
