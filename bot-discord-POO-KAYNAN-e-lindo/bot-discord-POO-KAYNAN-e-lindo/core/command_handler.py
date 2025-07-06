import discord
from discord.ext import commands
from discord.ui import View, button
import asyncio
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import traceback
from spotify_config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from core.audio_manager import AudioManager
from music.player import Player
from music.track import Track
from music.queue import MusicQueue
from core.voice_local import LocalVoiceRecognizer
from abc import ABC, abstractmethod

# Singleton do Spotify (creational pattern)
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

def spotify_to_query(url):
    if "track" in url:
        track_info = sp.track(url)
        track_name = track_info["name"]
        artist = track_info["artists"][0]["name"]
        return f"{track_name} {artist}"
    elif "playlist" in url:
        playlist_info = sp.playlist_tracks(url)
        tracks = []
        for item in playlist_info["items"]:
            track = item["track"]
            name = track["name"]
            artist = track["artists"][0]["name"]
            tracks.append(f"{name} {artist}")
        return tracks
    else:
        raise Exception("URL do Spotify não reconhecida.")

class CommandHandler:
    # Padrões Command e Observer simplificados dentro da classe
    class Command(ABC):
        @abstractmethod
        async def execute(self, ctx):
            pass

    class Observer(ABC):
        @abstractmethod
        def update(self, info):
            pass

    class MusicObserver(Observer):
        def update(self, info):
            print(f"[Observer] Música mudou para: {info}")

    class Subject:
        def __init__(self):
            self._observers = []
            self._state = None

        def attach(self, observer):
            self._observers.append(observer)

        def detach(self, observer):
            self._observers.remove(observer)

        def notify(self):
            for observer in self._observers:
                observer.update(self._state)

        def set_state(self, state):
            self._state = state
            self.notify()

    def __init__(self, bot):
        self.bot = bot
        self.guild_states = {}
        self.voice_threads = {}
        self.voice_recognizers = {}
        self.player = Player()
        self.music_subject = self.Subject()
        self.music_subject.attach(self.MusicObserver())
        self.register_commands()

    def get_guild_state(self, guild_id):
        if guild_id not in self.guild_states:
            self.guild_states[guild_id] = {
                'audio_manager': AudioManager(),
                'queue': MusicQueue(),
                'current_track': None,
                'last_track': None,
                'loop': False
            }
        return self.guild_states[guild_id]

    def start_voice_recognition(self, guild_id, text_channel):
        if guild_id in self.voice_threads and self.voice_threads[guild_id].is_alive():
            print(f"🎙️ Reconhecimento de voz já ativo no servidor {guild_id}.")
            return

        recognizer = LocalVoiceRecognizer()

        def process_command(command):
            class SimpleCtx:
                def __init__(self, channel):
                    self.channel = channel
                    self.guild = channel.guild

                async def send(self, msg):
                    await self.channel.send(msg)

                @property
                def voice_client(self):
                    return self.guild.voice_client

            fake_ctx = SimpleCtx(text_channel)

            if "pausa" in command or "pause" in command or "pausar" in command:
                asyncio.run_coroutine_threadsafe(self.pause_music(fake_ctx), self.bot.loop)
                print(f"🔊 Comando de voz reconhecido no servidor {guild_id}: {command}")
            elif "continua" in command or "resume" in command or "continuar" in command or "continue" in command:
                asyncio.run_coroutine_threadsafe(self.resume_music(fake_ctx), self.bot.loop)
                print(f"🔊 Comando de voz reconhecido no servidor {guild_id}: {command}")
            else:
                pass  # Correção do else inválido

        thread = recognizer.start_background_listening(process_command)
        self.voice_threads[guild_id] = thread
        self.voice_recognizers[guild_id] = recognizer
        print(f"🎧 Reconhecimento de voz ativado no servidor {guild_id}.")

    def stop_voice_recognition(self, guild_id):
        if guild_id in self.voice_threads and self.voice_threads[guild_id].is_alive():
            self.voice_threads[guild_id].do_run = False  # Sua thread deve checar essa flag para parar
            del self.voice_threads[guild_id]
            del self.voice_recognizers[guild_id]
            print(f"🛑 Reconhecimento de voz desativado no servidor {guild_id}.")
        else:
            print(f"⚠️ Reconhecimento de voz não estava ativo no servidor {guild_id}.")

    async def pause_music(self, ctx):
        voice_client = ctx.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await ctx.send("⏸️ Música pausada!")

    async def resume_music(self, ctx):
        voice_client = ctx.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await ctx.send("▶️ Música continuada!")

    async def force_skip(self, ctx):
        voice_client = ctx.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await ctx.send("⏭️ Música pulada!")

    async def toggle_loop(self, ctx):
        state = self.get_guild_state(ctx.guild.id)
        state['loop'] = not state['loop']
        msg = "🔂 Loop ativado!" if state['loop'] else "⏹️ Loop desativado!"
        await ctx.send(msg)

    async def play_last_track(self, ctx):
        state = self.get_guild_state(ctx.guild.id)
        voice_client = ctx.voice_client

        if not voice_client:
            await ctx.send("❌ O bot não está conectado em um canal de voz.")
            return

        if not state['last_track']:
            await ctx.send("⚠️ Não há música anterior para voltar.")
            return

        try:
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()

            self.player.play(voice_client, state['last_track'].url)
            state['current_track'] = state['last_track']
            state['last_track'] = None
            await ctx.send(f"🔁 Tocando novamente: {state['current_track'].title}")
        except Exception as e:
            await ctx.send(f"❌ Erro ao tocar a última música: {str(e)}")

    async def play_next(self, ctx):
        state = self.get_guild_state(ctx.guild.id)
        voice_client = ctx.guild.voice_client
        if not voice_client:
            return

        def after_playing(error):
            fut = asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)
            try:
                fut.result()
            except Exception as e:
                print(f"Erro no after_playing: {e}")

        if state['loop'] and state['current_track']:
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()
            self.player.play(voice_client, state['current_track'].url, after_callback=after_playing, loop_forever=True)
            return

        if not state['queue'].is_empty():
            next_track = state['queue'].next_track()
            state['last_track'] = state['current_track']
            state['current_track'] = next_track

            self.player.play(voice_client, next_track.url, after_callback=after_playing)
            await ctx.send(f'🎶 Tocando agora: {next_track.url}')
        else:
            state['current_track'] = None
            await ctx.send("✅ Fila de músicas acabou.")

    async def process_url(self, ctx, url, add_only=False):
        state = self.get_guild_state(ctx.guild.id)

        if "open.spotify.com" in url:
            result = spotify_to_query(url)

            if isinstance(result, list):
                for track_query in result:
                    track = Track(track_query, url=track_query)
                    state['queue'].add_track(track)
                await ctx.send(f'🎶 Playlist adicionada à fila!')
            else:
                track = Track("Música", result)
                state['queue'].add_track(track)
        else:
            track = Track("Música", url)
            state['queue'].add_track(track)

        voice_client = ctx.guild.voice_client
        if voice_client and not voice_client.is_playing() and not add_only:
            current = state['queue'].next_track()
            if current:
                state['last_track'] = state['current_track']
                state['current_track'] = current

                def after_playing(error):
                    fut = asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)
                    fut.result()

                self.player.play(voice_client, current.url, after_callback=after_playing)
                await ctx.send(f'Tocando agora: {current.url}')

    def register_commands(self):
        @self.bot.command(name="ouvir_on")
        async def ouvir_on(ctx):
            self.start_voice_recognition(ctx.guild.id, ctx.channel)
            await ctx.send("🎙️ Reconhecimento de voz ativado neste servidor!")

        @self.bot.command(name="ouvir_off")
        async def ouvir_off(ctx):
            self.stop_voice_recognition(ctx.guild.id)
            await ctx.send("🛑 Reconhecimento de voz desativado neste servidor!")

        @self.bot.command(name="entra")
        async def join(ctx):
            state = self.get_guild_state(ctx.guild.id)
            await state['audio_manager'].join_channel(ctx)

            thread = await ctx.channel.create_thread(
                name=f"🎵 Controle - {ctx.author.display_name}",
                type=discord.ChannelType.public_thread,
                auto_archive_duration=60
            )

            state['control_thread'] = thread

            await send_music_panel(thread, self, ctx)

        @self.bot.command(name="sai")
        async def leave(ctx):
            state = self.get_guild_state(ctx.guild.id)
            await state['audio_manager'].leave_channel(ctx)
            state['queue'] = MusicQueue()
            state['current_track'] = None

            if 'control_thread' in state and state['control_thread']:
                try:
                    await state['control_thread'].delete()
                except Exception as e:
                    print(f"Erro ao deletar thread: {e}")

        @self.bot.command(name="toca")
        async def play(ctx, url: str):
            await self.process_url(ctx, url)

        @self.bot.command(name="fila")
        async def add_to_queue(ctx, url: str = None):
            if not url:
                await ctx.send("❗ Use `!fila <URL da música>`.")
                return
            await self.process_url(ctx, url, add_only=True)
            await ctx.send(f"✅ Música adicionada à fila: {url}")

        @self.bot.command(name="loop")
        async def toggle_loop(ctx):
            state = self.get_guild_state(ctx.guild.id)
            state['loop'] = not state['loop']
            msg = "🔂 Loop ativado!" if state['loop'] else "⏹️ Loop desativado!"
            await ctx.send(msg)

        @self.bot.command(name="fpula")
        async def force_skip(ctx):
            voice_client = ctx.voice_client
            if voice_client and voice_client.is_playing():
                voice_client.stop()
                await ctx.send("⏭️ Música pulada!")

        @self.bot.command(name="pausa")
        async def pause_music(ctx):
            voice_client = ctx.voice_client
            if voice_client and voice_client.is_playing():
                voice_client.pause()
                await ctx.send("⏸️ Música pausada!")

        @self.bot.command(name="continuar")
        async def resume_music(ctx):
            voice_client = ctx.voice_client
            if voice_client and voice_client.is_paused():
                voice_client.resume()
                await ctx.send("▶️ Música continuada!")

        @self.bot.command(name="pula")
        async def play_now(ctx, *, query=None):
            if not query:
                await ctx.send("⚠️ Você precisa informar o nome ou link da música.")
                return

            voice_client = ctx.voice_client
            if not voice_client:
                await ctx.send("❌ O bot não está em um canal de voz.")
                return

            if voice_client.is_playing():
                voice_client.stop()

            state = self.get_guild_state(ctx.guild.id)
            state['last_track'] = state['current_track']
            state['current_track'] = Track("Música", query)

            try:
                self.player.play(voice_client, query)
                await ctx.send(f"▶️ Tocando agora: {query}")
            except Exception as e:
                await ctx.send(f"❌ Erro ao tocar: {str(e)}")

        @self.bot.command(name="ajuda")
        async def help_command(ctx):
            comandos = [
                "!entra - Entra no canal de voz",
                "!sai - Sai do canal de voz e limpa a fila",
                "!toca <Link> - Toca uma música (Spotify ou YouTube)",
                "!fila <Link> - Adiciona uma música na fila",
                "!loop - Ativa ou desativa o loop da música atual",
                "!fpula - Força pular a música atual e toca a próxima da fila",
                "!pula <Link> - Para a música atual e toca uma nova",
                "!pausa - Pausa a música atual",
                "!continuar - Continua a música pausada",
                "!volta - Toca novamente a última música",
                "!menu - Abre o menu de controle",
                "!ajuda - Mostra essa lista de comandos"
            ]
            await ctx.send("📃 **Lista de Comandos:**\n" + "\n".join(comandos))

        @self.bot.command(name="menu")
        async def painel(ctx):
            await send_music_panel(ctx.channel, self, ctx)

        @self.bot.command(name="volta")
        async def play_last(ctx):
            await self.play_last_track(ctx)

# Modal para entrada de música via painel (UI)
class MusicInputModal(discord.ui.Modal):
    def __init__(self, command_handler, ctx):
        super().__init__(title="🎶 Tocar ou adicionar música")
        self.command_handler = command_handler
        self.ctx = ctx

        self.music_input = discord.ui.TextInput(
            label="Nome ou Link da Música",
            placeholder="Exemplo: https://youtu.be/xxxx ou o nome da música",
            required=True
        )
        self.add_item(self.music_input)

    async def on_submit(self, interaction: discord.Interaction):
        music_name = self.music_input.value

        try:
            await interaction.response.defer(thinking=True)
            await self.command_handler.process_url(self.ctx, music_name)
            await interaction.followup.send(f"✅ Música adicionada: `{music_name}`", ephemeral=True)

        except Exception as e:
            print(f"Erro ao processar o modal: {e}")
            traceback.print_exc()
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Erro ao adicionar a música.", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Erro ao adicionar a música.", ephemeral=True)
            except Exception as inner_e:
                print(f"Erro ao tentar enviar mensagem de erro: {inner_e}")

class ControlPanel(View):
    def __init__(self, command_handler, ctx):
        super().__init__(timeout=None)
        self.command_handler = command_handler
        self.ctx = ctx

    @button(label="⏮️ Voltar Música ", style=discord.ButtonStyle.primary)
    async def play_last(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.command_handler.play_last_track(self.ctx)    


#---------------------------------------------------------------------------------------------------#

    @button(label="⏸️ Pausar ", style=discord.ButtonStyle.primary)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.command_handler.pause_music(self.ctx)
#---------------------------------------------------------------------------------------------------#


    @button(label="▶️ Continuar ", style=discord.ButtonStyle.primary)
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.command_handler.resume_music(self.ctx)
#---------------------------------------------------------------------------------------------------#


    @button(label="⏭️ Pular ", style=discord.ButtonStyle.primary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.command_handler.force_skip(self.ctx)
#---------------------------------------------------------------------------------------------------#
    
    
    @button(label="➕ Adicionar Música ", style=discord.ButtonStyle.success)
    async def add_music(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = MusicInputModal(self.command_handler, self.ctx)
        await interaction.response.send_modal(modal)
#---------------------------------------------------------------------------------------------------#    
    
    @button(label="🔁 Loop ", style=discord.ButtonStyle.success)
    async def loop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.command_handler.toggle_loop(self.ctx)
#---------------------------------------------------------------------------------------------------#


    @button(label="👀 Ver Fila ", style=discord.ButtonStyle.success)
    async def show_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = self.command_handler.get_guild_state(self.ctx.guild.id)
        if state['queue'].is_empty():
            await interaction.response.send_message("📭 A fila está vazia.", ephemeral=True)
            return
        fila_texto = "**🎶 Fila de músicas:**\n"
        for idx, track in enumerate(state['queue'].get_all_tracks(), start=1):
            fila_texto += f"{idx}. {track.get_info()}\n"
        await interaction.response.send_message(fila_texto, ephemeral=True)
#---------------------------------------------------------------------------------------------------#
    @button(label="☝️ Ajuda ", style=discord.ButtonStyle.success)
    async def help_command(self, interaction: discord.Interaction, button: discord.ui.Button):
        comandos = [
            "!entra - Entra no canal de voz",
            "!sai - Sai do canal de voz e limpa a fila",
            "!toca <Link> - Toca uma música",
            "!fila <Link> - Adiciona na fila",
            "!loop - Liga/Desliga o loop",
            "!fpula - Força pular",
            "!pausa - Pausa a música",
            "!continuar - Continua a música",
            "!volta - Toca a última música",
            "!menu - Abre o menu de controle",
            "!ajuda - Mostra essa lista"
        ]
        await interaction.response.send_message("📃 **Lista de Comandos:**\n" + "\n".join(comandos), ephemeral=True)
#---------------------------------------------------------------------------------------------------#

    @button(label="🎙️ Ativar Voz ", style=discord.ButtonStyle.secondary)
    async def ativar_voz(self, interaction: discord.Interaction, button: discord.ui.Button):    
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ Você não pode usar este botão.", ephemeral=True)
            return
        guild_id = self.ctx.guild.id
        self.command_handler.start_voice_recognition(guild_id, self.ctx.channel)
        await interaction.response.send_message("🎙️ Reconhecimento de voz ativado!", ephemeral=True)
#---------------------------------------------------------------------------------------------------#

    @button(label="⏹️ Desativar Voz ", style=discord.ButtonStyle.secondary)
    async def desativar_voz(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ Você não pode usar este botão.", ephemeral=True)
            return
        guild_id = self.ctx.guild.id
        self.command_handler.stop_voice_recognition(guild_id)
        await interaction.response.send_message("🛑 Reconhecimento de voz desativado!", ephemeral=True)

#---------------------------------------------------------------------------------------------------#
    @button(label="😣sair ", style=discord.ButtonStyle.danger)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ Você não pode usar este botão.", ephemeral=True)
            return
        state = self.command_handler.get_guild_state(self.ctx.guild.id)
        await state['audio_manager'].leave_channel(self.ctx)
        state['queue'] = MusicQueue()
        state['current_track'] = None
        await interaction.response.send_message("👋 Saí do canal de voz e limpei a fila.", ephemeral=True)
# Fim da classe CommandHandler




async def send_music_panel(channel, command_handler, ctx):
    # Envia imagem + painel de botões
    # Cria o embed com título, descrição e imagem
    embed = discord.Embed(
    title="🎶 Painel de Controle da Música",
    description=f"Use os botões abaixo para controlar a música!",
    color=0x8e44ad  # Roxo escuro elegante
)
    

    # Substitua pela URL da imagem ou gif decorativo que você quiser
    embed.set_image(url="https://giffiles.alphacoders.com/923/9231.gif")

    view = ControlPanel(command_handler, ctx)
    await channel.send(embed=embed, view=view)
