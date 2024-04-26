# -*- coding: utf-8 -*-

## Modmail Channel Module ##
# Handles Modmail functionality through Channels #

from __future__ import annotations

from typing import Any

import discord

from modules.context import CommandContext


async def create_modmail_channel(modmail, ticket: dict[str, Any], user: discord.User | discord.Member) -> discord.TextChannel:
    """Creates a channel under modmail category"""
    guild: discord.Guild = modmail._bot.get_guild(int(ticket['guild_id']))
    guild_config = modmail._bot.guild_config[guild.id]
    category: discord.CategoryChannel = guild.get_channel(int(guild_config['modmail_category']))
    modmail_channel: discord.TextChannel = guild.get_channel(int(guild_config['modmail_channel']))
    ticket_channel: discord.TextChannel = await guild.create_text_channel(str(ticket['_id']), category=category)
    modmail._db.update_ticket(ticket["_id"], {"modmail_channel_id": str(ticket_channel.id)})
    
    if isinstance(user, discord.User):
        user = guild.get_member(user.id)

    url = modmail._bot.config["modmail"]["public_url"] + f'/modmail/{ticket["_id"]}'
    fields = [
        {'name': 'Dashboard', 'value': f"You can view full details and work further in the Ticket dashboard:\r\n{url}"},
    ]
    footer = {
        'text': f"{user.name} · Ticket ID {ticket['_id']}",
        'icon_url': user.avatar.url
    }
    await modmail._bot.send_embed_message(modmail_channel, "New Ticket", color=2067276, fields=fields, footer=footer)

    roles = " ".join([f"<@&{role.id}>" for role in user.roles])
    description = f"Type a message in this channel to reply. Messages starting with the server prefix `{guild_config['modmail_character']}` " \
                + f"are ignored, and can be used for staff discussion. User the command `{guild_config['modmail_character']}close <reason:optional>` to " \
                + "close the ticket."
    fields = [
        {'name': 'User', 'value': f"<@{user.id}> ({user.id})", 'inline': True},
        {'name': 'Roles', 'value': roles, 'inline': True},
        {'name': 'Dashboard', 'value': f"You can view full details and work further in the Ticket dashboard:\r\n{url}"}
    ]
    await modmail._bot.send_embed_message(ticket_channel, "New Ticket", description, color=2067276, fields=fields, footer=footer)
    return ticket_channel


async def lock_channel(bot: discord.AutoShardedBot, context: CommandContext) -> None:
    """Locks a channel"""
    await context.channel.edit(name="🔒 " + context.channel.name, reason="Locked channel")
    await bot.send_embed_message(context.channel, "Ticket locked 🔒", 
        "No messages will be relayed to user until channel is unlocked again.", color=0xff8409)


async def unlock_channel(bot: discord.AutoShardedBot, context: CommandContext) -> None:
    """Unlocks a channel"""
    await context.channel.edit(name=context.channel.name[2:], reason="Unlocked channel")
    await bot.send_embed_message(context.channel, "Ticket unlocked 🔓", 
        f"Messages will be relayed to user again until channel is locked.\r\n\
        You can still use {context.modmail_character} to force ignore messages sent in this channel.", color=0xff8409)


async def delete_channel(context: CommandContext) -> None:
    """Deletes a channel"""
    await context.channel.delete()
