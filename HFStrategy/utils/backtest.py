from prettytable import PrettyTable
from .CustomLogger import CustomLogger

logger = CustomLogger('HFBacktest', logLevel='INFO')

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

def execOffline(candles, strategy):
  for candle in candles:
    strategy.onCandle(candle)
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
  
  logTrades(positions)
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

