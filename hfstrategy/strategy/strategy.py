import logging
import math
import asyncio
from threading import Thread
from pyee import EventEmitter

from .position_manager import PositionManager
from .position import Position
from ..utils.custom_logger import CustomLogger
from ..models import Events, PriceUpdate

def candleMarketDataKey(candle):
  return '%s-%s' % (candle['symbol'], candle['tf'])

class ExchangeType:
  """ The type of exchange to operate on """
  EXCHANGE = 'EXCHANGE'
  MARGIN = 'MARGIN'

class Strategy(PositionManager):
  """
  This class is the base of the HF framework and is used to help easily maintain
  position on the market. This class also exposes function from the PositionManager
  which are used to open/update/close orders. An event emitter is available which triggers
  on price updates and positions updates, here is a full list of the available events:

  *Note: price udates occur whenever that is a new candle or a new public trade has been
  matched on the orderbook

  @event on_error: an error has occured
  @event on_enter: there is no open position and the price is updated
  @event on_update: there is a price update
  @event on_update_long: you have a long position open and the price has been updated
  @event on_update_short: you have a short position open and the price has been updated
  @event on_order_fill: a new order is filled
  @event on_position_updated: you have a position open and the price has been updated
  @event on_position_close: you had a position open and it has now been closed
  @event on_position_stop_reached: your open position has just reached its stop price
  @event on_position_target_reached: your open position has just reached its target price
  """
  ExchangeType = ExchangeType()

  def __init__(self, backtesting=False, symbol='tBTCUSD', indicators={}, logLevel='INFO',
      exchange_type=ExchangeType.EXCHANGE):
    self.exchange_type = exchange_type
    self.marketData = {}
    self.positions = {}
    self.lastPrice = {}
    self.closedPositions = []
    self.is_ready = False
    self.indicators = indicators
    self.candle_price_key = 'close'
    self.backtesting = backtesting
    self.symbol = symbol
    self.events = EventEmitter(scheduler=asyncio.ensure_future)
    # initialise custom logger
    self.logLevel = logLevel
    self.logger = CustomLogger('HFStrategy', logLevel=logLevel)
    super(Strategy, self).__init__()

  async def _emit(self, event, *args, **kwargs):
    await self._execute_events(event, *args, **kwargs)

  async def _execute_events(self, event, *args, **kwargs):
    # get all coroutines that are listening to the event
    listeners = self.events.listeners(event)
    # execute them now to avoid pyee scheduling them
    await asyncio.gather(*[f(*args, **kwargs) for f in listeners])

  def _add_indicator_data(self, dataType, data):
    for key in self.indicators:
      i = self.indicators[key]
      dt = i.get_data_type()
      dk = i.get_data_key()
  
      if dt == '*' or dt == dataType:
        if dk == '*':
          i.add(data)
        else:
          d = data.get(dk)
          if d:
            i.add(d)

  def _update_indicator_data(self, dataType, data):
    for key in self.indicators:
      i = self.indicators[key]
      dt = i.get_data_type()
      dk = i.get_data_key()
 
      if dt == '*' or dt == dataType:
        if dk == '*':
          i.update(data)
        else:
          d = data.get(dk)
          if d:
            i.update(d)

  def _add_candle_data(self, candle):
    dataKey = candleMarketDataKey(candle)
    if dataKey in self.marketData:
      self.marketData[dataKey].append(candle)
    else:
      self.marketData[dataKey] = []

  def _update_candle_data(self, candle):
    dataKey = candleMarketDataKey(candle)
    if dataKey in self.marketData:
      self.marketData[dataKey][-1] = candle
    else:
      self.marketData[dataKey] = [candle]

  #############################
  #      Private events       #
  #############################

  async def _process_new_candle(self, candle):
    self._add_indicator_data('candle', candle)

    if self.is_indicators_ready():
      price = candle[self.candle_price_key]
      pu = PriceUpdate(
        price, candle['symbol'], candle['mts'], PriceUpdate.CANDLE, candle=candle)
      pu.set_indicator_values(self.get_indicator_values())
      await self._process_price_update(pu)

  async def _process_new_trade(self, trade):
    price = trade['price']
    self._update_indicator_data('trade', trade)

    if self.is_indicators_ready():
      pu = PriceUpdate(
        price, trade['symbol'], trade['mts'], PriceUpdate.TRADE, trade=trade)
      pu.set_indicator_values(self.get_indicator_values())
      await self._process_price_update(pu)

  def _process_new_seed_candle(self, candle):
    self._add_indicator_data('candle', candle)
    candle['iv'] = self.get_indicator_values()
    self._add_candle_data(candle)

  def _process_new_seed_trade(self, trade):
    self._update_indicator_data('trade', trade)

  async def _process_price_update(self, update):
    self.lastPrice[update.symbol] = update
    # TODO: Handle stops/targets
    if update.symbol not in self.positions:
      await self._execute_events(Events.ON_ENTER, update)
    else:
      symPosition = self.positions[update.symbol]
      amount = symPosition.amount
      symPosition.update_with_price(update.price)

      await self._execute_events(Events.ON_UPDATE, update, symPosition)

      # Check if stop or target price has been reached
      if symPosition.has_reached_stop(update):
        self.logger.info("Stop price reached for position: {}".format(symPosition))
        if symPosition.exit_order.is_stop_market():
          await self.close_position_market(
            mtsCreate=update.mts, tag="Stop price reached")
          return await self._execute_events(
            Events.ON_POSITION_STOP_REACHED, update, symPosition)
      if symPosition.has_reached_target(update):
        self.logger.info("Target price reached for position: {}".format(symPosition))
        if symPosition.exit_order.is_target_market():
          await self.close_position_market(
            mtsCreate=update.mts, tag="Target price reached")
          return await self._execute_events(
            Events.ON_POSITION_TARGET_REACHED, update, symPosition)

      if amount > 0:
        await self._execute_events(Events.ON_UPDATE_LONG, update, symPosition)
      else:
        await self._execute_events(Events.ON_UPDATE_SHORT, update, symPosition)

  def _connected(self):
    # check if there are any positions open
    if len(self.positions.keys()) > 0:
      self.logger.info("New connection detected, resetting strategy positions.")
      self._reset()

  async def _ready(self, *args, **kwargs):
    self.is_ready = True
    await self._execute_events(Events.ON_READY)

  def _reset(self):
    """
    Resets the state of the strategy to have no open positions. This
    is called by default when the websocket disconnects and the dead_man_switch
    kicks in.
    """
    self.logger.info("Reset called. Moving all positions to closed.")
    # set all positions to closed
    for key in self.positions.keys():
      self.positions[key].close()
      self.closedPositions += [self.positions[key]]
    self.positions = {}

  def _add_position(self, position):
    self.positions[position.symbol] = position

  def _remove_position(self, position):
    self.logger.debug("Archiving closed position {}".format(position))
    self.closedPositions += [position]
    del self.positions[position.symbol]

  ############################
  #      Public Functions    #
  ############################

  def get_last_price_update(self, symbol):
    """
    Get the last received price update

    @param symbol: string currency pair i.e 'tBTCUSD'
    @return PriceUpdate
    """
    update = self.lastPrice.get(symbol, None)
    return update

  def get_position(self, symbol):
    """
    Get the position of the given symbol. If it is not open then
    return None

    @param symbol: string currency pair i.e 'tBTCUSD'
    @return Position
    """
    return self.positions.get(symbol)

  def get_indicator_values(self):
    values = {}
    for key in self.indicators:
      values[key] = self.indicators[key].v()
    return values

  def is_indicators_ready(self):
    for key in self.indicators:
      if not self.indicators[key].ready():
        return False
    return True

  def on(self, event, func=None):
    """
    Subscribe to the given event

    func can be either an asyncio coroutine or a function.

    @param event: string event name
    @param func: called when event name emitted
    """
    if not func:
      return self.events.on(event)
    self.events.on(event, func)

  def once(self, event, func=None):
    """
    Subscribe to the given event but only fire once.
    func can be either an asyncio coroutine or a function

    @param event: string event name
    @param func: called when event name emitted
    """
    if not func:
      return self.events.once(event)
    self.events.once(event, func)

  def get_indicators(self):
    """
    Get all indicatios
  
    @return dict
    """
    return self.indicators

  def is_backtesting(self):
    """
    Get the mode of the strategy.

    @return True if in backtesting mode
    """
    return self.backtesting

  ############################
  #       Event Hooks        #
  ############################

  def on_error(self, func=None):
    """
    Subscribe to the on error event

    This event is fired whenever an error occurs from either the websocket
    or the strategy class.
    func can be either an asyncio coroutine or a function.

    @event Exception
    @param func: called when an error is emitted
    """
    if not func:
      return self.events.on(Events.ERROR)
    self.events.on(Events.ERROR, func)

  def on_ready(self, func=None):
    """
    Subscribe to the on ready event

    This event is fired whenever the strategy is ready to begin execution. This could
    be triggered either by webscoket authentication, backtest websocket connection or
    backtest data loaded.

    @param func: called when the strategy is ready
    """
    if not func:
      return self.events.on(Events.ON_READY)
    self.events.on(Events.ON_READY, func)

  def on_enter(self, func=None):
    """
    Subscribe to the on enter event

    This event is fired whenever a price update is received but there are
    no open positions. Once a position is opened then this event will
    stop being called once again until all positions are closed.
    func can be either an asyncio coroutine or a function.

    @event PriceUpdate
    @param func: called when a price update is emitted
    """
    if not func:
      return self.events.on(Events.ON_ENTER)
    self.events.on(Events.ON_ENTER, func)

  def on_update(self, func=None):
    """
    Subscribe to the on update event

    This event is fired whenever a price update is received.
    func can be either an asyncio coroutine or a function.

    @event PriceUpdate, Position
    @param func: called when update event emitted
    """
    if not func:
      return self.events.on(Events.ON_UPDATE)
    self.events.on(Events.ON_UPDATE, func)

  def on_update_long(self, func=None):
    """
    Subscribe to the on update long event

    This event fires whenever there is a price update and
    there is an open long position.
    func can be either an asyncio coroutine or a function.

    @event PriceUpdate, Position
    @param func: called when update long emitted
    """
    if not func:
      return self.events.on(Events.ON_UPDATE_LONG)
    self.events.on(Events.ON_UPDATE_LONG, func)

  def on_update_short(self, func=None):
    """
    Subscribe to the on update short event

    This event fires whenever there is a price update and there
    is an open short position.
    func can be either an asyncio coroutine or a function.

    @event PriceUpdate, Position
    @param func: called when update short emitted 
    """
    if not func:
      return self.events.on(Events.ON_UPDATE_SHORT)
    self.events.on(Events.ON_UPDATE_SHORT, func)

  def on_order_fill(self, func=None):
    """
    Subscribe to the on order fill event

    This event firest whenever a submitted order has been filled.
    func can be either an asyncio coroutine or a function.

    @event Order
    @param func: called when order fill emitted
    """
    if not func:
      return self.events.on(Events.ON_ORDER_FILL)
    self.events.on(Events.ON_ORDER_FILL, func)

  def on_position_update(self, func=None):
    """
    Subscribe to the on position update event

    This event fired whenever the position is updated with a new order.
    func can be either an asyncio coroutine or a function.

    @event Position
    @param func: called when position update emitted
    """
    if not func:
      return self.events.on(Events.ON_POSITION_UPDATE)
    self.events.on(Events.ON_POSITION_UPDATE, func)

  def on_position_close(self, func=None):
    """
    Subscribe to the on position close event

    This event is fired whenever an open position is closed.
    func can be either an asyncio coroutine or a function.

    @event Position
    @param func: called when position close emitted
    """
    if not func:
      return self.events.on(Events.ON_POSITION_CLOSE)
    self.events.on(Events.ON_POSITION_CLOSE, func)

  def on_position_stop_reached(self, func=None):
    """
    Subscribe to the on position stop reached event

    This event is fired whenever an open position reaches its
    specified stop price. Please be aware that the closing of
    the position will have already been handled at the time of the event
    being fired.
    func can be either an asyncio coroutine or a function.

    @event PriceUpdate, Position
    @param func: called when position stop reached emitted
    """
    if not func:
      return self.events.on(Events.ON_POSITION_STOP_REACHED)
    self.events.on(Events.ON_POSITION_STOP_REACHED, func)

  def on_position_target_reached(self, func=None):
    """
    Subscribe to the on position target reached event

    This event is fired whenever an open position reaches its
    specified target price. Please be aware that the closing of
    the position will have already been handled at the time of the event
    being fired.
    func can be either an asyncio coroutine or a function.

    @event PriceUpdate, Position
    @param func: called when position target reached emitted
    """
    if not func:
      return self.events.on(Events.ON_POSITION_TARGET_REACHED)
    self.events.on(Events.ON_POSITION_TARGET_REACHED, func)
