from HFStrategy.indicators.indicator import Indicator
from HFStrategy.indicators.ema import EMA

class MassIndex(Indicator):
  def __init__(self, args = []):
    [ period ] = args

    self._smoothing = period
    self._singleEMA = EMA([9])
    self._doubleEMA = EMA([9])
    self._buffer = []

    super().__init__({
      'args': args,
      'id': 'mi',
      'name': 'Mass Index(%f)' % period,
      'seedPeriod': 9 + period,
      'dataType': 'candle',
      'dataKey': '*'
    })

  def reset(self):
    super().reset()
    self._singleEMA.reset()
    self._doubleEMA.reset()
    self._buffer = []

  def update(self, candle):
    high = candle['high']
    low = candle['low']

    self._singleEMA.update(high - low)
    self._doubleEMA.update(self._singleEMA.v())

    if len(self._buffer) == 0:
      self._buffer.append(self._singleEMA.v() / self._doubleEMA.v())
    else:
      self._buffer[-1] = self._singleEMA.v() / self._doubleEMA.v()
    
    if len(self._buffer) < self._smoothing:
      return self.v()
    
    return super().update(sum(self._buffer))

  def add(self, candle):
    high = candle['high']
    low = candle['low']

    self._singleEMA.add(high - low)
    self._doubleEMA.add(self._singleEMA.v())

    self._buffer.append(self._singleEMA.v() / self._doubleEMA.v())

    if len(self._buffer) > self._smoothing:
      del self._buffer[0]
    elif len(self._buffer) < self._smoothing:
      return self.v()
    
    return super().add(sum(self._buffer))
