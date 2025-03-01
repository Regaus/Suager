# Code adapted from: https://github.com/okbuddyhololive/polkabot
import discord
from aiohttp import ClientSession

from utils import bot_data, commands, general, pretender, database


class Pretender(commands.Cog):
    def __init__(self, bot: bot_data.Bot):
        self.bot = bot
        self.db = database.Database("pretender.db")  # Pretender uses a separate database
        # Whitelist:      SL: general,        elite-lounge,       secret-room-2,      secret-room-3,      secret-room-8,      secret-room-15
        # Whitelist:      RK general,         Alex: general,      gamer-hub,          Satan Rib general
        # Whitelist:      SPHG: general,      memes,              computers-and-int,  software-and-junk,  animation,          random-art
        # Whitelist:      SPHG: shrek-anime,  edge-posters-vomit, OB: general,         cars
        # Whitelist:      Huskie's: general,  memes,               video-games,         images,              art,                 some-stuff
        # Whitelist:      Huskie's: gun-talk,  for-the-lonelies,    cursed,              quotes,              cars
        # Whitelist:      DanFanClub: general, chitterzone,       danzone,            mrdan-gaming-rig,  glaucoma-interception, manosphere
        # Whitelist:      DanFanClub: dangames-chitter, cosmic-owl, the-daily-tony,   the-foodaloo-channel, field-operations,  the-bit-list,        the-gym
        self.whitelist = [568148147457490958, 658112535656005663, 672535025698209821, 681647810357362786, 725835449502924901, 969720792457822219,
                          738425419325243424, 857504678371917855, 917150209149141042, 872464449255125033,
                          878332203094913025, 582110154170826755, 805519707045232692, 770529037566738443, 805510833764565042, 878335070996418600,
                          862397829087887361, 828742737493884968, 1086802718011695194, 1078443562611511498,
                          858493124727668737, 1013930855988736050, 1047179515174064139, 1013930827941425204, 1037347886263959673, 1020066152187183154,
                          1020374953956233327, 1047557126907777024, 1051896581571477524, 1063979467510390834, 1069642573611815033,
                          895443182798663743, 823730078507728918, 823727366852968529, 727244938277945415, 889536962044784710, 1072881977872613376,
                          823730477538082826, 1097933031081259138, 951605898546135060, 873829544325427200, 1003129070793535520, 1061449765004529715, 1067994081210421259]
        self.messages = pretender.MessageManager(self.db)
        self.webhooks = pretender.WebhookManager(self.db)

    def check_ignore(self, message: discord.Message) -> bool:
        if message.author.bot:
            return True
        if not message.content:
            return True
        if message.channel.id not in self.whitelist:
            return True
        if self.db.fetchrow("SELECT * FROM pretender_blacklist WHERE uid=?", (message.author.id,)):
            return True
        return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if self.check_ignore(message):
            return
        # Checks for message content moved to the add method
        self.messages.add(message)

    @commands.Cog.listener()
    async def on_message_edit(self, _: discord.Message, after: discord.Message):
        if self.check_ignore(after):
            return
        self.messages.edit(after)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if self.check_ignore(message):
            return
        self.messages.delete_message(message.id)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list[discord.Message]):
        for message in messages:
            if self.check_ignore(message):
                continue
            self.messages.delete_message(message.id)

    @commands.command(name="count")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def count(self, ctx: commands.Context, *, content: str):
        """ Counts the amount of messages containing a keyword and shows the Top #10 people who said it. """
        keyword = content.lower()
        occurrences = {}
        # Ignore the secret room messages for counting (For future self, maybe do the same behaviour as impersonate command?)
        messages = self.db.fetch("SELECT * FROM pretender_messages WHERE content REGEXP ? AND channel IS NULL", (keyword,))

        for message in messages:
            text = message.get("content")
            text = text.lower()
            author = message["author"]

            if author not in occurrences:
                occurrences[author] = 0

            occurrences[author] += text.count(keyword)

        # sorting it by the highest number of occurrences
        occurrences = dict(sorted(occurrences.items(), key=lambda occurrence: occurrence[1], reverse=True))
        embed = discord.Embed(
            title=f"Top #10 users who've said '{keyword}':",
            # description="(based on message data collected here thus far)",
            colour=general.random_colour(),
            timestamp=ctx.message.created_at
        )
        embed.set_footer(text=f"Invoked by {ctx.author}", icon_url=str(ctx.author.display_avatar))
        index = 1

        for uid, count in occurrences.items():
            user = self.bot.get_user(int(uid))
            if not user:
                try:
                    user = await self.bot.fetch_user(int(uid))
                except discord.NotFound:
                    continue

            embed.add_field(name=f"#{index} - {general.username(user)}", value=f"**{count}** uses", inline=False)

            if index == 10:  # 10th place
                break
            index += 1
        return await ctx.message.reply(embed=embed, mention_author=False)

    @commands.command(name="optin")
    async def opt_in(self, ctx: commands.Context):
        """ Opts back into the message collection process, if you are in the blacklist. """
        if not self.db.fetchrow("SELECT * FROM pretender_blacklist WHERE uid=?", (ctx.author.id,)):
            return await ctx.send("You're already opted in.")

        self.db.execute("DELETE FROM pretender_blacklist WHERE uid=?", (ctx.author.id,))
        return await ctx.send("You're now opted in.")

    @commands.command(name="optout")
    async def opt_out(self, ctx: commands.Context):
        """ Opts out of the message collection process, which will all you to the blacklist for message logging. """
        if self.db.fetchrow("SELECT * FROM pretender_blacklist WHERE uid=?", (ctx.author.id,)):
            return await ctx.send("You're already opted out.")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == "✅"

        message = await ctx.send(f"{general.username(ctx.author)}, Are you sure you want to opt out?\n"
                                 f"All your saved messages will be deleted from the database. "
                                 f"You may opt back in at any time, but the messages cannot be restored.\n"
                                 f"The impersonate command can still be used on you, but it will only use others' messages.\n"
                                 f"React with ✅ to confirm.")
        await message.add_reaction("✅")

        try:
            await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except TimeoutError:
            return await message.edit(content="Didn't get a reaction in time, so you're still opted in.")

        self.messages.remove(ctx.author)
        self.db.execute("INSERT INTO pretender_blacklist VALUES (?)", (ctx.author.id,))
        await message.delete()
        return await ctx.send("Successfully deleted all message data from you and added you to the log blacklist.")

    @commands.command(name="impersonate")
    @commands.cooldown(rate=1, per=7.5, type=commands.BucketType.user)
    @commands.bot_has_permissions(manage_webhooks=True, manage_messages=True)
    async def impersonate(self, ctx: commands.Context, victim: discord.User = None):
        """ Impersonates a user (or you), based on their messages that have been collected.
        If the user has opted out of message collecting, or there are not enough messages, it will be based on all messages in the database. """
        victim = victim or ctx.author
        session = ClientSession()
        try:  # For secret rooms, generate message based on the messages already there
            message = self.messages.generate(victim, ctx.channel.id if pretender.separation_condition(ctx.channel) else None)
            webhook = await self.webhooks.get(ctx.channel, session)

            try:
                await ctx.message.delete()
            except (discord.NotFound, discord.Forbidden):
                # If we can't delete the ctx message, then so be it, just tell the user about it
                await ctx.send("Failed to delete original message...", delete_after=5)

            await webhook.send(message, username=victim.display_name, avatar_url=str(victim.display_avatar), allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))
        except Exception:
            raise
        finally:
            await session.close()


async def setup(bot: bot_data.Bot):
    await bot.add_cog(Pretender(bot))
