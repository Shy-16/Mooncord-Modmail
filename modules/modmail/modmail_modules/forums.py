# -*- coding: utf-8 -*-

## Modmail Forums Module ##
# Handles Modmail functionality through Forums #

from __future__ import annotations
from typing import Any

import discord

from modules.context import CommandContext


async def create_modmail_channel(modmail, ticket: dict[str, Any], user: discord.User | discord.Member) -> discord.Thread:
    """Creates a thread under modmail forums"""
    guild: discord.Guild = modmail._bot.get_guild(int(ticket['guild_id']))
    guild_config = modmail._bot.guild_config[guild.id]
    forum_channel: discord.ForumChannel = guild.get_channel(int(guild_config['modmail_forum']))
    tags = [tag for tag in forum_channel.available_tags if "new" in tag.name]
    
    if isinstance(user, discord.User):
        user = guild.get_member(user.id)

    roles = " ".join([f"<@&{role.id}>" for role in user.roles])
    description = f"Type a message in this channel to reply. Messages starting with the server prefix `{guild_config['modmail_character']}` " \
                + f"are ignored, and can be used for staff discussion. User the command `{guild_config['modmail_character']}close <reason:optional>` to " \
                + "close the ticket."
    url = modmail._bot.config["modmail"]["public_url"] + f'/modmail/{ticket["_id"]}'
    embed = {
        "type": "rich",
        "title": "New Ticket",
        "description": description,
        "color": 2067276,
        "fields": [
            {'name': 'User', 'value': f"<@{user.id}> ({user.id})", 'inline': True},
            {'name': 'Roles', 'value': roles, 'inline': True},
            {'name': 'Dashboard', 'value': f"You can view full details and work further in the Ticket dashboard:\r\n{url}"}
        ],
        "footer": {
            'text': f"{user.name}#{user.discriminator} · Ticket ID {ticket['_id']}",
            'icon_url': user.avatar.url
        }
    }
    
    ticket_channel: discord.Thread = \
        await forum_channel.create_thread(str(ticket['_id']), embed=discord.Embed.from_dict(embed), applied_tags=tags)
    modmail._db.update_ticket(ticket["_id"], {"modmail_channel_id": str(ticket_channel.id)})
    return ticket_channel


async def lock_forums_thread(bot: discord.AutoShardedBot, context: CommandContext) -> None:
    """Locks a channel and applies a tag"""
    #tags = [tag for tag in context.channel.parent.available_tags if "lock" in tag.name]
    await context.channel.edit(name="🔒 " + context.channel.name, reason="Locked channel")
    await bot.send_embed_message(context.channel, "Ticket locked 🔒", 
        "No messages will be relayed to user until channel is unlocked again.", color=0xff8409)


async def unlock_forums_thread(bot: discord.AutoShardedBot, context: CommandContext) -> None:
    """Unlocks a channel"""
    await context.channel.edit(name=context.channel.name[2:], reason="Unlocked channel")
    await bot.send_embed_message(context.channel, "Ticket unlocked 🔓", 
        f"Messages will be relayed to user again until channel is locked.\r\n\
        You can still use {context.modmail_character} to force ignore messages sent in this channel.", color=0xff8409)


async def delete_forums_thread(bot: discord.AutoShardedBot, context: CommandContext) -> None:
    """Deletes a channel"""
    await context.channel.edit(archived=True, reason="Ticket resolved")
