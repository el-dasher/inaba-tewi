from typing import Union

import discord
from discord.ext import commands

from helpers.osu.droid.user_data.osu_droid_data import OsuDroidProfile, new_osu_droid_profile
from utils.osu_ppy_and_droid_utils import (
    default_user_exists_check,
    submit_profile_to_db,
    default_search_for_uid_in_db_handling
)


class Submit(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    @staticmethod
    async def submit_profile_main(
            ctx: commands.Context, uid: Union[int, None] = None, force_submit: bool = False
    ):
        osu_droid_user: OsuDroidProfile = await new_osu_droid_profile(
            uid, needs_player_html=True, needs_pp_data=True
        )

        if await default_user_exists_check(ctx, osu_droid_user):
            async with ctx.typing():
                bot_submit_res: str = "✅ **| Os seus dados foram sequestrados por mim com sucesso!**"
                if force_submit:
                    await ctx.reply("**Irei tentar sequestrar os dados dele!**")
                    bot_submit_res = "✅ **| Os dados dele foram sequestrados por mim com sucesso!**"
                else:
                    await ctx.reply("**Irei tentar sequestrar seus dados!**")

            await submit_profile_to_db(osu_droid_user)
            await ctx.reply(bot_submit_res)

    @commands.has_permissions(administrator=True)
    @commands.command(name='forcesubmit')
    async def force_submit(self, ctx: commands.Context, member: Union[discord.Member, int] = None):
        if not member:
            return await ctx.reply('❎ **| Ei adm, você esqueceu do usúario que você quer submitar!**')

        droid_user_id = member
        if isinstance(member, discord.Member):
            droid_user_id: Union[int, None] = await default_search_for_uid_in_db_handling(ctx=ctx, uid=member)

        if not droid_user_id:
            return None

        await self.submit_profile_main(ctx, droid_user_id, True)

    @commands.command(name="submit")
    async def submit_profile(self, ctx: commands.Context):
        droid_user_id: Union[int, None] = await default_search_for_uid_in_db_handling(ctx=ctx, uid=None)

        if not droid_user_id:
            return None

        await self.submit_profile_main(ctx, droid_user_id)


def setup(bot):
    bot.add_cog(Submit(bot))
