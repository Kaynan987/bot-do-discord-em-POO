# Define uma classe chamada BotUser
class BotUser:

    # Método construtor: é chamado quando um novo BotUser é criado
    def __init__(self, discord_user):
        # Armazena o objeto do usuário do Discord em um atributo "protegido"
        self._discord_user = discord_user

    # Método público para acessar o nome de usuário do Discord
    def get_username(self):
        return self._discord_user.name
