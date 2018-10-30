def execOffline(candles, trades, strategy):
  currentTrade = 0

  for candle in candles:
    while currentTrade < len(trades) and trades[currentTrade]['mts'] < candle['mts']:
      strategy.onTrade(trades[currentTrade])
      currentTrade += 1

    strategy.onCandle(candle)
