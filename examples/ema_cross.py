import json
import sys
import logging
sys.path.append('../')

from HFStrategy import Strategy, execOffline
from HFStrategy import PositionError
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
        try:
          return self.openLongPositionMarket({
            'mtsCreate': update['mts'],
            'price': update['price'],
            'amount': 1,
          })
        except PositionError as e:
          logging.error(e)
      else:
        try:
          return self.openShortPositionMarket({
            'mtsCreate': update['mts'],
            'price': update['price'],
            'amount': 1,
          })
        except PositionError as e:
          logging.error(e)

  def onUpdateShort(self, update):
    iv = self.indicatorValues()
    s = iv['emaS']
    l = iv['emaL']
    if s > l:
      try:
        return self.closePositionMarket({
          'mtsCreate': update['mts'],
          'price': update['price']
        })
      except PositionError as e:
        logging.error(e)

  def onUpdateLong(self, update):
    iv = self.indicatorValues()
    s = iv['emaS']
    l = iv['emaL']
    if s < l:
      try:
        return self.closePositionMarket({
          'mtsCreate': update['mts'],
          'price': update['price']
        })
      except PositionError as e:
        logging.error(e)

with open('btc_candle_data.json', 'r') as f:
  btcCandleData = json.load(f)
  btcCandleData.reverse()
  candles = map(lambda candleArray: {
    'mts': candleArray[0],
    'open': candleArray[1],
    'close': candleArray[2],
    'high': candleArray[3],
    'low': candleArray[4],
    'volume': candleArray[5],
    'symbol': 'tBTCUSD',
    'tf': '1hr',
  }, btcCandleData)

  strategy = EMAStrategy(backtesting=True, symbol='tBTCUSD')
  execOffline(candles, strategy)
