from abc import ABC, abstractmethod

class BotEntity(ABC):
    def __init__(self, name):
        self._name = name

    def get_name(self):
        return self._name

    @abstractmethod
    def info(self):
        pass
