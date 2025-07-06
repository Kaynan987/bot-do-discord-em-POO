class MusicQueue:
    def __init__(self):
        # Usando encapsulamento: a fila interna é protegida (_queue)
        self._queue = []

    def add_track(self, track):
        # Método público para adicionar faixas à fila
        # Simples e direto, seguindo o princípio da responsabilidade única (SRP)
        self._queue.append(track)

    def next_track(self):
        # Remove e retorna a próxima faixa da fila
        # Implementa o comportamento FIFO (First In, First Out) típico de uma fila
        return self._queue.pop(0) if self._queue else None

    def is_empty(self):
        # Método para verificar se a fila está vazia
        return len(self._queue) == 0

    def get_all_tracks(self):
        # Retorna uma cópia da lista para evitar que o cliente altere a fila diretamente
        # Princípio de encapsulamento e proteção do estado interno do objeto
        return list(self._queue)
