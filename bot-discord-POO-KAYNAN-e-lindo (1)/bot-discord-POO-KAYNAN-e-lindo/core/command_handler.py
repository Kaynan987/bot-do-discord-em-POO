from discord.ext import commands
from core.audio_manager import AudioManager
from music.player import Player
from music.track import Track
from music.queue import MusicQueue

class CommandHandler:
    def __init__(self, bot):
        self.bot = bot
        self.audio_manager = AudioManager()
        self.player = Player()
        self.queue = MusicQueue()

        @bot.command(name="kay")
        async def join(ctx):
            await self.audio_manager.join_channel(ctx)

        @bot.command(name="leave")
        async def leave(ctx):
            await self.audio_manager.leave_channel(ctx)

        @bot.command(name="toca")
        async def play(ctx, url: str):
            track = Track("Música", url)
            self.queue.add_track(track)
            voice_client = ctx.guild.voice_client
            if voice_client and not voice_client.is_playing():
                current = self.queue.next_track()
                if current:
                    self.player.play(voice_client, current.url)
                    await ctx.send(f'Tocando: {current.url}')
