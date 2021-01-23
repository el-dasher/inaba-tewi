from datetime import datetime

import discord
from discord.ext import commands


def setup_generic_embed(bot: commands.Bot, ctx_author: discord.Member):
    generic_embed = discord.Embed(color=ctx_author.color, timestamp=datetime.utcnow())
    generic_embed.set_footer(text=bot.user.display_name, icon_url=bot.user.avatar_url)

    return generic_embed
