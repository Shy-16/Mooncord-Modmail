# -*- coding: utf-8 -*-

## Setup Modmail Button ##
# Sends a followup Modal. #

import discord

def create_modmail_setup_button(bot: discord.Bot, disabled: bool=False):
    class ModmailButton(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(
            custom_id="setup_modmail_button",
            style=discord.ButtonStyle.secondary,
            label="Create Ticket",
            emoji="📩",
            disabled=disabled)
        async def button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
            await interaction.response.send_modal(bot.modmail.create_interaction_modal())

    return ModmailButton()
