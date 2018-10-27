from HFStrategy.indicators.indicator import Indicator
from HFStrategy.indicators.ema import EMA
from math import isfinite

class TRIX(Indicator):
  def __init__(self, args = []):
    [ period ] = args

    self._emaFirst = EMA([period])
    self._emaSecond = EMA([period])
    self._emaThird = EMA([period])

    super().__init__({
      'args': args,
      'id': 'trix',
      'name': 'TRIX(%f)' % (period),
      'seedPeriod': (period * 3) + 1
    })
  
  def reset(self):
    super().reset()
    self._emaFirst.reset()
    self._emaSecond.reset()
    self._emaThird.reset()

  def update(self, v):
    self._emaFirst.update(v)
    self._emaSecond.update(self._emaFirst.v())
    self._emaThird.update(self._emaSecond.v())

    curr = self._emaThird.v()

    if not isfinite(curr) or self._emaThird.l() < 2:
      return self.v()

    prev = self._emaThird.prev()
   
    return super().update(((curr / prev) - 1) * 10000)

  def add(self, v):
    self._emaFirst.add(v)
    self._emaSecond.add(self._emaFirst.v())
    self._emaThird.add(self._emaSecond.v())

    curr = self._emaThird.v()

    if not isfinite(curr) or self._emaThird.l() < 2:
      return self.v()

    prev = self._emaThird.prev()
   
    return super().add(((curr / prev) - 1) * 10000)
