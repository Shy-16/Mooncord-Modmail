# -*- coding: utf-8 -*-

## Help ##
# Help command. #

from modules.context import CommandContext, DMContext
from modules.command import Command, verify_permission


class Help(Command):
    @verify_permission
    async def execute(self, context: CommandContext) -> None:
        description = "Executing the command with no arguments will always show the help for that command."

        fields = [
            {
            "name": f'`{context.modmail_character}`',
            "value": f'When adding `{context.modmail_character}` in front of any message it will be ignored by Modmail.\r\n\
                Commands will not be ignored.'
            },
            {
            "name": 'close <reason:optional>',
            "value": 'When used within a modmail channel, close the ticket with provided optional reason.'
            },
            {
            "name": 'lock / unlock',
            "value": f"Lock or unlock a channel. A locked channel will not rely any typed information to the user so it can be used to effectively\
                have a conversation not having to put `{context.modmail_character}` before every message."
            }
        ]
        footer = {"text": f'{self._bot.guild.name} Mod Team'}
        await self._bot.send_embed_message(context.channel, "Modmail Help", description, color=0x6658ff, fields=fields, footer=footer)

    async def dm(self, context: DMContext):
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
        footer = {"text": f'{self._bot.guild.name} Mod Team'}
        await self._bot.send_embed_dm(context.author, "Modmail Help", color=0x6658ff, fields=fields, footer=footer)
