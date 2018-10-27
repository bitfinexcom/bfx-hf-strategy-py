from HFStrategy.indicators.indicator import Indicator
from HFStrategy.indicators.ema import EMA
from HFStrategy.indicators.accumulation_distribution import AccumulationDistribution
from math import isfinite

class ChaikinOsc(Indicator):
  def __init__(self, args = []):
    [ short, long ] = args

    self._shortEMA = EMA([short])
    self._longEMA = EMA([long])
    self._adl = AccumulationDistribution()

    super().__init__({
      'args': args,
      'id': 'chaikinosc',
      'name': 'ChaikinOsc(%f, %f)' % (short, long),
      'seedPeriod': max([short, long]),
      'dataType': 'candle',
      'dataKey': '*'
    })

  def reset(self):
    super().reset()
    self._shortEMA.reset()
    self._longEMA.reset()
    self._adl.reset()

  def update(self, candle):
    self._adl.update(candle)
    adl = self._adl.v()

    if not isfinite(adl):
      return
    
    self._shortEMA.update(adl)
    self._longEMA.update(adl)

    short = self._shortEMA.v()
    long = self._longEMA.v()

    if (isfinite(short) and isfinite(long)):
      super().update(short - long)

    return self.v()

  def add(self, candle):
    self._adl.add(candle)
    adl = self._adl.v()

    if not isfinite(adl):
      return
    
    self._shortEMA.add(adl)
    self._longEMA.add(adl)

    short = self._shortEMA.v()
    long = self._longEMA.v()

    if (isfinite(short) and isfinite(long)):
      super().add(short - long)

    return self.v()
