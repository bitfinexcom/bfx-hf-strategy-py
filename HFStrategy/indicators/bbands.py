from HFStrategy.indicators.indicator import Indicator
from HFStrategy.indicators.sma import SMA
from HFStrategy.indicators.stddev import StdDeviation

class BollingerBands(Indicator):
  def __init__(self, args = []):
    [ period, mul ] = args

    self._p = period
    self._m = mul
    self._sma = SMA([period])
    self._stddev = StdDeviation([period])

    super().__init__({
      'args': args,
      'id': 'bbands',
      'name': 'BBANDS(%f, %f)' % (period, mul),
      'seedPeriod': period
    })

  def reset(self):
    super().reset()
    self._sma.reset()
    self._stddev.reset()

  def update(self, v):
    self._sma.update(v)
    self._stddev.update(v)

    middle = self._sma.v()
    stddev = self._stddev.v()

    super().update({
      'top': middle + (self._m * stddev),
      'middle': middle,
      'bottom': middle - (self._m * stddev)
    })

    return self.v()

  def add(self, v):
    self._sma.add(v)
    self._stddev.add(v)

    middle = self._sma.v()
    stddev = self._stddev.v()

    super().add({
      'top': middle + (self._m * stddev),
      'middle': middle,
      'bottom': middle - (self._m * stddev)
    })

    return self.v()
