import sys
import logging
sys.path.append('../')

from HFStrategy import Strategy
from HFStrategy import PositionError
from bfxhfindicators import EMA

class EMAStrategy(Strategy):
  indicators = {
    'emaL': EMA([100]),
    'emaS': EMA([20])
  }

  async def onEnter(self, update):
    iv = self.indicatorValues()
    emaS = self.indicators['emaS']

    s = iv['emaS']
    l = iv['emaL']
    await self.openLongPositionMarket(
        mtsCreate=update['mts'], price=update['price'], amount=1)
    # if emaS.crossed(l):
    #   if True:
    #     if s > l:
    #       try:
    #         await self.openLongPositionMarket(
    #             mtsCreate=update['mts'], price=update['price'], amount=1)
    #       except PositionError as e:
    #         logging.error(e)
    #     else:
    #       try:
    #         await self.openShortPositionMarket(
    #             mtsCreate=update['mts'], price=update['price'], amount=1)
    #       except PositionError as e:
    #         logging.error(e)

  async def onUpdateShort(self, update):
    iv = self.indicatorValues()
    s = iv['emaS']
    l = iv['emaL']
    if s > l:
      try:
        await self.closePositionMarket(price=update['price'], mtsCreate=update['mts'])
      except PositionError as e:
        logging.error(e)

  async def onUpdateLong(self, update):
    iv = self.indicatorValues()
    s = iv['emaS']
    l = iv['emaL']
    if s < l:
      try:
        await self.closePositionMarket(price=update['price'], mtsCreate=update['mts'], )
      except PositionError as e:
        logging.error(e)

# Initialise strategy
strategy = EMAStrategy(
  symbol='tBTCUSD'
)

# Backtest offline
# from HFStrategy import backtestOffline
# backtestOffline(strategy, file='btc_candle_data.json', tf='1hr')

# Backtest with data-backtest server
# import time
# from HFStrategy import backtestWithDataServer
# now = int(round(time.time() * 1000))
# then = now - (1000 * 60 * 60 * 24 * 2) # 5 days ago
# backtestWithDataServer(strategy, then, now)

# Execute live
from HFStrategy import executeLive
API_KEY='UIHBTNmAnleuiZkYiQKzueDvYkHPlU9Rtb7wz1QQ3ff'
API_SECRET='kzX7amS3bzl3VvXwte0w45CblcqUxH4MYNmlx31OyXj'
executeLive(strategy, API_KEY, API_SECRET)

# Backtest live
# from HFStrategy import backtestLive
# backtestLive(strategy)
