# -*- coding: utf-8 -*-

## Bot Module ##
# This is the main Bot module with functionality #

import logging
import traceback
from typing import Any

import discord

from modules import Modmail
from database import Database
from application_commands import slash_help, slash_modmail, context_modmail


log: logging.Logger = logging.getLogger("discord")


class Bot(discord.Bot):
    def __init__(self, config: dict) -> None:
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        
        self.config: dict[str, Any] = config
        self.guild_config: dict[int, dict[str, Any]] = {}
        self.default_guild: dict[str, Any] = None

        self.db = Database(config['database'])
        self.modmail = Modmail(self)

    ## On error handler
    async def on_error(self, *args, **kwargs):
        exc_err = traceback.format_exc()
        log.error("Bot handled an error on event: {} with error:\r\n{}".format(args, exc_err))

    ### Client Events
    async def on_ready(self) -> None:
        log.info(f"New bot instance created: {self.user.name} ID: {self.user.id}.")
        log.info('Loading guild configuration.')
        for guild in self.guilds:
            guild_config = await self.db.load_server_configuration(guild, self)
            self.guild_config[guild.id] = guild_config
            if self.default_guild is None: self.default_guild = guild_config
            print(f'Guild {guild.id} loaded.')
            logging.info(f'Loaded configuration for guild: {guild.id}.')
        log.info('Finished loading all guild info.')
        log.info("All configuration finished.")
        
        slash_help(self)
        slash_modmail(self)
        context_modmail(self)
        
    async def on_interaction(self, interaction: discord.Interaction) -> None:
        """Handles incoming interactions"""
        print(interaction, interaction.application_id)
        await self.modmail.handle_interaction(interaction)
        
    async def on_message(self, message: discord.Message) -> None:
        """Handle create message event"""
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id or message.author.bot:
            return

        # Someone sent a DM to the bot.
        if not hasattr(message, 'guild') or message.guild is None:
            await self.modmail.handle_dm_commands(message)
            return

        # Check for pings
        if len(message.mentions) > 0 and message.mentions[0].id == self.user.id:
            # Someone pinged the bot.
            await self.modmail.handle_ping_commands(message)
            return

        # Someone used a command.
        if message.content.startswith(self.guild_config[message.guild.id]['modmail_character']):
            await self.modmail.handle_commands(message)
            return

        # Else check if we belong to a modmail channel
        await self.modmail.handle_message(message)

    # Utils to make stuff easier
    def build_message_url(self, guild_id: int, channel_id: int, message_id: int) -> str:
        """Build message url"""
        return f'https://discord.com/channels/{guild_id}/{channel_id}/{message_id}'
    
    async def send_message(self, channel: int | discord.TextChannel, content: str="") -> dict:
        """Send a regular message on a channel"""
        try:
            if isinstance(channel, int):
                message = await self.get_channel(channel).send(content=content)
            else:
                message = await channel.send(content=content)
        except Exception:
            message = {}
        return message
    
    async def send_embed_message(self, channel: int | discord.TextChannel, title: str="", description: str="", 
        color: int=0x0aeb06, fields: list=None, footer: dict=None, image: dict=None, view: discord.ui.View | None=None,
        url: str | None = None, thumbnail: dict[str, str] | None = None) -> dict:
        """Sends an embed message to given channel_id"""
        embed = {
            "type": "rich",
            "title": title,
            "description": description,
            "color": color,
            "fields": fields or []
        }
        if footer is not None:
            embed['footer'] = footer
        if image is not None:
            embed['image'] = image
        if url is not None:
            embed['url'] = url
        if thumbnail is not None:
            embed['thumbnail'] = thumbnail

        try:
            if isinstance(channel, int):
                message = await self.get_channel(channel).send(embed=discord.Embed.from_dict(embed), view=view)
            else:
                message = await channel.send(embed=discord.Embed.from_dict(embed), view=view)
        except Exception:
            message = {}

        return message

    async def send_dm(self, user: int | discord.User, content: str="") -> dict:
        """Send a regular DM"""
        try:
            if isinstance(user, int):
                dm_channel = await self.get_user(user).create_dm()
            else:
                dm_channel = await user.create_dm()
            message = await dm_channel.send(content=content)
        except Exception:
            message = {}
        return message

    async def send_embed_dm(self, user: int | discord.User, title: str="", description: str="", color: int=0x0aeb06, fields: list=None,
        footer: dict=None, image: dict=None) -> dict:
        """Sends an embed DM to given user_id"""

        embed = {
            "type": "rich",
            "title": title,
            "description": description,
            "color": color,
            "fields": fields
        }

        if footer is not None:
            embed['footer'] = footer

        if image is not None:
            embed['image'] = image

        try:
            if isinstance(user, int):
                dm_channel = await self.get_user(user).create_dm()
            else:
                dm_channel = await user.create_dm()
            message = await dm_channel.send(embed=discord.Embed.from_dict(embed))
        except Exception:
            message = {}

        return message
