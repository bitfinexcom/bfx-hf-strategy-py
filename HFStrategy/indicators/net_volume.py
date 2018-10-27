from HFStrategy.indicators.indicator import Indicator

class NetVolume(Indicator):
  def __init__(self, args = []):
    super().__init__({
      'args': args,
      'id': 'nv',
      'name': 'Net Volume',
      'seedPeriod': 0,
      'dataType': 'candle',
      'dataKey': '*'
    })

  def update(self, candle):
    vol = candle['vol']

    if candle['close'] >= candle['open']:
      return super().update(vol)
    else:
      return super().update(-vol)

  def add(self, candle):
    vol = candle['vol']

    if candle['close'] >= candle['open']:
      return super().add(vol)
    else:
      return super().add(-vol)
