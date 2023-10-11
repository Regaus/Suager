import discord

from discord.ext import commands


def is_owner(ctx):
    return ctx.author.id in ctx.bot.config["owners"]


async def check_permissions(ctx, perms, *, check=all, owner_bypass: bool = True):
    if is_owner(ctx) and owner_bypass:
        return True
    resolved = ctx.channel.permissions_for(ctx.author)
    output = check(getattr(resolved, name, None) == value for name, value in perms.items())
    if output:
        return True
    missing = [name for name, value in perms.items() if getattr(resolved, name, None) != value]
    raise commands.MissingPermissions(missing)


def has_permissions(*, check=all, owner_bypass: bool = True, **perms):
    async def pred(ctx):
        return await check_permissions(ctx, perms, check=check, owner_bypass=owner_bypass)
    return commands.check(pred)


def can_send(ctx):
    return isinstance(ctx.channel, discord.DMChannel) or ctx.channel.permissions_for(ctx.guild.me).send_messages


def can_react(ctx):
    return isinstance(ctx.channel, discord.DMChannel) or ctx.channel.permissions_for(ctx.guild.me).add_reactions
