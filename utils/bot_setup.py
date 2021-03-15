from typing import Tuple

from utils.env_setup import setup_env

DEBUG: bool = False
setup_env()

DEFAULT_BOT_PREFIXES: Tuple[str, ...]
if DEBUG:
    DEFAULT_BOT_PREFIXES = ('d!',)
else:
    DEFAULT_BOT_PREFIXES = ('i!',)

_RAW_COGS: Tuple[str, ...] = (
    'osu.droid.userbind', 'osu.droid.profile', 'osu.droid.recent', 'osu.droid.compare',
    'osu.droid.submit', 'osu.droid.ppcheck',
    'osu.droid.tasks.br_rank',
    'osu.ppy.beatmap_search', 'osu.ppy.beatmap_calc',
    'handlers.error_handler',
    'tools.avatar',
    'tools.guilds.prefix'
)

COGS: tuple = tuple(map(lambda cog_path: f'cogs.{cog_path}', _RAW_COGS))
