# -*- coding: utf-8 -*-

import asyncio
import signal
import sys
import traceback
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import discord

from modmail import Modmail
from database import Database
from commands import create_ticket, close_ticket, help_command, help_dm_command, lock_ticket, unlock_ticket
from commands import handle_modmail_slash, handle_modmail_context, handle_help_slash, setup_ticket_button
from commands import handle_create_ticket_button, handle_create_ticket_modal

log: logging.Logger = logging.getLogger("client")


class Bot(discord.Client):

    def __init__(self, *, config: dict) -> None:
        super().__init__(intents=discord.Intents.all())

        self.config = config
        self.guild_config = dict()
        self.default_guild = None

        self.modmail = Modmail(self)

        self.commands = {
            "help": help_command,
            "close": close_ticket,
            "lock": lock_ticket,
            "unlock": unlock_ticket,
            "setup_button": setup_ticket_button
        }

        self.dm_commands = {
            "help": help_dm_command
        }

        handle_modmail_slash(self)
        handle_modmail_context(self)
        handle_help_slash(self)
        handle_create_ticket_button(self)
        handle_create_ticket_modal(self)

    ## On error handler
    async def on_error(self, event, err):
        exc_err = traceback.format_exc()
        log.error("Bot handled an error on event: {} with error:\r\n{}".format(event, exc_err))

    async def on_ready(self, ctx):
        db = Database(self.config['database'])

        for guild in self.guilds:
            print(f'Guild {guild.id} is being loaded.')
            guild_config = await db.load_server_configuration(guild.__dict__, self)
            self.guild_config[guild.id] = guild_config
            if self.default_guild is None: self.default_guild = guild_config
            print(f'Guild {guild.id} loaded.')
            logging.info(f'Loaded configuration for guild: {guild.id}.')

        print('Finished loading all guild info.')
        logging.info("All configuration finished.")

    async def on_message_create(self, message):
        # # 'attachments', 'author', 'channel_id', 'components', 'content', 'edited_timestamp', 'embeds', 'event_name', 'flags', 'guild_id', 'id', 
        # 'member', 'mention_everyone', 'mention_roles', 'mentions', 'nonce', 'pinned', 'referenced_message', 'send', 'timestamp', 'tts', 'type'

        if str(message.author['id']) == str(self.user.id) or message.author.get('bot', False):
            return

        if not hasattr(message, 'guild_id'):
            # If guild_id is missing means this message is a DM

            # If the user has an active ticket it will override any commands
            # so it doesnt interfere with explanations
            ticket = await self.modmail.get_ticket({'user_id': int(message.author['id']), 'status': 'active'})

            if not ticket or (len(message.content) > 1 and message.content[0] == self.default_guild['modmail_character']):
                # if there is a ticket available only try to execute a command if it starts with command prefix
                # if there is no ticket go for it
                command = message.content
                params = list()
                command = command.replace(self.default_guild['modmail_character'], '')

                if ' ' in command:
                    command, params = (command.split()[0], command.split()[1:])
                
                command = command.lower()

                if command in self.dm_commands:
                    await self.dm_commands[command](self, message, params)
                    return

            await self.modmail.handle_dm_message(message, ticket)
            return

        if message.content.startswith(self.guild_config[str(message.guild_id)]['modmail_character']):
            command = message.content
            params = list()
            command = command.replace(self.guild_config[str(message.guild_id)]['modmail_character'], '')

            if ' ' in command:
                command, params = (command.split()[0], command.split()[1:])

            command = command.lower()

            if command in self.commands:
                await self.commands[command](self, message, params)
                return

            # if it starts with = but it doesnt fall into any command then we ignore the message
            # but we still create a >comment< message
            await self.modmail.handle_comment(message)
            return

        # Else check if we belong to a modmail channel
        await self.modmail.handle_message(message)

    # Utils to make stuff easier
    def build_message_url(self, guild_id: int, channel_id: int, message_id: int) -> str:
        """
        Build message url

        @guild_id: int: guild id
        @channel_id: int: channel id
        @message_id: int: message id

        return: str: built URL to message
        """

        return f'https://discord.com/channels/{guild_id}/{channel_id}/{message_id}'

    def build_avatar_url(self, user: dict) -> str:
        """
        Build user avatar

        @user: dict: User data

        return: str: built URL to avatar
        """

        return f'https://cdn.discordapp.com/avatars/{user["id"]}/{user["avatar"]}.png?size=4096'

    async def send_message(self, channel_id: int, content: str = ""):
        message = await self.http.send_message(channel_id, content)

        return message

    async def send_embed_message(self, channel_id: int, title: str = "", description: str = "", color: int = 0x0aeb06, fields: list = list(),
        footer: dict = None, components: Optional[list] = None) -> dict:
        embed = {
            "type": "rich",
            "title": title,
            "description": description,
            "color": color,
            "fields": fields
        }

        if footer is not None:
            embed['footer'] = footer

        message = await self.http.send_message(channel_id, '', embed=embed, components=components)

        return message

    async def send_dm(self, user_id: int, content: str = ""):
        dm_channel = await self.http.create_dm(user_id)
        message = await self.http.send_message(dm_channel['id'], content)

        return message

    async def send_embed_dm(self, user_id: int, title: str = "", description: str = "", color: int = 0x0aeb06, fields: list = list(),
        footer: dict = None) -> dict:

        embed = {
            "type": "rich",
            "title": title,
            "description": description,
            "color": color,
            "fields": fields
        }

        if footer is not None:
            embed['footer'] = footer

        dm_channel = await self.http.create_dm(user_id)
        message = await self.http.send_message(dm_channel['id'], '', embed=embed)

        return message
