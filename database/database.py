# -*- coding: utf-8 -*-

## Database Module ##
# Connect to database and prepare a connection. #

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import discord
from pymongo import MongoClient
from bson.objectid import ObjectId

log = logging.getLogger(__name__)

_connection = None

def get_conn(path):
    """
    Get a DB object.
    
    """

    # check to see if we exist already (singleton!)

    global _connection   # pylint: disable=global-statement

    if _connection is not None:
    	# Do cleanup if necessary
        return _connection

    # create a new instance
    _connection = MongoClient(path)
    log.info(f"Created new connection to database.")

    return _connection

class Database:

	def __init__(self, config):
		"""Create and configure a connection to database.

		Provide with wrapper for database
		"""

		self._db_config = config
		self._conn = get_conn(config['path'])
		self._db = self._conn[config['db_name']]

	def close(self):
		"""Close connection to database"""
		self._conn.close()

	# Ticket related
	def get_ticket(self, params: dict) -> Union[dict, None]:
		"""
		Given search parameters, return ticket associated to it

		@params: typeof Dictionary

		returns: Union[dict: ticket information, None]
		"""

		col = self._db['modmail_tickets']

		for arg in params:
			if isinstance(params[arg], int):
				params[arg] = params[arg]

			if arg == "_id":
				params[arg] = ObjectId(params[arg])

		ticket = col.find_one(params)

		if ticket is None:
			return None

		col = self._db['modmail_users']
		ticket['user'] = col.find_one({'discord_id': ticket['user_id']})

		return ticket

	def create_ticket(self, user: dict, channel_id: Optional[int], dm_channel_id: int, guild_id: int, source: str) -> dict:
		"""
		Given a user channel and guild, make a new ticket.

		@user: dict User Data
		@channel_id: int Channel ID
		@dm_channel_id: int Private DM Channel ID
		@guild_id: int Guild ID
		@source: str Source of the ticket

		returns: ticket
		"""

		col = self._db['modmail_tickets']
		ticket = col.find_one({'user_id': user['id'], 'status': 'active'})

		if ticket is None:
			ticket = {
				'user_id': user['id'],
				'status': 'active',
				'channel_id': dm_channel_id,
				'original_channel_id': channel_id if channel_id else None,
				'guild_id': guild_id,
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
		mm_user = col.find_one({'discord_id': user['id']})

		if mm_user is None:

			mm_user = {
				'discord_id': user['id'],
				'username': user['username'],
				'username_handle': user['discriminator'],
				'avatar': user['avatar'],
				'created_date': datetime.now().isoformat(),
				'updated_date': datetime.now().isoformat()
			}

			result = col.insert_one(mm_user)
			mm_user['_id'] = result.inserted_id

		ticket['user'] = mm_user

		return ticket

	def create_ticket_message(self, ticket: dict, content: str, attachments: Optional[List[dict]] = list(), author: dict = dict()) -> dict:
		"""
		Given a ticket, message and user add an entry to the ticket history.

		@ticket: dict: Ticket information
		@content: str: message content
		@author: dict: author data

		returns: dict: history entry
		"""

		col = self._db['modmail_users']

		user = col.find_one({'discord_id': author['id']})

		if user is None:
			user = {
				'discord_id': author['id'],
				'username': author['username'],
				'username_handle': author['discriminator'],
				'avatar': author['avatar'],
				'created_date': datetime.now().isoformat(),
				'updated_date': datetime.now().isoformat()
			}

			result = col.insert_one(user)
			user['_id'] = result.inserted_id

		col = self._db['modmail_history']
		entry = {
			'ticket_id': ObjectId(ticket['_id']),
			'user_id': author['id'],
			'message': content,
			'attachments': list(),
			'created_date': datetime.now().isoformat(),
			'updated_date': datetime.now().isoformat()
		}

		for att in attachments:
			entry['attachments'].append({
				'content_type': att['content_type'],
				'filename': att['filename'],
				'id': att['id'],
				'size': att['size'],
				'url': att['url']
			})

		result = col.insert_one(entry)
		entry['_id'] = result.inserted_id

		return entry

	def lock_ticket(self, ticket_id: int) -> dict:
		"""
		Given a ticket_id lock a given ticket.

		@ticket_id: string, ticket_id

		returns: ticket
		"""

		col = self._db['modmail_tickets']

		data = {
			'updated_date': datetime.now().isoformat(),
			'locked': True
		}

		result = col.find_one_and_update({'_id': ObjectId(ticket_id)}, {"$set" : data })

		return result

	def unlock_ticket(self, ticket_id: int) -> dict:
		"""
		Given a ticket_id lock a given ticket.

		@ticket_id: string, ticket_id

		returns: ticket
		"""

		col = self._db['modmail_tickets']

		data = {
			'updated_date': datetime.now().isoformat(),
			'locked': False
		}

		result = col.find_one_and_update({'_id': ObjectId(ticket_id)}, {"$set" : data })

		return result

	def close_ticket(self, ticket_id: int, author_id: int, data: dict) -> dict:
		"""
		Given a ticket_id, author_id and data close a given ticket.

		@ticket_id: string, ticket_id
		@user_id: discord user_id
		@data: data to update

		returns: ticket
		"""

		col = self._db['modmail_tickets']

		data['updated_date'] = datetime.now().isoformat()
		data['closed_date'] = datetime.now().isoformat()
		data['closed_user_id'] = author_id
		data['status'] = 'closed'

		result = col.find_one_and_update({'_id': ObjectId(ticket_id)}, {"$set" : data })

		return result

	# Server configuration for start up
	async def load_server_configuration(self, guild: dict, bot: discord.Client):
		"""
		Given a guild, load its configuration

		@guild: typeof Discord.Guild

		returns: guild_config
		"""

		col = self._db['discord_config']

		guild_info = col.find_one({'guild_id': guild['id']})

		if guild_info is None:

			# get all server info
			full_info = await bot.http.get_guild(guild['id'])

			# Get default admin roles
			admin_roles = []

			for role in full_info['roles']:
				if int(role['permissions']) & 0x0000000008 == 0x0000000008:
					admin_roles.append(role['id'])

			guild_info = {
				'guild_id': guild['id'],
				'name': guild['name'],
				'command_character': bot.config['discord']['default_command_character'],
				'modmail_character': bot.config['modmail']['default_command_character'],
				'allowed_channels': list(),
				'denied_channels': list(),
				'admin_roles': admin_roles,
				'mod_roles': list(),
				'ban_roles': list(),
				'log_channel': None,
				'modmail_channel': None,
				'override_silent': False,
				'auto_timeout_on_reenter': True,
				'joined_date': datetime.now().isoformat()
			}

			result = col.insert_one(guild_info)
			guild_info['_id'] = result.inserted_id

		return guild_info


if __name__ == '__main__':
	import pprint

	config = {
		'path': 'mongodb://sakurazaki:testpasswd@localhost:27017/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&ssl=false',
		'db_name': 'moon2web'
	}

	conn = get_conn(config['path'])
	conn.close()
