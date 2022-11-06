# -*- coding: utf-8 -*-

## Command Context ##
# Loads all context required to execute commands #

import discord


class CommandContext:
    def __init__(self, bot: discord.Bot, command: str, params: list[str], message: discord.Message) -> None:
        self._bot = bot
        self.command = command
        self.params = params
        self.message = message
        self.content = self.message.content

        self.id = message.id
        self.author = message.author
        self.guild = message.guild
        self.channel = message.channel
        self.channel_id = message.channel.id

        self.mentions = message.mentions
        self.role_mentions = message.role_mentions
        self.channel_mentions = message.channel_mentions

        self.stickers = message.stickers

        self.is_admin = self._is_admin()
        self.is_mod = self._is_mod()
        self.log_channel = int(self._bot.guild_config[self.guild.id]['log_channel'])
        self.command_character = self._bot.guild_config[self.guild.id]['command_character']
        self.modmail_category = int(self._bot.guild_config[self.guild.id]['modmail_category'])
        self.modmail_channel = int(self._bot.guild_config[self.guild.id]['modmail_channel'])
        self.modmail_character = self._bot.guild_config[self.guild.id]['modmail_character']
        self.ban_roles = [discord.Object(int(role)) for role in self._bot.guild_config[self.guild.id]['ban_roles']]

    def _is_admin(self):
        """Check all roles for admin privileges"""
        for role in self.author.roles:
            if str(role.id) in self._bot.guild_config[self.guild.id]['admin_roles']:
                return True
        return False

    def _is_mod(self):
        """Check all roles for mod privileges"""
        for role in self.author.roles:
            if str(role.id) in self._bot.guild_config[self.guild.id]['mod_roles']:
                return True
        return False


class DMContext:
    def __init__(self, bot: discord.Bot, message: discord.Message) -> None:
        self._bot = bot
        self.message = message

        self.author = message.author
        self.channel = message.channel
        self.channel_id = message.channel.id
        self.mentions = message.mentions
        self.channel_mentions = message.channel_mentions

        self.log_channel = int(self._bot.guild_config[self.guild.id]['log_channel'])
        self.command_character = self._bot.guild_config[self.guild.id]['command_character']
        self.modmail_category = int(self._bot.guild_config[self.guild.id]['modmail_category'])
        self.modmail_channel = int(self._bot.guild_config[self.guild.id]['modmail_channel'])
        self.modmail_character = self._bot.guild_config[self.guild.id]['modmail_character']
