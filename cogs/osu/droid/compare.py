from typing import Union, List

import aioosuapi
import discord
from discord.ext import commands
from oppadc.osustats import OsuStats

from helpers.osu.beatmaps.droid_oppadc import new_osu_droid_map, OsuDroidMap
from utils.const_responses import BEATMAP_NOT_BEING_TALKED
from utils.database import TEWI_DB
from utils.osu_ppy_and_droid_utils import (
    default_search_for_uid_in_db_handling,
    get_default_beatmap_stats_string,
)
from helpers.osu.droid.user_data.osu_droid_data import OsuDroidProfile, OsuDroidProfileFromParams

from datetime import datetime
from utils.osuapi import OSU_PPY_API


class DatabaseOsuDroidPlay:
    def __init__(
            self, beatmap_id: int, title: str, mods: str, accuracy: float,
            max_combo: int, misses: int, rank_url: str, date: datetime, hash_: str, score: int
    ):
        self.beatmap_id: int = beatmap_id
        self.title: str = title
        self.mods: str = mods
        self.accuracy: float = accuracy
        self.max_combo: int = max_combo
        self.misses: int = misses
        self.rank_url: str = rank_url
        self.date: datetime = date
        self.hash: str = hash_
        self.score: int = score


class Compare(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    @commands.command(name="compare", aliases=["c"])
    async def compare(self, ctx: commands.Context) -> Union[discord.Message, None]:
        async with ctx.typing():
            current_recent_plays: dict = TEWI_DB.get_recent_plays()
            current_users: dict = TEWI_DB.get_users_document()

            try:
                play_to_compare_to = current_recent_plays[str(ctx.channel.id)]
            except KeyError:
                return await ctx.reply(BEATMAP_NOT_BEING_TALKED)

            droid_user_id: Union[str,  None] = await default_search_for_uid_in_db_handling(ctx=ctx, uid=ctx.author)

            if not droid_user_id:
                return None

            droid_user_id = str(droid_user_id)

            if droid_user_id in current_users:
                osu_droid_user_raw: dict = current_users[str(droid_user_id)]
            else:
                return await ctx.reply(f"❎ **| Você não submitou suas plays a base de dados, use `{ctx.prefix}submit`")

            osu_droid_user: OsuDroidProfile = OsuDroidProfileFromParams(
                username=osu_droid_user_raw['username'], avatar=osu_droid_user_raw['avatar']
            )

            user_plays: List[dict, ...] = osu_droid_user_raw['user_plays']

            found_plays: filter = filter(lambda a: a['beatmap_id'] == play_to_compare_to, user_plays)

            comparison_play_raw = next(found_plays, None)

            if comparison_play_raw:
                comparison_play: DatabaseOsuDroidPlay = DatabaseOsuDroidPlay(
                    comparison_play_raw['beatmap_id'], comparison_play_raw['title'], comparison_play_raw['mods'],
                    comparison_play_raw['accuracy'], comparison_play_raw['max_combo'], comparison_play_raw['misses'],
                    comparison_play_raw['rank_url'], comparison_play_raw['date'], comparison_play_raw['hash'],
                    comparison_play_raw['score']
                )
            else:
                return await ctx.reply(
                    "❎ **| Eu não consegui achar a sua play nesse mapa na base de dados,"
                    " talvez seja por que o mapa não está submitado no site do ppy?**")

            beatmap_data_from_api: aioosuapi.Beatmap = await OSU_PPY_API.get_beatmap(h=comparison_play.hash)

            bumped_play: OsuDroidMap = await new_osu_droid_map(
                comparison_play.beatmap_id, comparison_play.mods, comparison_play.misses,
                comparison_play.accuracy, comparison_play.max_combo,
                beatmap_data_from_osu_api=beatmap_data_from_api
            )

            droid_stats: OsuStats = bumped_play.getStats(Mods=comparison_play.mods)

            droid_diff: float = droid_stats.total

            compare_embed: discord.Embed = discord.Embed(timestamp=comparison_play.date, color=ctx.author.color)

            compare_embed.set_author(
                url=beatmap_data_from_api.url,
                name=f"{comparison_play.title} +{comparison_play.mods} - {droid_diff:.2f}★)",
                icon_url=osu_droid_user.avatar
            )

            compare_embed.set_thumbnail(url=beatmap_data_from_api.thumbnail)
            compare_embed.set_footer(text="\u200b", icon_url=comparison_play.rank_url)

            compare_embed.add_field(
                name=f"Dados da play do(a) {osu_droid_user.username}",
                value=">>> "
                      "**"
                      f"BR_DPP: {bumped_play.raw_pp:.2f} \n"
                      f"Accuracy: {comparison_play.accuracy:.2f}%\n"
                      f"Score: {comparison_play.score:,}\n"
                      f"Combo: {comparison_play.max_combo} / {bumped_play.maxCombo()}\n"
                      f"Misses: {comparison_play.misses}\n"
                      "**"
            )

            compare_embed.add_field(
                name=f"Infos do beatmap", value=get_default_beatmap_stats_string(bumped_play), inline=False
            )

        await ctx.reply(content=ctx.author.mention, embed=compare_embed)
        await TEWI_DB.clear_previous_calc_from_db(ctx, 240)


def setup(bot):
    bot.add_cog(Compare(bot))
