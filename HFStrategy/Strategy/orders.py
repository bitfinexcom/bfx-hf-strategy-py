import logging

def submitOrder(orderParams):
  pass

def _simulateOrderFill(orderParams):
  pass

def submitTrade(orderParams, backtesting):
  if (backtesting):
    # simulate
    return None, None
  else:
    ## trade for real
    return None, None

def tradeForOrder(orderParams, label, tag):
  pass

def validateOrderParams(orderParams):
  pass
