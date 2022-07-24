# -*- coding: utf-8 -*-

import asyncio

import discord


def setup(bot: discord.Client):
    @bot.command(
        type=3,
        name="modmail",
        scope=int(bot.config['discord']['default_server_id'])
    )
    async def handle_modmail_context(ctx: discord.InteractionContext):
        # ctx: 'application_id', 'channel_id', 'data', 'guild_id', 'id', 'member', 'send', 'token', 'type', 'version'

        # Defer the message so we dont fuck up the command
        data = {
            "type": 5,
            "data": {
                "tts": False,
                "content": "Creating ticket, please wait...",
                "embeds": [],
                "allowed_mentions": { "parse": [] },
                "flags": 64
            }
        }
        await bot.http.create_interaction_response(token=ctx.token, application_id=ctx.id, data=data)

        # First of all verify that the user has no tickets created yet.
        ticket = await bot.modmail.get_ticket({'user_id': ctx.member['user']['id'], 'status': 'active'})

        # Make a DM channel where a notification will be sent afterwards.
        dm_channel = await bot.http.create_dm(ctx.member['user']['id'])

        # Get the message that was right clicked
        target_message = ctx.data['resolved']['messages'][ctx.data['target_id']]

        if ticket is not None:
            # if the user has a ticket, simply add the new request as a message
            entry = await bot.modmail.create_ticket_message(ticket, target_message['content'], 
                attachments=target_message.get("attachments", list()), author=ctx.member['user'])

            # rely information
            has_video = False

            embed = {
                "type": "rich",
                "title": "Message reported",
                "description": "",
                "color": 0x0aeb06,
                "fields": [],
                "footer": {
                    "text": f"{target_message['author']['username']}#{target_message['author']['discriminator']} · Ticket ID {ticket['_id']}",
                    "icon_url": bot.build_avatar_url(target_message['author'])
                },
                "url": bot.build_message_url(ctx.guild_id, ctx.channel_id, ctx.data['target_id'])
            }

            # if message has only attachment and no content then dont add it to fields
            if target_message['content']:
                embed["fields"].append({"name": "Message content", "value": target_message['content']})

            # if attachments include them in embed
            if target_message.get("attachments"):
                att = target_message['attachments'][0]
                embed["fields"].append({"name": "Attachment Information", "value": att['url']})

                if 'image' in att['content_type']:
                    embed["thumbnail"] = {"url": att['url']}
                elif 'video' in att['content_type']:
                    has_video = True
                else:
                    # in case of unknown att do something else, for now not used
                    pass

                embed["fields"].append({"name": "Name", "value": att['filename'], "inline": True})
                embed["fields"].append({"name": "Content Type", "value": att['content_type'], "inline": True})
                embed["fields"].append({"name": "Size", "value": f"{att['width']} x {att['height']}", "inline": True})

            await bot.http.send_message(ticket['modmail_channel_id'], "", embed=embed)
            if has_video:
                await bot.http.send_message(ticket['modmail_channel_id'], target_message['attachments'][0]['url'])

            # Let the user know the message was relied properly.
            embed = {
                "type": "rich",
                "title": "Ticket updated",
                "description": "Your ticket was updated.",
                "color": 0x0aeb06,
                "fields": [
                    {'name': 'Info', 'value': 'The new information was correctly sent to the ticket you previously opened.', 'inline': False}
                ],
                "footer": {
                    "text": f'{bot.default_guild["name"]} Mod Team · Ticket: {ticket["_id"]}'
                }
            }

            data = {
                "tts": False,
                "content": "",
                "embeds": [embed],
                "allowed_mentions": { "parse": [] },
                "flags": 64
            }

            await bot.http.edit_interaction_response(data, ctx.token, ctx.application_id)
            return

        # Create a new ticket for the user
        ticket = await bot.modmail.create_ticket(author=ctx.member['user'],
                                                channel_id=None,
                                                dm_channel_id=dm_channel['id'],
                                                guild_id=ctx.guild_id,
                                                source="slash")

        if ticket is None:
            embed = {
                "type": "rich",
                "title": "Error",
                "description": "There was an error creating your ticket. Please try again or contact a moderator.",
                "color": 0x802d2d,
                "footer": {"text": f'{bot.default_guild["name"]} Mod Team'}
            }

            data = {
                "tts": False,
                "content": "",
                "embeds": [embed],
                "allowed_mentions": { "parse": [] },
                "flags": 64
            }

            await bot.http.edit_interaction_response(data, ctx.token, ctx.application_id)
            return

        # Let the user know it was created properly.
        embed = {
            "type": "rich",
            "title": "Ticket created",
            "description": "Your ticket has been created.",
            "color": 0x0aeb06,
            "fields": [
                {'name': 'Info', 'value': 'Once the Mod Team reviews your ticket they will put in contact with you.\r\n\
                please make sure you enable DMs from people in the same server \
                or you will not be able to receive support from the mod team.', 'inline': False}
            ],
            "footer": {
                "text": f'{bot.default_guild["name"]} Mod Team · Ticket: {ticket["_id"]}'
            }
        }

        data = {
            "tts": False,
            "content": "",
            "embeds": [embed],
            "allowed_mentions": { "parse": [] },
            "flags": 64
        }

        await bot.http.edit_interaction_response(data, ctx.token, ctx.application_id)

        # Add the message to the ticket
        entry = await bot.modmail.create_ticket_message(ticket, target_message['content'], 
                attachments=target_message.get("attachments", list()), author=ctx.member['user'])

        await asyncio.sleep(2) # give 2 seconds for modmail to create the channel and to get modmail_channel_id
        ticket = await bot.modmail.get_ticket({'user_id': ctx.member['user']['id'], 'status': 'active'})

        # rely information
        has_video = False

        embed = {
            "type": "rich",
            "title": "Message reported",
            "description": "",
            "color": 0x0aeb06,
            "fields": [],
            "footer": {
                "text": f"{target_message['author']['username']}#{target_message['author']['discriminator']} · Ticket ID {ticket['_id']}",
                "icon_url": bot.build_avatar_url(target_message['author'])
            },
            "url": bot.build_message_url(ctx.guild_id, ctx.channel_id, ctx.data['target_id'])
        }

        # if message has only attachment and no content then dont add it to fields
        if target_message['content']:
            embed["fields"].append({"name": "Message content", "value": target_message['content']})

        # if attachments include them in embed
        if target_message.get("attachments"):
            att = target_message['attachments'][0]
            embed["fields"].append({"name": "Attachment Information", "value": att['url']})

            if 'image' in att['content_type']:
                embed["thumbnail"] = {"url": att['url']}
            elif 'video' in att['content_type']:
                has_video = True
            else:
                # in case of unknown att do something else, for now not used
                pass

            embed["fields"].append({"name": "Name", "value": att['filename'], "inline": True})
            embed["fields"].append({"name": "Content Type", "value": att['content_type'], "inline": True})
            embed["fields"].append({"name": "Size", "value": f"{att['width']} x {att['height']}", "inline": True})

        await bot.http.send_message(ticket['modmail_channel_id'], "", embed=embed)
        if has_video:
            await bot.http.send_message(ticket['modmail_channel_id'], target_message['attachments'][0]['url'])
