from utils.env_setup import setup_env
from typing import Tuple

# DEBUG is here so some behaviours are changed while debugging
DEBUG: bool = False
setup_env()

DEFAULT_BOT_PREFIXES: Tuple[str, ...]
if DEBUG:
    DEFAULT_BOT_PREFIXES = ('d!', 'owo!')
else:
    DEFAULT_BOT_PREFIXES = ('tewi!', 'uwu!')

_RAW_COGS: tuple = (
    'osu.droid.userbind', 'osu.droid.profile', 'osu.droid.recent', 'osu.droid.beatmap_calc', 'osu.droid.compare',
    'osu.droid.submit', 'osu.droid.ppcheck',
    'handlers.error_handler',
    'tools.avatar'
)

COGS: tuple = tuple(map(lambda cog_path: f'cogs.{cog_path}', _RAW_COGS))
