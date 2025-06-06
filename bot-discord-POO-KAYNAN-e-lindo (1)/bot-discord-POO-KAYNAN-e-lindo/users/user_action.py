class UserAction:
  def __init__(self, user):
      self.user = user

  def perform(self, action):
      print(f"{self.user.get_username()} executou: {action}")
