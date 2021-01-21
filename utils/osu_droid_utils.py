from typing import Union

from helpers.osu.droid.osu_droid_data import new_osu_droid_profile
import discord
from utils.database import users_collection
from discord.ext import commands
from utils.const_responses import USER_NOT_BINDED, USER_NOT_FOUND


def default_total_dpp(osu_droid_user: new_osu_droid_profile) -> Union[str, None]:
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


async def default_user_exists_check(ctx: commands.Context, osu_droid_user: new_osu_droid_profile) -> bool:
    user_exists: bool = False
    if osu_droid_user.exists:
        user_exists = True
    else:
        await ctx.reply(USER_NOT_FOUND)

    return user_exists


async def default_search_for_user_in_db_handling(ctx: commands.Context, uid: Union[discord.Member, int] = None):
    """
    :param ctx: The discord Context to the bot reply to.
    :param uid: The uid to search in the database:

    :return: The found binded uid of that certain user if it founds it in the db,
     else it replies with the USER_NOT_BINDED message in the context
    """

    user_to_search_in_db: Union[discord.Member, int] = uid

    if not uid:
        user_to_search_in_db = ctx.author
        droid_user_id = (await get_droid_user_in_db(user_to_search_in_db))['uid']
    else:
        if isinstance(user_to_search_in_db, discord.Member):
            response_from_db = (await get_droid_user_in_db(user_to_search_in_db))

            if response_from_db['in_db']:
                droid_user_id = response_from_db['uid']
            else:
                return await ctx.reply(USER_NOT_BINDED)
        else:
            droid_user_id = uid

    return droid_user_id


async def get_droid_user_in_db(discord_user: discord.Member) -> Union[dict[str, int, bool, None]]:
    """
    :param discord_user: A discord user to get from the db
    :return: The user's osu!droid uid
    """

    current_binded_users: dict = users_collection.get().to_dict()
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
