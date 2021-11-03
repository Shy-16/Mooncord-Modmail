# -*- coding: utf-8 -*-
#pylint: disable=unused-variable,unused-argument,too-many-lines

from discord import Embed
from discord.ext.commands import Bot, Cog
from discord_slash import cog_ext, SlashContext

class Slash(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @cog_ext.cog_slash(name="modmail")
    async def modmail(self, ctx: SlashContext):
        embed = Embed(title="Embed Test")
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Slash(bot))