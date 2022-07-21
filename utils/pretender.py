# Code adapted from: https://github.com/okbuddyhololive/polkabot
from __future__ import annotations

import discord
import markovify
from aiohttp import ClientSession

from utils.database import Database


class MessageManager:
    def __init__(self, min_limit: int = 500, max_limit: int = 100000, length: int = 200, tries: int = 100):
        # The original had the min_limit set to 1000, but let's have it at 500 here since a lot of users might not have that many
        # The original had the max_limit set to 25000
        self.db = Database()

        self.min_limit = min_limit
        self.max_limit = max_limit
        self.length = length

        self.tries = tries

    def default(self) -> list[dict]:
        return self.db.fetch("SELECT * FROM pretender_messages WHERE channel IS NULL", ())[:self.max_limit]

    def add(self, message: discord.Message):
        # We only need to track the channel if the channel is a Secret Room - else, mash everything together
        _channel = message.channel.id if message.channel.category_id == 663031673813860420 else None
        self.db.execute("INSERT INTO pretender_messages VALUES (?, ?, ?)", (message.author.id, _channel, message.clean_content))

    def remove(self, author: discord.Member | discord.User):
        self.db.execute("DELETE FROM pretender_messages WHERE author=?", (author.id,))

    def generate(self, author: discord.Member | discord.User, channel_id: int = None) -> str:
        if channel_id:
            dataset = self.db.fetch("SELECT * FROM pretender_messages WHERE author=? AND channel=?", (author.id, channel_id))[:self.max_limit]
        else:
            dataset = self.db.fetch("SELECT * FROM pretender_messages WHERE author=? AND channel IS NULL", (author.id,))[:self.max_limit]

        if not dataset or len(dataset) < self.min_limit:
            dataset = self.default()

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
