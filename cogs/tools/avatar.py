import discord
from discord.ext import commands
from utils.bot_defaults import setup_generic_embed


class Avatar(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    @commands.command()
    async def avatar(self, ctx: discord.ext.commands.Context, member: discord.Member = None):
        bot_avatar_res: str = "O avatar dele é muito legal"
        if member is None:
            bot_avatar_res = "O seu avatar é top"

            member = ctx.author

        avatar_embed: discord.Embed = setup_generic_embed(self.bot, member)
        avatar_embed.set_image(url=member.avatar_url)
        avatar_embed.set_author(name=bot_avatar_res, url=member.avatar_url)

        await ctx.reply(ctx.author.mention, embed=avatar_embed)


def setup(bot):
    bot.add_cog(Avatar(bot))
