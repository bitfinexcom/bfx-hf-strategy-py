import json
import websocket

from prettytable import PrettyTable
from .Strategy import Strategy
from ..utils.CustomLogger import CustomLogger
from ..utils.WebSockets import DataServerWebsocket

def logTrades(positions):
  x = PrettyTable()
  x.field_names = ["Date", "Symbol", "Direction", "Amount", "Price", "Fee", "P&L", "Label"]

  for pos in positions:
    for i, t in enumerate(pos.trades):
      lastItem = i+1 == len(pos.trades)
      pl = round(pos.netProfitLoss, 2)
      x.add_row([t.date, pos.symbol, t.direction, abs(t.amount), round(t.price, 2),
                round(t.fee, 2), pl if lastItem else 0, t.tag])

  print(x)

class BacktestStrategy(Strategy):
  '''
  This class simply wraps the base Strategy class bus adds certain functions that allows
  it to perform backtests such as executeOffline and executeOnline.
  '''
  
  def __init__(self, *args, **kwargs):
    super(BacktestStrategy, self).__init__(multiThreading=False, backtesting=True, *args, **kwargs)
    self.bLogger = CustomLogger('HFBacktesStrategy', logLevel='INFO')

  def executeOffline(self, file=None, candles=None, symbol='tBTCUSD', tf='1hr'):
    if candles:
      return self._executeWithCandles(candles)
    elif file:
      with open(file, 'r') as f:
        candleData = json.load(f)
        candleData.reverse()
        candles = map(lambda candleArray: self.format_candle(
          candleArray[0], candleArray[1], candleArray[2], candleArray[3],
          candleArray[4], candleArray[5], symbol, tf
        ))
        self._executeWithCandles(candles)
    else:
      raise KeyError("Expected either 'candles' or 'file' in parameters.")
  
  def _executeWithCandles(self, candles):
    for candle in candles:
      self.onCandle(candle)
    self._finish()
  
  def format_candle(self, mts, open, close, high, low, volume, symbol, tf):
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

  def executeWithDataServer(self, fromDate, toDate, host='ws://localhost:8899',
      trades=True, candles=True, tf='1m', candleFields="*", tradeFields="*", sync=True):
    DataServerWebsocket(
      fromDate, toDate, self.symbol, trades, candles, tf, candleFields, 
      tradeFields, sync, host,
      onCandleHook=lambda candle: self.onCandle(candle),
      onTradeHook=lambda trade: self.onTrade(trade),
      onCompleteHook=lambda: self._finish()
    )
  
  def _finish(self):
    self.closeOpenPositions()
    print ("\nBacktesting complete: \n")

    profitLoss = 0
    totalFees = 0
    totalTrades = 0
    totalVolume = 0
    positions = self.closedPositions
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
    
    logTrades(positions)
    print('')

    totalNetProfitLoss = profitLoss - totalFees
    self.bLogger.info("Net P/L {} | Gross P/L {} | Vol {} | Fees {}".format(
        round(totalNetProfitLoss, 2), round(profitLoss, 2),
        round(totalVolume, 2), round(totalFees, 2)))
    self.bLogger.info("Min P/L {} | Max P/L {} | Avg P/L {}".format(
        round(minProfitLoss, 2), round(maxProfitLoss, 2), 
        round(totalNetProfitLoss / totalTrades, 2)))
    self.bLogger.info("Losses {} (total {}) | Gains {} (total {})".format(
        totalLossesCount, round(totalLosses, 2), totalGainersCount,
        round(totalGainers, 2)))
    self.bLogger.info("{} Positions | {} Trades".format(len(positions), totalTrades))
