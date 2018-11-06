from prettytable import PrettyTable

def logTrades(positions):
  x = PrettyTable()
  x.field_names = ["Date", "Symbol", "Direction", "Amount", "Price", "Fee", "P&L", "Label"]

  for pos in positions:
    for i, t in enumerate(pos.trades):
      lastItem = i+1 == len(pos.trades)
      pl = round(pos.profitLoss, 2)
      x.add_row([t.date, pos.symbol, t.direction, t.amount, round(t.price, 2),
                round(t.fee, 2), pl if lastItem else 0, ''])

  print(x)

def execOffline(candles, trades, strategy):
  currentTrade = 0

  for candle in candles:
    strategy.onCandle(candle)

  print ("\nBacktesting complete: \n")

  profitLoss = 0
  totalFees = 0
  totalTrades = 0
  positions = strategy.closedPositions
  for pos in positions:
    profitLoss += pos.profitLoss
    totalFees += pos.totalFees
    totalTrades += len(pos.trades)
  
  logTrades(positions)
  
  print ("\nGross Profit/loss: {}".format(profitLoss))
  print ("Fees: {}".format(totalFees))
  print ("Net Profit/loss: {}".format(profitLoss - totalFees))

  print ("{} Positions | {} Trades".format(len(positions), totalTrades))

