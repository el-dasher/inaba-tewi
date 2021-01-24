from datetime import datetime
from typing import Tuple, Dict, Any, List
from typing import Union

import discord
from discord.ext import commands
from firebase_admin.firestore import firestore

from helpers.osu.droid.user_data.osu_droid_data import new_osu_droid_profile, OsuDroidProfile, OsuDroidPlay
from utils.database import BINDED_DOCUMENT, USERS_DOCUMENT
from utils.osu_droid_utils import default_total_dpp, default_user_exists_check, default_search_for_uid_in_db_handling
from utils.osuapi import OSU_PPY_API


class UserBind(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    @staticmethod
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

    async def bind_user(
            self, ctx: commands.Context, member_to_bind: discord.Member,
            osu_droid_user_: OsuDroidProfile, force_bind: bool = False
    ) -> discord.Message:
        if await default_user_exists_check(ctx, osu_droid_user_):
            bind_embed: discord.Embed = self.new_bind_embed(member_to_bind, osu_droid_user_, force_bind)

            BINDED_DOCUMENT.set({f"{member_to_bind.id}": osu_droid_user_.uid}, merge=True)
            await self.submit_profile_to_db(osu_droid_user_)

            return await ctx.reply(ctx.author.mention, embed=bind_embed)

    def new_bind_embed(
            self, member_to_bind: discord.member, osu_droid_user_: OsuDroidProfile, force_bind: bool = False
    ) -> discord.Embed:

        bind_header: str = f'Você cadastrou seu usuário... {osu_droid_user_.username}'
        droid_username: str = osu_droid_user_.username

        if force_bind:
            bind_header: str = (
                f'O(a) adm cadastrou o(a) {droid_username} para o(a) {member_to_bind.display_name}'
            )

        bind_embed: discord.Embed = discord.Embed(color=member_to_bind.color, timestamp=datetime.utcnow())
        bind_embed.set_author(name=bind_header, url=osu_droid_user_.main_profile_url)
        bind_embed.set_image(url=osu_droid_user_.avatar)
        bind_embed.set_footer(text=self.bot.user.display_name, icon_url=self.bot.user.avatar_url)

        droid_user_total_dpp: Union[int, None] = default_total_dpp(osu_droid_user_)

        bind_embed.add_field(
            name=f"Informações do(a) {droid_username}",
            value=f">>> "
                  f"**"
                  f"Rank: #{osu_droid_user_.rank_score}           \n"
                  f"Total score: {osu_droid_user_.total_score:,}  \n"
                  f"Total DPP: {droid_user_total_dpp}             \n"
                  f"Overall acc: {osu_droid_user_.accuracy}%      \n"
                  f"Playcount: {osu_droid_user_.play_count}       \n"
                  f"**"
        )

        return bind_embed

    @commands.command(name='userbind', aliases=('bindme', 'droidset', 'bind'))
    async def user_bind(self, ctx: commands.Context, uid: int = None) -> discord.Message:
        if not uid:
            return await ctx.reply('❎ **| Você esqueceu do ID do seu perfil...**')

        osu_droid_user: OsuDroidProfile = await new_osu_droid_profile(uid, needs_player_html=True, needs_pp_data=True)

        return await self.bind_user(ctx=ctx, member_to_bind=ctx.author, osu_droid_user_=osu_droid_user)

    @commands.has_permissions(administrator=True)
    @commands.command(name='forcebind', aliases=('bindhim', 'bindher', 'bindzir'))
    async def force_user_bind(
            self, ctx: commands.Context, member: discord.Member = None, uid: int = None
    ) -> discord.Message:
        if not member:
            return await ctx.reply('❎ **| Ei adm, você esqueceu do usúario que você quer bindar!**')
        if not uid:
            return await ctx.reply('❎ **| Ei adm, você esqueceu do id desse usúario no jogo!**')

        osu_droid_user: OsuDroidProfile = await new_osu_droid_profile(uid, needs_player_html=True, needs_pp_data=True)

        return await self.bind_user(ctx, member_to_bind=member, osu_droid_user_=osu_droid_user, force_bind=True)

    @commands.command(name="submitprofile", aliases=("submit", "submitpf"))
    async def submit_profile(self, ctx: commands.Context):
        droid_user_id: Union[int, None] = await default_search_for_uid_in_db_handling(ctx=ctx, uid=None)

        if not droid_user_id:
            return None

        await self.submit_profile_main(ctx, droid_user_id)

    @commands.has_permissions(administrator=True)
    @commands.command(name='forcesubmit', aliases=('submithim', 'submither', 'submitzir'))
    async def force_submit(self, ctx: commands.Context, member: Union[discord.Member, int] = None):
        if not member:
            return await ctx.reply('❎ **| Ei adm, você esqueceu do usúario que você quer submitar!**')

        droid_user_id = member
        if isinstance(member, discord.Member):
            droid_user_id: Union[int, None] = await default_search_for_uid_in_db_handling(ctx=ctx, uid=member)

        if not droid_user_id:
            return None

        await self.submit_profile_main(ctx, droid_user_id, True)

    async def submit_profile_main(
            self, ctx: commands.Context, uid: Union[int, None] = None, force_submit: bool = False
    ):
        osu_droid_user: OsuDroidProfile = await new_osu_droid_profile(
            uid, needs_player_html=True, needs_pp_data=True
        )

        if await default_user_exists_check(ctx, osu_droid_user):

            await ctx.reply("**Irei tentar sequestrar seus dados!**")
            await self.submit_profile_to_db(osu_droid_user)

            bot_submit_res: str = "✅ **| Os seus dados foram sequestrados por mim com sucesso!**"
            if force_submit:
                bot_submit_res = "✅ **| Os dados dele foram sequestrados por mim com sucesso!**"

            await ctx.reply(bot_submit_res)


def setup(bot):
    bot.add_cog(UserBind(bot))
