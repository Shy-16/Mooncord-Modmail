# -*- coding: utf-8 -*-

## Modmail Module ##
# Interacts with Modmail functionality through API #

import asyncio

import discord
from typing import Any

from modules.context import CommandContext, DMContext
from .commands import (
    Help,
    CloseTicket,
    Lock,
    Unlock,
    SetupModmailButton
)
from .components import ModmailModal


class Modmail:
    def __init__(self, bot: discord.Bot) -> None:
        self._bot = bot
        self._db = bot.db
        
        self.commands = {
            "help": Help(self, 'mod', ['help', 'elp']),
            "close": CloseTicket(self, 'mod'),
            "lock": Lock(self, 'mod'),
            "unlock": Unlock(self, 'mod'),
            "setup_button": SetupModmailButton(self, 'mod')
        }

        self.dm_commands = {
            "help": self.commands['help']
        }

        self.ping_commands = {}

        self._pending_interaction: list[int] = []
        
    def init_tasks(self) -> None:
        """Initialize the different asks that run in the background"""

    async def handle_commands(self, message: discord.Message) -> None:
        """Handles any commands given through the designed character"""
        command = message.content.replace(self._bot.guild_config[message.guild.id]['modmail_character'], '')
        params = []
        if ' ' in command:
            command, params = (command.split()[0], command.split()[1:])
        command = command.lower()
        if command in self.commands:
            await self.commands[command].execute(CommandContext(self._bot, command, params, message))
            return
        # if it starts with = but it doesnt fall into any command then we create a >comment< message
        await self.handle_comment(message)

    async def handle_dm_commands(self, message: discord.Message) -> None:
        """Handles any commands given by a user through DMs"""
        ticket = await self.get_ticket(author_id=message.author.id, filter={'status': 'active'})
        if not ticket or (len(message.content) > 1 and message.content[0] == self._bot.default_guild['modmail_character']):
            # if there is a ticket available only try to execute a command if it starts with command prefix
            # if there is no ticket go for it
            command = message.content.replace(self._bot.default_guild['modmail_character'], '')
            if ' ' in command:
                command, _ = (command.split()[0], command.split()[1:])
            command = command.lower()
            if command in self.dm_commands:
                await self.dm_commands[command].dm(DMContext(self._bot, message))
                return
        await self.handle_dm_message(message, ticket)

    async def handle_ping_commands(self, message: discord.Message) -> None:
        """Handles any commands given by a user through a ping"""
    
    # Functionality
    async def handle_message(self, message: discord.Message, ticket: dict[str, Any] | None = None) -> None:
        """Handles a message sent in a Modmail channel."""
        if not ticket:
            ticket = await self.get_ticket(channel_id=message.channel.id, filter={'status': 'active'})
            if not ticket:
                return

        # if ticket is locked ignore
        if ticket.get("locked"):
            await self.handle_comment(message, ticket)
            return
        
        # otherwise first of all store message
        await self.create_ticket_message(ticket, message.content, message.author, message.attachments)

        # Then rely message in DMs
        if message.content:
            fields = [
                {'name': f"{message.author.name}#{message.author.discriminator}", 'value': message.content, 'inline': False}
            ]
            footer = {'text': f"{message.guild.name} · Ticket ID {ticket['_id']}"}
            try:
                await self._bot.send_embed_dm(int(ticket['author_id']), "Message received", fields=fields, footer=footer)
            except discord.Forbidden as ex:
                # The user doesn't have DM's open or has blocked modmail
                await self._bot.send_embed_message(int(ticket['modmail_channel_id']), "Message delivery failed",
                    f"Message delivery failed with:\r\n{ex}", color=0xcc0000)
                await self.create_ticket_message(ticket, f"Message delivery failed with:\r\n{ex}", self._bot.user)
                await message.add_reaction("✅")
                return

        for attachment in message.attachments:
            try:
                await self._bot.send_dm(int(ticket['author_id']), attachment.url)
            except discord.Forbidden:
                # we shouldn't land in this situation since we already catched
                # it above but... just in case
                pass

        # finally, react to show we sent message properly.
        await message.add_reaction("✅")

    async def handle_dm_message(self, message: discord.Message, ticket: dict | None = None) -> None:
        """Handles a new DM sent to the bot that didnt fall into any command category"""

        if message.author.id in self._pending_interaction:
            # Message is handled by the wait_for event instead.
            return

        # Check for user active tickets
        if not ticket:
            ticket = await self.get_ticket(author_id=message.author.id, filter={'status': 'active'})

        # If there is still no ticket then proceed
        if not ticket:
            # Ask the user if they want to make a new ticket.
            request_message: discord.Message = await self._bot.send_dm(message.author, "Would you like to create a new ticket to report an issue to the Mod team?")
            await request_message.add_reaction("✅")
            await request_message.add_reaction("⛔")

            def wait_for_react(reaction: discord.Reaction, user: discord.User) -> bool:
                return user == message.author and (str(reaction.emoji) == "✅" or str(reaction.emoji) == "⛔")

            reaction: discord.Reaction = None
            try:
                reaction, _ = await self._bot.wait_for('reaction_add', check=wait_for_react, timeout=60.0)
            except asyncio.TimeoutError:
                await reaction.message.delete()
                await self._bot.send_dm(message.author, "Time expired. Please try initiating the Ticket process again.")
                return

            await reaction.message.delete()

            if str(reaction.emoji) == "⛔":
                return

            if str(reaction.emoji) == "✅":
                self._pending_interaction.append(message.author.id)
                await self._bot.send_dm(message.author, "Please explain the issue that you'd like to report:")

                def wait_for_dm_reply(event_message: discord.Message) -> bool:
                    return event_message.author == message.author

                ticket_message: discord.Message = None

                try:
                    ticket_message = await self._bot.wait_for('message', check=wait_for_dm_reply, timeout=60.0)
                except asyncio.TimeoutError:
                    await self._bot.send_dm(message.author, "Time expired. Please try initiating the Ticket process again.")
                    self._pending_interaction.remove(message.author.id)
                    return

                self._pending_interaction.remove(message.author.id)

                # Create the ticket
                ticket = await self.create_ticket(author=message.author,
                                            channel_id=None,
                                            dm_channel_id=message.channel.id,
                                            guild_id=self._bot.default_guild['guild_id'],
                                            source="dm")

                # Send information to the user
                fields = [
                    {'name': 'Info', 'value': "Anything you type in this DM will be conveyed to the Mod Team .\r\n"+
                        "Once the Mod Team reviews your ticket they will put in contact with you through this same channel.", 'inline': False},
                ]

                footer = {"text": f'{self._bot.default_guild["name"]} Mod Team · Ticket: {ticket["_id"]}'}

                await self._bot.send_embed_dm(message.author, "Ticket created", description="Your ticket has been created.", color=0x0aeb06,
                    fields=fields, footer=footer)

                # Create channel in server
                modmail_channel = await self.create_modmail_channel(ticket, message.author)
                ticket["modmail_channel_id"] = str(modmail_channel.id)
                
                # Rely information to server
                footer = {
                    "text": f"{ticket_message.author.name}#{ticket_message.author.discriminator} · Ticket ID {ticket['_id']}",
                    "icon_url": ticket_message.author.avatar.url
                }
                await self._bot.send_embed_message(modmail_channel, "Message received", ticket_message.content,
                                                    color=0x0aeb06, footer=footer)
                for attachment in ticket_message.attachments:
                    await self._bot.send_message(modmail_channel, attachment.url)

                # add a new entry to history of ticket
                await self.create_ticket_message(ticket, ticket_message.content, ticket_message.author, ticket_message.attachments)

                footer = {"text": f'{self._bot.default_guild["name"]} Mod Team · Ticket: {ticket["_id"]}'}
                await self._bot.send_embed_dm(ticket_message.author, "Message sent", ticket_message.content, footer=footer)
                return

        # rely information
        footer = {
            "text": f"{message.author.name}#{message.author.discriminator} · Ticket ID {ticket['_id']}",
            "icon_url": message.author.avatar.url
        }
        await self._bot.send_embed_message(int(ticket['modmail_channel_id']), "Message received", message.content,
                                            color=0x0aeb06, footer=footer)
        for attachment in message.attachments:
            await self._bot.send_message(int(ticket['modmail_channel_id']), attachment.url)

        # add a new entry to history of ticket
        await self.create_ticket_message(ticket, message.content, message.author, message.attachments)

        footer = {"text": f'{self._bot.default_guild["name"]} Mod Team · Ticket: {ticket["_id"]}'}
        await self._bot.send_embed_dm(message.author, "Message sent", message.content, footer=footer)

    async def handle_comment(self, message: discord.Message, ticket: dict[str, Any] | None = None) -> None:
        """Creates a comment sent in a Modmail channel."""
        if not ticket:
            ticket = await self.get_ticket(channel_id=message.channel.id, filter={'status': 'active'})
            if not ticket:
                return
        await self.create_ticket_message(ticket, message.content, author=message.author, mode='comment')
        
    async def handle_interaction(self, interaction: discord.Interaction) -> None:
        """Handles interactions from Application commands"""
        if interaction.custom_id == "setup_modmail_button":
            await interaction.response.send_modal(self.create_interaction_modal())

    async def get_ticket(self, author_id: int | None = None, channel_id: int | None = None, filter: dict | None = None) -> dict | None:
        """Get a ticket for given user or channel."""
        params = {}
        if author_id is not None:
            params["author_id"] = str(author_id)
        if channel_id is not None:
            params["modmail_channel_id"] = str(channel_id)
        if filter:
            params.update(filter)
        return self._db.get_ticket(params)

    async def create_ticket(self, author: discord.Member | discord.User, channel_id: int | None, 
                            dm_channel_id: int, guild_id: int, source: str = "dm") -> dict:
        """Create a new ticket."""
        ticket = self._db.create_ticket(author=author,
                                        channel_id=channel_id,
                                        dm_channel_id=dm_channel_id,
                                        guild_id=guild_id,
                                        source=source)
        return ticket

    async def create_ticket_message(self, ticket: dict[str, Any], content: str, author: discord.User | discord.Member,
                                    attachments: list[discord.Attachment] | None = None, mode: str = 'message') -> dict:
        """Create a new message for given ticket from provided context."""
        entry = self._db.create_ticket_message(str(ticket['_id']), content, author, attachments, mode)
        return entry

    async def lock_ticket(self, ticket: dict[str, Any]) -> dict:
        """Locks a ticket"""
        ticket = self._db.lock_ticket(ticket_id=str(ticket['_id']))
        return ticket

    async def unlock_ticket(self, ticket: dict[str, Any]) -> dict:
        """Unlocks a ticket"""
        ticket = self._db.unlock_ticket(ticket_id=str(ticket['_id']))
        return ticket

    async def close_ticket(self, ticket: dict[str, Any], author: discord.Member, data: dict) -> dict:
        """Closes a ticket"""
        ticket = self._db.close_ticket(ticket_id=str(ticket['_id']), author_id=str(author.id), data=data)
        return ticket
    
    # Helpers
    async def create_modmail_channel(self, ticket: dict[str, Any], user: discord.User | discord.Member) -> discord.TextChannel:
        """Creeates a channel with given ticket_id name"""
        guild: discord.Guild = self._bot.get_guild(int(ticket['guild_id']))
        guild_config = self._bot.guild_config[guild.id]
        category: discord.CategoryChannel = guild.get_channel(int(guild_config['modmail_category']))
        modmail_channel: discord.TextChannel = guild.get_channel(int(guild_config['modmail_channel']))
        ticket_channel: discord.TextChannel = await guild.create_text_channel(str(ticket['_id']), category=category)
        self._db.update_ticket(ticket["_id"], {"modmail_channel_id": str(ticket_channel.id)})
        
        if isinstance(user, discord.User):
            user = guild.get_member(user.id)

        url = self._bot.config["modmail"]["public_url"] + f'/modmail/tickets/{ticket["_id"]}'
        fields = [
            {'name': 'Dashboard', 'value': f"You can view full details and work further in the Ticket dashboard:\r\n{url}"},
        ]
        footer = {
            'text': f"{user.name}#{user.discriminator} · Ticket ID {ticket['_id']}",
            'icon_url': user.avatar.url
        }
        await self._bot.send_embed_message(modmail_channel, "New Ticket", color=2067276, fields=fields, footer=footer)

        roles = " ".join([f"<@&{role.id}>" for role in user.roles])
        description = f"Type a message in this channel to reply. Messages starting with the server prefix `{guild_config['modmail_character']}` " \
                    + f"are ignored, and can be used for staff discussion. User the command `{guild_config['modmail_character']}close <reason:optional>` to " \
                    + "close the ticket."
        fields = [
            {'name': 'User', 'value': f"<@{user.id}> ({user.id})", 'inline': True},
            {'name': 'Roles', 'value': roles, 'inline': True},
            {'name': 'Dashboard', 'value': f"You can view full details and work further in the Ticket dashboard:\r\n{url}"}
        ]
        await self._bot.send_embed_message(ticket_channel, "New Ticket", description, color=2067276, fields=fields, footer=footer)
        return ticket_channel

    # Interactions
    def create_interaction_modal(self) -> discord.ui.Modal:
        """Creates a modal to respond to interactions"""
        modal_input = discord.ui.InputText(
            style=discord.InputTextStyle.long,
            custom_id="modmail_topic",
            label="Ticket Topic",
            placeholder="Please state the issue you'd like to report",
            min_length=1,
            max_length=2000,
            required=True
        )
        return ModmailModal(modal_input, title="New Modmail", custom_id="create_ticket_modal", bot=self._bot)
