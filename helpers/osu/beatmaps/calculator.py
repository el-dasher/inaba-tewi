from typing import Union

import aiohttp
import aioosuapi

import oppadc


class OsuDroidBeatmapData(oppadc.OsuMap):
    # The super class call is missed on purpouse, it gets called in "setup"
    def __init__(self, beatmap_id: Union[str, int], mods: str = "NM", misses: int = 0, accuracy: float = 100.00,
                 achieved_combo: int = None, speed_multiplier: float = 1.00,
                 adjust_to_droid: bool = False, beatmap_data_from_osu_api: aioosuapi.Beatmap = None):
        """
        :param achieved_combo: the max_combo obtained on the play, defaults to beatmap max-combo
        :param accuracy: accuracy of the play
        :param misses: number of misses of the play
        :param mods: a string of the mods used e.g: DTHD
        :param beatmap_id: id of the beatmap you want to get br pp info
        :return: a dict: {raw_pp, aim_pp, speed_pp, acc_pp, acc_percent}
        """

        super().__init__(raw_str="NONE")

        self._beatmap_data_from_osu_api: Union[aioosuapi.Beatmap, None] = beatmap_data_from_osu_api
        self._adjust_to_droid: bool = adjust_to_droid
        self._beatmap_data: Union[str, None] = None

        self.beatmap_id: Union[str, int] = str(beatmap_id)
        self.mods: str = f"{mods.upper()}TD"
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

        self.bpm = 0
        if self._beatmap_data_from_osu_api:
            self.bpm: float = float(self._beatmap_data_from_osu_api.bpm) * self.speed_multiplier
            if "DT" in self.mods:
                self.bpm *= 1.5

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
        if "PR" in self.mods:
            self.od = 3 + 1.2 * self.od
        if "REZ" in self.mods:
            self.ar -= 0.5
            self.cs -= 4
            self.od /= 4
            self.hp /= 4
        if "SU" in self.mods:
            self.speed_multiplier = 1.25 * self.speed_multiplier

    def _calculate_br_dpp(self):
        # noinspection PyTypeChecker
        calculated_pp = self.getPP(Mods=self.mods, accuracy=self.accuracy, misses=self.misses, combo=self.max_combo, recalculate=True)

        self.raw_pp = calculated_pp.total_pp
        self.aim_pp = calculated_pp.aim_pp
        self.speed_pp = calculated_pp.speed_pp * self.speed_multiplier
        self.acc_pp = calculated_pp.speed_pp


    async def setup(self) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://osu.ppy.sh/osu/{self.beatmap_id}", allow_redirects=True) as res:
                beatmap_osu: str = await res.text()

                super().__init__(raw_str=beatmap_osu)

                self._beatmap_data = beatmap_osu

        self._calculate_diff()
        if self.max_combo is None:
            self.max_combo = self.maxCombo()
        if self._adjust_to_droid:
            self._calculate_droid_stats()

        self._calculate_br_dpp()


async def new_osu_droid_play_bpp(
        beatmap_id, mods: str = "NM", misses: int = 0, accuracy: float = 100.00,
        max_combo: int = None, custom_speed: float = 1.00,
        adjust_to_droid: bool = False, beatmap_data_from_osu_api: aioosuapi.Beatmap = None
) -> OsuDroidBeatmapData:
    osu_droid_play_bpp: OsuDroidBeatmapData = OsuDroidBeatmapData(
        beatmap_id, mods, misses, accuracy, max_combo, custom_speed, adjust_to_droid, beatmap_data_from_osu_api
    )
    await osu_droid_play_bpp.setup()

    return osu_droid_play_bpp
