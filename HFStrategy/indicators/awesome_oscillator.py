from HFStrategy.indicators.indicator import Indicator
from HFStrategy.indicators.sma import SMA

class AO(Indicator):
  def __init__(self, args = []):
    self._smaShort = SMA([5])
    self._smaLong = SMA([34])

    super().__init__({
      'args': args,
      'id': 'ao',
      'name': 'AO',
      'seedPeriod': None,
      'dataType': 'candle',
      'dataKey': '*'
    })

  def reset(self):
    super().reset()

    self._smaShort.reset()
    self._smaLong.reset()

  def update(self, candle):
    v = (candle['high'] + candle['low']) / 2

    self._smaShort.update(v)
    self._smaLong.update(v)

    super().update(self._smaShort.v() - self._smaLong.v())
    return self.v()

  def add(self, candle):
    v = (candle['high'] + candle['low']) / 2

    self._smaShort.add(v)
    self._smaLong.add(v)

    super().add(self._smaShort.v() - self._smaLong.v())
    return self.v()
   