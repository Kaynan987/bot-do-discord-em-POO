# Define uma classe chamada Logger
class Logger:
  # Define um método estático, ou seja, que pode ser chamado sem criar um objeto da classe
  @staticmethod
  def log(message):
      # Exibe a mensagem no terminal com a tag [LOG]
      print(f'[LOG] {message}')
