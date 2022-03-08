# -*- coding: utf-8 -*-

import asyncio
import discord

async def setup_ticket_button(bot: discord.Client, ctx: discord.Context, params: list) -> None:
	# 'attachments', 'author', 'channel_id', 'components', 'content', 'edited_timestamp', 'embeds', 'event_name', 'flags', 
	# 'guild_id', 'id', 'member', 'mention_everyone', 'mention_roles', 'mentions', 'nonce', 'pinned', 'referenced_message', 'timestamp', 'tts', 'type'

	# Setup the message
	content = "To create a message react with 📩\r\n\
	Please note that you should not be creating a ticket unless it is necessary, and you will be punished for making meme tickets."
	footer = {
		"text": f"{bot.guild_config[ctx.guild_id]['name']} · Mod Team"
	}

	# Setup the button
	button_component = {
		"type": 2, # button
		"style": 2, # secondary or gray
		"label": "Create Ticket",
		"emoji": {
			"id": None,
			"name": "📩",
			"animated": False
		},
		"custom_id": "create_ticket_button"
	}

	action_row = {
		"type": 1,
		"components": [button_component]
	}

	await bot.send_embed_message(ctx.channel_id, "Contact staff", content, color=10038562, footer=footer, components=[action_row])

def setup(bot: discord.Client):
	@bot.component(
		name="create_ticket_button"
	)
	async def handle_create_ticket_button(ctx: discord.InteractionContext):
		# ctx: 'application_id', 'channel_id', 'data', 'guild_id', 'id', 'member', 'send', 'token', 'type', 'version'

		# setup the input
		input_component = {
			"type": 4, # input
			"custom_id": "modmail_topic",
			"label": "Ticket Topic",
			"style": 2,
			"min_length": 24,
			"max_length": 2000,
			"placeholder": "Please state the issue you'd like to report",
			"required": True
		}

		action_row = {
			"type": 1,
			"components": [input_component]
		}

		# Defer the message so we dont fuck up the command
		data = {
			"type": 9,
			"data": {
                "custom_id": "create_ticket_modal",
                "title": "New Modmail",
                "components": [action_row],
            }
		}
		await bot.http.create_interaction_response(token=ctx.token, application_id=ctx.id, data=data)

def setup2(bot: discord.Client):
	@bot.component(
		name="create_ticket_modal"
	)
	async def handle_create_ticket_modal(ctx: discord.InteractionContext):
		# ctx: 'application_id', 'channel_id', 'data', 'guild_id', 'id', 'member', 'send', 'token', 'type', 'version'

		# data={'custom_id': 'create_ticket_modal', 'components': [{'type': 1, 'components': [{'value': 'testing 123_ piss in my ass motherfucker', 'type': 4, 'custom_id': 'modmail_topic'}]}]}

		# Defer the message so we dont fuck up the command
		data = {
			"type": 5,
			"data": {
                "tts": False,
                "content": "Creating ticket, please wait...",
                "embeds": [],
                "allowed_mentions": { "parse": [] },
                "flags": 64
            }
		}
		await bot.http.create_interaction_response(token=ctx.token, application_id=ctx.id, data=data)

		# First of all verify that the user has no tickets created yet.
		ticket = await bot.modmail.get_ticket({'user_id': ctx.member['user']['id'], 'status': 'active'})

		# Make a DM channel where a notification will be sent afterwards.
		dm_channel = await bot.http.create_dm(ctx.member['user']['id'])

		# Get the message
		# data -> action row -> input
		message_content = ctx.data['components'][0]['components'][0]['value']

		if ticket is not None:
			# if the user has a ticket, simply add the new request as a message
			entry = await bot.modmail.create_ticket_message(ticket, message_content, 
				attachments=list(), author=ctx.member['user'])

			embed = {
				"type": "rich",
				"title": "Message received",
				"description": message_content,
				"color": 0x0aeb06,
				"fields": [],
				"footer": {
					"text": f"{ctx.member['user']['username']}#{ctx.member['user']['discriminator']} · Ticket ID {ticket['_id']}",
					"icon_url": bot.build_avatar_url(ctx.member['user'])
				}
			}

			await bot.http.send_message(ticket['modmail_channel_id'], "", embed=embed)

			# Let the user know the message was relied properly.
			embed = {
				"type": "rich",
				"title": "Ticket updated",
				"description": "Your ticket was updated.",
				"color": 0x0aeb06,
				"fields": [
					{'name': 'Info', 'value': 'The new information was correctly sent to the ticket you previously opened.', 'inline': False}
				],
				"footer": {
					"text": f'{bot.default_guild["name"]} Mod Team · Ticket: {ticket["_id"]}'
				}
			}

			data = {
				"tts": False,
				"content": "",
				"embeds": [embed],
				"allowed_mentions": { "parse": [] },
				"flags": 64
			}

			await bot.http.edit_interaction_response(data, ctx.token, ctx.application_id)
			return

		# Create a new ticket for the user
		ticket = await bot.modmail.create_ticket(author=ctx.member['user'],
												channel_id=None,
												dm_channel_id=dm_channel['id'],
												guild_id=ctx.guild_id,
												source="slash")

		if ticket is None:
			embed = {
				"type": "rich",
				"title": "Error",
				"description": "There was an error creating your ticket. Please try again or contact a moderator.",
				"color": 0x802d2d,
				"footer": {"text": f'{bot.default_guild["name"]} Mod Team'}
			}

			data = {
				"tts": False,
				"content": "",
				"embeds": [embed],
				"allowed_mentions": { "parse": [] },
				"flags": 64
			}

			await bot.http.edit_interaction_response(data, ctx.token, ctx.application_id)
			return

		# Let the user know it was created properly.
		embed = {
			"type": "rich",
			"title": "Ticket created",
			"description": "Your ticket has been created.",
			"color": 0x0aeb06,
			"fields": [
				{'name': 'Info', 'value': 'A followup DM has been sent to you.\r\n\
				Please send any related attachments and further inquiries through that channel.', 'inline': False}
			],
			"footer": {
				"text": f'{bot.default_guild["name"]} Mod Team · Ticket: {ticket["_id"]}'
			}
		}

		data = {
			"tts": False,
			"content": "",
			"embeds": [embed],
			"allowed_mentions": { "parse": [] },
			"flags": 64
		}

		await bot.http.edit_interaction_response(data, ctx.token, ctx.application_id)

		await asyncio.sleep(2) # give 2 seconds for modmail to create the channel and to get modmail_channel_id
		ticket = await bot.modmail.get_ticket({'user_id': ctx.member['user']['id'], 'status': 'active'})

		# create DM message as followup
		footer = {"text": f'{bot.default_guild["name"]} Mod Team · Ticket: {ticket["_id"]}'}

		await bot.send_embed_dm(ctx.member['user']['id'], "A new ticket has been created correctly.\r\nAny further inquiries please type them here.", footer=footer)

		# Add the message to the ticket
		entry = await bot.modmail.create_ticket_message(ticket, message_content, 
				attachments=list(), author=ctx.member['user'])

		embed = {
			"type": "rich",
			"title": "Message received",
			"description": message_content,
			"color": 0x0aeb06,
			"fields": [],
			"footer": {
				"text": f"{ctx.member['user']['username']}#{ctx.member['user']['discriminator']} · Ticket ID {ticket['_id']}",
				"icon_url": bot.build_avatar_url(ctx.member['user'])
			}
		}

		await bot.http.send_message(ticket['modmail_channel_id'], "", embed=embed)
