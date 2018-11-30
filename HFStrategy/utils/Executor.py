import json
import asyncio

from prettytable import PrettyTable
from ..utils.CustomLogger import CustomLogger
from bfxapi import Client
from .DataServerWebsocket import DataServerWebsocket
from ..Strategy.OrderManager import OrderManager
import websockets

logger = CustomLogger('HFExecutor', logLevel='INFO')

def _format_candle(mts, open, close, high, low, volume, symbol, tf):
  return {
    'mts': mts,
    'open': open,
    'close': close,
    'high': high,
    'low': low,
    'volume':volume,
    'symbol': symbol,
    'tf': tf,
  }

def _logTrades(positions):
  x = PrettyTable()
  x.field_names = ["Date", "Symbol", "Direction", "Amount", "Price", "Fee", "P&L", "Label"]

  for pos in positions:
    for i, t in enumerate(pos.trades):
      lastItem = i+1 == len(pos.trades)
      pl = round(pos.netProfitLoss, 2)
      x.add_row([t.date, pos.symbol, t.direction, abs(t.amount), round(t.price, 2),
                round(t.fee, 2), pl if lastItem else 0, t.tag])
  print(x)

def _finish(strategy):
  print ("\nBacktesting complete: \n")

  profitLoss = 0
  totalFees = 0
  totalTrades = 0
  totalVolume = 0
  positions = strategy.closedPositions
  minProfitLoss = 0
  maxProfitLoss = 0
  totalLossesCount = 0
  totalLosses = 0
  totalGainersCount = 0
  totalGainers = 0

  for pos in positions:
    profitLoss += pos.profitLoss
    totalFees += pos.totalFees
    totalTrades += len(pos.trades)
    totalVolume += pos.volume
    if pos.netProfitLoss < 0:
      totalLossesCount += 1
      totalLosses += pos.netProfitLoss
    else:
      totalGainersCount += 1
      totalGainers += pos.netProfitLoss
    netP = pos.netProfitLoss
    minProfitLoss = netP if netP < minProfitLoss else minProfitLoss
    maxProfitLoss = netP if netP > maxProfitLoss else maxProfitLoss
  
  _logTrades(positions)
  print('')

  totalNetProfitLoss = profitLoss - totalFees
  logger.info("Net P/L {} | Gross P/L {} | Vol {} | Fees {}".format(
    round(totalNetProfitLoss, 2), round(profitLoss, 2),
    round(totalVolume, 2), round(totalFees, 2)))
  logger.info("Min P/L {} | Max P/L {} | Avg P/L {}".format(
    round(minProfitLoss, 2), round(maxProfitLoss, 2), 
    round(totalNetProfitLoss / totalTrades, 2)))
  logger.info("Losses {} (total {}) | Gains {} (total {})".format(
    totalLossesCount, round(totalLosses, 2), totalGainersCount,
    round(totalGainers, 2)))
  logger.info("{} Positions | {} Trades".format(len(positions), totalTrades))

####################################################
#                Public Functions                  #
####################################################

def backtestWithDataServer(strategy, fromDate, toDate, trades=True, candles=True,
  tf='1m', candleFields="*", tradeFields="*", sync=True):
  def end():
    _finish(strategy)
  try:
    ws = DataServerWebsocket(symbol=strategy.symbol)
    strategy.ws = ws
    ws.on('done', end)
    ws.on('new_candle', strategy._process_new_candle)
    ws.on('new_trade', strategy._process_new_trade)
    strategy.OrderManager = OrderManager(ws, backtesting=True, logLevel='INFO')
    strategy.ws.run(fromDate, toDate, trades, candles, tf, candleFields, tradeFields, sync)
  except websockets.ConnectionClosed:
      pass 

async def _process_candle_batch(strategy, candles):
  for c in candles:
    await strategy._process_new_candle(c)
  async def call_finish():
    await strategy.close_open_positions()
    _finish(strategy)
  # call via event emitter so it scheduled correctly
  strategy.on("done", call_finish)
  await strategy._emit("done")

def backtestOffline(strategy, file=None, candles=None, tf='1hr'):
  strategy.OrderManager = OrderManager(None, backtesting=True, logLevel='INFO')
  if candles:
    return strategy._executeWithCandles(candles)
  elif file:
    with open(file, 'r') as f:
      candleData = json.load(f)
      candleData.reverse()
      candles = map(lambda candleArray: _format_candle(
        candleArray[0], candleArray[1], candleArray[2], candleArray[3],
        candleArray[4], candleArray[5], strategy.symbol, tf
      ), candleData)
      # run async event loop
      loop = asyncio.get_event_loop()
      task = asyncio.ensure_future(_process_candle_batch(strategy, candles))
      loop.run_until_complete(task)
  else:
    raise KeyError("Expected either 'candles' or 'file' in parameters.")

def _start_bfx_ws(strategy, API_KEY=None, API_SECRET=None):
  bfx = Client(
    API_KEY,
    API_SECRET,
    manageOrderBooks=True
  )
  async def subscribe():
    await bfx.ws.subscribe('candles', strategy.symbol, timeframe='1m')
    await bfx.ws.subscribe('trades', strategy.symbol)
    await bfx.ws.subscribe('book', strategy.symbol)
  bfx.ws.on('connected', subscribe)
  bfx.ws.on('new_candle', strategy._process_new_candle)
  bfx.ws.on('new_trade', strategy._process_new_trade)
  bfx.ws.run()

async def _seed_candles(strategy, bfxapi):
  seed_candles = await bfxapi.rest.get_seed_candles(strategy.symbol)
  candles = map(lambda candleArray: _format_candle(
    candleArray[0], candleArray[1], candleArray[2], candleArray[3],
    candleArray[4], candleArray[5], strategy.symbol, '1m'
  ), seed_candles)
  for candle in candles:
    strategy._process_new_seed_candle(candle)

def backtestLive(strategy):
  backtesting=True
  bfx = Client()
  strategy.OrderManager = OrderManager(bfx.ws, backtesting=backtesting, logLevel='INFO')
  t = asyncio.ensure_future(_seed_candles(strategy, bfx))
  asyncio.get_event_loop().run_until_complete(t)
  _start_bfx_ws(strategy)

def executeLive(strategy, API_KEY, API_SECRET):
  backtesting=False 
  bfx = Client(
    API_KEY=API_KEY,
    API_SECRET=API_SECRET
  )
  strategy.OrderManager = OrderManager(bfx.ws, backtesting=backtesting, logLevel='INFO')
  t = asyncio.ensure_future(_seed_candles(strategy, bfx))
  asyncio.get_event_loop().run_until_complete(t)
  bfx.ws.run()
  bfx.ws.on('new_candle', strategy._process_new_candle)
  bfx.ws.on('new_trade', strategy._process_new_trade)
