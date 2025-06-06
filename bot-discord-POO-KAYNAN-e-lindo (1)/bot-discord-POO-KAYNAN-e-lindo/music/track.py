class Track:
  def __init__(self, title, url):
      self.title = title
      self.url = url

  def get_info(self):
      return f'{self.title} - {self.url}'
