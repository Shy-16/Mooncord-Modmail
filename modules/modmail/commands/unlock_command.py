# -*- coding: utf-8 -*-

## Unlock ##
# Unlock modmail channels. #

from modules.context import CommandContext
from modules.command import Command, verify_permission
from modules.modmail.modmail_constants import MODMAIL_FORUMS_TYPE
from modules.modmail.modmail_modules.forums import unlock_forums_thread
from modules.modmail.modmail_modules.channels import unlock_channel


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
        if context.modmail_mode == MODMAIL_FORUMS_TYPE:
            await unlock_forums_thread(self._bot, context)
        else:
            await unlock_channel(self._bot, context)
