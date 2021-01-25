from typing import Union, List

import aioosuapi
import discord
from discord.ext import commands
from oppadc.osustats import OsuStats

from helpers.osu.beatmaps.calculator import new_bumped_osu_play, BumpedOsuPlay
from utils.const_responses import BEATMAP_NOT_BEING_TALKED
from utils.database import RECENT_CALC_DOCUMENT, USERS_DOCUMENT
from utils.osu_droid_utils import (
    default_search_for_uid_in_db_handling,
    get_default_beatmap_stats_string,
    clear_previous_calc_from_db_in_one_minute
)
from utils.osuapi import OSU_PPY_API



class Compare(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    @commands.command(name="compare", aliases=["c", "comparison"])
    async def compare(self, ctx: commands.Context):
        current_recent_play: dict = RECENT_CALC_DOCUMENT.get().to_dict()
        current_users: dict = USERS_DOCUMENT.get().to_dict()

        if f"{ctx.channel.id}" in current_recent_play:
            play_to_compare_to = current_recent_play[f"{ctx.channel.id}"]
        else:
            return await ctx.reply(BEATMAP_NOT_BEING_TALKED)

        droid_user_id: Union[int, str, None] = await default_search_for_uid_in_db_handling(ctx=ctx, uid=ctx.author)

        if not droid_user_id:
            return None

        droid_user_id = f"{droid_user_id}"
        if droid_user_id in current_users:
            osu_droid_user: dict = current_users[f"{droid_user_id}"]
        else:
            return await ctx.reply(f"❎ **| Você não submitou suas plays a base de dados, use `{ctx.prefix}submit`")

        user_plays: List[dict] = osu_droid_user['user_plays']

        try:
            play_info: Union[tuple, dict] = tuple(
                filter(lambda a: a['beatmap_id'] == play_to_compare_to, user_plays)
            )[0]
        except TypeError:
            return await ctx.reply(
                "❎ **| Eu não consegui achar a sua play nesse mapa na base de dados,"
                " talvez seja por que o mapa não está submitado no site do peppy?**")

        beatmap_data_from_api: aioosuapi.Beatmap = await OSU_PPY_API.get_beatmap(h=play_info['hash'])
        bumped_play: BumpedOsuPlay = await new_bumped_osu_play(
            play_info['beatmap_id'], play_info['mods'], play_info['misses'],
            play_info['accuracy'], play_info['max_combo'], 1.00, True, beatmap_data_from_api
        )

        play_stats: OsuStats = bumped_play.getStats(Mods=play_info['mods'])
        play_diff: float = play_stats.total

        compare_embed: discord.Embed = discord.Embed(timestamp=play_info['date'])

        compare_embed.set_author(
            url=beatmap_data_from_api.url,
            name=f"{beatmap_data_from_api.title} {play_info['mods']} - {play_diff:.2f}★",
            icon_url=osu_droid_user['avatar']
        )

        compare_embed.set_thumbnail(url=beatmap_data_from_api.thumbnail)
        compare_embed.set_footer(text="\u200b", icon_url=play_info['rank_url'], )

        compare_embed.add_field(
            name=f"Dados da play do(a) {osu_droid_user['username']}",
            value=">>> "
                  "**"
                  f"BR_DPP: {bumped_play.raw_pp:.2f}                           \n"
                  f"Accuracy: {play_info['accuracy']:.2f}%                      \n"
                  f"Score: {play_info['score']:,}                               \n"
                  f"Combo: {play_info['max_combo']} / {bumped_play.maxCombo()}  \n"
                  f"Misses: {play_info['misses']}                               \n"
                  "**".strip()
        )

        compare_embed.add_field(
            name=f"Infos do beatmap", value=get_default_beatmap_stats_string(bumped_play), inline=False
        )

        await ctx.reply(content=ctx.author.mention, embed=compare_embed)

        await clear_previous_calc_from_db_in_one_minute(ctx)


def setup(bot):
    bot.add_cog(Compare(bot))
