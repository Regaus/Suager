import json

import discord
from discord.ext import commands

from utils import bot_data, general, time


class Polls(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.group(name="poll", aliases=["polls"], case_insensitive=True, invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def poll(self, ctx: commands.Context, duration: str, *, question: str):
        """ Start a new poll or interact with existing ones

        Duration: s = seconds, m = minutes, h = hours, d = days, w = weeks
        Example: 2d12h = 2 days and 12 hours | 15m = 15 minutes
        Recommended duration: 1-6 hours | Limit: 1 week"""
        if ctx.invoked_subcommand is None:
            language = self.bot.language(ctx)
            delta = time.interpret_time(duration)
            expiry, error = time.add_time(delta)
            if time.rd_is_above_1w(delta):
                return await general.send(language.string("polls_length_limit"), ctx.channel)
            if error:
                return await general.send(language.string("polls_length_error", expiry), ctx.channel)
            _question = general.reason(ctx.author, question)
            _duration = language.delta_rd(delta, accuracy=4, brief=False, affix=False)
            _expiry = language.time(expiry, short=1, dow=False, seconds=False, tz=False)
            poll_channel: discord.TextChannel = ctx.channel
            poll_anonymity = True
            data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
            if data:
                settings = json.loads(data["data"])
                if "polls" in settings:
                    polls = settings["polls"]
                    if polls["channel"]:
                        poll_channel: discord.TextChannel = ctx.guild.get_channel(polls["channel"])
                        if not poll_channel:
                            poll_channel = ctx.channel
                    poll_anonymity = polls["voter_anonymity"]
            embed = discord.Embed(colour=general.yellow)
            embed.title = language.string("polls_new_title")
            poll_id = general.random_id2()
            while self.bot.db.fetchrow("SELECT poll_id FROM polls WHERE poll_id=?", (poll_id,)):
                poll_id = general.random_id2()
            embed.description = language.string("polls_new_description", poll_id, _question, _duration, _expiry)
            embed.set_footer(text=language.string("polls_new_footer", ctx.prefix, poll_id))
            embed.add_field(name=language.string("polls_votes_current"), inline=False,
                            value=language.string("polls_votes_current2", 0, 0, 0, 0, 0, language.number(0, precision=2, percentage=True)))
            if not poll_anonymity:
                embed.add_field(name=language.string("polls_votes_yes"), value=language.string("polls_votes_none"), inline=True)
                embed.add_field(name=language.string("polls_votes_neutral"), value=language.string("polls_votes_none"), inline=True)
                embed.add_field(name=language.string("polls_votes_no"), value=language.string("polls_votes_none"), inline=True)
            message = await general.send(None, poll_channel, embed=embed)
            self.bot.db.execute("INSERT INTO polls VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (ctx.guild.id, poll_channel.id, message.id, poll_id, _question, "[]", "[]", "[]", expiry, poll_anonymity))
            return await general.send(language.string("polls_new_success", ctx.author.name), ctx.channel)

    @poll.command(name="vote")
    async def poll_vote(self, ctx: commands.Context, poll_id: int, response: str):
        """ Vote on a poll """
        language = self.bot.language(ctx)
        response = response.lower()
        if response not in ["yes", "neutral", "no"]:
            return await general.send(language.string("polls_vote_invalid"), ctx.channel)
        data = self.bot.db.fetchrow("SELECT * FROM polls WHERE poll_id=? OR message_id=?", (poll_id, poll_id))
        if not data:
            return await general.send(language.string("polls_not_found", poll_id), ctx.channel)
        voters_yes: list = json.loads(data["voters_yes"])
        voters_neutral: list = json.loads(data["voters_neutral"])
        voters_no: list = json.loads(data["voters_no"])
        voted_yes, voted_neutral, voted_no = response == "yes", response == "neutral", response == "no"
        if ctx.author.id in voters_yes:
            if voted_yes:
                return await general.send(language.string("polls_vote_already_yes"), ctx.channel)
            voters_yes.remove(ctx.author.id)
        if ctx.author.id in voters_neutral:
            if voted_neutral:
                return await general.send(language.string("polls_vote_already_neutral"), ctx.channel)
            voters_neutral.remove(ctx.author.id)
        if ctx.author.id in voters_no:
            if voted_no:
                return await general.send(language.string("polls_vote_already_no"), ctx.channel)
            voters_no.remove(ctx.author.id)
        if voted_yes:
            voters_yes.append(ctx.author.id)
        if voted_neutral:
            voters_neutral.append(ctx.author.id)
        if voted_no:
            voters_no.append(ctx.author.id)
        self.bot.db.execute("UPDATE polls SET voters_yes=?, voters_neutral=?, voters_no=? WHERE poll_id=?",
                            (json.dumps(voters_yes), json.dumps(voters_neutral), json.dumps(voters_no), data["poll_id"]))
        anonymous = data["anonymous"]
        guild_id, channel_id, message_id = data["guild_id"], data["channel_id"], data["message_id"]
        guild: discord.Guild = self.bot.get_guild(guild_id)
        if guild:
            channel: discord.TextChannel = guild.get_channel(channel_id)
            if channel:
                try:
                    message: discord.Message = await channel.fetch_message(message_id)
                    if message.embeds:
                        embed = message.embeds[0]
                        yes, neutral, no = len(voters_yes), len(voters_neutral), len(voters_no)
                        total = yes + neutral + no
                        score = yes - no
                        try:
                            upvotes = yes / (yes + no)
                        except ZeroDivisionError:
                            upvotes = 0
                        embed.set_field_at(0, name=language.string("polls_votes_current"), inline=False,
                                           value=language.string("polls_votes_current2", language.number(yes), language.number(neutral), language.number(no),
                                                                 language.number(total), language.number(score), language.number(upvotes, precision=2, percentage=True)))
                        if score > 0:
                            embed.colour = general.green
                        elif score < 0:
                            embed.colour = general.red
                        else:
                            embed.colour = general.yellow
                        if not anonymous:
                            _yes = "\n".join([f"<@{voter}>" for voter in voters_yes[:45]])
                            if yes >= 45:
                                _yes += language.string("polls_votes_many", language.number(yes - 45))
                            if not _yes:
                                _yes = language.string("polls_votes_none")
                            embed.set_field_at(1, name=language.string("polls_votes_yes"), value=_yes, inline=True)
                            _neutral = "\n".join([f"<@{voter}>" for voter in voters_neutral[:45]])
                            if neutral >= 45:
                                _neutral += language.string("polls_votes_many", language.number(neutral - 45))
                            if not _neutral:
                                _neutral = language.string("polls_votes_none")
                            embed.set_field_at(2, name=language.string("polls_votes_neutral"), value=_neutral, inline=True)
                            _no = "\n".join([f"<@{voter}>" for voter in voters_no[:45]])
                            if no >= 45:
                                _no += language.string("polls_votes_many", language.number(no - 45))
                            if not _no:
                                _no = language.string("polls_votes_none")
                            embed.set_field_at(3, name=language.string("polls_votes_no"), value=_no, inline=True)
                        await message.edit(embed=embed)
                except (discord.NotFound, discord.Forbidden):
                    pass  # The vote was counted anyways, and it's their own fault for not letting the message show up...
        return await general.send(language.string("polls_vote_success"), ctx.channel)

    @poll.command(name="status", aliases=["stats", "info"])
    async def poll_status(self, ctx: commands.Context, poll_id: int):
        """ See the status of an ongoing poll """
        language = self.bot.language(ctx)
        data = self.bot.db.fetchrow("SELECT * FROM polls WHERE poll_id=? OR message_id=?", (poll_id, poll_id))
        if not data:
            return await general.send(language.string("polls_not_found", poll_id), ctx.channel)
        voters_yes: list = json.loads(data["voters_yes"])
        voters_neutral: list = json.loads(data["voters_neutral"])
        voters_no: list = json.loads(data["voters_no"])
        yes, neutral, no = len(voters_yes), len(voters_neutral), len(voters_no)
        total = yes + neutral + no
        score = yes - no
        try:
            upvotes = yes / (yes + no)
        except ZeroDivisionError:
            upvotes = 0
        if score > 0:
            colour = general.green
        elif score < 0:
            colour = general.red
        else:
            colour = general.yellow
        embed = discord.Embed(colour=colour)
        embed.title = language.string("polls_status_title", data["poll_id"])
        ends = language.time(data["expiry"], short=1, dow=False, seconds=False, tz=False)
        ends_in = language.delta_dt(data["expiry"], accuracy=3, brief=False, affix=True)
        embed.description = language.string("polls_status_description", data["question"], ends, ends_in)
        embed.add_field(name=language.string("polls_votes_current"), inline=False,
                        value=language.string("polls_votes_current2", language.number(yes), language.number(neutral), language.number(no),
                                              language.number(total), language.number(score), language.number(upvotes, precision=2, percentage=True)))
        return await general.send(None, ctx.channel, embed=embed)

    @poll.command(name="list")
    async def poll_list(self, ctx: commands.Context):
        """ List all polls for this server """
        language = self.bot.language(ctx)
        polls = self.bot.db.fetch("SELECT * FROM polls WHERE guild_id=?", (ctx.guild.id,))
        if not polls:
            return await general.send(language.string("polls_list_none"), ctx.channel)
        output = []
        for i, poll in enumerate(polls, start=1):
            ends = language.time(poll["expiry"], short=1, dow=False, seconds=False, tz=False)
            ends_in = language.delta_dt(poll["expiry"], accuracy=3, brief=False, affix=True)
            output.append(language.string("polls_list_entry", language.number(i, commas=False), poll["poll_id"], poll["question"], ends, ends_in))
        return await general.send(language.string("polls_list", ctx.guild.name, "\n\n".join(output)), ctx.channel)


def setup(bot: bot_data.Bot):
    bot.add_cog(Polls(bot))
