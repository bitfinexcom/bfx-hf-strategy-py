import json
import sys
sys.path.append('../')

from hfstrategy import Strategy, execOffline
from bfxhfindicators import EMA

class EMAStrategy(Strategy):
  indicators = {
    'emaL': EMA([100]),
    'emaS': EMA([20])
  }

  def onEnter(self, update):
    iv = self.indicatorValues()
    emaS = self.indicators['emaS']
    s = iv['emaS']
    l = iv['emaL']

    if emaS.crossed(l):
      if s > l:
        return self.openLongPositionMarket({
          'mtsCreate': update['mts'],
          'price': update['price'],
          'amount': 1,
        })
      else:
        return self.openShortPositionMarket({
          'mtsCreate': update['mts'],
          'price': update['price'],
          'amount': 1,
        })

  def onUpdateShort(self, update):
    iv = self.indicatorValues()
    s = iv['emaS']
    l = iv['emaL']

    if s < l:
      return self.closePositionMarket({
        'mtsCreate': update['mts'],
        'price': update['price']
      })

  def onUpdateLong(self, update):
    iv = self.indicatorValues()
    s = iv['emaS']
    l = iv['emaL']

    if s > l:
      return self.closePositionMarket({
        'mtsCreate': update['mts'],
        'price': update['price']
      })

with open('btc_candle_data.json', 'r') as f:
  btcCandleData = json.load(f)
  candles = map(lambda candleArray: {
    'mts': candleArray[0],
    'open': candleArray[1],
    'close': candleArray[2],
    'high': candleArray[3],
    'low': candleArray[4],
    'volume': candleArray[5],
    'symbol': 'tBTCUSD',
    'tf': '1min',
  }, btcCandleData)

  strategy = EMAStrategy()

  execOffline(candles, [], strategy)