from HFStrategy.indicators.indicator import Indicator
from HFStrategy.indicators.roc import ROC
from math import isfinite

class Acceleration(Indicator):
  def __init__(self, args = []):
    [ period ] = args

    self._p = period
    self._roc = ROC([period])
    self._buffer = []
 
    super().__init__({
      'args': args,
      'id': 'acc',
      'name': 'Acceleration(%f)' % (period),
      'seedPeriod': period
    })

  def reset(self):
    super().reset()

    self._buffer = []
    self._roc.reset()

  def update(self, v):
    self._roc.update(v)
    roc = self._roc.v()

    if not isfinite(roc):
      return

    if len(self._buffer) == 0:
      self._buffer.append(roc)
    else:
      self._buffer[-1] = roc

    if len(self._buffer) < self._p:
      return
    
    super().update(roc - self._buffer[0])
    return self.v()

  def add(self, v):
    self._roc.add(v)
    roc = self._roc.v()

    if not isfinite(roc):
      return

    if len(self._buffer) == self._p:
      super().add(roc - self._buffer[0])

    self._buffer.append(roc)

    if len(self._buffer) > self._p:
      del self._buffer[0]

    return self.v()
