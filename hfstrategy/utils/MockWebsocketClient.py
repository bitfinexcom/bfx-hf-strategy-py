import asyncio
from pyee import EventEmitter

class MockWebsocket:
  events = EventEmitter(scheduler=asyncio.ensure_future)

  def on(self, *args, **kwargs):
    self.events.on(*args, **kwargs)

  async def _emit(self, event, *args, **kwargs):
    listeners = self.events.listeners(event)
    await asyncio.gather(*[f(*args, **kwargs) for f in listeners])

  def remove_all_listeners(self, *args, **kwargs):
    self.events.remove_all_listeners(*args, **kwargs)

  async def cancel_order(self, *args, **kawargs):
    pass

class MockClient:
  ws = MockWebsocket()
