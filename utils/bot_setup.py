from utils.env_setup import setup_env

DEBUG: bool = False
setup_env()

DEFAULT_BOT_PREFIXES: tuple
if DEBUG:
    DEFAULT_BOT_PREFIXES = ('d!',)
else:
    DEFAULT_BOT_PREFIXES = ('tewi!', 'awa!', 'd!')

_RAW_COGS: tuple = ('osu.droid.userbind', 'osu.droid.profile', 'osu.droid.recent', 'handlers.error_handler')
COGS: tuple = tuple(map(lambda cog_path: f'cogs.{cog_path}', _RAW_COGS))
