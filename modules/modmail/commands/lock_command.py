# -*- coding: utf-8 -*-

## Lock ##
# Lock Modmail channels. #

from modules.context import CommandContext
from modules.command import Command, verify_permission


class Lock(Command):
    @verify_permission
    async def execute(self, context: CommandContext) -> None:
        ticket = await self._module.get_ticket(channel_id=context.channel.id)
        if not ticket:
            ticket = await self._module.get_ticket({'_id': context.channel.name})
        if not ticket:
            description = f"Couldn't find any associated tickets to this channel. ID: {context.channel.id} · Name: {context.channel.name}"
            await self._bot.send_embed_message(context.channel, description, color=0xb30000)

        await self._module.lock_ticket(ticket)
        await context.channel.edit(name="🔒 " + context.channel.name, reason="Locked channel")
        await self._bot.send_embed_message(context.channel, "Ticket locked 🔒", 
            "No messages will be relied to user until channel is unlocked again.", color=0xff8409)
