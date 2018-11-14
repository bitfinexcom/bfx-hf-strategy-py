import logging
from enum import Enum
from .Position import Position
from ..utils.CustomLogger import CustomLogger

# Simple wrapper to log the calling of a function
# to enable set the logger to debug mode
def logfunc(func):
    def wrapper(*args, **kwargs):
      args[0].logger.debug("['{0}'] params: {1} kwargs: {2}".
                           format(func.__name__, args, kwargs))
      return func(*args, **kwargs)
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

class OrderType(Enum):
  '''
  An Enum used to represent the diffrent types of orders that 
  are possible.
  '''
  MARKET = 1
  EXCHANGE_MARKET = 2
  LIMIT = 3
  EXCHANGE_LIMIT = 4

class PositionManager(object):

  ############################
  # Close Position functions #
  ############################

  @logfunc
  def closePosition(self, *args, **kwargs):
    self.closePositionWithOrder(*args, **kwargs)
  
  @logfunc
  def closeOpenPositions(self):
    openPositions = list(self.positions.values())
    count = len(openPositions)
    for pos in openPositions:
      price, mts = self.getLastPrice(pos.symbol)
      self.closePositionMarket(
          symbol=pos.symbol, price=price, mtsCreate=mts, tag='Close all positions')
    self.logger.trade('CLOSED_ALL {} open positions.'.format(count))
  
  @logfunc
  def closePositionLimit(self, *args, **kwargs):
    orderType = OrderType.LIMIT if hasattr(self, 'margin') else OrderType.EXCHANGE_LIMIT
    return self.closePosition(*args, **kwargs, type=orderType)

  @logfunc
  def closePositionMarket(self, *args, **kwargs):
    orderType = OrderType.MARKET if hasattr(self, 'margin') else OrderType.EXCHANGE_MARKET
    return self.closePosition(*args, **kwargs, type=orderType)

  @logfunc
  def closePositionWithOrder(self, price, mtsCreate, symbol=None, **kwargs):
    symbol = symbol or self.symbol
    position = self.getPosition(symbol)
  
    if position == None:
      raise PositionError('No position exists for %s' % (symbol))

    amount = position.amount * -1
    def submit(self):
      order, trade = self.OrderManager.submitTrade(symbol, price, amount,
          mtsCreate, **kwargs)
      position.addTrade(trade)
      position.close()
      self.removePosition(position)
      self.logger.info("Position closed:")
      self.logger.trade("CLOSED " + str(trade))
      self.onOrderFill({ trade: trade, order: order })
      self.onTrade(trade)
      self.onPositionClose({
        'position': position,
        'order': order,
        'trade': trade
      })
    self._startNewThread(submit)

  ###########################
  # Open Position functions #
  ###########################

  @logfunc
  def openPosition(self, *args, **kwargs):
    return self.openPositionWithOrder(*args, **kwargs)

  @logfunc
  def openShortPosition(self, amount, *args, **kwargs):
    return self.openPosition(amount=-amount, *args, **kwargs)

  @logfunc
  def openLongPosition(self, *args, **kwargs):
    return self.openPosition(*args, **kwargs)

  @logfunc
  def openPositionLimit(self, *args, **kwargs):
    orderType = OrderType.LIMIT if hasattr(self, 'margin') else OrderType.EXCHANGE_LIMIT
    return self.openPosition(type=orderType, *args, **kwargs)

  @logfunc
  def openPositionMarket(self, *args, **kwargs):
    orderType = OrderType.MARKET if hasattr(self, 'margin') else OrderType.EXCHANGE_MARKET
    return self.openPosition(type=orderType, *args, **kwargs)

  @logfunc
  def openPositionWithOrder(self, amount, price, mtsCreate, symbol=None, 
      stop=None, target=None, tag='', **kwargs):
    symbol = symbol or self.symbol
    # check for open positions
    if self.getPosition(symbol) != None:
      raise PositionError('A position already exists for %s' % (symbol))

    # create submit functions so its easier to pass onto
    # a new thread
    def submit(self):
      order, trade = self.OrderManager.submitTrade(symbol, price, amount,
          mtsCreate, **kwargs)
      position = Position(symbol, stop, target, tag)
      position.addTrade(trade)
      self.addPosition(position)
      self.logger.info("New Position opened:")
      self.logger.trade("OPENED " + str(trade))
      self.onOrderFill({ trade: trade, order: order })
      self.onTrade(trade)
      self.onPositionUpdate({
        'position': position,
        'order': order,
        'trade': trade
      })
    self._startNewThread(submit)

  @logfunc
  def openShortPositionMarket(self, amount, *args, **kwargs):
    return self.openPositionMarket(amount=-amount, *args, **kwargs)

  @logfunc
  def openShortPositionLimit(self, amount, *args, **kwargs):
    return self.openPositionMarket(amount=-amount, *args, **kwargs)

  @logfunc
  def openLongPositionMarket(self, *args, **kwargs):
    return self.openPositionMarket(*args, **kwargs)

  @logfunc
  def openLongPositionLimit(self, *args, **kwargs):
    return self.openPositionLimit(*args, **kwargs)

  #############################
  # Update Position functions #
  #############################

  @logfunc
  def updatePosition(self, *args, **kwargs):
    return self.updatePositionWithOrder(*args, **kwargs)

  @logfunc
  def updateShortPosition(self, amount, *args, **kwargs):
    return self.updatePosition(amount=amount, *args, **kwargs)

  @logfunc
  def updateLongPosition(self, *args, **kwargs):
    return self.updatePosition(*args, **kwargs)

  @logfunc
  def updateLongPositionLimit(self, *args, **kwargs):
    orderType = OrderType.LIMIT if hasattr(self, 'margin') else OrderType.EXCHANGE_LIMIT
    return self.updatePosition(type=orderType, *args, **kwargs)

  @logfunc
  def updateLongPositionMarket(self, *args, **kwargs):
    orderType = OrderType.MARKET if hasattr(self, 'margin') else OrderType.EXCHANGE_MARKET
    return self.updatePosition(type=orderType, *args, **kwargs)

  @logfunc
  def updatePositionLimit(self, *args, **kwargs):
    orderType = OrderType.LIMIT if hasattr(self, 'margin') else OrderType.EXCHANGE_LIMIT
    return self.updatePosition(type=orderType, *args, **kwargs)

  @logfunc
  def updatePositionMarket(self, *args, **kwargs):
    orderType = OrderType.MARKET if hasattr(self, 'margin') else OrderType.EXCHANGE_MARKET
    return self.updatePosition(type=orderType, *args, **kwargs)

  @logfunc
  def updatePositionWithOrder(self, price, amount, mtsCreate, symbol=None, **kwargs):
    symbol = symbol or self.symbol
    position = self.getPosition(symbol)

    # check for open positions
    if self.getPosition(symbol) == None:
      raise PositionError('No position exists for %s' % (symbol))

    def update(self):
      order, trade = self.OrderManager.submitTrade(symbol, price, amount,
          mtsCreate, tag='Update position' **kwargs)
      position.addTrade(trade)
      self.logger.info("Position updated:")
      self.logger.trade("UPDATED POSITION " + str(trade))
      self.onOrderFill({ trade: trade, order: order })
      self.onTrade(trade)
      self.onPositionUpdate({
        'position': position,
        'order': order,
        'trade': trade
      })
    self._startNewThread(update)
  
  @logfunc
  def updateShortPositionLimit(self, amount, *args, **kwargs):
    return self.updatePosition(amount=-amount, *args, **kwargs)
  
  @logfunc
  def updateShortPositionMarket(self, amount, *args, **kwargs):
    return self.updatePosition(amount=-amount, *args, **kwargs)

  ############################
  # Other Position functions #
  ############################

  def setPositionStop(self, stop, symbol):
    position = self.getPosition(symbol or self.symbol)
    position.stop = stop
