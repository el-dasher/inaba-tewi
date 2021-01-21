from datetime import datetime, timedelta
from json.decoder import JSONDecodeError
from os import getenv
from typing import Union

import aiohttp
from bs4 import BeautifulSoup
# noinspection PyProtectedMember
from bs4 import Tag, NavigableString

from .exceptions import MissingRequiredArgument

_DPP_BOARD_API_KEY: str = getenv('DPP_BOARD_API_KEY')


class _OsuDroidProfile:
    def __init__(self, uid: int, needs_player_html: bool = False, needs_pp_data: bool = False):
        self.needs_player_html: bool = needs_player_html
        self.needs_pp_data: bool = needs_pp_data

        self.uid: int = uid
        self._user_pp_data_json: Union[None, dict] = None
        self._player_html: Union[None, BeautifulSoup] = None
        self._stats: Union[None, list] = None

        self._needs_pp_data_string: str = 'needs_pp_data'
        self._needs_player_html_string: str = 'needs_player_html'

        self.main_profile_url: str = f"http://ops.dgsrz.com/profile.php?uid={self.uid}"

        self.pp_profile_url: str = (
            f"http://droidppboard.herokuapp.com/api/getplayertop?key={_DPP_BOARD_API_KEY}&uid={self.uid}"
        )

        self.pp_board_is_offline = True
        self.in_pp_database: Union[bool, None] = None

    async def setup(self) -> dict:
        async with aiohttp.ClientSession() as session:
            if self.needs_player_html:
                async with session.get(self.main_profile_url) as res:
                    self._player_html = BeautifulSoup(await res.text(), features="html.parser")
                    self._stats = list(map(lambda a: a.text,
                                           self._player_html.find_all("span", class_="pull-right")[-5:]))
            if self.needs_pp_data:
                async with session.get(self.pp_profile_url) as res:
                    bad_request: dict = {
                        "uid": 0,
                        "username": "None",
                        "list": []
                    }
                    try:
                        pp_board_res = (await res.json(content_type='text/html'))
                    except JSONDecodeError:
                        pass
                    else:
                        self.pp_board_is_offline = False
                        self._user_pp_data_json = bad_request

                        if 'data' in pp_board_res:
                            self._user_pp_data_json = pp_board_res['data']

                        if self._user_pp_data_json:
                            self.in_pp_database = True
                        else:
                            self.in_pp_database = False

        return {
            self._needs_player_html_string: self._player_html,
            self._needs_pp_data_string: self._user_pp_data_json
        }

    def _pp_data_required(self):
        if not self.needs_pp_data:
            raise MissingRequiredArgument(missed_arg_name=self._needs_pp_data_string)

        if 'pp' not in self._user_pp_data_json:
            self._user_pp_data_json['pp']['total'] = "OFF"

    def _player_html_required(self):
        if not self.needs_player_html:
            raise MissingRequiredArgument(missed_arg_name=self._needs_player_html_string)

    @staticmethod
    def _get_play_data(play_html: Union[Tag, NavigableString]):
        return _OsuDroidPlay(play_html)

    @property
    def total_score(self) -> int:
        self._player_html_required()

        total_score: int = int(self._stats[0].replace(',', ''))
        return total_score

    @property
    def accuracy(self) -> float:
        self._player_html_required()

        accuracy: float = float(self._stats[1][:-1])
        return accuracy

    @property
    def total_playcount(self) -> int:
        self._player_html_required()

        playcount: int = int(self._stats[2])
        return playcount

    @property
    def username(self) -> str:
        self._player_html_required()

        username: str = self._player_html.find("div", class_="h3 m-t-xs m-b-xs").text
        return username

    @property
    def rank_score(self) -> str:
        self._player_html_required()

        rank_score: str = self._player_html.find("span", class_="m-b-xs h4 block").text
        return rank_score

    @property
    def avatar(self) -> str:
        self._player_html_required()

        avatar: str = self._player_html.find("a", class_="thumb-lg").find("img")['src']
        return avatar

    @property
    def country(self) -> str:
        self._player_html_required()

        country: str = self._player_html.find("small", class_="text-muted").text
        return country

    @property
    def pp_data(self) -> dict:
        self._pp_data_required()

        pp_data: dict = self._user_pp_data_json
        return pp_data

    @property
    def total_dpp(self) -> Union[int, None]:
        self._pp_data_required()

        total_dpp = self._user_pp_data_json['pp']['total']

        return total_dpp

    @property
    def best_play(self) -> dict:
        self._pp_data_required()

        best_play: dict = self._user_pp_data_json['pp']['list'][0]
        return best_play

    @property
    def recent_play(self):
        self._player_html_required()

        play_html: Union[Tag, NavigableString] = self._player_html.find("li", class_="list-group-item")
        recent_play = self._get_play_data(play_html)

        return recent_play

    @property
    def exists(self) -> bool:
        self._player_html_required()

        return self.username != ""

    # @property
    # def recent_plays(self):
    #   unfiltered_recent_plays = BeautifulSoup(requests.get(
    #       f"http://ops.dgsrz.com/profile.php?uid={self.uid}").text, features="html.parser"
    #                                           ).find_all("li", class_="list-group-item")
    #
    #    recent_plays = []
    #   for play in unfiltered_recent_plays:
    #        try:
    #            play_data = self.get_play_data(play)
    #        except AttributeError:
    #            pass
    #        else:
    #            recent_plays.append(play_data)
    #   return recent_plays


class _OsuDroidPlay:
    def __init__(self, play_html: Union[Tag, NavigableString]):
        self.title: str = play_html.find("strong", class_="block").text
        self.rank_url: str = self._handle_rank(play_html.find("img")['src'])
        self.stats: tuple = tuple(map(lambda a: a.strip(), play_html.find("small").text.split("/")))

        self.date: datetime = datetime.strptime(self.stats[0], '%Y-%m-%d %H:%M:%S') - timedelta(hours=1)
        self.score: int = int(self.stats[1].replace(",", ''))
        self.mods: str = _replace_mods(self.stats[2])
        self.combo: int = int(self.stats[3][:-1])
        self.accuracy: float = float(self.stats[4][:-1])

        self.hidden_data = list(map(
            lambda a: a.strip().split(":")[1].replace("}", ""), play_html.find("span", class_="hidden").text.split(",")
        ))

        self.misscount = int(self.hidden_data[0])
        self.hash_ = self.hidden_data[1]

    @staticmethod
    def _handle_rank(rank_src) -> str:
        rank_url: str = f"http://ops.dgsrz.com/{rank_src}"

        return rank_url


def _replace_mods(modstring: str):
    modstring = modstring.replace("DoubleTime", "DT").replace(
        "Hidden", "HD").replace("HardRock", "HR").replace(
        "Hidden", "HD").replace("HardRock", "HR").replace(
        "Precise", "PR").replace("NoFail", "NF").replace(
        "Easy", "EZ").replace("NightCore", "NC").replace(
        "Precise", "PR").replace("None", "NM").replace(",", "").strip().replace(" ", "")

    if modstring == "" or modstring is None:
        modstring = "NM"

    return modstring


async def new_osu_droid_profile(uid: int, needs_player_html: bool = False, needs_pp_data: bool = False):
    user = _OsuDroidProfile(uid, needs_player_html=needs_player_html, needs_pp_data=needs_pp_data)
    await user.setup()

    return user
