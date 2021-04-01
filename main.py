import logging
from os import getenv

import discord
from typing import Union
from discord.ext.commands import Bot

from utils import bot_setup
from utils.database import MAIN_TEWI_DB

BOT_TOKEN: str = getenv('BOT_TOKEN')

logging.basicConfig(level=logging.INFO)


def get_custom_prefix(msg: discord.Message) -> Union[str, None]:
    guild_prefix: str = MAIN_TEWI_DB.get_guild_custom_prefix(msg.guild)
    return guild_prefix


class InabaTewi(Bot):
    def __init__(self):
        super().__init__(command_prefix=bot_setup.DEFAULT_BOT_PREFIXES, intents=discord.Intents.all())

    def setup(self):
        for cog_path in bot_setup.COGS:
            self.load_extension(cog_path)

    def run(self):
        self.setup()
        super().run(BOT_TOKEN)

    async def on_connect(self):
        print(f'{self.user} connected to discord succesfully')

    async def on_disconnect(self):
        print(f"{self.user} got disconnected, why?")

    async def on_ready(self):
        print(f"{self.user} is ready to pat @everyone")

    async def on_message(self, msg: discord.Message):
        if (
                (
                        msg.author != self.user or not isinstance(msg.channel, discord.DMChannel)
                )
        ):

            for prefix in bot_setup.DEFAULT_BOT_PREFIXES:
                got_custom_prefix: str = get_custom_prefix(msg)

                if got_custom_prefix and not msg.content.startswith(got_custom_prefix):
                    return
                else:
                    if msg.content.startswith(prefix) or got_custom_prefix and msg.content.startswith(got_custom_prefix):
                        try:
                            msg.content = msg.content.replace(got_custom_prefix, bot_setup.DEFAULT_BOT_PREFIXES[0])
                        except TypeError:
                            pass

                        return await self.process_commands(msg)


inaba_tewi: InabaTewi = InabaTewi()
inaba_tewi.run()
