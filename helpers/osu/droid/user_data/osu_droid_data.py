from datetime import datetime, timedelta
from json.decoder import JSONDecodeError
from os import getenv
from typing import Union, Tuple, Dict, List

import aiohttp
from bs4 import BeautifulSoup
# noinspection PyProtectedMember
from bs4 import Tag, NavigableString

from helpers.osu.droid.user_data.exceptions import MissingRequiredArgument

_DPP_BOARD_API_KEY: str = getenv('DPP_BOARD_API_KEY')

"""
my_http_headers: dict = {
    "User-Agent":
        "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0)"
        " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"
}
"""


class OsuDroidProfile:
    def __init__(self, uid: int, needs_player_html: bool = False, needs_pp_data: bool = False):
        self.needs_player_html: bool = needs_player_html
        self.needs_pp_data: bool = needs_pp_data

        self.uid: int = uid
        self._user_pp_data_json: Union[None, dict] = None
        self._player_html: Union[None, BeautifulSoup] = None
        self._stats: Union[None, List[str, ...]] = None

        self._needs_pp_data_string: str = 'needs_pp_data'
        self._needs_player_html_string: str = 'needs_player_html'

        self.main_profile_url: str = f"http://ops.dgsrz.com/profile.php?uid={self.uid}"

        self.pp_profile_url: str = (
            f"http://droidppboard.herokuapp.com/api/getplayertop?key={_DPP_BOARD_API_KEY}&uid={self.uid}"
        )

        self.pp_board_is_offline = True
        self.in_pp_database: Union[bool, None] = None

        self._total_score: Union[int, None] = None
        self._accuracy: Union[float, None] = None
        self._play_count: Union[int, None] = None
        self._username: Union[str, None] = None
        self._rank_score: Union[int, None] = None
        self._avatar: Union[str, None] = None
        self._country: Union[str, None] = None
        self._recent_play: Union[OsuDroidPlay, None] = None
        self._recent_plays: Union[Tuple[OsuDroidPlay, ...], None] = None
        self._fast_username: Union[str, None] = None

        self._bad_request: dict = {}

    async def setup(self) -> dict:
        async with aiohttp.ClientSession() as session:
            if self.needs_player_html:
                async with session.get(self.main_profile_url) as res:
                    self._player_html = BeautifulSoup(await res.text(), features="html.parser")
                    self._stats = list(map(lambda a: a.text,
                                           self._player_html.find_all("span", class_="pull-right")[-5:]))
            if self.needs_pp_data:
                async with session.get(self.pp_profile_url) as res:
                    self._bad_request: Dict[str, int, str, list] = {
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
                        self._user_pp_data_json = self._bad_request

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
            self._user_pp_data_json = self._bad_request

    def _player_html_required(self):
        if not self.needs_player_html:
            raise MissingRequiredArgument(missed_arg_name=self._needs_player_html_string)

    @staticmethod
    def _get_play_data(play_html: Union[Tag, NavigableString]):
        return OsuDroidPlay(play_html)

    @property
    def total_score(self) -> int:
        self._player_html_required()

        if not self._total_score:
            self._total_score = int(self._stats[0].replace(',', ''))

        return self._total_score

    @property
    def accuracy(self) -> float:
        self._player_html_required()

        if not self._accuracy:
            self._accuracy = float(self._stats[1][:-1])

        return self._accuracy

    @property
    def play_count(self) -> int:
        self._player_html_required()

        if not self._play_count:
            self._play_count = int(self._stats[2])

        return self._play_count

    @property
    def username(self) -> str:
        self._player_html_required()

        if not self._username:
            self._username = self._player_html.find("div", class_="h3 m-t-xs m-b-xs").text

        return self._username

    @property
    def fast_username(self) -> str:
        self._pp_data_required()

        if not self._fast_username:
            self._fast_username = self.pp_data['username']

        return self._fast_username

    @property
    def rank_score(self) -> str:
        self._player_html_required()

        if not self._rank_score:
            self._rank_score = self._player_html.find("span", class_="m-b-xs h4 block").text

        return self._rank_score

    @property
    def avatar(self) -> str:
        self._player_html_required()

        if not self._avatar:
            self._avatar = self._player_html.find("a", class_="thumb-lg").find("img")['src']

        return self._avatar

    @property
    def country(self) -> str:
        self._player_html_required()

        if not self._country:
            self._country = self._player_html.find("small", class_="text-muted").text

        return self._country

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

        if not self._recent_play:
            play_html: Union[Tag, NavigableString] = self._player_html.find("li", class_="list-group-item")

            try:
                self._recent_play = self._get_play_data(play_html)
            except AttributeError:
                return None

        return self._recent_play

    @property
    def exists(self) -> bool:
        exists: bool = False

        if self._player_html or self._user_pp_data_json:
            if self._fast_username != "" or self.username != "":
                exists = True
        else:
            raise AttributeError

        return exists

    @property
    def recent_plays(self) -> tuple:
        self._player_html_required()

        if not self._recent_plays:
            recent_plays_htmls = self._player_html.find_all("li", class_="list-group-item")

            def get_play_data(play_html):
                try:
                    play_data: OsuDroidPlay = self._get_play_data(play_html)
                except AttributeError:
                    pass
                else:
                    return play_data

            self._recent_plays = tuple(filter(lambda b: b, map(lambda a: get_play_data(a), recent_plays_htmls)))

        return self._recent_plays


class OsuDroidPlay:
    def __init__(self, play_html: Union[Tag, NavigableString]):
        self._title: str = play_html.find("strong", class_="block").text
        self._rank_url: str = self._handle_rank(play_html.find("img")['src'])
        self._stats: tuple = tuple(map(lambda a: a.strip(), play_html.find("small").text.split("/")))

        self._date: datetime = datetime.strptime(self._stats[0], '%Y-%m-%d %H:%M:%S') - timedelta(hours=1)
        self._score: int = int(self._stats[1].replace(",", ''))
        self._mods: str = _replace_mods(self._stats[2])
        self._max_combo: int = int(self._stats[3][:-1])
        self._accuracy: float = float(self._stats[4][:-1])

        self._hidden_data = list(map(
            lambda a: a.strip().split(":")[1].replace("}", ""), play_html.find("span", class_="hidden").text.split(",")
        ))

        self._misscount = int(self._hidden_data[0])
        self._hash_ = self._hidden_data[1]

    @property
    def title(self) -> str:
        return self._title

    @property
    def rank_url(self) -> str:
        return self._rank_url

    @property
    def date(self) -> datetime:
        return self._date

    @property
    def score(self) -> int:
        return self._score

    @property
    def mods(self) -> str:
        return self._mods

    @property
    def max_combo(self) -> int:
        return self._max_combo

    @property
    def accuracy(self) -> float:
        return self._accuracy

    @property
    def misses(self) -> int:
        return self._misscount

    @property
    def hash(self) -> str:
        return self._hash_

    @staticmethod
    def _handle_rank(rank_src) -> str:
        rank_url: str = f"http://ops.dgsrz.com/{rank_src}"

        return rank_url


def _replace_mods(modstring: str) -> str:
    modstring = modstring.replace("DoubleTime", "DT").replace(
        "Hidden", "HD").replace("HardRock", "HR").replace(
        "Hidden", "HD").replace("HardRock", "HR").replace(
        "Precise", "PR").replace("NoFail", "NF").replace(
        "Easy", "EZ").replace("NightCore", "NC").replace(
        "Precise", "PR").replace("None", "NM").replace(",", "").strip().replace(" ", "")

    if modstring == "" or modstring is None:
        modstring = "NM"

    return modstring


async def new_osu_droid_profile(
        uid: int, needs_player_html: bool = False, needs_pp_data: bool = False
) -> OsuDroidProfile:
    user = OsuDroidProfile(uid, needs_player_html=needs_player_html, needs_pp_data=needs_pp_data)
    await user.setup()

    return user
