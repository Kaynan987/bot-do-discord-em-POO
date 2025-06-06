from base.bot_entity import BotEntity

class AudioEntity(BotEntity):
    def __init__(self, name):
        super().__init__(name)

    def info(self):
        return f'Entidade de áudio: {self._name}'
