class MusicQueue:
  def __init__(self):
      self.queue = []

  def add_track(self, track):
      self.queue.append(track)

  def next_track(self):
      return self.queue.pop(0) if self.queue else None

  def is_empty(self):
      return len(self.queue) == 0
