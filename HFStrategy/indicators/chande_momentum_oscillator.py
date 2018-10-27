from HFStrategy.indicators.indicator import Indicator

class ChandeMO(Indicator):
  def __init__(self, args = []):
    [ period ] = args

    self._p = period
    self._buffer = []

    super().__init__({
      'args': args,
      'id': 'chandemo',
      'name': 'ChandeMO(%f)' % period,
      'seedPeriod': period,
      'dataType': 'candle',
      'dataKey': '*'
    })

  def reset(self):
    super().reset()
    self._buffer = []

  def update(self, candle):
    if len(self._buffer) == 0:
      self._buffer.append(candle)
    else:
      self._buffer[-1] = candle
    
    if len(self._buffer) < self._p:
      return
    
    uCandles = filter(lambda c: c['close'] > c['open'], self._buffer)
    dCandles = filter(lambda c: c['close'] < c['open'], self._buffer)

    sU = sum(map(lambda c: c['close'] - c['open'], uCandles))
    sD = sum(map(lambda c: c['open'] - c['close'], dCandles))

    super().update(((sU - sD) / (sU + sD)) * 100)
    return self.v()

  def add(self, candle):
    self._buffer.append(candle)

    if len(self._buffer) > self._p:
      del self._buffer[0]
    elif len(self._buffer) < self._p:
      return
    
    uCandles = filter(lambda c: c['close'] > c['open'], self._buffer)
    dCandles = filter(lambda c: c['close'] < c['open'], self._buffer)

    sU = sum(map(lambda c: c['close'] - c['open'], uCandles))
    sD = sum(map(lambda c: c['open'] - c['close'], dCandles))

    super().add(((sU - sD) / (sU + sD)) * 100)
    return self.v()
