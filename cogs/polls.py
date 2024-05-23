import json

import discord

from utils import bot_data, commands, general, time


class Polls(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot

    @commands.group(name="poll", aliases=["polls"], case_insensitive=True, invoke_without_command=True, enabled=False)
    @commands.guild_only()
    # @commands.check(lambda ctx: ctx.guild is not None and ctx.guild.id in [869975256566210641, 738425418637639775])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def poll(self, ctx: commands.Context, duration: str, *, question: str):
        """ Start a new poll or interact with existing ones

        Duration: s = seconds, m = minutes, h = hours, d = days, w = weeks
        Example: 2d12h = 2 days and 12 hours | 15m = 15 minutes
        Recommended duration: 1-6 hours | Limit: 1 week"""
        await ctx.send("Warning: This command will be disabled on 1 March 2024!")
        if ctx.invoked_subcommand is None:
            language = self.bot.language(ctx)
            delta = time.interpret_time(duration)
            expiry, error = time.add_time(delta)
            if time.rd_is_above_1w(delta):
                return await ctx.send(language.string("polls_length_limit"))
            if ctx.guild.id == 869975256566210641:  # Nuriki server
                if time.rd_is_below_1h(delta):
                    return await ctx.send(language.string("polls_length_limit2"))
                # if 929035370623037500 not in [role.id for role in ctx.author.roles]:  # Anarchist
                #     return await ctx.send("You need the Anarchist role to start new polls or vote in existing ones.")
            if error:
                return await ctx.send(language.string("polls_length_error", err=expiry))
            _question = general.reason(ctx.author, question)
            _duration = language.delta_rd(delta, accuracy=4, brief=False, affix=False)
            _expiry = language.time(expiry, short=1, dow=False, seconds=False, tz=True)
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
            # TODO: Rewrite this to just use PRIMARY KEY instead...
            poll_id = general.random_id2()
            while self.bot.db.fetchrow("SELECT poll_id FROM polls WHERE poll_id=?", (poll_id,)):
                poll_id = general.random_id2()
            embed.description = language.string("polls_new_description", id=poll_id, question=_question, duration=_duration, time=_expiry)
            embed.set_footer(text=language.string("polls_new_footer", p=ctx.prefix, id=poll_id))
            embed.add_field(name=language.string("polls_votes_current"), inline=False,
                            value=language.string("polls_votes_current2", yes=0, neutral=0, no=0, total=0, score=0, percentage=language.number(0, precision=2, percentage=True)))
            if not poll_anonymity:
                embed.add_field(name=language.string("polls_votes_yes"), value=language.string("polls_votes_none"), inline=True)
                embed.add_field(name=language.string("polls_votes_neutral"), value=language.string("polls_votes_none"), inline=True)
                embed.add_field(name=language.string("polls_votes_no"), value=language.string("polls_votes_none"), inline=True)
            content = "<@&880091178559737946>" if ctx.guild.id == 869975256566210641 else None
            message = await poll_channel.send(content, embed=embed)
            self.bot.db.execute("INSERT INTO polls VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (ctx.guild.id, poll_channel.id, message.id, poll_id, _question, "[]", "[]", "[]", expiry, poll_anonymity))
            return await ctx.send(language.string("polls_new_success", author=ctx.author.name))

    @poll.command(name="vote", enabled=False)
    async def poll_vote(self, ctx: commands.Context, poll_id: int, response: str):
        """ Vote on a poll """
        language = self.bot.language(ctx)
        response = response.lower()
        if response not in ["yes", "neutral", "no"]:
            return await ctx.send(language.string("polls_vote_invalid"))

        # Nuriki server - Anarchist role
        # if ctx.guild.id == 869975256566210641 and 929035370623037500 not in [role.id for role in ctx.author.roles]:
        #     return await ctx.send("You need the Anarchist role to vote in polls.")
        data = self.bot.db.fetchrow("SELECT * FROM polls WHERE poll_id=? OR message_id=?", (poll_id, poll_id))
        if not data:
            return await ctx.send(language.string("polls_not_found", id=poll_id))
        voters_yes: list = json.loads(data["voters_yes"])
        voters_neutral: list = json.loads(data["voters_neutral"])
        voters_no: list = json.loads(data["voters_no"])
        voted_yes, voted_neutral, voted_no = response == "yes", response == "neutral", response == "no"
        if ctx.author.id in voters_yes:
            if voted_yes:
                return await ctx.send(language.string("polls_vote_already_yes"))
            voters_yes.remove(ctx.author.id)
        if ctx.author.id in voters_neutral:
            if voted_neutral:
                return await ctx.send(language.string("polls_vote_already_neutral"))
            voters_neutral.remove(ctx.author.id)
        if ctx.author.id in voters_no:
            if voted_no:
                return await ctx.send(language.string("polls_vote_already_no"))
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
                                           value=language.string("polls_votes_current2", yes=language.number(yes), neutral=language.number(neutral), no=language.number(no),
                                                                 total=language.number(total), score=language.number(score, positives=True),
                                                                 percentage=language.number(upvotes, precision=2, percentage=True)))
                        if 3 >= score > 0:
                            embed.colour = general.green2
                        elif score > 3:
                            embed.colour = general.green
                        elif -3 <= score < 0:
                            embed.colour = general.red2
                        elif score < -3:
                            embed.colour = general.red
                        else:
                            embed.colour = general.yellow
                        if not anonymous:
                            _yes = "\n".join([f"<@{voter}>" for voter in voters_yes[:45]])
                            if yes >= 45:
                                _yes += language.string("polls_votes_many", val=language.number(yes - 45))
                            if not _yes:
                                _yes = language.string("polls_votes_none")
                            embed.set_field_at(1, name=language.string("polls_votes_yes"), value=_yes, inline=True)
                            _neutral = "\n".join([f"<@{voter}>" for voter in voters_neutral[:45]])
                            if neutral >= 45:
                                _neutral += language.string("polls_votes_many", val=language.number(neutral - 45))
                            if not _neutral:
                                _neutral = language.string("polls_votes_none")
                            embed.set_field_at(2, name=language.string("polls_votes_neutral"), value=_neutral, inline=True)
                            _no = "\n".join([f"<@{voter}>" for voter in voters_no[:45]])
                            if no >= 45:
                                _no += language.string("polls_votes_many", val=language.number(no - 45))
                            if not _no:
                                _no = language.string("polls_votes_none")
                            embed.set_field_at(3, name=language.string("polls_votes_no"), value=_no, inline=True)
                        await message.edit(embed=embed)
                except (discord.NotFound, discord.Forbidden):
                    pass  # The vote was counted anyways, and it's their own fault for not letting the message show up...
        return await ctx.send(language.string("polls_vote_success"))

    @poll.command(name="status", aliases=["stats", "info"], enabled=False)
    async def poll_status(self, ctx: commands.Context, poll_id: int):
        """ See the status of an ongoing poll """
        language = self.bot.language(ctx)
        data = self.bot.db.fetchrow("SELECT * FROM polls WHERE poll_id=? OR message_id=?", (poll_id, poll_id))
        if not data:
            return await ctx.send(language.string("polls_not_found", id=poll_id))
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
        if 3 >= score > 0:
            colour = general.green2
        elif score > 3:
            colour = general.green
        elif -3 <= score < 0:
            colour = general.red2
        elif score < -3:
            colour = general.red
        else:
            colour = general.yellow
        embed = discord.Embed(colour=colour)
        embed.title = language.string("polls_status_title", id=data["poll_id"])
        ends = language.time(data["expiry"], short=1, dow=False, seconds=False, tz=True, uid=ctx.author.id)
        ends_in = language.delta_dt(data["expiry"], accuracy=3, brief=False, affix=True)
        embed.description = language.string("polls_status_description", question=data["question"], time=ends, delta=ends_in)
        embed.add_field(name=language.string("polls_votes_current"), inline=False,
                        value=language.string("polls_votes_current2", yes=language.number(yes), neutral=language.number(neutral), no=language.number(no),
                                              total=language.number(total), score=language.number(score, positives=True),
                                              percentage=language.number(upvotes, precision=2, percentage=True)))
        return await ctx.send(embed=embed)

    @poll.command(name="list", enabled=False)
    async def poll_list(self, ctx: commands.Context):
        """ List all ongoing polls in this server """
        language = self.bot.language(ctx)
        polls = self.bot.db.fetch("SELECT * FROM polls WHERE guild_id=? ORDER BY expiry", (ctx.guild.id,))
        if not polls:
            return await ctx.send(language.string("polls_list_none"))
        output = []
        for i, poll in enumerate(polls, start=1):
            ends = language.time(poll["expiry"], short=1, dow=False, seconds=False, tz=True, uid=ctx.author.id)
            ends_in = language.delta_dt(poll["expiry"], accuracy=3, brief=False, affix=True)
            output.append(language.string("polls_list_entry", i=language.number(i, commas=False), id=poll["poll_id"], question=poll["question"], time=ends, delta=ends_in))
        return await ctx.send(language.string("polls_list", server=ctx.guild.name, data="\n\n".join(output)))


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Polls(bot))
