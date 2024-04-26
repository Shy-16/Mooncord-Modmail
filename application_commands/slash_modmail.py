# -*- coding: utf-8 -*-

import discord
from discord import option, default_permissions


def slash_modmail(bot: discord.AutoShardedBot):
    @bot.slash_command(
        description="Create a new ticket to contact staff.",
        guild_ids=[bot.guilds[0].id]
    )
    @default_permissions(send_messages=True)
    @option("description", str, description="Description of the ticket.", required=True)
    async def modmail(context: discord.ApplicationContext, description: str) -> None:
        await context.response.defer(ephemeral=True)

        ticket = await bot.modmail.get_ticket(author_id=context.user.id, filter={'status': 'active'})
        if ticket is not None:
            await bot.modmail.create_ticket_message(ticket, description, author=context.user)
            footer = {
                "text": f"{context.user.name} · Ticket ID {ticket['_id']}",
                "icon_url": context.user.avatar.url
            }
            await bot.send_embed_message(int(ticket['modmail_channel_id']), "Message received", description, footer=footer)

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
                    "text": f'{context.guild.id} Mod Team · Ticket: {ticket["_id"]}'
                }
            }
            await context.send_followup(embed=discord.Embed.from_dict(embed), ephemeral=True)
            return

        # Create a new ticket for the user
        if context.user.dm_channel is None:
            await context.user.create_dm()
        ticket = await bot.modmail.create_ticket(author=context.user,
                                                channel_id=str(context.channel.id),
                                                dm_channel_id=str(context.user.dm_channel.id),
                                                guild_id=str(context.guild.id),
                                                source="slash")

        if ticket is None:
            embed = {
                "type": "rich",
                "title": "Error",
                "description": "There was an error creating your ticket. Please try again or contact a moderator.",
                "color": 0x802d2d,
                "footer": {"text": f'{context.guild.name} Mod Team'}
            }
            await context.send_followup(embed=discord.Embed.from_dict(embed), ephemeral=True)
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
                "text": f'{context.guild.id} Mod Team · Ticket: {ticket["_id"]}'
            }
        }
        await context.send_followup(embed=discord.Embed.from_dict(embed), ephemeral=True)
        
        # Create channel in server
        modmail_channel = await bot.modmail.create_modmail_channel(ticket, context.guild_id, context.user)
        ticket["modmail_channel_id"] = str(modmail_channel.id)
        
        # create DM message as followup
        fields = [
            {'name': 'Info', 'value': "Anything you type in this DM will be conveyed to the Mod Team .\r\n"+
                "Once the Mod Team reviews your ticket they will put in contact with you through this same channel.", 'inline': False},
        ]
        footer = {"text": f'{context.guild.name} Mod Team · Ticket: {ticket["_id"]}'}
        await bot.send_embed_dm(context.user, "Ticket created", description="Your ticket has been created.", color=0x0aeb06,
            fields=fields, footer=footer)
        
        # Relay information to server
        footer = {
            "text": f"{context.user.name} · Ticket ID {ticket['_id']}",
            "icon_url": context.user.avatar.url
        }
        await bot.send_embed_message(modmail_channel, "Message received", description,
                                            color=0x0aeb06, footer=footer)

        # add a new entry to history of ticket
        await bot.modmail.create_ticket_message(ticket, description, context.user)
