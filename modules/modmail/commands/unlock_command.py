# -*- coding: utf-8 -*-

## Unlock ##
# Unlock modmail channels. #

from modules.context import CommandContext
from modules.command import Command, verify_permission


class Unlock(Command):
    @verify_permission
    async def execute(self, context: CommandContext) -> None:
        ticket = await self._module.get_ticket(channel_id=context.channel.id)
        if not ticket:
            ticket = await self._module.get_ticket({'_id': context.channel.name})
        if not ticket:
            description = f"Couldn't find any associated tickets to this channel. ID: {context.channel.id} · Name: {context.channel.name}"
            await self._bot.send_embed_message(context.channel, description, color=0xb30000)


        await self._module.unlock_ticket(ticket)
        await context.channel.edit(name=context.channel.name[2:], reason="Unlocked channel")
        await self._bot.send_embed_message(context.channel, "Ticket unlocked 🔓", 
            f"Messages will be relied to user again until channel is locked.\r\n\
            You can still use {context.modmail_character} to force ignore messages sent in this channel.", color=0xff8409)
