import os
import discord
from discord.ext import commands
from bot_config import TOKEN
from core.command_handler import CommandHandler


if not discord.opus.is_loaded():
    try:
        discord.opus.load_opus('libopus.so')
        print("Opus foi esssa porra.")
    except Exception as e:
        print("Opus é uma merda", e)

print("Opus está cargado?", discord.opus.is_loaded())





os.system("apt update && apt install -y ffmpeg")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'🎶 Bot está pronto! Logado como {bot.user}')


CommandHandler(bot)
bot.run(TOKEN)


