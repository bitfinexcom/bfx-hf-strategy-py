from HFStrategy.indicators.indicator import Indicator

class BOP(Indicator):
  def __init__(self, args = []):
    super().__init__({
      'args': args,
      'id': 'bop',
      'name': 'Balance of Power',
      'seedPeriod': 0,
      'dataType': 'candle',
      'dataKey': '*'
    })

  def update(self, c):
    if c['high'] == c['low']:
      super().update(1)
    else:
      super().update((c['close'] - c['open']) / (c['high'] - c['low']))
    return self.v()

  def add(self, c):
    if c['high'] == c['low']:
      super().add(1)
    else:
      super().add((c['close'] - c['open']) / (c['high'] - c['low']))
    return self.v()
   