from HFStrategy.indicators.indicator import Indicator
from HFStrategy.indicators.sma import SMA

class RVGI(Indicator):
  def __init__(self, args = []):
    [ period ] = args

    self._numeratorSMA = SMA([period])
    self._denominatorSMA = SMA([period])
    self._buffer = []

    super().__init__({
      'args': args,
      'id': 'rvgi',
      'name': 'RVGI(%f)' % period,
      'seedPeriod': period,
      'dataType': 'candle',
      'dataKey': '*'
    })
  
  def reset(self):
    super().reset()
    self._numeratorSMA.reset()
    self._denominatorSMA.reset()
    self._buffer = []

  def calc(candle, buffer):
    barA = candle['close'] - candle['open']
    barB = buffer[2]['close'] - buffer[2]['open']
    barC = buffer[1]['close'] - buffer[1]['open']
    barD = buffer[0]['close'] - buffer[0]['open']
    num = (barA + (barB * 2) + (barC * 2) + barD) / 6

    e = candle['high'] - candle['low']
    f = buffer[2]['high'] - buffer[2]['low']
    g = buffer[1]['high'] - buffer[1]['low']
    h = buffer[0]['high'] - buffer[0]['low']
    den = (e + (f * 2) + (g * 2) + h) / 6

    return [num, den]

  def update(self, candle):
    if len(self._buffer) == 0:
      self._buffer.append(candle)
    else:
      self._buffer[-1] = candle

    if len(self._buffer) < 4:
      return super().update(0)

    [num, den] = RVGI.calc(candle, self._buffer)

    self._numeratorSMA.update(num)
    self._denominatorSMA.update(den)

    rvi = self._numeratorSMA.v() / self._denominatorSMA.v()
    signal = 0

    if self.l() >= 3:
      i = self.v()['rvi']
      j = self.prev(1)['rvi']
      k = self.prev(2)['rvi']
      signal = (rvi + (i * 2) + (j * 2) + k) / 6

    super().update({
      'rvi': rvi,
      'signal': signal
    })

  def add(self, candle):
    self._buffer.append(candle)

    if len(self._buffer) > 4:
      del self._buffer[0]
    elif len(self._buffer) < 4:
      return self.v()

    [num, den] = RVGI.calc(candle, self._buffer)

    self._numeratorSMA.add(num)
    self._denominatorSMA.add(den)

    rvi = self._numeratorSMA.v() / self._denominatorSMA.v()
    signal = 0

    if self.l() >= 4:
      i = self.prev(1)['rvi']
      j = self.prev(2)['rvi']
      k = self.prev(3)['rvi']
      signal = (rvi + (i * 2) + (j * 2) + k) / 6

    super().add({
      'rvi': rvi,
      'signal': signal
    })
