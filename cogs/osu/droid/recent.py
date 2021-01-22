from datetime import datetime
from typing import Union

import discord
from aioosuapi import Beatmap
from discord.ext import commands
from oppadc.osumap import OsuStats

from helpers.osu.beatmaps.calculator import new_osu_droid_play_bpp, OsuDroidBeatmapData
from helpers.osu.droid.user_data.osu_droid_data import new_osu_droid_profile, OsuDroidPlay
from utils.osu_droid_utils import default_search_for_uid_in_db_handling, default_user_exists_check
from utils.osuapi import OSU_PPY_API


class Recent(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    @commands.command(name="recent", aliases=["rs", "recentme", "recenthe"])
    async def recent(
            self, ctx: commands.Context, uid: Union[discord.Member, int] = None
    ) -> Union[discord.Message, None]:
        droid_user_id: Union[int, None] = await default_search_for_uid_in_db_handling(ctx=ctx, uid=uid)

        osu_droid_user: new_osu_droid_profile = await new_osu_droid_profile(
            droid_user_id, needs_player_html=True, needs_pp_data=True
        )

        if not await default_user_exists_check(ctx, osu_droid_user):
            return None

        recent_embed: discord.Embed = discord.Embed(color=ctx.author.color, timestamp=datetime.utcnow())

        recent_play: OsuDroidPlay = osu_droid_user.recent_play
        recent_beatmap: Beatmap = (await OSU_PPY_API.get_beatmap(h=recent_play.hash))

        # Play data adjusted to osu!droid values, e.g: nerfs, bpp
        bumped_play: OsuDroidBeatmapData = await new_osu_droid_play_bpp(
            recent_beatmap.beatmap_id, recent_play.mods, recent_play.misses,
            recent_play.accuracy, recent_play.max_combo, adjust_to_droid=True, beatmap_data_from_osu_api=recent_beatmap
        )

        play_stats: OsuStats = bumped_play.getStats(Mods=recent_play.mods)
        play_diff: float = play_stats.total

        recent_embed.set_author(
            url=osu_droid_user.main_profile_url,
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
                  f"Accuracy: {recent_play.accuracy}%                          \n"
                  f"Score: {recent_play.score:,}                               \n"
                  f"Combo: {recent_play.max_combo} / {bumped_play.maxCombo()}  \n"
                  f"Misses: {recent_play.misses}                               \n"
                  "**".strip()
        )

        recent_embed.add_field(
            name=f"Infos do beatmap",
            value=">>> "
                  "**"
                  f"CS/OD: {bumped_play.base_cs} / {bumped_play.base_od}  \n"
                  f"AR/HP: {bumped_play.base_ar} / {bumped_play.base_hp}  \n"
                  f"BPM: {bumped_play.bpm}                                \n"
                  "**".strip()
        )

        await ctx.reply(content=ctx.author.mention, embed=recent_embed)


def setup(bot):
    bot.add_cog(Recent(bot))
