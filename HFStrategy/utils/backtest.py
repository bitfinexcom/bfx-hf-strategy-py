def execOffline(candles, trades, strategy):
  currentTrade = 0

  for candle in candles:
    while currentTrade < len(trades) and trades[currentTrade]['mts'] < candle['mts']:
      strategy.onTrade(trades[currentTrade])
      currentTrade += 1

    strategy.onCandle(candle)

  print ("\nBacktesting complete: \n")

  # TODO: calculate fees and averages ect...
  # TODO: calculate profit and loss correctly

  profitLoss = 0
  for pos in strategy.closedPositions:
    print (pos)

    if pos.amount < 0:
      profitLoss -= pos.price
    else:
      profitLoss += pos.price
  
  print ("\nProfit/loss: {}".format(profitLoss))
