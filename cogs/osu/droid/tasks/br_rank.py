from datetime import datetime
from json import JSONDecodeError

import discord
from aioosuapi import Beatmap
from discord.ext import commands, tasks
from discord.ext.commands import Cog

from helpers.osu.beatmaps.droid_oppadc import OsuDroidMap, new_osu_droid_map
from helpers.osu.droid.user_data.osu_droid_data import new_osu_droid_profile, OsuDroidProfile
from utils.bot_setup import DEBUG
from utils.database import OSU_DROID_TEWI_DB
from utils.osuapi import OSU_PPY_API


class BRRank(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        self.br_rank.start()

    @tasks.loop(hours=2)
    async def br_rank(self):

        if DEBUG:
            return None

        try:
            br_rank_channel: discord.TextChannel = self.bot.get_channel(826232339054067745)
            br_rank_message: discord.Message = await br_rank_channel.fetch_message(827262984697937930)
        except AttributeError:
            return print("Os canais do rank de dpp provavelmente foram deletados!")

        fetched_data: list = []

        uid_list: list = OSU_DROID_TEWI_DB.get_br_uids()

        for uid in uid_list:
            print(uid)

            bpp_aim_list, bpp_speed_list, diff_ar_list = [], [], []

            osu_droid_user: OsuDroidProfile = await new_osu_droid_profile(
                uid, needs_player_html=True, needs_pp_data=True
            )

            if not osu_droid_user.exists or not osu_droid_user.in_pp_database:
                continue

            top_plays = osu_droid_user.pp_data['pp']['list']

            try:
                for top_play in top_plays:
                    osu_api_beatmap: Beatmap = await OSU_PPY_API.get_beatmap(h=top_play['hash'])

                    if not osu_api_beatmap:
                        continue
                    else:
                        beatmap_data: OsuDroidMap = await new_osu_droid_map(
                            osu_api_beatmap.beatmap_id,
                            mods=top_play['mods'], misses=top_play['miss'],
                            accuracy=top_play['accuracy'], max_combo=top_play['combo'], custom_speed=1.00
                        )

                        bpp_aim_list.append(beatmap_data.aim_pp)
                        bpp_speed_list.append(beatmap_data.speed_pp)
                        diff_ar_list.append(beatmap_data.ar)

                to_calculate = [
                    diff_ar_list,
                    bpp_speed_list,
                    bpp_aim_list,
                ]

                calculated: list = []

                for calc_list in to_calculate:
                    try:
                        res: float = sum(calc_list) / len(calc_list)
                    except ZeroDivisionError:
                        continue
                    else:
                        calculated.append(res)
                try:
                    user_data = {
                        'uid': osu_droid_user.uid,
                        'total_dpp': osu_droid_user.total_dpp,
                        'total_score': osu_droid_user.total_score,
                        'overall_acc': osu_droid_user.accuracy,
                        'username': osu_droid_user.username,
                        'rank_score': osu_droid_user.rank_score,
                        'avatar': osu_droid_user.avatar,
                        'play_count': osu_droid_user.play_count,
                        'reading': calculated[0],
                        'speed': calculated[1],
                        'aim': calculated[2],
                        'pp_data': top_plays
                    }
                except ValueError as e:
                    print(e)
                except IndexError:
                    continue
                else:
                    fetched_data.append(user_data)
            except (KeyError, JSONDecodeError):
                continue

        fetched_data.sort(key=lambda u: u['total_dpp'], reverse=True)
        top_players = fetched_data[:25]

        OSU_DROID_TEWI_DB.set_new_br_droid_top_players(fetched_data)

        updated_data = discord.Embed(title="RANK DPP BR", timestamp=datetime.utcnow(), color=self.bot.user.color)
        updated_data.set_footer(text="Atualizado")

        for i, user in enumerate(top_players):
            updated_data.add_field(
                name=f"{i + 1} - {user['username']}",
                value=(
                    f">>> ```"
                    f"{user['total_dpp']:.2f}dpp"
                    f" accuracy: {user['overall_acc']:.2f}% - rankscore: #{user['rank_score']}\n"
                    f"[speed: {user['speed']:.2f} |"
                    f" aim: {user['aim']:.2f} |"
                    f" reading: AR{user['reading']:.2f}]"
                    f"```"
                ),
                inline=False
            )

        # noinspection PyBroadException
        if br_rank_message:
            return await br_rank_message.edit(content="", embed=updated_data)
        else:
            return await br_rank_channel.send("Não foi possivel encontrar a mensagem do rank dpp")


def setup(bot):
    bot.add_cog(BRRank(bot))
