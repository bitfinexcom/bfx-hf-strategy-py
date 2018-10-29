import logging
from enum import Enum
from .orders import submitTrade

# Simple wrapper to log the calling of a function
# to enable set the logger to debug mode
def logfunc(func):
    def wrapper(*args, **kwargs):
      logging.debug("['{0}'] params: {1} kwargs: {2}".
                    format(func.__name__, args, kwargs))
      return func(*args, **kwargs)
    return wrapper

class PositionError(Exception):
  ''' 
  An Error that is thrown whenever there is a problem with opening,
  creating or updating a position.
  '''
  def __init__(self, message, errors):
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

class Position(object):

  ############################
  # Close Position functions #
  ############################

  @logfunc
  def closePosition(self, params):
    # some state usage here
    pass
  
  @logfunc
  def closeOpenPositions(self, params):
    pass
  
  @logfunc
  def closePositionLimit(self, params):
    pass
  
  @logfunc
  def closePositionLimit(self, params):
    pass

  @logfunc
  def closePositionMarket(self, params):
    pass

  @logfunc
  def closePositionWithOrder(self, params):
    pass

  ###########################
  # Open Position functions #
  ###########################

  @logfunc
  def openPosition(self, params):
    return self.openPositionWithOrder(params)

  @logfunc
  def openShortPosition(self, params):
    pass

  @logfunc
  def openLongPosition(self, params):
    pass

  @logfunc
  def openPositionLimit(self, params):
    pass

  @logfunc
  def openPositionMarket(self, params):
    params['type'] = OrderType.MARKET if hasattr(self, 'margin') else OrderType.EXCHNAGE_MARKET
    return self.openPosition(params)

  @logfunc
  def openPositionWithOrder(self, params):
    symbol = params.get('symbol', self.symbol)
    if symbol is None:
      raise KeyError('Expected paramater value \'symbol\' but not present.')
    # check for open positions
    if self.getPosition(symbol) != None:
      raise PositionError('A position already exists for %s' % (sym))
    # create submit functions so its easier to pass onto
    # a new thread
    def submit(self):
      # submit Trade
      # TODO: update state and use real trade/order objects
      # TODO: create position object
      trade, order = submitTrade(None, backtesting=self.backtesting)
      self.onOrderFill(dict({ trade: trade, order: order }))
      self.onPositionUpdate(dict({
        'position': None,
        'order': order,
        'trade': trade
      }))
      # callback on onOrderFill event
      # callback on onPositionOpen event
      logging.info('Opened short position')
      return

    self._startNewThread(submit)

  @logfunc
  def openShortPositionMarket(self, params):
    params['amount'] = -params.get('amount')
    return self.openPositionMarket(params)

  @logfunc
  def openShortPositionLimit(self, params):
    pass

  @logfunc
  def openLongPositionMarket(self, params):
    return self.openPositionMarket(params)

  @logfunc
  def openLongPositionLimit(self, params):
    pass

  #############################
  # Update Position functions #
  #############################

  @logfunc
  def updatePosition(self, params):
    pass

  @logfunc
  def updateShortPosition(self, params):
    pass

  @logfunc
  def updateLongPosition(self, params):
    pass

  @logfunc
  def updateLongPositionLimit(self, params):
    pass

  @logfunc
  def updateLongPositionMarket(self, params):
    pass

  @logfunc
  def updatePositionLimit(self, params):
    pass

  @logfunc
  def updatePositionMarket(self, params):
    pass

  @logfunc
  def updatePositionWithOrder(self, params):
    pass
  
  @logfunc
  def closePositionMarket(self, params):
    pass
  
  @logfunc
  def updateShortPositionLimit(self, params):
    pass
  
  @logfunc
  def updateShortPositionMarket(self, params):
    pass

  ############################
  # Other Position functions #
  ############################

  def createPositionObject(self, params):
    pass
  
  def positionPl(self, params):
    pass

  def setPositionStop(self, params):
    pass

  def throwIfPosition(self, params):
    pass
  
  def withNoPosition(self, params):
    pass
  
  def withPosition(self, params):
    pass
