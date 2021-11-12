# -*- coding: utf-8 -*-

import discord

async def lock_ticket(bot: discord.Client, ctx: discord.Context, params: list) -> None:
	# 'attachments', 'author', 'channel_id', 'components', 'content', 'edited_timestamp', 'embeds', 'flags',
	# 'guild_id', 'id', 'member', 'mention_everyone', 'mention_roles', 'mentions', 'nonce', 'pinned', 'referenced_message', 'timestamp', 'tts', 'type'

	ticket = await bot.modmail.get_ticket({'modmail_channel_id': ctx.channel_id})
	channel = await bot.http.get_channel(ctx.channel_id)

	# if we didnt get a ticket maybe try from channel name?
	if not ticket:
		ticket = await bot.modmail.get_ticket({'_id': channel['name']})

	# If we didnt get a ticket welp... I guess just return a failure
	if not ticket:
		await bot.http.send_message(ctx.channel_id, 
			f'I couldn\'t find any related tickets to this channel. ID: {ctx.channel_id} · Name: {channel["name"]}')

	ticket = await bot.modmail.lock_ticket(ticket=ticket)

	await bot.http.modify_channel(ctx.channel_id, data={'name': "🔒 " + channel['name']}, reason=None)

	await bot.send_embed_message(ctx.channel_id, "Ticket locked 🔒", 
		f"No messages will be relied to user until channel is unlocked again.", color=0xff8409)

async def unlock_ticket(bot: discord.Client, ctx: discord.Context, params: list) -> None:
	# 'attachments', 'author', 'channel_id', 'components', 'content', 'edited_timestamp', 'embeds', 'flags',
	# 'guild_id', 'id', 'member', 'mention_everyone', 'mention_roles', 'mentions', 'nonce', 'pinned', 'referenced_message', 'timestamp', 'tts', 'type'

	ticket = await bot.modmail.get_ticket({'modmail_channel_id': ctx.channel_id})
	channel = await bot.http.get_channel(ctx.channel_id)

	# if we didnt get a ticket maybe try from channel name?
	if not ticket:
		ticket = await bot.modmail.get_ticket({'_id': channel['name']})

	# If we didnt get a ticket welp... I guess just return a failure
	if not ticket:
		await bot.http.send_message(ctx.channel_id, 
			f'I couldn\'t find any related tickets to this channel. ID: {ctx.channel_id} · Name: {channel["name"]}')

	ticket = await bot.modmail.unlock_ticket(ticket=ticket)

	await bot.http.modify_channel(ctx.channel_id, data={'name': channel['name'][2:]}, reason="Channel unlocked by a moderator.")

	await bot.send_embed_message(ctx.channel_id, "Ticket unlocked 🔓", 
		f"Messages will be relied to user again until channel is locked.\r\n\
		You can still use {bot.default_guild['modmail_character']} to force ignore messages sent in this channel.", color=0xff8409)