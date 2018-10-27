from HFStrategy.indicators.indicator import Indicator

class EMA(Indicator):
  def __init__(self, args = []):
    [ period ] = args

    super().__init__({
      'args': args,
      'id': 'ema',
      'name': 'EMA(%f)' % (period),
      'seedPeriod': period
    })

    self._a = 2 / (period + 1)

  def update(self, v):
    if self.l() < 2:
      super().update(v)
    else:
      super().update((self._a * v) + ((1 - self._a) * self.prev()))

    return self.v()

  def add(self, v):
    if self.l() == 0:
      super().add(v)
    else: 
      super().add((self._a * v) + ((1 - self._a) * self.v()))

    return self.v()
