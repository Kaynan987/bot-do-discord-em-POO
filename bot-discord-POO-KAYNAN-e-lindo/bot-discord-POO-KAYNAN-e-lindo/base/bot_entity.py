# Importa recursos para criar classes abstratas
from abc import ABC, abstractmethod

# Classe base abstrata para entidades do bot
class BotEntity(ABC):
    def __init__(self, name):
        # Atributo protegido que armazena o nome da entidade
        self._name = name

    def get_name(self):
        # Retorna o nome da entidade
        return self._name

    # Método abstrato que obriga subclasses a implementarem esta função
    @abstractmethod
    def info(self):
        pass
