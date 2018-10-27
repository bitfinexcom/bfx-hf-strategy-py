from HFStrategy.indicators.indicator import Indicator
from HFStrategy.indicators.sma import SMA

class Stochastic(Indicator):
  def __init__(self, args = []):
    [ period, smoothK, smoothD ] = args

    self._p = period
    self._buffer = []
    self._kSMA = SMA([smoothK])
    self._dSMA = SMA([smoothD])

    super().__init__({
      'args': args,
      'id': 'stoch',
      'name': 'Stoch(%f)' % (period),
      'seedPeriod': period,
      'dataType': 'candle',
      'dataKey': '*'
    })
  
  def reset(self):
    super().reset()
    self._buffer = []
    self._kSMA.reset()
    self._dSMA.reset()

  def update(self, candle):
    if len(self._buffer) == 0:
      self._buffer.append(candle)
    else:
      self._buffer[-1] = candle

    if len(self._buffer) < self._p:
      return self.v()
    
    close = candle['close']
    lowestLow = min(map(lambda c: c['low'], self._buffer))
    highestHigh = max(map(lambda c: c['high'], self._buffer))
    k = 100 * ((close - lowestLow) / (highestHigh - lowestLow))

    self._kSMA.update(k)
    self._dSMA.update(self._kSMA.v())

    return super().update({
      'k': self._kSMA.v(),
      'd': self._dSMA.v()
    })

  def add(self, candle):
    self._buffer.append(candle)

    if len(self._buffer) > self._p:
      del self._buffer[0]
    elif len(self._buffer) < self._p:
      return self.v()

    close = candle['close']
    lowestLow = min(map(lambda c: c['low'], self._buffer))
    highestHigh = max(map(lambda c: c['high'], self._buffer))
    k = 100 * ((close - lowestLow) / (highestHigh - lowestLow))

    self._kSMA.add(k)
    self._dSMA.add(self._kSMA.v())

    return super().add({
      'k': self._kSMA.v(),
      'd': self._dSMA.v()
    })
