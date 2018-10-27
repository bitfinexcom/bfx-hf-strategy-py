from HFStrategy.indicators.indicator import Indicator
from HFStrategy.indicators.sma import SMA
from math import isfinite

class Envelope(Indicator):
  def __init__(self, args = []):
    [ length, percent ] = args

    self._sma = SMA([length])
    self._p = percent / 100

    super().__init__({
      'args': args,
      'id': 'env',
      'name': 'Env(%f, %f)' % (length, percent),
      'seedPeriod': length,
    })
  
  def reset(self):
    super().reset()
    self._sma.reset()

  def update(self, v):
    self._sma.update(v)
    basis = self._sma.v()

    if not isfinite(basis):
      return
    
    delta = basis * self._p
    super().update({
      'upper': basis + delta,
      'basis': basis,
      'lower': basis - delta
    })

    return self.v()

  def add(self, v):
    self._sma.add(v)
    basis = self._sma.v()

    if not isfinite(basis):
      return
    
    delta = basis * self._p
    super().add({
      'upper': basis + delta,
      'basis': basis,
      'lower': basis - delta
    })

    return self.v()
