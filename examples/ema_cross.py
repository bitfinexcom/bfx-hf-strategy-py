import sys
import asyncio
sys.path.append('../')

from hfstrategy import Strategy
from bfxhfindicators import EMA

# Initialise strategy
strategy = Strategy(
  symbol='tBTCUSD',
  indicators={
    # see https://github.com/bitfinexcom/bfx-hf-indicators-py for more info
    'emaL': EMA(100),
    'emaS': EMA(20)
  },
  exchange_type=Strategy.ExchangeType.EXCHANGE,
  logLevel='INFO'
)

@strategy.on_enter
async def enter(update):
  emaS = strategy.get_indicators()['emaS']
  emaL = strategy.get_indicators()['emaL']
  if emaS.crossed(emaL.v()):
    if emaS.v() > emaL.v():
      await strategy.open_long_position_market(mtsCreate=update.mts, amount=1)
    else:
      await strategy.open_short_position_market(mtsCreate=update.mts, amount=1)

@strategy.on_update_short
async def update_short(update, position):
  if (position.amount == 0):
    print ("Position not filled yet")
    return
  emaS = strategy.get_indicators()['emaS']
  emaL = strategy.get_indicators()['emaL']
  if emaS.v() > emaL.v():
    await strategy.close_position_market(mtsCreate=update.mts)

@strategy.on_update_long
async def update_long(update, position):
  emaS = strategy.get_indicators()['emaS']
  emaL = strategy.get_indicators()['emaL']
  if emaS.v() < emaL.v():
    await strategy.close_position_market(mtsCreate=update.mts)

from hfstrategy import Executor
exe = Executor(strategy,  timeframe='30m')

# Backtest offline
exe.offline(file='btc_candle_data.json')

# Execute live
# import os
# API_KEY=os.getenv("BFX_KEY")
# API_SECRET=os.getenv("BFX_SECRET")
# exe.live(API_KEY, API_SECRET)

# Backtest live
# exe.backtest_live()
