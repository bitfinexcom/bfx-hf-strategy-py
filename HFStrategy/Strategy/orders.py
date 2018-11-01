import logging

from .Order import Order
from .Trade import Trade

logger = logging.getLogger('HFStrategy')

def submitOrder(orderParams):
  pass

def _simulateOrderFill(orderParams):
  price = orderParams.get('price')
  order = Order(orderParams.get('symbol'), price)
  return order

def submitTrade(orderParams, backtesting):
  logger.info("boom")
  if (backtesting):
    # simulate
    order = _simulateOrderFill(orderParams)
    trade = Trade(order)
    return order, trade
  else:
    ## trade for real
    return None, None

def tradeForOrder(orderParams, label, tag):
  pass

def validateOrderParams(orderParams):
  pass
