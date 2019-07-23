import logging
import time

from enum import Enum
from .position import Position, ExitOrder
from ..utils.custom_logger import CustomLogger
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
STOP_LIMIT = 'STOP LIMIT'
EXCHANGE_STOP_LIMIT = 'EXCHANGE STOP LIMIT'

MARGIN_ORDERS = [MARKET, LIMIT, STOP_LIMIT]
EXCHANGE_ORDERS = [EXCHANGE_MARKET, EXCHANGE_LIMIT, EXCHANGE_STOP_LIMIT]

class PositionManager(object):

  def __init__(self):
    self.orderManager = None

  async def _process_order_change(self, order):
    symbol = order.symbol
    position = self.get_position(symbol)
    e_type = self.exchange_type
    if not position:
      return
    # ignore exchange if in margin mode
    if (e_type == self.ExchangeType.MARGIN
        and order.type not in MARGIN_ORDERS):
      return
    # ignore margin orders if in exchange mode
    elif (e_type == self.ExchangeType.EXCHANGE
          and order.type not in EXCHANGE_ORDERS):
      return
    position.process_order_update(order)
    # if no value filled then ignore resetting exit order
    if (order.amount_filled == 0):
      return position
    if position.amount != 0:
      # re-create the stop/target order with new amount
      eo = position.exit_order
      newEo = ExitOrder(-position.amount, eo.target, eo.stop, eo.stop_type,
        eo.target_type)
      await self.set_position_exit(position, newEo)
    else:
      # remove stop and target orders
      await self.remove_position_exit_order()
    return position

  async def _process_order_closed(self, order):
    """
    We have to process order closes directly from the websocket
    since a stop loss may have been triggered
    """
    position = await self._process_order_change(order)
    if not position:
      return
    last = self.get_last_price_update(position.symbol)
    # close position
    # TODO: find way to add tag to close
    # order.tag = tag
    if position.amount == 0:
      position.update_with_price(last.price)
      position.close()
      # check if was a stop loss exit
      if position.has_reached_stop(last):
        order.tag = "Stop price reached"
        await self._execute_events(
              Events.ON_POSITION_STOP_REACHED, last, position)
      # check if was a reach target price exit
      if position.has_reached_target(last):
        order.tag = "Target price reached"
        await self._execute_events(
              Events.ON_POSITION_TARGET_REACHED, last, position)
      self._remove_position(position)
      self.logger.info("Position closed:")
      self.logger.trade("CLOSED " + str(order))
      self.logger.position(position)
      await self._emit(Events.ON_POSITION_CLOSE, position)
      await self._emit(Events.ON_ORDER_FILL, order)
    await self._emit(Events.ON_POSITION_UPDATE, position)

  async def _process_order_update(self, order):
    pos = await self._process_order_change(order)
    if not pos:
      return
    await self._emit(Events.ON_POSITION_UPDATE, pos)

  async def _process_order_new(self, order):
    pos = await self._process_order_change(order)
    if not pos:
      return
    await self._emit(Events.ON_POSITION_UPDATE, pos)

  def set_order_manager(self, orderManager):
    self.orderManager = orderManager
    # remove any existing listeners
    self.orderManager.ws.remove_all_listeners("order_new")
    self.orderManager.ws.remove_all_listeners("order_update")
    self.orderManager.ws.remove_all_listeners("order_closed")
    # attach strategy functions
    self.orderManager.ws.on("order_new", self._process_order_new)
    self.orderManager.ws.on("order_update", self._process_order_update)
    self.orderManager.ws.on("order_closed", self._process_order_closed)

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
    orderType = LIMIT if self.exchange_type == self.ExchangeType.MARGIN else EXCHANGE_LIMIT
    return await self.close_position(*args, **kwargs, market_type=orderType)

  @logfunc
  async def close_position_market(self, *args, **kwargs):
    orderType = MARKET if self.exchange_type == self.ExchangeType.MARGIN else EXCHANGE_MARKET
    price = self._market_price()
    return await self.close_position(*args, **kwargs, price=price, market_type=orderType)

  @logfunc
  async def close_position_with_order(self, price, mtsCreate, symbol=None,
      market_type=None, tag="", **kwargs):
    symbol = symbol or self.symbol
    position = self.get_position(symbol)
  
    if position == None:
      raise PositionError('No position exists for %s' % (symbol))

    amount = position.amount * -1

    async def callback(order):
      order.tag = tag
      await self._process_order_closed(order)
    await self._submit_position_trade(position, price, amount, mtsCreate,
      market_type, onClose=callback, **kwargs)


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
    orderType = LIMIT if self.exchange_type == self.ExchangeType.MARGIN else EXCHANGE_LIMIT
    return await self.open_position(market_type=orderType, *args, **kwargs)

  @logfunc
  async def open_position_market(self, *args, **kwargs):
    orderType = MARKET if self.exchange_type == self.ExchangeType.MARGIN else EXCHANGE_MARKET
    price = self._market_price()
    return await self.open_position(market_type=orderType, price=price, *args, **kwargs)

  @logfunc
  async def open_position_with_order(self, amount, price, mtsCreate, symbol=None, 
      stop=None, target=None, tag="", market_type=None, **kwargs):
    """
    Open a new position with the given order specifications

    @param amount: order size: how much you want to buy/sell,
      a negative amount indicates a sell order and positive a buy order
    @param price: the price you want to buy/sell at (must be positive)
    @param mtsCreate
    @param symbol: the name of the symbol i.e 'tBTCUSD
    @param stop
    @param target
    @param tag
    @param market_type
    """
    symbol = symbol or self.symbol
    # check for open positions
    if self.get_position(symbol) != None:
      raise PositionError('A position already exists for %s' % (symbol))
    position = Position(symbol, stop=stop, target=target, tag=tag)
    self._add_position(position)

    async def callback(order):
      order.tag = tag
      position.process_order_update(order)
      self.logger.info("New Position opened:")
      self.logger.trade("OPENED " + str(order))
      self.logger.position(position)
      #TODO - batch these up
      await self._emit(Events.ON_ORDER_FILL, order)
    await self._submit_position_trade(position, price, amount, mtsCreate,
      market_type, tag='Update position', onClose=callback, **kwargs)

  @logfunc
  async def open_short_position_market(self, amount, *args, **kwargs):
    return await self.open_position_market(amount=-amount, *args, **kwargs)

  @logfunc
  async def open_short_position_limit(self, amount, *args, **kwargs):
    return await self.open_position_limit(amount=-amount, *args, **kwargs)

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
    orderType = LIMIT if self.exchange_type == self.ExchangeType.MARGIN else EXCHANGE_LIMIT
    return await self.update_position(market_type=orderType, *args, **kwargs)

  @logfunc
  async def update_long_position_market(self, *args, **kwargs):
    orderType = MARKET if self.exchange_type == self.ExchangeType.MARGIN else EXCHANGE_MARKET
    price = self._market_price()
    return await self.update_position(market_type=orderType, price=price, *args, **kwargs)

  @logfunc
  async def update_position_limit(self, *args, **kwargs):
    orderType = LIMIT if self.exchange_type == self.ExchangeType.MARGIN else EXCHANGE_LIMIT
    return await self.update_position(market_type=orderType, *args, **kwargs)

  @logfunc
  async def update_position_market(self, *args, **kwargs):
    orderType = MARKET if self.exchange_type == self.ExchangeType.MARGIN else EXCHANGE_MARKET
    price = self._market_price()
    return await self.update_position(market_type=orderType, price=price, *args, **kwargs)

  @logfunc
  async def update_position_with_order(self, price, amount, mtsCreate, symbol=None,
      market_type=None, tag="", **kwargs):
    symbol = symbol or self.symbol
    position = self.get_position(symbol)

    # check for open positions
    if self.get_position(symbol) == None:
      raise PositionError('No position exists for %s' % (symbol))

    async def callback(order):
      order.tag = tag
      position.process_order_update(order)
      self.logger.info("Position updated:")
      self.logger.trade("UPDATED POSITION " + str(order))
      self.logger.position(position)
      await self._emit(Events.ON_ORDER_FILL, order)
    await self._submit_position_trade(position, price, amount, mtsCreate, market_type,
      tag='Update position', onClose=callback, **kwargs)

  @logfunc
  async def update_short_position_limit(self, amount, *args, **kwargs):
    return await self.update_position_limit(amount=-amount, *args, **kwargs)

  @logfunc
  async def update_short_position_market(self, amount, *args, **kwargs):
    return await self.update_position_market(amount=-amount, *args, **kwargs)

  ############################
  # Other Position functions #
  ############################

  async def set_position_stop(self, stop, symbol=None, exit_type=None):
    symbol = symbol or self.symbol
    position = self.get_position(symbol)
    target = position.exit_order.target
    target_type = position.exit_order.target_type
    stop_type = exit_type or position.exit_order.stop_type
    eo = ExitOrder(-position.amount, target, stop, stop_type, target_type)
    await self.set_position_exit(position, eo)

  async def set_position_target(self, target, symbol=None, exit_type=None):
    symbol = symbol or self.symbol
    position = self.get_position(symbol)
    stop = position.exit_order.stop
    stop_type = position.exit_order.stop_type
    target_type = exit_type or position.exit_order.target_type
    eo = ExitOrder(-position.amount, target, stop, stop_type, target_type)
    await self.set_position_exit(position, eo)


  async def remove_position_target(self, symbol=None):
    symbol = symbol or self.symbol
    position = self.get_position(symbol)
    eo = ExitOrder(position.exit_order.amount, None,
                  position.exit_order.stop, position.exit_order.stop_type, None)
    await self.set_position_exit(position, eo)

  async def remove_position_stop(self, symbol=None):
    symbol = symbol or self.symbol
    position = self.get_position(symbol)
    eo = ExitOrder(position.exit_order.amount, position.exit_order.target,
                  None, None, position.exit_order.target_type)
    await self.set_position_exit(position, eo)

  async def remove_position_exit_order(self, symbol=None):
    self.logger.info("Removing position exit order.")
    symbol = symbol or self.symbol
    position = self.get_position(symbol)
    eo = ExitOrder(0, None, None)
    await self.set_position_exit(position, eo)

  async def set_position_exit(self, position, new_exit_order):
    self.logger.info("Setting new exit position: {}".format(new_exit_order))
    last = self.get_last_price_update(position.symbol)
    # decide whether to use exchange or margin markets
    limit_type = LIMIT if self.exchange_type == self.ExchangeType.MARGIN else EXCHANGE_LIMIT
    stop_type = STOP_LIMIT if self.exchange_type == self.ExchangeType.MARGIN else EXCHANGE_STOP_LIMIT
    # set local vars
    current_exit_order = position.exit_order
    # check if we need to update
    if new_exit_order.is_equal_to(current_exit_order):
      self.logger.info("New exit order is the same as live exit order.")
      return
    # check if there is already a pending order with same values
    if position.pending_exit_order:
      if position.pending_exit_order.is_equal_to(new_exit_order):
        self.logger.info("New exit order is the same as pending exit order.")
        return
    position.exit_order.stop_type = new_exit_order.stop_type
    position.exit_order.target_type = new_exit_order.target_type
    position.exit_order.stop = new_exit_order.stop
    position.exit_order.target = new_exit_order.target
    position.exit_order.amount = new_exit_order.amount
    # check if we are in backtest mode
    if self.is_backtesting():
      # TODO fake limit stop loss for backtesting
      return

    # set position exit_order callback
    async def create_complete(order):
      print ("********* Complete")
      # now stop is confirmed, we can set local vars
      position.exit_order.amount = new_exit_order.amount
      position.pending_exit_order = None
      position.exit_order.set_order(order)

    async def create_exit_order(order):
      print ("******** CREATING")
      # set a pending exit order on position
      position.pending_exit_order = new_exit_order
      group_id = int(round(time.time() * 1000))
      if new_exit_order.is_target_limit() and new_exit_order.is_stop_limit():
        self.logger.info("Submitting stop loss at price={} amount={}".format(
          new_exit_order.stop, new_exit_order.amount))
        self.logger.info("Submitting target exit at price={} amount={}".format(
          new_exit_order.target, new_exit_order.amount))
        # open oco order
        await self._submit_position_trade(position, new_exit_order.target, new_exit_order.amount,
          last.mts, limit_type, oco=True, oco_stop_price=new_exit_order.stop, gid=group_id,
          onConfirm=create_complete)
      elif new_exit_order.is_target_limit():
        # just a limit for target
        self.logger.info("Submitting target exit at price={} amount={}".format(
          new_exit_order.target, new_exit_order.amount))
        await self._submit_position_trade(position, new_exit_order.target, new_exit_order.amount,
          last.mts, limit_type, gid=group_id, onConfirm=create_complete)
      elif new_exit_order.is_stop_limit():
        # just a stop-limit for stop loss
        self.logger.info("Submitting stop loss at price={} amount={}".format(
          new_exit_order.stop, new_exit_order.amount))
        await self._submit_position_trade(position, new_exit_order.stop, new_exit_order.amount,
          last.mts, stop_type, gid=group_id, price_aux_limit=new_exit_order.stop,
          onConfirm=create_complete)
      else:
        # exit order is of type market
        await create_complete(None)

    print ("Here.....")
    # check if we currently have an exit order set
    if position.exit_order.order:
      if new_exit_order.amount != 0:
        print ("Recreate")
        # close the current exit order and re-create
        await self.orderManager.cancel_order_group(position.exit_order.order.gid, onConfirm=create_exit_order)
      else:
        print ("cancel gid: {}".format(position.exit_order.order.gid))
        # just cancel order
        await self.orderManager.cancel_order_group(position.exit_order.order.gid)
        position.exit_order.order = None
    else:
      print ("Create")
      # create the exit order
      await create_exit_order(None)

  async def _submit_position_trade(self, position, price, amount, mts_create, market_type,
      *args, **kwargs):
    symbol = position.symbol
    await self.orderManager.submit_trade(symbol, price, amount, mts_create,
      market_type, *args, **kwargs)

  def _market_price(self):
    ## market price does not matter when submitting orders to bfx
    ## but this helps the offline backtests stay in sync
    return self.get_last_price_update(self.symbol).price
