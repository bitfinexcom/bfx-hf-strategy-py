from math import isfinite

class Indicator:
  def __init__(self, params = {}):
    self.name = params['name']
    self.seedPeriod = params['seedPeriod']
    self.id = params['id']
    self.args = params['args']
    self.dataType = params.get('dataType') or '*'
    self.dataKey = params.get('dataKey') or 'close'
    self.reset()

  def reset(self):
    self.values = []

  def l(self):
    return len(self.values)

  def v(self):
    if len(self.values) == 0:
      return 0

    return self.values[-1]

  def prev(self, n = 1):
    if len(self.values) < n:
      return 0

    return self.values[-1 - n]

  def add(self, v):
    self.values.append(v)
    return v

  def update(self, v):
    if len(self.values) == 0:
      return self.add(v)

    self.values[-1] = v
    return v

  def crossed(self, target):
    if self.l() < 2:
      return False
    
    v = self.v()
    prev = self.prev()

    return (
      (v >= target and prev <= target) or
      (v <= target and prev >= target)
    )

  def ready(self):
    return len(self.values) > 0
  