import asyncio
from pyee import EventEmitter

class MockWebsocket:
  events = EventEmitter(scheduler=asyncio.ensure_future)

  def on(self, *args, **kwargs):
    self.events.on(*args, **kwargs)

  def _emit(self, *args, **kwargs):
    self.events.emit(*args, **kwargs)

  def remove_all_listeners(self, *args, **kwargs):
    self.events.remove_all_listeners(*args, **kwargs)

class MockClient:
  ws = MockWebsocket()
