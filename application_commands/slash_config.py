# -*- coding: utf-8 -*-

import discord
from discord import option, default_permissions

from modules.modmail.modmail_constants import MODMAIL_FORUMS_TYPE, MODMAIL_CHANNELS_TYPE


def config_slash(bot: discord.AutoShardedBot) -> None:
    cmd_group = bot.create_group(
        name="config",
        description="Configure Modmail.",
        guild_ids=[bot.guilds[0].id]
    )
    
    @cmd_group.command(
        name="show",
        description="Show Modmail configuration."
    )
    @default_permissions(moderate_members=True)
    async def handle_config_show(
        ctx: discord.ApplicationContext
    ) -> None:
        await ctx.response.defer(ephemeral=True)
        guild_config = bot.guild_config[ctx.guild.id]
        
        category = "Not set"
        if guild_config['modmail_category']:
            category = f"<#{guild_config['modmail_category']}> ({guild_config['modmail_category']})"
        channel = "Not set"
        if guild_config['modmail_channel']:
            channel = f"<#{guild_config['modmail_channel']}> ({guild_config['modmail_channel']})"
        forum = "Not set"
        if guild_config['modmail_forum']:
            forum = f"<#{guild_config['modmail_forum']}> ({guild_config['modmail_forum']})"

        embed = {
            "type": "rich",
            "title": "Config",
            "color": 0x0aeb06,
            "fields": [
                {'name': 'modmail_character', 'value': f"{guild_config['modmail_character']}", 'inline': False},
                {'name': 'modmail_mode', 'value': f"{guild_config['modmail_mode']}", 'inline': False},
                {'name': 'modmail_category', 'value': category, 'inline': False},
                {'name': 'modmail_channel', 'value': channel, 'inline': False},
                {'name': 'modmail_forum', 'value': forum, 'inline': False}
            ]
        }
        await ctx.send_followup(embed=discord.Embed.from_dict(embed), ephemeral=True)
        
    @cmd_group.command(
        name="prefix",
        description="Choose prefix to invoke Modmail commands."
    )
    @default_permissions(moderate_members=True)
    @option("prefix", str, required=True)
    async def handle_config_mode(
        ctx: discord.ApplicationContext,
        prefix: str,
    ) -> None:
        await ctx.response.defer(ephemeral=True)
        
        query = {'guild_id': str(ctx.guild_id)}
        data = {'modmail_character': prefix}
        bot.db.update_server_configuration(query, data)
        await bot.reload_config()

        embed = {
            "type": "rich",
            "title": "Config updated",
            "description": f"Modmail prefix is now set to {prefix}.",
            "color": 0x0aeb06
        }
        await ctx.send_followup(embed=discord.Embed.from_dict(embed), ephemeral=True)
    
    @cmd_group.command(
        name="mode",
        description="Choose between Channels and Forums for Modmail management."
    )
    @default_permissions(moderate_members=True)
    @option("mode", str,
            choices=[discord.OptionChoice("Channels", MODMAIL_CHANNELS_TYPE), discord.OptionChoice("Forums", MODMAIL_FORUMS_TYPE)], 
            required=True)
    async def handle_config_mode(
        ctx: discord.ApplicationContext,
        mode: str,
    ) -> None:
        await ctx.response.defer(ephemeral=True)
        
        query = {'guild_id': str(ctx.guild_id)}
        data = {'modmail_mode': mode}
        bot.db.update_server_configuration(query, data)
        await bot.reload_config()

        embed = {
            "type": "rich",
            "title": "Config updated",
            "description": f"Modmail is now set to {mode}.",
            "color": 0x0aeb06
        }
        await ctx.send_followup(embed=discord.Embed.from_dict(embed), ephemeral=True)

    @cmd_group.command(
        name="forums_channel",
        description="Setup the channel for Modmail Forums."
    )
    @default_permissions(moderate_members=True)
    @option("channel", discord.abc.GuildChannel, required=True)
    async def handle_forum_channel(
        ctx: discord.ApplicationContext,
        channel: discord.ForumChannel,
    ) -> None:
        await ctx.response.defer(ephemeral=True)
        
        query = {'guild_id': str(ctx.guild_id)}
        data = {'modmail_forum': str(channel.id)}
        bot.db.update_server_configuration(query, data)
        await bot.reload_config()

        embed = {
            "type": "rich",
            "title": "Config updated",
            "description": f"Modmail Forums is now set to <#{channel.id}>.",
            "color": 0x0aeb06
        }
        await ctx.send_followup(embed=discord.Embed.from_dict(embed), ephemeral=True)
        
    @cmd_group.command(
        name="category",
        description="Setup the category for Modmail Channels."
    )
    @default_permissions(moderate_members=True)
    @option("category", discord.abc.GuildChannel, required=True)
    async def handle_forum_channel(
        ctx: discord.ApplicationContext,
        category: discord.CategoryChannel,
    ) -> None:
        await ctx.response.defer(ephemeral=True)
        
        query = {'guild_id': str(ctx.guild_id)}
        data = {'modmail_category': str(category.id)}
        bot.db.update_server_configuration(query, data)
        await bot.reload_config()

        embed = {
            "type": "rich",
            "title": "Config updated",
            "description": f"Modmail Category is now set to <#{category.id}>.",
            "color": 0x0aeb06
        }
        await ctx.send_followup(embed=discord.Embed.from_dict(embed), ephemeral=True)
        
    @cmd_group.command(
        name="channel",
        description="Setup the channel for Modmail Channels."
    )
    @default_permissions(moderate_members=True)
    @option("channel", discord.abc.GuildChannel, required=True)
    async def handle_forum_channel(
        ctx: discord.ApplicationContext,
        channel: discord.TextChannel,
    ) -> None:
        await ctx.response.defer(ephemeral=True)
        
        query = {'guild_id': str(ctx.guild_id)}
        data = {'modmail_channel': str(channel.id)}
        bot.db.update_server_configuration(query, data)
        await bot.reload_config()

        embed = {
            "type": "rich",
            "title": "Config updated",
            "description": f"Modmail Channel is now set to <#{channel.id}>.",
            "color": 0x0aeb06
        }
        await ctx.send_followup(embed=discord.Embed.from_dict(embed), ephemeral=True)
