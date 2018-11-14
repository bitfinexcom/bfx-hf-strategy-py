import logging
import time

from .Order import Order
from .Trade import Trade
from ..utils.CustomLogger import CustomLogger

class OrderManager(object):
  ''' Handles raw orders and communication with the websocket '''

  def __init__(self, ws, backtesting=False, logLevel='INFO'):
    self.ws = ws
    self.logger = CustomLogger('HFOrderManager', logLevel=logLevel)
    self.backtesting = backtesting

  async def _submit_order(self, symbol, price, amount, mtsCreate, **kwargs):
    self.logger.info('Strategy in live mode, submitting order.')
    await self.ws.submit_order(symbol, price, amount, mtsCreate)
    return Order(symbol, amount, price, mtsCreate)

  def _simulate_order_fill(self, symbol, price, amount, mtsCreate, **kwargs):
    self.logger.info('Strategy in backtest mode, Simulating order fill.')
    return Order(symbol, amount, price, mtsCreate)

  async def submitTrade(self, *args, **kwargs):
    tag = kwargs.get('tag', '')
    if (self.backtesting):
      order = self._simulate_order_fill(*args, **kwargs)
      trade = Trade(order, tag=tag)
      return order, trade
    else:
      order = await self._submit_order(*args, **kwargs)
      trade = Trade(order, tag=tag)
      return order, trade

