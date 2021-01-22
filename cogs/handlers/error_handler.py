from typing import Union

import discord
from discord.ext import commands


class ErrorHandler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, exc: Exception) -> Union[Exception, discord.Message]:
        if isinstance(exc, commands.CommandNotFound):
            return await ctx.reply("❎ **| Eu não tenho esse comando atualmente, desculpa...**")
        elif isinstance(exc, commands.MemberNotFound):
            return await ctx.reply("❎ **| Eu não consegui encontrar o usuário mencionado...**")
        elif isinstance(exc, commands.MissingPermissions):
            return await ctx.reply("❎ **| Você não tem permissão para usar esse comando!**")
        elif isinstance(exc, commands.BotMissingPermissions):
            return await ctx.reply("❎ **|Eu não tenho permissões para fazer isso!**")
        elif isinstance(exc, commands.MissingRequiredArgument):
            return await ctx.reply("❎ **| Você esqueceu de algum argumento necessário para o comando**")
        elif isinstance(exc, commands.ChannelNotFound):
            return await ctx.reply("❎ **| Não foi possível encontrar o canal especificado!**")
        elif isinstance(exc, commands.BadUnionArgument) or isinstance(exc, commands.BadArgument):
            return await ctx.reply(
                "❎ **| Algum parâmetro que você digitou no comando está com o tipo errado. Ex: ID (números) -> letras**"
            )
        elif hasattr(exc, "original"):
            raise exc.original
        else:
            raise exc


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
