def candleMarketDataKey(candle):
  return '%s-%s' % (candle['symbol'], candle['tf'])

class Strategy:
  def __init__(self, backtesting = False):
    self.marketData = {}
    self.positions = {}
    self.candlePrice = 'close'
    self.backtesting = backtesting

  def indicatorValues(self):
    values = {}

    for key in self.indicators:
      values[key] = self.indicators[key].v()
    
    return values

  def indicatorsReady(self):
    for key in self.indicators:
      if not self.indicators[key].ready():
        return False
  
    return True

  def addIndicatorData(self, dataType, data):
    for key in self.indicators:
      i = self.indicators[key]
  
      if i.dataType == '*' or i.dataType == dataType:
        if i.dataKey == '*':
          i.add(data)
        else:
          i.add(data[i.dataKey])

  def updateIndicatorData(self, dataType, data):
    for key in self.indicators:
      i = self.indicators[key]
  
      if i.dataType == '*' or i.dataType == dataType:
        if i.dataKey == '*':
          i.update(data)
        else:
          i.update(data[i.dataKey])

  def addCandleData(self, candle):
    dataKey = candleMarketDataKey(candle)

    if dataKey in self.marketData:
      self.marketData[dataKey].append(candle)
    else:
      self.marketData[dataKey] = []

  def updateCandleData(self, candle):
    dataKey = candleMarketDataKey(candle)

    if dataKey in self.marketData:
      self.marketData[dataKey][-1] = candle
    else:
      self.marketData[dataKey] = [candle]
 
  def onCandle(self, candle):
    self.addIndicatorData('candle', candle)
    candle['iv'] = self.indicatorValues()
    self.addCandleData(candle)

    if self.indicatorsReady():
      self.onPriceUpdate({
        'mts': candle['mts'],
        'price': candle[self.candlePrice],
        'symbol': candle['symbol'],
        'candle': candle,
        'type': 'candle'
      })

  def onSeedCandle(self, candle):
    self.addIndicatorData('candle', candle)
    candle['iv'] = self.indicatorValues()
    self.addCandleData(candle)

  def onCandleUpdate(self, candle):
    self.updateIndicatorData('candle', candle)
    candle['iv'] = self.indicatorValues()
    self.updateCandleData(candle)

    if self.indicatorsReady():
      self.onPriceUpdate({
        'mts': candle['mts'],
        'price': candle[self.candlePrice],
        'symbol': candle['symbol'],
        'candle': candle,
        'type': 'candle'
      })
  
  def onSeedCandleUpdate(self, candle):
    self.updateIndicatorData('candle', candle)

  def onTrade(self, trade):
    price = trade['price']
    self.updateIndicatorData('trade', price)

    if self.indicatorsReady():
      self.onPriceUpdate({
        'mts': trade['mts'],
        'price': price,
        'symbol': trade['symbol'],
        'candle': trade,
        'type': 'candle'
      })

  def onSeedTrade(self, trade):
    self.updateIndicatorData('trade', trade['price'])

  def onPriceUpdate(self, update):
    symbol = update['symbol']

    # TODO: Handle stops/targets

    if symbol not in self.positions:
      self.onEnter(update)
    else:
      symPosition = self.positions[symbol]
      amount = symPosition['amount']

      self.onUpdate(update)

      if amount > 1:
        self.onUpdateLong(update)
      else:
        self.onUpdateShort(update)

  def onEnter(self, update):
    pass

  def onUpdate(self, update):
    pass

  def onUpdateLong(self, update):
    pass

  def onUpdateShort(self, update):
    pass

  def getPosition(self, symbol):
    return self.positions.get(symbol)
  
  def openShortPositionMarket(self, params):
    sym = params.get('symbol')
    pos = self.getPosition(sym)

    if pos: # TODO: Throw exception or use logging facility
      print('position already exists for symbol %s' % (sym))
      return
    
    # TODO

    print('open short position')
    pass

  def openLongPositionMarket(self, params):
    sym = params.get('symbol')
    pos = self.getPosition(sym)

    if pos: # TODO: Throw exception or use logging facility
      print('position already exists for symbol %s' % (sym))
      return
    
    # TODO

    print('open long position')
    pass

  def closePositionMarket(self, params):
    pass