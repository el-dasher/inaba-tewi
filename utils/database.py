import discord
from discord.ext import commands
from firebase_admin.firestore import firestore
from helpers.osu.droid.user_data.osu_droid_data import OsuDroidProfile
from aioosuapi import Beatmap
from typing import Union
import asyncio
from typing import Dict

from config.firebase.database import TEWI_DB as TEWI_DB_BASE


class UidInDBResponse:
    def __init__(self, uid: Union[int, None], in_db: bool):
        self.uid: Union[int, None] = uid
        self.in_db: bool = in_db


class MainTewiDB:
    def __init__(self):
        # noinspection PyTypeChecker
        self.MAIN_COLLECTION: firestore.CollectionReference = TEWI_DB_BASE.collection("MAIN")
        self.CUSTOM_PREFIXES_DOCUMENT: firestore.DocumentReference = self.MAIN_COLLECTION.document("CUSTOM_PREFIXES")

    def get_guild_custom_prefix(self, guild: discord.Guild) -> Union[str, None]:
        curr_custom_prefixes: Dict[str, str] = self.CUSTOM_PREFIXES_DOCUMENT.get().to_dict()

        try:
            guild_custom_prefix: str = curr_custom_prefixes[str(guild.id)]
        except KeyError:
            return None
        else:
            return guild_custom_prefix

    def post_new_custom_prefix(self, guild: discord.Guild, custom_prefix: str):
        self.CUSTOM_PREFIXES_DOCUMENT.set({str(guild.id): custom_prefix}, merge=True)


class OsuDroidTewiDB:
    def __init__(self):
        # noinspection PyTypeChecker
        self.OSU_DROID_COLLECTION: firestore.CollectionReference = TEWI_DB_BASE.collection('OSU!DROID')
        self.BINDED_DOCUMENT: firestore.DocumentReference = self.OSU_DROID_COLLECTION.document('BINDED_USERS')
        self.USERS_DOCUMENT: firestore.DocumentReference = self.OSU_DROID_COLLECTION.document('USERS_DATA')
        self.RECENT_CALC_DOCUMENT: firestore.DocumentReference = self.OSU_DROID_COLLECTION.document("RECENT_CALC")
        self.BR_UIDS_DOCUMENT: firestore.DocumentReference = self.OSU_DROID_COLLECTION.document("BR_UIDS")
        self.TOP_DROID_PLAYERS_DOCUMENT: firestore.DocumentReference = self.OSU_DROID_COLLECTION.document("TOP_PLAYERS")

    async def clear_previous_calc_from_db(self, ctx: Union[commands.Context, discord.Message], timer: int = None):
        if timer:
            await asyncio.sleep(timer)

        self.RECENT_CALC_DOCUMENT.update({str(ctx.channel.id): firestore.DELETE_FIELD})

    def update_user_in_users_document(self, osu_droid_user: OsuDroidProfile, user_plays: list):
        droid_user_uid: str = str(osu_droid_user.uid)
        self.USERS_DOCUMENT.set({droid_user_uid: {"user_plays": firestore.DELETE_FIELD}}, merge=True)

        self.USERS_DOCUMENT.set(
            {
                droid_user_uid: {
                    "username": osu_droid_user.username,
                    "rank_score": osu_droid_user.rank_score,
                    "total_score": osu_droid_user.total_score,
                    "accuracy": osu_droid_user.accuracy,
                    "play_count": osu_droid_user.play_count,
                    "avatar": osu_droid_user.avatar,
                    "total_dpp": osu_droid_user.total_dpp,
                    "user_plays": user_plays
                }
            }, merge=True
        )

    def get_users_document(self):
        return self.USERS_DOCUMENT.get().to_dict()

    def bind_user(self, member_to_bind: discord.Member, osu_droid_user: OsuDroidProfile):
        self.BINDED_DOCUMENT.set({str(member_to_bind.id): osu_droid_user.uid}, merge=True)

    def get_binded_users(self):
        return self.BINDED_DOCUMENT.get().to_dict()

    def get_br_uids(self):
        return self.BR_UIDS_DOCUMENT.get().to_dict()['0']

    def set_new_br_droid_top_players(self, new_data: dict):
        self.TOP_DROID_PLAYERS_DOCUMENT.set({'user': new_data})

    async def set_recent_play(self, ctx: commands.Context, recent_beatmap: Beatmap):
        if recent_beatmap:
            self.RECENT_CALC_DOCUMENT.set({str(ctx.channel.id): recent_beatmap.beatmap_id}, merge=True)

    def get_recent_plays(self):
        return self.RECENT_CALC_DOCUMENT.get().to_dict()

    def get_droid_uid_in_db(self, discord_user: discord.Member) -> UidInDBResponse:
        """
        :param discord_user: A discord user to get from the db
        :return: The user's osu!droid uid
        """

        current_binded_users: dict = self.get_binded_users()
        user_in_db: bool = False
        got_user: Union[int, None] = None

        def create_response(got_user_: Union[int, None], user_in_db_: bool):
            return UidInDBResponse(got_user_, user_in_db_)

        if str(discord_user.id) in current_binded_users:
            user_in_db: bool = True
            got_user: int = current_binded_users[str(discord_user.id)]

        return create_response(got_user, user_in_db)


OSU_DROID_TEWI_DB: OsuDroidTewiDB = OsuDroidTewiDB()
MAIN_TEWI_DB: MainTewiDB = MainTewiDB()
