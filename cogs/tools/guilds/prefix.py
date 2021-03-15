import discord

from discord.ext import commands
from utils.bot_defaults import GenericEmbed

from utils.database import MAIN_TEWI_DB
from utils.bot_setup import DEFAULT_BOT_PREFIXES


class PrefixHelpEmbed(GenericEmbed):
    def __init__(self, bot: commands.Bot, ctx_author: discord.Member, **kwargs):
        super().__init__(bot, ctx_author, **kwargs)

        self.add_field(name='prefix -get', value=">>> **Pega o prefixo customizado do servidor atual**", inline=False)
        self.add_field(name='prefix -set', value=">>> **Muda o prefixo customizado do servidor atual**", inline=False)


class Prefix(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    @commands.has_permissions(administrator=True)
    @commands.command(name="prefix")
    async def prefix_main(self, ctx: commands.Context, *args) -> discord.Message:
        if not args:
            prefix_help_embed: PrefixHelpEmbed = PrefixHelpEmbed(self.bot, ctx.author)

            return await ctx.reply(ctx.author.mention, embed=prefix_help_embed)
        elif args[0] == '-set':
            if not args[1]:
                return await ctx.reply('❎ **| Você precisa definir um prefixo para a guilda! **')
            else:
                new_custom_prefix: str = args[1]
                MAIN_TEWI_DB.post_new_custom_prefix(ctx.guild, new_custom_prefix)

                return await ctx.reply(f"✅ **| O prefixo neste servidor foi atualizado para `{new_custom_prefix}`**")
        elif args[0] == '-get':
            guild_custom_prefix: str = MAIN_TEWI_DB.get_guild_custom_prefix(ctx.guild)

            if not guild_custom_prefix:
                return await ctx.reply(
                    f'❎ ** | O meu prefixo padrão é `{DEFAULT_BOT_PREFIXES[0]}`!'
                    f' este servidor não usa um prefixo customizado **'
                )
            else:
                return await ctx.reply(f"✅ **| O meu prefixo neste servidor é `{guild_custom_prefix}`!**")


def setup(bot):
    bot.add_cog(Prefix(bot))
