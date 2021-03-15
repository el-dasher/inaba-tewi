from typing import Union

import aiohttp
import aioosuapi
import oppadc


# Wrap everything like that seens like a reaallly bad iea but it should be fine for now ~~lmao~~
class OsuDroidMap(oppadc.OsuMap):

    # The super class call is missed on purpouse, it gets called in "setup"
    def __init__(
        self, beatmap_id: Union[int, str], mods: str = "NM", misses: int = 0, accuracy: float = 100.00,
        achieved_combo: int = None, speed_multiplier: float = 1.00,
        beatmap_data_from_osu_api: aioosuapi.Beatmap = None, raw_str: Union[None, str] = None
    ):
        """
        :param achieved_combo: the max_combo obtained on the play, defaults to beatmap max-combo
        :param accuracy: accuracy of the play
        :param misses: number of misses of the play
        :param mods: a string of the mods used e.g: DTHD
        :param beatmap_id: id of the beatmap you want to get br pp info
        :return: a dict: {raw_pp, aim_pp, speed_pp, acc_pp, acc_percent}
        """

        super().__init__(raw_str="NONE")

        self.base_mod_input: str = mods

        self._beatmap_data_from_osu_api: Union[aioosuapi.Beatmap, None] = beatmap_data_from_osu_api
        self._beatmap_data: Union[str, None] = None

        self.beatmap_id: Union[str, int] = str(beatmap_id)

        self.mods: str = f"{mods.upper()}TD"

        self.misses: int = misses
        self.accuracy: float = accuracy
        self.max_combo: int = achieved_combo
        self.total_objects: int = 0

        self.raw_pp: Union[float, None] = None
        self.aim_pp: Union[float, None] = None
        self.speed_pp: Union[float, None] = None
        self.acc_pp: Union[float, None] = None

        self.pp_object: Union[oppadc.osumap.OsuDifficulty, None] = None
        self.diff_object: Union[oppadc.osumap.OsuPP, None] = None
        self.stats_object: Union[oppadc.osumap.OsuStats, None] = None

        self.predicted_values = None
        self.speed_multiplier: float = speed_multiplier

        self.base_cs: Union[float, None] = None
        self.base_od: Union[float, None] = None
        self.base_ar: Union[float, None] = None
        self.base_hp: Union[float, None] = None

        self.combo: int = achieved_combo
        self.bpm: Union[float, None] = None
        self.total_length: Union[float, None] = None
        self.beatmap_osu: Union[str, None] = None
        self.raw_str = raw_str
        self.original: Union[oppadc.osumap, None] = None

    async def setup(self) -> None:
        if self.raw_str:
            self.beatmap_osu = self.raw_str
            self._beatmap_data = self.beatmap_osu
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://osu.ppy.sh/osu/{self.beatmap_id}", allow_redirects=True) as res:
                    self.beatmap_osu: str = await res.text()
                    self._beatmap_data = self.beatmap_osu

        super().__init__(raw_str=self.beatmap_osu)
        self.original: oppadc.OsuMap = oppadc.OsuMap(raw_str=self.beatmap_osu)

        self._main()

    def _main(self):
        self._calculate_diff()
        if self.max_combo is None:
            self.max_combo = self.maxCombo()

        self._calculate_droid_stats()

        self._calculate_br_dpp()
        self._dispose_beatmap_data_from_osu_api_diff_data()

    def _calculate_diff(self):
        self.diff_object = self.getDifficulty(Mods=self.mods)

        self.base_cs = self.diff_object.cs
        self.base_od = self.diff_object.od
        self.base_ar = self.diff_object.ar
        self.base_hp = self.diff_object.hp

    def _calculate_droid_stats(self):
        self.od = 5 - (75 + 5 * (5 - self.base_od) - 50) / 6
        self.cs = self.base_cs - 4

        if "SC" in self.mods:
            self.cs += 4
            self.base_cs += 4
        if "PR" in self.mods:
            self.od = 3 + 1.2 * self.od
            self.base_od = 3 + 1.2 * self.base_od
        if "REZ" in self.mods:
            self.ar -= 0.5

            self.cs -= 4
            self.base_cs -= 4

            self.od /= 4
            self.hp /= 4
            self.base_od /= 4
            self.base_hp /= 4
        if "SU" in self.mods:
            self.speed_multiplier = 1.25 * self.speed_multiplier

    def _calculate_br_dpp(self):
        # noinspection PyTypeChecker
        self.pp_object = self.getPP(
            Mods=self.mods, accuracy=self.accuracy, misses=self.misses, combo=self.max_combo, recalculate=True
        )

        self.stats_object = self.getStats(self.mods, recalculate=True)
        self.total_objects = self.amount_circle + self.amount_slider + self.amount_spinner

        self.aim_pp = self.pp_object.aim_pp
        self.speed_pp = self.pp_object.speed_pp * self.speed_multiplier
        self.acc_pp = self.pp_object.acc_pp
        self.raw_pp = self.pp_object.total_pp

        final_multiplier = 1.44

        if "NM" in self.mods:
            final_multiplier *= max(0.9, 1.0 - 0.2 * self.misses)

        # Extreme penalty
        # =======================================================
        # added to penalize map with little aim but ridiculously
        # high speed value (which is easily abusable by using more than 2 fingers).
        extreme_penalty = pow(
            1 - abs(self.speed_pp - pow(self.aim_pp, 1.15)) /
            max(self.speed_pp, pow(self.aim_pp, 1.15)),
            0.2
        )

        final_multiplier *= max(
            pow(extreme_penalty, 2),
            -2 * pow(1 - extreme_penalty, 2) + 1
        )

        self.raw_pp = (
                pow(
                    pow(self.aim_pp, 1.1) + pow(self.speed_pp, 1.1) + pow(self.acc_pp, 1.1),
                    1.0 / 1.1
                ) * final_multiplier
        )

    def _dispose_beatmap_data_from_osu_api_diff_data(self):
        if self._beatmap_data_from_osu_api:
            self.total_length: int = int(float(self._beatmap_data_from_osu_api.total_length) / self.speed_multiplier)
            self.bpm: float = float(self._beatmap_data_from_osu_api.bpm) * self.speed_multiplier

            if "DT" in self.mods:
                self.bpm *= 1.5
                self.total_length /= 0.75


async def new_osu_droid_map(
        beatmap_id, mods: str = "NM", misses: int = 0, accuracy: float = 100.00,
        max_combo: int = None, custom_speed: float = 1.00,
        beatmap_data_from_osu_api: aioosuapi.Beatmap = None, raw_str: str = None
) -> OsuDroidMap:
    osu_droid_bumped_play: OsuDroidMap = OsuDroidMap(
        beatmap_id, mods, misses, accuracy, max_combo, custom_speed, beatmap_data_from_osu_api, raw_str
    )
    await osu_droid_bumped_play.setup()

    return osu_droid_bumped_play
