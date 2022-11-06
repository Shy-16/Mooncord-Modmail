# -*- coding: utf-8 -*-

## Help ##
# Help command. #

from modules.context import CommandContext
from modules.command import Command, verify_permission


class CloseTicket(Command):
    @verify_permission
    async def execute(self, context: CommandContext) -> None:
        ticket = await self._module.get_ticket(channel_id=context.channel.id)

        # if we didnt get a ticket maybe try from channel name?
        if not ticket:
            channel = await self._bot.fetch_channel(context.channel.id)
            if channel:
                if channel.name.startswith('🔒'):
                    ticket = await self._module.get_ticket({'_id': channel.name[2:]})
                ticket = await self._module.get_ticket({'_id': channel.name})

        # If we didnt get a ticket welp... I guess just return a failure
        if not ticket:
            description = f"Couldn't find any associated tickets to this channel. ID: {context.channel.id} · Name: {context.channel.name}"
            await self._bot.send_embed_message(context.channel, description, color=0xb30000)

        reason = 'No reason given.'
        if len(context.params) > 0:
            reason = " ".join(context.params[0:])

        ticket = await self._module.close_ticket(ticket, context.author, data={'closed_comment': reason, 'action_taken': 'no_action'})

        fields = [
            {'name': 'Closing Reason', 'value': reason, 'inline': False},
            {'name': 'Mod Info', 'value': f"<@{context.author.id}>", 'inline': False}
        ]
        footer = {
            "text": f"{context.guild.name} Mod team · Ticket ID {ticket['_id']}"
        }

        try:
            await self._bot.send_embed_dm(int(ticket['author_id']), "Ticket closed", f"Ticket {ticket['_id']} was closed.", color=10038562, fields=fields, footer=footer)
        except:
            pass
        await self._bot.send_embed_message(int(self._bot.guild_config[context.guild.id]['modmail_channel']), "Ticket closed", f"Ticket {ticket['_id']} was closed.", color=10038562, fields=fields, footer=footer)
        await context.channel.delete()
