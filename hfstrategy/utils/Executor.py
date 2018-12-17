import json
import asyncio
import websockets

from prettytable import PrettyTable
from bfxapi import Client

from ..utils.CustomLogger import CustomLogger
from ..utils.MockWebsocketClient import MockClient
from .DataServerWebsocket import DataServerWebsocket
from ..Strategy.OrderManager import OrderManager

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
    for i, o in enumerate(list(pos.orders.values())):
      lastItem = i+1 == len(pos.orders)
      direction = "SHORT" if o.amount <0 else "LONG"
      pl = round(pos.netProfitLoss, 2)
      x.add_row([o.date, pos.symbol, direction, abs(o.amount), round(o.price, 2),
                round(o.fee, 2), pl if lastItem else 0, o.tag])
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
    totalTrades += len(pos.orders)
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
    strategy.orderManager = OrderManager(ws, backtesting=True, logLevel='INFO')
    strategy.backtesting = True
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
  bfx = MockClient()
  bfxOrderManager = OrderManager(bfx, backtesting=True, logLevel='INFO')
  strategy.set_order_manager(bfxOrderManager)
  strategy.backtesting = True
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

def _start_bfx_ws(strategy, API_KEY=None, API_SECRET=None, backtesting=False):
  bfx = Client(
    API_KEY,
    API_SECRET,
    manageOrderBooks=True, # verify orderbook locally
    dead_man_switch=True, # Kill all orders on disconnect
    ws_host='wss://test.bitfinex.com/ws/2',
    logLevel=strategy.logLevel
  )
  bfxOrderManager = OrderManager(bfx, backtesting=backtesting, logLevel=strategy.logLevel)
  strategy.set_order_manager(bfxOrderManager)
  # Start seeding cancles
  t = asyncio.ensure_future(_seed_candles(strategy, bfx))
  asyncio.get_event_loop().run_until_complete(t)
  async def subscribe():
    await bfx.ws.subscribe('candles', strategy.symbol, timeframe='1m')
    await bfx.ws.subscribe('trades', strategy.symbol)
    await bfx.ws.subscribe('book', strategy.symbol)
  # bind events
  bfx.ws.on('connected', subscribe)
  bfx.ws.on('new_candle', strategy._process_new_candle)
  bfx.ws.on('new_trade', strategy._process_new_trade)
  # bfx.ws.run()
  return bfx

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
  strategy.backtesting = True
  return _start_bfx_ws(strategy, backtesting=backtesting)

def executeLive(strategy, API_KEY, API_SECRET):
  backtesting=False
  return _start_bfx_ws(strategy, API_KEY, API_SECRET, backtesting)
