import discord

class AudioManager:
    def __init__(self):
        self.voice_clients = {}

    async def join_channel(self, ctx):
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            self.voice_clients[ctx.guild.id] = await channel.connect()
            await ctx.send(f'🎧 Entrei em {channel.name}')
        else:
            await ctx.send("Você precisa estar em um canal de voz.")

    async def leave_channel(self, ctx):
        voice_client = self.voice_clients.get(ctx.guild.id)
        if voice_client:
            await voice_client.disconnect()
            await ctx.send("Saí do canal de voz.")
