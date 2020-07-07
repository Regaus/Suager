import asyncio

import discord
from discord.ext import commands

from core.utils import general, database, time, permissions


class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database(self.bot.name)

    @commands.group(name="tag", aliases=["tags", "t"], invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def tags(self, ctx: commands.Context, *, tag_name: str):
        """ Tags """
        if ctx.invoked_subcommand is None:
            tag = self.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
            if tag:
                self.db.execute("UPDATE tags SET usage=? WHERE gid=? AND name=?", (tag["usage"] + 1, ctx.guild.id, tag_name.lower()))
                return await general.send(tag["content"], ctx.channel)
            else:
                return await general.send(f"There is no tag named `{tag_name.lower()}`", ctx.channel)

    @tags.command(name="create")
    async def create_tag(self, ctx: commands.Context, tag_name: str, *, content: str):
        """ Create a new tag """
        tag = self.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if tag:
            return await general.send(f"Tag `{tag_name.lower()}` already exists", ctx.channel)
        self.db.fetchrow("INSERT INTO tags VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                         (ctx.guild.id, ctx.author.id, ctx.author.id, tag_name.lower(), content, time.now_ts(), time.now_ts(), 0))
        return await general.send(f"Your tag `{tag_name.lower()}` has been successfully created, {ctx.author.name}.", ctx.channel)

    def get_user(self, guild: discord.Guild, uid: int) -> str:
        try:
            return str([user for user in guild.members if user.id == uid][0])
        except IndexError:
            no = " | User is no longer in this server"
            try:
                return str([user for user in self.bot.users if user.id == uid][0]) + no
            except IndexError:
                return str(uid) + no

    @tags.command(name="info")
    async def tag_info(self, ctx: commands.Context, *, tag_name: str):
        """ See info about a tag """
        tag = self.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await general.send(f"There is no tag named `{tag_name.lower()}`", ctx.channel)
        embed = discord.Embed(colour=general.random_colour())
        g = ctx.guild
        embed.description = f"Name: {tag['name']}\nUses: {tag['usage']:,}\nOwner: {self.get_user(g, tag['owner'])}\nCreator: " \
                            f"{self.get_user(g, tag['creator'])}\nCreated at: {time.time_output(time.from_ts(tag['created']))}\n" \
                            f"Last edited: {time.time_output(time.from_ts(tag['edited']))}"
        embed.add_field(name="Tag content", value=tag["content"])
        return await general.send(f"ℹ About tag {tag['name']}", ctx.channel, embed=embed)

    @tags.command(name="delete", aliases=["del"])
    async def delete_tag(self, ctx: commands.Context, *, tag_name: str):
        """ Delete a tag """
        tag = self.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await general.send(f"There is no tag named `{tag_name.lower()}`", ctx.channel)

        def check_confirm(m):
            if m.author == ctx.author and m.channel == ctx.channel:
                if m.content.startswith("yes"):
                    return True
            return False
        if tag["owner"] == ctx.author.id or (await permissions.check_permissions(ctx, perms={'kick_members': True})):
            confirm_msg = await general.send(f"{ctx.author.name}, are you sure you want to delete the tag `{tag['name']}`? This action cannot be undone. "
                                             f"Type `yes` to confirm.", ctx.channel)
            try:
                await self.bot.wait_for('message', timeout=30.0, check=check_confirm)
            except asyncio.TimeoutError:
                content = "Okay then, nothing will be deleted..."
                return await confirm_msg.edit(content=content)
            self.db.execute("DELETE FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag['name']))
            return await general.send(f"The tag `{tag['name']}` has been successfully deleted.", ctx.channel)
        else:
            return await general.send(f"{ctx.author.name}, you can't delete this tag.", ctx.channel)

    @tags.command(name="edit")
    async def edit_tag(self, ctx: commands.Context, tag_name: str, *, new_content: str):
        """ Edit a tag """
        tag = self.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await general.send(f"There is no tag named `{tag_name.lower()}`", ctx.channel)
        if tag["owner"] != ctx.author.id:
            return await general.send("You can't edit a tag you don't own", ctx.channel)
        else:
            self.db.execute("UPDATE tags SET content=?, edited=? WHERE gid=? AND name=?", (new_content, time.now_ts(), ctx.guild.id, tag_name.lower()))
            return await general.send(f"The tag `{tag['name']}` has been successfully edited.", ctx.channel)

    @tags.command(name="rename")
    async def rename_tag(self, ctx: commands.Context, tag_name: str, *, new_name: str):
        """ Rename a tag """
        tag = self.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await general.send(f"There is no tag named `{tag_name.lower()}`", ctx.channel)
        _tag = self.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, new_name.lower()))
        if _tag:
            return await general.send(f"There is already a tag named `{tag_name.lower()}`", ctx.channel)
        if tag["owner"] != ctx.author.id:
            return await general.send("You can't rename a tag you don't own", ctx.channel)
        else:
            self.db.execute("UPDATE tags SET name=?, edited=? WHERE gid=? AND name=?", (new_name.lower(), time.now_ts(), ctx.guild.id, tag['name']))
            return await general.send(f"The tag `{tag['name']}` has been successfully renamed to `{new_name.lower()}`.", ctx.channel)

    @tags.command(name="transfer")
    async def transfer_tag(self, ctx: commands.Context, tag_name: str, *, user: discord.Member):
        """ Transfer your tag to someone else """
        tag = self.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await general.send(f"There is no tag named `{tag_name.lower()}`", ctx.channel)
        if tag["owner"] != ctx.author.id:
            return await general.send(f"{ctx.author.name}, you can't transfer a tag you don't own", ctx.channel)
        else:
            self.db.execute("UPDATE tags SET owner=? WHERE gid=? AND name=?", (user.id, ctx.guild.id, tag_name.lower()))
            return await general.send(f"The tag `{tag['name']}` has now been transferred to {user}.", ctx.channel)

    @tags.command(name="claim")
    async def claim_tag(self, ctx: commands.Context, *, tag_name: str):
        """ Claim a tag of a user who left the server """
        tag = self.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await general.send(f"There is no tag named `{tag_name.lower()}`", ctx.channel)
        if tag["owner"] == ctx.author.id:
            return await general.send(f"{ctx.author.name}, you already own this tag.", ctx.channel)
        elif tag["owner"] in [u.id for u in ctx.guild.members]:
            return await general.send(f"{ctx.author.name}, this tag belongs to a user who's still in this server.", ctx.channel)
        else:
            self.db.execute("UPDATE tags SET owner=? WHERE gid=? AND name=?", (ctx.author.id, ctx.guild.id, tag["name"]))
            return await general.send(f"{ctx.author.name}, you now own the tag `{tag['name']}`", ctx.channel)

    @tags.command(name="user")
    async def tags_user(self, ctx: commands.Context, who: discord.Member = None, page: int = 1):
        """ See someone's tags """
        user = who or ctx.author
        tags = self.db.fetch("SELECT * FROM tags WHERE owner=? AND gid=? ORDER BY name", (user.id, ctx.guild.id))
        if not tags:
            return await general.send(f"{user.name} has no tags so far.", ctx.channel)
        block = "```fix"
        for i, d in enumerate(tags[(page - 1) * 20:page * 20], start=(page - 1) * 20 + 1):
            block += f"\n[{i:02d}] {d['name']} | Uses: {d['usage']:,}"
        return await general.send(f"Tags belonging to user {user.name} | Page {page} of {len(tags) // 20 + 1}\n{block}```", ctx.channel)

    @tags.command(name="all")
    async def tags_all(self, ctx: commands.Context, page: int = 1):
        """ See all tags sorted alphabetically """
        tags = self.db.fetch("SELECT * FROM tags WHERE gid=? ORDER BY name", (ctx.guild.id,))
        if not tags:
            return await general.send(f"There are no tags in {ctx.guild.name} so far.", ctx.channel)
        block = "```fix"
        for i, d in enumerate(tags[(page - 1) * 20:page * 20], start=(page - 1) * 20 + 1):
            block += f"\n[{i:02d}] {d['name']} | Uses: {d['usage']:,}"
        return await general.send(f"Tags in {ctx.guild.name} - Sorted by name | Page {page} of {len(tags) // 20 + 1}\n{block}```", ctx.channel)

    @tags.command(name="top")
    async def tags_top(self, ctx: commands.Context, page: int = 1):
        """ See all tags sorted by usage """
        tags = self.db.fetch("SELECT * FROM tags WHERE gid=? ORDER BY usage DESC", (ctx.guild.id,))
        if not tags:
            return await general.send(f"There are no tags in {ctx.guild.name} so far.", ctx.channel)
        block = "```fix"
        for i, d in enumerate(tags[(page - 1) * 20:page * 20], start=(page - 1) * 20 + 1):
            block += f"\n[{i:02d}] {d['name']} | Uses: {d['usage']:,}"
        return await general.send(f"Tags in {ctx.guild.name} - Sorted by usage | Page {page} of {len(tags) // 20 + 1}\n{block}```", ctx.channel)


def setup(bot):
    bot.add_cog(Tags(bot))
