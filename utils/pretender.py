# Code adapted from: https://github.com/okbuddyhololive/polkabot
from __future__ import annotations

import random
import re

import discord
import markovify
from aiohttp import ClientSession

from utils.database import Database


def separation_condition(channel: discord.TextChannel | discord.Thread):
    """ Check whether the channel should have a separate message record or be mashed together with everything else """
    if not channel.guild:
        return False
    # If the channel is a Secret Room or is in Satan's Rib or Shepherd Rep edge posters channel
    return channel.category_id == 663031673813860420 or channel.guild.id == 866050967249223720 or channel.id == 828742737493884968


class MessageManager:
    def __init__(self, min_limit: int = 500, max_limit: int = 10000, length: int = 200, tries: int = 100):
        # The original had the min_limit set to 1000, but let's have it at 500 here since a lot of users might not have that many
        # The original had the max_limit set to 25000, used to be 50000, now I set it to 10000 in hopes of reducing lag upon loading the messages
        self.db = Database()

        self.min_limit = min_limit
        self.max_limit = max_limit
        self.length = length

        self.tries = tries

    @staticmethod
    def fix_content(original: str):
        """ Remove unnecessary things from the message content """
        content = re.sub(r"https?://(\S+)", "", original)  # Replace links with nothing
        return content

    def add(self, message: discord.Message):
        """ Add a new messages to the database """
        prefixes = ["a,", "a.", "//", ",/", ",,"]  # Ignore bot command messages
        for prefix in prefixes:
            if message.content.startswith(prefix):
                return

        content = self.fix_content(message.content)
        if not content:  # If nothing is left in the message content, ignore the message
            return

        # We only need to track the channel if the channel is a Secret Room - else, mash everything together
        _channel = message.channel.id if separation_condition(message.channel) else None

        # If we ever somehow end up adding the same message twice, it will raise a silent IntegrityError in Database.execute(), so we can just ignore that edge case
        self.db.execute("INSERT INTO pretender_messages VALUES (?, ?, ?, ?)", (message.id, message.author.id, _channel, content))

    def edit(self, message: discord.Message):
        """ This is the updated message - we change the content of the messages with the given ID """
        # This will fail if the message originally had empty content or was a bot command, and then was edited into a message with normal text,
        # but I this is the kind of edge case I don't think is worth handling.
        # Besides, it would silently do nothing, so it's no harm anyways

        content = self.fix_content(message.content)
        if not content:  # If nothing is left in the message content, delete the message
            return self.delete_message(message.id)
        self.db.execute("UPDATE pretender_messages SET content=? WHERE id=?", (message.content, message.id))

    def delete_message(self, message_id: int):
        """ Delete a specific message - correlates to being deleted on Discord """
        self.db.execute("DELETE FROM pretender_messages WHERE id=?", (message_id,))

    def remove(self, author: discord.Member | discord.User):
        """ Wipe all messages from a given user, this would happen if they decide to opt out of Pretender """
        self.db.execute("DELETE FROM pretender_messages WHERE author=?", (author.id,))

    def generate(self, author: discord.Member | discord.User, channel_id: int = None) -> str:
        # If the channel is one of the separated channels, first try to fetch the user's messages in that channel.
        # If there are not enough messages from the channel, use the user's messages from non-separated channels.
        # Else if the dataset is still too low, use any messages from non-separated channels
        if channel_id:
            dataset = self.db.fetch("SELECT * FROM pretender_messages WHERE author=? AND channel=?", (author.id, channel_id))
            if len(dataset) < self.min_limit:
                dataset = self.db.fetch("SELECT * FROM pretender_messages WHERE author=? AND channel IS NULL", (author.id,))
        else:
            dataset = self.db.fetch("SELECT * FROM pretender_messages WHERE author=? AND channel IS NULL", (author.id,))

        if not dataset or len(dataset) < self.min_limit:
            dataset = self.db.fetch("SELECT * FROM pretender_messages WHERE channel IS NULL", ())

        # This should make it so that if the length of the dataset exceeds the limit, it will use random entries in the database instead of the same ones over and over again
        if len(dataset) > self.max_limit:
            random.shuffle(dataset)
            dataset = dataset[:self.max_limit]

        dataset = [message.get("content") for message in dataset]
        chain = markovify.NewlineText(dataset, well_formed=False)

        return chain.make_short_sentence(min_chars=10, max_chars=self.length, tries=self.tries)


class WebhookManager:
    def __init__(self):
        self.db = Database()

    # methods for interacting with a specific webhook in a collection
    async def get(self, channel: discord.TextChannel, session: ClientSession) -> discord.Webhook:
        webhook = self.db.fetchrow("SELECT * FROM pretender_webhooks WHERE channel=?", (channel.id,))

        if webhook is None:
            return await self.create(channel)

        # stuff so that the webhook class will work
        webhook.pop("channel")
        webhook["type"] = 1

        return discord.Webhook(webhook, session=session)

    async def create(self, channel: discord.TextChannel) -> discord.Webhook:
        webhook = await channel.create_webhook(name=f"#{channel.name} Impersonation Webhook")
        self.db.execute("INSERT INTO pretender_webhooks VALUES (?, ?, ?)", (webhook.id, webhook.token, channel.id))
        return webhook

    def remove(self, channel: discord.TextChannel):
        return self.db.execute("DELETE FROM pretender_webhooks WHERE channel=?", (channel.id,))
