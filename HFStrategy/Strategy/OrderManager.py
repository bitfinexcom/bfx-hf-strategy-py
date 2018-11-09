import logging
import time

from .Order import Order
from .Trade import Trade
from ..utils.CustomLogger import CustomLogger

class OrderManager(object):
  ''' Handles raw orders and communication with the websocket '''

  def __init__(self, backtesting=False, logLevel='INFO'):
      self.logger = CustomLogger('HFOrderManager', logLevel=logLevel)
      self.backtesting = backtesting

  def submitOrder(self, orderParams):
    self.logger.info('Strategy in live mode, submitting order.')
    pass

  def _simulateOrderFill(self, symbol, price, amount, mtsCreate, **kwargs):
    self.logger.info('Strategy in backtest mode, Simulating order fill.')
    return Order(symbol, amount, price, mtsCreate)

  def submitTrade(self, *args, **kwargs):
    tag = kwargs.get('tag', '')
    if (self.backtesting):
      order = self._simulateOrderFill(*args, **kwargs)
      trade = Trade(order, tag=tag)
      return order, trade
    else:
      ## trade for real
      order = self._simulateOrderFill(*args, **kwargs)
      trade = Trade(order, tag=tag)
      return order, trade

