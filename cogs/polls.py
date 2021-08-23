import json

import discord
from discord.ext import commands
from discord.guild import BanEntry

from cogs.mod import MemberID
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
            if ctx.guild.id == 869975256566210641:
                if time.rd_is_below_1h(delta):
                    return await general.send(language.string("polls_length_limit2"), ctx.channel)
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
                                                                 language.number(total), language.number(score, positives=True),
                                                                 language.number(upvotes, precision=2, percentage=True)))
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
        embed.title = language.string("polls_status_title", data["poll_id"])
        ends = language.time(data["expiry"], short=1, dow=False, seconds=False, tz=False)
        ends_in = language.delta_dt(data["expiry"], accuracy=3, brief=False, affix=True)
        embed.description = language.string("polls_status_description", data["question"], ends, ends_in)
        embed.add_field(name=language.string("polls_votes_current"), inline=False,
                        value=language.string("polls_votes_current2", language.number(yes), language.number(neutral), language.number(no),
                                              language.number(total), language.number(score, positives=True), language.number(upvotes, precision=2, percentage=True)))
        return await general.send(None, ctx.channel, embed=embed)

    @poll.command(name="list")
    async def poll_list(self, ctx: commands.Context):
        """ List all ongoing polls in this server """
        language = self.bot.language(ctx)
        polls = self.bot.db.fetch("SELECT * FROM polls WHERE guild_id=? ORDER BY expiry", (ctx.guild.id,))
        if not polls:
            return await general.send(language.string("polls_list_none"), ctx.channel)
        output = []
        for i, poll in enumerate(polls, start=1):
            ends = language.time(poll["expiry"], short=1, dow=False, seconds=False, tz=False)
            ends_in = language.delta_dt(poll["expiry"], accuracy=3, brief=False, affix=True)
            output.append(language.string("polls_list_entry", language.number(i, commas=False), poll["poll_id"], poll["question"], ends, ends_in))
        return await general.send(language.string("polls_list", ctx.guild.name, "\n\n".join(output)), ctx.channel)

    @commands.group(name="trial", aliases=["trials"], case_insensitive=True, invoke_without_command=True)
    @commands.guild_only()
    @commands.check(lambda ctx: ctx.guild.id in [869975256566210641, 738425418637639775])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def trial(self, ctx: commands.Context, duration: str, action: str, user: MemberID, *, reason: str = None):
        """ Start a new trial to take action against a user or interact with existing ones
        Supported actions: mute, unmute, kick, ban, unban
        For muting, you can specify the length of the mute, or only specify a reason if you with to mute permanently
        Mute length limit: 30 days

        Duration: s = seconds, m = minutes, h = hours, d = days, w = weeks
        Example: 2d12h = 2 days and 12 hours | 15m = 15 minutes
        Recommended duration: 1-6 hours | Limits: min 15 minutes, max 1 week

        How to use:
        //trial 1h ban @user Doing something very bad
        //trial 1w unban @user He wasn't that bad after all
        //trial 30m mute @user 1h Spamming

        You can only start a new trial once every 5 minutes."""
        if ctx.invoked_subcommand is None:
            language = self.bot.language(ctx)
            if user == ctx.author.id:
                return await general.send(language.string("trials_user_self"), ctx.channel)
            try:
                _user = await self.bot.fetch_user(user)
            except discord.NotFound:
                return await general.send(language.string("trials_user_none", user), ctx.channel)
            action = action.lower()
            if action not in ["mute", "unmute", "kick", "ban", "unban"]:
                return await general.send(language.string("trials_action_invalid"), ctx.channel)
            if action in ["ban", "unban"]:
                try:
                    bans: list[BanEntry] = await ctx.guild.bans()
                    banned = False
                    for ban in bans:
                        if ban.user.id == user:
                            banned = True
                            break
                    if action == "ban" and banned:
                        return await general.send(language.string("trials_new_fail_ban"), ctx.channel)
                    if action == "unban" and not banned:
                        return await general.send(language.string("trials_new_fail_unban"), ctx.channel)
                except discord.Forbidden:
                    pass  # Can't check current bans
            poll_anonymity = True
            mute_role: None = None
            data = self.bot.db.fetchrow("SELECT * FROM settings WHERE gid=? AND bot=?", (ctx.guild.id, self.bot.name))
            if data:
                settings = json.loads(data["data"])
                if "polls" in settings:
                    polls = settings["polls"]
                    poll_anonymity = polls["voter_anonymity"]
                if "mute_role" in settings:
                    if settings["mute_role"]:
                        mute_role: discord.Role = ctx.guild.get_role(settings["mute_role"])
                        if not mute_role:
                            if action in ["mute", "unmute"]:
                                return await general.send(language.string("trials_new_fail_mute2"), ctx.channel)
            if action in ["kick", "mute", "unmute"]:
                member: discord.Member = ctx.guild.get_member(user)
                if not member:
                    return await general.send(language.string("trials_new_fail_kick"), ctx.channel)
                muted = mute_role in member.roles
                if action == "mute" and muted:
                    await general.send(language.string("trials_new_fail_mute"), ctx.channel, delete_after=30)
                if action == "unmute" and not muted:
                    return await general.send(language.string("trials_new_fail_unmute"), ctx.channel)
            now_ts = time.now_ts()
            recent = self.bot.db.fetchrow("SELECT * FROM trials WHERE author_id=? AND start_time>?", (ctx.author.id, now_ts - 300))
            if recent:
                wait = language.delta_ts(recent["start_time"] + 300, accuracy=3, brief=False, affix=False)
                return await general.send(language.string("trials_already_recent", wait), ctx.channel)
            action_text = {
                "ban": "trials_action_ban",
                "kick": "trials_action_kick",
                "mute": "trials_action_mute",
                "unban": "trials_action_unban",
                "unmute": "trials_action_unmute"
            }.get(action, "generic_unknown")
            already = self.bot.db.fetchrow("SELECT * FROM trials WHERE user_id=? AND type=?", (user, action))
            if already:
                return await general.send(language.string("trials_already", language.string(action_text, _user), ctx.prefix, already["trial_id"]), ctx.channel)
            delta = time.interpret_time(duration)
            expiry, error = time.add_time(delta)
            if time.rd_is_above_1w(delta):
                return await general.send(language.string("trials_length_limit_max"), ctx.channel)
            if time.rd_is_below_15m(delta):
                return await general.send(language.string("trials_length_limit_min"), ctx.channel)
            if error:
                return await general.send(language.string("trials_length_error", expiry), ctx.channel)
            mute_duration = 0
            _duration2 = ""
            if action == "mute":
                _mute_duration = reason.split(" ")[0]
                _delta = time.interpret_time(_mute_duration)
                _expiry, _error = time.add_time(_delta)
                if time.rd_is_above_30d(_delta):
                    return await general.send(language.string("trials_length_limit_mute"), ctx.channel)
                # if _error:
                #    return await general.send(language.string("trials_length_error2", _expiry), ctx.channel)
                if not _error:
                    mute_duration = int((_expiry - time.now2()).total_seconds())
                    reason = " ".join(reason.split(" ")[1:])
                    _duration2 = language.delta_rd(_delta, accuracy=6, brief=False, affix=False)
                else:
                    mute_duration = 0
                    await general.send(language.string("trials_length_error2"), ctx.channel, delete_after=30)
            reason = reason or language.string("mod_reason_none")
            _reason = general.reason(ctx.author, reason)
            _duration = language.delta_rd(delta, accuracy=4, brief=False, affix=False)
            _expiry = language.time(expiry, short=1, dow=False, seconds=False, tz=False)
            if ctx.guild.id == 869975256566210641:
                poll_channel: discord.TextChannel = self.bot.get_channel(871811287166898187)
            else:
                poll_channel: discord.TextChannel = ctx.channel
            talked = self.bot.db.fetch("SELECT * FROM leveling WHERE last>? AND gid=?", (int(now_ts) - 21600, ctx.guild.id))  # All users who have talked within the last 6 hours
            required = round(len(talked) * 0.4)  # 40% of the people who've talked in the last 6 hours
            if required < 3:
                required = 3  # 3 is the minimum requirement to do anything
            _required = language.number(required, positives=True)
            embed = discord.Embed(colour=general.yellow)
            embed.title = language.string("trials_new_title")
            trial_id = general.random_id2()
            while self.bot.db.fetchrow("SELECT trial_id FROM trials WHERE trial_id=?", (trial_id,)):
                trial_id = general.random_id2()
            if mute_duration:
                embed.description = language.string("trials_new_description2", trial_id, language.string(action_text, _user), _reason, _duration, _expiry, _duration2)
            else:
                embed.description = language.string("trials_new_description", trial_id, language.string(action_text, _user), _reason, _duration, _expiry)
            embed.set_footer(text=language.string("trials_new_footer", ctx.prefix, trial_id))
            zero = language.number(0)
            embed.add_field(name=language.string("trials_votes_current"), inline=False,
                            value=language.string("trials_votes_current2", zero, zero, zero, zero, zero, language.number(0, precision=2, percentage=True), _required))
            if not poll_anonymity:
                embed.add_field(name=language.string("polls_votes_yes"), value=language.string("polls_votes_none"), inline=True)
                embed.add_field(name=language.string("polls_votes_neutral"), value=language.string("polls_votes_none"), inline=True)
                embed.add_field(name=language.string("polls_votes_no"), value=language.string("polls_votes_none"), inline=True)
            message = await general.send(None, poll_channel, embed=embed)
            self.bot.db.execute(f"INSERT INTO trials VALUES ({'?, ' * 15}?)",
                                (ctx.guild.id, poll_channel.id, message.id, trial_id, ctx.author.id, user, action, mute_duration, _reason,
                                 "[]", "[]", "[]", now_ts, expiry, poll_anonymity, required))
            return await general.send(language.string("trials_new_success"), ctx.channel)

    @trial.command(name="vote")
    async def trial_vote(self, ctx: commands.Context, trial_id: int, response: str):
        """ Vote on a trial """
        language = self.bot.language(ctx)
        response = response.lower()
        if response not in ["yes", "neutral", "no"]:
            return await general.send(language.string("polls_vote_invalid"), ctx.channel)
        data = self.bot.db.fetchrow("SELECT * FROM trials WHERE trial_id=? OR message_id=? OR user_id=?", (trial_id, trial_id, trial_id))
        if not data:
            return await general.send(language.string("trials_not_found", trial_id), ctx.channel)
        if data["user_id"] == ctx.author.id:
            return await general.send(language.string("trials_user_self2"), ctx.channel)
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
        self.bot.db.execute("UPDATE trials SET voters_yes=?, voters_neutral=?, voters_no=? WHERE trial_id=?",
                            (json.dumps(voters_yes), json.dumps(voters_neutral), json.dumps(voters_no), data["trial_id"]))
        anonymous = data["anonymous"]
        yes, neutral, no = len(voters_yes), len(voters_neutral), len(voters_no)
        total = yes + neutral + no
        score = yes - no
        try:
            upvotes = yes / (yes + no)
        except ZeroDivisionError:
            upvotes = 0
        required = data["required_score"]
        guild_id, channel_id, message_id = data["guild_id"], data["channel_id"], data["message_id"]
        if score >= (required * 2) and upvotes >= 0.9:
            # Give 15 seconds grace for just in case
            self.bot.db.execute("UPDATE trials SET expiry=? WHERE trial_id=?", (time.now2() + time.td(seconds=15), trial_id))
        guild: discord.Guild = self.bot.get_guild(guild_id)
        if guild:
            if guild_id == 869975256566210641 and data["type"] in ["mute", "kick", "ban"]:
                _member = ctx.guild.get_member(data["user_id"])
                if _member:
                    if score >= required and upvotes >= 0.6:
                        await _member.add_roles(ctx.guild.get_role(870338399922446336), reason="Trial in progress")  # Give the On Trial role
                        await _member.remove_roles(ctx.guild.get_role(869975498799845406), reason="Trial in progress")  # Revoke the Anarchists role
                    else:
                        await _member.remove_roles(ctx.guild.get_role(870338399922446336), reason="Trial in progress")  # Remove the On Trial role
                        await _member.add_roles(ctx.guild.get_role(869975498799845406), reason="Trial in progress")  # Give the Anarchists role
            channel: discord.TextChannel = guild.get_channel(channel_id)
            if channel:
                try:
                    message: discord.Message = await channel.fetch_message(message_id)
                    if message.embeds:
                        embed = message.embeds[0]
                        embed.set_field_at(0, name=language.string("trials_votes_current"), inline=False,
                                           value=language.string("trials_votes_current2", language.number(yes), language.number(neutral), language.number(no),
                                                                 language.number(total), language.number(score, positives=True),
                                                                 language.number(upvotes, precision=2, percentage=True), language.number(required, positives=True)))
                        if required > score > 0:
                            embed.colour = general.green2
                        elif score >= required:
                            embed.colour = general.green
                        elif -required < score < 0:
                            embed.colour = general.red2
                        elif score <= -required:
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

    @trial.command(name="status", aliases=["stats", "info"])
    async def trial_status(self, ctx: commands.Context, trial_id: int):
        """ See the status of an ongoing trial """
        language = self.bot.language(ctx)
        data = self.bot.db.fetchrow("SELECT * FROM trials WHERE trial_id=? OR message_id=? OR user_id=?", (trial_id, trial_id, trial_id))
        if not data:
            return await general.send(language.string("trials_not_found", trial_id), ctx.channel)
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
        required = data["required_score"]
        if required > score > 0:
            colour = general.green2
        elif score >= required:
            colour = general.green
        elif -required < score < 0:
            colour = general.red2
        elif score <= -required:
            colour = general.red
        else:
            colour = general.yellow
        embed = discord.Embed(colour=colour)
        embed.title = language.string("trials_status_title", data["trial_id"])
        ends = language.time(data["expiry"], short=1, dow=False, seconds=False, tz=False)
        ends_in = language.delta_dt(data["expiry"], accuracy=3, brief=False, affix=True)
        action_text = {
            "ban": "trials_action_ban",
            "kick": "trials_action_kick",
            "mute": "trials_action_mute",
            "unban": "trials_action_unban",
            "unmute": "trials_action_unmute"
        }.get(data["type"], "generic_unknown")
        user = await self.bot.fetch_user(data["user_id"])
        if data["type"] == "mute" and data["mute_length"]:
            _duration = language.delta_int(data["mute_length"], accuracy=3, brief=False, affix=False)
            embed.description = language.string("trials_status_description2", language.string(action_text, user), data["reason"], ends, ends_in, _duration)
        else:
            embed.description = language.string("trials_status_description", language.string(action_text, user), data["reason"], ends, ends_in)
        embed.add_field(name=language.string("trials_votes_current"), inline=False,
                        value=language.string("trials_votes_current2", language.number(yes), language.number(neutral), language.number(no),
                                              language.number(total), language.number(score, positives=True),
                                              language.number(upvotes, precision=2, percentage=True), language.number(required, positives=True)))
        return await general.send(None, ctx.channel, embed=embed)

    @trial.command(name="list")
    async def trial_list(self, ctx: commands.Context):
        """ List all ongoing trials in this server """
        language = self.bot.language(ctx)
        trials = self.bot.db.fetch("SELECT * FROM trials WHERE guild_id=? ORDER BY expiry", (ctx.guild.id,))
        if not trials:
            return await general.send(language.string("trials_list_none"), ctx.channel)
        output = []
        for i, trial in enumerate(trials, start=1):
            ends = language.time(trial["expiry"], short=1, dow=False, seconds=False, tz=False)
            ends_in = language.delta_dt(trial["expiry"], accuracy=3, brief=False, affix=True)
            action_text = {
                "ban": "trials_action_ban",
                "kick": "trials_action_kick",
                "mute": "trials_action_mute",
                "unban": "trials_action_unban",
                "unmute": "trials_action_unmute"
            }.get(trial["type"], "generic_unknown")
            user = await self.bot.fetch_user(trial["user_id"])
            output.append(language.string("trials_list_entry", language.number(i, commas=False), trial["trial_id"], language.string(action_text, user),
                                          ends, ends_in, trial["reason"]))
        return await general.send(language.string("trials_list", ctx.guild.name, "\n\n".join(output)), ctx.channel)


def setup(bot: bot_data.Bot):
    bot.add_cog(Polls(bot))
