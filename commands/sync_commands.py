# -*- coding: utf-8 -*-

import interactions

async def sync_commands(bot: interactions.Client, ctx: interactions.context.Context):
	commands = await bot.http.get_application_command(bot.me.id, 553454168631934977)
	print(bot.me.id, commands)

	for command in commands:
		await bot.http.delete_application_command(application_id=bot.me.id, command_id=command['id'], guild_id=command.get("guild_id"))
