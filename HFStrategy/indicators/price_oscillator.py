from HFStrategy.indicators.indicator import Indicator
from HFStrategy.indicators.ema import EMA

class PPO(Indicator):
  def __init__(self, args = []):
    [ shortPeriod, longPeriod ] = args

    self._shortEMA = EMA([shortPeriod])
    self._longEMA = EMA([longPeriod])
    self._signalEMA = EMA([9])

    super().__init__({
      'args': args,
      'id': 'ppo',
      'name': 'PPO(%f, %f)' % (shortPeriod, longPeriod),
      'seedPeriod': longPeriod
    })

  def reset(self):
    super().reset()
    self._shortEMA.reset()
    self._longEMA.reset()
    self._signalEMA.reset()

  def update(self, v):
    self._shortEMA.update(v)
    self._longEMA.update(v)

    short = self._shortEMA.v()
    long = self._longEMA.v()
    ppo = 0 if long == 0 else ((short - long) / long) * 100

    self._signalEMA.update(ppo)

    return super().update(self._signalEMA.v())

  def add(self, v):
    self._shortEMA.add(v)
    self._longEMA.add(v)

    short = self._shortEMA.v()
    long = self._longEMA.v()
    ppo = 0 if long == 0 else ((short - long) / long) * 100

    self._signalEMA.add(ppo)

    return super().add(self._signalEMA.v())
