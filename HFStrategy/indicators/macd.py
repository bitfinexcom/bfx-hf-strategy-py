from HFStrategy.indicators.indicator import Indicator
from HFStrategy.indicators.ema import EMA
from math import isfinite

class MACD(Indicator):
  def __init__(self, args = []):
    [ fastMA, slowMA, signalMA ] = args

    self._slowEMA = EMA([slowMA])
    self._fastEMA = EMA([fastMA])
    self._signalEMA = EMA([signalMA])

    super().__init__({
      'args': args,
      'id': 'macd',
      'name': 'MACD(%f, %f, %f)' % (fastMA, slowMA, signalMA),
      'seedPeriod': max([fastMA, slowMA]) + signalMA
    })
  
  def reset(self):
    super().reset()

    self._slowEMA.reset()
    self._fastEMA.reset()
    self._signalEMA.reset()

  def update(self, v):
    slowEMA = self._slowEMA.update(v)
    fastEMA = self._fastEMA.update(v)

    if not isfinite(slowEMA) or not isfinite(fastEMA):
      return

    macd = fastEMA - slowEMA
    signalEMA = self._signalEMA.update(macd)

    if not isfinite(signalEMA):
      return

    histogram = macd - signalEMA

    super().update({
      'macd': macd,
      'signal': signalEMA,
      'histogram': histogram
    })

    return self.v()

  def add(self, v):
    slowEMA = self._slowEMA.add(v)
    fastEMA = self._fastEMA.add(v)

    if not isfinite(slowEMA) or not isfinite(fastEMA):
      return

    macd = fastEMA - slowEMA
    signalEMA = self._signalEMA.add(macd)

    if not isfinite(signalEMA):
      return

    histogram = macd - signalEMA

    super().add({
      'macd': macd,
      'signal': signalEMA,
      'histogram': histogram
    })

    return self.v()
