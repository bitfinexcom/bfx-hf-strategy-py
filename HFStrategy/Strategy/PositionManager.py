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
  EXCHNAGE_MARKET = 2
  LIMIT = 3
  EXCHNAGE_LIMIT = 4

class PositionManager(object):

  ############################
  # Close Position functions #
  ############################

  @logfunc
  def closePosition(self, params):
    self.closePositionWithOrder(params)
  
  @logfunc
  def closeOpenPositions(self):
    positions = self.positions.items()
    for key, pos in positions:
      def close_pos(self):
        price, mts = self.getLastPrice(pos.symbol)
        self.closePositionMarket({
          "symbol": pos.symbol,
          "price": price,
          "mts": mts
        })
      self._startNewThread(close_pos)
    print ("Boom")
    self.logger.trade('CLOSED_ALL {} open positions.'.format(len(positions)))
  
  @logfunc
  def closePositionLimit(self, params):
    params['type'] = OrderType.LIMIT if hasattr(self, 'margin') else OrderType.EXCHNAGE_LIMIT
    return self.closePosition(params)

  @logfunc
  def closePositionMarket(self, params):
    params['type'] = OrderType.MARKET if hasattr(self, 'margin') else OrderType.EXCHNAGE_MARKET
    return self.closePosition(params)

  @logfunc
  def closePositionWithOrder(self, params):
    symbol = params.get('symbol', self.symbol)
    prevPosition = self.getPosition(symbol)

    if symbol is None:
      raise KeyError('Expected paramater value \'symbol\' but not present.')
    if self.getPosition == None:
      raise PositionError('No position exists for %s' % (symbol))
    
    amount = prevPosition.amount * -1
    def submit(self):
      order, trade = self.OrderManager.submitTrade(params)
      self.removePosition(prevPosition)
      self.logger.info("Position closed:")
      self.logger.trade("CLOSED " + str(prevPosition))
      self.onOrderFill({ trade: trade, order: order })
      self.onPositionClose({
        'position': prevPosition,
        'order': order,
        'trade': trade
      })
    self._startNewThread(submit)

  ###########################
  # Open Position functions #
  ###########################

  @logfunc
  def openPosition(self, params):
    return self.openPositionWithOrder(params)

  @logfunc
  def openShortPosition(self, params):
    params['amount'] = -params.get('amount')
    return self.openPosition(params)

  @logfunc
  def openLongPosition(self, params):
    return self.openPosition(params)

  @logfunc
  def openPositionLimit(self, params):
    params['type'] = OrderType.LIMIT if hasattr(self, 'margin') else OrderType.EXCHNAGE_LIMIT
    return self.openPosition(params)

  @logfunc
  def openPositionMarket(self, params):
    params['type'] = OrderType.MARKET if hasattr(self, 'margin') else OrderType.EXCHNAGE_MARKET
    return self.openPosition(params)

  @logfunc
  def openPositionWithOrder(self, params):
    symbol = params.get('symbol', self.symbol)
    amount = params.get('amount')
    stop = params.get('stop', None)
    target = params.get('target', None)
    tag = params.get('tag', None)
    if symbol is None:
      raise KeyError('Expected paramater value \'symbol\' but not present.')
    # check for open positions
    if self.getPosition(symbol) != None:
      raise PositionError('A position already exists for %s' % (symbol))
    # create submit functions so its easier to pass onto
    # a new thread
    def submit(self):
      order, trade = self.OrderManager.submitTrade(params)
      position = Position(symbol, amount, order.priceAvg,
                          [trade], stop, target, tag)
      self.addPosition(position)
      self.logger.info("New Position opened:")
      self.logger.trade("OPENED " + str(position))
      self.onOrderFill({ trade: trade, order: order })
      self.onPositionUpdate({
        'position': position,
        'order': order,
        'trade': trade
      })
    self._startNewThread(submit)

  @logfunc
  def openShortPositionMarket(self, params):
    params['amount'] = -params.get('amount')
    return self.openPositionMarket(params)

  @logfunc
  def openShortPositionLimit(self, params):
    params['amount'] = -params.get('amount')
    return self.openPositionMarket(params)

  @logfunc
  def openLongPositionMarket(self, params):
    return self.openPositionMarket(params)

  @logfunc
  def openLongPositionLimit(self, params):
    return self.openPositionLimit(params)

  #############################
  # Update Position functions #
  #############################

  @logfunc
  def updatePosition(self, params):
    return self.updatePositionWithOrder(params)

  @logfunc
  def updateShortPosition(self, params):
    params['amount'] = -params.get('amount')
    return self.updatePosition(params)

  @logfunc
  def updateLongPosition(self, params):
    return self.updatePosition(params)

  @logfunc
  def updateLongPositionLimit(self, params):
    params['type'] = OrderType.LIMIT if hasattr(self, 'margin') else OrderType.EXCHNAGE_LIMIT
    return self.updatePosition(params)

  @logfunc
  def updateLongPositionMarket(self, params):
    params['type'] = OrderType.MARKET if hasattr(self, 'margin') else OrderType.EXCHNAGE_MARKET
    return self.updatePosition(params)

  @logfunc
  def updatePositionLimit(self, params):
    params['type'] = OrderType.LIMIT if hasattr(self, 'margin') else OrderType.EXCHNAGE_LIMIT
    return self.updatePosition(params)

  @logfunc
  def updatePositionMarket(self, params):
    params['type'] = OrderType.MARKET if hasattr(self, 'margin') else OrderType.EXCHNAGE_MARKET
    return self.updatePosition(params)

  @logfunc
  def updatePositionWithOrder(self, params):
    symbol = params.get('symbol', self.symbol)
    position = self.getPosition(symbol)
    amount = params.get('amount', position.amount)
    price = params.get('price', position.price)
    stop = params.get('stop', position.stop)
    target = params.get('target', position.target)
    tag = params.get('tag', position.tag)

    if symbol is None:
      raise KeyError('Expected paramater value \'symbol\' but not present.')
    # check for open positions
    if self.getPosition(symbol) == None:
      raise PositionError('No position exists for %s' % (symbol))

    # Throw if order closes position?
    def update(self):
      order, trade = self.OrderManager.submitTrade(params)
      newPosition = Position(symbol, amount, order.priceAvg,
                          [trade], stop, target, tag)
      self.addPosition(newPosition)
      self.logger.info("Position updated:")
      self.logger.trade("UPDATED FROM" + str(position))
      self.logger.trade("UPDATED TO" + str(newPosition))
      self.onOrderFill({ trade: trade, order: order })
      self.onPositionUpdate({
        'position': newPosition,
        'order': order,
        'trade': trade
      })
    self._startNewThread(update)
  
  @logfunc
  def updateShortPositionLimit(self, params):
    params['amount'] = -params.get('amount')
    return self.updatePosition(params)
  
  @logfunc
  def updateShortPositionMarket(self, params):
    params['amount'] = -params.get('amount')
    return self.updatePosition(params)

  ############################
  # Other Position functions #
  ############################

  def setPositionStop(self, stop, symbol):
    position = self.getPosition(symbol or self.symbol)
    position.stop = stop
