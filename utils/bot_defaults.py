from datetime import datetime

import discord
from discord.ext import commands


class GenericEmbed(discord.Embed):
    def __init__(self, bot: commands.Bot, ctx_author: discord.Member,  **kwargs):
        super().__init__(**kwargs)

        self.color = ctx_author.color
        self.timestamp = datetime.utcnow()
        self.set_footer(text=bot.user.display_name, icon_url=bot.user.avatar_url)

