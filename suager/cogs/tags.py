import asyncio
from math import ceil

import discord
from discord.ext import commands

from core.utils import general, permissions, time
from languages import langs


class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="tag", aliases=["tags", "t"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def tags(self, ctx: commands.Context, *, tag_name: str):
        """ Tags """
        if ctx.invoked_subcommand is None:
            tag = self.bot.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
            if tag:
                self.bot.db.execute("UPDATE tags SET usage=usage+1 WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
                return await general.send(tag["content"], ctx.channel)
            else:
                locale = langs.gl(ctx)
                return await general.send(langs.gls("tags_not_found", locale, tag_name.lower()), ctx.channel)

    @tags.command(name="create")
    async def create_tag(self, ctx: commands.Context, tag_name: str, *, content: str):
        """ Create a new tag """
        locale = langs.gl(ctx)
        tag = self.bot.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if tag:
            return await general.send(langs.gls("tags_create_already", locale, tag_name.lower()), ctx.channel)
        self.bot.db.fetchrow("INSERT INTO tags VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                             (ctx.guild.id, ctx.author.id, ctx.author.id, tag_name.lower(), content, int(time.now_ts()), int(time.now_ts()), 0))
        return await general.send(langs.gls("tags_create_success", locale, tag_name.lower(), ctx.author.name), ctx.channel)

    async def get_user(self, guild: discord.Guild, uid: int, locale: str) -> str:
        user = guild.get_member(uid)
        return str(user) if user is not None else str(await self.bot.fetch_user(uid)) + f" | {langs.gls('tags_user_guild', locale)}"

    @tags.command(name="info")
    async def tag_info(self, ctx: commands.Context, *, tag_name: str):
        """ See info about a tag """
        locale = langs.gl(ctx)
        tag = self.bot.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await general.send(langs.gls("tags_not_found", locale, tag_name.lower()), ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        g = ctx.guild
        embed.description = langs.gls("tags_info_data", locale, tag["name"], langs.gns(tag["usage"], locale), await self.get_user(g, tag["owner"], locale),
                                      await self.get_user(g, tag["creator"], locale), langs.gts(time.from_ts(tag["created"]), locale),
                                      langs.gts(time.from_ts(tag["edited"]), locale))
        c = tag["content"]
        if len(c) > 1024:
            c = f"{c[:1021]}..."
        embed.add_field(name=langs.gls("tags_info_content", locale), value=c)
        return await general.send(langs.gls("tags_info_about", locale, tag["name"]), ctx.channel, embed=embed)

    @tags.command(name="delete", aliases=["del"])
    async def delete_tag(self, ctx: commands.Context, *, tag_name: str):
        """ Delete a tag """
        locale = langs.gl(ctx)
        tag = self.bot.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await general.send(langs.gls("tags_not_found", locale, tag_name.lower()), ctx.channel)

        def check_confirm(m):
            if m.author == ctx.author and m.channel == ctx.channel:
                if m.content.startswith("yes"):
                    return True
            return False
        if tag["owner"] == ctx.author.id or (await permissions.check_permissions(ctx, perms={'kick_members': True})):
            confirm_msg = await general.send(langs.gls("tags_delete_confirm", locale, ctx.author.name, tag["name"]), ctx.channel)
            try:
                await self.bot.wait_for('message', timeout=30.0, check=check_confirm)
            except asyncio.TimeoutError:
                return await confirm_msg.edit(content=langs.gls("generic_timed_out", locale, confirm_msg.clean_content))
            self.bot.db.execute("DELETE FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag['name']))
            return await general.send(langs.gls("tags_delete_success", locale, tag["name"]), ctx.channel)
        else:
            return await general.send(langs.gls("tags_delete_deny", locale), ctx.channel)

    @tags.command(name="edit")
    async def edit_tag(self, ctx: commands.Context, tag_name: str, *, new_content: str):
        """ Edit a tag """
        locale = langs.gl(ctx)
        tag = self.bot.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await general.send(langs.gls("tags_not_found", locale, tag_name.lower()), ctx.channel)
        if tag["owner"] != ctx.author.id:
            return await general.send(langs.gls("tags_edit_deny", locale), ctx.channel)
        else:
            self.bot.db.execute("UPDATE tags SET content=?, edited=? WHERE gid=? AND name=?", (new_content, int(time.now_ts()), ctx.guild.id, tag_name.lower()))
            return await general.send(langs.gls("tags_edit_success", locale, tag["name"]), ctx.channel)

    @tags.command(name="rename")
    async def rename_tag(self, ctx: commands.Context, tag_name: str, *, new_name: str):
        """ Rename a tag """
        locale = langs.gl(ctx)
        tag = self.bot.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await general.send(langs.gls("tags_not_found", locale, tag_name.lower()), ctx.channel)
        _tag = self.bot.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, new_name.lower()))
        if _tag:
            return await general.send(langs.gls("tags_rename_already", locale, new_name.lower()), ctx.channel)
        if tag["owner"] != ctx.author.id:
            return await general.send(langs.gls("tags_rename_deny", locale), ctx.channel)
        else:
            self.bot.db.execute("UPDATE tags SET name=?, edited=? WHERE gid=? AND name=?", (new_name.lower(), int(time.now_ts()), ctx.guild.id, tag['name']))
            return await general.send(langs.gls("tags_rename_success", locale, tag["name"], new_name.lower()), ctx.channel)

    @tags.command(name="transfer")
    async def transfer_tag(self, ctx: commands.Context, tag_name: str, *, user: discord.Member):
        """ Transfer your tag to someone else """
        locale = langs.gl(ctx)
        tag = self.bot.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await general.send(langs.gls("tags_not_found", locale, tag_name.lower()), ctx.channel)
        if tag["owner"] != ctx.author.id:
            return await general.send(langs.gls("tags_transfer_deny", locale), ctx.channel)
        else:
            self.bot.db.execute("UPDATE tags SET owner=? WHERE gid=? AND name=?", (user.id, ctx.guild.id, tag_name.lower()))
            return await general.send(langs.gls("tags_transfer_success", locale, tag["name"], user), ctx.channel)

    @tags.command(name="claim")
    async def claim_tag(self, ctx: commands.Context, *, tag_name: str):
        """ Claim a tag of a user who left the server """
        locale = langs.gl(ctx)
        tag = self.bot.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await general.send(langs.gls("tags_not_found", locale, tag_name.lower()), ctx.channel)
        if tag["owner"] == ctx.author.id:
            return await general.send(langs.gls("tags_claim_owned", locale), ctx.channel)
        elif tag["owner"] in [u.id for u in ctx.guild.members]:
            return await general.send(langs.gls("tags_claim_server", locale), ctx.channel)
        else:
            self.bot.db.execute("UPDATE tags SET owner=? WHERE gid=? AND name=?", (ctx.author.id, ctx.guild.id, tag["name"]))
            return await general.send(langs.gls("tags_claim_success", locale, ctx.author.name, tag["name"]), ctx.channel)

    @tags.command(name="user")
    async def tags_user(self, ctx: commands.Context, who: discord.Member = None, page: int = 1):
        """ See someone's tags """
        locale = langs.gl(ctx)
        user = who or ctx.author
        tags = self.bot.db.fetch("SELECT * FROM tags WHERE owner=? AND gid=? ORDER BY name", (user.id, ctx.guild.id))
        if not tags:
            return await general.send(langs.gls("tags_user_none", locale, user.name), ctx.channel)
        block = "```fix"
        for i, d in enumerate(tags[(page - 1) * 20:page * 20], start=(page - 1) * 20 + 1):
            block += f"\n{langs.gns(i, locale, 2, False)}) {d['name']} | {langs.plural(d['usage'], 'tags_list_uses', locale)}"
        return await general.send(langs.gls("tags_user", locale, user, langs.gns(page, locale), langs.gns(ceil(len(tags) / 20), locale), block), ctx.channel)

    @tags.command(name="all")
    async def tags_all(self, ctx: commands.Context, page: int = 1):
        """ See all tags sorted alphabetically """
        locale = langs.gl(ctx)
        tags = self.bot.db.fetch("SELECT * FROM tags WHERE gid=? ORDER BY name", (ctx.guild.id,))
        if not tags:
            return await general.send(langs.gls("tags_list_none", locale, ctx.guild.name), ctx.channel)
        block = "```fix"
        for i, d in enumerate(tags[(page - 1) * 20:page * 20], start=(page - 1) * 20 + 1):
            block += f"\n{langs.gns(i, locale, 2, False)}) {d['name']} | {langs.plural(d['usage'], 'tags_list_uses', locale)}"
        return await general.send(langs.gls("tags_all", locale, ctx.guild, langs.gns(page, locale), langs.gns(ceil(len(tags) / 20), locale), block),
                                  ctx.channel)

    @tags.command(name="top")
    async def tags_top(self, ctx: commands.Context, page: int = 1):
        """ See all tags sorted by usage """
        locale = langs.gl(ctx)
        tags = self.bot.db.fetch("SELECT * FROM tags WHERE gid=? ORDER BY usage DESC", (ctx.guild.id,))
        if not tags:
            return await general.send(langs.gls("tags_list_none", locale, ctx.guild.name), ctx.channel)
        block = "```fix"
        for i, d in enumerate(tags[(page - 1) * 20:page * 20], start=(page - 1) * 20 + 1):
            block += f"\n{langs.gns(i, locale, 2, False)}) {d['name']} | {langs.plural(d['usage'], 'tags_list_uses', locale)}"
        return await general.send(langs.gls("tags_top", locale, ctx.guild, langs.gns(page, locale), langs.gns(ceil(len(tags) / 20), locale), block),
                                  ctx.channel)


def setup(bot):
    bot.add_cog(Tags(bot))
