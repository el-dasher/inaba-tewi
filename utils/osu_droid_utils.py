import asyncio
import datetime
from typing import Union, List, Tuple, Dict, Any

import aioosuapi
import discord
from discord.ext import commands
from firebase_admin.firestore import firestore

from utils.osuapi import OSU_PPY_API

from helpers.osu.beatmaps.calculator import BumpedOsuPlay
from helpers.osu.droid.user_data.osu_droid_data import OsuDroidProfile, OsuDroidPlay
from utils.const_responses import USER_NOT_BINDED, USER_NOT_FOUND
from utils.database import BINDED_DOCUMENT, RECENT_CALC_DOCUMENT, USERS_DOCUMENT


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

    if not uid:
        user_to_search_in_db = ctx.author
        droid_user_id = (await get_droid_user_id_in_db(user_to_search_in_db))['uid']
    else:
        if isinstance(user_to_search_in_db, discord.Member):
            response_from_db = (await get_droid_user_id_in_db(user_to_search_in_db))

            if response_from_db['in_db']:
                droid_user_id = response_from_db['uid']
            else:
                await ctx.reply(USER_NOT_BINDED)
                droid_user_id = None
        else:
            droid_user_id = uid

    return droid_user_id


async def get_droid_user_id_in_db(discord_user: discord.Member) -> dict[str, int, bool, None]:
    """
    :param discord_user: A discord user to get from the db
    :return: The user's osu!droid uid
    """

    current_binded_users: dict = BINDED_DOCUMENT.get().to_dict()
    user_in_db: bool = False
    getted_user: Union[int, None] = None

    def create_return_dict(getted_user_: Union[int, None], user_in_db_: bool):
        return {
            'uid': getted_user_,
            'in_db': user_in_db_,
        }

    if str(discord_user.id) in current_binded_users:
        user_in_db = True
        getted_user = current_binded_users[str(discord_user.id)]

    return create_return_dict(getted_user, user_in_db)


def get_default_beatmap_stats_string(
        bumped_osu_play: BumpedOsuPlay, beatmap_data_from_api: aioosuapi.Beatmap = None
) -> str:
    extra_information: str = ""

    if beatmap_data_from_api:
        approved_state: str = beatmap_data_from_api.approved

        approved_str = ""
        if approved_state == "-1":
            approved_str = "Graveyard"
        elif approved_state == "0":
            approved_str = "In-Progress"
        elif approved_state == "1":
            approved_str = "Ranked"
        elif approved_state == "2":
            approved_str = "Approved"
        elif approved_state == "3":
            approved_str = "Qualified"
        elif approved_state == "4":
            approved_str = "Loved"
        extra_information = (
            f"Circles: {bumped_osu_play.amount_circle} - Sliders: {bumped_osu_play.amount_slider}    "
            f"Spinners: {bumped_osu_play.amount_spinner}                                           \n"
            f"{approved_str} | ❤ - {beatmap_data_from_api.favourite_count}                        \n".strip()
        )

    total_length: datetime.timedelta = datetime.timedelta(seconds=bumped_osu_play.total_length)

    default_beatmap_stats_string: str = (
        ">>> "
        "**"
        f"CS: {bumped_osu_play.base_cs:.2f} | OD: {bumped_osu_play.base_od:.2f}    "
        f"AR:  {bumped_osu_play.base_ar:.2f} | HP: {bumped_osu_play.base_hp:.2f} \n"
        f"BPM: {bumped_osu_play.bpm:.2f} | Length: {total_length}                \n"
        f"{extra_information}"
        "**".strip()
    )

    return default_beatmap_stats_string


async def clear_previous_calc_from_db_in_one_minute(ctx: Union[commands.Context, discord.Message]):
    await asyncio.sleep(60)

    RECENT_CALC_DOCUMENT.update({f"{ctx.channel.id}": firestore.DELETE_FIELD})


async def submit_profile_to_db(osu_droid_user_: OsuDroidProfile):
    new_user_plays: Union[Tuple[OsuDroidPlay], List[Dict[str, Any]]] = osu_droid_user_.recent_plays

    new_user_plays_info: List[Dict[str, any]] = []

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

    old_users_data: dict = USERS_DOCUMENT.get().to_dict()

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

    droid_user_uid: str = f"{osu_droid_user_.uid}"

    USERS_DOCUMENT.set({droid_user_uid: {"user_plays": firestore.DELETE_FIELD}}, merge=True)

    USERS_DOCUMENT.set(
        {
            droid_user_uid: {
                "username": osu_droid_user_.username,
                "rank_score": osu_droid_user_.rank_score,
                "total_score": osu_droid_user_.total_score,
                "accuracy": osu_droid_user_.accuracy,
                "play_count": osu_droid_user_.play_count,
                "avatar": osu_droid_user_.avatar,
                "total_dpp": osu_droid_user_.total_dpp,
                "user_plays": user_plays
            }
        }, merge=True
    )
