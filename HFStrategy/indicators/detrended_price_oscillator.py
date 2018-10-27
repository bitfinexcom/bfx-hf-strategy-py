from HFStrategy.indicators.indicator import Indicator
from HFStrategy.indicators.sma import SMA
from math import floor

class DPO(Indicator):
  def __init__(self, args = []):
    [ period ] = args

    self._pricePeriod = floor(period / 2) + 1
    self._sma = SMA([period])

    super().__init__({
      'args': args,
      'id': 'dpo',
      'name': 'DPO(%f)' % period,
      'seedPeriod': period
    })
  
  def reset(self):
    super().reset()
    self._sma.reset()

  def update(self, v):
    self._sma.update(v)
    super().update(v - self._sma.prev(self._pricePeriod - 1))
    return self.v()

  def add(self, v):
    self._sma.add(v)

    if self._sma.l() < self._pricePeriod + 1:
      return

    super().add(v - self._sma.prev(self._pricePeriod))
    return self.v()
