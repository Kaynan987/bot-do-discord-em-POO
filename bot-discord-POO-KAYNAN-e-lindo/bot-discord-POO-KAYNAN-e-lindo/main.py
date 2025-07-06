import os
import discord
from discord.ext import commands
from bot_config import TOKEN
from core.command_handler import CommandHandler  # [Command] Gerencia e encapsula comandos de forma modular
from discord import opus
import asyncio

# Tenta carregar o Opus manualmente (ajuste se quiser)
if not discord.opus.is_loaded():
    try:
        discord.opus.load_opus('libopus-0.dll')  # [Proxy ou Façade - opcional] encapsula complexidade do carregamento da biblioteca nativa
    except Exception as e:
        print(f"❌ Falha ao carregar Opus: {e}")
print(f"Opus está carregado? {discord.opus.is_loaded()}")

# 🎮 Intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# 🤖 Bot customizado
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)
        self.command_handler = CommandHandler(self)  # [Command] Centraliza o tratamento de comandos

    async def on_ready(self):
        print(f"🎶 Bot está pronto! Logado como {self.user}")

# 🚀 Inicializa o bot
bot = MyBot()  # [Singleton - implícito] O bot geralmente é único na aplicação
bot.run(TOKEN)
# [Facade] O bot encapsula a complexidade de interações com a API do Discord