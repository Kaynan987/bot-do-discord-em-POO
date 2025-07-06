# Importa a biblioteca do Discord para manipulação de canais de voz
import discord

class AudioManager:
    def __init__(self):
        # Dicionário para armazenar conexões de voz ativas por guild (servidor)
        self.voice_clients = {}

    async def join_channel(self, ctx):
        # Verifica se o usuário que enviou o comando está em um canal de voz
        if ctx.author.voice:
            # Obtém o canal de voz do usuário
            channel = ctx.author.voice.channel
            # Conecta o bot ao canal de voz e armazena a conexão no dicionário
            self.voice_clients[ctx.guild.id] = await channel.connect()
            # Envia mensagem confirmando que entrou no canal
            await ctx.send(f'🎧 Entrei em {channel.name}')
        else:
            # Caso o usuário não esteja em canal de voz, avisa que precisa estar
            await ctx.send("Você precisa estar em um canal de voz.")

    async def leave_channel(self, ctx):
        # Recupera a conexão de voz do bot para a guild atual
        voice_client = self.voice_clients.get(ctx.guild.id)
        if voice_client:
            # Desconecta o bot do canal de voz
            await voice_client.disconnect()
            # Envia mensagem confirmando que saiu do canal
            await ctx.send("Saí, seu Lindo.")
