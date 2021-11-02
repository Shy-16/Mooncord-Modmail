# -*- coding: utf-8 -*-

import asyncio

import interactions

def setup(bot: interactions.Client):
	@bot.command(
		type=3,
		name="modmail",
		scope=int(bot.config['discord']['default_server_id'])
	)
	async def handle_modmail_context(ctx: interactions.context.Context):
		# ctx: 'application_id', 'author', 'channel', 'channel_id', 'data', 'guild_id', 'id', 'message', 'send', 'token', 'type', 'user'
		# ctx.member['user']: {'username': 'yuigahamayui', 'public_flags': 128, 'id': '539881999926689829', 'discriminator': '7441', 'avatar': 'f493550c33cd55aaa0819be4e9a988a6'}
		# ctx.message: None
		# ctx.data.resolved {'messages': {'904551183497175080': {'type': 0, 'tts': False, 'timestamp': '2021-11-01T02:03:27.894000+00:00', 'pinned': False, 
		#    'mentions': [], 'mention_roles': [], 'mention_everyone': False, 'id': '904551183497175080', 'flags': 0, 'embeds': [], 'edited_timestamp': None, 
		#    'content': '', 'components': [], 'channel_id': '593048383405555725', 'author': {'username': 'yuigahamayui', 'public_flags': 128, 
		#    'id': '539881999926689829', 'discriminator': '7441', 'avatar': 'f493550c33cd55aaa0819be4e9a988a6'}, 
		#    'attachments': [{'width': 573, 'url': 'https://cdn.discordapp.com/attachments/593048383405555725/904551183270686770/nadeStare.png', 'size': 510143, 
		#        'proxy_url': 'https://media.discordapp.net/attachments/593048383405555725/904551183270686770/nadeStare.png', 'id': '904551183270686770', 
		#        'height': 542, 'filename': 'nadeStare.png', 'content_type': 'image/png'}]
		#    }}}
		# ctx.data.target_id - message_id! 904551183497175080

		print(ctx.data)

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

		# Get the message that was right clicked
		target_message = ctx.data['resolved']['messages'][ctx.data['target_id']]

		if ticket is not None:
			# if the user has a ticket, simply add the new request as a message
			entry = await bot.modmail.create_ticket_message(ticket, target_message['content'], 
				attachments=target_message.get("attachments", list()), author=ctx.member['user'])

			# rely information
			has_video = False

			embed = {
				"type": "rich",
				"title": "Message reported",
				"description": "",
				"color": 0x0aeb06,
				"fields": [],
				"footer": {
					"text": f"{ctx.member['user']['username']}#{ctx.member['user']['discriminator']} · Ticket ID {ticket['_id']}",
					"icon_url": bot.build_avatar_url(ctx.member['user'])
				},
				"url": bot.build_message_url(ctx.guild_id, ctx.channel_id, ctx.data['target_id'])
			}

			# if message has only attachment and no content then dont add it to fields
			if target_message['content']:
				embed["fields"].append({"name": "Message content", "value": target_message['content']})

			# if attachments include them in embed
			if target_message.get("attachments"):
				att = target_message['attachments'][0]
				embed["fields"].append({"name": "Attachment Information", "value": att['url']})

				if 'image' in att['content_type']:
					embed["thumbnail"] = {"url": att['url']}
				elif 'video' in att['content_type']:
					has_video = True
				else:
					# in case of unknown att do something else, for now not used
					pass

				embed["fields"].append({"name": "Name", "value": att['filename'], "inline": True})
				embed["fields"].append({"name": "Content Type", "value": att['content_type'], "inline": True})
				embed["fields"].append({"name": "Size", "value": f"{att['width']} x {att['height']}", "inline": True})

			await bot.http.send_message(ticket['modmail_channel_id'], "", embed=embed)
			if has_video:
				await bot.http.send_message(ticket['modmail_channel_id'], target_message['attachments'][0]['url'])

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
		entry = await bot.modmail.create_ticket_message(ticket, target_message['content'], 
				attachments=target_message.get("attachments", list()), author=ctx.member['user'])

		await asyncio.sleep(2) # give 2 seconds for modmail to create the channel and to get modmail_channel_id
		ticket = await bot.modmail.get_ticket({'user_id': int(ctx.member['user']['id']), 'status': 'active'})

		# rely information
		has_video = False

		embed = {
			"type": "rich",
			"title": "Message reported",
			"description": "",
			"color": 0x0aeb06,
			"fields": [],
			"footer": {
				"text": f"{ctx.member['user']['username']}#{ctx.member['user']['discriminator']} · Ticket ID {ticket['_id']}",
				"icon_url": bot.build_avatar_url(ctx.member['user'])
			},
			"url": bot.build_message_url(ctx.guild_id, ctx.channel_id, ctx.data['target_id'])
		}

		# if message has only attachment and no content then dont add it to fields
		if target_message['content']:
			embed["fields"].append({"name": "Message content", "value": target_message['content']})

		# if attachments include them in embed
		if target_message.get("attachments"):
			att = target_message['attachments'][0]
			embed["fields"].append({"name": "Attachment Information", "value": att['url']})

			if 'image' in att['content_type']:
				embed["thumbnail"] = {"url": att['url']}
			elif 'video' in att['content_type']:
				has_video = True
			else:
				# in case of unknown att do something else, for now not used
				pass

			embed["fields"].append({"name": "Name", "value": att['filename'], "inline": True})
			embed["fields"].append({"name": "Content Type", "value": att['content_type'], "inline": True})
			embed["fields"].append({"name": "Size", "value": f"{att['width']} x {att['height']}", "inline": True})

		await bot.http.send_message(ticket['modmail_channel_id'], "", embed=embed)
		if has_video:
			await bot.http.send_message(ticket['modmail_channel_id'], target_message['attachments'][0]['url'])
