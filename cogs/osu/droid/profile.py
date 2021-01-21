from typing import Union

import discord
from discord.ext import commands

from helpers.osu.droid.osu_droid_data import new_osu_droid_profile
from utils.osu_droid_utils import default_total_dpp, default_search_for_user_in_db_handling, default_user_exists_check


class Profile(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    @commands.command(name="profile", aliases=["pfme", "pfid", "pf"])
    async def profile(
            self, ctx: commands.Context, uid: Union[discord.Member, int] = None
    ) -> Union[discord.Message, None]:
        droid_user_id: Union[int, None] = await default_search_for_user_in_db_handling(ctx=ctx, uid=uid)

        osu_droid_user: new_osu_droid_profile = await new_osu_droid_profile(
            droid_user_id, needs_player_html=True, needs_pp_data=True
        )

        profile_embed: discord.Embed = discord.Embed(color=ctx.author.color)
        profile_embed.set_thumbnail(url=osu_droid_user.avatar)

        profile_embed.set_author(
            url=f"http://ops.dgsrz.com/profile.php?uid={osu_droid_user.uid}",
            name=f"Perfil do(a) {osu_droid_user.username}"
        )

        if await default_user_exists_check(ctx, osu_droid_user):
            droid_user_total_dpp: Union[str, None] = default_total_dpp(osu_droid_user)
        else:
            return None

        profile_embed.add_field(
            name="---Informações ",
            value=">>> "
                  "**"
                  f"Ele(a) é do(a) (:flag_{osu_droid_user.country.lower()}:) \n"
                  f"Rank: #{osu_droid_user.rank_score}                       \n"
                  f"Total score: {osu_droid_user.total_score:,}              \n"
                  f"Total DPP: {droid_user_total_dpp}                        \n"
                  f"Overall acc: {osu_droid_user.accuracy}%                   \n"
                  f"Playcount: {osu_droid_user.total_playcount}              \n"
                  "**".strip()
        )

        await ctx.reply(content=ctx.author.mention, embed=profile_embed)


def setup(bot):
    bot.add_cog(Profile(bot))
