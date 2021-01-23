from datetime import datetime
from typing import Union

import discord
from aioosuapi import Beatmap
from discord.ext import commands
from oppadc.osumap import OsuStats

from helpers.osu.beatmaps.calculator import new_bumped_osu_play, BumpedOsuPlay
from helpers.osu.droid.user_data.osu_droid_data import new_osu_droid_profile, OsuDroidPlay
from utils.database import RECENT_CALC_DOCUMENT
from utils.osu_droid_utils import (
    default_search_for_uid_in_db_handling,
    default_user_exists_check,
    get_default_beatmap_stats_string,
    clear_previous_calc_from_db_in_30_seconds
)
from utils.osuapi import OSU_PPY_API


class Recent(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    @commands.command(name="recent", aliases=["rs", "recentme", "recenthe"])
    async def recent(
            self, ctx: commands.Context, uid: Union[discord.Member, int] = None
    ) -> None:
        droid_user_id: Union[int, None] = await default_search_for_uid_in_db_handling(ctx=ctx, uid=uid)

        osu_droid_user: new_osu_droid_profile = await new_osu_droid_profile(
            droid_user_id, needs_player_html=True, needs_pp_data=True
        )

        if not droid_user_id:
            return None
        if not await default_user_exists_check(ctx, osu_droid_user):
            return None

        recent_embed: discord.Embed = discord.Embed(color=ctx.author.color, timestamp=datetime.utcnow())

        recent_play: OsuDroidPlay = osu_droid_user.recent_play
        recent_beatmap: Beatmap = (await OSU_PPY_API.get_beatmap(h=recent_play.hash))

        # Play data adjusted to osu!droid values, e.g: nerfs, bpp
        bumped_play: BumpedOsuPlay = await new_bumped_osu_play(
            recent_beatmap.beatmap_id, recent_play.mods, recent_play.misses,
            recent_play.accuracy, recent_play.max_combo, adjust_to_droid=True, beatmap_data_from_osu_api=recent_beatmap
        )

        play_stats: OsuStats = bumped_play.getStats(Mods=recent_play.mods)
        play_diff: float = play_stats.total

        recent_embed.set_author(
            url=recent_beatmap.url,
            name=f"{recent_play.title} {recent_play.mods} - {play_diff:.2f}★",
            icon_url=osu_droid_user.avatar
        )

        recent_embed.set_thumbnail(url=recent_beatmap.thumbnail)
        recent_embed.set_footer(text="\u200b", icon_url=recent_play.rank_url)

        recent_embed.add_field(
            name=f"Dados da play do(a) {osu_droid_user.username}",
            value=">>> "
                  "**"
                  f"BR_DPP: {bumped_play.raw_pp:.2f}                           \n"
                  f"Accuracy: {recent_play.accuracy:.2f}%                      \n"
                  f"Score: {recent_play.score:,}                               \n"
                  f"Combo: {recent_play.max_combo} / {bumped_play.maxCombo()}  \n"
                  f"Misses: {recent_play.misses}                               \n"
                  "**".strip()
        )

        recent_embed.add_field(
            name=f"Infos do beatmap", value=get_default_beatmap_stats_string(bumped_play), inline=False
        )

        RECENT_CALC_DOCUMENT.set({f"{ctx.channel.id}": recent_beatmap.beatmap_id}, merge=True)

        await ctx.reply(content=ctx.author.mention, embed=recent_embed)

        await clear_previous_calc_from_db_in_30_seconds(ctx.channel.id)


def setup(bot):
    bot.add_cog(Recent(bot))
