
import datetime
from typing import Union, List, Tuple, Dict
from utils.database import OSU_DROID_TEWI_DB

import aioosuapi
import discord
from discord.ext import commands
from firebase_admin.firestore import firestore

from helpers.osu.beatmaps.droid_oppadc import OsuDroidMap
from helpers.osu.droid.user_data.osu_droid_data import OsuDroidProfile, OsuDroidPlay
from utils.const_responses import USER_NOT_BINDED, USER_NOT_FOUND
from utils.osuapi import OSU_PPY_API


def default_total_dpp(osu_droid_user: OsuDroidProfile) -> Union[str, None]:
    """
    :param osu_droid_user: The user to get it's total_dpp
    :return: A formatted string of the user's total dpp and 'off' if rian8337's droidppboard API is offline
    """

    droid_user_total_dpp: Union[str, None] = "OFF"

    if not osu_droid_user.pp_board_is_offline:
        if osu_droid_user.in_pp_database:
            droid_user_total_dpp = f'{osu_droid_user.total_dpp:.2f}'
        else:
            droid_user_total_dpp = None

    return droid_user_total_dpp


async def default_user_exists_check(ctx: commands.Context, osu_droid_user: OsuDroidProfile) -> bool:
    user_exists: bool = False

    if osu_droid_user.exists:
        user_exists = True
    else:
        await ctx.reply(USER_NOT_FOUND)

    return user_exists


async def default_search_for_uid_in_db_handling(ctx: commands.Context, uid: Union[discord.Member, int] = None):
    """
    :param ctx: The discord Context to the bot reply to.
    :param uid: The uid to search in the database:

    :return: The found binded uid of that certain user if it founds it in the db,
     else it replies with the USER_NOT_BINDED message in the context
    """

    user_to_search_in_db: Union[discord.Member, int] = uid

    if not uid or uid <= 50:
        user_to_search_in_db = ctx.author
        droid_user_id = OSU_DROID_TEWI_DB.get_droid_uid_in_db(user_to_search_in_db).uid

        if not droid_user_id:
            await ctx.reply(USER_NOT_BINDED)
    else:
        if isinstance(user_to_search_in_db, discord.Member):
            response_from_db = OSU_DROID_TEWI_DB.get_droid_uid_in_db(user_to_search_in_db)

            if response_from_db.in_db:
                droid_user_id = response_from_db.uid
            else:
                await ctx.reply(USER_NOT_BINDED)
                droid_user_id = None
        else:
            droid_user_id = uid

    return droid_user_id


def get_approved_str(approved_state_str: str) -> str:
    approved_state: int = int(approved_state_str)
    approved_strs: Tuple[str, ...] = ("In-Progress", "Ranked", "Approved", "Qualified", "Loved", "Graveyard")

    approved_str: str = approved_strs[approved_state]

    return approved_str


def get_default_beatmap_stats_string(
        bumped_osu_play: OsuDroidMap, beatmap_data_from_api: aioosuapi.Beatmap = None
) -> str:
    extra_information: str = ""

    if beatmap_data_from_api:
        approved_str: str = get_approved_str(beatmap_data_from_api.approved)

        extra_information = (
            f"Circles: {bumped_osu_play.amount_circle} - Sliders: {bumped_osu_play.amount_slider}    "
            f"Spinners: {bumped_osu_play.amount_spinner}                                           \n"
            f"{approved_str} | ❤ - {beatmap_data_from_api.favourite_count}                        \n".strip()
        )

    total_length: datetime.timedelta = datetime.timedelta(seconds=bumped_osu_play.total_length)

    default_beatmap_stats_string: str = (
        ">>> "
        "**"
        f"CS: {bumped_osu_play.base_cs:.2f} | OD: {bumped_osu_play.base_od:.2f} | "
        f"AR:  {bumped_osu_play.base_ar:.2f} | HP: {bumped_osu_play.base_hp:.2f} \n"
        f"BPM: {bumped_osu_play.bpm:.2f} | Length: {total_length}                \n"
        f"{extra_information}"
        "**".strip()
    )

    return default_beatmap_stats_string


async def submit_profile_to_db(osu_droid_user_: OsuDroidProfile):
    new_user_plays: Tuple[OsuDroidPlay, ...] = osu_droid_user_.recent_plays

    new_user_plays_info: List[Dict[str]] = []

    for play in new_user_plays:
        play_beatmap = await OSU_PPY_API.get_beatmap(h=play.hash)

        if play_beatmap is None:
            continue

        new_user_play = {
            "title": play.title,
            "score": play.score,
            "accuracy": play.accuracy,
            "misses": play.misses,
            "mods": play.mods,
            "max_combo": play.max_combo,
            "rank_url": play.rank_url,
            "hash": play.hash,
            "date": play.date,
            "beatmap_id": play_beatmap.beatmap_id
        }

        if new_user_play not in new_user_plays_info:
            new_user_plays_info.append(new_user_play)

    old_users_data: dict = OSU_DROID_TEWI_DB.get_users_document()

    old_user_plays: List[dict] = []

    user_id_str: str = f"{osu_droid_user_.uid}"

    if user_id_str in old_users_data:
        old_user_data = old_users_data[user_id_str]
        if "user_plays" in old_user_data:
            # So duplicated plays don't get uploaded to the db
            old_user_plays = list(
                map(lambda a: a if a['hash'] not in list(map(lambda b: b['hash'], new_user_plays_info)) else None,
                    old_user_data['user_plays'])
            )

            # Filters the None values caused by the play being a duplicate
            old_user_plays = list(filter(lambda a: a is not None, old_user_plays))

    user_plays = []

    user_plays.extend(new_user_plays_info)
    user_plays.extend(old_user_plays)

    OSU_DROID_TEWI_DB.update_user_in_users_document(osu_droid_user_, user_plays)
