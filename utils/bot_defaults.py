from discord.ext import commands
import discord
from datetime import datetime


def setup_generic_embed(bot: commands.Bot, ctx_author: discord.Member):
    generic_embed = discord.Embed(color=ctx_author.color, timestamp=datetime.utcnow())
    generic_embed.set_footer(text=bot.user.display_name, icon_url=bot.user.avatar_url)

    return generic_embed
