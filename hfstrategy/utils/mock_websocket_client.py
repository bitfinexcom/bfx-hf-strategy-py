import time
import asyncio

from pyee import EventEmitter

class MockWebsocket():

  def __init__(self):
    self.events = EventEmitter(scheduler=asyncio.ensure_future)
    self.saved_items = []
    self.emitted_items = []

  def on(self, *args, **kwargs):
    self.events.on(*args, **kwargs)

  def once(self, *args, **kwargs):
    self.events.once(*args, **kwargs)

  def _emit(self, event, *args, **kwargs):
    # save published items for testing
    self.emitted_items += [{
      'time': int(round(time.time() * 1000)),
      'data': {
        'event': event,
        'args': args,
        'kwargs': kwargs
      }
    }]
    self.events.emit(event, *args,  **kwargs)

  def remove_all_listeners(self, *args, **kwargs):
    self.events.remove_all_listeners(*args, **kwargs)

  def cancel_order(self, *args, **kawargs):
    pass

  def submit_order(self, *args, **kawargs):
    pass

  def get_emitted_items(self):
    return self.emitted_items

  def get_last_emitted_item(self):
    return self.emitted_items[-1:][0]

  def get_emitted_items_count(self):
    return len(self.emitted_items)

class MockClient:
  ws = MockWebsocket()
