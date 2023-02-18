# -*- coding: utf-8 -*-

## Setup Modmail Modal ##
# The followup Modal to create tickets. #

import discord


class ModmailModal(discord.ui.Modal):
    def __init__(self, *children, title: str, custom_id: str | None = None, 
                    timeout: float | None = None, bot: discord.Bot | None = None) -> None:
        super().__init__(*children, title=title, custom_id=custom_id, timeout=timeout)
        self._bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        ticket = await self._bot.modmail.get_ticket(author_id=interaction.user.id, filter={'status': 'active'})

        # Get the message
        # data: {'custom_id': 'create_ticket_modal', 'components': [{'type': 1, 'components': [{'value': 'test', 'type': 4, 'custom_id': 'modmail_topic'}]}]}
        message_content = interaction.data['components'][0]['components'][0]['value']

        if ticket is not None:
            # if the user has a ticket, simply add the new request as a message
            await self._bot.modmail.create_ticket_message(ticket, message_content, author=interaction.user)
            footer = {
                "text": f"{interaction.user.name}#{interaction.user.discriminator} · Ticket ID {ticket['_id']}",
                "icon_url": interaction.user.avatar.url
            }
            await self._bot.send_embed_message(int(ticket['modmail_channel_id']), "Message received", message_content, footer=footer)

            # Let the user know the message was relayed properly.
            embed = {
                "type": "rich",
                "title": "Ticket updated",
                "description": "Your ticket was updated.",
                "color": 0x0aeb06,
                "fields": [
                    {'name': 'Info', 'value': 'The new information was correctly sent to the ticket you previously opened.', 'inline': False}
                ],
                "footer": {
                    "text": f'{interaction.guild.name} Mod Team · Ticket: {ticket["_id"]}'
                }
            }
            await interaction.followup.send(embed=discord.Embed.from_dict(embed), ephemeral=True)
            return

        # Create a new ticket for the user
        if interaction.user.dm_channel is None:
            await interaction.user.create_dm()
        ticket = await self._bot.modmail.create_ticket(author=interaction.user,
                                                channel_id=str(interaction.channel.id),
                                                dm_channel_id=str(interaction.user.dm_channel.id),
                                                guild_id=str(interaction.guild.id),
                                                source="slash")

        if ticket is None:
            embed = {
                "type": "rich",
                "title": "Error",
                "description": "There was an error creating your ticket. Please try again or contact a moderator.",
                "color": 0x802d2d,
                "footer": {"text": f'{interaction.guild.name} Mod Team'}
            }
            await interaction.followup.send(embed=discord.Embed.from_dict(embed), ephemeral=True)
            return

        # Let the user know it was created properly.
        embed = {
            "type": "rich",
            "title": "Ticket created",
            "description": "Your ticket has been created.",
            "color": 0x0aeb06,
            "fields": [
                {'name': 'Info', 'value': 'A followup DM has been sent to you.\r\n\
                Please send any related attachments and further inquiries through that channel.\r\n\r\n\
                If you didn\'t receive any DMs please make sure you enable DMs from people in the same server \
                or you will not be able to receive support from the mod team.', 'inline': False}
            ],
            "footer": {
                "text": f'{interaction.guild.id} Mod Team · Ticket: {ticket["_id"]}'
            }
        }
        await interaction.followup.send(embed=discord.Embed.from_dict(embed), ephemeral=True)

        # Create channel in server
        modmail_channel = await self._bot.modmail.create_modmail_channel(ticket, interaction.guild_id, interaction.user)
        ticket["modmail_channel_id"] = str(modmail_channel.id)

        # create DM message as followup
        fields = [
            {'name': 'Info', 'value': "Anything you type in this DM will be conveyed to the Mod Team .\r\n"+
                "Once the Mod Team reviews your ticket they will put in contact with you through this same channel.", 'inline': False},
        ]
        footer = {"text": f'{interaction.guild.name} Mod Team · Ticket: {ticket["_id"]}'}
        await self._bot.send_embed_dm(interaction.user, "Ticket created", description="Your ticket has been created.", color=0x0aeb06,
            fields=fields, footer=footer)
        
        # Relay information to server
        footer = {
            "text": f"{interaction.user.name}#{interaction.user.discriminator} · Ticket ID {ticket['_id']}",
            "icon_url": interaction.user.avatar.url
        }
        await self._bot.send_embed_message(modmail_channel, "Message received", message_content,
                                            color=0x0aeb06, footer=footer)

        # add a new entry to history of ticket
        await self._bot.modmail.create_ticket_message(ticket, message_content, interaction.user)
