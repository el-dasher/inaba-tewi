from os import getenv

import discord
from discord.ext.commands import Bot

from utils import bot_setup

import logging

BOT_TOKEN: str = getenv('BOT_TOKEN')

logging.basicConfig(level=logging.INFO)


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

    async def on_message(self, message: discord.Message):
        if message.author != self.user or not isinstance(message.channel, discord.DMChannel):
            await self.process_commands(message)


inaba_tewi: InabaTewi = InabaTewi()
inaba_tewi.run()
