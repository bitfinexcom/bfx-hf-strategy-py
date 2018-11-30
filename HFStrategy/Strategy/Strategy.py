import logging
import math
import asyncio
from threading import Thread
from pyee import EventEmitter

from .PositionManager import PositionManager
from .Position import Position
from ..utils.CustomLogger import CustomLogger
from ..models import Events, PriceUpdate

def candleMarketDataKey(candle):
  return '%s-%s' % (candle['symbol'], candle['tf'])

class Strategy(PositionManager):
  def __init__(self, backtesting = False, symbol='tBTCUSD', indicators={}, logLevel='INFO'):
    self.marketData = {}
    self.positions = {}
    self.lastPrice = {}
    self.closedPositions = []
    self.indicators = indicators
    self.candle_price_key = 'close'
    self.backtesting = backtesting
    self.symbol = symbol
    self.events = EventEmitter(scheduler=asyncio.ensure_future)
    # initialise custom logger
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
          i.add(data[dk])

  def _update_indicator_data(self, dataType, data):
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
    self._update_indicator_data('trade', price)

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
    self._update_indicator_data('trade', trade['price'])

  async def _process_price_update(self, update):
    self.lastPrice[update.symbol] = update
    # TODO: Handle stops/targets
    if update.symbol not in self.positions:
      await self._execute_events(Events.ON_ENTER, update)
    else:
      symPosition = self.positions[update.symbol]
      amount = symPosition.amount

      await self._execute_events(Events.ON_UPDATE, update)

      if amount > 0:
        await self._execute_events(Events.ON_UPDATE_LONG, update)
      else:
        await self._execute_events(Events.ON_UPDATE_SHORT, update)

  ############################
  #      Public Functions    #
  ############################

  def get_last_price_update(self, symbol):
    update = self.lastPrice[symbol]
    return update

  def get_position(self, symbol):
    return self.positions.get(symbol)

  def add_position(self, position):
    self.positions[position.symbol] = position

  def remove_position(self, position):
    self.logger.debug("Archiving closed position {}".format(position))
    self.closedPositions += [position]
    del self.positions[position.symbol]

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
    if not func:
      return self.events.on(event)
    self.events.on(event, func)

  def once(self, event, func=None):
    if not func:
      return self.events.once(event)
    self.events.once(event, func)

  def set_indicators(self, indicators):
    self.indicators = indicators

  def get_indicators(self):
    return self.indicators
  
  ############################
  #       Event Hooks        #
  ############################

  def on_error(self, func=None):
    if not func:
      return self.events.on(Events.ERROR)
    self.events.on(Events.ERROR, func)

  def on_enter(self, func=None):
    if not func:
      return self.events.on(Events.ON_ENTER)
    self.events.on(Events.ON_ENTER, func)

  def on_update(self, func=None):
    if not func:
      return self.events.on(Events.ON_UPDATE)
    self.events.on(Events.ON_UPDATE, func)

  def on_update_long(self, func=None):
    if not func:
      return self.events.on(Events.ON_UPDATE_LONG)
    self.events.on(Events.ON_UPDATE_LONG, func)

  def on_update_short(self, func=None):
    if not func:
      return self.events.on(Events.ON_UPDATE_SHORT)
    self.events.on(Events.ON_UPDATE_SHORT, func)

  def on_order_fill(self, func=None):
    if not func:
      return self.events.on(Events.ON_ORDER_FILL)
    self.events.on(Events.ON_ORDER_FILL, func)

  def on_position_update(self, func=None):
    if not func:
      return self.events.on(Events.ON_POSITION_UPDATE)
    self.events.on(Events.ON_POSITION_UPDATE, func)

  def on_position_close(self, func=None):
    if not func:
      return self.events.on(Events.ON_POSITION_CLOSE)
    self.events.on(Events.ON_POSITION_CLOSE, func)
