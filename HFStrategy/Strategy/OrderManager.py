import logging
import time

from .Order import Order
from .Trade import Trade
from ..utils.CustomLogger import CustomLogger

class OrderManager(object):
  ''' Handles raw orders and communication with the websocket '''

  def __init__(self, backtesting=False, logLevel='INFO'):
      # initialise custom logger
      self.logger = CustomLogger('HFOrderManager', logLevel=logLevel)
      self.backtesting = backtesting

  def submitOrder(self, orderParams):
    self.logger.info('Strategy in live mode, submitting order.')
    pass

  def _simulateOrderFill(self, orderParams):
    self.logger.info('Strategy in backtest mode, Simulating order fill.')
    priceAvg = orderParams.get('price')
    mtsCreate = now_in_mills()
    return Order(orderParams.get('symbol'), priceAvg)

  def submitTrade(self, orderParams):
    if (self.backtesting):
      # simulate
      order = self._simulateOrderFill(orderParams)
      trade = Trade(order)
      return order, trade
    else:
      ## trade for real
      return None, None

