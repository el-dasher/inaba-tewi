from typing import Tuple, Union, List

import aioosuapi
import discord
from discord.ext import commands

from helpers.osu.beatmaps.droid_oppadc import OsuDroidMap, new_osu_droid_map
from utils.bot_defaults import GenericEmbed
from utils.const_responses import BEATMAP_NOT_BEING_TALKED
from utils.database import TEWI_DB
from utils.osu_ppy_and_droid_utils import get_default_beatmap_stats_string
from utils.osuapi import OSU_PPY_API


def is_droid_calc(message: discord.Message):
    it_is: bool = False
    if '-droid' in message.content:
        it_is = True

    return it_is


class CalcEmbed(GenericEmbed):
    def __init__(
        self, bot: commands.Bot, ctx_author: discord.Member, calc_beatmap, beatmap_data_from_osu_api: aioosuapi.Beatmap,
        mods: str, misses: int, accuracy: float, speed_multiplier: float, max_values_with_calc_acc: OsuDroidMap,
        **kwargs
    ):
        super().__init__(bot, ctx_author, **kwargs)

        self.set_author(
            name=f"{calc_beatmap.title} [{beatmap_data_from_osu_api.version}]"
                 f" +{mods} {misses}m {float(accuracy):.2f}% {speed_multiplier}x",
            url=beatmap_data_from_osu_api.url
        )

        self.set_thumbnail(url=beatmap_data_from_osu_api.thumbnail)

        raw_pp_str: str = (
            f"PP RAW: {calc_beatmap.raw_pp:.2f} -({max_values_with_calc_acc.raw_pp:.2f}) | "
        )

        speed_pp_str: str = f"Speed PP: {calc_beatmap.speed_pp:.2f}\n"
        aim_pp_str: str = f"Aim PP: {calc_beatmap.aim_pp:.2f}      \n"
        acc_pp_str: str = f"Acc PP: {calc_beatmap.acc_pp:.2f}      \n"

        self.add_field(
            name="---Performance",
            value=">>> **"
                  "__BR_DPP -(max_br_dpp)__ \n"
                  f"{raw_pp_str}"
                  f"{aim_pp_str}"
                  f"{speed_pp_str}"
                  f"{acc_pp_str}"
                  f"**"
        )

        self.add_field(
            name="---Beatmap",
            value=get_default_beatmap_stats_string(calc_beatmap, beatmap_data_from_osu_api),
            inline=False
        )


class MapCalc(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    async def calculate_main(
            self, ctx: Union[discord.Message, commands.Context], is_droid=False,
            *args: Union[Tuple[Union[int, str]], List[Union[int, str]]],
    ) -> Union[GenericEmbed, None]:
        if not is_droid:
            return await ctx.reply("❎ **| Por enquanto o calculo de beatmaps só funciona em beatmaps do osu!droid!**")

        args = args[0]
        beatmap_id = args[0]

        # This means that the user probably provided a beatmap url over a beatmap_id
        if type(args[0]) == str:
            beatmap_id = args[0].split("/")[-1]

        # Excludes the beatmap_id or url
        args = args[1:]

        mods: str = "NM"
        misses: int = 0
        accuracy: float = 100.00
        combo: Union[int, None] = None
        speed_multiplier: float = 1.00
        beatmap_data_from_osu_api: aioosuapi.Beatmap = await OSU_PPY_API.get_beatmap(b=beatmap_id)

        if not beatmap_data_from_osu_api:
            await ctx.reply("❎ **| Não foi possivel encontrar um beatmap com o id que você me forneceu!**")

            return None

        # Filtering the user input to get the correct parameters
        for param in args:
            if param.startswith("+"):
                mods = param.replace("+", "")
            else:
                param_to_int: str = param[:-1]
                if param.endswith("m"):
                    misses = int(param_to_int)
                elif param.endswith("x"):
                    combo = int(param_to_int)
                else:
                    param_to_float: str = param[:-1]
                    try:
                        floating_param: float = float(param_to_float)
                    except ValueError:
                        continue
                    else:
                        if param.endswith("%"):
                            accuracy = floating_param
                        elif param.endswith("s"):
                            speed_multiplier = floating_param
        calc_beatmap: Union[OsuDroidMap, None] = None
        max_values_with_calc_acc: Union[OsuDroidMap, None] = None
        try:
            if is_droid:
                calc_beatmap = await new_osu_droid_map(
                    beatmap_id, mods, misses, accuracy, combo, speed_multiplier,
                    beatmap_data_from_osu_api
                )
                max_values_with_calc_acc = await new_osu_droid_map(
                    beatmap_id, mods, 0, accuracy, calc_beatmap.maxCombo(),
                    speed_multiplier, beatmap_data_from_osu_api, raw_str=calc_beatmap.raw_str
                )
        except AttributeError:
            return await ctx.reply("❎ **| Ocorreu um erro ao calcular o beatmap")

        calc_embed: GenericEmbed = CalcEmbed(
            self.bot, ctx.author, calc_beatmap, beatmap_data_from_osu_api, mods,
            misses, accuracy, speed_multiplier, max_values_with_calc_acc
        )

        await TEWI_DB.set_recent_play(ctx, calc_beatmap)
        return calc_embed

    @commands.command(name="manualcalc", aliases=["prevcalc"])
    async def map_calc(
            self, ctx: commands.Context, *args: Union[int, str]
    ) -> None:
        args: List[Union[int, str], ...] = list(args)

        if ctx.invoked_with == "prevcalc":
            previous_beatmaps = TEWI_DB.get_recent_plays()

            try:
                previous_beatmap_id = previous_beatmaps[f"{ctx.channel.id}"]
            except KeyError:
                return await ctx.reply(BEATMAP_NOT_BEING_TALKED)

            args.insert(0, previous_beatmap_id)

        if is_droid_calc(ctx.message):
            calc_embed = await self.calculate_main(ctx, True, args)
        else:
            calc_embed = await self.calculate_main(ctx, False, args)

        if calc_embed:
            await ctx.reply(ctx.author.mention, embed=calc_embed)
            await TEWI_DB.clear_previous_calc_from_db(ctx, 240)

    """
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if False:
            if message.content.startswith("https://osu.ppy.sh/"):
                beatmap_base_urls: Tuple[str, ...] = (
                    "https://osu.ppy.sh/beatmapsets/",
                    "https://osu.ppy.sh/beatmaps/",
                    "https://osu.ppy.sh/b/"
                )

                base_url_list: List[str, ...] = message.content.split("/")

                if len(base_url_list) >= 5:
                    if base_url_list[-2].endswith("#osu"):
                        del base_url_list[-2]

                    base_url_list[1] = "//"
                    base_url_list[-1] = "/"
                    base_url_list[3] = f"/{base_url_list[3]}"
                else:
                    return None

                base_url = "".join(base_url_list)
                if base_url in beatmap_base_urls:
                    args: List[str, ...] = message.content.split()

                    if is_droid_calc(message):
                        calc_embed = await self.calculate_main(message, True, args)
                    else:
                        calc_embed = await self.calculate_main(message, False, args)

                    if calc_embed:
                        await message.reply(message.author.mention, embed=calc_embed)
    """


def setup(bot):
    bot.add_cog(MapCalc(bot))
