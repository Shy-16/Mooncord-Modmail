# -*- coding: utf-8 -*-

## Database Module ##
# Connect to database and prepare a connection. #

import logging
from datetime import datetime
from typing import Any

import discord
from pymongo import MongoClient
from bson.objectid import ObjectId

log = logging.getLogger(__name__)

_connection = None


def get_conn(path):
    """Get a DB object."""
    global _connection # pylint: disable=global-statement, invalid-name
    if _connection is not None:
        return _connection
    _connection = MongoClient(path)
    log.info("Created new connection to database.")
    return _connection


class Database:
    def __init__(self, config):
        """Create and configure a connection to database.
        Provide a wrapper for database.
        """
        self._db_config = config
        self._conn = get_conn(config['path'])
        self._db = self._conn[config['db_name']]

    def close(self) -> None:
        """Close connection to database"""
        self._conn.close()

    # Ticket related
    def get_ticket(self, params: dict[str, Any]) -> dict[str, Any] | None:
        """Given search parameters, return ticket associated to it"""
        col = self._db['modmail_tickets']
        if "_id" in params:
            params["_id"] = ObjectId(params["_id"])

        ticket = col.find_one(params)
        if ticket is None:
            return None

        col = self._db['modmail_users']
        ticket['author'] = col.find_one({'discord_id': ticket['author_id']})
        return ticket

    def get_users_ticket_count(self, user_id: str) -> int:
        """Given a user_id, return the number of total tickets."""
        col = self._db['modmail_tickets']
        return col.count_documents({'author_id': user_id})

    def create_ticket(self, author: discord.Member, channel_id: str | None, 
                        dm_channel_id: str, guild_id: str, source: str) -> dict[str, Any]:
        """Given a user channel and guild, make a new ticket."""
        col = self._db['modmail_tickets']
        ticket = col.find_one({'author_id': str(author.id), 'status': 'active'})

        if ticket is None:
            ticket = {
                'author_id': str(author.id),
                'channel_id': channel_id if channel_id else None,
                'dm_channel_id': dm_channel_id,
                'guild_id': guild_id,
                'status': 'active',
                'created_date': datetime.now().isoformat(),
                'updated_date': datetime.now().isoformat(),
                'closed_date': None,
                'closed_user_id': None,
                'closed_comment': None,
                'action_taken': None,
                'source': source
            }

            result = col.insert_one(ticket)
            ticket['_id'] = result.inserted_id

        col = self._db['modmail_users']
        ticket_author = col.find_one({'discord_id': str(author.id)})
        if ticket_author is None:
            ticket_author = {
                'discord_id': str(author.id),
                'username': author.name,
                'created_date': datetime.now().isoformat(),
                'updated_date': datetime.now().isoformat()
            }
            result = col.insert_one(ticket_author)
            ticket_author['_id'] = result.inserted_id
        ticket['author'] = ticket_author
        return ticket
    
    def update_ticket(self, ticket_id: str, params: dict[str, Any]) -> dict[str, Any] | None:
        """Given a ticket, update database with given params."""
        col = self._db['modmail_tickets']
        return col.find_one_and_update({'_id': ObjectId(ticket_id)}, {"$set" : params })

    def create_ticket_message(self, ticket_id: str, content: str, author: discord.Member,
                                attachments: list[discord.Attachment] | None = None, mode: str = 'message') -> dict[str, Any]:
        """Add a new message to an existing ticket."""
        col = self._db['modmail_users']
        if col.find_one({'discord_id': str(author.id)}) is None:
            user = {
                'discord_id': str(author.id),
                'username': author.name,
                'created_date': datetime.now().isoformat(),
                'updated_date': datetime.now().isoformat()
            }
            col.insert_one(user)

        col = self._db['modmail_history']
        entry = {
            'ticket_id': ObjectId(ticket_id),
            'author_id': str(author.id),
            'message': content,
            'mode': mode,
            'attachments': [],
            'created_date': datetime.now().isoformat(),
            'updated_date': datetime.now().isoformat()
        }

        attachments = attachments or []
        for att in attachments:
            entry['attachments'].append({
                'id': str(att.id),
                'filename': att.filename,
                'content_type': att.content_type,
                'size': att.size,
                'url': att.url
            })

        result = col.insert_one(entry)
        entry['_id'] = result.inserted_id
        return entry

    def lock_ticket(self, ticket_id: str) -> dict[str, Any]:
        """Given a ticket_id lock a given ticket."""
        col = self._db['modmail_tickets']
        data = {
            'locked': True,
            'updated_date': datetime.now().isoformat()
        }
        result = col.find_one_and_update({'_id': ObjectId(ticket_id)}, {"$set" : data })
        return result

    def unlock_ticket(self, ticket_id: str) -> dict[str, Any]:
        """Given a ticket_id lock a given ticket."""
        col = self._db['modmail_tickets']
        data = {
            'locked': False,
            'updated_date': datetime.now().isoformat()
        }
        result = col.find_one_and_update({'_id': ObjectId(ticket_id)}, {"$set" : data })
        return result

    def close_ticket(self, ticket_id: str, author_id: str, data: dict) -> dict[str, Any]:
        """Given a ticket_id, author_id and data close a given ticket."""
        col = self._db['modmail_tickets']
        data['updated_date'] = datetime.now().isoformat()
        data['closed_date'] = datetime.now().isoformat()
        data['closed_user_id'] = author_id
        data['status'] = 'closed'
        result = col.find_one_and_update({'_id': ObjectId(ticket_id)}, {"$set" : data })
        return result

    # Server configuration for start up
    async def load_server_configuration(self, guild: discord.Guild, bot: discord.Bot) -> dict[str, Any]:
        """Given a guild, load its configuration"""
        col = self._db['discord_config']
        guild_info = col.find_one({'guild_id': str(guild.id)})
        if guild_info is None:
            dc_guild = await bot.fetch_guild(guild.id)
            admin_roles = []
            for role in dc_guild.roles:
                # 1 << 3 == 0x8 == administrator
                if role.permissions.administrator:
                    admin_roles.append(role.id)
            guild_info = {
                'guild_id': str(guild.id),
                'name': guild.name,
                'command_character': bot.config['discord']['default_command_character'],
                'modmail_character': bot.config['discord']['default_command_character'],
                'allowed_channels': [],
                'denied_channels': [],
                'admin_roles': admin_roles,
                'mod_roles': [],
                'ban_roles': [],
                'log_channel': None,
                'modmail_category': None,
                'modmail_channel': None,
                'modmail_forum': None,
                'modmail_mode': "channels",
                'override_silent': False,
                'auto_timeout_on_reenter': True,
                'joined_date': datetime.now().isoformat()
            }
            result = col.insert_one(guild_info)
            guild_info['_id'] = result.inserted_id
        return guild_info

    def update_server_configuration(self, query: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        """Updates server configuration"""
        col = self._db['discord_config']
        result = col.find_one_and_update(query, {"$set" : data })
        return result