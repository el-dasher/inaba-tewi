from typing import Union

import discord
import oppadc
from aioosuapi import Beatmap
from discord.ext import commands
from oppadc.osumap import OsuStats
from utils.database import OSU_DROID_TEWI_DB

from helpers.osu.beatmaps.droid_oppadc import new_osu_droid_map, OsuDroidMap
from helpers.osu.droid.user_data.osu_droid_data import new_osu_droid_profile, OsuDroidPlay, OsuDroidProfile

from utils.osu_ppy_and_droid_utils import (
    default_search_for_uid_in_db_handling,
    default_user_exists_check,
    get_default_beatmap_stats_string,
)

from utils.osuapi import OSU_PPY_API


class Recent(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    @commands.command(name="recent", aliases=["rs", "recentme", "recenthe"])
    async def recent(
            self, ctx: commands.Context, uid_or_index: Union[discord.Member, int] = None, optional_index: int = None
    ) -> None:
        async with ctx.typing():
            index = 0
            droid_user_id: Union[int, None] = await default_search_for_uid_in_db_handling(ctx=ctx, uid=uid_or_index)
            osu_droid_user: OsuDroidProfile = await new_osu_droid_profile(droid_user_id, needs_player_html=True)

            if not droid_user_id or not await default_user_exists_check(ctx, osu_droid_user):
                return None

            if optional_index:
                index = optional_index
            elif uid_or_index is not None and type(uid_or_index) == int and uid_or_index <= 50:
                index = uid_or_index - 1

            recent_play: OsuDroidPlay = osu_droid_user.recent_plays[index]
            recent_beatmap: Beatmap = (await OSU_PPY_API.get_beatmap(h=recent_play.hash))
            recent_embed: discord.Embed = discord.Embed(color=ctx.author.color, timestamp=recent_play.date)

            bumped_play: Union[OsuDroidMap, None] = None
            ppv2_play: Union[oppadc.OsuMap, None] = None

            bumped_play_max_combo_str: str = ""

            try:
                bumped_play = await new_osu_droid_map(
                    recent_beatmap.beatmap_id, recent_play.mods, recent_play.misses,
                    recent_play.accuracy, recent_play.max_combo,
                    beatmap_data_from_osu_api=recent_beatmap
                )
                ppv2_play = bumped_play.original
            except AttributeError:
                play_diff: Union[float, None] = None
            else:
                bumped_play_max_combo_str = f"/ {bumped_play.maxCombo()}"
                play_stats: OsuStats = ppv2_play.getStats(Mods=recent_play.mods)
                droid_play_stats: OsuStats = bumped_play.getStats(Mods=recent_play.mods)

                droid_diff: float = droid_play_stats.total
                play_diff: float = play_stats.total

                # noinspection PyTypeChecker
                ppv2_pp = ppv2_play.getPP(
                    Mods=recent_play.mods, accuracy=recent_play.accuracy,
                    misses=recent_play.misses, combo=recent_play.max_combo, recalculate=True
                )

            diff_str: str = ""
            if play_diff and droid_play_stats:
                play_diff_str = f"{play_diff:.2f}★"
                droid_diff_str = f"{droid_diff:.2f}★"

                diff_str = f"- {droid_diff_str} -({play_diff_str})"

            recent_beatmap_thumbnail: str = ""
            recent_beatmap_url: str = ""
            if recent_beatmap:
                recent_beatmap_thumbnail = recent_beatmap.thumbnail
                recent_beatmap_url = recent_beatmap.url

            recent_embed.set_author(
                url=recent_beatmap_url,
                name=f"{recent_play.title} +{recent_play.mods} {diff_str}",
                icon_url=osu_droid_user.avatar
            )

            recent_embed.set_thumbnail(url=recent_beatmap_thumbnail)
            recent_embed.set_footer(text="\u200b", icon_url=recent_play.rank_url)

            info_beatmap_str: str = "> ❎ **| Não encontrei o beatmap no site do ppy...**"
            pp_info_str: str = "UNKNOWN"
            if bumped_play and ppv2_play:
                br_dpp_str = f"BR_DPP: {bumped_play.raw_pp:.2f}"
                ppv2_str = f"PPV2: {ppv2_pp.total_pp:.2f}"

                info_beatmap_str = get_default_beatmap_stats_string(bumped_play)
                pp_info_str = f"{br_dpp_str} | {ppv2_str}"

            recent_embed.add_field(
                name=f"Dados da play do(a) {osu_droid_user.username}",
                value=">>> "
                      "**"
                      f"{pp_info_str}                                              \n" 
                      f"Accuracy: {recent_play.accuracy:.2f}%                      \n"
                      f"Score: {recent_play.score:,}                               \n"
                      f"Combo: {recent_play.max_combo} {bumped_play_max_combo_str} \n"
                      f"Misses: {recent_play.misses}                                 "
                      "**".strip()
            )

            recent_embed.add_field(name=f"Infos do beatmap", value=info_beatmap_str, inline=False)

        await ctx.reply(content=ctx.author.mention, embed=recent_embed)
        await OSU_DROID_TEWI_DB.set_recent_play(ctx, recent_beatmap)


def setup(bot):
    bot.add_cog(Recent(bot))
