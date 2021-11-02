# -*- coding: utf-8 -*-

import asyncio

import interactions
from interactions.enums import OptionType

def setup(bot: interactions.Client):
	@bot.command(
		type=1,
		name="modmail",
		description="Create a new ticket to contact staff.",
		scope=int(bot.config['discord']['default_server_id']),
		options=[{"name":"description", "description":"Description of the ticket", "required":True, "type":OptionType.STRING}]
	)
	async def handle_modmail_slash(ctx: interactions.context.Context) -> None:
		# ctx: 'application_id', 'channel_id', 'data', 'guild_id', 'id', 'member', 'send', 'token', 'type', 'version'
		# ctx.member: {'user': {'username': 'yuigahamayui', 'public_flags': 128, 'id': '539881999926689829', 'discriminator': '7441', 'avatar': 'f493550c33cd55aaa0819be4e9a988a6'}, 'roles': ['553472623300968448', '553456439046307841', '553482195067732000', '553454347795824650', '553483070687281163', '553882357443198986', '553482969969459214', '553985892914692117', '555747311016476693'], 'premium_since': None, 'permissions': '1099511627775', 'pending': False, 'nick': 'yui', 'mute': False, 'joined_at': '2019-03-08T05:49:16.519000+00:00', 'is_pending': False, 'deaf': False, 'avatar': None}
		# ctx.data: {'type': 1, 'options': [{'value': 'testing again', 'type': 3, 'name': 'description'}], 'name': 'modmail', 'id': '905174418228125776'}

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
		ticket = await bot.modmail.get_ticket({'user_id': int(ctx.member['user']['id']), 'status': 'active'})

		# Make a DM channel where a notification will be sent afterwards.
		dm_channel = await bot.http.create_dm(ctx.member['user']['id'])

		if ticket is not None:
			# if the user has a ticket, simply add the new request as a message
			entry = await bot.modmail.create_ticket_message(ticket, ctx.data['options'][0]['value'], author=ctx.member['user'])

			# rely information
			embed = {
				"type": "rich",
				"title": "Message received",
				"description": ctx.data['options'][0]['value'],
				"color": 0x0aeb06,
				"fields": [],
				"footer": {
					"text": f"{ctx.member['user']['username']}#{ctx.member['user']['discriminator']} · Ticket ID {ticket['_id']}",
					"icon_url": bot.build_avatar_url(ctx.member['user'])
				}
			}

			await bot.http.send_message(ticket['modmail_channel_id'], '', embed=embed)

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
				{'name': 'Info', 'value': 'Once the Mod Team reviews your ticket they will put in contact with you.', 'inline': False}
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

		# Add the message to the ticket
		entry = await bot.modmail.create_ticket_message(ticket, ctx.data['options'][0]['value'], author=ctx.member['user'])

		await asyncio.sleep(1) # give 1 second for modmail to create the channel and to get modmail_channel_id
		ticket = await bot.modmail.get_ticket({'user_id': int(ctx.member['user']['id']), 'status': 'active'})

		# rely information
		embed = {
			"type": "rich",
			"title": "Message received",
			"description": ctx.data['options'][0]['value'],
			"color": 0x0aeb06,
			"fields": [],
			"footer": {
				"text": f"{ctx.member['user']['username']}#{ctx.member['user']['discriminator']} · Ticket ID {ticket['_id']}",
				"icon_url": bot.build_avatar_url(ctx.member['user'])
			}
		}

		await bot.http.send_message(ticket['modmail_channel_id'], '', embed=embed)
