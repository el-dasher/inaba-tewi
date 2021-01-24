from utils.env_setup import setup_env

DEBUG: bool = True
setup_env()

DEFAULT_BOT_PREFIXES: tuple
if DEBUG:
    DEFAULT_BOT_PREFIXES = ('d!', 'owo!')
else:
    DEFAULT_BOT_PREFIXES = ('tewi!', 'uwu!')

_RAW_COGS: tuple = (
    'osu.droid.userbind', 'osu.droid.profile', 'osu.droid.recent', 'osu.droid.beatmap_calc', 'osu.droid.compare',
    'handlers.error_handler',
    'tools.avatar'
)

COGS: tuple = tuple(map(lambda cog_path: f'cogs.{cog_path}', _RAW_COGS))
