import dataclasses
import io
from math import ceil

import discord

from utils import languages


async def save_file(attachment: discord.Attachment, filesize_limit: int = discord.utils.DEFAULT_FILE_SIZE_LIMIT_BYTES) -> discord.File | None:
    """ Try to save a file """
    file = io.BytesIO()
    try:
        await attachment.save(file)
    except (discord.NotFound, discord.HTTPException):
        try:
            await attachment.save(file, use_cached=True)
        except (discord.NotFound, discord.HTTPException):
            return None
    # Return the attachment if it could be saved and is below the maximum filesize, otherwise return None (i.e. could not be saved)
    if 0 < file.getbuffer().nbytes <= filesize_limit:
        file.seek(0)
        return discord.File(file, filename=attachment.filename)
    else:
        return None


@dataclasses.dataclass
class EmbedsAndLinks:
    """ Represents the output of the embed_or_link_attachments() function """
    main_embed: discord.Embed
    """ The main embed used for showing information """
    embeds: list[discord.Embed] = dataclasses.field(default_factory=list, init=False)  # noqa: E221
    """ Additional embeds with images or videos """
    links: list[str]            = dataclasses.field(default_factory=list, init=False)  # noqa: E221
    """ Links to any materials that couldn't be embedded """
    files: list[discord.File]   = dataclasses.field(default_factory=list, init=False)  # noqa: E221
    """ Attachments that had to be salvaged as files """
    embedded_attachments: int   = dataclasses.field(default_factory=int, init=False)   # noqa: E221
    """ Amount of attachments that were added as embeds """
    embedded_embeds: int        = dataclasses.field(default_factory=int, init=False)   # noqa: E221
    """ Amount of embeds that were added as embeds"""
    embedded_stickers: int      = dataclasses.field(default_factory=int, init=False)   # noqa: E221
    """ Amount of stickers that were added as embeds """
    linked_attachments: int     = dataclasses.field(default_factory=int, init=False)   # noqa: E221
    """ Amount of attachments that were added as links """
    linked_embeds: int          = dataclasses.field(default_factory=int, init=False)   # noqa: E221
    """ Amount of embeds that were added as links """
    linked_stickers: int        = dataclasses.field(default_factory=int, init=False)   # noqa: E221
    """ Amount of stickers that were added as links """
    deleted: int                = dataclasses.field(default_factory=int, init=False)   # noqa: E221
    """ Amount of deleted attachments that couldn't be saved """
    ignored: int                = dataclasses.field(default_factory=int, init=False)   # noqa: E221
    """ Amount of embeds that have been ignored and weren't shown """


async def embed_or_link_attachments(message: discord.Message, language: languages.Language, main_embed: discord.Embed, *, salvage_mode: bool = False) -> EmbedsAndLinks:
    """ Embed or link any attachments, embeds, or stickers in the message

     :param message: The message to scan through (the message to add to Starboard or the one that was deleted/edited)
     :param language: The language to use
     :param main_embed: The main output embed
     :param salvage_mode: If enabled, try to download attachments instead of simply linking them """
    # Set variables for the embedded and linked attachments
    embed_limit = 4
    output = EmbedsAndLinks(main_embed)

    # Texts for linked attachments
    text_aa = language.string("starboard_attachment_audio")
    text_ai = language.string("starboard_attachment_image")
    text_av = language.string("starboard_attachment_video")
    text_ao = language.string("starboard_attachment_other")
    text_ei = language.string("starboard_embed_image")
    text_ev = language.string("starboard_embed_video")
    text_stk = language.string("starboard_sticker")
    text_del = language.string("events_message_deleted_file")

    count = start = 0
    # The first attachment has its content embedded, if possible
    # Any other attachments are tagged along as links or included in extra embeds
    # If there is an embed in the original message, it's also included after the main embed
    if message.attachments:
        count = len(message.attachments)
        attachment = message.attachments[0]
        content = str(attachment.content_type)
        if content.startswith("image/"):  # the attachment contains an image
            if not salvage_mode:
                start = 1
                output.main_embed.set_image(url=attachment.url)

    # Try to embed or link all remaining attachments
    if count > start:
        for attachment in message.attachments[start:]:
            if not salvage_mode:
                content = str(attachment.content_type)
                if len(output.embeds) < embed_limit and content.startswith("image/"):
                    _embed = discord.Embed(title=text_ai)  # type="image", url=att.url)
                    _embed._image = {"url": attachment.url, "proxy_url": attachment.proxy_url, "height": attachment.height, "width": attachment.width}
                    output.embeds.append(_embed)
                    output.embedded_attachments += 1
                else:
                    if content.startswith("image/"):
                        text = text_ai
                    elif content.startswith("video/"):
                        text = text_av
                    elif content.startswith("audio/"):
                        text = text_aa
                    else:
                        text = text_ao
                    output.links.append(f"[{text}]({attachment.url}) - {attachment.filename}")
                    output.linked_attachments += 1
            else:
                file = await save_file(attachment, message.guild.filesize_limit)
                if file:
                    output.files.append(file)
                    output.embedded_attachments += 1
                else:
                    output.links.append(f"{text_del} - {attachment.filename}")
                    output.deleted += 1

    def _get_link_and_filename(url: str) -> tuple[str, str]:
        _link = str(url)
        return _link, _link.split('/')[-1].split("?", maxsplit=1)[0]

    # Add the message's embeds to the other ones (up to 4 total)
    for message_embed in message.embeds:
        if len(output.embeds) < embed_limit:
            if message_embed.type == "image":
                # Note: This assumes that all image embeds are from discord, where it uses thumbnail instead of image for whatever odd reason
                if not hasattr(output.main_embed, "_image"):  # if the image has not yet been set to the current embed
                    # noinspection PyProtectedMember
                    output.main_embed._image = message_embed._thumbnail  # set that embed's image as our image
                else:
                    _embed = discord.Embed()
                    # noinspection PyProtectedMember
                    _embed._image = message_embed._thumbnail
                    output.embeds.append(_embed)
                    output.embedded_embeds += 1
            elif message_embed.type == "video":
                link, filename = _get_link_and_filename(message_embed.video.url)
                output.links.append(f"[{text_ev}]({link}) - {filename}")
                output.linked_embeds += 1
            else:
                output.embeds.append(message_embed)
                output.embedded_embeds += 1
        else:
            if message_embed.type == "image":
                # Note: This assumes that all image embeds are from discord, where it uses thumbnail instead of image for whatever odd reason
                link = str(message_embed.thumbnail.url)
                filename = link.split('/')[-1].split("?")[0]
                output.links.append(f"[{text_ei}]({link}) - {filename}")
                output.linked_embeds += 1
            elif message_embed.type == "video":
                link = str(message_embed.video.url)
                filename = link.split('/')[-1].split("?")[0]
                output.links.append(f"[{text_ev}]({link}) - {filename}")
                output.linked_embeds += 1
            else:
                # Only image and video embeds will be linked, others are ignored.
                output.ignored += 1

    for message_sticker in message.stickers:
        if len(output.embeds) < embed_limit:
            _embed = discord.Embed(title=text_stk)
            _embed.set_image(url=message_sticker.url)
            _embed.description = language.string("starboard_sticker_name", name=message_sticker.name)
            output.embeds.append(_embed)
            output.embedded_stickers += 1
        else:
            link = str(message_sticker.url)
            output.links.append(f"[{text_stk}]({link}) - {message_sticker.name}")
            output.linked_stickers += 1

    if any((output.embeds, output.links, output.files, output.deleted, output.ignored)):
        def _add_status(status_str: str, number: int, word: str):
            if number:
                status.append(language.string(status_str, count=language.plural(number, word)))

        status = []
        status_embedded = "starboard_message_embedded"
        status_linked = "starboard_message_linked"
        word_attachment = "starboard_word_attachment"
        word_embed = "starboard_word_embed"
        word_sticker = "starboard_word_sticker"

        _add_status(status_embedded, output.embedded_attachments, word_attachment)
        _add_status(status_linked, output.linked_attachments, word_attachment)
        _add_status("events_message_deleted_status", output.deleted, word_attachment)
        _add_status(status_embedded, output.embedded_embeds, word_embed)
        _add_status(status_linked, output.linked_embeds, word_embed)
        _add_status(status_embedded, output.embedded_stickers, word_sticker)
        _add_status(status_linked, output.linked_stickers, word_sticker)
        _add_status("starboard_message_ignored", output.ignored, word_embed)
        _status = "\n".join(status)
        if len(output.links) <= 4:
            _links = "\n\n" + "\n".join(output.links) if output.links else ""
            output.main_embed.add_field(name=language.string("starboard_attachments"), value=(_status + _links)[:1024], inline=False)
        else:
            output.main_embed.add_field(name=language.string("starboard_attachments"), value=_status, inline=False)
            links_per_part = 4
            parts = ceil(len(output.links) / links_per_part)
            for part in range(parts):
                i = part * links_per_part
                _links = "\n".join(output.links[i:i+links_per_part])
                output.main_embed.add_field(name=language.string("starboard_attachments_part", part=language.number(part + 1)), value=_links, inline=False)
    return output
