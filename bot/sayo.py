# -*- coding: utf-8 -*-

## Sayo Module ##
# This is the main Bot module with functionality #

import logging
import yaml
import datetime
import discord
from discord.utils import get
from discord.ext import tasks
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option

from db import Database
from .utils import iso_to_datetime, datetime_to_iso, date_string_to_timedelta
from .log_utils import init_log, do_log

from .commands import CommandContext, DMContext, BotConfig, Help, Close, Shutdown
from .modules.modmail import Modmail

guilds_ids = [553454168631934977]

class Sayo(discord.Client):

    def __init__(self, config, args):
        super().__init__(intents=discord.Intents.all())
        self.slash = SlashCommand(self, sync_commands=True)

        if(not args.token):
            print("You need to provide a secret token with \"--token\" or \"-t\" ")
            return

        self.config = config
        self.guild_config = dict()
        self.default_guild = None
        self.args = args
        self.db = Database(self.config['database'])

        self.end_bot = False

        self.modmail = Modmail(self)
        self.handling_dm = []

        self.commands = {
            "shutdown": Shutdown(self, 'admin'),
            "config": BotConfig(self, 'admin'),
            "help": Help(self, 'mod', ['help', 'elp'])
        }

        self.dm_commands = {
            "help": self.commands['help']
        }

        self.modmail_commands = {
            "close": Close(self, self.modmail, 'mod')
        }

        self.slash.add_slash_command(self.modmail_slash, name="modmail", description="Send a new modmail to the staff.",
            options=[create_option(name="description", description="What you want to report", option_type=3, required=True)],
            guild_ids=guilds_ids)

        init_log()

    def run(self):
        super().run(self.args.token)

    async def modmail_slash(self, ctx: SlashContext, description: str):
        print("hi im here", self, ctx, description)
        embed = Embed(title="Embed Test")
        await ctx.send(embed=embed)

    ### Client Events
    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author == self.user or message.author.bot:
            return

        if message.channel.type == discord.enums.ChannelType.private:
            # Someone sent a DM to the bot.
            if message.author.id in self.handling_dm: return

            # If the user has an active ticket it will override any commands
            # so it doesnt interfere with explanations
            ticket = await self.modmail.has_active_ticket(DMContext(self, message))

            if not ticket or (len(message.content) > 1 and message.content[0] == self.default_guild['modmail_character']):
                # if there is a ticket available only try to execute a command if it starts with command prefix
                # if there is no ticket go for it
                for dm_command in self.dm_commands:
                    for keyword in self.dm_commands[dm_command].dm_keywords:
                        if keyword in message.content:
                            await self.dm_commands[dm_command].dm(DMContext(self, message))
                            return

            await self.modmail.handle_dm_message(DMContext(self, message))
            return

        if message.content.startswith(self.guild_config[message.guild.id]['modmail_character']):
            command = message.content
            params = list()
            command = command.replace(self.guild_config[message.guild.id]['modmail_character'], '')

            if ' ' in command:
                command, params = (command.split()[0], command.split()[1:])

            command = command.lower()

            if command in self.commands:
                await self.commands[command].execute(CommandContext(self, command, params, message))
                return
            
            elif command in self.modmail_commands:
                await self.modmail_commands[command].execute(CommandContext(self, command, params, message))
                return

            return

        # else check if its in a channel dedicated to modmail
        await self.modmail.handle_message(DMContext(self, message))

    async def on_reaction_add(self, reaction, user):
        # This event doesnt trigger if the message is no longer cached

        if user == self.user or user.bot:
            return

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')
        logging.info(f"New bot instance created: {self.user.name} ID: {self.user.id}.")

        print('Loading configuration for guilds:')
        # Load server configuration from database
        for guild in self.guilds:
            print(f'Guild {guild.id} is being loaded.')
            guild_config = self.db.load_server_configuration(guild, self)
            self.guild_config[guild.id] = guild_config
            if self.default_guild is None: self.default_guild = guild_config
            print(f'Guild {guild.id} loaded.')
            logging.info(f"Loaded configuration for guild: {guild.id}.")

        print('Finished loading all guild info.')
        logging.info("All configuration finished.")

        activity = discord.Game("DM to contact staff | DM help for more info.")
        await super().change_presence(activity=activity)

    async def update_guild_configuration(self, guild):
        guild_config = self.db.load_server_configuration(guild, self)
        self.guild_config[guild.id] = guild_config

    ### Utils
    async def send_message(self, channel, message=""):
        if type(channel) is not discord.channel.TextChannel:
            await self.get_channel(channel).send(message)
            return

        new_message = await channel.send(message)
        return new_message

    async def send_embed_message(self, channel, title="", description='', colour=discord.Colour.dark_green(), fields=[], footer=None, footer_icon=discord.Embed.Empty):
        embed = discord.Embed(
            title=title,
            description=description,
            type="rich",
            colour=colour
        )
        for field in fields:
            embed.add_field(name=field['name'],
                            value=field['value'],
                            inline=field['inline'])

        if footer is not None:
            embed.set_footer(text=footer, icon_url=footer_icon)
            
        if type(channel) is not discord.channel.TextChannel:
            chan = self.get_channel(channel)

            if chan is None:
                chan = await self.fetch_channel(channel)

            await chan.send("", embed=embed)
            return

        new_message = await channel.send("", embed=embed)
        return new_message

    async def send_dm(self, user, message=""):
        if isinstance(user, int) or isinstance(user, str):
            user = self.get_user(user)

        new_message = await user.send(message)
        return new_message

    async def send_embed_dm(self, user, title="", description='', colour=discord.Colour.dark_green(), fields=[], footer=None, footer_icon=discord.Embed.Empty):
        embed = discord.Embed(
            title=title,
            description=description,
            type="rich",
            colour=colour
        )
        for field in fields:
            embed.add_field(name=field['name'],
                            value=field['value'],
                            inline=field['inline'])

        if footer is not None:
            embed.set_footer(text=footer, icon_url=footer_icon)

        if isinstance(user, int) or isinstance(user, str):
            user = self.get_user(user)

        new_message = await user.send("", embed=embed)
        return new_message
