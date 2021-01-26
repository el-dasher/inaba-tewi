"""
Literally a copy of rian8337's version but python tho
"""

import discord
from discord.ext import commands
import aiohttp
from typing import List, Tuple
from utils.bot_defaults import setup_generic_embed
from utils.osu_ppy_and_droid_utils import get_approved_str
import asyncio
from datetime import datetime


class BeatmapSearch(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot
        self.decrease_increace_by: int = 5

    async def new_maps_embed(
            self, ctx: commands.Context, found_maps: List[dict], page_number: int = 0, show_downloads: bool = False
    ) -> discord.Embed:
        maps_embed: discord.Embed = setup_generic_embed(self.bot, ctx.author)

        if page_number < 0:
            page_number = len(found_maps) - abs(page_number)

        current_maps: List[dict, ...] = found_maps[page_number:][:self.decrease_increace_by]

        for i, beatmap in enumerate(current_maps):
            download_str: str = ""
            approved_str: str = f"**{get_approved_str(beatmap['approved'])}**"
            last_update: datetime = datetime.fromtimestamp(beatmap['lastupdate'])

            if show_downloads:
                download_str: str = f"**Download**: [osu - download](http://osu.ppy.sh/beatmapsets/{beatmap['sid']})\n"

            maps_embed.add_field(
                name=f"{page_number + i + 1} - {beatmap['artist']} - {beatmap['title']} ({beatmap['creator']})",
                value=f">>> {download_str}**Last update**: {last_update} | {approved_str} | "
                      f"**❤ {beatmap['favourite_count']:,} - ➡ {beatmap['play_count']:,}**",
                inline=False
            )

        return maps_embed

    @commands.command(name="beatmapsearch", aliases=("mapsearch", ))
    async def mapsearch(self, ctx: commands.Context, *query):
        if not query:
            return await ctx.reply("❎ **| Você esqueceu da sua query para eu pesquisar...**")

        query: str = " ".join(query)
        sayobot_url: str = f"https://api.sayobot.cn/beatmaplist?&T=4&L=100&M=1&K={query}"

        async with aiohttp.ClientSession() as session:
            async with session.get(sayobot_url) as res:
                found_maps: List[dict, ...] = (await res.json(content_type=None))['data']

        page_number: int = 0

        maps_embed: discord.Embed = await self.new_maps_embed(ctx, found_maps, page_number)

        maps_msg: discord.Message = await ctx.reply(ctx.author.mention, embed=maps_embed)

        arrows: Tuple[str, ...] = ("⏮", "⬅", "➡", "⏭", "📥")
        for arrow in arrows:
            await maps_msg.add_reaction(arrow)

        while True:
            try:
                valid_reaction: discord.Reaction = (await self.bot.wait_for(
                    "reaction_add",
                    check=lambda r, user: (
                            user == ctx.author and r.emoji in arrows and r.message == maps_msg
                    ), timeout=60
                ))[0]
            except asyncio.TimeoutError:
                await maps_msg.clear_reactions()
                return None
            else:
                page_limit: int = len(found_maps) - 5
                show_downloads: bool = False

                if valid_reaction.emoji == arrows[0] or page_number >= page_limit or page_number <= -page_limit:
                    page_number = 0
                elif valid_reaction.emoji == arrows[1]:
                    page_number -= self.decrease_increace_by
                elif valid_reaction.emoji == arrows[2]:
                    page_number += self.decrease_increace_by
                elif valid_reaction.emoji == arrows[3]:
                    page_number = -self.decrease_increace_by
                else:
                    show_downloads = True

                maps_embed: discord.Embed = await self.new_maps_embed(ctx, found_maps, page_number, show_downloads)

                await maps_msg.edit(embed=maps_embed)


def setup(bot):
    bot.add_cog(BeatmapSearch(bot))
