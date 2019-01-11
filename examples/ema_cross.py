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
async def update_short(update, position):
  iv = update.get_indicator_values()
  s = iv['emaS']
  l = iv['emaL']
  if s > l:
    await strategy.close_position_market(mtsCreate=update.mts)

@strategy.on_update_long
async def update_long(update, position):
  iv = update.get_indicator_values()
  s = iv['emaS']
  l = iv['emaL']
  if s < l:
    await strategy.close_position_market(mtsCreate=update.mts)

from hfstrategy import Executor
exe = Executor(strategy,  timeframe='1hr')

# Backtest offline
exe.offline(file='btc_candle_data.json')

# Backtest with data-backtest server
# import time
# now = int(round(time.time() * 1000))
# then = now - (1000 * 60 * 60 * 24 * 2) # 5 days ago
# exe.with_data_server(then, now)

# Execute live
# import os
# API_KEY=os.getenv("BFX_KEY")
# API_SECRET=os.getenv("BFX_SECRET")
# exe.live(API_KEY, API_SECRET)

# Backtest live
# exe.backtest_live()
