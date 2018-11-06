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

  def _simulateOrderFill(self, orderParams):
    self.logger.info('Strategy in backtest mode, Simulating order fill.')
    priceAvg = orderParams.get('price')
    amount = orderParams.get('amount')
    symbol = orderParams.get('symbol')
    mtsCreate = orderParams.get('mtsCreate')
    return Order(symbol, amount, priceAvg, mtsCreate)

  def submitTrade(self, orderParams):
    if (self.backtesting):
      order = self._simulateOrderFill(orderParams)
      trade = Trade(order)
      return order, trade
    else:
      ## trade for real
      return None, None

