from base.audio_entity import AudioEntity
from yt_dlp import YoutubeDL
import discord

class Player(AudioEntity):
    def __init__(self):
        super().__init__("Player de Música")

    def play(self, voice_channel, url):
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'nocheckcertificate': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0'
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Soporte para playlists
            if 'entries' in info:
                info = next((entry for entry in info['entries'] if entry), None)
                if not info:
                    raise Exception("não existe esse link dessa playlists seu burro do caralho")

            # Extracción de audio URL
            if 'url' in info:
                audio_url = info['url']
            elif 'formats' in info and len(info['formats']) > 0:
                best_audio = next((f for f in info['formats'] if f.get('acodec') != 'none'), info['formats'][0])
                audio_url = best_audio['url']
            else:
                raise Exception("burro n funciona")

            voice_channel.play(discord.FFmpegPCMAudio(audio_url))
