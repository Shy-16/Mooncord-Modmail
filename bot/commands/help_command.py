# -*- coding: utf-8 -*-

## Timeout ##
# A command to timeout people. #

from .command import Command, verify_permission
from bot.log_utils import do_log

class Help(Command):

	def __init__(self, bot, permission='mod', dm_keywords=list()):
		"""
		@bot: Sayo
		@permission: A minimum allowed permission to execute command.
		"""
		super().__init__(bot, permission, dm_keywords)

	@verify_permission
	async def execute(self, context):

		fields = [
			{'name': 'Help', 'value': f"Executing the command with no arguments will always show the help for that command.", 'inline': False},
			{'name': 'config', 'value': f"{context.command_character}config will show server configuration.\r\n"+
				"You can configure server variables with this command.", 'inline': False},
			{'name': 'timeout', 'value': f"{context.command_character}timeout will set a timeout for a given user.\r\n"+ 
				f"The time parameter expects the following format: <1-2 digit number><one of: s, m, h, d> where s is second, m is minute, h is hour, d is day.\r\n"+
				f"Example command: {context.command_character}timeout <@{self._bot.user.id}> 24h Being a bad bot", 'inline': False},
			{'name': 'timeoutns', 'value': f"{context.command_character}timeoutns will set a timeout for a given user without adding a strike to their account.\r\n"+ 
				f"Usage is the same as `{context.command_character}timeout`", 'inline': False},
			{'name': 'ban', 'value': "An alias for timeout", 'inline': False},
			{'name': 'release', 'value': f"{context.command_character}release will end a user's timeout immediately.\r\n"+ 
				f"Optional parameter: `amend`: If amend is provided it will also delete the most recent strike issued to the user.\r\n"+
				f"Example command: {context.command_character}release <@{self._bot.user.id}> amend", 'inline': False},
			{'name': 'strikes', 'value': f"{context.command_character}strikes is used to add and remove strikes from a user or view a user's strike history.\r\n"+ 
				f"This comand has additional help information within the command.\r\n"+
				f"Example command: {context.command_character}strikes <@{self._bot.user.id}> verbose", 'inline': False},
			{'name': 'roles', 'value': f"{context.command_character}roles will take a list of roles and users and either \
				add or remove all given roles in the list to all given users.\r\n"+ 
				f"This comand has additional help information within the command.\r\n"+
				f"Example command: {context.command_character}roles add @GAMEJAM @GAMEDEV <@{self._bot.user.id}>.", 'inline': False},
			{'name': 'shutdown', 'value': f"Shut down the bot (Warning: This doesn't restart it) - Admin only command.\r\n"+ 
				f"Example command: {context.command_character}shutdown", 'inline': False}
		]

		await self._bot.send_embed_message(context.log_channel, "Bot Help", fields=fields)

	async def dm(self, context):


		fields = [
			{'name': 'Info', 'value': f"This is the Mooncord moderation ticketing system.\r\n\
				If you would like to open a ticket, simply DM anything message to me and I'll open a ticket for you.\r\n\
				After the ticket is made you may explain the issue and will be relied to the mod team.", 'inline': False}
		]

		await self._bot.send_embed_dm(context.author, "Bot Help", fields=fields)

	async def send_help(self, context):
		fields = [
			{'name': 'Help', 'value': f"Do you really need help for the help command?.", 'inline': False}
		]

		await self._bot.send_embed_message(context.channel, "Bot Help", fields=fields)

	async def send_no_permission_message(self, context):
		fields = [
			{'name': 'Permission Error', 'value': f"You need to be {self.permission} to execute this command.", 'inline': False}
		]

		await self._bot.send_embed_message(context.channel, "Bot Help", fields=fields)
