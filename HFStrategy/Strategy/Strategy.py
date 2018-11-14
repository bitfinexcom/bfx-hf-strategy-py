import logging
import math
import asyncio
from threading import Thread

from .PositionManager import PositionManager
from .Position import Position
from ..utils.CustomLogger import CustomLogger

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
        t = type(data)
        if t is float or t is int:
          if math.isfinite(data):
            i.update(data)
            return
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

  async def onCandle(self, candle):
    print ('On Candle')
    print (candle)
    self.addIndicatorData('candle', candle)
    candle['iv'] = self.indicatorValues()
    self.addCandleData(candle)

    if self.indicatorsReady():
      await self._onPriceUpdate({
        'mts': candle['mts'],
        'price': candle[self.candlePrice],
        'symbol': candle['symbol'],
        'candle': candle,
        'type': 'candle'
      })

  async def onTrade(self, trade):
    print ('On Trade')
    print (trade)
    price = trade['price']
    self.updateIndicatorData('trade', price)

    if self.indicatorsReady():
      await self._onPriceUpdate({
        'mts': trade['mts'],
        'price': price,
        'symbol': trade['symbol'],
        'trade': trade,
        'type': 'trade'
      })

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

  async def _onPriceUpdate(self, update):
    symbol = update['symbol']
    self.lastPrice[symbol] = (update['price'], update['mts'])
    # TODO: Handle stops/targets
    if symbol not in self.positions:
      await self.onEnter(update)
    else:
      symPosition = self.positions[symbol]
      amount = symPosition.amount

      await self.onUpdate(update)

      if amount > 0:
        await self.onUpdateLong(update)
      else:
        await self.onUpdateShort(update)
  
  ############################
  #      Function Hooks      #
  ############################

  async def onEnter(self, update):
    pass

  async def onUpdate(self, update):
    pass

  async def onUpdateLong(self, update):
    pass

  async def onUpdateShort(self, update):
    pass

  async def onOrderFill(self, params):
    pass
  
  async def onPositionUpdate(self, params):
    pass

  async def onPositionClose(self, params):
    pass
