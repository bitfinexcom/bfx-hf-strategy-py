import logging
import time
import asyncio

from ..utils.custom_logger import CustomLogger
from bfxapi.models import Order, Trade

class OrderManager(object):
  ''' Handles raw orders and communication with the websocket '''

  def __init__(self, bfxapi, logLevel='INFO'):
    self.bfxapi = bfxapi
    self.ws = bfxapi.ws
    self.logger = CustomLogger('HFOrderManager', logLevel=logLevel)

  async def _submit_order(self, symbol, price, amount, mtsCreate,
      market_type, *args, **kwargs):
    self.logger.info('Strategy in live mode, submitting order.')
    await self.ws.submit_order(symbol, price, amount, market_type, *args, **kwargs)

  async def cancel_active_order(self, *args, **kwargs):
    await self.ws.cancel_order(*args, **kwargs)

  async def cancel_order_group(self, *args, **kwargs):
    await self.ws.cancel_order_group(*args, **kwargs)

  async def submit_trade(self, *args, **kwargs):
    await self._submit_order(*args, **kwargs)

