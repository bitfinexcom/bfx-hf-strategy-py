import json
import asyncio
import websockets
import signal
import sys

from prettytable import PrettyTable
from bfxapi import Client
from pyee import EventEmitter

from ..utils.custom_logger import CustomLogger
from ..utils.mock_websocket_client import MockClient
from ..utils.mock_order_manager import MockOrderManager
from .data_server_websocket import DataServerWebsocket
from ..strategy.order_manager import OrderManager
from ..utils.charts import show_orders_chart

logger = CustomLogger('HFExecutor', logLevel='INFO')

async def _process_candle_batch(strategy, candles):
  await strategy._ready()
  for c in candles:
    await strategy._process_new_candle(c)
  async def call_finish():
    await strategy.close_open_positions()
    _finish(strategy)
  # call via event emitter so it scheduled correctly
  strategy.on("done", call_finish)
  await strategy._emit("done")

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
      # lastItem = i+1 == len(pos.orders)
      direction = "SHORT" if o.amount_filled < 0 else "LONG"
      pl = pos.realised_profit_loss.get(o.id, 0)
      x.add_row([o.date, pos.symbol, direction, o.amount_filled, round(o.price_avg, 2),
                round(o.fee, 2), pl, o.tag])
  print(x)

def _finish(strategy):
  print ("\nBacktesting complete: \n")
  total_gross_profit_loss = 0
  total_net_profit_loss = 0
  total_fees = 0
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
    current_gross_pl = pos.get_profit_loss()['gross']
    total_gross_profit_loss += current_gross_pl
    total_net_profit_loss += pos.get_profit_loss()['net']
    total_fees += pos.total_fees
    totalTrades += len(pos.orders)
    totalVolume += pos.volume
    net_pl = pos.get_realised_profit_loss()

    if current_gross_pl < 0:
      totalLossesCount += 1
      totalLosses += current_gross_pl
    else:
      totalGainersCount += 1
      totalGainers += current_gross_pl
    minProfitLoss = current_gross_pl if current_gross_pl < minProfitLoss else minProfitLoss
    maxProfitLoss = current_gross_pl if current_gross_pl > maxProfitLoss else maxProfitLoss
  
  if not positions:
    logger.info("No closed positions recorded.")
    return

  _logTrades(positions)
  print('')

  logger.info("Net P/L {} | Gross P/L {} | Vol {} | Fees {}".format(
    round(total_net_profit_loss, 2), round(total_gross_profit_loss, 2),
    round(totalVolume, 2), round(total_fees, 2)))
  logger.info("Min P/L {} | Max P/L {} | Avg P/L {}".format(
    round(minProfitLoss, 2), round(maxProfitLoss, 2), 
    round(total_gross_profit_loss / totalTrades, 2)))
  logger.info("Losses {} (total {}) | Gains {} (total {})".format(
    totalLossesCount, round(totalLosses, 2), totalGainersCount,
    round(totalGainers, 2)))
  logger.info("{} Positions | {} Trades".format(len(positions), totalTrades))

async def _seed_candles(strategy, bfxapi, tf):
  seed_candles = await bfxapi.rest.get_seed_candles(strategy.symbol, tf=tf)
  candles = map(lambda candleArray: _format_candle(
    candleArray[0], candleArray[1], candleArray[2], candleArray[3],
    candleArray[4], candleArray[5], strategy.symbol, tf
  ), seed_candles)
  for candle in candles:
    strategy._process_new_seed_candle(candle)

class Executor:

  def __init__(self, strategy, timeframe='1hr', show_chart=True):
    self.strategy = strategy
    self.stored_prices = {}
    self.timeframe = timeframe
    self.show_chart = show_chart

  def _store_candle_price(self, candle):
    self.stored_prices[candle['mts']] = candle['close']

  def _draw_chart(self):
    if (self.show_chart):
      show_orders_chart(self.stored_prices, self.strategy)

  def _kill_signal_handler(self, sig, frame):
    _finish(self.strategy)
    self._draw_chart()
    sys.exit(0)

  def _register_log_on_sigkill(self):
    signal.signal(signal.SIGINT, self._kill_signal_handler)

  def _start_bfx_ws(self, API_KEY=None, API_SECRET=None, backtesting=False):
    bfx = Client(
      API_KEY,
      API_SECRET,
      manageOrderBooks=True, # verify orderbook locally
      dead_man_switch=True, # Kill all orders on disconnect
      logLevel=self.strategy.logLevel,
      max_retries=120, # connection retry 120 times before exiting (10 mins)
      # stop the client creating a seperate thread for the event emitter and
      # use the strategies event emitter
      create_event_emitter=lambda: self.strategy.events
    )
    # use mock order manager if in backtest mode
    if backtesting:
      bfxOrderManager = MockOrderManager(bfx, logLevel=self.strategy.logLevel)
      bfx.ws.on('connected', self.strategy._ready)
    else:
      bfxOrderManager = OrderManager(bfx, logLevel=self.strategy.logLevel)
      bfx.ws.on('authenticated', self.strategy._ready)
    self.strategy.set_order_manager(bfxOrderManager)
    # Start seeding cancles
    t = asyncio.ensure_future(_seed_candles(self.strategy, bfx, self.timeframe))
    asyncio.get_event_loop().run_until_complete(t)
    async def subscribe():
      await bfx.ws.subscribe('candles', self.strategy.symbol, timeframe=self.timeframe)
      await bfx.ws.subscribe('trades', self.strategy.symbol)
      await bfx.ws.subscribe('book', self.strategy.symbol)
    # bind events
    bfx.ws.on('connected', subscribe)
    bfx.ws.on('connected', self.strategy._connected)
    bfx.ws.on('new_candle', self.strategy._process_new_candle)
    bfx.ws.on('new_candle', self._store_candle_price)
    bfx.ws.on('new_trade', self.strategy._process_new_trade)
    bfx.ws.run()

  def with_data_server(self, fromDate, toDate, trades=True, candles=True, sync=True):
    def end():
      _finish(self.strategy)
      self._draw_chart()
    ws = DataServerWebsocket(
      logLevel=self.strategy.logLevel,
      create_event_emitter=lambda: self.strategy.events # use the strategies event emitter
      )
    self.strategy.ws = ws
    ws.on('connected', self.strategy._ready)
    ws.on('done', end)
    ws.on('new_candle', self.strategy._process_new_candle)
    ws.on('new_candle', self._store_candle_price)
    ws.on('new_trade', self.strategy._process_new_trade)
    # mock order simulation
    bfx = MockClient()
    bfxOrderManager = MockOrderManager(bfx, logLevel=self.strategy.logLevel)
    self.strategy.set_order_manager(bfxOrderManager)
    self.strategy.backtesting = True
    self.strategy.ws.run(self.strategy.symbol, fromDate, toDate, trades, candles, self.timeframe, sync)

  def offline(self, file=None, candles=None):
    bfx = MockClient()
    bfxOrderManager = MockOrderManager(bfx, logLevel=self.strategy.logLevel)
    self.strategy.set_order_manager(bfxOrderManager)
    self.strategy.backtesting = True
    if candles:
      return self.strategy._executeWithCandles(candles)
    elif file:
      with open(file, 'r') as f:
        candleData = json.load(f)
        candleData.reverse()
        candles = [_format_candle(
          candleArray[0], candleArray[1], candleArray[2], candleArray[3],
          candleArray[4], candleArray[5], self.strategy.symbol, self.timeframe
        ) for candleArray in candleData]
        # save candles so we can draw a chart later on
        for c in candles:
          self.stored_prices[c['mts']] = c['close']
        # run async event loop
        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(_process_candle_batch(self.strategy, candles))
        loop.run_until_complete(task)
        self._draw_chart()
    else:
      raise KeyError("Expected either 'candles' or 'file' in parameters.")

  def backtest_live(self):
    self.strategy.backtesting = True
    self._register_log_on_sigkill()
    return self._start_bfx_ws(backtesting=True)

  def live(self, API_KEY, API_SECRET):
    self.strategy.backtesting = False
    self._register_log_on_sigkill()
    return self._start_bfx_ws(API_KEY, API_SECRET, backtesting=False)
