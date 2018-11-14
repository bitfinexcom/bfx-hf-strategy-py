import json

from prettytable import PrettyTable
from ..utils.CustomLogger import CustomLogger
from ..BfxWebsocket.LiveWebsocket import LiveBfxWebsocket
from ..BfxWebsocket.DataServerWebsocket import DataServerWebsocket
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
    for i, t in enumerate(pos.trades):
      lastItem = i+1 == len(pos.trades)
      pl = round(pos.netProfitLoss, 2)
      x.add_row([t.date, pos.symbol, t.direction, abs(t.amount), round(t.price, 2),
                round(t.fee, 2), pl if lastItem else 0, t.tag])
  print(x)

def _finish(strategy):
  strategy.closeOpenPositions()
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
  ws = DataServerWebsocket(
    symbol=strategy.symbol,
    onCandleHook=lambda candle: strategy.onCandle(candle),
    onTradeHook=lambda trade: strategy.onTrade(trade),
    onCompleteHook=lambda: strategy._finish()
  )
  strategy.ws = ws
  strategy.OrderManager = OrderManager(ws, backtesting=True, logLevel='INFO')
  strategy.ws.run(fromDate, toDate, trades, candles, tf, candleFields, tradeFields, sync)

def backtestOffline(strategy, file=None, candles=None, tf='1hr'):
  if candles:
    return strategy._executeWithCandles(candles)
  elif file:
    with open(file, 'r') as f:
      candleData = json.load(f)
      candleData.reverse()
      candles = map(lambda candleArray: _format_candle(
        candleArray[0], candleArray[1], candleArray[2], candleArray[3],
        candleArray[4], candleArray[5], strategy.symbol, tf
      ))
      for candle in candles:
        strategy.onCandle(candle)
      _finish(strategy)
  else:
    raise KeyError("Expected either 'candles' or 'file' in parameters.")

def backtestLive(strategy):
  backtesting=True
  ws = LiveBfxWebsocket(
    API_KEY='',
    API_SECRET='',
    backtest=backtesting,
    symbol=strategy.symbol,
    onCandleHook=strategy.onCandle,
    onTradeHook=strategy.onTrade,
    onCompleteHook=lambda: 1 + 2,
    onSeedCandleHook=strategy._onSeedCandle,
    onSeedTradeHook=strategy._onSeedTrade
  )
  strategy.OrderManager = OrderManager(ws, backtesting=backtesting, logLevel='INFO')
  ws.run()

def executeLive(strategy, API_KEY, API_SECRET):
  backtesting=False
  ws = LiveBfxWebsocket(
    API_KEY=API_KEY,
    API_SECRET=API_SECRET,
    symbol=strategy.symbol,
    backtest=backtesting,
    onCandleHook=strategy.onCandle,
    onTradeHook=strategy.onTrade,
    onCompleteHook=lambda: 1 + 2,
    onSeedCandleHook=strategy._onSeedCandle,
    onSeedTradeHook=strategy._onSeedTrade
  )
  strategy.OrderManager = OrderManager(ws, backtesting=backtesting, logLevel='INFO')
  ws.run()
