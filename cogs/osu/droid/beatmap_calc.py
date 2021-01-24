from typing import Tuple, Union, List

import aioosuapi
import discord
from discord.ext import commands

from helpers.osu.beatmaps.calculator import new_bumped_osu_play, BumpedOsuPlay
from utils.bot_defaults import setup_generic_embed
from utils.bot_setup import DEBUG
from utils.const_responses import BEATMAP_NOT_BEING_TALKED
from utils.database import RECENT_CALC_DOCUMENT
from utils.osu_droid_utils import get_default_beatmap_stats_string, clear_previous_calc_from_db_in_one_minute
from utils.osuapi import OSU_PPY_API


class MapCalc(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    async def calculate_main(
            self, ctx: Union[discord.Message, commands.Context],
            *params: Union[Tuple[Union[int, str]], List[Union[int, str]]],
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
            await ctx.reply("❎ **| Não foi possivel encontrar um beatmap com o id que você me forneceu!**")

            return None

        # Filtering the user input to get the correct paramters
        for param in params:
            if param.startswith("+"):
                mods = param.replace("+", "")
            else:
                param_to_int: str = param[:-1]

                if param_to_int.isnumeric():
                    if param.endswith("m"):
                        misses = int(param_to_int)
                    elif param.endswith("x"):
                        combo = int(param_to_int)
                else:
                    try:
                        if param.endswith("%"):
                            accuracy = float(param)
                        elif param.endswith("s"):
                            speed_multiplier = float(param)
                    except ValueError:
                        continue

        try:
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
        except AttributeError:
            return await ctx.reply("❎ **| Ocorreu um erro ao calcular o beatmap")

        calc_embed = setup_generic_embed(self.bot, ctx.author)

        calc_embed.set_author(
            name=f"{calc_beatmap.title} +{mods} {misses}m {float(accuracy):.2f}% {speed_multiplier}x",
            url=beatmap_data_from_osu_api.url
        )

        calc_embed.set_thumbnail(url=beatmap_data_from_osu_api.thumbnail)

        raw_pp_str: str = (
            f"PP RAW: {calc_beatmap.raw_pp:.2f} -({max_values_with_calc_acc.raw_pp:.2f}) | {ppv2_calc.raw_pp:.2f}\n"
        )

        speed_pp_str: str = f"Speed PP: {calc_beatmap.speed_pp:.2f} | {ppv2_calc.speed_pp:.2f}\n"
        aim_pp_str: str = f"Aim PP: {calc_beatmap.aim_pp:.2f} | {ppv2_calc.aim_pp:.2f}\n"
        acc_pp_str: str = f"Acc PP: {calc_beatmap.acc_pp:.2f} | {ppv2_calc.acc_pp:.2f}\n"

        calc_embed.add_field(
            name="---Performance",
            value=">>> **"
                  "__BR_DPP -(max_br_dpp) | PPV2__\n"
                  f"{raw_pp_str}"
                  f"{aim_pp_str}"
                  f"{speed_pp_str}"
                  f"{acc_pp_str}"
                  f"**"
        )

        calc_embed.add_field(
            name="---Beatmap",
            value=get_default_beatmap_stats_string(calc_beatmap, beatmap_data_from_osu_api),
            inline=False
        )

        RECENT_CALC_DOCUMENT.set({f"{ctx.channel.id}": beatmap_id}, merge=True)

        return calc_embed

    @commands.command(name="mapcalc", aliases=["calc", "prevcalc"])
    async def map_calc(
            self, ctx: commands.Context, *params: Union[int, str]
    ) -> None:
        params = list(params)

        if ctx.invoked_with == "prevcalc":
            try:
                previous_beatmap_id = RECENT_CALC_DOCUMENT.get().to_dict()[f"{ctx.channel.id}"]
            except KeyError:
                return await ctx.reply(BEATMAP_NOT_BEING_TALKED)
            else:
                params.insert(0, previous_beatmap_id)

        calc_embed = await self.calculate_main(ctx, params)

        if calc_embed:
            await ctx.reply(ctx.author.mention, embed=calc_embed)
            await clear_previous_calc_from_db_in_one_minute(ctx)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if DEBUG:
            if message.content.startswith("https://osu.ppy.sh/"):
                beatmap_base_urls: tuple = (
                    "https://osu.ppy.sh/beatmapsets/",
                    "https://osu.ppy.sh/beatmaps/",
                    "https://osu.ppy.sh/b/"
                )

                base_url = message.content.split("/")

                if len(base_url) >= 5:
                    base_url[1] = "//"
                    base_url[-1] = "/"
                    base_url[3] = f"/{base_url[3]}"
                else:
                    return None

                base_url = "".join(base_url)

                if base_url in beatmap_base_urls:
                    params: list = message.content.split()
                    calc_embed = await self.calculate_main(message, params)

                    if calc_embed:
                        await message.reply(message.author.mention, embed=calc_embed)
                        await clear_previous_calc_from_db_in_one_minute(message)


def setup(bot):
    bot.add_cog(MapCalc(bot))
