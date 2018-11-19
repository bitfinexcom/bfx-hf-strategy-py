import logging
from enum import Enum
from .Position import Position
from ..utils.CustomLogger import CustomLogger

# Simple wrapper to log the calling of a function
# to enable set the logger to debug mode
def logfunc(func):
    async def wrapper(*args, **kwargs):
      args[0].logger.debug("['{0}'] params: {1} kwargs: {2}".
                           format(func.__name__, args, kwargs))
      return await func(*args, **kwargs)
    return wrapper

class PositionError(Exception):
  ''' 
  An Error that is thrown whenever there is a problem with opening,
  creating or updating a position.
  '''
  def __init__(self, message, errors=None):
        # Pass the message to the base class
        super().__init__(message)
        self.errors = errors

MARKET = 'MARKET'
EXCHANGE_MARKET = 'EXCHANGE MARKET'
LIMIT = 'LIMIT'
EXCHANGE_LIMIT = 'EXCHANGE LIMIT'

class PositionManager(object):

  ############################
  # Close Position functions #
  ############################

  @logfunc
  async def closePosition(self, *args, **kwargs):
    return await self.closePositionWithOrder(*args, **kwargs)
  
  @logfunc
  async def closeOpenPositions(self):
    openPositions = list(self.positions.values())
    count = len(openPositions)
    # TODO batch close
    for pos in openPositions:
      price, mts = self.getLastPrice(pos.symbol)
      await self.closePositionMarket(
          symbol=pos.symbol, price=price, mtsCreate=mts, tag='Close all positions')
    self.logger.trade('CLOSED_ALL {} open positions.'.format(count))
  
  @logfunc
  async def closePositionLimit(self, *args, **kwargs):
    orderType = LIMIT if hasattr(self, 'margin') else EXCHANGE_LIMIT
    return await self.closePosition(*args, **kwargs, market_type=orderType)

  @logfunc
  async def closePositionMarket(self, *args, **kwargs):
    orderType = MARKET if hasattr(self, 'margin') else EXCHANGE_MARKET
    return await self.closePosition(*args, **kwargs, market_type=orderType)

  @logfunc
  async def closePositionWithOrder(self, price, mtsCreate, symbol=None,
      market_type=None, **kwargs):
    symbol = symbol or self.symbol
    position = self.getPosition(symbol)
  
    if position == None:
      raise PositionError('No position exists for %s' % (symbol))

    amount = position.amount * -1

    async def callback(order, trade):
      position.addTrade(trade)
      position.close()
      self.removePosition(position)
      self.logger.info("Position closed:")
      self.logger.trade("CLOSED " + str(trade))
      await self.onOrderFill({ trade: trade, order: order })
      await self.onPositionClose({
        'position': position,
        'order': order,
        'trade': trade
      })

    await self.OrderManager.submitTrade(symbol, price, amount,
      mtsCreate, market_type, onComplete=callback, **kwargs)

  ###########################
  # Open Position functions #
  ###########################

  @logfunc
  async def openPosition(self, *args, **kwargs):
    return await self.openPositionWithOrder(*args, **kwargs)

  @logfunc
  async def openShortPosition(self, amount, *args, **kwargs):
    return await self.openPosition(amount=-amount, *args, **kwargs)

  @logfunc
  async def openLongPosition(self, *args, **kwargs):
    return await self.openPosition(*args, **kwargs)

  @logfunc
  async def openPositionLimit(self, *args, **kwargs):
    orderType = LIMIT if hasattr(self, 'margin') else EXCHANGE_LIMIT
    return await self.openPosition(market_type=orderType, *args, **kwargs)

  @logfunc
  async def openPositionMarket(self, *args, **kwargs):
    orderType = MARKET if hasattr(self, 'margin') else EXCHANGE_MARKET
    return await self.openPosition(market_type=orderType, *args, **kwargs)

  @logfunc
  async def openPositionWithOrder(self, amount, price, mtsCreate, symbol=None, 
      stop=None, target=None, tag='', market_type=None, **kwargs):
    symbol = symbol or self.symbol
    # check for open positions
    if self.getPosition(symbol) != None:
      raise PositionError('A position already exists for %s' % (symbol))

    async def callback(order, trade):
      position = Position(symbol, stop, target, tag)
      position.addTrade(trade)
      self.addPosition(position)
      self.logger.info("New Position opened:")
      self.logger.trade("OPENED " + str(trade))
      #TODO - batch these up
      await self.onOrderFill({ trade: trade, order: order })
      await self.onPositionUpdate({
        'position': position,
        'order': order,
        'trade': trade
      })

    await self.OrderManager.submitTrade(symbol, price, amount,
        mtsCreate, market_type, onComplete=callback, **kwargs)

  @logfunc
  async def openShortPositionMarket(self, amount, *args, **kwargs):
    return await self.openPositionMarket(amount=-amount, *args, **kwargs)

  @logfunc
  async def openShortPositionLimit(self, amount, *args, **kwargs):
    return await self.openPositionMarket(amount=-amount, *args, **kwargs)

  @logfunc
  async def openLongPositionMarket(self, *args, **kwargs):
    return await self.openPositionMarket(*args, **kwargs)

  @logfunc
  async def openLongPositionLimit(self, *args, **kwargs):
    return await self.openPositionLimit(*args, **kwargs)

  #############################
  # Update Position functions #
  #############################

  @logfunc
  async def updatePosition(self, *args, **kwargs):
    return await self.updatePositionWithOrder(*args, **kwargs)

  @logfunc
  async def updateShortPosition(self, amount, *args, **kwargs):
    return await self.updatePosition(amount=amount, *args, **kwargs)

  @logfunc
  async def updateLongPosition(self, *args, **kwargs):
    return await self.updatePosition(*args, **kwargs)

  @logfunc
  async def updateLongPositionLimit(self, *args, **kwargs):
    orderType = LIMIT if hasattr(self, 'margin') else EXCHANGE_LIMIT
    return await self.updatePosition(market_type=orderType, *args, **kwargs)

  @logfunc
  async def updateLongPositionMarket(self, *args, **kwargs):
    orderType = MARKET if hasattr(self, 'margin') else EXCHANGE_MARKET
    return await self.updatePosition(market_type=orderType, *args, **kwargs)

  @logfunc
  async def updatePositionLimit(self, *args, **kwargs):
    orderType = LIMIT if hasattr(self, 'margin') else EXCHANGE_LIMIT
    return await self.updatePosition(market_type=orderType, *args, **kwargs)

  @logfunc
  async def updatePositionMarket(self, *args, **kwargs):
    orderType = MARKET if hasattr(self, 'margin') else EXCHANGE_MARKET
    return await self.updatePosition(market_type=orderType, *args, **kwargs)

  @logfunc
  async def updatePositionWithOrder(self, price, amount, mtsCreate, symbol=None,
      market_type=None, **kwargs):
    symbol = symbol or self.symbol
    position = self.getPosition(symbol)

    # check for open positions
    if self.getPosition(symbol) == None:
      raise PositionError('No position exists for %s' % (symbol))

    async def callback(order, trade):
      position.addTrade(trade)
      self.logger.info("Position updated:")
      self.logger.trade("UPDATED POSITION " + str(trade))
      await self.onOrderFill({ trade: trade, order: order })
      await self.onPositionUpdate({
        'position': position,
        'order': order,
        'trade': trade
      })

    await self.OrderManager.submitTrade(symbol, price, amount,
      mtsCreate, market_type, tag='Update position', onComplete=callback, **kwargs)
  
  @logfunc
  async def updateShortPositionLimit(self, amount, *args, **kwargs):
    return await self.updatePosition(amount=-amount, *args, **kwargs)
  
  @logfunc
  async def updateShortPositionMarket(self, amount, *args, **kwargs):
    return await self.updatePosition(amount=-amount, *args, **kwargs)

  ############################
  # Other Position functions #
  ############################

  def setPositionStop(self, stop, symbol):
    position = self.getPosition(symbol or self.symbol)
    position.stop = stop
