from HFStrategy.indicators.indicator import Indicator
from math import isfinite, exp, pow

class ALMA(Indicator):
  def __init__(self, args = []):
    [ period, offset, sigma ] = args

    self._p = period
    self._offset = offset
    self._s = sigma
    self._buffer = []
 
    super().__init__({
      'args': args,
      'id': 'alma',
      'name': 'ALMA(%f, %f, %f)' % (period, offset, sigma),
      'seedPeriod': period
    })

  def reset(self):
    super().reset()
    self._buffer = []

  def calc(buffer, period, offset, sigma):
    m = offset * (period - 1)
    s = period / sigma
    windowSum = 0
    sum = 0

    for i in range(period):
      ex = exp(-1 * (pow(i - m, 2) / (2 * pow(s, 2))))
      windowSum += ex * buffer[i]
      sum += ex
    
    return windowSum / sum

  def update(self, v):
    if len(self._buffer) == 0:
      self._buffer.append(v)
    else:
      self._buffer[-1] = v
    
    if len(self._buffer) < self._p:
      return
    
    super().update(ALMA.calc(self._buffer, self._p, self._offset, self._s))
    return self.v()

  def add(self, v):
    self._buffer.append(v)

    if len(self._buffer) > self._p:
      del self._buffer[0]
    elif len(self._buffer) < self._p:
      return
    
    super().add(ALMA.calc(self._buffer, self._p, self._offset, self._s))
    return self.v()
