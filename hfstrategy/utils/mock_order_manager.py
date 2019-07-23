import logging
import time
import asyncio

from ..utils.custom_logger import CustomLogger
from bfxapi.models import Order, Trade

def generate_fake_data(symbol, price, amount, mts_create, market_type, *args, gid=None, **kwargs):
  order_id = int(round(time.time() * 1000))
  d = [order_id, gid, 3, symbol, mts_create, mts_create, 0, amount, market_type, market_type,
      None, None, None, "EXECUTED @ {}({})".format(price, amount), None, None, price,
      price, 0, 0, None, None, None, 0, 0, None, None, None, "API>BFX", None, None, None]
  return Order.from_raw_order(d)

class MockOrderManager(object):

  def __init__(self, bfxapi, *args, logLevel='INFO', **kwargs):
    self.logger = CustomLogger('HFSimulatedOrderManager', logLevel=logLevel)
    self.bfxapi = bfxapi
    self.ws = bfxapi.ws
    self.sent_requests = []

  async def cancel_active_order(self, *args, onConfirm=None, **kwargs):
    # save submission for testing
    self._save_request('cancel_active_order', *args, **kwargs)
    if onConfirm:
      await onConfirm(None)

  async def cancel_order_multi(self, *args, onConfirm=None, **kwargs):
    self._save_request('cancel_order_multi', *args, **kwargs)
    if onConfirm:
      await onConfirm(None)

  async def cancel_order_group(self, *args, onConfirm=None, **kwargs):
    self._save_request('cancel_order_group', *args, **kwargs)
    if onConfirm:
      await onConfirm(None)

  async def submit_trade(self, *args, onConfirm=None, onClose=None, **kwargs):
    # save submission for testing
    self._save_request('submit_trade', *args, **kwargs)
    order = generate_fake_data(*args, **kwargs)
    if onConfirm:
      await onConfirm(order)
    if onClose:
      await onClose(order)
      if asyncio.iscoroutinefunction(self.bfxapi.ws._emit):
        await self.bfxapi.ws._emit('order_closed', order)
      else:
        self.bfxapi.ws._emit('order_closed', order)

  def _save_request(self, func_name, *args, **kwargs):
    self.sent_requests += [{
      'time': int(round(time.time() * 1000)),
      'data': {
        "func": func_name,
        "args": args,
        "kwargs": kwargs
      }
    }]

  def get_sent_items(self):
    return self.sent_requests

  def get_last_sent_item(self):
    return self.sent_requests[-1:][0]

  def get_sent_items_count(self):
    return len(self.sent_requests)
