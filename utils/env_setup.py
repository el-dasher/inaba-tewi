from pathlib import Path

from dotenv import load_dotenv


def setup_env():
    env_path: Path = Path("./") / ".env"
    load_dotenv(env_path)


setup_env()
