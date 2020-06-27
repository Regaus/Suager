import asyncio

import discord
from discord.ext import commands

from utils import generic, database, time, permissions


class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database()
        self.invalid_names = ["reagus", "reggie", "regoose", "reegaus", "reguas", "regigigas", "suwuager", "suwu", "regauwus", "register"]
        self.invalid_names2 = ["regaus", "suager", "регаус", "reg"]

    @commands.group(name="tag", aliases=["tags", "t"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def tags(self, ctx: commands.Context, *, tag_name: str):
        """ Tags """
        if ctx.invoked_subcommand is None:
            locale = generic.get_lang(ctx.guild)
            if generic.is_locked(ctx.guild, "tag"):
                return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
            tag = self.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
            if tag:
                self.db.execute("UPDATE tags SET usage=? WHERE gid=? AND name=?", (tag["usage"] + 1, ctx.guild.id, tag_name.lower()))
                return await generic.send(tag["content"], ctx.channel)
            else:
                return await generic.send(generic.gls(locale, "tag_not_found", [tag_name.lower()]), ctx.channel)

    @tags.command(name="create")
    async def create_tag(self, ctx: commands.Context, tag_name: str, *, content: str):
        """ Create a new tag """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "tag"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        tag = self.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if tag:
            return await generic.send(generic.gls(locale, "tag_already_exists", [tag_name.lower()]), ctx.channel)
        if (tag_name.lower() in self.invalid_names2 and ctx.author.id != 302851022790066185) or tag_name.lower() in self.invalid_names:
            return await generic.send(generic.gls(locale, "tag_name_invalid", [ctx.author.name]), ctx.channel)
        self.db.fetchrow("INSERT INTO tags VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                         (ctx.guild.id, ctx.author.id, ctx.author.id, tag_name.lower(), content, time.now_ts(), time.now_ts(), 0))
        return await generic.send(generic.gls(locale, "tag_created", [tag_name.lower(), ctx.author.name]), ctx.channel)

    def get_user(self, guild: discord.Guild, uid: int) -> str:
        try:
            return str([user for user in guild.members if user.id == uid][0])
        except IndexError:
            locale = generic.get_lang(guild)
            try:
                return str([user for user in self.bot.users if user.id == uid][0]) + generic.gls(locale, "user_not_in_guild")
            except IndexError:
                return str(uid) + generic.gls(locale, "user_not_in_guild")

    @tags.command(name="info")
    async def tag_info(self, ctx: commands.Context, *, tag_name: str):
        """ See info about a tag """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "tag"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        tag = self.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await generic.send(generic.gls(locale, "tag_not_found", [tag_name.lower()]), ctx.channel)
        embed = discord.Embed(colour=generic.random_colour())
        g = ctx.guild
        embed.description = generic.gls(locale, "tag_info", [tag["name"], tag["usage"], self.get_user(g, tag["owner"]), self.get_user(g, tag["creator"]),
                                                             time.time_output(time.from_ts(tag["created"])), time.time_output(time.from_ts(tag["edited"]))])
        embed.add_field(name=generic.gls(locale, "tag_content"), value=tag["content"])
        return await generic.send(generic.gls(locale, "tag_info2", [tag["name"]]), ctx.channel, embed=embed)

    @tags.command(name="delete", aliases=["del"])
    async def delete_tag(self, ctx: commands.Context, *, tag_name: str):
        """ Delete a tag """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "tag"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        tag = self.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await generic.send(generic.gls(locale, "tag_not_found", [tag_name.lower()]), ctx.channel)

        def check_confirm(m):
            if m.author == ctx.author and m.channel == ctx.channel:
                if m.content.startswith("yes"):
                    return True
                if m.content.startswith("да"):
                    return True
            return False
        if tag["owner"] == ctx.author.id or (await permissions.check_permissions(ctx, perms={'kick_members': True})):
            confirm_msg = await generic.send(generic.gls(locale, "tag_del_confirm", [ctx.author.name, tag["name"]]), ctx.channel)
            try:
                await self.bot.wait_for('message', timeout=30.0, check=check_confirm)
            except asyncio.TimeoutError:
                content = generic.gls(locale, "tag_del_cancel")
                return await confirm_msg.edit(content=content)
            self.db.execute("DELETE FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
            return await generic.send(generic.gls(locale, "tag_deleted", [ctx.author.name, tag["name"]]), ctx.channel)
        else:
            return await generic.send(generic.gls(locale, "tag_del_deny", [ctx.author.name]), ctx.channel)

    @tags.command(name="edit")
    async def edit_tag(self, ctx: commands.Context, tag_name: str, *, new_content: str):
        """ Edit a tag """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "tag"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        tag = self.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await generic.send(generic.gls(locale, "tag_not_found", [tag_name.lower()]), ctx.channel)
        if tag["owner"] != ctx.author.id:
            return await generic.send(generic.gls(locale, "tag_edit_deny", [ctx.author.name]), ctx.channel)
        else:
            self.db.execute("UPDATE tags SET content=?, edited=? WHERE gid=? AND name=?", (new_content, time.now_ts(), ctx.guild.id, tag_name.lower()))
            return await generic.send(generic.gls(locale, "tag_edited", [ctx.author.name, tag["name"]]), ctx.channel)

    @tags.command(name="rename")
    async def rename_tag(self, ctx: commands.Context, tag_name: str, *, new_name: str):
        """ Rename a tag """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "tag"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        tag = self.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if (new_name.lower() in self.invalid_names2 and ctx.author.id != 302851022790066185) or new_name.lower() in self.invalid_names:
            return await generic.send(generic.gls(locale, "tag_name_invalid", [ctx.author.name]), ctx.channel)
        if not tag:
            return await generic.send(generic.gls(locale, "tag_not_found", [tag_name.lower()]), ctx.channel)
        _tag = self.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, new_name.lower()))
        if _tag:
            return await generic.send(generic.gls(locale, "tag_already_exists", [new_name.lower()]), ctx.channel)
        if tag["owner"] != ctx.author.id:
            return await generic.send(generic.gls(locale, "tag_rename_deny", [ctx.author.name]), ctx.channel)
        else:
            self.db.execute("UPDATE tags SET name=?, edited=? WHERE gid=? AND name=?", (new_name.lower(), time.now_ts(), ctx.guild.id, tag_name.lower()))
            return await generic.send(generic.gls(locale, "tag_renamed", [ctx.author.name, tag["name"], new_name.lower()]), ctx.channel)

    @tags.command(name="transfer")
    async def transfer_tag(self, ctx: commands.Context, tag_name: str, *, user: discord.Member):
        """ Transfer your tag to someone else """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "tag"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        tag = self.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await generic.send(generic.gls(locale, "tag_not_found", [tag_name.lower()]), ctx.channel)
        if tag["owner"] != ctx.author.id:
            return await generic.send(generic.gls(locale, "tag_transfer_deny", [ctx.author.name]), ctx.channel)
        else:
            self.db.execute("UPDATE tags SET owner=? WHERE gid=? AND name=?", (user.id, ctx.guild.id, tag_name.lower()))
            return await generic.send(generic.gls(locale, "tag_transferred", [ctx.author.name, tag["name"], user]), ctx.channel)

    @tags.command(name="claim")
    async def claim_tag(self, ctx: commands.Context, *, tag_name: str):
        """ Claim a tag """
        locale = generic.get_lang(ctx.guild)
        if generic.is_locked(ctx.guild, "tag"):
            return await generic.send(generic.gls(locale, "server_locked"), ctx.channel)
        tag = self.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await generic.send(generic.gls(locale, "tag_not_found", [tag_name.lower()]), ctx.channel)
        if tag["owner"] == ctx.author.id:
            return await generic.send(generic.gls(locale, "tag_claim_own", [ctx.author.name]), ctx.channel)
        elif tag["owner"] in [u.id for u in ctx.guild.members]:
            return await generic.send(generic.gls(locale, "tag_claim_deny", [ctx.author.name]), ctx.channel)
        else:
            self.db.execute("UPDATE tags SET owner=? WHERE gid=? AND name=?", (ctx.author.id, ctx.guild.id, tag["name"]))
            return await generic.send(generic.gls(locale, "tag_claimed", [ctx.author.name, tag["name"]]), ctx.channel)


def setup(bot):
    bot.add_cog(Tags(bot))
