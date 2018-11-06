import logging
from threading import Thread

from .PositionManager import PositionManager
from .Position import Position
from ..utils.CustomLogger import CustomLogger
from .OrderManager import OrderManager

def candleMarketDataKey(candle):
  return '%s-%s' % (candle['symbol'], candle['tf'])

class Strategy(PositionManager):
  def __init__(self, backtesting = False, symbol='tBTCUSD', logLevel='INFO'):
    self.marketData = {}
    self.positions = {}
    self.lastPrice = {}
    self.closedPositions = []
    self.candlePrice = 'close'
    self.backtesting = backtesting
    self.symbol = symbol
    # initialise custom logger
    self.logger = CustomLogger('HFStrategy', logLevel=logLevel)
    self.OrderManager = OrderManager(backtesting=backtesting, logLevel=logLevel)
    super(Strategy, self).__init__()

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
      dt = i.get_data_type()
      dk = i.get_data_key()
  
      if dt == '*' or dt == dataType:
        if dk == '*':
          i.add(data)
        else:
          i.add(data[dk])

  def updateIndicatorData(self, dataType, data):
    for key in self.indicators:
      i = self.indicators[key]
      dt = i.get_data_type()
      dk = i.get_data_key()
 
      if dt == '*' or dt == dataType:
        if dk == '*':
          i.update(data)
        else:
          i.update(data[dk])

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
  
  def getLastPrice(self, symbol):
    mtsPrice = self.lastPrice[symbol]
    return mtsPrice[0], mtsPrice[1]

  def getPosition(self, symbol):
    return self.positions.get(symbol)

  def addPosition(self, position):
    self.positions[position.symbol] = position
  
  def removePosition(self, position):
    self.logger.debug("Archiving closed position {}".format(position))
    self.closedPositions += [position]
    del self.positions[position.symbol]

  def onCandle(self, candle):
    self.addIndicatorData('candle', candle)
    candle['iv'] = self.indicatorValues()
    self.addCandleData(candle)

    if self.indicatorsReady():
      self._onPriceUpdate({
        'mts': candle['mts'],
        'price': candle[self.candlePrice],
        'symbol': candle['symbol'],
        'candle': candle,
        'type': 'candle'
      })
  
  # Starts a thread with the given parameters
  def _startNewThread(self, func):
    ## multithreading makes backtesting unreliable
    ## since the main thread will continue to process the
    ## backtest data but the threads with orders may take longer
    if self.backtesting:
      # Run on mainthread
      func(self)
    else:
      # Spawn seperate thread
      t = Thread(target=func, args=(self,))
      t.start()

  def _onSeedCandle(self, candle):
    self.addIndicatorData('candle', candle)
    candle['iv'] = self.indicatorValues()
    self.addCandleData(candle)

  def _onCandleUpdate(self, candle):
    self.updateIndicatorData('candle', candle)
    candle['iv'] = self.indicatorValues()
    self.updateCandleData(candle)

    if self.indicatorsReady():
      self._onPriceUpdate({
        'mts': candle['mts'],
        'price': candle[self.candlePrice],
        'symbol': candle['symbol'],
        'candle': candle,
        'type': 'candle'
      })
  
  def _onSeedCandleUpdate(self, candle):
    self.updateIndicatorData('candle', candle)

  def _onSeedTrade(self, trade):
    self.updateIndicatorData('trade', trade['price'])

  def _onPriceUpdate(self, update):
    symbol = update['symbol']
    self.lastPrice[symbol] = (update['price'], update['mts'])
    # TODO: Handle stops/targets
    if symbol not in self.positions:
      self.onEnter(update)
    else:
      symPosition = self.positions[symbol]
      amount = symPosition.amount

      self.onUpdate(update)

      if amount > 0:
        self.onUpdateLong(update)
      else:
        self.onUpdateShort(update)
  
  ############################
  #      Function Hooks      #
  ############################

  def onEnter(self, update):
    pass

  def onUpdate(self, update):
    pass

  def onUpdateLong(self, update):
    pass

  def onUpdateShort(self, update):
    pass

  def onOrderFill(self, params):
    pass

  def onTrade(self, trade):
    pass
  
  def onPositionUpdate(self, params):
    pass

  def onPositionClose(self, params):
    pass
