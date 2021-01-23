from datetime import datetime
from typing import Union
from typing import Tuple, Dict, Any

import discord
from discord.ext import commands

from helpers.osu.droid.user_data.osu_droid_data import new_osu_droid_profile, OsuDroidProfile, OsuDroidPlay
from utils.database import BINDED_DOCUMENT, USERS_DOCUMENT
from utils.osu_droid_utils import default_total_dpp, default_user_exists_check, default_search_for_uid_in_db_handling


class UserBind(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    @staticmethod
    def submit_profile_to_db(osu_droid_user_: OsuDroidProfile):
        user_plays: Union[Tuple[OsuDroidPlay], Tuple[Dict[str, Any]]] = osu_droid_user_.recent_plays

        user_plays = tuple(map(
            lambda a: {
                "title": a.title,
                "score": a.score,
                "accuracy": a.accuracy,
                "misses": a.misses,
                "mods": a.mods,
                "max_combo": a.max_combo,
                "hash": a.hash
            },
            user_plays
        ))

        USERS_DOCUMENT.set(
            {
                f"{osu_droid_user_.uid}": {
                    "username": osu_droid_user_.username,
                    "rank_score": osu_droid_user_.rank_score,
                    "total_score": osu_droid_user_.total_score,
                    "accuracy": osu_droid_user_.accuracy,
                    "play_count": osu_droid_user_.play_count,
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
            self.submit_profile_to_db(osu_droid_user_)

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

        osu_droid_user: OsuDroidProfile = await new_osu_droid_profile(
            droid_user_id, needs_player_html=True, needs_pp_data=True
        )

        self.submit_profile_to_db(osu_droid_user)


def setup(bot):
    bot.add_cog(UserBind(bot))
