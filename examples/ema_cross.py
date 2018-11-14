import sys
import logging
sys.path.append('../')

from HFStrategy import BacktestStrategy
from HFStrategy import PositionError
from bfxhfindicators import EMA

class EMAStrategy(BacktestStrategy):
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
          self.openLongPositionMarket(
              mtsCreate=update['mts'], price=update['price'], amount=1)
        except PositionError as e:
          logging.error(e)
      else:
        try:
          self.openShortPositionMarket(
              mtsCreate=update['mts'], price=update['price'], amount=1)
        except PositionError as e:
          logging.error(e)

  def onUpdateShort(self, update):
    iv = self.indicatorValues()
    s = iv['emaS']
    l = iv['emaL']
    if s > l:
      try:
        self.closePositionMarket(
          mtsCreate=update['mts'], price=update['price'])
      except PositionError as e:
        logging.error(e)

  def onUpdateLong(self, update):
    iv = self.indicatorValues()
    s = iv['emaS']
    l = iv['emaL']
    if s < l:
      try:
        self.closePositionMarket(
          mtsCreate=update['mts'], price=update['price'])
      except PositionError as e:
        logging.error(e)

strategy = EMAStrategy(symbol='tBTCUSD')
strategy.runWithCandlesFile('btc_candle_data.json', symbol='tBTCUSD', tf='1hr')
