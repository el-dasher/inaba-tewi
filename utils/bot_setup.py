from utils.env_setup import setup_env

setup_env()

DEFAULT_BOT_PREFIXES: tuple = ('tewi!', 'awa!')

_RAW_COGS: tuple = ('osu.droid.userbind', 'osu.droid.profile', 'handlers.error_handler')
COGS: tuple = tuple(map(lambda cog_path: f'cogs.{cog_path}', _RAW_COGS))
