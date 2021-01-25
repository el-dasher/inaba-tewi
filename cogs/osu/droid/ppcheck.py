import discord
from discord.ext import commands
from typing import Union, List
from utils.osu_droid_utils import (
    default_search_for_uid_in_db_handling,
    default_user_exists_check,
    default_total_dpp,
    OsuDroidProfile
)
from utils.bot_defaults import setup_generic_embed
from helpers.osu.droid.user_data.osu_droid_data import new_osu_droid_profile
import asyncio


class PPCheck(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    async def new_ppcheck_embed(
            self, ctx: commands.Context, plays: List[dict], osu_droid_user: OsuDroidProfile
    ) -> discord.Embed:
        ppcheck_embed: discord.Embed = setup_generic_embed(self.bot, ctx.author)
        ppcheck_embed.set_author(name=f"Top plays do(a) {osu_droid_user.username}", url=osu_droid_user.pp_profile_url)

        droid_user_total_dpp: Union[str, None] = default_total_dpp(osu_droid_user)
        ppcheck_embed.add_field(name="Informações", value=f">>> **Total DPP: {droid_user_total_dpp}**", inline=False)

        for i, play in enumerate(plays):
            play_mods: str = play['mods']
            play_mods_str: str = "+NM"

            if play_mods != "":
                play_mods_str: str = f"+{play_mods}"

            ppcheck_embed.add_field(
                name=f"{i+1} - {play['title']} {play_mods_str}",
                value=f">>> ```{play['combo']}x | {play['accuracy']}% | {play['miss']} misses | {play['pp']}pp```",
                inline=False
            )

        return ppcheck_embed

    @commands.command(name="ppcheck")
    async def ppcheck(
            self, ctx: commands.Context, uid: Union[discord.Member, int] = None
    ) -> Union[discord.Message, None]:
        droid_user_id: Union[int, None] = await default_search_for_uid_in_db_handling(ctx=ctx, uid=uid)

        if not droid_user_id:
            return None

        osu_droid_user: OsuDroidProfile = await new_osu_droid_profile(
            droid_user_id, needs_player_html=True, needs_pp_data=True
        )

        if not await default_user_exists_check(ctx, osu_droid_user):
            return None

        ppcheck_page: int = 0

        pp_plays: List[dict] = osu_droid_user.pp_data['pp']['list']

        current_plays: List[dict] = pp_plays[ppcheck_page:5]
        ppcheck_embed: discord.Embed = await self.new_ppcheck_embed(
                    ctx, current_plays, osu_droid_user
        )

        ppcheck_msg: discord.Message = await ctx.reply(ctx.author.mention, embed=ppcheck_embed)

        await ppcheck_msg.add_reaction("⬅")
        await ppcheck_msg.add_reaction("➡")

        while True:
            try:
                await self.bot.wait_for(
                    "reaction_add",
                    check=lambda r, user: (
                            user == ctx.author and str(r.emoji) in ("⬅", "➡") and r.message == ppcheck_msg
                    ), timeout=60
                )
            except asyncio.TimeoutError:
                await ppcheck_msg.clear_reactions()
                return None
            else:
                # Changes the page of the ppcheck based if it's the first reaction or other
                if ppcheck_page == 0:
                    ppcheck_page += 6
                else:
                    ppcheck_page += 5

                current_plays: List[dict] = pp_plays[ppcheck_page::5]
                ppcheck_embed: discord.Embed = await self.new_ppcheck_embed(
                    ctx, current_plays, osu_droid_user
                )

                await ppcheck_msg.edit(embed=ppcheck_embed)


def setup(bot):
    bot.add_cog(PPCheck(bot))
