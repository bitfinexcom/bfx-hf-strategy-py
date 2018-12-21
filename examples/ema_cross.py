import sys
import logging
import asyncio
import time
sys.path.append('../')

from hfstrategy import Strategy
from hfstrategy import PositionError
from bfxhfindicators import EMA
from hfstrategy.models.price_update import PriceUpdate

# Initialise strategy
strategy = Strategy(
  symbol='tBTCUSD',
  indicators={
    'emaL': EMA([100]),
    'emaS': EMA([20])
  },
  exchange_type=Strategy.ExchangeType.EXCHANGE,
  logLevel='INFO'
)

@strategy.on_enter
async def enter(update):
  iv = update.get_indicator_values()
  emaS = strategy.get_indicators()['emaS']
  s = iv['emaS']
  l = iv['emaL']
  if emaS.crossed(l):
    if s > l:
      await strategy.open_long_position_market(mtsCreate=update.mts, amount=1)
    else:
      await strategy.open_short_position_market(mtsCreate=update.mts, amount=1)

@strategy.on_update_short
async def update_short(update):
  iv = update.get_indicator_values()
  s = iv['emaS']
  l = iv['emaL']
  if s > l:
    await strategy.close_position_market(mtsCreate=update.mts)

@strategy.on_update_long
async def update_long(update):
  iv = update.get_indicator_values()
  s = iv['emaS']
  l = iv['emaL']
  if s < l:
    await strategy.close_position_market(mtsCreate=update.mts)

# Backtest offline
from hfstrategy import backtestOffline
backtestOffline(strategy, file='btc_candle_data.json', tf='1hr')

# Backtest with data-backtest server
# import time
# from HFStrategy import backtestWithDataServer
# now = int(round(time.time() * 1000))
# then = now - (1000 * 60 * 60 * 24 * 2) # 5 days ago
# backtestWithDataServer(strategy, then, now)

# Execute live
# import os
# from hfstrategy import executeLive
# API_KEY=os.getenv("BFX_KEY")
# API_SECRET=os.getenv("BFX_SECRET")
# bfx = executeLive(strategy, API_KEY, API_SECRET)

# @strategy.on_position_update
# async def pos_updated(position):
#   print ("--------------------------")
#   print ("POSITION HAS BEEN UPDATED")
#   print ("--------------------------")
#   print (position)
#   print ("")

# @bfx.ws.on('authenticated')
# async def on_auth(x):
#   mts = int(round(time.time() * 1000))
#   update = PriceUpdate(18079, 'tBTCUSD', mts, PriceUpdate.TRADE)
#   strategy.lastPrice['tBTCUSD'] = update

#   print ("RUNNING")
#   await strategy.open_short_position_market(mtsCreate=update.mts, amount=0.02)
#   await asyncio.sleep(5)
#   await strategy.update_short_position_market(mtsCreate=update.mts, amount=0.01)
#   await asyncio.sleep(5)
#   await strategy.set_position_stop(20000, exit_type='LIMIT')
#   await strategy.update_long_position_market(mtsCreate=update.mts, amount=0.03)

# bfx.ws.run()

# Backtest live
# from HFStrategy import backtestLive
# backtestLive(strategy)
