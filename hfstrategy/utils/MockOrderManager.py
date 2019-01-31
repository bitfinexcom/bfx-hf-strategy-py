import logging
import time
import asyncio

from ..utils.CustomLogger import CustomLogger
from bfxapi.models import Order, Trade

def generate_fake_data(symbol, price, amount, mts_create, market_type, *args, **kwargs):
  order_id = int(round(time.time() * 1000))
  d = [order_id, 2, 3, symbol, mts_create, mts_create, 0, amount, market_type, market_type,
      None, None, None, "EXECUTED @ {}({})".format(price, amount), None, None, price,
      price, 0, 0, None, None, None, 0, 0, None, None, None, "API>BFX", None, None, None]
  return Order.from_raw_order(d)

class MockOrderManager(object):

  def __init__(self, bfxapi, *args, logLevel='INFO', **kwargs):
    self.logger = CustomLogger('HFSimulatedOrderManager', logLevel=logLevel)
    self.bfxapi = bfxapi
    self.ws = bfxapi.ws

  async def cancel_active_order(self, *args, **kwargs):
    pass

  async def submit_trade(self, *args, onConfirm=None, onClose=None, **kwargs):
    order = generate_fake_data(*args, **kwargs)
    if onConfirm:
      await onConfirm(order)
    if onClose:
      await onClose(order)
      if asyncio.iscoroutinefunction(self.bfxapi.ws._emit):
        await self.bfxapi.ws._emit('order_closed', order)
      else:
        self.bfxapi.ws._emit('order_closed', order)
