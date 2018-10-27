from HFStrategy.indicators.indicator import Indicator

class ATR(Indicator):
  def __init__(self, args = []):
    [ period ] = args

    self._p = period
    self._prevCandle = None
    self._buffer = []
 
    super().__init__({
      'args': args,
      'id': 'atr',
      'name': 'ATR(%f)' % period,
      'seedPeriod': period,
      'dataType': 'candle',
      'dataKey': '*'
    })

  def reset(self):
    super().reset()

    self._prevCandle = None
    self._buffer = []

  def seed(candles):
    tr = map(lambda t: (
      ATR.tr(None if t[0] == 0 else candles[t[0] - 1], t[1])
    ), enumerate(candles))

    return sum(list(tr)) / len(candles)
  
  def calc(prevATR, p, prevCandle, candle):
    return (prevATR * (p - 1) + ATR.tr(prevCandle, candle)) / p

  def tr(prevCandle, candle):
    if prevCandle == None:
      return 0

    return max([
      prevCandle['high'] - prevCandle['low'],
      abs(candle['high'] - prevCandle['close']),
      abs(candle['low'] - prevCandle['close'])
    ])

  def update(self, candle):
    if self.l() == 0:
      if len(self._buffer) < self._p:
        self._buffer.append(candle)
      else:
        self._buffer[-1] = candle
      
      if len(self._buffer) == self._p:
        super().update(ATR.seed(self._buffer))
    else:
      super().update(
        ATR.calc(self.prev(), self._p, self._prevCandle, candle)
      )

    return self.v()

  def add(self, candle):
    if self.l() == 0:
      if len(self._buffer) < self._p:
        self._buffer.append(candle)
      
      if len(self._buffer) == self._p:
        super().add(ATR.seed(self._buffer))
    else:
      super().add(
        ATR.calc(self.v(), self._p, self._prevCandle, candle)
      )
    
    self._prevCandle = candle
    return self.v()
