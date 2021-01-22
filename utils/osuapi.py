from os import getenv

from helpers.osu.aioosuapi import aioosuapi

_osu_ppy_api_key: str = getenv("OSU_PPY_API_KEY")
OSU_PPY_API: aioosuapi = aioosuapi(_osu_ppy_api_key)
