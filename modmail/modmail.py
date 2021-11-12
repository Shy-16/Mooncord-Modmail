# -*- coding: utf-8 -*-

## Modmail Module ##
# Interacts with Modmail functionality through API #

import asyncio
from typing import Any, Dict, List, Optional, Tuple, Union

import interactions

from .api_connector import do_api_call
from .api_endpoints import POST_PUBLISH_TICKET, POST_PUBLISH_MESSAGE
from database import Database

class Modmail:

	def __init__(self, bot: interactions.Client) -> None:
		"""
		@bot: interactions.Client
		"""
		self._bot = bot
		self.PUBLIC_URL = bot.config['modmail']['public_url']
		self.API_URI = bot.config['modmail']['api_uri']
		self.API_KEY = bot.config['modmail']['api_key']

		self._db = Database(bot.config['database'])

		self._pending_interaction = list()

	async def get_ticket(self, params: dict) -> Union[dict, None]:
		"""
		Given a context get the ticket of the author, if any.

		@params: dict: Parameters to filter the ticket by

		return: Union[dict: ticket, None]
		"""

		return self._db.get_ticket(params)

	async def create_ticket(self, author: dict, channel_id: Optional[int], dm_channel_id: int, guild_id: int, source: str = "dm") -> dict:
		"""
		Create a new ticket from the requested interaction.

		@author: dict User Data
		@channel_id: int Channel ID
		@dm_channel_id: int Private DM Channel ID
		@guild_id: int Guild ID
		@source: str Source of the ticket

		return: created ticket
		"""

		# Create the ticket
		ticket = self._db.create_ticket(user=author,
										channel_id=channel_id,
										dm_channel_id=dm_channel_id,
										guild_id=guild_id,
										source=source)

		# Publish ticket to API to take care of the heavy stuff like creating a new channel.
		response = do_api_call(self.API_URI + POST_PUBLISH_TICKET % str(ticket['_id']), self.API_KEY, method="POST")

		return ticket

	async def create_ticket_message(self, ticket: dict, content: str, attachments: Optional[List[dict]] = list(), author: dict = dict()) -> dict:
		"""
		Create a new message for given ticket from provided context.

		@ticket: dict: Ticket information
		@content: str: message content
		@attachments: List[dict]: List of attachments
		@author: dict: author data

		return: dict: New message information
		"""

		# Store message in database
		entry = self._db.create_ticket_message(ticket, content, attachments, author=author)

		# Publish message through API to replicate in socket.io on website.
		data = {
			'message': content,
			'attachments': list(),
			**ticket
		}

		for att in attachments:
			data['attachments'].append({
				'content_type': att['content_type'],
				'filename': att['filename'],
				'id': att['id'],
				'size': att['size'],
				'url': att['url']
			})

		data['_id'] = str(data['_id'])
		data['user']['_id'] = str(data['user']['_id'])

		response = do_api_call(self.API_URI + POST_PUBLISH_MESSAGE % str(ticket['_id']), self.API_KEY, data=data, method="POST")

		return entry

	async def lock_ticket(self, ticket: dict) -> dict:
		"""
		Locks a ticket

		@ticket: dict: Ticket to close

		return: dict: Locked ticket
		"""

		# Close the ticket
		ticket = self._db.lock_ticket(ticket_id=str(ticket['_id']))

		return ticket

	async def unlock_ticket(self, ticket: dict) -> dict:
		"""
		Locks a ticket

		@ticket: dict: Ticket to close

		return: dict: Locked ticket
		"""

		# Close the ticket
		ticket = self._db.unlock_ticket(ticket_id=str(ticket['_id']))

		return ticket

	async def close_ticket(self, ticket: dict, author_id: int, data: dict) -> dict:
		"""
		Closes a ticket

		@ticket: dict: Ticket to close
		@author_id: int: Closing ticket author's ID
		@data: dict: additional data to store in database

		return: dict: Closed ticket
		"""

		# Close the ticket
		ticket = self._db.close_ticket(ticket_id=str(ticket['_id']), author_id=author_id, data=data)

		return ticket

	async def handle_message(self, message: interactions.api.models.message.Message, ticket: dict = None) -> None:
		"""
		Handles a new message sent to the bot that didnt fall into any command category
		and was written in a public channel, not in DMs

		@message: interactions.api.models.message.Message
		@ticket: dict: Ticket info if there is any from previous steps
		"""

		# Check for user active tickets
		if not ticket:
			ticket = await self.get_ticket({'modmail_channel_id': message.channel_id, 'status': 'active'})

		if not ticket:
			return

		# if ticket is locked ignore
		if ticket.get("locked"):
			return

		# First rely the message
		if message.content:
			fields = [
				{'name': f"{message.author['username']}#{message.author['discriminator']}", 'value': message.content, 'inline': False}
			]

			footer = {'text': f"{self._bot.guild_config[str(ticket['guild_id'])]['name']} · Ticket ID {ticket['_id']}"}

			await self._bot.send_embed_dm(ticket['user_id'], "Message received", fields=fields, footer=footer)

		for attachment in message.attachments:
			await self._bot.send_dm(ticket['user_id'], attachment['url'])

		# then store message in database
		entry = await self.create_ticket_message(ticket, message.content, author=message.author)

		# finally, react to show we sent message properly.
		await self._bot.http.create_reaction(message.channel_id, message.id, "✅")

	async def handle_dm_message(self, message: interactions.api.models.message.Message, ticket: dict = None) -> None:
		"""
		Handles a new DM sent to the bot that didnt fall into any command category

		@message: interactions.api.models.message.Message
		@ticket: dict: Ticket info if there is any from previous steps
		"""

		if message.author['id'] in self._pending_interaction:
			# Message is handled by the wait_for event instead.
			return

		# Check for user active tickets
		if not ticket:
			ticket = await self.get_ticket({'user_id': message.author['id'], 'status': 'active'})

		# If there is still no ticket then proceed
		if not ticket:
			# Ask the user if they want to make a new ticket.
			request_message = await self._bot.send_dm(message.author['id'], "Would you like to create a new ticket to report an issue to the Mod team?")

			await self._bot.http.create_reaction(request_message['channel_id'], request_message['id'], "✅")
			await self._bot.http.create_reaction(request_message['channel_id'], request_message['id'], "⛔")
			
			def check(event_message: interactions.api.models.message.Message) -> bool:
				return event_message.user_id == message.author['id'] and (event_message.emoji['name'] == "✅" or event_message.emoji['name'] == "⛔")

			reaction_message = None

			try:
				reaction_message = await self._bot.wait_for('message_reaction_add', timeout=60.0, check=check)

			except asyncio.TimeoutError:
				await self._bot.http.delete_message(request_message['channel_id'], request_message['id'])
				await self._bot.send_dm(message.author['id'], "Time expired. Please try initiating the Ticket process again.")
				return

			await self._bot.http.delete_message(request_message['channel_id'], request_message['id'])

			if reaction_message.emoji['name'] == "⛔":
				return

			elif reaction_message.emoji['name'] == "✅":
				self._pending_interaction.append(message.author['id'])
				await self._bot.send_dm(message.author['id'], "Please explain the issue that you'd like to report:")

				def modmaiL_wait_for_dm_reply(event_message: interactions.api.models.message.Message) -> bool:
					return event_message.author['id'] == message.author['id']

				ticket_message = None

				try:
					ticket_message = await self._bot.wait_for('message_create', check=modmaiL_wait_for_dm_reply, timeout=60.0)

				except asyncio.TimeoutError:
					await self._bot.send_dm(message.author['id'], "Time expired. Please try initiating the Ticket process again.")
					self._pending_interaction.remove(message.author['id'])
					return

				self._pending_interaction.remove(message.author['id'])

				# Create the ticket
				ticket = await self.create_ticket(author=ticket_message.author,
											channel_id=None,
											dm_channel_id=ticket_message.channel_id,
											guild_id=self._bot.default_guild['guild_id'],
											source="dm")

				# Send information to the user
				fields = [
					{'name': 'Info', 'value': "Anything you type in this DM will be conveyed to the Mod Team .\r\n\r\n"+
						"Once the Mod Team reviews your ticket they will put in contact with you through this same channel.", 'inline': False},
				]

				footer = {"text": f'{self._bot.default_guild["name"]} Mod Team · Ticket: {ticket["_id"]}'}

				await self._bot.send_embed_dm(ticket_message.author['id'], "Ticket created", description="Your ticket has been created.", color=0x0aeb06,
					fields=fields, footer=footer)

				await asyncio.sleep(1) # give 1 second for modmail to create the channel and to get modmail_channel_id
				ticket = await self.get_ticket({'user_id': ticket_message.author['id'], 'status': 'active'})

				# rely information
				embed = {
					"type": "rich",
					"title": "Message received",
					"description": ticket_message.content,
					"color": 0x0aeb06,
					"fields": [],
					"footer": {
						"text": f"{ticket_message.author['username']}#{ticket_message.author['discriminator']} · Ticket ID {ticket['_id']}",
						"icon_url": self._bot.build_avatar_url(ticket_message.author)
					}
				}

				await self._bot.http.send_message(ticket['modmail_channel_id'], '', embed=embed)

				for attachment in ticket_message.attachments:
					await self._bot.send_message(ticket['modmail_channel_id'], attachment['url'])

				# add a new entry to history of ticket
				entry = await self.create_ticket_message(ticket, ticket_message.content, author=ticket_message.author)

				footer = {"text": f'{self._bot.default_guild["name"]} Mod Team · Ticket: {ticket["_id"]}'}

				await self._bot.send_embed_dm(ticket_message.author['id'], "Message sent", ticket_message.content, footer=footer)
				return

		# rely information
		embed = {
			"type": "rich",
			"title": "Message received",
			"description": message.content,
			"color": 0x0aeb06,
			"fields": [],
			"footer": {
				"text": f"{message.author['username']}#{message.author['discriminator']} · Ticket ID {ticket['_id']}",
				"icon_url": self._bot.build_avatar_url(message.author)
			}
		}

		await self._bot.http.send_message(ticket['modmail_channel_id'], '', embed=embed)

		for attachment in message.attachments:
			await self._bot.send_message(ticket['modmail_channel_id'], attachment['url'])

		# add a new entry to history of ticket
		entry = await self.create_ticket_message(ticket, message.content, author=message.author)

		footer = {"text": f'{self._bot.default_guild["name"]} Mod Team · Ticket: {ticket["_id"]}'}

		await self._bot.send_embed_dm(message.author['id'], "Message sent", message.content, footer=footer)
