import json

import discord
from discord.ext import commands

from utils import generic, permissions, time


prefix_template = {'prefixes': [], 'default': True}


class Discord(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="server", aliases=["guild"])
    @commands.guild_only()
    async def server(self, ctx):
        """ Check info about current server """
        if ctx.invoked_subcommand is None:
            bots = sum(1 for member in ctx.guild.members if member.bot)
            embed = discord.Embed(colour=generic.random_colour())
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.add_field(name="Server name", value=ctx.guild.name, inline=True)
            embed.add_field(name="Server ID", value=ctx.guild.id, inline=True)
            embed.add_field(name="Members", value=ctx.guild.member_count, inline=True)
            embed.add_field(name="Bots", value=str(bots), inline=True)
            embed.add_field(name="Owner", value=ctx.guild.owner, inline=True)
            embed.add_field(name="Region", value=ctx.guild.region, inline=True)
            embed.add_field(name="Created at", value=time.time_output(ctx.guild.created_at), inline=True)
            return await ctx.send(f"About **{ctx.guild.name}**", embed=embed)

    @server.command(name="icon", aliases=["avatar"])
    async def server_icon(self, ctx):
        """ Get server icon """
        return await ctx.send(f"Icon of **{ctx.guild.name}**:\n{ctx.guild.icon_url_as(size=1024)}")

    @server.command(name="bots")
    async def server_bots(self, ctx):
        """ Bots in servers """
        bots = [a for a in ctx.guild.members if a.bot]
        m = ''
        for i in range(len(bots)):
            n = str(i+1) if i >= 9 else f"0{i+1}"
            m += f"[{n}] {bots[i]}\n"
        return await ctx.send(f"Bots in **{ctx.guild.name}**: ```ini\n{m}```")

    @server.group(name="prefix")
    async def server_prefix(self, ctx):
        """ Server prefix """
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(colour=generic.random_colour())
            embed.title = f"Prefixes in {ctx.guild.name}"
            try:
                data = json.loads(open(f'{generic.prefixes}/{ctx.guild.id}.json', 'r').read())
            except FileNotFoundError:
                data = prefix_template.copy()
            dp = generic.get_config().prefix
            defaults = dp if data['default'] else []
            defaults.append(ctx.bot.user.mention)
            embed.add_field(name="Default Prefixes", value='\n'.join(defaults), inline=True)
            if data['prefixes']:
                embed.add_field(name="Custom Prefixes", value='\n'.join(data['prefixes']), inline=True)
            p = ctx.prefix
            i = ctx.invoked_with
            embed.set_footer(text=f"Add custom prefixes with {p}{i} add\nRemove custom prefixes with {p}{i} remove\n"
                                  f"To toggle default prefixes use {p}{i} default <True | False>\n"
                                  f"Feature: You can't have quotes in your prefix.")
            return await ctx.send(embed=embed)

    @server_prefix.command(name="add")
    @permissions.has_permissions(manage_server=True)
    async def sp_add(self, ctx, *, what: str):
        """ Add a custom prefix """
        f = f'{generic.prefixes}/{ctx.guild.id}.json'
        try:
            data = json.loads(open(f, 'r').read())
        except FileNotFoundError:
            data = prefix_template.copy()
        new = what.replace('"', '')
        data['prefixes'].append(new)
        open(f, 'w+').write(json.dumps(data))
        return await ctx.send(f"Added `{new}` to server prefixes")

    @server_prefix.command(name="remove", aliases=["delete"])
    @permissions.has_permissions(manage_server=True)
    async def sp_remove(self, ctx, *, what: str):
        """ Remove a custom prefix """
        f = f'{generic.prefixes}/{ctx.guild.id}.json'
        try:
            data = json.loads(open(f, 'r').read())
        except FileNotFoundError:
            return await ctx.send("This server doesn't seem to even have any custom prefixes...")
        new = what.replace('"', '')
        try:
            data['prefixes'].remove(new)
        except ValueError:
            try:
                data['prefixes'].remove(f"{new} ")
            except ValueError:
                return await ctx.send("This value is not in the list of prefixes... Try writing \"like this \", "
                                      "including all spaces where necessary")
        open(f, 'w+').write(json.dumps(data))
        return await ctx.send(f"Removed `{new}` from server prefixes")

    @server_prefix.command(name="default")
    @permissions.has_permissions(manage_server=True)
    async def sp_default(self, ctx, toggle: bool = None):
        """ Toggle use of default prefixes """
        f = f'{generic.prefixes}/{ctx.guild.id}.json'
        try:
            data = json.loads(open(f, 'r').read())
        except FileNotFoundError:
            data = prefix_template.copy()
        data['default'] = toggle if toggle is not None else not data['default']
        open(f, 'w+').write(json.dumps(data))
        return await ctx.send(f"Use of default prefixes is now set to {data['default']}")

    @commands.command(name="emojis")
    @commands.is_owner()
    async def get_all_emotes(self, ctx):
        """ Yoink all emotes """
        channel = self.bot.get_channel(676154789159239740)
        await channel.send(f"This stash of emotes was made on {time.time()}")
        for guild in self.bot.guilds:
            emotes = sorted([e for e in guild.emojis if len(e.roles) == 0 and e.available], key=lambda e: e.name)
            paginator = commands.Paginator(suffix='', prefix='')
            for emote in emotes:
                paginator.add_line(f'{emote.name} = "`{emote}`"')
            await channel.send(f"Next lot -> {guild.name}\n\n\n")
            for page in paginator.pages:
                await channel.send(page)
        return await ctx.send(f"Done yoinking emotes, {ctx.author.mention}, you may fuck off now.")


def setup(bot):
    bot.add_cog(Discord(bot))
