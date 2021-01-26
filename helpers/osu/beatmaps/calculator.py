from typing import Union

import aiohttp
import aioosuapi
from copy import deepcopy
import oppadc


# Wrap everything like that seens like a reaallly bad iea but it should be fine for now ~~lmao~~
class BumpedOsuPlay(oppadc.OsuMap):
    # The super class call is missed on purpouse, it gets called in "setup"
    def __init__(self, beatmap_id: Union[int, str], mods: str = "NM", misses: int = 0, accuracy: float = 100.00,
                 achieved_combo: int = None, speed_multiplier: float = 1.00,
                 adjust_to_droid: bool = False, beatmap_data_from_osu_api: aioosuapi.Beatmap = None,
                 raw_str: Union[None, str] = None):
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
        self._adjust_to_droid: bool = adjust_to_droid
        self._beatmap_data: Union[str, None] = None

        self.beatmap_id: Union[str, int] = str(beatmap_id)

        self.mods = mods.upper()
        if self._adjust_to_droid:
            self.mods: str = f"{self.mods}TD"

        self.misses: int = misses
        self.accuracy: float = accuracy
        self.max_combo: int = achieved_combo

        self.raw_pp: Union[float, None] = None
        self.aim_pp: Union[float, None] = None
        self.speed_pp: Union[float, None] = None
        self.acc_pp: Union[float, None] = None

        self.speed_multiplier: float = speed_multiplier

        self.base_cs: Union[float, None] = None
        self.base_od: Union[float, None] = None
        self.base_ar: Union[float, None] = None
        self.base_hp: Union[float, None] = None

        self.bpm: Union[float, None] = None
        self.total_length: Union[float, None] = None
        self.beatmap_osu: Union[str, None] = None
        self.raw_str = raw_str
        self.original: Union[oppadc.osumap, None] = None

    async def setup(self) -> None:
        if self.raw_str:
            self.beatmap_osu = self.raw_str
            self._beatmap_data = self.beatmap_osu
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
        if self._adjust_to_droid:
            self._calculate_droid_stats()

        self._calculate_br_dpp()
        self._dispose_beatmap_data_from_osu_api_diff_data()

    def _calculate_diff(self):
        calculated_diff = self.getDifficulty(Mods=self.mods)

        self.base_cs = calculated_diff.cs
        self.base_od = calculated_diff.od
        self.base_ar = calculated_diff.ar
        self.base_hp = calculated_diff.hp

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
        calculated_pp = self.getPP(
            Mods=self.mods, accuracy=self.accuracy, misses=self.misses, combo=self.max_combo, recalculate=True
        )

        self.aim_pp = calculated_pp.aim_pp
        self.speed_pp = (calculated_pp.speed_pp * self.speed_multiplier)
        self.acc_pp = calculated_pp.acc_pp
        self.raw_pp = calculated_pp.total_pp

        if True:
            if self._adjust_to_droid:
                self._base_speed_pp = self.speed_pp
                self._base_aim_pp = self.aim_pp

                self.speed_pp *= 0.8
                self.aim_pp *= 0.8

                """
                if self.aim_pp <= self.raw_pp / 3 and self.speed_pp >= self.raw_pp / 1.6:
                    self.speed_pp *= 0.6
                elif self.aim_pp <= self.raw_pp / 2.5 and self.speed_pp >= self.raw_pp / 1.25:
                    self.speed_pp *= 0.5
                """

                self.raw_pp -= ((self._base_speed_pp - self.speed_pp) + (self._base_aim_pp - self.aim_pp))

    def _dispose_beatmap_data_from_osu_api_diff_data(self):
        if self._beatmap_data_from_osu_api:
            self.total_length: int = int(float(self._beatmap_data_from_osu_api.total_length) / self.speed_multiplier)
            self.bpm: float = float(self._beatmap_data_from_osu_api.bpm) * self.speed_multiplier

            if "DT" in self.mods:
                self.bpm *= 1.5
                self.total_length /= 0.75


async def new_bumped_osu_play(
        beatmap_id, mods: str = "NM", misses: int = 0, accuracy: float = 100.00,
        max_combo: int = None, custom_speed: float = 1.00,
        adjust_to_droid: bool = False,
        beatmap_data_from_osu_api: aioosuapi.Beatmap = None, raw_str: str = None
) -> BumpedOsuPlay:
    osu_droid_bumped_play: BumpedOsuPlay = BumpedOsuPlay(
        beatmap_id, mods, misses, accuracy, max_combo, custom_speed, adjust_to_droid, beatmap_data_from_osu_api, raw_str
    )
    await osu_droid_bumped_play.setup()

    return osu_droid_bumped_play
