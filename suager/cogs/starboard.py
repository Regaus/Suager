import json

import discord
from discord.ext import commands

from core.utils import general, logger, time
from languages import langs
from suager.cogs.birthdays import Ctx


class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def starboard_update(self, payload: discord.RawReactionActionEvent):
        """ Handle updating the data on the message. """
        # _type = {
        #     discord.RawReactionActionEvent: 1,
        #     discord.RawReactionClearEvent: 2,
        #     discord.RawReactionClearEmojiEvent: 3,
        #     # discord.RawMessageDeleteEvent: 4
        # }.get(type(payload))
        increase = 1 if payload.event_type == "REACTION_ADD" else -1 if payload.event_type == "REACTION_REMOVE" else 0
        # if _type in [1, 3]:
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
        locale = langs.gl(Ctx(guild, self.bot))
        channel = payload.channel_id
        _channel: discord.TextChannel = self.bot.get_channel(channel)
        if "channel" not in __settings["starboard"] or not __settings["starboard"]["channel"]:
            starboard_channel = None
            try:
                await general.send(langs.gls("starboard_error_channel", locale), _channel)
            except discord.Forbidden:
                pass
            # return await general.send("Starboard will not be able to function - there is no channel set up.", _channel)
        else:
            starboard_channel = self.bot.get_channel(__settings["starboard"]["channel"])
            if not starboard_channel:
                try:
                    await general.send(langs.gls("starboard_error_channel2", locale), _channel)
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
        data = self.bot.db.fetchrow("SELECT * FROM starboard WHERE message=?", (message,))
        new = not data
        stars = 1 if new else data["stars"] + increase  # if _type == 1 else 0
        star_message = f"⭐ {stars} - <#{channel}>"
        if "minimum" not in __settings["starboard"] or not __settings["starboard"]["minimum"]:
            minimum = 3
        else:
            minimum = __settings["starboard"]["minimum"]
        if new and stars != 0:
            self.bot.db.execute("INSERT INTO starboard VALUES (?, ?, ?, ?, ?, ?)", (message, channel, _author, server, stars, None))
        # elif _type == 4:
        #     self.bot.db.execute("DELETE FROM starboard WHERE message=?", (message,))  # The message has been deleted, so also remove it from the database.
        #     logger.log(self.bot.name, "starboard", f"{time.time()} - Message ID {message} has been deleted.")
        else:
            # if _type == 1:
            self.bot.db.execute("UPDATE starboard SET stars=stars+? WHERE message=?", (increase, message))
            # else:
            #     self.bot.db.execute("UPDATE starboard SET stars=0 WHERE message=?", (increase, message))
        logger.log(self.bot.name, "starboard", f"{time.time()} > Message ID {message} in #{_channel.name} ({guild.name}) now has {stars} stars.")

        async def send_starboard_message():
            embed = discord.Embed(colour=0xffff00)
            author = _message.author
            author_name = author.name
            author_url = author.avatar_url_as(size=64, format="png")
            embed.set_author(name=author_name, icon_url=author_url)
            embed.description = _message.content
            if _message.attachments:
                att = _message.attachments[0]
                embed.set_image(url=att.url)
            embed.add_field(name=langs.gls("starboard_message_jump", locale), value=langs.gls("starboard_message_jump2", locale, _message.jump_url), inline=False)
            # embed.add_field(name="Jump to message", value=f"[Click here]({_message.jump_url})", inline=False)
            embed.set_footer(text=f"Message ID {message}")
            embed.timestamp = _message.created_at
            try:
                _starboard_message = await general.send(star_message, starboard_channel, embed=embed)
                self.bot.db.execute("UPDATE starboard SET star_message=? WHERE message=?", (_starboard_message.id, message))
                logger.log(self.bot.name, "starboard", f"{time.time()} > Saved Message ID {message} to starboard channel")
            except discord.Forbidden:
                try:
                    await general.send(langs.gls("starboard_error_message", locale), _channel)
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
                            await general.send(langs.gls("starboard_error_fetch", locale), _channel)
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
        # return await self.starboard_update(payload)
        # Delete the message from the database, but keep it on the starboard channel
        output = self.bot.db.execute("DELETE FROM starboard WHERE message=?", (payload.message_id,))
        if output != "DELETE 0":
            logger.log(self.bot.name, "starboard", f"{time.time()} > Reactions of Message ID {payload.message_id} were cleared.")

    @commands.Cog.listener()
    async def on_raw_reaction_clear_emoji(self, payload: discord.RawReactionClearEmojiEvent):
        """ An emote has been cleared from a message """
        # return await self.starboard_update(payload)
        if payload.emoji.name == "⭐":
            # Delete the message from the database, but keep it on the starboard channel
            output = self.bot.db.execute("DELETE FROM starboard WHERE message=?", (payload.message_id,))
            if output != "DELETE 0":
                logger.log(self.bot.name, "starboard", f"{time.time()} > Star reactions of Message ID {payload.message_id} were cleared.")

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        """ Message was deleted """
        # return await self.starboard_update(payload)
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
        if user is None:
            embed = discord.Embed(colour=general.random_colour())
            data = self.bot.db.fetch("SELECT * FROM starboard WHERE guild=? ORDER BY stars DESC", (ctx.guild.id,))
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
            embed.title = f"Starboard stats for {ctx.guild.name}"
            embed.description = f"⭐ **{stars:,} stars** across {len(data):,} messages"
            embed.set_thumbnail(url=ctx.guild.icon_url)
            top_messages = ""
            authors_out = ""
            # Top Starred Posts
            for i, _message in enumerate(top, start=1):
                # [<stars> by <author>](link)
                # try:
                #     message = await self.bot.get_channel(_message["channel"]).fetch_message(_message["message"])
                jump_url = f"https://discord.com/channels/{_message['guild']}/{_message['channel']}/{_message['message']}"
                top_messages += f"\n{i}) ⭐ {_message['stars']} - {self.find_user(_message['author'])} - [#{self.bot.get_channel(_message['channel'])}]({jump_url})"
                # except (discord.NotFound, AttributeError):
                #     embed.description += f"\n{i + 1}) ⭐ {_message['stars']} Deleted message"
            for i, _data in enumerate(authors_sorted.items(), start=1):
                if i <= 5:
                    _uid, _stars = _data
                    authors_out += f"\n{i}) ⭐ {_stars} - <@{_uid}>"
            if top_messages:
                embed.add_field(name="Top starred messages", value=top_messages, inline=False)
            if authors_out:
                embed.add_field(name="Top message authors", value=authors_out, inline=False)
            return await general.send(None, ctx.channel, embed=embed)
        else:
            embed = discord.Embed(colour=general.random_colour())
            data = self.bot.db.fetch("SELECT * FROM starboard WHERE guild=? AND author=? ORDER BY stars DESC", (ctx.guild.id, user.id))
            stars = 0
            top = []
            for i, message in enumerate(data):
                # message = data[i]
                if i < 10:
                    top.append(message)
                stars += message["stars"]
            embed.title = f"Starboard stats for {user} in {ctx.guild.name}"
            embed.description = f"Received ⭐ **{stars:,} stars** across {len(data):,} messages\n\nTop messages:"
            embed.set_thumbnail(url=user.avatar_url)
            for i, _message in enumerate(top, start=1):
                jump_url = f"https://discord.com/channels/{_message['guild']}/{_message['channel']}/{_message['message']}"
                embed.description += f"\n{i}) ⭐ {_message['stars']} - [#{self.bot.get_channel(_message['channel'])}]({jump_url})"
            return await general.send(None, ctx.channel, embed=embed)


def setup(bot):
    bot.add_cog(Starboard(bot))
