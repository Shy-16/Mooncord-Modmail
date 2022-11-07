# -*- coding: utf-8 -*-

import discord
from discord import default_permissions


def slash_help(bot: discord.Bot):
    @bot.slash_command(
        description="Check Modmail help information.",
        guild_ids=[bot.guilds[0].id]
    )
    @default_permissions(send_messages=True)
    async def help(context: discord.ApplicationContext) -> None:
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
            "footer": {"text": f'{context.guild.name} Mod Team'}
        }
        await context.response.send_message(embed=discord.Embed.from_dict(embed), ephemeral=True)
