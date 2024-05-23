import json
from typing import NamedTuple

import discord

from utils import bot_data, commands, general, logger, time


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
            _settings = self.bot.db.fetchrow(f"SELECT * FROM settings WHERE gid=?", (server,))
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
                self.bot.db.execute("INSERT INTO starboard VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (message, channel, _author, server, stars, None, self.bot.name, None))
            else:
                self.bot.db.execute("UPDATE starboard SET stars=? WHERE message=? AND bot=?", (stars, message, self.bot.name))
            logger.log(self.bot.name, "starboard", f"{time.time()} > Message ID {message} in #{_channel.name} ({guild.name}) now has {stars} stars.")

            async def send_starboard_message():
                embed = discord.Embed(colour=0xffff00)
                author = _message.author
                author_name = general.username(author)
                author_url = str(author.display_avatar.replace(size=64, format="png"))
                embed.set_author(name=author_name, icon_url=author_url)
                embed.description = _message.content

                # The first attachment has its content embedded, if possible
                # Any other attachments are tagged along as links or included in extra embeds
                # If there is an embed in the original message, it's also included after the main embed
                if _message.attachments:
                    count = len(_message.attachments)
                    start = 1
                    att = _message.attachments[0]
                    content = str(att.content_type)
                    if content.startswith("image/"):  # the attachment contains an image
                        embed.set_image(url=att.url)
                    # elif content.startswith("video/"):
                    #     embed.set_video(url=att.url)
                    else:
                        start = 0
                else:
                    count, start = 0, 0

                # Set a few variables for the embedded and linked attachments
                embed_limit = 9
                embeds = []
                links = []
                embedded = 0   # Embedded attachments
                embedded2 = 0  # Embedded embeds
                linked = 0     # Linked attachments
                linked2 = 0    # Linked embeds
                ignored = 0    # Ignored embeds

                # Texts for linked attachments
                text_aa = language.string("starboard_attachment_audio")
                text_ai = language.string("starboard_attachment_image")
                text_av = language.string("starboard_attachment_video")
                text_ao = language.string("starboard_attachment_other")
                text_ei = language.string("starboard_embed_image")
                text_ev = language.string("starboard_embed_video")

                # Try to embed or link all remaining attachments
                if count > start:
                    for att in _message.attachments[start:]:
                        content = str(att.content_type)
                        if len(embeds) < embed_limit and content.startswith("image/"):
                            _embed = discord.Embed()  # type="image", url=att.url)
                            _embed._image = {"url": att.url, "proxy_url": att.proxy_url, "height": att.height, "width": att.width}
                            # _embed.set_image(url=att.url)
                            embeds.append(_embed)
                            embedded += 1
                        else:
                            if content.startswith("image/"):
                                text = text_ai
                            elif content.startswith("video/"):
                                text = text_av
                            elif content.startswith("audio/"):
                                text = text_aa
                            else:
                                text = text_ao
                            links.append(f"[{text}]({att.url}) - {att.filename}")
                            # links.append(att.url)
                            linked += 1

                # Add the message's embeds to the other ones (up to 9 total)
                for __embed in _message.embeds:
                    if len(embeds) < embed_limit:
                        if __embed.type == "image":
                            # Note: This assumes that all image embeds are from discord, where it uses thumbnail instead of image for whatever odd reason
                            if not hasattr(embed, "_image"):  # if the image has not yet been set to the current embed
                                embed._image = __embed._thumbnail  # set that embed's image as our image
                            else:
                                _embed = discord.Embed()
                                _embed._image = __embed._thumbnail
                                embeds.append(_embed)
                                embedded2 += 1
                        elif __embed.type == "video":
                            links.append(f"[{text_ev}]({__embed.video.url}) - {__embed.video.url.split('/')[-1].split('?')[0]}")
                            linked2 += 1
                        else:
                            embeds.append(__embed)
                            embedded2 += 1
                    else:
                        if __embed.type == "image":
                            # Note: This assumes that all image embeds are from discord, where it uses thumbnail instead of image for whatever odd reason
                            link = str(__embed.thumbnail.url)
                            filename = link.split('/')[-1].split("?")[0]
                            links.append(f"[{text_ei}]({link}) - {filename}")
                            linked2 += 1
                        elif __embed.type == "video":
                            link = str(__embed.video.url)
                            filename = link.split('/')[-1].split("?")[0]
                            links.append(f"[{text_ev}]({link}) - {filename}")
                            linked2 += 1
                        else:
                            # Only image and video embeds will be linked, others are ignored.
                            ignored += 1

                embed.add_field(name=language.string("starboard_message_jump"), value=language.string("starboard_message_jump2", url=_message.jump_url), inline=False)
                if any((embedded, embedded2, linked, linked2, ignored)):
                    status = []
                    if embedded:
                        status.append(language.string("starboard_message_embedded", count=language.plural(embedded, "starboard_word_attachment")))
                    if linked:
                        status.append(language.string("starboard_message_linked", count=language.plural(linked, "starboard_word_attachment")))
                    if embedded2:
                        status.append(language.string("starboard_message_embedded", count=language.plural(embedded2, "starboard_word_embed")))
                    if linked2:
                        status.append(language.string("starboard_message_linked", count=language.plural(linked2, "starboard_word_embed")))
                    if ignored:
                        status.append(language.string("starboard_message_ignored", count=language.plural(ignored, "starboard_word_embed")))
                    _status = "\n".join(status)

                    if links:
                        _links = "\n\n" + "\n".join(links)
                    else:
                        _links = ""

                    embed.add_field(name=language.string("starboard_attachments"), value=_status + _links, inline=False)
                # embed.add_field(name="Jump to message", value=f"[Click here]({_message.jump_url})", inline=False)
                embed.set_footer(text=f"Message ID {message}")
                embed.timestamp = _message.created_at

                try:
                    _starboard_message = await starboard_channel.send(star_message, embeds=[embed] + embeds[:9])  # Only up to 10 embeds can be present
                    self.bot.db.execute("UPDATE starboard SET star_message=? WHERE message=? AND bot=?", (_starboard_message.id, message, self.bot.name))
                    logger.log(self.bot.name, "starboard", f"{time.time()} > Saved Message ID {message} to starboard channel")
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
                            logger.log(self.bot.name, "starboard", f"{time.time()} > Resending starboard message for Message ID {message}")
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
                            logger.log(self.bot.name, "starboard", f"{time.time()} > Deleted starboard message for Message ID {message}, no longer enough stars.")
                        except (discord.NotFound, discord.Forbidden):
                            pass  # If there is no message or I can't fetch it and delete it, ignore
            self.bot.db.execute("DELETE FROM starboard WHERE stars=0")
        except Exception as e:
            out = f"{time.time()} > Starboard update > {guild.name} ({payload.guild_id}) > Message {payload.message_id} > {type(e).__name__}: {e}"
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

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload: discord.RawReactionClearEvent):
        """ All reactions were cleared from a message """
        # Delete the message from the database, but keep it on the starboard channel
        # I think we don't need to specify the bot name here. If the stars are no longer available on the message,
        # then we might as well delete all relevant entries at once.
        output = self.bot.db.execute("DELETE FROM starboard WHERE message=?", (payload.message_id,))
        if output != "DELETE 0":
            logger.log(self.bot.name, "starboard", f"{time.time()} > Reactions of Message ID {payload.message_id} were cleared.")

    @commands.Cog.listener()
    async def on_raw_reaction_clear_emoji(self, payload: discord.RawReactionClearEmojiEvent):
        """ An emote has been cleared from a message """
        if payload.emoji.name == "⭐":
            # Delete the message from the database, but keep it on the starboard channel
            output = self.bot.db.execute("DELETE FROM starboard WHERE message=?", (payload.message_id,))
            if output != "DELETE 0":
                logger.log(self.bot.name, "starboard", f"{time.time()} > Star reactions of Message ID {payload.message_id} were cleared.")

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        """ Message was deleted """
        # Delete the message from the database, but keep it on the starboard channel
        output = self.bot.db.execute("DELETE FROM starboard WHERE message=?", (payload.message_id,))
        if output != "DELETE 0":
            logger.log(self.bot.name, "starboard", f"{time.time()} > Message ID {payload.message_id} has been deleted.")

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload: discord.RawBulkMessageDeleteEvent):
        """ Several messages were deleted """
        for message in payload.message_ids:
            output = self.bot.db.execute("DELETE FROM starboard WHERE message=?", (message,))
            if output != "DELETE 0":
                logger.log(self.bot.name, "starboard", f"{time.time()} > Message ID {message} has been bulk-deleted.")

    def find_user(self, user_id: int):
        user = self.bot.get_user(user_id)
        return user if user is not None else f"Unknown user {user_id}"

    @commands.command(name="stars", aliases=["starboard", "sb"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def star_data(self, ctx: commands.Context, user: discord.User = None):
        """ Starboard stats for the server or a specific user """
        language = self.bot.language(ctx)
        if user is None:
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
                top_messages += f"\n{i}) ⭐ {_stars} - {self.find_user(_message['author'])} - [#{self.bot.get_channel(_message['channel'])}]({jump_url})"
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
        else:
            embed = discord.Embed(colour=general.random_colour())
            data = self.bot.db.fetch("SELECT * FROM starboard WHERE guild=? AND author=? AND bot=? ORDER BY stars DESC", (ctx.guild.id, user.id, self.bot.name))
            if not data:
                return await ctx.send(language.number("starboard_stats_none2", user=general.username(user)))
            stars = 0
            top = []
            for i, message in enumerate(data):
                # message = data[i]
                if i < 10:
                    top.append(message)
                stars += message["stars"]
            # embed.title = f"Starboard stats for {user} in {ctx.guild.name}"
            embed.title = language.string("starboard_stats_user", user=general.username(user), server=ctx.guild.name)
            # embed.description = f"Received ⭐ **{stars:,} stars** across {len(data):,} messages\n\nTop messages:"
            embed.description = language.string("starboard_stats_user_desc", stars=language.number(stars), messages=language.number(len(data)))
            embed.set_thumbnail(url=str(user.display_avatar))
            for i, _message in enumerate(top, start=1):
                jump_url = f"https://discord.com/channels/{_message['guild']}/{_message['channel']}/{_message['message']}"
                _stars = language.number(_message["stars"])
                embed.description += f"\n{i}) ⭐ {_stars} - [#{self.bot.get_channel(_message['channel'])}]({jump_url})"
            return await ctx.send(embed=embed)


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Starboard(bot))
