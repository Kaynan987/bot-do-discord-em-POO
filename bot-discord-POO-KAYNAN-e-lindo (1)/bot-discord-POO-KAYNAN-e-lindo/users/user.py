class BotUser:
  def __init__(self, discord_user):
      self._discord_user = discord_user

  def get_username(self):
      return self._discord_user.name
