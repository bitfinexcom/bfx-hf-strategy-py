import time
import json
import asyncio

from .. import Strategy
from bfxhfindicators import MACD
from ..utils.mock_websocket_client import MockClient
from ..utils.mock_order_manager import MockOrderManager

def generate_fake_candle(mts=None, open=6373,  close=6374.5, high=6375.9,
		low=6369.2, volume=38.58293517, symbol='tBTCUSD', tf='1h'):
	mts = mts or int(round(time.time() * 1000))
	return {
		'mts': mts,
		'open': open,
		'close': close,
		'high': high,
		'low': low,
		'volume': volume,
		'symbol': symbol,
		'tf': tf,
	}

def create_mock_strategy(symbol='tBTCUSD', indicators=None):
	if not indicators:
		indicators = {
      'macd': MACD([10, 26, 9]),
    }

	# create a test strategy
	strategy = Strategy(
		symbol=symbol,
		indicators=indicators,
		exchange_type=Strategy.ExchangeType.EXCHANGE,
		logLevel='DEBUG'
	)

  # create mock bfxapi
	bfx = MockClient()
  # create a backtest mode order manager
	bfxOrderManager = MockOrderManager(bfx, logLevel='DEBUG')
	strategy.set_order_manager(bfxOrderManager)
	strategy.mock_ws = bfx
	return strategy

class EventWatcher():

	def __init__(self, eventListener, event):
		self.value = None
		self.event = event
		eventListener.once(event, self._finish)

	async def _finish(self, value):
		self.value = value or {}

	@classmethod
	def watch(cls, eventListener, event):
		return EventWatcher(eventListener, event)

	async def wait_until_complete(self, max_wait_time=5):
		counter = 0
		while self.value == None:
			if counter > 5:
				raise Exception('Wait time limit exceeded for event {}'.format(self.event))
			# force schedler to reposition in queue
			await asyncio.sleep(0.001)
			counter += 1
		return self.value
