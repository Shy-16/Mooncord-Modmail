# -*- coding: utf-8 -*-

## Config ##
# Manage Guild Configuration. #

from .command import Command, verify_permission

class BotConfig(Command):

	def __init__(self, bot, permission='admin'):
		"""
		@bot: Sayo
		@permission: A minimum allowed permission to execute command.
		"""
		super().__init__(bot, permission)

	@verify_permission
	async def execute(self, context):
		if len(context.params) == 0:
			# Show current server config
			await self._show_server_configuration(context)
			return

		if len(context.params) <= 2:
			await self.send_help(context)
			return

		if context.params[0] == "set":

			if context.params[1] == "modmail_channel":
				await self._set_modmail_channel(context)

			elif context.params[1] == "modmail_character":
				await self._set_command_character(context)

	async def send_help(self, context):
		fields = [
			{'name': 'Help', 'value': f"Use {context.command_character}config set|add|rm <name> <value> \
				to set a new value or add/remove a value from an array.", 'inline': False}
		]

		await self._bot.send_embed_message(context.channel, "Server Configuration", fields=fields)

	async def send_no_permission_message(self, context):
		fields = [
			{'name': 'Permission Error', 'value': f"You need to be {self.permission} to execute this command.", 'inline': False}
		]

		await self._bot.send_embed_message(context.channel, "Server Configuration", fields=fields)

	# Private functions
	async def _show_server_configuration(self, context):
		guild_config = self._bot.guild_config[context.guild.id]

		modmail_channel = "No channel configured"
		if guild_config.get('modmail_channel') is not None:
			modmail_channel = f"<#{guild_config['modmail_channel']}>"

		modmail_category = "No category configured"
		if guild_config.get('modmail_category') is not None:
			modmail_category = f"<#{guild_config['modmail_category']}> ({guild_config['modmail_category']})"

		fields = [
			{'name': 'Help', 'value': f"Use {guild_config['modmail_character']}config set <name> <value> \
				to set a new value.", 'inline': False},
			{'name': 'modmail_character', 'value': f"{guild_config['modmail_character']}", 'inline': False},
			{'name': 'modmail_channel', 'value': f"{modmail_channel}", 'inline': False},
			{'name': 'modmail_category', 'value': f"{modmail_category}", 'inline': False}
		]

		await self._bot.send_embed_message(context.channel, f"{guild_config['name']} Config", fields=fields)

	async def _set_modmail_channel(self, context):
		if context.channel_mentions:
			channel_id = context.channel_mentions[0].id
			category_id = context.channel_mentions[0].category_id

			config_params = {
				'modmail_channel': channel_id,
				'modmail_category': category_id
			}

			guild_config = self._bot.db.update_server_configuration(context.guild, config_params)
			await self._bot.update_guild_configuration(context.guild)

			fields= [
				{'name': 'modmail_channel', 'value': f"Modmail Channel was properly set up to: #{context.channel_mentions[0].name}", 'inline': False}
			]

			await self._bot.send_embed_message(context.channel, "Server Configuration", fields=fields)

		else:
			fields= [
				{'name': 'modmail_channel', 'value': f"You need to mention a channel. Ex: `{guild_config['command_character']}config \
					set modmail_channel #channel_mention`", 'inline': False}
			]
			await self._bot.send_embed_message(context.channel, "Server Configuration", fields=fields)

	async def _set_command_character(self, context):
		value = context.params[2]

		if value is None or value == '':
			fields= [
				{'name': 'modmail_character', 'value': "Modmail Character cannot be empty.", 'inline': False}
			]

			await self._bot.send_embed_message(context.channel, "Server Configuration", fields=fields)

		guild_config = self._bot.db.update_server_configuration(context.guild, {'modmail_character': value})
		await self._bot.update_guild_configuration(context.guild)

		fields= [
			{'name': 'modmail_character', 'value': f"Modmail charactes was properly set to: {value}. Make sure it doesn't conflict with other bots.", 'inline': False}
		]

		await self._bot.send_embed_message(context.channel, "Server Configuration", fields=fields)
