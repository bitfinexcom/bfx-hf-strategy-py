import logging
import time

from ..utils.CustomLogger import CustomLogger
from bfxapi.models import Order, Trade

def generate_fake_data(symbol, price, amount, mtsCreate, market_type, *args, **kwargs):
  d = [1, 2, 3, symbol, mtsCreate, mtsCreate, amount, amount, market_type, market_type,
      None, None, None, "EXECUTED @ {}({})".format(price, amount), None, None, price,
      price, 0, 0, None, None, None, 0, 0, None, None, None, "API>BFX", None, None, None]
  return Order.from_raw_ws_order(d)

class OrderManager(object):
  ''' Handles raw orders and communication with the websocket '''

  def __init__(self, ws, backtesting=False, logLevel='INFO'):
    self.ws = ws
    self.logger = CustomLogger('HFOrderManager', logLevel=logLevel)
    self.backtesting = backtesting

  async def _submit_order(self, symbol, price, amount, mtsCreate,
      market_type, *args, **kwargs):
    self.logger.info('Strategy in live mode, submitting order.')
    await self.ws.submit_order(symbol, price, amount, market_type, *args, **kwargs)

  async def _simulate_order_fill(self, *args, onClose=None, **kwargs):
    self.logger.info('Strategy in backtest mode, Simulating order fill.')
    order = generate_fake_data(*args, **kwargs)
    if onClose:
      await onClose(order)
    

  async def submitTrade(self, *args, **kwargs):
    tag = kwargs.get('tag', '')
    if (self.backtesting):
      await self._simulate_order_fill(*args, **kwargs)
    else:
      await self._submit_order(*args, **kwargs)

