import json
from typing import NamedTuple

import discord
from discord import app_commands

from utils import bot_data, commands, general, logger, time, messages


class Starboard(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    async def starboard_update(self, payload: discord.RawReactionActionEvent):
        """ Handle updating the data on the message. """
        guild = NamedTuple("Guild", name=str)(name=str(payload.guild_id))  # Just a placeholder guild variable in the highly unlikely case something breaks before then
        try:
            # _type = {
            #     discord.RawReactionActionEvent: 1,
            #     discord.RawReactionClearEvent: 2,
            #     discord.RawReactionClearEmojiEvent: 3,
            #     # discord.RawMessageDeleteEvent: 4
            # }.get(type(payload))
            # increase = 1 if payload.event_type == "REACTION_ADD" else -1 if payload.event_type == "REACTION_REMOVE" else 0
            emoji = payload.emoji
            if emoji.name != "⭐":
                return  # Not a star, ignore.
            server = payload.guild_id
            if server is None:
                return
            guild = self.bot.get_guild(server)
            _settings = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=? AND bot=?", (server, self.bot.name))
            if _settings:
                __settings = json.loads(_settings['data'])
                try:
                    if not __settings['starboard']['enabled']:
                        return
                except KeyError:
                    return
            else:
                return
            # ^ Checks that the server has starboard enabled
            language = self.bot.language(commands.FakeContext(guild, self.bot))
            # locale = languages.gl(Ctx(guild, self.bot))
            channel = payload.channel_id
            _channel: discord.TextChannel = self.bot.get_channel(channel)
            if "channel" not in __settings["starboard"] or not __settings["starboard"]["channel"]:
                starboard_channel = None
                try:
                    await _channel.send(language.string("starboard_error_channel"))
                except discord.Forbidden:
                    pass
                # return await general.send("Starboard will not be able to function - there is no channel set up.", _channel)
            else:
                starboard_channel = self.bot.get_channel(__settings["starboard"]["channel"])
                if not starboard_channel:
                    try:
                        await _channel.send(language.string("starboard_error_channel2"))
                    except discord.Forbidden:
                        pass
                    # return await general.send("Starboard channel could not be accessed. Starboard will not be able to function.", _channel)
            message = payload.message_id
            try:
                _message: discord.Message = await _channel.fetch_message(message)
            except (discord.NotFound, discord.Forbidden):
                return  # Since what's the point of starring a message you don't even know
            # if _type == 1:
            user = payload.user_id
            _author = _message.author.id
            if user == _author:
                return  # You shouldn't star your own messages
            # else:
            #     _author = 0
            # adder = payload.user_id
            data = self.bot.db.fetchrow("SELECT * FROM starboard WHERE message=? AND bot=?", (message, self.bot.name))
            new = not data
            # Get new star count: If no star emoji found, then there are zero stars. Else, set the start count to the count of the star emoji
            _stars = [r.count for r in _message.reactions if r.emoji == "⭐"]
            if not _stars:
                stars = 0
            else:
                stars = _stars[0]
            # stars = 1 if new else data["stars"] + increase  # if _type == 1 else 0
            star_message = f"⭐ {stars} - <#{channel}>"
            if "minimum" not in __settings["starboard"] or not __settings["starboard"]["minimum"]:
                minimum = 3
            else:
                minimum = __settings["starboard"]["minimum"]
            if new and stars != 0:
                self.bot.db.execute("INSERT INTO starboard VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (message, channel, _author, server, stars, None, False, self.bot.name, None))
            else:
                self.bot.db.execute("UPDATE starboard SET stars=? WHERE message=? AND bot=?", (stars, message, self.bot.name))
            logger.log(self.bot.name, "starboard", f"{time.time()} > {self.bot.full_name} > {guild.name} ({payload.guild_id}) > #{_channel.name} > Message ID {message} now has {stars} stars.")

            async def send_starboard_message():
                nonlocal _message
                embed = discord.Embed(colour=0xffff00)
                author = _message.author
                author_name = general.username(author)
                author_url = str(author.display_avatar.replace(size=64, format="png"))
                embed.set_author(name=author_name, icon_url=author_url)
                jump_url = _message.jump_url
                if _message.message_snapshots:
                    embed.title = language.string("starboard_message_forwarded")
                    message_snapshot = _message.message_snapshots[0]  # Forwarded message
                    if message_snapshot.cached_message:
                        _message = message_snapshot.cached_message  # type: ignore
                    else:
                        _message = message_snapshot
                embed.description = _message.content
                embed.add_field(name=language.string("starboard_message_jump"), value=language.string("starboard_message_jump2", url=jump_url), inline=False)

                embeds_and_links = await messages.embed_or_link_attachments(_message, language, embed, salvage_mode=False)
                embed = embeds_and_links.main_embed

                # embed.add_field(name="Jump to message", value=f"[Click here]({_message.jump_url})", inline=False)
                embed.set_footer(text=language.string("events_message_id", id=message))
                embed.timestamp = _message.created_at

                try:
                    _starboard_message = await starboard_channel.send(star_message, embeds=[embed] + embeds_and_links.embeds[:9])  # Only up to 10 embeds can be present
                    self.bot.db.execute("UPDATE starboard SET star_message=? WHERE message=? AND bot=?", (_starboard_message.id, message, self.bot.name))
                    logger.log(self.bot.name, "starboard", f"{time.time()} > {self.bot.full_name} > {guild.name} ({payload.guild_id}) > Saved Message ID {message} to starboard channel")
                except discord.Forbidden:
                    try:
                        await _channel.send(language.string("starboard_error_message"))
                    except discord.Forbidden:
                        pass
                    # await general.send("Imagine not being able to send messages to the starboard channel", _channel)

            if starboard_channel is not None:
                if stars >= minimum:  # If there are enough stars
                    if not data or not data["star_message"]:
                        await send_starboard_message()
                    else:
                        try:
                            starboard_message: discord.Message = await starboard_channel.fetch_message(data["star_message"])
                        except discord.NotFound:
                            logger.log(self.bot.name, "starboard", f"{time.time()} > {self.bot.full_name} > {guild.name} > Resending starboard message for Message ID {message}")
                            # await general.send(f"Starboard for message {message} could not be found - Resending message.",
                            #                    self.bot.get_channel(channel))
                            await send_starboard_message()
                        except discord.Forbidden:
                            try:
                                await _channel.send(language.string("starboard_error_fetch"))
                            except discord.Forbidden:
                                pass
                            # await general.send(f"Starboard update failed for message {message} - Not allowed to fetch messages from starboard channel.\n"
                            #                    f"Star amount was still updated on database.",
                            #                    self.bot.get_channel(channel))
                        else:
                            await starboard_message.edit(content=star_message)
                else:
                    if not data or not data["star_message"]:
                        pass
                    else:
                        try:
                            starboard_message: discord.Message = await starboard_channel.fetch_message(data["star_message"])
                            await starboard_message.delete()
                            logger.log(self.bot.name, "starboard", f"{time.time()} > {self.bot.full_name} > {guild.name} ({payload.guild_id}) > "
                                                                   f"Deleted starboard message for Message ID {message}, no longer enough stars.")
                        except (discord.NotFound, discord.Forbidden):
                            pass  # If there is no message or I can't fetch it and delete it, ignore
            self.bot.db.execute("DELETE FROM starboard WHERE stars=0")
        except Exception as e:
            out = f"{time.time()} > {self.bot.full_name} > Starboard update > {guild.name} ({payload.guild_id}) > Message {payload.message_id} > {type(e).__name__}: {e}"
            general.print_error(out)
            # print(general.traceback_maker(e, code_block=False))
            logger.log(self.bot.name, "errors", out)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """ Reaction was added to a message """
        return await self.starboard_update(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """ Reaction was removed from a message """
        return await self.starboard_update(payload)

    async def delete_message(self, payload: discord.RawReactionClearEvent | discord.RawReactionClearEmojiEvent | discord.RawMessageDeleteEvent | discord.RawBulkMessageDeleteEvent):
        """ Handle a message being deleted or its star reactions getting cleared """
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message_ids = payload.message_ids if isinstance(payload, discord.RawBulkMessageDeleteEvent) else [payload.message_id]
        log_header = f"{time.time()} > {self.bot.full_name} > {guild.name} ({payload.guild_id}) > #{channel.name} > "
        settings_data = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=? AND bot=?", (payload.guild_id, self.bot.name))
        if not settings_data:
            return
        settings_dict = json.loads(settings_data["data"])
        if "starboard" not in settings_dict or not settings_dict["starboard"]["enabled"]:
            return
        if "channel" not in settings_dict["starboard"] or not settings_dict["starboard"]["channel"]:
            starboard_channel = None
        else:
            starboard_channel = guild.get_channel(settings_dict["starboard"]["channel"])
        if isinstance(payload, (discord.RawReactionClearEvent, discord.RawReactionClearEmojiEvent)):
            # Delete the database entry and remove from starboard
            for message_id in message_ids:
                data = self.bot.db.fetchrow("SELECT * FROM starboard WHERE message=? AND bot=?", (message_id, self.bot.name))
                output = self.bot.db.execute("DELETE FROM starboard WHERE message=? AND bot=?", (message_id, self.bot.name))
                if output != "DELETE 0":
                    logger.log(self.bot.name, "starboard", log_header + f"Star reactions of Message ID {message_id} were cleared.")
                if starboard_channel and data is not None and data["star_message"]:
                    try:
                        starboard_message = await starboard_channel.fetch_message(data["star_message"])
                        await starboard_message.delete()
                    except (discord.NotFound, discord.Forbidden):
                        logger.log(self.bot.name, "starboard", log_header + f"Starboard message for no longer valid Message ID {message_id} could not be deleted")
        else:
            # Notify that the message has been deleted, but keep it in the database
            language = self.bot.language(commands.FakeContext(guild, self.bot))
            for message_id in message_ids:
                data = self.bot.db.fetchrow("SELECT * FROM starboard WHERE message=? AND bot=?", (message_id, self.bot.name))
                output = self.bot.db.execute("UPDATE starboard SET deleted=1 WHERE message=? AND bot=?", (message_id, self.bot.name))
                if output != "UPDATE 0":
                    logger.log(self.bot.name, "starboard", log_header + f"Message ID {message_id} has been deleted.")
                if starboard_channel and data is not None and data["star_message"]:
                    try:
                        star_text = f"⭐ {data["stars"]} - <#{data["channel"]}>\n{language.string("starboard_message_deleted")}"
                        starboard_message = await starboard_channel.fetch_message(data["star_message"])
                        await starboard_message.edit(content=star_text)
                    except (discord.NotFound, discord.Forbidden):
                        logger.log(self.bot.name, "starboard", log_header + f"Starboard message for deleted Message ID {message_id} could not be updated")

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload: discord.RawReactionClearEvent):
        """ All reactions were cleared from a message """
        return await self.delete_message(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_clear_emoji(self, payload: discord.RawReactionClearEmojiEvent):
        """ An emote has been cleared from a message """
        if payload.emoji.name == "⭐":
            return await self.delete_message(payload)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        """ Message was deleted """
        return await self.delete_message(payload)

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload: discord.RawBulkMessageDeleteEvent):
        """ Several messages were deleted """
        return await self.delete_message(payload)

    def find_user(self, user_id: int):
        user = self.bot.get_user(user_id)
        return user if user is not None else f"Unknown user {user_id}"

    @commands.hybrid_group(name="starboard", aliases=["stars", "sb"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.guild_only()
    async def starboard_data(self, ctx: commands.Context):
        """ See starboard stats for the entire server or a specific member """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @starboard_data.command(name="server", aliases=["guild"])
    async def starboard_server(self, ctx: commands.Context):
        """ See starboard stats for the current server """
        await ctx.defer(ephemeral=True)
        language = self.bot.language(ctx)
        embed = discord.Embed(colour=general.random_colour())
        data = self.bot.db.fetch("SELECT * FROM starboard WHERE guild=? AND bot=? ORDER BY stars DESC", (ctx.guild.id, self.bot.name))
        if not data:
            return await ctx.send(language.string("starboard_stats_none"))
        stars = 0
        authors = {}
        top = []
        for i, message in enumerate(data):
            # message = data[i]
            if i < 5:
                top.append(message)
            stars += message["stars"]
            if message["author"] in authors:
                authors[message["author"]] += message["stars"]
            else:
                authors[message["author"]] = message["stars"]
        authors_sorted = dict(sorted(authors.items(), key=lambda x: x[1], reverse=True))
        # embed.title = f"Starboard stats for {ctx.guild.name}"
        embed.title = language.string("starboard_stats", server=ctx.guild.name)
        # embed.description = f"⭐ **{stars:,} stars** across {len(data):,} messages"
        embed.description = language.string("starboard_stats_desc", stars=language.number(stars), messages=language.number(len(data)))
        if ctx.guild.icon:
            embed.set_thumbnail(url=str(ctx.guild.icon.replace(size=1024, static_format="png")))
        top_messages = ""
        authors_out = ""
        # Top Starred Posts
        for i, _message in enumerate(top, start=1):
            # [<stars> by <author>](link)
            # try:
            #     message = await self.bot.get_channel(_message["channel"]).fetch_message(_message["message"])
            jump_url = f"https://discord.com/channels/{_message['guild']}/{_message['channel']}/{_message['message']}"
            _stars = language.number(_message["stars"])
            channel = self.bot.get_channel(_message['channel']) or language.string("starboard_stats_channel_unknown")
            link = language.string("starboard_stats_deleted", channel=f"#{channel}") if _message["deleted"] else f"[#{channel}]({jump_url})"
            top_messages += f"\n{i}) ⭐ {_stars} - {self.find_user(_message['author'])} - {link}"
            # except (discord.NotFound, AttributeError):
            #     embed.description += f"\n{i + 1}) ⭐ {_message['stars']} Deleted message"
        for i, _data in enumerate(authors_sorted.items(), start=1):
            if i <= 5:
                _uid, _stars = _data
                authors_out += f"\n{i}) ⭐ {_stars} - <@{_uid}>"
        if top_messages:
            embed.add_field(name=language.string("starboard_stats_messages"), value=top_messages, inline=False)
        if authors_out:
            embed.add_field(name=language.string("starboard_stats_authors"), value=authors_out, inline=False)
        return await ctx.send(embed=embed)

    @starboard_data.command(name="member", aliases=["user"])
    @app_commands.describe(member="The member whose stats to look up. Shows your stats if not specified.")
    async def starboard_member(self, ctx: commands.Context, member: discord.Member = None):
        """ See starboard stats for a specific member within the server """
        await ctx.defer(ephemeral=True)
        language = self.bot.language(ctx)
        member = member or ctx.author
        embed = discord.Embed(colour=general.random_colour())
        data = self.bot.db.fetch("SELECT * FROM starboard WHERE guild=? AND author=? AND bot=? ORDER BY stars DESC", (ctx.guild.id, member.id, self.bot.name))
        if not data:
            return await ctx.send(language.string("starboard_stats_none2", user=general.username(member)))
        stars = 0
        top = []
        for i, message in enumerate(data):
            # message = data[i]
            if i < 10:
                top.append(message)
            stars += message["stars"]
        # embed.title = f"Starboard stats for {user} in {ctx.guild.name}"
        embed.title = language.string("starboard_stats_user", user=general.username(member), server=ctx.guild.name)
        # embed.description = f"Received ⭐ **{stars:,} stars** across {len(data):,} messages\n\nTop messages:"
        embed.description = language.string("starboard_stats_user_desc", stars=language.number(stars), messages=language.number(len(data)))
        embed.set_thumbnail(url=str(member.display_avatar))
        for i, _message in enumerate(top, start=1):
            jump_url = f"https://discord.com/channels/{_message['guild']}/{_message['channel']}/{_message['message']}"
            _stars = language.number(_message["stars"])
            channel = self.bot.get_channel(_message['channel']) or language.string("starboard_stats_channel_unknown")
            link = language.string("starboard_stats_deleted", channel=f"#{channel}") if _message["deleted"] else f"[#{channel}]({jump_url})"
            embed.description += f"\n{i}) ⭐ {_stars} - {link}"
        return await ctx.send(embed=embed)


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Starboard(bot))
