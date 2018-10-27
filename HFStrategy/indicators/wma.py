from HFStrategy.indicators.indicator import Indicator

class WMA(Indicator):
  def __init__(self, args = []):
    [ period ] = args

    d = 0

    for i in range(period):
      d += (i + 1)

    self._d = d
    self._p = period
    self._buffer = []

    super().__init__({
      'args': args,
      'id': 'wma',
      'name': 'WMA(%f)' % period,
      'seedPeriod': period
    })
  
  def reset(self):
    super().reset()
    self._buffer = []

  def update(self, v):
    if len(self._buffer) == 0:
      self._buffer.append(v)
    else:
      self._buffer[-1] = v
    
    if len(self._buffer) < self._p:
      return
    
    n = 0

    for i in range(self._p):
      n += self._buffer[-i - 1] * (self._p - i)
    
    super().update(n / self._d)
    return self.v()

  def add(self, v):
    self._buffer.append(v)

    if len(self._buffer) > self._p:
      del self._buffer[0]
    elif len(self._buffer) < self._p:
      return

    n = 0

    for i in range(self._p):
      n += self._buffer[-i - 1] * (self._p - i)
    
    super().add(n / self._d)
    return self.v()
