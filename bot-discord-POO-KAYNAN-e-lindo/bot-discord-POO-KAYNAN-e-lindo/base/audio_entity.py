# AudioEntity herda da classe base BotEntity, especializando para entidades relacionadas a áudio
from base.bot_entity import BotEntity

class AudioEntity(BotEntity):
    def __init__(self, name):
        # Chama o construtor da superclasse para inicializar o nome da entidade
        super().__init__(name)

    def info(self):
        # Retorna uma string informativa sobre a entidade de áudio
        return f'Entidade de áudio: {self._name}'
