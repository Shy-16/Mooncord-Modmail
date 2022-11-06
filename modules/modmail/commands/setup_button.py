# -*- coding: utf-8 -*-

## Setup Button ##
# Creates the Modal button message. #

from modules.context import CommandContext
from modules.command import Command, verify_permission
from modules.modmail.components import create_modmail_setup_button


class SetupModmailButton(Command):
    @verify_permission
    async def execute(self, context: CommandContext) -> None:
        content = "To create a message react with 📩\r\n\r\n\
        Please refrain from using modmail to send memes.\r\nDoing so will result in a timeout and a strike."
        footer = {
            "text": f"{context.guild.name} · Mod Team"
        }

        # Setup the button
        button = create_modmail_setup_button(self._bot)
        await self._bot.send_embed_message(context.channel, "Contact staff", content, color=10038562, footer=footer, view=button)
