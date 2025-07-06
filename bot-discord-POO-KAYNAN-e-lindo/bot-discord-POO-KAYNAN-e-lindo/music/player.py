from base.audio_entity import AudioEntity
from yt_dlp import YoutubeDL
import discord

class Player(AudioEntity):
    def __init__(self):
        # Chama o construtor da classe base AudioEntity
        super().__init__("Player de Música")

    def play(self, voice_channel, url, after_callback=None, loop_forever=False):
        # Configurações para o yt-dlp para extrair áudio de URLs (YouTube, Spotify, etc.)
        ydl_opts = {
            'format': 'bestaudio[ext=webm]/bestaudio/best',  # Melhor áudio possível, preferindo webm
            'quiet': True,  # Silencia saída no console
            'nocheckcertificate': True,  # Ignora checagem de certificado SSL
            'default_search': 'auto',  # Permite pesquisar pelo termo se não for URL direto
            'source_address': '0.0.0.0',  # Usa IP local padrão para conexões
            'http_headers': {  # Cabeçalhos para evitar bloqueios por User-Agent
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
            }
        }

        with YoutubeDL(ydl_opts) as ydl:
            # Extrai informações da URL sem baixar o arquivo
            info = ydl.extract_info(url, download=False)

            # Se for playlist, tenta pegar a primeira música válida
            if 'entries' in info:
                info = next((entry for entry in info['entries'] if entry), None)
                if not info:
                    raise Exception("❌ Link de playlist inválido ou vazio.")

            # Extrai a URL direta do áudio
            if 'url' in info:
                audio_url = info['url']
            elif 'formats' in info and len(info['formats']) > 0:
                # Caso múltiplos formatos, escolhe o melhor áudio válido
                best_audio = next(
                    (f for f in info['formats'] if f.get('acodec') != 'none'),
                    info['formats'][0]
                )
                audio_url = best_audio['url']
            else:
                raise Exception("❌ Não foi possível extrair o link de áudio.")

            # Opção para repetir o áudio indefinidamente (loop)
            before_opts = "-stream_loop -1" if loop_forever else None
            
            # Opções para ffmpeg para garantir reconexão e ignorar erros leves
            ffmpeg_options = (
                "-vn "  # Sem vídeo
                "-reconnect 1 "
                "-reconnect_streamed 1 "
                "-reconnect_delay_max 5 "
                "-err_detect ignore_err "
                "-timeout 5000000"
            )

            # Cria fonte de áudio para discord com as opções definidas
            source = discord.FFmpegPCMAudio(audio_url, before_options=before_opts, options=ffmpeg_options)

            # Controle de volume do áudio (50% padrão)
            source = discord.PCMVolumeTransformer(source, volume=0.5)

            # Inicia a reprodução no canal de voz com callback opcional
            voice_channel.play(source, after=after_callback)
