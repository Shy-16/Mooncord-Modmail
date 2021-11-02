# -*- coding: utf-8 -*-

import interactions

async def create_ticket(bot: interactions.Client, message: interactions.api.models.message.Message, params: list) -> None:
	# 'attachments', 'author', 'channel_id', 'components', 'content', 'edited_timestamp', 'embeds', 'flags',
	# 'guild_id', 'id', 'member', 'mention_everyone', 'mention_roles', 'mentions', 'nonce', 'pinned', 'referenced_message', 'timestamp', 'tts', 'type'

	ticket = await bot.modmail.get_ticket({'modmail_channel_id': message.channel_id})

	# if we didnt get a ticket maybe try from channel name?
	if not ticket:
		channel = await bot.http.get_channel(message.channel_id)
		ticket = await bot.modmail.get_ticket({'_id': channel['name']})

	# If we didnt get a ticket welp... I guess just return a failure
	if not ticket:
		await bot.http.send_message(message.channel_id, 
			f'I couldn\'t find any related tickets to this channel. ID: {message.channel_id} · Name: {channel["name"]}')

	if len(params) > 0:
		reason = " ".join(params[0:])
	else:
		reason = 'No reason given.'

	ticket = await bot.modmail.close_ticket(ticket=ticket, author_id=message.author.id, data={'closed_comment': reason, 'action_taken': 'no_action'})

	fields = [
		{'name': 'Closing Reason', 'value': reason, 'inline': False},
		{'name': 'Mod Info', 'value': f"<@{message.author.id}>", 'inline': False}
	]

	footer = {
		"text": f"{bot.guild_config[message.guild_id]['name']} · Ticket ID {ticket['_id']}"
	}

	await bot.send_embed_dm(message.author.id, "Ticket closed", f"Ticket {ticket['_id']} was closed.", color=10038562, fields=fields, footer=footer)
	await bot.send_embed_message(bot.guild_config[message.guild_id]['modmail_channel'], "Ticket closed", f"Ticket {ticket['_id']} was closed.", color=10038562, fields=fields, footer=footer)

	await bot.http.delete_channel(message.channel_id)
