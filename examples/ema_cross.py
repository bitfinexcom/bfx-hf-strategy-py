import sys
import logging
import asyncio
sys.path.append('../')

from HFStrategy import Strategy
from HFStrategy import PositionError
from bfxhfindicators import EMA

# Initialise strategy
strategy = Strategy(
  symbol='tBTCUSD',
  indicators={
    'emaL': EMA([100]),
    'emaS': EMA([20])
  }
)

@strategy.on_enter
async def enter(update):
  iv = update.get_indicator_values()
  emaS = strategy.get_indicators()['emaS']
  s = iv['emaS']
  l = iv['emaL']
  if emaS.crossed(l):
    if s > l:
      await strategy.open_long_position_market(
        mtsCreate=update.mts, price=update.price, amount=0.1)
    else:
      await strategy.open_short_position_market(
        mtsCreate=update.mts, price=update.price, amount=0.1)

@strategy.on_update_short
async def update_short(update):
  iv = update.get_indicator_values()
  s = iv['emaS']
  l = iv['emaL']
  if s > l:
    await strategy.close_position_market(
      price=update.price, mtsCreate=update.mts)

@strategy.on_update_long
async def update_long(update):
  iv = update.get_indicator_values()
  s = iv['emaS']
  l = iv['emaL']
  if s < l:
    await strategy.close_position_market(
      price=update.price, mtsCreate=update.mts)

@strategy.on_error
def log_error(error):
  print ("ERROR: {}".format(error))

# Backtest offline
from HFStrategy import backtestOffline
backtestOffline(strategy, file='btc_candle_data.json', tf='1hr')

# Backtest with data-backtest server
# import time
# from HFStrategy import backtestWithDataServer
# now = int(round(time.time() * 1000))
# then = now - (1000 * 60 * 60 * 24 * 2) # 5 days ago
# backtestWithDataServer(strategy, then, now)

# Execute live
# import os
# from HFStrategy import executeLive
# API_KEY=os.getenv("BFX_KEY")
# API_SECRET=os.getenv("BFX_SECRET")
# executeLive(strategy, API_KEY, API_SECRET)

# Backtest live
# from HFStrategy import backtestLive
# backtestLive(strategy)
