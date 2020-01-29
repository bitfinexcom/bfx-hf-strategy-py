import os
import asyncio
import sys
import time
sys.path.append('../../')

from hfstrategy import Strategy, Executor, Position
from bfxhfindicators import EMA

fake_candle = {
  'mts': 1533919680000,
  'open': 15000,
  'close': 15000,
  'high': 15000,
  'low': 15000,
  'volume': 38.58293517,
  'symbol': 'tBTCUSD',
  'tf': '1h',
}

# Initialise strategy
strategy = Strategy(
  symbol='tBTCUSD',
  indicators={
    'emaL': EMA(100),
    'emaS': EMA(20)
  },
  exchange_type=Strategy.ExchangeType.MARGIN,
  logLevel='DEBUG'
)

def get_mts():
  return int(round(time.time() * 1000))

async def wait(seconds):
  for _ in range(seconds):
    await asyncio.sleep(1)

async def wait_mills(mills):
  for _ in range(mills):
    await asyncio.sleep(0.01)

@strategy.on_ready
async def ready():
  wait_time = 5
  loop_time = 0.1
  await strategy._process_new_candle(fake_candle)
  await strategy.open_long_position_market(mtsCreate=get_mts(), amount=0.01)
  # sleep for 5 seconds
  await wait(wait_time)
  await strategy.set_position_target(18000, exit_type=Position.ExitType.LIMIT)
  # wait for 5 seconds
  await wait(wait_time)
  await strategy.set_position_stop(14000, exit_type=Position.ExitType.LIMIT)
  # update position with 50 market orders every 10 milliseconds
  for i in range(0, 50):
    await wait_mills(10)
    await strategy.update_position_market(mtsCreate=get_mts(), amount=0.01)
  # wait for 5 seconds
  await wait(wait_time)
  await strategy.set_position_stop(14000, exit_type=Position.ExitType.MARKET)
  # # wait for 5 seconds
  await wait(wait_time)
  await strategy.close_position_market(mtsCreate=get_mts())


API_KEY=os.getenv("BFX_KEY")
API_SECRET=os.getenv("BFX_SECRET")
Executor(strategy, timeframe='30m').live(API_KEY, API_SECRET)
