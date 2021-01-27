from typing import Union

import discord
from discord.ext import commands


class ErrorHandler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, exc: Exception) -> Union[Exception, discord.Message]:
        unexpected_response: str = "❎ **|  Ocorreu um  erro inesperado!**"
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
            args_0: str = exc.args[0]
            if "ContentTypeError" or "ClientConnectorError" in args_0:
                if "ContentTypeError" in args_0:
                    return await ctx.reply(
                        "❎ **| Não foi possivel adquirir uma resposta adequada do site"
                        " ou API necessária para que este comando funcione!**"
                    )
                elif "ClientConnectorError" in args_0:
                    return await ctx.reply(
                        "❎ **| Não foi possível se conectar ao site ou API necessária para que esse comando funcione!**"
                    )
            else:
                await ctx.reply(unexpected_response)
                raise exc
        else:
            await ctx.reply(unexpected_response)
            raise exc

def setup(bot):
    bot.add_cog(ErrorHandler(bot))
