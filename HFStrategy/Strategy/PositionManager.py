import logging
from enum import Enum
from .Position import Position
from ..utils.CustomLogger import CustomLogger
from ..models import Events

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
  async def close_position(self, *args, **kwargs):
    return await self.close_position_with_order(*args, **kwargs)
  
  @logfunc
  async def close_open_positions(self):
    open_positions = list(self.positions.values())
    count = len(open_positions)
    # TODO batch close
    for pos in open_positions:
      update = self.get_last_price_update(pos.symbol)
      await self.close_position_market(
          symbol=pos.symbol, mtsCreate=update.mts, tag='Close all positions')
    self.logger.trade('CLOSED_ALL {} open positions.'.format(count))
  
  @logfunc
  async def close_position_limit(self, *args, **kwargs):
    orderType = LIMIT if hasattr(self, 'margin') else EXCHANGE_LIMIT
    return await self.close_position(*args, **kwargs, market_type=orderType)

  @logfunc
  async def close_position_market(self, *args, **kwargs):
    orderType = MARKET if hasattr(self, 'margin') else EXCHANGE_MARKET
    price = self._market_price()
    return await self.close_position(*args, **kwargs, price=price, market_type=orderType)

  @logfunc
  async def close_position_with_order(self, price, mtsCreate, symbol=None,
      market_type=None, **kwargs):
    symbol = symbol or self.symbol
    position = self.get_position(symbol)
  
    if position == None:
      raise PositionError('No position exists for %s' % (symbol))

    amount = position.amount * -1

    async def callback(order, trade):
      position.addTrade(trade)
      position.close()
      self.remove_position(position)
      self.logger.info("Position closed:")
      self.logger.trade("CLOSED " + str(trade))
      await self._emit(Events.ON_ORDER_FILL, { trade: trade, order: order })
      await self._emit(Events.ON_POSITION_CLOSE, {
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
  async def open_position(self, *args, **kwargs):
    return await self.open_position_with_order(*args, **kwargs)

  @logfunc
  async def open_short_position(self, amount, *args, **kwargs):
    return await self.open_position(amount=-amount, *args, **kwargs)

  @logfunc
  async def open_long_position(self, *args, **kwargs):
    return await self.open_position(*args, **kwargs)

  @logfunc
  async def open_position_limit(self, *args, **kwargs):
    orderType = LIMIT if hasattr(self, 'margin') else EXCHANGE_LIMIT
    return await self.open_position(market_type=orderType, *args, **kwargs)

  @logfunc
  async def open_position_market(self, *args, **kwargs):
    orderType = MARKET if hasattr(self, 'margin') else EXCHANGE_MARKET
    price = self._market_price()
    return await self.open_position(market_type=orderType, price=price, *args, **kwargs)

  @logfunc
  async def open_position_with_order(self, amount, price, mtsCreate, symbol=None, 
      stop=None, target=None, tag='', market_type=None, **kwargs):
    symbol = symbol or self.symbol
    # check for open positions
    if self.get_position(symbol) != None:
      raise PositionError('A position already exists for %s' % (symbol))

    async def callback(order, trade):
      position = Position(symbol, stop, target, tag)
      position.addTrade(trade)
      self.add_position(position)
      self.logger.info("New Position opened:")
      self.logger.trade("OPENED " + str(trade))
      #TODO - batch these up
      await self._emit(Events.ON_ORDER_FILL, { trade: trade, order: order })
      await self._emit(Events.ON_POSITION_UPDATE, {
        'position': position,
        'order': order,
        'trade': trade
      })
    await self.OrderManager.submitTrade(symbol, price, amount,
        mtsCreate, market_type, onComplete=callback, **kwargs)

  @logfunc
  async def open_short_position_market(self, amount, *args, **kwargs):
    return await self.open_position_market(amount=-amount, *args, **kwargs)

  @logfunc
  async def open_short_position_limit(self, amount, *args, **kwargs):
    return await self.open_position_market(amount=-amount, *args, **kwargs)

  @logfunc
  async def open_long_position_market(self, *args, **kwargs):
    return await self.open_position_market(*args, **kwargs)

  @logfunc
  async def open_long_position_limit(self, *args, **kwargs):
    return await self.open_position_limit(*args, **kwargs)

  #############################
  # Update Position functions #
  #############################

  @logfunc
  async def update_position(self, *args, **kwargs):
    return await self.update_position_with_order(*args, **kwargs)

  @logfunc
  async def update_short_position(self, amount, *args, **kwargs):
    return await self.update_position(amount=amount, *args, **kwargs)

  @logfunc
  async def update_long_position(self, *args, **kwargs):
    return await self.update_position(*args, **kwargs)

  @logfunc
  async def update_long_position_limit(self, *args, **kwargs):
    orderType = LIMIT if hasattr(self, 'margin') else EXCHANGE_LIMIT
    return await self.update_position(market_type=orderType, *args, **kwargs)

  @logfunc
  async def update_long_position_market(self, *args, **kwargs):
    orderType = MARKET if hasattr(self, 'margin') else EXCHANGE_MARKET
    price = self._market_price()
    return await self.update_position(market_type=orderType, price=price, *args, **kwargs)

  @logfunc
  async def update_position_limit(self, *args, **kwargs):
    orderType = LIMIT if hasattr(self, 'margin') else EXCHANGE_LIMIT
    return await self.update_position(market_type=orderType, *args, **kwargs)

  @logfunc
  async def update_position_market(self, *args, **kwargs):
    orderType = MARKET if hasattr(self, 'margin') else EXCHANGE_MARKET
    price = self._market_price()
    return await self.update_position(market_type=orderType, price=price, *args, **kwargs)

  @logfunc
  async def update_position_with_order(self, price, amount, mtsCreate, symbol=None,
      market_type=None, **kwargs):
    symbol = symbol or self.symbol
    position = self.get_position(symbol)

    # check for open positions
    if self.get_position(symbol) == None:
      raise PositionError('No position exists for %s' % (symbol))

    async def callback(order, trade):
      position.addTrade(trade)
      self.logger.info("Position updated:")
      self.logger.trade("UPDATED POSITION " + str(trade))
      await self._emit(Events.ON_ORDER_FILL, { trade: trade, order: order })
      await self._emit(Events.ON_POSITION_UPDATE, {
        'position': position,
        'order': order,
        'trade': trade
      })
    await self.OrderManager.submitTrade(symbol, price, amount,
      mtsCreate, market_type, tag='Update position', onComplete=callback, **kwargs)

  @logfunc
  async def update_short_position_limit(self, amount, *args, **kwargs):
    return await self.update_position_limit(amount=-amount, *args, **kwargs)

  @logfunc
  async def update_short_position_market(self, amount, *args, **kwargs):
    return await self.update_position_market(amount=-amount, *args, **kwargs)

  ############################
  # Other Position functions #
  ############################

  def setPositionStop(self, stop, symbol):
    position = self.get_position(symbol or self.symbol)
    position.stop = stop

  def _market_price(self):
    ## market price does not matter when submitting orders to bfx
    ## but this helps the offline backtests stay in sync
    return self.get_last_price_update(self.symbol).price
