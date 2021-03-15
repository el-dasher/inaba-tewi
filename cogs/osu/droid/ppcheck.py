import asyncio
from typing import Union, List, Tuple

import discord
from discord.ext import commands

from helpers.osu.droid.user_data.osu_droid_data import new_osu_droid_profile, OsuDroidProfile
from utils.bot_defaults import GenericEmbed
from utils.osu_ppy_and_droid_utils import (
    default_search_for_uid_in_db_handling,
    default_user_exists_check,
    default_total_dpp,
)


class PPCheck(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    async def new_ppcheck_embed(
            self, ctx: commands.Context, plays: List[dict], osu_droid_user: OsuDroidProfile, page_number: int = 0
    ) -> discord.Embed:
        ppcheck_embed: discord.Embed = GenericEmbed(self.bot, ctx.author)
        ppcheck_embed.set_author(
            name=f"Top plays do(a) {osu_droid_user.fast_username}", url=osu_droid_user.pp_profile_url
        )

        droid_user_total_dpp: Union[str, None] = default_total_dpp(osu_droid_user)
        ppcheck_embed.add_field(name="Informações", value=f">>> **Total DPP: {droid_user_total_dpp}**", inline=False)

        if page_number < 0:
            page_number = len(osu_droid_user.pp_data['pp']['list']) - abs(page_number)

        for i, play in enumerate(plays):
            play_mods: str = play['mods']
            play_mods_str: str = "+NM"

            if play_mods != "":
                play_mods_str: str = f"+{play_mods}"

            ppcheck_embed.add_field(
                name=f"{page_number + i + 1} - {play['title']} {play_mods_str}",
                value=f">>> ```{play['combo']}x | {play['accuracy']}% | {play['miss']} misses | {play['pp']}pp```",
                inline=False
            )

        return ppcheck_embed

    @commands.command(name="ppcheck")
    async def ppcheck(
            self, ctx: commands.Context, uid: Union[discord.Member, int] = None
    ) -> Union[discord.Message, None]:
        async with ctx.typing():
            droid_user_id: Union[int, None] = await default_search_for_uid_in_db_handling(ctx=ctx, uid=uid)

            if not droid_user_id:
                return None

            osu_droid_user: OsuDroidProfile = await new_osu_droid_profile(droid_user_id, needs_pp_data=True)

            if not await default_user_exists_check(ctx, osu_droid_user):
                return None

            ppcheck_page: int = 0

            pp_plays: List[dict, ...] = osu_droid_user.pp_data['pp']['list']

            current_plays: List[dict, ...] = pp_plays[ppcheck_page:5]
            ppcheck_embed: discord.Embed = await self.new_ppcheck_embed(
                ctx, current_plays, osu_droid_user
            )

        ppcheck_msg: discord.Message = await ctx.reply(ctx.author.mention, embed=ppcheck_embed)

        arrows: Tuple[str, ...] = ("⏮", "⬅", "➡", "⏭")
        for arrow in arrows:
            await ppcheck_msg.add_reaction(arrow)

        while True:
            try:
                valid_reaction: discord.Reaction = (await self.bot.wait_for(
                    "reaction_add",
                    check=lambda r, user: (
                            user == ctx.author and r.emoji in arrows and r.message == ppcheck_msg
                    ), timeout=60
                ))[0]
            except asyncio.TimeoutError:
                return await ppcheck_msg.clear_reactions()
            else:
                decrease_increase_by: int = 5
                page_limit: int = len(pp_plays) - 5

                if valid_reaction.emoji == arrows[0] or ppcheck_page >= page_limit or ppcheck_page <= -page_limit:
                    ppcheck_page = 0
                elif valid_reaction.emoji == arrows[1] or valid_reaction.emoji == arrows[3]:
                    ppcheck_page -= decrease_increase_by
                else:
                    ppcheck_page += decrease_increase_by

                current_plays: List[dict, ...] = pp_plays[ppcheck_page:][:decrease_increase_by]

                ppcheck_embed: discord.Embed = await self.new_ppcheck_embed(
                    ctx, current_plays, osu_droid_user, ppcheck_page
                )

                return await ppcheck_msg.edit(embed=ppcheck_embed)


def setup(bot):
    bot.add_cog(PPCheck(bot))
