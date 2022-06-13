import asyncio
from math import ceil

import discord

from utils import bot_data, commands, general, languages, permissions, time


class Tags(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.group(name="tag", aliases=["tags", "t"], invoke_without_command=True, case_insensitive=True)
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def tags(self, ctx: commands.Context, *, tag_name: str):
        """ Tags """
        if ctx.invoked_subcommand is None:
            tag = self.bot.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
            language = self.bot.language(ctx)
            if tag:
                self.bot.db.execute("UPDATE tags SET usage=usage+1 WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
                content = tag["content"]\
                    .replace("[USERNAME]", ctx.author.name)\
                    .replace("[USER]", str(ctx.author))\
                    .replace("[USER_ID]", str(ctx.author.id))\
                    .replace("[AVATAR]", str(ctx.author.display_avatar.replace(static_format="png", size=1024)))\
                    .replace("[JOINED]", language.time(ctx.author.joined_at, short=0, dow=False, seconds=True, tz=True))\
                    .replace("[USER_CREATED]", language.time(ctx.author.created_at, short=0, dow=False, seconds=True, tz=True))\
                    .replace("[SERVER_CREATED]", language.time(ctx.guild.created_at, short=0, dow=False, seconds=True, tz=True))\
                    .replace("[CHANNEL]", ctx.channel.mention)\
                    .replace("[CHANNEL_NAME]", ctx.channel.name)\
                    .replace("[SERVER]", ctx.guild.name)\
                    .replace("[SERVER_ID]", str(ctx.guild.id))\
                    .replace("[MEMBERS]", str(len(ctx.guild.members)))\
                    .replace("[OWNER]", str(ctx.guild.owner))\
                    .replace("[SERVER_ICON]", str(ctx.guild.icon.replace(static_format="png", size=1024)) if ctx.guild.icon else "No server icon")\
                    .replace("[USAGE]", str(tag["usage"] + 1))
                return await ctx.send(content, allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=False))
            else:
                return await ctx.send(language.string("tags_not_found", tag=tag_name.lower()))

    @tags.command(name="variables", aliases=["arguments", "args", "vars"])
    async def tag_variables(self, ctx: commands.Context):
        """ Lists all available tag variables """
        variables = {
            "USERNAME": f"Your username (e.g. {ctx.author.name})",
            "USER": f"Your name and tag (e.g. {ctx.author})",
            "USER_ID": "Your user ID",
            "AVATAR": "URL to your avatar/profile picture",
            "JOINED": "When you joined this server",
            "USER_CREATED": "When you created your account",
            "SERVER_CREATED": "When the server was created",
            "CHANNEL": "Mentions the channel the tag was used in",
            "CHANNEL_NAME": "The name of the channel",
            "SERVER": "The name of this server",
            "SERVER_ID": "This server's ID",
            "MEMBERS": "How many members there are in the server",
            "OWNER": "The server owner",
            "SERVER_ICON": "URL to the server icon",
            "USAGE": "How many times the tag has been used"
        }
        output = "\n".join(sorted([f"[{key}] - {value}" for key, value in variables.items()]))
        return await ctx.send(f"Here are the currently available tag variables:\n{output}")

    @tags.command(name="create", aliases=["add"])
    async def create_tag(self, ctx: commands.Context, tag_name: str, *, content: str):
        """ Create a new tag """
        language = self.bot.language(ctx)
        tag = self.bot.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if tag:
            return await ctx.send(language.string("tags_create_already", tag=tag_name.lower()))
        self.bot.db.fetchrow("INSERT INTO tags VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                             (ctx.guild.id, ctx.author.id, ctx.author.id, tag_name.lower(), content, int(time.now_ts()), int(time.now_ts()), 0))
        return await ctx.send(language.string("tags_create_success", tag=tag_name.lower(), author=ctx.author.name))

    async def try_get(self, uid: int):
        try:
            return await self.bot.fetch_user(uid)
        except discord.NotFound:
            return f"Unknown User {uid}"

    async def get_user(self, guild: discord.Guild, uid: int, language: languages.Language) -> str:
        user = guild.get_member(uid)
        return str(user) if user is not None else str(await self.try_get(uid)) + f" | {language.string('tags_user_guild')}"

    @tags.command(name="info")
    async def tag_info(self, ctx: commands.Context, *, tag_name: str):
        """ See info about a tag """
        language = self.bot.language(ctx)
        tag = self.bot.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await ctx.send(language.string("tags_not_found", tag=tag_name.lower()))
        embed = discord.Embed(colour=general.random_colour())
        g = ctx.guild
        embed.description = language.string("tags_info_data", name=tag["name"], usage=language.number(tag["usage"]), owner=await self.get_user(g, tag["owner"], language),
                                            creator=await self.get_user(g, tag["creator"], language),
                                            created=language.time(time.from_ts(tag["created"]), tz=True, uid=ctx.author.id),
                                            edited=language.time(time.from_ts(tag["edited"]), tz=True, uid=ctx.author.id))
        c = tag["content"]
        if len(c) > 1024:
            c = f"{c[:1021]}..."
        embed.add_field(name=language.string("tags_info_content"), value=c)
        return await ctx.send(language.string("tags_info_about", tag=tag["name"]), embed=embed)

    @tags.command(name="delete", aliases=["del"])
    async def delete_tag(self, ctx: commands.Context, *, tag_name: str):
        """ Delete a tag """
        language = self.bot.language(ctx)
        tag = self.bot.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await ctx.send(language.string("tags_not_found", tag=tag_name.lower()))

        def check_confirm(m):
            if m.author == ctx.author and m.channel == ctx.channel:
                if m.content.startswith("yes"):
                    return True
            return False
        if tag["owner"] == ctx.author.id or (await permissions.check_permissions(ctx, perms={'kick_members': True})):
            confirm_msg = await ctx.send(language.string("tags_delete_confirm", author=ctx.author.name, tag=tag["name"]))
            try:
                await self.bot.wait_for('message', timeout=30.0, check=check_confirm)
            except asyncio.TimeoutError:
                return await confirm_msg.edit(content=language.string("generic_timed_out", text=confirm_msg.clean_content))
            self.bot.db.execute("DELETE FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag['name']))
            await confirm_msg.delete()
            return await ctx.send(language.string("tags_delete_success", tag=tag["name"]))
        else:
            return await ctx.send(language.string("tags_delete_deny"))

    @tags.command(name="edit")
    async def edit_tag(self, ctx: commands.Context, tag_name: str, *, new_content: str):
        """ Edit a tag """
        language = self.bot.language(ctx)
        tag = self.bot.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await ctx.send(language.string("tags_not_found", tag=tag_name.lower()))
        if tag["owner"] != ctx.author.id:
            return await ctx.send(language.string("tags_edit_deny"))
        else:
            self.bot.db.execute("UPDATE tags SET content=?, edited=? WHERE gid=? AND name=?", (new_content, int(time.now_ts()), ctx.guild.id, tag_name.lower()))
            return await ctx.send(language.string("tags_edit_success", tag=tag["name"]))

    @tags.command(name="rename")
    async def rename_tag(self, ctx: commands.Context, tag_name: str, *, new_name: str):
        """ Rename a tag """
        language = self.bot.language(ctx)
        tag = self.bot.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await ctx.send(language.string("tags_not_found", tag=tag_name.lower()))
        _tag = self.bot.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, new_name.lower()))
        if _tag:
            return await ctx.send(language.string("tags_rename_already", name=new_name.lower()))
        if tag["owner"] != ctx.author.id:
            return await ctx.send(language.string("tags_rename_deny"))
        else:
            self.bot.db.execute("UPDATE tags SET name=?, edited=? WHERE gid=? AND name=?", (new_name.lower(), int(time.now_ts()), ctx.guild.id, tag['name']))
            return await ctx.send(language.string("tags_rename_success", tag=tag["name"], name=new_name.lower()))

    @tags.command(name="transfer")
    async def transfer_tag(self, ctx: commands.Context, tag_name: str, *, user: discord.Member):
        """ Transfer your tag to someone else """
        language = self.bot.language(ctx)
        tag = self.bot.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await ctx.send(language.string("tags_not_found", tag=tag_name.lower()))
        if tag["owner"] != ctx.author.id:
            return await ctx.send(language.string("tags_transfer_deny"))
        else:
            self.bot.db.execute("UPDATE tags SET owner=? WHERE gid=? AND name=?", (user.id, ctx.guild.id, tag_name.lower()))
            return await ctx.send(language.string("tags_transfer_success", tag=tag["name"], target=user))

    @tags.command(name="claim")
    async def claim_tag(self, ctx: commands.Context, *, tag_name: str):
        """ Claim a tag of a user who left the server """
        language = self.bot.language(ctx)
        tag = self.bot.db.fetchrow("SELECT * FROM tags WHERE gid=? AND name=?", (ctx.guild.id, tag_name.lower()))
        if not tag:
            return await ctx.send(language.string("tags_not_found", tag=tag_name.lower()))
        if tag["owner"] == ctx.author.id:
            return await ctx.send(language.string("tags_claim_owned"))
        elif tag["owner"] in [u.id for u in ctx.guild.members]:
            return await ctx.send(language.string("tags_claim_server"))
        else:
            self.bot.db.execute("UPDATE tags SET owner=? WHERE gid=? AND name=?", (ctx.author.id, ctx.guild.id, tag["name"]))
            return await ctx.send(language.string("tags_claim_success", author=ctx.author.name, tag=tag["name"]))

    @tags.command(name="user")
    async def tags_user(self, ctx: commands.Context, who: discord.Member = None, page: int = 1):
        """ See someone's tags """
        language = self.bot.language(ctx)
        user = who or ctx.author
        tags = self.bot.db.fetch("SELECT * FROM tags WHERE owner=? AND gid=? ORDER BY name", (user.id, ctx.guild.id))
        if not tags:
            return await ctx.send(language.string("tags_user_none", user=user.name))
        block = "```fix"
        for i, d in enumerate(tags[(page - 1) * 20:page * 20], start=(page - 1) * 20 + 1):
            block += f"\n{i:02d}) {d['name']} | {language.plural(d['usage'], 'tags_list_uses')}"
        return await ctx.send(language.string("tags_user", user=user.name, page=language.number(page), max=language.number(ceil(len(tags) / 20)), data=block))

    @tags.command(name="all")
    async def tags_all(self, ctx: commands.Context, page: int = 1):
        """ See all tags sorted alphabetically """
        language = self.bot.language(ctx)
        tags = self.bot.db.fetch("SELECT * FROM tags WHERE gid=? ORDER BY name", (ctx.guild.id,))
        if not tags:
            return await ctx.send(language.string("tags_list_none", server=ctx.guild.name))
        block = "```fix"
        for i, d in enumerate(tags[(page - 1) * 20:page * 20], start=(page - 1) * 20 + 1):
            block += f"\n{i:02d}) {d['name']} | {language.plural(d['usage'], 'tags_list_uses')}"
        return await ctx.send(language.string("tags_all", server=ctx.guild, page=language.number(page), max=language.number(ceil(len(tags) / 20)), data=block))

    @tags.command(name="top")
    async def tags_top(self, ctx: commands.Context, page: int = 1):
        """ See all tags sorted by usage """
        language = self.bot.language(ctx)
        tags = self.bot.db.fetch("SELECT * FROM tags WHERE gid=? ORDER BY usage DESC", (ctx.guild.id,))
        if not tags:
            return await ctx.send(language.string("tags_list_none", server=ctx.guild.name))
        block = "```fix"
        for i, d in enumerate(tags[(page - 1) * 20:page * 20], start=(page - 1) * 20 + 1):
            block += f"\n{i:02d}) {d['name']} | {language.plural(d['usage'], 'tags_list_uses')}"
        return await ctx.send(language.string("tags_top", server=ctx.guild, page=language.number(page), max=language.number(ceil(len(tags) / 20)), data=block))

    @tags.command(name="search")
    async def tags_search(self, ctx: commands.Context, search: str, page: int = 1):
        """ See all tags containing a substring
         Write search string "like this" if it contains 2 or more words"""
        language = self.bot.language(ctx)
        _search = "%" + search.replace("!", "!!").replace("%", "!%").replace("_", "!_").replace("[", "![") + "%"
        tags = self.bot.db.fetch("SELECT * FROM tags WHERE gid=? AND (content LIKE ? ESCAPE '!' OR name LIKE ? ESCAPE '!') ORDER BY name",
                                 (ctx.guild.id, _search, _search))
        if not tags:
            return await ctx.send(language.string("tags_search_none", server=ctx.guild.name))
        block = "```fix"
        for i, d in enumerate(tags[(page - 1) * 20:page * 20], start=(page - 1) * 20 + 1):
            block += f"\n{i:02d}) {d['name']} | {language.plural(d['usage'], 'tags_list_uses')}"
        return await ctx.send(language.string("tags_search", server=ctx.guild, page=language.number(page), max=language.number(ceil(len(tags) / 20)), data=block))

    @tags.command(name="unclaimed", aliases=["claimable"])
    async def tags_unclaimed(self, ctx: commands.Context, page: int = 1):
        """ See all tags that are unclaimed"""
        language = self.bot.language(ctx)
        members = tuple(m.id for m in ctx.guild.members)
        self.bot.db.execute("CREATE TEMP TABLE tags_members (uid INTEGER NOT NULL)")
        for member in members:
            self.bot.db.execute("INSERT INTO tags_members VALUES (?)", (member,))
        tags = self.bot.db.fetch("SELECT * FROM tags WHERE gid=? AND owner NOT IN (SELECT * FROM tags_members) ORDER BY name", (ctx.guild.id,))
        self.bot.db.execute("DROP TABLE tags_members")
        if not tags:
            return await ctx.send(language.string("tags_search_none", server=ctx.guild.name))
        block = "```fix"
        for i, d in enumerate(tags[(page - 1) * 20:page * 20], start=(page - 1) * 20 + 1):
            block += f"\n{i:02d}) {d['name']} | {language.plural(d['usage'], 'tags_list_uses')}"
        return await ctx.send(language.string("tags_unclaimed", server=ctx.guild, page=language.number(page), max=language.number(ceil(len(tags) / 20)), data=block))


def setup(bot: bot_data.Bot):
    bot.add_cog(Tags(bot))
