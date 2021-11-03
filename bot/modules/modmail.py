# -*- coding: utf-8 -*-

## Modmail Module ##
# Interacts with Modmail functionality through API #

from .api_connector import do_api_call
from .api_endpoints import POST_PUBLISH_TICKET, POST_PUBLISH_MESSAGE
from db import ModmailDatabase
import asyncio

class Modmail:

	def __init__(self, bot):
		"""
		@bot: Sayo
		"""
		self._bot = bot
		self.PUBLIC_URL = bot.config['modmail']['public_url']
		self.API_URI = bot.config['modmail']['api_uri']
		self.API_KEY = bot.config['modmail']['api_key']

		self._db = ModmailDatabase(bot.config['database'])

	async def has_active_ticket(self, context):
		"""
		Review if the user DMing the bot has an active ticket.

		@context: bot.commands.context.DMContext

		return ticket
		"""

		ticket = self._db.get_user_ticket(context.author)

		return ticket

	async def handle_message(self, context):
		"""
		Handles a new message sent to the bot that didnt fall into any command category
		and was written in a public channel, not in DMs

		@context: bot.commands.context.DMContext
		"""

		# Check for active tickets with channel id
		ticket = self._db.get_ticket({'modmail_channel_id': context.channel.id})

		if not ticket:
			return

		# First rely the message
		fields = [
			{'name': f"{context.author.name}#{context.author.discriminator}", 'value': context.message.content, 'inline': False}
		]

		footer = f"{self._bot.guild_config[ticket['guild_id']]['name']} · Ticket ID {ticket['_id']}"

		await self._bot.send_embed_dm(ticket['user_id'], "Message received", fields=fields, footer=footer)

		for attachment in context.message.attachments:
			await self._bot.send_dm(ticket['user_id'], attachment.url)

		# then store message in database
		self._db.add_ticket_message(ticket, context.message, context.author)

		# publish message to replicate where needed
		data = {
			'message': context.message.content,
			'attachments': list(),
			**ticket
		}

		for att in context.message.attachments:
			data['attachments'].append({
				'content_type': att.content_type,
				'filename': att.filename,
				'id': att.id,
				'size': att.size,
				'url': att.url
			})

		data['_id'] = str(data['_id'])
		data['user']['_id'] = str(data['user']['_id'])

		response = do_api_call(self.API_URI + POST_PUBLISH_MESSAGE % str(ticket['_id']), self.API_KEY, data=data, method="POST")

		# finally, react to show we sent message properly.
		await context.message.add_reaction("✅")

	async def handle_dm_message(self, context):
		"""
		Handles a new DM sent to the bot that didnt fall into any command category

		@context: bot.commands.context.DMContext
		"""

		# Check for user active tickets
		ticket = self._db.get_user_ticket(context.author)

		if not ticket:
			# Ask the user if they want to make a new ticket.
			reaction_message = await self._bot.send_dm(context.author, "Would you like to create a new ticket to report an issue to moderators?")
			await reaction_message.add_reaction("✅")
			await reaction_message.add_reaction("⛔")
			
			def check(reaction, user):
				return user == context.author and (str(reaction.emoji) == "✅" or str(reaction.emoji) == "⛔")

			reaction, user = None, None

			try:
				reaction, user = await self._bot.wait_for('reaction_add', timeout=60.0, check=check)

			except asyncio.TimeoutError:
				await reaction_message.delete()
				await self._bot.send_dm(context.author, "Time expired. Please try initiating the Ticket process again.")
				return

			if reaction.emoji == "⛔":
				await reaction_message.delete()
				return

			elif reaction.emoji == "✅":
				await reaction_message.delete()

				self._bot.handling_dm.append(user.id)
				await self._bot.send_dm(user, "Please explain the issue that you'd like to report:")

				def modmaiL_wait_for_dm_reply(message):
					return message.author.id == user.id

				ticket_message = None

				try:
					ticket_message = await self._bot.wait_for('message', check=modmaiL_wait_for_dm_reply, timeout=60.0)

				except asyncio.TimeoutError:
					await self._bot.send_dm(context.author, "Time expired. Please try initiating the Ticket process again.")
					self._bot.handling_dm.remove(user.id)
					return

				self._bot.handling_dm.remove(user.id)
				ticket = self._db.create_ticket(user, ticket_message.channel, self._bot.default_guild)

				fields = [
					{'name': 'Ticket created', 'value': 'A new ticket has been created.', 'inline': False},
					{'name': 'Usage Info', 'value': "Anything you type in this DM will be conveyed to the Mod Team .\r\n\r\n"+
						"Once the Mod Team reviews your ticket they will put in contact with you through this same channel.", 'inline': False},
				]

				footer = f"{ticket['guild']['name']} · Ticket ID {ticket['_id']}"

				await self._bot.send_embed_dm(user, "New Ticket", fields=fields, footer=footer)
				response = do_api_call(self.API_URI + POST_PUBLISH_TICKET % str(ticket['_id']), self.API_KEY, method="POST")

				ticket = self._db.get_user_ticket(context.author)

				# rely information
				footer = f"{user.name}#{user.discriminator} · Ticket ID {ticket['_id']}"

				await self._bot.send_embed_message(ticket['modmail_channel_id'], "Message received", ticket_message.content,
					footer=footer, footer_icon=user.avatar.url)

				for attachment in ticket_message.attachments:
					await self._bot.send_message(ticket['modmail_channel_id'], attachment.url)

				# add a new entry to history of ticket
				self._db.add_ticket_message(ticket, ticket_message, context.author)

				data = {
					'message': ticket_message.content,
					'attachments': list(),
					**ticket
				}

				for att in ticket_message.attachments:
					data['attachments'].append({
						'content_type': att.content_type,
						'filename': att.filename,
						'id': att.id,
						'size': att.size,
						'url': att.url
					})

				data['_id'] = str(data['_id'])
				data['user']['_id'] = str(data['user']['_id'])

				response = do_api_call(self.API_URI + POST_PUBLISH_MESSAGE % str(ticket['_id']), self.API_KEY, data=data, method="POST")

				footer = f'{self._bot.default_guild["name"]} Mod Team · Ticket: {str(ticket["_id"])}'

				await self._bot.send_embed_dm(user, "Message sent", ticket_message.content, footer=footer)
				return

		# rely information
		footer = f"{context.author.name}#{context.author.discriminator} · Ticket ID {ticket['_id']}"

		await self._bot.send_embed_message(ticket['modmail_channel_id'], "Message received", context.message.content,
			footer=footer, footer_icon=context.author.avatar.url)

		for attachment in context.message.attachments:
			await self._bot.send_message(ticket['modmail_channel_id'], attachment.url)

		# add a new entry to history of ticket
		self._db.add_ticket_message(ticket, context.message, context.author)

		data = {
			'message': context.message.content,
			'attachments': list(),
			**ticket
		}

		for att in context.message.attachments:
			data['attachments'].append({
				'content_type': att.content_type,
				'filename': att.filename,
				'id': att.id,
				'size': att.size,
				'url': att.url
			})

		data['_id'] = str(data['_id'])
		data['user']['_id'] = str(data['user']['_id'])

		response = do_api_call(self.API_URI + POST_PUBLISH_MESSAGE % str(ticket['_id']), self.API_KEY, data=data, method="POST")

		footer = f'{self._bot.default_guild["name"]} Mod Team · Ticket: {str(ticket["_id"])}'

		await self._bot.send_embed_dm(context.author, "Message sent", context.message.content, footer=footer)

	async def close_ticket(self, context):
		"""
		Handles closing a ticket from commands in a guild

		@context: typeof bot.commands.Context
		"""

		ticket = self._db.get_ticket({'modmail_channel_id': context.channel.id})

		if not ticket:
			ticket = self._db.get_ticket({'_id': context.channel.name})

		if not ticket:
			return

		ticket_id = str(ticket['_id'])

		if len(context.params) > 0:
			reason = " ".join(context.params[0:])
		else:
			reason = 'No reason given.'

		ticket = self._db.close_ticket(ticket_id, context.author.id, {'closed_comment': reason, 'action_taken': 'no_action'})

		fields = [
			{'name': 'Closing Reason', 'value': reason, 'inline': False},
			{'name': 'Mod Info', 'value': f"<@{context.author.id}>", 'inline': False}
		]

		footer = f"{context.guild.name} · Ticket ID {ticket_id}"

		user = context.guild.get_member(ticket['user_id'])

		await self._bot.send_embed_dm(user, "Ticket closed", f"Ticket {ticket_id} was closed.", colour=10038562, fields=fields, footer=footer)
		await self._bot.send_embed_message(context.modmail_channel, "Ticket closed", f"Ticket {ticket_id} was closed.", colour=10038562, fields=fields, footer=footer)

		await context.channel.delete(reason=reason)