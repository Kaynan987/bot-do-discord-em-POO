from yt_dlp import YoutubeDL

class Track:
    def __init__(self, title_or_url, url=None):
        # Constructor flexível - pode receber só URL (extrai título) ou título + URL
        # Factory Method (simplificado): Decide como construir o objeto com base nos argumentos
        if url is None:
            self.url = title_or_url
            self.title = self._get_title_from_url(self.url)
        else:
            self.title = title_or_url
            self.url = url

    def _get_title_from_url(self, url):
        # Método responsável por encapsular a lógica de extração do título
        # Encapsulamento e Responsabilidade Única (Single Responsibility Principle)
        try:
            with YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get('title', 'Título Desconhecido')
        except Exception as e:
            print(f"[Erro] Falha ao obter título do YouTube: {e}")
            return "Título Desconhecido"

    def get_info(self):
        # Método para retorno formatado das informações da Track
        # Encapsula como a informação é apresentada, facilitando manutenção
        return f'{self.title} - {self.url}'
