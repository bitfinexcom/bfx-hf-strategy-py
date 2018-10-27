from HFStrategy.indicators.indicator import Indicator
from HFStrategy.indicators.sma import SMA
from math import isfinite

class EOM(Indicator):
  def __init__(self, args = []):
    [ divisor, length ] = args

    self._d = divisor
    self._sma = SMA([length])
    self._lastCandle = None

    super().__init__({
      'args': args,
      'id': 'eom',
      'name': 'EOM(%f, %f)' % (divisor, length),
      'seedPeriod': length,
      'dataType': 'candle',
      'dataKey': '*'
    })

  def reset(self):
    super().reset()
    self._lastCandle = None
    self._sma.reset()

  def calcEOM(candle, lastCandle, divisor):
    high = candle['high']
    low = candle['low']
    vol = candle['vol']
    lastHigh = lastCandle['high']
    lastLow = lastCandle['low']

    moved = ((high + low) / 2) - ((lastHigh + lastLow) / 2)

    if high == low:
      boxRatio = 1
    else:
      boxRatio = (vol / divisor) / (high - low)

    return moved / boxRatio
 
  def update(self, candle):
    if self._lastCandle == None:
      return
    
    eom = EOM.calcEOM(candle, self._lastCandle, self._d)
    self._sma.update(eom)

    v = self._sma.v()

    if isfinite(v):
      super().update(v)
    return self.v()

  def add(self, candle):
    if self._lastCandle == None:
      self._lastCandle = candle
      return
    
    eom = EOM.calcEOM(candle, self._lastCandle, self._d)
    self._sma.add(eom)

    v = self._sma.v()

    if isfinite(v):
      super().add(v)
    
    self._lastCandle = candle
    return self.v()
