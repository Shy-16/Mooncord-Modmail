# -*- coding: utf-8 -*-

import discord

async def help_command(bot: discord.Client, ctx: discord.Context, params: list) -> None:
	
	fields = [
		{
		  "name": f'`{bot.default_guild["modmail_character"]}`',
		  "value": f'When adding `{bot.default_guild["modmail_character"]}` in front of any message it will be ignored by Modmail.\r\n\
		  	Commands will not be ignored.'
		},
		{
		  "name": 'close <reason:optional>',
		  "value": 'When used within a modmail channel, close the ticket with provided optional reason.'
		},
		{
		  "name": 'lock / unlock',
		  "value": f"Lock or unlock a channel. A locked channel will not rely any typed information to the user so it can be used to effectively\
		  	have a conversation not having to put `{bot.default_guild['modmail_character']}` before every message."
		}
	]

	footer = {"text": f'{bot.default_guild["name"]} Mod Team'}

	await bot.send_embed_dm(ctx.author['id'],
							title="Modmail Help",
							description="These are the commands for Moderation Team.", 
							color=0x6658ff, fields=fields, footer=footer)

async def help_dm_command(bot: discord.Client, ctx: discord.Context, params: list) -> None:
	
	fields = [
		{
		  "name": 'Direct Message',
		  "value": 'Open a Direct Message with Modmail and type anything, the process will begin afterwards.'
		},
		{
		  "name": 'Using /modmail command',
		  "value": "Start typing `/modmail` in your chat and you'll be promted with the command to quickly create a ticket from anywhere."
		},
		{
		  "name": 'Right click a message and select apps -> modmail',
		  "value": 'You can directly report a message by right clicking over it and then following the interface to modmail. '\
		  	'It will embed the message as the ticket information.'
		},
		{
		  "name": 'Additional Information',
		  "value": "If you'd like to add attachments for the Mod team to review, you can do it from Direct Messages. "\
		  	"The attachment will be properly added to the ticket and conveyed for the mod team to review."
		}
	]

	footer = {"text": f'{bot.default_guild["name"]} Mod Team'}

	await bot.send_embed_dm(ctx.author['id'],
							title="Modmail Help",
							description="This is the Mooncord moderation ticketing system.\r\n\
							If you'd like to create a new ticket follow one of the following methods.", 
							color=0x6658ff, fields=fields, footer=footer)

def setup(bot: discord.Client):
	@bot.command(
		type=1,
		name="help",
		description="Check Modmail help information.",
		scope=int(bot.config['discord']['default_server_id'])
	)
	async def handle_help_slash(ctx: discord.Context) -> None:
		# ctx: 'application_id', 'author', 'channel', 'channel_id', 'data', 'guild_id', 'id', 'message', 'send', 'token', 'type', 'user'
		# ctx.message = None
		# ctx.channel = None
		# ctx.author.user: {'username': 'yuigahamayui', 'public_flags': 128, 'id': '539881999926689829', 'discriminator': '7441', 'avatar': 'f493550c33cd55aaa0819be4e9a988a6'}
		# ctx.data.options: [{'value': 'test', 'type': 3, 'name': 'description'}]

		# Defer the message so we dont fuck up the command
		embed = {
			"type": "rich",
			"title": "Modmail Help",
			"description": "This is the Mooncord moderation ticketing system.\r\n\
							If you'd like to create a new ticket follow one of the following methods.",
			"color": 0x6658ff,
			"fields": [
				{
				  "name": 'Direct Message',
				  "value": 'Open a Direct Message with Modmail and type anything, the process will begin afterwards.'
				},
				{
				  "name": 'Using /modmail command',
				  "value": "Start typing `/modmail` in your chat and you'll be promted with the command to quickly create a ticket from anywhere."
				},
				{
				  "name": 'Right click a message and select apps -> modmail',
				  "value": 'You can directly report a message by right clicking over it and then following the interface to modmail. It will embed the message as the ticket information.'
				},
				{
				  "name": 'Additional Information',
				  "value": "If you'd like to add attachments for the Mod team to review, you can do it from Direct Messages. The attachment will be properly added to the ticket and conveyed for the mod team to review."
				}
			],
			"footer": {"text": f'{bot.default_guild["name"]} Mod Team'}
		}

		data = {
			"type": 4,
			"data": {
                "tts": False,
                "content": "",
                "embeds": [embed],
                "allowed_mentions": { "parse": [] },
                "flags": 64
            }
		}
		await bot.http.create_interaction_response(token=ctx.token, application_id=ctx.id, data=data)
