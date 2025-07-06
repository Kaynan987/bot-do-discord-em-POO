# Classe que representa uma ação executada por um usuário
class UserAction:
    # Construtor que recebe um objeto user (espera-se que tenha método get_username())
    def __init__(self, user):
        self.user = user  # Guarda o usuário como atributo da instância

    # Método que realiza a ação e imprime no console qual usuário fez qual ação
    def perform(self, action):
        print(f"{self.user.get_username()} executou: {action}")
