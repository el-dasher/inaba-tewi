import discord
from discord.ext import commands

from helpers.osu.beatmaps.calculator import new_bumped_osu_play, BumpedOsuPlay
from utils.osu_droid_utils import get_default_beatmap_stats_string
from utils.bot_defaults import setup_generic_embed
from utils.osuapi import OSU_PPY_API
import aioosuapi

from typing import Tuple, Union, List


class MapCalc(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    async def calculate_main(
            self, ctx: Union[discord.Message, commands.Context],
            *params: Union[Tuple[Union[int, str]], List[Union[int, str]]],
            reply_errors: bool = True
    ):

        params = params[0]
        beatmap_id = params[0]

        # This means that the user probably provided a beatmap url over a beatmap_id
        if type(params[0]) == str:
            beatmap_id = params[0].split("/")[-1]

        # Excludes the beatmap_id or url
        params = params[1:]

        mods: str = "NM"
        misses: int = 0
        accuracy: float = 100.00
        combo: Union[int, None] = None
        speed_multiplier: float = 1.00
        adjust_to_droid = True
        beatmap_data_from_osu_api: aioosuapi.Beatmap = await OSU_PPY_API.get_beatmap(b=beatmap_id)

        if not beatmap_data_from_osu_api:
            if reply_errors:
                await ctx.reply("❎ **| Não foi possivel encontrar um beatmap com o id que você me forneceu!**")

            return None

        # Filtering the user input to get the correct paramters
        for param in params:
            if param.startswith("+"):
                mods = param.replace("+", "")
            else:
                param = param[:-1]

                if param.isnumeric():
                    if param.endswith("m"):
                        misses = int(param)
                    elif param.endswith("x"):
                        combo = int(param)
                else:
                    try:
                        if param.endswith("%"):
                            accuracy = float(param)
                        elif param.endswith("s"):
                            speed_multiplier = float(param)
                    except ValueError:
                        continue

        calc_beatmap: BumpedOsuPlay = await new_bumped_osu_play(
            beatmap_id, mods, misses, accuracy, combo, speed_multiplier, adjust_to_droid, beatmap_data_from_osu_api
        )
        max_values_with_calc_acc: BumpedOsuPlay = await new_bumped_osu_play(
            beatmap_id, mods, 0, accuracy, calc_beatmap.maxCombo(),
            speed_multiplier, adjust_to_droid, beatmap_data_from_osu_api
        )
        ppv2_calc: BumpedOsuPlay = await new_bumped_osu_play(
            beatmap_id, mods, 0, accuracy, calc_beatmap.maxCombo(),
            speed_multiplier, False, beatmap_data_from_osu_api
        )

        calc_embed = setup_generic_embed(self.bot, ctx.author)

        calc_embed.set_author(
            name=f"{calc_beatmap.title} +{mods} {misses}m {float(accuracy):.2f}% {speed_multiplier}x",
            url=beatmap_data_from_osu_api.url
        )

        calc_embed.set_thumbnail(url=beatmap_data_from_osu_api.thumbnail)

        raw_pp_str: str = (
            f"PP RAW: {calc_beatmap.raw_pp:.2f} -({max_values_with_calc_acc.raw_pp:.2f}) | {ppv2_calc.raw_pp:.2f}\n"
        )

        calc_embed.add_field(
            name="---Performance",
            value=">>> **"
                  "BR_DPP | PPV2                                                     \n"
                  f"{raw_pp_str}"
                  f"Aim PP: {calc_beatmap.aim_pp:.2f} | {ppv2_calc.aim_pp:.2f}       \n"
                  f"Speed PP: {calc_beatmap.speed_pp:.2f} | {ppv2_calc.speed_pp:.2f} \n"
                  f"Acc PP: {calc_beatmap.acc_pp:.2f} | {ppv2_calc.acc_pp:.2f}       \n"
                  f"**".strip()
        )

        calc_embed.add_field(
            name="---Beatmap",
            value=get_default_beatmap_stats_string(calc_beatmap, beatmap_data_from_osu_api),
            inline=False
        )

        return calc_embed

    @commands.command(name="mapcalc", aliases=["calc"])
    async def map_calc(
            self, ctx: commands.Context, *params: Union[int, str]
    ) -> Union[discord.Message, None]:

        calc_embed = await self.calculate_main(ctx, params)

        if calc_embed:
            return await ctx.reply(ctx.author.mention, embed=calc_embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        beatmap_base_urls: tuple = ("https://osu.ppy.sh/beatmapsets/", "https://osu.ppy.sh/beatmapsets/")

        if message.content.startswith(beatmap_base_urls[0] or message.content.startswith(beatmap_base_urls[1])):
            params: list = message.content.split()
            calc_embed = await self.calculate_main(message, params, reply_errors=False)

            if calc_embed:
                return await message.reply(message.author.mention, embed=calc_embed)


def setup(bot):
    bot.add_cog(MapCalc(bot))
